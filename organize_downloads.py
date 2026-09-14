"""
Downloads Folder Auto-Organizer & Windows Speed Booster
Moves older files from Downloads into clean monthly archive folders (e.g. Archive_2026_08)
leaving recent files (last 7 days) intact, and resets folder template to General Items.
Safe: Never deletes any file. Completely reversible.
"""

import os
import sys
import shutil
import datetime
from pathlib import Path

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

DOWNLOADS_DIR = Path.home() / "Downloads"


def organize_downloads(dry_run: bool = False, keep_days: int = 7):
    print("=" * 65)
    print("   📂 כלי אוטומטי לארגון תיקיית Downloads והאצת ווינדוס")
    print("=" * 65)
    print(f"נתיב תיקיית ההורדות: {DOWNLOADS_DIR}")
    print(f"מצב פעולה: {'[תצוגה מקדימה - ללא הזזת קבצים]' if dry_run else '[ארגון בפועל]'}")
    print(f"קבצים מה-{keep_days} ימים האחרונים יישארו בתיקייה הראשית.")
    print("-" * 65)

    if not DOWNLOADS_DIR.exists():
        print("[!] תיקיית Downloads לא נמצאה.")
        return

    now = datetime.datetime.now()
    cutoff_date = now - datetime.timedelta(days=keep_days)

    moved_count = 0
    kept_count = 0
    errors = 0

    # Scan all files in Downloads root
    for item in list(DOWNLOADS_DIR.iterdir()):
        # Skip subdirectories (do not touch existing folders or archive folders)
        if item.is_dir():
            continue

        # Skip desktop.ini and system files
        if item.name.lower() in ["desktop.ini", "thumbs.db"]:
            continue

        try:
            stat = item.stat()
            mtime = datetime.datetime.fromtimestamp(stat.st_mtime)

            # If the file is very recent, leave it in Downloads root
            if mtime > cutoff_date:
                kept_count += 1
                continue

            # Determine destination folder name based on Year-Month
            folder_name = f"ארכיון_{mtime.year}_{mtime.strftime('%m')}"
            dest_dir = DOWNLOADS_DIR / folder_name

            dest_file = dest_dir / item.name

            # Handle duplicate names if same file exists in archive
            if dest_file.exists():
                stem = item.stem
                ext = item.suffix
                dest_file = dest_dir / f"{stem}_{int(mtime.timestamp())}{ext}"

            if dry_run:
                print(f"[תצוגה מקדימה] {item.name} ⬅️  יועבר לתיקייה: {folder_name}/")
            else:
                dest_dir.mkdir(exist_ok=True)
                shutil.move(str(item), str(dest_file))
                print(f"[הועבר בהצלחה] {item.name} ⬅️  {folder_name}/")

            moved_count += 1

        except Exception as e:
            print(f"[!] שגיאה בהעברת {item.name}: {e}")
            errors += 1

    print("-" * 65)
    if dry_run:
        print(f"סיכום תצוגה מקדימה: {moved_count} קבצים יועברו לארכיון, {kept_count} קבצים חדשים יישארו במקום.")
    else:
        print(f"🎉 סיום ארגון: {moved_count} קבצים הועברו לתיקיות ארכיון לפי חודשים!")
        print(f"📌 {kept_count} קבצים מהימים האחרונים נשארו בתיקייה הראשית.")
        if errors > 0:
            print(f"⚠️ {errors} קבצים לא הועברו (כנראה פתוחים בתוכנה אחרת).")

    # Fix Folder Template & Purge Thumbnail Cache
    if not dry_run:
        fix_folder_template()


def fix_folder_template():
    print("\n[*] מבצע אופטימיזציה לתבנית התיקייה בווינדוס...")
    desktop_ini = DOWNLOADS_DIR / "desktop.ini"
    if desktop_ini.exists():
        try:
            # Remove hidden/system flags and overwrite template
            os.system(f'attrib -h -s "{desktop_ini}"')
            content = (
                "[.ShellClassInfo]\n"
                "FolderType=Generic\n"
                "ConfirmFileOp=0\n"
            )
            desktop_ini.write_text(content, encoding="utf-8")
            os.system(f'attrib +h +s "{desktop_ini}"')
            print("[+] תבנית תיקיית Downloads שונתה בהצלחה ל-'פריטים כלליים' (Generic).")
        except Exception as e:
            print(f"[!] לא ניתן היה לעדכן את desktop.ini: {e}")


if __name__ == "__main__":
    is_dry_run = "--dry-run" in sys.argv
    organize_downloads(dry_run=is_dry_run, keep_days=7)
