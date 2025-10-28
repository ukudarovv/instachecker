"""
Optimized auto-checker using APScheduler for reliable interval-based checking.

Features:
- Runs in separate thread with own event loop (non-blocking)
- Uses APScheduler for reliable scheduling
- Prevents overlapping runs (max_instances=1)
- Combines missed runs (coalesce=True)
- Optimized event loop handling
- Thread-safe operation
"""

import asyncio
import threading
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import sessionmaker
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

try:
    from .cron.auto_checker import check_pending_accounts
    from .utils.async_bot_wrapper import AsyncBotWrapper
except ImportError:
    from cron.auto_checker import check_pending_accounts
    from utils.async_bot_wrapper import AsyncBotWrapper


class AutoCheckerScheduler:
    """
    Automatic account checker using APScheduler.
    Runs checks at specified intervals using AsyncIOScheduler.
    """
    
    def __init__(
        self,
        bot_token: str,
        SessionLocal: sessionmaker,
        interval_minutes: int = 5,
        run_immediately: bool = True,
    ):
        """
        Initialize auto-checker scheduler.
        
        Args:
            bot_token: Telegram bot token
            SessionLocal: SQLAlchemy session factory
            interval_minutes: Check interval in minutes (default: 5)
            run_immediately: Run initial check on startup (default: True)
        """
        self._bot_token = bot_token
        self._SessionLocal = SessionLocal
        self._interval_minutes = interval_minutes
        self._run_immediately = run_immediately
        
        # Initialize scheduler
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._stop_event = threading.Event()
        
        print(f"[AUTO-CHECK-SCHEDULER] Initialized (interval: {interval_minutes} minutes)")
    
    async def _check_job(self):
        """Job that runs on schedule."""
        try:
            print(f"[AUTO-CHECK-SCHEDULER] Starting check at {datetime.now()}")
            
            # Create bot wrapper for this check
            async_bot = AsyncBotWrapper(self._bot_token)
            
            await check_pending_accounts(
                SessionLocal=self._SessionLocal,
                bot=async_bot,
                max_accounts=999999,
                notify_admin=True
            )
            
            print(f"[AUTO-CHECK-SCHEDULER] Check completed at {datetime.now()}")
            
        except Exception as e:
            print(f"[AUTO-CHECK-SCHEDULER] Error during check: {e}")
            import traceback
            traceback.print_exc()
    
    def _run_scheduler(self):
        """Run scheduler in separate thread with its own event loop."""
        # Create new event loop for this thread
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        try:
            # Create scheduler
            self._scheduler = AsyncIOScheduler()
            
            # Add job with interval trigger
            self._scheduler.add_job(
                self._check_job,
                trigger=IntervalTrigger(minutes=self._interval_minutes),
                id='auto_check',
                name='Instagram Account Auto-Check',
                replace_existing=True,
                max_instances=1,  # Prevent overlapping runs
                coalesce=True,    # Combine missed runs into one
            )
            
            # Start scheduler
            self._scheduler.start()
            
            print(f"[AUTO-CHECK-SCHEDULER] Scheduler started (every {self._interval_minutes} minutes)")
            if self._scheduler.get_jobs():
                print(f"[AUTO-CHECK-SCHEDULER] Next check scheduled at: {self._scheduler.get_jobs()[0].next_run_time}")
            
            # Run immediate check if requested
            if self._run_immediately:
                print("[AUTO-CHECK-SCHEDULER] Running immediate initial check...")
                self._loop.run_until_complete(self._check_job())
            
            # Run event loop until stop event is set
            # Use asyncio.run() for better performance
            try:
                self._loop.run_forever()
            except KeyboardInterrupt:
                pass
                
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
    
    def get_next_run_time(self) -> Optional[datetime]:
        """Get next scheduled run time."""
        if self._scheduler and self._scheduler.running:
            jobs = self._scheduler.get_jobs()
            if jobs:
                return jobs[0].next_run_time
        return None
    
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._scheduler is not None and self._scheduler.running

