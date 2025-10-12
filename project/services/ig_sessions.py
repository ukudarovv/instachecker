"""Instagram session management services."""

import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
try:
    from ..models import InstagramSession
    from ..utils.encryptor import OptionalFernet
except ImportError:
    from models import InstagramSession
    from utils.encryptor import OptionalFernet


def save_session(
    session: Session,
    user_id: int,
    ig_username: str,
    cookies_json: List[Dict[str, Any]],
    fernet: OptionalFernet,
    ttl_days: int = 30,
    ig_password: Optional[str] = None,
) -> InstagramSession:
    """Save Instagram session with encrypted cookies and optional password."""
    raw = json.dumps(cookies_json, ensure_ascii=False)
    enc = fernet.encrypt(raw)
    
    # Encrypt password if provided
    enc_password = None
    if ig_password:
        enc_password = fernet.encrypt(ig_password)
    
    obj = InstagramSession(
        user_id=user_id,
        username=ig_username,
        password=enc_password,
        cookies=enc,
        is_active=True,
        last_used=datetime.utcnow(),
        expires_at=(datetime.utcnow() + timedelta(days=ttl_days)),
    )
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


def get_active_session(session: Session, user_id: int) -> Optional[InstagramSession]:
    """Get active Instagram session for user."""
    return (
        session.query(InstagramSession)
        .filter(InstagramSession.user_id == user_id, InstagramSession.is_active == True)
        .order_by(InstagramSession.last_used.desc())
        .first()
    )


def is_session_expired(ig_session: InstagramSession, fernet: OptionalFernet) -> bool:
    """Check if Instagram session cookies are expired."""
    try:
        cookies = decode_cookies(fernet, ig_session.cookies)
        
        print(f"🍪 Checking session @{ig_session.username} with {len(cookies)} cookies")
        
        # Debug: show all cookie names
        cookie_names = [c.get('name', 'unknown') for c in cookies]
        print(f"🍪 Cookie names: {', '.join(cookie_names[:10])}{'...' if len(cookie_names) > 10 else ''}")
        
        # Look for sessionid cookie which is crucial for Instagram
        sessionid_cookie = None
        for cookie in cookies:
            if cookie.get('name') == 'sessionid':
                sessionid_cookie = cookie
                break
        
        if not sessionid_cookie:
            print(f"❌ No sessionid cookie found - session invalid for @{ig_session.username}")
            print(f"ℹ️ This usually means the login didn't complete successfully")
            return True
        
        # Check if sessionid has expired
        expires = sessionid_cookie.get('expires', -1)
        if expires != -1 and expires > 0:
            import time
            current_time = int(time.time())
            if current_time >= expires:
                print(f"❌ Sessionid cookie expired (expires: {expires}, current: {current_time})")
                return True
        
        print(f"✅ Sessionid cookie is valid for @{ig_session.username}")
        return False
        
    except Exception as e:
        print(f"❌ Error checking session validity: {e}")
        return True


def mark_session_inactive(session: Session, ig_session: InstagramSession) -> None:
    """Mark Instagram session as inactive."""
    ig_session.is_active = False
    session.commit()
    print(f"⚠️ Marked session @{ig_session.username} as inactive")


def get_valid_session(session: Session, user_id: int, fernet: OptionalFernet) -> Optional[InstagramSession]:
    """Get valid Instagram session for user, checking cookie expiration."""
    ig_session = get_active_session(session, user_id)
    
    if not ig_session:
        print("❌ No active session found")
        return None
    
    if is_session_expired(ig_session, fernet):
        print(f"⚠️ Session @{ig_session.username} is expired, marking as inactive")
        mark_session_inactive(session, ig_session)
        return None
    
    print(f"✅ Valid session found: @{ig_session.username}")
    return ig_session


def decode_cookies(fernet: OptionalFernet, cookies_enc: str) -> List[Dict[str, Any]]:
    """Decode encrypted cookies to JSON list."""
    return json.loads(fernet.decrypt(cookies_enc))


def update_session_cookies(
    session: Session,
    session_id: int,
    new_cookies: List[Dict[str, Any]],
    fernet: OptionalFernet
) -> None:
    """Update cookies for an existing Instagram session."""
    ig_session = session.query(InstagramSession).filter(InstagramSession.id == session_id).first()
    if ig_session:
        raw = json.dumps(new_cookies, ensure_ascii=False)
        enc = fernet.encrypt(raw)
        ig_session.cookies = enc
        ig_session.last_used = datetime.utcnow()
        session.commit()


def decode_password(fernet: OptionalFernet, password_enc: str) -> str:
    """Decode encrypted password."""
    return fernet.decrypt(password_enc)
