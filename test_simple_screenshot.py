#!/usr/bin/env python3
"""
Простой тест скриншота Instagram профиля через proxy.
Без лишних проверок, только скриншот.
"""

import asyncio
import os
from datetime import datetime
from project.services.ig_screenshot import check_account_with_header_screenshot

async def test_simple_screenshot():
    """Тест простого скриншота профиля через proxy."""
    
    # Настройки
    username = "ukudarov"  # Замените на нужный username
    proxy_url = "http://proxy:port"  # Замените на ваш proxy
    
    # Создаем папку для скриншотов
    screenshots_dir = "screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    
    # Генерируем путь для скриншота
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(screenshots_dir, f"test_{username}_{timestamp}.png")
    
    print(f"🧪 Тест простого скриншота для @{username}")
    print(f"🌐 Proxy: {proxy_url}")
    print(f"📸 Путь скриншота: {screenshot_path}")
    print("-" * 50)
    
    try:
        # Вызываем функцию скриншота
        result = await check_account_with_header_screenshot(
            username=username,
            proxy_url=proxy_url,
            screenshot_path=screenshot_path,
            headless=True,
            timeout_ms=60000,  # 60 секунд
            dark_theme=True,   # Темная тема
            mobile_emulation=False,  # Desktop формат
            crop_ratio=0  # Полный скриншот
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
        else:
            print(f"❌ Скриншот не создан!")
        
        print("=" * 50)
        
        return result
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_multiple_accounts():
    """Тест скриншотов для нескольких аккаунтов."""
    
    # Список аккаунтов для тестирования
    accounts = [
        "ukudarov",
        "instagram", 
        "test_account"
    ]
    
    # Настройки proxy (замените на ваш)
    proxy_url = "http://proxy:port"
    
    print(f"🧪 Тест скриншотов для {len(accounts)} аккаунтов")
    print(f"🌐 Proxy: {proxy_url}")
    print("=" * 50)
    
    results = []
    
    for i, username in enumerate(accounts, 1):
        print(f"\n[{i}/{len(accounts)}] Тестируем @{username}...")
        
        # Создаем папку для скриншотов
        screenshots_dir = "screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        
        # Генерируем путь для скриншота
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(screenshots_dir, f"test_{username}_{timestamp}.png")
        
        try:
            result = await check_account_with_header_screenshot(
                username=username,
                proxy_url=proxy_url,
                screenshot_path=screenshot_path,
                headless=True,
                timeout_ms=60000,
                dark_theme=True,
                mobile_emulation=False,
                crop_ratio=0
            )
            
            results.append({
                'username': username,
                'success': result.get('exists', False),
                'screenshot': result.get('screenshot_path'),
                'error': result.get('error')
            })
            
            print(f"  ✅ Результат: {result.get('exists', False)}")
            if result.get('screenshot_path'):
                print(f"  📸 Скриншот: {result.get('screenshot_path')}")
            if result.get('error'):
                print(f"  ❌ Ошибка: {result.get('error')}")
                
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
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
    print("🚀 Запуск тестов скриншотов Instagram профилей")
    print("=" * 50)
    
    # Выберите тест
    test_choice = input("Выберите тест:\n1. Один аккаунт\n2. Несколько аккаунтов\nВведите номер (1 или 2): ").strip()
    
    if test_choice == "1":
        # Тест одного аккаунта
        username = input("Введите username для тестирования: ").strip()
        if username:
            # Обновляем username в функции
            import sys
            sys.modules[__name__].test_simple_screenshot.__code__ = test_simple_screenshot.__code__.replace(
                b"ukudarov", username.encode()
            )
        
        asyncio.run(test_simple_screenshot())
    elif test_choice == "2":
        # Тест нескольких аккаунтов
        asyncio.run(test_multiple_accounts())
    else:
        print("❌ Неверный выбор. Запускаем тест одного аккаунта...")
        asyncio.run(test_simple_screenshot())
