"""Automatic background checker for accounts with parallel user processing."""

import asyncio
import os
import random
from datetime import datetime, timedelta, date
from sqlalchemy.orm import sessionmaker

try:
    from ..models import Account, User
    from ..services.main_checker import check_account_main
    from ..services.system_settings import get_global_verify_mode
    from ..services.traffic_monitor import get_traffic_monitor
    from ..services.autocheck_traffic_stats import AutoCheckTrafficStats
    from ..utils.encryptor import OptionalFernet
    from ..config import get_settings
except ImportError:
    from models import Account, User
    from services.main_checker import check_account_main
    from services.system_settings import get_global_verify_mode
    from services.traffic_monitor import get_traffic_monitor
    from services.autocheck_traffic_stats import AutoCheckTrafficStats
    from utils.encryptor import OptionalFernet
    from config import get_settings


async def send_traffic_report_to_admins(SessionLocal: sessionmaker, bot, user_id: int, traffic_stats):
    """
    Send traffic report to all admin users.
    
    Args:
        SessionLocal: SQLAlchemy session factory
        bot: TelegramBot instance
        user_id: User ID that was checked
        traffic_stats: AutoCheckTrafficStats instance with statistics
    """
    with SessionLocal() as session:
        # Get all admin users
        admin_users = session.query(User).filter(
            User.role.in_(['admin', 'superuser']),
            User.is_active == True
        ).all()
        
        if not admin_users:
            print("[AUTO-CHECK] ⚠️ No admin users found to send traffic report")
            return
        
        # Get checked user info
        checked_user = session.query(User).get(user_id)
        username = checked_user.username if checked_user else f"User {user_id}"
        
        # Generate report
        report = f"👤 <b>Пользователь: @{username}</b>\n\n"
        report += traffic_stats.get_report()
        
        # Send report to all admins
        for admin in admin_users:
            try:
                await bot.send_message(admin.id, report)
                print(f"[AUTO-CHECK] 📤 Traffic report sent to admin {admin.id} (@{admin.username})")
            except Exception as e:
                print(f"[AUTO-CHECK] ❌ Failed to send traffic report to admin {admin.id}: {e}")


async def check_user_accounts(user_id: int, user_accounts: list, SessionLocal: sessionmaker, fernet: OptionalFernet, bot=None):
    """
    Check accounts for a specific user using new API + Proxy logic.
    
    Args:
        user_id: User ID
        user_accounts: List of accounts for this user
        SessionLocal: SQLAlchemy session factory
        fernet: Fernet encryptor
        bot: Optional TelegramBot instance
    """
    print(f"[AUTO-CHECK] 🧵 Starting check for user {user_id} with {len(user_accounts)} accounts")
    
    checked = 0
    found = 0
    not_found = 0
    errors = 0
    
    # Initialize traffic statistics tracker
    traffic_stats = AutoCheckTrafficStats()
    traffic_monitor = get_traffic_monitor()
    
    # Get initial traffic count
    initial_traffic = traffic_monitor.total_traffic
    
    with SessionLocal() as session:
        # Get user info
        user = session.query(User).get(user_id)
        if not user:
            print(f"[AUTO-CHECK] ❌ User {user_id} not found")
            return {"checked": 0, "found": 0, "not_found": 0, "errors": 1}
        
        # Get global verification mode
        verify_mode = get_global_verify_mode(session)
        print(f"[AUTO-CHECK] 👤 User {user_id} - режим проверки: {verify_mode}")
        
        # Check all accounts using new main_checker logic
        for idx, acc in enumerate(user_accounts):
            check_start_traffic = traffic_monitor.total_traffic
            check_start_time = datetime.now()
            
            try:
                print(f"[AUTO-CHECK] [{idx+1}/{len(user_accounts)}] Проверка @{acc.account}...")
                
                # Use new main_checker with API + Proxy logic
                success, message, screenshot_path = await check_account_main(
                    username=acc.account,
                        session=session,
                    user_id=user_id
                    )
                
                checked += 1
                
                # Calculate traffic consumed by this check
                check_end_time = datetime.now()
                check_traffic = traffic_monitor.total_traffic - check_start_traffic
                check_duration_ms = (check_end_time - check_start_time).total_seconds() * 1000
                
                # Add to traffic stats
                traffic_stats.add_check(
                    username=acc.account,
                    is_active=success,
                    traffic_bytes=check_traffic,
                    duration_ms=check_duration_ms,
                    error=False
                )
                    
                if success:
                    found += 1
                    print(f"[AUTO-CHECK] ✅ @{acc.account} - FOUND: {message}")
                    
                    # Mark account as done
                    account = session.query(Account).filter(
                        Account.user_id == user_id,
                        Account.account == acc.account
                    ).first()
                    if account:
                        account.done = True
                        account.date_of_finish = date.today()
                        session.commit()
                        print(f"[AUTO-CHECK] ✅ Marked @{acc.account} as done")
                        
                        # Send notification to user if bot is provided
                        if bot:
                            try:
                                # Calculate time completed
                                completed_text = "1 дней"  # Default fallback
                                # Используем from_date_time если доступно, иначе from_date
                                if hasattr(acc, 'from_date_time') and acc.from_date_time:
                                    start_datetime = acc.from_date_time
                                elif acc.from_date:
                                    if isinstance(acc.from_date, datetime):
                                        start_datetime = acc.from_date
                                    else:
                                        start_datetime = datetime.combine(acc.from_date, datetime.min.time())
                                else:
                                    start_datetime = None
                                
                                if start_datetime:
                                    current_datetime = datetime.now()
                                    time_diff = current_datetime - start_datetime
                                    total_seconds = int(time_diff.total_seconds())
                                    
                                    # Calculate days, hours, minutes
                                    days = total_seconds // 86400
                                    remaining_seconds = total_seconds % 86400
                                    hours = remaining_seconds // 3600
                                    minutes = (remaining_seconds % 3600) // 60
                                    
                                    # Format result: "X дней Y часов Z минут"
                                    parts = []
                                    if days > 0:
                                        parts.append(f"{days} {'день' if days == 1 else 'дней' if days > 4 else 'дня'}")
                                    if hours > 0:
                                        parts.append(f"{hours} {'час' if hours == 1 else 'часов' if hours > 4 else 'часа'}")
                                    if minutes > 0 or not parts:  # Show minutes if present or if no days/hours
                                        parts.append(f"{minutes} {'минута' if minutes == 1 else 'минут' if minutes > 4 else 'минуты'}")
                                    
                                    completed_text = " ".join(parts)
                                
                                # Format start date with time if available
                                if hasattr(acc, 'from_date_time') and acc.from_date_time:
                                    start_date_str = acc.from_date_time.strftime("%d.%m.%Y в %H:%M")
                                elif acc.from_date:
                                    start_date_str = acc.from_date.strftime("%d.%m.%Y")
                                else:
                                    start_date_str = "N/A"
                                
                                message = f"""Имя пользователя: <a href="https://www.instagram.com/{acc.account}/">{acc.account}</a>
Начало работ: {start_date_str}
Заявлено: {acc.period} дней
Завершено за: {completed_text}
Конец работ: {acc.to_date.strftime("%d.%m.%Y") if acc.to_date else "N/A"}
Статус: Аккаунт разблокирован✅"""
                                
                                # Send screenshot with message as caption
                                if screenshot_path and os.path.exists(screenshot_path):
                                    try:
                                                success = await bot.send_photo(
                                                    user.id,
                                                    screenshot_path,
                                                    message
                                                )
                                                if success:
                                                    print(f"[AUTO-CHECK] 📸 Screenshot sent successfully with caption!")
                                    except Exception as e:
                                        print(f"[AUTO-CHECK] ❌ Failed to send photo: {e}")
                                        # Fallback: send message separately if photo fails
                                        await bot.send_message(user.id, message)
                                else:
                                    # If no screenshot, send message separately
                                    await bot.send_message(user.id, message)
                                    
                            except Exception as e:
                                print(f"[AUTO-CHECK] ❌ Failed to send notification to user {user.id}: {e}")
                    
                else:
                    not_found += 1
                    print(f"[AUTO-CHECK] ❌ @{acc.account} - NOT FOUND: {message}")
                    
                    # Send notification to user for API key exhaustion
                    if bot and "Все API ключи исчерпаны" in message:
                        try:
                            notification = f"""⚠️ **Проблема с API ключами**

Все API ключи исчерпаны.

Аккаунт: @{acc.account}
Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"""
                            
                            await bot.send_message(user.id, notification)
                            print(f"[AUTO-CHECK] 📤 Sent API exhaustion notification to user {user.id}")
                        except Exception as e:
                            print(f"[AUTO-CHECK] ❌ Failed to send API exhaustion notification: {e}")
                
                # Minimal delay between checks (0.5-1 second for rate limiting)
                if idx < len(user_accounts) - 1:
                    delay = random.uniform(0.5, 1.0)
                    await asyncio.sleep(delay)
                        
            except Exception as e:
                errors += 1
                print(f"[AUTO-CHECK] ❌ Error checking @{acc.account}: {str(e)}")
                
                # Calculate traffic even for errors
                check_end_time = datetime.now()
                check_traffic = traffic_monitor.total_traffic - check_start_traffic
                check_duration_ms = (check_end_time - check_start_time).total_seconds() * 1000
                
                # Add error to traffic stats
                traffic_stats.add_check(
                    username=acc.account,
                    is_active=False,
                    traffic_bytes=check_traffic,
                    duration_ms=check_duration_ms,
                    error=True
                )
        
        # Finalize traffic stats
        traffic_stats.finalize()
        
        print(f"[AUTO-CHECK] 🧵 User {user_id} check complete: {checked} checked, {found} found, {not_found} not found, {errors} errors")
        print(f"[AUTO-CHECK] 📊 Total traffic consumed: {traffic_stats.format_bytes(traffic_monitor.total_traffic - initial_traffic)}")
        
        return {
            "checked": checked,
            "found": found,
            "not_found": not_found,
            "errors": errors,
            "traffic_stats": traffic_stats
        }


async def check_user_pending_accounts(user_id: int, SessionLocal: sessionmaker, bot=None, max_accounts: int = 999999, send_report: bool = True):
    """
    Check pending accounts (done=False) for a specific user.
    
    Args:
        user_id: User ID to check accounts for
        SessionLocal: SQLAlchemy session factory
        bot: Optional TelegramBot instance to send notifications
        max_accounts: Maximum number of accounts to check per run
        send_report: Send traffic report to admins after check
    """
    settings = get_settings()
    fernet = OptionalFernet(settings.encryption_key)
    
    with SessionLocal() as session:
        # Check if user exists and autocheck is enabled
        user = session.query(User).get(user_id)
        if not user:
            print(f"[AUTO-CHECK-USER-{user_id}] ❌ User {user_id} not found")
            return
        
        if not user.auto_check_enabled:
            print(f"[AUTO-CHECK-USER-{user_id}] ⏸️ Auto-check disabled for user {user_id}")
            return
        
        # Get pending accounts for this user only
        pending_accounts = (
            session.query(Account)
            .filter(
                Account.user_id == user_id,
                Account.done == False
            )
            .order_by(Account.from_date.asc())
            .limit(max_accounts)
            .all()
        )
        
        if not pending_accounts:
            print(f"[AUTO-CHECK-USER-{user_id}] No pending accounts to check.")
            return
        
        print(f"[AUTO-CHECK-USER-{user_id}] {datetime.now()} - Starting check for user {user_id} with {len(pending_accounts)} accounts")
        
        # Check accounts for this user
        result = await check_user_accounts(user_id, pending_accounts, SessionLocal, fernet, bot)
        
        print(f"[AUTO-CHECK-USER-{user_id}] ✅ Check completed: {result.get('checked', 0)} checked, {result.get('found', 0)} found")
        
        # Send traffic report to admins if requested
        if send_report and bot and result.get('traffic_stats'):
            await send_traffic_report_to_admins(
                SessionLocal=SessionLocal,
                bot=bot,
                user_id=user_id,
                traffic_stats=result['traffic_stats']
            )


async def check_pending_accounts(SessionLocal: sessionmaker, bot=None, max_accounts: int = 5, notify_admin: bool = True):
    """
    Check pending accounts (done=False) for all users in parallel.
    
    Args:
        SessionLocal: SQLAlchemy session factory
        bot: Optional TelegramBot instance to send notifications
        max_accounts: Maximum number of accounts to check per run
        notify_admin: Send notification to admin about check start/finish
    """
    settings = get_settings()
    fernet = OptionalFernet(settings.encryption_key)
    
    print(f"\n[AUTO-CHECK] {datetime.now()} - Starting automatic check...")
    
    # NOTE: Expiry notifications are now handled by separate daily scheduler at 10:00 AM
    # See project/expiry_scheduler.py
    
    # Get admin users for notifications
    admin_users = []
    if bot and notify_admin:
        with SessionLocal() as session:
            admin_users = session.query(User).filter(
                User.role.in_(['admin', 'superuser']),
                User.is_active == True
            ).all()
    
    with SessionLocal() as session:
        # Get all pending accounts
        pending_accounts = (
            session.query(Account)
            .filter(Account.done == False)
            .order_by(Account.from_date.asc())
            .limit(max_accounts)
            .all()
        )
        
        if not pending_accounts:
            print("[AUTO-CHECK] No pending accounts to check.")
            return
        
        print(f"[AUTO-CHECK] Found {len(pending_accounts)} pending accounts to check.")
        
        # Group accounts by user for parallel processing
        accounts_by_user = {}
        for acc in pending_accounts:
            if acc.user_id not in accounts_by_user:
                accounts_by_user[acc.user_id] = []
            accounts_by_user[acc.user_id].append(acc)
        
        print(f"[AUTO-CHECK] 📊 Found {len(accounts_by_user)} users with pending accounts")
        
        # Create tasks for parallel processing
        tasks = []
        for user_id, user_accounts in accounts_by_user.items():
            task = check_user_accounts(user_id, user_accounts, SessionLocal, fernet, bot)
            tasks.append(task)
        
        # Run all user checks in parallel
        print(f"[AUTO-CHECK] 🚀 Starting parallel checks for {len(tasks)} users...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        total_checked = 0
        total_found = 0
        total_not_found = 0
        total_errors = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"[AUTO-CHECK] ❌ Error in user {list(accounts_by_user.keys())[i]}: {result}")
                total_errors += 1
            else:
                total_checked += result.get("checked", 0)
                total_found += result.get("found", 0)
                total_not_found += result.get("not_found", 0)
                total_errors += result.get("errors", 0)
        
        print(f"[AUTO-CHECK] 📊 Final results: {total_checked} checked, {total_found} found, {total_not_found} not found, {total_errors} errors")
        
        # Update final statistics
        checked = total_checked
        found = total_found
        not_found = total_not_found
        errors = total_errors
        
        print(f"[AUTO-CHECK] Completed!")
        print(f"  • Checked: {checked}")
        print(f"  • Found: {found}")
        print(f"  • Not found: {not_found}")
        print(f"  • Errors: {errors}")


def start_auto_checker(SessionLocal: sessionmaker, bot=None, interval_minutes: int = 3, run_immediately: bool = True):
    """
    Start the automatic checker with APScheduler.
    
    Args:
        SessionLocal: SQLAlchemy session factory
        bot: Optional TelegramBot instance
        interval_minutes: Check interval in minutes
        run_immediately: Run check immediately on start
    """
    print(f"[AUTO-CHECK-SCHEDULER] Starting automatic checker (every {interval_minutes} minutes)")
    
    # Import APScheduler
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.interval import IntervalTrigger
    except ImportError:
        print("[AUTO-CHECK-SCHEDULER] APScheduler not available, using fallback timer")
        return
    
    # Create scheduler
    scheduler = AsyncIOScheduler()
    
    # Define the check job
    async def auto_check_job():
        """Periodic auto-check job."""
        print(f"[AUTO-CHECK-SCHEDULER] Check started at {datetime.now()}")
        try:
            await check_pending_accounts(SessionLocal, bot, max_accounts=999999, notify_admin=True)
            print(f"[AUTO-CHECK-SCHEDULER] Check completed at {datetime.now()}")
        except Exception as e:
            print(f"[AUTO-CHECK-SCHEDULER] Error in auto-check: {e}")
    
    # Add job to scheduler
    scheduler.add_job(
        auto_check_job,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id='auto_check_job',
        name='Automatic Account Checker',
        replace_existing=True
    )
    
    # Start scheduler
    scheduler.start()
    print(f"[AUTO-CHECK-SCHEDULER] Scheduler started (every {interval_minutes} minutes)")
    
    # Run immediately if requested
    if run_immediately:
        print(f"[AUTO-CHECK-SCHEDULER] Running initial check...")
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            loop.create_task(auto_check_job())
        except Exception as e:
            print(f"[AUTO-CHECK-SCHEDULER] Error in initial check: {e}")
    
    return scheduler