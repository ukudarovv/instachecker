"""Test immediate check on startup."""

import asyncio
import sys
import os
import time

# Add project directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'project'))

from config import get_settings
from database import get_engine, get_session_factory, init_db
from auto_checker_scheduler import AutoCheckerScheduler
from services.system_settings import get_auto_check_interval

def test_immediate_check():
    """Test that immediate check runs on startup."""
    
    print("=" * 70)
    print("Testing Immediate Check on Startup")
    print("=" * 70)
    print()
    
    # Initialize
    settings = get_settings()
    engine = get_engine(settings.db_url)
    session_factory = get_session_factory(engine)
    init_db(engine)
    
    with session_factory() as session:
        interval_minutes = get_auto_check_interval(session)
    
    print(f"✅ Interval: {interval_minutes} minutes")
    print()
    
    # Create scheduler with immediate run
    print("Starting scheduler with run_immediately=True...")
    scheduler = AutoCheckerScheduler(
        bot_token=settings.bot_token,
        SessionLocal=session_factory,
        interval_minutes=interval_minutes,
        run_immediately=True,  # Should run immediately!
    )
    
    scheduler.start()
    print()
    
    # Wait for immediate check to complete
    print("Waiting 10 seconds for immediate check...")
    for i in range(10):
        time.sleep(1)
        print(f"  {i+1}/10 seconds...")
    print()
    
    # Stop scheduler
    scheduler.stop()
    
    print("=" * 70)
    print("✅ TEST COMPLETE")
    print("=" * 70)
    print()
    print("Check the output above:")
    print("- You should see '[AUTO-CHECK-SCHEDULER] Running immediate initial check...'")
    print("- You should see '[AUTO-CHECK-SCHEDULER] Starting check at...'")
    print("- You should see '[AUTO-CHECK-SCHEDULER] Check completed at...'")
    print()

if __name__ == "__main__":
    try:
        test_immediate_check()
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

