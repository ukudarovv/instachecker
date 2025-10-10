"""Proxy connectivity checker."""

import asyncio
from typing import Optional
from aiohttp import ClientSession, ClientTimeout
from aiohttp_socks import ProxyConnector, ProxyType

DEFAULT_TIMEOUT = 6

async def _build_connector(scheme: str, host: str, username: Optional[str], password: Optional[str]):
    """Build proxy connector."""
    # Parse host:port
    if ':' in host:
        hostname, port = host.rsplit(':', 1)
        port = int(port)
    else:
        hostname = host
        port = 8080  # default
    
    # Determine proxy type
    scheme_lower = scheme.lower()
    if scheme_lower == 'http':
        proxy_type = ProxyType.HTTP
    elif scheme_lower == 'https':
        proxy_type = ProxyType.HTTP
    elif scheme_lower == 'socks5':
        proxy_type = ProxyType.SOCKS5
    elif scheme_lower == 'socks4':
        proxy_type = ProxyType.SOCKS4
    else:
        proxy_type = ProxyType.HTTP
    
    return ProxyConnector(
        proxy_type=proxy_type,
        host=hostname,
        port=port,
        username=username,
        password=password,
        rdns=True
    )

async def test_proxy_connectivity(scheme: str, host: str, username: Optional[str], password: Optional[str]) -> bool:
    """
    Test proxy connectivity by trying to access Instagram.
    
    Args:
        scheme: proxy scheme (http/https/socks5)
        host: proxy host:port
        username: optional username
        password: optional password
        
    Returns:
        True if proxy works, False otherwise
    """
    connector = await _build_connector(scheme, host, username, password)
    timeout = ClientTimeout(total=DEFAULT_TIMEOUT)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit Safari/537.36"}
    try:
        async with ClientSession(connector=connector, timeout=timeout, headers=headers) as sess:
            async with sess.get("https://www.instagram.com/") as resp:
                return 200 <= resp.status < 400
    except Exception as e:
        print(f"❌ Proxy test failed: {e}")
        return False
