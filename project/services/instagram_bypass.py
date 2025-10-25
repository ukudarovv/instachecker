"""Полная система обхода защиты Instagram с множественными методами."""

import time
import random
import requests
import json
import os
from typing import Optional, List, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
try:
    from selenium_stealth import stealth
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False
    print("[BYPASS] ⚠️ selenium-stealth не установлен, некоторые функции недоступны")

class InstagramBypass:
    """Комплексная система обхода защиты Instagram"""
    
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        # Расширенные мобильные User-Agents
        self.mobile_user_agents = [
            'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 15_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 12; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Mobile Safari/537.36',
            'Instagram 269.0.0.18.75 (iPhone13,4; iOS 16_5; en_US; en-US; scale=3.00; 1284x2778; 463736449) AppleWebKit/420+',
        ]
        
        # Различные варианты мобильных заголовков
        self.mobile_headers_list = [
            {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Accept-Encoding': 'gzip,deflate',
                'Connection': 'keep-alive',
            },
            {
                'User-Agent': 'Instagram 269.0.0.18.75 (iPhone13,4; iOS 16_5; en_US; en-US; scale=3.00; 1284x2778; 463736449) AppleWebKit/420+',
                'X-IG-App-ID': '124024574287414',
                'X-IG-Capabilities': '3brTvx8=',
                'X-IG-Connection-Type': 'WIFI',
            },
            {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
                'X-Requested-With': 'com.instagram.android',
            }
        ]
        
        self.mobile_headers = {
            'User-Agent': 'Instagram 269.0.0.18.75 (iPhone13,4; iOS 16_5; en_US; en-US; scale=3.00; 1284x2778; 463736449) AppleWebKit/420+',
            'X-IG-App-ID': '124024574287414',
            'X-IG-Capabilities': '3brTvx8=',
            'X-IG-Connection-Type': 'WIFI',
            'Accept-Language': 'en-US',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
    
    def create_fully_undetected_driver(self) -> uc.Chrome:
        """Создание полностью скрытого браузера"""
        print("[BYPASS] 🔧 Создание скрытого браузера...")
        
        options = uc.ChromeOptions()
        
        # Основные настройки скрытия
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-ipc-flooding-protection')
        options.add_argument('--no-default-browser-check')
        options.add_argument('--disable-component-extensions-with-background-pages')
        options.add_argument('--disable-default-apps')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-translate')
        
        # User-Agent и языки
        user_agent = random.choice(self.user_agents)
        options.add_argument(f'--user-agent={user_agent}')
        options.add_argument('--accept-lang=en-US,en;q=0.9')
        
        # Графические настройки
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-webgl')
        options.add_argument('--disable-canvas-aa')
        options.add_argument('--disable-2d-canvas-clip-aa')
        
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        
        driver = uc.Chrome(options=options)
        
        # Удаление WebDriver признаков
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": user_agent,
            "platform": "Win32",
            "userAgentMetadata": {
                "brands": [
                    {"brand": "Not A;Brand", "version": "99"},
                    {"brand": "Chromium", "version": "120"},
                    {"brand": "Google Chrome", "version": "120"}
                ],
                "fullVersion": "120.0.0.0",
                "platform": "Windows",
                "platformVersion": "10.0.0",
                "architecture": "x86",
                "model": ""
            }
        })
        
        # Скрипты для скрытия автоматизации
        stealth_scripts = [
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
            "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})",
            "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})",
            "Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8})",
            "Object.defineProperty(navigator, 'deviceMemory', {get: () => 8})",
            "Object.defineProperty(screen, 'width', {get: () => 1920})",
            "Object.defineProperty(screen, 'height', {get: () => 1080})",
            "window.chrome = {runtime: {}}",
            "const originalQuery = window.navigator.permissions.query; window.navigator.permissions.query = (parameters) => (parameters.name === 'notifications' ? Promise.resolve({state: Notification.permission}) : originalQuery(parameters))"
        ]
        
        for script in stealth_scripts:
            try:
                driver.execute_script(script)
            except:
                pass
        
        print("[BYPASS] ✅ Скрытый браузер создан")
        return driver
    
    def check_profile_multiple_endpoints(self, username: str) -> Optional[bool]:
        """Проверка через множественные API endpoints"""
        print(f"[BYPASS] 🔍 Проверка @{username} через API endpoints...")
        
        endpoints = [
            # Public JSON endpoints
            f'https://www.instagram.com/api/v1/users/web_profile_info/?username={username}',
            f'https://i.instagram.com/api/v1/users/web_profile_info/?username={username}',
            f'https://www.instagram.com/{username}/?__a=1&__d=dis',
            f'https://www.instagram.com/{username}/channel/?__a=1',
            
            # GraphQL endpoints
            f'https://www.instagram.com/graphql/query/?query_hash=profile_info&username={username}',
            f'https://www.instagram.com/graphql/query/?query_hash=user_info&username={username}',
            
            # Mobile API endpoints
            f'https://i.instagram.com/api/v1/users/{username}/usernameinfo/',
            f'https://i.instagram.com/api/v1/users/{username}/info/',
        ]
        
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'X-Requested-With': 'XMLHttpRequest',
            'X-IG-App-ID': '936619743392459',
            'X-ASBD-ID': '198387',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Referer': f'https://www.instagram.com/{username}/',
        }
        
        for i, endpoint in enumerate(endpoints):
            try:
                print(f"[BYPASS] 🔗 Endpoint {i+1}/{len(endpoints)}: {endpoint[:50]}...")
                response = requests.get(endpoint, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    # Различные проверки существования пользователя
                    if any(key in str(data) for key in ['user', 'data', 'graphql', 'id', 'username']):
                        print(f"[BYPASS] ✅ Найден через endpoint {i+1}")
                        return True
                elif response.status_code == 404:
                    print(f"[BYPASS] ❌ Не найден через endpoint {i+1}")
                    return False
                    
            except Exception as e:
                print(f"[BYPASS] ⚠️ Ошибка endpoint {i+1}: {e}")
                continue
        
        print(f"[BYPASS] ⚠️ Все endpoints недоступны")
        return None
    
    def check_mobile_endpoints(self, username: str) -> Optional[bool]:
        """Проверка через мобильные API endpoints"""
        print(f"[BYPASS] 📱 Проверка @{username} через мобильные endpoints...")
        
        mobile_endpoints = [
            f'https://i.instagram.com/api/v1/users/web_profile_info/?username={username}',
            f'https://i.instagram.com/api/v1/users/{username}/usernameinfo/',
            f'https://i.instagram.com/api/v1/users/search/?q={username}',
        ]
        
        for i, endpoint in enumerate(mobile_endpoints):
            try:
                print(f"[BYPASS] 📱 Mobile endpoint {i+1}/{len(mobile_endpoints)}")
                response = requests.get(endpoint, headers=self.mobile_headers, timeout=10)
                
                if response.status_code == 200:
                    print(f"[BYPASS] ✅ Найден через мобильный endpoint {i+1}")
                    return True
                elif response.status_code == 404:
                    print(f"[BYPASS] ❌ Не найден через мобильный endpoint {i+1}")
                    return False
                    
            except Exception as e:
                print(f"[BYPASS] ⚠️ Ошибка мобильного endpoint {i+1}: {e}")
                continue
        
        print(f"[BYPASS] ⚠️ Все мобильные endpoints недоступны")
        return None
    
    def quick_instagram_check(self, username: str) -> Optional[bool]:
        """Быстрая проверка с обходом 403 (мобильные заголовки + отключение редиректов)"""
        print(f"[BYPASS] ⚡ Быстрая проверка @{username} (мобильные заголовки)...")
        
        try:
            # Используем мобильный User-Agent и отключаем редиректы
            headers = random.choice(self.mobile_headers_list)
            
            # Пробуем разные endpoints
            endpoints = [
                f'https://www.instagram.com/{username}/?__a=1&__d=dis',
                f'https://i.instagram.com/api/v1/users/web_profile_info/?username={username}',
                f'https://www.instagram.com/{username}/',
            ]
            
            for i, endpoint in enumerate(endpoints):
                try:
                    print(f"[BYPASS] ⚡ Endpoint {i+1}/{len(endpoints)}: {endpoint[:50]}...")
                    response = requests.get(endpoint, headers=headers, timeout=10, allow_redirects=False)
                    
                    print(f"[BYPASS] Status Code: {response.status_code}")
                    
                    if response.status_code == 200:
                        print(f"[BYPASS] ✅ Найден через быстрый метод")
                        return True
                    elif response.status_code == 404:
                        print(f"[BYPASS] ❌ Не найден (404)")
                        return False
                    elif response.status_code == 302:
                        location = response.headers.get('Location', '')
                        print(f"[BYPASS] Redirect to: {location}")
                        if 'login' not in location:
                            print(f"[BYPASS] ✅ Найден (редирект не на логин)")
                            return True
                        
                except Exception as e:
                    print(f"[BYPASS] ⚠️ Ошибка endpoint {i+1}: {e}")
                    continue
                    
        except Exception as e:
            print(f"[BYPASS] ⚠️ Общая ошибка быстрой проверки: {e}")
        
        return None
    
    def check_public_sources(self, username: str) -> Optional[bool]:
        """Проверка через альтернативные публичные источники (Google Cache, Archive.org)"""
        print(f"[BYPASS] 🌐 Проверка @{username} через публичные источники...")
        
        # Google кэш
        try:
            print(f"[BYPASS] 🔍 Проверка Google Cache...")
            google_cache_url = f'https://webcache.googleusercontent.com/search?q=cache:https://www.instagram.com/{username}/'
            headers = {'User-Agent': random.choice(self.user_agents)}
            response = requests.get(google_cache_url, headers=headers, timeout=10)
            
            if response.status_code == 200 and username in response.text:
                print(f"[BYPASS] ✅ Найден в Google Cache")
                return True
        except Exception as e:
            print(f"[BYPASS] ⚠️ Ошибка Google Cache: {e}")
        
        # Archive.org
        try:
            print(f"[BYPASS] 📚 Проверка Archive.org...")
            archive_url = f'https://web.archive.org/web/20230000000000*/https://www.instagram.com/{username}/'
            headers = {'User-Agent': random.choice(self.user_agents)}
            response = requests.get(archive_url, headers=headers, timeout=10)
            
            if response.status_code == 200 and 'available' in response.text.lower():
                print(f"[BYPASS] ✅ Найден в Archive.org")
                return True
        except Exception as e:
            print(f"[BYPASS] ⚠️ Ошибка Archive.org: {e}")
        
        # Поиск через Google
        try:
            print(f"[BYPASS] 🔍 Проверка Google Search...")
            google_search_url = f'https://www.google.com/search?q=site:instagram.com+{username}'
            headers = {'User-Agent': random.choice(self.user_agents)}
            response = requests.get(google_search_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Ищем ссылки на Instagram в результатах поиска
                instagram_links = soup.find_all('a', href=True)
                for link in instagram_links:
                    if f'instagram.com/{username}' in link.get('href', ''):
                        print(f"[BYPASS] ✅ Найден через Google Search")
                        return True
        except Exception as e:
            print(f"[BYPASS] ⚠️ Ошибка Google Search: {e}")
        
        print(f"[BYPASS] ⚠️ Не найден в публичных источниках")
        return None
    
    def create_mobile_emulated_driver(self) -> uc.Chrome:
        """Создание драйвера с эмуляцией мобильного устройства"""
        print("[BYPASS] 📱 Создание мобильного эмулированного драйвера...")
        
        mobile_emulation = {
            "deviceMetrics": {"width": 375, "height": 812, "pixelRatio": 3.0},
            "userAgent": random.choice(self.mobile_user_agents)
        }
        
        options = uc.ChromeOptions()
        options.add_experimental_option("mobileEmulation", mobile_emulation)
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        driver = uc.Chrome(options=options, version_main=None)
        
        # Скрытие признаков автоматизации
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("[BYPASS] ✅ Мобильный драйвер создан")
        return driver
    
    def check_with_mobile_emulation(self, username: str) -> Optional[bool]:
        """Проверка с эмуляцией мобильного устройства"""
        print(f"[BYPASS] 📱 Проверка @{username} с мобильной эмуляцией...")
        
        driver = self.create_mobile_emulated_driver()
        
        try:
            # Сначала заходим на главную страницу
            driver.get('https://www.instagram.com/')
            time.sleep(random.uniform(3, 6))
            
            # Эмулируем поведение мобильного пользователя
            driver.execute_script("window.scrollTo(0, 300)")
            time.sleep(1)
            
            # Теперь проверяем целевой профиль
            driver.get(f'https://www.instagram.com/{username}/')
            time.sleep(random.uniform(4, 7))
            
            current_url = driver.current_url
            page_source = driver.page_source
            
            # Проверяем различные сценарии
            if 'accounts/login' in current_url:
                print("[BYPASS] 🔄 Перенаправление на логин - профиль вероятно существует")
                return True
            elif username in current_url:
                if "Sorry, this page isn't available" in page_source or 'Not Found' in page_source:
                    print(f"[BYPASS] ❌ Профиль не найден")
                    return False
                else:
                    print(f"[BYPASS] ✅ Профиль найден")
                    return True
            else:
                # Проверяем элементы страницы
                if username.lower() in page_source.lower():
                    print(f"[BYPASS] ✅ Профиль найден в исходном коде")
                    return True
                else:
                    print(f"[BYPASS] ❌ Профиль не найден")
                    return False
                
        except Exception as e:
            print(f"[BYPASS] ❌ Ошибка при проверке: {e}")
            return None
        finally:
            driver.quit()
    
    def setup_instagram_session(self, driver):
        """Подготовка сессии для обхода защиты"""
        print("[BYPASS] 🌐 Подготовка Instagram сессии...")
        
        # Шаг 1: Посещение главной страницы
        driver.get('https://www.instagram.com/')
        time.sleep(random.uniform(3, 7))
        
        # Шаг 2: Эмуляция человеческого поведения
        self.human_like_behavior(driver)
        
        # Шаг 3: Принятие куки (если требуется)
        try:
            cookie_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Allow')]") + \
                           driver.find_elements(By.XPATH, "//button[contains(text(), 'Accept')]") + \
                           driver.find_elements(By.XPATH, "//button[contains(text(), 'Разрешить')]")
            if cookie_buttons:
                cookie_buttons[0].click()
                print("[BYPASS] 🍪 Приняты cookies")
                time.sleep(2)
        except:
            pass
        
        # Шаг 4: Дополнительные действия для имитации реального пользователя
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0)")
        time.sleep(1)
        
        print("[BYPASS] ✅ Сессия подготовлена")
    
    def human_like_behavior(self, driver):
        """Эмуляция человеческого поведения"""
        print("[BYPASS] 🧑 Эмуляция человеческого поведения...")
        
        # Случайные движения мыши
        for _ in range(random.randint(2, 5)):
            x = random.randint(100, 500)
            y = random.randint(100, 500)
            driver.execute_script(f"window.scrollTo({x}, {y})")
            time.sleep(random.uniform(0.5, 1.5))
        
        # Случайные клики
        try:
            body = driver.find_element(By.TAG_NAME, 'body')
            for _ in range(random.randint(1, 3)):
                body.click()
                time.sleep(random.uniform(0.3, 0.8))
        except:
            pass
        
        # Ввод случайных клавиш
        try:
            body = driver.find_element(By.TAG_NAME, 'body')
            body.send_keys(Keys.SPACE)
            time.sleep(0.5)
            body.send_keys(Keys.ESCAPE)
        except:
            pass
    
    def check_profile_stealth(self, driver, username: str) -> Optional[bool]:
        """Скрытая проверка профиля через браузер"""
        print(f"[BYPASS] 🕵️ Скрытая проверка @{username}...")
        
        # Подготовка сессии
        self.setup_instagram_session(driver)
        time.sleep(random.uniform(5, 10))
        
        # Использование косвенных URL
        indirect_urls = [
            f'https://www.instagram.com/explore/people/?search={username}',
            f'https://www.instagram.com/web/search/topsearch/?query={username}',
            f'https://www.instagram.com/{username}/followers/',
            f'https://www.instagram.com/{username}/following/',
            f'https://www.instagram.com/{username}/',
        ]
        
        for i, url in enumerate(indirect_urls):
            try:
                print(f"[BYPASS] 🔗 Косвенный URL {i+1}/{len(indirect_urls)}: {url[:50]}...")
                driver.get(url)
                time.sleep(random.uniform(4, 8))
                
                # Проверка на редирект
                if 'accounts/login' not in driver.current_url:
                    page_source = driver.page_source
                    
                    # Множественные проверки существования
                    checks = [
                        username.lower() in page_source.lower(),
                        f'"{username}"' in page_source,
                        f"@{username}" in page_source,
                        any(indicator in page_source for indicator in ['profile_pic_url', 'biography', 'followed_by', 'user'])
                    ]
                    
                    if any(checks):
                        print(f"[BYPASS] ✅ Найден через косвенный URL {i+1}")
                        return True
                    elif any(indicator in page_source for indicator in ['error', '404', 'not found', 'Страница не найдена']):
                        print(f"[BYPASS] ❌ Не найден через косвенный URL {i+1}")
                        return False
                else:
                    print(f"[BYPASS] ⚠️ Редирект на логин через URL {i+1}")
                    
            except Exception as e:
                print(f"[BYPASS] ⚠️ Ошибка косвенного URL {i+1}: {e}")
                continue
        
        print(f"[BYPASS] ⚠️ Все косвенные URL недоступны")
        return None
    
    def ultimate_profile_check(self, username: str, max_retries: int = 3, screenshot_path: Optional[str] = None) -> Optional[bool]:
        """Ультимативный метод проверки с множеством подходов (403 Bypass)"""
        print(f"[BYPASS] 🚀 Ультимативная проверка @{username} (макс. {max_retries} попыток)")
        print(f"[BYPASS] 🎯 Включены все методы обхода 403 ошибок")
        
        for attempt in range(max_retries):
            print(f"\n[BYPASS] 🔄 Попытка {attempt + 1}/{max_retries}")
            
            # Метод 1: Быстрая проверка с мобильными заголовками (НОВЫЙ)
            print("[BYPASS] ⚡ Метод 1: Быстрая проверка (мобильные headers + no redirects)")
            result = self.quick_instagram_check(username)
            if result is not None:
                print(f"[BYPASS] ✅ Результат через быструю проверку: {result}")
                return result
            
            # Метод 2: Прямые API запросы
            print("[BYPASS] 📡 Метод 2: API endpoints")
            result = self.check_profile_multiple_endpoints(username)
            if result is not None:
                print(f"[BYPASS] ✅ Результат через API: {result}")
                return result
            
            # Метод 3: Мобильные endpoints
            print("[BYPASS] 📱 Метод 3: Мобильные endpoints")
            result = self.check_mobile_endpoints(username)
            if result is not None:
                print(f"[BYPASS] ✅ Результат через мобильные API: {result}")
                return result
            
            # Метод 4: Публичные источники (НОВЫЙ)
            print("[BYPASS] 🌐 Метод 4: Публичные источники (Google Cache, Archive.org)")
            result = self.check_public_sources(username)
            if result is not None:
                print(f"[BYPASS] ✅ Результат через публичные источники: {result}")
                return result
            
            # Метод 5: Мобильная эмуляция (НОВЫЙ) - используем только на последней попытке
            if attempt == max_retries - 1:
                print("[BYPASS] 📱 Метод 5: Мобильная эмуляция (Chrome Mobile)")
                result = self.check_with_mobile_emulation(username)
                if result is not None:
                    print(f"[BYPASS] ✅ Результат через мобильную эмуляцию: {result}")
                    return result
            
            # Метод 6: Продвинутая мобильная эмуляция (самый надежный)
            if attempt == max_retries - 1:
                print("[BYPASS] 📱 Метод 6: Продвинутая мобильная эмуляция")
                try:
                    from .instagram_mobile_bypass import check_account_with_mobile_bypass
                    
                    # Мобильная эмуляция - синхронный вызов
                    import asyncio
                    result = asyncio.run(check_account_with_mobile_bypass(
                        username=username,
                        screenshot_path=screenshot_path,
                        headless=True,
                        max_retries=1
                    ))
                    
                    if result.get("exists") is not None:
                        print(f"[BYPASS] ✅ Результат через мобильную эмуляцию: {result.get('exists')}")
                        return result.get("exists")
                    else:
                        print(f"[BYPASS] ⚠️ Мобильная эмуляция не дала результата")
                        return None
                        
                except Exception as e:
                    print(f"[BYPASS] ❌ Ошибка мобильной эмуляции: {e}")
                    return None
            
            # Задержка между попытками
            if attempt < max_retries - 1:
                delay = random.uniform(5, 15)
                print(f"[BYPASS] ⏳ Ожидание {delay:.1f}с перед следующей попыткой...")
                time.sleep(delay)
        
        print(f"[BYPASS] ❌ Все методы исчерпаны для @{username}")
        return None


# Функция для интеграции с существующей системой
async def check_account_with_bypass(
    username: str,
    screenshot_path: Optional[str] = None,
    headless: bool = True,
    max_retries: int = 2
) -> Dict[str, Any]:
    """
    Проверка аккаунта с использованием всех методов обхода защиты Instagram (403 Bypass)
    
    Включает следующие методы:
    1. Быстрая проверка с мобильными заголовками (no redirects)
    2. API endpoints (множественные)
    3. Мобильные API endpoints (Instagram App)
    4. Публичные источники (Google Cache, Archive.org)
    5. Мобильная эмуляция (Chrome Mobile Emulation)
    6. Полная скрытая проверка через браузер
    
    Args:
        username: Instagram username
        screenshot_path: Путь для сохранения скриншота (optional)
        headless: Запуск в headless режиме (default: True)
        max_retries: Максимальное количество попыток (default: 2)
        
    Returns:
        dict с результатами проверки:
            - username: str
            - exists: bool | None
            - is_private: None
            - full_name: None
            - followers: None
            - following: None
            - posts: None
            - error: str | None
            - checked_via: str
            - screenshot_path: None
            - bypass_methods_used: list
    """
    print(f"[BYPASS] 🚀 Запуск полной проверки @{username} с обходом 403 ошибок")
    print(f"[BYPASS] 🎯 Максимум попыток: {max_retries}")
    
    bypass = InstagramBypass()
    
    # Ультимативная проверка со всеми методами обхода
    result = bypass.ultimate_profile_check(username, max_retries=max_retries, screenshot_path=screenshot_path)
    
    methods_used = [
        "quick_mobile_check",      # Быстрая проверка
        "api_endpoints",           # API endpoints
        "mobile_endpoints",        # Мобильные endpoints
        "public_sources",          # Публичные источники
        "mobile_emulation",        # Мобильная эмуляция
        "stealth_browser"          # Скрытый браузер
    ]
    
    # Если bypass методы не создали скриншот, но аккаунт найден, создаем его
    final_screenshot_path = screenshot_path
    if result is True and screenshot_path:
        # Проверяем, создался ли скриншот
        if not os.path.exists(screenshot_path):
            print(f"[BYPASS] 📸 Screenshot not created by bypass methods - creating now...")
            try:
                # Создаем скриншот через undetected chrome без прокси
                from .undetected_checker import check_account_undetected_chrome
                
                screenshot_result = await check_account_undetected_chrome(
                    username=username,
                    proxy=None,  # Без прокси для обхода 403
                    screenshot_path=screenshot_path,
                    headless=headless
                )
                
                if screenshot_result.get("screenshot_path"):
                    final_screenshot_path = screenshot_result["screenshot_path"]
                    print(f"[BYPASS] 📸 Screenshot created via undetected chrome: {screenshot_result['screenshot_path']}")
                else:
                    print(f"[BYPASS] ⚠️ Failed to create screenshot via undetected chrome")
                    final_screenshot_path = None
                    
            except Exception as screenshot_error:
                print(f"[BYPASS] ⚠️ Failed to create screenshot: {screenshot_error}")
                final_screenshot_path = None
    
    response = {
        "username": username,
        "exists": result,
        "is_private": None,
        "full_name": None,
        "followers": None,
        "following": None,
        "posts": None,
        "error": None if result is not None else "Все методы обхода 403 не сработали",
        "checked_via": "bypass_403_all_methods",
        "screenshot_path": final_screenshot_path if final_screenshot_path and os.path.exists(final_screenshot_path) else None,
        "bypass_methods_used": methods_used
    }
    
    if result is True:
        print(f"[BYPASS] ✅ Профиль @{username} НАЙДЕН через систему обхода 403")
    elif result is False:
        print(f"[BYPASS] ❌ Профиль @{username} НЕ НАЙДЕН")
    else:
        print(f"[BYPASS] ⚠️ Не удалось определить статус @{username}")
    
    return response


# Быстрая тестовая функция для отладки
async def quick_test_bypass(username: str) -> None:
    """
    Быстрый тест системы обхода для одного username
    
    Args:
        username: Instagram username для тестирования
    """
    print(f"\n{'='*60}")
    print(f"[TEST] 🧪 Тестирование обхода 403 для @{username}")
    print(f"{'='*60}\n")
    
    result = await check_account_with_bypass(username, max_retries=1)
    
    print(f"\n{'='*60}")
    print(f"[TEST] 📊 РЕЗУЛЬТАТЫ ТЕСТА")
    print(f"{'='*60}")
    print(f"Username: {result['username']}")
    print(f"Exists: {result['exists']}")
    print(f"Error: {result['error']}")
    print(f"Checked via: {result['checked_via']}")
    print(f"Methods used: {', '.join(result['bypass_methods_used'])}")
    print(f"{'='*60}\n")
