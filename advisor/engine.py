"""
Smart Advisor Engine
Rule-based expert diagnostic system that analyzes live telemetry snapshots
and provides actionable hardware engineering and Windows OS troubleshooting guidance.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class AdvisoryCard:
    category: str
    severity: str  # "CRITICAL", "WARNING", "INFO", "OPTIMAL"
    title: str
    problem: str
    root_cause: str
    hardware_advice: str
    software_advice: str
    powershell_fix: Optional[str] = None


class SmartAdvisorEngine:
    def __init__(self):
        pass

    def evaluate(
        self,
        cpu_metrics: Dict[str, Any],
        disk_metrics: Dict[str, Any],
        mem_metrics: Dict[str, Any],
        diagnostics: Optional[Dict[str, Any]] = None
    ) -> List[AdvisoryCard]:
        """
        Executes rule engine across telemetry inputs and produces diagnostic advisory cards.
        """
        advisories: List[AdvisoryCard] = []

        # ==========================================
        # 1. CPU TEMPERATURE & THERMAL THROTTLING RULES
        # ==========================================
        package_temp = cpu_metrics.get("package_temp")
        cpu_load = cpu_metrics.get("total_percent", 0.0)
        curr_freq = cpu_metrics.get("current_freq_mhz", 0.0)
        max_freq = cpu_metrics.get("max_freq_mhz", 3200.0)
        is_throttling = cpu_metrics.get("is_throttling", False)

        if package_temp is not None:
            if package_temp >= 90.0 or is_throttling:
                advisories.append(AdvisoryCard(
                    category="CPU Thermals",
                    severity="CRITICAL",
                    title="Severe Thermal Throttling Detected",
                    problem=f"CPU Package temperature is reaching {package_temp}°C. Clock frequency drops under load ({curr_freq} MHz vs {max_freq} MHz rated).",
                    root_cause="Degraded thermal paste (pump-out effect), improper heatsink mounting pressure, clogged radiator fins, or dead AIO liquid pump.",
                    hardware_advice=(
                        "1. Re-paste the CPU IHS with high-performance thermal paste (e.g., Thermal Grizzly Kryonaut, Arctic MX-6) or PTM7950 phase-change pad.\n"
                        "2. Inspect AIO cooler: touch both tubes to check for fluid flow and listen for pump cavitation or air bubbles.\n"
                        "3. Verify cooler mounting torque in cross-pattern to prevent uneven contact.\n"
                        "4. Blow compressed air through heatsink fins and mesh dust filters."
                    ),
                    software_advice=(
                        "1. Set fan curve in BIOS or FanControl app to 100% PWM at 80°C.\n"
                        "2. Check Windows Power Plan: ensure 'Minimum processor state' is not stuck at 100%.\n"
                        "3. Apply a -0.050V to -0.080V negative voltage offset (Undervolt) via BIOS / Intel XTU / AMD PBO Curve Optimizer."
                    ),
                    powershell_fix="powercfg /setactive scheme_balanced"
                ))
            elif package_temp >= 82.0:
                advisories.append(AdvisoryCard(
                    category="CPU Thermals",
                    severity="WARNING",
                    title="Elevated CPU Temperatures Under Sustained Load",
                    problem=f"CPU temperature reached {package_temp}°C. Approaching thermal threshold.",
                    root_cause="Sub-optimal case airflow, restrictive front panel, or aggressive motherboard multi-core enhancement (MCE).",
                    hardware_advice=(
                        "1. Check case fan configuration (ensure positive or balanced static pressure: intake > exhaust).\n"
                        "2. Reposition radiator to top or front with fans in push configuration."
                    ),
                    software_advice=(
                        "1. Disable 'Asus MultiCore Enhancement' or 'Enhanced Turbo' in BIOS to stick to Intel/AMD spec wattage limits (PL1/PL2).\n"
                        "2. Clean background bloatware consuming background CPU cycles."
                    ),
                    powershell_fix=None
                ))
            else:
                advisories.append(AdvisoryCard(
                    category="CPU Thermals",
                    severity="OPTIMAL",
                    title="CPU Thermal Envelope Operating Within Safe Spec",
                    problem="None detected.",
                    root_cause=f"Current temperature is {package_temp}°C with normal cooling performance.",
                    hardware_advice="Maintain periodic dust cleaning schedule every 3-6 months.",
                    software_advice="Keep chipset drivers up-to-date.",
                    powershell_fix=None
                ))
        else:
            # Temperature sensor requires admin/LHM
            advisories.append(AdvisoryCard(
                category="CPU Thermals",
                severity="INFO",
                title="Direct Hardware Thermal Sensors Restricted",
                problem="Windows ACPI OEM table does not expose temperature to standard unprivileged user-space.",
                root_cause="Modern laptop/OEM motherboards restrict raw temperature registers unless running with elevated ring-0 driver access.",
                hardware_advice="To view live hardware sensors directly, launch LibreHardwareMonitor or run this dashboard as Administrator.",
                software_advice="Open LibreHardwareMonitor and enable 'Options' -> 'Remote Web Server' or WMI publishing.",
                powershell_fix="Start-Process powershell -Verb RunAs"
            ))

        # ==========================================
        # 2. DISK I/O & DOWNLOADS DIRECTORY LAG RULES
        # ==========================================
        disk_queue = disk_metrics.get("queue_length", 0.0)
        active_time = disk_metrics.get("active_time_percent", 0.0)
        total_throughput = disk_metrics.get("total_throughput_mb_s", 0.0)

        # Evaluate folder-specific diagnostics if provided
        if diagnostics and diagnostics.get("exists", False):
            scan_ms = diagnostics.get("scan_latency_ms", 0.0)
            file_count = diagnostics.get("total_files", 0)
            folder_type = diagnostics.get("folder_template", "")
            thumb_cache = diagnostics.get("thumbnail_cache_size_mb", 0.0)
            incomplete = diagnostics.get("incomplete_downloads", 0)
            executables = diagnostics.get("executables_count", 0)

            if scan_ms > 300.0 or "Media" in folder_type or file_count > 600 or thumb_cache > 300.0:
                reasons = []
                if "Media" in folder_type:
                    reasons.append("Windows Explorer is forcing picture/video thumbnail parsing on non-media files.")
                if file_count > 600:
                    reasons.append(f"{file_count} loose files in directory root causing MFT index traversal lag.")
                if thumb_cache > 300.0:
                    reasons.append(f"Corrupt or bloated Windows Thumbnail cache ({thumb_cache} MB).")
                if incomplete > 0:
                    reasons.append(f"{incomplete} stuck unfinished browser downloads (.crdownload/.tmp).")
                if executables > 40:
                    reasons.append(f"{executables} executables being actively inspected by Windows Defender on enumeration.")

                advisories.append(AdvisoryCard(
                    category="Downloads Lag & Disk",
                    severity="CRITICAL",
                    title="Windows Explorer Downloads Folder Latency Bottleneck Identified",
                    problem=f"Opening Downloads takes ~{scan_ms}ms (Normal: <50ms). Disk Queue: {disk_queue:.1f}, Active: {active_time:.1f}%.",
                    root_cause="; ".join(reasons) if reasons else "File lock contention and Explorer view template mismatch.",
                    hardware_advice=(
                        "1. Verify NVMe SSD health using CrystalDiskInfo (check for Media Errors, 0E Spare Capacity, or overheating above 70°C).\n"
                        "2. Ensure SSD has at least 15-20% free space for SLC cache allocation and wear leveling.\n"
                        "3. If Downloads is located on a mechanical HDD, consider moving it to an NVMe/SATA SSD."
                    ),
                    software_advice=(
                        "1. Fix Folder Optimization: Right-click 'Downloads' -> Properties -> Customize tab -> Set 'Optimize this folder for: General Items' and check 'Also apply this template to all subfolders'.\n"
                        "2. Clear Corrupted Thumbnail Cache: Delete thumbcache files using the PowerShell snippet below.\n"
                        "3. Exclude Downloads from aggressive real-time Defender archive scanning or remove leftover .crdownload files.\n"
                        "4. Rebuild Windows Search Index."
                    ),
                    powershell_fix=(
                        "# 1. Reset folder template to General Items\n"
                        "$ini = \"$HOME\\Downloads\\desktop.ini\"; if (Test-Path $ini) { attrib -h -s $ini; Remove-Item $ini -Force }\n"
                        "# 2. Purge thumbnail cache and restart Explorer\n"
                        "taskkill /f /im explorer.exe; Get-ChildItem -Path \"$env:LOCALAPPDATA\\Microsoft\\Windows\\Explorer\" -Filter thumbcache_*.db | Remove-Item -Force; start explorer.exe"
                    )
                ))
            elif disk_queue >= 2.0 or active_time >= 85.0:
                advisories.append(AdvisoryCard(
                    category="Downloads Lag & Disk",
                    severity="WARNING",
                    title="High Storage Subsystem Contention",
                    problem=f"Disk active time is {active_time:.1f}% with queue length {disk_queue:.2f}.",
                    root_cause="Background Windows Update, Superfetch/SysMain indexing, or intensive background read/writes.",
                    hardware_advice="Check if NVMe drive is running in Gen 3/4/5 mode via CrystalDiskInfo and check drive temperature.",
                    software_advice="Open Resource Monitor (resmon.exe) -> Disk tab to identify processes with highest Total (B/sec).",
                    powershell_fix="Get-Process | Sort-Object -Property CPU -Descending | Select-Object -First 10"
                ))
            else:
                advisories.append(AdvisoryCard(
                    category="Downloads Lag & Disk",
                    severity="OPTIMAL",
                    title="Disk I/O & Downloads Folder Metrics Healthy",
                    problem="None detected.",
                    root_cause=f"Folder scan latency: {scan_ms}ms, Disk queue: {disk_queue:.2f}.",
                    hardware_advice="Drive throughput and latency are within nominal boundaries.",
                    software_advice="Keep Downloads organized into monthly sub-folders to prevent MFT fragmentation.",
                    powershell_fix=None
                ))

        # ==========================================
        # 3. RAM & PAGEFILE SATURATION RULES
        # ==========================================
        ram_percent = mem_metrics.get("ram_percent", 0.0)
        swap_percent = mem_metrics.get("swap_percent", 0.0)
        used_ram = mem_metrics.get("used_ram_gb", 0.0)
        total_ram = mem_metrics.get("total_ram_gb", 0.0)

        if ram_percent >= 88.0:
            advisories.append(AdvisoryCard(
                category="Memory & System",
                severity="WARNING" if ram_percent < 95.0 else "CRITICAL",
                title="RAM Exhaustion & Pagefile Thrashing Risk",
                problem=f"RAM allocation is at {ram_percent}% ({used_ram} GB / {total_ram} GB). Pagefile usage: {swap_percent}%.",
                root_cause="Memory leaks or too many concurrent memory-intensive tasks (browser tabs, Docker, IDEs, VMs).",
                hardware_advice="Consider upgrading to 32GB or 64GB DDR4/DDR5 kit in dual-channel configuration.",
                software_advice="Close high-footprint background processes and ensure Windows Pagefile is on your fastest NVMe drive.",
                powershell_fix="Get-Process | Sort-Object -Property WorkingSet64 -Descending | Select-Object -First 5 -Property Name, @{Name='RAM (MB)';Expression={[math]::Round($_.WorkingSet64 / 1MB, 1)}}"
            ))

        return advisories
