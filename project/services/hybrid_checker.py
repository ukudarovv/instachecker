"""Hybrid checker: API + Instagram with screenshots."""

from __future__ import annotations
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import date

try:
    from ..models import Account, InstagramSession, Proxy
    from .check_via_api import check_account_exists_via_api
    from .ig_simple_checker import check_account_with_screenshot
    from .proxy_checker import check_account_via_proxy_with_screenshot
    from .ig_sessions import get_active_session, decode_cookies
    from ..utils.encryptor import OptionalFernet
    from ..config import get_settings
except ImportError:
    from models import Account, InstagramSession, Proxy
    from services.check_via_api import check_account_exists_via_api
    from services.ig_simple_checker import check_account_with_screenshot
    from services.proxy_checker import check_account_via_proxy_with_screenshot
    from services.ig_sessions import get_active_session, decode_cookies
    from utils.encryptor import OptionalFernet
    from config import get_settings


async def check_account_hybrid(
    session: Session,
    user_id: int,
    username: str,
    ig_session: Optional[InstagramSession] = None,
    fernet: Optional[OptionalFernet] = None,
    skip_instagram_verification: bool = False,
    verify_mode: str = "api+instagram"
) -> Dict[str, Any]:
    """
    Hybrid check: API + (Instagram or Proxy).
    
    Process:
    1. Check via RapidAPI (fast, uses quota)
    2. If exists:
       - If verify_mode='api+instagram' and IG session available - Instagram screenshot
       - If verify_mode='api+proxy' and proxy available - Proxy screenshot (no login)
    3. Return combined result
    
    Args:
        session: Database session
        user_id: User ID
        username: Instagram username to check
        ig_session: Optional Instagram session for screenshots (for api+instagram mode)
        fernet: Optional encryptor for cookies
        skip_instagram_verification: If True, skip verification even if account found via API
        verify_mode: Verification mode ('api+instagram' or 'api+proxy')
        
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
    
    # Step 3: Account exists via API - VERIFY with Instagram or Proxy
    if api_result["exists"] is True and not skip_instagram_verification:
        # Choose verification method based on verify_mode
        if verify_mode == "api+instagram" and ig_session and fernet:
            # INSTAGRAM VERIFICATION (with login)
            result["checked_via"] = "api+instagram"
            print(f"📸 Using INSTAGRAM verification (with cookies and login) for @{username}")
            try:
                cookies = decode_cookies(fernet, ig_session.cookies)
                ig_result = await check_account_with_screenshot(
                    username=username,
                    cookies=cookies,
                    headless=settings.ig_headless,
                    timeout_ms=30000
                )
                
                # CRITICAL: If Instagram says NOT FOUND, override API result
                if ig_result.get("exists") is False:
                    result["exists"] = False
                    result["error"] = "api_found_but_instagram_not_found"
                    print(f"⚠️ API says exists, but Instagram says NOT FOUND for @{username}")
                    return result
                
                # Instagram confirms account exists
                if ig_result.get("exists") is True:
                    result["full_name"] = ig_result.get("full_name")
                    result["followers"] = ig_result.get("followers")
                    result["following"] = ig_result.get("following")
                    result["posts"] = ig_result.get("posts")
                    result["screenshot_path"] = ig_result.get("screenshot_path")
                    print(f"✅ Both API and Instagram confirm @{username} is active")
                else:
                    result["error"] = f"instagram_verification_error: {ig_result.get('error', 'unknown')}"
                    print(f"⚠️ API found @{username}, but Instagram verification failed: {result['error']}")
                    
            except Exception as e:
                result["error"] = f"instagram_error: {str(e)}"
                print(f"❌ Instagram check error for @{username}: {str(e)}")
        
        elif verify_mode == "api+proxy":
            # PROXY VERIFICATION (without login)
            result["checked_via"] = "api+proxy"
            print(f"🌐 Using PROXY verification (no cookies, no login) for @{username}")
            try:
                # Get user's active proxy
                proxy = session.query(Proxy).filter(
                    Proxy.user_id == user_id,
                    Proxy.is_active == True
                ).order_by(Proxy.priority.asc()).first()
                
                if proxy:
                    # Generate screenshot path
                    import os
                    from datetime import datetime
                    screenshot_dir = "screenshots"
                    os.makedirs(screenshot_dir, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_path = os.path.join(screenshot_dir, f"ig_{username}_{timestamp}.png")
                    
                    proxy_result = await check_account_via_proxy_with_screenshot(
                        username=username,
                        proxy=proxy,
                        headless=settings.ig_headless,
                        timeout_ms=30000,
                        screenshot_path=screenshot_path
                    )
                    
                    # CRITICAL: If proxy says NOT FOUND, override API result
                    if proxy_result.get("exists") is False:
                        result["exists"] = False
                        result["error"] = "api_found_but_proxy_not_found"
                        print(f"⚠️ API says exists, but Proxy says NOT FOUND for @{username}")
                        return result
                    
                    # Proxy confirms account exists
                    if proxy_result.get("exists") is True:
                        result["screenshot_path"] = proxy_result.get("screenshot_path")
                        result["is_private"] = proxy_result.get("is_private")
                        print(f"✅ Both API and Proxy confirm @{username} is active")
                    else:
                        # If proxy failed (connection error, etc.), don't consider it successful
                        result["error"] = f"proxy_verification_error: {proxy_result.get('error', 'unknown')}"
                        print(f"⚠️ API found @{username}, but Proxy verification failed: {result['error']}")
                        
                        # If it's a connection error, mark as not found
                        proxy_error = str(proxy_result.get('error', ''))
                        if any(err in proxy_error for err in [
                            "ERR_TUNNEL_CONNECTION_FAILED",
                            "ERR_PROXY_CONNECTION_FAILED", 
                            "ERR_CONNECTION_REFUSED",
                            "ERR_TIMED_OUT"
                        ]):
                            result["exists"] = False
                            print(f"❌ Proxy connection failed for @{username}, marking as not found")
                            return result
                else:
                    result["error"] = "no_active_proxy"
                    print(f"⚠️ No active proxy found for user {user_id} - skipping @{username}")
                    result["exists"] = False
                    
            except Exception as e:
                result["error"] = f"proxy_error: {str(e)}"
                print(f"❌ Proxy check error for @{username}: {str(e)}")
    
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

