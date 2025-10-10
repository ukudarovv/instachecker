#!/usr/bin/env python3
"""Manual FSM testing instructions."""

import os
import sys

# Add project to path
sys.path.insert(0, '.')

from project.config import get_settings

def test_fsm_manual():
    """Manual FSM testing instructions."""
    print("🔄 Manual FSM Testing Instructions")
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
    print("\n📋 FSM Testing Steps:")
    print("1. Start the bot: python run_bot.py")
    print("2. Send /start to your bot in Telegram")
    print("3. Click 'Добавить аккаунт' button")
    print("4. Follow the FSM flow:")
    print("   - Step 1: Enter Instagram username (e.g., 'testuser' or '@testuser')")
    print("   - Step 2: Enter number of days (e.g., '10')")
    print("   - Success: You'll see account details")
    
    print("\n🧪 Test Cases:")
    print("✅ Valid usernames: testuser, @testuser, test.user, test_user, test123")
    print("❌ Invalid usernames: 'test user', 'test@user', '', 'a'*31, 'test-user'")
    print("✅ Valid days: 1, 7, 30, 365")
    print("❌ Invalid days: 0, -1, 'abc', ''")
    
    print("\n🔄 FSM Flow:")
    print("1. Click 'Добавить аккаунт' → FSM starts")
    print("2. Enter username → Validation → Next step")
    print("3. Enter days → Validation → Account created")
    print("4. Success message with account details")
    print("5. Return to main menu")
    
    print("\n❌ Cancel Flow:")
    print("1. Click 'Отмена' at any step → FSM cancelled")
    print("2. Return to main menu")
    
    print("\n🔄 Error Handling:")
    print("- Invalid username → Stay on step 1, try again")
    print("- Invalid days → Stay on step 2, try again")
    print("- Duplicate account → Error message, return to menu")
    print("- Inactive user → Access denied")
    
    print("\n🎯 Expected Results:")
    print("- FSM starts when clicking 'Добавить аккаунт'")
    print("- Username validation works correctly")
    print("- Days validation works correctly")
    print("- Account created with correct dates")
    print("- Success message shows account details")
    print("- Cancel button works at any step")
    print("- Duplicate detection works")
    
    print("\n🚀 Ready to test!")
    print("Run: python run_bot.py")

if __name__ == "__main__":
    test_fsm_manual()
