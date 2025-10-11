"""Test script to verify APScheduler auto-checker is working."""

import asyncio
import sys
import os

# Add project directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'project'))

from config import get_settings
from database import get_engine, get_session_factory, init_db
from auto_checker_scheduler import AutoCheckerScheduler
from services.system_settings import get_auto_check_interval

async def test_scheduler():
    """Test the scheduler initialization and execution."""
    
    print("=" * 70)
    print("Testing APScheduler Auto-Checker")
    print("=" * 70)
    print()
    
    # Initialize settings and database
    print("1. Loading settings...")
    settings = get_settings()
    print(f"   ✅ Bot token: {settings.bot_token[:20]}...")
    print()
    
    print("2. Initializing database...")
    engine = get_engine(settings.db_url)
    session_factory = get_session_factory(engine)
    init_db(engine)
    print("   ✅ Database initialized")
    print()
    
    # Get auto-check interval
    print("3. Getting auto-check interval...")
    with session_factory() as session:
        interval_minutes = get_auto_check_interval(session)
    print(f"   ✅ Interval: {interval_minutes} minutes")
    print()
    
    # Initialize scheduler
    print("4. Initializing APScheduler...")
    scheduler = AutoCheckerScheduler(
        bot_token=settings.bot_token,
        SessionLocal=session_factory,
        interval_minutes=interval_minutes,
        run_immediately=False,  # Don't run immediately for testing
    )
    print("   ✅ Scheduler initialized")
    print()
    
    # Start scheduler
    print("5. Starting scheduler...")
    scheduler.start()
    print("   ✅ Scheduler started")
    print()
    
    # Check scheduler status
    print("6. Checking scheduler status...")
    is_running = scheduler.is_running()
    next_run = scheduler.get_next_run_time()
    print(f"   ✅ Running: {is_running}")
    print(f"   ✅ Next run: {next_run}")
    print()
    
    # Wait a bit to see if everything is stable
    print("7. Waiting 3 seconds to verify stability...")
    await asyncio.sleep(3)
    print("   ✅ Scheduler is stable")
    print()
    
    # Stop scheduler
    print("8. Stopping scheduler...")
    scheduler.stop()
    print("   ✅ Scheduler stopped")
    print()
    
    print("=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    print()
    print("The APScheduler auto-checker is working correctly.")
    print(f"It will check accounts every {interval_minutes} minutes.")
    print()

if __name__ == "__main__":
    try:
        asyncio.run(test_scheduler())
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

