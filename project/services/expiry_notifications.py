"""Expiry notifications service."""

from typing import List
from datetime import date, timedelta
from sqlalchemy.orm import sessionmaker

try:
    from ..models import Account, User, ExpiryNotification
    from ..services.accounts import get_expired_accounts, get_accounts_expiring_soon
    from ..utils.access import ensure_active
except ImportError:
    from models import Account, User, ExpiryNotification
    from services.accounts import get_expired_accounts, get_accounts_expiring_soon
    from utils.access import ensure_active


def was_notification_sent_today(session, user_id: int, account_id: int, notification_type: str) -> bool:
    """
    Check if notification was already sent today for this account.
    
    Args:
        session: SQLAlchemy session
        user_id: User ID
        account_id: Account ID
        notification_type: Type of notification ('expiring_soon' | 'expired')
    
    Returns:
        True if notification was sent today, False otherwise
    """
    today = date.today()
    
    existing = session.query(ExpiryNotification).filter(
        ExpiryNotification.user_id == user_id,
        ExpiryNotification.account_id == account_id,
        ExpiryNotification.notification_type == notification_type,
        ExpiryNotification.notification_date == today
    ).first()
    
    return existing is not None


def mark_notification_sent(session, user_id: int, account_id: int, notification_type: str):
    """
    Mark notification as sent for today.
    
    Args:
        session: SQLAlchemy session
        user_id: User ID
        account_id: Account ID
        notification_type: Type of notification ('expiring_soon' | 'expired')
    """
    today = date.today()
    
    # Check if already exists (shouldn't happen, but just in case)
    existing = session.query(ExpiryNotification).filter(
        ExpiryNotification.user_id == user_id,
        ExpiryNotification.account_id == account_id,
        ExpiryNotification.notification_type == notification_type,
        ExpiryNotification.notification_date == today
    ).first()
    
    if not existing:
        notification = ExpiryNotification(
            user_id=user_id,
            account_id=account_id,
            notification_type=notification_type,
            notification_date=today
        )
        session.add(notification)
        session.commit()


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
        
        # Get accounts expiring soon (in next 7 days)
        expiring_soon = get_accounts_expiring_soon(session, days_ahead=7)
        
        print(f"[EXPIRY-CHECK] Found {len(expired_accounts)} expired accounts (before filtering)")
        print(f"[EXPIRY-CHECK] Found {len(expiring_soon)} accounts expiring soon (before filtering)")
        
        # Filter out accounts that already received notification today
        expired_accounts_to_notify = []
        for acc in expired_accounts:
            if not was_notification_sent_today(session, acc.user_id, acc.id, 'expired'):
                expired_accounts_to_notify.append(acc)
            else:
                print(f"[EXPIRY-CHECK] ⏭️ Skipping expired notification for @{acc.account} - already sent today")
        
        expiring_soon_to_notify = []
        for acc in expiring_soon:
            if not was_notification_sent_today(session, acc.user_id, acc.id, 'expiring_soon'):
                expiring_soon_to_notify.append(acc)
            else:
                print(f"[EXPIRY-CHECK] ⏭️ Skipping expiring soon notification for @{acc.account} - already sent today")
        
        print(f"[EXPIRY-CHECK] {len(expired_accounts_to_notify)} expired accounts to notify")
        print(f"[EXPIRY-CHECK] {len(expiring_soon_to_notify)} expiring soon accounts to notify")
        
        # Group accounts by user
        user_expired = {}
        user_expiring = {}
        
        for acc in expired_accounts_to_notify:
            if acc.user_id not in user_expired:
                user_expired[acc.user_id] = []
            user_expired[acc.user_id].append(acc)
        
        for acc in expiring_soon_to_notify:
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
                    
                    # Mark notifications as sent for all accounts
                    for acc in accounts:
                        mark_notification_sent(session, user_id, acc.id, 'expired')
                        print(f"[EXPIRY-CHECK] 📝 Marked expired notification as sent for @{acc.account}")
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
                    
                    # Mark notifications as sent for all accounts
                    for acc in accounts:
                        mark_notification_sent(session, user_id, acc.id, 'expiring_soon')
                        print(f"[EXPIRY-CHECK] 📝 Marked expiring soon notification as sent for @{acc.account}")
                else:
                    print(f"[EXPIRY-CHECK] ⚠️ User {user_id} not found or inactive")
            except Exception as e:
                print(f"[EXPIRY-CHECK] ❌ Failed to send expiring soon notification to user {user_id}: {e}")


async def send_expired_notification(bot, user: User, accounts: List[Account]):
    """Send notification about expired accounts with interactive buttons."""
    # Original message format
    message_lines = [
        "⚠️ <b>ВНИМАНИЕ: Истек срок мониторинга!</b>\n",
        "📅 Следующие аккаунты достигли конца периода мониторинга:"
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
        "📱 Используйте кнопку 'Неактивные аккаунты' для управления"
    ])
    
    message = "\n".join(message_lines)
    
    # Create inline keyboard with buttons for each account
    keyboard = []
    for acc in accounts:
        days_overdue = (date.today() - acc.to_date).days
        button_text = f"@{acc.account} (просрочен на {days_overdue} дн.)"
        keyboard.append([{
            "text": button_text,
            "callback_data": f"expiry_expired:{acc.id}"
        }])
    
    # Add "Manage accounts" button
    keyboard.append([{
        "text": "📱 Неактивные аккаунты",
        "callback_data": "show_inactive_accounts"
    }])
    
    reply_markup = {"inline_keyboard": keyboard}
    
    try:
        # Send message with inline keyboard
        await bot.send_message(user.id, message, reply_markup=reply_markup)
    except Exception as e:
        print(f"[EXPIRY-CHECK] Failed to send expired notification: {e}")


async def send_expiring_soon_notification(bot, user: User, accounts: List[Account]):
    """Send notification about accounts expiring soon with interactive buttons."""
    # Header message
    message_lines = [
        "⏰ <b>Напоминание: скоро истечет срок мониторинга</b>\n",
        f"📅 Найдено аккаунтов: {len(accounts)}\n",
        "💡 <b>Рекомендация:</b> Увеличьте период мониторинга заранее\n",
        "👇 Нажмите на кнопку с аккаунтом для просмотра информации:"
    ]
    
    message = "\n".join(message_lines)
    
    # Create inline keyboard with buttons for each account
    keyboard = []
    for acc in accounts:
        days_left = (acc.to_date - date.today()).days
        button_text = f"@{acc.account} (осталось {days_left} дн.)"
        keyboard.append([{
            "text": button_text,
            "callback_data": f"expiry_soon:{acc.id}"
        }])
    
    # Add "Manage accounts" button
    keyboard.append([{
        "text": "📱 Неактивные аккаунты",
        "callback_data": "show_inactive_accounts"
    }])
    
    reply_markup = {"inline_keyboard": keyboard}
    
    try:
        # Send message with inline keyboard
        await bot.send_message(user.id, message, reply_markup=reply_markup)
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
