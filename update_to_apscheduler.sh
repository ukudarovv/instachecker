#!/bin/bash

# Script to update bot to APScheduler-based auto-checker

echo "🔄 Updating to APScheduler-based auto-checker..."
echo ""

# Stop bot if running
echo "⏹️  Stopping bot..."
pkill -f "python.*run_bot.py" 2>/dev/null || echo "Bot not running"
sleep 2

# Navigate to project directory
cd "$(dirname "$0")" || exit 1

# Activate virtual environment
echo "🔧 Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "❌ Virtual environment not found!"
    exit 1
fi

# Update dependencies
echo "📦 Installing new dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if APScheduler installed
echo "✅ Checking APScheduler..."
python3 -c "import apscheduler; print(f'APScheduler version: {apscheduler.__version__}')" || {
    echo "❌ Failed to install APScheduler!"
    exit 1
}

# Check if aiohttp installed
echo "✅ Checking aiohttp..."
python3 -c "import aiohttp; print(f'aiohttp version: {aiohttp.__version__}')" || {
    echo "❌ Failed to install aiohttp!"
    exit 1
}

echo ""
echo "✅ Dependencies updated successfully!"
echo ""
echo "🚀 Starting bot with APScheduler..."
echo ""

# Start bot
python3 run_bot.py

