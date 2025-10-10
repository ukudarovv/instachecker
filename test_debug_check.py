#!/usr/bin/env python3
"""Test debug account checking with detailed proxy logs."""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from project.database import get_engine, get_session_factory, init_db
from project.config import get_settings
from project.models import User, Proxy, Account
from project.services.checker_adv import check_username_with_details
from datetime import date, timedelta


async def main():
    """Test account checking with debug logs."""
    print("🧪 DEBUG TEST: Account Checking with Proxy Logs")
    print("="*70)
    
    # Setup
    settings = get_settings()
    engine = get_engine(settings.db_url)
    session_factory = get_session_factory(engine)
    init_db(engine)
    
    # Create test data
    with session_factory() as session:
        # Find or create test user
        user = session.query(User).filter(User.username == "test_debug").first()
        if not user:
            user = User(
                username="test_debug",
                role="user",
                is_active=True
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            print(f"✅ Created test user: {user.username}")
        else:
            print(f"✅ Using existing test user: {user.username} (ID: {user.id})")
        
        # Check if proxy exists
        existing_proxy = session.query(Proxy).filter(
            Proxy.user_id == user.id
        ).first()
        
        if existing_proxy:
            print(f"✅ Using existing proxy #{existing_proxy.id}: {existing_proxy.host}")
        else:
            print("❌ No proxies found for test user")
            print("\n💡 To add a proxy:")
            print("   1. Run the bot: python run_bot.py")
            print("   2. Go to 'Прокси' → 'Добавить прокси'")
            print("   3. Add your proxy URL")
            return
        
        user_id = user.id
    
    # Test account checking
    print(f"\n{'='*70}")
    print("🎯 Starting account check with debug logging...")
    print(f"{'='*70}\n")
    
    test_username = "instagram"  # Test with a known account
    
    result = await check_username_with_details(
        session=session_factory(),
        user_id=user_id,
        username=test_username,
        wait_selector=settings.screenshot_wait_selector,
        fallback_selector=settings.screenshot_fallback_selector,
        headless=settings.screenshot_headless,
        timeout_ms=settings.screenshot_timeout_ms,
    )
    
    # Print results
    print(f"\n{'='*70}")
    print("📊 FINAL RESULTS")
    print(f"{'='*70}")
    print(f"Username: @{result['username']}")
    print(f"Exists: {result.get('exists')}")
    print(f"Full name: {result.get('full_name', 'N/A')}")
    print(f"Followers: {result.get('followers', 'N/A')}")
    print(f"Following: {result.get('following', 'N/A')}")
    print(f"Posts: {result.get('posts', 'N/A')}")
    print(f"Screenshot: {result.get('screenshot_path', 'N/A')}")
    print(f"Error: {result.get('error', 'None')}")
    print(f"{'='*70}\n")
    
    # Check proxy statistics
    with session_factory() as session:
        proxies = session.query(Proxy).filter(Proxy.user_id == user_id).all()
        
        if proxies:
            print("\n📊 Proxy Statistics:")
            print("="*70)
            for p in proxies:
                print(f"\nProxy #{p.id}: {p.scheme}://{p.host}")
                print(f"  Status: {'✅ Active' if p.is_active else '❌ Inactive'}")
                print(f"  Priority: {p.priority}")
                print(f"  Used: {p.used_count} times")
                print(f"  Success: {p.success_count} times")
                print(f"  Fail streak: {p.fail_streak}")
                if p.cooldown_until:
                    print(f"  ❄️ Cooldown until: {p.cooldown_until}")
                print(f"  Last checked: {p.last_checked}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
