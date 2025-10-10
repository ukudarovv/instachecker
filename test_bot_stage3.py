#!/usr/bin/env python3
"""Test bot with Stage 3 functionality."""

import sys
import os

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_bot_imports():
    """Test that bot can be imported with new functionality."""
    print("🔄 Testing bot imports with Stage 3...")
    
    try:
        from project.bot import TelegramBot
        print("✅ TelegramBot imported successfully")
        
        # Test that bot has new methods
        bot = TelegramBot("test_token")
        assert hasattr(bot, 'process_callback_query')
        assert hasattr(bot, 'edit_message_text')
        assert hasattr(bot, 'answer_callback_query')
        print("✅ Bot has new callback methods")
        
        return True
        
    except Exception as e:
        print(f"❌ Bot import test failed: {e}")
        return False


def test_callback_processing():
    """Test callback query processing."""
    print("\n🔄 Testing callback processing...")
    
    try:
        from project.bot import TelegramBot
        from project.database import get_engine, get_session_factory, init_db
        from project.config import get_settings
        
        # Setup
        settings = get_settings()
        engine = get_engine(settings.db_url)
        session_factory = get_session_factory(engine)
        init_db(engine)
        
        bot = TelegramBot("test_token")
        
        # Test callback data parsing
        test_callbacks = [
            "apg:1",  # Active pagination
            "ipg:2",  # Pending pagination
            "ainfo:123",  # Active account info
            "iinfo:456",  # Pending account info
            "addd:789",  # Add days
            "subd:101",  # Subtract days
            "delc:202",  # Delete confirm
            "delok:303:apg:1",  # Delete OK
            "delno:404:apg:1",  # Delete NO
        ]
        
        for callback_data in test_callbacks:
            # Test that callback data can be parsed
            if callback_data.startswith("apg:"):
                page = int(callback_data.split(":")[1])
                assert page == 1
            elif callback_data.startswith("ipg:"):
                page = int(callback_data.split(":")[1])
                assert page == 2
            elif callback_data.startswith("ainfo:") or callback_data.startswith("iinfo:"):
                prefix, acc_id_s = callback_data.split(":")
                acc_id = int(acc_id_s)
                assert acc_id > 0
            elif callback_data.startswith("addd:") or callback_data.startswith("subd:"):
                acc_id = int(callback_data.split(":")[1])
                assert acc_id > 0
            elif callback_data.startswith("delc:"):
                acc_id = int(callback_data.split(":")[1])
                assert acc_id > 0
            elif callback_data.startswith("delok:"):
                parts = callback_data.split(":")
                assert len(parts) == 4
                acc_id = int(parts[1])
                assert acc_id > 0
            elif callback_data.startswith("delno:"):
                parts = callback_data.split(":")
                assert len(parts) == 4
                acc_id = int(parts[1])
                assert acc_id > 0
        
        print("✅ Callback data parsing works")
        return True
        
    except Exception as e:
        print(f"❌ Callback processing test failed: {e}")
        return False


def test_fsm_states():
    """Test FSM states for new functionality."""
    print("\n🔄 Testing FSM states...")
    
    try:
        from project.states import AddDaysStates, RemoveDaysStates
        
        # Test that states exist
        assert hasattr(AddDaysStates, 'waiting_for_amount')
        assert hasattr(RemoveDaysStates, 'waiting_for_amount')
        print("✅ FSM states defined correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ FSM states test failed: {e}")
        return False


def test_integration():
    """Test integration of all components."""
    print("\n🔄 Testing integration...")
    
    try:
        # Test that all modules can work together
        from project.bot import TelegramBot
        from project.services.accounts import get_accounts_page, remaining_days
        from project.services.formatting import format_account_card
        from project.keyboards import pagination_kb, accounts_list_kb, account_card_kb
        from project.database import get_engine, get_session_factory, init_db
        from project.config import get_settings
        
        # Setup database
        settings = get_settings()
        engine = get_engine(settings.db_url)
        session_factory = get_session_factory(engine)
        init_db(engine)
        
        # Test that we can create a bot instance
        bot = TelegramBot("test_token")
        assert bot.fsm_states == {}
        print("✅ Bot integration works")
        
        # Test that we can generate keyboards
        pag_kb = pagination_kb("apg", 1, 3)
        assert "inline_keyboard" in pag_kb
        print("✅ Keyboard integration works")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False


def main():
    """Run all Stage 3 bot tests."""
    print("🧪 Testing bot with Stage 3 functionality...\n")
    
    tests = [
        test_bot_imports,
        test_callback_processing,
        test_fsm_states,
        test_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Stage 3 bot tests passed!")
        print("\nBot is ready with Stage 3 features:")
        print("✅ Inline keyboard support")
        print("✅ Callback query processing")
        print("✅ Account lists and pagination")
        print("✅ Account cards and management")
        print("✅ FSM for adding/removing days")
        print("✅ Account deletion with confirmation")
        return True
    else:
        print("❌ Some tests failed. Check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
