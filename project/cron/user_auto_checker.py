"""
User-specific auto checker with individual scheduling intervals.
Each user has their own independent checker that runs at their configured interval.
"""
import asyncio
from datetime import datetime, timedelta, date
from typing import Optional
from sqlalchemy.orm import sessionmaker
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

try:
    from ..models import Account, User
    from ..services.main_checker import check_account_main
    from ..services.system_settings import get_global_verify_mode
    from ..utils.encryptor import OptionalFernet
    from ..config import get_settings
except ImportError:
    from models import Account, User
    from services.main_checker import check_account_main
    from services.system_settings import get_global_verify_mode
    from utils.encryptor import OptionalFernet
    from config import get_settings


class UserAutoChecker:
    """
    Auto checker for a specific user.
    Runs independently with user's configured interval.
    """
    
    def __init__(
        self, 
        user_id: int,
        session_factory: sessionmaker,
        bot=None,
        fernet: Optional[OptionalFernet] = None
    ):
        """
        Initialize user auto checker.
        
        Args:
            user_id: User ID
            session_factory: SQLAlchemy session factory
            bot: Optional TelegramBot instance
            fernet: Optional Fernet encryptor
        """
        self.user_id = user_id
        self.session_factory = session_factory
        self.bot = bot
        self.fernet = fernet or OptionalFernet()
        
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.job_id = f"auto_check_user_{user_id}"
        self._is_running = False
        self._last_check_time: Optional[datetime] = None
        self._total_checks = 0
        self._total_found = 0
        self._total_errors = 0
        self._pending_tasks = set()  # Отслеживаем pending задачи
        
        print(f"[USER-AUTO-CHECK] 🧵 Initialized checker for user {user_id}")
    
    async def check_user_accounts(self):
        """Check all pending accounts for this user."""
        print(f"[USER-AUTO-CHECK] 🎯 check_user_accounts() called for user {self.user_id}")
        
        if self._is_running:
            print(f"[USER-AUTO-CHECK] ⚠️ Check already running for user {self.user_id}, skipping...")
            return
        
        self._is_running = True
        start_time = datetime.now()
        
        try:
            print(f"\n{'='*80}")
            print(f"[USER-AUTO-CHECK] 🔍 Starting check for user {self.user_id} at {start_time}")
            print(f"{'='*80}\n")
            
            with self.session_factory() as session:
                # Get user info
                user = session.query(User).filter(User.id == self.user_id).first()
                if not user:
                    print(f"[USER-AUTO-CHECK] ❌ User {self.user_id} not found!")
                    return
                
                if not user.auto_check_enabled:
                    print(f"[USER-AUTO-CHECK] ⚠️ Auto-check disabled for user {self.user_id}")
                    return
                
                # Get pending accounts (done = False)
                accounts = session.query(Account).filter(
                    Account.user_id == self.user_id,
                    Account.done == False
                ).all()
                
                if not accounts:
                    print(f"[USER-AUTO-CHECK] ℹ️ No pending accounts for user {self.user_id} (@{user.username})")
                    return
                
                print(f"[USER-AUTO-CHECK] 📋 Found {len(accounts)} pending accounts for @{user.username}")
                print(f"[USER-AUTO-CHECK] 🔧 Verify mode: {user.verify_mode}")
                print(f"[USER-AUTO-CHECK] ⏱️ Interval: {user.auto_check_interval} minutes\n")
                
                checked = 0
                found = 0
                not_found = 0
                errors = 0
                
                # Check each account
                for acc in accounts:
                    try:
                        print(f"[USER-AUTO-CHECK] 🔍 Checking @{acc.account}...")
                        
                        result = await check_account_main(
                            session=session,
                            user_id=self.user_id,
                            username=acc.account,
                            verify_mode=user.verify_mode,
                            bot=self.bot,
                            send_notification=True
                        )
                        
                        checked += 1
                        
                        if result.get("exists"):
                            found += 1
                            print(f"[USER-AUTO-CHECK] ✅ @{acc.account} - FOUND!")
                        elif result.get("error"):
                            errors += 1
                            print(f"[USER-AUTO-CHECK] ❌ @{acc.account} - ERROR: {result.get('error')}")
                        else:
                            not_found += 1
                            print(f"[USER-AUTO-CHECK] ⚠️ @{acc.account} - not found")
                        
                        # Small delay between checks
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        errors += 1
                        print(f"[USER-AUTO-CHECK] ❌ Error checking @{acc.account}: {e}")
                        import traceback
                        traceback.print_exc()
                
                # Update statistics
                self._total_checks += checked
                self._total_found += found
                self._total_errors += errors
                self._last_check_time = datetime.now()
                
                # Print summary
                duration = (datetime.now() - start_time).total_seconds()
                print(f"\n{'='*80}")
                print(f"[USER-AUTO-CHECK] 📊 Summary for user {self.user_id} (@{user.username}):")
                print(f"  • Checked: {checked}")
                print(f"  • Found: {found}")
                print(f"  • Not found: {not_found}")
                print(f"  • Errors: {errors}")
                print(f"  • Duration: {duration:.1f}s")
                print(f"  • Total checks (all time): {self._total_checks}")
                print(f"  • Total found (all time): {self._total_found}")
                print(f"{'='*80}\n")
                
                # Notify user if any accounts were found
                if found > 0 and self.bot:
                    try:
                        message = (
                            f"🎉 <b>Автопроверка завершена!</b>\n\n"
                            f"✅ Найдено активных аккаунтов: {found}\n"
                            f"📋 Проверено всего: {checked}\n"
                            f"⏱️ Время: {duration:.1f}с"
                        )
                        self.bot.send_message(self.user_id, message)
                    except Exception as e:
                        print(f"[USER-AUTO-CHECK] ⚠️ Failed to send notification: {e}")
        
        except Exception as e:
            print(f"[USER-AUTO-CHECK] ❌ Critical error in check for user {self.user_id}: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self._is_running = False
    
    def start(self, interval_minutes: int, run_immediately: bool = False):
        """
        Start the auto checker for this user.
        
        Args:
            interval_minutes: Check interval in minutes
            run_immediately: Run check immediately on start
        """
        if self.scheduler:
            print(f"[USER-AUTO-CHECK] ⚠️ Scheduler already running for user {self.user_id}")
            return
        
        print(f"[USER-AUTO-CHECK] 🚀 Starting scheduler for user {self.user_id} (every {interval_minutes} min)")
        
        # Create scheduler with explicit event loop
        try:
            loop = asyncio.get_running_loop()
            self.scheduler = AsyncIOScheduler(event_loop=loop)
            print(f"[USER-AUTO-CHECK] ✅ Scheduler created with event loop for user {self.user_id}")
        except RuntimeError:
            # Fallback if no loop is running
            self.scheduler = AsyncIOScheduler()
            print(f"[USER-AUTO-CHECK] ⚠️ Scheduler created without explicit loop for user {self.user_id}")
        
        # Add job
        self.scheduler.add_job(
            self.check_user_accounts,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id=self.job_id,
            name=f'Auto Check User {self.user_id}',
            replace_existing=True
        )
        
        # Start scheduler
        self.scheduler.start()
        print(f"[USER-AUTO-CHECK] ✅ Scheduler.start() called for user {self.user_id}")
        
        next_run = datetime.now() + timedelta(minutes=interval_minutes)
        print(f"[USER-AUTO-CHECK] ✅ Scheduler started for user {self.user_id}")
        print(f"[USER-AUTO-CHECK] ⏰ Next check: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run immediately if requested
        if run_immediately:
            print(f"[USER-AUTO-CHECK] 🔄 Running initial check for user {self.user_id}...")
            try:
                # Запускаем задачу сразу через asyncio
                # Используем try-except для обработки разных ситуаций с event loop
                try:
                    loop = asyncio.get_running_loop()
                    # Если loop уже запущен, создаем задачу и сохраняем ссылку
                    task = loop.create_task(self.check_user_accounts())
                    self._pending_tasks.add(task)
                    # Удаляем задачу из набора после завершения
                    task.add_done_callback(lambda t: self._pending_tasks.discard(t))
                    print(f"[USER-AUTO-CHECK] ✅ Initial check task created for user {self.user_id}")
                except RuntimeError:
                    # Если loop не запущен, используем планировщик
                    from apscheduler.triggers.date import DateTrigger
                    self.scheduler.add_job(
                        self.check_user_accounts,
                        trigger=DateTrigger(run_date=datetime.now()),
                        id=f"{self.job_id}_initial",
                        name=f'Initial Check User {self.user_id}',
                        replace_existing=True
                    )
                    print(f"[USER-AUTO-CHECK] ✅ Initial check scheduled via scheduler for user {self.user_id}")
            except Exception as e:
                print(f"[USER-AUTO-CHECK] ❌ Error scheduling initial check: {e}")
                import traceback
                traceback.print_exc()
    
    def stop(self):
        """Stop the auto checker for this user."""
        if not self.scheduler:
            return
        
        print(f"[USER-AUTO-CHECK] 🛑 Stopping scheduler for user {self.user_id}")
        
        try:
            self.scheduler.remove_job(self.job_id)
            self.scheduler.shutdown(wait=False)
            self.scheduler = None
            print(f"[USER-AUTO-CHECK] ✅ Scheduler stopped for user {self.user_id}")
        except Exception as e:
            print(f"[USER-AUTO-CHECK] ⚠️ Error stopping scheduler: {e}")
    
    def update_interval(self, new_interval_minutes: int):
        """
        Update the check interval for this user.
        
        Args:
            new_interval_minutes: New interval in minutes
        """
        if not self.scheduler:
            print(f"[USER-AUTO-CHECK] ⚠️ Scheduler not running for user {self.user_id}")
            return
        
        print(f"[USER-AUTO-CHECK] 🔄 Updating interval for user {self.user_id}: {new_interval_minutes} min")
        
        try:
            # Remove old job
            self.scheduler.remove_job(self.job_id)
            
            # Add new job with updated interval
            self.scheduler.add_job(
                self.check_user_accounts,
                trigger=IntervalTrigger(minutes=new_interval_minutes),
                id=self.job_id,
                name=f'Auto Check User {self.user_id}',
                replace_existing=True
            )
            
            next_run = datetime.now() + timedelta(minutes=new_interval_minutes)
            print(f"[USER-AUTO-CHECK] ✅ Interval updated for user {self.user_id}")
            print(f"[USER-AUTO-CHECK] ⏰ Next check: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            print(f"[USER-AUTO-CHECK] ❌ Error updating interval: {e}")
    
    def get_stats(self) -> dict:
        """Get statistics for this user's auto checker."""
        return {
            "user_id": self.user_id,
            "is_running": self.scheduler is not None,
            "is_checking": self._is_running,
            "last_check_time": self._last_check_time,
            "total_checks": self._total_checks,
            "total_found": self._total_found,
            "total_errors": self._total_errors
        }

