#!/usr/bin/env python3
"""
🔥 Тестирование Instagram проверки через Playwright
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from project.services.instagram_playwright import check_account_with_playwright
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Убедитесь, что вы находитесь в корневой директории проекта")
    sys.exit(1)


async def test_playwright(username: str, proxy: str = None):
    """Тестирование Playwright проверки."""
    
    print("╔═══════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                               ║")
    print("║              🔥 PLAYWRIGHT INSTAGRAM CHECKER - ТЕСТ  🔥                     ║")
    print("║                                                                               ║")
    print("╚═══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    print("=" * 80)
    print(f"🔍 Тестирование Playwright для @{username}")
    if proxy:
        # Скрываем пароль в выводе
        if '@' in proxy:
            proxy_display = proxy.split('@')[0].split(':')[0] + ':***@' + proxy.split('@')[1]
        else:
            proxy_display = proxy
        print(f"🔗 Прокси: {proxy_display}")
    else:
        print("🔗 Прокси: Не указан")
    print("=" * 80)
    print()
    
    # Создаем путь для скриншота
    screenshot_dir = "screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(screenshot_dir, f"playwright_{username}_{timestamp}.png")
    
    print(f"📸 Скриншот будет сохранен: {screenshot_path}")
    print()
    
    # Тестирование
    print("🧪 ЗАПУСК PLAYWRIGHT ПРОВЕРКИ")
    print("-" * 80)
    
    try:
        result = await check_account_with_playwright(
            username=username,
            screenshot_path=screenshot_path,
            headless=True,
            max_retries=2,
            proxy=proxy
        )
        
        print()
        print("=" * 80)
        print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
        print("=" * 80)
        
        print(f"\n🎯 Профиль: @{username}")
        
        if result.get("exists") is True:
            print("✅ Статус: ПРОФИЛЬ НАЙДЕН")
        elif result.get("exists") is False:
            print("❌ Статус: ПРОФИЛЬ НЕ НАЙДЕН")
        else:
            print("⚠️ Статус: НЕИЗВЕСТЕН")
        
        print(f"\n🔗 Прокси использован: {result.get('proxy_used', False)}")
        print(f"📊 Статус код: {result.get('status_code', 'N/A')}")
        print(f"🌐 Проверено через: {result.get('checked_via', 'N/A')}")
        
        print(f"\n📸 Скриншот создан: {result.get('screenshot_created', False)}")
        if result.get("screenshot_path"):
            print(f"📁 Путь к скриншоту: {result['screenshot_path']}")
            if os.path.exists(result['screenshot_path']):
                size = os.path.getsize(result['screenshot_path'])
                print(f"📏 Размер файла: {size} байт ({size/1024:.1f} KB)")
                
                # Проверяем качество скриншота
                if size > 50000:  # Больше 50KB
                    print("✅ Качество скриншота: ОТЛИЧНОЕ")
                elif size > 20000:  # Больше 20KB
                    print("✅ Качество скриншота: ХОРОШЕЕ")
                else:
                    print("⚠️ Качество скриншота: НИЗКОЕ")
        
        if result.get("error"):
            print(f"\n⚠️ Ошибка: {result['error']}")
        
        print()
        print("=" * 80)
        print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
        print("=" * 80)
        
        # Дополнительная информация
        print("\n💡 ПРЕИМУЩЕСТВА PLAYWRIGHT:")
        print("✅ Нативная поддержка прокси с аутентификацией")
        print("✅ Отличный обход защиты Instagram")
        print("✅ Быстрая работа и надежность")
        print("✅ Современный API и асинхронность")
        print("✅ Агрессивное закрытие модальных окон")
        print("✅ Мобильная эмуляция")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Главная функция."""
    if len(sys.argv) < 2:
        print("Использование: python test_playwright_instagram.py <username> [proxy]")
        print("\nПримеры:")
        print("  # Без прокси:")
        print("  python test_playwright_instagram.py gid_halal")
        print("\n  # С прокси:")
        print("  python test_playwright_instagram.py gid_halal http://user:pass@host:port")
        print("  python test_playwright_instagram.py gid_halal http://aiiigauk:pi8vftb70eic@142.111.48.253:7030")
        print("\n💡 Преимущества Playwright:")
        print("  - Нативная поддержка прокси с аутентификацией")
        print("  - Отличный обход защиты Instagram")
        print("  - Агрессивное закрытие модальных окон")
        print("  - Современный асинхронный API")
        print("\n📦 Установка:")
        print("  pip install playwright")
        print("  playwright install chromium")
        sys.exit(1)
    
    username = sys.argv[1]
    proxy = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"🚀 Запуск Playwright проверки для @{username}")
    if proxy:
        print(f"🔗 С прокси (нативная поддержка)")
    print(f"📸 С агрессивным закрытием модальных окон")
    print()
    
    # Запуск асинхронного тестирования
    result = asyncio.run(test_playwright(username, proxy))
    
    # Код возврата
    if result and result.get("exists") is True:
        sys.exit(0)
    elif result and result.get("exists") is False:
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()


