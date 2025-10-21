#!/usr/bin/env python3
"""
Тестирование продвинутой мобильной эмуляции для обхода блокировок Instagram.
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


async def test_mobile_bypass(username: str, verbose: bool = True):
    """Тестирование мобильной эмуляции."""
    
    print("╔═══════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                               ║")
    print("║              📱 INSTAGRAM MOBILE BYPASS - ТЕСТИРОВАНИЕ  📱                   ║")
    print("║                                                                               ║")
    print("╚═══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    print("=" * 60)
    print(f"🔍 Тестирование мобильной эмуляции для @{username}")
    print("=" * 60)
    
    # Создаем путь для скриншота
    screenshot_dir = "screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(screenshot_dir, f"mobile_{username}_{timestamp}.png")
    
    print(f"📸 Скриншот будет сохранен: {screenshot_path}")
    print()
    
    # Тест 1: Продвинутая мобильная эмуляция
    print("🧪 ТЕСТ 1: Продвинутая мобильная эмуляция")
    print("-" * 50)
    
    try:
        result = await check_account_with_mobile_bypass(
            username=username,
            screenshot_path=screenshot_path,
            headless=True,
            max_retries=2
        )
        
        print(f"Результат: {result}")
        
        if result.get("exists") is True:
            print("✅ Мобильная эмуляция: Профиль найден")
            if result.get("screenshot_path"):
                print(f"📸 Скриншот создан: {result['screenshot_path']}")
        elif result.get("exists") is False:
            print("❌ Мобильная эмуляция: Профиль не найден")
        else:
            print("⚠️ Мобильная эмуляция: Не удалось определить")
            
    except Exception as e:
        print(f"❌ Ошибка мобильной эмуляции: {e}")
    
    print()
    
    # Тест 2: Полная bypass система с мобильной эмуляцией
    print("🧪 ТЕСТ 2: Полная bypass система (включая мобильную эмуляцию)")
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
    print("🎯 Тестирование завершено!")


def main():
    """Главная функция."""
    if len(sys.argv) < 2:
        print("Использование: python test_mobile_bypass.py <username> [--verbose]")
        print("Пример: python test_mobile_bypass.py gid_halal --verbose")
        sys.exit(1)
    
    username = sys.argv[1]
    verbose = "--verbose" in sys.argv
    
    print(f"🚀 Запуск тестирования мобильной эмуляции для @{username}")
    print(f"📊 Verbose режим: {'включен' if verbose else 'выключен'}")
    print()
    
    # Запуск асинхронного тестирования
    asyncio.run(test_mobile_bypass(username, verbose))


if __name__ == "__main__":
    main()
