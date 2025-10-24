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
    """Применяет темную тему к странице Instagram (легкая версия)."""
    # Ждем полной загрузки страницы
    await page.wait_for_load_state('networkidle')
    
    # Добавляем небольшую задержку для полной отрисовки
    await page.wait_for_timeout(1000)
    
    # ЛЕГКАЯ темная тема - только фон, БЕЗ изменения контента
    dark_theme_css = """
    /* Только основной фон страницы */
    body, html {
        background-color: #000000 !important;
    }
    
    /* НЕ трогаем контент - только основные контейнеры */
    body > div {
        background-color: transparent !important;
    }
    """
    
    await page.add_style_tag(content=dark_theme_css)
    
    # МИНИМАЛЬНОЕ применение стилей - только body и html
    await page.evaluate("""
        () => {
            console.log('🌙 Применение легкой темной темы (только фон)...');
            
            // ТОЛЬКО body и html - не трогаем контент!
            document.body.style.setProperty('background-color', '#000000', 'important');
            document.documentElement.style.setProperty('background-color', '#000000', 'important');
            
            console.log('✅ Легкая темная тема применена (фон страницы)');
        }
    """)
    
    # Дополнительная задержка для применения стилей
    await page.wait_for_timeout(500)


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
    proxy_kwargs = _proxy_kwargs_from_url(proxy_url)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
        ])
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
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
                await _apply_dark_theme(page)

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
    
    print(f"\n[PROXY-HEADER-SCREENSHOT] 🔍 Проверка @{username} через proxy с header-скриншотом")
    print(f"[PROXY-HEADER-SCREENSHOT] 🌐 Proxy: {proxy_url[:50]}...")
    print(f"[PROXY-HEADER-SCREENSHOT] 🌙 Темная тема: {dark_theme}")
    print(f"[PROXY-HEADER-SCREENSHOT] 📱 Мобильная эмуляция: {mobile_emulation}")
    print(f"[PROXY-HEADER-SCREENSHOT] ✂️  Обрезка: {crop_ratio*100:.0f}% верха (header + био + кнопки)")
    
    result = {
        "username": username,
        "exists": None,
        "screenshot_path": None,
        "error": None,
        "checked_via": "proxy_header_screenshot",
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
    proxy_kwargs = _proxy_kwargs_from_url(proxy_url)
    
    try:
        async with async_playwright() as p:
            # 🔥 УЛУЧШЕННАЯ настройка браузера
            launch_args = [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
            
            # Принудительная темная тема на уровне браузера
            if dark_theme:
                launch_args.extend([
                    "--force-dark-mode",
                    "--enable-features=WebUIDarkMode"
                ])
            
            # 🔥 ПРОКСИ на уровне браузера (обязательно для Playwright)
            browser = await p.chromium.launch(
                headless=headless,
                args=launch_args,
                proxy=proxy_kwargs  # Прокси ДОЛЖЕН быть здесь
            )
            
            # 🔥 МОБИЛЬНАЯ ЭМУЛЯЦИЯ или обычный режим
            if mobile_emulation:
                # Используем iPhone 12 для мобильной версии
                device = p.devices["iPhone 12"]
                context_options = {
                    **device
                    # proxy НЕ передаем - уже передан в browser.launch()
                }
                
                # 🔥 ТЕМНАЯ ТЕМА на уровне устройства
                if dark_theme:
                    context_options["color_scheme"] = "dark"
                
                print(f"[PROXY-HEADER-SCREENSHOT] 📱 Эмуляция: iPhone 12")
            else:
                # Обычный desktop режим
                context_options = {
                    "viewport": {"width": 1280, "height": 900},
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    # proxy НЕ передаем - уже передан в browser.launch()
                }
                
                # 🔥 ТЕМНАЯ ТЕМА для desktop
                if dark_theme:
                    context_options["color_scheme"] = "dark"
            
            context = await browser.new_context(**context_options)
            
            # 🔥 ПРИНУДИТЕЛЬНАЯ ТЕМНАЯ ТЕМА через JavaScript injection
            if dark_theme:
                await context.add_init_script("""
                    // Принудительно включаем темную тему
                    localStorage.setItem('dark_mode', '1');
                    localStorage.setItem('ig_dark_mode', '1');
                    localStorage.setItem('theme', 'dark');
                    
                    // Переопределяем matchMedia для темной темы
                    Object.defineProperty(window, 'matchMedia', {
                        writable: true,
                        value: (query) => ({
                            matches: query.includes('dark') ? true : false,
                            media: query,
                            addListener: () => {},
                            removeListener: () => {},
                            addEventListener: () => {},
                            removeEventListener: () => {},
                            dispatchEvent: () => true,
                        }),
                    });
                    
                    console.log('🌙 Темная тема принудительно включена через localStorage и matchMedia');
                """)
            
            # Стелс-режим
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            """)
            
            page = await context.new_page()
            
            # 🔥 ЭМУЛЯЦИЯ ТЕМНОЙ ТЕМЫ через media
            if dark_theme:
                await page.emulate_media(color_scheme='dark')
                print(f"[PROXY-HEADER-SCREENSHOT] 🌙 Темная тема активирована через emulate_media")
            
            try:
                print(f"[PROXY-HEADER-SCREENSHOT] 📡 Переход на: {url}")
                response = await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                status_code = response.status if response else None
                
                print(f"[PROXY-HEADER-SCREENSHOT] 📊 HTTP Status: {status_code}")
                
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
                await page.wait_for_timeout(5000)  # 5 секунд для полной загрузки
                
                # Проверяем URL - перекинуло ли на login
                current_url = page.url
                print(f"[PROXY-HEADER-SCREENSHOT] 🔗 Текущий URL: {current_url}")
                
                if "accounts/login" in current_url:
                    print(f"[PROXY-HEADER-SCREENSHOT] 🔄 Перекинуло на страницу логина, пробуем вернуться...")
                    # Пробуем вернуться на профиль
                    await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                    await page.wait_for_timeout(2000)
                    current_url = page.url
                    print(f"[PROXY-HEADER-SCREENSHOT] 🔗 После повтора: {current_url}")
                
                # Проверяем контент страницы СНАЧАЛА
                content = await page.content()
                
                # Проверяем, не показывает ли Instagram страницу "Open app" или "Continue on web"
                if "Open app" in content or "open_app" in current_url.lower() or "Continue on web" in content:
                    print(f"[PROXY-HEADER-SCREENSHOT] ⚠️ Instagram показывает блокировку - переключаемся на desktop...")
                    
                    # Закрываем текущий браузер
                    await browser.close()
                    
                    # Перезапускаем с DESKTOP эмуляцией
                    print(f"[PROXY-HEADER-SCREENSHOT] 🖥️ Переключаемся на DESKTOP режим...")
                    
                    browser = await p.chromium.launch(
                        headless=headless,
                        args=launch_args,
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
                
                # Сначала пробуем ESC для закрытия модалок
                try:
                    await page.keyboard.press("Escape")
                    await page.wait_for_timeout(500)
                    print(f"[PROXY-HEADER-SCREENSHOT] ⌨️ Нажали ESC")
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
                
                # Принудительное удаление всех модальных окон через JavaScript - АГРЕССИВНО
                print(f"[PROXY-HEADER-SCREENSHOT] 🔥 Принудительное удаление всех модальных окон (агрессивный режим)...")
                removed_count = await page.evaluate("""
                    () => {
                        let count = 0;
                        
                        // Удаляем несколько раз для надежности
                        for (let iteration = 0; iteration < 3; iteration++) {
                            
                            // 1. Удаляем все диалоги (role="dialog")
                            document.querySelectorAll('[role="dialog"]').forEach(el => {
                                el.remove();
                                count++;
                            });
                            
                            // 2. Удаляем все overlay/backdrop/modal элементы
                            document.querySelectorAll('[class*="overlay"], [class*="Overlay"], [class*="backdrop"], [class*="Backdrop"], [class*="modal"], [class*="Modal"]').forEach(el => {
                                el.remove();
                                count++;
                            });
                            
                            // 3. Удаляем скелетоны загрузки (белые прямоугольники)
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
                        }
                        
                        // Убираем overflow: hidden с body (модалки часто блокируют прокрутку)
                        document.body.style.overflow = 'auto';
                        document.documentElement.style.overflow = 'auto';
                        
                        return count;
                    }
                """)
                print(f"[PROXY-HEADER-SCREENSHOT] 🗑️ Удалено элементов: {removed_count}")
                
                # Ждем после удаления для перерисовки
                await page.wait_for_timeout(1500)
                
                if "Sorry, this page isn't available" in content:
                    print(f"[PROXY-HEADER-SCREENSHOT] ❌ Страница недоступна")
                    result["exists"] = False
                    result["error"] = "page_not_found"
                    await browser.close()
                    return result
                
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
                
                # Даем время Instagram применить встроенную темную тему
                if dark_theme:
                    print(f"[PROXY-HEADER-SCREENSHOT] 🌙 Ожидание применения встроенной темной темы Instagram...")
                    await page.wait_for_timeout(5000)  # 5 секунд - даем время Instagram применить тему
                    
                    # Проверяем темную тему
                    dark_theme_verified = await page.evaluate("""
                        () => {
                            const body = document.body;
                            const computedStyle = window.getComputedStyle(body);
                            const bgColor = computedStyle.backgroundColor;
                            
                            // Проверяем что фон темный
                            const isDark = bgColor.includes('0, 0, 0') || bgColor.includes('#000') || bgColor.includes('rgb(0, 0, 0)');
                            return isDark;
                        }
                    """)
                    
                    result["dark_theme_applied"] = dark_theme_verified
                    
                    if dark_theme_verified:
                        print(f"[PROXY-HEADER-SCREENSHOT] ✅ Встроенная темная тема Instagram активна")
                    else:
                        print(f"[PROXY-HEADER-SCREENSHOT] ℹ️  Instagram использует светлую тему")
                else:
                    result["dark_theme_applied"] = False
                
                # Делаем скриншот header'а или всей страницы
                if header_elem and crop_ratio == 0:
                    # Если crop_ratio=0 И header найден - делаем скриншот только header'а (без обрезки)
                    print(f"[PROXY-HEADER-SCREENSHOT] 📸 Создание скриншота только header'а профиля...")
                    await header_elem.screenshot(path=screenshot_path, type="png")
                elif crop_ratio > 0:
                    print(f"[PROXY-HEADER-SCREENSHOT] 📸 Создание скриншота header'а (с обрезкой)...")
                    
                    if header_elem:
                        # Скриншот только header'а
                        await header_elem.screenshot(path=screenshot_path, type="png")
                    else:
                        # Скриншот всего viewport
                        await page.screenshot(path=screenshot_path, full_page=False)
                else:
                    # ПОЛНЫЙ скриншот всей страницы (если header не найден)
                    print(f"[PROXY-HEADER-SCREENSHOT] 📸 Создание ПОЛНОГО скриншота всей страницы (full_page=True)...")
                    await page.screenshot(path=screenshot_path, full_page=True)
                
                # Обрезка по бокам на 15% с каждой стороны
                if os.path.exists(screenshot_path):
                    try:
                        from PIL import Image
                        
                        img = Image.open(screenshot_path)
                        width, height = img.size
                        
                        # Вычисляем новые границы (убираем 15% с каждой стороны)
                        crop_left = int(width * 0.15)
                        crop_right = int(width * 0.85)
                        
                        # Увеличиваем высоту на 15px сверху и снизу
                        crop_top = max(0, -15)  # -15px сверху (расширяем вверх)
                        crop_bottom = min(height, height + 15)  # +15px снизу (расширяем вниз)
                        
                        print(f"[PROXY-HEADER-SCREENSHOT] ✂️ Обрезка по бокам: {width}px -> {crop_right - crop_left}px (убираем 15% с каждой стороны)")
                        print(f"[PROXY-HEADER-SCREENSHOT] ✂️ Увеличение высоты: {height}px -> {crop_bottom - crop_top}px (+15px сверху и снизу)")
                        
                        # Обрезаем по бокам и увеличиваем высоту
                        cropped = img.crop((crop_left, crop_top, crop_right, crop_bottom))
                        cropped.save(screenshot_path, quality=95)
                        
                        new_width = crop_right - crop_left
                        new_height = crop_bottom - crop_top
                        print(f"[PROXY-HEADER-SCREENSHOT] ✂️ Скриншот обрезан: {width}x{height} -> {new_width}x{new_height}")
                        
                        result["cropped_sides"] = True
                        result["original_width"] = width
                        result["final_width"] = new_width
                        
                    except ImportError:
                        print(f"[PROXY-HEADER-SCREENSHOT] ⚠️ PIL не установлен, сохраняем без обрезки")
                        result["cropped_sides"] = False
                    except Exception as crop_error:
                        print(f"[PROXY-HEADER-SCREENSHOT] ⚠️ Ошибка обрезки по бокам: {crop_error}")
                        result["cropped_sides"] = False
                
                # ОБРЕЗКА: Если скриншот получился слишком большим, обрезаем его
                if os.path.exists(screenshot_path) and crop_ratio > 0:
                    try:
                        from PIL import Image
                        
                        # Открываем изображение
                        img = Image.open(screenshot_path)
                        width, height = img.size
                        
                        # Обрезаем до указанного процента верха (только header)
                        new_height = int(height * crop_ratio)
                        
                        print(f"[PROXY-HEADER-SCREENSHOT] ✂️ Обрезка до header'а: {crop_ratio*100:.0f}% верха ({height}px -> {new_height}px)")
                        
                        # Обрезаем (оставляем только header)
                        cropped = img.crop((0, 0, width, new_height))
                        
                        # Сохраняем обрезанное изображение
                        cropped.save(screenshot_path, quality=95)
                        
                        size = os.path.getsize(screenshot_path) / 1024
                        print(f"[PROXY-HEADER-SCREENSHOT] ✂️ Скриншот обрезан: {width}x{height} → {width}x{new_height}")
                        print(f"[PROXY-HEADER-SCREENSHOT] 📸 Финальный размер: {size:.1f} KB")
                        
                        result["cropped"] = True
                        result["original_size"] = f"{width}x{height}"
                        result["final_size"] = f"{width}x{new_height}"
                        
                    except ImportError:
                        print(f"[PROXY-HEADER-SCREENSHOT] ⚠️ PIL не установлен, сохраняем без обрезки")
                        result["cropped"] = False
                    except Exception as crop_error:
                        print(f"[PROXY-HEADER-SCREENSHOT] ⚠️ Ошибка обрезки: {crop_error}")
                        result["cropped"] = False
                
                if os.path.exists(screenshot_path):
                    size = os.path.getsize(screenshot_path) / 1024
                    print(f"[PROXY-HEADER-SCREENSHOT] ✅ Скриншот header'а создан: {size:.1f} KB")
                    result["screenshot_path"] = screenshot_path
                    result["exists"] = True
                else:
                    print(f"[PROXY-HEADER-SCREENSHOT] ❌ Скриншот не создан")
                    result["error"] = "screenshot_failed"
                
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