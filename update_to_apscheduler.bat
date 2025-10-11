@echo off
REM Script to update bot to APScheduler-based auto-checker

echo.
echo ============================================
echo   Updating to APScheduler auto-checker
echo ============================================
echo.

REM Stop bot if running
echo Stopping bot...
taskkill /f /im python.exe 2>nul
timeout /t 2 /nobreak >nul

REM Activate virtual environment
echo Activating virtual environment...
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo ERROR: Virtual environment not found!
    pause
    exit /b 1
)

REM Update dependencies
echo.
echo Installing new dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Check if APScheduler installed
echo.
echo Checking APScheduler...
python -c "import apscheduler; print(f'APScheduler version: {apscheduler.__version__}')" || (
    echo ERROR: Failed to install APScheduler!
    pause
    exit /b 1
)

REM Check if aiohttp installed
echo.
echo Checking aiohttp...
python -c "import aiohttp; print(f'aiohttp version: {aiohttp.__version__}')" || (
    echo ERROR: Failed to install aiohttp!
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Dependencies updated successfully!
echo ============================================
echo.
echo Starting bot with APScheduler...
echo.

REM Start bot
python run_bot.py

