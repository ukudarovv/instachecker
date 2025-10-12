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
        
        # Handle "Проверить через IG" by delegating to ig_simple_check
        if text == "Проверить через IG":
            if hasattr(bot, 'ig_simple_check_process_message'):
                bot.ig_simple_check_process_message(message, session_factory)
            else:
                bot.send_message(chat_id, "⚠️ Обработчик проверки не зарегистрирован.")
            return
        
        # Handle cancel button
        if text == "❌ Отмена":
            if chat_id in bot.fsm_states:
                del bot.fsm_states[chat_id]
            bot.send_message(chat_id, "❌ Добавление сессии отменено.", reply_markup=instagram_menu_kb())
            return
        
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
                
                # Create inline keyboard with sessions list
                keyboard = []
                for s in sessions:
                    status_icon = "✅" if s.is_active else "❌"
                    date_str = s.created_at.strftime("%d.%m.%Y %H:%M") if s.created_at else "N/A"
                    keyboard.append([{
                        "text": f"{status_icon} @{s.username} ({date_str})",
                        "callback_data": f"ig_session:{s.id}"
                    }])
                
                # Add back button
                keyboard.append([{"text": "⬅ Назад", "callback_data": "ig_back"}])
                
                bot.send_message(
                    chat_id, 
                    f"📋 Ваши IG-сессии ({len(sessions)}):",
                    reply_markup={"inline_keyboard": keyboard}
                )

        elif text == "Добавить IG-сессию":
            bot.send_message(
                chat_id,
                "Выберите способ добавления сессии:\n\n"
                "📋 **Импорт cookies** - рекомендуется для аккаунтов с 2FA\n"
                "  • Войдите в Instagram через браузер\n"
                "  • Экспортируйте cookies\n"
                "  • Надежно и безопасно\n\n"
                "🔐 **Логин через Playwright** - автоматический вход\n"
                "  • Потребует username и password\n"
                "  • Может не работать с 2FA\n"
                "  • Требует установки браузера на сервере"
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
            
            if mode == "cancel":
                # Clear FSM state if any
                if chat_id in bot.fsm_states:
                    del bot.fsm_states[chat_id]
                bot.send_message(chat_id, "❌ Отменено.", reply_markup=instagram_menu_kb())
                bot.answer_callback_query(callback_query["id"])
                return
            
            elif mode == "cookies":
                bot.send_message(
                    chat_id, 
                    "📋 Пришлите cookies в формате JSON.\n\n"
                    "**Как получить cookies:**\n"
                    "1. Откройте Instagram в браузере и войдите\n"
                    "2. Откройте консоль (F12)\n"
                    "3. Во вкладке Application → Cookies → instagram.com\n"
                    "4. Экспортируйте все cookies в JSON\n\n"
                    "Минимально нужны: name, value, domain, path\n\n"
                    "Для отмены напишите: /cancel"
                )
                bot.fsm_states[chat_id] = {"state": "waiting_cookies", "mode": "cookies"}
                
            elif mode == "login":
                bot.send_message(chat_id, "Введите IG username (под которым будем логиниться):\n\nДля отмены напишите: /cancel")
                bot.fsm_states[chat_id] = {"state": "waiting_username", "mode": "login"}
            
            bot.answer_callback_query(callback_query["id"])
        
        elif data == "ig_back":
            # Return to Instagram menu
            bot.send_message(chat_id, "Раздел «Instagram»", reply_markup=instagram_menu_kb())
            bot.answer_callback_query(callback_query["id"])
        
        elif data.startswith("ig_session:"):
            session_id = int(data.split(":")[1])
            # Show session details with delete option
            with session_factory() as session:
                user = get_or_create_user(session, callback_query["from"])
                ig_session = session.query(InstagramSession).filter(
                    InstagramSession.id == session_id,
                    InstagramSession.user_id == user.id
                ).first()
                
                if not ig_session:
                    bot.send_message(chat_id, "❌ Сессия не найдена.")
                    bot.answer_callback_query(callback_query["id"])
                    return
                
                status_icon = "✅" if ig_session.is_active else "❌"
                date_str = ig_session.created_at.strftime("%d.%m.%Y %H:%M") if ig_session.created_at else "N/A"
                
                message_text = (
                    f"📋 Детали IG-сессии:\n\n"
                    f"• ID: {ig_session.id}\n"
                    f"• Username: @{ig_session.username}\n"
                    f"• Статус: {status_icon} {'Активна' if ig_session.is_active else 'Неактивна'}\n"
                    f"• Создана: {date_str}"
                )
                
                keyboard = [
                    [{"text": "🗑 Удалить", "callback_data": f"ig_delete:{session_id}"}],
                    [{"text": "⬅ Назад к списку", "callback_data": "ig_sessions"}]
                ]
                
                bot.send_message(
                    chat_id,
                    message_text,
                    reply_markup={"inline_keyboard": keyboard}
                )
                bot.answer_callback_query(callback_query["id"])
        
        elif data == "ig_sessions":
            # Show sessions list again
            with session_factory() as session:
                user = get_or_create_user(session, callback_query["from"])
                sessions = session.query(InstagramSession).filter(
                    InstagramSession.user_id == user.id
                ).order_by(InstagramSession.created_at.desc()).all()
                
                if not sessions:
                    bot.send_message(chat_id, "📭 У вас нет сохранённых IG-сессий.", reply_markup=instagram_menu_kb())
                    bot.answer_callback_query(callback_query["id"])
                    return
                
                # Create inline keyboard with sessions list
                keyboard = []
                for s in sessions:
                    status_icon = "✅" if s.is_active else "❌"
                    date_str = s.created_at.strftime("%d.%m.%Y %H:%M") if s.created_at else "N/A"
                    keyboard.append([{
                        "text": f"{status_icon} @{s.username} ({date_str})",
                        "callback_data": f"ig_session:{s.id}"
                    }])
                
                # Add back button
                keyboard.append([{"text": "⬅ Назад", "callback_data": "ig_back"}])
                
                bot.send_message(
                    chat_id, 
                    f"📋 Ваши IG-сессии ({len(sessions)}):",
                    reply_markup={"inline_keyboard": keyboard}
                )
                bot.answer_callback_query(callback_query["id"])
        
        elif data.startswith("ig_delete:"):
            session_id = int(data.split(":")[1])
            with session_factory() as session:
                user = get_or_create_user(session, callback_query["from"])
                ig_session = session.query(InstagramSession).filter(
                    InstagramSession.id == session_id,
                    InstagramSession.user_id == user.id
                ).first()
                
                if ig_session:
                    username = ig_session.username
                    session.delete(ig_session)
                    session.commit()
                    bot.send_message(chat_id, f"✅ IG-сессия @{username} удалена.", reply_markup=instagram_menu_kb())
                else:
                    bot.send_message(chat_id, "❌ Сессия не найдена.")
                
                bot.answer_callback_query(callback_query["id"])

    def process_instagram_flow(message: dict, session_factory) -> None:
        """Process Instagram session flow messages."""
        text = message.get("text", "")
        chat_id = message["chat"]["id"]
        
        # Handle cancel command
        if text and text.strip().lower() == "/cancel":
            if chat_id in bot.fsm_states:
                del bot.fsm_states[chat_id]
            bot.send_message(chat_id, "❌ Добавление сессии отменено.", reply_markup=instagram_menu_kb())
            return
        
        if chat_id not in bot.fsm_states:
            return
            
        state_data = bot.fsm_states[chat_id]
        state = state_data.get("state")
        mode = state_data.get("mode")
        
        settings = get_settings()
        fernet = OptionalFernet(settings.encryption_key)

        if state == "waiting_cookies":
            # Parse JSON cookies
            import json
            try:
                cookies = json.loads(text)
                if not isinstance(cookies, list):
                    raise ValueError("Cookies должны быть списком")
            except Exception as e:
                bot.send_message(chat_id, f"⚠️ Неверный JSON: {str(e)}\n\nПришлите **список** cookie-объектов.")
                return
            
            # Ask for IG username to label the session
            bot.fsm_states[chat_id] = {"state": "waiting_username", "mode": "cookies", "cookies": cookies}
            bot.send_message(chat_id, "Укажите IG username для этой сессии (только для подписи):")
            return
        
        elif state == "waiting_username":
            ig_username = (text or "").strip().lstrip("@")
            bot.fsm_states[chat_id]["ig_username"] = ig_username
            
            if mode == "cookies":
                # Save session with imported cookies
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
            
            elif mode == "login":
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
                error_msg = str(e)
                
                # Provide user-friendly error messages
                if "TimeoutError" in error_msg or "Timeout" in error_msg:
                    bot.send_message(
                        chat_id, 
                        "⚠️ Превышено время ожидания при входе в Instagram.\n\n"
                        "💡 Возможные причины:\n"
                        "• Медленное интернет-соединение\n"
                        "• Instagram блокирует автоматический вход\n"
                        "• Требуется подтверждение в приложении\n\n"
                        "👉 Рекомендация: используйте **📋 Импорт cookies** вместо автоматического входа.\n\n"
                        "Это надежнее и работает с любыми аккаунтами!"
                    )
                elif "2FA" in error_msg or "two_factor" in error_msg:
                    bot.send_message(
                        chat_id,
                        "🔐 У вашего аккаунта включена двухфакторная аутентификация (2FA).\n\n"
                        "❌ Автоматический вход с 2FA невозможен.\n\n"
                        "👉 Используйте **📋 Импорт cookies**:\n"
                        "1. Войдите в Instagram через браузер\n"
                        "2. Откройте консоль (F12)\n"
                        "3. Выполните скрипт экспорта cookies\n"
                        "4. Вставьте результат в бот"
                    )
                elif "challenge" in error_msg.lower():
                    bot.send_message(
                        chat_id,
                        "🛡️ Instagram требует дополнительное подтверждение безопасности.\n\n"
                        "❌ Автоматическая обработка невозможна.\n\n"
                        "👉 Решение:\n"
                        "1. Войдите в Instagram через браузер\n"
                        "2. Пройдите проверку безопасности\n"
                        "3. Используйте **📋 Импорт cookies**"
                    )
                else:
                    bot.send_message(
                        chat_id, 
                        f"⚠️ Не удалось выполнить вход.\n\n"
                        f"Ошибка: {error_msg}\n\n"
                        f"💡 Попробуйте:\n"
                        f"• Проверить правильность username и password\n"
                        f"• Использовать **📋 Импорт cookies** (надежнее)"
                    )
                return
            
            with session_factory() as s:
                user = get_or_create_user(s, message["from"])
                obj = save_session(
                    session=s,
                    user_id=user.id,
                    ig_username=ig_username,
                    cookies_json=cookies,
                    fernet=fernet,
                    ig_password=ig_password,  # Save encrypted password for re-login
                )
            
            del bot.fsm_states[chat_id]
            bot.send_message(chat_id, f"✅ Сессия @{ig_username} создана (id={obj.id}).", reply_markup=instagram_menu_kb())

    # Register handlers
    bot.ig_menu_process_message = process_message
    bot.ig_menu_process_callback_query = process_callback_query
    bot.ig_menu_process_instagram_flow = process_instagram_flow
