@echo off
title Hardware Diagnostics Dashboard Launcher
echo ========================================================
echo   Real-Time Hardware Diagnostics & Advisor Engine
echo ========================================================
echo.

:: Check if virtual environment exists
if not exist "venv" (
    echo [*] Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [!] Error creating virtual environment. Ensure Python 3.10+ is in your PATH.
        pause
        exit /b
    )
)

:: Activate virtual environment
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat

:: Install requirements
echo [*] Checking dependencies...
pip install -r requirements.txt --quiet

:: Launch Streamlit
echo.
echo [*] Launching Dashboard on http://localhost:8501 ...
echo [*] Press Ctrl+C in this console to stop the server.
echo.
streamlit run app.py

pause
