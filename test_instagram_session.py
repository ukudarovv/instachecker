#!/usr/bin/env python3
"""Test Instagram session functionality."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from project.config import get_settings
from project.database import get_engine, get_session_factory, init_db
from project.models import User, InstagramSession
from project.utils.encryptor import OptionalFernet
from project.services.ig_sessions import save_session, get_active_session, decode_cookies
import json


def test_encryption():
    """Test encryption functionality."""
    print("🔐 Testing encryption...")
    
    # Test with key
    key = "test_key_32_bytes_long_for_fernet_encryption"
    fernet = OptionalFernet(key)
    
    test_data = "test_cookies_data"
    encrypted = fernet.encrypt(test_data)
    decrypted = fernet.decrypt(encrypted)
    
    assert decrypted == test_data, f"Encryption failed: {decrypted} != {test_data}"
    print("✅ Encryption works correctly")
    
    # Test without key
    fernet_no_key = OptionalFernet(None)
    encrypted_no_key = fernet_no_key.encrypt(test_data)
    decrypted_no_key = fernet_no_key.decrypt(encrypted_no_key)
    
    assert decrypted_no_key == test_data, f"No-key encryption failed: {decrypted_no_key} != {test_data}"
    print("✅ No-key encryption works correctly")


def test_ig_sessions():
    """Test Instagram session management."""
    print("\n📱 Testing Instagram sessions...")
    
    settings = get_settings()
    engine = get_engine(settings.db_url)
    session_factory = get_session_factory(engine)
    init_db(engine)
    
    fernet = OptionalFernet(settings.encryption_key)
    
    with session_factory() as session:
        # Create test user
        user = session.query(User).filter(User.username == "test_ig_user").first()
        if not user:
            user = User(
                username="test_ig_user",
                role="user",
                is_active=True
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            print(f"✅ Created test user: {user.username}")
        else:
            print(f"✅ Using existing test user: {user.username}")
        
        # Test cookies
        test_cookies = [
            {"name": "sessionid", "value": "test_session_id", "domain": ".instagram.com", "path": "/"},
            {"name": "csrftoken", "value": "test_csrf_token", "domain": ".instagram.com", "path": "/"},
            {"name": "ds_user_id", "value": "123456789", "domain": ".instagram.com", "path": "/"}
        ]
        
        # Save session
        ig_session = save_session(
            session=session,
            user_id=user.id,
            ig_username="test_instagram_user",
            cookies_json=test_cookies,
            fernet=fernet,
            proxy_id=None,
            ttl_days=30
        )
        
        print(f"✅ Saved Instagram session: ID={ig_session.id}, username={ig_session.username}")
        
        # Test getting active session
        active_session = get_active_session(session, user.id)
        assert active_session is not None, "Active session not found"
        assert active_session.id == ig_session.id, "Wrong session returned"
        print(f"✅ Retrieved active session: ID={active_session.id}")
        
        # Test decoding cookies
        decoded_cookies = decode_cookies(fernet, active_session.cookies)
        assert len(decoded_cookies) == 3, f"Expected 3 cookies, got {len(decoded_cookies)}"
        assert decoded_cookies[0]["name"] == "sessionid", "First cookie name mismatch"
        print(f"✅ Decoded cookies correctly: {len(decoded_cookies)} cookies")
        
        # Test session info
        print(f"📊 Session info:")
        print(f"   ID: {ig_session.id}")
        print(f"   Username: {ig_session.username}")
        print(f"   Active: {ig_session.is_active}")
        print(f"   Created: {ig_session.created_at}")
        print(f"   Expires: {ig_session.expires_at}")
        print(f"   Proxy ID: {ig_session.proxy_id}")


def test_imports():
    """Test all Instagram-related imports."""
    print("\n📦 Testing imports...")
    
    try:
        from project.services.ig_sessions import save_session, get_active_session, decode_cookies
        print("✅ ig_sessions imports OK")
    except ImportError as e:
        print(f"❌ ig_sessions import failed: {e}")
        return False
    
    try:
        from project.services.ig_requests import fetch_with_cookies, cookies_jar_from_list
        print("✅ ig_requests imports OK")
    except ImportError as e:
        print(f"❌ ig_requests import failed: {e}")
        return False
    
    try:
        from project.services.ig_profile_loggedin import parse_profile_html
        print("✅ ig_profile_loggedin imports OK")
    except ImportError as e:
        print(f"❌ ig_profile_loggedin import failed: {e}")
        return False
    
    try:
        from project.services.checker_ig_session import check_username_via_ig_session
        print("✅ checker_ig_session imports OK")
    except ImportError as e:
        print(f"❌ checker_ig_session import failed: {e}")
        return False
    
    try:
        from project.services.ig_login import playwright_login_and_get_cookies
        print("✅ ig_login imports OK")
    except ImportError as e:
        print(f"❌ ig_login import failed: {e}")
        return False
    
    return True


def test_config():
    """Test Instagram configuration."""
    print("\n⚙️ Testing Instagram configuration...")
    
    settings = get_settings()
    
    # Test encryption key
    print(f"🔐 Encryption key: {'Set' if settings.encryption_key else 'Not set'}")
    
    # Test Instagram settings
    print(f"📱 Instagram headless: {settings.ig_headless}")
    print(f"⏱️ Login timeout: {settings.ig_login_timeout_ms}ms")
    print(f"⏱️ 2FA timeout: {settings.ig_2fa_timeout_ms}ms")
    print(f"📸 Header selector: {settings.ig_screenshot_header_selector}")
    print(f"📸 Fallback selector: {settings.ig_screenshot_fallback_selector}")
    
    print("✅ Configuration loaded successfully")


def main():
    """Run all tests."""
    print("🧪 INSTAGRAM SESSION TESTING")
    print("=" * 50)
    
    try:
        test_imports()
        test_config()
        test_encryption()
        test_ig_sessions()
        
        print("\n🎉 All Instagram session tests passed!")
        print("=" * 50)
        print("✅ Instagram session functionality is ready!")
        print("📱 You can now:")
        print("   • Add Instagram sessions via cookies import")
        print("   • Check accounts through Instagram sessions")
        print("   • Use encrypted cookie storage")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
