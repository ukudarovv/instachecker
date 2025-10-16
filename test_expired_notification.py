"""Test expired notification with buttons."""

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


async def test_send_expired_to_admin():
    """Send test expired notification to admin."""
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
        
        # Get some expired accounts (or create test accounts)
        expired_accounts = session.query(Account).filter(
            Account.user_id == admin.id,
            Account.done == False,
            Account.to_date < date.today()
        ).limit(3).all()
        
        if not expired_accounts:
            print("[TEST] No expired accounts found for admin.")
            print("[TEST] Creating test data...")
            
            # Create test expired accounts
            test_accounts = []
            for i in range(2):
                test_account = Account(
                    user_id=admin.id,
                    account=f"test_expired_{i+1}",
                    from_date=date.today() - timedelta(days=30),
                    period=25,
                    to_date=date.today() - timedelta(days=5 + i),  # Expired 5-6 days ago
                    done=False
                )
                session.add(test_account)
                test_accounts.append(test_account)
            
            session.commit()
            for acc in test_accounts:
                session.refresh(acc)
            
            expired_accounts = test_accounts
            print(f"[TEST] Created {len(test_accounts)} test expired accounts")
        
        print(f"[TEST] Found {len(expired_accounts)} expired accounts:")
        for acc in expired_accounts:
            days_overdue = (date.today() - acc.to_date).days
            print(f"  - @{acc.account} (просрочен на {days_overdue} дн.)")
        
        print("\n[TEST] Sending EXPIRED notification with BUTTONS...")
        
        try:
            await send_expired_notification(bot, admin, expired_accounts)
            print("\n[TEST] ✅ Expired notification sent successfully!")
            print(f"[TEST] Check Telegram chat with user ID {admin.id}")
            print("\n[TEST] You should see:")
            print("  - ⚠️ ВНИМАНИЕ: Истек срок мониторинга!")
            print("  - BUTTONS for each expired account ← ЭТО КНОПКИ!")
            print("  - Button 'Неактивные аккаунты'")
            print("\n[TEST] Click on any expired account button to see account info!")
        except Exception as e:
            print(f"\n[TEST] ❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("=" * 70)
    print("ТЕСТ ОТПРАВКИ УВЕДОМЛЕНИЯ ОБ ИСТЕКШЕМ СРОКЕ С КНОПКАМИ")
    print("=" * 70)
    print()
    
    asyncio.run(test_send_expired_to_admin())
