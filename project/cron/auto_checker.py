"""Automatic background checker for accounts with parallel user processing."""

import asyncio
import random
from datetime import datetime, timedelta, date
from sqlalchemy.orm import sessionmaker

try:
    from ..models import Account, User
    from ..services.hybrid_checker import check_account_hybrid
    from ..services.triple_checker import check_account_triple
    from ..services.simple_checkers import check_account_instagram_only, check_account_proxy_only, check_account_instagram_proxy
    from ..services.ig_sessions import get_priority_valid_session
    from ..utils.encryptor import OptionalFernet
    from ..config import get_settings
except ImportError:
    from models import Account, User
    from services.hybrid_checker import check_account_hybrid
    from services.triple_checker import check_account_triple
    from services.simple_checkers import check_account_instagram_only, check_account_proxy_only, check_account_instagram_proxy
    from services.ig_sessions import get_priority_valid_session
    from utils.encryptor import OptionalFernet
    from config import get_settings


async def check_user_accounts(user_id: int, user_accounts: list, SessionLocal: sessionmaker, fernet: OptionalFernet, bot=None):
    """
    Check accounts for a specific user in a separate thread.
    
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
    
    with SessionLocal() as session:
        # Get user info
        user = session.query(User).get(user_id)
        if not user:
            print(f"[AUTO-CHECK] ❌ User {user_id} not found")
            return {"checked": 0, "found": 0, "not_found": 0, "errors": 1}
        
        verify_mode = user.verify_mode or "api+instagram"
        print(f"[AUTO-CHECK] 👤 User {user_id} mode: {verify_mode}")
        
        # Get appropriate session based on verify_mode
        if verify_mode in ["api+instagram", "instagram", "instagram+proxy", "api+proxy+instagram"]:
            # Modes that need Instagram session
            ig_session = get_priority_valid_session(session, user_id, fernet)
            if not ig_session:
                print(f"[AUTO-CHECK] ❌ No valid IG session for user {user_id}")
                return {"checked": 0, "found": 0, "not_found": 0, "errors": len(user_accounts)}
        else:
            ig_session = None
        
        if verify_mode in ["api+proxy", "proxy", "instagram+proxy", "api+proxy+instagram"]:
            # Modes that need Proxy
            from ..models import Proxy
            proxy = session.query(Proxy).filter(
                Proxy.user_id == user_id,
                Proxy.is_active == True
            ).first()
            
            if not proxy:
                print(f"[AUTO-CHECK] ⏭️ User {user_id} has no active proxy - SKIPPING")
                return {"checked": 0, "found": 0, "not_found": 0, "errors": 0}
        
        # PHASE 1: API checks for this user's accounts (skip for non-API modes)
        accounts_to_verify = []
        
        # Check if this mode uses API
        uses_api = verify_mode in ["api+instagram", "api+proxy", "api+proxy+instagram"]
        
        if uses_api:
            print(f"[AUTO-CHECK] 📡 Phase 1: API checks for user {user_id}...")
            
            # Add delay between checks to avoid Instagram rate limiting
            import time
            import random
            
            for idx, acc in enumerate(user_accounts):
                try:
                    print(f"[AUTO-CHECK] [{idx+1}/{len(user_accounts)}] API check @{acc.account} (user {user_id})...")
                    
                    # Perform API-only check
                    result = await check_account_hybrid(
                        session=session,
                        user_id=user_id,
                        username=acc.account,
                        ig_session=ig_session,
                        fernet=fernet,
                        skip_instagram_verification=True,  # SKIP verification in Phase 1
                        verify_mode=verify_mode
                    )
                    
                    checked += 1
                    
                    # If API says account is active, add to verification list
                    if result.get("exists") is True:
                        accounts_to_verify.append((acc, result))
                        verification_method = "Instagram" if verify_mode == "api+instagram" else "Proxy"
                        print(f"[AUTO-CHECK] ✓ @{acc.account} - API says ACTIVE (will verify with {verification_method})")
                    elif result.get("exists") is False:
                        not_found += 1
                        print(f"[AUTO-CHECK] ❌ @{acc.account} - API says NOT FOUND")
                    else:
                        errors += 1
                        print(f"[AUTO-CHECK] ❓ @{acc.account} - API ERROR: {result.get('error', 'unknown')}")
                    
                    # Random delay between API checks (2-5 seconds) to avoid rate limiting
                    if idx < len(user_accounts) - 1:
                        delay = random.uniform(2, 5)
                        print(f"[AUTO-CHECK] ⏳ Waiting {delay:.1f}s before next check...")
                        await asyncio.sleep(delay)
                        
                except Exception as e:
                    errors += 1
                    print(f"[AUTO-CHECK] ❌ Error in API check @{acc.account}: {str(e)}")
            
            print(f"[AUTO-CHECK] 📡 Phase 1 complete for user {user_id}: {len(accounts_to_verify)} accounts to verify")
        else:
            # For non-API modes, check all accounts directly
            print(f"[AUTO-CHECK] 🔍 Skipping API phase (mode: {verify_mode}), checking all accounts directly...")
            for acc in user_accounts:
                accounts_to_verify.append((acc, None))  # No API result
        
        # PHASE 2: Verification for active accounts
        if accounts_to_verify:
            print(f"[AUTO-CHECK] 📸 Phase 2: Verification for user {user_id}...")
            
            for idx, (acc, api_result) in enumerate(accounts_to_verify):
                try:
                    # Select appropriate checker based on verify_mode
                    if verify_mode == "api+proxy+instagram":
                        verification_method = "API + Proxy + Instagram"
                        print(f"[AUTO-CHECK] [{idx+1}/{len(accounts_to_verify)}] {verification_method} triple verify @{acc.account}...")
                        
                        result = await check_account_triple(
                            session=session,
                            user_id=user_id,
                            username=acc.account,
                            ig_session=ig_session,
                            fernet=fernet
                        )
                    
                    elif verify_mode == "instagram+proxy":
                        verification_method = "Instagram + Proxy"
                        print(f"[AUTO-CHECK] [{idx+1}/{len(accounts_to_verify)}] {verification_method} verify @{acc.account}...")
                        
                        result = await check_account_instagram_proxy(
                            session=session,
                            user_id=user_id,
                            username=acc.account,
                            ig_session=ig_session,
                            fernet=fernet
                        )
                    
                    elif verify_mode == "instagram":
                        verification_method = "Instagram only"
                        print(f"[AUTO-CHECK] [{idx+1}/{len(accounts_to_verify)}] {verification_method} verify @{acc.account}...")
                        
                        result = await check_account_instagram_only(
                            session=session,
                            user_id=user_id,
                            username=acc.account,
                            ig_session=ig_session,
                            fernet=fernet
                        )
                    
                    elif verify_mode == "proxy":
                        verification_method = "Proxy only"
                        print(f"[AUTO-CHECK] [{idx+1}/{len(accounts_to_verify)}] {verification_method} verify @{acc.account}...")
                        
                        result = await check_account_proxy_only(
                            session=session,
                            user_id=user_id,
                            username=acc.account
                        )
                    
                    else:
                        # api+instagram or api+proxy modes
                        verification_method = "Instagram" if verify_mode == "api+instagram" else "Proxy"
                        print(f"[AUTO-CHECK] [{idx+1}/{len(accounts_to_verify)}] {verification_method} verify @{acc.account}...")
                        
                        result = await check_account_hybrid(
                            session=session,
                            user_id=user_id,
                            username=acc.account,
                            ig_session=ig_session,
                            fernet=fernet,
                            skip_instagram_verification=False,  # DO verification in Phase 2
                            verify_mode=verify_mode
                        )
                    
                    # Log the full result for debugging
                    print(f"[AUTO-CHECK] 🔍 Result for @{acc.account}: exists={result.get('exists')}, checked_via={result.get('checked_via')}, screenshot_path={result.get('screenshot_path')}")
                    
                    # Longer delay between proxy/Instagram checks (5-10 seconds) to avoid detection
                    if idx < len(accounts_to_verify) - 1:
                        delay = random.uniform(5, 10)
                        print(f"[AUTO-CHECK] ⏳ Waiting {delay:.1f}s before next verification...")
                        await asyncio.sleep(delay)
                    
                    # Update statistics and handle results
                    if result.get("exists") is True:
                        found += 1
                        print(f"[AUTO-CHECK] ✅ @{acc.account} - FOUND (verified via {result.get('checked_via', 'unknown')})")
                        
                        # Mark account as done ONLY if truly found
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
                                # Calculate real days completed
                                completed_days = 1  # Default fallback
                                if acc.from_date:
                                    if isinstance(acc.from_date, datetime):
                                        start_date = acc.from_date.date()
                                    else:
                                        start_date = acc.from_date
                                    
                                    current_date = date.today()
                                    completed_days = (current_date - start_date).days + 1  # +1 to include start day
                                    
                                    # Ensure completed_days is at least 1
                                    completed_days = max(1, completed_days)
                                
                                message = f"""Имя пользователя: <a href="https://www.instagram.com/{acc.account}/">{acc.account}</a>
Начало работ: {acc.from_date.strftime("%d.%m.%Y") if acc.from_date else "N/A"}
Заявлено: {acc.period} дней
Завершено за: {completed_days} дней
Конец работ: {acc.to_date.strftime("%d.%m.%Y") if acc.to_date else "N/A"}
Статус: Аккаунт разблокирован✅"""
                                # Send message
                                await bot.send_message(user.id, message)
                                
                                # Send screenshot if available
                                if result.get("screenshot_path"):
                                    import os
                                    screenshot_path = result["screenshot_path"]
                                    print(f"[AUTO-CHECK] 📸 Screenshot path found: {screenshot_path}")
                                    
                                    if os.path.exists(screenshot_path):
                                        print(f"[AUTO-CHECK] 📸 Screenshot file exists, size: {os.path.getsize(screenshot_path)} bytes")
                                        try:
                                            print(f"[AUTO-CHECK] 📸 Sending screenshot to user {user.id}...")
                                            # Send photo
                                            success = await bot.send_photo(
                                                user.id,
                                                screenshot_path,
                                                f'📸 <a href="https://www.instagram.com/{acc.account}/">@{acc.account}</a>'
                                            )
                                            
                                            if success:
                                                print(f"[AUTO-CHECK] 📸 Screenshot sent successfully!")
                                                # Delete screenshot after sending
                                                os.remove(screenshot_path)
                                                print(f"[AUTO-CHECK] 📸 Screenshot deleted: {screenshot_path}")
                                            else:
                                                print(f"[AUTO-CHECK] ⚠️ Screenshot send returned False")
                                        except Exception as e:
                                            print(f"[AUTO-CHECK] ❌ Failed to send photo: {e}")
                                            import traceback
                                            traceback.print_exc()
                                    else:
                                        print(f"[AUTO-CHECK] ⚠️ Screenshot file NOT found: {screenshot_path}")
                                else:
                                    print(f"[AUTO-CHECK] ⚠️ No screenshot path in result")
                                    
                            except Exception as e:
                                print(f"[AUTO-CHECK] ❌ Failed to send notification to user {user.id}: {e}")
                    
                    # Check for warnings (API active but profile not found)
                    elif result.get("warning"):
                        print(f"[AUTO-CHECK] ⚠️ @{acc.account} - WARNING: {result.get('warning')}")
                        
                        # Send warning notification to user if bot is provided
                        if bot:
                            try:
                                warning_message = f"""⚠️ **Предупреждение для @{acc.account}**

📡 **API проверка:** Активен ✅
🌐 **Страница профиля:** Не найдена ❌

**Что это значит:**
API показывает, что аккаунт активен, но при проверке через прокси + Instagram страница профиля не найдена.

**Возможные причины:**
• Аккаунт временно недоступен
• Блокировка по региону
• Технические проблемы Instagram

**Рекомендация:** Проверьте аккаунт вручную через браузер"""
                                
                                await bot.send_message(user.id, warning_message)
                                print(f"[AUTO-CHECK] ⚠️ Warning notification sent to user {user.id}")
                            except Exception as e:
                                print(f"[AUTO-CHECK] ❌ Failed to send warning to user {user.id}: {e}")
                    
                    else:
                        errors += 1
                        print(f"[AUTO-CHECK] ❌ @{acc.account} - Verification failed: {result.get('error', 'unknown')}")
                    
                    # Delay between verifications (5 seconds)
                    if idx < len(accounts_to_verify) - 1:
                        await asyncio.sleep(5)
                        
                except Exception as e:
                    errors += 1
                    print(f"[AUTO-CHECK] ❌ Error in verification @{acc.account}: {str(e)}")
        
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