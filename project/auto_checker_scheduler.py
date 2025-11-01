"""
Auto-checker using APScheduler for reliable interval-based checking.
This creates separate scheduler jobs for each user with their own intervals.
"""

import asyncio
import threading
from datetime import datetime
from typing import Optional, Dict
from sqlalchemy.orm import sessionmaker
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

try:
    from .cron.auto_checker import check_user_pending_accounts
    from .cron.auto_checker_optimized import check_user_accounts_optimized
    from .utils.async_bot_wrapper import AsyncBotWrapper
    from .utils.encryptor import OptionalFernet
    from .config import get_settings
    from .models import User, Account
except ImportError:
    from cron.auto_checker import check_user_pending_accounts
    from cron.auto_checker_optimized import check_user_accounts_optimized
    from utils.async_bot_wrapper import AsyncBotWrapper
    from utils.encryptor import OptionalFernet
    from config import get_settings
    from models import User, Account


class AutoCheckerScheduler:
    """
    Automatic account checker using APScheduler.
    Creates separate scheduler jobs for each user with their individual intervals.
    """
    
    def __init__(
        self,
        bot_token: str,
        SessionLocal: sessionmaker,
        interval_minutes: int = 5,  # Legacy: not used anymore, each user has their own interval
        run_immediately: bool = True,
    ):
        """
        Initialize auto-checker scheduler.
        
        Args:
            bot_token: Telegram bot token
            SessionLocal: SQLAlchemy session factory
            interval_minutes: Legacy parameter (not used, each user has their own interval)
            run_immediately: Run initial check on startup (default: True)
        """
        self._bot_token = bot_token
        self._SessionLocal = SessionLocal
        self._run_immediately = run_immediately
        
        # Initialize scheduler
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._stop_event = threading.Event()
        
        # Track user jobs: {user_id: job_id}
        self._user_jobs: Dict[int, str] = {}
        
        print(f"[AUTO-CHECK-SCHEDULER] Initialized (per-user intervals)")
    
    async def _check_user_job(self, user_id: int):
        """OPTIMIZED: Job that runs on schedule for a specific user with parallel checking."""
        try:
            print(f"[AUTO-CHECK-SCHEDULER-USER-{user_id}] 🚀 Starting OPTIMIZED check at {datetime.now()}")
            
            # Get settings and fernet
            settings = get_settings()
            fernet = OptionalFernet(settings.encryption_key)
            
            # Create bot wrapper for this check
            async_bot = AsyncBotWrapper(self._bot_token)
            
            # Get pending accounts for this user
            with self._SessionLocal() as session:
                user = session.query(User).get(user_id)
                if not user or not user.auto_check_enabled:
                    print(f"[AUTO-CHECK-SCHEDULER-USER-{user_id}] User not found or auto-check disabled")
                    return
                
                pending_accounts = session.query(Account).filter(
                    Account.user_id == user_id,
                    Account.done == False
                ).order_by(Account.from_date.asc()).all()
                
                if not pending_accounts:
                    print(f"[AUTO-CHECK-SCHEDULER-USER-{user_id}] No pending accounts")
                    return
            
            # Use optimized parallel checker (batch size 3 for balance between speed and resources)
            result = await check_user_accounts_optimized(
                user_id=user_id,
                user_accounts=pending_accounts,
                SessionLocal=self._SessionLocal,
                fernet=fernet,
                bot=async_bot,
                batch_size=3  # Check 3 accounts in parallel
            )
            
            # Send traffic report to admins
            if result and result.get('traffic_stats'):
                try:
                    from .cron.auto_checker import send_traffic_report_to_admins
                except ImportError:
                    from cron.auto_checker import send_traffic_report_to_admins
                
                await send_traffic_report_to_admins(
                    SessionLocal=self._SessionLocal,
                    bot=async_bot,
                    user_id=user_id,
                    traffic_stats=result['traffic_stats']
                )
            
            print(f"[AUTO-CHECK-SCHEDULER-USER-{user_id}] ✅ Check completed at {datetime.now()}")
            
        except Exception as e:
            print(f"[AUTO-CHECK-SCHEDULER-USER-{user_id}] ❌ Error during check: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_and_schedule_users(self):
        """Load all users with autocheck enabled and schedule their jobs."""
        with self._SessionLocal() as session:
            # Get all active users with autocheck enabled
            users = session.query(User).filter(
                User.is_active == True,
                User.auto_check_enabled == True
            ).all()
            
            print(f"[AUTO-CHECK-SCHEDULER] Found {len(users)} users with autocheck enabled")
            
            for user in users:
                interval = user.auto_check_interval or 5  # Default to 5 minutes if not set
                job_id = f"user_check_{user.id}"
                user_id = user.id  # Capture user_id in local variable to avoid closure issue
                
                # Remove existing job if it exists
                if job_id in self._user_jobs.values():
                    try:
                        self._scheduler.remove_job(job_id)
                    except:
                        pass
                
                # Create async wrapper function factory to properly capture user_id
                def make_user_check_job(uid):
                    async def user_check_job():
                        await self._check_user_job(uid)
                    return user_check_job
                
                # Add job with user's specific interval
                self._scheduler.add_job(
                    make_user_check_job(user_id),
                    trigger=IntervalTrigger(minutes=interval),
                    id=job_id,
                    name=f'User {user_id} Auto-Check ({interval} min)',
                    replace_existing=True,
                    max_instances=1,  # Prevent overlapping runs
                    coalesce=True,    # Combine missed runs into one
                )
                
                self._user_jobs[user_id] = job_id
                print(f"[AUTO-CHECK-SCHEDULER] ✅ Scheduled user {user_id} (@{user.username}) - interval: {interval} minutes")
    
    def _run_scheduler(self):
        """Run scheduler in separate thread with its own event loop."""
        # Create new event loop for this thread
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        try:
            # Create scheduler
            self._scheduler = AsyncIOScheduler()
            
            # Load users and schedule their jobs
            self._load_and_schedule_users()
            
            # Start scheduler
            self._scheduler.start()
            
            print(f"[AUTO-CHECK-SCHEDULER] Scheduler started with {len(self._user_jobs)} user jobs")
            
            # Run immediate check if requested
            if self._run_immediately:
                print("[AUTO-CHECK-SCHEDULER] Running immediate initial checks...")
                # Run initial check for all users
                tasks = []
                for user_id in self._user_jobs.keys():
                    tasks.append(self._check_user_job(user_id))
                
                if tasks:
                    self._loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
            
            # Run event loop until stop event is set
            while not self._stop_event.is_set():
                self._loop.run_until_complete(asyncio.sleep(1))
                
        except Exception as e:
            print(f"[AUTO-CHECK-SCHEDULER] Error in scheduler thread: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self._scheduler and self._scheduler.running:
                self._scheduler.shutdown(wait=False)
            self._loop.close()
    
    def start(self):
        """Start the scheduler in a separate thread."""
        if self._thread and self._thread.is_alive():
            print("[AUTO-CHECK-SCHEDULER] Scheduler already running")
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_scheduler, name="APScheduler", daemon=True)
        self._thread.start()
        print("[AUTO-CHECK-SCHEDULER] Scheduler thread started")
    
    def stop(self):
        """Stop the scheduler."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        print("[AUTO-CHECK-SCHEDULER] Scheduler stopped")
    
    def reload_users(self):
        """Reload users and update scheduler jobs. Call this when users are added/removed or intervals change."""
        if self._scheduler and self._scheduler.running and self._loop:
            print("[AUTO-CHECK-SCHEDULER] Reloading users and updating jobs...")
            # Schedule reload in the event loop thread-safe way
            def reload():
                try:
                    self._load_and_schedule_users()
                except Exception as e:
                    print(f"[AUTO-CHECK-SCHEDULER] Error reloading users: {e}")
            
            # Schedule in the event loop
            if self._loop.is_running():
                self._loop.call_soon_threadsafe(reload)
            else:
                # If loop is not running, call directly (shouldn't happen normally)
                reload()
    
    def get_next_run_time(self, user_id: Optional[int] = None) -> Optional[datetime]:
        """Get next scheduled run time for a user or all users."""
        if not self._scheduler or not self._scheduler.running:
            return None
        
        if user_id:
            # Get next run time for specific user
            job_id = self._user_jobs.get(user_id)
            if job_id:
                job = self._scheduler.get_job(job_id)
                if job:
                    return job.next_run_time
        else:
            # Get earliest next run time across all users
            jobs = self._scheduler.get_jobs()
            if jobs:
                next_times = [job.next_run_time for job in jobs if job.next_run_time]
                if next_times:
                    return min(next_times)
        
        return None
    
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._scheduler is not None and self._scheduler.running
