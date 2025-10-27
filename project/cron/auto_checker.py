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
    from ..services.api_v2_proxy_checker import batch_check_with_optimized_screenshots
    from ..utils.encryptor import OptionalFernet
    from ..config import get_settings
except ImportError:
    from models import Account, User
    from services.main_checker import check_account_main
    from services.system_settings import get_global_verify_mode
    from services.api_v2_proxy_checker import batch_check_with_optimized_screenshots
    from utils.encryptor import OptionalFernet
    from config import get_settings


def calculate_optimal_concurrency(total_tasks: int, task_type: str = "accounts") -> int:
    """
    Calculate optimal concurrency based on task count and type.
    
    Args:
        total_tasks: Total number of tasks
        task_type: Type of tasks ("accounts" or "users")
        
    Returns:
        Optimal concurrency limit
    """
    if task_type == "accounts":
        # Для аккаунтов: минимум 5, максимум 20, зависит от количества
        if total_tasks <= 10:
            return min(5, total_tasks)
        elif total_tasks <= 50:
            return min(10, total_tasks)
        elif total_tasks <= 100:
            return min(15, total_tasks)
        else:
            return min(20, total_tasks)
    else:  # users
        # Для пользователей: минимум 2, максимум 8
        if total_tasks <= 5:
            return min(3, total_tasks)
        elif total_tasks <= 20:
            return min(5, total_tasks)
        else:
            return min(8, total_tasks)


async def run_limited_parallel(tasks, max_concurrent=None, task_type="accounts"):
    """
    Run tasks in parallel with adaptive concurrency to prevent database overload.
    
    Args:
        tasks: List of coroutines to run
        max_concurrent: Maximum number of concurrent tasks (auto-calculated if None)
        task_type: Type of tasks ("accounts" or "users")
        
    Returns:
        List of results
    """
    if max_concurrent is None:
        max_concurrent = calculate_optimal_concurrency(len(tasks), task_type)
    
    print(f"[AUTO-CHECK] 🎯 Optimal concurrency for {len(tasks)} {task_type}: {max_concurrent}")
    
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def limited_task(task):
        async with semaphore:
            return await task
    
    limited_tasks = [limited_task(task) for task in tasks]
    return await asyncio.gather(*limited_tasks, return_exceptions=True)


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
    
    # Получаем информацию о пользователе БЫСТРО и закрываем сессию
    try:
        print(f"[AUTO-CHECK] 📂 Opening session to get user {user_id} info...")
        with SessionLocal() as session:
            # Get user info
            user = session.query(User).get(user_id)
            if not user:
                print(f"[AUTO-CHECK] ❌ User {user_id} not found in database")
                return {"checked": 0, "found": 0, "not_found": 0, "errors": 1}
            
            print(f"[AUTO-CHECK] ✅ User {user_id} found")
            
            # Копируем данные пользователя для использования вне сессии
            user_data = {
                "id": user.id,
                "username": user.username if hasattr(user, 'username') else None
            }
            
            # Get global verification mode
            verify_mode = get_global_verify_mode(session)
            print(f"[AUTO-CHECK] 👤 User {user_id} - режим проверки: {verify_mode}")
        print(f"[AUTO-CHECK] ✅ Session closed, starting account checks...")
    except Exception as e:
        print(f"[AUTO-CHECK] ❌ Error getting user info: {e}")
        import traceback
        traceback.print_exc()
        return {"checked": 0, "found": 0, "not_found": 0, "errors": 1}
    
    # ✨ НОВАЯ ОПТИМИЗИРОВАННАЯ ЛОГИКА: Сначала API для всех, потом скриншоты только для активных
    print(f"[AUTO-CHECK] 🚀 Используем оптимизированную проверку для {len(user_accounts)} аккаунтов")
    
    # Подготавливаем список username'ов для батчевой проверки
    usernames = [acc.account for acc in user_accounts]
    
    try:
        # Используем новую оптимизированную функцию
        with SessionLocal() as batch_session:
            batch_results = await batch_check_with_optimized_screenshots(
                session=batch_session,
                user_id=user_id,
                usernames=usernames,
                delay_between_api=0.0,  # Без задержек между API запросами
                delay_between_screenshots=0.0  # Без задержек между скриншотами
            )
        
        print(f"[AUTO-CHECK] ✅ Батчевая проверка завершена: {len(batch_results)} результатов")
        
        # Обрабатываем результаты и отправляем уведомления
        checked = 0
        found = 0
        not_found = 0
        errors = 0
        
        for result in batch_results:
            checked += 1
            username = result["username"]
            
            # Находим соответствующий объект Account
            acc_obj = None
            for acc in user_accounts:
                if acc.account == username:
                    acc_obj = acc
                    break
            
            if not acc_obj:
                print(f"[AUTO-CHECK] ⚠️ Не найден объект Account для @{username}")
                continue
            
            # Определяем успешность проверки
            is_success = result.get("exists") is True and result.get("screenshot_success", False)
            
            if is_success:
                found += 1
                print(f"[AUTO-CHECK] ✅ @{username} - FOUND с скриншотом (уведомление уже отправлено)")
                
                # Уведомление уже отправлено в send_immediate_notification
                # Аккаунт уже помечен как выполненный
            
            elif result.get("exists") is False:
                not_found += 1
                print(f"[AUTO-CHECK] ❌ @{username} - NOT FOUND")
                
                # Mark account as done (not found)
                with SessionLocal() as update_session:
                    account = update_session.query(Account).filter(
                        Account.user_id == user_id,
                        Account.account == username
                    ).first()
                    if account:
                        account.done = True
                        account.date_of_finish = date.today()
                        update_session.commit()
                        print(f"[AUTO-CHECK] ✅ Marked @{username} as done (not found)")
            
            else:
                errors += 1
                error_msg = result.get("error", "Unknown error")
                print(f"[AUTO-CHECK] ❌ @{username} - ERROR: {error_msg}")
                
                # Send notification to user for missing proxies
                if bot and "no_proxies_available" in error_msg:
                    try:
                        with SessionLocal() as user_session:
                            user = user_session.query(User).get(user_id)
                        
                        if user:
                            notification = f"""🔧 **Необходимо добавить прокси**

        Для проверки аккаунтов необходимо добавить прокси.

        Аккаунт: @{username}
        Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}

        Используйте команду /add_proxy для добавления прокси."""
                            
                            await bot.send_message(user.id, notification)
                            print(f"[AUTO-CHECK] 📤 Sent proxy requirement notification to user {user_id}")
                    except Exception as e:
                        print(f"[AUTO-CHECK] ❌ Failed to send proxy requirement notification: {e}")
                
                # Send notification to user for API key exhaustion
                elif bot and "Все API ключи исчерпаны" in error_msg:
                    try:
                        with SessionLocal() as user_session:
                            user = user_session.query(User).get(user_id)
                        
                        if user:
                            notification = f"""⚠️ **Проблема с API ключами**

        Все API ключи исчерпаны.

        Аккаунт: @{username}
        Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"""
                            
                            await bot.send_message(user.id, notification)
                            print(f"[AUTO-CHECK] 📤 Sent API exhaustion notification to user {user_id}")
                    except Exception as e:
                        print(f"[AUTO-CHECK] ❌ Failed to send API exhaustion notification: {e}")
    
    except Exception as e:
        print(f"[AUTO-CHECK] ❌ Error in batch check: {e}")
        import traceback
        traceback.print_exc()
        return {"checked": 0, "found": 0, "not_found": 0, "errors": len(user_accounts)}
    
    print(f"[AUTO-CHECK] 🧵 User {user_id} check complete: {checked} checked, {found} found, {not_found} not found, {errors} errors")
    return {"checked": checked, "found": found, "not_found": not_found, "errors": errors}


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
        
        # Run all user checks in parallel (adaptive concurrency)
        print(f"[AUTO-CHECK] 🚀 Starting parallel checks for {len(tasks)} users...")
        results = await run_limited_parallel(tasks, task_type="users")
        
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