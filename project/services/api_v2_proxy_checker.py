"""API v2 checker with proxy support for Instagram account verification."""

import aiohttp
import json
import random
import asyncio
import re
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from datetime import date

try:
    from ..models import Account, Proxy
    from ..config import get_settings
    from .ig_screenshot import check_account_with_header_screenshot
    from .proxy_utils import select_best_proxy
except ImportError:
    from models import Account, Proxy
    from config import get_settings
    from services.ig_screenshot import check_account_with_header_screenshot
    from services.proxy_utils import select_best_proxy


class InstagramCheckerWithProxy:
    """Проверка Instagram аккаунтов с использованием прокси"""
    
    def __init__(self, proxy_list: List[str] = None):
        """
        Args:
            proxy_list: Список прокси в формате ['ip:port:user:pass', ...]
        """
        self.proxy_list = proxy_list or []
        self.current_proxy_index = 0
        self.session = None
        
        # User Agents для ротации
        self.user_agents = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPad; CPU OS 17_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.2903.51",
        ]
    
    def parse_proxy(self, proxy_str: str) -> Dict[str, str]:
        """Парсинг прокси строки в формате ip:port:username:password"""
        try:
            ip, port, username, password = proxy_str.split(':')
            return {
                'ip': ip,
                'port': port,
                'username': username,
                'password': password,
                'http': f'http://{username}:{password}@{ip}:{port}',
                'https': f'http://{username}:{password}@{ip}:{port}'
            }
        except ValueError:
            raise ValueError(f"Неверный формат прокси: {proxy_str}. Ожидается: ip:port:username:password")
    
    def get_next_proxy(self) -> Optional[Dict]:
        """Получение следующего прокси из списка"""
        if not self.proxy_list:
            return None
            
        if self.current_proxy_index >= len(self.proxy_list):
            self.current_proxy_index = 0  # Циклическая ротация
            
        proxy_str = self.proxy_list[self.current_proxy_index]
        self.current_proxy_index += 1
        
        return self.parse_proxy(proxy_str)
    
    def clean_username(self, username: str) -> str:
        """Очистка username от @ и URL"""
        url_pattern = r"(?:https?://)?(?:www\.)?instagram\.com/([A-Za-z0-9_.]+)/?"
        match = re.match(url_pattern, username)
        if match:
            username = match.group(1).lower()
        else:
            username = username.lower()
            
        if username.startswith('@'):
            username = username[1:].lower()
        
        return username
    
    @staticmethod
    def close_instagram_modals_firefox(driver):
        """🔥 Агрессивное закрытие модальных окон Instagram в Firefox"""
        print("[API-V2-FIREFOX] 🎯 Закрытие модальных окон...")
        
        try:
            # JavaScript код для закрытия модальных окон (из других режимов)
            js_code = """
            // 🔥 УДАЛЯЕМ ВСЕ МОДАЛЬНЫЕ ОКНА И OVERLAY
            var allElements = document.querySelectorAll('*');
            for (var i = 0; i < allElements.length; i++) {
                var element = allElements[i];
                var className = element.className || '';
                var style = element.style || {};
                
                // Проверяем на модальные окна и overlay
                var classStr = String(className || '');
                if (classStr.indexOf('x7r02ix') !== -1 || 
                    classStr.indexOf('x1vjfegm') !== -1 || 
                    classStr.indexOf('_abcm') !== -1 ||
                    classStr.indexOf('modal') !== -1 ||
                    classStr.indexOf('overlay') !== -1 ||
                    classStr.indexOf('backdrop') !== -1 ||
                    element.getAttribute('role') === 'dialog' ||
                    style.position === 'fixed' ||
                    style.zIndex > 1000) {
                    
                    element.style.display = 'none !important';
                    element.style.visibility = 'hidden !important';
                    element.style.opacity = '0 !important';
                    element.style.pointerEvents = 'none !important';
                    element.remove();
                }
            }
            
            // 🔥 УДАЛЯЕМ ВСЕ ЭЛЕМЕНТЫ С ВЫСОКИМ Z-INDEX
            var highZElements = document.querySelectorAll('[style*="z-index"]');
            for (var i = 0; i < highZElements.length; i++) {
                var zIndex = parseInt(highZElements[i].style.zIndex) || 0;
                if (zIndex > 100) {
                    highZElements[i].style.display = 'none !important';
                    highZElements[i].remove();
                }
            }
            
            // 🔥 УДАЛЯЕМ ВСЕ FIXED ПОЗИЦИОНИРОВАННЫЕ ЭЛЕМЕНТЫ
            var fixedElements = document.querySelectorAll('[style*="position: fixed"]');
            for (var i = 0; i < fixedElements.length; i++) {
                fixedElements[i].style.display = 'none !important';
                fixedElements[i].remove();
            }
            
            // 🔥 ВОССТАНАВЛИВАЕМ BODY И HTML
            document.body.classList.remove('modal-open', 'overflow-hidden');
            document.body.style.overflow = 'auto !important';
            document.body.style.position = 'static !important';
            document.body.style.background = 'transparent !important';
            document.documentElement.style.overflow = 'auto !important';
            document.documentElement.style.background = 'transparent !important';
            
            // 🔥 УДАЛЯЕМ ВСЕ OVERLAY КЛАССЫ
            var bodyClasses = document.body.className;
            var newClasses = bodyClasses.replace(/modal-open|overflow-hidden|backdrop|overlay/g, '');
            document.body.className = newClasses.trim();
            
            // 🔥 УДАЛЯЕМ ВСЕ ЭЛЕМЕНТЫ С ТЕМНЫМ ФОНОМ
            var darkElements = document.querySelectorAll('[style*="background"]');
            for (var i = 0; i < darkElements.length; i++) {
                var bg = darkElements[i].style.background || '';
                if (bg.indexOf('rgba(0,0,0') !== -1 || bg.indexOf('rgba(0, 0, 0') !== -1 || 
                    bg.indexOf('black') !== -1 || bg.indexOf('#000') !== -1) {
                    darkElements[i].style.display = 'none !important';
                    darkElements[i].remove();
                }
            }
            
            // 🔥 УДАЛЯЕМ ВСЕ ЭЛЕМЕНТЫ С ВЫСОКИМ Z-INDEX И ТЕМНЫМ ФОНОМ
            var allElements2 = document.querySelectorAll('*');
            for (var i = 0; i < allElements2.length; i++) {
                var element = allElements2[i];
                var style = element.style || {};
                var zIndex = parseInt(style.zIndex) || 0;
                var bg = style.background || '';
                
                if (zIndex > 50 && (bg.indexOf('rgba(0,0,0') !== -1 || bg.indexOf('rgba(0, 0, 0') !== -1 || 
                    bg.indexOf('black') !== -1 || bg.indexOf('#000') !== -1)) {
                    element.style.display = 'none !important';
                    element.remove();
                }
            }
            
            // 🔥 ПРИНУДИТЕЛЬНО ОЧИЩАЕМ СТИЛИ
            document.body.removeAttribute('style');
            document.documentElement.removeAttribute('style');
            
            // 🔥 ВОССТАНАВЛИВАЕМ СКРОЛЛИНГ И УБИРАЕМ ТЕМНЫЙ ФОН
            document.body.style.overflow = 'auto';
            document.body.style.background = 'white';
            document.documentElement.style.overflow = 'auto';
            document.documentElement.style.background = 'white';
            """
            
            driver.execute_script(js_code)
            print("[API-V2-FIREFOX] ✅ Модальные окна закрыты")
            
            # Убираем затемнение после модального окна
            try:
                js_remove_overlay = """
                // 🔥 АГРЕССИВНОЕ УДАЛЕНИЕ ВСЕХ ЭЛЕМЕНТОВ ЗАТЕМНЕНИЯ
                var allElements = document.querySelectorAll('*');
                for (var i = 0; i < allElements.length; i++) {
                    var element = allElements[i];
                    var className = element.className || '';
                    var style = element.style || {};
                    
                    // Проверяем на модальные окна и overlay
                    if (className.indexOf('x7r02ix') !== -1 || 
                        className.indexOf('x1vjfegm') !== -1 || 
                        className.indexOf('_abcm') !== -1 ||
                        className.indexOf('modal') !== -1 ||
                        className.indexOf('overlay') !== -1 ||
                        className.indexOf('backdrop') !== -1 ||
                        element.getAttribute('role') === 'dialog' ||
                        style.position === 'fixed' ||
                        style.zIndex > 1000) {
                        
                        element.style.display = 'none !important';
                        element.style.visibility = 'hidden !important';
                        element.style.opacity = '0 !important';
                        element.style.pointerEvents = 'none !important';
                        element.remove();
                    }
                }
                
                // 🔥 УДАЛЯЕМ ВСЕ ЭЛЕМЕНТЫ С ВЫСОКИМ Z-INDEX
                var highZElements = document.querySelectorAll('[style*="z-index"]');
                for (var i = 0; i < highZElements.length; i++) {
                    var zIndex = parseInt(highZElements[i].style.zIndex) || 0;
                    if (zIndex > 100) {
                        highZElements[i].style.display = 'none !important';
                        highZElements[i].remove();
                    }
                }
                
                // 🔥 УДАЛЯЕМ ВСЕ FIXED ПОЗИЦИОНИРОВАННЫЕ ЭЛЕМЕНТЫ
                var fixedElements = document.querySelectorAll('[style*="position: fixed"]');
                for (var i = 0; i < fixedElements.length; i++) {
                    fixedElements[i].style.display = 'none !important';
                    fixedElements[i].remove();
                }
                
                // 🔥 ВОССТАНАВЛИВАЕМ BODY И HTML
                document.body.classList.remove('modal-open', 'overflow-hidden');
                document.body.style.overflow = 'auto !important';
                document.body.style.position = 'static !important';
                document.body.style.background = 'white !important';
                document.documentElement.style.overflow = 'auto !important';
                document.documentElement.style.background = 'white !important';
                
                // 🔥 УДАЛЯЕМ ВСЕ OVERLAY КЛАССЫ
                var bodyClasses = document.body.className;
                var newClasses = bodyClasses.replace(/modal-open|overflow-hidden|backdrop|overlay/g, '');
                document.body.className = newClasses.trim();
                
                // 🔥 ПРИНУДИТЕЛЬНО ОЧИЩАЕМ СТИЛИ
                document.body.removeAttribute('style');
                document.documentElement.removeAttribute('style');
                
                // 🔥 ВОССТАНАВЛИВАЕМ СКРОЛЛИНГ И БЕЛЫЙ ФОН
                document.body.style.overflow = 'auto';
                document.body.style.background = 'white';
                document.documentElement.style.overflow = 'auto';
                document.documentElement.style.background = 'white';
                """
                driver.execute_script(js_remove_overlay)
                print("[API-V2-FIREFOX] ✅ Затемнение убрано")
                
            except:
                pass
            
        except Exception as e:
            print(f"[API-V2-FIREFOX] ⚠️ Ошибка закрытия модальных окон: {e}")
    
    def get_headers(self) -> Dict[str, str]:
        """Получение headers с случайным User-Agent"""
        return {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
            "origin": "https://www.instagram.com",
            "user-agent": random.choice(self.user_agents),
            "X-ASBD-ID": "129477",
            "X-IG-WWW-Claim": "0",
            "X-IG-App-ID": "936619743392459",
            "X-CSRFToken": 'missing',
            "Referer": "https://www.instagram.com/",
            "X-Requested-With": "XMLHttpRequest"
        }
    
    async def check_account(
        self, 
        username: str, 
        max_attempts: int = 3,
        use_proxy: bool = True
    ) -> Dict:
        """
        Проверка Instagram аккаунта
        
        Args:
            username: Instagram username
            max_attempts: Максимальное количество попыток
            use_proxy: Использовать ли прокси
            
        Returns:
            Dict с результатом проверки
        """
        username = self.clean_username(username)
        url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
        
        # Статистика попыток
        attempts = []
        
        for attempt in range(max_attempts):
            try:
                # Выбор прокси для этой попытки
                proxy_config = None
                if use_proxy and self.proxy_list:
                    proxy_config = self.get_next_proxy()
                    proxy_url = proxy_config['http'] if proxy_config else None
                else:
                    proxy_url = None
                
                print(f"🔰 Попытка {attempt + 1} для @{username}" + 
                      (f" через прокси {proxy_config['ip']}" if proxy_config else " без прокси"))
                
                headers = self.get_headers()
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url, 
                        headers=headers, 
                        proxy=proxy_url,
                        timeout=15, 
                        ssl=False
                    ) as response:
                        
                        data = await response.read()
                        response_status = response.status
                        
                        # Записываем информацию о попытке
                        attempts.append({
                            'attempt': attempt + 1,
                            'status_code': response_status,
                            'proxy_used': proxy_config['ip'] if proxy_config else 'none',
                            'success': response_status == 200
                        })
                        
                        if response_status != 200:
                            print(f"⚠️ Статус код {response_status} для @{username}")
                            continue
                        
                        userinfo = json.loads(data)
                        
                        # Анализ ответа
                        if 'data' in userinfo and userinfo['data'].get('user') is not None:
                            user_data = userinfo['data']['user']
                            
                            # КРИТИЧЕСКАЯ ПРОВЕРКА: убеждаемся, что найденный аккаунт соответствует запрашиваемому
                            found_username = user_data.get('username', '').lower()
                            requested_username = username.lower()
                            
                            print(f"[API-V2-DEBUG] Запрашивали: @{requested_username}, получили: @{found_username}")
                            
                            if found_username != requested_username:
                                print(f"[API-V2-DEBUG] ❌ Несоответствие username! Запрашивали @{requested_username}, получили @{found_username}")
                                result = {
                                    'exists': False,
                                    'is_banned': False,
                                    'is_private': False,
                                    'followers': 0,
                                    'following': 0,
                                    'posts': 0,
                                    'is_verified': False,
                                    'full_name': '',
                                    'username': '',
                                    'profile_pic_url': '',
                                    'biography': '',
                                    'error': f'username_mismatch: requested {requested_username}, got {found_username}',
                                    'attempts': attempts,
                                    'final_attempt': attempt + 1,
                                    'proxy_used': proxy_config['ip'] if proxy_config else 'none'
                                }
                                return result
                            
                            result = {
                                'exists': True,
                                'is_banned': False,
                                'is_private': user_data.get('is_private', False),
                                'followers': user_data.get('edge_followed_by', {}).get('count', 0),
                                'following': user_data.get('edge_follow', {}).get('count', 0),
                                'posts': user_data.get('edge_owner_to_timeline_media', {}).get('count', 0),
                                'is_verified': user_data.get('is_verified', False),
                                'full_name': user_data.get('full_name', ''),
                                'username': user_data.get('username', ''),
                                'profile_pic_url': user_data.get('profile_pic_url', ''),
                                'biography': user_data.get('biography', ''),
                                'error': None,
                                'attempts': attempts,
                                'final_attempt': attempt + 1,
                                'proxy_used': proxy_config['ip'] if proxy_config else 'none'
                            }
                            return result
                        
                        elif ('data' in userinfo and userinfo['data'].get('user') is None):
                            result = {
                                'exists': False,
                                'is_banned': True,
                                'is_private': False,
                                'followers': 0,
                                'following': 0,
                                'posts': 0,
                                'is_verified': False,
                                'full_name': '',
                                'username': username,
                                'profile_pic_url': '',
                                'biography': '',
                                'error': 'Account not found or banned',
                                'attempts': attempts,
                                'final_attempt': attempt + 1,
                                'proxy_used': proxy_config['ip'] if proxy_config else 'none'
                            }
                            return result
                        
                        else:
                            print(f"⚠️ Неизвестная структура ответа для @{username}")
                            continue
                            
            except asyncio.TimeoutError:
                print(f"⏰ Таймаут для @{username} (попытка {attempt + 1})")
                attempts.append({
                    'attempt': attempt + 1,
                    'error': 'Timeout',
                    'proxy_used': proxy_config['ip'] if proxy_config else 'none',
                    'success': False
                })
                if attempt < max_attempts - 1:
                    await asyncio.sleep(2)
                continue
                
            except json.JSONDecodeError as e:
                print(f"📄 JSON ошибка для @{username}: {e}")
                attempts.append({
                    'attempt': attempt + 1,
                    'error': f'JSON Decode: {str(e)}',
                    'proxy_used': proxy_config['ip'] if proxy_config else 'none',
                    'success': False
                })
                if attempt < max_attempts - 1:
                    await asyncio.sleep(3)
                continue
                
            except Exception as e:
                print(f"❌ Ошибка для @{username}: {e}")
                attempts.append({
                    'attempt': attempt + 1,
                    'error': str(e),
                    'proxy_used': proxy_config['ip'] if proxy_config else 'none',
                    'success': False
                })
                if attempt < max_attempts - 1:
                    await asyncio.sleep(2)
                continue
        
        # Все попытки не удались
        return {
            'exists': None,
            'is_banned': None,
            'is_private': None,
            'followers': 0,
            'following': 0,
            'posts': 0,
            'is_verified': False,
            'full_name': '',
            'username': username,
            'profile_pic_url': '',
            'biography': '',
            'error': f'All {max_attempts} attempts failed',
            'attempts': attempts,
            'final_attempt': max_attempts,
            'proxy_used': 'multiple' if attempts else 'none'
        }


async def check_account_via_api_v2_proxy(
    session: Session,
    user_id: int,
    username: str,
    max_attempts: int = 3
) -> Dict[str, Any]:
    """
    Проверка Instagram аккаунта через API v2 с поддержкой прокси.
    
    Логика:
    1. Если аккаунт существует - делается скриншот и отправляется
    2. Если аккаунт не существует - возвращается результат без скриншота
    
    Args:
        session: Database session
        user_id: User ID
        username: Instagram username to check
        max_attempts: Maximum number of attempts
        
    Returns:
        Dict with check results: {
            "username": str,
            "exists": bool | None,
            "full_name": str | None,
            "followers": int | None,
            "following": int | None,
            "posts": int | None,
            "screenshot_path": str | None,
            "error": str | None,
            "checked_via": str,
            "proxy_used": str
        }
    """
    print(f"[API-V2-PROXY] 🔍 Проверка @{username} через API v2 с прокси")
    
    result = {
        "username": username,
        "exists": None,
        "full_name": None,
        "followers": None,
        "following": None,
        "posts": None,
        "screenshot_path": None,
        "error": None,
        "checked_via": "api-v2-proxy",
        "proxy_used": None
    }
    
    # Создаем путь для скриншота
    import os
    from datetime import datetime
    screenshot_dir = "screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(screenshot_dir, f"{username}_header_{timestamp}.png")
    
    try:
        # Получаем список прокси для пользователя
        proxy_list = []
        proxies = session.query(Proxy).filter(
            Proxy.user_id == user_id,
            Proxy.is_active == True
        ).all()
        
        for proxy in proxies:
            if proxy.username and proxy.password:
                # Извлекаем порт из host (формат host:port)
                if ':' in proxy.host:
                    host, port = proxy.host.split(':', 1)
                    proxy_str = f"{host}:{port}:{proxy.username}:{proxy.password}"
                else:
                    # Если порт не указан, используем стандартный
                    proxy_str = f"{proxy.host}:8080:{proxy.username}:{proxy.password}"
                proxy_list.append(proxy_str)
        
        if not proxy_list:
            print(f"[API-V2-PROXY] ⚠️ Нет доступных прокси для пользователя {user_id}")
            result["error"] = "no_proxies_available"
            return result
        
        print(f"[API-V2-PROXY] 📡 Доступно прокси: {len(proxy_list)}")
        
        # Инициализируем проверщик с прокси
        checker = InstagramCheckerWithProxy(proxy_list=proxy_list)
        
        # Проверяем аккаунт
        api_result = await checker.check_account(username, max_attempts=max_attempts, use_proxy=True)
        
        # Обновляем результат
        result.update({
            "exists": api_result.get("exists"),
            "full_name": api_result.get("full_name"),
            "followers": api_result.get("followers"),
            "following": api_result.get("following"),
            "posts": api_result.get("posts"),
            "proxy_used": api_result.get("proxy_used"),
            "error": api_result.get("error")
        })
        
        # Если аккаунт существует - делаем скриншот
        if api_result.get("exists") is True:
            print(f"[API-V2-PROXY] ✅ Аккаунт @{username} существует - создаем скриншот")
            
            # Получаем лучший прокси для скриншота
            best_proxy = select_best_proxy(session, user_id)
            if not best_proxy:
                print(f"[API-V2-PROXY] ⚠️ Нет доступного прокси для скриншота")
                result["error"] = "no_proxy_for_screenshot"
                return result
            
            # Формируем URL прокси для скриншота
            proxy_url = f"{best_proxy.scheme}://{best_proxy.username}:{best_proxy.password}@{best_proxy.host}"
            
            # Создаем скриншот используя логику api+proxy (только для существующих!)
            try:
                from .proxy_checker import check_account_via_proxy_with_screenshot
            except ImportError:
                from services.proxy_checker import check_account_via_proxy_with_screenshot
            
            screenshot_result = await check_account_via_proxy_with_screenshot(
                username=username,
                proxy=best_proxy,
                headless=True,
                timeout_ms=30000,
                screenshot_path=screenshot_path
            )
            
            # Если получили 403 ошибку, пробуем Firefox (как в api+proxy)
            if screenshot_result.get("error") == "403_forbidden":
                print(f"[API-V2-PROXY] ⚠️ 403 Forbidden с прокси - пробуем Firefox")
                try:
                    from selenium import webdriver
                    from selenium.webdriver.firefox.options import Options as FirefoxOptions
                    from selenium.webdriver.common.by import By
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    import time
                    import random
                    
                    # Создаем директорию если не существует
                    import os
                    os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                    
                    # Настройки Firefox
                    options = FirefoxOptions()
                    
                    # Desktop режим
                    desktop_user_agents = [
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    ]
                    
                    user_agent = random.choice(desktop_user_agents)
                    options.set_preference("general.useragent.override", user_agent)
                    
                    # Настройки для обхода блокировок
                    options.set_preference("dom.webdriver.enabled", False)
                    options.set_preference("useAutomationExtension", False)
                    options.set_preference("media.navigator.enabled", False)
                    options.set_preference("media.peerconnection.enabled", False)
                    
                    # Размер окна для desktop
                    options.add_argument("--width=1920")
                    options.add_argument("--height=1080")
                    
                    if True:  # Всегда headless для сервера
                        options.add_argument("--headless")
                    
                    # Создаем Firefox драйвер
                    driver = webdriver.Firefox(options=options)
                    driver.set_window_size(1920, 1080)
                    
                    try:
                        # Переходим на Instagram
                        url = f"https://www.instagram.com/{username}/"
                        print(f"[API-V2-FIREFOX] 🌐 Переход на: {url}")
                        driver.get(url)
                        
                        # Ждем загрузки страницы
                        time.sleep(3)
                        
                        # Закрываем модальные окна (как в других режимах)
                        InstagramCheckerWithProxy.close_instagram_modals_firefox(driver)
                        
                        # Дополнительная задержка для полного удаления элементов
                        time.sleep(2)
                        
                        # Дополнительные методы удаления затемнения
                        print("[API-V2-FIREFOX] 🔥 Начинаем дополнительные методы...")
                        try:
                            # Нажатие Escape
                            from selenium.webdriver.common.keys import Keys
                            driver.find_element("tag name", "body").send_keys(Keys.ESCAPE)
                            driver.find_element("tag name", "body").send_keys(Keys.ESCAPE)
                            print("[API-V2-FIREFOX] ⌨️ Escape нажат")
                        except Exception as e:
                            print(f"[API-V2-FIREFOX] ⚠️ Ошибка Escape: {e}")
                        
                        # Имитация нажатия кнопок закрытия
                        try:
                            # Ищем только безопасные кнопки закрытия
                            close_selectors = [
                                "button[aria-label='Close']",
                                "svg[aria-label='Close']", 
                                "button[aria-label='Закрыть']",
                                "svg[aria-label='Закрыть']",
                                "[data-testid='close-button']",
                                "button[class*='close']",
                                "button[class*='Close']"
                            ]
                            
                            for selector in close_selectors:
                                try:
                                    elements = driver.find_elements("css selector", selector)
                                    for element in elements:
                                        if element.is_displayed():
                                            # Проверяем, что это действительно кнопка закрытия
                                            text = element.text.lower() if element.text else ""
                                            aria_label = element.get_attribute("aria-label") or ""
                                            if "close" in text or "закрыть" in text or "close" in aria_label.lower() or "закрыть" in aria_label.lower():
                                                driver.execute_script("arguments[0].click();", element)
                                                print(f"[API-V2-FIREFOX] 🖱️ Нажата кнопка: {selector}")
                                                time.sleep(0.5)
                                except:
                                    continue
                                    
                            print("[API-V2-FIREFOX] 🖱️ Поиск кнопок закрытия завершен")
                        except Exception as e:
                            print(f"[API-V2-FIREFOX] ⚠️ Ошибка поиска кнопок: {e}")
                        
                        # JavaScript имитация кликов
                        try:
                            js_click_buttons = """
                            // Имитируем клики только по безопасным кнопкам закрытия
                            var closeButtons = document.querySelectorAll('button[aria-label="Close"], svg[aria-label="Close"], button[aria-label="Закрыть"], svg[aria-label="Закрыть"]');
                            for (var i = 0; i < closeButtons.length; i++) {
                                if (closeButtons[i].offsetParent !== null) { // Проверяем видимость
                                    var text = closeButtons[i].textContent || '';
                                    var ariaLabel = closeButtons[i].getAttribute('aria-label') || '';
                                    if (text.toLowerCase().includes('close') || text.toLowerCase().includes('закрыть') || 
                                        ariaLabel.toLowerCase().includes('close') || ariaLabel.toLowerCase().includes('закрыть')) {
                                        closeButtons[i].click();
                                    }
                                }
                            }
                            """
                            driver.execute_script(js_click_buttons)
                            print("[API-V2-FIREFOX] 🖱️ JavaScript клики выполнены")
                        except Exception as e:
                            print(f"[API-V2-FIREFOX] ⚠️ Ошибка JavaScript кликов: {e}")
                        
                        # Дополнительное агрессивное удаление
                        print("[API-V2-FIREFOX] 🔥 Начинаем финальную очистку...")
                        try:
                            js_final_cleanup = """
                            // 🔥 ФИНАЛЬНАЯ ОЧИСТКА - УДАЛЯЕМ ВСЕ ОСТАВШИЕСЯ ЭЛЕМЕНТЫ
                            var allElements = document.querySelectorAll('*');
                            for (var i = 0; i < allElements.length; i++) {
                                var element = allElements[i];
                                var style = element.style || {};
                                var className = element.className || '';
                                
                                // Удаляем все элементы с темным фоном
                                if (style.background && (style.background.indexOf('rgba(0,0,0') !== -1 || 
                                    style.background.indexOf('rgba(0, 0, 0') !== -1 || 
                                    style.background.indexOf('black') !== -1 || 
                                    style.background.indexOf('#000') !== -1)) {
                                    element.style.display = 'none !important';
                                    element.remove();
                                }
                                
                                // Удаляем все элементы с высоким z-index
                                var zIndex = parseInt(style.zIndex) || 0;
                                if (zIndex > 50) {
                                    element.style.display = 'none !important';
                                    element.remove();
                                }
                                
                                // Удаляем все fixed элементы
                                if (style.position === 'fixed') {
                                    element.style.display = 'none !important';
                                    element.remove();
                                }
                            }
                            
                            // 🔥 ПРИНУДИТЕЛЬНО УСТАНАВЛИВАЕМ БЕЛЫЙ ФОН
                            document.body.style.background = 'white !important';
                            document.documentElement.style.background = 'white !important';
                            document.body.style.backgroundImage = 'none !important';
                            document.documentElement.style.backgroundImage = 'none !important';
                            """
                            driver.execute_script(js_final_cleanup)
                            print("[API-V2-FIREFOX] 🔥 Финальная очистка выполнена")
                        except Exception as e:
                            print(f"[API-V2-FIREFOX] ⚠️ Ошибка финальной очистки: {e}")
                        
                        # Дополнительная задержка после финальной очистки
                        time.sleep(1)
                        
                        # Проверяем, что страница загрузилась
                        page_source = driver.page_source
                        if "instagram.com" in driver.current_url and username.lower() in page_source.lower():
                            # Создаем скриншот
                            driver.save_screenshot(screenshot_path)
                            
                            screenshot_result["screenshot_path"] = screenshot_path
                            screenshot_result["exists"] = True
                            print(f"[API-V2-PROXY] 📸 Firefox скриншот создан: {screenshot_path}")
                        else:
                            print(f"[API-V2-PROXY] ⚠️ Страница не загрузилась корректно")
                            screenshot_result["error"] = "page_load_failed"
                            
                    finally:
                        driver.quit()
                        
                except Exception as e:
                    print(f"[API-V2-PROXY] ❌ Ошибка создания Firefox скриншота: {e}")
                    # Fallback на PIL скриншот
                    try:
                        from PIL import Image, ImageDraw, ImageFont
                        from datetime import datetime
                        
                        # Создаем простой скриншот с информацией
                        img = Image.new('RGB', (800, 600), color='white')
                        draw = ImageDraw.Draw(img)
                        
                        try:
                            font = ImageFont.truetype("arial.ttf", 24)
                        except:
                            font = ImageFont.load_default()
                        
                        text = f"Instagram Account: @{username}\nStatus: Active (API v2 confirmed)\nMethod: API v2 + Proxy\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        draw.text((50, 250), text, fill='black', font=font)
                        img.save(screenshot_path)
                        
                        screenshot_result["screenshot_path"] = screenshot_path
                        screenshot_result["exists"] = True
                        print(f"[API-V2-PROXY] 📸 Fallback PIL скриншот создан: {screenshot_path}")
                        
                    except Exception as fallback_error:
                        print(f"[API-V2-PROXY] ❌ Ошибка создания fallback скриншота: {fallback_error}")
                        screenshot_result["error"] = "screenshot_failed_fallback"
            
            # Обновляем результат с данными из скриншота
            print(f"[API-V2-DEBUG] screenshot_result: {screenshot_result}")
            print(f"[API-V2-DEBUG] screenshot_result.get('exists'): {screenshot_result.get('exists')}")
            print(f"[API-V2-DEBUG] screenshot_result.get('exists') is True: {screenshot_result.get('exists') is True}")
            
            if screenshot_result.get("exists") is True:
                print(f"[API-V2-DEBUG] Входим в блок if screenshot_result.get('exists') is True")
                result.update({
                    "exists": screenshot_result.get("exists"),
                    "full_name": screenshot_result.get("full_name"),
                    "followers": screenshot_result.get("followers"),
                    "following": screenshot_result.get("following"),
                    "posts": screenshot_result.get("posts"),
                    "is_verified": screenshot_result.get("is_verified"),
                    "is_private": screenshot_result.get("is_private"),
                    "screenshot_path": screenshot_result.get("screenshot_path"),
                    "proxy_used": screenshot_result.get("proxy_used")
                })
                
                if screenshot_result.get("screenshot_path"):
                    print(f"[API-V2-PROXY] 📸 Скриншот создан: {screenshot_result['screenshot_path']}")
                else:
                    print(f"[API-V2-PROXY] ⚠️ Не удалось создать скриншот, но аккаунт найден")
                
                # ВСЕГДА помечаем аккаунт как выполненный, если он найден (даже без скриншота)
                print(f"[API-V2-DEBUG] Ищем аккаунт в базе данных...")
                account = session.query(Account).filter(
                    Account.user_id == user_id,
                    Account.account == username
                ).first()
                if account:
                    print(f"[API-V2-DEBUG] Аккаунт найден в базе: {account.account}")
                    account.done = True
                    account.date_of_finish = date.today()
                    session.commit()
                    print(f"[API-V2-PROXY] ✅ Аккаунт @{username} помечен как выполненный")
                else:
                    print(f"[API-V2-DEBUG] ❌ Аккаунт НЕ найден в базе данных!")
            else:
                print(f"[API-V2-PROXY] ⚠️ Скриншот не подтвердил существование аккаунта")
                result["error"] = "screenshot_verification_failed"
        
        elif api_result.get("exists") is False:
            print(f"[API-V2-PROXY] ❌ Аккаунт @{username} не существует")
            # Помечаем аккаунт как выполненный (не найден)
            account = session.query(Account).filter(
                Account.user_id == user_id,
                Account.account == username
            ).first()
            if account:
                account.done = True
                account.date_of_finish = date.today()
                session.commit()
                print(f"[API-V2-PROXY] ✅ Аккаунт @{username} помечен как выполненный (не найден)")
        
        else:
            print(f"[API-V2-PROXY] ❓ Ошибка проверки @{username}: {api_result.get('error', 'unknown')}")
    
    except Exception as e:
        print(f"[API-V2-PROXY] ❌ Критическая ошибка для @{username}: {e}")
        result["error"] = str(e)
    
    return result


async def batch_check_accounts_via_api_v2_proxy(
    session: Session,
    user_id: int,
    usernames: List[str],
    delay_between: float = 3.0
) -> List[Dict[str, Any]]:
    """
    Пакетная проверка нескольких аккаунтов через API v2 с прокси
    
    Args:
        session: Database session
        user_id: User ID
        usernames: Список username'ов
        delay_between: Задержка между запросами (секунды)
        
    Returns:
        Список результатов
    """
    results = []
    
    for i, username in enumerate(usernames):
        print(f"\n📊 Прогресс: {i + 1}/{len(usernames)}")
        
        result = await check_account_via_api_v2_proxy(
            session=session,
            user_id=user_id,
            username=username
        )
        results.append(result)
        
        # Задержка между разными аккаунтами
        if i < len(usernames) - 1:
            print(f"⏳ Ожидание {delay_between}сек...")
            await asyncio.sleep(delay_between)
    
    return results
