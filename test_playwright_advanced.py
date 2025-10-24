#!/usr/bin/env python3
"""
🎭 Тестирование продвинутой Playwright системы
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from project.services.instagram_playwright_advanced import check_account_with_playwright_advanced
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)


async def test_advanced(username: str, proxy: str = None):
    """Тестирование продвинутой Playwright системы."""
    
    print("╔═══════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                               ║")
    print("║          🎭 PLAYWRIGHT ADVANCED - ТЕСТ  🎭                                   ║")
    print("║                                                                               ║")
    print("╚═══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    print("=" * 80)
    print(f"🔍 Тестирование продвинутой Playwright системы для @{username}")
    if proxy:
        if '@' in proxy:
            proxy_display = proxy.split('@')[0].split(':')[0] + ':***@' + proxy.split('@')[1]
        else:
            proxy_display = proxy
        print(f"🔗 Прокси: {proxy_display}")
    else:
        print("🔗 Прокси: Не указан")
    print("=" * 80)
    print()
    
    # Путь для скриншота
    screenshot_dir = "screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(screenshot_dir, f"playwright_adv_{username}_{timestamp}.png")
    
    print(f"📸 Скриншот будет сохранен: {screenshot_path}")
    print()
    
    print("🧪 ЗАПУСК ПРОДВИНУТОЙ PLAYWRIGHT ПРОВЕРКИ")
    print("-" * 80)
    
    try:
        result = await check_account_with_playwright_advanced(
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
            if result.get("is_private"):
                print("🔒 Приватность: ЗАКРЫТЫЙ АККАУНТ")
            elif result.get("is_private") is False:
                print("🔓 Приватность: ОТКРЫТЫЙ АККАУНТ")
        elif result.get("exists") is False:
            print("❌ Статус: ПРОФИЛЬ НЕ НАЙДЕН")
        else:
            print("⚠️ Статус: НЕИЗВЕСТЕН")
        
        print(f"\n🔗 Прокси использован: {result.get('proxy_used', False)}")
        print(f"📊 Статус код: {result.get('status_code', 'N/A')}")
        print(f"🌐 Проверено через: {result.get('checked_via', 'N/A')}")
        
        print(f"\n📸 Скриншот создан: {result.get('screenshot_created', False)}")
        if result.get("screenshot_path"):
            if os.path.exists(result["screenshot_path"]):
                size = os.path.getsize(result["screenshot_path"])
                print(f"📁 Путь: {result['screenshot_path']}")
                print(f"📏 Размер: {size} байт ({size/1024:.1f} KB)")
                
                if size > 50000:
                    print("✅ Качество: ОТЛИЧНОЕ")
                elif size > 20000:
                    print("✅ Качество: ХОРОШЕЕ")
                else:
                    print("⚠️ Качество: НИЗКОЕ")
        
        if result.get("error"):
            print(f"\n⚠️ Ошибка: {result['error']}")
        
        print()
        print("=" * 80)
        print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
        print("=" * 80)
        
        print("\n💡 ОСОБЕННОСТИ ПРОДВИНУТОЙ СИСТЕМЫ:")
        print("✅ Стелс-режим (скрытие WebDriver)")
        print("✅ Эмуляция человеческого поведения")
        print("✅ Блокировка ненужных ресурсов")
        print("✅ Продвинутый анализ профиля")
        print("✅ Определение приватности")
        print("✅ Агрессивное закрытие модальных окон")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Главная функция."""
    if len(sys.argv) < 2:
        print("Использование: python test_playwright_advanced.py <username> [proxy]")
        print("\nПримеры:")
        print("  python test_playwright_advanced.py gid_halal")
        print("  python test_playwright_advanced.py gid_halal http://user:pass@host:port")
        print("\n🎭 Особенности продвинутой системы:")
        print("  - Стелс-режим (обход обнаружения)")
        print("  - Эмуляция человеческого поведения")
        print("  - Определение приватности профиля")
        print("  - Продвинутый анализ страницы")
        sys.exit(1)
    
    username = sys.argv[1]
    proxy = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"🚀 Запуск продвинутой Playwright проверки для @{username}")
    if proxy:
        print(f"🔗 С прокси")
    print(f"🎭 Со всеми продвинутыми функциями")
    print()
    
    result = asyncio.run(test_advanced(username, proxy))
    
    if result and result.get("exists") is True:
        sys.exit(0)
    elif result and result.get("exists") is False:
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()



