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
    Test proxy with Instagram check and screenshot.
    
    Args:
        proxy: Proxy object
        test_username: Instagram username to check
        bot_token: Telegram bot token (for sending screenshots)
        
    Returns:
        Tuple of (success, message, screenshot_path)
    """
    proxy_url = build_proxy_url(proxy)
    
    try:
        # Import universal checker
        try:
            from ..services.universal_playwright_checker import check_instagram_account_universal
        except ImportError:
            from services.universal_playwright_checker import check_instagram_account_universal
        
        # Generate screenshot path
        screenshots_dir = "screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(screenshots_dir, f"{test_username}_{timestamp}.png")
        
        # Test with header screenshot (same as ptest_screenshot mode)
        try:
            from .ig_screenshot import check_account_with_header_screenshot
        except ImportError:
            from ig_screenshot import check_account_with_header_screenshot
        
        result = await check_account_with_header_screenshot(
            username=test_username,
            proxy_url=proxy_url,
            screenshot_path=screenshot_path,
            headless=True,
            timeout_ms=60000,
            dark_theme=True,
            mobile_emulation=False,  # Desktop режим (как в ptest_screenshot)
            crop_ratio=0
        )
        
        success = result.get('exists', False)
        
        if success and result.get('screenshot_path') and os.path.exists(result['screenshot_path']):
            file_size = os.path.getsize(result['screenshot_path']) / 1024
            
            message = (
                f"✅ <b>Прокси работает отлично!</b>\n\n"
                f"📸 Скриншот профиля @{test_username}\n"
                f"📁 Размер файла: {file_size:.1f} KB\n"
                f"🌐 Прокси: {proxy.scheme}://{proxy.host}\n"
                f"⚡ Статус: Активен"
            )
            
            if result.get('error'):
                message += f"\n⚠️ Предупреждение: {result['error']}"
            
            return True, message, result['screenshot_path']
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

