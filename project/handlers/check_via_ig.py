"""Instagram session-based checking handlers."""

from sqlalchemy.orm import sessionmaker
try:
    from ..utils.access import get_or_create_user, ensure_active
    from ..models import Account
    from ..services.ig_sessions import get_active_session
    from ..utils.encryptor import OptionalFernet
    from ..config import get_settings
    from ..services.checker_ig_session import check_username_via_ig_session
except ImportError:
    from utils.access import get_or_create_user, ensure_active
    from models import Account
    from services.ig_sessions import get_active_session
    from utils.encryptor import OptionalFernet
    from config import get_settings
    from services.checker_ig_session import check_username_via_ig_session


def _fmt_result(d) -> str:
    """Format check result for display."""
    lines = [f"@{d['username']}"]
    if d.get("full_name"): 
        lines.append(f"Имя: {d['full_name']}")
    if d.get("followers") is not None: 
        lines.append(f"Подписчики: {d['followers']}")
    if d.get("following") is not None: 
        lines.append(f"Подписки: {d['following']}")
    if d.get("posts") is not None: 
        lines.append(f"Посты: {d['posts']}")
    if d.get("exists") is True: 
        lines.append("Статус: ✅ найден")
    elif d.get("exists") is False: 
        lines.append("Статус: ❌ не найден")
    else: 
        lines.append("Статус: ❓ не удалось определить")
    return "\n".join(lines)


def register_check_via_ig_handlers(bot, session_factory) -> None:
    """Register Instagram session checking handlers."""

    def process_message(message: dict, session_factory) -> None:
        """Process Instagram checking messages."""
        text = message.get("text", "")
        chat_id = message["chat"]["id"]
        
        if text == "Проверить через IG":
            settings = get_settings()
            fernet = OptionalFernet(settings.encryption_key)

            with session_factory() as session:
                user = get_or_create_user(session, message["from"])
                if not ensure_active(user):
                    bot.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                
                ig_session = get_active_session(session, user.id)
                if not ig_session:
                    bot.send_message(chat_id, "⚠️ Нет активной IG-сессии. Сначала добавьте её.")
                    return
                
                pending = session.query(Account).filter(
                    Account.user_id == user.id, 
                    Account.done == False
                ).all()

            if not pending:
                bot.send_message(chat_id, "📭 Нет аккаунтов на проверке.")
                return

            ok = nf = unk = 0
            bot.send_message(chat_id, "⏳ Проверяю через IG-сессию...")
            
            for acc in pending:
                with session_factory() as s2:
                    igs2 = s2.query(type(ig_session)).get(ig_session.id)
                    try:
                        import asyncio
                        info = asyncio.run(check_username_via_ig_session(
                            db=s2,
                            ig_session=igs2,
                            fernet=fernet,
                            username=acc.account,
                            timeout_sec=12,
                        ))
                        bot.send_message(chat_id, _fmt_result(info))
                        
                        if info.get("exists") is True:
                            a = s2.query(Account).get(acc.id)
                            if a:
                                a.done = True
                                s2.commit()
                            ok += 1
                        elif info.get("exists") is False:
                            nf += 1
                        else:
                            unk += 1
                    except Exception as e:
                        bot.send_message(chat_id, f"❌ Ошибка при проверке @{acc.account}: {str(e)}")
                        unk += 1
            
            bot.send_message(chat_id, f"Готово: найдено — {ok}, не найдено — {nf}, неизвестно — {unk}.")

    # Register handlers
    bot.check_via_ig_process_message = process_message
