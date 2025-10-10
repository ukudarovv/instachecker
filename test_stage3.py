#!/usr/bin/env python3
"""Test script for Stage 3 functionality."""

import sys
import os

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all new modules can be imported."""
    print("🔄 Testing imports...")
    
    try:
        from project.states import AddDaysStates, RemoveDaysStates
        print("✅ States imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import states: {e}")
        return False
    
    try:
        from project.services.accounts import (
            get_accounts_page, get_account_by_id, remaining_days,
            increase_days, decrease_days, delete_account
        )
        print("✅ Account services imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import account services: {e}")
        return False
    
    try:
        from project.services.formatting import format_account_card
        print("✅ Formatting services imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import formatting services: {e}")
        return False
    
    try:
        from project.keyboards import (
            pagination_kb, accounts_list_kb, account_card_kb, confirm_delete_kb
        )
        print("✅ New keyboards imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import new keyboards: {e}")
        return False
    
    return True


def test_keyboards():
    """Test keyboard generation."""
    print("\n🔄 Testing keyboard generation...")
    
    try:
        from project.keyboards import pagination_kb, accounts_list_kb, account_card_kb, confirm_delete_kb
        
        # Test pagination keyboard
        pag_kb = pagination_kb("apg", 1, 3)
        assert "inline_keyboard" in pag_kb
        assert len(pag_kb["inline_keyboard"][0]) == 5  # 5 buttons
        print("✅ Pagination keyboard works")
        
        # Test accounts list keyboard
        class MockAccount:
            def __init__(self, id, account):
                self.id = id
                self.account = account
        
        mock_accounts = [MockAccount(1, "testuser"), MockAccount(2, "testuser2")]
        list_kb = accounts_list_kb("ainfo", mock_accounts)
        assert "inline_keyboard" in list_kb
        assert len(list_kb["inline_keyboard"]) == 2  # 2 accounts
        print("✅ Accounts list keyboard works")
        
        # Test account card keyboard
        card_kb = account_card_kb(1, "apg", 1)
        assert "inline_keyboard" in card_kb
        print("✅ Account card keyboard works")
        
        # Test confirm delete keyboard
        del_kb = confirm_delete_kb(1, "apg", 1)
        assert "inline_keyboard" in del_kb
        print("✅ Confirm delete keyboard works")
        
        return True
        
    except Exception as e:
        print(f"❌ Keyboard test failed: {e}")
        return False


def test_account_services():
    """Test account service functions."""
    print("\n🔄 Testing account services...")
    
    try:
        from project.services.accounts import remaining_days
        from project.utils.dates import today
        from datetime import date, timedelta
        
        # Test remaining_days function
        class MockAccount:
            def __init__(self, to_date):
                self.to_date = to_date
        
        # Test with future date
        future_date = today() + timedelta(days=5)
        acc = MockAccount(future_date)
        remaining = remaining_days(acc)
        assert remaining == 6  # 5 days + 1 (inclusive)
        print("✅ remaining_days calculation works")
        
        # Test with past date
        past_date = today() - timedelta(days=5)
        acc = MockAccount(past_date)
        remaining = remaining_days(acc)
        assert remaining == 0  # Should be 0 for past dates
        print("✅ remaining_days handles past dates correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Account services test failed: {e}")
        return False


def test_formatting():
    """Test formatting functions."""
    print("\n🔄 Testing formatting...")
    
    try:
        from project.services.formatting import format_account_card
        from datetime import date, timedelta
        
        class MockAccount:
            def __init__(self, account, from_date, period, to_date, done):
                self.account = account
                self.from_date = from_date
                self.period = period
                self.to_date = to_date
                self.done = done
        
        # Test formatting
        acc = MockAccount("testuser", date.today(), 7, date.today() + timedelta(days=7), False)
        formatted = format_account_card(acc)
        
        assert "testuser" in formatted
        assert "7" in formatted
        assert "На проверке" in formatted
        print("✅ Account card formatting works")
        
        return True
        
    except Exception as e:
        print(f"❌ Formatting test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Testing Stage 3 functionality...\n")
    
    tests = [
        test_imports,
        test_keyboards,
        test_account_services,
        test_formatting
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Stage 3 tests passed!")
        print("\nStage 3 features ready:")
        print("✅ Account lists with pagination")
        print("✅ Account cards with details")
        print("✅ Add/remove days functionality")
        print("✅ Account deletion with confirmation")
        print("✅ Inline keyboard navigation")
        return True
    else:
        print("❌ Some tests failed. Check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
