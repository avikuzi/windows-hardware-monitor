@echo off
title Hardware Dashboard - Online Remote Access
echo ========================================================
echo   Hardware Diagnostics Dashboard - Online Tunnel Mode
echo ========================================================
echo.

:: Check virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

:: Run the automated online launcher
python share_online.py

pause
