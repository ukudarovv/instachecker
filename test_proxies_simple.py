#!/usr/bin/env python3
"""
🔍 Простое тестирование прокси
Сначала без прокси, потом с каждым прокси
"""

import asyncio
import sys
import os
import sqlite3
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from project.services.instagram_playwright import check_account_with_playwright

DB_PATH = "bot.db"


async def main():
    """Главная функция"""
    
    print("╔═══════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                               ║")
    print("║              🔍 ПРОСТОЕ ТЕСТИРОВАНИЕ ПРОКСИ  🔍                               ║")
    print("║                                                                               ║")
    print("╚═══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    username = "gid_halal"
    
    # Тест 1: Без прокси (базовая проверка)
    print("=" * 80)
    print("🧪 ТЕСТ 1: БЕЗ ПРОКСИ (базовая проверка)")
    print("=" * 80)
    print()
    
    screenshot_dir = "screenshots/proxy_tests"
    os.makedirs(screenshot_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(screenshot_dir, f"no_proxy_{username}_{timestamp}.png")
    
    try:
        result = await check_account_with_playwright(
            username=username,
            screenshot_path=screenshot_path,
            headless=True,
            max_retries=1,
            proxy=None
        )
        
        print(f"\n📊 Результат БЕЗ прокси:")
        print(f"✅ Профиль найден: {result.get('exists')}")
        print(f"📊 Статус код: {result.get('status_code')}")
        print(f"📸 Скриншот создан: {result.get('screenshot_created', False)}")
        
        if result.get("screenshot_path") and os.path.exists(result["screenshot_path"]):
            size = os.path.getsize(result["screenshot_path"])
            print(f"📁 Скриншот: {size} байт ({size/1024:.1f} KB)")
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print()
    print("=" * 80)
    
    # Получаем прокси из базы
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, host, username, password FROM proxies WHERE is_active = 1 LIMIT 3")
    proxies = cursor.fetchall()
    conn.close()
    
    if not proxies:
        print("⚠️ Нет активных прокси в базе!")
        return
    
    print(f"\n📊 Найдено {len(proxies)} прокси для тестирования")
    print()
    
    # Тест 2: С каждым прокси
    for index, proxy_row in enumerate(proxies, 1):
        proxy_id, host_with_port, username_proxy, password = proxy_row
        
        print("=" * 80)
        print(f"🧪 ТЕСТ {index + 1}: С ПРОКСИ #{proxy_id} ({host_with_port})")
        print("=" * 80)
        print()
        
        proxy_url = f"http://{username_proxy}:{password}@{host_with_port}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(screenshot_dir, f"proxy_{proxy_id}_{host_with_port.replace(':', '_')}_{username}_{timestamp}.png")
        
        try:
            result = await check_account_with_playwright(
                username=username,
                screenshot_path=screenshot_path,
                headless=True,
                max_retries=1,
                proxy=proxy_url
            )
            
            print(f"\n📊 Результат С прокси {host_with_port}:")
            print(f"✅ Профиль найден: {result.get('exists')}")
            print(f"📊 Статус код: {result.get('status_code')}")
            print(f"📸 Скриншот создан: {result.get('screenshot_created', False)}")
            
            if result.get("screenshot_path") and os.path.exists(result["screenshot_path"]):
                size = os.path.getsize(result["screenshot_path"])
                print(f"📁 Скриншот: {size} байт ({size/1024:.1f} KB)")
                print(f"✅ Прокси РАБОТАЕТ!")
            else:
                print(f"❌ Прокси НЕ РАБОТАЕТ (скриншот не создан)")
        
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        print()
        
        # Задержка
        if index < len(proxies):
            await asyncio.sleep(3)
    
    print("=" * 80)
    print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())



