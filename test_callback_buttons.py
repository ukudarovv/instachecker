"""Test callback button handling."""

import asyncio
import sys
import os
from datetime import date, timedelta

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from project.config import get_settings
from project.database import get_session_factory, get_engine
from project.models import User, Account
from project.bot import TelegramBot
from project.utils.async_bot_wrapper import AsyncBotWrapper


async def test_callback_handling():
    """Test callback button handling."""
    settings = get_settings()
    engine = get_engine(settings.db_url)
    SessionLocal = get_session_factory(engine)
    
    # Create bot instance
    bot = TelegramBot(settings.bot_token)
    
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
        
        # Get an expired account
        expired_account = session.query(Account).filter(
            Account.user_id == admin.id,
            Account.done == False,
            Account.to_date < date.today()
        ).first()
        
        if not expired_account:
            print("[TEST] No expired accounts found for admin.")
            return
        
        print(f"[TEST] Found expired account: @{expired_account.account}")
        
        # Test callback data
        callback_data = f"expiry_expired:{expired_account.id}"
        print(f"[TEST] Testing callback: {callback_data}")
        
        # Simulate callback query
        callback_query = {
            "id": "test_callback_123",
            "from": {
                "id": admin.id,
                "username": admin.username
            },
            "message": {
                "message_id": 12345,
                "chat": {
                    "id": admin.id
                }
            },
            "data": callback_data
        }
        
        print("[TEST] Simulating callback query...")
        
        try:
            # Process callback query
            await bot.process_callback_query(callback_query, SessionLocal)
            print("[TEST] ✅ Callback processed successfully!")
        except Exception as e:
            print(f"[TEST] ❌ Error processing callback: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("=" * 70)
    print("ТЕСТ ОБРАБОТКИ CALLBACK КНОПОК")
    print("=" * 70)
    print()
    
    asyncio.run(test_callback_handling())
