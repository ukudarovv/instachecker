"""Test Instagram session functionality."""

import asyncio
import sys
import os

# Add project directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from project.services.ig_sessions import get_active_session, decode_cookies, decode_password
    from project.utils.encryptor import OptionalFernet
    from project.config import get_settings
    from project.database import get_engine, get_session_factory
    from project.models import User, InstagramSession
    from sqlalchemy.orm import sessionmaker
except ImportError as e:
    print(f"Import error: {e}")
    # Try alternative import path
    try:
        import sys
        sys.path.append('project')
        from services.ig_sessions import get_active_session, decode_cookies, decode_password
        from utils.encryptor import OptionalFernet
        from config import get_settings
        from database import get_engine, get_session_factory
        from models import User, InstagramSession
        from sqlalchemy.orm import sessionmaker
    except ImportError as e2:
        print(f"Alternative import error: {e2}")
        sys.exit(1)


async def test_session():
    """Test Instagram session functionality."""
    settings = get_settings()
    fernet = OptionalFernet(settings.encryption_key)
    
    # Initialize database
    engine = get_engine(settings.db_url)
    session_factory = get_session_factory(engine)
    
    with session_factory() as session:
        # Get first user with IG session
        user = session.query(User).join(InstagramSession).first()
        
        if not user:
            print("❌ No users with IG sessions found")
            return
        
        print(f"👤 Testing with user: {user.username} (ID: {user.id})")
        
        # Get active session
        ig_session = get_active_session(session, user.id)
        
        if not ig_session:
            print("❌ No active IG session found for user")
            return
        
        print(f"📱 Found IG session: @{ig_session.username} (ID: {ig_session.id})")
        
        # Decode cookies
        try:
            cookies = decode_cookies(fernet, ig_session.cookies)
            print(f"🍪 Decoded {len(cookies)} cookies")
            
            # Show cookie names
            cookie_names = [c.get('name', 'unknown') for c in cookies]
            print(f"🍪 Cookie names: {', '.join(cookie_names[:5])}{'...' if len(cookie_names) > 5 else ''}")
            
        except Exception as e:
            print(f"❌ Failed to decode cookies: {e}")
            return
        
        # Decode password if available
        ig_password = None
        if ig_session.password:
            try:
                ig_password = decode_password(fernet, ig_session.password)
                print(f"🔑 Password decoded successfully")
            except Exception as e:
                print(f"⚠️ Failed to decode password: {e}")
        else:
            print("⚠️ No password stored for this session")
        
        # Test session with simple checker
        try:
            from project.services.ig_simple_checker import check_account_with_screenshot
            
            print(f"🔍 Testing session with profile check...")
            
            result = await check_account_with_screenshot(
                username="instagram",  # Test with Instagram's own profile
                cookies=cookies,
                headless=True,
                timeout_ms=30000,
                ig_username=ig_session.username,
                ig_password=ig_password,
                session_db_update_callback=None  # Don't update DB in test
            )
            
            print(f"📊 Test result:")
            print(f"  - Username: {result.get('username')}")
            print(f"  - Exists: {result.get('exists')}")
            print(f"  - Error: {result.get('error')}")
            print(f"  - Screenshot: {'Yes' if result.get('screenshot_path') else 'No'}")
            
            if result.get('error'):
                print(f"❌ Test failed: {result['error']}")
            else:
                print(f"✅ Test completed successfully")
                
        except Exception as e:
            print(f"❌ Test error: {e}")


if __name__ == "__main__":
    print("🧪 Testing Instagram session functionality...")
    asyncio.run(test_session())
