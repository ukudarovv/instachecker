"""Proxy menu handlers."""

try:
    from aiogram import types
    from aiogram.dispatcher import Dispatcher
except ImportError:
    # Fallback for direct API usage
    types = None
    Dispatcher = None

from sqlalchemy.orm import sessionmaker

try:
    from ..utils.access import get_or_create_user, ensure_active, ensure_admin
    from ..keyboards import proxies_menu_kb, main_menu, proxy_card_kb
    from ..models import Proxy
except ImportError:
    from utils.access import get_or_create_user, ensure_active, ensure_admin
    from keyboards import proxies_menu_kb, main_menu, proxy_card_kb
    from models import Proxy


def _fmt_proxy(p: Proxy) -> str:
    """Format proxy for display."""
    creds = f"{p.username}:{p.password}@" if p.username and p.password else ""
    return (
        f"🧩 Proxy #{p.id}\n"
        f"• {p.scheme}://{creds}{p.host}\n"
        f"• active: {p.is_active} | prio: {p.priority}\n"
        f"• used: {p.used_count} | success: {p.success_count} | fail_streak: {p.fail_streak}\n"
        f"• cooldown_until: {p.cooldown_until}\n"
        f"• last_checked: {p.last_checked}"
    )


def register_proxy_menu_handlers(dp, SessionLocal):
    """Register proxy menu handlers."""
    
    # These handlers will be integrated into the main bot logic
    # since we're using direct API calls
    pass
