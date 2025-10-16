"""Test expiry notification with buttons."""

import asyncio
import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from project.config import get_settings
from project.database import get_session_factory, get_engine
from project.services.expiry_notifications import check_and_send_expiry_notifications
from project.utils.async_bot_wrapper import AsyncBotWrapper


async def test_notifications():
    """Test sending expiry notifications."""
    settings = get_settings()
    engine = get_engine(settings.db_url)
    SessionLocal = get_session_factory(engine)
    
    # Create async bot wrapper
    bot = AsyncBotWrapper(settings.bot_token)
    
    print("[TEST] Checking and sending expiry notifications...")
    print("[TEST] This will send notifications for accounts expiring in next 7 days\n")
    
    try:
        await check_and_send_expiry_notifications(SessionLocal, bot)
        print("\n[TEST] ✅ Notifications sent successfully!")
        print("[TEST] Check your Telegram for messages with buttons")
    except Exception as e:
        print(f"\n[TEST] ❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60)
    print("ТЕСТ УВЕДОМЛЕНИЙ О СКОРОМ ИСТЕЧЕНИИ СРОКА")
    print("=" * 60)
    print()
    
    asyncio.run(test_notifications())

