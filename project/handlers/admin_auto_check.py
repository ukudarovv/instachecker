"""Admin handlers for managing user auto-check settings."""

try:
    from ..models import User
    from ..utils.access import ensure_admin
except ImportError:
    from models import User
    from utils.access import ensure_admin


def get_checker_scheduler():
    """Get the global checker scheduler instance."""
    try:
        # Try to import from bot.py's global variable
        import sys
        import importlib
        
        # Check if bot module is loaded
        if 'project.bot' in sys.modules:
            bot_module = sys.modules['project.bot']
            if hasattr(bot_module, '_checker_scheduler'):
                return bot_module._checker_scheduler
        
        # Fallback: try direct import
        try:
            from project.bot import _checker_scheduler
            return _checker_scheduler
        except:
            pass
    except:
        pass
    return None


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
            
            response = "👥 <b>Настройки автопроверки пользователей</b>\n\n"
            
            scheduler = get_checker_scheduler()
            
            for u in users:
                status_emoji = "✅" if u.auto_check_enabled else "❌"
                running_emoji = "🔄" if scheduler and scheduler.is_running() else "⏸️"
                
                response += f"{status_emoji} <b>@{u.username}</b> (ID: {u.id})\n"
                response += f"   • Интервал: {u.auto_check_interval} мин\n"
                response += f"   • Статус: {running_emoji} {'Работает' if scheduler and scheduler.is_running() else 'Не запущен'}\n"
                
                # Get next run time if scheduler is available
                if scheduler:
                    next_run = scheduler.get_next_run_time(user_id=u.id)
                    if next_run:
                        response += f"   • Следующая проверка: {next_run.strftime('%H:%M:%S')}\n"
                
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
            
            # Reload scheduler to update user intervals
            scheduler = get_checker_scheduler()
            if scheduler:
                scheduler.reload_users()
            
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
                
                # Enable autocheck for user
                target_user.auto_check_enabled = True
                session.commit()
            
            # Reload scheduler to update user settings
            scheduler = get_checker_scheduler()
            if scheduler:
                scheduler.reload_users()
            
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
                
                # Disable autocheck for user
                target_user.auto_check_enabled = False
                session.commit()
            
            # Reload scheduler to update user settings
            scheduler = get_checker_scheduler()
            if scheduler:
                scheduler.reload_users()
            
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
        
        scheduler = get_checker_scheduler()
        if not scheduler:
            bot.send_message(message["chat"]["id"], "⚠️ Планировщик автопроверки не инициализирован")
            return
        
        if not scheduler.is_running():
            bot.send_message(message["chat"]["id"], "⚠️ Планировщик не запущен")
            return
        
        with session_factory() as session:
            users = session.query(User).filter(
                User.is_active == True,
                User.auto_check_enabled == True
            ).all()
        
        if not users:
            bot.send_message(message["chat"]["id"], "⚠️ Нет активных пользователей с включенной автопроверкой")
            return
        
        response = f"📊 <b>Статус автопроверки</b>\n\n"
        response += f"Всего пользователей: {len(users)}\n\n"
        
        for u in users:
            status_emoji = "✅" if u.auto_check_enabled else "❌"
            
            response += f"{status_emoji} <b>@{u.username}</b> (ID: {u.id})\n"
            response += f"   • Интервал: {u.auto_check_interval} мин\n"
            
            # Get next run time
            next_run = scheduler.get_next_run_time(user_id=u.id)
            if next_run:
                response += f"   • Следующая проверка: {next_run.strftime('%d.%m %H:%M:%S')}\n"
            
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
            
            # Trigger check manually
            scheduler = get_checker_scheduler()
            if scheduler:
                import asyncio
                bot.send_message(message["chat"]["id"], f"🔄 Запускаю проверку для @{username}...")
                
                # Trigger user check manually
                async def trigger_check():
                    try:
                        from ..cron.auto_checker import check_user_pending_accounts
                        from ..utils.async_bot_wrapper import AsyncBotWrapper
                    except ImportError:
                        from cron.auto_checker import check_user_pending_accounts
                        from utils.async_bot_wrapper import AsyncBotWrapper
                    
                    with session_factory() as session:
                        bot_token = session.query(User).first()  # Get bot token somehow
                        # This is a simplified trigger - in production you'd get bot_token properly
                        async_bot = None  # Would need bot token here
                        await check_user_pending_accounts(
                            user_id=target_user_id,
                            SessionLocal=session_factory,
                            bot=async_bot,
                            max_accounts=999999
                        )
                
                # Run check in background
                try:
                    loop = asyncio.get_event_loop()
                    loop.create_task(trigger_check())
                    bot.send_message(message["chat"]["id"], f"✅ Проверка запущена для @{username}")
                except Exception as e:
                    bot.send_message(message["chat"]["id"], f"❌ Ошибка запуска проверки: {e}")
            else:
                bot.send_message(message["chat"]["id"], "⚠️ Планировщик автопроверки не инициализирован")
            
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

