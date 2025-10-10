"""Instagram menu handlers."""

import json
from sqlalchemy.orm import sessionmaker
try:
    from ..utils.access import get_or_create_user, ensure_active, ensure_admin
    from ..keyboards import instagram_menu_kb, main_menu, ig_add_mode_kb
    from ..models import InstagramSession
    from ..utils.encryptor import OptionalFernet
    from ..config import get_settings
    from ..services.ig_sessions import save_session
except ImportError:
    from utils.access import get_or_create_user, ensure_active, ensure_admin
    from keyboards import instagram_menu_kb, main_menu, ig_add_mode_kb
    from models import InstagramSession
    from utils.encryptor import OptionalFernet
    from config import get_settings
    from services.ig_sessions import save_session


def register_ig_menu_handlers(bot, session_factory) -> None:
    """Register Instagram menu handlers."""

    def process_message(message: dict, session_factory) -> None:
        """Process Instagram menu messages."""
        text = message.get("text", "")
        chat_id = message["chat"]["id"]
        
        if text == "Instagram":
            with session_factory() as session:
                user = get_or_create_user(session, message["from"])
                if not ensure_active(user):
                    bot.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                bot.send_message(chat_id, "Раздел «Instagram»", reply_markup=instagram_menu_kb())

        elif text == "Мои IG-сессии":
            with session_factory() as session:
                user = get_or_create_user(session, message["from"])
                if not ensure_active(user):
                    bot.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                
                sessions = session.query(InstagramSession).filter(
                    InstagramSession.user_id == user.id
                ).order_by(InstagramSession.created_at.desc()).all()
                
                if not sessions:
                    bot.send_message(chat_id, "📭 У вас нет сохранённых IG-сессий.", reply_markup=instagram_menu_kb())
                    return
                
                lines = []
                for s in sessions:
                    lines.append(f"• id={s.id}, @{s.username}, active={s.is_active}, created={s.created_at}")
                bot.send_message(chat_id, "\n".join(lines), reply_markup=instagram_menu_kb())

        elif text == "Добавить IG-сессию":
            bot.send_message(
                chat_id,
                "Выберите способ добавления сессии:\n"
                "• Импорт cookies (рекомендуется)\n"
                "• Логин (Playwright, потребует пароль и возможен 2FA)",
                reply_markup=instagram_menu_kb()
            )
            bot.send_message(chat_id, "Режим:", reply_markup=ig_add_mode_kb())

        elif text == "Назад в меню":
            with session_factory() as session:
                user = get_or_create_user(session, message["from"])
                is_admin = user.role in ["admin", "superuser"]
                bot.send_message(chat_id, "Главное меню", reply_markup=main_menu(is_admin))

    def process_callback_query(callback_query: dict, session_factory) -> None:
        """Process Instagram menu callback queries."""
        data = callback_query.get("data", "")
        chat_id = callback_query["message"]["chat"]["id"]
        message_id = callback_query["message"]["message_id"]
        
        if data.startswith("ig_mode:"):
            mode = data.split(":")[1]
            
            if mode == "cookies":
                bot.send_message(
                    chat_id,
                    "Пришлите cookies в формате JSON (список объектов, как выдаёт DevTools/Extension).\n"
                    "Минимум: name, value, domain, path."
                )
                # Set FSM state
                bot.fsm_states[chat_id] = {"state": "waiting_cookies", "mode": "cookies"}
                
            elif mode == "login":
                bot.send_message(chat_id, "Введите IG username (под которым будем логиниться):")
                bot.fsm_states[chat_id] = {"state": "waiting_username", "mode": "login"}
            
            bot.answer_callback_query(callback_query["id"])

    def process_instagram_flow(message: dict, session_factory) -> None:
        """Process Instagram session flow messages."""
        text = message.get("text", "")
        chat_id = message["chat"]["id"]
        
        if chat_id not in bot.fsm_states:
            return
            
        state_data = bot.fsm_states[chat_id]
        state = state_data.get("state")
        mode = state_data.get("mode")
        
        settings = get_settings()
        fernet = OptionalFernet(settings.encryption_key)

        if state == "waiting_cookies":
            # JSON с cookie-list
            try:
                cookies = json.loads(text)
                if not isinstance(cookies, list):
                    raise ValueError
            except Exception:
                bot.send_message(chat_id, "⚠️ Неверный JSON. Пришлите **список** cookie-объектов.")
                return
            
            # спросим IG username, чтобы подписать сессию
            bot.fsm_states[chat_id] = {"state": "waiting_username", "mode": "cookies", "cookies": cookies}
            bot.send_message(chat_id, "Укажите IG username для этой сессии (только для подписи):")

        elif state == "waiting_username":
            ig_username = (text or "").strip().lstrip("@")
            bot.fsm_states[chat_id]["ig_username"] = ig_username
            
            if mode == "cookies":
                cookies = bot.fsm_states[chat_id].get("cookies")
                with session_factory() as s:
                    user = get_or_create_user(s, message["from"])
                    obj = save_session(
                        session=s,
                        user_id=user.id,
                        ig_username=ig_username,
                        cookies_json=cookies,
                        fernet=fernet,
                    )
                del bot.fsm_states[chat_id]
                bot.send_message(chat_id, f"✅ Сессия @{ig_username} импортирована (id={obj.id}).", reply_markup=instagram_menu_kb())
                return
            else:
                bot.fsm_states[chat_id]["state"] = "waiting_password"
                bot.send_message(chat_id, "Теперь введите пароль IG:")
                return

        elif state == "waiting_password":
            ig_password = text or ""
            ig_username = bot.fsm_states[chat_id].get("ig_username")
            
            # Выполним headless-логин и сохраним cookies
            try:
                from ..services.ig_login import playwright_login_and_get_cookies
            except ImportError:
                from services.ig_login import playwright_login_and_get_cookies
            
            bot.send_message(chat_id, "⏳ Выполняю вход в IG (может потребоваться 2FA/подтверждение)...")
            
            try:
                import asyncio
                cookies = asyncio.run(playwright_login_and_get_cookies(
                    ig_username=ig_username,
                    ig_password=ig_password,
                    headless=settings.ig_headless,
                    login_timeout_ms=settings.ig_login_timeout_ms,
                    twofa_timeout_ms=settings.ig_2fa_timeout_ms,
                    proxy_url=None,  # Без прокси
                ))
            except Exception as e:
                del bot.fsm_states[chat_id]
                bot.send_message(chat_id, f"⚠️ Не удалось выполнить вход: {str(e)}")
                return
            
            with session_factory() as s:
                user = get_or_create_user(s, message["from"])
                obj = save_session(
                    session=s,
                    user_id=user.id,
                    ig_username=ig_username,
                    cookies_json=cookies,
                    fernet=fernet,
                )
            
            del bot.fsm_states[chat_id]
            bot.send_message(chat_id, f"✅ Сессия @{ig_username} создана (id={obj.id}).", reply_markup=instagram_menu_kb())

    # Register handlers
    bot.ig_menu_process_message = process_message
    bot.ig_menu_process_callback_query = process_callback_query
    bot.ig_menu_process_instagram_flow = process_instagram_flow
