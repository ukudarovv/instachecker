"""
Тестовый скрипт для проверки полных скриншотов профиля.
Проверяет, что скриншот делается полностью без обрезки.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from project.services.universal_playwright_checker import check_instagram_account_universal


async def test_full_screenshot():
    """Тест полного скриншота профиля"""
    
    print("=" * 60)
    print("🧪 ТЕСТ: Полный скриншот профиля Instagram")
    print("=" * 60)
    
    # Тестовый username (публичный профиль)
    test_username = "instagram"  # Официальный аккаунт Instagram
    
    # Создаем папку для скриншотов
    screenshots_dir = "screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    
    # Путь для скриншота
    screenshot_path = os.path.join(screenshots_dir, f"test_full_{test_username}.png")
    
    print(f"\n📋 Параметры теста:")
    print(f"   Username: @{test_username}")
    print(f"   Screenshot path: {screenshot_path}")
    print(f"   Headless: True")
    print()
    
    # Выполняем проверку
    print(f"🔍 Запускаем проверку...")
    print()
    
    try:
        success, message, screenshot, profile_data = await check_instagram_account_universal(
            username=test_username,
            proxy_url=None,  # Без прокси для простоты
            screenshot_path=screenshot_path,
            headless=True,
            timeout=60
        )
        
        print()
        print("=" * 60)
        print("📊 РЕЗУЛЬТАТЫ ТЕСТА")
        print("=" * 60)
        print(f"✅ Успех: {success}")
        print(f"📝 Сообщение: {message}")
        print(f"📸 Скриншот: {screenshot}")
        
        if screenshot and os.path.exists(screenshot):
            # Проверяем размер файла
            size = os.path.getsize(screenshot) / 1024  # KB
            print(f"📏 Размер файла: {size:.1f} KB")
            
            # Проверяем размер изображения
            try:
                from PIL import Image
                img = Image.open(screenshot)
                width, height = img.size
                print(f"🖼️  Размер изображения: {width}x{height} px")
                
                # Проверяем, что это НЕ обрезанный скриншот
                # Обрезанный был бы ~25% высоты (примерно 225px для viewport 900px)
                # Полный должен быть ~900px
                if height < 400:
                    print()
                    print("⚠️  ВНИМАНИЕ: Скриншот выглядит обрезанным!")
                    print(f"   Высота {height}px слишком мала для полного скриншота")
                    print(f"   Ожидается ~800-900px")
                else:
                    print()
                    print("✅ УСПЕХ: Скриншот полный (не обрезанный)")
                    print(f"   Высота {height}px соответствует полному профилю")
                    
            except ImportError:
                print("⚠️  PIL не установлен, пропускаем проверку размера изображения")
            
            print()
            print(f"📂 Скриншот сохранен: {screenshot}")
            print(f"   Откройте файл, чтобы убедиться, что это полный профиль")
        else:
            print()
            print("❌ ОШИБКА: Скриншот не создан!")
        
        print()
        print("=" * 60)
        
        return success
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ ОШИБКА ТЕСТА: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print()
    print("🚀 Запуск теста полного скриншота...")
    print()
    
    result = asyncio.run(test_full_screenshot())
    
    print()
    if result:
        print("✅ Тест завершен успешно!")
    else:
        print("❌ Тест завершен с ошибками")
    print()

