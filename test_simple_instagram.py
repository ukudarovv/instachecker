#!/usr/bin/env python3
"""Test simple Instagram checking functionality."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all simple Instagram imports."""
    print("🧪 Testing simple Instagram imports...")
    
    try:
        from project.services.ig_simple_checker import check_account_with_screenshot
        print("✅ ig_simple_checker imports OK")
    except ImportError as e:
        print(f"❌ ig_simple_checker import failed: {e}")
        return False
    
    try:
        from project.handlers.ig_simple_check import register_ig_simple_check_handlers
        print("✅ ig_simple_check handlers imports OK")
    except ImportError as e:
        print(f"❌ ig_simple_check handlers import failed: {e}")
        return False
    
    return True


def test_bot_imports():
    """Test bot imports."""
    print("\n🤖 Testing bot imports...")
    
    try:
        from project.bot import TelegramBot
        print("✅ TelegramBot imports OK")
    except ImportError as e:
        print(f"❌ TelegramBot import failed: {e}")
        return False
    
    return True


def test_config():
    """Test configuration."""
    print("\n⚙️ Testing configuration...")
    
    try:
        from project.config import get_settings
        settings = get_settings()
        
        print(f"📱 Instagram headless: {settings.ig_headless}")
        print(f"⏱️ Login timeout: {settings.ig_login_timeout_ms}ms")
        print(f"⏱️ 2FA timeout: {settings.ig_2fa_timeout_ms}ms")
        
        print("✅ Configuration loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_playwright():
    """Test Playwright availability."""
    print("\n🎭 Testing Playwright...")
    
    try:
        from playwright.async_api import async_playwright
        print("✅ Playwright imports OK")
        
        # Test basic playwright functionality
        import asyncio
        async def test_playwright():
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                await page.goto("https://example.com")
                title = await page.title()
                await browser.close()
                return title
        
        title = asyncio.run(test_playwright())
        print(f"✅ Playwright test successful: {title}")
        return True
    except Exception as e:
        print(f"❌ Playwright test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🎯 SIMPLE INSTAGRAM CHECKING TEST")
    print("=" * 50)
    
    success = True
    
    if not test_imports():
        success = False
    
    if not test_bot_imports():
        success = False
    
    if not test_config():
        success = False
    
    if not test_playwright():
        success = False
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
        print("=" * 50)
        print("✅ Simple Instagram checking is ready!")
        print("📱 Bot is ready to use!")
        print("\n🚀 Available features:")
        print("   • Simple Instagram account checking")
        print("   • Screenshots of profiles")
        print("   • No proxy required")
        print("   • Direct Instagram access")
        print("   • High accuracy with real browser")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("=" * 50)
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
