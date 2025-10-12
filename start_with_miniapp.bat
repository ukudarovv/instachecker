@echo off
REM Start bot with Mini App (Windows)

echo ====================================
echo 🚀 Starting InstaChecker with Mini App
echo ====================================
echo.

echo 📝 Инструкция:
echo 1. Установите ngrok: https://ngrok.com/download
echo 2. Запустите ngrok в отдельном терминале: ngrok http 8001
echo 3. Скопируйте HTTPS URL из ngrok
echo 4. Добавьте в env файл: IG_MINI_APP_URL=https://xxxx.ngrok-free.app
echo 5. Перезапустите этот скрипт
echo.

REM Check if ngrok URL is set
findstr /C:"IG_MINI_APP_URL=http" env >nul
if %errorlevel% neq 0 (
    echo ⚠️  IG_MINI_APP_URL не настроен в файле env
    echo.
    echo Выполните шаги выше и перезапустите
    pause
    exit /b 1
)

echo ✅ IG_MINI_APP_URL настроен
echo.

REM Start Django Mini App in background
echo 📱 Starting Django Mini App server...
start "Mini App Server" cmd /k "cd miniapp && python manage.py runserver 0.0.0.0:8001"

REM Wait for server to start
timeout /t 3 /nobreak >nul

echo.
echo ✅ Mini App server started on http://localhost:8001
echo 📡 Убедитесь, что ngrok запущен!
echo.

REM Start main bot
echo 🤖 Starting Telegram bot...
python run_bot.py

pause

