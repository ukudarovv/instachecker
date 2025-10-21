"""
🎭 Продвинутая проверка Instagram через Playwright
Включает все лучшие практики и техники обхода защиты
"""

import asyncio
import random
import os
from typing import Optional, Dict, Any, List
from datetime import datetime


class InstagramPlaywrightAdvanced:
    """Продвинутый Instagram checker с полным набором функций"""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        # Мобильные User-Agents
        self.user_agents = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPad; CPU OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36"
        ]
        
        # Мобильные устройства (точные названия из Playwright)
        self.mobile_devices = [
            "iPhone 12",
            "iPhone 13",
            "Pixel 5",
            "iPhone 13 Pro"
        ]
        
        # Viewports
        self.viewports = [
            {"width": 390, "height": 844},  # iPhone 12/13
            {"width": 393, "height": 851},  # Pixel 7
            {"width": 360, "height": 800},  # Galaxy S21
            {"width": 412, "height": 915},  # Pixel 7 Pro
        ]
    
    async def initialize(self, proxy: Optional[str] = None, headless: bool = True, device: Optional[str] = None):
        """🚀 Инициализация браузера с продвинутыми настройками"""
        print("[PLAYWRIGHT-ADV] 🚀 Инициализация продвинутого Playwright...")
        
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            print("[PLAYWRIGHT-ADV] ❌ Playwright не установлен!")
            return False
        
        self.playwright = await async_playwright().start()
        
        # Настройки запуска браузера
        launch_options = {
            "headless": headless,
            "args": [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-features=VizDisplayCompositor",
                "--disable-notifications",
                "--disable-popup-blocking"
            ]
        }
        
        # Настройка прокси
        if proxy:
            proxy_config = self._parse_proxy(proxy)
            if proxy_config:
                launch_options["proxy"] = proxy_config
                print(f"[PLAYWRIGHT-ADV] 🔗 Прокси настроен: {proxy_config['server']}")
        
        self.browser = await self.playwright.chromium.launch(**launch_options)
        
        # Выбор устройства
        if not device:
            device = random.choice(self.mobile_devices)
        
        print(f"[PLAYWRIGHT-ADV] 📱 Эмуляция устройства: {device}")
        
        device_config = self.playwright.devices[device]
        
        # Создание контекста с улучшенными настройками
        self.context = await self.browser.new_context(
            **device_config,
            locale='ru-RU',
            timezone_id='Europe/Moscow',
            permissions=[],  # Отключаем все permissions
            color_scheme='light',
            reduced_motion='reduce'
        )
        
        # Дополнительные заголовки
        await self.context.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        })
        
        # Создание страницы
        self.page = await self.context.new_page()
        
        # Стелс-режим
        await self._enable_stealth_mode()
        
        # Блокировка ненужных ресурсов для ускорения
        await self._setup_resource_blocking()
        
        print("[PLAYWRIGHT-ADV] ✅ Браузер инициализирован")
        return True
    
    def _parse_proxy(self, proxy: str) -> Optional[Dict[str, str]]:
        """Парсинг прокси URL"""
        try:
            proxy_clean = proxy.replace('http://', '').replace('https://', '')
            
            if '@' in proxy_clean:
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
                if ':' in proxy_clean:
                    host, port = proxy_clean.split(':', 1)
                else:
                    host = proxy_clean
                    port = '80'
                
                return {"server": f"http://{host}:{port}"}
        
        except Exception as e:
            print(f"[PLAYWRIGHT-ADV] ❌ Ошибка парсинга прокси: {e}")
            return None
    
    async def _enable_stealth_mode(self):
        """🛡️ Включение стелс-режима для обхода обнаружения"""
        print("[PLAYWRIGHT-ADV] 🛡️ Включение стелс-режима...")
        
        # Удаление WebDriver признаков
        await self.page.add_init_script("""
            () => {
                // Удаление webdriver свойства
                delete Object.getPrototypeOf(navigator).webdriver;
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Маскировка permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Маскировка плагинов
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                // Маскировка languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en', 'ru'],
                });
                
                // Маскировка chrome
                window.chrome = {
                    runtime: {}
                };
            }
        """)
        
        # Эмуляция реального браузера (дополнительный скрипт)
        await self.page.add_init_script("""
            () => {
                // Маскировка WebGL
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) {
                        return 'Intel Inc.';
                    }
                    if (parameter === 37446) {
                        return 'Intel Iris OpenGL Engine';
                    }
                    return getParameter.call(this, parameter);
                };
            }
        """)
        
        print("[PLAYWRIGHT-ADV] ✅ Стелс-режим активирован")
    
    async def _setup_resource_blocking(self):
        """⚡ Блокировка ненужных ресурсов для ускорения"""
        
        async def handle_route(route):
            # Блокируем ненужные типы ресурсов
            blocked_types = ['image', 'font', 'media']
            
            if route.request.resource_type in blocked_types:
                await route.abort()
            else:
                await route.continue_()
        
        await self.page.route("**/*", handle_route)
        print("[PLAYWRIGHT-ADV] ⚡ Блокировка ресурсов настроена")
    
    async def human_like_behavior(self, duration: int = 5):
        """🎭 Эмуляция человеческого поведения"""
        print(f"[PLAYWRIGHT-ADV] 🎭 Эмуляция человеческого поведения ({duration}с)...")
        
        actions = [
            "scroll_down",
            "scroll_up",
            "move_mouse",
            "wait"
        ]
        
        for _ in range(random.randint(3, 7)):
            action = random.choice(actions)
            
            if action == "scroll_down":
                await self.page.mouse.wheel(0, random.randint(100, 500))
            elif action == "scroll_up":
                await self.page.mouse.wheel(0, random.randint(-500, -100))
            elif action == "move_mouse":
                x = random.randint(100, 400)
                y = random.randint(100, 400)
                await self.page.mouse.move(x, y)
            elif action == "wait":
                await asyncio.sleep(random.uniform(0.5, 1.5))
            
            await asyncio.sleep(random.uniform(0.3, 1.0))
    
    async def close_instagram_modals(self):
        """🎯 Агрессивное закрытие модальных окон Instagram"""
        print("[PLAYWRIGHT-ADV] 🎯 Закрытие модальных окон...")
        
        # Метод 1: Клик по кнопкам
        modal_selectors = [
            "button[aria-label='Close']",
            "svg[aria-label='Close']",
            "button[aria-label='Закрыть']",
            "svg[aria-label='Закрыть']"
        ]
        
        for selector in modal_selectors:
            try:
                close_button = self.page.locator(selector).first
                if await close_button.count() > 0 and await close_button.is_visible():
                    await close_button.click()
                    print(f"[PLAYWRIGHT-ADV] ✅ Кнопка закрытия нажата: {selector}")
                    await asyncio.sleep(1)
            except Exception:
                pass
        
        # Метод 2: JavaScript удаление
        try:
            await self.page.evaluate("""
                () => {
                    // Удаляем все диалоги
                    const dialogs = document.querySelectorAll('[role="dialog"]');
                    dialogs.forEach(d => d.remove());
                    
                    // Удаляем overlay
                    const overlays = document.querySelectorAll('[class*="x7r02ix"], [class*="overlay"], [class*="backdrop"]');
                    overlays.forEach(o => o.remove());
                    
                    // Восстанавливаем body
                    document.body.style.overflow = 'auto';
                    document.body.style.position = 'static';
                    document.body.style.background = 'transparent';
                    document.documentElement.style.overflow = 'auto';
                }
            """)
            print("[PLAYWRIGHT-ADV] ✅ JavaScript удаление выполнено")
        except Exception as e:
            print(f"[PLAYWRIGHT-ADV] ⚠️ JavaScript ошибка: {e}")
        
        # Метод 3: Escape
        try:
            await self.page.keyboard.press('Escape')
            await self.page.keyboard.press('Escape')
            print("[PLAYWRIGHT-ADV] ⌨️ Escape нажат")
        except Exception:
            pass
        
        await asyncio.sleep(2)
    
    async def check_profile(self, username: str, screenshot_path: Optional[str] = None) -> Dict[str, Any]:
        """📊 Полная проверка профиля Instagram"""
        print(f"[PLAYWRIGHT-ADV] 📊 Проверка профиля: @{username}")
        
        try:
            # Переход на страницу
            url = f"https://www.instagram.com/{username}/"
            print(f"[PLAYWRIGHT-ADV] 🌐 Переход на: {url}")
            
            response = await self.page.goto(url, wait_until="networkidle", timeout=45000)
            status_code = response.status
            
            print(f"[PLAYWRIGHT-ADV] 📊 Статус код: {status_code}")
            
            # Ожидание загрузки
            await asyncio.sleep(random.uniform(3, 5))
            
            # Человекоподобное поведение
            await self.human_like_behavior(random.randint(3, 5))
            
            # Закрытие модальных окон
            await self.close_instagram_modals()
            
            # Дополнительное ожидание
            await asyncio.sleep(2)
            
            # Анализ страницы
            current_url = self.page.url
            page_content = await self.page.content()
            page_title = await self.page.title()
            
            print(f"[PLAYWRIGHT-ADV] 📋 Анализ:")
            print(f"[PLAYWRIGHT-ADV]   🔗 URL: {current_url}")
            print(f"[PLAYWRIGHT-ADV]   📝 Заголовок: {page_title}")
            print(f"[PLAYWRIGHT-ADV]   📄 Длина контента: {len(page_content)}")
            
            # Проверки существования
            checks = {
                "login_redirect": "accounts/login" in current_url,
                "profile_found": username.lower() in page_content.lower(),
                "error_404": any(msg in page_content.lower() for msg in [
                    "not found", "404", "страница не найдена", "sorry, this page"
                ]),
                "private_profile": any(msg in page_content.lower() for msg in [
                    "private", "закрытый", "this account is private"
                ]),
                "instagram_title": "instagram" in page_title.lower()
            }
            
            print(f"[PLAYWRIGHT-ADV] 📋 Результаты проверок: {checks}")
            
            # Определение существования
            exists = None
            reason = "undetermined"
            is_private = None
            
            if status_code == 404 or checks["error_404"]:
                exists = False
                reason = "page_not_found"
            elif checks["login_redirect"]:
                exists = True
                reason = "login_redirect"
            elif checks["private_profile"]:
                exists = True
                is_private = True
                reason = "private_profile"
            elif checks["profile_found"]:
                exists = True
                is_private = False
                reason = "profile_content"
            
            print(f"[PLAYWRIGHT-ADV] 📊 Итог: exists={exists}, private={is_private}, reason={reason}")
            
            # Скриншот
            screenshot_created = False
            if screenshot_path:
                try:
                    await self.page.screenshot(path=screenshot_path, full_page=False)
                    if os.path.exists(screenshot_path):
                        file_size = os.path.getsize(screenshot_path)
                        print(f"[PLAYWRIGHT-ADV] 📸 Скриншот: {screenshot_path} ({file_size} байт)")
                        screenshot_created = True
                except Exception as e:
                    print(f"[PLAYWRIGHT-ADV] ⚠️ Ошибка скриншота: {e}")
            
            return {
                "exists": exists,
                "is_private": is_private,
                "reason": reason,
                "status_code": status_code,
                "screenshot_path": screenshot_path if screenshot_created else None,
                "screenshot_created": screenshot_created,
                "checked_via": "playwright_advanced"
            }
        
        except Exception as e:
            print(f"[PLAYWRIGHT-ADV] ❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "exists": None,
                "is_private": None,
                "reason": f"error: {str(e)}",
                "status_code": None,
                "screenshot_path": None,
                "screenshot_created": False,
                "checked_via": "playwright_advanced"
            }
    
    async def close(self):
        """🔒 Закрытие ресурсов"""
        print("[PLAYWRIGHT-ADV] 🔒 Закрытие ресурсов...")
        
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        
        print("[PLAYWRIGHT-ADV] ✅ Ресурсы закрыты")


async def check_account_with_playwright_advanced(
    username: str,
    screenshot_path: Optional[str] = None,
    headless: bool = True,
    max_retries: int = 2,
    proxy: Optional[str] = None
) -> Dict[str, Any]:
    """
    🎭 Продвинутая проверка Instagram через Playwright
    
    Args:
        username: Instagram username
        screenshot_path: Path for screenshot
        headless: Run in headless mode
        max_retries: Maximum retry attempts
        proxy: Proxy URL (http://user:pass@host:port)
        
    Returns:
        Dict with check results
    """
    print(f"[PLAYWRIGHT-ADV-CHECK] 🎭 Запуск продвинутой проверки для @{username}")
    
    checker = InstagramPlaywrightAdvanced()
    
    for attempt in range(max_retries):
        print(f"[PLAYWRIGHT-ADV-CHECK] 🔄 Попытка {attempt + 1}/{max_retries}")
        
        try:
            # Инициализация
            success = await checker.initialize(proxy=proxy, headless=headless)
            if not success:
                print("[PLAYWRIGHT-ADV-CHECK] ❌ Не удалось инициализировать браузер")
                continue
            
            # Проверка профиля
            result = await checker.check_profile(username, screenshot_path)
            
            # Закрытие
            await checker.close()
            
            if result.get("exists") is not None:
                print(f"[PLAYWRIGHT-ADV-CHECK] ✅ Проверка завершена успешно")
                return {
                    "username": username,
                    "exists": result["exists"],
                    "is_private": result.get("is_private"),
                    "full_name": None,
                    "followers": None,
                    "following": None,
                    "posts": None,
                    "screenshot_path": result.get("screenshot_path"),
                    "error": None if result["exists"] is not None else result.get("reason"),
                    "checked_via": "playwright_advanced",
                    "proxy_used": bool(proxy),
                    "status_code": result.get("status_code"),
                    "screenshot_created": result.get("screenshot_created", False)
                }
            
            # Повторная попытка
            if attempt < max_retries - 1:
                delay = random.uniform(3, 7)
                print(f"[PLAYWRIGHT-ADV-CHECK] ⏳ Ожидание {delay:.1f}с...")
                await asyncio.sleep(delay)
        
        except Exception as e:
            print(f"[PLAYWRIGHT-ADV-CHECK] ❌ Ошибка: {e}")
            await checker.close()
            
            if attempt < max_retries - 1:
                delay = random.uniform(3, 7)
                await asyncio.sleep(delay)
    
    # Все попытки не удались
    print(f"[PLAYWRIGHT-ADV-CHECK] ❌ Все попытки не удались")
    return {
        "username": username,
        "exists": None,
        "is_private": None,
        "full_name": None,
        "followers": None,
        "following": None,
        "posts": None,
        "screenshot_path": None,
        "error": "Все попытки продвинутой проверки не удались",
        "checked_via": "playwright_advanced",
        "proxy_used": bool(proxy),
        "screenshot_created": False
    }

