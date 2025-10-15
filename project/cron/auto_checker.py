"""Automatic background checker for accounts."""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker

try:
    from ..models import Account, User
    from ..services.hybrid_checker import check_account_hybrid
    from ..services.ig_sessions import get_priority_valid_session
    from ..utils.encryptor import OptionalFernet
    from ..config import get_settings
except ImportError:
    from models import Account, User
    from services.hybrid_checker import check_account_hybrid
    from services.ig_sessions import get_priority_valid_session
    from utils.encryptor import OptionalFernet
    from config import get_settings


async def check_pending_accounts(SessionLocal: sessionmaker, bot=None, max_accounts: int = 5, notify_admin: bool = True):
    """
    Check pending accounts (done=False) for all users.
    
    Args:
        SessionLocal: SQLAlchemy session factory
        bot: Optional TelegramBot instance to send notifications
        max_accounts: Maximum number of accounts to check per run
        notify_admin: Send notification to admin about check start/finish
    """
    settings = get_settings()
    fernet = OptionalFernet(settings.encryption_key)
    
    print(f"\n[AUTO-CHECK] {datetime.now()} - Starting automatic check...")
    
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
        
        # Notify admins about check start - DISABLED
        # if bot and admin_users:
        #     for admin in admin_users:
        #         try:
        #             await bot.send_message(
        #                 admin.id,
        #                 f"🔄 Автопроверка запущена\n\n"
        #                 f"📊 Аккаунтов к проверке: {len(pending_accounts)}\n"
        #                 f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
        #             )
        #         except Exception as e:
        #             print(f"[AUTO-CHECK] Failed to notify admin {admin.id}: {e}")
        
        checked = 0
        found = 0
        not_found = 0
        errors = 0
        
        # Create tasks for parallel checking
        tasks = []
        
        async def check_single_account(acc):
            """Check single account in parallel."""
            nonlocal checked, found, not_found, errors
            
            try:
                # Get user's priority Instagram session
                with SessionLocal() as s:
                    ig_session = get_priority_valid_session(s, acc.user_id, fernet)
                
                if not ig_session:
                    print(f"[AUTO-CHECK] Skipping @{acc.account} - no valid IG session for user {acc.user_id}")
                    return
                
                print(f"[AUTO-CHECK] Checking @{acc.account}...")
                
                # Perform hybrid check
                with SessionLocal() as s:
                    result = await check_account_hybrid(
                        session=s,
                        user_id=acc.user_id,
                        username=acc.account,
                        ig_session=ig_session,
                        fernet=fernet
                    )
                
                checked += 1
                
                # Update statistics and handle results
                if result.get("exists") is True:
                    found += 1
                    print(f"[AUTO-CHECK] ✅ @{acc.account} - FOUND (verified via {result.get('checked_via', 'unknown')})")
                    
                    # Mark account as done ONLY if truly found
                    with SessionLocal() as s:
                        account = s.query(Account).filter(
                            Account.user_id == acc.user_id,
                            Account.account == acc.account
                        ).first()
                        if account:
                            account.done = True
                            from datetime import date
                            account.date_of_finish = date.today()
                            s.commit()
                            print(f"[AUTO-CHECK] ✅ Marked @{acc.account} as done")
                    
                    # Send notification to user if bot is provided
                    if bot:
                        try:
                            with SessionLocal() as s:
                                user = s.query(User).get(acc.user_id)
                                if user:
                                    # Calculate real days completed
                                    completed_days = 1  # Default fallback
                                    if acc.from_date:
                                        from datetime import date, datetime
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
                                    await bot.send_message(user.id, message)
                                    
                                    # Send screenshot if available
                                    if result.get("screenshot_path"):
                                        import os
                                        if os.path.exists(result["screenshot_path"]):
                                            try:
                                                await bot.send_photo(user.id, result["screenshot_path"], f'📸 <a href="https://www.instagram.com/{acc.account}/">@{acc.account}</a>')
                                                # Delete screenshot after sending
                                                os.remove(result["screenshot_path"])
                                                print(f"[AUTO-CHECK] 📸 Screenshot sent and deleted for @{acc.account}")
                                            except Exception as e:
                                                print(f"[AUTO-CHECK] Failed to send photo: {e}")
                        except Exception as e:
                            print(f"[AUTO-CHECK] Failed to send notification: {e}")
                
                elif result.get("exists") is False:
                    not_found += 1
                    error_detail = result.get("error", "")
                    if "api_found_but_instagram_not_found" in error_detail:
                        print(f"[AUTO-CHECK] ❌ @{acc.account} - NOT FOUND (API said exists, but Instagram confirms NOT FOUND)")
                    else:
                        print(f"[AUTO-CHECK] ❌ @{acc.account} - NOT FOUND")
                    
                    # Keep account as not done (done=False) - will be checked again later
                    print(f"[AUTO-CHECK] ⏳ @{acc.account} remains pending (done=False)")
                else:
                    errors += 1
                    print(f"[AUTO-CHECK] ❓ @{acc.account} - ERROR: {result.get('error', 'unknown')}")
                    # Keep as not done on error too
                
            except Exception as e:
                errors += 1
                print(f"[AUTO-CHECK] ❌ Error checking @{acc.account}: {str(e)}")
        
        # Run all checks in parallel with semaphore to limit concurrency
        semaphore = asyncio.Semaphore(1)  # Max 1 parallel check to avoid rate limits
        
        async def check_with_semaphore(acc):
            async with semaphore:
                await check_single_account(acc)
                # Much longer delay between checks to avoid rate limits and redirects
                print(f"[AUTO-CHECK] ⏳ Waiting 30 seconds before next check...")
                await asyncio.sleep(30)  # 30 seconds between checks
        
        # Create tasks for all accounts
        tasks = [check_with_semaphore(acc) for acc in pending_accounts]
        
        # Run all tasks in parallel
        await asyncio.gather(*tasks, return_exceptions=True)
        
        print(f"\n[AUTO-CHECK] Completed!")
        print(f"  • Checked: {checked}")
        print(f"  • Found: {found}")
        print(f"  • Not found: {not_found}")
        print(f"  • Errors: {errors}\n")
        
        # Notify admins about check completion - DISABLED
        # if bot and admin_users:
        #     for admin in admin_users:
        #         try:
        #             result_text = (
        #                 f"✅ Автопроверка завершена\n\n"
        #                 f"📊 Результаты:\n"
        #                 f"• Проверено: {checked}\n"
        #                 f"• Найдено: {found}\n"
        #                 f"• Не найдено: {not_found}\n"
        #                 f"• Ошибок: {errors}\n\n"
        #                 f"⏰ Завершено: {datetime.now().strftime('%H:%M:%S')}"
        #             )
        #             await bot.send_message(admin.id, result_text)
        #         except Exception as e:
        #             print(f"[AUTO-CHECK] Failed to notify admin {admin.id} about completion: {e}")


def start_auto_checker(SessionLocal: sessionmaker, bot=None, interval_minutes: int = 3, run_immediately: bool = True):
    """
    Start automatic background checker.
    
    Args:
        SessionLocal: SQLAlchemy session factory
        bot: Optional TelegramBot instance for notifications
        interval_minutes: Check interval in minutes (default: 3)
        run_immediately: Run first check immediately on startup (default: True)
    """
    import aiocron
    import asyncio
    import threading
    
    # Run first check immediately if requested (check ALL accounts)
    if run_immediately:
        print("[AUTO-CHECK] Running initial full check immediately...")
        
        def run_initial_check():
            """Run initial check in separate thread with its own event loop."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # Check ALL accounts (max_accounts=999999)
                loop.run_until_complete(
                    check_pending_accounts(SessionLocal, bot, max_accounts=999999, notify_admin=True)
                )
            except Exception as e:
                print(f"[AUTO-CHECK] Error in initial check: {e}")
            finally:
                loop.close()
        
        # Run in separate thread to avoid event loop conflicts
        check_thread = threading.Thread(target=run_initial_check, daemon=True)
        check_thread.start()
        check_thread.join(timeout=300)  # Wait max 5 minutes
    
    # Create event loop for cron if needed
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Use asyncio timer for more reliable short intervals (< 5 minutes)
    if interval_minutes < 5:
        print(f"[AUTO-CHECK] Using asyncio timer for short interval ({interval_minutes} minutes)")
        
        async def periodic_check():
            """Periodic check using asyncio timer."""
            while True:
                try:
                    await asyncio.sleep(interval_minutes * 60)  # Wait first, then check
                    print(f"[AUTO-CHECK] Timer triggered at {datetime.now()}")
                    await check_pending_accounts(SessionLocal, bot, max_accounts=999999, notify_admin=True)
                    print(f"[AUTO-CHECK] Timer completed at {datetime.now()}")
                except Exception as e:
                    print(f"[AUTO-CHECK] Error in timer check: {e}")
        
        # Start the periodic task
        try:
            # Schedule the task in the existing event loop
            loop.call_soon_threadsafe(asyncio.create_task, periodic_check())
            print(f"[AUTO-CHECK] Started periodic timer (every {interval_minutes} minutes)")
            print(f"[AUTO-CHECK] Next check will be at: {datetime.now() + timedelta(minutes=interval_minutes)}")
        except Exception as e:
            print(f"[AUTO-CHECK] Failed to start periodic timer: {e}")
            # Fallback: try to start in current thread
            try:
                import threading
                def run_periodic():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    new_loop.run_until_complete(periodic_check())
                
                timer_thread = threading.Thread(target=run_periodic, daemon=True)
                timer_thread.start()
                print(f"[AUTO-CHECK] Started periodic timer in separate thread (every {interval_minutes} minutes)")
            except Exception as e2:
                print(f"[AUTO-CHECK] Fallback timer also failed: {e2}")
    
    else:
        # Use aiocron for longer intervals (>= 5 minutes)
        cron_pattern = f"*/{interval_minutes} * * * *"
        print(f"[AUTO-CHECK] Using aiocron with pattern: {cron_pattern}")
        
        @aiocron.crontab(cron_pattern, loop=loop)
        async def auto_check_job():
            """Periodic auto-check job."""
            print(f"[AUTO-CHECK] Cron job triggered at {datetime.now()}")
            try:
                await check_pending_accounts(SessionLocal, bot, max_accounts=999999, notify_admin=True)
                print(f"[AUTO-CHECK] Cron job completed at {datetime.now()}")
            except Exception as e:
                print(f"[AUTO-CHECK] Error in auto-check job: {e}")
        
        print(f"[AUTO-CHECK] Started automatic checker (every {interval_minutes} minutes, checking ALL accounts)")
        print(f"[AUTO-CHECK] Next check will be at: {datetime.now() + timedelta(minutes=interval_minutes)}")
        print(f"[AUTO-CHECK] Cron job registered with pattern: {cron_pattern}")

