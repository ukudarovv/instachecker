"""
🔥 Instagram checker using Playwright - самое современное и надежное решение
"""

import asyncio
import os
import time
from typing import Optional, Dict, Any
from datetime import datetime


class InstagramPlaywrightChecker:
    """Instagram checker using Playwright with full proxy support."""
    
    def __init__(self):
        self.mobile_user_agents = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 12; SM-S906N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Mobile Safari/537.36"
        ]
        
        self.mobile_devices = {
            "iPhone 13 Pro": {"width": 390, "height": 844},
            "iPhone 12": {"width": 390, "height": 844},
            "Samsung Galaxy S21": {"width": 360, "height": 800},
            "Pixel 7": {"width": 412, "height": 915}
        }
    
    def parse_proxy(self, proxy: str) -> Dict[str, Any]:
        """Парсинг прокси URL для Playwright."""
        if not proxy:
            return None
        
        try:
            # Формат: http://user:pass@host:port
            proxy_clean = proxy.replace('http://', '').replace('https://', '')
            
            if '@' in proxy_clean:
                # С аутентификацией
                auth_part, server_part = proxy_clean.split('@', 1)
                username, password = auth_part.split(':', 1)
                
                if ':' in server_part:
                    host, port = server_part.split(':', 1)
                else:
                    host = server_part
                    port = '80'
                
                return {
                    "server": f"http://{host}:{port}",
                    "username": username,
                    "password": password
                }
            else:
                # Без аутентификации
                if ':' in proxy_clean:
                    host, port = proxy_clean.split(':', 1)
                else:
                    host = proxy_clean
                    port = '80'
                
                return {
                    "server": f"http://{host}:{port}"
                }
        
        except Exception as e:
            print(f"[PLAYWRIGHT] ❌ Ошибка парсинга прокси: {e}")
            return None
    
    async def close_instagram_modals_aggressive(self, page):
        """🔥 Агрессивное закрытие всех модальных окон Instagram."""
        print("[PLAYWRIGHT] 🎯 Закрытие модальных окон...")
        
        try:
            # Ждем появления модальных окон
            await page.wait_for_timeout(3000)
            
            # Метод 1: JavaScript принудительное удаление
            js_code = """
            // 🔥 УДАЛЯЕМ ВСЕ МОДАЛЬНЫЕ ОКНА И OVERLAY
            const allElements = document.querySelectorAll('*');
            allElements.forEach(element => {
                const className = String(element.className || '');
                const style = element.style || {};
                
                // Проверяем на модальные окна и overlay
                if (className.includes('x7r02ix') || 
                    className.includes('x1vjfegm') || 
                    className.includes('_abcm') ||
                    className.includes('modal') ||
                    className.includes('overlay') ||
                    className.includes('backdrop') ||
                    element.getAttribute('role') === 'dialog' ||
                    style.position === 'fixed' ||
                    parseInt(style.zIndex) > 1000) {
                    
                    element.style.display = 'none';
                    element.style.visibility = 'hidden';
                    element.style.opacity = '0';
                    element.remove();
                }
            });
            
            // 🔥 УДАЛЯЕМ ЭЛЕМЕНТЫ С ВЫСОКИМ Z-INDEX
            const highZElements = document.querySelectorAll('[style*="z-index"]');
            highZElements.forEach(element => {
                const zIndex = parseInt(element.style.zIndex) || 0;
                if (zIndex > 100) {
                    element.style.display = 'none';
                    element.remove();
                }
            });
            
            // 🔥 УДАЛЯЕМ FIXED ПОЗИЦИОНИРОВАННЫЕ ЭЛЕМЕНТЫ
            const fixedElements = document.querySelectorAll('[style*="position: fixed"]');
            fixedElements.forEach(element => {
                element.style.display = 'none';
                element.remove();
            });
            
            // 🔥 ВОССТАНАВЛИВАЕМ BODY И HTML
            document.body.classList.remove('modal-open', 'overflow-hidden');
            document.body.style.overflow = 'auto';
            document.body.style.position = 'static';
            document.body.style.background = 'transparent';
            document.documentElement.style.overflow = 'auto';
            document.documentElement.style.background = 'transparent';
            
            // 🔥 ОЧИЩАЕМ СТИЛИ
            document.body.removeAttribute('style');
            document.documentElement.removeAttribute('style');
            document.body.style.overflow = 'auto';
            document.documentElement.style.overflow = 'auto';
            """
            
            await page.evaluate(js_code)
            print("[PLAYWRIGHT] ✅ JavaScript удаление модальных окон выполнено")
            
            # Метод 2: Клик по кнопкам закрытия
            close_selectors = [
                "button[aria-label='Close']",
                "svg[aria-label='Close']",
                "button[aria-label='Закрыть']",
                "svg[aria-label='Закрыть']"
            ]
            
            for selector in close_selectors:
                try:
                    close_button = await page.query_selector(selector)
                    if close_button:
                        await close_button.click()
                        print(f"[PLAYWRIGHT] ✅ Клик по кнопке закрытия: {selector}")
                        await page.wait_for_timeout(1000)
                except Exception:
                    pass
            
            # Метод 3: Escape клавиша
            try:
                await page.keyboard.press('Escape')
                await page.keyboard.press('Escape')
                await page.keyboard.press('Escape')
                print("[PLAYWRIGHT] ⌨️ Нажатие Escape выполнено")
            except Exception:
                pass
            
            # Финальная пауза
            await page.wait_for_timeout(2000)
            
            print("[PLAYWRIGHT] ✅ Модальные окна обработаны")
            return True
            
        except Exception as e:
            print(f"[PLAYWRIGHT] ⚠️ Ошибка закрытия модальных окон: {e}")
            return False
    
    async def check_profile_existence(
        self,
        username: str,
        screenshot_path: Optional[str] = None,
        headless: bool = True,
        proxy: Optional[str] = None
    ) -> Dict[str, Any]:
        """Проверка существования профиля через Playwright."""
        
        print(f"[PLAYWRIGHT] 🚀 Запуск проверки для @{username}")
        
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            print("[PLAYWRIGHT] ❌ Playwright не установлен!")
            print("[PLAYWRIGHT] 💡 Установите: pip install playwright && playwright install chromium")
            return {
                "exists": None,
                "error": "Playwright не установлен",
                "screenshot_path": None
            }
        
        try:
            async with async_playwright() as p:
                # Парсим прокси
                proxy_config = self.parse_proxy(proxy) if proxy else None
                
                if proxy_config:
                    print(f"[PLAYWRIGHT] 🔗 Использование прокси: {proxy_config['server']}")
                    if 'username' in proxy_config:
                        print(f"[PLAYWRIGHT] 🔐 С аутентификацией: {proxy_config['username']}:***")
                
                # Запускаем браузер с прокси
                browser = await p.chromium.launch(
                    headless=headless,
                    proxy=proxy_config
                )
                
                # Создаем контекст с мобильной эмуляцией
                import random
                device_name = random.choice(list(self.mobile_devices.keys()))
                device = self.mobile_devices[device_name]
                user_agent = random.choice(self.mobile_user_agents)
                
                print(f"[PLAYWRIGHT] 📱 Эмуляция устройства: {device_name}")
                print(f"[PLAYWRIGHT] 🌐 User-Agent: {user_agent[:50]}...")
                
                context = await browser.new_context(
                    viewport={"width": device["width"], "height": device["height"]},
                    user_agent=user_agent,
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
                await page.wait_for_timeout(5000)
                
                # Закрываем модальные окна
                await self.close_instagram_modals_aggressive(page)
                
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
                
                elif "Войдите в Instagram" in content or "Log in to Instagram" in content:
                    # Попытка обойти экран входа
                    exists = True  # Профиль существует, но требуется вход
                    print(f"[PLAYWRIGHT] ⚠️ Требуется вход, но профиль существует")
                
                else:
                    exists = True
                    print(f"[PLAYWRIGHT] ✅ Профиль @{username} найден")
                
                # Создаем скриншот
                if screenshot_path:
                    await page.screenshot(path=screenshot_path, full_page=False)
                    
                    if os.path.exists(screenshot_path):
                        file_size = os.path.getsize(screenshot_path)
                        print(f"[PLAYWRIGHT] 📸 Скриншот сохранен: {screenshot_path} ({file_size} байт)")
                    else:
                        print(f"[PLAYWRIGHT] ❌ Скриншот не создан")
                        screenshot_path = None
                
                # Закрываем браузер
                await browser.close()
                
                return {
                    "exists": exists,
                    "error": error,
                    "screenshot_path": screenshot_path,
                    "status_code": status_code,
                    "checked_via": "playwright"
                }
        
        except Exception as e:
            print(f"[PLAYWRIGHT] ❌ Ошибка проверки: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "exists": None,
                "error": str(e),
                "screenshot_path": None,
                "checked_via": "playwright"
            }


async def check_account_with_playwright(
    username: str,
    screenshot_path: Optional[str] = None,
    headless: bool = True,
    max_retries: int = 2,
    proxy: Optional[str] = None
) -> Dict[str, Any]:
    """
    🔥 Проверка Instagram аккаунта через Playwright
    
    Args:
        username: Instagram username
        screenshot_path: Path for screenshot
        headless: Run in headless mode
        max_retries: Maximum retry attempts
        proxy: Proxy URL (http://user:pass@host:port)
        
    Returns:
        Dict with check results
    """
    print(f"[PLAYWRIGHT-CHECK] 🚀 Запуск Playwright проверки для @{username}")
    
    checker = InstagramPlaywrightChecker()
    
    for attempt in range(max_retries):
        print(f"[PLAYWRIGHT-CHECK] 🔄 Попытка {attempt + 1}/{max_retries}")
        
        try:
            result = await checker.check_profile_existence(
                username=username,
                screenshot_path=screenshot_path,
                headless=headless,
                proxy=proxy
            )
            
            if result.get("exists") is not None:
                print(f"[PLAYWRIGHT-CHECK] ✅ Проверка завершена успешно")
                return {
                    "username": username,
                    "exists": result["exists"],
                    "is_private": None,
                    "full_name": None,
                    "followers": None,
                    "following": None,
                    "posts": None,
                    "screenshot_path": result.get("screenshot_path"),
                    "error": result.get("error"),
                    "checked_via": "playwright",
                    "proxy_used": bool(proxy),
                    "status_code": result.get("status_code"),
                    "screenshot_created": bool(result.get("screenshot_path"))
                }
            
            # Если результат неопределенный, пробуем еще раз
            if attempt < max_retries - 1:
                import random
                delay = random.uniform(3, 7)
                print(f"[PLAYWRIGHT-CHECK] ⏳ Ожидание {delay:.1f}с перед следующей попыткой...")
                await asyncio.sleep(delay)
        
        except Exception as e:
            print(f"[PLAYWRIGHT-CHECK] ❌ Ошибка в попытке {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                import random
                delay = random.uniform(3, 7)
                print(f"[PLAYWRIGHT-CHECK] ⏳ Ожидание {delay:.1f}с перед следующей попыткой...")
                await asyncio.sleep(delay)
    
    # Все попытки не удались
    print(f"[PLAYWRIGHT-CHECK] ❌ Все попытки проверки не удались")
    return {
        "username": username,
        "exists": None,
        "is_private": None,
        "full_name": None,
        "followers": None,
        "following": None,
        "posts": None,
        "screenshot_path": None,
        "error": "Все попытки Playwright проверки не удались",
        "checked_via": "playwright",
        "proxy_used": bool(proxy),
        "screenshot_created": False
    }

