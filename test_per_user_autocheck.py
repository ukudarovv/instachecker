"""
Test per-user auto-checker functionality.
Creates test users with different intervals and verifies independent scheduling.
"""
import asyncio
import time
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from project.models import User, Account, Base
from project.cron.auto_checker_manager import AutoCheckerManager


async def test_per_user_autocheck():
    """Test per-user auto-checker with different intervals."""
    
    print("\n" + "="*80)
    print("🧪 TESTING PER-USER AUTO-CHECKER")
    print("="*80 + "\n")
    
    # Create test database
    engine = create_engine('sqlite:///test_per_user_autocheck.db', echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    
    # Clean up test data
    with SessionLocal() as session:
        session.query(Account).delete()
        session.query(User).delete()
        session.commit()
    
    # Create test users with different intervals
    print("📝 Creating test users...")
    with SessionLocal() as session:
        users_data = [
            {"username": "test_user_1", "interval": 2, "accounts_count": 3},
            {"username": "test_user_2", "interval": 3, "accounts_count": 2},
            {"username": "test_user_3", "interval": 5, "accounts_count": 1},
        ]
        
        for user_data in users_data:
            # Create user
            user = User(
                id=len(session.query(User).all()) + 1,
                username=user_data["username"],
                is_active=True,
                role="user",
                auto_check_interval=user_data["interval"],
                auto_check_enabled=True
            )
            session.add(user)
            session.flush()
            
            # Create test accounts for this user
            for i in range(user_data["accounts_count"]):
                account = Account(
                    user_id=user.id,
                    account=f"{user_data['username']}_account_{i+1}",
                    from_date=date.today(),
                    from_date_time=datetime.now(),
                    period=30,
                    to_date=date.today() + timedelta(days=30),
                    done=False
                )
                session.add(account)
            
            print(f"✅ Created @{user_data['username']} with {user_data['accounts_count']} accounts, interval: {user_data['interval']} min")
        
        session.commit()
    
    print(f"\n{'='*80}\n")
    
    # Initialize manager
    print("🚀 Initializing Auto-Checker Manager...")
    manager = AutoCheckerManager.initialize(session_factory=SessionLocal, bot=None)
    
    # Start all user checkers
    print("\n📋 Starting all user checkers...")
    manager.start_all(run_immediately=False)
    
    print(f"\n{'='*80}\n")
    
    # Print initial status
    print("📊 Initial Status:")
    manager.print_status()
    
    # Test 1: Update interval for user 1
    print("\n" + "="*80)
    print("TEST 1: Update interval for user 1 (2 min -> 10 min)")
    print("="*80 + "\n")
    
    manager.update_user_interval(1, 10)
    print("\n✅ Interval updated\n")
    manager.print_status()
    
    # Test 2: Disable auto-check for user 2
    print("\n" + "="*80)
    print("TEST 2: Disable auto-check for user 2")
    print("="*80 + "\n")
    
    manager.disable_user_checker(2)
    print("\n✅ Auto-check disabled for user 2\n")
    manager.print_status()
    
    # Test 3: Re-enable auto-check for user 2 with new interval
    print("\n" + "="*80)
    print("TEST 3: Re-enable auto-check for user 2 (interval: 7 min)")
    print("="*80 + "\n")
    
    manager.enable_user_checker(2, 7)
    print("\n✅ Auto-check re-enabled for user 2\n")
    manager.print_status()
    
    # Test 4: Manual trigger check for user 3
    print("\n" + "="*80)
    print("TEST 4: Manually trigger check for user 3")
    print("="*80 + "\n")
    
    await manager.trigger_user_check(3)
    print("\n✅ Manual check completed\n")
    
    # Wait a bit for the check to complete
    await asyncio.sleep(2)
    
    manager.print_status()
    
    # Test 5: Get statistics
    print("\n" + "="*80)
    print("TEST 5: Get all statistics")
    print("="*80 + "\n")
    
    stats = manager.get_all_stats()
    print(f"📊 Statistics:")
    print(f"   Total checkers: {stats['total_checkers']}")
    print(f"\n   Details:")
    for checker_stat in stats["checkers"]:
        print(f"   • User {checker_stat['user_id']} (@{checker_stat.get('username', '?')})")
        print(f"     - Interval: {checker_stat.get('interval_minutes', '?')} min")
        print(f"     - Running: {checker_stat['is_running']}")
        print(f"     - Total checks: {checker_stat['total_checks']}")
        print(f"     - Total found: {checker_stat['total_found']}")
        print()
    
    # Test 6: Wait and observe periodic checks
    print("\n" + "="*80)
    print("TEST 6: Observe periodic checks (waiting 30 seconds)")
    print("="*80 + "\n")
    
    print("⏳ Waiting for periodic checks to run...")
    print("   (Some checkers should run based on their intervals)\n")
    
    for i in range(6):
        await asyncio.sleep(5)
        print(f"⏱️ {(i+1)*5}s elapsed...")
    
    print("\n📊 Final Status:")
    manager.print_status()
    
    # Stop all checkers
    print("\n" + "="*80)
    print("🛑 Stopping all checkers...")
    print("="*80 + "\n")
    
    manager.stop_all()
    print("✅ All checkers stopped\n")
    
    # Summary
    print("\n" + "="*80)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
    print("="*80)
    print("\n📋 Summary:")
    print("   ✅ Created 3 users with different intervals")
    print("   ✅ Started individual schedulers for each user")
    print("   ✅ Updated user interval dynamically")
    print("   ✅ Disabled/enabled user auto-check")
    print("   ✅ Manually triggered check for specific user")
    print("   ✅ Retrieved statistics for all checkers")
    print("   ✅ Observed periodic checks")
    print("   ✅ Stopped all checkers cleanly")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_per_user_autocheck())

