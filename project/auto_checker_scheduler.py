"""
Auto-checker using APScheduler for reliable interval-based checking.
This replaces the threading-based approach with a more robust scheduler.
"""

import asyncio
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
        
        # Create async bot wrapper
        self._async_bot = AsyncBotWrapper(bot_token)
        
        # Initialize scheduler
        self._scheduler: Optional[AsyncIOScheduler] = None
        
        print(f"[AUTO-CHECK-SCHEDULER] Initialized (interval: {interval_minutes} minutes)")
    
    async def _check_job(self):
        """Job that runs on schedule."""
        try:
            print(f"[AUTO-CHECK-SCHEDULER] Starting check at {datetime.now()}")
            
            await check_pending_accounts(
                SessionLocal=self._SessionLocal,
                bot=self._async_bot,
                max_accounts=999999,
                notify_admin=True
            )
            
            print(f"[AUTO-CHECK-SCHEDULER] Check completed at {datetime.now()}")
            
        except Exception as e:
            print(f"[AUTO-CHECK-SCHEDULER] Error during check: {e}")
            import traceback
            traceback.print_exc()
    
    def start(self):
        """Start the scheduler."""
        if self._scheduler and self._scheduler.running:
            print("[AUTO-CHECK-SCHEDULER] Scheduler already running")
            return
        
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
        print(f"[AUTO-CHECK-SCHEDULER] Next check scheduled at: {self._scheduler.get_jobs()[0].next_run_time}")
        
        # Run immediate check if requested
        if self._run_immediately:
            print("[AUTO-CHECK-SCHEDULER] Running immediate initial check...")
            # Schedule immediate execution using asyncio
            loop = asyncio.get_event_loop()
            loop.create_task(self._check_job())
    
    def stop(self):
        """Stop the scheduler."""
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=False)
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

