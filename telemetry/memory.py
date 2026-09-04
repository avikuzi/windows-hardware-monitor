"""
Memory Telemetry Module
Tracks RAM allocation, available buffers, and pagefile/swap exhaustion.
"""

from typing import Dict, Any
import psutil


class MemoryTelemetry:
    def get_memory_metrics(self) -> Dict[str, Any]:
        """Collects RAM and swap (Pagefile) metrics."""
        vm = psutil.virtual_memory()
        swap = psutil.swap_memory()

        total_ram_gb = round(vm.total / (1024 ** 3), 2)
        used_ram_gb = round(vm.used / (1024 ** 3), 2)
        available_ram_gb = round(vm.available / (1024 ** 3), 2)
        ram_percent = vm.percent

        total_swap_gb = round(swap.total / (1024 ** 3), 2)
        used_swap_gb = round(swap.used / (1024 ** 3), 2)
        swap_percent = swap.percent

        is_under_pressure = ram_percent > 88.0 or (swap_percent > 75.0 and ram_percent > 80.0)

        return {
            "total_ram_gb": total_ram_gb,
            "used_ram_gb": used_ram_gb,
            "available_ram_gb": available_ram_gb,
            "ram_percent": ram_percent,
            "total_swap_gb": total_swap_gb,
            "used_swap_gb": used_swap_gb,
            "swap_percent": swap_percent,
            "is_under_pressure": is_under_pressure
        }
