"""Simple Instagram account checker using Playwright with screenshots."""

import asyncio
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError, BrowserContext
from bs4 import BeautifulSoup
from PIL import Image
import re

# Regular expressions for parsing profile data
RE_FOLLOWERS = re.compile(r'"edge_followed_by"\s*:\s*\{"count"\s*:\s*(\d+)\}', re.I)
RE_FOLLOWING = re.compile(r'"edge_follow"\s*:\s*\{"count"\s*:\s*(\d+)\}', re.I)
RE_POSTS = re.compile(r'"edge_owner_to_timeline_media"\s*:\s*\{"count"\s*:\s*(\d+)\}', re.I)


async def check_and_refresh_session(
    page,
    ig_username: Optional[str] = None,
    ig_password: Optional[str] = None
) -> tuple[bool, List[Dict[str, Any]]]:
    """
    Check if Instagram session is valid and refresh if needed.
    
    Args:
        page: Playwright page object
        ig_username: Instagram username for login (optional)
        ig_password: Instagram password for login (optional)
        
    Returns:
        Tuple of (is_valid, new_cookies)
    """
    try:
        # Try to access Instagram home page
        await page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(2000)
        
        # Check if we're logged in by looking for login indicators
        current_url = page.url
        print(f"🔍 Current URL after navigation: {current_url}")
        
        # Check for login page indicators
        login_indicators = [
            "accounts/login" in current_url,
            "Log In" in await page.content(),
            "Sign up" in await page.content()
        ]
        
        is_login_page = any(login_indicators)
        
        if is_login_page:
            print("🔄 Session expired, attempting to login...")
            
            if not ig_username or not ig_password:
                print("❌ No credentials provided for login")
                return False, []
            
            # Attempt login
            try:
                print(f"🔐 Attempting login for @{ig_username}")
                await page.fill('input[name="username"]', ig_username)
                await page.fill('input[name="password"]', ig_password)
                await page.click('button[type="submit"]')
                
                # Wait for navigation after login
                await page.wait_for_timeout(3000)
                
                # Check current URL to see what happened
                current_url = page.url
                print(f"🔍 URL after login attempt: {current_url}")
                
                # Check if login was successful
                if "accounts/login" in current_url:
                    # Still on login page - check for error messages
                    try:
                        error_selectors = [
                            '[role="alert"]',
                            '.error',
                            '[data-testid="error"]',
                            'text=Incorrect username or password',
                            'text=Please wait a few minutes',
                            'text=Try again later'
                        ]
                        
                        for selector in error_selectors:
                            try:
                                error_element = await page.locator(selector).first
                                if await error_element.count() > 0:
                                    error_text = await error_element.text_content()
                                    print(f"❌ Login error: {error_text}")
                                    return False, []
                            except:
                                continue
                        
                        print("❌ Login failed - still on login page")
                        return False, []
                        
                    except Exception as e:
                        print(f"❌ Login failed - error checking: {e}")
                        return False, []
                else:
                    # Successfully navigated away from login page
                    try:
                        await page.wait_for_selector('nav, a[href="/accounts/edit/"], [data-testid="user-avatar"]', timeout=5000)
                        print("✅ Login successful")
                        
                        # Get new cookies from the page context
                        context = page.context
                        new_cookies = await context.cookies()
                        print(f"🍪 Retrieved {len(new_cookies)} new cookies after login")
                        return True, new_cookies
                        
                    except PWTimeoutError:
                        # Might need 2FA or other verification
                        print("⚠️ Login might require 2FA or additional verification")
                        return False, []
                    
            except Exception as e:
                print(f"❌ Login error: {e}")
                return False, []
        else:
            # Session is valid
            print("✅ Session is valid - user is logged in")
            return True, []
            
    except Exception as e:
        print(f"⚠️ Session check error: {e}")
        return False, []


async def _apply_dark_theme_simple(page):
    """Применяет темную тему к странице Instagram для простого чекера."""
    try:
        # Ждем полной загрузки страницы
        await page.wait_for_load_state('networkidle')
        
        # Добавляем небольшую задержку для полной отрисовки
        await page.wait_for_timeout(1000)
        
        # Применяем стили через JavaScript для более надежного результата
        await page.evaluate("""
            () => {
                // Применяем стили ко всем элементам
                const allElements = document.querySelectorAll('*');
                allElements.forEach(el => {
                    if (el.tagName !== 'IMG' && el.tagName !== 'SVG') {
                        el.style.setProperty('background-color', '#000000', 'important');
                        el.style.setProperty('color', '#ffffff', 'important');
                    }
                });
                
                // Специально для body и html
                document.body.style.setProperty('background-color', '#000000', 'important');
                document.body.style.setProperty('color', '#ffffff', 'important');
                document.documentElement.style.setProperty('background-color', '#000000', 'important');
                document.documentElement.style.setProperty('color', '#ffffff', 'important');
            }
        """)
        print("🌙 Dark theme applied to page")
    except Exception as e:
        print(f"⚠️ Failed to apply dark theme: {e}")


def crop_to_upper_half(image_path: str) -> str:
    """
    Crop image to show only upper part with custom margins.
    - Vertical: upper 50% minus 30% from bottom = 35% of total height
    - Horizontal: 43% width (removes 17% from left, 40% from right)
    
    Args:
        image_path: Path to the original image
        
    Returns:
        Path to the cropped image (same as input, overwrites original)
    """
    try:
        # Open the image
        img = Image.open(image_path)
        width, height = img.size
        
        # Calculate vertical crop (35% сверху)
        upper_half_height = height // 2  # 50% of total height
        bottom_crop = int(upper_half_height * 0.35)  # Remove 30% from bottom of upper half
        final_height = upper_half_height - bottom_crop  # This gives us 35% of total height
        
        # Calculate horizontal crop (43% width - убираем 17% слева, 40% справа)
        left_crop = int(width * 0.17)  # Remove 17% from left
        right_crop = int(width * 0.40)  # Remove 40% from right
        
        # Crop (left, top, right, bottom)
        cropped_img = img.crop((left_crop, 0, width - right_crop, final_height))
        
        # Save cropped image (overwrite original)
        cropped_img.save(image_path)
        print(f"✂️ Image cropped (43% width, top 35% height, 17% left crop): {image_path}")
        
        return image_path
    except Exception as e:
        print(f"⚠️ Failed to crop image: {e}")
        return image_path


async def check_account_with_screenshot(
    username: str,
    cookies: list,
    headless: bool = True,
    timeout_ms: int = 30000,
    screenshot_dir: str = "screenshots",
    ig_username: Optional[str] = None,
    ig_password: Optional[str] = None,
    session_db_update_callback: Optional[callable] = None,
    proxy_server: Optional[str] = None,
    proxy_username: Optional[str] = None,
    proxy_password: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check Instagram account using Playwright with screenshot.
    
    Args:
        username: Instagram username to check (without @)
        cookies: List of cookies from Instagram session
        headless: Run browser in headless mode
        timeout_ms: Timeout for page operations
        screenshot_dir: Directory to save screenshots
        ig_username: Instagram username for re-login if session expired
        ig_password: Instagram password for re-login if session expired
        session_db_update_callback: Callback to update cookies in DB (takes new_cookies as arg)
        proxy_server: Proxy server (e.g., "http://host:port")
        proxy_username: Proxy username for authentication
        proxy_password: Proxy password for authentication
        
    Returns:
        Dict with check results and screenshot path
    """
    result = {
        "username": username,
        "exists": None,
        "full_name": None,
        "followers": None,
        "following": None,
        "posts": None,
        "screenshot_path": None,
        "error": None
    }
    
    # Clean username
    username = username.strip().lstrip("@")
    url = f"https://www.instagram.com/{username}/"
    
    # Create screenshot directory
    os.makedirs(screenshot_dir, exist_ok=True)
    
    async with async_playwright() as p:
        # Prepare proxy configuration
        proxy_config = None
        if proxy_server:
            proxy_config = {"server": proxy_server}
            if proxy_username and proxy_password:
                proxy_config["username"] = proxy_username
                proxy_config["password"] = proxy_password
        
        browser = await p.chromium.launch(
            headless=headless,
            proxy=proxy_config,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding"
            ]
        )
        
        # Random User-Agent to avoid detection
        import random
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=random.choice(user_agents),
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )
        
        # Add cookies to context
        print(f"🍪 Adding {len(cookies)} cookies to browser context...")
        for cookie in cookies:
            try:
                cookie_data = {
                    "name": cookie["name"],
                    "value": cookie["value"],
                    "domain": cookie.get("domain", ".instagram.com"),
                    "path": cookie.get("path", "/"),
                }
                
                # Handle expires field - Playwright needs unix timestamp or omit the field
                if "expires" in cookie and cookie["expires"] not in [-1, None, ""]:
                    # If expires is a valid timestamp, use it
                    cookie_data["expires"] = cookie["expires"]
                # Otherwise, omit expires field for session cookies
                
                # Add optional fields if present
                if "httpOnly" in cookie:
                    cookie_data["httpOnly"] = cookie["httpOnly"]
                if "secure" in cookie:
                    cookie_data["secure"] = cookie["secure"]
                if "sameSite" in cookie and cookie["sameSite"] in ["Strict", "Lax", "None"]:
                    cookie_data["sameSite"] = cookie["sameSite"]
                
                await context.add_cookies([cookie_data])
                print(f"✅ Added cookie: {cookie['name']} (domain: {cookie_data['domain']})")
            except Exception as e:
                print(f"❌ Failed to add cookie {cookie.get('name', 'unknown')}: {e}")
        
        page = await context.new_page()
        
        # Check if session is valid and refresh if needed
        session_valid, new_cookies = await check_and_refresh_session(
            page, 
            ig_username=ig_username, 
            ig_password=ig_password
        )
        
        if not session_valid:
            result["error"] = "Session expired and failed to re-login"
            print(f"❌ Cannot proceed without valid session")
            await context.close()
            await browser.close()
            return result
        
        # If we got new cookies, update them in the DB
        if new_cookies and session_db_update_callback:
            try:
                session_db_update_callback(new_cookies)
                print("✅ Session cookies updated in database")
            except Exception as e:
                print(f"⚠️ Failed to update cookies in DB: {e}")
        
        try:
            print(f"🔍 Checking @{username}...")
            
            # Navigate to profile with retry logic for redirects
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    print(f"🔍 Attempt {attempt + 1}/{max_retries} to navigate to @{username}")
                    
                    # Clear any existing redirects
                    await page.evaluate("() => { window.history.replaceState(null, '', '/'); }")
                    
                    # Navigate with domcontentloaded strategy (faster, less prone to timeout)
                    await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                    
                    # Wait longer for page to load and render
                    await page.wait_for_timeout(5000)  # Increased to 5 seconds
                    
                    # Log current URL for debugging
                    current_url = page.url
                    print(f"🔍 Current URL after navigation: {current_url}")
                    
                    # Check if we got stuck in redirects
                    if current_url != url and "instagram.com" in current_url and username not in current_url:
                        print(f"⚠️ Redirected away from profile page: {current_url}")
                        if attempt < max_retries - 1:
                            print(f"🔄 Retrying in 10 seconds...")
                            await page.wait_for_timeout(10000)
                            continue
                        else:
                            result["error"] = f"Too many redirects - final URL: {current_url}"
                            return result
                    
                    # If we got here, navigation was successful
                    break
                    
                except Exception as e:
                    if "ERR_TOO_MANY_REDIRECTS" in str(e):
                        print(f"⚠️ Too many redirects on attempt {attempt + 1}: {e}")
                        if attempt < max_retries - 1:
                            print(f"🔄 Waiting 15 seconds before retry...")
                            await page.wait_for_timeout(15000)
                            continue
                        else:
                            result["error"] = f"ERR_TOO_MANY_REDIRECTS after {max_retries} attempts"
                            return result
                    else:
                        print(f"❌ Navigation error: {e}")
                        if attempt < max_retries - 1:
                            await page.wait_for_timeout(5000)
                            continue
                        else:
                            raise e
            
            # Double-check that we're still logged in AND we're on the profile page
            current_url = page.url
            if "accounts/login" in current_url:
                result["error"] = "Session lost during navigation - redirected to login"
                print(f"❌ Lost session during navigation to @{username}")
                return result
            
            # Check if redirected to home page (Instagram sometimes does this for suspicious activity)
            if current_url == "https://www.instagram.com/" or current_url == "https://www.instagram.com":
                print(f"⚠️ Redirected to home page for @{username}, retrying...")
                # Add delay and retry
                await page.wait_for_timeout(2000)
                await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                await page.wait_for_timeout(3000)
                current_url = page.url
                print(f"🔍 URL after retry: {current_url}")
                
                # If still redirected, might be rate limited
                if current_url == "https://www.instagram.com/" or current_url == "https://www.instagram.com":
                    result["error"] = "Redirected to home page - possible rate limit"
                    print(f"❌ Still redirected to home for @{username} - possible rate limit")
                    return result
            
            # Check if profile exists - multiple methods
            try:
                # Method 1: Look for "Sorry, this page isn't available" or similar
                # Note: "This Account is Private" is NOT a not-found indicator - private accounts are still active
                not_found_selectors = [
                    "text=Sorry, this page isn't available",
                    "text=The link you followed may be broken",
                    "[data-testid='error-page']",
                    "h2:has-text('Sorry')"
                ]
                
                for selector in not_found_selectors:
                    try:
                        count = await page.locator(selector).count()
                        if count > 0:
                            result["exists"] = False
                            print(f"❌ Profile @{username} not found (selector: {selector})")
                            return result
                    except:
                        continue
                
                # Method 2: Check URL redirect or 404
                current_url = page.url
                if "instagram.com/accounts/login" in current_url or "instagram.com/404" in current_url:
                    result["exists"] = False
                    print(f"❌ Profile @{username} not found (redirect to login/404)")
                    return result
                    
            except Exception as e:
                print(f"Warning: Error checking profile existence: {e}")
                pass
            
            # Try to find profile elements
            try:
                # Wait for profile header or main content
                await page.wait_for_selector("header, main, [role='main']", timeout=10000)
            except PWTimeoutError:
                result["error"] = "timeout"
                print(f"⏰ Timeout waiting for @{username}")
                return result
            
            # Get page content for parsing
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            
            # Parse profile data
            result = parse_profile_data(username, html, soup, result)
            
            # Take screenshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_filename = f"ig_{username}_{timestamp}.png"
            screenshot_path = os.path.join(screenshot_dir, screenshot_filename)
            
            try:
                # Apply dark theme before screenshot
                await _apply_dark_theme_simple(page)
                
                # Take screenshot of the main content area
                await page.screenshot(
                    path=screenshot_path,
                    full_page=False,
                    clip={"x": 0, "y": 0, "width": 1280, "height": 900}
                )
                print(f"📸 Screenshot saved: {screenshot_path}")
                
                # Crop to upper half
                cropped_path = crop_to_upper_half(screenshot_path)
                result["screenshot_path"] = cropped_path
            except Exception as e:
                print(f"⚠️ Failed to take screenshot: {e}")
                result["screenshot_path"] = None
            
            # Determine if profile exists
            if result["exists"] is None:
                # Check if account is private (already handled in parse_profile_data)
                if result.get("is_private"):
                    result["exists"] = True
                    print(f"🔒 Profile @{username} is private - marking as active")
                # Check if we have any profile data
                elif any([
                    result["full_name"],
                    result["followers"] is not None,
                    result["following"] is not None,
                    result["posts"] is not None
                ]):
                    result["exists"] = True
                    print(f"✅ Profile @{username} found with data")
                else:
                    # No data found - check if we can find any profile elements
                    try:
                        # Look for common profile elements
                        profile_elements = await page.locator("header, [role='main'], article, [data-testid='user-avatar']").count()
                        if profile_elements > 0:
                            result["exists"] = True
                            print(f"✅ Profile @{username} found (profile elements detected)")
                        else:
                            result["exists"] = False
                            print(f"❌ Profile @{username} not found (no profile elements)")
                    except:
                        # If we can't check elements, assume not found
                        result["exists"] = False
                        print(f"❌ Profile @{username} not found (error checking elements)")
            
        except Exception as e:
            result["error"] = str(e)
            print(f"❌ Error checking @{username}: {e}")
        
        finally:
            await context.close()
            await browser.close()
    
    return result


def parse_profile_data(username: str, html: str, soup: BeautifulSoup, result: Dict[str, Any]) -> Dict[str, Any]:
    """Parse profile data from HTML."""
    
    # Check if account is private - if so, mark as active
    if "This Account is Private" in html:
        result["exists"] = True
        result["is_private"] = True
        print(f"🔒 Profile @{username} is private - marking as active")
        return result
    
    # Look for full name in meta tags
    try:
        og_title = soup.find("meta", {"property": "og:title"})
        if og_title and og_title.get("content"):
            title = og_title["content"]
            # Try different formats
            if "(" in title and ")" in title:
                # Extract name from title like "Name (@username) • Instagram photos and videos"
                name = title.split("(")[0].strip()
                if name and name != username and name != "Instagram":
                    result["full_name"] = name
            elif " • " in title:
                # Format: "Name • Instagram photos and videos"
                name = title.split(" • ")[0].strip()
                if name and name != username and name != "Instagram":
                    result["full_name"] = name
    except Exception as e:
        print(f"Debug: Failed to parse og:title: {e}")
        pass
    
    # Also try og:description for additional info
    try:
        og_desc = soup.find("meta", {"property": "og:description"})
        if og_desc and og_desc.get("content"):
            desc = og_desc["content"]
            # Format: "X Followers, Y Following, Z Posts - See Instagram photos and videos from @username"
            # or: "X Followers, Y Following, Z Posts"
            if "Followers" in desc and not result.get("followers"):
                parts = desc.split(",")
                for part in parts:
                    part = part.strip()
                    if "Followers" in part:
                        num = part.split()[0].replace(",", "")
                        try:
                            result["followers"] = int(num)
                        except:
                            pass
                    elif "Following" in part:
                        num = part.split()[0].replace(",", "")
                        try:
                            result["following"] = int(num)
                        except:
                            pass
                    elif "Posts" in part:
                        num = part.split()[0].replace(",", "")
                        try:
                            result["posts"] = int(num)
                        except:
                            pass
    except Exception as e:
        print(f"Debug: Failed to parse og:description: {e}")
        pass
    
    # Parse JSON data for followers/following/posts
    try:
        # Look for followers count
        followers_match = RE_FOLLOWERS.search(html)
        if followers_match:
            result["followers"] = int(followers_match.group(1))
        
        # Look for following count
        following_match = RE_FOLLOWING.search(html)
        if following_match:
            result["following"] = int(following_match.group(1))
        
        # Look for posts count
        posts_match = RE_POSTS.search(html)
        if posts_match:
            result["posts"] = int(posts_match.group(1))
    except Exception as e:
        print(f"Warning: Failed to parse profile data: {e}")
    
    return result


async def check_multiple_accounts(
    usernames: list,
    cookies: list,
    headless: bool = True,
    timeout_ms: int = 30000
) -> list:
    """
    Check multiple Instagram accounts.
    
    Args:
        usernames: List of usernames to check
        cookies: Instagram session cookies
        headless: Run browser in headless mode
        timeout_ms: Timeout for each account
        
    Returns:
        List of check results
    """
    results = []
    
    for username in usernames:
        try:
            result = await check_account_with_screenshot(
                username=username,
                cookies=cookies,
                headless=headless,
                timeout_ms=timeout_ms
            )
            results.append(result)
        except Exception as e:
            results.append({
                "username": username,
                "exists": None,
                "error": str(e),
                "screenshot_path": None
            })
    
    return results
