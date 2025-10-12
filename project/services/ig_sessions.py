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
