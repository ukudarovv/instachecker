#!/usr/bin/env python3
"""Test unified auto checker."""

import sys
import os
import asyncio
import time

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from project.database import get_engine, get_session_factory
from project.cron.unified_auto_checker import UnifiedAutoChecker

def test_unified_checker():
    """Test the unified auto checker."""
    print("="*80)
    print("🧪 TESTING UNIFIED AUTO CHECKER")
    print("="*80)
    
    # Load env
    load_dotenv()
    
    # Create session
    db_url = os.getenv("DB_URL", "sqlite:///bot.db")
    engine = get_engine(db_url)
    session_factory = get_session_factory(engine)
    
    # Initialize checker
    checker = UnifiedAutoChecker.initialize(
        session_factory=session_factory,
        bot=None  # No bot for testing
    )
    
    # Start checker
    checker.start()
    
    # Wait a bit to see if it works
    print("\n⏳ Waiting 30 seconds to observe checker behavior...")
    print("Press Ctrl+C to stop\n")
    
    try:
        for i in range(30):
            time.sleep(1)
            if i % 10 == 0:
                stats = checker.get_stats()
                print(f"\n📊 Stats after {i}s:")
                print(f"  • Total checks: {stats['total_checks']}")
                print(f"  • Total found: {stats['total_found']}")
                print(f"  • Total errors: {stats['total_errors']}")
                print(f"  • Is running: {stats['is_running']}")
                print(f"  • Users: {stats['user_count']}\n")
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user")
    
    # Stop checker
    print("\n🛑 Stopping checker...")
    checker.stop()
    
    # Final stats
    stats = checker.get_stats()
    print("\n" + "="*80)
    print("📊 FINAL STATS:")
    print(f"  • Total checks: {stats['total_checks']}")
    print(f"  • Total found: {stats['total_found']}")
    print(f"  • Total errors: {stats['total_errors']}")
    print(f"  • Last check: {stats['last_check_time']}")
    print("="*80)

if __name__ == "__main__":
    test_unified_checker()

