#!/usr/bin/env python3
"""Test FSM functionality."""

import os
import sys

# Add project to path
sys.path.insert(0, '.')

from project.config import get_settings
from project.database import get_engine, get_session_factory, init_db
from project.models import User, Account
from project.utils.access import get_or_create_user
from project.services.accounts import normalize_username, find_duplicate, create_account
from project.services.checker import is_valid_instagram_username, check_account_exists_placeholder
from project.utils.dates import today, add_days, clamp_min_days

def test_fsm():
    """Test FSM functionality."""
    print("🔄 Testing FSM functionality...")
    
    # Initialize database
    settings = get_settings()
    engine = get_engine(settings.db_url)
    session_factory = get_session_factory(engine)
    init_db(engine)
    
    with session_factory() as session:
        # Create test user
        class TestUser:
            def __init__(self, user_id, username=None):
                self.id = user_id
                self.username = username
        
        test_user = TestUser(12345, "testuser")
        user = get_or_create_user(session, test_user)
        user.is_active = True
        session.commit()
        
        print(f"✅ Test user created: {user.username}, active: {user.is_active}")
        
        # Test username validation
        print("\n🔍 Testing username validation...")
        
        test_cases = [
            ("testuser", True),
            ("@testuser", True),
            ("test.user", True),
            ("test_user", True),
            ("test123", True),
            ("", False),
            ("test user", False),
            ("test@user", False),
            ("a" * 31, False),  # Too long
            ("test-user", False),  # Invalid character
        ]
        
        for username, expected in test_cases:
            normalized = normalize_username(username)
            result = is_valid_instagram_username(normalized)
            status = "✅" if result == expected else "❌"
            print(f"{status} '{username}' -> '{normalized}' -> {result} (expected {expected})")
        
        # Test account creation
        print("\n📝 Testing account creation...")
        
        # Test duplicate detection
        username = "testuser"
        if find_duplicate(session, user.id, username):
            print("⚠️ Duplicate found (expected for first run)")
        else:
            print("✅ No duplicate found (first account)")
        
        # Create first account
        acc1 = create_account(session, user.id, username, 10)
        print(f"✅ Account created: @{acc1.account}, period: {acc1.period} days")
        print(f"   From: {acc1.from_date}, To: {acc1.to_date}")
        
        # Test duplicate detection after creation
        if find_duplicate(session, user.id, username):
            print("✅ Duplicate detection works")
        else:
            print("❌ Duplicate detection failed")
        
        # Test date calculations
        print("\n📅 Testing date calculations...")
        today_date = today()
        print(f"Today: {today_date}")
        
        test_days = [1, 7, 30, 365]
        for days in test_days:
            clamped = clamp_min_days(days)
            end_date = add_days(today_date, clamped)
            print(f"  {days} days -> {clamped} days -> {end_date}")
        
        # Test account checker
        print("\n🔍 Testing account checker...")
        checker_tests = [
            ("validuser", True),
            ("invalid user", False),
            ("", False),
        ]
        
        for username, expected in checker_tests:
            result = check_account_exists_placeholder(username)
            status = "✅" if result == expected else "❌"
            print(f"{status} '{username}' -> {result} (expected {expected})")
        
        # Show all accounts
        print("\n📋 All accounts in database:")
        accounts = session.query(Account).filter(Account.user_id == user.id).all()
        for acc in accounts:
            print(f"  - @{acc.account}: {acc.from_date} to {acc.to_date} ({acc.period} days)")
        
        print("\n🎉 FSM tests completed!")
        print("\nTo test with real bot:")
        print("1. Set BOT_TOKEN in .env file")
        print("2. Run: python run_bot.py")
        print("3. Send /start to bot")
        print("4. Click 'Добавить аккаунт'")
        print("5. Follow the FSM flow")

if __name__ == "__main__":
    test_fsm()
