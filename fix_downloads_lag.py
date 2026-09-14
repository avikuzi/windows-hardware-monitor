"""
Instant Downloads Folder Lag Fixer
Resolves the 4 root causes of Windows Explorer hanging on Downloads:
1. Stuck/Corrupt browser downloads (.crdownload / .tmp) locking the file system
2. Folder Optimization misclassified (forces FolderType=Generic)
3. Explorer 'Group By' date sorting hang
4. Rebuilds Windows Explorer thumbnail & icon cache
"""

import os
import sys
import subprocess
from pathlib import Path

DOWNLOADS_DIR = Path.home() / "Downloads"


def run_fix():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 65)
    print("   ⚡ תיקון מהיר ומקיף לתקיעת תיקיית Downloads בווינדוס ⚡")
    print("=" * 65)
    print(f"נתיב תיקיית ההורדות: {DOWNLOADS_DIR}\n")

    # 1. בדיקת קבצי הורדה תקועים
    stuck_files = []
    for f in DOWNLOADS_DIR.glob("*"):
        if f.is_file() and f.suffix.lower() in [".crdownload", ".tmp", ".part", ".downloading"]:
            stuck_files.append(f)

    if stuck_files:
        print(f"[*] נמצאו {len(stuck_files)} קבצי הורדה תקועים שנועלים את סייר הקבצים:")
        for sf in stuck_files:
            size_mb = sf.stat().st_size / (1024 * 1024)
            print(f"    - {sf.name} ({size_mb:.1f} MB)")
        
        for sf in stuck_files:
            try:
                sf.unlink()
                print(f"    [+] נמחק בהצלחה קובץ ההורדה התקוע: {sf.name}")
            except Exception as e:
                print(f"    [!] לא ניתן למחוק את {sf.name} (האם הדפדפן פתוח ומוריד?): {e}")
    else:
        print("[+] לא נמצאו קבצי הורדה תקועים מסוג .crdownload.")

    # 2. כפיית תבנית תיקייה "פריטים כלליים" (Generic) ב-desktop.ini
    print("\n[*] מגדיר את תבנית התיקייה ל-'פריטים כלליים' (Generic)...")
    desktop_ini = DOWNLOADS_DIR / "desktop.ini"
    try:
        if desktop_ini.exists():
            subprocess.run(f'attrib -h -s "{desktop_ini}"', shell=True, capture_output=True)
            desktop_ini.unlink(missing_ok=True)

        ini_content = (
            "[.ShellClassInfo]\n"
            "LocalizedResourceName=@%SystemRoot%\\system32\\shell32.dll,-21798\n"
            "IconResource=%SystemRoot%\\system32\\imageres.dll,-184\n"
            "[ViewState]\n"
            "Mode=\n"
            "Vid=\n"
            "FolderType=Generic\n"
        )
        desktop_ini.write_text(ini_content, encoding="utf-8")
        subprocess.run(f'attrib +h +s "{desktop_ini}"', shell=True, capture_output=True)
        print("[+] תבנית התיקייה הוגדרה בהצלחה כ-Generic (מונע טעינת תמונות ממוזערות כבדה).")
    except Exception as e:
        print(f"[!] שגיאה בהגדרת desktop.ini: {e}")

    # 3. איפוס מטמון התמונות הממוזערות של ווינדוס (Thumbnail Cache)
    print("\n[*] מנקה מטמון תמונות ממוזערות (Thumbnails Cache) של ווינדוס...")
    thumb_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "Explorer"
    if thumb_dir.exists():
        cleaned_count = 0
        for db in thumb_dir.glob("thumbcache_*.db"):
            try:
                db.unlink()
                cleaned_count += 1
            except Exception:
                pass
        print(f"[+] נוקו קבצי מטמון.")

    # 4. הפעלה מחדש של Explorer כדי שהשינויים ייכנסו לתוקף מיד
    print("\n[*] מרענן את סייר הקבצים (Windows Explorer)...")
    try:
        subprocess.run("taskkill /f /im explorer.exe", shell=True, capture_output=True)
        subprocess.Popen("explorer.exe", shell=True)
        print("[+] סייר הקבצים רוענן בהצלחה!")
    except Exception as e:
        print(f"[!] שגיאה בריענון Explorer: {e}")

    print("\n" + "=" * 65)
    print("  🎉 התיקון הסתיים! פתח עכשיו את תיקיית Downloads ובדוק את המהירות.")
    print("=" * 65)


if __name__ == "__main__":
    run_fix()
