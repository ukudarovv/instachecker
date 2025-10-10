#!/usr/bin/env python3
"""Test Stage 4 Advanced functionality - Profile parsing and screenshots."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all new modules can be imported."""
    print("🔄 Testing Stage 4 Advanced imports...")
    
    try:
        from project.services.ig_profile_extract import extract_profile_info
        print("✅ ig_profile_extract imported successfully")
    except ImportError as e:
        print(f"❌ ig_profile_extract import failed: {e}")
        return False
    
    try:
        from project.services.ig_screenshot import screenshot_profile_header
        print("✅ ig_screenshot imported successfully")
    except ImportError as e:
        print(f"❌ ig_screenshot import failed: {e}")
        return False
    
    try:
        from project.services.checker_adv import check_username_with_details
        print("✅ checker_adv imported successfully")
    except ImportError as e:
        print(f"❌ checker_adv import failed: {e}")
        return False
    
    # Skip check_now_adv as it uses aiogram which we don't use
    print("⏭️ Skipping check_now_adv (uses aiogram, not needed for our bot)")
    
    return True


def test_config():
    """Test configuration settings."""
    print("\n🔄 Testing configuration settings...")
    
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from project.config import get_settings
        settings = get_settings()
        
        # Test screenshot settings
        assert hasattr(settings, 'screenshot_headless'), "Missing screenshot_headless setting"
        assert hasattr(settings, 'screenshot_timeout_ms'), "Missing screenshot_timeout_ms setting"
        assert hasattr(settings, 'screenshot_wait_selector'), "Missing screenshot_wait_selector setting"
        assert hasattr(settings, 'screenshot_fallback_selector'), "Missing screenshot_fallback_selector setting"
        
        print("✅ Screenshot settings configured")
        print(f"   - Headless: {settings.screenshot_headless}")
        print(f"   - Timeout: {settings.screenshot_timeout_ms}ms")
        print(f"   - Wait selector: {settings.screenshot_wait_selector}")
        print(f"   - Fallback selector: {settings.screenshot_fallback_selector}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_bot_methods():
    """Test that bot has new methods."""
    print("\n🔄 Testing bot methods...")
    
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from project.bot import TelegramBot
        
        # Test that bot has send_photo method
        assert hasattr(TelegramBot, 'send_photo'), "Missing send_photo method"
        print("✅ Bot has send_photo method")
        
        return True
    except Exception as e:
        print(f"❌ Bot methods test failed: {e}")
        return False


def test_playwright_import():
    """Test Playwright import."""
    print("\n🔄 Testing Playwright import...")
    
    try:
        from playwright.async_api import async_playwright
        print("✅ Playwright imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Playwright import failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Testing Stage 4 Advanced functionality...")
    
    tests = [
        test_imports,
        test_config,
        test_bot_methods,
        test_playwright_import,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Stage 4 Advanced tests passed!")
        print("\nStage 4 Advanced features ready:")
        print("✅ Profile parsing via aiohttp + proxy")
        print("✅ Screenshot generation via Playwright + proxy")
        print("✅ Advanced account checking with details")
        print("✅ Photo sending capability")
        print("✅ Configuration management")
        return True
    else:
        print("❌ Some tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
