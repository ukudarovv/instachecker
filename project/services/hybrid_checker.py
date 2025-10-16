"""Hybrid checker: API + Instagram with screenshots."""

from __future__ import annotations
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import date

try:
    from ..models import Account, InstagramSession
    from .check_via_api import check_account_exists_via_api
    from .ig_simple_checker import check_account_with_screenshot
    from .ig_sessions import get_active_session, decode_cookies
    from ..utils.encryptor import OptionalFernet
    from ..config import get_settings
except ImportError:
    from models import Account, InstagramSession
    from services.check_via_api import check_account_exists_via_api
    from services.ig_simple_checker import check_account_with_screenshot
    from services.ig_sessions import get_active_session, decode_cookies
    from utils.encryptor import OptionalFernet
    from config import get_settings


async def check_account_hybrid(
    session: Session,
    user_id: int,
    username: str,
    ig_session: Optional[InstagramSession] = None,
    fernet: Optional[OptionalFernet] = None,
    skip_instagram_verification: bool = False
) -> Dict[str, Any]:
    """
    Hybrid check: API + Instagram screenshot.
    
    Process:
    1. Check via RapidAPI (fast, uses quota)
    2. If exists and IG session available - take screenshot (unless skip_instagram_verification=True)
    3. Return combined result
    
    Args:
        session: Database session
        user_id: User ID
        username: Instagram username to check
        ig_session: Optional Instagram session for screenshots
        fernet: Optional encryptor for cookies
        skip_instagram_verification: If True, skip Instagram check even if account found via API
        
    Returns:
        Dict with check results: {
            "username": str,
            "exists": bool | None,
            "full_name": str | None,
            "followers": int | None,
            "following": int | None,
            "posts": int | None,
            "screenshot_path": str | None,
            "error": str | None,
            "checked_via": str  # "api", "api+instagram", "instagram_only"
        }
    """
    settings = get_settings()
    
    result = {
        "username": username,
        "exists": None,
        "full_name": None,
        "followers": None,
        "following": None,
        "posts": None,
        "screenshot_path": None,
        "error": None,
        "checked_via": "api"
    }
    
    # Step 1: Check via API first (fast)
    api_result = await check_account_exists_via_api(session, user_id, username)
    
    if api_result["exists"] is None:
        # API check failed - try Instagram only if available
        if ig_session and fernet:
            result["checked_via"] = "instagram_only"
            try:
                cookies = decode_cookies(fernet, ig_session.cookies)
                ig_result = await check_account_with_screenshot(
                    username=username,
                    cookies=cookies,
                    headless=settings.ig_headless,
                    timeout_ms=30000
                )
                
                result["exists"] = ig_result.get("exists")
                result["full_name"] = ig_result.get("full_name")
                result["followers"] = ig_result.get("followers")
                result["following"] = ig_result.get("following")
                result["posts"] = ig_result.get("posts")
                result["screenshot_path"] = ig_result.get("screenshot_path")
                result["error"] = ig_result.get("error")
                
                # Mark as done if found via Instagram
                if result["exists"] is True:
                    acc = session.query(Account).filter(
                        Account.user_id == user_id,
                        Account.account == username
                    ).first()
                    if acc:
                        acc.done = True
                        acc.date_of_finish = date.today()
                        session.commit()
                
            except Exception as e:
                result["error"] = f"instagram_error: {str(e)}"
        else:
            result["error"] = api_result.get("error", "api_failed_no_ig_session")
        
        return result
    
    # Step 2: API found result
    result["exists"] = api_result["exists"]
    
    if api_result["exists"] is False:
        # Not found via API - no need for screenshot
        result["checked_via"] = "api"
        return result
    
    # Step 3: Account exists via API - VERIFY with Instagram if session available
    if api_result["exists"] is True and ig_session and fernet and not skip_instagram_verification:
        result["checked_via"] = "api+instagram"
        try:
            cookies = decode_cookies(fernet, ig_session.cookies)
            ig_result = await check_account_with_screenshot(
                username=username,
                cookies=cookies,
                headless=settings.ig_headless,
                timeout_ms=30000
            )
            
            # CRITICAL: If Instagram says NOT FOUND, override API result
            # This means the account was deleted/suspended after API cache was updated
            if ig_result.get("exists") is False:
                result["exists"] = False
                result["error"] = "api_found_but_instagram_not_found"
                print(f"⚠️ API says exists, but Instagram says NOT FOUND for @{username}")
                # Don't mark as done - account is not active
                return result
            
            # Instagram confirms account exists or is private
            if ig_result.get("exists") is True:
                # Merge Instagram data
                result["full_name"] = ig_result.get("full_name")
                result["followers"] = ig_result.get("followers")
                result["following"] = ig_result.get("following")
                result["posts"] = ig_result.get("posts")
                result["screenshot_path"] = ig_result.get("screenshot_path")
                
                # Mark as done - both API and Instagram confirm
                print(f"✅ Both API and Instagram confirm @{username} is active")
            else:
                # Instagram check had an error - keep API result but note the issue
                result["error"] = f"instagram_verification_error: {ig_result.get('error', 'unknown')}"
                print(f"⚠️ API found @{username}, but Instagram verification failed: {result['error']}")
                # Still keep exists=True from API in this case
                
        except Exception as e:
            result["error"] = f"instagram_verification_failed: {str(e)}"
            print(f"⚠️ Failed to verify @{username} via Instagram: {str(e)}")
            # Keep API result if Instagram check completely failed
    
    return result


async def check_multiple_accounts_hybrid(
    session: Session,
    user_id: int,
    usernames: list,
    ig_session: Optional[InstagramSession] = None,
    fernet: Optional[OptionalFernet] = None
) -> list:
    """
    Check multiple accounts using hybrid method.
    
    Args:
        session: Database session
        user_id: User ID
        usernames: List of usernames to check
        ig_session: Optional Instagram session
        fernet: Optional encryptor
        
    Returns:
        List of check results
    """
    results = []
    
    for username in usernames:
        try:
            result = await check_account_hybrid(
                session=session,
                user_id=user_id,
                username=username,
                ig_session=ig_session,
                fernet=fernet
            )
            results.append(result)
        except Exception as e:
            results.append({
                "username": username,
                "exists": None,
                "error": str(e),
                "screenshot_path": None,
                "checked_via": "error"
            })
    
    return results

