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
                from .proxy_checker import check_account_via_proxy_with_fallback
            except ImportError:
                from services.proxy_checker import check_account_via_proxy_with_fallback
            
            screenshot_result = await check_account_via_proxy_with_fallback(
                session=session,
                user_id=user_id,
                username=username,
                max_attempts=3,
                headless=True,
                timeout_ms=30000,
                screenshot_path=screenshot_path
            )
            
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
