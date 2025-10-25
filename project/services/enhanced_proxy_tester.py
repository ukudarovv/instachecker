"""Enhanced proxy testing service with comprehensive testing capabilities."""

import asyncio
import aiohttp
import time
from typing import Optional, Tuple, Dict, List
from datetime import datetime
import os
import json

try:
    from ..models import Proxy, Account
    from ..utils.encryptor import OptionalFernet
    from ..config import get_settings
    from .simple_monitor_checker import check_account_simple
    from .ig_screenshot import check_account_with_header_screenshot
except ImportError:
    from models import Proxy, Account
    from utils.encryptor import OptionalFernet
    from config import get_settings
    from services.simple_monitor_checker import check_account_simple
    from services.ig_screenshot import check_account_with_header_screenshot


def build_proxy_url(proxy: Proxy) -> str:
    """Build proxy URL from Proxy object."""
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


async def test_proxy_connectivity(proxy: Proxy) -> Tuple[bool, str, Optional[float]]:
    """
    Enhanced basic proxy connectivity test with multiple endpoints.
    
    Args:
        proxy: Proxy object
        
    Returns:
        Tuple of (success, message, response_time)
    """
    proxy_url = build_proxy_url(proxy)
    
    # Test endpoints
    test_endpoints = [
        ("http://httpbin.org/ip", "HTTPBin IP"),
        ("https://api.ipify.org?format=json", "IPify API"),
        ("http://ip-api.com/json", "IP-API")
    ]
    
    results = []
    
    for endpoint, name in test_endpoints:
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                start_time = time.time()
                
                async with session.get(
                    endpoint,
                    proxy=proxy_url,
                    ssl=False
                ) as resp:
                    response_time = time.time() - start_time
                    
                    if resp.status == 200:
                        data = await resp.json()
                        ip = data.get('origin') or data.get('ip') or data.get('query', 'Unknown')
                        results.append({
                            'endpoint': name,
                            'success': True,
                            'ip': ip,
                            'response_time': response_time
                        })
                    else:
                        results.append({
                            'endpoint': name,
                            'success': False,
                            'error': f"HTTP {resp.status}",
                            'response_time': response_time
                        })
                        
        except asyncio.TimeoutError:
            results.append({
                'endpoint': name,
                'success': False,
                'error': "Timeout",
                'response_time': None
            })
        except Exception as e:
            results.append({
                'endpoint': name,
                'success': False,
                'error': str(e)[:50],
                'response_time': None
            })
    
    # Analyze results
    successful_tests = [r for r in results if r['success']]
    failed_tests = [r for r in results if not r['success']]
    
    if successful_tests:
        # Get most common IP
        ips = [r['ip'] for r in successful_tests]
        most_common_ip = max(set(ips), key=ips.count)
        
        avg_response_time = sum(r['response_time'] for r in successful_tests if r['response_time']) / len(successful_tests)
        
        message = f"✅ <b>Прокси работает!</b>\n\n"
        message += f"🌐 IP: {most_common_ip}\n"
        message += f"⚡ Время отклика: {avg_response_time:.2f}s\n"
        message += f"✅ Успешных тестов: {len(successful_tests)}/{len(results)}\n"
        
        if failed_tests:
            message += f"\n⚠️ Неудачных: {len(failed_tests)}"
            for test in failed_tests:
                message += f"\n  • {test['endpoint']}: {test['error']}"
        
        return True, message, avg_response_time
    else:
        error_messages = [f"{r['endpoint']}: {r['error']}" for r in failed_tests]
        return False, f"❌ Все тесты не прошли:\n" + "\n".join(error_messages), None


async def test_proxy_speed(proxy: Proxy) -> Tuple[bool, str, Dict]:
    """
    Test proxy speed with multiple requests.
    
    Args:
        proxy: Proxy object
        
    Returns:
        Tuple of (success, message, speed_data)
    """
    proxy_url = build_proxy_url(proxy)
    
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        
        # Test with multiple requests
        test_urls = [
            "http://httpbin.org/ip",
            "http://httpbin.org/user-agent",
            "http://httpbin.org/headers"
        ]
        
        response_times = []
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for i, url in enumerate(test_urls):
                try:
                    start_time = time.time()
                    async with session.get(url, proxy=proxy_url, ssl=False) as resp:
                        response_time = time.time() - start_time
                        if resp.status == 200:
                            response_times.append(response_time)
                except Exception as e:
                    print(f"[PROXY-SPEED] Request {i+1} failed: {e}")
        
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            
            # Speed rating
            if avg_time < 2:
                speed_rating = "🚀 Очень быстро"
            elif avg_time < 5:
                speed_rating = "⚡ Быстро"
            elif avg_time < 10:
                speed_rating = "🐌 Средне"
            else:
                speed_rating = "🐢 Медленно"
            
            message = f"📊 <b>Тест скорости прокси</b>\n\n"
            message += f"{speed_rating}\n"
            message += f"⚡ Среднее время: {avg_time:.2f}s\n"
            message += f"🏃 Минимум: {min_time:.2f}s\n"
            message += f"🚶 Максимум: {max_time:.2f}s\n"
            message += f"📈 Успешных запросов: {len(response_times)}/{len(test_urls)}"
            
            speed_data = {
                'avg_time': avg_time,
                'min_time': min_time,
                'max_time': max_time,
                'successful_requests': len(response_times),
                'total_requests': len(test_urls)
            }
            
            return True, message, speed_data
        else:
            return False, "❌ Не удалось выполнить ни одного запроса", {}
            
    except Exception as e:
        return False, f"❌ Ошибка теста скорости: {str(e)[:100]}", {}


async def test_proxy_instagram_access(proxy: Proxy, test_username: str = "instagram") -> Tuple[bool, str, Optional[Dict]]:
    """
    Test proxy with Instagram access and account data.
    
    Args:
        proxy: Proxy object
        test_username: Instagram username to test
        
    Returns:
        Tuple of (success, message, profile_data)
    """
    proxy_url = build_proxy_url(proxy)
    
    try:
        # Test Instagram access
        is_active, status_text, user_data = await check_account_simple(
            username=test_username,
            proxy=proxy_url,
            timeout=30,
            retry_count=2
        )
        
        if is_active and user_data:
            followers = user_data.get('edge_followed_by', {}).get('count', 0)
            following = user_data.get('edge_follow', {}).get('count', 0)
            posts = user_data.get('edge_owner_to_timeline_media', {}).get('count', 0)
            is_verified = user_data.get('is_verified', False)
            is_private = user_data.get('is_private', False)
            
            message = f"✅ <b>Instagram доступен!</b>\n\n"
            message += f"👤 Тестовый аккаунт: @{test_username}\n"
            message += f"👥 Подписчиков: {followers:,}\n"
            message += f"👤 Подписок: {following:,}\n"
            message += f"📸 Публикаций: {posts:,}\n"
            
            if is_verified:
                message += "✓ Verified\n"
            if is_private:
                message += "🔒 Приватный\n"
            
            message += f"\n{status_text}"
            
            return True, message, user_data
        else:
            return False, f"❌ Не удалось получить данные Instagram\n{status_text}", None
            
    except Exception as e:
        return False, f"❌ Ошибка доступа к Instagram: {str(e)[:100]}", None


async def test_proxy_screenshot(proxy: Proxy, test_username: str = "instagram") -> Tuple[bool, str, Optional[str]]:
    """
    Test proxy with Instagram screenshot.
    
    Args:
        proxy: Proxy object
        test_username: Instagram username to test
        
    Returns:
        Tuple of (success, message, screenshot_path)
    """
    proxy_url = build_proxy_url(proxy)
    
    try:
        # Generate screenshot path
        screenshots_dir = "screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(screenshots_dir, f"proxy_test_{test_username}_{timestamp}.png")
        
        # Test with screenshot
        result = await check_account_with_header_screenshot(
            username=test_username,
            proxy_url=proxy_url,
            screenshot_path=screenshot_path,
            headless=True,
            timeout_ms=60000,
            dark_theme=True,
            mobile_emulation=False,
            crop_ratio=0
        )
        
        if result.get('exists') and result.get('screenshot_path') and os.path.exists(result['screenshot_path']):
            file_size = os.path.getsize(result['screenshot_path']) / 1024
            
            message = f"📸 <b>Скриншот создан!</b>\n\n"
            message += f"👤 Профиль: @{test_username}\n"
            message += f"📁 Размер файла: {file_size:.1f} KB\n"
            message += f"✅ Прокси работает с Instagram\n"
            
            if result.get('error'):
                message += f"\n⚠️ Предупреждение: {result['error']}"
            
            return True, message, result['screenshot_path']
        else:
            error_msg = result.get('error', 'Неизвестная ошибка')
            return False, f"❌ Не удалось создать скриншот\n{error_msg}", None
            
    except Exception as e:
        return False, f"❌ Ошибка создания скриншота: {str(e)[:100]}", None


async def test_proxy_comprehensive(proxy: Proxy, test_username: str = "instagram") -> Dict:
    """
    Comprehensive proxy test with all available tests.
    
    Args:
        proxy: Proxy object
        test_username: Instagram username to test
        
    Returns:
        Dictionary with all test results
    """
    print(f"[ENHANCED-PROXY-TEST] 🧪 Начинаем комплексное тестирование прокси {proxy.host}")
    
    results = {
        'proxy_id': proxy.id,
        'proxy_host': proxy.host,
        'test_username': test_username,
        'timestamp': datetime.now().isoformat(),
        'tests': {}
    }
    
    # Test 1: Basic connectivity
    print(f"[ENHANCED-PROXY-TEST] 🔗 Тест 1: Базовая связность...")
    connectivity_success, connectivity_msg, response_time = await test_proxy_connectivity(proxy)
    results['tests']['connectivity'] = {
        'success': connectivity_success,
        'message': connectivity_msg,
        'response_time': response_time
    }
    
    # Test 2: Speed test
    print(f"[ENHANCED-PROXY-TEST] ⚡ Тест 2: Скорость...")
    speed_success, speed_msg, speed_data = await test_proxy_speed(proxy)
    results['tests']['speed'] = {
        'success': speed_success,
        'message': speed_msg,
        'data': speed_data
    }
    
    # Test 3: Instagram access
    print(f"[ENHANCED-PROXY-TEST] 📱 Тест 3: Доступ к Instagram...")
    instagram_success, instagram_msg, profile_data = await test_proxy_instagram_access(proxy, test_username)
    results['tests']['instagram'] = {
        'success': instagram_success,
        'message': instagram_msg,
        'profile_data': profile_data
    }
    
    # Test 4: Screenshot test
    print(f"[ENHANCED-PROXY-TEST] 📸 Тест 4: Скриншот...")
    screenshot_success, screenshot_msg, screenshot_path = await test_proxy_screenshot(proxy, test_username)
    results['tests']['screenshot'] = {
        'success': screenshot_success,
        'message': screenshot_msg,
        'screenshot_path': screenshot_path
    }
    
    # Calculate overall score
    total_tests = 4
    successful_tests = sum(1 for test in results['tests'].values() if test['success'])
    overall_score = (successful_tests / total_tests) * 100
    
    results['overall_score'] = overall_score
    results['successful_tests'] = successful_tests
    results['total_tests'] = total_tests
    
    print(f"[ENHANCED-PROXY-TEST] 📊 Результат: {successful_tests}/{total_tests} тестов пройдено ({overall_score:.1f}%)")
    
    return results


def format_comprehensive_results(results: Dict) -> str:
    """
    Format comprehensive test results for display.
    
    Args:
        results: Test results dictionary
        
    Returns:
        Formatted message string
    """
    proxy_host = results['proxy_host']
    overall_score = results['overall_score']
    successful_tests = results['successful_tests']
    total_tests = results['total_tests']
    
    message = f"🧪 <b>Комплексное тестирование прокси</b>\n\n"
    message += f"🌐 Прокси: {proxy_host}\n"
    message += f"📊 Общий результат: {successful_tests}/{total_tests} ({overall_score:.1f}%)\n\n"
    
    # Test results
    for test_name, test_result in results['tests'].items():
        status = "✅" if test_result['success'] else "❌"
        test_title = {
            'connectivity': '🔗 Базовая связность',
            'speed': '⚡ Скорость',
            'instagram': '📱 Instagram доступ',
            'screenshot': '📸 Скриншот'
        }.get(test_name, test_name)
        
        message += f"{status} {test_title}\n"
        
        # Add details for successful tests
        if test_result['success']:
            if test_name == 'connectivity' and test_result.get('response_time'):
                message += f"   ⚡ Время отклика: {test_result['response_time']:.2f}s\n"
            elif test_name == 'speed' and test_result.get('data'):
                data = test_result['data']
                message += f"   📊 Среднее время: {data.get('avg_time', 0):.2f}s\n"
            elif test_name == 'instagram' and test_result.get('profile_data'):
                profile = test_result['profile_data']
                followers = profile.get('edge_followed_by', {}).get('count', 0)
                message += f"   👥 Подписчиков: {followers:,}\n"
            elif test_name == 'screenshot' and test_result.get('screenshot_path'):
                screenshot_path = test_result['screenshot_path']
                if os.path.exists(screenshot_path):
                    file_size = os.path.getsize(screenshot_path) / 1024
                    message += f"   📁 Размер: {file_size:.1f} KB\n"
        
        message += "\n"
    
    return message


async def test_multiple_proxies_enhanced(proxies: List[Proxy], test_username: str = "instagram") -> Dict:
    """
    Test multiple proxies with enhanced testing.
    
    Args:
        proxies: List of Proxy objects
        test_username: Instagram username to test
        
    Returns:
        Dictionary with results for all proxies
    """
    print(f"[ENHANCED-PROXY-TEST] 🧪 Начинаем тестирование {len(proxies)} прокси")
    
    results = {
        'total_proxies': len(proxies),
        'test_username': test_username,
        'timestamp': datetime.now().isoformat(),
        'proxies': {}
    }
    
    for i, proxy in enumerate(proxies, 1):
        print(f"[ENHANCED-PROXY-TEST] 🔍 Тестируем прокси {i}/{len(proxies)}: {proxy.host}")
        
        try:
            proxy_results = await test_proxy_comprehensive(proxy, test_username)
            results['proxies'][proxy.id] = proxy_results
        except Exception as e:
            print(f"[ENHANCED-PROXY-TEST] ❌ Ошибка тестирования прокси {proxy.host}: {e}")
            results['proxies'][proxy.id] = {
                'proxy_id': proxy.id,
                'proxy_host': proxy.host,
                'error': str(e),
                'overall_score': 0,
                'successful_tests': 0,
                'total_tests': 4
            }
    
    # Calculate summary
    successful_proxies = sum(1 for p in results['proxies'].values() if p.get('overall_score', 0) > 50)
    results['successful_proxies'] = successful_proxies
    results['success_rate'] = (successful_proxies / len(proxies)) * 100 if proxies else 0
    
    print(f"[ENHANCED-PROXY-TEST] 📊 Результат: {successful_proxies}/{len(proxies)} прокси работают ({results['success_rate']:.1f}%)")
    
    return results


def format_batch_results_enhanced(results: Dict) -> str:
    """
    Format batch test results for display.
    
    Args:
        results: Batch test results dictionary
        
    Returns:
        Formatted message string
    """
    total_proxies = results['total_proxies']
    successful_proxies = results['successful_proxies']
    success_rate = results['success_rate']
    
    message = f"🧪 <b>Результаты тестирования прокси</b>\n\n"
    message += f"📊 Всего прокси: {total_proxies}\n"
    message += f"✅ Работающих: {successful_proxies}\n"
    message += f"📈 Успешность: {success_rate:.1f}%\n\n"
    
    # Sort proxies by score
    sorted_proxies = sorted(
        results['proxies'].items(),
        key=lambda x: x[1].get('overall_score', 0),
        reverse=True
    )
    
    for proxy_id, proxy_results in sorted_proxies[:10]:  # Show top 10
        proxy_host = proxy_results.get('proxy_host', 'Unknown')
        overall_score = proxy_results.get('overall_score', 0)
        successful_tests = proxy_results.get('successful_tests', 0)
        total_tests = proxy_results.get('total_tests', 4)
        
        status = "✅" if overall_score > 50 else "❌"
        message += f"{status} {proxy_host}: {successful_tests}/{total_tests} ({overall_score:.1f}%)\n"
    
    if len(sorted_proxies) > 10:
        message += f"\n... и еще {len(sorted_proxies) - 10} прокси"
    
    return message
