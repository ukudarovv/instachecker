"""Instagram profile extraction via aiohttp + proxy."""

import re
import json
from typing import Optional, Dict, Any
from aiohttp import ClientSession, ClientTimeout
from aiohttp_socks import ProxyConnector
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit Safari/537.36"
TIMEOUT = 12

# Регексы для старых/новых встраиваемых JSON
RE_FOLLOWERS = re.compile(r'"edge_followed_by"\s*:\s*\{"count"\s*:\s*(\d+)\}', re.I)
RE_FOLLOWING = re.compile(r'"edge_follow"\s*:\s*\{"count"\s*:\s*(\d+)\}', re.I)
RE_POSTS     = re.compile(r'"edge_owner_to_timeline_media"\s*:\s*\{"count"\s*:\s*(\d+)\}', re.I)
RE_AVATAR    = re.compile(r'"profile_pic_url_hd"\s*:\s*"([^"]+)"', re.I)


async def fetch_html_via_proxy(url: str, proxy_url: str) -> Optional[str]:
    """Fetch HTML content via proxy."""
    from urllib.parse import urlparse
    from aiohttp_socks import ProxyType
    
    print(f"🌐 Connecting to {url} via {proxy_url}")
    
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
        print(f"❌ Unsupported proxy type: {scheme}")
        return None
    
    # Build connector
    connector = ProxyConnector(
        proxy_type=proxy_type,
        host=parsed.hostname,
        port=parsed.port,
        username=parsed.username,
        password=parsed.password,
        rdns=True
    )
    
    timeout = ClientTimeout(total=TIMEOUT)
    headers = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}
    try:
        async with ClientSession(connector=connector, timeout=timeout, headers=headers) as sess:
            async with sess.get(url, allow_redirects=True) as resp:
                print(f"📡 Response status: {resp.status}")
                if resp.status == 404:
                    print("✅ 404 - Profile not found")
                    return ""  # 404 = явно нет
                if resp.status >= 500:
                    print(f"❌ Server error: {resp.status}")
                    return None
                html = await resp.text(errors="ignore")
                print(f"📄 Got HTML: {len(html)} characters")
                return html
    except Exception as e:
        print(f"❌ Connection error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


def _extract_from_ldjson(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract data from ld+json scripts."""
    data = {"full_name": None, "avatar_url": None}
    for tag in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            obj = json.loads(tag.text)
            # Поля могут быть как в dict, так и в списке
            cand = obj if isinstance(obj, dict) else (obj[0] if isinstance(obj, list) and obj else None)
            if not isinstance(cand, dict):
                continue
            name = cand.get("name")
            image = cand.get("image")
            if name and not data["full_name"]:
                data["full_name"] = name
            if image and not data["avatar_url"]:
                data["avatar_url"] = image
        except Exception:
            continue
    return data


def _extract_from_inline_json(html: str) -> Dict[str, Any]:
    """Extract data from inline JSON blocks."""
    data = {"followers": None, "following": None, "posts": None, "avatar_url": None}
    m = RE_FOLLOWERS.search(html)
    if m: data["followers"] = int(m.group(1))
    m = RE_FOLLOWING.search(html)
    if m: data["following"] = int(m.group(1))
    m = RE_POSTS.search(html)
    if m: data["posts"] = int(m.group(1))
    m = RE_AVATAR.search(html)
    if m: data["avatar_url"] = m.group(1).encode("utf-8").decode("unicode_escape")
    return data


def _normalize_counts(d: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize count values."""
    for k in ("followers", "following", "posts"):
        if k in d and isinstance(d[k], str) and d[k].isdigit():
            d[k] = int(d[k])
    return d


async def extract_profile_info(username: str, proxy_url: str) -> Dict[str, Any]:
    """
    Extract Instagram profile information via proxy.
    
    Returns:
    {
      "exists": bool|None,
      "username": str,
      "full_name": str|None,
      "avatar_url": str|None,
      "followers": int|None,
      "following": int|None,
      "posts": int|None,
      "error": str|None
    }
    """
    url = f"https://www.instagram.com/{username.strip('@')}/"
    print(f"🔍 Fetching {url} via proxy {proxy_url}")
    
    html = await fetch_html_via_proxy(url, proxy_url)
    result = {
        "exists": None, "username": username, "full_name": None, "avatar_url": None,
        "followers": None, "following": None, "posts": None, "error": None
    }
    
    if html is None:
        result["error"] = "fetch_error"
        print(f"❌ Fetch failed for {username}")
        return result
    if html == "":
        result["exists"] = False
        print(f"✅ 404 - Profile {username} not found")
        return result

    print(f"📄 Got HTML ({len(html)} chars) for {username}")
    
    soup = BeautifulSoup(html, "html.parser")

    # Эвристика «страница не найдена»
    if "page not found" in html.lower():
        result["exists"] = False
        print(f"✅ Page not found for {username}")
        return result

    # Пробуем вытащить ld+json блок
    ld = _extract_from_ldjson(soup)
    inl = _extract_from_inline_json(html)
    result.update({k: v for k, v in ld.items() if v})
    result.update({k: v for k, v in inl.items() if v is not None})

    print(f"🔍 Extracted data for {username}: ld={ld}, inline={inl}")

    # Если есть хоть какие-то валидные сигналы — считаем exists=True
    if result["avatar_url"] or result["followers"] is not None or result["following"] is not None or result["posts"] is not None:
        result["exists"] = True
        print(f"✅ Profile {username} found with data")
    else:
        # могли получить страницу логина/ограничений — неопределённо
        result["exists"] = None
        print(f"❓ Profile {username} status unclear - might be login page or blocked")
    _normalize_counts(result)
    return result
