"""Hybrid check handlers: API + Instagram with screenshots."""

try:
    from aiogram import types
    from aiogram.dispatcher import Dispatcher
except ImportError:
    types = None
    Dispatcher = None

from sqlalchemy.orm import sessionmaker
import os

try:
    from ..utils.access import get_or_create_user, ensure_active
    from ..models import Account
    from ..services.hybrid_checker import check_account_hybrid
    from ..services.ig_sessions import get_active_session
    from ..utils.encryptor import OptionalFernet
    from ..config import get_settings
except ImportError:
    from utils.access import get_or_create_user, ensure_active
    from models import Account
    from services.hybrid_checker import check_account_hybrid
    from services.ig_sessions import get_active_session
    from utils.encryptor import OptionalFernet
    from config import get_settings


def register_check_hybrid_handlers(dp: Dispatcher, SessionLocal: sessionmaker) -> None:
    """
    Register hybrid check handlers.
    
    Args:
        dp: Aiogram dispatcher
        SessionLocal: SQLAlchemy session factory
    """

    @dp.message_handler(lambda m: m.text == "Проверка (API + скриншот)")
    async def check_all_hybrid(message: types.Message):
        """Check all pending accounts using hybrid method."""
        await message.answer("⏳ Проверяю аккаунты через API + Instagram (со скриншотами)...")
        
        settings = get_settings()
        fernet = OptionalFernet(settings.encryption_key)
        
        with SessionLocal() as s:
            user = get_or_create_user(s, message.from_user)
            if not ensure_active(user):
                await message.answer("⛔ Доступ пока не выдан.")
                return
            
            # Get pending accounts
            accs = s.query(Account).filter(
                Account.user_id == user.id,
                Account.done == False
            ).all()
            
            # Get Instagram session for screenshots
            ig_session = get_active_session(s, user.id)
        
        if not accs:
            await message.answer("📭 Нет аккаунтов на проверке.")
            return
        
        if not ig_session:
            await message.answer(
                "⚠️ Нет активной Instagram-сессии для скриншотов.\n"
                "Будет выполнена только проверка через API.\n"
                "Добавьте IG-сессию через меню 'Instagram' для получения скриншотов."
            )
        
        ok_count = 0
        not_found_count = 0
        unknown_count = 0
        
        for acc in accs:
            with SessionLocal() as s2:
                info = await check_account_hybrid(
                    session=s2,
                    user_id=user.id,
                    username=acc.account,
                    ig_session=ig_session,
                    fernet=fernet
                )
            
            # Count results
            if info["exists"] is True:
                ok_count += 1
            elif info["exists"] is False:
                not_found_count += 1
            else:
                unknown_count += 1
            
            # Format message
            mark = "✅" if info["exists"] is True else ("❌" if info["exists"] is False else "❓")
            
            lines = [f"{mark} @{info['username']}"]
            
            # Add details if available
            if info.get("full_name"):
                lines.append(f"Имя: {info['full_name']}")
            if info.get("followers") is not None:
                lines.append(f"Подписчики: {info['followers']:,}")
            if info.get("following") is not None:
                lines.append(f"Подписки: {info['following']:,}")
            if info.get("posts") is not None:
                lines.append(f"Посты: {info['posts']:,}")
            
            # Add check method info
            check_via = info.get("checked_via", "unknown")
            if check_via == "api+instagram":
                lines.append("🔍 Проверено: API + Instagram")
            elif check_via == "api":
                lines.append("🔍 Проверено: API")
            elif check_via == "instagram_only":
                lines.append("🔍 Проверено: Instagram")
            
            # Add error if any
            if info.get("error"):
                lines.append(f"⚠️ {info['error']}")
            
            caption = "\n".join(lines)
            
            # Send text result
            await message.answer(caption)
            
            # Send screenshot if available
            if info.get("screenshot_path") and os.path.exists(info["screenshot_path"]):
                try:
                    with open(info["screenshot_path"], 'rb') as photo:
                        await message.answer_photo(
                            photo,
                            caption=f"📸 Скриншот @{acc.account}"
                        )
                except Exception as e:
                    print(f"Failed to send photo: {e}")
        
        # Final summary
        summary = (
            f"🎯 Готово!\n\n"
            f"📊 Результаты:\n"
            f"• Найдено: {ok_count}\n"
            f"• Не найдено: {not_found_count}\n"
            f"• Ошибки: {unknown_count}"
        )
        await message.answer(summary)

