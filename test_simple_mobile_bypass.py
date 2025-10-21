#!/usr/bin/env python3
"""
Упрощенный тест мобильной эмуляции без сложных настроек.
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from project.services.instagram_bypass import check_account_with_bypass
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)


async def test_simple_bypass(username: str, verbose: bool = True):
    """Простое тестирование bypass системы."""
    
    print("╔═══════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                               ║")
    print("║                    🚀 SIMPLE BYPASS TEST - ПРОСТОЙ ТЕСТ  🚀                 ║")
    print("║                                                                               ║")
    print("╚═══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    print("=" * 60)
    print(f"🔍 Простое тестирование bypass системы для @{username}")
    print("=" * 60)
    
    # Создаем путь для скриншота
    screenshot_dir = "screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(screenshot_dir, f"simple_{username}_{timestamp}.png")
    
    print(f"📸 Скриншот будет сохранен: {screenshot_path}")
    print()
    
    # Тест bypass системы
    print("🧪 ТЕСТ: Bypass система (API + мобильная эмуляция)")
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
    print("🎯 Простое тестирование завершено!")


def main():
    """Главная функция."""
    if len(sys.argv) < 2:
        print("Использование: python test_simple_mobile_bypass.py <username> [--verbose]")
        print("Примеры:")
        print("  python test_simple_mobile_bypass.py gid_halal --verbose")
        sys.exit(1)
    
    username = sys.argv[1]
    verbose = "--verbose" in sys.argv
    
    print(f"🚀 Запуск простого тестирования bypass системы для @{username}")
    print(f"📊 Verbose режим: {'включен' if verbose else 'выключен'}")
    print()
    
    # Запуск асинхронного тестирования
    asyncio.run(test_simple_bypass(username, verbose))


if __name__ == "__main__":
    main()
