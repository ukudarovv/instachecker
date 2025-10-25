#!/usr/bin/env python3
"""
🔥 Тестирование Playwright с прокси
Специальный тест с правильной обработкой прокси
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


async def test_playwright_with_proxy(username: str, proxy_dict: dict):
    """Тестирование Playwright с правильно подготовленным прокси."""
    
    print("╔═══════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                               ║")
    print("║              🔥 PLAYWRIGHT С ПРОКСИ - ТЕСТ  🔥                              ║")
    print("║                                                                               ║")
    print("╚═══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    print("=" * 80)
    print(f"🔍 Тестирование Playwright для @{username}")
    print(f"🔗 Прокси: {proxy_dict['host']}:{proxy_dict['port']}")
    print(f"🔐 Аутентификация: {proxy_dict['username']}:***")
    print("=" * 80)
    print()
    
    # Создаем путь для скриншота
    screenshot_dir = "screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(screenshot_dir, f"playwright_proxy_{username}_{timestamp}.png")
    
    print(f"📸 Скриншот будет сохранен: {screenshot_path}")
    print()
    
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ Playwright не установлен!")
        print("💡 Установите: pip install playwright && playwright install chromium")
        return None
    
    # Тестирование
    print("🧪 ЗАПУСК PLAYWRIGHT ПРОВЕРКИ С ПРОКСИ")
    print("-" * 80)
    
    try:
        async with async_playwright() as p:
            # Настройка прокси для Playwright
            proxy_config = {
                "server": f"http://{proxy_dict['host']}:{proxy_dict['port']}",
                "username": proxy_dict['username'],
                "password": proxy_dict['password']
            }
            
            print(f"[PLAYWRIGHT] 🔗 Конфигурация прокси:")
            print(f"[PLAYWRIGHT]   Server: {proxy_config['server']}")
            print(f"[PLAYWRIGHT]   Auth: {proxy_config['username']}:***")
            
            # Запускаем браузер с прокси
            print(f"[PLAYWRIGHT] 🚀 Запуск Chromium с прокси...")
            browser = await p.chromium.launch(
                headless=True,
                proxy=proxy_config
            )
            
            # Создаем контекст с мобильной эмуляцией
            mobile_user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
            
            print(f"[PLAYWRIGHT] 📱 Создание контекста с мобильной эмуляцией...")
            context = await browser.new_context(
                viewport={"width": 390, "height": 844},
                user_agent=mobile_user_agent,
                locale='ru-RU',
                timezone_id='Europe/Moscow'
            )
            
            # Создаем страницу
            page = await context.new_page()
            
            # Скрываем признаки автоматизации
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            """)
            
            # Устанавливаем таймауты
            page.set_default_timeout(45000)
            
            # Переходим на страницу профиля
            url = f"https://www.instagram.com/{username}/"
            print(f"[PLAYWRIGHT] 🌐 Переход на: {url}")
            
            response = await page.goto(url, wait_until='domcontentloaded')
            
            # Проверяем статус ответа
            status_code = response.status
            print(f"[PLAYWRIGHT] 📊 Статус код: {status_code}")
            
            # Ждем загрузки контента
            print(f"[PLAYWRIGHT] ⏳ Ожидание загрузки контента...")
            await page.wait_for_timeout(5000)
            
            # Закрываем модальные окна
            print(f"[PLAYWRIGHT] 🎯 Закрытие модальных окон...")
            js_code = """
            // Удаляем все модальные окна
            const dialogs = document.querySelectorAll('[role="dialog"]');
            dialogs.forEach(d => d.remove());
            
            // Удаляем overlay
            const overlays = document.querySelectorAll('[class*="x7r02ix"]');
            overlays.forEach(o => o.remove());
            
            // Восстанавливаем body
            document.body.style.overflow = 'auto';
            document.body.style.position = 'static';
            document.documentElement.style.overflow = 'auto';
            """
            
            await page.evaluate(js_code)
            print(f"[PLAYWRIGHT] ✅ Модальные окна обработаны")
            
            # Клик по кнопкам закрытия
            try:
                close_button = await page.query_selector("button[aria-label='Close']")
                if close_button:
                    await close_button.click()
                    print(f"[PLAYWRIGHT] ✅ Кнопка закрытия нажата")
            except Exception:
                pass
            
            # Escape клавиша
            try:
                await page.keyboard.press('Escape')
                await page.keyboard.press('Escape')
                print(f"[PLAYWRIGHT] ⌨️ Escape нажат")
            except Exception:
                pass
            
            await page.wait_for_timeout(2000)
            
            # Получаем содержимое страницы
            content = await page.content()
            page_title = await page.title()
            
            print(f"[PLAYWRIGHT] 📄 Заголовок страницы: {page_title}")
            
            # Определяем существование профиля
            exists = None
            error = None
            
            if status_code == 404:
                exists = False
                error = "404_not_found"
                print(f"[PLAYWRIGHT] ❌ Профиль @{username} не найден (404)")
            
            elif status_code == 403:
                exists = None
                error = "403_forbidden"
                print(f"[PLAYWRIGHT] 🚫 Доступ запрещен (403)")
            
            elif "Страница не найдена" in content or "Sorry, this page isn't available" in content:
                exists = False
                error = "page_not_found"
                print(f"[PLAYWRIGHT] ❌ Профиль @{username} не найден (контент)")
            
            else:
                exists = True
                print(f"[PLAYWRIGHT] ✅ Профиль @{username} найден")
            
            # Создаем скриншот
            print(f"[PLAYWRIGHT] 📸 Создание скриншота...")
            await page.screenshot(path=screenshot_path, full_page=False)
            
            if os.path.exists(screenshot_path):
                file_size = os.path.getsize(screenshot_path)
                print(f"[PLAYWRIGHT] ✅ Скриншот сохранен: {file_size} байт")
            else:
                print(f"[PLAYWRIGHT] ❌ Скриншот не создан")
                screenshot_path = None
            
            # Закрываем браузер
            await browser.close()
            print(f"[PLAYWRIGHT] 🔒 Браузер закрыт")
            
            # Результаты
            print()
            print("=" * 80)
            print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
            print("=" * 80)
            
            print(f"\n🎯 Профиль: @{username}")
            
            if exists is True:
                print("✅ Статус: ПРОФИЛЬ НАЙДЕН")
            elif exists is False:
                print("❌ Статус: ПРОФИЛЬ НЕ НАЙДЕН")
            else:
                print("⚠️ Статус: НЕИЗВЕСТЕН")
            
            print(f"\n🔗 Прокси использован: Да")
            print(f"📊 Статус код: {status_code}")
            print(f"🌐 Проверено через: Playwright + Proxy")
            
            print(f"\n📸 Скриншот создан: {screenshot_path is not None}")
            if screenshot_path and os.path.exists(screenshot_path):
                size = os.path.getsize(screenshot_path)
                print(f"📁 Путь к скриншоту: {screenshot_path}")
                print(f"📏 Размер файла: {size} байт ({size/1024:.1f} KB)")
                
                # Проверяем качество скриншота
                if size > 50000:
                    print("✅ Качество скриншота: ОТЛИЧНОЕ")
                elif size > 20000:
                    print("✅ Качество скриншота: ХОРОШЕЕ")
                else:
                    print("⚠️ Качество скриншота: НИЗКОЕ")
            
            if error:
                print(f"\n⚠️ Ошибка: {error}")
            
            print()
            print("=" * 80)
            print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
            print("=" * 80)
            
            # Дополнительная информация
            print("\n💡 ПРЕИМУЩЕСТВА PLAYWRIGHT + PROXY:")
            print("✅ Нативная поддержка прокси с аутентификацией")
            print("✅ Отличный обход защиты Instagram")
            print("✅ Быстрая работа и надежность")
            print("✅ Современный асинхронный API")
            print("✅ Агрессивное закрытие модальных окон")
            print("✅ Мобильная эмуляция")
            
            return {
                "exists": exists,
                "status_code": status_code,
                "screenshot_path": screenshot_path,
                "error": error
            }
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Главная функция."""
    if len(sys.argv) < 2:
        print("Использование: python test_playwright_with_proxy.py <username>")
        print("\nПример:")
        print("  python test_playwright_with_proxy.py gid_halal")
        print("\nПрокси будет использован:")
        print("  Host: 142.111.48.253")
        print("  Port: 7030")
        print("  Username: aiiigauk")
        print("  Password: pi8vftb70eic")
        sys.exit(1)
    
    username = sys.argv[1]
    
    # Прокси конфигурация (жестко заданная для теста)
    proxy_dict = {
        "host": "142.111.48.253",
        "port": "7030",
        "username": "aiiigauk",
        "password": "pi8vftb70eic"
    }
    
    print(f"🚀 Запуск Playwright проверки для @{username}")
    print(f"🔗 С прокси: {proxy_dict['host']}:{proxy_dict['port']}")
    print(f"🔐 Аутентификация: {proxy_dict['username']}:***")
    print()
    
    # Запуск асинхронного тестирования
    result = asyncio.run(test_playwright_with_proxy(username, proxy_dict))
    
    # Код возврата
    if result and result.get("exists") is True:
        sys.exit(0)
    elif result and result.get("exists") is False:
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()




