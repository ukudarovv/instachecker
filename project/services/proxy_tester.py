"""Proxy testing service with Instagram account check and screenshot."""

import asyncio
import aiohttp
from typing import Optional, Tuple, Dict
from datetime import datetime
import os

try:
    from ..models import Proxy, Account
    from ..utils.encryptor import OptionalFernet
    from ..config import get_settings
    from .simple_monitor_checker import check_account_simple
except ImportError:
    from models import Proxy, Account
    from utils.encryptor import OptionalFernet
    from config import get_settings
    from services.simple_monitor_checker import check_account_simple


def build_proxy_url(proxy: Proxy) -> str:
    """
    Build proxy URL from Proxy object.
    
    Args:
        proxy: Proxy object
        
    Returns:
        Proxy URL string
    """
    if proxy.username and proxy.password:
        try:
            settings = get_settings()
            encryptor = OptionalFernet(settings.encryption_key)
            password = encryptor.decrypt(proxy.password)
            return f"{proxy.scheme}://{proxy.username}:{password}@{proxy.host}"
        except:
            return f"{proxy.scheme}://{proxy.host}"
    else:
        return f"{proxy.scheme}://{proxy.host}"


async def test_proxy_basic(proxy: Proxy) -> Tuple[bool, str, Optional[float]]:
    """
    Basic proxy connectivity test.
    
    Args:
        proxy: Proxy object
        
    Returns:
        Tuple of (success, message, response_time)
    """
    proxy_url = build_proxy_url(proxy)
    
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            start_time = asyncio.get_event_loop().time()
            
            async with session.get(
                "http://httpbin.org/ip",
                proxy=proxy_url,
                ssl=False
            ) as resp:
                response_time = asyncio.get_event_loop().time() - start_time
                
                if resp.status == 200:
                    data = await resp.json()
                    ip = data.get('origin', 'Unknown')
                    return True, f"✅ Работает\n🌐 IP: {ip}", response_time
                elif resp.status == 407:
                    return False, "❌ Ошибка авторизации (407)", response_time
                else:
                    return False, f"❌ HTTP {resp.status}", response_time
                    
    except asyncio.TimeoutError:
        return False, "⏱️ Timeout - не отвечает", None
    except Exception as e:
        error_msg = str(e)
        if "407" in error_msg:
            return False, "❌ Неверный логин/пароль", None
        elif "Connection refused" in error_msg:
            return False, "❌ Соединение отклонено", None
        else:
            return False, f"❌ Ошибка: {error_msg[:50]}", None


async def test_proxy_with_instagram(
    proxy: Proxy,
    test_username: str = "instagram"
) -> Tuple[bool, str, Optional[Dict]]:
    """
    Test proxy with Instagram account check.
    
    Args:
        proxy: Proxy object
        test_username: Instagram username to check
        
    Returns:
        Tuple of (success, message, user_data)
    """
    proxy_url = build_proxy_url(proxy)
    
    try:
        # Check Instagram account through proxy
        is_active, status_text, user_data = await check_account_simple(
            username=test_username,
            proxy=proxy_url,
            timeout=20,
            retry_count=2
        )
        
        if is_active and user_data:
            followers = user_data.get('edge_followed_by', {}).get('count', 0)
            is_verified = user_data.get('is_verified', False)
            
            message = (
                f"✅ <b>Прокси работает с Instagram!</b>\n\n"
                f"Тестовый аккаунт: @{test_username}\n"
                f"👥 Подписчиков: {followers:,}\n"
                f"{'✓ Verified' if is_verified else ''}\n\n"
                f"{status_text}"
            )
            
            return True, message, user_data
        else:
            return False, f"❌ Не удалось проверить аккаунт\n{status_text}", None
            
    except Exception as e:
        return False, f"❌ Ошибка: {str(e)[:100]}", None


async def test_proxy_with_screenshot(
    proxy: Proxy,
    test_username: str = "instagram",
    bot_token: str = None
) -> Tuple[bool, str, Optional[str]]:
    """
    Test proxy with Instagram check and generated profile image (NO BROWSER).
    
    Args:
        proxy: Proxy object
        test_username: Instagram username to check
        bot_token: Telegram bot token (for sending screenshots)
        
    Returns:
        Tuple of (success, message, screenshot_path)
    """
    proxy_url = build_proxy_url(proxy)
    
    try:
        # Import API checker and profile generator
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        from test_api_with_profile_gen import generate_instagram_profile_image_improved
        import aiohttp
        
        # Get Instagram API data via proxy WITH TRAFFIC MONITORING
        url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={test_username}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "*/*",
            "X-IG-App-ID": "936619743392459",
        }
        
        # Traffic monitoring
        traffic_sent = 0
        traffic_received = 0
        
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            async with session.get(url, proxy=proxy_url) as resp:
                if resp.status != 200:
                    return False, f"❌ API ошибка: HTTP {resp.status}", None
                
                # Calculate traffic
                content = await resp.read()
                traffic_received = len(content)
                
                # Estimate sent traffic (headers + request line)
                request_line = f"GET {url} HTTP/1.1\r\n"
                headers_str = "\r\n".join([f"{k}: {v}" for k, v in headers.items()])
                traffic_sent = len(request_line.encode()) + len(headers_str.encode()) + len(url.encode())
                
                # Parse JSON
                import json
                data = json.loads(content)
                user = data.get("data", {}).get("user", {})
                
                if not user:
                    return False, f"❌ Аккаунт @{test_username} не найден", None
        
        # Generate profile image
        screenshots_dir = "screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(screenshots_dir, f"{test_username}_{timestamp}.png")
        
        result = await generate_instagram_profile_image_improved(
            username=user.get("username", test_username),
            full_name=user.get("full_name", ""),
            posts=(user.get("edge_owner_to_timeline_media") or {}).get("count", 0),
            followers=(user.get("edge_followed_by") or {}).get("count", 0),
            following=(user.get("edge_follow") or {}).get("count", 0),
            is_private=user.get("is_private", False),
            is_verified=user.get("is_verified", False),
            biography=user.get("biography", ""),
            profile_pic_url=user.get("profile_pic_url_hd") or user.get("profile_pic_url") or "",
            output_path=screenshot_path
        )
        
        success = result.get('success', False)
        
        if success and result.get('image_path') and os.path.exists(result['image_path']):
            file_size = os.path.getsize(result['image_path']) / 1024
            screenshot_path = result['image_path']
            
            # Calculate total traffic
            total_traffic_kb = (traffic_sent + traffic_received) / 1024
            
            message = (
                f"✅ <b>Прокси работает отлично!</b>\n\n"
                f"🎨 Шапка профиля @{test_username} сгенерирована\n"
                f"📁 Размер файла: {file_size:.1f} KB\n"
                f"🌐 Прокси: {proxy.scheme}://{proxy.host}\n"
                f"⚡ Статус: Активен\n"
                f"🚀 Без браузера (API + генерация)\n\n"
                f"📊 <b>Трафик:</b>\n"
                f"   ⬆️ Отправлено: {traffic_sent / 1024:.2f} KB\n"
                f"   ⬇️ Получено: {traffic_received / 1024:.2f} KB\n"
                f"   📈 Всего: {total_traffic_kb:.2f} KB"
            )
            
            if result.get('error'):
                message += f"\n⚠️ Предупреждение: {result['error']}"
            
            return True, message, screenshot_path
        else:
            error_msg = result.get('error', 'Неизвестная ошибка')
            return False, f"❌ Прокси не работает: {error_msg}", None
            
    except Exception as e:
        return False, f"❌ Ошибка тестирования: {str(e)[:100]}", None


async def test_multiple_proxies(
    proxies: list,
    test_username: str = "instagram",
    with_screenshot: bool = False
) -> Dict[int, Dict]:
    """
    Test multiple proxies.
    
    Args:
        proxies: List of Proxy objects
        test_username: Instagram username to test
        with_screenshot: Include screenshot test
        
    Returns:
        Dict mapping proxy.id to test results
    """
    results = {}
    
    for proxy in proxies:
        if with_screenshot:
            success, message, screenshot = await test_proxy_with_screenshot(
                proxy,
                test_username
            )
            results[proxy.id] = {
                'success': success,
                'message': message,
                'screenshot': screenshot,
                'proxy_url': build_proxy_url(proxy)
            }
        else:
            success, message, user_data = await test_proxy_with_instagram(
                proxy,
                test_username
            )
            results[proxy.id] = {
                'success': success,
                'message': message,
                'user_data': user_data,
                'proxy_url': build_proxy_url(proxy)
            }
        
        # Small delay between tests
        await asyncio.sleep(2)
    
    return results


def format_batch_test_results(results: Dict[int, Dict], proxies: list) -> str:
    """
    Format batch test results.
    
    Args:
        results: Test results dict
        proxies: List of tested proxies
        
    Returns:
        Formatted results string
    """
    success_count = sum(1 for r in results.values() if r['success'])
    fail_count = len(results) - success_count
    
    message_parts = [
        f"📊 <b>Результаты тестирования прокси:</b>\n",
        f"✅ Работают: {success_count}/{len(results)}",
        f"❌ Не работают: {fail_count}/{len(results)}\n"
    ]
    
    # Working proxies
    if success_count > 0:
        message_parts.append("✅ <b>Рабочие:</b>")
        for proxy in proxies:
            if results.get(proxy.id, {}).get('success'):
                message_parts.append(f"  • {proxy.scheme}://{proxy.host[:30]}")
    
    # Failed proxies
    if fail_count > 0:
        message_parts.append("\n❌ <b>Не работают:</b>")
        for proxy in proxies:
            if not results.get(proxy.id, {}).get('success'):
                message_parts.append(f"  • {proxy.scheme}://{proxy.host[:30]}")
    
    return "\n".join(message_parts)

