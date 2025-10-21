"""Admin menu handlers."""

import os

try:
    from ..keyboards import admin_menu_kb, main_menu, admin_verify_mode_selection_kb
    from ..utils.access import get_or_create_user, ensure_active, ensure_admin
    from ..services.system_settings import get_auto_check_interval, set_auto_check_interval, get_global_verify_mode, set_global_verify_mode
    from ..models import Account, User, APIKey, Proxy, InstagramSession
    from .user_management import register_user_management_handlers
except ImportError:
    from keyboards import admin_menu_kb, main_menu, admin_verify_mode_selection_kb
    from utils.access import get_or_create_user, ensure_active, ensure_admin
    from services.system_settings import get_auto_check_interval, set_auto_check_interval, get_global_verify_mode, set_global_verify_mode
    from models import Account, User, APIKey, Proxy, InstagramSession
    from handlers.user_management import register_user_management_handlers


def register_admin_menu_handlers(bot, session_factory):
    """
    Register admin menu handlers.
    
    Args:
        bot: TelegramBot instance
        session_factory: SQLAlchemy session factory
    """
    
    def handle_admin_menu(message, user):
        """Handle Админка button."""
        if not ensure_admin(user):
            bot.send_message(message["chat"]["id"], "⛔ Доступ запрещен. Требуются права администратора.")
            return
        
        with session_factory() as session:
            interval = get_auto_check_interval(session)
            current_mode = get_global_verify_mode(session)
        
        bot.send_message(
            message["chat"]["id"],
            f"⚙️ **Админ-панель**\n\n"
            f"Текущие настройки:\n"
            f"• Интервал автопроверки: **{interval} мин**\n"
            f"• Режим проверки: **{current_mode}**\n\n"
            f"Выберите действие:",
            admin_menu_kb()
        )
    
    def handle_interval_menu(message, user):
        """Handle Интервал автопроверки button."""
        if not ensure_admin(user):
            bot.send_message(message["chat"]["id"], "⛔ Доступ запрещен.")
            return
        
        with session_factory() as session:
            interval = get_auto_check_interval(session)
        
        bot.send_message(
            message["chat"]["id"],
            f"⏱ **Интервал автопроверки**\n\n"
            f"Текущий интервал: **{interval} минут**\n\n"
            f"Введите новый интервал (в минутах):\n"
            f"• Минимум: 1 минута\n"
            f"• Максимум: 1440 минут (24 часа)\n"
            f"• Рекомендуемые: 5, 10, 15, 30\n\n"
            f"Или отправьте /cancel для отмены."
        )
    
    def handle_verify_mode_menu(message, user):
        """Handle Режим проверки button."""
        if not ensure_admin(user):
            bot.send_message(message["chat"]["id"], "⛔ Доступ запрещен.")
            return
        
        with session_factory() as session:
            current_mode = get_global_verify_mode(session)
        
        try:
            from ..keyboards import admin_verify_mode_selection_kb
        except ImportError:
            from keyboards import admin_verify_mode_selection_kb
        
        bot.send_message(
            message["chat"]["id"],
            f"🔧 **Режим проверки**\n\n"
            f"Текущий режим: **{current_mode}**\n\n"
            f"Выберите новый режим проверки для всех пользователей:",
            admin_verify_mode_selection_kb(current_mode)
        )
        
    
    def handle_interval_input(message, user):
        """Handle interval input."""
        text = message.get("text", "").strip()
        
        if not text.isdigit():
            bot.send_message(
                message["chat"]["id"],
                "❌ Неверный формат. Введите целое число от 1 до 1440."
            )
            return
        
        interval = int(text)
        
        if interval < 1 or interval > 1440:
            bot.send_message(
                message["chat"]["id"],
                "❌ Интервал должен быть от 1 до 1440 минут.\n"
                "Попробуйте еще раз или отправьте /cancel."
            )
            return
        
        # Save to database
        with session_factory() as session:
            set_auto_check_interval(session, interval)
        
        # Clear FSM state
        user_id = message["from"]["id"]
        if user_id in bot.fsm_states:
            del bot.fsm_states[user_id]
        
        # Calculate stats
        checks_per_hour = 60 // interval
        checks_per_day = checks_per_hour * 24
        
        # Get verify_mode for keyboard
        with session_factory() as session:
            verify_mode = get_global_verify_mode(session)
        
        keyboard = main_menu(is_admin=ensure_admin(user), verify_mode=verify_mode)
        bot.send_message(
            message["chat"]["id"],
            f"✅ **Интервал автопроверки обновлен!**\n\n"
            f"• Новый интервал: **{interval} минут**\n"
            f"• Проверок в час: ~{checks_per_hour}\n"
            f"• Проверок в день: ~{checks_per_day}\n\n"
            f"⚠️ **Важно:** Для применения изменений перезапустите бота!\n"
            f"Текущая сессия использует старый интервал.",
            keyboard
        )
    
    def handle_statistics(message, user):
        """Handle Статистика системы button."""
        if not ensure_admin(user):
            bot.send_message(message["chat"]["id"], "⛔ Доступ запрещен.")
            return
        
        with session_factory() as session:
            # Get statistics
            total_users = session.query(User).count()
            active_users = session.query(User).filter(User.is_active == True).count()
            
            total_accounts = session.query(Account).count()
            active_accounts = session.query(Account).filter(Account.done == True).count()
            pending_accounts = session.query(Account).filter(Account.done == False).count()
            
            total_api_keys = session.query(APIKey).count()
            working_api_keys = session.query(APIKey).filter(APIKey.is_work == True).count()
            
            total_proxies = session.query(Proxy).count()
            active_proxies = session.query(Proxy).filter(Proxy.is_active == True).count()
            
            total_ig_sessions = session.query(InstagramSession).count()
            active_ig_sessions = session.query(InstagramSession).filter(InstagramSession.is_active == True).count()
            
            interval = get_auto_check_interval(session)
        
        # Calculate auto-check stats
        checks_per_hour = 60 // interval
        checks_per_day = checks_per_hour * 24
        
        # Format message
        stats_text = (
            f"📊 **Статистика системы**\n\n"
            f"👥 **Пользователи:**\n"
            f"• Всего: {total_users}\n"
            f"• Активных: {active_users}\n\n"
            f"📱 **Аккаунты:**\n"
            f"• Всего: {total_accounts}\n"
            f"• Найдено: {active_accounts}\n"
            f"• На проверке: {pending_accounts}\n\n"
            f"🔑 **API ключи:**\n"
            f"• Всего: {total_api_keys}\n"
            f"• Рабочих: {working_api_keys}\n\n"
            f"🌐 **Прокси:**\n"
            f"• Всего: {total_proxies}\n"
            f"• Активных: {active_proxies}\n\n"
            f"📸 **IG-сессии:**\n"
            f"• Всего: {total_ig_sessions}\n"
            f"• Активных: {active_ig_sessions}\n\n"
            f"⏱ **Автопроверка:**\n"
            f"• Интервал: {interval} мин\n"
            f"• Проверок/час: ~{checks_per_hour}\n"
            f"• Проверок/день: ~{checks_per_day}"
        )
        
        bot.send_message(message["chat"]["id"], stats_text)
    
    def handle_restart_bot(message, user):
        """Handle Перезапуск бота button."""
        if not ensure_admin(user):
            bot.send_message(message["chat"]["id"], "⛔ Доступ запрещен.")
            return
        
        bot.send_message(
            message["chat"]["id"],
            "🔄 **Перезапуск бота**\n\n"
            "⚠️ **Внимание!** Это остановит бота.\n"
            "Вам нужно будет вручную запустить его снова.\n\n"
            "Вы уверены? Отправьте:\n"
            "• `ДА` - для подтверждения\n"
            "• Любой другой текст - для отмены"
        )
        
        # Set FSM state
        user_id = message["from"]["id"]
        bot.fsm_states[user_id] = {"state": "waiting_for_restart_confirm", "data": {}}
    
    def handle_restart_confirm(message, user):
        """Handle restart confirmation."""
        text = message.get("text", "").strip().upper()
        
        # Clear FSM state
        user_id = message["from"]["id"]
        if user_id in bot.fsm_states:
            del bot.fsm_states[user_id]
        
        if text != "ДА":
            keyboard = admin_menu_kb()
            bot.send_message(
                message["chat"]["id"],
                "❌ Перезапуск отменён.",
                keyboard
            )
            return
        
        # Send final message
        with session_factory() as session:
            verify_mode = get_global_verify_mode(session)
        keyboard = main_menu(is_admin=ensure_admin(user), verify_mode=verify_mode)
        bot.send_message(
            message["chat"]["id"],
            "🔄 Бот перезапускается...\n\n"
            "⏳ Пожалуйста, подождите несколько секунд.\n"
            "Бот автоматически запустится снова.",
            keyboard
        )
        
        # Graceful shutdown with restart (exit code 0)
        import sys
        print("\n[ADMIN] Bot restart requested by admin")
        print("[ADMIN] Shutting down gracefully for restart...")
        sys.exit(0)  # Exit code 0 = auto-restart
    
    # Register user management handlers
    user_mgmt_handlers, user_mgmt_callbacks = register_user_management_handlers(bot, session_factory)
    
    # Combine all handlers
    message_handlers = {
        "Админка": handle_admin_menu,
        "Интервал автопроверки": handle_interval_menu,
        "Режим проверки": handle_verify_mode_menu,
        "Статистика системы": handle_statistics,
        "Перезапуск бота": handle_restart_bot,
    }
    
    # Add user management handlers
    message_handlers.update(user_mgmt_handlers)
    
    fsm_handlers = {
        "waiting_for_interval": handle_interval_input,
        "waiting_for_restart_confirm": handle_restart_confirm,
    }
    
    # Register message handlers
    return message_handlers, fsm_handlers, user_mgmt_callbacks

