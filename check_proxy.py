#!/usr/bin/env python3
"""Quick proxy checker - проверка прокси перед добавлением в бот."""

import asyncio
import sys
from aiohttp import ClientSession, ClientTimeout
from aiohttp_socks import ProxyConnector


async def check_proxy(proxy_url: str) -> dict:
    """
    Проверить прокси и вернуть результаты.
    
    Args:
        proxy_url: URL прокси в формате scheme://[user:pass@]host:port
        
    Returns:
        dict с результатами проверки
    """
    result = {
        'url': proxy_url,
        'works': False,
        'ip': None,
        'response_time': None,
        'error': None
    }
    
    print(f"\n{'='*60}")
    print(f"🔍 Проверка прокси: {proxy_url}")
    print(f"{'='*60}")
    
    try:
        # Create connector
        connector = ProxyConnector.from_url(proxy_url)
        print(f"✅ Connector создан")
        
        # Test connection
        timeout = ClientTimeout(total=15)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        import time
        start_time = time.time()
        
        print(f"📡 Подключение к http://httpbin.org/ip...")
        
        async with ClientSession(connector=connector, timeout=timeout, headers=headers) as sess:
            async with sess.get("http://httpbin.org/ip") as resp:
                response_time = time.time() - start_time
                result['response_time'] = response_time
                
                print(f"📊 HTTP Status: {resp.status}")
                print(f"⏱️ Время ответа: {response_time:.2f}s")
                
                if resp.status == 200:
                    data = await resp.json()
                    proxy_ip = data.get('origin', 'Unknown')
                    result['ip'] = proxy_ip
                    result['works'] = True
                    
                    print(f"✅ ПРОКСИ РАБОТАЕТ!")
                    print(f"🌐 IP прокси: {proxy_ip}")
                    return result
                elif resp.status == 407:
                    result['error'] = "407 Proxy Authentication Required"
                    print(f"❌ Ошибка 407: Неверная авторизация")
                    print(f"💡 Проверьте логин и пароль")
                else:
                    result['error'] = f"HTTP {resp.status}"
                    print(f"❌ Ошибка: HTTP {resp.status}")
                
    except asyncio.TimeoutError:
        result['error'] = "Timeout"
        print(f"❌ Timeout: Прокси не отвечает")
        print(f"💡 Прокси слишком медленный или недоступен")
    except Exception as e:
        result['error'] = str(e)
        print(f"❌ Ошибка: {e}")
        
        # Более детальные советы
        if "407" in str(e):
            print(f"💡 Проверьте учетные данные прокси")
        elif "Connection refused" in str(e):
            print(f"💡 Прокси-сервер отклоняет подключение")
        elif "getaddrinfo failed" in str(e):
            print(f"💡 Не удается найти прокси-сервер (неверный адрес)")
        elif "Connection timeout" in str(e):
            print(f"💡 Прокси не отвечает (недоступен или заблокирован)")
    
    return result


async def check_multiple_proxies(proxy_list: list) -> list:
    """Проверить несколько прокси."""
    results = []
    
    for i, proxy_url in enumerate(proxy_list, 1):
        print(f"\n\n📋 Прокси {i}/{len(proxy_list)}")
        result = await check_proxy(proxy_url)
        results.append(result)
        
        # Небольшая пауза между проверками
        if i < len(proxy_list):
            await asyncio.sleep(1)
    
    return results


def print_summary(results: list):
    """Вывести сводку по всем прокси."""
    print(f"\n\n{'='*60}")
    print(f"📊 СВОДКА")
    print(f"{'='*60}\n")
    
    working = [r for r in results if r['works']]
    failed = [r for r in results if not r['works']]
    
    print(f"✅ Рабочих: {len(working)}/{len(results)}")
    print(f"❌ Не работают: {len(failed)}/{len(results)}")
    
    if working:
        print(f"\n🎉 Рабочие прокси:")
        for r in working:
            print(f"  ✅ {r['url']}")
            print(f"     IP: {r['ip']}")
            print(f"     Время: {r['response_time']:.2f}s")
    
    if failed:
        print(f"\n❌ Не работают:")
        for r in failed:
            print(f"  ❌ {r['url']}")
            print(f"     Причина: {r['error']}")
    
    print(f"\n{'='*60}")


async def main():
    """Main function."""
    print("🔍 Проверка прокси для InstaChecker Bot")
    
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        # Прокси переданы как аргументы
        proxies = sys.argv[1:]
    else:
        # Интерактивный режим
        print("\nВведите proxy URL в формате: scheme://[user:pass@]host:port")
        print("Примеры:")
        print("  http://proxy.com:8080")
        print("  http://user:pass@proxy.com:8080")
        print("  socks5://user:pass@1.2.3.4:1080")
        print("\nДля проверки нескольких прокси введите по одному на строку.")
        print("Для завершения ввода нажмите Enter на пустой строке.\n")
        
        proxies = []
        while True:
            proxy = input(f"Прокси {len(proxies)+1} (или Enter для начала): ").strip()
            if not proxy:
                break
            proxies.append(proxy)
        
        if not proxies:
            print("❌ Не введено ни одного прокси")
            return
    
    # Проверяем прокси
    results = await check_multiple_proxies(proxies)
    
    # Выводим сводку
    if len(results) > 1:
        print_summary(results)
    
    # Советы
    print("\n💡 СОВЕТЫ:")
    print("  1. Добавляйте только рабочие прокси в бот")
    print("  2. Используйте приватные прокси для лучшей стабильности")
    print("  3. Добавьте несколько прокси для ротации")
    print("  4. Проверяйте прокси перед добавлением в бот")
    print("\n📖 Документация: PROXY_TEST_REPORT.md")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Прервано пользователем")
