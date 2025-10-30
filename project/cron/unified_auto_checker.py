"""
Unified Auto Checker - единый поток для всех автопроверок.
Работает в отдельном потоке с собственным event loop.
"""
import asyncio
import threading
from datetime import datetime, date
from typing import Optional, Dict
from sqlalchemy.orm import sessionmaker
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

try:
    from ..models import Account, User
    from ..services.main_checker import check_account_main
    from ..utils.encryptor import OptionalFernet
    from ..config import get_settings
except ImportError:
    from models import Account, User
    from services.main_checker import check_account_main
    from utils.encryptor import OptionalFernet
    from config import get_settings


class UnifiedAutoChecker:
    """
    Единый автопроверщик для всех пользователей.
    Работает в отдельном потоке с собственным event loop и планировщиком.
    """
    
    _instance: Optional['UnifiedAutoChecker'] = None
    _lock = threading.Lock()
    
    def __init__(self, session_factory: sessionmaker, bot=None):
        """
        Initialize unified auto checker.
        
        Args:
            session_factory: SQLAlchemy session factory
            bot: Optional TelegramBot instance
        """
        self.session_factory = session_factory
        self.bot = bot
        self.fernet = OptionalFernet()
        
        # Threading
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._scheduler: Optional[AsyncIOScheduler] = None
        
        # Statistics
        self._total_checks = 0
        self._total_found = 0
        self._total_errors = 0
        self._last_check_time: Optional[datetime] = None
        
        # User-specific intervals (user_id -> interval_minutes)
        self._user_intervals: Dict[int, int] = {}
        
        print("[UNIFIED-AUTO-CHECK] 🚀 Initialized unified auto checker")
    
    @classmethod
    def get_instance(cls) -> Optional['UnifiedAutoChecker']:
        """Get singleton instance."""
        return cls._instance
    
    @classmethod
    def initialize(cls, session_factory: sessionmaker, bot=None) -> 'UnifiedAutoChecker':
        """Initialize singleton instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(session_factory, bot)
        return cls._instance
    
    async def check_user_accounts(self, user_id: int):
        """
        Check all pending accounts for a specific user.
        
        Args:
            user_id: User ID to check
        """
        start_time = datetime.now()
        
        try:
            print(f"\n{'='*80}")
            print(f"[UNIFIED-AUTO-CHECK] 🔍 Checking user {user_id} at {start_time}")
            print(f"{'='*80}\n")
            
            with self.session_factory() as session:
                # Get user
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    print(f"[UNIFIED-AUTO-CHECK] ❌ User {user_id} not found")
                    return
                
                if not user.auto_check_enabled:
                    print(f"[UNIFIED-AUTO-CHECK] ⚠️ Auto-check disabled for user {user_id}")
                    return
                
                # Get pending accounts
                accounts = session.query(Account).filter(
                    Account.user_id == user_id,
                    Account.done == False
                ).all()
                
                if not accounts:
                    print(f"[UNIFIED-AUTO-CHECK] ℹ️ No pending accounts for user {user_id} (@{user.username})")
                    return
                
                print(f"[UNIFIED-AUTO-CHECK] 📋 Found {len(accounts)} pending accounts for @{user.username}")
                print(f"[UNIFIED-AUTO-CHECK] 🔧 Verify mode: {user.verify_mode}")
                
                checked = 0
                found = 0
                not_found = 0
                errors = 0
                
                # Check each account
                for acc in accounts:
                    try:
                        print(f"[UNIFIED-AUTO-CHECK] 🔍 Checking @{acc.account}...")
                        
                        # check_account_main returns (success, message, screenshot_path)
                        success, message, screenshot_path = await check_account_main(
                            username=acc.account,
                            session=session,
                            user_id=user_id
                        )
                        
                        checked += 1
                        
                        if success:
                            found += 1
                            print(f"[UNIFIED-AUTO-CHECK] ✅ @{acc.account} - FOUND! {message}")
                        else:
                            not_found += 1
                            print(f"[UNIFIED-AUTO-CHECK] ⚠️ @{acc.account} - not found: {message}")
                        
                        # Small delay between checks
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        errors += 1
                        print(f"[UNIFIED-AUTO-CHECK] ❌ Error checking @{acc.account}: {e}")
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
                print(f"[UNIFIED-AUTO-CHECK] 📊 Summary for user {user_id} (@{user.username}):")
                print(f"  • Checked: {checked}")
                print(f"  • Found: {found}")
                print(f"  • Not found: {not_found}")
                print(f"  • Errors: {errors}")
                print(f"  • Duration: {duration:.1f}s")
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
                        self.bot.send_message(user_id, message)
                    except Exception as e:
                        print(f"[UNIFIED-AUTO-CHECK] ⚠️ Failed to send notification: {e}")
        
        except Exception as e:
            print(f"[UNIFIED-AUTO-CHECK] ❌ Critical error for user {user_id}: {e}")
            import traceback
            traceback.print_exc()
    
    async def _check_all_users(self):
        """Check all users with enabled auto-check."""
        print(f"\n[UNIFIED-AUTO-CHECK] 🔄 Starting check cycle at {datetime.now()}")
        
        with self.session_factory() as session:
            # Get all active users with auto-check enabled
            users = session.query(User).filter(
                User.is_active == True,
                User.auto_check_enabled == True
            ).all()
            
            if not users:
                print("[UNIFIED-AUTO-CHECK] ℹ️ No users with auto-check enabled")
                return
            
            print(f"[UNIFIED-AUTO-CHECK] 📋 Checking {len(users)} users")
            
            # Check each user sequentially (or in parallel if needed)
            for user in users:
                try:
                    await self.check_user_accounts(user.id)
                except Exception as e:
                    print(f"[UNIFIED-AUTO-CHECK] ❌ Error checking user {user.id}: {e}")
        
        print(f"[UNIFIED-AUTO-CHECK] ✅ Check cycle completed at {datetime.now()}\n")
    
    def _run_in_thread(self):
        """Run scheduler in separate thread with own event loop."""
        print("[UNIFIED-AUTO-CHECK] 🧵 Starting checker thread...")
        
        # Create new event loop for this thread
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        try:
            # Create scheduler
            self._scheduler = AsyncIOScheduler(event_loop=self._loop)
            print("[UNIFIED-AUTO-CHECK] ✅ Scheduler created")
            
            # Add jobs for each user with their own interval
            with self.session_factory() as session:
                users = session.query(User).filter(
                    User.is_active == True,
                    User.auto_check_enabled == True
                ).all()
                
                print(f"[UNIFIED-AUTO-CHECK] 📋 Setting up jobs for {len(users)} users")
                
                for user in users:
                    interval = user.auto_check_interval or 5
                    self._user_intervals[user.id] = interval
                    
                    # Add job for this user
                    self._scheduler.add_job(
                        self.check_user_accounts,
                        trigger=IntervalTrigger(minutes=interval),
                        args=[user.id],
                        id=f'user_{user.id}',
                        name=f'Check User {user.id}',
                        replace_existing=True
                    )
                    print(f"[UNIFIED-AUTO-CHECK] ✅ Job added for user {user.id} (@{user.username}) - every {interval} min")
            
            # Start scheduler
            self._scheduler.start()
            print("[UNIFIED-AUTO-CHECK] ✅ Scheduler started")
            
            # Run initial check for all users
            print("[UNIFIED-AUTO-CHECK] 🔄 Running initial check for all users...")
            self._loop.run_until_complete(self._check_all_users())
            
            # Keep the loop running
            print("[UNIFIED-AUTO-CHECK] 🔄 Entering main loop...")
            while not self._stop_event.is_set():
                self._loop.run_until_complete(asyncio.sleep(1))
            
        except Exception as e:
            print(f"[UNIFIED-AUTO-CHECK] ❌ Error in checker thread: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Cleanup
            if self._scheduler:
                self._scheduler.shutdown(wait=False)
            if self._loop:
                self._loop.close()
            print("[UNIFIED-AUTO-CHECK] 🛑 Checker thread stopped")
    
    def start(self):
        """Start the unified auto checker."""
        if self._thread and self._thread.is_alive():
            print("[UNIFIED-AUTO-CHECK] ⚠️ Checker thread already running")
            return
        
        print("\n" + "="*80)
        print("[UNIFIED-AUTO-CHECK] 🚀 Starting unified auto checker...")
        print("="*80 + "\n")
        
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_in_thread,
            name="UnifiedAutoChecker",
            daemon=True
        )
        self._thread.start()
        
        print("[UNIFIED-AUTO-CHECK] ✅ Checker thread started")
    
    def stop(self):
        """Stop the unified auto checker."""
        print("[UNIFIED-AUTO-CHECK] 🛑 Stopping unified auto checker...")
        self._stop_event.set()
        
        if self._thread:
            self._thread.join(timeout=5)
        
        print("[UNIFIED-AUTO-CHECK] ✅ Unified auto checker stopped")
    
    def get_stats(self) -> dict:
        """Get checker statistics."""
        return {
            "total_checks": self._total_checks,
            "total_found": self._total_found,
            "total_errors": self._total_errors,
            "last_check_time": self._last_check_time,
            "is_running": self._thread is not None and self._thread.is_alive(),
            "user_count": len(self._user_intervals)
        }
    
    def add_user(self, user_id: int, interval_minutes: int):
        """
        Add or update user checker job.
        
        Args:
            user_id: User ID
            interval_minutes: Check interval in minutes
        """
        if not self._scheduler:
            print(f"[UNIFIED-AUTO-CHECK] ⚠️ Scheduler not running, cannot add user {user_id}")
            return
        
        self._user_intervals[user_id] = interval_minutes
        
        # Add/update job in the scheduler's loop
        if self._loop:
            asyncio.run_coroutine_threadsafe(
                self._add_user_job(user_id, interval_minutes),
                self._loop
            )
    
    async def _add_user_job(self, user_id: int, interval_minutes: int):
        """Add user job (must run in scheduler's loop)."""
        job_id = f'user_{user_id}'
        
        # Remove existing job if any
        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)
        
        # Add new job
        self._scheduler.add_job(
            self.check_user_accounts,
            trigger=IntervalTrigger(minutes=interval_minutes),
            args=[user_id],
            id=job_id,
            name=f'Check User {user_id}',
            replace_existing=True
        )
        print(f"[UNIFIED-AUTO-CHECK] ✅ Job updated for user {user_id} - every {interval_minutes} min")
    
    def remove_user(self, user_id: int):
        """
        Remove user checker job.
        
        Args:
            user_id: User ID
        """
        if user_id in self._user_intervals:
            del self._user_intervals[user_id]
        
        if self._scheduler:
            job_id = f'user_{user_id}'
            try:
                self._scheduler.remove_job(job_id)
                print(f"[UNIFIED-AUTO-CHECK] ✅ Job removed for user {user_id}")
            except:
                pass


def get_unified_checker() -> Optional[UnifiedAutoChecker]:
    """Get the unified auto checker instance."""
    return UnifiedAutoChecker.get_instance()

