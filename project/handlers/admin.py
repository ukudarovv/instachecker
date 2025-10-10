"""Admin message handlers."""

try:
    from aiogram import types
    from aiogram.dispatcher import FSMContext
except ImportError:
    # Fallback for direct API usage
    types = None
    FSMContext = None

from sqlalchemy.orm import sessionmaker

try:
    from ..utils.access import get_or_create_user, ensure_admin
except ImportError:
    from utils.access import get_or_create_user, ensure_admin


def register_admin_handlers(dp, SessionLocal):
    """Register admin handlers."""
    
    @dp.message_handler(lambda m: m.text == "Админка")
    async def admin_menu(message):
        """Handle Admin button."""
        with SessionLocal() as session:
            user = get_or_create_user(session, message.from_user)
            if not ensure_admin(user):
                await message.answer("⛔ Доступ запрещён. Нужны права администратора.")
                return
            await message.answer("🛡 Админ-панель (заглушка). Разделы появятся на Этапе 6.")
