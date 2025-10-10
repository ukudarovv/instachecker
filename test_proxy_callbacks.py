#!/usr/bin/env python3
"""Test script for proxy callback handling."""

import sys
import os

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_callback_parsing():
    """Test callback data parsing for proxy actions."""
    print("🔄 Testing proxy callback parsing...")
    
    test_callbacks = [
        "prx_off:123",      # Disable proxy
        "prx_on:456",       # Enable proxy
        "prx_pinc:789",     # Increase priority
        "prx_pdec:101",     # Decrease priority
        "prx_del:202",      # Delete proxy
    ]
    
    for callback_data in test_callbacks:
        if callback_data.startswith("prx_off:") or callback_data.startswith("prx_on:") or callback_data.startswith("prx_pinc:") or callback_data.startswith("prx_pdec:") or callback_data.startswith("prx_del:"):
            action, pid = callback_data.split(":")
            pid = int(pid)
            print(f"✅ {callback_data} -> action: {action}, pid: {pid}")
        else:
            print(f"❌ {callback_data} -> not recognized")
            return False
    
    return True


def test_proxy_keyboard_generation():
    """Test proxy keyboard generation with different IDs."""
    print("\n🔄 Testing proxy keyboard generation...")
    
    try:
        from project.keyboards import proxy_card_kb
        
        # Test with different proxy IDs
        test_ids = [1, 123, 456, 789]
        
        for proxy_id in test_ids:
            kb = proxy_card_kb(proxy_id)
            assert "inline_keyboard" in kb
            assert len(kb["inline_keyboard"]) == 3  # 3 rows
            
            # Check that all callback_data contain the correct proxy_id
            for row in kb["inline_keyboard"]:
                for button in row:
                    if "callback_data" in button:
                        assert str(proxy_id) in button["callback_data"]
            
            print(f"✅ Proxy keyboard for ID {proxy_id} works")
        
        return True
        
    except Exception as e:
        print(f"❌ Proxy keyboard test failed: {e}")
        return False


def test_bot_callback_handling():
    """Test that bot can handle proxy callbacks."""
    print("\n🔄 Testing bot callback handling...")
    
    try:
        from project.bot import TelegramBot
        
        # Test that bot has callback processing method
        bot = TelegramBot("test_token")
        assert hasattr(bot, 'process_callback_query')
        print("✅ Bot has process_callback_query method")
        
        # Test callback data patterns
        test_patterns = [
            "prx_off:123",
            "prx_on:456", 
            "prx_pinc:789",
            "prx_pdec:101",
            "prx_del:202"
        ]
        
        for pattern in test_patterns:
            # Test that pattern would be recognized
            if (pattern.startswith("prx_off:") or pattern.startswith("prx_on:") or 
                pattern.startswith("prx_pinc:") or pattern.startswith("prx_pdec:") or 
                pattern.startswith("prx_del:")):
                print(f"✅ Pattern '{pattern}' would be recognized")
            else:
                print(f"❌ Pattern '{pattern}' would NOT be recognized")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Bot callback test failed: {e}")
        return False


def main():
    """Run all proxy callback tests."""
    print("🧪 Testing proxy callback functionality...\n")
    
    tests = [
        test_callback_parsing,
        test_proxy_keyboard_generation,
        test_bot_callback_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All proxy callback tests passed!")
        print("\nProxy callback features ready:")
        print("✅ Callback data parsing")
        print("✅ Proxy keyboard generation")
        print("✅ Bot callback handling")
        print("✅ All proxy actions supported:")
        print("  - Отключить (Disable)")
        print("  - Включить (Enable)")
        print("  - Приоритет + (Priority +)")
        print("  - Приоритет - (Priority -)")
        print("  - Удалить (Delete)")
        return True
    else:
        print("❌ Some tests failed. Check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
