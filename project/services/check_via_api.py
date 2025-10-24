"""Account checking service via RapidAPI."""

from __future__ import annotations
from typing import Dict, Any
from aiohttp import ClientSession, ClientTimeout
from sqlalchemy.orm import Session
from datetime import date

try:
    from ..models import Account, APIKey
    from .api_keys import pick_best_key, incr_usage, set_work_status
    from ..config import get_settings
except ImportError:
    from models import Account, APIKey
    from services.api_keys import pick_best_key, incr_usage, set_work_status
    from config import get_settings


async def check_account_exists_via_api(session: Session, user_id: int, username: str) -> Dict[str, Any]:
    """
    Check if Instagram account exists via RapidAPI.
    
    Args:
        session: Database session
        user_id: User ID
        username: Instagram username to check
        
    Returns:
        Dict with check results: {
            "username": str,
            "exists": bool | None,
            "error": str | None
        }
    """
    settings = get_settings()
    key = pick_best_key(session, user_id)
    
    if not key:
        print(f"❌ No available API key for user {user_id} (all keys may have reached daily limit)")
        return {
            "username": username,
            "exists": None,
            "error": "no_available_api_key"
        }
    
    print(f"🔑 Using API key {key.id} for @{username} (current usage: {key.qty_req or 0}/{settings.api_daily_limit})")

    timeout = ClientTimeout(total=settings.rapidapi_timeout_seconds)
    headers = {
        "X-RapidAPI-Key": key.key,
        "X-RapidAPI-Host": settings.rapidapi_host
    }
    params = {"ig": username.lower()}

    try:
        async with ClientSession(timeout=timeout, headers=headers) as sess:
            async with sess.get(settings.rapidapi_url, params=params) as resp:
                # Count usage even if response is not found
                incr_usage(session, key)

                # Parse response
                data = await resp.json(content_type=None)
                
                # Check if account exists according to your schema
                exists = False
                if isinstance(data, list) and data:
                    exists = (data[0] or {}).get("username") == username.lower()
                elif isinstance(data, dict):
                    exists = (data.get("username") == username.lower())

                if exists:
                    # Mark account as done
                    acc = session.query(Account).filter(
                        Account.user_id == user_id,
                        Account.account == username
                    ).first()
                    if acc:
                        acc.done = True
                        acc.date_of_finish = date.today()
                        session.commit()
                    
                    return {
                        "username": username,
                        "exists": True,
                        "error": None
                    }
                else:
                    return {
                        "username": username,
                        "exists": False,
                        "error": None
                    }
    except Exception as e:
        # Don't mark key as non-working after single failure
        # (we can implement streak-based marking later)
        set_work_status(session, key, ok=True)
        return {
            "username": username,
            "exists": None,
            "error": str(e)
        }

