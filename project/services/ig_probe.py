"""Instagram profile checking via proxy."""

import asyncio
from typing import Optional
from aiohttp import ClientSession, ClientTimeout
from aiohttp_socks import ProxyConnector
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit Safari/537.36"
TIMEOUT = 8

async def fetch_profile_exists_via_proxy(username: str, proxy_url: str) -> Optional[bool]:
    """
    Check if Instagram profile exists via proxy.
    
    Args:
        username: Instagram username to check
        proxy_url: proxy URL in format scheme://[user:pass@]host:port
        
    Returns:
        True if profile exists, False if not found, None if uncertain/error
    """
    timeout = ClientTimeout(total=TIMEOUT)
    connector = ProxyConnector.from_url(proxy_url)
    headers = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}
    url = f"https://www.instagram.com/{username.strip('@')}/"

    try:
        async with ClientSession(connector=connector, timeout=timeout, headers=headers) as sess:
            async with sess.get(url, allow_redirects=True) as resp:
                status = resp.status
                text = await resp.text(errors="ignore")
                if status == 404:
                    return False
                if status >= 500:
                    return None
                if status == 200:
                    # грубая эвристика
                    if "Page Not Found" in text or "content=\"Instagram\" name=\"apple-mobile-web-app-title\"" in text and "/accounts/login/" in text:
                        # может быть редирект на логин, не однозначно
                        # попробуем meta og:url
                        soup = BeautifulSoup(text, "html.parser")
                        meta = soup.find("meta", {"property":"og:url"})
                        if meta and username.lower() in (meta.get("content","").lower()):
                            return True
                        # если явно «Page Not Found»
                        if "page not found" in text.lower():
                            return False
                        # не ясно
                        return None
                    # часто для реальных профилей meta og:url присутствует
                    soup = BeautifulSoup(text, "html.parser")
                    meta = soup.find("meta", {"property":"og:url"})
                    if meta and username.lower() in (meta.get("content","").lower()):
                        return True
                    # fallback
                    return None
                # редиректы на логин/челлендж — считаем неопределённо
                return None
    except Exception:
        return None
