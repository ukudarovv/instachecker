#!/bin/bash
# Bot starter script for Linux/Mac

echo "========================================"
echo "Instagram Checker Bot - Auto Restart"
echo "========================================"
echo ""

# Activate virtual environment if exists
if [ -f ".venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Start bot with auto-restart
python3 start_bot.py

