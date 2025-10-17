"""Instagram account checker via proxy without login."""

import asyncio
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

try:
    from ..models import Proxy
except ImportError:
    from models import Proxy


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
    
    # Build proxy config if proxy provided
    proxy_config = None
    if proxy:
        proxy_url = f"{proxy.scheme}://{proxy.host}"
        if proxy.username and proxy.password:
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
    result = await check_account_via_proxy(username, proxy, headless, timeout_ms)
    
    # If account exists and screenshot requested, take it
    if result["exists"] is True and screenshot_path:
        try:
            async with async_playwright() as p:
                proxy_config = None
                if proxy:
                    proxy_url = f"{proxy.scheme}://{proxy.host}"
                    if proxy.username and proxy.password:
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
