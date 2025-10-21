#!/usr/bin/env python3
"""
🔍 Тестирование всех прокси из базы данных
Проверка аккаунта gid_halal через каждый прокси со скриншотами
"""

import asyncio
import sys
import os
import sqlite3
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from project.services.instagram_playwright import check_account_with_playwright

DB_PATH = "bot.db"


async def test_single_proxy(proxy_id: int, host_with_port: str, username: str, password: str, target_username: str):
    """Тестирование одного прокси"""
    
    proxy_url = f"http://{username}:{password}@{host_with_port}"
    proxy_display = host_with_port
    
    print(f"\n{'=' * 80}")
    print(f"🔍 Прокси #{proxy_id}: {proxy_display}")
    print(f"{'=' * 80}")
    
    # Путь для скриншота
    screenshot_dir = "screenshots/proxy_tests"
    os.makedirs(screenshot_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(screenshot_dir, f"proxy_{proxy_id}_{host_with_port.replace(':', '_')}_{target_username}_{timestamp}.png")
    
    try:
        result = await check_account_with_playwright(
            username=target_username,
            screenshot_path=screenshot_path,
            headless=True,
            max_retries=1,
            proxy=proxy_url
        )
        
        # Результаты
        status = "✅ РАБОТАЕТ" if result.get("exists") is not None else "❌ НЕ РАБОТАЕТ"
        
        print(f"📊 Статус: {status}")
        print(f"🎯 Профиль найден: {result.get('exists')}")
        print(f"📊 Статус код: {result.get('status_code', 'N/A')}")
        print(f"📸 Скриншот создан: {result.get('screenshot_created', False)}")
        
        if result.get("screenshot_path") and os.path.exists(result["screenshot_path"]):
            size = os.path.getsize(result["screenshot_path"])
            print(f"📁 Скриншот: {result['screenshot_path']} ({size} байт)")
        
        if result.get("error"):
            print(f"⚠️ Ошибка: {result['error']}")
        
        return {
            "proxy_id": proxy_id,
            "proxy": proxy_display,
            "status": "success" if result.get("exists") is not None else "failed",
            "exists": result.get("exists"),
            "screenshot_path": result.get("screenshot_path"),
            "screenshot_created": result.get("screenshot_created", False),
            "error": result.get("error")
        }
    
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return {
            "proxy_id": proxy_id,
            "proxy": proxy_display,
            "status": "error",
            "exists": None,
            "screenshot_path": None,
            "screenshot_created": False,
            "error": str(e)
        }


async def test_all_proxies(target_username: str = "gid_halal", max_proxies: int = None):
    """Тестирование всех прокси из базы данных"""
    
    print("╔═══════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                               ║")
    print("║              🔍 ТЕСТИРОВАНИЕ ВСЕХ ПРОКСИ  🔍                                  ║")
    print("║                                                                               ║")
    print("╚═══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    # Получаем все активные прокси из базы
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        if max_proxies:
            cursor.execute("SELECT id, host, username, password FROM proxies WHERE is_active = 1 LIMIT ?", (max_proxies,))
        else:
            cursor.execute("SELECT id, host, username, password FROM proxies WHERE is_active = 1")
        
        proxies = cursor.fetchall()
        total_proxies = len(proxies)
        
        print(f"📊 Найдено активных прокси: {total_proxies}")
        print(f"🎯 Целевой аккаунт: @{target_username}")
        print(f"📸 Скриншоты будут сохранены в: screenshots/proxy_tests/")
        print()
        
        if total_proxies == 0:
            print("⚠️ Нет активных прокси в базе данных!")
            print("💡 Запустите: python add_proxies_batch.py")
            return []
        
        input(f"\n⏸️ Нажмите Enter для начала тестирования {total_proxies} прокси...")
        print()
        
        results = []
        
        for index, proxy in enumerate(proxies, 1):
            proxy_id, host_with_port, username, password = proxy
            
            print(f"\n🔄 Прогресс: {index}/{total_proxies}")
            
            result = await test_single_proxy(
                proxy_id=proxy_id,
                host_with_port=host_with_port,
                username=username,
                password=password,
                target_username=target_username
            )
            
            results.append(result)
            
            # Небольшая задержка между запросами
            if index < total_proxies:
                await asyncio.sleep(2)
    
        # Итоговая статистика
        print("\n" + "=" * 80)
        print("📊 ИТОГОВАЯ СТАТИСТИКА")
        print("=" * 80)
        
        success_count = sum(1 for r in results if r["status"] == "success")
        failed_count = sum(1 for r in results if r["status"] == "failed")
        error_count = sum(1 for r in results if r["status"] == "error")
        screenshots_count = sum(1 for r in results if r["screenshot_created"])
        
        print(f"\n✅ Успешных проверок: {success_count}/{total_proxies}")
        print(f"❌ Неудачных проверок: {failed_count}/{total_proxies}")
        print(f"⚠️ Ошибок: {error_count}/{total_proxies}")
        print(f"📸 Скриншотов создано: {screenshots_count}/{total_proxies}")
        
        # Детальные результаты
        print("\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        print("-" * 80)
        
        for result in results:
            status_emoji = "✅" if result["status"] == "success" else "❌"
            screenshot_emoji = "📸" if result["screenshot_created"] else "🚫"
            
            print(f"{status_emoji} Прокси #{result['proxy_id']}: {result['proxy']}")
            print(f"   Статус: {result['status']}")
            print(f"   Профиль найден: {result['exists']}")
            print(f"   {screenshot_emoji} Скриншот: {result['screenshot_created']}")
            if result["error"]:
                print(f"   ⚠️ Ошибка: {result['error'][:100]}")
            print()
        
        # Список рабочих прокси
        print("=" * 80)
        print("✅ РАБОЧИЕ ПРОКСИ:")
        print("=" * 80)
        
        working_proxies = [r for r in results if r["status"] == "success"]
        
        if working_proxies:
            for r in working_proxies:
                print(f"  • {r['proxy']} (ID: {r['proxy_id']})")
        else:
            print("  ⚠️ Нет рабочих прокси")
        
        print()
        
        return results
    
    finally:
        conn.close()


def main():
    """Главная функция"""
    
    if len(sys.argv) < 2:
        print("Использование: python test_all_proxies.py <username> [max_proxies]")
        print("\nПримеры:")
        print("  # Проверить все прокси")
        print("  python test_all_proxies.py gid_halal")
        print("\n  # Проверить первые 10 прокси")
        print("  python test_all_proxies.py gid_halal 10")
        print("\n💡 Сначала добавьте прокси:")
        print("  python add_proxies_batch.py")
        sys.exit(1)
    
    target_username = sys.argv[1]
    max_proxies = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    print(f"\n🚀 Запуск тестирования прокси для @{target_username}")
    if max_proxies:
        print(f"📊 Максимум прокси: {max_proxies}")
    print()
    
    results = asyncio.run(test_all_proxies(target_username, max_proxies))
    
    # Код возврата
    if results:
        success_count = sum(1 for r in results if r["status"] == "success")
        if success_count > 0:
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()

