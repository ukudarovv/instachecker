"""
Daily expiry notification scheduler.
Sends notifications at 10:00 AM every day.
"""

import asyncio
import threading
from datetime import datetime, time
from typing import Optional
from sqlalchemy.orm import sessionmaker
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

try:
    from .services.expiry_notifications import check_and_send_expiry_notifications
    from .utils.async_bot_wrapper import AsyncBotWrapper
except ImportError:
    from services.expiry_notifications import check_and_send_expiry_notifications
    from utils.async_bot_wrapper import AsyncBotWrapper


class ExpiryNotificationScheduler:
    """
    Daily expiry notification scheduler using APScheduler.
    Sends notifications at 10:00 AM every day.
    """
    
    def __init__(
        self,
        bot_token: str,
        SessionLocal: sessionmaker,
        notification_time: time = time(10, 0),  # 10:00 AM
    ):
        """
        Initialize expiry notification scheduler.
        
        Args:
            bot_token: Telegram bot token
            SessionLocal: SQLAlchemy session factory
            notification_time: Time to send notifications (default: 10:00 AM)
        """
        self._bot_token = bot_token
        self._SessionLocal = SessionLocal
        self._notification_time = notification_time
        
        # Initialize scheduler
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._stop_event = threading.Event()
        
        print(f"[EXPIRY-SCHEDULER] Initialized (notification time: {notification_time.strftime('%H:%M')})")
    
    async def _notification_job(self):
        """Job that runs daily at specified time."""
        try:
            print(f"[EXPIRY-SCHEDULER] Starting expiry check at {datetime.now()}")
            
            # Create bot wrapper for this check
            async_bot = AsyncBotWrapper(self._bot_token)
            
            await check_and_send_expiry_notifications(
                SessionLocal=self._SessionLocal,
                bot=async_bot
            )
            
            print(f"[EXPIRY-SCHEDULER] Expiry check completed at {datetime.now()}")
            
        except Exception as e:
            print(f"[EXPIRY-SCHEDULER] Error during expiry check: {e}")
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
            
            # Add job with cron trigger (daily at specified time)
            self._scheduler.add_job(
                self._notification_job,
                trigger=CronTrigger(
                    hour=self._notification_time.hour,
                    minute=self._notification_time.minute,
                    second=0
                ),
                id='expiry_notifications',
                name='Daily Expiry Notifications',
                replace_existing=True,
                max_instances=1,  # Prevent overlapping runs
                coalesce=True,    # Combine missed runs into one
            )
            
            # Start scheduler
            self._scheduler.start()
            
            print(f"[EXPIRY-SCHEDULER] Scheduler started (daily at {self._notification_time.strftime('%H:%M')})")
            if self._scheduler.get_jobs():
                next_run = self._scheduler.get_jobs()[0].next_run_time
                print(f"[EXPIRY-SCHEDULER] Next notification scheduled at: {next_run}")
            
            # Run event loop until stop event is set
            while not self._stop_event.is_set():
                self._loop.run_until_complete(asyncio.sleep(1))
                
        except Exception as e:
            print(f"[EXPIRY-SCHEDULER] Error in scheduler thread: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self._scheduler and self._scheduler.running:
                self._scheduler.shutdown(wait=False)
            self._loop.close()
    
    def start(self):
        """Start the scheduler in a separate thread."""
        if self._thread and self._thread.is_alive():
            print("[EXPIRY-SCHEDULER] Scheduler already running")
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_scheduler, name="ExpiryScheduler", daemon=True)
        self._thread.start()
        print("[EXPIRY-SCHEDULER] Scheduler thread started")
    
    def stop(self):
        """Stop the scheduler."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        print("[EXPIRY-SCHEDULER] Scheduler stopped")
    
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

