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
    """Применяет темную тему к странице Instagram."""
    # Ждем полной загрузки страницы
    await page.wait_for_load_state('networkidle')
    
    # Добавляем небольшую задержку для полной отрисовки
    await page.wait_for_timeout(2000)
    
    dark_theme_css = """
    /* Основной фон */
    body, html {
        background-color: #000000 !important;
        color: #ffffff !important;
    }
    
    /* Контейнеры и секции */
    div, section, article, header, main {
        background-color: #000000 !important;
        color: #ffffff !important;
    }
    
    /* Текст */
    span, p, h1, h2, h3, h4, h5, h6, a {
        color: #ffffff !important;
        background-color: transparent !important;
    }
    
    /* Ссылки */
    a {
        color: #ffffff !important;
    }
    
    /* Кнопки */
    button {
        background-color: #333333 !important;
        color: #ffffff !important;
        border-color: #555555 !important;
    }
    
    /* Специфичные селекторы для Instagram */
    [style*="background-color"] {
        background-color: #000000 !important;
    }
    
    [style*="color"] {
        color: #ffffff !important;
    }
    
    /* Убираем белые фоны */
    * {
        background-color: #000000 !important;
        color: #ffffff !important;
    }
    
    /* Исключения для изображений */
    img, svg {
        background-color: transparent !important;
    }
    
    /* Профиль хедер */
    header section {
        background-color: #000000 !important;
    }
    
    /* Статистика профиля */
    ul li {
        color: #ffffff !important;
    }
    
    /* Имя пользователя и описание */
    h1, h2 {
        color: #ffffff !important;
    }
    """
    
    await page.add_style_tag(content=dark_theme_css)
    
    # Дополнительно применяем стили через JavaScript для более надежного результата
    await page.evaluate("""
        () => {
            // Применяем стили ко всем элементам
            const allElements = document.querySelectorAll('*');
            allElements.forEach(el => {
                if (el.tagName !== 'IMG' && el.tagName !== 'SVG') {
                    el.style.setProperty('background-color', '#000000', 'important');
                    el.style.setProperty('color', '#ffffff', 'important');
                }
            });
            
            // Специально для body и html
            document.body.style.setProperty('background-color', '#000000', 'important');
            document.body.style.setProperty('color', '#ffffff', 'important');
            document.documentElement.style.setProperty('background-color', '#000000', 'important');
            document.documentElement.style.setProperty('color', '#ffffff', 'important');
        }
    """)


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
