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


@retry(
    stop=stop_after_attempt(2), 
    wait=wait_exponential(multiplier=3, min=3, max=15),
    reraise=True
)
async def playwright_login_and_get_cookies(
    ig_username: str,
    ig_password: str,
    headless: bool,
    login_timeout_ms: int,
    twofa_timeout_ms: int,
    proxy_url: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Login via Chromium, optionally wait for 2FA (code entered by user in Telegram).
    Returns list of cookies (dicts).
    """
    proxy_kwargs = _proxy_kwargs_from_url(proxy_url)
    
    # Use custom user agent or default realistic one
    if not user_agent:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless, 
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-software-rasterizer"
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=user_agent,
            proxy=proxy_kwargs,
            locale="en-US",
            timezone_id="America/New_York",
            permissions=["geolocation"],
            geolocation={"latitude": 40.7128, "longitude": -74.0060},
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
        )
        
        # Add stealth settings to avoid detection
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            window.chrome = {
                runtime: {}
            };
        """)
        
        page = await context.new_page()
        try:
            # Set longer timeout for navigation
            print(f"🌐 Navigating to Instagram login page...")
            await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=max(login_timeout_ms, 30000))
            
            # Wait for page to fully load
            await page.wait_for_timeout(2000)
            
            # Ввод логина/пароля с задержками (имитация человека)
            print(f"🔐 Logging in as @{ig_username}...")
            
            # Focus and type username slowly - try multiple selectors
            username_input = None
            username_selectors = [
                'input[name="username"]',
                'input[aria-label="Phone number, username, or email"]',
                'input[type="text"]',
                'input._aa4b._add6._ac4d._ap35'
            ]
            
            for selector in username_selectors:
                try:
                    print(f"🔍 Trying selector: {selector}")
                    username_input = await page.wait_for_selector(selector, timeout=5000)
                    if username_input:
                        print(f"✅ Found username input with selector: {selector}")
                        break
                except:
                    continue
            
            if not username_input:
                print(f"❌ Could not find username input field with any selector")
                print(f"📸 Current URL: {page.url}")
                # Try to save screenshot for debugging
                try:
                    await page.screenshot(path="login_error.png")
                    print(f"📸 Screenshot saved as login_error.png")
                except:
                    pass
                raise Exception("Instagram login page not loaded correctly. Please use cookies import method.")
            
            await username_input.click()
            await page.wait_for_timeout(500)
            await username_input.type(ig_username, delay=100)
            await page.wait_for_timeout(500)
            print(f"✅ Username entered")
            
            # Focus and type password slowly - try multiple selectors
            password_input = None
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[aria-label="Password"]',
                'input._aa4b._add6._ac4d._ap35[type="password"]'
            ]
            
            for selector in password_selectors:
                try:
                    print(f"🔍 Trying selector: {selector}")
                    password_input = await page.wait_for_selector(selector, timeout=5000)
                    if password_input:
                        print(f"✅ Found password input with selector: {selector}")
                        break
                except:
                    continue
            
            if not password_input:
                print(f"❌ Could not find password input field with any selector")
                raise Exception("Instagram login page structure changed. Please use cookies import method.")
            
            await password_input.click()
            await page.wait_for_timeout(500)
            await password_input.type(ig_password, delay=100)
            await page.wait_for_timeout(1000)
            print(f"✅ Password entered")
            
            # Click login button
            print("🖱️ Clicking login button...")
            await page.click('button[type="submit"]')
            
            # Wait for navigation after login
            print("⏳ Waiting for response...")
            await page.wait_for_timeout(5000)
            
            # Check current URL
            current_url = page.url
            print(f"🔍 URL after login: {current_url}")
            
            # Check various scenarios after login
            
            # Scenario 1: Still on login page (error)
            if "/accounts/login" in current_url:
                print("❌ Login failed - still on login page")
                # Check for error messages
                try:
                    error_element = await page.locator('[role="alert"]').first
                    if await error_element.count() > 0:
                        error_text = await error_element.text_content()
                        print(f"❌ Login error: {error_text}")
                        raise Exception(f"Login failed: {error_text}")
                except:
                    pass
                raise Exception("Login failed - credentials may be incorrect")
            
            # Scenario 2: Challenge or security check
            if "/challenge/" in current_url or "challenge_required" in await page.content():
                print("⚠️ Instagram security challenge detected")
                print("ℹ️ Trying to handle challenge...")
                
                # Wait a bit for challenge to load
                await page.wait_for_timeout(3000)
                
                # Try to click "Send Security Code" if available
                try:
                    send_code_btn = await page.locator('button:has-text("Send Security Code")').first
                    if await send_code_btn.count() > 0:
                        await send_code_btn.click()
                        print("📧 Requested security code")
                        await page.wait_for_timeout(2000)
                except:
                    pass
                
                # For now, we can't handle this automatically
                print("❌ Cannot proceed with security challenge automatically")
                print("💡 Please login manually in browser first, then export cookies")
                raise Exception("Security challenge required - cannot automate")
            
            # Scenario 3: 2FA required
            if "two_factor" in current_url or "two_factor" in await page.content():
                print("🔐 Two-factor authentication required")
                print("❌ Cannot proceed with 2FA automatically")
                print("💡 Please use cookies import method instead")
                raise Exception("2FA required - use cookies import method")
            
            # Scenario 4: "Save Your Login Info?" prompt
            try:
                save_info_button = await page.locator('button:has-text("Not Now")').first
                if await save_info_button.count() > 0:
                    print("💾 Dismissing 'Save Login Info' prompt...")
                    await save_info_button.click()
                    await page.wait_for_timeout(1000)
            except:
                pass
            
            # Scenario 5: "Turn on Notifications?" prompt
            try:
                not_now_button = await page.locator('button:has-text("Not Now")').first
                if await not_now_button.count() > 0:
                    print("🔔 Dismissing notifications prompt...")
                    await not_now_button.click()
                    await page.wait_for_timeout(1000)
            except:
                pass
            
            # Scenario 6: Successful login
            try:
                print("✅ Waiting for successful login indicators...")
                await page.wait_for_selector('nav, a[href="/accounts/edit/"], [data-testid="user-avatar"], svg[aria-label="Home"]', timeout=15000)
                print("✅ Login successful!")
                
                # Wait for cookies to be properly set
                await page.wait_for_timeout(3000)
                
                # Navigate to home to ensure all cookies are set
                print("🏠 Navigating to home page...")
                await page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(3000)
                
                print("✅ All set!")
                
            except PWTimeoutError:
                print("⚠️ Timeout waiting for login confirmation")
                print("ℹ️ Continuing anyway, checking cookies...")
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
