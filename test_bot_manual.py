#!/usr/bin/env python3
"""Manual testing script for the bot."""

import os
import sys
import sqlite3

# Add project to path
sys.path.insert(0, '.')

from project.config import get_settings
from project.database import get_engine, get_session_factory, init_db
from project.models import User

def test_manual():
    """Manual testing instructions."""
    print("🧪 Manual Bot Testing Instructions")
    print("=" * 50)
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("Create .env file with your BOT_TOKEN:")
        print("BOT_TOKEN=your_bot_token_here")
        print("ADMIN_IDS=123456789,987654321")
        print("DB_URL=sqlite:///bot.db")
        print("LOG_LEVEL=INFO")
        print("TZ=Asia/Aqtobe")
        return
    
    # Check bot token
    settings = get_settings()
    if not settings.bot_token or settings.bot_token == "put_your_token_here":
        print("❌ BOT_TOKEN not set in .env file!")
        print("Please set your real bot token in .env file.")
        return
    
    print("✅ Configuration looks good!")
    print("\n📋 Testing Steps:")
    print("1. Start the bot: python run_bot.py")
    print("2. Send /start to your bot in Telegram")
    print("3. Check that you get 'access not granted' message")
    print("4. Check database for user creation")
    
    # Show database info
    print("\n🗄️ Database Information:")
    try:
        engine = get_engine(settings.db_url)
        session_factory = get_session_factory(engine)
        init_db(engine)
        
        with session_factory() as session:
            users = session.query(User).all()
            print(f"Total users in database: {len(users)}")
            for user in users:
                print(f"  - ID: {user.id}, Username: {user.username}, Active: {user.is_active}, Role: {user.role}")
        
        print("\n🔧 To test admin functionality:")
        print("1. Connect to database: sqlite3 bot.db")
        print("2. Update your user: UPDATE users SET is_active=1, role='admin' WHERE id=YOUR_TELEGRAM_ID;")
        print("3. Send /start again to see admin menu")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    print("\n🎯 Expected Behavior:")
    print("- First /start: User created, access denied message")
    print("- After activation: Main menu with all buttons")
    print("- Admin users: Additional 'Админка' button")
    print("- Non-admin users: No admin button")

if __name__ == "__main__":
    test_manual()
