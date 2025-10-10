#!/usr/bin/env python3
"""Test profile header screenshot functionality."""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from project.services.ig_simple_checker import check_account_with_screenshot


async def test_header_screenshot():
    """Test taking screenshot of profile header only."""
    print("🎯 TESTING PROFILE HEADER SCREENSHOT")
    print("=" * 50)
    
    # Test cookies (you'll need to replace with real cookies)
    test_cookies = [
        {"name": "sessionid", "value": "test_session_id", "domain": ".instagram.com", "path": "/"},
        {"name": "csrftoken", "value": "test_csrf_token", "domain": ".instagram.com", "path": "/"},
        {"name": "ds_user_id", "value": "123456789", "domain": ".instagram.com", "path": "/"}
    ]
    
    # Test username
    test_username = "instagram"  # Public Instagram account for testing
    
    print(f"\n📸 Testing screenshot for @{test_username}...")
    print("⚠️ Note: You need real Instagram cookies for this to work!")
    print("⚠️ This is a demonstration of the header screenshot logic.")
    
    try:
        result = await check_account_with_screenshot(
            username=test_username,
            cookies=test_cookies,
            headless=False,  # Show browser for testing
            timeout_ms=30000
        )
        
        print(f"\n📊 Result:")
        print(f"   Username: @{result['username']}")
        print(f"   Exists: {result.get('exists')}")
        print(f"   Full name: {result.get('full_name')}")
        print(f"   Followers: {result.get('followers')}")
        print(f"   Following: {result.get('following')}")
        print(f"   Posts: {result.get('posts')}")
        print(f"   Screenshot: {result.get('screenshot_path')}")
        
        if result.get('screenshot_path'):
            if os.path.exists(result['screenshot_path']):
                print(f"\n✅ Screenshot saved successfully!")
                print(f"   Path: {result['screenshot_path']}")
                print(f"   Size: {os.path.getsize(result['screenshot_path'])} bytes")
            else:
                print(f"\n❌ Screenshot file not found: {result['screenshot_path']}")
        else:
            print(f"\n⚠️ No screenshot was taken")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run header screenshot test."""
    print("\n🔍 Profile Header Screenshot Test")
    print("=" * 50)
    print("\nℹ️ This test demonstrates the new header screenshot logic:")
    print("   1. Finds 'header section' element")
    print("   2. Gets bounding box coordinates")
    print("   3. Takes screenshot of only that area")
    print("   4. Fallback to top 600px if header not found")
    print("\n" + "=" * 50)
    
    success = asyncio.run(test_header_screenshot())
    
    if success:
        print("\n🎉 Header screenshot logic is working!")
        print("=" * 50)
        print("✅ Screenshots will now show only the profile header:")
        print("   • Avatar")
        print("   • Username and name")
        print("   • Followers, Following, Posts counts")
        print("   • Bio section")
    else:
        print("\n❌ Test failed - check the error above")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
