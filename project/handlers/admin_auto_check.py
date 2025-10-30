"""Admin handlers for managing user auto-check settings."""

try:
    from ..models import User
    from ..utils.access import ensure_admin
    from ..cron.auto_checker_manager import get_auto_checker_manager
except ImportError:
    from models import User
    from utils.access import ensure_admin
    from cron.auto_checker_manager import get_auto_checker_manager


def register_admin_auto_check_handlers(bot, session_factory):
    """
    Register admin handlers for managing user auto-check settings.
    
    Returns:
        dict: Text handlers mapping
    """
    
    text_handlers = {}
    
    def handle_auto_check_users_list(message, user):
        """Show list of all users with auto-check settings."""
        if not ensure_admin(user):
            bot.send_message(message["chat"]["id"], "⛔ Доступ запрещен. Требуются права администратора.")
            return
        
        with session_factory() as session:
            users = session.query(User).filter(User.is_active == True).all()
            
            if not users:
                bot.send_message(message["chat"]["id"], "⚠️ Нет активных пользователей")
                return
            
            # Get manager stats
            manager = get_auto_checker_manager()
            stats = manager.get_all_stats() if manager else {"checkers": []}
            
            # Create stats dict for quick lookup
            stats_dict = {stat["user_id"]: stat for stat in stats["checkers"]}
            
            response = "👥 <b>Настройки автопроверки пользователей</b>\n\n"
            
            for u in users:
                status_emoji = "✅" if u.auto_check_enabled else "❌"
                running_emoji = "🔄" if u.id in stats_dict and stats_dict[u.id]["is_running"] else "⏸️"
                
                response += f"{status_emoji} <b>@{u.username}</b> (ID: {u.id})\n"
                response += f"   • Интервал: {u.auto_check_interval} мин\n"
                response += f"   • Статус: {running_emoji} {'Работает' if u.id in stats_dict else 'Не запущен'}\n"
                
                if u.id in stats_dict:
                    stat = stats_dict[u.id]
                    response += f"   • Всего проверок: {stat['total_checks']}\n"
                    response += f"   • Найдено: {stat['total_found']}\n"
                    if stat['last_check_time']:
                        response += f"   • Последняя проверка: {stat['last_check_time'].strftime('%H:%M:%S')}\n"
                
                response += "\n"
            
            response += "\n<b>Команды для управления:</b>\n"
            response += "/user_autocheck_set {user_id} {interval} - установить интервал\n"
            response += "/user_autocheck_enable {user_id} - включить автопроверку\n"
            response += "/user_autocheck_disable {user_id} - выключить автопроверку\n"
            response += "/user_autocheck_status - показать статус\n"
            response += "/user_autocheck_trigger {user_id} - запустить проверку вручную"
            
            bot.send_message(message["chat"]["id"], response)
    
    def handle_set_user_interval_cmd(message, user):
        """Handle /user_autocheck_set {user_id} {interval}"""
        if not ensure_admin(user):
            bot.send_message(message["chat"]["id"], "⛔ Доступ запрещен.")
            return
        
        text = message.get("text", "").strip()
        parts = text.split()
        
        if len(parts) != 3:
            bot.send_message(
                message["chat"]["id"],
                "❌ Неверный формат.\n"
                "Использование: /user_autocheck_set {user_id} {interval}\n"
                "Пример: /user_autocheck_set 123 10"
            )
            return
        
        try:
            target_user_id = int(parts[1])
            new_interval = int(parts[2])
            
            if new_interval < 1 or new_interval > 1440:
                bot.send_message(message["chat"]["id"], "❌ Интервал должен быть от 1 до 1440 минут")
                return
            
            # Update database
            with session_factory() as session:
                target_user = session.query(User).filter(User.id == target_user_id).first()
                if not target_user:
                    bot.send_message(message["chat"]["id"], f"❌ Пользователь {target_user_id} не найден")
                    return
                
                old_interval = target_user.auto_check_interval
                target_user.auto_check_interval = new_interval
                session.commit()
                
                username = target_user.username
            
            # Update scheduler
            manager = get_auto_checker_manager()
            if manager:
                manager.update_user_interval(target_user_id, new_interval)
            
            bot.send_message(
                message["chat"]["id"],
                f"✅ Интервал для @{username} (ID: {target_user_id}) изменен:\n"
                f"• Было: {old_interval} мин\n"
                f"• Стало: {new_interval} мин"
            )
            
        except ValueError:
            bot.send_message(message["chat"]["id"], "❌ User ID и интервал должны быть числами")
        except Exception as e:
            bot.send_message(message["chat"]["id"], f"❌ Ошибка: {e}")
    
    def handle_enable_user_autocheck_cmd(message, user):
        """Handle /user_autocheck_enable {user_id}"""
        if not ensure_admin(user):
            bot.send_message(message["chat"]["id"], "⛔ Доступ запрещен.")
            return
        
        text = message.get("text", "").strip()
        parts = text.split()
        
        if len(parts) != 2:
            bot.send_message(
                message["chat"]["id"],
                "❌ Неверный формат.\n"
                "Использование: /user_autocheck_enable {user_id}\n"
                "Пример: /user_autocheck_enable 123"
            )
            return
        
        try:
            target_user_id = int(parts[1])
            
            with session_factory() as session:
                target_user = session.query(User).filter(User.id == target_user_id).first()
                if not target_user:
                    bot.send_message(message["chat"]["id"], f"❌ Пользователь {target_user_id} не найден")
                    return
                
                username = target_user.username
                interval = target_user.auto_check_interval
            
            # Enable in manager
            manager = get_auto_checker_manager()
            if manager:
                manager.enable_user_checker(target_user_id, interval)
            
            bot.send_message(
                message["chat"]["id"],
                f"✅ Автопроверка включена для @{username} (ID: {target_user_id})\n"
                f"• Интервал: {interval} мин"
            )
            
        except ValueError:
            bot.send_message(message["chat"]["id"], "❌ User ID должен быть числом")
        except Exception as e:
            bot.send_message(message["chat"]["id"], f"❌ Ошибка: {e}")
    
    def handle_disable_user_autocheck_cmd(message, user):
        """Handle /user_autocheck_disable {user_id}"""
        if not ensure_admin(user):
            bot.send_message(message["chat"]["id"], "⛔ Доступ запрещен.")
            return
        
        text = message.get("text", "").strip()
        parts = text.split()
        
        if len(parts) != 2:
            bot.send_message(
                message["chat"]["id"],
                "❌ Неверный формат.\n"
                "Использование: /user_autocheck_disable {user_id}\n"
                "Пример: /user_autocheck_disable 123"
            )
            return
        
        try:
            target_user_id = int(parts[1])
            
            with session_factory() as session:
                target_user = session.query(User).filter(User.id == target_user_id).first()
                if not target_user:
                    bot.send_message(message["chat"]["id"], f"❌ Пользователь {target_user_id} не найден")
                    return
                
                username = target_user.username
            
            # Disable in manager
            manager = get_auto_checker_manager()
            if manager:
                manager.disable_user_checker(target_user_id)
            
            bot.send_message(
                message["chat"]["id"],
                f"✅ Автопроверка выключена для @{username} (ID: {target_user_id})"
            )
            
        except ValueError:
            bot.send_message(message["chat"]["id"], "❌ User ID должен быть числом")
        except Exception as e:
            bot.send_message(message["chat"]["id"], f"❌ Ошибка: {e}")
    
    def handle_autocheck_status_cmd(message, user):
        """Handle /user_autocheck_status"""
        if not ensure_admin(user):
            bot.send_message(message["chat"]["id"], "⛔ Доступ запрещен.")
            return
        
        manager = get_auto_checker_manager()
        if not manager:
            bot.send_message(message["chat"]["id"], "⚠️ Менеджер автопроверки не инициализирован")
            return
        
        stats = manager.get_all_stats()
        
        if stats["total_checkers"] == 0:
            bot.send_message(message["chat"]["id"], "⚠️ Нет активных планировщиков")
            return
        
        response = f"📊 <b>Статус автопроверки</b>\n\n"
        response += f"Всего планировщиков: {stats['total_checkers']}\n\n"
        
        for stat in stats["checkers"]:
            username = stat.get("username", "Unknown")
            user_id = stat["user_id"]
            interval = stat.get("interval_minutes", "?")
            is_running = "✅" if stat["is_running"] else "❌"
            is_checking = "🔄" if stat["is_checking"] else "⏸️"
            
            response += f"{is_running} <b>@{username}</b> (ID: {user_id})\n"
            response += f"   • Интервал: {interval} мин {is_checking}\n"
            response += f"   • Проверок: {stat['total_checks']}\n"
            response += f"   • Найдено: {stat['total_found']}\n"
            response += f"   • Ошибок: {stat['total_errors']}\n"
            
            if stat['last_check_time']:
                response += f"   • Последняя: {stat['last_check_time'].strftime('%d.%m %H:%M:%S')}\n"
            
            response += "\n"
        
        bot.send_message(message["chat"]["id"], response)
    
    def handle_trigger_user_check_cmd(message, user):
        """Handle /user_autocheck_trigger {user_id}"""
        if not ensure_admin(user):
            bot.send_message(message["chat"]["id"], "⛔ Доступ запрещен.")
            return
        
        text = message.get("text", "").strip()
        parts = text.split()
        
        if len(parts) != 2:
            bot.send_message(
                message["chat"]["id"],
                "❌ Неверный формат.\n"
                "Использование: /user_autocheck_trigger {user_id}\n"
                "Пример: /user_autocheck_trigger 123"
            )
            return
        
        try:
            target_user_id = int(parts[1])
            
            with session_factory() as session:
                target_user = session.query(User).filter(User.id == target_user_id).first()
                if not target_user:
                    bot.send_message(message["chat"]["id"], f"❌ Пользователь {target_user_id} не найден")
                    return
                
                username = target_user.username
            
            # Trigger check
            manager = get_auto_checker_manager()
            if manager:
                import asyncio
                bot.send_message(message["chat"]["id"], f"🔄 Запускаю проверку для @{username}...")
                asyncio.create_task(manager.trigger_user_check(target_user_id))
                bot.send_message(message["chat"]["id"], f"✅ Проверка запущена для @{username}")
            else:
                bot.send_message(message["chat"]["id"], "⚠️ Менеджер автопроверки не инициализирован")
            
        except ValueError:
            bot.send_message(message["chat"]["id"], "❌ User ID должен быть числом")
        except Exception as e:
            bot.send_message(message["chat"]["id"], f"❌ Ошибка: {e}")
    
    # Register handlers
    text_handlers["/user_autocheck_list"] = handle_auto_check_users_list
    text_handlers["/user_autocheck_set"] = handle_set_user_interval_cmd
    text_handlers["/user_autocheck_enable"] = handle_enable_user_autocheck_cmd
    text_handlers["/user_autocheck_disable"] = handle_disable_user_autocheck_cmd
    text_handlers["/user_autocheck_status"] = handle_autocheck_status_cmd
    text_handlers["/user_autocheck_trigger"] = handle_trigger_user_check_cmd
    
    return text_handlers

