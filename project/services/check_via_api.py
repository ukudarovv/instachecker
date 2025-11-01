"""Account checking service via RapidAPI."""

from __future__ import annotations
from typing import Dict, Any
import time
import uuid
from aiohttp import ClientSession, ClientTimeout
from sqlalchemy.orm import Session
from datetime import date

try:
    from ..models import Account, APIKey
    from .api_keys import pick_best_key, incr_usage, set_work_status, _reset_if_new_day
    from .traffic_monitor import get_traffic_monitor
    from ..config import get_settings
    from sqlalchemy import and_
except ImportError:
    from models import Account, APIKey
    from services.api_keys import pick_best_key, incr_usage, set_work_status, _reset_if_new_day
    from services.traffic_monitor import get_traffic_monitor
    from config import get_settings
    from sqlalchemy import and_


async def check_account_exists_via_api(session: Session, user_id: int, username: str) -> Dict[str, Any]:
    """
    Check if Instagram account exists via RapidAPI with automatic key rotation.

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

    # Get all available keys for user
    all_keys = (
        session.query(APIKey)
        .filter(and_(APIKey.user_id == user_id, APIKey.is_work == True))
        .order_by(APIKey.id.asc())
        .all()
    )

    if not all_keys:
        print(f"❌ No API keys available for user {user_id}")
        return {
            "username": username,
            "exists": None,
            "error": "no_api_keys_available"
        }

    # Try each key until we find one that works
    for key in all_keys:
        _reset_if_new_day(key)

        # Skip if key has reached daily limit
        if (key.qty_req or 0) >= settings.api_daily_limit:
            print(f"⚠️ API key {key.id} has reached daily limit ({key.qty_req}/{settings.api_daily_limit})")
            continue

        print(f"🔑 Trying API key {key.id} for @{username} (current usage: {key.qty_req or 0}/{settings.api_daily_limit})")

        timeout = ClientTimeout(total=settings.rapidapi_timeout_seconds)
        headers = {
            "X-RapidAPI-Key": key.key,
            "X-RapidAPI-Host": settings.rapidapi_host,
            "Content-Type": "application/json"
        }
        payload = {"username": username.lower()}
        
        # Initialize traffic monitoring
        monitor = get_traffic_monitor()
        request_id = str(uuid.uuid4())
        monitor.start_request(request_id, "rapidapi", settings.rapidapi_url)
        
        # Calculate request size
        import json as json_lib
        request_size = len(settings.rapidapi_url.encode('utf-8'))
        request_size += len(str(headers).encode('utf-8'))
        request_size += len(json_lib.dumps(payload).encode('utf-8'))

        try:
            start_time = time.time()
            async with ClientSession(timeout=timeout, headers=headers) as sess:
                async with sess.post(settings.rapidapi_url, json=payload) as resp:
                    # Parse response
                    response_text = await resp.text()
                    
                    # Calculate response size and duration
                    response_size = len(response_text.encode('utf-8'))
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # End traffic monitoring
                    monitor.end_request(
                        request_id=request_id,
                        success=True,
                        status_code=resp.status,
                        request_size=request_size,
                        response_size=response_size,
                        duration_ms=duration_ms
                    )
                    
                    # Parse JSON from text
                    import json as json_lib
                    data = json_lib.loads(response_text)

                    # Debug logging
                    print(f"[API-DEBUG] Response for @{username}: {data}")

                    # Check for quota exceeded error
                    if isinstance(data, dict) and "message" in data:
                        if "exceeded the DAILY quota" in data["message"]:
                            print(f"⚠️ API key {key.id} exceeded daily quota - setting to 950 and trying next key")
                            key.qty_req = 950  # Set to max limit
                            session.commit()
                            continue  # Try next key
                        elif "quota" in data["message"].lower():
                            print(f"⚠️ API key {key.id} quota issue: {data['message']}")
                            key.qty_req = 950  # Set to max limit
                            session.commit()
                            continue  # Try next key

                    # Count usage for successful request
                    incr_usage(session, key)

                    # Check if account exists according to new API schema
                    exists = False
                    if isinstance(data, dict):
                        # Check for success response with result
                        if "result" in data and data["result"]:
                            result_data = data["result"]
                            exists = result_data.get("username", "").lower() == username.lower()
                            print(f"[API-DEBUG] Success format: username={result_data.get('username')}, expected={username.lower()}")
                        # Check for error response
                        elif "success" in data and data["success"] is False:
                            exists = False
                            print(f"[API-DEBUG] Error format: success={data.get('success')}, message={data.get('message')}")
                        else:
                            print(f"[API-DEBUG] Unexpected dict format: {data}")
                    else:
                        print(f"[API-DEBUG] Unexpected data format: {type(data)}")

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
            print(f"❌ Error with API key {key.id}: {e}")
            
            # End traffic monitoring for failed request
            try:
                duration_ms = (time.time() - start_time) * 1000 if 'start_time' in locals() else 0
                monitor.end_request(
                    request_id=request_id,
                    success=False,
                    status_code=0,
                    request_size=request_size if 'request_size' in locals() else 0,
                    response_size=0,
                    duration_ms=duration_ms
                )
            except:
                pass
            
            # Mark key as potentially problematic but don't give up yet
            set_work_status(session, key, ok=False)
            continue  # Try next key

    # If we get here, all keys failed
    print(f"❌ All API keys exhausted for user {user_id}")
    return {
        "username": username,
        "exists": None,
        "error": "all_api_keys_exhausted"
    }