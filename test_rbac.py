#!/usr/bin/env python3
"""Test RBAC functionality."""

import os
import sys

# Add project to path
sys.path.insert(0, '.')

from project.config import get_settings
from project.database import get_engine, get_session_factory, init_db
from project.models import User
from project.utils.access import get_or_create_user, ensure_active, ensure_admin

def test_rbac():
    """Test RBAC functionality."""
    print("🔐 Testing RBAC functionality...")
    
    # Initialize database
    settings = get_settings()
    engine = get_engine(settings.db_url)
    session_factory = get_session_factory(engine)
    init_db(engine)
    
    with session_factory() as session:
        # Test user creation
        print("\n👤 Testing user creation...")
        
        # Create test user object
        class TestUser:
            def __init__(self, user_id, username=None):
                self.id = user_id
                self.username = username
        
        test_user = TestUser(12345, "testuser")
        
        # Test get_or_create_user
        user = get_or_create_user(session, test_user)
        print(f"✅ User created: ID={user.id}, username={user.username}, is_active={user.is_active}, role={user.role}")
        
        # Test access control
        print("\n🔒 Testing access control...")
        
        # Test inactive user
        print(f"❌ Inactive user - ensure_active: {ensure_active(user)}")
        print(f"❌ Inactive user - ensure_admin: {ensure_admin(user)}")
        
        # Activate user
        user.is_active = True
        session.commit()
        print(f"✅ User activated - ensure_active: {ensure_active(user)}")
        print(f"❌ Regular user - ensure_admin: {ensure_admin(user)}")
        
        # Make user admin
        user.role = "admin"
        session.commit()
        print(f"✅ Admin user - ensure_active: {ensure_active(user)}")
        print(f"✅ Admin user - ensure_admin: {ensure_admin(user)}")
        
        # Test superuser
        user.role = "superuser"
        session.commit()
        print(f"✅ Superuser - ensure_active: {ensure_active(user)}")
        print(f"✅ Superuser - ensure_admin: {ensure_admin(user)}")
        
        # Test keyboard generation
        print("\n⌨️ Testing keyboard generation...")
        try:
            from project.keyboards import main_menu
            
            # Test regular user menu
            regular_menu = main_menu(is_admin=False)
            print("✅ Regular user menu created")
            
            # Test admin menu
            admin_menu = main_menu(is_admin=True)
            print("✅ Admin menu created")
            
            if isinstance(regular_menu, dict):
                print(f"📱 Regular menu buttons: {len(regular_menu['keyboard'])} rows")
                print(f"📱 Admin menu buttons: {len(admin_menu['keyboard'])} rows")
            
        except Exception as e:
            print(f"❌ Keyboard test failed: {e}")
        
        print("\n🎉 RBAC tests completed!")
        print("\nTo test with real bot:")
        print("1. Set BOT_TOKEN in .env file")
        print("2. Run: python run_bot.py")
        print("3. Send /start to bot")
        print("4. Check database to see user creation")
        print("5. Manually set is_active=True and role='admin' in database")
        print("6. Send /start again to see admin menu")

if __name__ == "__main__":
    test_rbac()
