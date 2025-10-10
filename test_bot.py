#!/usr/bin/env python3
"""Test script for the Telegram bot."""

import os
import sys

# Add project to path
sys.path.insert(0, '.')

from project.config import get_settings
from project.database import get_engine, get_session_factory, init_db
from project.utils.logging_setup import setup_logging

def test_bot():
    """Test bot configuration and database."""
    print("🧪 Testing bot configuration...")
    
    # Test settings
    settings = get_settings()
    print(f"✅ Bot token: {'Set' if settings.bot_token else 'Not set'}")
    print(f"✅ DB URL: {settings.db_url}")
    print(f"✅ Log level: {settings.log_level}")
    
    # Test database
    print("\n🗄️ Testing database...")
    try:
        engine = get_engine(settings.db_url)
        session_factory = get_session_factory(engine)
        init_db(engine)
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    # Test logging
    print("\n📝 Testing logging...")
    try:
        logger = setup_logging(settings.log_level)
        logger.info("Test log message")
        print("✅ Logging configured successfully")
    except Exception as e:
        print(f"❌ Logging error: {e}")
        return False
    
    print("\n🎉 All tests passed! Bot is ready to run.")
    print("\nTo start the bot, run:")
    print("python run_bot.py")
    print("\nOr use Makefile:")
    print("make run")
    print("\nMake sure to set your BOT_TOKEN in the .env file!")
    
    return True

if __name__ == "__main__":
    test_bot()
