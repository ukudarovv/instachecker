#!/usr/bin/env python3
"""
Тестирование мобильной эмуляции с Firefox для обхода блокировок Instagram.
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from project.services.instagram_mobile_bypass import check_account_with_mobile_bypass
    from project.services.instagram_bypass import check_account_with_bypass
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Убедитесь, что вы находитесь в корневой директории проекта")
    sys.exit(1)


async def test_firefox_bypass(username: str, proxy: str = None, verbose: bool = True):
    """Тестирование мобильной эмуляции с Firefox."""
    
    print("╔═══════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                               ║")
    print("║              🦊 FIREFOX MOBILE BYPASS - ТЕСТИРОВАНИЕ  🦊                    ║")
    print("║                                                                               ║")
    print("╚═══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    print("=" * 60)
    print(f"🔍 Тестирование Firefox мобильной эмуляции для @{username}")
    if proxy:
        print(f"🔗 Прокси: {proxy}")
    else:
        print("🔗 Прокси: Не указан (прямое подключение)")
    print("=" * 60)
    
    # Создаем путь для скриншота
    screenshot_dir = "screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(screenshot_dir, f"firefox_{username}_{timestamp}.png")
    
    print(f"📸 Скриншот будет сохранен: {screenshot_path}")
    print()
    
    # Тест 1: Firefox мобильная эмуляция
    print("🧪 ТЕСТ 1: Firefox мобильная эмуляция")
    print("-" * 50)
    
    try:
        result = await check_account_with_mobile_bypass(
            username=username,
            screenshot_path=screenshot_path,
            headless=True,
            max_retries=2,
            proxy=proxy
        )
        
        print(f"Результат: {result}")
        
        if result.get("exists") is True:
            print("✅ Firefox мобильная эмуляция: Профиль найден")
            if result.get("screenshot_path"):
                print(f"📸 Скриншот создан: {result['screenshot_path']}")
        elif result.get("exists") is False:
            print("❌ Firefox мобильная эмуляция: Профиль не найден")
        else:
            print("⚠️ Firefox мобильная эмуляция: Не удалось определить")
            
    except Exception as e:
        print(f"❌ Ошибка Firefox мобильной эмуляции: {e}")
    
    print()
    
    # Тест 2: Полная bypass система (включая Firefox)
    print("🧪 ТЕСТ 2: Полная bypass система (включая Firefox)")
    print("-" * 50)
    
    try:
        result = await check_account_with_bypass(
            username=username,
            screenshot_path=screenshot_path,
            headless=True,
            max_retries=2
        )
        
        print(f"Результат: {result}")
        
        if result.get("exists") is True:
            print("✅ Bypass система: Профиль найден")
            if result.get("screenshot_path"):
                print(f"📸 Скриншот создан: {result['screenshot_path']}")
        elif result.get("exists") is False:
            print("❌ Bypass система: Профиль не найден")
        else:
            print("⚠️ Bypass система: Не удалось определить")
            
    except Exception as e:
        print(f"❌ Ошибка bypass системы: {e}")
    
    print()
    print("=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    
    # Проверяем созданные скриншоты
    if os.path.exists(screenshot_path):
        print(f"✅ Скриншот создан: {screenshot_path}")
        print(f"📏 Размер файла: {os.path.getsize(screenshot_path)} байт")
    else:
        print(f"❌ Скриншот не создан: {screenshot_path}")
    
    print()
    print("🎯 Тестирование Firefox завершено!")


def main():
    """Главная функция."""
    if len(sys.argv) < 2:
        print("Использование: python test_firefox_bypass.py <username> [proxy] [--verbose]")
        print("Примеры:")
        print("  python test_firefox_bypass.py gid_halal --verbose")
        print("  python test_firefox_bypass.py gid_halal http://proxy:port --verbose")
        print("  python test_firefox_bypass.py gid_halal http://user:pass@proxy:port --verbose")
        sys.exit(1)
    
    username = sys.argv[1]
    proxy = None
    verbose = "--verbose" in sys.argv
    
    # Проверяем, есть ли прокси в аргументах
    for arg in sys.argv[2:]:
        if arg.startswith("http://") or arg.startswith("https://") or arg.startswith("socks5://"):
            proxy = arg
            break
    
    print(f"🚀 Запуск тестирования Firefox мобильной эмуляции для @{username}")
    print(f"🔗 Прокси: {proxy if proxy else 'Не указан (прямое подключение)'}")
    print(f"📊 Verbose режим: {'включен' if verbose else 'выключен'}")
    print()
    
    # Запуск асинхронного тестирования
    asyncio.run(test_firefox_bypass(username, proxy, verbose))


if __name__ == "__main__":
    main()
