"""Optimized automatic background checker for accounts with parallel user processing.

Features:
- Parallel processing of all users in one thread (non-blocking)
- Concurrency limits to prevent resource exhaustion (max 10 users)
- Timeout protection (5 minutes per user)
- Account limits (max 100 accounts per run)
- Performance monitoring and logging
- Runs in separate thread via AutoCheckerScheduler
"""

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


# Using parallel processing for all users in one thread


async def check_user_accounts(user_id: int, user_accounts: list, SessionLocal: sessionmaker, fernet: OptionalFernet, bot=None):
    """
    Check accounts for a specific user using new API + Proxy logic (parallel processing).
    
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
                delay_between_screenshots=0.0,  # Без задержек между скриншотами
                bot=bot  # Передаем бота для уведомлений
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
                if bot and error_msg and "no_proxies_available" in error_msg:
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
    Check pending accounts (done=False) for all users in parallel in one thread.
    
    Args:
        SessionLocal: SQLAlchemy session factory
        bot: Optional TelegramBot instance to send notifications
        max_accounts: Maximum number of accounts to check per run
        notify_admin: Send notification to admin about check start/finish
    """
    settings = get_settings()
    fernet = OptionalFernet(settings.encryption_key)
    
    start_time = datetime.now()
    print(f"\n[AUTO-CHECK] {start_time} - Starting automatic check...")
    
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
        # Get all pending accounts with reasonable limit
        # Limit to prevent system overload
        effective_max_accounts = min(max_accounts, 100)  # Max 100 accounts per run
        pending_accounts = (
            session.query(Account)
            .filter(Account.done == False)
            .order_by(Account.from_date.asc())
            .limit(effective_max_accounts)
            .all()
        )
        
        if not pending_accounts:
            print("[AUTO-CHECK] No pending accounts to check.")
            return
        
        print(f"[AUTO-CHECK] Found {len(pending_accounts)} pending accounts to check.")
        
        # Process all accounts in parallel in one thread
        print(f"[AUTO-CHECK] 🚀 Starting parallel check for {len(pending_accounts)} accounts...")
        
        # Group accounts by user for batch processing
        accounts_by_user = {}
        for acc in pending_accounts:
            if acc.user_id not in accounts_by_user:
                accounts_by_user[acc.user_id] = []
            accounts_by_user[acc.user_id].append(acc)
        
        print(f"[AUTO-CHECK] 📊 Found {len(accounts_by_user)} users with pending accounts")
        
        # Process all users' accounts in parallel using asyncio.gather with concurrency limit
        print(f"[AUTO-CHECK] 🔄 Executing parallel user checks...")
        try:
            # Limit concurrent users to prevent resource exhaustion
            max_concurrent_users = min(10, len(accounts_by_user))  # Max 10 users at once
            semaphore = asyncio.Semaphore(max_concurrent_users)
            
            async def limited_check_user_accounts(user_id, user_accounts, SessionLocal, fernet, bot):
                async with semaphore:
                    try:
                        # Add timeout to prevent hanging
                        return await asyncio.wait_for(
                            check_user_accounts(user_id, user_accounts, SessionLocal, fernet, bot),
                            timeout=300  # 5 minutes timeout per user
                        )
                    except asyncio.TimeoutError:
                        print(f"[AUTO-CHECK] ⏰ Timeout for user {user_id} after 5 minutes")
                        return {"checked": 0, "found": 0, "not_found": 0, "errors": len(user_accounts)}
            
            # Create limited tasks
            limited_tasks = []
            for user_id, user_accounts in accounts_by_user.items():
                print(f"[AUTO-CHECK] 👤 Creating task for user {user_id} with {len(user_accounts)} accounts...")
                task = limited_check_user_accounts(user_id, user_accounts, SessionLocal, fernet, bot)
                limited_tasks.append(task)
            
            results = await asyncio.gather(*limited_tasks, return_exceptions=True)
            
            # Process results
            total_checked = 0
            total_found = 0
            total_not_found = 0
            total_errors = 0
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"[AUTO-CHECK] ❌ Error in user task {i}: {result}")
                    # Count all accounts for this user as errors
                    user_id = list(accounts_by_user.keys())[i]
                    total_errors += len(accounts_by_user[user_id])
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
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print(f"[AUTO-CHECK] ✅ Completed in {duration:.2f} seconds!")
            print(f"  • Checked: {checked}")
            print(f"  • Found: {found}")
            print(f"  • Not found: {not_found}")
            print(f"  • Errors: {errors}")
            print(f"  • Performance: {checked/duration:.2f} accounts/second" if duration > 0 else "  • Performance: N/A")
            
        except Exception as e:
            print(f"[AUTO-CHECK] ❌ Error in parallel execution: {e}")
            import traceback
            traceback.print_exc()


# Note: start_auto_checker function removed - use AutoCheckerScheduler instead
# This prevents confusion and potential blocking of the main thread