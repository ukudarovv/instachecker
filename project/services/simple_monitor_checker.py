"""
Simple Monitor Checker - режим проверки на основе логики из app.py
Простой и эффективный метод мониторинга Instagram аккаунтов.
"""

import aiohttp
import asyncio
import json
import random
from typing import Dict, Optional, Tuple
from datetime import datetime

# User agents из app.py
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPod touch; CPU iPhone 17_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.2903.51",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.7; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Vivaldi/7.0.3495.15"
]


def get_headers() -> Dict[str, str]:
    """
    Получить заголовки для запроса (как в app.py).
    
    Returns:
        dict с заголовками
    """
    return {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
        "origin": "https://www.instagram.com",
        "user-agent": random.choice(USER_AGENTS),
        "X-ASBD-ID": "129477",
        "X-IG-WWW-Claim": "0",
        "X-IG-App-ID": "936619743392459",
        "X-CSRFToken": "missing",
        "Referer": "https://www.instagram.com/",
        "X-Requested-With": "XMLHttpRequest"
    }


async def check_account_simple(
    username: str,
    proxy: Optional[str] = None,
    timeout: int = 15,
    retry_count: int = 3
) -> Tuple[bool, str, Optional[Dict]]:
    """
    Простая проверка аккаунта (логика из app.py).
    
    Args:
        username: Instagram username
        proxy: Прокси URL (format: http://user:pass@host:port)
        timeout: Таймаут в секундах
        retry_count: Количество попыток
        
    Returns:
        Tuple[is_active, status_text, user_data]
        - is_active: True если аккаунт активен, False если забанен
        - status_text: Текстовое описание статуса
        - user_data: Данные пользователя (если есть)
    """
    url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
    
    for attempt in range(retry_count):
        try:
            headers = get_headers()
            
            async with aiohttp.ClientSession() as session:
                kwargs = {
                    'headers': headers,
                    'timeout': aiohttp.ClientTimeout(total=timeout),
                    'ssl': False
                }
                
                if proxy:
                    kwargs['proxy'] = proxy
                
                async with session.get(url, **kwargs) as response:
                    data = await response.read()
                    userinfo = json.loads(data)
                    
                    # Логика проверки из app.py
                    if 'data' in userinfo and userinfo['data'].get('user') is not None:
                        # Аккаунт активен
                        user = userinfo['data']['user']
                        followers = user.get('edge_followed_by', {}).get('count', 0)
                        is_verified = user.get('is_verified', False)
                        is_private = user.get('is_private', False)
                        
                        status_parts = []
                        if is_verified:
                            status_parts.append("✓ Verified")
                        if is_private:
                            status_parts.append("🔒 Private")
                        
                        status_text = f"✅ Active ({followers:,} followers)"
                        if status_parts:
                            status_text += f" [{', '.join(status_parts)}]"
                        
                        return True, status_text, user
                    
                    elif ('data' in userinfo and userinfo['data'].get('user') is None) or \
                         ('status' in userinfo and userinfo['status'] == 'ok'):
                        # Аккаунт забанен или не существует
                        return False, "❌ Banned or Not Found", None
                    
                    else:
                        # Неожиданная структура ответа
                        if attempt < retry_count - 1:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        return False, "⚠️ Unexpected response structure", None
        
        except asyncio.TimeoutError:
            if attempt < retry_count - 1:
                await asyncio.sleep(3)
                continue
            return False, "⏱️ Timeout - proxy too slow or unavailable", None
        
        except json.JSONDecodeError:
            if attempt < retry_count - 1:
                await asyncio.sleep(2)
                continue
            return False, "❌ Invalid JSON response", None
        
        except aiohttp.ClientError as e:
            if "407" in str(e):
                return False, "❌ Proxy authentication failed", None
            if "403" in str(e):
                return False, "🚫 Instagram blocked request (403)", None
            if "429" in str(e):
                return False, "⏸️ Rate limited (429)", None
            
            if attempt < retry_count - 1:
                await asyncio.sleep(3)
                continue
            return False, f"❌ Connection error: {str(e)[:50]}", None
        
        except Exception as e:
            if attempt < retry_count - 1:
                await asyncio.sleep(3)
                continue
            return False, f"❌ Error: {str(e)[:50]}", None
    
    return False, "❌ Max retries reached", None


async def check_account_with_details(
    username: str,
    proxy: Optional[str] = None
) -> Dict[str, any]:
    """
    Проверка аккаунта с детальной информацией.
    
    Args:
        username: Instagram username
        proxy: Прокси URL (optional)
        
    Returns:
        dict с результатами проверки:
        {
            'success': bool,
            'is_active': bool,
            'status': str,
            'username': str,
            'followers': int,
            'is_verified': bool,
            'is_private': bool,
            'full_name': str,
            'biography': str,
            'profile_pic_url': str,
            'error': str (if failed)
        }
    """
    result = {
        'success': False,
        'is_active': False,
        'status': '',
        'username': username,
        'followers': 0,
        'is_verified': False,
        'is_private': False,
        'full_name': None,
        'biography': None,
        'profile_pic_url': None,
        'error': None,
        'checked_at': datetime.now().isoformat()
    }
    
    try:
        is_active, status_text, user_data = await check_account_simple(username, proxy)
        
        result['success'] = True
        result['is_active'] = is_active
        result['status'] = status_text
        
        if user_data:
            result['followers'] = user_data.get('edge_followed_by', {}).get('count', 0)
            result['is_verified'] = user_data.get('is_verified', False)
            result['is_private'] = user_data.get('is_private', False)
            result['full_name'] = user_data.get('full_name')
            result['biography'] = user_data.get('biography')
            result['profile_pic_url'] = user_data.get('profile_pic_url')
        
    except Exception as e:
        result['error'] = str(e)
        result['status'] = f"❌ Exception: {str(e)[:50]}"
    
    return result


async def batch_check_accounts(
    usernames: list,
    proxy: Optional[str] = None,
    concurrent_limit: int = 5
) -> Dict[str, Dict]:
    """
    Проверка нескольких аккаунтов параллельно.
    
    Args:
        usernames: Список username'ов
        proxy: Прокси URL
        concurrent_limit: Лимит параллельных проверок
        
    Returns:
        dict где ключ - username, значение - результат проверки
    """
    results = {}
    semaphore = asyncio.Semaphore(concurrent_limit)
    
    async def check_with_semaphore(username):
        async with semaphore:
            return username, await check_account_with_details(username, proxy)
    
    tasks = [check_with_semaphore(username) for username in usernames]
    completed = await asyncio.gather(*tasks, return_exceptions=True)
    
    for item in completed:
        if isinstance(item, Exception):
            continue
        username, result = item
        results[username] = result
    
    return results


# Для совместимости с существующими сервисами
async def check_instagram_account(username: str, proxy_url: str = None) -> tuple:
    """
    Совместимость с существующим API.
    
    Returns:
        (success: bool, message: str, screenshot_path: str or None)
    """
    is_active, status_text, user_data = await check_account_simple(username, proxy_url)
    
    if is_active:
        return True, status_text, None
    else:
        return False, status_text, None

