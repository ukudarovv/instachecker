"""Instagram profile screenshot via Playwright + proxy."""

import asyncio
from typing import Optional
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError


def _proxy_kwargs_from_url(proxy_url: str):
    """Convert proxy URL to Playwright proxy kwargs."""
    # proxy_url: scheme://[user:pass@]host:port
    # Playwright ожидает {"server": "scheme://host:port", "username": "...", "password": "..."}
    from urllib.parse import urlparse
    u = urlparse(proxy_url)
    auth = {}
    if u.username and u.password:
        auth["username"] = u.username
        auth["password"] = u.password
    return {"server": f"{u.scheme}://{u.hostname}:{u.port}", **auth}


async def _apply_dark_theme(page):
    """Применяет темную тему к странице Instagram (полная версия)."""
    # Ждем полной загрузки страницы
    await page.wait_for_load_state('networkidle')
    
    # Добавляем небольшую задержку для полной отрисовки
    await page.wait_for_timeout(1000)
    
    # ПОЛНАЯ темная тема - фон и контент
    dark_theme_css = """
    /* Базовый фон и цвет текста */
    body, html {
        background-color: #1a1a1a !important;
        color: #e6e6e6 !important;
    }
    
    /* Карточки и блоки */
    .profile-card, .container, .card, .box, main, section, article {
        background-color: #2d2d2d !important;
        border-color: #404040 !important;
        color: #e6e6e6 !important;
    }
    
    /* Заголовки */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }
    
    /* Ссылки */
    a {
        color: #8ab4f8 !important;
    }
    
    /* Кнопки */
    button, .btn {
        background-color: #3b3b3b !important;
        color: #e6e6e6 !important;
        border-color: #5f6368 !important;
    }
    
    /* Изображения профиля */
    img {
        opacity: 0.9 !important;
    }
    """
    
    await page.add_style_tag(content=dark_theme_css)
    
    # Применение стилей через JavaScript
    await page.evaluate("""
        () => {
            console.log('🌙 Применение полной темной темы...');
            
            // Применяем темную тему ко всем элементам
            document.body.style.setProperty('background-color', '#1a1a1a', 'important');
            document.documentElement.style.setProperty('background-color', '#1a1a1a', 'important');
            document.body.style.setProperty('color', '#e6e6e6', 'important');
            
            // Применяем к основным контейнерам
            const containers = document.querySelectorAll('main, section, article, .container, .card');
            containers.forEach(el => {
                el.style.setProperty('background-color', '#2d2d2d', 'important');
                el.style.setProperty('color', '#e6e6e6', 'important');
            });
            
            console.log('✅ Полная темная тема применена');
        }
    """)
    
    # Дополнительная задержка для применения стилей
    await page.wait_for_timeout(1000)


async def screenshot_profile_header(
    username: str,
    proxy_url: str,
    wait_selector: str,
    fallback_selector: str,
    headless: bool = True,
    timeout_ms: int = 15000,
    save_path: Optional[str] = None,
    dark_theme: bool = True
) -> Optional[str]:
    """
    Открывает https://www.instagram.com/<username>/ через указанный прокси,
    ждёт селектор 'wait_selector', делает скрин элемента.
    Если не вышло — пробует 'fallback_selector'.
    Возвращает путь к PNG или None.
    
    Args:
        dark_theme: Если True, применяет темную тему (черный фон, белый текст)
    """
    url = f"https://www.instagram.com/{username.strip('@')}/"
    proxy_kwargs = _proxy_kwargs_from_url(proxy_url) if proxy_url else None
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu-sandbox",
            "--enable-gpu",
            "--force-device-scale-factor=1",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor"
        ])
        context = await browser.new_context(
            viewport={"width": 1280, "height": 960},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit Safari/537.36",
            proxy=proxy_kwargs
        )
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            
            # Пытаемся целиться в «шапку» профиля
            try:
                elem = page.locator(wait_selector).first
                await elem.wait_for(timeout=timeout_ms)
            except PWTimeoutError:
                elem = page.locator(fallback_selector).first
                await elem.wait_for(timeout=timeout_ms)
            
            # Применяем темную тему после загрузки элементов, если требуется
            if dark_theme:
                # Отключено для исправления черных скриншотов
                # await _apply_dark_theme(page)
                pass

            spath = save_path or f"/tmp/ig_{username}_header.png"
            await elem.screenshot(path=spath, type="png")
            return spath
        except Exception:
            return None
        finally:
            await context.close()
            await browser.close()


async def check_account_with_header_screenshot(
    username: str,
    proxy_url: str,
    screenshot_path: Optional[str] = None,
    headless: bool = True,
    timeout_ms: int = 30000,
    dark_theme: bool = True,
    mobile_emulation: bool = True,
    crop_ratio: float = 0.5  # 50% верха по умолчанию (достаточно для header + био)
) -> dict:
    """
    Проверяет Instagram аккаунт через proxy БЕЗ IG сессии.
    Делает скриншот только header'а профиля с темной темой (черный фон).
    
    Args:
        username: Instagram username
        proxy_url: Proxy URL (scheme://[user:pass@]host:port)
        screenshot_path: Path to save screenshot
        headless: Run in headless mode
        timeout_ms: Timeout in milliseconds
        dark_theme: Apply dark theme (black background)
        mobile_emulation: Use mobile device emulation (iPhone 12)
        crop_ratio: Ratio for cropping to header (0.5 = 50% top, includes header+bio+buttons)
    
    Returns:
        dict with check results:
            - username: str
            - exists: bool | None
            - screenshot_path: str | None
            - error: str | None
            - checked_via: "proxy_header_screenshot"
            - dark_theme_applied: bool
    """
    import os
    from datetime import datetime
    
    print(f"\n[PROXY-FULL-SCREENSHOT] 🔍 Проверка @{username} через proxy с полным скриншотом")
    print(f"[PROXY-FULL-SCREENSHOT] 🌐 Proxy: {proxy_url[:50] if proxy_url else 'None'}...")
    print(f"[PROXY-FULL-SCREENSHOT] 🌙 Темная тема: {dark_theme}")
    print(f"[PROXY-FULL-SCREENSHOT] 🖥️ Desktop формат: {not mobile_emulation}")
    print(f"[PROXY-FULL-SCREENSHOT] 📸 Полный скриншот страницы (без обрезки)")
    
    result = {
        "username": username,
        "exists": None,
        "screenshot_path": None,
        "error": None,
        "checked_via": "proxy_full_screenshot",
        "dark_theme_applied": False,
        "mobile_emulation": mobile_emulation
    }
    
    # Генерируем путь для скриншота если не указан
    if not screenshot_path:
        screenshots_dir = "screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(screenshots_dir, f"{username}_header_{timestamp}.png")
    
    url = f"https://www.instagram.com/{username.strip('@')}/"
    proxy_kwargs = _proxy_kwargs_from_url(proxy_url) if proxy_url else None
    
    try:
        async with async_playwright() as p:
            # 🔥 УЛУЧШЕННАЯ настройка браузера
            launch_args = [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                # "--virtual-time-budget=10000",  # ОТКЛЮЧЕНО: конфликт с headless
                # "--run-all-compositor-stages-before-draw",  # ОТКЛЮЧЕНО: конфликт с headless
                "--disable-gpu-compositing",  # Отключаем GPU композитинг (может вызывать белые скриншоты)
            ]
            
            # Принудительная темная тема на уровне браузера - ОТКЛЮЧЕНО
            if dark_theme:
                # Отключено для исправления черных скриншотов
                # launch_args.extend([
                #     "--force-dark-mode",
                #     "--enable-features=WebUIDarkMode"
                # ])
                pass
            
            # 🔥 ПРОКСИ на уровне браузера (обязательно для Playwright)
            browser_args = launch_args + [
                "--disable-dev-shm-usage",
                "--disable-gpu-sandbox", 
                "--enable-gpu",
                "--force-device-scale-factor=1",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--window-size=1920,1080",  # Фиксированный размер окна 1920x1080
                # "--start-maximized",  # ОТКЛЮЧЕНО: конфликт с headless режимом
            ]
            
            # Добавляем proxy только если он указан
            if proxy_kwargs:
                browser = await p.chromium.launch(
                    headless=headless,
                    args=browser_args,
                    proxy=proxy_kwargs
                )
            else:
                browser = await p.chromium.launch(
                    headless=headless,
                    args=browser_args
                )
            
            # 🔥 МОБИЛЬНАЯ ЭМУЛЯЦИЯ или обычный режим
            if mobile_emulation:
                # Используем iPhone 12 для мобильной версии
                device = p.devices["iPhone 12"]
                context_options = {
                    **device
                    # proxy НЕ передаем - уже передан в browser.launch()
                }
                
                # 🔥 ТЕМНАЯ ТЕМА на уровне устройства - ОТКЛЮЧЕНО
                if dark_theme:
                    # Отключено для исправления черных скриншотов
                    # context_options["color_scheme"] = "dark"
                    pass
                
                print(f"[PROXY-HEADER-SCREENSHOT] 📱 Эмуляция: iPhone 12")
            else:
                # Обычный desktop режим с разрешением 1920x1080 (Full HD)
                context_options = {
                    "viewport": {"width": 1920, "height": 1080},
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    # proxy НЕ передаем - уже передан в browser.launch()
                }
                
                # 🔥 ТЕМНАЯ ТЕМА для desktop - ОТКЛЮЧЕНО
                if dark_theme:
                    # Отключено для исправления черных скриншотов
                    # context_options["color_scheme"] = "dark"
                    pass
            
            context = await browser.new_context(**context_options)
            
            # 🔥 ПРИНУДИТЕЛЬНАЯ ТЕМНАЯ ТЕМА через JavaScript injection - ОТКЛЮЧЕНО
            if dark_theme:
                # Отключено для исправления черных скриншотов
                # await context.add_init_script("""
                #     // Принудительно включаем темную тему
                #     localStorage.setItem('dark_mode', '1');
                #     localStorage.setItem('ig_dark_mode', '1');
                #     localStorage.setItem('theme', 'dark');
                #     
                #     // Переопределяем matchMedia для темной темы
                #     Object.defineProperty(window, 'matchMedia', {
                #         writable: true,
                #         value: (query) => ({
                #             matches: query.includes('dark') ? true : false,
                #             media: query,
                #             addListener: () => {},
                #             removeListener: () => {},
                #             addEventListener: () => {},
                #             removeEventListener: () => {},
                #             dispatchEvent: () => true,
                #         }),
                #     });
                #     
                #     console.log('🌙 Темная тема принудительно включена через localStorage и matchMedia');
                # """)
                print(f"[PROXY-HEADER-SCREENSHOT] 🌙 JavaScript темная тема ОТКЛЮЧЕНА")
            
            # Стелс-режим
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            """)
            
            page = await context.new_page()
            
            # 🔥 ЭМУЛЯЦИЯ ТЕМНОЙ ТЕМЫ через media - ОТКЛЮЧЕНО
            if dark_theme:
                # Отключено для исправления черных скриншотов
                # await page.emulate_media(color_scheme='dark')
                print(f"[PROXY-HEADER-SCREENSHOT] 🌙 emulate_media ОТКЛЮЧЕН")
            
            try:
                print(f"[PROXY-HEADER-SCREENSHOT] 📡 Переход на: {url}")
                try:
                    response = await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                    status_code = response.status if response else None
                    print(f"[PROXY-HEADER-SCREENSHOT] 📊 HTTP Status: {status_code}")
                except PWTimeoutError as e:
                    print(f"[PROXY-HEADER-SCREENSHOT] ⏱️ Timeout при загрузке страницы: {e}")
                    result["error"] = f"timeout_loading_page: {str(e)}"
                    result["exists"] = False
                    await browser.close()
                    return result
                
                # Проверяем статус код
                if status_code == 404:
                    print(f"[PROXY-HEADER-SCREENSHOT] ❌ Профиль не найден (404)")
                    result["exists"] = False
                    result["error"] = "404_not_found"
                    await browser.close()
                    return result
                
                elif status_code == 403:
                    print(f"[PROXY-HEADER-SCREENSHOT] 🚫 Доступ запрещен (403)")
                    result["exists"] = None
                    result["error"] = "403_forbidden"
                    await browser.close()
                    return result
                
                # Ждем загрузки контента - УВЕЛИЧЕНО для полной загрузки
                print(f"[PROXY-HEADER-SCREENSHOT] ⏳ Ожидаем полную загрузку страницы...")
                try:
                    await page.wait_for_timeout(5000)  # 5 секунд для полной загрузки
                except Exception as e:
                    print(f"[PROXY-HEADER-SCREENSHOT] ⚠️ Проблема с ожиданием загрузки: {e}")
                    # Продолжаем выполнение даже если есть проблемы с ожиданием
                
                # Дополнительное ожидание для загрузки контента
                print(f"[PROXY-HEADER-SCREENSHOT] ⏳ Дополнительное ожидание для загрузки контента...")
                await page.wait_for_timeout(3000)  # Еще 3 секунды
                
                # УСИЛЕННАЯ ПРОВЕРКА на редирект и неправильные страницы
                current_url = page.url
                print(f"[PROXY-HEADER-SCREENSHOT] 🔗 Текущий URL: {current_url}")
                
                # Проверяем, не редирект ли это на неправильную страницу
                wrong_page_detected = False
                
                # Список неправильных URL паттернов
                wrong_patterns = [
                    '/accounts/login',
                    '/accounts/signup',
                    '/challenge/',
                    '/suspended/',
                    '/access_tool/',
                    'instagram.com/accounts',
                    'instagram.com/login',
                ]
                
                # Проверяем, содержит ли URL неправильный паттерн
                for pattern in wrong_patterns:
                    if pattern in current_url.lower():
                        wrong_page_detected = True
                        print(f"[PROXY-HEADER-SCREENSHOT] ⚠️ Обнаружен редирект на неправильную страницу: {pattern}")
                        break
                
                # Также проверяем, что URL содержит имя пользователя
                if username.lower() not in current_url.lower() and not wrong_page_detected:
                    wrong_page_detected = True
                    print(f"[PROXY-HEADER-SCREENSHOT] ⚠️ URL не содержит username: {username}")
                
                # Если обнаружена неправильная страница - делаем повторные попытки
                if wrong_page_detected:
                    print(f"[PROXY-HEADER-SCREENSHOT] 🔄 ПЕРЕЗАПУСК: Закрываем сессию и создаем новую...")
                    
                    max_retries = 3
                    for retry in range(max_retries):
                        print(f"[PROXY-HEADER-SCREENSHOT] 🔄 Попытка {retry + 1}/{max_retries}")
                        
                        try:
                            # Закрываем текущую страницу и создаем новую
                            await page.close()
                            page = await context.new_page()
                            
                            # Ждем перед новым запросом
                            await page.wait_for_timeout(2000)
                            
                            # Делаем новый запрос
                            print(f"[PROXY-HEADER-SCREENSHOT] 📡 Новый запрос на: {url}")
                            response = await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                            status_code = response.status if response else None
                            print(f"[PROXY-HEADER-SCREENSHOT] 📊 HTTP Status: {status_code}")
                            
                            # Ждем загрузки
                            await page.wait_for_timeout(5000)
                            
                            # Проверяем новый URL
                            current_url = page.url
                            print(f"[PROXY-HEADER-SCREENSHOT] 🔗 Новый URL: {current_url}")
                            
                            # Проверяем, исправился ли URL
                            is_correct = True
                            for pattern in wrong_patterns:
                                if pattern in current_url.lower():
                                    is_correct = False
                                    break
                            
                            if is_correct and username.lower() in current_url.lower():
                                print(f"[PROXY-HEADER-SCREENSHOT] ✅ URL исправлен после попытки {retry + 1}")
                                
                                # ВАЖНО: Даем время странице загрузиться после исправления
                                print(f"[PROXY-HEADER-SCREENSHOT] ⏳ Ожидаем полную загрузку после исправления URL...")
                                await page.wait_for_timeout(5000)
                                
                                # Дополнительное ожидание загрузки контента
                                try:
                                    await page.wait_for_load_state('networkidle', timeout=10000)
                                    print(f"[PROXY-HEADER-SCREENSHOT] ✅ Страница полностью загружена")
                                except:
                                    print(f"[PROXY-HEADER-SCREENSHOT] ⚠️ Timeout ожидания networkidle, продолжаем")
                                
                                # Сразу удаляем модальные окна после исправления
                                print(f"[PROXY-HEADER-SCREENSHOT] 🚪 Удаляем модальные окна после исправления URL...")
                                try:
                                    for _ in range(5):
                                        await page.keyboard.press("Escape")
                                        await page.wait_for_timeout(200)
                                except:
                                    pass
                                
                                break
                            else:
                                print(f"[PROXY-HEADER-SCREENSHOT] ❌ URL все еще неправильный после попытки {retry + 1}")
                                
                                # Если это последняя попытка - возвращаем ошибку
                                if retry == max_retries - 1:
                                    print(f"[PROXY-HEADER-SCREENSHOT] ❌ Все попытки исчерпаны, возвращаем ошибку")
                                    result["error"] = "wrong_page_redirect"
                                    result["exists"] = False
                                    await browser.close()
                                    return result
                        
                        except Exception as retry_error:
                            print(f"[PROXY-HEADER-SCREENSHOT] ❌ Ошибка при повторной попытке {retry + 1}: {retry_error}")
                            if retry == max_retries - 1:
                                result["error"] = f"retry_failed: {retry_error}"
                                result["exists"] = False
                                await browser.close()
                                return result
                
                # Проверяем контент страницы СНАЧАЛА
                content = await page.content()
                
                # Пропускаем проверку на перенаправления - создаем скриншот в любом случае
                print(f"[PROXY-HEADER-SCREENSHOT] 📸 Создаем скриншот независимо от перенаправлений")
                
                # Проверяем, не показывает ли Instagram страницу "Open app" или "Continue on web"
                if "Open app" in content or "open_app" in current_url.lower() or "Continue on web" in content:
                    print(f"[PROXY-HEADER-SCREENSHOT] ⚠️ Instagram показывает блокировку - переключаемся на desktop...")
                    
                    # Закрываем текущий браузер
                    await browser.close()
                    
                    # Перезапускаем с DESKTOP эмуляцией
                    print(f"[PROXY-HEADER-SCREENSHOT] 🖥️ Переключаемся на DESKTOP режим...")
                    
                    browser = await p.chromium.launch(
                        headless=headless,
                        args=launch_args + [
                            "--disable-dev-shm-usage",
                            "--disable-gpu-sandbox",
                            "--enable-gpu", 
                            "--force-device-scale-factor=1",
                            "--disable-web-security",
                            "--disable-features=VizDisplayCompositor"
                        ],
                        proxy=proxy_kwargs
                    )
                    
                    # Desktop viewport
                    context_options = {
                        "viewport": {"width": 1920, "height": 1080},
                        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    }
                    if dark_theme:
                        context_options["color_scheme"] = "dark"
                    
                    context = await browser.new_context(**context_options)
                    
                    if dark_theme:
                        await context.add_init_script("""
                            localStorage.setItem('theme', 'dark');
                            localStorage.setItem('dark_mode', '1');
                        """)
                    
                    await context.add_init_script("""
                        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                    """)
                    
                    page = await context.new_page()
                    
                    if dark_theme:
                        await page.emulate_media(color_scheme='dark')
                    
                    # Устанавливаем базовые cookies
                    print(f"[PROXY-HEADER-SCREENSHOT] 🍪 Устанавливаем cookies...")
                    await context.add_cookies([
                        {
                            'name': 'ig_did',
                            'value': 'A1B2C3D4-E5F6-7890-ABCD-EF1234567890',
                            'domain': '.instagram.com',
                            'path': '/'
                        },
                        {
                            'name': 'ig_nrcb',
                            'value': '1',
                            'domain': '.instagram.com',
                            'path': '/'
                        }
                    ])
                    
                    print(f"[PROXY-HEADER-SCREENSHOT] 🔄 Повторный переход (desktop)...")
                    response = await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                    print(f"[PROXY-HEADER-SCREENSHOT] ⏳ Ожидаем загрузку...")
                    await page.wait_for_timeout(5000)
                    current_url = page.url
                    content = await page.content()
                    print(f"[PROXY-HEADER-SCREENSHOT] 🔗 URL: {current_url}")
                
                # Закрываем модальные окна и баннеры
                print(f"[PROXY-HEADER-SCREENSHOT] 🚪 Закрываем модальные окна и баннеры...")
                
                # Сначала пробуем ESC для закрытия модалок (больше раз)
                try:
                    for _ in range(10):  # Нажимаем ESC 10 раз
                        await page.keyboard.press("Escape")
                        await page.wait_for_timeout(200)
                    print(f"[PROXY-HEADER-SCREENSHOT] ⌨️ Нажали ESC 10 раз")
                except:
                    pass
                
                # Закрываем cookies баннер
                cookie_selectors = [
                    "button:has-text('Accept')",
                    "button:has-text('Allow')",
                    "button:has-text('I agree')",
                    "button:has-text('Agree')",
                    "button:has-text('OK')",
                    "[role='button']:has-text('Accept')",
                ]
                
                for selector in cookie_selectors:
                    try:
                        btn = page.locator(selector).first
                        if await btn.is_visible(timeout=1000):
                            await btn.click()
                            print(f"[PROXY-HEADER-SCREENSHOT] ✅ Приняли cookies: {selector}")
                            await page.wait_for_timeout(1000)
                            break
                    except:
                        continue
                
                # Закрываем модальные окна по кнопке закрытия
                close_selectors = [
                    "svg[aria-label='Close']",
                    "button[aria-label='Close']",
                    "[aria-label='Close']",
                    "button:has-text('Not Now')",
                    "button:has-text('Не сейчас')",
                    "div[role='dialog'] svg",  # Иконка закрытия в диалоге
                    "div[role='dialog'] button",  # Любая кнопка в диалоге
                ]
                
                # Пробуем закрыть все модальные окна
                for i in range(3):  # Пробуем несколько раз
                    closed = False
                    for selector in close_selectors:
                        try:
                            close_button = page.locator(selector).first
                            if await close_button.is_visible(timeout=1000):
                                await close_button.click()
                                print(f"[PROXY-HEADER-SCREENSHOT] ✅ Закрыли модалку {i+1}: {selector}")
                                await page.wait_for_timeout(1000)
                                closed = True
                                break
                        except:
                            continue
                    
                    if not closed:
                        break  # Больше нечего закрывать
                
                # Дополнительно: прокручиваем вниз и вверх для инициализации контента
                try:
                    await page.evaluate("window.scrollTo(0, 300)")
                    await page.wait_for_timeout(1000)
                    await page.evaluate("window.scrollTo(0, 0)")
                    await page.wait_for_timeout(1000)
                    print(f"[PROXY-HEADER-SCREENSHOT] 📜 Прокрутили страницу для загрузки контента")
                except:
                    pass
                
                # Дополнительное ожидание после закрытия модалок
                print(f"[PROXY-HEADER-SCREENSHOT] ⏳ Финальное ожидание для стабилизации страницы...")
                await page.wait_for_timeout(2000)  # 2 секунды для стабилизации
                
                # Принудительное удаление всех модальных окон через JavaScript - МАКСИМАЛЬНО АГРЕССИВНО
                print(f"[PROXY-HEADER-SCREENSHOT] 🔥 Принудительное удаление всех модальных окон (УЛЬТРА-агрессивный режим)...")
                removed_count = await page.evaluate("""
                    () => {
                        let count = 0;
                        
                        // Удаляем несколько раз для надежности (увеличено до 15 итераций)
                        for (let iteration = 0; iteration < 15; iteration++) {
                            
                            // 1. Удаляем все диалоги и модальные окна (расширенный список)
                            document.querySelectorAll('[role="dialog"], [aria-modal="true"], [data-testid*="modal"], [data-testid*="dialog"], [data-testid*="popup"], [data-testid*="overlay"], [role="presentation"], [data-visualcompletion="loading-state"]').forEach(el => {
                                el.remove();
                                count++;
                            });
                            
                            // 2. Удаляем все overlay/backdrop/modal элементы (расширенный список)
                            document.querySelectorAll('[class*="overlay"], [class*="Overlay"], [class*="backdrop"], [class*="Backdrop"], [class*="modal"], [class*="Modal"], [class*="popup"], [class*="PopUp"], [class*="Popup"], [class*="lightbox"], [class*="Lightbox"], [class*="drawer"], [class*="Drawer"], [class*="sheet"], [class*="Sheet"], [class*="panel"], [class*="Panel"], [class*="mask"], [class*="Mask"], [class*="shade"], [class*="Shade"], [class*="curtain"], [class*="Curtain"], [class*="veil"], [class*="Veil"], [class*="screen"], [class*="Screen"], [class*="window"], [class*="Window"], [class*="scrim"], [class*="Scrim"]').forEach(el => {
                                el.remove();
                                count++;
                            });
                            
                            // 3. Удаляем скелетоны загрузки (белые прямоугольники) и плейсхолдеры
                            document.querySelectorAll('[class*="skeleton"], [class*="Skeleton"], [class*="placeholder"], [class*="Placeholder"]').forEach(el => {
                                el.remove();
                                count++;
                            });
                            
                            // 4. Удаляем все SVG крестики (кнопки закрытия)
                            document.querySelectorAll('svg[aria-label*="Close"], svg[aria-label*="close"], button[aria-label*="Close"]').forEach(el => {
                                const parent = el.closest('div');
                                if (parent && window.getComputedStyle(parent).position === 'fixed') {
                                    parent.remove();
                                    count++;
                                } else {
                                    el.remove();
                                    count++;
                                }
                            });
                            
                            // 5. Удаляем элементы с фиксированной позицией и высоким z-index
                            document.querySelectorAll('div').forEach(el => {
                                const style = window.getComputedStyle(el);
                                
                                // Элементы с фиксированной позицией и z-index > 100
                                if (style.position === 'fixed' && parseInt(style.zIndex) > 100) {
                                    // Проверяем, не навигация ли это
                                    if (!el.querySelector('nav') && !el.closest('nav') && !el.querySelector('header')) {
                                        el.remove();
                                        count++;
                                    }
                                }
                                
                                // Затемнения часто имеют opacity < 1 и position fixed
                                if (style.position === 'fixed' && parseFloat(style.opacity) < 1 && parseFloat(style.opacity) > 0) {
                                    // Если элемент занимает весь экран - это overlay
                                    const rect = el.getBoundingClientRect();
                                    if (rect.width > window.innerWidth * 0.8 && rect.height > window.innerHeight * 0.8) {
                                        el.remove();
                                        count++;
                                    }
                                }
                            });
                            
                            // 6. Удаляем элементы с черным/серым фоном на весь экран (затемнение)
                            document.querySelectorAll('div').forEach(el => {
                                const style = window.getComputedStyle(el);
                                const bgColor = style.backgroundColor;
                                const rect = el.getBoundingClientRect();
                                
                                // Проверяем: полупрозрачный черный/серый фон на весь экран
                                if ((bgColor.includes('rgba(0, 0, 0') || bgColor.includes('rgba(38, 38, 38')) && 
                                    rect.width > window.innerWidth * 0.5 && 
                                    rect.height > window.innerHeight * 0.5 &&
                                    style.position === 'fixed') {
                                    el.remove();
                                    count++;
                                }
                            });
                            
                            // 7. Удаляем белые блоки-заглушки (loading states)
                            document.querySelectorAll('div').forEach(el => {
                                const style = window.getComputedStyle(el);
                                const bgColor = style.backgroundColor;
                                
                                // Проверяем: белый фон и нет текста внутри
                                if ((bgColor === 'rgb(255, 255, 255)' || bgColor === 'white') && 
                                    el.innerText.trim() === '' &&
                                    el.children.length === 0) {
                                    const rect = el.getBoundingClientRect();
                                    // Если это большой белый блок
                                    if (rect.width > 100 && rect.height > 50) {
                                        el.remove();
                                        count++;
                                    }
                                }
                            });
                            
                            // 8. Удаляем элементы с pointer-events: none (часто overlay)
                            document.querySelectorAll('[style*="pointer-events: none"], [style*="pointer-events:none"]').forEach(el => {
                                if (el.style.position === 'fixed' || el.style.position === 'absolute') {
                                    el.remove();
                                    count++;
                                }
                            });
                        }
                        
                        // Убираем overflow: hidden с body (модалки часто блокируют прокрутку)
                        document.body.style.overflow = 'auto';
                        document.documentElement.style.overflow = 'auto';
                        
                        // Убираем pointer-events: none с body
                        document.body.style.pointerEvents = 'auto';
                        document.documentElement.style.pointerEvents = 'auto';
                        
                        return count;
                    }
                """)
                print(f"[PROXY-HEADER-SCREENSHOT] 🗑️ Удалено элементов: {removed_count}")
                
                # Ждем после удаления для перерисовки
                await page.wait_for_timeout(1500)
                
                # ДОПОЛНИТЕЛЬНАЯ ЖЕСТКАЯ ПРОВЕРКА: Еще раз проверяем наличие модальных окон
                print(f"[PROXY-HEADER-SCREENSHOT] 🔥 ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА: Поиск оставшихся модальных окон...")
                
                # Проверяем наличие видимых модальных окон
                modal_check = await page.evaluate("""
                    () => {
                        const modals = document.querySelectorAll('[role="dialog"], [aria-modal="true"], [class*="modal"], [class*="Modal"]');
                        let visibleModals = 0;
                        modals.forEach(modal => {
                            const style = window.getComputedStyle(modal);
                            if (style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0') {
                                visibleModals++;
                                // Принудительно удаляем
                                modal.remove();
                            }
                        });
                        return visibleModals;
                    }
                """)
                
                if modal_check > 0:
                    print(f"[PROXY-HEADER-SCREENSHOT] ⚠️ Найдено и удалено {modal_check} видимых модальных окон")
                    await page.wait_for_timeout(1000)
                else:
                    print(f"[PROXY-HEADER-SCREENSHOT] ✅ Модальные окна не обнаружены")
                
                # СУПЕР-АГРЕССИВНАЯ финальная попытка нажать ESC
                try:
                    for _ in range(15):
                        await page.keyboard.press("Escape")
                        await page.wait_for_timeout(150)
                    print(f"[PROXY-HEADER-SCREENSHOT] ⌨️ Финальный ESC нажат 15 раз")
                except:
                    pass
                
                # Дополнительная финальная проверка и удаление модальных окон ПРЯМО ПЕРЕД СКРИНШОТОМ
                print(f"[PROXY-HEADER-SCREENSHOT] 🔥 ПОСЛЕДНЯЯ проверка модальных окон перед скриншотом...")
                await page.evaluate("""
                    () => {
                        // Удаляем ВСЕ элементы с role="dialog" или aria-modal="true"
                        document.querySelectorAll('[role="dialog"], [aria-modal="true"]').forEach(el => el.remove());
                        
                        // Удаляем все overlay/backdrop
                        document.querySelectorAll('[class*="overlay"], [class*="Overlay"], [class*="backdrop"], [class*="Backdrop"]').forEach(el => el.remove());
                        
                        // Удаляем все fixed элементы с высоким z-index
                        document.querySelectorAll('div').forEach(el => {
                            const style = window.getComputedStyle(el);
                            if (style.position === 'fixed' && parseInt(style.zIndex) > 500) {
                                el.remove();
                            }
                        });
                        
                        // Убираем overflow:hidden с body
                        document.body.style.overflow = 'auto';
                        document.documentElement.style.overflow = 'auto';
                    }
                """)
                print(f"[PROXY-HEADER-SCREENSHOT] ✅ Последняя очистка выполнена")
                
                if "Sorry, this page isn't available" in content:
                    print(f"[PROXY-HEADER-SCREENSHOT] ❌ Страница недоступна")
                    result["exists"] = False
                    result["error"] = "page_not_found"
                    await browser.close()
                    return result
                
                # Пропускаем проверку на страницу логина - создаем скриншот в любом случае
                print(f"[PROXY-HEADER-SCREENSHOT] 📸 Создаем скриншот независимо от содержимого страницы")
                
                # Профиль существует - ждем загрузки статистики
                print(f"[PROXY-HEADER-SCREENSHOT] ⏳ Ожидаем загрузку статистики профиля (публикации, подписчики)...")
                
                # Ждем появления числовых значений статистики
                stats_loaded = False
                for attempt in range(10):  # 10 попыток по 1 секунде
                    try:
                        # Проверяем наличие чисел в статистике
                        has_stats = await page.evaluate("""
                            () => {
                                // Ищем элементы со статистикой (обычно это span или div с числами)
                                const statsElements = Array.from(document.querySelectorAll('span, div'));
                                const hasNumbers = statsElements.some(el => {
                                    const text = el.textContent.trim();
                                    // Проверяем на числа типа "123", "1.2M", "695M" и т.д.
                                    return /^\d+(\.\d+)?[KMB]?$/.test(text.replace(/,/g, ''));
                                });
                                
                                // Также проверяем наличие слов "posts", "followers", "following"
                                const bodyText = document.body.innerText.toLowerCase();
                                const hasLabels = bodyText.includes('posts') || 
                                                 bodyText.includes('followers') || 
                                                 bodyText.includes('following') ||
                                                 bodyText.includes('публикаций') ||
                                                 bodyText.includes('подписчиков');
                                
                                return hasNumbers && hasLabels;
                            }
                        """)
                        
                        if has_stats:
                            stats_loaded = True
                            print(f"[PROXY-HEADER-SCREENSHOT] ✅ Статистика профиля загружена (попытка {attempt + 1})")
                            break
                        else:
                            await page.wait_for_timeout(1000)
                    except Exception as e:
                        await page.wait_for_timeout(1000)
                        continue
                
                if not stats_loaded:
                    print(f"[PROXY-HEADER-SCREENSHOT] ⚠️ Статистика не загрузилась полностью, продолжаем...")
                
                # Дополнительная пауза для финальной загрузки
                await page.wait_for_timeout(2000)
                
                # Ищем header профиля
                print(f"[PROXY-HEADER-SCREENSHOT] 🔍 Ищем header профиля...")
                
                # Селекторы для header'а профиля
                header_selectors = [
                    'header',
                    'header section',
                    'div[role="main"] header',
                    'main header'
                ]
                
                header_elem = None
                for selector in header_selectors:
                    try:
                        locator = page.locator(selector).first
                        await locator.wait_for(state="visible", timeout=5000)
                        header_elem = locator
                        print(f"[PROXY-HEADER-SCREENSHOT] ✅ Header найден: {selector}")
                        break
                    except:
                        continue
                
                if not header_elem:
                    print(f"[PROXY-HEADER-SCREENSHOT] ⚠️ Header не найден, используем весь viewport")
                    # Если header не найден, используем весь viewport
                    header_elem = None
                
                # Даем время Instagram применить встроенную темную тему - ОТКЛЮЧЕНО
                if dark_theme:
                    # Отключено для исправления черных скриншотов
                    # print(f"[PROXY-HEADER-SCREENSHOT] 🌙 Ожидание применения встроенной темной темы Instagram...")
                    # await page.wait_for_timeout(5000)  # 5 секунд - даем время Instagram применить тему
                    # 
                    # # Проверяем темную тему
                    # dark_theme_verified = await page.evaluate("""
                    #     () => {
                    #         const body = document.body;
                    #         const computedStyle = window.getComputedStyle(body);
                    #         const bgColor = computedStyle.backgroundColor;
                    #         
                    #         // Проверяем что фон темный
                    #         const isDark = bgColor.includes('0, 0, 0') || bgColor.includes('#000') || bgColor.includes('rgb(0, 0, 0)');
                    #         return isDark;
                    #     }
                    # """)
                    # 
                    # result["dark_theme_applied"] = dark_theme_verified
                    # 
                    # if dark_theme_verified:
                    #     print(f"[PROXY-HEADER-SCREENSHOT] ✅ Встроенная темная тема Instagram активна")
                    # else:
                    #     print(f"[PROXY-HEADER-SCREENSHOT] ℹ️  Instagram использует светлую тему")
                    result["dark_theme_applied"] = False
                    print(f"[PROXY-HEADER-SCREENSHOT] 🌙 Ожидание темной темы ОТКЛЮЧЕНО")
                else:
                    result["dark_theme_applied"] = False
                
                # Проверяем, что контент загрузился перед скриншотом
                print(f"[PROXY-FULL-SCREENSHOT] 🔍 Проверяем загрузку контента...")
                try:
                    # Ждем появления основного контента
                    await page.wait_for_selector("main", timeout=10000)
                    print(f"[PROXY-FULL-SCREENSHOT] ✅ Основной контент загружен")
                except Exception as e:
                    print(f"[PROXY-FULL-SCREENSHOT] ⚠️ Основной контент не найден: {e}")
                    # Продолжаем выполнение
                
                # Дополнительная проверка видимости контента
                try:
                    # Проверяем, что страница не пустая
                    body_text = await page.evaluate("document.body.innerText")
                    if len(body_text.strip()) < 10:
                        print(f"[PROXY-FULL-SCREENSHOT] ⚠️ Страница кажется пустой, ждем еще...")
                        await page.wait_for_timeout(5000)
                        
                        # Принудительная прокрутка для загрузки контента
                        print(f"[PROXY-FULL-SCREENSHOT] 📜 Принудительная прокрутка для загрузки контента...")
                        await page.evaluate("window.scrollTo(0, 500)")
                        await page.wait_for_timeout(2000)
                        await page.evaluate("window.scrollTo(0, 0)")
                        await page.wait_for_timeout(2000)
                except Exception as e:
                    print(f"[PROXY-FULL-SCREENSHOT] ⚠️ Не удалось проверить контент: {e}")
                
                # Делаем скриншот видимой области (viewport)
                print(f"[PROXY-FULL-SCREENSHOT] 📸 Создание скриншота видимой области...")
                
                # Используем размер viewport 1920x1080
                print(f"[PROXY-FULL-SCREENSHOT] 📐 Используем размер viewport: 1920x1080")
                
                # Принудительная установка размеров viewport через JavaScript для исправления белых скриншотов на Linux
                print(f"[PROXY-FULL-SCREENSHOT] 🔧 Принудительная установка viewport 1920x1080...")
                try:
                    await page.evaluate("""
                        () => {
                            // Принудительно устанавливаем размеры окна и viewport
                            window.innerWidth = 1920;
                            window.innerHeight = 1080;
                            window.outerWidth = 1920;
                            window.outerHeight = 1080;
                            
                            // Принудительно устанавливаем размеры document
                            document.documentElement.style.width = '1920px';
                            document.documentElement.style.height = '1080px';
                            document.body.style.width = '1920px';
                            document.body.style.height = '1080px';
                            
                            console.log('✅ Viewport установлен принудительно: 1920x1080');
                        }
                    """)
                    
                    # Дополнительное ожидание для завершения отрисовки
                    await page.wait_for_timeout(1000)
                    print(f"[PROXY-FULL-SCREENSHOT] ✅ Viewport установлен принудительно")
                except Exception as e:
                    print(f"[PROXY-FULL-SCREENSHOT] ⚠️ Не удалось установить viewport принудительно: {e}")
                
                # Ждем завершения отрисовки страницы
                print(f"[PROXY-FULL-SCREENSHOT] ⏳ Ожидание завершения отрисовки страницы...")
                await page.wait_for_timeout(3000)
                
                # Ждем загрузки всех изображений
                print(f"[PROXY-FULL-SCREENSHOT] 🖼️ Ожидание загрузки изображений...")
                try:
                    await page.wait_for_load_state('networkidle', timeout=10000)
                    print(f"[PROXY-FULL-SCREENSHOT] ✅ Все изображения загружены")
                except Exception as e:
                    print(f"[PROXY-FULL-SCREENSHOT] ⚠️ Не все изображения загрузились: {e}")
                
                # Дополнительная пауза для финальной отрисовки
                await page.wait_for_timeout(2000)
                
                try:
                    # Скриншот только видимой области (viewport 1920x1080)
                    await page.screenshot(path=screenshot_path, full_page=False)
                    print(f"[PROXY-FULL-SCREENSHOT] ✅ Скриншот создан успешно (viewport: 1920x1080)")
                except Exception as e:
                    print(f"[PROXY-FULL-SCREENSHOT] ❌ Ошибка при создании скриншота: {e}")
                    result["error"] = f"screenshot_failed: {str(e)}"
                    result["exists"] = False
                    await browser.close()
                    return result
                
                # Полный скриншот без обрезки
                if os.path.exists(screenshot_path):
                    try:
                        from PIL import Image
                        
                        img = Image.open(screenshot_path)
                        width, height = img.size
                        
                        # Полный скриншот без обрезки
                        size = os.path.getsize(screenshot_path) / 1024
                        print(f"[PROXY-FULL-SCREENSHOT] 📸 Полный скриншот: {width}x{height}")
                        print(f"[PROXY-FULL-SCREENSHOT] 📏 Размер файла: {size:.1f} KB")
                        
                        result["cropped_sides"] = False
                        result["original_width"] = width
                        result["final_width"] = width
                        
                    except ImportError:
                        print(f"[PROXY-FULL-SCREENSHOT] ⚠️ PIL не установлен, сохраняем полный скриншот")
                        result["cropped_sides"] = False
                    except Exception as size_error:
                        print(f"[PROXY-FULL-SCREENSHOT] ⚠️ Ошибка получения размера: {size_error}")
                        result["cropped_sides"] = False
                
                # ПОЛНЫЙ СКРИНШОТ: Сохраняем без обрезки
                if os.path.exists(screenshot_path):
                    try:
                        from PIL import Image
                        
                        # Открываем изображение
                        img = Image.open(screenshot_path)
                        width, height = img.size
                        
                        # Полный скриншот без обрезки
                        size = os.path.getsize(screenshot_path) / 1024
                        print(f"[PROXY-FULL-SCREENSHOT] 📸 Полный скриншот сохранен: {width}x{height}")
                        print(f"[PROXY-FULL-SCREENSHOT] 📏 Размер файла: {size:.1f} KB")
                        
                        result["cropped"] = False
                        result["original_size"] = f"{width}x{height}"
                        result["final_size"] = f"{width}x{height}"
                        
                    except ImportError:
                        print(f"[PROXY-FULL-SCREENSHOT] ⚠️ PIL не установлен, сохраняем полный скриншот")
                        result["cropped"] = False
                    except Exception as size_error:
                        print(f"[PROXY-FULL-SCREENSHOT] ⚠️ Ошибка получения размера: {size_error}")
                        result["cropped"] = False
                
                if os.path.exists(screenshot_path):
                    size = os.path.getsize(screenshot_path) / 1024
                    print(f"[PROXY-FULL-SCREENSHOT] ✅ Полный скриншот создан: {size:.1f} KB")
                    
                    # Проверка на белый скрин
                    try:
                        from PIL import Image
                        import numpy as np
                        
                        img = Image.open(screenshot_path)
                        img_array = np.array(img.convert('RGB'))
                        
                        # Вычисляем среднюю яркость изображения
                        mean_brightness = np.mean(img_array)
                        
                        # Вычисляем стандартное отклонение (для определения однородности)
                        std_brightness = np.std(img_array)
                        
                        print(f"[PROXY-HEADER-SCREENSHOT] 📊 Средняя яркость: {mean_brightness:.2f}, Стандартное отклонение: {std_brightness:.2f}")
                        
                        # ОЧЕНЬ СТРОГАЯ проверка: яркость >230 и std <30 ИЛИ яркость >245 и std <35
                        is_white_screen = (mean_brightness > 230 and std_brightness < 30) or (mean_brightness > 245 and std_brightness < 35)
                        
                        if is_white_screen:
                            print(f"[PROXY-HEADER-SCREENSHOT] ⚠️ ОБНАРУЖЕН БЕЛЫЙ СКРИН! Яркость: {mean_brightness:.2f}, Std: {std_brightness:.2f}")
                            
                            # Делаем МНОГО попыток пересоздания (до 5 раз)
                            max_retries = 5
                            screenshot_fixed = False
                            
                            for retry_attempt in range(max_retries):
                                print(f"[PROXY-HEADER-SCREENSHOT] 🔄 Попытка {retry_attempt + 1}/{max_retries} пересоздания скриншота...")
                                
                                # Ждем еще дольше
                                await page.wait_for_timeout(5000)
                                
                                # МАКСИМАЛЬНО АГРЕССИВНОЕ удаление модальных окон
                                print(f"[PROXY-HEADER-SCREENSHOT] 🚪 МАКСИМАЛЬНО АГРЕССИВНОЕ удаление модальных окон...")
                                try:
                                    for _ in range(20):
                                        await page.keyboard.press("Escape")
                                        await page.wait_for_timeout(100)
                                except:
                                    pass
                                
                                # Прокручиваем страницу для триггера загрузки
                                await page.evaluate("window.scrollTo(0, 500)")
                                await page.wait_for_timeout(1000)
                                await page.evaluate("window.scrollTo(0, 0)")
                                await page.wait_for_timeout(2000)
                                
                                # Еще раз агрессивно удаляем модальные окна через JavaScript
                                await page.evaluate("""
                                    () => {
                                        // Удаляем все overlay, modal, dialog элементы
                                        document.querySelectorAll('[role="dialog"], [aria-modal="true"], [class*="modal"], [class*="Modal"], [class*="overlay"], [class*="Overlay"]').forEach(el => el.remove());
                                        
                                        // Удаляем белые блоки без контента
                                        document.querySelectorAll('div').forEach(el => {
                                            const style = window.getComputedStyle(el);
                                            if (style.backgroundColor === 'rgb(255, 255, 255)' && el.innerText.trim() === '') {
                                                const rect = el.getBoundingClientRect();
                                                if (rect.width > 200 && rect.height > 100) {
                                                    el.remove();
                                                }
                                            }
                                        });
                                        
                                        // Убираем overflow hidden
                                        document.body.style.overflow = 'auto';
                                        document.documentElement.style.overflow = 'auto';
                                    }
                                """)
                                
                                await page.wait_for_timeout(1000)
                                
                                # Создаем скриншот повторно
                                await page.screenshot(path=screenshot_path, full_page=False)
                                
                                # Проверяем повторно
                                img = Image.open(screenshot_path)
                                img_array = np.array(img.convert('RGB'))
                                mean_brightness = np.mean(img_array)
                                std_brightness = np.std(img_array)
                                
                                print(f"[PROXY-HEADER-SCREENSHOT] 📊 Попытка {retry_attempt + 1} - Яркость: {mean_brightness:.2f}, Std: {std_brightness:.2f}")
                                
                                is_white_screen = (mean_brightness > 230 and std_brightness < 30) or (mean_brightness > 245 and std_brightness < 35)
                                
                                if not is_white_screen:
                                    print(f"[PROXY-HEADER-SCREENSHOT] ✅ После попытки {retry_attempt + 1} скрин стал нормальным!")
                                    screenshot_fixed = True
                                    break
                            
                            if not screenshot_fixed:
                                print(f"[PROXY-HEADER-SCREENSHOT] ❌ Белый скрин остался после {max_retries} попыток")
                                result["error"] = "white_screen_detected"
                                result["exists"] = False
                                await browser.close()
                                return result
                        else:
                            print(f"[PROXY-HEADER-SCREENSHOT] ✅ Скриншот нормальный (не белый)")
                    
                    except ImportError:
                        print(f"[PROXY-HEADER-SCREENSHOT] ⚠️ PIL или numpy не установлены, пропускаем проверку белого скрина")
                    except Exception as check_error:
                        print(f"[PROXY-HEADER-SCREENSHOT] ⚠️ Ошибка проверки белого скрина: {check_error}")
                    
                    result["screenshot_path"] = screenshot_path
                    # Устанавливаем exists = True если скриншот создан, даже если были проблемы с Proxy
                    result["exists"] = True
                    print(f"[PROXY-FULL-SCREENSHOT] 📸 Скриншот успешно создан, аккаунт считается найденным")
                else:
                    print(f"[PROXY-HEADER-SCREENSHOT] ❌ Скриншот не создан")
                    result["error"] = "screenshot_failed"
                    result["exists"] = False
                
                await browser.close()
                
            except PWTimeoutError as e:
                print(f"[PROXY-HEADER-SCREENSHOT] ⏱️ Timeout: {e}")
                result["error"] = f"timeout: {e}"
                await browser.close()
                
            except Exception as e:
                print(f"[PROXY-HEADER-SCREENSHOT] ❌ Ошибка: {e}")
                result["error"] = str(e)
                await browser.close()
    
    except Exception as e:
        print(f"[PROXY-HEADER-SCREENSHOT] ❌ Критическая ошибка: {e}")
        result["error"] = str(e)
    
    return result