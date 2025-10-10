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


async def screenshot_profile_header(
    username: str,
    proxy_url: str,
    wait_selector: str,
    fallback_selector: str,
    headless: bool = True,
    timeout_ms: int = 15000,
    save_path: Optional[str] = None
) -> Optional[str]:
    """
    Открывает https://www.instagram.com/<username>/ через указанный прокси,
    ждёт селектор 'wait_selector', делает скрин элемента.
    Если не вышло — пробует 'fallback_selector'.
    Возвращает путь к PNG или None.
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

            spath = save_path or f"/tmp/ig_{username}_header.png"
            await elem.screenshot(path=spath, type="png")
            return spath
        except Exception:
            return None
        finally:
            await context.close()
            await browser.close()
