#!/usr/bin/env python3
"""
Быстрый тест скриншота Instagram профиля.
Простая версия без сложной логики.
"""

import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright

async def quick_screenshot_test(username="ukudarov"):
    """Быстрый тест скриншота."""
    
    # Создаем папку для скриншотов
    screenshots_dir = "screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    
    # Генерируем путь для скриншота
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(screenshots_dir, f"quick_{username}_{timestamp}.png")
    
    print(f"🎯 Быстрый тест скриншота для @{username}")
    print(f"📸 Путь скриншота: {screenshot_path}")
    print("-" * 50)
    
    try:
        async with async_playwright() as p:
            # Запускаем браузер
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
                
                if file_size > 1:
                    print("✅ Скриншот содержит данные")
                    return True
                else:
                    print("⚠️ Скриншот слишком маленький")
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

async def test_multiple_accounts():
    """Тест нескольких аккаунтов."""
    
    accounts = ["ukudarov", "instagram", "test_account"]
    
    print(f"🧪 Тест {len(accounts)} аккаунтов")
    print("=" * 50)
    
    results = []
    
    for i, username in enumerate(accounts, 1):
        print(f"\n[{i}/{len(accounts)}] Тестируем @{username}...")
        
        success = await quick_screenshot_test(username)
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
    print("🚀 Запуск быстрых тестов скриншотов")
    print("=" * 50)
    
    # Выберите тест
    test_choice = input("Выберите тест:\n1. Один аккаунт\n2. Несколько аккаунтов\nВведите номер (1 или 2): ").strip()
    
    if test_choice == "1":
        # Тест одного аккаунта
        username = input("Введите username для тестирования: ").strip()
        if not username:
            username = "ukudarov"
        
        success = asyncio.run(quick_screenshot_test(username))
        print("\n" + "=" * 50)
        print("📊 РЕЗУЛЬТАТ:")
        print("=" * 50)
        print(f"✅ Успех: {success}")
        
    elif test_choice == "2":
        # Тест нескольких аккаунтов
        asyncio.run(test_multiple_accounts())
        
    else:
        print("❌ Неверный выбор. Запускаем тест одного аккаунта...")
        asyncio.run(quick_screenshot_test())
