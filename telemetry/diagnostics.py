"""
Diagnostics Module: Downloads Directory Profiler & Windows Explorer Lag Inspector
Deeply inspects the Downloads directory and Windows subsystem to diagnose
severe folder loading delays, shell hangs, and I/O bottlenecks.
"""

import os
import time
from pathlib import Path
from typing import Dict, Any, List


class DownloadsDiagnostic:
    def __init__(self, custom_path: str = None):
        if custom_path and os.path.exists(custom_path):
            self.downloads_path = Path(custom_path)
        else:
            self.downloads_path = Path.home() / "Downloads"

    def run_benchmark_and_audit(self) -> Dict[str, Any]:
        """
        Performs a full diagnostic on the Downloads directory:
        1. Traversal Latency (ms)
        2. File count and category distribution (.exe, .zip, .crdownload, media)
        3. Thumbnail cache audit
        4. Folder template verification (desktop.ini)
        5. File I/O read latency probe
        """
        results = {
            "path": str(self.downloads_path),
            "exists": self.downloads_path.exists(),
            "scan_latency_ms": 0.0,
            "read_latency_ms": 0.0,
            "total_files": 0,
            "total_folders": 0,
            "total_size_mb": 0.0,
            "incomplete_downloads": 0,
            "executables_count": 0,
            "archives_count": 0,
            "media_count": 0,
            "thumbnail_cache_size_mb": 0.0,
            "desktop_ini_found": False,
            "folder_template": "Default / Automatic",
            "is_severe_lag": False,
            "primary_culprit": "None",
            "findings": []
        }

        if not results["exists"]:
            results["findings"].append("Downloads directory path was not found.")
            return results

        # 1. Directory Traversal Latency Test
        start_scan = time.perf_counter()
        total_size = 0
        total_files = 0
        total_folders = 0
        incomplete = 0
        executables = 0
        archives = 0
        media = 0
        sample_file_path = None

        try:
            with os.scandir(self.downloads_path) as it:
                for entry in it:
                    try:
                        if entry.is_file(follow_symlinks=False):
                            total_files += 1
                            stat = entry.stat()
                            total_size += stat.st_size
                            ext = Path(entry.name).suffix.lower()

                            if not sample_file_path and stat.st_size > 1024:
                                sample_file_path = entry.path

                            if ext in [".crdownload", ".part", ".tmp", ".downloading"]:
                                incomplete += 1
                            elif ext in [".exe", ".msi", ".bat", ".cmd", ".ps1"]:
                                executables += 1
                            elif ext in [".zip", ".rar", ".7z", ".tar", ".gz", ".iso"]:
                                archives += 1
                            elif ext in [".mp4", ".mkv", ".avi", ".mov", ".jpg", ".jpeg", ".png", ".webp", ".gif"]:
                                media += 1
                        elif entry.is_dir(follow_symlinks=False):
                            total_folders += 1
                    except (PermissionError, FileNotFoundError):
                        continue
        except Exception as e:
            results["findings"].append(f"Directory scan error: {str(e)}")

        end_scan = time.perf_counter()
        scan_latency_ms = round((end_scan - start_scan) * 1000.0, 2)

        results["scan_latency_ms"] = scan_latency_ms
        results["total_files"] = total_files
        results["total_folders"] = total_folders
        results["total_size_mb"] = round(total_size / (1024 * 1024), 2)
        results["incomplete_downloads"] = incomplete
        results["executables_count"] = executables
        results["archives_count"] = archives
        results["media_count"] = media

        # 2. File I/O Read Latency Probe (4KB random read)
        if sample_file_path and os.path.exists(sample_file_path):
            try:
                start_read = time.perf_counter()
                with open(sample_file_path, "rb") as f:
                    _ = f.read(4096)
                end_read = time.perf_counter()
                results["read_latency_ms"] = round((end_read - start_read) * 1000.0, 2)
            except Exception:
                pass

        # 3. Check desktop.ini Folder Optimization Template
        desktop_ini = self.downloads_path / "desktop.ini"
        if desktop_ini.exists():
            results["desktop_ini_found"] = True
            try:
                content = desktop_ini.read_text(errors="ignore")
                if "FolderType=Pictures" in content or "FolderType=Videos" in content or "FolderType=Music" in content:
                    results["folder_template"] = "Media (Forced Thumbnail Generation!)"
                elif "FolderType=Generic" in content:
                    results["folder_template"] = "Generic / General Items (Optimal)"
                else:
                    results["folder_template"] = "Custom / Unspecified"
            except Exception:
                pass

        # 4. Check Windows Thumbnail Cache Size
        thumb_cache_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "Explorer"
        thumb_cache_size = 0
        if thumb_cache_dir.exists():
            try:
                for f in thumb_cache_dir.glob("thumbcache_*.db"):
                    try:
                        thumb_cache_size += f.stat().st_size
                    except Exception:
                        pass
                results["thumbnail_cache_size_mb"] = round(thumb_cache_size / (1024 * 1024), 2)
            except Exception:
                pass

        # 5. Culprit Evaluation
        culprits = []
        if scan_latency_ms > 350.0:
            results["is_severe_lag"] = True
            culprits.append("Directory traversal latency exceeds normal threshold (>350ms)")

        if total_files > 800:
            results["is_severe_lag"] = True
            culprits.append(f"High file clutter: {total_files} loose items in root directory")

        if "Media" in results["folder_template"]:
            results["is_severe_lag"] = True
            culprits.append("Folder template misconfigured as Media (triggers heavy thumbnail generation)")

        if results["thumbnail_cache_size_mb"] > 250.0:
            culprits.append(f"Bloated Windows thumbnail database ({results['thumbnail_cache_size_mb']} MB)")

        if incomplete > 0:
            culprits.append(f"Found {incomplete} stuck/incomplete downloads (.crdownload / .tmp) locking file handles")

        if executables > 50:
            culprits.append(f"Heavy executable density ({executables} binaries) triggering real-time Antivirus/SmartScreen inspections")

        results["findings"] = culprits
        if culprits:
            results["primary_culprit"] = culprits[0]

        return results
