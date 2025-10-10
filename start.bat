@echo off
REM Bot starter script for Windows
echo ========================================
echo Instagram Checker Bot - Auto Restart
echo ========================================
echo.

REM Activate virtual environment if exists
if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Start bot with auto-restart
python start_bot.py

pause

