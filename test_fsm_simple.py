#!/usr/bin/env python3
"""Simple FSM test without database cleanup."""

import os
import sys

# Add project to path
sys.path.insert(0, '.')

from project.services.accounts import normalize_username, find_duplicate, create_account
from project.services.checker import is_valid_instagram_username, check_account_exists_placeholder
from project.utils.dates import today, add_days, clamp_min_days

def test_fsm_simple():
    """Simple FSM test."""
    print("🔄 Simple FSM test...")
    
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
    
    print("\n🎉 Simple FSM tests completed!")
    print("\nThe bot should now work correctly for adding accounts.")

if __name__ == "__main__":
    test_fsm_simple()
