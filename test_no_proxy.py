#!/usr/bin/env python3
"""
Тест основной функции без proxy.
"""

import asyncio
import os
from datetime import datetime
from project.services.ig_screenshot import check_account_with_header_screenshot

async def test_no_proxy():
    """Тест основной функции без proxy."""
    
    username = "ukudarov"
    
    # Создаем папку для скриншотов
    screenshots_dir = "screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    
    # Генерируем путь для скриншота
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(screenshots_dir, f"no_proxy_{username}_{timestamp}.png")
    
    print(f"🎯 Тест основной функции БЕЗ proxy для @{username}")
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

async def test_multiple_accounts_no_proxy():
    """Тест нескольких аккаунтов без proxy."""
    
    accounts = ["ukudarov", "instagram", "test_account"]
    
    print(f"🧪 Тест {len(accounts)} аккаунтов БЕЗ proxy")
    print("=" * 50)
    
    results = []
    
    for i, username in enumerate(accounts, 1):
        print(f"\n[{i}/{len(accounts)}] Тестируем @{username}...")
        
        # Создаем папку для скриншотов
        screenshots_dir = "screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        
        # Генерируем путь для скриншота
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(screenshots_dir, f"no_proxy_{username}_{timestamp}.png")
        
        try:
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
            
            success = result.get('exists', False) and result.get('screenshot_path') and os.path.exists(result['screenshot_path'])
            results.append({
                'username': username,
                'success': success,
                'screenshot': result.get('screenshot_path'),
                'error': result.get('error')
            })
            
            if success:
                file_size = os.path.getsize(result['screenshot_path']) / 1024
                print(f"  ✅ @{username} - успешно ({file_size:.1f} KB)")
            else:
                print(f"  ❌ @{username} - неудачно: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"  ❌ @{username} - ошибка: {e}")
            results.append({
                'username': username,
                'success': False,
                'screenshot': None,
                'error': str(e)
            })
    
    # Итоговый отчет
    print("\n" + "=" * 50)
    print("📊 ИТОГОВЫЙ ОТЧЕТ:")
    print("=" * 50)
    
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"✅ Успешных: {successful}/{total}")
    print(f"❌ Неудачных: {total - successful}/{total}")
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"{status} @{result['username']}: {result['error'] or 'OK'}")
    
    return results

if __name__ == "__main__":
    print("🚀 Запуск тестов БЕЗ proxy")
    print("=" * 50)
    
    # Выберите тест
    test_choice = input("Выберите тест:\n1. Один аккаунт\n2. Несколько аккаунтов\nВведите номер (1 или 2): ").strip()
    
    if test_choice == "1":
        # Тест одного аккаунта
        username = input("Введите username для тестирования: ").strip()
        if not username:
            username = "ukudarov"
        
        success = asyncio.run(test_no_proxy())
        print("\n" + "=" * 50)
        print("📊 РЕЗУЛЬТАТ:")
        print("=" * 50)
        print(f"✅ Успех: {success}")
        
    elif test_choice == "2":
        # Тест нескольких аккаунтов
        asyncio.run(test_multiple_accounts_no_proxy())
        
    else:
        print("❌ Неверный выбор. Запускаем тест одного аккаунта...")
        asyncio.run(test_no_proxy())
