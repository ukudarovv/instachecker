#!/bin/bash
# Start bot with Mini App (Linux/Mac)

echo "===================================="
echo "🚀 Starting InstaChecker with Mini App"
echo "===================================="
echo ""

echo "📝 Инструкция:"
echo "1. Установите ngrok: https://ngrok.com/download"
echo "2. Запустите ngrok в отдельном терминале: ngrok http 8001"
echo "3. Скопируйте HTTPS URL из ngrok"
echo "4. Добавьте в env файл: IG_MINI_APP_URL=https://xxxx.ngrok-free.app"
echo "5. Перезапустите этот скрипт"
echo ""

# Check if ngrok URL is set
if ! grep -q "IG_MINI_APP_URL=http" env; then
    echo "⚠️  IG_MINI_APP_URL не настроен в файле env"
    echo ""
    echo "Выполните шаги выше и перезапустите"
    exit 1
fi

echo "✅ IG_MINI_APP_URL настроен"
echo ""

# Start Django Mini App in background
echo "📱 Starting Django Mini App server..."
cd miniapp
python manage.py runserver 0.0.0.0:8001 &
DJANGO_PID=$!
cd ..

# Wait for server to start
sleep 3

echo ""
echo "✅ Mini App server started on http://localhost:8001 (PID: $DJANGO_PID)"
echo "📡 Убедитесь, что ngrok запущен!"
echo ""

# Start main bot
echo "🤖 Starting Telegram bot..."
python run_bot.py

# Cleanup on exit
kill $DJANGO_PID 2>/dev/null

