"""Instagram session-based checking handlers."""

from sqlalchemy.orm import sessionmaker
try:
    from ..utils.access import get_or_create_user, ensure_active
    from ..models import Account
    from ..services.ig_sessions import get_priority_valid_session
    from ..utils.encryptor import OptionalFernet
    from ..config import get_settings
    from ..services.checker_ig_session import check_username_via_ig_session
except ImportError:
    from utils.access import get_or_create_user, ensure_active
    from models import Account
    from services.ig_sessions import get_priority_valid_session
    from utils.encryptor import OptionalFernet
    from config import get_settings
    from services.checker_ig_session import check_username_via_ig_session


def _fmt_result(d, account=None) -> str:
    """Format check result for display in old bot format."""
    result = f"Имя пользователя: <a href=\"https://www.instagram.com/{d['username']}/\">{d['username']}</a>"
    
    # Add dates and period if account data is available
    if account:
        from datetime import datetime, date
        
        # Calculate time completed
        completed_text = "1 дней"  # Default fallback
        # Используем from_date_time если доступно, иначе from_date
        if hasattr(account, 'from_date_time') and account.from_date_time:
            start_datetime = account.from_date_time
        elif account.from_date:
            if isinstance(account.from_date, datetime):
                start_datetime = account.from_date
            else:
                start_datetime = datetime.combine(account.from_date, datetime.min.time())
        else:
            start_datetime = None
        
        if start_datetime:
            current_datetime = datetime.now()
            time_diff = current_datetime - start_datetime
            
            # If less than 24 hours, show hours
            if time_diff.total_seconds() < 86400:  # 24 hours = 86400 seconds
                hours = int(time_diff.total_seconds() / 3600)
                if hours < 1:
                    hours = 1
                completed_text = f"{hours} часов" if hours > 1 else "1 час"
            else:
                # Show days
                completed_days = time_diff.days + 1  # +1 to include start day
                completed_days = max(1, completed_days)
                completed_text = f"{completed_days} дней"
        
        result += f"""
Начало работ: {account.from_date.strftime("%d.%m.%Y") if account.from_date else "N/A"}
Заявлено: {account.period} дней
Завершено за: {completed_text}
Конец работ: {account.to_date.strftime("%d.%m.%Y") if account.to_date else "N/A"}"""
    
    # Status in old bot format
    if d.get("exists") is True:
        if d.get("is_private"):
            result += "\nСтатус: Аккаунт разблокирован✅"
        else:
            result += "\nСтатус: Аккаунт разблокирован✅"
    elif d.get("exists") is False:
        result += "\nСтатус: Заблокирован❌"
    else:
        result += "\nСтатус: ❓ не удалось определить"
    
    if d.get("error"):
        result += f"\nОшибка: {d['error']}"
    
    return result


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
                
                ig_session = get_priority_valid_session(session, user.id, fernet)
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
                        bot.send_message(chat_id, _fmt_result(info, acc))
                        
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
                        bot.send_message(chat_id, f"❌ Ошибка при проверке <a href=\"https://www.instagram.com/{acc.account}/\">@{acc.account}</a>: {str(e)}")
                        unk += 1
            
            bot.send_message(chat_id, f"Готово: найдено — {ok}, не найдено — {nf}, неизвестно — {unk}.")

    # Register handlers
    bot.check_via_ig_process_message = process_message
