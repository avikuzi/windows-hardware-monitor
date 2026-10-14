"""
Deep Downloads Lag Fixer & Auto-Organizer
1. Moves loose media (Photos/Videos/HEIC) into a dedicated folder
2. Moves older files to monthly archive
3. Enforces Generic folder template in desktop.ini
4. Applies permanent Windows Registry fix to disable 'Group By Date'
5. Clears corrupt thumbnail caches and restarts Explorer
"""

import os
import sys
import time
import shutil
import winreg
import subprocess
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

DOWNLOADS_DIR = Path.home() / "Downloads"


def apply_registry_fix():
    print("[*] Applying permanent registry fix (Disabling 'Group by Date' & Enforcing Generic view)...")
    try:
        # Override TopViews GroupBy in HKCU
        tv_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\FolderTypes\{885a186e-a440-4ada-812b-db871b942259}\TopViews\{00000000-0000-0000-0000-000000000000}"
        k1 = winreg.CreateKey(winreg.HKEY_CURRENT_USER, tv_path)
        winreg.SetValueEx(k1, "GroupBy", 0, winreg.REG_SZ, "")
        winreg.SetValueEx(k1, "PrimaryProperty", 0, winreg.REG_SZ, "")
        winreg.CloseKey(k1)

        # Force Downloads AllFolders template to Generic with no GroupBy
        all_path = r"Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\Bags\AllFolders\Shell\{885a186e-a440-4ada-812b-db871b942259}"
        k2 = winreg.CreateKey(winreg.HKEY_CURRENT_USER, all_path)
        winreg.SetValueEx(k2, "FolderType", 0, winreg.REG_SZ, "Generic")
        winreg.SetValueEx(k2, "GroupBy", 0, winreg.REG_SZ, "")
        winreg.SetValueEx(k2, "LogicalViewMode", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(k2)
        print("[+] Registry fix applied successfully!")
    except Exception as e:
        print(f"[!] Registry fix warning: {e}")


def organize_media_and_archives():
    print(f"[*] Scanning {DOWNLOADS_DIR}...")
    media_folder = DOWNLOADS_DIR / "תמונות וסרטונים"
    media_folder.mkdir(exist_ok=True)
    media_exts = {".jpg", ".jpeg", ".png", ".heic", ".mp4", ".mkv", ".avi", ".mov"}

    moved_media = 0
    for item in list(DOWNLOADS_DIR.iterdir()):
        if item.is_file() and item.suffix.lower() in media_exts:
            dest = media_folder / item.name
            if dest.exists():
                dest = media_folder / f"{item.stem}_{int(time.time())}{item.suffix}"
            try:
                shutil.move(str(item), str(dest))
                moved_media += 1
            except Exception as e:
                print(f"[!] Error moving {item.name}: {e}")

    print(f"[+] Moved {moved_media} loose media/video/photo files to '{media_folder.name}/'")

    # Archive older files
    archive_folder = DOWNLOADS_DIR / "ארכיון_2026_10"
    archive_folder.mkdir(exist_ok=True)
    now = time.time()
    moved_old = 0
    for item in list(DOWNLOADS_DIR.iterdir()):
        if item.is_file() and item.name.lower() not in ["desktop.ini", "thumbs.db"]:
            # If older than 3 days
            if (now - item.stat().st_mtime) > (3 * 86400):
                dest = archive_folder / item.name
                if dest.exists():
                    dest = archive_folder / f"{item.stem}_{int(time.time())}{item.suffix}"
                try:
                    shutil.move(str(item), str(dest))
                    moved_old += 1
                except Exception:
                    pass

    print(f"[+] Moved {moved_old} older files to '{archive_folder.name}/'")


def reset_desktop_ini():
    ini = DOWNLOADS_DIR / "desktop.ini"
    try:
        if ini.exists():
            subprocess.run(f'attrib -h -s "{ini}"', shell=True, capture_output=True)
        ini_content = (
            "[.ShellClassInfo]\n"
            "LocalizedResourceName=@%SystemRoot%\\system32\\shell32.dll,-21798\n"
            "IconResource=%SystemRoot%\\system32\\imageres.dll,-184\n"
            "[ViewState]\n"
            "Mode=\n"
            "Vid=\n"
            "FolderType=Generic\n"
        )
        ini.write_text(ini_content, encoding="utf-8")
        subprocess.run(f'attrib +h +s "{ini}"', shell=True, capture_output=True)
        print("[+] desktop.ini set to Generic (prevents thumbnail generation thrashing).")
    except Exception as e:
        print(f"[!] ini error: {e}")


def restart_explorer():
    print("[*] Refreshing Windows Explorer...")
    # Clear thumbnail cache
    thumb_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "Explorer"
    if thumb_dir.exists():
        for db in thumb_dir.glob("thumbcache_*.db"):
            try:
                db.unlink()
            except Exception:
                pass
    subprocess.run("taskkill /f /im explorer.exe", shell=True, capture_output=True)
    time.sleep(1)
    subprocess.Popen("explorer.exe", shell=True)
    print("[+] Windows Explorer restarted cleanly.")


def main():
    print("=" * 60)
    print("   🚀 Running Deep Downloads Lag & Freeze Fix 🚀")
    print("=" * 60)
    apply_registry_fix()
    organize_media_and_archives()
    reset_desktop_ini()
    restart_explorer()
    print("=" * 60)
    print("   🎉 COMPLETE! Downloads folder optimized for speed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
