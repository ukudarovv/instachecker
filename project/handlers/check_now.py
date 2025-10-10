"""Check accounts now handlers."""

try:
    from aiogram import types
    from aiogram.dispatcher import Dispatcher
except ImportError:
    # Fallback for direct API usage
    types = None
    Dispatcher = None

from sqlalchemy.orm import sessionmaker

try:
    from ..utils.access import get_or_create_user, ensure_active
    from ..services.checker import check_pending_accounts_via_proxy
except ImportError:
    from utils.access import get_or_create_user, ensure_active
    from services.checker import check_pending_accounts_via_proxy


def register_check_now_handlers(dp, SessionLocal):
    """Register check now handlers."""
    
    # These handlers will be integrated into the main bot logic
    # since we're using direct API calls
    pass
