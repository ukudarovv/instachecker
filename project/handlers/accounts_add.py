"""Account addition FSM handlers."""

try:
    from aiogram import types
    from aiogram.dispatcher import Dispatcher, FSMContext
    from aiogram.dispatcher.filters import Text
except ImportError:
    # Fallback for direct API usage
    types = None
    Dispatcher = None
    FSMContext = None
    Text = None

from sqlalchemy.orm import sessionmaker

try:
    from ..states import AddAccountStates
    from ..keyboards import cancel_kb, main_menu
    from ..utils.access import get_or_create_user, ensure_active, ensure_admin
    from ..services.accounts import normalize_username, find_duplicate, create_account
    from ..services.checker import is_valid_instagram_username, check_account_exists_placeholder
except ImportError:
    from states import AddAccountStates
    from keyboards import cancel_kb, main_menu
    from utils.access import get_or_create_user, ensure_active, ensure_admin
    from services.accounts import normalize_username, find_duplicate, create_account
    from services.checker import is_valid_instagram_username, check_account_exists_placeholder


def register_add_account_handlers(dp, SessionLocal):
    """Register add account FSM handlers."""
    
    @dp.message_handler(lambda m: m.text == "Добавить аккаунт")
    async def start_add_account(message):
        """Start add account FSM - simplified without days input."""
        with SessionLocal() as session:
            user = get_or_create_user(session, message.from_user)
            if not ensure_active(user):
                await message.answer("⛔ Доступ пока не выдан. Обратись к администратору.")
                return
        
        await message.answer(
            "🆔 Введите Instagram username (можно с @):\n\n"
            "📅 Период мониторинга: 30 дней (по умолчанию)\n"
            "ℹ️ После добавления аккаунт будет автоматически проверяться",
            reply_markup=cancel_kb()
        )
        # Set state for username input
        # Note: In direct API mode, we'll handle state in bot.py
    
    @dp.message_handler(lambda m: m.text == "Отмена")
    async def cancel_any(message):
        """Cancel any FSM operation."""
        # Reset state and show main menu
        with SessionLocal() as session:
            user = get_or_create_user(session, message.from_user)
            await message.answer("❌ Отменено.", reply_markup=main_menu(is_admin=ensure_admin(user)))
    
    # These handlers will be integrated into the main bot logic
    # since we're using direct API calls
