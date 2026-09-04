"""
CPU Telemetry Module
Monitors CPU temperatures, per-core utilization, clock frequencies,
and detects active thermal throttling using Windows-native APIs and fallbacks.
"""

import os
import time
from typing import Dict, List, Optional, Any
import psutil

# Optional WMI import for Windows thermal zones
try:
    import wmi
    import pythoncom
    HAS_WMI = True
except ImportError:
    HAS_WMI = False


class CPUTelemetry:
    def __init__(self):
        self._last_poll_time = time.time()
        self.base_freq_mhz = self._get_base_frequency()

    def _get_base_frequency(self) -> float:
        """Determines CPU base/max frequency in MHz."""
        freq = psutil.cpu_freq()
        if freq and freq.max > 0:
            return freq.max
        elif freq and freq.current > 0:
            return freq.current
        return 3200.0  # Safe default if unavailable

    def get_temperature_celsius(self) -> Dict[str, Any]:
        """
        Attempts multiple Windows temperature extraction techniques:
        1. LibreHardwareMonitor / OpenHardwareMonitor WMI namespace
        2. Windows ACPI ThermalZone WMI namespace (MSAcpi_ThermalZoneTemperature)
        3. psutil sensors_temperatures() (Linux/FreeBSD or patched Windows psutil)
        Returns:
            Dict containing package temp, per-core temps (if available), sensor source, and status.
        """
        result = {
            "package_temp": None,
            "core_temps": [],
            "source": "None",
            "is_hardware_direct": False,
            "error": None
        }

        # Method 1: LibreHardwareMonitor / OpenHardwareMonitor WMI (Gold standard for Windows)
        if HAS_WMI:
            try:
                pythoncom.CoInitialize()
                for namespace in ["root\\LibreHardwareMonitor", "root\\OpenHardwareMonitor"]:
                    try:
                        w = wmi.WMI(namespace=namespace)
                        sensors = w.Sensor()
                        cpu_temps = [
                            s.Value for s in sensors 
                            if s.SensorType == "Temperature" and ("CPU" in s.Name or "Core" in s.Name or "Package" in s.Name)
                        ]
                        if cpu_temps:
                            result["package_temp"] = round(float(max(cpu_temps)), 1)
                            result["core_temps"] = [round(float(t), 1) for t in cpu_temps]
                            result["source"] = namespace.split("\\")[-1]
                            result["is_hardware_direct"] = True
                            return result
                    except Exception:
                        continue
            except Exception as e:
                result["error"] = str(e)
            finally:
                try:
                    pythoncom.CoUninitialize()
                except Exception:
                    pass

        # Method 2: Windows native ACPI Thermal Zone
        if HAS_WMI and result["package_temp"] is None:
            try:
                pythoncom.CoInitialize()
                w = wmi.WMI(namespace="root\\wmi")
                zones = w.MSAcpi_ThermalZoneTemperature()
                temps = []
                for zone in zones:
                    # Windows reports temperature in tenths of Kelvin
                    raw_kelvin = getattr(zone, "CurrentTemperature", None)
                    if raw_kelvin and raw_kelvin > 2732:  # > 0°C sanity check
                        celsius = (raw_kelvin - 2732) / 10.0
                        if 10.0 <= celsius <= 125.0:  # Valid PC operating range
                            temps.append(celsius)
                if temps:
                    result["package_temp"] = round(float(max(temps)), 1)
                    result["core_temps"] = [round(float(t), 1) for t in temps]
                    result["source"] = "WMI ACPI ThermalZone"
                    result["is_hardware_direct"] = True
                    return result
            except Exception as e:
                # ACPI access often requires admin rights or OEM ACPI tables
                result["error"] = str(e)
            finally:
                try:
                    pythoncom.CoUninitialize()
                except Exception:
                    pass

        # Method 3: Standard psutil sensors (if supported on platform)
        if hasattr(psutil, "sensors_temperatures"):
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    all_readings = []
                    for name, entries in temps.items():
                        for entry in entries:
                            if entry.current is not None:
                                all_readings.append(entry.current)
                    if all_readings:
                        result["package_temp"] = round(float(max(all_readings)), 1)
                        result["source"] = "psutil sensors"
                        result["is_hardware_direct"] = True
                        return result
            except Exception:
                pass

        # If OEM ACPI does not expose thermal sensors to standard non-admin userspace:
        result["source"] = "Unexposed by OEM / Requires Admin"
        result["is_hardware_direct"] = False
        return result

    def get_cpu_metrics(self) -> Dict[str, Any]:
        """Collects complete real-time CPU telemetry."""
        total_percent = psutil.cpu_percent(interval=None)
        per_core_percent = psutil.cpu_percent(interval=None, percpu=True)
        freq_info = psutil.cpu_freq()
        
        current_freq_mhz = freq_info.current if freq_info else 0.0
        max_freq_mhz = freq_info.max if (freq_info and freq_info.max > 0) else self.base_freq_mhz

        # Temperature metrics
        temp_data = self.get_temperature_celsius()
        package_temp = temp_data["package_temp"]

        # Thermal Throttling Logic
        # Condition 1: Temp > 88°C is near or at TjMax thermal throttle threshold
        # Condition 2: Temp > 80°C and Frequency dropped severely (< 75% base clock) under high load (> 70%)
        is_throttling = False
        throttle_severity = "NONE"
        throttle_reason = "Normal operation"

        if package_temp is not None:
            if package_temp >= 92.0:
                is_throttling = True
                throttle_severity = "CRITICAL"
                throttle_reason = f"Extreme temperature ({package_temp}°C) exceeding safety junction TjMax."
            elif package_temp >= 85.0:
                if total_percent >= 65.0 and current_freq_mhz < (max_freq_mhz * 0.80):
                    is_throttling = True
                    throttle_severity = "SEVERE"
                    throttle_reason = f"Clock throttling: Frequency dipped to {current_freq_mhz:.0f} MHz while under {total_percent}% load at {package_temp}°C."
                else:
                    throttle_severity = "WARNING"
                    throttle_reason = f"High thermal envelope ({package_temp}°C) approaching throttle limit."

        # Top CPU-consuming processes
        top_processes = []
        try:
            for p in sorted(
                psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']),
                key=lambda x: x.info['cpu_percent'] or 0.0,
                reverse=True
            )[:5]:
                top_processes.append({
                    "pid": p.info['pid'],
                    "name": p.info['name'],
                    "cpu_percent": p.info['cpu_percent'],
                    "mem_percent": round(p.info['memory_percent'] or 0.0, 1)
                })
        except Exception:
            pass

        return {
            "total_percent": total_percent,
            "per_core_percent": per_core_percent,
            "physical_cores": psutil.cpu_count(logical=False) or 1,
            "logical_cores": psutil.cpu_count(logical=True) or 1,
            "current_freq_mhz": round(current_freq_mhz, 0),
            "max_freq_mhz": round(max_freq_mhz, 0),
            "temperature_data": temp_data,
            "package_temp": package_temp,
            "is_throttling": is_throttling,
            "throttle_severity": throttle_severity,
            "throttle_reason": throttle_reason,
            "top_processes": top_processes
        }
