"""Cleanup expired Instagram sessions."""

import sys
import os

# Add project directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from project.services.ig_sessions import get_active_session, is_session_expired, mark_session_inactive
    from project.utils.encryptor import OptionalFernet
    from project.config import get_settings
    from project.database import get_engine, get_session_factory
    from project.models import User, InstagramSession
except ImportError as e:
    print(f"Import error: {e}")
    # Try alternative import path
    try:
        sys.path.append('project')
        from services.ig_sessions import get_active_session, is_session_expired, mark_session_inactive
        from utils.encryptor import OptionalFernet
        from config import get_settings
        from database import get_engine, get_session_factory
        from models import User, InstagramSession
    except ImportError as e2:
        print(f"Alternative import error: {e2}")
        sys.exit(1)


def cleanup_expired_sessions():
    """Check and mark expired sessions as inactive."""
    settings = get_settings()
    fernet = OptionalFernet(settings.encryption_key)
    
    # Initialize database
    engine = get_engine(settings.db_url)
    session_factory = get_session_factory(engine)
    
    with session_factory() as session:
        # Get all active sessions
        active_sessions = session.query(InstagramSession).filter(
            InstagramSession.is_active == True
        ).all()
        
        print(f"🔍 Found {len(active_sessions)} active sessions to check")
        
        cleaned_count = 0
        for ig_session in active_sessions:
            try:
                print(f"📱 Checking session @{ig_session.username} (ID: {ig_session.id})")
                
                if is_session_expired(ig_session, fernet):
                    mark_session_inactive(session, ig_session)
                    cleaned_count += 1
                    print(f"✅ Marked @{ig_session.username} as inactive")
                else:
                    print(f"✅ Session @{ig_session.username} is still valid")
                    
            except Exception as e:
                print(f"❌ Error checking session @{ig_session.username}: {e}")
        
        print(f"🧹 Cleanup complete: {cleaned_count} sessions marked as inactive")


if __name__ == "__main__":
    print("🧹 Cleaning up expired Instagram sessions...")
    cleanup_expired_sessions()
