"""Triple checker: API + Proxy + Instagram Login + Profile Check."""

from __future__ import annotations
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import os

try:
    from ..models import Proxy, InstagramSession
    from .check_via_api import check_account_exists_via_api
    from .ig_sessions import decode_cookies
    from ..utils.encryptor import OptionalFernet
    from ..config import get_settings
except ImportError:
    from models import Proxy, InstagramSession
    from services.check_via_api import check_account_exists_via_api
    from services.ig_sessions import decode_cookies
    from utils.encryptor import OptionalFernet
    from config import get_settings


async def check_account_triple(
    session: Session,
    user_id: int,
    username: str,
    ig_session: Optional[InstagramSession] = None,
    fernet: Optional[OptionalFernet] = None
) -> Dict[str, Any]:
    """
    Triple check: API → Proxy + Instagram Login → Profile Check.
    
    Process:
    1. Check via RapidAPI (fast)
    2. If API shows active:
       - Connect via Proxy
       - Login with Instagram session
       - Check if profile page exists
       - If profile exists: take screenshot and mark as active
       - If profile doesn't exist: return warning (API active but no profile)
    3. Return combined result
    
    Args:
        session: Database session
        user_id: User ID
        username: Instagram username to check
        ig_session: Instagram session for login
        fernet: Encryptor for cookies
    
    Returns:
        Dict with check results including:
        - exists: True/False/None
        - api_active: API check result
        - profile_exists: Profile check result
        - screenshot_path: Path to screenshot (if profile exists)
        - error: Error message if any
        - checked_via: "api+proxy+instagram"
    """
    result = {
        "username": username,
        "exists": None,
        "api_active": None,
        "profile_exists": None,
        "screenshot_path": None,
        "error": None,
        "checked_via": "api+proxy+instagram",
        "warning": None
    }
    
    print(f"🔍 Triple check for @{username}")
    
    # Step 1: API Check
    print(f"📡 Step 1: API check for @{username}")
    api_result = await check_account_exists_via_api(session, user_id, username)
    result["api_active"] = api_result.get("exists", False)
    
    if not result["api_active"]:
        print(f"❌ API shows @{username} is not active")
        result["exists"] = False
        return result
    
    print(f"✅ API shows @{username} is active - proceeding to Step 2")
    
    # Step 2: Check if user has proxy
    print(f"🔗 Step 2: Checking proxy for user {user_id}")
    proxy = session.query(Proxy).filter(
        Proxy.user_id == user_id,
        Proxy.is_active == True
    ).order_by(Proxy.priority.asc()).first()
    
    if not proxy:
        print(f"⚠️ No active proxy for user {user_id}")
        result["error"] = "no_active_proxy"
        result["exists"] = False
        return result
    
    print(f"✅ Found active proxy: {proxy.scheme}://{proxy.host}")
    
    # Step 3: Check if user has Instagram session
    print(f"🔐 Step 3: Checking Instagram session for user {user_id}")
    if not ig_session:
        print(f"⚠️ No Instagram session provided for user {user_id}")
        result["error"] = "no_instagram_session"
        result["exists"] = False
        return result
    
    print(f"✅ Found Instagram session: @{ig_session.username}")
    
    # Step 4: Connect via Proxy + Login + Check Profile
    print(f"🌐 Step 4: Connecting via proxy and logging in...")
    
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
    from datetime import datetime
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
            page_content = await page.content()
            
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
            page_title = await page.title()
            
            # Check for "Sorry, this page isn't available"
            not_found_text = await page.locator('text="Sorry, this page isn\'t available"').count()
            
            if not_found_text > 0:
                print(f"❌ API active but profile page doesn't exist for @{username}")
                result["api_active"] = True
                result["profile_exists"] = False
                result["exists"] = False
                result["warning"] = "API показал активным, но страница профиля не найдена"
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
                print(f"❌ API active but cannot determine profile status for @{username}")
                result["api_active"] = True
                result["profile_exists"] = False
                result["exists"] = False
                result["warning"] = "API показал активным, но профиль не определен"
            
            await browser.close()
            
    except Exception as e:
        print(f"❌ Triple check error for @{username}: {e}")
        result["error"] = f"triple_check_error: {e}"
        result["exists"] = False
    
    return result

