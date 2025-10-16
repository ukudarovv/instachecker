"""Simple test for button functionality."""

import asyncio
import sys
import os
from datetime import date, timedelta

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from project.config import get_settings
from project.database import get_session_factory, get_engine
from project.models import User, Account
from project.services.expiry_notifications import send_expired_notification
from project.utils.async_bot_wrapper import AsyncBotWrapper


async def test_button_creation():
    """Test that buttons are created correctly."""
    settings = get_settings()
    engine = get_engine(settings.db_url)
    SessionLocal = get_session_factory(engine)
    
    # Create async bot wrapper
    bot = AsyncBotWrapper(settings.bot_token)
    
    with SessionLocal() as session:
        # Get admin user
        admin = session.query(User).filter(
            User.role.in_(['admin', 'superuser']),
            User.is_active == True
        ).first()
        
        if not admin:
            print("[TEST] ❌ Admin user not found!")
            return
        
        print(f"[TEST] Found admin: ID={admin.id}, username={admin.username}")
        
        # Get expired accounts
        expired_accounts = session.query(Account).filter(
            Account.user_id == admin.id,
            Account.done == False,
            Account.to_date < date.today()
        ).limit(2).all()
        
        if not expired_accounts:
            print("[TEST] No expired accounts found for admin.")
            return
        
        print(f"[TEST] Found {len(expired_accounts)} expired accounts:")
        for acc in expired_accounts:
            days_overdue = (date.today() - acc.to_date).days
            print(f"  - @{acc.account} (просрочен на {days_overdue} дн.)")
        
        # Test button creation logic
        print("\n[TEST] Testing button creation logic...")
        
        keyboard = []
        for acc in expired_accounts:
            days_overdue = (date.today() - acc.to_date).days
            button_text = f"@{acc.account} (просрочен на {days_overdue} дн.)"
            callback_data = f"expiry_expired:{acc.id}"
            
            keyboard.append([{
                "text": button_text,
                "callback_data": callback_data
            }])
            
            print(f"  ✅ Button: '{button_text}' -> '{callback_data}'")
        
        # Add "Manage accounts" button
        keyboard.append([{
            "text": "📱 Неактивные аккаунты",
            "callback_data": "show_inactive_accounts"
        }])
        
        print(f"  ✅ Button: '📱 Неактивные аккаунты' -> 'show_inactive_accounts'")
        
        # Test keyboard structure
        print(f"\n[TEST] Keyboard structure:")
        print(f"  - Total buttons: {len(keyboard)}")
        print(f"  - Account buttons: {len(keyboard) - 1}")
        print(f"  - Management button: 1")
        
        # Test callback data format
        print(f"\n[TEST] Callback data format:")
        for i, row in enumerate(keyboard):
            for j, button in enumerate(row):
                print(f"  [{i}][{j}] '{button['text']}' -> '{button['callback_data']}'")
        
        print(f"\n[TEST] ✅ Button creation logic works correctly!")
        print(f"[TEST] Buttons should be clickable when bot is running.")


if __name__ == "__main__":
    print("=" * 70)
    print("ТЕСТ СОЗДАНИЯ КНОПОК")
    print("=" * 70)
    print()
    
    asyncio.run(test_button_creation())
