#!/usr/bin/env python3
"""
Простой тест без proxy и без интерактивности.
"""

import asyncio
import os
from datetime import datetime
from project.services.ig_screenshot import check_account_with_header_screenshot

async def simple_test():
    """Простой тест без proxy."""
    
    username = "ukudarov"
    
    # Создаем папку для скриншотов
    screenshots_dir = "screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    
    # Генерируем путь для скриншота
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(screenshots_dir, f"simple_{username}_{timestamp}.png")
    
    print(f"🎯 Простой тест БЕЗ proxy для @{username}")
    print(f"📸 Путь скриншота: {screenshot_path}")
    print("-" * 50)
    
    try:
        # Вызываем основную функцию БЕЗ proxy
        result = await check_account_with_header_screenshot(
            username=username,
            proxy_url=None,  # БЕЗ proxy
            screenshot_path=screenshot_path,
            headless=True,
            timeout_ms=60000,
            dark_theme=True,
            mobile_emulation=False,
            crop_ratio=0
        )
        
        print("\n" + "=" * 50)
        print("📊 РЕЗУЛЬТАТЫ ТЕСТА:")
        print("=" * 50)
        
        # Выводим результаты
        print(f"👤 Username: {result.get('username', 'N/A')}")
        print(f"✅ Exists: {result.get('exists', 'N/A')}")
        print(f"📸 Screenshot: {result.get('screenshot_path', 'N/A')}")
        print(f"❌ Error: {result.get('error', 'None')}")
        print(f"⚠️ Warning: {result.get('warning', 'None')}")
        print(f"🔧 Checked via: {result.get('checked_via', 'N/A')}")
        
        # Проверяем файл скриншота
        if result.get('screenshot_path') and os.path.exists(result['screenshot_path']):
            file_size = os.path.getsize(result['screenshot_path']) / 1024
            print(f"📏 Размер файла: {file_size:.1f} KB")
            print(f"✅ Скриншот создан успешно!")
            return True
        else:
            print(f"❌ Скриншот не создан!")
            return False
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Запуск простого теста БЕЗ proxy")
    print("=" * 50)
    
    success = asyncio.run(simple_test())
    
    print("\n" + "=" * 50)
    print("📊 ИТОГОВЫЙ РЕЗУЛЬТАТ:")
    print("=" * 50)
    print(f"✅ Успех: {success}")
