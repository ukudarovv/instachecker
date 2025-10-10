"""Account validation and checking services."""

import re

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9._]{1,30}$")


def is_valid_instagram_username(username: str) -> bool:
    """
    Простая проверка формата имени IG: буквы, цифры, точка, нижнее подчёркивание, до 30 символов.
    Не проверяет существование в IG.
    """
    if not username:
        return False
    return bool(_USERNAME_RE.fullmatch(username))


def check_account_exists_placeholder(username: str) -> bool:
    """
    ВРЕМЕННО: всегда True, если формат валидный. На Этапе 4 заменим на реальный вызов API.
    """
    return is_valid_instagram_username(username)


# Proxy-based checking functions
async def check_single_username_via_proxies(session, user_id: int, username: str, max_attempts: int = 3):
    """
    Check single username via proxies with rotation.
    
    Args:
        session: database session
        user_id: user ID
        username: username to check
        max_attempts: maximum attempts with different proxies
        
    Returns:
        True if exists, False if not found, None if uncertain
    """
    try:
        from .proxy_utils import select_best_proxy, mark_success, mark_failure
        from .ig_probe import fetch_profile_exists_via_proxy
    except ImportError:
        from proxy_utils import select_best_proxy, mark_success, mark_failure
        from ig_probe import fetch_profile_exists_via_proxy
    
    tried = set()
    for _ in range(max_attempts):
        p = select_best_proxy(session, user_id)
        if not p or p.id in tried:
            break
        tried.add(p.id)
        
        # Build proxy URL
        auth = f"{p.username}:{p.password}@" if p.username and p.password else ""
        proxy_url = f"{p.scheme}://{auth}{p.host}"
        
        result = await fetch_profile_exists_via_proxy(username, proxy_url)
        if result is True:
            mark_success(session, p)
            return True
        elif result is False:
            mark_success(session, p)  # сам запрос успешен, просто профиль не найден
            return False
        else:
            mark_failure(session, p)
            continue
    return None


async def check_pending_accounts_via_proxy(session, user_id: int):
    """
    Check all pending accounts via proxy.
    
    Args:
        session: database session
        user_id: user ID
        
    Returns:
        List of (username, exists) tuples
    """
    try:
        from ..models import Account
    except ImportError:
        from models import Account
    
    accs = session.query(Account).filter(Account.user_id == user_id, Account.done == False).all()
    results = []
    for a in accs:
        res = await check_single_username_via_proxies(session, user_id, a.account)
        # если определённо True -> done=True, date_of_finish = today
        if res is True:
            a.done = True
            session.commit()
        results.append((a.account, res))
    return results
