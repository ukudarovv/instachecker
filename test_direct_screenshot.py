#!/usr/bin/env python3
"""
Прямой тест скриншота Instagram профиля через Playwright.
Минимальные проверки, только скриншот.
"""

import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright

async def direct_screenshot_test():
    """Прямой тест скриншота без лишних проверок."""
    
    # Настройки
    username = "ukudarov"  # Замените на нужный username
    proxy_url = "http://proxy:port"  # Замените на ваш proxy
    
    # Создаем папку для скриншотов
    screenshots_dir = "screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    
    # Генерируем путь для скриншота
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(screenshots_dir, f"direct_{username}_{timestamp}.png")
    
    print(f"🎯 Прямой тест скриншота для @{username}")
    print(f"🌐 Proxy: {proxy_url}")
    print(f"📸 Путь скриншота: {screenshot_path}")
    print("-" * 50)
    
    try:
        async with async_playwright() as p:
            # Настройки браузера
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu-sandbox",
                    "--enable-gpu",
                    "--force-device-scale-factor=1",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor"
                ]
            )
            
            # Создаем контекст с proxy
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # Создаем страницу
            page = await context.new_page()
            
            # URL профиля
            url = f"https://www.instagram.com/{username}/"
            
            print(f"🌐 Переход на: {url}")
            
            # Переходим на страницу
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Ждем загрузки
            print("⏳ Ожидаем загрузку страницы...")
            await page.wait_for_timeout(5000)
            
            # Проверяем URL
            current_url = page.url
            print(f"🔗 Текущий URL: {current_url}")
            
            # Применяем темную тему
            print("🌙 Применяем темную тему...")
            await page.evaluate("""
                // Применяем темную тему
                document.body.style.setProperty('background-color', '#1a1a1a', 'important');
                document.documentElement.style.setProperty('background-color', '#1a1a1a', 'important');
                document.body.style.setProperty('color', '#e6e6e6', 'important');
            """)
            
            # Дополнительное ожидание
            await page.wait_for_timeout(2000)
            
            # Создаем скриншот
            print("📸 Создание скриншота...")
            await page.screenshot(path=screenshot_path, full_page=True)
            
            # Проверяем результат
            if os.path.exists(screenshot_path):
                file_size = os.path.getsize(screenshot_path) / 1024
                print(f"✅ Скриншот создан: {screenshot_path}")
                print(f"📏 Размер файла: {file_size:.1f} KB")
                
                # Получаем размеры изображения
                try:
                    from PIL import Image
                    img = Image.open(screenshot_path)
                    width, height = img.size
                    print(f"📐 Размеры: {width}x{height}")
                except ImportError:
                    print("⚠️ PIL не установлен, размеры не получены")
                
                return {
                    "success": True,
                    "screenshot_path": screenshot_path,
                    "file_size": file_size,
                    "url": current_url
                }
            else:
                print("❌ Скриншот не создан!")
                return {
                    "success": False,
                    "error": "screenshot_not_created"
                }
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }
    
    finally:
        try:
            await browser.close()
        except:
            pass

async def test_without_proxy():
    """Тест скриншота без proxy."""
    
    username = "ukudarov"
    
    # Создаем папку для скриншотов
    screenshots_dir = "screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    
    # Генерируем путь для скриншота
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(screenshots_dir, f"no_proxy_{username}_{timestamp}.png")
    
    print(f"🎯 Тест скриншота без proxy для @{username}")
    print(f"📸 Путь скриншота: {screenshot_path}")
    print("-" * 50)
    
    try:
        async with async_playwright() as p:
            # Настройки браузера
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu-sandbox",
                    "--enable-gpu"
                ]
            )
            
            # Создаем контекст без proxy
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # Создаем страницу
            page = await context.new_page()
            
            # URL профиля
            url = f"https://www.instagram.com/{username}/"
            
            print(f"🌐 Переход на: {url}")
            
            # Переходим на страницу
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Ждем загрузки
            print("⏳ Ожидаем загрузку страницы...")
            await page.wait_for_timeout(5000)
            
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
                return True
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

if __name__ == "__main__":
    print("🚀 Запуск прямых тестов скриншотов")
    print("=" * 50)
    
    # Выберите тест
    test_choice = input("Выберите тест:\n1. С proxy\n2. Без proxy\nВведите номер (1 или 2): ").strip()
    
    if test_choice == "1":
        # Тест с proxy
        username = input("Введите username для тестирования: ").strip()
        if username:
            # Обновляем username
            import sys
            sys.modules[__name__].direct_screenshot_test.__code__ = direct_screenshot_test.__code__.replace(
                b"ukudarov", username.encode()
            )
        
        result = asyncio.run(direct_screenshot_test())
        print("\n" + "=" * 50)
        print("📊 РЕЗУЛЬТАТ:")
        print("=" * 50)
        print(f"✅ Успех: {result.get('success', False)}")
        if result.get('screenshot_path'):
            print(f"📸 Скриншот: {result.get('screenshot_path')}")
        if result.get('error'):
            print(f"❌ Ошибка: {result.get('error')}")
            
    elif test_choice == "2":
        # Тест без proxy
        username = input("Введите username для тестирования: ").strip()
        if username:
            # Обновляем username
            import sys
            sys.modules[__name__].test_without_proxy.__code__ = test_without_proxy.__code__.replace(
                b"ukudarov", username.encode()
            )
        
        success = asyncio.run(test_without_proxy())
        print("\n" + "=" * 50)
        print("📊 РЕЗУЛЬТАТ:")
        print("=" * 50)
        print(f"✅ Успех: {success}")
        
    else:
        print("❌ Неверный выбор. Запускаем тест с proxy...")
        asyncio.run(direct_screenshot_test())
