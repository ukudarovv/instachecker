"""Instagram account checker via proxy without login."""

import asyncio
import random
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# List of realistic User-Agents for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
]

def get_random_user_agent():
    """Get a random User-Agent string"""
    return random.choice(USER_AGENTS)

def get_next_proxy(session, user_id, current_proxy_id=None):
    """Get next available proxy for user, excluding current one"""
    try:
        from ..models import Proxy
    except ImportError:
        from models import Proxy
    
    query = session.query(Proxy).filter(
        Proxy.user_id == user_id,
        Proxy.is_active == True
    ).order_by(Proxy.priority.asc())
    
    if current_proxy_id:
        query = query.filter(Proxy.id != current_proxy_id)
    
    return query.first()

try:
    from ..models import Proxy
except ImportError:
    from models import Proxy


async def test_proxy_connectivity(proxy: Proxy, timeout_ms: int = 10000) -> Dict[str, Any]:
    """
    Test proxy connectivity.
    
    Args:
        proxy: Proxy object to test
        timeout_ms: Timeout in milliseconds
    
    Returns:
        dict with test results: {
            "success": bool,
            "error": str (optional)
        }
    """
    result = {
        "success": False,
        "error": None
    }
    
    # Build proxy config
    proxy_url = f"{proxy.scheme}://{proxy.host}"
    proxy_config = None
    
    # Playwright doesn't support SOCKS5 with authentication
    # Only use HTTP proxies with auth, or SOCKS5 without auth
    if proxy.scheme == "socks5" and (proxy.username or proxy.password):
        print(f"[PROXY-TEST] ⚠️ SOCKS5 with auth not supported by Playwright, using without auth")
        proxy_config = {
            "server": proxy_url
        }
    elif proxy.username and proxy.password:
        proxy_config = {
            "server": proxy_url,
            "username": proxy.username,
            "password": proxy.password
        }
    else:
        proxy_config = {
            "server": proxy_url
        }
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                proxy=proxy_config,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # Create context with realistic browser settings
            context = await browser.new_context(
                user_agent=get_random_user_agent(),
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='America/New_York'
            )
            
            # Add stealth scripts
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            page = await context.new_page()
            
            try:
                # Try to open a simple page
                response = await page.goto("https://www.google.com", timeout=timeout_ms, wait_until="domcontentloaded")
                
                if response and response.ok:
                    result["success"] = True
                else:
                    result["error"] = "Failed to load page"
                    
            except Exception as e:
                result["error"] = str(e)
            finally:
                await browser.close()
                
    except Exception as e:
        result["error"] = f"Browser error: {str(e)}"
    
    return result


async def check_account_via_proxy(
    username: str,
    proxy: Optional[Proxy] = None,
    headless: bool = True,
    timeout_ms: int = 30000
) -> Dict[str, Any]:
    """
    Check if Instagram account exists using proxy without login.
    Just opens the public profile page.
    
    Args:
        username: Instagram username to check
        proxy: Proxy object (optional)
        headless: Run browser in headless mode
        timeout_ms: Timeout in milliseconds
    
    Returns:
        dict with keys:
            - username: str
            - exists: bool (True if found, False if not found, None if error)
            - is_private: bool (optional, if found)
            - error: str (optional, if error occurred)
            - checked_via: str = 'proxy'
    """
    result = {
        "username": username,
        "exists": None,
        "is_private": None,
        "error": None,
        "checked_via": "proxy"
    }
    
    # Log proxy configuration
    print(f"[PROXY-CHECK] 🔍 Checking @{username} via proxy...")
    if proxy:
        print(f"[PROXY-CHECK] 🔗 Proxy: {proxy.scheme}://{proxy.host}")
        print(f"[PROXY-CHECK] 👤 Auth: {proxy.username} (password: {'Yes' if proxy.password else 'No'})")
    else:
        print(f"[PROXY-CHECK] ⚠️ No proxy - using direct connection")
    
    # Build proxy config if proxy provided
    proxy_config = None
    if proxy:
        proxy_url = f"{proxy.scheme}://{proxy.host}"
        
        # Playwright doesn't support SOCKS5 with authentication
        # Only use HTTP proxies with auth, or SOCKS5 without auth
        if proxy.scheme == "socks5" and (proxy.username or proxy.password):
            print(f"[PROXY-CHECK] ⚠️ SOCKS5 with auth not supported by Playwright, using without auth")
            print(f"[PROXY-CHECK] 💡 Tip: Use HTTP proxy with auth instead of SOCKS5")
            proxy_config = {
                "server": proxy_url
            }
        elif proxy.username and proxy.password:
            proxy_config = {
                "server": proxy_url,
                "username": proxy.username,
                "password": proxy.password
            }
        else:
            proxy_config = {
                "server": proxy_url
            }
    
    try:
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(
                headless=headless,
                proxy=proxy_config
            )
            
            context = await browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            
            page = await context.new_page()
            
            try:
                # Navigate to Instagram profile
                url = f"https://www.instagram.com/{username}/"
                print(f"[PROXY-CHECK] Opening {url}...")
                
                response = await page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
                
                # Wait a bit for page to load
                await asyncio.sleep(2)
                
                # Check if account exists by looking for common indicators
                # Method 1: Check page title
                title = await page.title()
                print(f"[PROXY-CHECK] Page title: {title}")
                
                # Method 2: Check for "Sorry, this page isn't available"
                not_found_text = await page.locator('text="Sorry, this page isn\'t available"').count()
                
                if not_found_text > 0:
                    print(f"[PROXY-CHECK] ❌ Account @{username} not found (page not available)")
                    result["exists"] = False
                    result["error"] = "Page not available"
                elif "Login" in title or "Instagram" in title:
                    # Instagram redirected to login page - account likely exists but requires login
                    print(f"[PROXY-CHECK] ⚠️ Account @{username} - redirected to login (likely exists)")
                    result["exists"] = True
                    result["is_private"] = None  # Cannot determine privacy without login
                    result["note"] = "Redirected to login page"
                else:
                    # Account likely exists
                    # Try to detect if private
                    private_text = await page.locator('text="This Account is Private"').count()
                    
                    if private_text > 0:
                        print(f"[PROXY-CHECK] ✅ Account @{username} found (private)")
                        result["exists"] = True
                        result["is_private"] = True
                    else:
                        # Check for meta tags or profile data
                        # If we can see any profile elements, account exists
                        profile_pic = await page.locator('img[alt*="profile picture"]').count()
                        profile_header = await page.locator('header').count()
                        
                        if profile_pic > 0 or profile_header > 0:
                            print(f"[PROXY-CHECK] ✅ Account @{username} found (public)")
                            result["exists"] = True
                            result["is_private"] = False
                        else:
                            # Check if we're on a login page or rate limited
                            page_content = await page.content()
                            if "Login" in page_content or "log in" in page_content.lower():
                                print(f"[PROXY-CHECK] ⚠️ Account @{username} - redirected to login (likely exists)")
                                result["exists"] = True
                                result["is_private"] = None
                                result["note"] = "Redirected to login page"
                            else:
                                # Might be rate limited or other issue
                                print(f"[PROXY-CHECK] ⚠️ Account @{username} - uncertain (no clear indicators)")
                                result["exists"] = None
                                result["error"] = "Cannot determine account status"
                
            except PlaywrightTimeout:
                print(f"[PROXY-CHECK] ⏱️ Timeout checking @{username}")
                result["exists"] = None
                result["error"] = "Timeout"
            except Exception as e:
                print(f"[PROXY-CHECK] ❌ Error checking @{username}: {str(e)}")
                result["exists"] = None
                result["error"] = str(e)
            finally:
                await browser.close()
                
    except Exception as e:
        print(f"[PROXY-CHECK] ❌ Browser error: {str(e)}")
        result["exists"] = None
        result["error"] = f"Browser error: {str(e)}"
    
    return result


async def check_account_via_proxy_with_screenshot(
    username: str,
    proxy: Optional[Proxy] = None,
    headless: bool = True,
    timeout_ms: int = 30000,
    screenshot_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check Instagram account via proxy and optionally take screenshot.
    
    Args:
        username: Instagram username
        proxy: Proxy object
        headless: Run in headless mode
        timeout_ms: Timeout in milliseconds
        screenshot_path: Path to save screenshot (optional)
    
    Returns:
        Same as check_account_via_proxy plus:
            - screenshot_path: str (if screenshot was taken)
    """
    # Log proxy usage
    if proxy:
        print(f"[PROXY-CHECK] 🔗 Using proxy: {proxy.scheme}://{proxy.host}")
        print(f"[PROXY-CHECK] 👤 Proxy user: {proxy.username}")
        print(f"[PROXY-CHECK] 🔑 Proxy auth: {'Yes' if proxy.password else 'No'}")
    else:
        print(f"[PROXY-CHECK] ⚠️ No proxy configured - using direct connection")
    
    result = await check_account_via_proxy(username, proxy, headless, timeout_ms)
    
    # If account exists and screenshot requested, take it
    if result["exists"] is True and screenshot_path:
        try:
            async with async_playwright() as p:
                proxy_config = None
                if proxy:
                    proxy_url = f"{proxy.scheme}://{proxy.host}"
                    
                    # Playwright doesn't support SOCKS5 with authentication
                    if proxy.scheme == "socks5" and (proxy.username or proxy.password):
                        print(f"[PROXY-CHECK] ⚠️ SOCKS5 with auth not supported by Playwright, using without auth")
                        proxy_config = {"server": proxy_url}
                    elif proxy.username and proxy.password:
                        proxy_config = {
                            "server": proxy_url,
                            "username": proxy.username,
                            "password": proxy.password
                        }
                    else:
                        proxy_config = {"server": proxy_url}
                
                browser = await p.chromium.launch(headless=headless, proxy=proxy_config)
                context = await browser.new_context(viewport={"width": 1280, "height": 900})
                page = await context.new_page()
                
                url = f"https://www.instagram.com/{username}/"
                await page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
                await asyncio.sleep(2)
                
                # Take screenshot
                await page.screenshot(
                    path=screenshot_path,
                    full_page=False,
                    clip={"x": 0, "y": 0, "width": 1280, "height": 900}
                )
                result["screenshot_path"] = screenshot_path
                print(f"[PROXY-CHECK] 📸 Screenshot saved: {screenshot_path}")
                
                await browser.close()
        except Exception as e:
            print(f"[PROXY-CHECK] ⚠️ Failed to take screenshot: {e}")
    
    return result


async def check_account_via_proxy_with_fallback(
    session,
    user_id: int,
    username: str,
    max_attempts: int = 3,
    headless: bool = True,
    timeout_ms: int = 30000,
    screenshot_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check Instagram account via proxy with automatic fallback to other proxies.
    
    Args:
        session: Database session
        user_id: User ID
        username: Instagram username
        max_attempts: Maximum number of proxy attempts
        headless: Run in headless mode
        timeout_ms: Timeout in milliseconds
        screenshot_path: Path to save screenshot (optional)
    
    Returns:
        dict with keys:
            - username: str
            - exists: bool (True if found, False if not found, None if error)
            - is_private: bool (optional, if found)
            - error: str (optional, if error occurred)
            - checked_via: str = 'proxy'
            - screenshot_path: str (if screenshot was taken)
            - proxy_used: str (proxy that worked)
            - attempts: int (number of attempts made)
    """
    result = {
        "username": username,
        "exists": None,
        "is_private": None,
        "error": None,
        "checked_via": "proxy",
        "screenshot_path": None,
        "proxy_used": None,
        "attempts": 0
    }
    
    print(f"[PROXY-FALLBACK] 🔄 Starting fallback check for @{username} (max {max_attempts} attempts)")
    
    current_proxy_id = None
    
    for attempt in range(1, max_attempts + 1):
        result["attempts"] = attempt
        
        # Get next proxy
        proxy = get_next_proxy(session, user_id, current_proxy_id)
        
        if not proxy:
            print(f"[PROXY-FALLBACK] ❌ No more proxies available for user {user_id}")
            result["error"] = "No more proxies available"
            break
        
        current_proxy_id = proxy.id
        print(f"[PROXY-FALLBACK] 🔗 Attempt {attempt}/{max_attempts} - Using proxy: {proxy.scheme}://{proxy.host}")
        
        # Try check with current proxy
        check_result = await check_account_via_proxy_with_screenshot(
            username=username,
            proxy=proxy,
            headless=headless,
            timeout_ms=timeout_ms,
            screenshot_path=screenshot_path
        )
        
        # Check if we got redirected to login - this means account exists!
        if (check_result.get("exists") is True and 
            check_result.get("note") == "Redirected to login page"):
            print(f"[PROXY-FALLBACK] ✅ Proxy {proxy.host} confirmed account exists (redirected to login)")
            result.update(check_result)
            result["proxy_used"] = f"{proxy.scheme}://{proxy.host}"
            print(f"[PROXY-FALLBACK] ✅ Success with proxy {proxy.host}")
            break
        
        # If we got a definitive result (not redirected to login), use it
        if check_result.get("exists") is not None:
            result.update(check_result)
            result["proxy_used"] = f"{proxy.scheme}://{proxy.host}"
            print(f"[PROXY-FALLBACK] ✅ Success with proxy {proxy.host}")
            break
        else:
            print(f"[PROXY-FALLBACK] ⚠️ Proxy {proxy.host} failed - trying next proxy...")
            continue
    
    if result["exists"] is None and not result.get("error"):
        result["error"] = f"All {max_attempts} proxies failed"
        print(f"[PROXY-FALLBACK] ❌ All proxies failed for @{username}")
    
    return result
