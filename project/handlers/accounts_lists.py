"""Account lists and cards handlers."""

try:
    from aiogram import types
    from aiogram.dispatcher import Dispatcher
    from aiogram.dispatcher.filters import Text
except ImportError:
    # Fallback for direct API usage
    types = None
    Dispatcher = None
    Text = None

from sqlalchemy.orm import sessionmaker

try:
    from ..utils.access import get_or_create_user, ensure_active, ensure_admin
    from ..services.accounts import get_accounts_page, get_account_by_id
    from ..services.formatting import format_account_card
    from ..keyboards import (
        main_menu, pagination_kb, accounts_list_kb, account_card_kb, confirm_delete_kb
    )
except ImportError:
    from utils.access import get_or_create_user, ensure_active, ensure_admin
    from services.accounts import get_accounts_page, get_account_by_id
    from services.formatting import format_account_card
    from keyboards import (
        main_menu, pagination_kb, accounts_list_kb, account_card_kb, confirm_delete_kb
    )


def register_accounts_list_handlers(dp, SessionLocal):
    """Register accounts list handlers."""
    
    # These handlers will be integrated into the main bot logic
    # since we're using direct API calls
    pass
