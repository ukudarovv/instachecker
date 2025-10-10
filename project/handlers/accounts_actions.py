"""Account actions handlers."""

try:
    from aiogram import types
    from aiogram.dispatcher import Dispatcher, FSMContext
except ImportError:
    # Fallback for direct API usage
    types = None
    Dispatcher = None
    FSMContext = None

from sqlalchemy.orm import sessionmaker

try:
    from ..states import AddDaysStates, RemoveDaysStates
    from ..utils.access import get_or_create_user
    from ..services.accounts import get_account_by_id, increase_days, decrease_days, delete_account
    from ..services.formatting import format_account_card
    from ..keyboards import account_card_kb
except ImportError:
    from states import AddDaysStates, RemoveDaysStates
    from utils.access import get_or_create_user
    from services.accounts import get_account_by_id, increase_days, decrease_days, delete_account
    from services.formatting import format_account_card
    from keyboards import account_card_kb


def register_accounts_actions_handlers(dp, SessionLocal):
    """Register accounts actions handlers."""
    
    # These handlers will be integrated into the main bot logic
    # since we're using direct API calls
    pass
