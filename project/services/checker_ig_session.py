"""Instagram session-based account checking."""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
try:
    from ..models import Proxy, InstagramSession
    from ..services.ig_sessions import decode_cookies
    from ..services.ig_requests import fetch_with_cookies
    from ..services.ig_profile_loggedin import parse_profile_html
    from ..utils.encryptor import OptionalFernet
except ImportError:
    from models import Proxy, InstagramSession
    from services.ig_sessions import decode_cookies
    from services.ig_requests import fetch_with_cookies
    from services.ig_profile_loggedin import parse_profile_html
    from utils.encryptor import OptionalFernet


def _proxy_to_url(p: Optional[Proxy]) -> Optional[str]:
    """Convert Proxy model to URL string."""
    if not p:
        return None
    auth = f"{p.username}:{p.password}@" if p.username and p.password else ""
    return f"{p.scheme}://{auth}{p.host}"


async def check_username_via_ig_session(
    db: Session,
    ig_session: InstagramSession,
    fernet: OptionalFernet,
    username: str,
    timeout_sec: int = 12,
) -> Dict[str, Any]:
    """
    Check username using Instagram session cookies.
    Optionally use attached proxy.
    """
    cookies = decode_cookies(fernet, ig_session.cookies)
    proxy_url = _proxy_to_url(ig_session.proxy)
    url = f"https://www.instagram.com/{username.strip('@')}/"
    html = await fetch_with_cookies(url, cookies, proxy_url=proxy_url, timeout_sec=timeout_sec)
    info = parse_profile_html(username, html or "")
    return info
