"""Check accounts via API handlers."""

try:
    from aiogram import types
    from aiogram.dispatcher import Dispatcher
except ImportError:
    types = None
    Dispatcher = None

from sqlalchemy.orm import sessionmaker

try:
    from ..utils.access import get_or_create_user, ensure_active
    from ..models import Account
    from ..services.check_via_api import check_account_exists_via_api
except ImportError:
    from utils.access import get_or_create_user, ensure_active
    from models import Account
    from services.check_via_api import check_account_exists_via_api


def register_check_via_api_handlers(dp: Dispatcher, SessionLocal: sessionmaker) -> None:
    """
    Register check via API handlers.
    
    Args:
        dp: Aiogram dispatcher
        SessionLocal: SQLAlchemy session factory
    """

    @dp.message_handler(lambda m: m.text == "Проверка через API (все)")
    async def check_all(message: types.Message):
        """Check all pending accounts via RapidAPI."""
        await message.answer("⏳ Проверяю аккаунты через RapidAPI...")
        
        with SessionLocal() as s:
            user = get_or_create_user(s, message.from_user)
            if not ensure_active(user):
                await message.answer("⛔ Доступ пока не выдан.")
                return
            accs = s.query(Account).filter(
                Account.user_id == user.id,
                Account.done == False
            ).all()
        
        if not accs:
            await message.answer("📭 Нет аккаунтов на проверке.")
            return

        ok_count = 0
        not_found_count = 0
        unknown_count = 0
        
        for a in accs:
            with SessionLocal() as s2:
                info = await check_account_exists_via_api(s2, user.id, a.account)
            
            if info["exists"] is True:
                ok_count += 1
            elif info["exists"] is False:
                not_found_count += 1
            else:
                unknown_count += 1
            
            mark = "✅" if info["exists"] is True else ("❌" if info["exists"] is False else "❓")
            error_msg = f" — {info.get('error')}" if info.get('error') else " — ok"
            await message.answer(f"{mark} @{info['username']}{error_msg}")
        
        await message.answer(
            f"Готово: найдено — {ok_count}, не найдено — {not_found_count}, неизвестно — {unknown_count}."
        )

