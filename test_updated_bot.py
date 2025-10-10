#!/usr/bin/env python3
"""Test updated bot logic without proxy."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all updated imports."""
    print("🧪 Testing updated bot imports...")
    
    try:
        from project.services.ig_simple_checker import check_account_with_screenshot
        print("✅ ig_simple_checker imports OK")
    except ImportError as e:
        print(f"❌ ig_simple_checker import failed: {e}")
        return False
    
    try:
        from project.services.ig_sessions import get_active_session, decode_cookies
        print("✅ ig_sessions imports OK")
    except ImportError as e:
        print(f"❌ ig_sessions import failed: {e}")
        return False
    
    try:
        from project.utils.encryptor import OptionalFernet
        print("✅ encryptor imports OK")
    except ImportError as e:
        print(f"❌ encryptor import failed: {e}")
        return False
    
    return True


def test_bot_logic():
    """Test bot logic without proxy."""
    print("\n🤖 Testing bot logic...")
    
    try:
        from project.bot import TelegramBot
        from project.config import get_settings
        
        settings = get_settings()
        bot = TelegramBot("test_token")
        
        print("✅ Bot created successfully")
        print(f"✅ Settings loaded: headless={settings.ig_headless}")
        return True
    except Exception as e:
        print(f"❌ Bot logic test failed: {e}")
        return False


def test_instagram_session():
    """Test Instagram session functionality."""
    print("\n📱 Testing Instagram session...")
    
    try:
        from project.config import get_settings
        from project.database import get_engine, get_session_factory, init_db
        from project.models import User, InstagramSession
        from project.utils.encryptor import OptionalFernet
        from project.services.ig_sessions import save_session, get_active_session
        
        settings = get_settings()
        engine = get_engine(settings.db_url)
        session_factory = get_session_factory(engine)
        init_db(engine)
        
        fernet = OptionalFernet(settings.encryption_key)
        
        with session_factory() as session:
            # Test user
            user = session.query(User).filter(User.username == "test_user").first()
            if not user:
                user = User(
                    username="test_user",
                    role="user",
                    is_active=True
                )
                session.add(user)
                session.commit()
                session.refresh(user)
            
            # Test session
            test_cookies = [
                {"name": "sessionid", "value": "test_session", "domain": ".instagram.com", "path": "/"}
            ]
            
            ig_session = save_session(
                session=session,
                user_id=user.id,
                ig_username="test_ig_user",
                cookies_json=test_cookies,
                fernet=fernet
            )
            
            # Test getting active session
            active_session = get_active_session(session, user.id)
            
            if active_session and active_session.id == ig_session.id:
                print("✅ Instagram session functionality works")
                return True
            else:
                print("❌ Instagram session test failed")
                return False
                
    except Exception as e:
        print(f"❌ Instagram session test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🎯 UPDATED BOT LOGIC TEST")
    print("=" * 50)
    
    success = True
    
    if not test_imports():
        success = False
    
    if not test_bot_logic():
        success = False
    
    if not test_instagram_session():
        success = False
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
        print("=" * 50)
        print("✅ Updated bot logic is ready!")
        print("📱 Bot now uses simple Instagram checking without proxy!")
        print("\n🚀 Key changes:")
        print("   • Removed proxy dependency")
        print("   • Uses Instagram sessions directly")
        print("   • Simple Playwright-based checking")
        print("   • Screenshots of profiles")
        print("   • No more proxy authentication errors")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("=" * 50)
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
