"""Expiry notifications service."""

from typing import List
from datetime import date, timedelta
from sqlalchemy.orm import sessionmaker

try:
    from ..models import Account, User
    from ..services.accounts import get_expired_accounts, get_accounts_expiring_soon
    from ..utils.access import ensure_active
except ImportError:
    from models import Account, User
    from services.accounts import get_expired_accounts, get_accounts_expiring_soon
    from utils.access import ensure_active


async def check_and_send_expiry_notifications(SessionLocal: sessionmaker, bot=None):
    """
    Check for expired accounts and send notifications to users.
    
    Args:
        SessionLocal: SQLAlchemy session factory
        bot: Optional TelegramBot instance to send notifications
    """
    if not bot:
        print("[EXPIRY-CHECK] No bot instance provided, skipping notifications")
        return
    
    print(f"[EXPIRY-CHECK] {date.today()} - Checking for expired accounts...")
    
    with SessionLocal() as session:
        # Get expired accounts (to_date < today)
        expired_accounts = get_expired_accounts(session)
        
        # Get accounts expiring soon (in next 3 days)
        expiring_soon = get_accounts_expiring_soon(session, days_ahead=3)
        
        print(f"[EXPIRY-CHECK] Found {len(expired_accounts)} expired accounts")
        print(f"[EXPIRY-CHECK] Found {len(expiring_soon)} accounts expiring soon")
        
        # Group accounts by user
        user_expired = {}
        user_expiring = {}
        
        for acc in expired_accounts:
            if acc.user_id not in user_expired:
                user_expired[acc.user_id] = []
            user_expired[acc.user_id].append(acc)
        
        for acc in expiring_soon:
            if acc.user_id not in user_expiring:
                user_expiring[acc.user_id] = []
            user_expiring[acc.user_id].append(acc)
        
        # Send notifications for expired accounts
        for user_id, accounts in user_expired.items():
            try:
                user = session.query(User).get(user_id)
                if user and ensure_active(user):
                    await send_expired_notification(bot, user, accounts)
                    print(f"[EXPIRY-CHECK] ✅ Sent expired notification to user {user_id}")
                else:
                    print(f"[EXPIRY-CHECK] ⚠️ User {user_id} not found or inactive")
            except Exception as e:
                print(f"[EXPIRY-CHECK] ❌ Failed to send expired notification to user {user_id}: {e}")
        
        # Send notifications for accounts expiring soon
        for user_id, accounts in user_expiring.items():
            try:
                user = session.query(User).get(user_id)
                if user and ensure_active(user):
                    await send_expiring_soon_notification(bot, user, accounts)
                    print(f"[EXPIRY-CHECK] ✅ Sent expiring soon notification to user {user_id}")
                else:
                    print(f"[EXPIRY-CHECK] ⚠️ User {user_id} not found or inactive")
            except Exception as e:
                print(f"[EXPIRY-CHECK] ❌ Failed to send expiring soon notification to user {user_id}: {e}")


async def send_expired_notification(bot, user: User, accounts: List[Account]):
    """Send notification about expired accounts."""
    message_lines = [
        "⚠️ <b>ВНИМАНИЕ: Истек срок мониторинга!</b>\n",
        f"📅 Следующие аккаунты достигли конца периода мониторинга:"
    ]
    
    for acc in accounts:
        days_overdue = (date.today() - acc.to_date).days
        message_lines.append(
            f"• <a href='https://www.instagram.com/{acc.account}/'>@{acc.account}</a> "
            f"(просрочен на {days_overdue} дн.)"
        )
    
    message_lines.extend([
        "",
        "🔄 <b>Что делать:</b>",
        "1️⃣ Увеличить период мониторинга",
        "2️⃣ Удалить аккаунт из списка",
        "",
        "📱 Используйте кнопку 'Активные аккаунты' для управления"
    ])
    
    message = "\n".join(message_lines)
    
    try:
        await bot.send_message(user.id, message)
    except Exception as e:
        print(f"[EXPIRY-CHECK] Failed to send expired notification: {e}")


async def send_expiring_soon_notification(bot, user: User, accounts: List[Account]):
    """Send notification about accounts expiring soon."""
    message_lines = [
        "⏰ <b>Напоминание: скоро истечет срок мониторинга</b>\n",
        "📅 Следующие аккаунты скоро достигнут конца периода:"
    ]
    
    for acc in accounts:
        days_left = (acc.to_date - date.today()).days
        message_lines.append(
            f"• <a href='https://www.instagram.com/{acc.account}/'>@{acc.account}</a> "
            f"(осталось {days_left} дн.)"
        )
    
    message_lines.extend([
        "",
        "💡 <b>Рекомендация:</b> Увеличьте период мониторинга заранее",
        "",
        "📱 Используйте кнопку 'Активные аккаунты' для управления"
    ])
    
    message = "\n".join(message_lines)
    
    try:
        await bot.send_message(user.id, message)
    except Exception as e:
        print(f"[EXPIRY-CHECK] Failed to send expiring soon notification: {e}")


def start_expiry_checker(SessionLocal: sessionmaker, bot=None, interval_hours: int = 24):
    """
    Start periodic expiry checker.
    
    Args:
        SessionLocal: SQLAlchemy session factory
        bot: Optional TelegramBot instance
        interval_hours: Check interval in hours (default: 24 hours)
    """
    import asyncio
    import threading
    from datetime import datetime, timedelta
    
    print(f"[EXPIRY-CHECKER] Starting periodic expiry checker (every {interval_hours} hours)")
    
    async def periodic_expiry_check():
        """Periodic expiry check using asyncio timer."""
        while True:
            try:
                # Wait first, then check
                await asyncio.sleep(interval_hours * 3600)  # Convert hours to seconds
                print(f"[EXPIRY-CHECKER] Timer triggered at {datetime.now()}")
                await check_and_send_expiry_notifications(SessionLocal, bot)
                print(f"[EXPIRY-CHECKER] Timer completed at {datetime.now()}")
            except Exception as e:
                print(f"[EXPIRY-CHECKER] Error in expiry check: {e}")
    
    def run_expiry_checker():
        """Run expiry checker in separate thread with its own event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(periodic_expiry_check())
        except Exception as e:
            print(f"[EXPIRY-CHECKER] Error in expiry checker thread: {e}")
        finally:
            loop.close()
    
    # Run in separate thread to avoid event loop conflicts
    expiry_thread = threading.Thread(target=run_expiry_checker, daemon=True)
    expiry_thread.start()
    
    print(f"[EXPIRY-CHECKER] Next expiry check will be at: {datetime.now() + timedelta(hours=interval_hours)}")
