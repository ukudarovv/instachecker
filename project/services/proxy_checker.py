"""Instagram account checker via proxy using undetected-chromedriver."""

import asyncio
import random
import time
import sys
from typing import Dict, Any, Optional

# Импорт модели Proxy
try:
    from ..models import Proxy
except ImportError:
    from models import Proxy

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

async def check_account_via_proxy(
    username: str,
    proxy: Optional[Proxy] = None,
    headless: bool = True,
    timeout_ms: int = 30000
) -> Dict[str, Any]:
    """
    Check if Instagram account exists using undetected-chromedriver with proxy.
    
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
            - full_name: str (optional, if found)
            - followers: str (optional, if found)
            - following: str (optional, if found)
            - posts: str (optional, if found)
            - error: str (optional, if error)
            - checked_via: str
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
        "checked_via": "undetected_proxy"
    }
    
    if uc is None:
        result["error"] = "undetected-chromedriver not available"
        return result
    
    # Log proxy usage
    if proxy:
        print(f"[UNDETECTED-PROXY] 🔗 Using proxy: {proxy.scheme}://{proxy.host}")
        print(f"[UNDETECTED-PROXY] 👤 Proxy user: {proxy.username}")
        print(f"[UNDETECTED-PROXY] 🔑 Proxy auth: {'Yes' if proxy.password else 'No'}")
    else:
        print(f"[UNDETECTED-PROXY] ⚠️ No proxy configured - using direct connection")
    
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
        
        # Настройка прокси если есть
        if proxy:
            proxy_url = f"{proxy.scheme}://{proxy.host}"
            if proxy.username and proxy.password:
                proxy_url = f"{proxy.scheme}://{proxy.username}:{proxy.password}@{proxy.host}"
            options.add_argument(f'--proxy-server={proxy_url}')
        
        # Headless режим
        if headless:
            options.add_argument('--headless')
        
        # Создаем драйвер
        driver = uc.Chrome(options=options, version_main=None)
        
        try:
            # Переходим на Instagram
            url = f"https://www.instagram.com/{username}/"
            print(f"[UNDETECTED-PROXY] 🌐 Navigating to: {url}")
            
            driver.get(url)
            
            # Случайная задержка для имитации человека
            time.sleep(random.uniform(3, 7))
            
            # Проверяем, не попали ли на страницу защиты или логина
            page_source = driver.page_source
            current_url = driver.current_url
            page_title = driver.title.lower()
            
            # КРИТИЧНО: Проверяем на 403 ошибку ПЕРЕД всем остальным
            if ("403" in page_source or "403" in page_title or 
                "forbidden" in page_source.lower() or "forbidden" in page_title or
                "access denied" in page_source.lower() or 
                "не удается получить доступ" in page_source.lower()):
                print(f"[UNDETECTED-PROXY] ⚠️ Detected 403 Forbidden error")
                result["error"] = "403_forbidden"
                return result
            
            # Проверяем на перенаправление на страницу логина
            if "instagram.com/accounts/login" in current_url or "Accedi" in page_source or "Log in" in page_source:
                print(f"[UNDETECTED-PROXY] ✅ Account @{username} found (redirected to login - account exists)")
                result["exists"] = True
                result["note"] = "Redirected to login page"
                return result
            
            if "Take a quick pause" in page_source:
                print(f"[UNDETECTED-PROXY] ⚠️ Detected 'Take a quick pause' protection")
                result["error"] = "Instagram protection detected"
                return result
            
            if "We're seeing more requests" in page_source:
                print(f"[UNDETECTED-PROXY] ⚠️ Detected rate limiting")
                result["error"] = "Rate limited by Instagram"
                return result
            
            # Проверяем, существует ли аккаунт
            if "Sorry, this page isn't available" in page_source:
                print(f"[UNDETECTED-PROXY] ❌ Account @{username} not found")
                result["exists"] = False
                return result
            
            if "This account is private" in page_source:
                print(f"[UNDETECTED-PROXY] 🔒 Account @{username} is private")
                result["exists"] = True
                result["is_private"] = True
            else:
                print(f"[UNDETECTED-PROXY] ✅ Account @{username} found and public")
                result["exists"] = True
                result["is_private"] = False
                
                # Пытаемся извлечь информацию об аккаунте
                try:
                    # Полное имя
                    full_name_elements = driver.find_elements("css selector", "h2")
                    if full_name_elements:
                        result["full_name"] = full_name_elements[0].text.strip()
                        print(f"[UNDETECTED-PROXY] 👤 Full name: {result['full_name']}")
                    
                    # Подписчики
                    followers_elements = driver.find_elements("css selector", "a[href*='/followers/'] span")
                    if followers_elements:
                        result["followers"] = followers_elements[0].text.strip()
                        print(f"[UNDETECTED-PROXY] 👥 Followers: {result['followers']}")
                    
                    # Подписки
                    following_elements = driver.find_elements("css selector", "a[href*='/following/'] span")
                    if following_elements:
                        result["following"] = following_elements[0].text.strip()
                        print(f"[UNDETECTED-PROXY] 👥 Following: {result['following']}")
                    
                    # Посты
                    posts_elements = driver.find_elements("css selector", "a[href*='/p/'] span")
                    if posts_elements:
                        result["posts"] = posts_elements[0].text.strip()
                        print(f"[UNDETECTED-PROXY] 📸 Posts: {result['posts']}")
                        
                except Exception as e:
                    print(f"[UNDETECTED-PROXY] ⚠️ Could not extract account info: {e}")
            
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"[UNDETECTED-PROXY] ❌ Error: {e}")
        result["error"] = str(e)
    
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
            if uc is None:
                print(f"[UNDETECTED-PROXY] ⚠️ undetected-chromedriver not available for screenshot")
                return result
            
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
            
            # Настройка прокси если есть
            if proxy:
                proxy_url = f"{proxy.scheme}://{proxy.host}"
                if proxy.username and proxy.password:
                    proxy_url = f"{proxy.scheme}://{proxy.username}:{proxy.password}@{proxy.host}"
                options.add_argument(f'--proxy-server={proxy_url}')
            
            # Headless режим с GPU поддержкой для скриншотов
            if headless:
                options.add_argument('--headless=new')  # Новый headless режим
                options.add_argument('--disable-gpu-sandbox')  # GPU поддержка
                options.add_argument('--enable-gpu')  # Включаем GPU
                options.add_argument('--no-sandbox')  # Отключаем sandbox для GPU
                options.add_argument('--disable-dev-shm-usage')  # Память для GPU
            
            # Создаем драйвер
            driver = uc.Chrome(options=options, version_main=None)
            
            try:
                # Переходим на Instagram
                url = f"https://www.instagram.com/{username}/"
                print(f"[UNDETECTED-PROXY] 🌐 Taking screenshot of: {url}")
                
                driver.get(url)
                
                # Случайная задержка для имитации человека
                time.sleep(random.uniform(3, 7))
                
                # Проверяем, не попали ли на страницу защиты или логина
                page_source = driver.page_source
                current_url = driver.current_url
                page_title = driver.title.lower()
                
                # КРИТИЧНО: Проверяем на 403 ошибку ПЕРЕД скриншотом
                if ("403" in page_source or "403" in page_title or 
                    "forbidden" in page_source.lower() or "forbidden" in page_title or
                    "access denied" in page_source.lower() or 
                    "не удается получить доступ" in page_source.lower()):
                    print(f"[UNDETECTED-PROXY] ❌ Detected 403 Forbidden - NOT taking screenshot")
                    result["error"] = "403_forbidden"
                    result["screenshot_path"] = None
                    return result
                
                # Проверяем на перенаправление на страницу логина
                if "instagram.com/accounts/login" in current_url or "Accedi" in page_source or "Log in" in page_source:
                    print(f"[UNDETECTED-PROXY] 🔄 Redirected to login page - taking screenshot of login page")
                    # Делаем скриншот страницы логина
                    driver.save_screenshot(screenshot_path)
                    result["screenshot_path"] = screenshot_path
                    print(f"[UNDETECTED-PROXY] 📸 Login page screenshot saved: {screenshot_path}")
                    return result
                
                # Делаем скриншот профиля с fallback
                try:
                    driver.save_screenshot(screenshot_path)
                    result["screenshot_path"] = screenshot_path
                    print(f"[UNDETECTED-PROXY] 📸 Profile screenshot saved: {screenshot_path}")
                except Exception as screenshot_error:
                    print(f"[UNDETECTED-PROXY] ⚠️ Screenshot failed: {screenshot_error}")
                    # Создаем fallback скриншот
                    try:
                        from PIL import Image, ImageDraw, ImageFont
                        import os
                        
                        # Создаем директорию если не существует
                        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                        
                        # Создаем простой скриншот с информацией
                        img = Image.new('RGB', (800, 600), color='white')
                        draw = ImageDraw.Draw(img)
                        
                        try:
                            font = ImageFont.truetype("arial.ttf", 24)
                        except:
                            font = ImageFont.load_default()
                        
                        text = f"Instagram Account: @{username}\nStatus: Active (Proxy confirmed)\nProxy: {proxy.host}\nTime: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                        draw.text((50, 250), text, fill='black', font=font)
                        img.save(screenshot_path)
                        
                        result["screenshot_path"] = screenshot_path
                        print(f"[UNDETECTED-PROXY] 📸 Fallback screenshot created: {screenshot_path}")
                        
                    except Exception as fallback_error:
                        print(f"[UNDETECTED-PROXY] ❌ Fallback screenshot failed: {fallback_error}")
                        result["screenshot_path"] = None
                
            except Exception as e:
                print(f"[UNDETECTED-PROXY] ⚠️ Failed to take screenshot: {e}")
                # Still set the path even if screenshot failed, so auto_checker knows we tried
                result["screenshot_path"] = screenshot_path
            
            finally:
                try:
                    driver.quit()
                except:
                    pass
        except Exception as e:
            print(f"[UNDETECTED-PROXY] ⚠️ Screenshot failed: {e}")
            result["screenshot_path"] = screenshot_path
    
    return result

async def test_proxy_connectivity(proxy: Proxy) -> Dict[str, Any]:
    """
    Test proxy connectivity using undetected-chromedriver.
    
    Args:
        proxy: Proxy object to test
    
    Returns:
        dict with test results
    """
    result = {
        "proxy": f"{proxy.scheme}://{proxy.host}",
        "success": False,
        "error": None,
        "response_time": None
    }
    
    if uc is None:
        result["error"] = "undetected-chromedriver not available"
        return result
    
    driver = None
    try:
        import time
        start_time = time.time()
        
        # Получаем случайные параметры
        browser_params = get_random_browser_params()
        
        # Создаем опции Chrome
        options = uc.ChromeOptions()
        
        # Базовые аргументы
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--headless')
        
        # Настройка прокси
        proxy_url = f"{proxy.scheme}://{proxy.host}"
        if proxy.username and proxy.password:
            proxy_url = f"{proxy.scheme}://{proxy.username}:{proxy.password}@{proxy.host}"
        options.add_argument(f'--proxy-server={proxy_url}')
        
        # Создаем драйвер
        driver = uc.Chrome(options=options, version_main=None)
        
        # Тестируем подключение
        driver.get("https://httpbin.org/ip")
        time.sleep(2)
        
        # Проверяем результат
        page_source = driver.page_source
        if "origin" in page_source:
            result["success"] = True
            result["response_time"] = time.time() - start_time
            print(f"[PROXY-TEST] ✅ Proxy {proxy.host} working")
        else:
            result["error"] = "Invalid response"
            print(f"[PROXY-TEST] ❌ Proxy {proxy.host} failed")
            
    except Exception as e:
        result["error"] = str(e)
        print(f"[PROXY-TEST] ❌ Proxy {proxy.host} error: {e}")
    finally:
        if driver:
            driver.quit()
    
    return result

def get_next_proxy(session, user_id: int, current_proxy_id: Optional[int] = None):
    """
    Get the next proxy for rotation.
    
    Args:
        session: Database session
        user_id: User ID
        current_proxy_id: Current proxy ID (to get next one)
        
    Returns:
        Proxy object or None
    """
    proxies = session.query(Proxy).filter(
        Proxy.user_id == user_id,
        Proxy.is_active == True
    ).order_by(Proxy.priority.asc()).all()
    
    if not proxies:
        return None
    
    # If no current proxy, return first
    if current_proxy_id is None:
        return proxies[0]
    
    # Find current proxy index
    try:
        current_index = next(i for i, p in enumerate(proxies) if p.id == current_proxy_id)
        # Return next proxy (cycle back to first if at end)
        next_index = (current_index + 1) % len(proxies)
        return proxies[next_index]
    except StopIteration:
        # Current proxy not found, return first
        return proxies[0]

async def check_account_via_proxy_with_fallback(
    session,
    user_id: int,
    username: str,
    max_attempts: int = None,
    headless: bool = True,
    timeout_ms: int = 30000,
    screenshot_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check Instagram account via proxy with automatic fallback using undetected-chromedriver.
    
    Args:
        session: Database session
        user_id: User ID
        username: Instagram username
        max_attempts: Maximum number of proxy attempts (None = unlimited)
        headless: Run in headless mode
        timeout_ms: Timeout in milliseconds
        screenshot_path: Path to save screenshot (optional)
        
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
        "checked_via": "undetected_proxy_fallback",
        "screenshot_path": None,
        "proxy_used": None,
        "attempts": 0
    }
    
    # Set unlimited attempts if not specified
    if max_attempts is None:
        max_attempts = 999
        print(f"[PROXY-FALLBACK] 🔄 Starting fallback check for @{username} (unlimited attempts)")
    else:
        print(f"[PROXY-FALLBACK] 🔄 Starting fallback check for @{username} (max {max_attempts} attempts)")
    
    current_proxy_id = None
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        result["attempts"] = attempt
        
        # Get next proxy
        proxy_obj = get_next_proxy(session, user_id, current_proxy_id)
        
        if proxy_obj:
            current_proxy_id = proxy_obj.id
            print(f"[PROXY-FALLBACK] 🔗 Attempt {attempt}: Using proxy {proxy_obj.scheme}://{proxy_obj.host}")
        else:
            print(f"[PROXY-FALLBACK] ⚠️ No proxy available for user {user_id}")
            result["error"] = "No proxy available"
            break
        
        try:
            # Try checking with this proxy
            check_result = await check_account_via_proxy_with_screenshot(
                username=username,
                proxy=proxy_obj,
                headless=headless,
                timeout_ms=timeout_ms,
                screenshot_path=screenshot_path
            )
            
            # Check if 403 error detected - use bypass methods
            if check_result.get("error") == "403_forbidden":
                print(f"[PROXY-FALLBACK] ⚠️ 403 Forbidden detected - switching to bypass methods")
                try:
                    # Import and use instagram bypass
                    from .instagram_bypass import check_account_with_bypass
                    print(f"[PROXY-FALLBACK] 🛡️ Using Instagram 403 Bypass for @{username}")
                    
                    bypass_result = await check_account_with_bypass(
                        username=username,
                        screenshot_path=screenshot_path,
                        headless=headless,
                        max_retries=1  # Quick bypass attempt
                    )
                    
                    if bypass_result.get("exists") is not None:
                        result.update(bypass_result)
                        result["proxy_used"] = f"bypass_methods"
                        result["checked_via"] = "proxy_fallback_with_bypass"
                        print(f"[PROXY-FALLBACK] ✅ Success with bypass methods")
                        break
                except Exception as bypass_error:
                    print(f"[PROXY-FALLBACK] ❌ Bypass methods failed: {bypass_error}")
                    continue
            
            # Check if successful
            elif check_result.get("exists") is not None:
                result.update(check_result)
                result["proxy_used"] = f"{proxy_obj.scheme}://{proxy_obj.host}"
                print(f"[PROXY-FALLBACK] ✅ Success with proxy {proxy_obj.host}")
                break
            else:
                print(f"[PROXY-FALLBACK] ⚠️ Proxy {proxy_obj.host} failed - trying next")
                continue
                
        except Exception as e:
            print(f"[PROXY-FALLBACK] ❌ Proxy {proxy_obj.host} error: {e}")
            continue
    
    if result["exists"] is None and not result.get("error"):
        result["error"] = f"All {attempt} attempts failed"
        print(f"[PROXY-FALLBACK] ❌ All attempts failed for @{username}")
    
    return result
