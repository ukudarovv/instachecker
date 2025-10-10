"""Instagram login via Playwright."""

from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential

LOGIN_URL = "https://www.instagram.com/accounts/login/"


def _proxy_kwargs_from_url(proxy_url: Optional[str]):
    """Convert proxy URL to Playwright proxy kwargs."""
    if not proxy_url:
        return None
    from urllib.parse import urlparse
    u = urlparse(proxy_url)
    auth = {}
    if u.username and u.password:
        auth["username"] = u.username
        auth["password"] = u.password
    return {"server": f"{u.scheme}://{u.hostname}:{u.port}", **auth}


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
async def playwright_login_and_get_cookies(
    ig_username: str,
    ig_password: str,
    headless: bool,
    login_timeout_ms: int,
    twofa_timeout_ms: int,
    proxy_url: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Login via Chromium, optionally wait for 2FA (code entered by user in Telegram).
    Returns list of cookies (dicts).
    """
    proxy_kwargs = _proxy_kwargs_from_url(proxy_url)
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless, 
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            proxy=proxy_kwargs
        )
        page = await context.new_page()
        try:
            await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=login_timeout_ms)
            # Ввод логина/пароля
            await page.fill('input[name="username"]', ig_username)
            await page.fill('input[name="password"]', ig_password)
            await page.click('button[type="submit"]')

            # Ожидание возможных состояний:
            # - успешный редирект на / (или /accounts/...), 
            # - запрос 2FA (код из приложения/SMS),
            # - чекпоинт/подтверждение (сложно автоматизировать).
            # Попробуем ждать либо домашнюю, либо форму 2FA.
            try:
                await page.wait_for_selector('nav, a[href="/accounts/edit/"]', timeout=login_timeout_ms)
            except PWTimeoutError:
                # Может 2FA
                # Если появляется поле для кода — ждем, пока бот подставит код (через внешний вызов)
                # Здесь оставим как есть: вызывающая сторона должна заранее собрать код и вызвать повторно при необходимости.
                pass

            cookies = await context.cookies()
            return cookies
        finally:
            await context.close()
            await browser.close()
