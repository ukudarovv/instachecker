"""API keys management service."""

from __future__ import annotations
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_
from aiohttp import ClientSession, ClientTimeout

try:
    from ..models import APIKey
    from ..config import get_settings
except ImportError:
    from models import APIKey
    from config import get_settings


def _reset_if_new_day(obj: APIKey) -> None:
    """Reset counter if a new day has started."""
    today = date.today()
    if obj.ref_date is None or obj.ref_date.date() != today:
        obj.ref_date = datetime.utcnow()
        obj.qty_req = 0


def list_keys_for_user(session: Session, user_id: int) -> List[APIKey]:
    """
    List all API keys for a user.
    
    Args:
        session: Database session
        user_id: User ID
        
    Returns:
        List of API keys sorted by status and usage
    """
    keys = (
        session.query(APIKey)
        .filter(APIKey.user_id == user_id)
        .order_by(APIKey.is_work.desc(), APIKey.qty_req.asc())
        .all()
    )
    # Update ref_date/qty_req on the fly (display only, not saving)
    for k in keys:
        _reset_if_new_day(k)
    return keys


def pick_best_key(session: Session, user_id: int) -> Optional[APIKey]:
    """
    Pick the best working API key with rotation logic.
    Keys are used in order, and when one reaches the limit (950), 
    the system moves to the next key.
    
    Args:
        session: Database session
        user_id: User ID
        
    Returns:
        Best available API key or None
    """
    settings = get_settings()
    keys = (
        session.query(APIKey)
        .filter(and_(APIKey.user_id == user_id, APIKey.is_work == True))
        .order_by(APIKey.id.asc())  # Use keys in order of creation (rotation)
        .all()
    )
    
    for k in keys:
        _reset_if_new_day(k)
        # Check if this key hasn't reached the daily limit
        if (k.qty_req or 0) < settings.api_daily_limit:
            return k
    
    return None


def incr_usage(session: Session, key: APIKey) -> None:
    """
    Increment usage counter for an API key.
    
    Args:
        session: Database session
        key: API key to increment
    """
    _reset_if_new_day(key)
    old_count = key.qty_req or 0
    key.qty_req = old_count + 1
    key.ref_date = datetime.utcnow()
    session.commit()
    
    # Log usage for monitoring
    settings = get_settings()
    remaining = settings.api_daily_limit - key.qty_req
    print(f"🔑 API Key {key.id}: {key.qty_req}/{settings.api_daily_limit} requests used (remaining: {remaining})")
    
    # Warn when approaching limit
    if remaining <= 50:
        print(f"⚠️ API Key {key.id} is approaching limit: {remaining} requests remaining")


def set_work_status(session: Session, key: APIKey, ok: bool) -> None:
    """
    Set work status for an API key.
    
    Args:
        session: Database session
        key: API key to update
        ok: Working status
    """
    key.is_work = bool(ok)
    session.commit()


def get_api_keys_status(session: Session, user_id: int) -> List[Dict[str, Any]]:
    """
    Get status information for all API keys of a user.
    
    Args:
        session: Database session
        user_id: User ID
        
    Returns:
        List of dictionaries with key status information
    """
    settings = get_settings()
    keys = (
        session.query(APIKey)
        .filter(APIKey.user_id == user_id)
        .order_by(APIKey.id.asc())
        .all()
    )
    
    status_list = []
    for key in keys:
        _reset_if_new_day(key)
        remaining = max(0, settings.api_daily_limit - (key.qty_req or 0))
        status_list.append({
            "id": key.id,
            "key": key.key[:8] + "..." if len(key.key) > 8 else key.key,
            "qty_req": key.qty_req or 0,
            "limit": settings.api_daily_limit,
            "remaining": remaining,
            "is_work": key.is_work,
            "ref_date": key.ref_date,
            "is_available": key.is_work and remaining > 0
        })
    
    return status_list


async def test_api_key(key_value: str, test_username: str = "instagram") -> Tuple[bool, Optional[str]]:
    """
    Test API key with a test request to RapidAPI.
    
    Args:
        key_value: API key to test
        test_username: Username to test with (default: "instagram")
        
    Returns:
        Tuple of (success: bool, error: Optional[str])
    """
    settings = get_settings()
    timeout = ClientTimeout(total=settings.rapidapi_timeout_seconds)
    headers = {
        "X-RapidAPI-Key": key_value,
        "X-RapidAPI-Host": settings.rapidapi_host
    }
    params = {"ig": test_username.lower()}
    
    try:
        async with ClientSession(timeout=timeout, headers=headers) as sess:
            async with sess.get(settings.rapidapi_url, params=params) as resp:
                data = await resp.json(content_type=None)
                
                # Check if response is valid according to your schema
                ok = False
                if isinstance(data, list) and data:
                    u = (data[0] or {}).get("username")
                    ok = (u == test_username.lower())
                elif isinstance(data, dict):
                    # Sometimes API returns object instead of array
                    u = data.get("username")
                    ok = (u == test_username.lower())
                
                return ok, None if ok else "unexpected_response"
    except Exception as e:
        return False, str(e)

