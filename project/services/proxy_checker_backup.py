"""Instagram account checker via proxy without login using undetected-chromedriver."""

import asyncio
import random
import time
import sys
from typing import Dict, Any, Optional

# Патч для исправления проблемы с distutils в Python 3.12
def patch_distutils():
    """Создает локальный патч для distutils"""
    try:
        import types
        
        # Создаем модуль distutils
        distutils = types.ModuleType('distutils')
        distutils.__path__ = []
        
        # Создаем модуль version
        version = types.ModuleType('version')
        
        # Простая реализация LooseVersion
        class LooseVersion:
            def __init__(self, vstring=None):
                self.vstring = str(vstring) if vstring else ""
                self.version = self.vstring
            
            def __str__(self):
                return self.vstring
            
            def __repr__(self):
                return f"LooseVersion('{self.vstring}')"
            
            def __lt__(self, other):
                return str(self) < str(other)
            
            def __le__(self, other):
                return str(self) <= str(other)
            
            def __gt__(self, other):
                return str(self) > str(other)
            
            def __ge__(self, other):
                return str(self) >= str(other)
            
            def __eq__(self, other):
                return str(self) == str(other)
            
            def __ne__(self, other):
                return str(self) != str(other)
        
        version.LooseVersion = LooseVersion
        distutils.version = version
        
        # Добавляем в sys.modules
        sys.modules['distutils'] = distutils
        sys.modules['distutils.version'] = version
        
        return True
    except Exception as e:
        print(f"[PROXY-CHECKER] ⚠️ Failed to patch distutils: {e}")
        return False

# Применяем патч
patch_distutils()

# Теперь импортируем undetected_chromedriver
try:
    import undetected_chromedriver as uc
    print("[PROXY-CHECKER] ✅ undetected-chromedriver imported successfully")
except ImportError as e:
    print(f"[PROXY-CHECKER] ❌ Failed to import undetected-chromedriver: {e}")
    uc = None

# Случайные параметры браузера для ротации
def get_random_browser_params():
    """Генерирует случайные параметры браузера для каждого запроса"""
    return {
        "user_agent": random.choice(USER_AGENTS),
        "viewport": random.choice([
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1536, "height": 864},
            {"width": 1440, "height": 900},
            {"width": 1280, "height": 720}
        ]),
        "locale": random.choice(["en-US", "en-GB", "de-DE", "fr-FR", "es-ES", "it-IT"]),
        "timezone": random.choice([
            "America/New_York", "America/Los_Angeles", "Europe/London", 
            "Europe/Berlin", "Europe/Paris", "Asia/Tokyo"
        ]),
        "geolocation": {
            "latitude": random.uniform(-90, 90),
            "longitude": random.uniform(-180, 180)
        }
    }

# Extended list of realistic User-Agents for better rotation
USER_AGENTS = [
    # Chrome on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    
    # Chrome on macOS
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    
    # Firefox on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
    
    # Firefox on macOS
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/120.0',
    
    # Safari on macOS
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
    
    # Chrome on Linux
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    
    # Edge
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0'
]

def get_random_user_agent():
    """Get a random User-Agent string"""
    return random.choice(USER_AGENTS)

def get_random_viewport():
    """Get a random viewport size"""
    viewports = [
        {'width': 1920, 'height': 1080},
        {'width': 1366, 'height': 768},
        {'width': 1440, 'height': 900},
        {'width': 1536, 'height': 864},
        {'width': 1280, 'height': 720},
        {'width': 1600, 'height': 900},
        {'width': 1024, 'height': 768}
    ]
    return random.choice(viewports)

def get_random_locale():
    """Get a random locale"""
    locales = ['en-US', 'en-GB', 'en-CA', 'en-AU', 'de-DE', 'fr-FR', 'es-ES', 'it-IT', 'pt-BR', 'ja-JP']
    return random.choice(locales)

def get_random_timezone():
    """Get a random timezone"""
    timezones = [
        'America/New_York', 'America/Los_Angeles', 'America/Chicago', 'America/Denver',
        'Europe/London', 'Europe/Paris', 'Europe/Berlin', 'Europe/Rome',
        'Asia/Tokyo', 'Asia/Shanghai', 'Australia/Sydney', 'America/Toronto'
    ]
    return random.choice(timezones)

async def validate_account_page(page, username):
    """
    Validate that we're actually on the Instagram account page.
    
    Args:
        page: Playwright page object
        username: Instagram username to validate
        
    Returns:
        dict with keys:
            - is_valid: bool
            - reason: str (if not valid)
    """
    try:
        # Check if we have Instagram-specific elements
        instagram_elements = await page.locator('header, main, [role="main"]').count()
        if instagram_elements == 0:
            return {"is_valid": False, "reason": "No Instagram page structure"}
        
        # Check for username in URL or page content
        current_url = page.url
        if username.lower() not in current_url.lower():
            return {"is_valid": False, "reason": f"Username @{username} not in URL: {current_url}"}
        
        # Check for profile-specific elements
        profile_indicators = await page.locator('img[alt*="profile"], header, main').count()
        if profile_indicators == 0:
            return {"is_valid": False, "reason": "No profile elements found"}
        
        # Check for error pages or blocked content
        error_indicators = await page.locator('text="Sorry", text="Error", text="Blocked", text="Access denied"').count()
        if error_indicators > 0:
            return {"is_valid": False, "reason": "Error page detected"}
        
        # Check for cookie consent or other blocking pages and auto-accept
        cookie_buttons = await page.locator('text="Allow cookies", text="Accept", text="Continue", text="Consenti", text="Accetta", text="Consenti tutti i cookie", text="Rifiuta cookie facoltativi"').count()
        if cookie_buttons > 0:
            print(f"[PROXY-CHECK] 🍪 Cookie consent detected, auto-accepting...")
            try:
                # Try different cookie acceptance buttons
                accept_selectors = [
                    'text="Consenti tutti i cookie"',  # Italian
                    'text="Allow all cookies"',       # English
                    'text="Accept all cookies"',      # English
                    'text="Consenti"',                 # Italian short
                    'text="Accept"',                   # English short
                    'text="Allow cookies"',            # English
                    'button:has-text("Consenti")',    # Button with text
                    'button:has-text("Accept")',      # Button with text
                    '[data-testid="cookie-banner-accept"]',  # Test ID
                    'button[aria-label*="Accept"]',    # Aria label
                    'button[aria-label*="Consenti"]'    # Aria label Italian
                ]
                
                for selector in accept_selectors:
                    try:
                        if await page.locator(selector).count() > 0:
                            await page.click(selector, timeout=2000)
                            print(f"[PROXY-CHECK] ✅ Clicked cookie button: {selector}")
                            await page.wait_for_timeout(2000)  # Wait for page to load
                            break
                    except:
                        continue
                
                # Re-validate after accepting cookies
                await page.wait_for_timeout(3000)
                return await validate_account_page(page, username)
                
            except Exception as e:
                print(f"[PROXY-CHECK] ⚠️ Failed to auto-accept cookies: {e}")
                return {"is_valid": False, "reason": "Blocking page (cookies/consent) - auto-accept failed"}
        
        return {"is_valid": True, "reason": "Valid account page"}
        
    except Exception as e:
        return {"is_valid": False, "reason": f"Validation error: {e}"}

def get_next_proxy(session, user_id, current_proxy_id=None):
    """Get next available proxy for user with smart rotation"""
    try:
        from ..models import Proxy
    except ImportError:
        from models import Proxy
    
    # Get all active proxies for user
    all_proxies = session.query(Proxy).filter(
        Proxy.user_id == user_id,
        Proxy.is_active == True
    ).order_by(Proxy.priority.asc()).all()
    
    if not all_proxies:
        return None
    
    # If no current proxy, return first one
    if not current_proxy_id:
        print(f"[PROXY-ROTATION] 🔄 Starting with first proxy: {all_proxies[0].scheme}://{all_proxies[0].host}")
        return all_proxies[0]
    
    # Find current proxy index
    current_index = None
    for i, proxy in enumerate(all_proxies):
        if proxy.id == current_proxy_id:
            current_index = i
            break
    
    # If current proxy not found, return first one
    if current_index is None:
        print(f"[PROXY-ROTATION] 🔄 Current proxy not found, using first: {all_proxies[0].scheme}://{all_proxies[0].host}")
        return all_proxies[0]
    
    # Get next proxy in rotation
    next_index = (current_index + 1) % len(all_proxies)
    next_proxy = all_proxies[next_index]
    
    print(f"[PROXY-ROTATION] 🔄 Rotating to next proxy: {next_proxy.scheme}://{next_proxy.host}")
    return next_proxy

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
            
            # Create context with random browser settings
            browser_params = get_random_browser_params()
            context = await browser.new_context(
                user_agent=browser_params["user_agent"],
                viewport=browser_params["viewport"],
                locale=browser_params["locale"],
                timezone_id=browser_params["timezone"],
                permissions=['geolocation'],
                geolocation=browser_params["geolocation"],
                color_scheme='light',
                reduced_motion='no-preference',
                forced_colors='none'
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
        "full_name": None,
        "followers": None,
        "following": None,
        "posts": None,
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
            # Enhanced browser launch with anti-detection
            browser = await p.chromium.launch(
                headless=headless,
                proxy=proxy_config,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-field-trial-config',
                    '--disable-ipc-flooding-protection',
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-default-apps',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-translate',
                    '--disable-background-networking',
                    '--disable-sync',
                    '--metrics-recording-only',
                    '--no-report-upload',
                    '--disable-logging',
                    '--disable-gpu-logging',
                    '--silent'
                ]
            )
            
            # Create context with random settings
            browser_params = get_random_browser_params()
            context = await browser.new_context(
                user_agent=browser_params["user_agent"],
                viewport=browser_params["viewport"],
                locale=browser_params["locale"],
                timezone_id=browser_params["timezone"],
                permissions=['geolocation'],
                geolocation=browser_params["geolocation"],
                color_scheme='light',
                reduced_motion='no-preference',
                forced_colors='none'
            )
            
            # Add stealth scripts
            await context.add_init_script("""
                // Hide webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // Override plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                // Override languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                
                // Mock chrome runtime
                if (!window.chrome) {
                    window.chrome = {};
                }
                if (!window.chrome.runtime) {
                    window.chrome.runtime = {
                        onConnect: undefined,
                        onMessage: undefined,
                    };
                }
            """)
            
            page = await context.new_page()
            
            try:
                # Navigate to Instagram profile with anti-detection
                url = f"https://www.instagram.com/{username}/"
                print(f"[PROXY-CHECK] Opening {url}...")
                
                # Add random delay before navigation
                await asyncio.sleep(random.uniform(1, 3))
                
                # Navigate with random wait strategy
                wait_strategies = ["domcontentloaded", "networkidle", "load"]
                wait_strategy = random.choice(wait_strategies)
                
                response = await page.goto(url, timeout=timeout_ms, wait_until=wait_strategy)
                
                # Random delay after page load
                await asyncio.sleep(random.uniform(2, 5))
                
                # Check for anti-bot protection
                page_content = await page.content()
                if "Take a quick pause" in page_content or "We're seeing more requests" in page_content:
                    print(f"[PROXY-CHECK] 🛡️ Anti-bot protection detected, waiting...")
                    # Wait longer and try to scroll to simulate human behavior
                    await asyncio.sleep(random.uniform(10, 20))
                    
                    # Simulate human-like scrolling
                    await page.evaluate("window.scrollTo(0, 100)")
                    await asyncio.sleep(random.uniform(1, 3))
                    await page.evaluate("window.scrollTo(0, 0)")
                    await asyncio.sleep(random.uniform(2, 4))
                    
                    # Try to click somewhere to simulate interaction
                    try:
                        await page.click('body', timeout=1000)
                    except:
                        pass
                    
                    await asyncio.sleep(random.uniform(5, 10))
                    
                    # Try to navigate again
                    print(f"[PROXY-CHECK] Retrying navigation...")
                    await page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
                    await asyncio.sleep(random.uniform(3, 6))
                
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
                    # Instagram redirected to login page - account exists but requires login
                    print(f"[PROXY-CHECK] ✅ Account @{username} found (redirected to login - account exists)")
                    result["exists"] = True
                    result["is_private"] = None  # Cannot determine privacy without login
                    result["note"] = "Account exists, requires login"
                else:
                    # Check if we're actually on the account page (not some other page)
                    page_validation = await validate_account_page(page, username)
                    if not page_validation["is_valid"]:
                        print(f"[PROXY-CHECK] ❌ Invalid page content: {page_validation['reason']}")
                        result["exists"] = None
                        result["error"] = f"Invalid page: {page_validation['reason']}"
                        return result
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
                            
                            # Try to extract account information
                            try:
                                # Extract full name
                                full_name_element = await page.locator('h2').first
                                if await full_name_element.count() > 0:
                                    full_name = await full_name_element.text_content()
                                    result["full_name"] = full_name.strip() if full_name else None
                                    print(f"[PROXY-CHECK] 👤 Full name: {result['full_name']}")
                                
                                # Extract followers count
                                followers_element = await page.locator('a[href*="/followers/"] span').first
                                if await followers_element.count() > 0:
                                    followers_text = await followers_element.text_content()
                                    result["followers"] = followers_text.strip() if followers_text else None
                                    print(f"[PROXY-CHECK] 👥 Followers: {result['followers']}")
                                
                                # Extract following count
                                following_element = await page.locator('a[href*="/following/"] span').first
                                if await following_element.count() > 0:
                                    following_text = await following_element.text_content()
                                    result["following"] = following_text.strip() if following_text else None
                                    print(f"[PROXY-CHECK] 👥 Following: {result['following']}")
                                
                                # Extract posts count
                                posts_element = await page.locator('span:has-text("posts")').first
                                if await posts_element.count() > 0:
                                    posts_text = await posts_element.text_content()
                                    result["posts"] = posts_text.strip() if posts_text else None
                                    print(f"[PROXY-CHECK] 📸 Posts: {result['posts']}")
                                
                            except Exception as e:
                                print(f"[PROXY-CHECK] ⚠️ Could not extract account info: {e}")
                                # Continue without account info
                        else:
                            # Check if we're on a login page or rate limited
                            page_content = await page.content()
                            if "Login" in page_content or "log in" in page_content.lower():
                                print(f"[PROXY-CHECK] ✅ Account @{username} found (redirected to login - account exists)")
                                result["exists"] = True
                                result["is_private"] = None
                                result["note"] = "Account exists, requires login"
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
                
                # Enhanced browser launch with anti-detection
                browser = await p.chromium.launch(
                    headless=headless,
                    proxy=proxy_config,
                    args=[
                        '--no-sandbox',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor',
                        '--disable-background-timer-throttling',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-renderer-backgrounding',
                        '--disable-field-trial-config',
                        '--disable-ipc-flooding-protection',
                        '--no-first-run',
                        '--no-default-browser-check',
                        '--disable-default-apps',
                        '--disable-extensions',
                        '--disable-plugins',
                        '--disable-translate',
                        '--disable-background-networking',
                        '--disable-sync',
                        '--metrics-recording-only',
                        '--no-report-upload',
                        '--disable-logging',
                        '--disable-gpu-logging',
                        '--silent',
                        '--disable-background-timer-throttling',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-renderer-backgrounding',
                        '--disable-features=TranslateUI',
                        '--disable-ipc-flooding-protection'
                    ]
                )
                
                # Create context with random settings
                browser_params = get_random_browser_params()
                context = await browser.new_context(
                    user_agent=browser_params["user_agent"],
                    viewport=browser_params["viewport"],
                    locale=browser_params["locale"],
                    timezone_id=browser_params["timezone"],
                    permissions=['geolocation'],
                    geolocation=browser_params["geolocation"],
                    color_scheme='light',
                    reduced_motion='no-preference',
                    forced_colors='none'
                )
                
                # Add stealth scripts
                await context.add_init_script("""
                    // Hide webdriver property
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                    
                    // Override plugins
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5],
                    });
                    
                    // Override languages
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en'],
                    });
                    
                    // Override permissions
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );
                    
                    // Mock chrome runtime
                    if (!window.chrome) {
                        window.chrome = {};
                    }
                    if (!window.chrome.runtime) {
                        window.chrome.runtime = {
                            onConnect: undefined,
                            onMessage: undefined,
                        };
                    }
                """)
                
                page = await context.new_page()
                
                url = f"https://www.instagram.com/{username}/"
                
                # Add random delay before navigation
                await asyncio.sleep(random.uniform(1, 3))
                
                # Navigate with random wait strategy
                wait_strategies = ["domcontentloaded", "networkidle", "load"]
                wait_strategy = random.choice(wait_strategies)
                
                await page.goto(url, timeout=timeout_ms, wait_until=wait_strategy)
                
                # Random delay after page load
                await asyncio.sleep(random.uniform(2, 5))
                
                # Check for anti-bot protection
                page_content = await page.content()
                if "Take a quick pause" in page_content or "We're seeing more requests" in page_content:
                    print(f"[PROXY-CHECK] 🛡️ Anti-bot protection detected, waiting...")
                    # Wait longer and try to scroll to simulate human behavior
                    await asyncio.sleep(random.uniform(10, 20))
                    
                    # Simulate human-like scrolling
                    await page.evaluate("window.scrollTo(0, 100)")
                    await asyncio.sleep(random.uniform(1, 3))
                    await page.evaluate("window.scrollTo(0, 0)")
                    await asyncio.sleep(random.uniform(2, 4))
                    
                    # Try to click somewhere to simulate interaction
                    try:
                        await page.click('body', timeout=1000)
                    except:
                        pass
                    
                    await asyncio.sleep(random.uniform(5, 10))
                
                # Take screenshot
                try:
                    await page.screenshot(
                        path=screenshot_path,
                        full_page=False,
                        clip={"x": 0, "y": 0, "width": 1280, "height": 900}
                    )
                    result["screenshot_path"] = screenshot_path
                    print(f"[PROXY-CHECK] 📸 Screenshot saved: {screenshot_path}")
                except Exception as screenshot_error:
                    print(f"[PROXY-CHECK] ⚠️ Failed to take screenshot: {screenshot_error}")
                    # Still set the path even if screenshot failed, so auto_checker knows we tried
                    result["screenshot_path"] = screenshot_path
                
                await browser.close()
        except Exception as e:
            print(f"[PROXY-CHECK] ⚠️ Failed to take screenshot: {e}")
            # Set screenshot path even on error so auto_checker can handle it
            result["screenshot_path"] = screenshot_path
    
    return result


async def check_account_via_proxy_with_fallback(
    session,
    user_id: int,
    username: str,
    max_attempts: int = None,  # No limit by default
    headless: bool = True,
    timeout_ms: int = 30000,
    screenshot_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check Instagram account via proxy with automatic fallback to other proxies.
    No limit on attempts - will try all available proxies.
    
    Args:
        session: Database session
        user_id: User ID
        username: Instagram username
        max_attempts: Maximum number of proxy attempts (None = unlimited)
        headless: Run in headless mode
        timeout_ms: Timeout in milliseconds
        screenshot_path: Path to save screenshot (optional)
        
    Returns:
        dict with keys:
            - username: str
            - exists: bool (True if found, False if not found, None if error)
            - is_private: bool (optional, if found)
            - full_name: str (optional, if found)
            - followers: str (optional, if found)
            - following: str (optional, if found)
            - posts: str (optional, if found)
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
        "full_name": None,
        "followers": None,
        "following": None,
        "posts": None,
        "error": None,
        "checked_via": "proxy",
        "screenshot_path": None,
        "proxy_used": None,
        "attempts": 0
    }
    
    # Set unlimited attempts if not specified
    if max_attempts is None:
        max_attempts = 999  # Effectively unlimited
        print(f"[PROXY-FALLBACK] 🔄 Starting fallback check for @{username} (unlimited attempts)")
    else:
        print(f"[PROXY-FALLBACK] 🔄 Starting fallback check for @{username} (max {max_attempts} attempts)")
    
    current_proxy_id = None
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        result["attempts"] = attempt
        
        # Get next proxy
        proxy = get_next_proxy(session, user_id, current_proxy_id)
        
        if not proxy:
            print(f"[PROXY-FALLBACK] ❌ No more proxies available for user {user_id}")
            result["error"] = "No more proxies available"
            break
        
        current_proxy_id = proxy.id
        if max_attempts == 999:
            print(f"[PROXY-FALLBACK] 🔗 Attempt {attempt} - Using proxy: {proxy.scheme}://{proxy.host}")
        else:
            print(f"[PROXY-FALLBACK] 🔗 Attempt {attempt}/{max_attempts} - Using proxy: {proxy.scheme}://{proxy.host}")
        
        # Try check with current proxy
        try:
            check_result = await check_account_via_proxy_with_screenshot(
                username=username,
                proxy=proxy,
                headless=headless,
                timeout_ms=timeout_ms,
                screenshot_path=screenshot_path
            )
            
            # Check if we got redirected to login - this means account exists!
            if (check_result.get("exists") is True and 
                (check_result.get("note") == "Redirected to login page" or 
                 check_result.get("note") == "Account exists, requires login")):
                print(f"[PROXY-FALLBACK] ✅ Proxy {proxy.host} confirmed account exists (redirected to login)")
                result.update(check_result)
                result["proxy_used"] = f"{proxy.scheme}://{proxy.host}"
                print(f"[PROXY-FALLBACK] ✅ Success with proxy {proxy.host}")
                break
            
            # Check if we got a definitive result
            if check_result.get("exists") is not None:
                result.update(check_result)
                result["proxy_used"] = f"{proxy.scheme}://{proxy.host}"
                print(f"[PROXY-FALLBACK] ✅ Success with proxy {proxy.host}")
                break
            else:
                # Check if it's an invalid page error (should try next proxy)
                if "Invalid page" in str(check_result.get("error", "")):
                    print(f"[PROXY-FALLBACK] ❌ Proxy {proxy.host} - invalid page: {check_result.get('error')}")
                    print(f"[PROXY-FALLBACK] 🔄 Switching to next proxy...")
                    continue
                else:
                    print(f"[PROXY-FALLBACK] ⚠️ Proxy {proxy.host} failed - trying next proxy...")
                    continue
                    
        except Exception as e:
            print(f"[PROXY-FALLBACK] ❌ Proxy {proxy.host} error: {e}")
            print(f"[PROXY-FALLBACK] 🔄 Switching to next proxy...")
            continue
    
    if result["exists"] is None and not result.get("error"):
        result["error"] = f"All {max_attempts} proxies failed"
        print(f"[PROXY-FALLBACK] ❌ All proxies failed for @{username}")
    
    return result
