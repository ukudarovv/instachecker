"""Simple Instagram account checker using Playwright with screenshots."""

import asyncio
import os
from typing import Optional, Dict, Any
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError
from bs4 import BeautifulSoup
from PIL import Image
import re

# Regular expressions for parsing profile data
RE_FOLLOWERS = re.compile(r'"edge_followed_by"\s*:\s*\{"count"\s*:\s*(\d+)\}', re.I)
RE_FOLLOWING = re.compile(r'"edge_follow"\s*:\s*\{"count"\s*:\s*(\d+)\}', re.I)
RE_POSTS = re.compile(r'"edge_owner_to_timeline_media"\s*:\s*\{"count"\s*:\s*(\d+)\}', re.I)


def crop_to_upper_half(image_path: str) -> str:
    """
    Crop image to show only upper part with custom margins.
    - Vertical: upper 50% minus 30% from bottom = 20% of total height
    - Horizontal: center 60% (removes 20% from each side)
    
    Args:
        image_path: Path to the original image
        
    Returns:
        Path to the cropped image (same as input, overwrites original)
    """
    try:
        # Open the image
        img = Image.open(image_path)
        width, height = img.size
        
        # Calculate vertical crop
        upper_half_height = height // 2  # 50% of total height
        bottom_crop = int(upper_half_height * 0.35)  # Remove 30% from bottom of upper half
        final_height = upper_half_height - bottom_crop  # This gives us 35% of total height
        
        # Calculate horizontal crop (remove 20% from each side)
        horizontal_crop = int(width * 0.20)  # 20% from each side
        left = horizontal_crop
        right = width - horizontal_crop
        
        # Crop (left, top, right, bottom)
        cropped_img = img.crop((left, 0, right, final_height))
        
        # Save cropped image (overwrite original)
        cropped_img.save(image_path)
        print(f"✂️ Image cropped (center 60% width, top 35% height): {image_path}")
        
        return image_path
    except Exception as e:
        print(f"⚠️ Failed to crop image: {e}")
        return image_path


async def check_account_with_screenshot(
    username: str,
    cookies: list,
    headless: bool = True,
    timeout_ms: int = 30000,
    screenshot_dir: str = "screenshots"
) -> Dict[str, Any]:
    """
    Check Instagram account using Playwright with screenshot.
    
    Args:
        username: Instagram username to check (without @)
        cookies: List of cookies from Instagram session
        headless: Run browser in headless mode
        timeout_ms: Timeout for page operations
        screenshot_dir: Directory to save screenshots
        
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
        browser = await p.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )
        
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Add cookies to context
        for cookie in cookies:
            try:
                await context.add_cookies([{
                    "name": cookie["name"],
                    "value": cookie["value"],
                    "domain": cookie.get("domain", ".instagram.com"),
                    "path": cookie.get("path", "/"),
                    "expires": cookie.get("expires", -1)
                }])
            except Exception as e:
                print(f"Warning: Failed to add cookie {cookie['name']}: {e}")
        
        page = await context.new_page()
        
        try:
            print(f"🔍 Checking @{username}...")
            
            # Navigate to profile
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            
            # Wait for page to load
            await page.wait_for_timeout(2000)
            
            # Check if profile exists - multiple methods
            try:
                # Method 1: Look for "Sorry, this page isn't available" or similar
                not_found_selectors = [
                    "text=Sorry, this page isn't available",
                    "text=The link you followed may be broken",
                    "text=This Account is Private",
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
                # Check if we have any profile data
                has_data = any([
                    result["full_name"],
                    result["followers"] is not None,
                    result["following"] is not None,
                    result["posts"] is not None
                ])
                
                if has_data:
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
