"""Proxy utilities and management."""

from typing import Optional, Tuple
from datetime import datetime, timedelta
import re
from sqlalchemy.orm import Session

try:
    from ..models import Proxy
except ImportError:
    from models import Proxy

_PROXY_RE = re.compile(
    r'^(?P<scheme>http|https|socks5)://(?:(?P<user>[^:@]+):(?P<pass>[^@]+)@)?(?P<host>[^:]+:\d+)$',
    re.IGNORECASE
)


def parse_proxy_url(url: str) -> Optional[dict]:
    """Parse proxy URL into components."""
    m = _PROXY_RE.match((url or "").strip())
    if not m:
        return None
    d = m.groupdict()
    return {
        "scheme": d["scheme"].lower(),
        "host": d["host"],
        "username": d.get("user"),
        "password": d.get("pass"),
    }


def save_proxy(session: Session, user_id: int, data: dict, priority: int = 5) -> Proxy:
    """Save proxy to database."""
    p = Proxy(
        user_id=user_id,
        scheme=data["scheme"],
        host=data["host"],
        username=data.get("username"),
        password=data.get("password"),
        priority=max(1, min(10, int(priority))),
        is_active=True,
    )
    session.add(p)
    session.commit()
    session.refresh(p)
    return p


def mark_success(session: Session, p: Proxy) -> None:
    """Mark proxy as successful."""
    print(f"   ✅ Прокси #{p.id}: Успешное использование")
    print(f"      Всего успехов: {p.success_count} → {p.success_count + 1}")
    
    p.used_count += 1
    p.success_count += 1
    p.fail_streak = 0
    p.cooldown_until = None
    session.commit()
    
    print(f"      Провалов сброшено: 0")


def mark_failure(session: Session, p: Proxy, cooldown_minutes: int = 15) -> None:
    """Mark proxy as failed."""
    print(f"   ❌ Прокси #{p.id}: Провал")
    print(f"      Провалов подряд: {p.fail_streak} → {p.fail_streak + 1}")
    
    p.used_count += 1
    p.fail_streak += 1
    
    if p.fail_streak >= 3:
        p.cooldown_until = datetime.utcnow() + timedelta(minutes=cooldown_minutes)
        print(f"      ❄️ Прокси отправлен в кулдаун на {cooldown_minutes} минут")
        print(f"      Кулдаун до: {p.cooldown_until.strftime('%H:%M:%S')}")
    else:
        print(f"      ⚠️ Еще {3 - p.fail_streak} провала до кулдауна")
    
    session.commit()


def is_available(p: Proxy) -> bool:
    """Check if proxy is available for use."""
    if not p.is_active:
        return False
    if p.cooldown_until and p.cooldown_until > datetime.utcnow():
        return False
    return True


def select_best_proxy(session: Session, user_id: int) -> Optional[Proxy]:
    """Select best available proxy for user."""
    # приоритет по: active & no cooldown → priority asc → fail_streak asc → used_count asc
    q = (
        session.query(Proxy)
        .filter(Proxy.user_id == user_id, Proxy.is_active == True)
        .order_by(Proxy.priority.asc(), Proxy.fail_streak.asc(), Proxy.used_count.asc())
        .all()
    )
    for p in q:
        if is_available(p):
            return p
    return None
