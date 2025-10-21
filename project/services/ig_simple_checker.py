"""Simple Instagram account checker using undetected-chromedriver with screenshots."""

import asyncio
import os
import sys
import time
import random
from typing import Optional, Dict, Any, List
from datetime import datetime
from bs4 import BeautifulSoup
from PIL import Image
import re

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
        print(f"[IG-SIMPLE-CHECKER] ⚠️ Failed to patch distutils: {e}")
        return False

# Применяем патч
patch_distutils()

# Теперь импортируем undetected_chromedriver
try:
    import undetected_chromedriver as uc
    print("[IG-SIMPLE-CHECKER] ✅ undetected-chromedriver imported successfully")
except ImportError as e:
    print(f"[IG-SIMPLE-CHECKER] ❌ Failed to import undetected-chromedriver: {e}")
    uc = None

# Regular expressions for parsing profile data
RE_FOLLOWERS = re.compile(r'"edge_followed_by"\s*:\s*\{"count"\s*:\s*(\d+)\}', re.I)
RE_FOLLOWING = re.compile(r'"edge_follow"\s*:\s*\{"count"\s*:\s*(\d+)\}', re.I)
RE_POSTS = re.compile(r'"edge_owner_to_timeline_media"\s*:\s*\{"count"\s*:\s*(\d+)\}', re.I)

# Расширенные случайные параметры браузера для ротации
def get_random_browser_params():
    """Генерирует случайные параметры браузера для каждого запроса"""
    return {
        "user_agent": random.choice([
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]),
        "viewport": random.choice([
            (1920, 1080), (1366, 768), (1536, 864), (1440, 900), (1280, 720),
            (1600, 900), (1024, 768), (1280, 1024), (1680, 1050), (2560, 1440)
        ]),
        "locale": random.choice([
            "en-US", "en-GB", "de-DE", "fr-FR", "es-ES", "it-IT", "pt-BR", "ru-RU",
            "ja-JP", "ko-KR", "zh-CN", "ar-SA", "hi-IN", "th-TH", "vi-VN"
        ]),
        "timezone": random.choice([
            "America/New_York", "America/Los_Angeles", "America/Chicago", "America/Denver",
            "Europe/London", "Europe/Berlin", "Europe/Paris", "Europe/Rome", "Europe/Madrid",
            "Asia/Tokyo", "Asia/Shanghai", "Asia/Seoul", "Asia/Dubai", "Asia/Kolkata",
            "Australia/Sydney", "Australia/Melbourne", "Africa/Cairo", "Africa/Johannesburg"
        ])
    }

async def check_and_refresh_session(
    driver,
    ig_username: Optional[str] = None,
    ig_password: Optional[str] = None,
    cookies: Optional[List[Dict]] = None
) -> bool:
    """
    Check if Instagram session is valid and refresh if needed using undetected-chromedriver.
    
    Args:
        driver: undetected-chromedriver instance
        ig_username: Instagram username for login
        ig_password: Instagram password for login
        cookies: List of cookies to set
    
    Returns:
        bool: True if session is valid or successfully refreshed
    """
    if uc is None:
        print("[IG-SIMPLE-CHECKER] ❌ undetected-chromedriver not available")
        return False
    
    try:
        # Check if we're already logged in
        current_url = driver.current_url
        if "instagram.com" in current_url and "accounts/login" not in current_url:
            # Try to access a profile to check if session is valid
            driver.get("https://www.instagram.com/")
            time.sleep(random.uniform(2, 4))
            
            # Check if we're redirected to login
            if "accounts/login" in driver.current_url:
                print("[IG-SIMPLE-CHECKER] 🔄 Session expired, need to login")
                return await login_to_instagram(driver, ig_username, ig_password, cookies)
            else:
                print("[IG-SIMPLE-CHECKER] ✅ Session is valid")
                return True
        else:
            print("[IG-SIMPLE-CHECKER] 🔄 Need to login")
            return await login_to_instagram(driver, ig_username, ig_password, cookies)
            
    except Exception as e:
        print(f"[IG-SIMPLE-CHECKER] ❌ Error checking session: {e}")
        return False

async def login_to_instagram(
    driver,
    ig_username: Optional[str] = None,
    ig_password: Optional[str] = None,
    cookies: Optional[List[Dict]] = None
) -> bool:
    """
    Login to Instagram using undetected-chromedriver.
    
    Args:
        driver: undetected-chromedriver instance
        ig_username: Instagram username
        ig_password: Instagram password
        cookies: List of cookies to set
    
    Returns:
        bool: True if login successful
    """
    if uc is None:
        print("[IG-SIMPLE-CHECKER] ❌ undetected-chromedriver not available")
        return False
    
    try:
        # Go to Instagram login page
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(random.uniform(3, 5))
        
        # Try to set cookies first if available
        if cookies:
            print("[IG-SIMPLE-CHECKER] 🍪 Setting cookies...")
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    print(f"[IG-SIMPLE-CHECKER] ⚠️ Failed to set cookie: {e}")
            
            # Refresh page to apply cookies
            driver.refresh()
            time.sleep(random.uniform(2, 4))
            
            # Check if cookies worked
            if "accounts/login" not in driver.current_url:
                print("[IG-SIMPLE-CHECKER] ✅ Login successful with cookies")
                return True
        
        # If cookies didn't work or not available, try username/password
        if ig_username and ig_password:
            print(f"[IG-SIMPLE-CHECKER] 🔑 Logging in with username: {ig_username}")
            
            # Find username field
            username_field = driver.find_element("name", "username")
            username_field.clear()
            username_field.send_keys(ig_username)
            time.sleep(random.uniform(1, 2))
            
            # Find password field
            password_field = driver.find_element("name", "password")
            password_field.clear()
            password_field.send_keys(ig_password)
            time.sleep(random.uniform(1, 2))
            
            # Click login button
            login_button = driver.find_element("css selector", "button[type='submit']")
            login_button.click()
            time.sleep(random.uniform(3, 5))
            
            # Check if login was successful
            if "accounts/login" not in driver.current_url:
                print("[IG-SIMPLE-CHECKER] ✅ Login successful")
                return True
            else:
                print("[IG-SIMPLE-CHECKER] ❌ Login failed")
                return False
        else:
            print("[IG-SIMPLE-CHECKER] ⚠️ No credentials provided for login")
            return False
            
    except Exception as e:
        print(f"[IG-SIMPLE-CHECKER] ❌ Login error: {e}")
        return False

async def check_account_with_screenshot(
    username: str,
    ig_username: Optional[str] = None,
    ig_password: Optional[str] = None,
    cookies: Optional[List[Dict]] = None,
    headless: bool = True,
    screenshot_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check Instagram account using undetected-chromedriver with session management.
    
    Args:
        username: Instagram username to check
        ig_username: Instagram username for session
        ig_password: Instagram password for session
        cookies: List of cookies for session
        headless: Run browser in headless mode
        screenshot_path: Path to save screenshot
    
    Returns:
        dict with check results
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
        "checked_via": "undetected_instagram",
        "screenshot_path": None
    }
    
    if uc is None:
        result["error"] = "undetected-chromedriver not available"
        return result
    
    driver = None
    try:
        # Получаем случайные параметры
        browser_params = get_random_browser_params()
        
        # Создаем опции Chrome
        options = uc.ChromeOptions()
        
        # Расширенные аргументы для обхода детекта и перенаправления
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-field-trial-config')
        options.add_argument('--disable-ipc-flooding-protection')
        options.add_argument('--no-first-run')
        options.add_argument('--no-default-browser-check')
        options.add_argument('--disable-default-apps')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-translate')
        options.add_argument('--disable-background-networking')
        options.add_argument('--disable-sync')
        options.add_argument('--metrics-recording-only')
        options.add_argument('--no-report-upload')
        options.add_argument('--disable-logging')
        options.add_argument('--disable-gpu-logging')
        options.add_argument('--silent')
        
        # Дополнительные аргументы для обхода перенаправления
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-ipc-flooding-protection')
        options.add_argument('--exclude-switches=enable-automation')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        options.add_argument('--disable-site-isolation-trials')
        options.add_argument('--disable-features=BlockInsecurePrivateNetworkRequests')
        options.add_argument('--disable-client-side-phishing-detection')
        options.add_argument('--disable-component-extensions-with-background-pages')
        options.add_argument('--disable-default-apps')
        options.add_argument('--disable-domain-reliability')
        options.add_argument('--disable-features=AudioServiceOutOfProcess')
        options.add_argument('--disable-hang-monitor')
        options.add_argument('--disable-prompt-on-repost')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-sync-preferences')
        options.add_argument('--disable-web-resources')
        options.add_argument('--no-service-autorun')
        options.add_argument('--password-store=basic')
        options.add_argument('--use-mock-keychain')
        
        # Случайные дополнительные аргументы
        additional_args = [
            '--disable-features=VizDisplayCompositor',
            '--disable-features=TranslateUI',
            '--disable-features=MediaRouter',
            '--disable-features=WebRTC',
            '--disable-features=WebRtcHideLocalIpsWithMdns',
            '--disable-features=WebRtcUseMinMaxVEADimensions',
            '--disable-features=WebRtcUseEchoCanceller3',
            '--disable-features=WebRtcUseMinMaxVEADimensions'
        ]
        
        # Добавляем случайные дополнительные аргументы
        for arg in random.sample(additional_args, random.randint(2, 4)):
            options.add_argument(arg)
        
        # Случайные параметры
        options.add_argument(f'--window-size={browser_params["viewport"][0]},{browser_params["viewport"][1]}')
        options.add_argument(f'--user-agent={browser_params["user_agent"]}')
        
        # Headless режим
        if headless:
            options.add_argument('--headless')
        
        # Создаем драйвер
        driver = uc.Chrome(options=options, version_main=None)
        
        # Check and refresh session
        session_valid = await check_and_refresh_session(driver, ig_username, ig_password, cookies)
        if not session_valid:
            result["error"] = "Failed to establish Instagram session"
            return result
        
        # Navigate to profile
        url = f"https://www.instagram.com/{username}/"
        print(f"[IG-SIMPLE-CHECKER] 🌐 Navigating to: {url}")
        driver.get(url)
        time.sleep(random.uniform(3, 5))
        
        # Check for login redirect
        current_url = driver.current_url
        page_source = driver.page_source
        
        if "accounts/login" in current_url or "Accedi" in page_source or "Log in" in page_source:
            print(f"[IG-SIMPLE-CHECKER] 🔄 Redirected to login - account exists but session expired")
            result["exists"] = True
            result["note"] = "Redirected to login page"
            result["error"] = "Session expired"
            
            # Take screenshot of login page if requested
            if screenshot_path:
                try:
                    driver.save_screenshot(screenshot_path)
                    result["screenshot_path"] = screenshot_path
                    print(f"[IG-SIMPLE-CHECKER] 📸 Login page screenshot saved: {screenshot_path}")
                except Exception as e:
                    print(f"[IG-SIMPLE-CHECKER] ⚠️ Failed to take login page screenshot: {e}")
            
            return result
        
        # Check for protection
        if "Take a quick pause" in page_source:
            print(f"[IG-SIMPLE-CHECKER] ⚠️ Detected 'Take a quick pause' protection")
            result["error"] = "Instagram protection detected"
            return result
        
        if "We're seeing more requests" in page_source:
            print(f"[IG-SIMPLE-CHECKER] ⚠️ Detected rate limiting")
            result["error"] = "Rate limited by Instagram"
            return result
        
        # Check if account exists
        if "Sorry, this page isn't available" in page_source:
            print(f"[IG-SIMPLE-CHECKER] ❌ Account @{username} not found")
            result["exists"] = False
            return result
        
        # Account exists, check if private
        if "This account is private" in page_source:
            print(f"[IG-SIMPLE-CHECKER] 🔒 Account @{username} is private")
            result["exists"] = True
            result["is_private"] = True
        else:
            print(f"[IG-SIMPLE-CHECKER] ✅ Account @{username} found and public")
            result["exists"] = True
            result["is_private"] = False
            
            # Extract account information
            try:
                # Full name
                full_name_elements = driver.find_elements("css selector", "h2")
                if full_name_elements:
                    result["full_name"] = full_name_elements[0].text.strip()
                    print(f"[IG-SIMPLE-CHECKER] 👤 Full name: {result['full_name']}")
                
                # Followers, Following, Posts
                counts_elements = driver.find_elements("css selector", "a[href*='/followers/'], a[href*='/following/'], a[href*='/p/'] span")
                if len(counts_elements) >= 3:
                    result["followers"] = counts_elements[0].text.strip()
                    result["following"] = counts_elements[1].text.strip()
                    result["posts"] = counts_elements[2].text.strip()
                    print(f"[IG-SIMPLE-CHECKER] 👥 Followers: {result['followers']}, Following: {result['following']}, Posts: {result['posts']}")
                    
            except Exception as e:
                print(f"[IG-SIMPLE-CHECKER] ⚠️ Could not extract account info: {e}")
        
        # Take screenshot if requested
        if screenshot_path:
            try:
                driver.save_screenshot(screenshot_path)
                result["screenshot_path"] = screenshot_path
                print(f"[IG-SIMPLE-CHECKER] 📸 Screenshot saved: {screenshot_path}")
            except Exception as e:
                print(f"[IG-SIMPLE-CHECKER] ⚠️ Failed to take screenshot: {e}")
        
    except Exception as e:
        print(f"[IG-SIMPLE-CHECKER] ❌ Error: {e}")
        result["error"] = str(e)
    finally:
        if driver:
            driver.quit()
    
    return result


async def check_account_with_enhanced_hybrid(
    username: str,
    screenshot_path: Optional[str] = None,
    headless: bool = True,
    max_retries: int = 2,
    proxy: Optional[str] = None
) -> Dict[str, Any]:
    """
    🔥 УЛУЧШЕННАЯ ГИБРИДНАЯ ПРОВЕРКА для ig_simple_checker
    
    Обертка над новой гибридной системой для совместимости
    с существующим кодом ig_simple_checker.
    
    Args:
        username: Instagram username to check
        screenshot_path: Path for screenshot
        headless: Run in headless mode
        max_retries: Maximum retry attempts
        proxy: Proxy string (optional)
        
    Returns:
        Dict with check results in ig_simple_checker format
    """
    print(f"[IG-ENHANCED] 🔥 Запуск улучшенной гибридной проверки для @{username}")
    
    try:
        # Импортируем улучшенную гибридную систему
        from .instagram_hybrid_proxy import check_account_with_hybrid_proxy
        
        # Вызываем улучшенную гибридную систему
        result = await check_account_with_hybrid_proxy(
            username=username,
            screenshot_path=screenshot_path,
            headless=headless,
            max_retries=max_retries,
            proxy=proxy
        )
        
        # Форматируем результат в формате ig_simple_checker
        formatted_result = {
            "username": result.get("username", username),
            "exists": result.get("exists"),
            "is_private": None,  # Не определяется в новой системе
            "full_name": result.get("full_name"),
            "followers": result.get("followers"),
            "following": result.get("following"),
            "posts": result.get("posts"),
            "screenshot_path": result.get("screenshot_path"),
            "error": result.get("error"),
            "checked_via": "enhanced_hybrid_proxy",
            "proxy_used": result.get("proxy_used", False),
            "api_method": result.get("api_method"),
            "api_status_code": result.get("api_status_code"),
            "screenshot_created": result.get("screenshot_created", False)
        }
        
        print(f"[IG-ENHANCED] 📊 Результат улучшенной проверки:")
        print(f"[IG-ENHANCED]   ✅ Профиль существует: {formatted_result.get('exists')}")
        print(f"[IG-ENHANCED]   📸 Скриншот создан: {formatted_result.get('screenshot_created', False)}")
        print(f"[IG-ENHANCED]   🔗 Прокси использован: {formatted_result.get('proxy_used', False)}")
        
        return formatted_result
        
    except Exception as e:
        print(f"[IG-ENHANCED] ❌ Ошибка улучшенной гибридной проверки: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "username": username,
            "exists": None,
            "is_private": None,
            "full_name": None,
            "followers": None,
            "following": None,
            "posts": None,
            "screenshot_path": None,
            "error": f"Ошибка улучшенной гибридной проверки: {e}",
            "checked_via": "enhanced_hybrid_proxy",
            "proxy_used": bool(proxy),
            "screenshot_created": False
        }

# Остальные функции остаются без изменений, но используют undetected-chromedriver
# ... (остальной код аналогично)
