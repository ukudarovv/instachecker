#!/usr/bin/env python3
"""
Минимальный тест скриншота Instagram профиля.
Только самое необходимое для создания скриншота.
"""

import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright

async def minimal_screenshot():
    """Минимальный тест скриншота."""
    
    # Настройки
    username = "ukudarov"  # Замените на нужный username
    
    # Создаем папку для скриншотов
    screenshots_dir = "screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    
    # Генерируем путь для скриншота
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(screenshots_dir, f"minimal_{username}_{timestamp}.png")
    
    print(f"🎯 Минимальный тест скриншота для @{username}")
    print(f"📸 Путь скриншота: {screenshot_path}")
    print("-" * 50)
    
    try:
        async with async_playwright() as p:
            # Запускаем браузер с минимальными настройками
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            
            # Создаем контекст
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080}
            )
            
            # Создаем страницу
            page = await context.new_page()
            
            # URL профиля
            url = f"https://www.instagram.com/{username}/"
            
            print(f"🌐 Переход на: {url}")
            
            # Переходим на страницу
            await page.goto(url, timeout=30000)
            
            # Ждем загрузки
            print("⏳ Ожидаем загрузку...")
            await page.wait_for_timeout(3000)
            
            # Проверяем URL
            current_url = page.url
            print(f"🔗 Текущий URL: {current_url}")
            
            # Создаем скриншот
            print("📸 Создание скриншота...")
            await page.screenshot(path=screenshot_path, full_page=True)
            
            # Проверяем результат
            if os.path.exists(screenshot_path):
                file_size = os.path.getsize(screenshot_path) / 1024
                print(f"✅ Скриншот создан: {screenshot_path}")
                print(f"📏 Размер файла: {file_size:.1f} KB")
                
                # Проверяем, что файл не пустой
                if file_size > 1:  # Больше 1 KB
                    print("✅ Скриншот содержит данные")
                    return True
                else:
                    print("⚠️ Скриншот слишком маленький, возможно пустой")
                    return False
            else:
                print("❌ Скриншот не создан!")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    
    finally:
        try:
            await browser.close()
        except:
            pass

async def test_different_accounts():
    """Тест разных аккаунтов."""
    
    accounts = [
        "ukudarov",
        "instagram",
        "test_account"
    ]
    
    print(f"🧪 Тест {len(accounts)} аккаунтов")
    print("=" * 50)
    
    results = []
    
    for i, username in enumerate(accounts, 1):
        print(f"\n[{i}/{len(accounts)}] Тестируем @{username}...")
        
        # Обновляем username в функции
        import sys
        import types
        # Создаем новую функцию с обновленным username
        def updated_minimal_screenshot():
            return minimal_screenshot.__code__.replace(
                b"ukudarov", username.encode()
            )
        
        success = await minimal_screenshot()
        results.append({"username": username, "success": success})
        
        if success:
            print(f"  ✅ @{username} - успешно")
        else:
            print(f"  ❌ @{username} - неудачно")
    
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
        print(f"{status} @{result['username']}")
    
    return results

if __name__ == "__main__":
    print("🚀 Запуск минимальных тестов скриншотов")
    print("=" * 50)
    
    # Выберите тест
    test_choice = input("Выберите тест:\n1. Один аккаунт\n2. Несколько аккаунтов\nВведите номер (1 или 2): ").strip()
    
    if test_choice == "1":
        # Тест одного аккаунта
        username = input("Введите username для тестирования: ").strip()
        if username:
            # Обновляем username
            import sys
            sys.modules[__name__].minimal_screenshot.__code__ = minimal_screenshot.__code__.replace(
                b"ukudarov", username.encode()
            )
        
        success = asyncio.run(minimal_screenshot())
        print("\n" + "=" * 50)
        print("📊 РЕЗУЛЬТАТ:")
        print("=" * 50)
        print(f"✅ Успех: {success}")
        
    elif test_choice == "2":
        # Тест нескольких аккаунтов
        asyncio.run(test_different_accounts())
        
    else:
        print("❌ Неверный выбор. Запускаем тест одного аккаунта...")
        asyncio.run(minimal_screenshot())
