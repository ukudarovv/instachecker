#!/usr/bin/env python3
"""Add test proxy to database for debugging."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from project.database import get_engine, get_session_factory, init_db
from project.config import get_settings
from project.models import User, Proxy
from project.services.proxy_utils import parse_proxy_url, save_proxy


def main():
    """Add test proxy to database."""
    print("🔧 Adding test proxy to database...")
    
    # Setup
    settings = get_settings()
    engine = get_engine(settings.db_url)
    session_factory = get_session_factory(engine)
    init_db(engine)
    
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
            print(f"✅ Created test user: {user.username} (ID: {user.id})")
        else:
            print(f"✅ Using existing test user: {user.username} (ID: {user.id})")
        
        # Check existing proxies
        existing_proxies = session.query(Proxy).filter(Proxy.user_id == user.id).all()
        print(f"\n📊 Existing proxies: {len(existing_proxies)}")
        
        for p in existing_proxies:
            print(f"   Proxy #{p.id}: {p.scheme}://{p.host}")
            print(f"      Active: {'✅' if p.is_active else '❌'}")
            print(f"      Priority: {p.priority}")
            print(f"      Success: {p.success_count}/{p.used_count}")
            if p.cooldown_until:
                print(f"      ❄️ Cooldown until: {p.cooldown_until}")
        
        # Add test proxy
        test_proxy_url = "http://RriFXeBz:CpuhKzJlX0@213.209.130.121:50100"
        
        print(f"\n🔧 Adding test proxy: {test_proxy_url}")
        
        # Parse proxy URL
        parsed = parse_proxy_url(test_proxy_url)
        if not parsed:
            print(f"❌ Failed to parse proxy URL: {test_proxy_url}")
            return
        
        print(f"✅ Parsed proxy:")
        print(f"   Scheme: {parsed['scheme']}")
        print(f"   Host: {parsed['host']}")
        print(f"   Username: {parsed.get('username', 'None')}")
        print(f"   Password: {'***' if parsed.get('password') else 'None'}")
        
        # Save proxy
        try:
            proxy = save_proxy(session, user.id, parsed, priority=5)
            print(f"✅ Proxy saved with ID: {proxy.id}")
            
            # Show final proxy list
            print(f"\n📊 Updated proxy list:")
            proxies = session.query(Proxy).filter(Proxy.user_id == user.id).all()
            for p in proxies:
                print(f"   Proxy #{p.id}: {p.scheme}://{p.host}")
                print(f"      Active: {'✅' if p.is_active else '❌'}")
                print(f"      Priority: {p.priority}")
                print(f"      Success: {p.success_count}/{p.used_count}")
                if p.cooldown_until:
                    print(f"      ❄️ Cooldown until: {p.cooldown_until}")
            
            print(f"\n🎉 Test proxy added successfully!")
            print(f"Now you can run: python test_debug_check.py")
            
        except Exception as e:
            print(f"❌ Failed to save proxy: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
