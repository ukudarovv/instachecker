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
) -> InstagramSession:
    """Save Instagram session with encrypted cookies."""
    raw = json.dumps(cookies_json, ensure_ascii=False)
    enc = fernet.encrypt(raw)
    obj = InstagramSession(
        user_id=user_id,
        username=ig_username,
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
