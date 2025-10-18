"""Simple checkers: Instagram only, Proxy only, Instagram+Proxy (without API)."""

from __future__ import annotations
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import os
from datetime import datetime

try:
    from ..models import Proxy, InstagramSession
    from .ig_sessions import decode_cookies
    from ..utils.encryptor import OptionalFernet
    from ..config import get_settings
except ImportError:
    from models import Proxy, InstagramSession
    from services.ig_sessions import decode_cookies
    from utils.encryptor import OptionalFernet
    from config import get_settings


async def check_account_instagram_only(
    session: Session,
    user_id: int,
    username: str,
    ig_session: Optional[InstagramSession] = None,
    fernet: Optional[OptionalFernet] = None
) -> Dict[str, Any]:
    """
    Check account using only Instagram (no API, no Proxy).
    
    Args:
        session: Database session
        user_id: User ID
        username: Instagram username to check
        ig_session: Instagram session for login
        fernet: Encryptor for cookies
    
    Returns:
        Dict with check results
    """
    result = {
        "username": username,
        "exists": None,
        "screenshot_path": None,
        "error": None,
        "checked_via": "instagram"
    }
    
    print(f"📸 Instagram-only check for @{username}")
    
    if not ig_session:
        print(f"❌ No Instagram session for user {user_id}")
        result["error"] = "no_instagram_session"
        result["exists"] = False
        return result
    
    # Get settings
    settings = get_settings()
    
    # Decrypt cookies and password
    if not fernet:
        fernet = OptionalFernet(settings.encryption_key)
    
    cookies = decode_cookies(fernet, ig_session.cookies) if ig_session.cookies else []
    ig_username = ig_session.username
    ig_password = fernet.decrypt(ig_session.password) if ig_session.password else None
    
    # Try to get proxy (optional for instagram mode)
    proxy_server = None
    proxy_username = None
    proxy_password = None
    
    try:
        proxy = session.query(Proxy).filter(
            Proxy.user_id == user_id,
            Proxy.is_active == True
        ).order_by(Proxy.priority.asc()).first()
        
        if proxy:
            proxy_server = f"{proxy.scheme}://{proxy.host}"
            proxy_username = proxy.username
            proxy_password = proxy.password
            print(f"✅ Found proxy for Instagram mode: {proxy_server}")
        else:
            print(f"⚠️ No proxy found for Instagram mode - using direct connection")
    except Exception as e:
        print(f"⚠️ Proxy check error: {e} - using direct connection")
    
    # Import check function
    try:
        from .ig_simple_checker import check_account_with_screenshot
    except ImportError:
        from services.ig_simple_checker import check_account_with_screenshot
    
    # Perform Instagram check
    try:
        ig_result = await check_account_with_screenshot(
            username=username,
            cookies=cookies,
            headless=settings.ig_headless,
            timeout_ms=30000,
            ig_username=ig_username,
            ig_password=ig_password,
            proxy_server=proxy_server,
            proxy_username=proxy_username,
            proxy_password=proxy_password
        )
        
        result.update(ig_result)
        print(f"✅ Instagram check complete for @{username}: exists={ig_result.get('exists')}")
        
    except Exception as e:
        print(f"❌ Instagram check error for @{username}: {e}")
        result["error"] = f"instagram_error: {e}"
        result["exists"] = False
    
    return result


async def check_account_proxy_only(
    session: Session,
    user_id: int,
    username: str
) -> Dict[str, Any]:
    """
    Check account using only Proxy (no API, no Instagram login).
    
    Args:
        session: Database session
        user_id: User ID
        username: Instagram username to check
    
    Returns:
        Dict with check results
    """
    result = {
        "username": username,
        "exists": None,
        "screenshot_path": None,
        "error": None,
        "checked_via": "proxy"
    }
    
    print(f"🌐 Proxy-only check for @{username}")
    
    # Check if user has proxy
    proxy = session.query(Proxy).filter(
        Proxy.user_id == user_id,
        Proxy.is_active == True
    ).order_by(Proxy.priority.asc()).first()
    
    if not proxy:
        print(f"❌ No active proxy for user {user_id}")
        result["error"] = "no_active_proxy"
        result["exists"] = False
        return result
    
    print(f"✅ Found active proxy: {proxy.scheme}://{proxy.host}")
    
    # Get settings
    settings = get_settings()
    
    # Prepare screenshot path
    screenshot_dir = "screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(screenshot_dir, f"ig_{username}_{timestamp}.png")
    
    # Import proxy checker
    try:
        from .proxy_checker import check_account_via_proxy_with_fallback
    except ImportError:
        from services.proxy_checker import check_account_via_proxy_with_fallback
    
    # Perform proxy check
    try:
        proxy_result = await check_account_via_proxy_with_fallback(
            session=session,
            user_id=user_id,
            username=username,
            max_attempts=3,
            headless=settings.ig_headless,
            timeout_ms=30000,
            screenshot_path=screenshot_path
        )
        
        result.update(proxy_result)
        print(f"✅ Proxy check complete for @{username}: exists={proxy_result.get('exists')}")
        
    except Exception as e:
        print(f"❌ Proxy check error for @{username}: {e}")
        result["error"] = f"proxy_error: {e}"
        result["exists"] = False
    
    return result


async def check_account_instagram_proxy(
    session: Session,
    user_id: int,
    username: str,
    ig_session: Optional[InstagramSession] = None,
    fernet: Optional[OptionalFernet] = None
) -> Dict[str, Any]:
    """
    Check account using Instagram + Proxy (no API).
    Similar to triple check but without API phase.
    
    Args:
        session: Database session
        user_id: User ID
        username: Instagram username to check
        ig_session: Instagram session for login
        fernet: Encryptor for cookies
    
    Returns:
        Dict with check results
    """
    result = {
        "username": username,
        "exists": None,
        "profile_exists": None,
        "screenshot_path": None,
        "error": None,
        "checked_via": "instagram+proxy",
        "warning": None
    }
    
    print(f"📸🌐 Instagram+Proxy check for @{username}")
    
    # Check if user has proxy
    print(f"🔗 Checking proxy for user {user_id}")
    proxy = session.query(Proxy).filter(
        Proxy.user_id == user_id,
        Proxy.is_active == True
    ).order_by(Proxy.priority.asc()).first()
    
    if not proxy:
        print(f"❌ No active proxy for user {user_id}")
        result["error"] = "no_active_proxy"
        result["exists"] = False
        return result
    
    print(f"✅ Found active proxy: {proxy.scheme}://{proxy.host}")
    
    # Check if user has Instagram session
    print(f"🔐 Checking Instagram session for user {user_id}")
    if not ig_session:
        print(f"❌ No Instagram session for user {user_id}")
        result["error"] = "no_instagram_session"
        result["exists"] = False
        return result
    
    print(f"✅ Found Instagram session: @{ig_session.username}")
    
    # Get settings
    settings = get_settings()
    
    # Decrypt cookies and password
    if not fernet:
        fernet = OptionalFernet(settings.encryption_key)
    
    cookies = decode_cookies(fernet, ig_session.cookies) if ig_session.cookies else []
    ig_username = ig_session.username
    ig_password = fernet.decrypt(ig_session.password) if ig_session.password else None
    
    # Import Playwright checker
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        result["error"] = "playwright_not_installed"
        return result
    
    # Setup proxy config
    proxy_config = {
        "server": f"{proxy.scheme}://{proxy.host}"
    }
    
    if proxy.username and proxy.password:
        proxy_config["username"] = proxy.username
        proxy_config["password"] = proxy.password
        print(f"🔑 Using proxy with authentication")
    
    # Prepare screenshot path
    screenshot_dir = "screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(screenshot_dir, f"ig_{username}_{timestamp}.png")
    
    try:
        async with async_playwright() as p:
            # Launch browser with proxy
            browser = await p.chromium.launch(
                headless=settings.ig_headless,
                proxy=proxy_config,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage'
                ]
            )
            
            # Create context
            context = await browser.new_context()
            
            # Set cookies
            if cookies:
                await context.add_cookies(cookies)
                print(f"🍪 Loaded {len(cookies)} cookies")
            
            page = await context.new_page()
            
            # Navigate to profile page
            url = f"https://www.instagram.com/{username}/"
            print(f"🌐 Navigating to {url}")
            
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
            
            # Check if we need to login
            current_url = page.url
            
            # Check if we're on login page
            if "/accounts/login" in current_url or "Login" in await page.title():
                print(f"🔐 Session expired, attempting to login...")
                
                if not ig_username or not ig_password:
                    print(f"❌ No credentials provided for login")
                    result["error"] = "no_credentials_for_login"
                    result["exists"] = False
                    await browser.close()
                    return result
                
                # Fill login form
                try:
                    await page.fill('input[name="username"]', ig_username)
                    await page.fill('input[name="password"]', ig_password)
                    await page.click('button[type="submit"]')
                    await page.wait_for_timeout(5000)
                    
                    # Navigate to profile again
                    await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    await page.wait_for_timeout(3000)
                    
                    print(f"✅ Login successful, navigated to profile")
                except Exception as login_error:
                    print(f"❌ Login failed: {login_error}")
                    result["error"] = f"login_failed: {login_error}"
                    result["exists"] = False
                    await browser.close()
                    return result
            
            # Check if profile exists
            page_content = await page.content()
            
            # Check for "Sorry, this page isn't available"
            not_found_text = await page.locator('text="Sorry, this page isn\'t available"').count()
            
            if not_found_text > 0:
                print(f"❌ Profile page doesn't exist for @{username}")
                result["profile_exists"] = False
                result["exists"] = False
                await browser.close()
                return result
            
            # Check if profile exists (has profile picture or header)
            profile_pic = await page.locator('img[alt*="profile picture"]').count()
            profile_header = await page.locator('header').count()
            
            if profile_pic > 0 or profile_header > 0:
                print(f"✅ Profile exists for @{username}, taking screenshot...")
                result["profile_exists"] = True
                result["exists"] = True
                
                # Take screenshot
                await page.screenshot(path=screenshot_path, full_page=False)
                result["screenshot_path"] = screenshot_path
                print(f"📸 Screenshot saved: {screenshot_path}")
            else:
                print(f"❌ Cannot determine profile status for @{username}")
                result["profile_exists"] = False
                result["exists"] = False
            
            await browser.close()
            
    except Exception as e:
        print(f"❌ Instagram+Proxy check error for @{username}: {e}")
        result["error"] = f"instagram_proxy_error: {e}"
        result["exists"] = False
    
    return result

