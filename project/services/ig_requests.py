"""Instagram requests with cookies via aiohttp."""

from typing import Optional, List, Dict, Any
from aiohttp import ClientSession, ClientTimeout
from aiohttp_socks import ProxyConnector, ProxyType
from urllib.parse import urlparse

try:
    from .traffic_monitor import get_traffic_monitor
    from .traffic_decorator import TrafficAwareSession
except ImportError:
    from services.traffic_monitor import get_traffic_monitor
    from services.traffic_decorator import TrafficAwareSession

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit Safari/537.36"


def cookies_jar_from_list(cookies: List[Dict[str, Any]]):
    """Convert cookies list to aiohttp CookieJar."""
    from aiohttp.cookiejar import CookieJar
    jar = CookieJar()
    for c in cookies:
        # Ожидаем поля: name, value, domain, path, expires (опционально)
        jar.update_cookies(
            {c["name"]: c["value"]}, 
            response_url=f"https://{c.get('domain','.instagram.com')}{c.get('path','/')}"
        )
    return jar


async def fetch_with_cookies(
    url: str, 
    cookies: List[Dict[str, Any]], 
    proxy_url: Optional[str] = None, 
    timeout_sec: int = 12
) -> Optional[str]:
    """Fetch URL with cookies and optional proxy."""
    jar = cookies_jar_from_list(cookies)
    timeout = ClientTimeout(total=timeout_sec)
    headers = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}
    
    connector = None
    if proxy_url:
        # Parse proxy URL
        parsed = urlparse(proxy_url)
        scheme = parsed.scheme.lower()

        # Determine proxy type
        if scheme == 'http':
            proxy_type = ProxyType.HTTP
        elif scheme == 'https':
            proxy_type = ProxyType.HTTP  # HTTPS proxies use HTTP CONNECT
        elif scheme == 'socks5':
            proxy_type = ProxyType.SOCKS5
        elif scheme == 'socks4':
            proxy_type = ProxyType.SOCKS4
        else:
            proxy_type = ProxyType.HTTP

        # Build connector
        connector = ProxyConnector(
            proxy_type=proxy_type,
            host=parsed.hostname,
            port=parsed.port,
            username=parsed.username,
            password=parsed.password,
            rdns=True
        )
    
    try:
        # Используем TrafficAwareSession для мониторинга трафика
        async with TrafficAwareSession(
            cookie_jar=jar, 
            connector=connector, 
            timeout=timeout, 
            headers=headers
        ) as sess:
            async with sess.get(url, allow_redirects=True) as resp:
                if resp.status >= 500:
                    return None
                return await resp.text(errors="ignore")
    except Exception:
        return None
