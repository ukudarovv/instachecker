"""Simple Instagram menu handlers."""

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


def get_ig_menu_kb():
    """Get Instagram menu keyboard with Mini App URL if configured."""
    settings = get_settings()
    return instagram_menu_kb(mini_app_url=settings.ig_mini_app_url if settings.ig_mini_app_url else None)


async def process_message(message: dict, session_factory, bot) -> None:
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
        bot.send_message(chat_id, "❌ Добавление сессии отменено.", reply_markup=get_ig_menu_kb())
        return
    
    if text == "Instagram":
        with session_factory() as session:
            user = get_or_create_user(session, message["from"])
            if not ensure_active(user):
                bot.send_message(chat_id, "⛔ Доступ пока не выдан.")
                return
            
            bot.send_message(chat_id, "Раздел «Instagram»", reply_markup=get_ig_menu_kb())

    elif text == "Мои IG-сессии":
        with session_factory() as session:
            user = get_or_create_user(session, message["from"])
            if not ensure_active(user):
                bot.send_message(chat_id, "⛔ Доступ пока не выдан.")
                return
            
            sessions = session.query(InstagramSession).filter(InstagramSession.user_id == user.id).all()
            
            if not sessions:
                bot.send_message(chat_id, "📋 У вас нет IG-сессий.", reply_markup=get_ig_menu_kb())
                return
            
            keyboard = []
            for session_obj in sessions:
                keyboard.append([{
                    "text": f"@{session_obj.ig_username}",
                    "callback_data": f"ig_session:{session_obj.id}"
                }])
            
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
            try:
                from ..services.system_settings import get_global_verify_mode
            except ImportError:
                from services.system_settings import get_global_verify_mode
            
            user = get_or_create_user(session, message["from"])
            is_admin = user.role in ["admin", "superuser"]
            verify_mode = get_global_verify_mode(session)
            bot.send_message(chat_id, "Главное меню", reply_markup=main_menu(is_admin, verify_mode=verify_mode))


def process_callback_query(callback_query: dict, session_factory, bot) -> None:
    """Process Instagram menu callback queries."""
    data = callback_query.get("data", "")
    chat_id = callback_query["message"]["chat"]["id"]
    message_id = callback_query["message"]["message_id"]
    
    if data.startswith("ig_mode:"):
        mode = data.split(":")[1]
        
        if mode == "cookies":
            bot.fsm_states[chat_id] = {"state": "waiting_cookies"}
            bot.send_message(chat_id, "📋 Вставьте cookies в формате JSON:")
        elif mode == "login":
            bot.fsm_states[chat_id] = {"state": "waiting_username"}
            bot.send_message(chat_id, "Введите IG username (под которым будем логиниться):\nДля отмены напишите: /cancel")
        elif mode == "complete":
            bot.fsm_states[chat_id] = {"state": "waiting_complete"}
            bot.send_message(chat_id, "📋 Введите полные данные сессии в формате:\nusername: your_username\npassword: your_password\ncookies: [paste cookies here]")
        elif mode == "cancel":
            if chat_id in bot.fsm_states:
                del bot.fsm_states[chat_id]
            bot.send_message(chat_id, "❌ Добавление сессии отменено.", reply_markup=get_ig_menu_kb())
    
    elif data.startswith("ig_session:"):
        session_id = int(data.split(":")[1])
        
        with session_factory() as session:
            session_obj = session.query(InstagramSession).filter(InstagramSession.id == session_id).first()
            if session_obj:
                bot.send_message(
                    chat_id,
                    f"📋 **Сессия @{session_obj.ig_username}**\n\n"
                    f"🆔 ID: {session_obj.id}\n"
                    f"👤 Username: @{session_obj.ig_username}\n"
                    f"📅 Создана: {session_obj.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                    f"🔄 Последнее использование: {session_obj.last_used_at.strftime('%d.%m.%Y %H:%M') if session_obj.last_used_at else 'Никогда'}"
                )
            else:
                bot.send_message(chat_id, "❌ Сессия не найдена.")
    
    bot.answer_callback_query(callback_query["id"])


def process_instagram_flow(message: dict, session_factory, bot) -> None:
    """Process Instagram session flow messages."""
    text = message.get("text", "")
    chat_id = message["chat"]["id"]
    
    # Handle cancel command
    if text == "/cancel":
        if chat_id in bot.fsm_states:
            del bot.fsm_states[chat_id]
        bot.send_message(chat_id, "❌ Добавление сессии отменено.", reply_markup=get_ig_menu_kb())
        return
    
    # Get current state
    state = bot.fsm_states.get(chat_id, {}).get("state")
    
    if state == "waiting_cookies":
        # Parse cookies
        try:
            cookies = json.loads(text)
            if not isinstance(cookies, list):
                bot.send_message(chat_id, "❌ Неверный формат cookies. Попробуйте еще раз.")
                return
        except json.JSONDecodeError:
            bot.send_message(chat_id, "❌ Неверный JSON формат. Попробуйте еще раз.")
            return
        
        # Save session
        with session_factory() as session:
            user = get_or_create_user(session, message["from"])
            settings = get_settings()
            fernet = OptionalFernet(settings.fernet_key)
            
            obj = save_session(
                session=session,
                user_id=user.id,
                ig_username="unknown",  # Will be updated from cookies
                cookies_json=cookies,
                fernet=fernet,
                ig_password=None
            )
        
        del bot.fsm_states[chat_id]
        bot.send_message(chat_id, f"✅ Сессия создана (id={obj.id}).", reply_markup=get_ig_menu_kb())
    
    elif state == "waiting_username":
        ig_username = text.strip()
        if not ig_username:
            bot.send_message(chat_id, "❌ Username не может быть пустым. Попробуйте еще раз.")
            return
        
        bot.fsm_states[chat_id]["ig_username"] = ig_username
        bot.fsm_states[chat_id]["state"] = "waiting_password"
        bot.send_message(chat_id, "Теперь введите пароль IG:")
    
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
            result = asyncio.run(playwright_login_and_get_cookies(
                ig_username=ig_username,
                ig_password=ig_password,
                headless=settings.ig_headless,
                login_timeout_ms=settings.ig_login_timeout_ms,
                twofa_timeout_ms=settings.ig_2fa_timeout_ms,
                proxy_url=None,  # Без прокси
                bot=bot,
                chat_id=chat_id,
            ))
            
            # Проверяем, требуется ли 2FA
            if isinstance(result, dict) and result.get("status") == "waiting_2fa":
                # Состояние уже установлено в функции, просто выходим
                return
            
            cookies = result
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
            else:
                bot.send_message(
                    chat_id, 
                    f"⚠️ Не удалось выполнить вход.\n\n"
                    f"Ошибка: {error_msg}\n\n"
                    f"💡 **Рекомендация:**\n"
                    f"Автоматический вход работает нестабильно.\n\n"
                    f"👉 Используйте **📋 Импорт cookies** (100% надежно):\n"
                    f"• Войдите в Instagram через браузер\n"
                    f"• Экспортируйте cookies (см. инструкцию)\n"
                    f"• Вставьте в бот"
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
        bot.send_message(chat_id, f"✅ Сессия @{ig_username} создана (id={obj.id}).", reply_markup=get_ig_menu_kb())
    
    elif state == "waiting_complete":
        # Parse complete session data (username, password, cookies)
        try:
            lines = text.strip().split('\n')
            data = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    data[key] = value
            
            # Validate required fields
            if 'username' not in data:
                bot.send_message(chat_id, "❌ Не указан username. Попробуйте еще раз.")
                return
            
            if 'password' not in data:
                bot.send_message(chat_id, "❌ Не указан password. Попробуйте еще раз.")
                return
            
            # Parse cookies if provided
            cookies = []
            if 'cookies' in data and data['cookies'].strip():
                try:
                    cookies = json.loads(data['cookies'])
                except json.JSONDecodeError:
                    bot.send_message(chat_id, "❌ Неверный формат cookies. Попробуйте еще раз.")
                    return
            
            # Save session
            with session_factory() as session:
                user = get_or_create_user(session, message["from"])
                settings = get_settings()
                fernet = OptionalFernet(settings.fernet_key)
                
                obj = save_session(
                    session=session,
                    user_id=user.id,
                    ig_username=data['username'],
                    cookies_json=cookies,
                    fernet=fernet,
                    ig_password=data['password']
                )
            
            del bot.fsm_states[chat_id]
            
            success_msg = f"✅ **Полная сессия создана!**\n\n"
            success_msg += f"👤 **Username:** @{data['username']}\n"
            success_msg += f"🔐 **Password:** {'*' * len(data['password'])}\n"
            success_msg += f"🍪 **Cookies:** {len(cookies)} шт.\n"
            success_msg += f"🆔 **ID сессии:** {obj.id}\n\n"
            success_msg += f"🎯 **Готово к использованию!**"
            
            bot.send_message(chat_id, success_msg, reply_markup=get_ig_menu_kb())
            
        except Exception as e:
            bot.send_message(chat_id, f"❌ Ошибка при создании сессии: {e}")
            return


def register_ig_menu_handlers(bot, session_factory) -> None:
    """Register Instagram menu handlers."""
    print(f"[IG-MENU] 🚀 Starting registration for bot {id(bot)}")
    
    # Create wrapper functions that pass bot parameter
    async def wrapped_process_message(message, session_factory):
        return await process_message(message, session_factory, bot)
    
    def wrapped_process_callback_query(callback_query, session_factory):
        return process_callback_query(callback_query, session_factory, bot)
    
    def wrapped_process_instagram_flow(message, session_factory):
        return process_instagram_flow(message, session_factory, bot)
    
    # Register handlers
    bot.ig_menu_process_message = wrapped_process_message
    bot.ig_menu_process_callback_query = wrapped_process_callback_query
    bot.ig_menu_process_instagram_flow = wrapped_process_instagram_flow
    print(f"[IG-MENU] ✅ Handlers registered: {hasattr(bot, 'ig_menu_process_message')}")
