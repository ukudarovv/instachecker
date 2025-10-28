"""Scheduled background tasks."""

import aiocron
from datetime import datetime, date
from sqlalchemy.orm import sessionmaker

try:
    from ..models import APIKey
    from ..services.system_settings import get_auto_check_interval
    from ..auto_checker_scheduler import AutoCheckerScheduler
except ImportError:
    from models import APIKey
    from services.system_settings import get_auto_check_interval
    from auto_checker_scheduler import AutoCheckerScheduler


def start_cron(SessionLocal: sessionmaker, bot=None, auto_check_interval: int = None):
    """
    Start cron jobs for background tasks.
    
    Args:
        SessionLocal: SQLAlchemy session factory
        bot: Optional TelegramBot instance for notifications
        auto_check_interval: Auto-check interval in minutes (optional, reads from DB if not provided)
    """
    
    # Get interval from database or use provided value or default
    if auto_check_interval is None:
        with SessionLocal() as s:
            auto_check_interval = get_auto_check_interval(s)
    
    # Reset API counters daily at 00:01 system time
    @aiocron.crontab("1 0 * * *")
    async def reset_api_counters():
        """Reset API key usage counters daily."""
        with SessionLocal() as s:
            keys = s.query(APIKey).all()
            for k in keys:
                k.qty_req = 0
                k.ref_date = datetime.utcnow()
            s.commit()
        print(f"[CRON] Reset {len(keys)} API key counters at {datetime.now()}")
    
    # Note: Auto-checker is now handled by AutoCheckerScheduler in main bot.py
    # This function only handles other cron jobs like API counter reset
    print(f"[CRON] Started cron jobs (API reset daily at 00:01)")
    print(f"[CRON] Auto-checker is handled by AutoCheckerScheduler (every {auto_check_interval} minutes)")

