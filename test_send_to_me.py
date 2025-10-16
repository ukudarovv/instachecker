"""Send test expiry notification to admin."""

import asyncio
import sys
import os
from datetime import date, timedelta

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from project.config import get_settings
from project.database import get_session_factory, get_engine
from project.models import User, Account
from project.services.expiry_notifications import send_expiring_soon_notification
from project.utils.async_bot_wrapper import AsyncBotWrapper


async def test_send_to_admin():
    """Send test notification to admin."""
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
        
        # Get some accounts expiring soon (or create test accounts)
        expiring_accounts = session.query(Account).filter(
            Account.user_id == admin.id,
            Account.done == False,
            Account.to_date >= date.today(),
            Account.to_date <= date.today() + timedelta(days=7)
        ).limit(5).all()
        
        if not expiring_accounts:
            print("[TEST] No accounts expiring soon found for admin.")
            print("[TEST] Creating test data...")
            
            # Create test account
            test_account = Account(
                user_id=admin.id,
                account="test_account_expiry",
                from_date=date.today() - timedelta(days=20),
                period=25,
                to_date=date.today() + timedelta(days=5),
                done=False
            )
            session.add(test_account)
            session.commit()
            session.refresh(test_account)
            
            expiring_accounts = [test_account]
            print(f"[TEST] Created test account: @{test_account.account}")
        
        print(f"[TEST] Found {len(expiring_accounts)} accounts:")
        for acc in expiring_accounts:
            days_left = (acc.to_date - date.today()).days
            print(f"  - @{acc.account} (осталось {days_left} дн.)")
        
        print("\n[TEST] Sending notification with BUTTONS...")
        
        try:
            await send_expiring_soon_notification(bot, admin, expiring_accounts)
            print("\n[TEST] ✅ Notification sent successfully!")
            print(f"[TEST] Check Telegram chat with user ID {admin.id}")
            print("\n[TEST] You should see:")
            print("  - Message header")
            print("  - BUTTONS for each account ← ЭТО КНОПКИ!")
            print("  - Button 'Неактивные аккаунты'")
            print("\n[TEST] Click on any account button to see account info!")
        except Exception as e:
            print(f"\n[TEST] ❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("=" * 70)
    print("ТЕСТ ОТПРАВКИ УВЕДОМЛЕНИЯ С КНОПКАМИ АДМИНУ")
    print("=" * 70)
    print()
    
    asyncio.run(test_send_to_admin())

