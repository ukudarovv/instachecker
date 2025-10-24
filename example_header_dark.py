"""
Простой пример использования header-скриншотов с темной темой через proxy.
"""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from project.services.ig_screenshot import check_account_with_header_screenshot


async def main():
    """Пример проверки профиля с header-скриншотом и темной темой"""
    
    print("=" * 60)
    print("📸 Пример: Header-скриншот с темной темой")
    print("=" * 60)
    print()
    
    # Параметры
    username = "instagram"  # Проверяемый профиль
    proxy_url = "http://user:pass@proxy.example.com:8080"  # ЗАМЕНИТЕ на ваш proxy
    screenshot_path = "screenshots/example_header_dark.png"
    
    print(f"🔍 Проверяем: @{username}")
    print(f"🌐 Proxy: {proxy_url[:30]}...")
    print(f"🌙 Темная тема: Включена")
    print()
    
    # Выполняем проверку
    result = await check_account_with_header_screenshot(
        username=username,
        proxy_url=proxy_url,
        screenshot_path=screenshot_path,
        headless=True,
        timeout_ms=30000,
        dark_theme=True  # Черный фон
    )
    
    # Результат
    print()
    print("=" * 60)
    print("📊 РЕЗУЛЬТАТ")
    print("=" * 60)
    
    if result.get("exists"):
        print("✅ Профиль найден!")
        print(f"📸 Скриншот: {result.get('screenshot_path')}")
        print()
        print("Откройте скриншот и проверьте:")
        print("  • Виден только header профиля")
        print("  • Фон черный")
        print("  • Текст белый")
    else:
        print(f"❌ Ошибка: {result.get('error')}")
    
    print()
    print("=" * 60)


if __name__ == "__main__":
    print()
    print("🚀 Запуск примера...")
    print()
    print("⚠️  ВНИМАНИЕ: Замените proxy_url на ваш реальный прокси!")
    print()
    
    # Проверяем, что пользователь изменил proxy
    example_proxy = "http://user:pass@proxy.example.com:8080"
    
    # Можно раскомментировать после замены proxy:
    # asyncio.run(main())
    
    print("❌ Пожалуйста, отредактируйте файл и замените proxy_url на реальный прокси")
    print()
    print("Или используйте тестовый скрипт с прокси из базы:")
    print("  python test_proxy_header_screenshot.py")
    print()

