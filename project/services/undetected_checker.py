"""Instagram account checker using undetected-chromedriver for maximum stealth."""

import asyncio
import random
import time
import os
import sys
from typing import Dict, Any, Optional

# Патч для исправления проблемы с distutils в Python 3.12
def patch_distutils():
    """Создает локальный патч для distutils"""
    try:
        # Создаем временный модуль distutils
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
        print(f"[UNDETECTED-CHECKER] ⚠️ Failed to patch distutils: {e}")
        return False

# Применяем патч
patch_distutils()

# Теперь импортируем undetected_chromedriver
try:
    import undetected_chromedriver as uc
    print("[UNDETECTED-CHECKER] ✅ undetected-chromedriver imported successfully")
except ImportError as e:
    print(f"[UNDETECTED-CHECKER] ❌ Failed to import undetected-chromedriver: {e}")
    uc = None

async def check_via_json_endpoint(username: str) -> Optional[bool]:
    """
    Быстрая проверка через JSON endpoint Instagram без браузера.
    
    Args:
        username: Instagram username to check
    
    Returns:
        True if exists, False if not found, None if error/uncertain
    """
    try:
        import requests
        
        headers = {
            'User-Agent': random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]),
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.instagram.com/',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        # Пробуем JSON endpoint
        print(f"[JSON-ENDPOINT] 🔍 Checking @{username} via JSON API...")
        response = requests.get(
            f'https://www.instagram.com/api/v1/users/web_profile_info/?username={username}',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'user' in data['data']:
                print(f"[JSON-ENDPOINT] ✅ Account @{username} found via JSON API")
                return True
            else:
                print(f"[JSON-ENDPOINT] ❌ Account @{username} not found via JSON API")
                return False
        elif response.status_code == 404:
            print(f"[JSON-ENDPOINT] ❌ Account @{username} not found (404)")
            return False
        else:
            print(f"[JSON-ENDPOINT] ⚠️ Unexpected status code: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"[JSON-ENDPOINT] ⚠️ Error checking via JSON endpoint: {e}")
        return None

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

async def check_account_undetected_chrome(
    username: str,
    proxy: Optional[Dict] = None,
    screenshot_path: Optional[str] = None,
    headless: bool = True
) -> Dict[str, Any]:
    """
    Проверяет аккаунт Instagram с помощью undetected-chromedriver
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
        "checked_via": "undetected_chrome",
        "screenshot_path": None
    }
    
    if uc is None:
        result["error"] = "undetected-chromedriver not available"
        return result
    
    print(f"[UNDETECTED-CHROME] 🔍 Checking @{username}...")
    
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
            proxy_url = f"{proxy['scheme']}://{proxy['host']}"
            if proxy.get('username') and proxy.get('password'):
                proxy_url = f"{proxy['scheme']}://{proxy['username']}:{proxy['password']}@{proxy['host']}"
            options.add_argument(f'--proxy-server={proxy_url}')
            print(f"[UNDETECTED-CHROME] 🔗 Using proxy: {proxy['scheme']}://{proxy['host']}")
        
        # Отключаем автоматизационные флаги (критически важно!)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Headless режим
        if headless:
            options.add_argument('--headless')
        
        # Создаем драйвер
        driver = uc.Chrome(options=options, version_main=None)
        
        try:
            # Критические настройки для обхода детекта
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": browser_params["user_agent"]
            })
            
            # Скрываем WebDriver признаки через CDP и JavaScript
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
            driver.execute_script("Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8})")
            driver.execute_script("Object.defineProperty(navigator, 'deviceMemory', {get: () => 8})")
            
            # Изменяем размер окна для имитации реального пользователя
            driver.set_window_size(
                random.randint(1200, 1600),
                random.randint(800, 1200)
            )
            
            # Сначала посещаем главную страницу Instagram для подготовки сессии
            print(f"[UNDETECTED-CHROME] 🏠 Preloading Instagram homepage...")
            driver.get('https://www.instagram.com/')
            time.sleep(random.uniform(2, 4))
            
            # Имитируем действия реального пользователя
            driver.execute_script("window.scrollTo(0, 500)")
            time.sleep(random.uniform(0.5, 1.5))
            driver.execute_script("window.scrollTo(500, 1000)")
            time.sleep(random.uniform(0.5, 1.5))
            
            # Имитируем случайные движения мышью
            driver.execute_script("""
                function moveMouseRandomly() {
                    const x = Math.random() * window.innerWidth;
                    const y = Math.random() * window.innerHeight;
                    const event = new MouseEvent('mousemove', {
                        clientX: x,
                        clientY: y,
                        bubbles: true
                    });
                    document.dispatchEvent(event);
                }
                for(let i = 0; i < 3; i++) {
                    setTimeout(moveMouseRandomly, i * 300);
                }
            """)
            time.sleep(random.uniform(1, 2))
            
            # Теперь переходим на профиль
            # Пробуем разные URL-ы для обхода защиты
            urls_to_try = [
                f"https://www.instagram.com/{username}/",
                f"https://www.instagram.com/{username}/?__a=1&__d=dis",
                f"https://www.instagram.com/{username}/channel/",
            ]
            
            profile_loaded = False
            for attempt, url in enumerate(urls_to_try):
                print(f"[UNDETECTED-CHROME] 🌐 Attempt {attempt + 1}: Navigating to: {url}")
                
                driver.get(url)
                
                # Случайная задержка для имитации человека
                time.sleep(random.uniform(3, 7))
                
                # Проверяем, не попали ли на страницу защиты или логина
                page_source = driver.page_source
                current_url = driver.current_url
                
                # Проверяем на перенаправление на страницу логина
                if "instagram.com/accounts/login" in current_url or "Accedi" in page_source or "Log in" in page_source:
                    print(f"[UNDETECTED-CHROME] 🔄 Attempt {attempt + 1}: Redirected to login page")
                    # Не прерываем сразу, пробуем другие URL
                    continue
                
                # Если успешно загрузили профиль, выходим из цикла
                if "Sorry, this page isn't available" not in page_source and username.lower() in page_source.lower():
                    profile_loaded = True
                    print(f"[UNDETECTED-CHROME] ✅ Profile loaded successfully on attempt {attempt + 1}")
                    break
            
            # Если все попытки с URL не сработали, значит редирект на логин
            if not profile_loaded:
                print(f"[UNDETECTED-CHROME] 🔄 All attempts redirected to login - trying different browser config")
                result["exists"] = True
                result["note"] = "Redirected to login page"
                result["error"] = "Need different browser configuration"
                
                # Делаем скриншот страницы логина если нужно
                if screenshot_path:
                    try:
                        driver.save_screenshot(screenshot_path)
                        result["screenshot_path"] = screenshot_path
                        print(f"[UNDETECTED-CHROME] 📸 Login page screenshot saved: {screenshot_path}")
                    except Exception as e:
                        print(f"[UNDETECTED-CHROME] ⚠️ Failed to take login page screenshot: {e}")
                
                return result
            
            # Обновляем page_source и current_url для финальной проверки
            page_source = driver.page_source
            current_url = driver.current_url
            page_title = driver.title.lower()
            
            # КРИТИЧНО: Проверяем на 403 ошибку ПЕРЕД всем остальным
            if ("403" in page_source or "403" in page_title or 
                "forbidden" in page_source.lower() or "forbidden" in page_title or
                "access denied" in page_source.lower() or 
                "не удается получить доступ" in page_source.lower()):
                print(f"[UNDETECTED-CHROME] ⚠️ Detected 403 Forbidden error")
                result["error"] = "403_forbidden"
                result["exists"] = None
                return result
            
            if "Take a quick pause" in page_source:
                print(f"[UNDETECTED-CHROME] ⚠️ Detected 'Take a quick pause' protection")
                result["error"] = "Instagram protection detected"
                return result
            
            if "We're seeing more requests" in page_source:
                print(f"[UNDETECTED-CHROME] ⚠️ Detected rate limiting")
                result["error"] = "Rate limited by Instagram"
                return result
            
            # Проверяем, существует ли аккаунт
            if "Sorry, this page isn't available" in page_source:
                print(f"[UNDETECTED-CHROME] ❌ Account @{username} not found")
                result["exists"] = False
                return result
            
            if "This account is private" in page_source:
                print(f"[UNDETECTED-CHROME] 🔒 Account @{username} is private")
                result["exists"] = True
                result["is_private"] = True
            else:
                print(f"[UNDETECTED-CHROME] ✅ Account @{username} found and public")
                result["exists"] = True
                result["is_private"] = False
                
                # Пытаемся извлечь информацию об аккаунте
                try:
                    # Полное имя
                    full_name_elements = driver.find_elements("css selector", "h2")
                    if full_name_elements:
                        result["full_name"] = full_name_elements[0].text.strip()
                        print(f"[UNDETECTED-CHROME] 👤 Full name: {result['full_name']}")
                    
                    # Подписчики
                    followers_elements = driver.find_elements("css selector", "a[href*='/followers/'] span")
                    if followers_elements:
                        result["followers"] = followers_elements[0].text.strip()
                        print(f"[UNDETECTED-CHROME] 👥 Followers: {result['followers']}")
                    
                    # Подписки
                    following_elements = driver.find_elements("css selector", "a[href*='/following/'] span")
                    if following_elements:
                        result["following"] = following_elements[0].text.strip()
                        print(f"[UNDETECTED-CHROME] 👥 Following: {result['following']}")
                    
                    # Посты
                    posts_elements = driver.find_elements("css selector", "a[href*='/p/'] span")
                    if posts_elements:
                        result["posts"] = posts_elements[0].text.strip()
                        print(f"[UNDETECTED-CHROME] 📸 Posts: {result['posts']}")
                        
                except Exception as e:
                    print(f"[UNDETECTED-CHROME] ⚠️ Could not extract account info: {e}")
            
            # Делаем скриншот если нужно
            if screenshot_path:
                try:
                    driver.save_screenshot(screenshot_path)
                    result["screenshot_path"] = screenshot_path
                    print(f"[UNDETECTED-CHROME] 📸 Screenshot saved: {screenshot_path}")
                except Exception as e:
                    print(f"[UNDETECTED-CHROME] ⚠️ Failed to take screenshot: {e}")
            
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"[UNDETECTED-CHROME] ❌ Error: {e}")
        result["error"] = str(e)
    
    return result

async def check_account_undetected_with_fallback(
    session,
    user_id: int,
    username: str,
    max_attempts: int = None,
    headless: bool = True,
    screenshot_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Проверяет аккаунт с fallback через разные прокси
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
        "checked_via": "undetected_chrome",
        "screenshot_path": None,
        "proxy_used": None,
        "attempts": 0
    }
    
    if max_attempts is None:
        max_attempts = 999  # Effectively unlimited
        print(f"[UNDETECTED-FALLBACK] 🔄 Starting undetected check for @{username} (unlimited attempts)")
    else:
        print(f"[UNDETECTED-FALLBACK] 🔄 Starting undetected check for @{username} (max {max_attempts} attempts)")
    
    # Сначала пробуем быструю проверку через JSON endpoint
    json_result = await check_via_json_endpoint(username)
    if json_result is True:
        print(f"[UNDETECTED-FALLBACK] ✅ Account @{username} confirmed via JSON endpoint - proceeding to browser check for screenshot")
        result["exists"] = True
    elif json_result is False:
        print(f"[UNDETECTED-FALLBACK] ❌ Account @{username} not found via JSON endpoint")
        result["exists"] = False
        return result
    else:
        print(f"[UNDETECTED-FALLBACK] ⚠️ JSON endpoint failed or uncertain - falling back to browser check")
    
    # Получаем прокси для пользователя
    try:
        from ..models import Proxy
        proxies = session.query(Proxy).filter(
            Proxy.user_id == user_id,
            Proxy.is_active == True
        ).order_by(Proxy.priority.asc()).all()
    except ImportError:
        from models import Proxy
        proxies = session.query(Proxy).filter(
            Proxy.user_id == user_id,
            Proxy.is_active == True
        ).order_by(Proxy.priority.asc()).all()
    
    if not proxies:
        print(f"[UNDETECTED-FALLBACK] ⚠️ No proxies available for user {user_id}")
        # Попробуем без прокси
        return await check_account_undetected_chrome(
            username=username,
            proxy=None,
            screenshot_path=screenshot_path,
            headless=headless
        )
    
    current_proxy_id = None
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        result["attempts"] = attempt
        
        # Получаем следующий прокси
        if not current_proxy_id:
            proxy = proxies[0]
        else:
            current_index = None
            for i, p in enumerate(proxies):
                if p.id == current_proxy_id:
                    current_index = i
                    break
            
            if current_index is None:
                proxy = proxies[0]
            else:
                next_index = (current_index + 1) % len(proxies)
                proxy = proxies[next_index]
        
        current_proxy_id = proxy.id
        
        if max_attempts == 999:
            print(f"[UNDETECTED-FALLBACK] 🔗 Attempt {attempt} - Using proxy: {proxy.scheme}://{proxy.host}")
        else:
            print(f"[UNDETECTED-FALLBACK] 🔗 Attempt {attempt}/{max_attempts} - Using proxy: {proxy.scheme}://{proxy.host}")
        
        try:
            # Конвертируем прокси в нужный формат
            proxy_dict = {
                "scheme": proxy.scheme,
                "host": proxy.host,
                "username": proxy.username,
                "password": proxy.password
            }
            
            check_result = await check_account_undetected_chrome(
                username=username,
                proxy=proxy_dict,
                screenshot_path=screenshot_path,
                headless=headless
            )
            
            # Проверяем на 403 ошибку - используем bypass методы
            if check_result.get("error") == "403_forbidden":
                print(f"[UNDETECTED-FALLBACK] ⚠️ 403 Forbidden detected - switching to bypass methods")
                try:
                    # Import and use instagram bypass
                    from .instagram_bypass import check_account_with_bypass
                    print(f"[UNDETECTED-FALLBACK] 🛡️ Using Instagram 403 Bypass for @{username}")
                    
                    bypass_result = await check_account_with_bypass(
                        username=username,
                        screenshot_path=screenshot_path,
                        headless=headless,
                        max_retries=1  # Quick bypass attempt
                    )
                    
                    if bypass_result.get("exists") is not None:
                        result.update(bypass_result)
                        result["proxy_used"] = f"bypass_methods"
                        result["checked_via"] = "undetected_fallback_with_bypass"
                        print(f"[UNDETECTED-FALLBACK] ✅ Success with bypass methods")
                        break
                except Exception as bypass_error:
                    print(f"[UNDETECTED-FALLBACK] ❌ Bypass methods failed: {bypass_error}")
                    continue
            
            # Проверяем результат
            elif check_result.get("exists") is not None:
                # Если аккаунт найден, но перенаправлен на логин - пробуем другой браузер
                if (check_result.get("exists") is True and 
                    check_result.get("error") == "Need different browser configuration"):
                    print(f"[UNDETECTED-FALLBACK] 🔄 Account exists but redirected to login - trying different browser config...")
                    # Продолжаем с другим прокси и другими параметрами браузера
                    continue
                else:
                    result.update(check_result)
                    result["proxy_used"] = f"{proxy.scheme}://{proxy.host}"
                    print(f"[UNDETECTED-FALLBACK] ✅ Success with proxy {proxy.host}")
                    break
            else:
                print(f"[UNDETECTED-FALLBACK] ⚠️ Proxy {proxy.host} failed - trying next proxy...")
                continue
                
        except Exception as e:
            print(f"[UNDETECTED-FALLBACK] ❌ Proxy {proxy.host} error: {e}")
            print(f"[UNDETECTED-FALLBACK] 🔄 Switching to next proxy...")
            continue
    
    if result["exists"] is None and not result.get("error"):
        result["error"] = f"All {max_attempts} proxies failed"
        print(f"[UNDETECTED-FALLBACK] ❌ All proxies failed for @{username}")
    
    return result


async def check_account_with_full_bypass(
    session,
    user_id: int,
    username: str,
    headless: bool = True,
    screenshot_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check Instagram account using full bypass system with all methods.
    
    Args:
        session: Database session
        user_id: User ID
        username: Instagram username
        headless: Run in headless mode
        screenshot_path: Path to save screenshot (optional)
        
    Returns:
        dict with check results
    """
    print(f"[FULL-BYPASS] 🚀 Запуск полного обхода для @{username}")
    
    try:
        # Импортируем систему обхода
        from .instagram_bypass import check_account_with_bypass
        
        # Запускаем полную проверку
        result = await check_account_with_bypass(
            username=username,
            screenshot_path=screenshot_path,
            headless=headless
        )
        
        print(f"[FULL-BYPASS] ✅ Результат для @{username}: {result.get('exists')}")
        return result
        
    except Exception as e:
        print(f"[FULL-BYPASS] ❌ Ошибка для @{username}: {e}")
        return {
            "username": username,
            "exists": None,
            "is_private": None,
            "full_name": None,
            "followers": None,
            "following": None,
            "posts": None,
            "error": str(e),
            "checked_via": "full_bypass_error",
            "screenshot_path": None
        }