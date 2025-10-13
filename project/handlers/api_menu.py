"""API menu handlers."""

try:
    from aiogram import types
    from aiogram.dispatcher import Dispatcher, FSMContext
    from aiogram.dispatcher.filters import Text
except ImportError:
    # For testing without aiogram
    types = None
    Dispatcher = None
    FSMContext = None
    Text = None

from sqlalchemy.orm import sessionmaker

try:
    from ..utils.access import get_or_create_user, ensure_active, ensure_admin
    from ..keyboards import api_menu_kb, main_menu, api_key_card_kb
    from ..models import APIKey
    from ..states import AddApiKeyStates
    from ..services.api_keys import list_keys_for_user
    from ..config import get_settings
except ImportError:
    from utils.access import get_or_create_user, ensure_active, ensure_admin
    from keyboards import api_menu_kb, main_menu, api_key_card_kb
    from models import APIKey
    from states import AddApiKeyStates
    from services.api_keys import list_keys_for_user
    from config import get_settings


def _fmt_key(k: APIKey) -> str:
    """Format API key for display."""
    # Mask the key
    masked = k.key[:4] + "..." + k.key[-4:] if k.key and len(k.key) > 8 else "***"
    return (
        f"🔑 id={k.id}\n"
        f"• key: {masked}\n"
        f"• is_work: {'✅' if k.is_work else '❌'}\n"
        f"• qty_req (сегодня): {k.qty_req or 0}\n"
        f"• ref_date: {k.ref_date or 'N/A'}"
    )


def register_api_menu_handlers(dp: Dispatcher, SessionLocal: sessionmaker) -> None:
    """
    Register API menu handlers.
    
    Args:
        dp: Aiogram dispatcher
        SessionLocal: SQLAlchemy session factory
    """

    @dp.message_handler(Text(equals="API"))
    async def open_api_menu(message: types.Message):
        """Open API menu."""
        with SessionLocal() as s:
            user = get_or_create_user(s, message.from_user)
            if not ensure_active(user):
                await message.answer("⛔ Доступ пока не выдан.")
                return
        await message.answer("Раздел «API ключи»", reply_markup=api_menu_kb())

    @dp.message_handler(Text(equals="Назад в меню"), state="*")
    async def back_to_menu(message: types.Message, state: FSMContext):
        """Return to main menu."""
        await state.finish()
        with SessionLocal() as s:
            user = get_or_create_user(s, message.from_user)
            is_admin = user.role in ["admin", "superuser"]
            await message.answer("Главное меню:", reply_markup=main_menu(is_admin=is_admin))

    @dp.message_handler(Text(equals="Мои API ключи"))
    async def my_api_keys(message: types.Message):
        """Show user's API keys."""
        with SessionLocal() as s:
            user = get_or_create_user(s, message.from_user)
            if not ensure_active(user):
                await message.answer("⛔ Доступ пока не выдан.")
                return
            keys = list_keys_for_user(s, user.id)
            if not keys:
                await message.answer("📭 У вас ещё нет ключей.", reply_markup=api_menu_kb())
                return
            for k in keys:
                await message.answer(_fmt_key(k), reply_markup=api_key_card_kb(k.id))

    @dp.message_handler(Text(equals="Добавить API ключ"))
    async def add_api_key_start(message: types.Message, state: FSMContext):
        """Start adding API key flow."""
        from ..keyboards import api_add_cancel_kb
        await message.answer("Пришлите ваш RapidAPI ключ (строка).", reply_markup=api_add_cancel_kb())
        await AddApiKeyStates.waiting_for_key.set()

    @dp.message_handler(state=AddApiKeyStates.waiting_for_key, content_types=types.ContentTypes.TEXT)
    async def add_api_key_finish(message: types.Message, state: FSMContext):
        """Finish adding API key."""
        key_value = (message.text or "").strip()
        
        # Check for cancel command
        if key_value.lower() in ['/cancel', 'отмена', 'cancel', '❌ отмена']:
            await state.finish()
            await message.answer("❌ Добавление API ключа отменено.", reply_markup=api_menu_kb())
            return
        
        if len(key_value) < 20:
            from ..keyboards import api_add_cancel_kb
            await message.answer("⚠️ Ключ слишком короткий. Пришлите действительный ключ.", reply_markup=api_add_cancel_kb())
            return
        
        with SessionLocal() as s:
            user = get_or_create_user(s, message.from_user)
            obj = APIKey(
                user_id=user.id,
                key=key_value,
                qty_req=0,
                is_work=True,
            )
            s.add(obj)
            s.commit()
            s.refresh(obj)
        
        await state.finish()
        await message.answer(f"✅ Ключ добавлен (id={obj.id}).", reply_markup=api_menu_kb())

    @dp.callback_query_handler(lambda c: c.data and c.data.startswith("api_del:"))
    async def api_key_actions(call: types.CallbackQuery):
        """Handle API key actions."""
        action, sid = call.data.split(":")
        sid = int(sid)
        
        with SessionLocal() as s:
            user = get_or_create_user(s, call.from_user)
            key = s.query(APIKey).filter(
                APIKey.id == sid,
                APIKey.user_id == user.id
            ).one_or_none()
            
            if not key:
                await call.answer("Не найдено/нет доступа", show_alert=True)
                return
            
            if action == "api_del":
                s.delete(key)
                s.commit()
                await call.message.edit_text("🗑 Ключ удалён.")
                await call.answer()
                return

