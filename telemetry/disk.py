"""
Disk Telemetry Module
Measures real-time Disk I/O throughput (Read/Write MB/s), IOPS,
Active Time percentage, and Queue Length across physical drives.
"""

import time
from typing import Dict, List, Any, Optional
import psutil

try:
    import wmi
    import pythoncom
    HAS_WMI = True
except ImportError:
    HAS_WMI = False


class DiskTelemetry:
    def __init__(self):
        self._last_poll_time = time.time()
        self._last_counters = psutil.disk_io_counters()

    def get_disk_metrics(self) -> Dict[str, Any]:
        """
        Calculates I/O throughput rates and queries queue length and partition capacities.
        """
        current_time = time.time()
        dt = max(current_time - self._last_poll_time, 0.001)
        current_counters = psutil.disk_io_counters()

        read_mb_s = 0.0
        write_mb_s = 0.0
        read_iops = 0.0
        write_iops = 0.0
        busy_time_ms = 0.0

        if self._last_counters and current_counters:
            read_bytes_delta = current_counters.read_bytes - self._last_counters.read_bytes
            write_bytes_delta = current_counters.write_bytes - self._last_counters.write_bytes
            read_count_delta = current_counters.read_count - self._last_counters.read_count
            write_count_delta = current_counters.write_count - self._last_counters.write_count

            read_mb_s = round((read_bytes_delta / (1024 * 1024)) / dt, 2)
            write_mb_s = round((write_bytes_delta / (1024 * 1024)) / dt, 2)
            read_iops = round(read_count_delta / dt, 1)
            write_iops = round(write_count_delta / dt, 1)

            if hasattr(current_counters, 'busy_time') and hasattr(self._last_counters, 'busy_time'):
                busy_time_ms = current_counters.busy_time - self._last_counters.busy_time

        self._last_counters = current_counters
        self._last_poll_time = current_time

        # Active time & Queue length via WMI PerfDisk
        queue_length = 0.0
        active_time_percent = 0.0
        wmi_status = "Fallback"

        if HAS_WMI:
            try:
                pythoncom.CoInitialize()
                w = wmi.WMI()
                # Query _Total physical disk performance
                disks = w.Win32_PerfFormattedData_PerfDisk_PhysicalDisk(Name="_Total")
                if disks:
                    d = disks[0]
                    queue_length = float(getattr(d, "CurrentQueueLength", 0.0))
                    active_time_percent = min(float(getattr(d, "PercentDiskTime", 0.0)), 100.0)
                    wmi_status = "Direct WMI PerfDisk"
            except Exception:
                pass
            finally:
                try:
                    pythoncom.CoUninitialize()
                except Exception:
                    pass

        # Fallback estimation of active time if WMI unavailable
        if wmi_status == "Fallback" and busy_time_ms > 0:
            active_time_percent = min(round((busy_time_ms / (dt * 1000.0)) * 100.0, 1), 100.0)
            queue_length = round(active_time_percent / 50.0, 2)

        # Drive partitions info
        partitions_data = []
        for p in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(p.mountpoint)
                partitions_data.append({
                    "device": p.device,
                    "mountpoint": p.mountpoint,
                    "fstype": p.fstype,
                    "total_gb": round(usage.total / (1024 ** 3), 1),
                    "used_gb": round(usage.used / (1024 ** 3), 1),
                    "free_gb": round(usage.free / (1024 ** 3), 1),
                    "percent": usage.percent
                })
            except (PermissionError, FileNotFoundError):
                continue

        # Bottleneck detection
        is_bottleneck = active_time_percent >= 90.0 or queue_length >= 2.0

        return {
            "read_mb_s": read_mb_s,
            "write_mb_s": write_mb_s,
            "total_throughput_mb_s": round(read_mb_s + write_mb_s, 2),
            "read_iops": read_iops,
            "write_iops": write_iops,
            "queue_length": queue_length,
            "active_time_percent": active_time_percent,
            "wmi_status": wmi_status,
            "partitions": partitions_data,
            "is_bottleneck": is_bottleneck
        }
