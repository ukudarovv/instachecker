"""Instagram login via Playwright."""

from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential

LOGIN_URL = "https://www.instagram.com/accounts/login/"


def _proxy_kwargs_from_url(proxy_url: Optional[str]):
    """Convert proxy URL to Playwright proxy kwargs."""
    if not proxy_url:
        return None
    from urllib.parse import urlparse
    u = urlparse(proxy_url)
    auth = {}
    if u.username and u.password:
        auth["username"] = u.username
        auth["password"] = u.password
    return {"server": f"{u.scheme}://{u.hostname}:{u.port}", **auth}


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
async def playwright_login_and_get_cookies(
    ig_username: str,
    ig_password: str,
    headless: bool,
    login_timeout_ms: int,
    twofa_timeout_ms: int,
    proxy_url: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Login via Chromium, optionally wait for 2FA (code entered by user in Telegram).
    Returns list of cookies (dicts).
    """
    proxy_kwargs = _proxy_kwargs_from_url(proxy_url)
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless, 
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            proxy=proxy_kwargs
        )
        page = await context.new_page()
        try:
            await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=login_timeout_ms)
            
            # Ввод логина/пароля
            print(f"🔐 Logging in as @{ig_username}...")
            await page.fill('input[name="username"]', ig_username)
            await page.fill('input[name="password"]', ig_password)
            await page.click('button[type="submit"]')
            
            # Wait for navigation after login
            await page.wait_for_timeout(3000)
            
            # Check current URL
            current_url = page.url
            print(f"🔍 URL after login: {current_url}")
            
            # Check if still on login page (error)
            if "/accounts/login" in current_url:
                print("❌ Login failed - still on login page")
                # Check for error messages
                try:
                    error_element = await page.locator('[role="alert"]').first
                    if await error_element.count() > 0:
                        error_text = await error_element.text_content()
                        print(f"❌ Login error: {error_text}")
                except:
                    pass
                # Still try to get cookies in case of partial login
                cookies = await context.cookies()
                return cookies
            
            # Wait for successful login indicators
            try:
                await page.wait_for_selector('nav, a[href="/accounts/edit/"], [data-testid="user-avatar"]', timeout=10000)
                print("✅ Login successful - waiting for cookies to be set...")
                
                # Wait a bit more for cookies to be properly set
                await page.wait_for_timeout(2000)
                
                # Navigate to home to ensure all cookies are set
                await page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(2000)
                
                print("✅ Navigated to home page")
                
            except PWTimeoutError:
                print("⚠️ Timeout waiting for login confirmation - might require 2FA")
                # May be 2FA or checkpoint - continue anyway
                pass

            # Get cookies
            cookies = await context.cookies()
            
            # Verify we have sessionid cookie
            has_sessionid = any(c.get('name') == 'sessionid' for c in cookies)
            print(f"🍪 Retrieved {len(cookies)} cookies, sessionid present: {has_sessionid}")
            
            if not has_sessionid:
                print("⚠️ Warning: sessionid cookie not found in response")
            
            return cookies
        finally:
            await context.close()
            await browser.close()
