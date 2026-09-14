@echo off
chcp 65001 >nul
title Downloads Auto-Organizer & Optimizer
echo ========================================================
echo   ארגון חכם של תיקיית Downloads והאצת סייר הקבצים
echo ========================================================
echo.
echo האם ברצונך לסדר את הקבצים הישנים בתיקיות חודשיות?
echo (קבצים מהשבוע האחרון יישארו במקומם, שום קובץ לא יימחק!)
echo.
set /p choice="להמשיך? [Y/N]: "
if /i "%choice%"=="Y" (
    python organize_downloads.py
) else (
    echo בוטל על ידי המשתמש.
)
echo.
pause
