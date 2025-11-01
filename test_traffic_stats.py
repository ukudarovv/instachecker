"""
Test script for traffic statistics in auto-check.
"""

import asyncio
from project.database import get_engine, get_session_factory
from project.config import get_settings
from project.services.autocheck_traffic_stats import AutoCheckTrafficStats


def test_traffic_stats():
    """Test AutoCheckTrafficStats functionality."""
    
    print("=== Testing AutoCheckTrafficStats ===\n")
    
    # Create stats instance
    stats = AutoCheckTrafficStats()
    
    # Simulate some checks
    # Active accounts (found)
    stats.add_check(username="active_user_1", is_active=True, traffic_bytes=5000, duration_ms=250)
    stats.add_check(username="active_user_2", is_active=True, traffic_bytes=5500, duration_ms=300)
    stats.add_check(username="active_user_3", is_active=True, traffic_bytes=4800, duration_ms=280)
    
    # Inactive accounts (not found)
    stats.add_check(username="inactive_user_1", is_active=False, traffic_bytes=1200, duration_ms=150)
    stats.add_check(username="inactive_user_2", is_active=False, traffic_bytes=1100, duration_ms=140)
    stats.add_check(username="inactive_user_3", is_active=False, traffic_bytes=1300, duration_ms=160)
    stats.add_check(username="inactive_user_4", is_active=False, traffic_bytes=1250, duration_ms=155)
    
    # Error
    stats.add_check(username="error_user", is_active=False, traffic_bytes=500, duration_ms=50, error=True)
    
    # Finalize
    stats.finalize()
    
    # Get summary
    summary = stats.get_summary()
    
    print("📊 Summary Statistics:")
    print(f"  Total checks: {summary['total_checks']}")
    print(f"  Active accounts: {summary['active_accounts']}")
    print(f"  Inactive accounts: {summary['inactive_accounts']}")
    print(f"  Errors: {summary['errors']}")
    print(f"  Total traffic: {stats.format_bytes(summary['total_traffic'])}")
    print(f"  Active traffic: {stats.format_bytes(summary['active_traffic'])}")
    print(f"  Inactive traffic: {stats.format_bytes(summary['inactive_traffic'])}")
    print(f"  Avg traffic (active): {stats.format_bytes(int(summary['avg_traffic_active']))}")
    print(f"  Avg traffic (inactive): {stats.format_bytes(int(summary['avg_traffic_inactive']))}")
    print(f"  Avg traffic per check: {stats.format_bytes(int(summary['avg_traffic_per_check']))}")
    print(f"  Duration: {summary['total_duration_sec']:.2f} sec")
    
    print("\n" + "="*60)
    print("📄 Formatted Report:")
    print("="*60)
    print(stats.get_report())
    
    print("\n✅ Test completed successfully!")


async def test_traffic_report_integration():
    """Test integration with auto-checker."""
    
    print("\n=== Testing Auto-Checker Integration ===\n")
    
    settings = get_settings()
    engine = get_engine(settings.db_url)
    SessionLocal = get_session_factory(engine)
    
    from project.models import User, Account
    
    with SessionLocal() as session:
        # Get a test user with accounts
        user = session.query(User).filter(
            User.is_active == True,
            User.auto_check_enabled == True
        ).first()
        
        if not user:
            print("⚠️ No active users with auto-check enabled found")
            return
        
        pending_accounts = session.query(Account).filter(
            Account.user_id == user.id,
            Account.done == False
        ).limit(3).all()
        
        if not pending_accounts:
            print(f"⚠️ No pending accounts for user {user.id}")
            return
        
        print(f"✅ Found user {user.id} (@{user.username}) with {len(pending_accounts)} pending accounts")
        print("   (Traffic stats will be generated during actual auto-check)")
    
    print("\n✅ Integration test setup complete!")


if __name__ == "__main__":
    # Test basic functionality
    test_traffic_stats()
    
    # Test integration
    print("\n" + "="*60 + "\n")
    asyncio.run(test_traffic_report_integration())

