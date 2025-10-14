"""User management handlers for admin panel."""

import math
from sqlalchemy import func

try:
    from ..keyboards import (
        user_management_kb, 
        users_list_kb, 
        user_card_kb,
        confirm_user_delete_kb,
        confirm_delete_inactive_kb,
        admin_menu_kb,
        user_accounts_kb
    )
    from ..utils.access import ensure_admin
    from ..models import User, Account, APIKey, Proxy, InstagramSession
    from ..services.system_settings import get_auto_check_interval
except ImportError:
    from keyboards import (
        user_management_kb, 
        users_list_kb, 
        user_card_kb,
        confirm_user_delete_kb,
        confirm_delete_inactive_kb,
        admin_menu_kb,
        user_accounts_kb
    )
    from utils.access import ensure_admin
    from models import User, Account, APIKey, Proxy, InstagramSession
    from services.system_settings import get_auto_check_interval


# Constants
USERS_PER_PAGE = 10
ACCOUNTS_PER_PAGE = 10


def register_user_management_handlers(bot, session_factory):
    """
    Register user management handlers.
    
    Args:
        bot: TelegramBot instance
        session_factory: SQLAlchemy session factory
    """
    
    def get_users_page(session, filter_type: str, page: int = 1):
        """Get paginated users list based on filter."""
        query = session.query(User)
        
        if filter_type == "active":
            query = query.filter(User.is_active == True)
        elif filter_type == "inactive":
            query = query.filter(User.is_active == False)
        elif filter_type == "admin":
            query = query.filter(User.role.in_(["admin", "superuser"]))
        
        # Get total count
        total_count = query.count()
        total_pages = math.ceil(total_count / USERS_PER_PAGE) if total_count > 0 else 1
        
        # Get paginated results
        offset = (page - 1) * USERS_PER_PAGE
        users = query.order_by(User.id).offset(offset).limit(USERS_PER_PAGE).all()
        
        return users, total_pages, total_count
    
    def get_accounts_page(session, user_id: int, show_active: bool, page: int = 1):
        """Get paginated accounts list for user."""
        query = session.query(Account).filter(Account.user_id == user_id)
        
        # Filter by status
        if show_active:
            query = query.filter(Account.done == True)
        else:
            query = query.filter(Account.done == False)
        
        # Get total count
        total_count = query.count()
        total_pages = math.ceil(total_count / ACCOUNTS_PER_PAGE) if total_count > 0 else 1
        
        # Get paginated results
        offset = (page - 1) * ACCOUNTS_PER_PAGE
        accounts = query.order_by(Account.id).offset(offset).limit(ACCOUNTS_PER_PAGE).all()
        
        return accounts, total_pages, total_count
    
    def handle_user_management_menu(message, user):
        """Handle Управление пользователями button."""
        if not ensure_admin(user):
            bot.send_message(message["chat"]["id"], "⛔ Доступ запрещен.")
            return
        
        with session_factory() as session:
            total_users = session.query(User).count()
            active_users = session.query(User).filter(User.is_active == True).count()
            inactive_users = session.query(User).filter(User.is_active == False).count()
            admins = session.query(User).filter(
                User.role.in_(["admin", "superuser"])
            ).count()
        
        bot.send_message(
            message["chat"]["id"],
            f"👥 <b>Управление пользователями</b>\n\n"
            f"📊 <b>Статистика:</b>\n"
            f"• Всего пользователей: {total_users}\n"
            f"• Активных: {active_users}\n"
            f"• Неактивных: {inactive_users}\n"
            f"• Администраторов: {admins}\n\n"
            f"Выберите действие:",
            user_management_kb()
        )
    
    def show_users_list(message, filter_type: str, page: int = 1):
        """Show users list with pagination."""
        with session_factory() as session:
            users, total_pages, total_count = get_users_page(session, filter_type, page)
            
            if not users:
                filter_names = {
                    "all": "пользователей",
                    "active": "активных пользователей",
                    "inactive": "неактивных пользователей",
                    "admin": "администраторов"
                }
                bot.send_message(
                    message["chat"]["id"],
                    f"📭 Нет {filter_names.get(filter_type, 'пользователей')}."
                )
                return
            
            # Prepare title
            filter_titles = {
                "all": "Все пользователи",
                "active": "Активные пользователи",
                "inactive": "Неактивные пользователи",
                "admin": "Администраторы"
            }
            filter_icons = {
                "all": "👥",
                "active": "✅",
                "inactive": "❌",
                "admin": "👑"
            }
            
            icon = filter_icons.get(filter_type, "👥")
            title = filter_titles.get(filter_type, "Пользователи")
            
            user_list_text = (
                f"{icon} <b>{title}</b>\n\n"
                f"📊 Всего: {total_count} | Страница {page}/{total_pages}\n\n"
                f"Выберите пользователя:"
            )
            
            bot.send_message(
                message["chat"]["id"],
                user_list_text,
                users_list_kb(users, page, total_pages, filter_type)
            )
    
    def handle_all_users(message, user):
        """Handle Все пользователи button."""
        if not ensure_admin(user):
            bot.send_message(message["chat"]["id"], "⛔ Доступ запрещен.")
            return
        show_users_list(message, "all", 1)
    
    def handle_active_users(message, user):
        """Handle Активные button."""
        if not ensure_admin(user):
            bot.send_message(message["chat"]["id"], "⛔ Доступ запрещен.")
            return
        show_users_list(message, "active", 1)
    
    def handle_inactive_users(message, user):
        """Handle Неактивные button."""
        if not ensure_admin(user):
            bot.send_message(message["chat"]["id"], "⛔ Доступ запрещен.")
            return
        show_users_list(message, "inactive", 1)
    
    def handle_admin_users(message, user):
        """Handle Администраторы button."""
        if not ensure_admin(user):
            bot.send_message(message["chat"]["id"], "⛔ Доступ запрещен.")
            return
        show_users_list(message, "admin", 1)
    
    def handle_delete_inactive(message, user):
        """Handle Удалить неактивных button."""
        if not ensure_admin(user):
            bot.send_message(message["chat"]["id"], "⛔ Доступ запрещен.")
            return
        
        with session_factory() as session:
            inactive_count = session.query(User).filter(
                User.is_active == False
            ).count()
            
            if inactive_count == 0:
                bot.send_message(
                    message["chat"]["id"],
                    "📭 Нет неактивных пользователей для удаления."
                )
                return
            
            bot.send_message(
                message["chat"]["id"],
                f"⚠️ <b>Внимание!</b>\n\n"
                f"Вы собираетесь удалить <b>{inactive_count}</b> неактивных пользователей.\n\n"
                f"Это действие также удалит:\n"
                f"• Все их аккаунты\n"
                f"• Все их API ключи\n"
                f"• Все их прокси\n"
                f"• Все их Instagram сессии\n\n"
                f"<b>Это действие необратимо!</b>\n\n"
                f"Вы уверены?",
                confirm_delete_inactive_kb()
            )
    
    def handle_back_to_admin(message, user):
        """Handle Назад в админку button."""
        if not ensure_admin(user):
            bot.send_message(message["chat"]["id"], "⛔ Доступ запрещен.")
            return
        
        with session_factory() as session:
            interval = get_auto_check_interval(session)
        
        bot.send_message(
            message["chat"]["id"],
            f"⚙️ <b>Админ-панель</b>\n\n"
            f"Текущие настройки:\n"
            f"• Интервал автопроверки: <b>{interval} мин</b>\n\n"
            f"Выберите действие:",
            admin_menu_kb()
        )
    
    # Register callback handlers
    def handle_callback_usr_page(callback_query, user, filter_type, page):
        """Handle pagination callback."""
        if not ensure_admin(user):
            bot.answer_callback_query(callback_query["id"], "⛔ Доступ запрещен")
            return
        
        page = int(page)
        
        with session_factory() as session:
            users, total_pages, total_count = get_users_page(session, filter_type, page)
            
            if not users:
                bot.answer_callback_query(
                    callback_query["id"],
                    "❌ Пользователи не найдены"
                )
                return
            
            # Prepare title
            filter_titles = {
                "all": "Все пользователи",
                "active": "Активные пользователи",
                "inactive": "Неактивные пользователи",
                "admin": "Администраторы"
            }
            filter_icons = {
                "all": "👥",
                "active": "✅",
                "inactive": "❌",
                "admin": "👑"
            }
            
            icon = filter_icons.get(filter_type, "👥")
            title = filter_titles.get(filter_type, "Пользователи")
            
            user_list_text = (
                f"{icon} <b>{title}</b>\n\n"
                f"📊 Всего: {total_count} | Страница {page}/{total_pages}\n\n"
                f"Выберите пользователя:"
            )
            
            bot.edit_message_text(
                callback_query["message"]["chat"]["id"],
                callback_query["message"]["message_id"],
                user_list_text,
                users_list_kb(users, page, total_pages, filter_type)
            )
            
            bot.answer_callback_query(callback_query["id"])
    
    def handle_callback_usr_view(callback_query, user, user_id, page=1, filter_type="all"):
        """Handle usr_view callback - show user details."""
        if not ensure_admin(user):
            bot.answer_callback_query(callback_query["id"], "⛔ Доступ запрещен")
            return
        
        page = int(page) if page else 1
        
        with session_factory() as session:
            target_user = session.query(User).filter(User.id == int(user_id)).first()
            
            if not target_user:
                bot.answer_callback_query(
                    callback_query["id"],
                    "❌ Пользователь не найден"
                )
                return
            
            # Get user statistics
            accounts_count = session.query(Account).filter(
                Account.user_id == user_id
            ).count()
            
            api_keys_count = session.query(APIKey).filter(
                APIKey.user_id == user_id
            ).count()
            
            proxies_count = session.query(Proxy).filter(
                Proxy.user_id == user_id
            ).count()
            
            ig_sessions_count = session.query(InstagramSession).filter(
                InstagramSession.user_id == user_id
            ).count()
            
            # Format role
            role_text = {
                "user": "👤 Пользователь",
                "admin": "👑 Администратор",
                "superuser": "👑 Суперпользователь"
            }.get(target_user.role, "❓ Неизвестно")
            
            # Format status
            status_text = "✅ Активен" if target_user.is_active else "❌ Неактивен"
            
            # Format verify mode
            verify_mode_text = {
                "api": "🔑 API",
                "proxy": "🌐 Прокси",
                "instagram": "📸 Instagram"
            }.get(target_user.verify_mode, "❓ Неизвестно")
            
            user_info = (
                f"👤 <b>Информация о пользователе</b>\n\n"
                f"<b>ID:</b> <code>{target_user.id}</code>\n"
                f"<b>Username:</b> @{target_user.username or 'не указан'}\n"
                f"<b>Статус:</b> {status_text}\n"
                f"<b>Роль:</b> {role_text}\n"
                f"<b>Режим проверки:</b> {verify_mode_text}\n\n"
                f"📊 <b>Статистика:</b>\n"
                f"• Аккаунтов: {accounts_count}\n"
                f"• API ключей: {api_keys_count}\n"
                f"• Прокси: {proxies_count}\n"
                f"• IG-сессий: {ig_sessions_count}\n\n"
                f"Выберите действие:"
            )
            
            bot.edit_message_text(
                callback_query["message"]["chat"]["id"],
                callback_query["message"]["message_id"],
                user_info,
                user_card_kb(target_user.id, target_user.is_active, target_user.role, page, filter_type)
            )
            
            bot.answer_callback_query(callback_query["id"])
    
    def handle_callback_usr_activate(callback_query, user, user_id, page=1, filter_type="all"):
        """Handle usr_activate callback - grant access to user."""
        if not ensure_admin(user):
            bot.answer_callback_query(callback_query["id"], "⛔ Доступ запрещен")
            return
        
        page = int(page) if page else 1
        
        with session_factory() as session:
            target_user = session.query(User).filter(User.id == int(user_id)).first()
            
            if not target_user:
                bot.answer_callback_query(
                    callback_query["id"],
                    "❌ Пользователь не найден"
                )
                return
            
            target_user.is_active = True
            session.commit()
            
            bot.answer_callback_query(
                callback_query["id"],
                f"✅ Доступ предоставлен для {target_user.username}"
            )
            
            # Refresh user card
            handle_callback_usr_view(callback_query, user, user_id, page, filter_type)
    
    def handle_callback_usr_deactivate(callback_query, user, user_id, page=1, filter_type="all"):
        """Handle usr_deactivate callback - revoke access from user."""
        if not ensure_admin(user):
            bot.answer_callback_query(callback_query["id"], "⛔ Доступ запрещен")
            return
        
        page = int(page) if page else 1
        
        # Prevent deactivating yourself
        if user.id == int(user_id):
            bot.answer_callback_query(
                callback_query["id"],
                "⛔ Нельзя отозвать доступ у самого себя!"
            )
            return
        
        with session_factory() as session:
            target_user = session.query(User).filter(User.id == int(user_id)).first()
            
            if not target_user:
                bot.answer_callback_query(
                    callback_query["id"],
                    "❌ Пользователь не найден"
                )
                return
            
            target_user.is_active = False
            session.commit()
            
            bot.answer_callback_query(
                callback_query["id"],
                f"🚫 Доступ отозван для {target_user.username}"
            )
            
            # Refresh user card
            handle_callback_usr_view(callback_query, user, user_id, page, filter_type)
    
    def handle_callback_usr_promote(callback_query, user, user_id, page=1, filter_type="all"):
        """Handle usr_promote callback - make user admin."""
        if not ensure_admin(user):
            bot.answer_callback_query(callback_query["id"], "⛔ Доступ запрещен")
            return
        
        page = int(page) if page else 1
        
        with session_factory() as session:
            target_user = session.query(User).filter(User.id == int(user_id)).first()
            
            if not target_user:
                bot.answer_callback_query(
                    callback_query["id"],
                    "❌ Пользователь не найден"
                )
                return
            
            target_user.role = "admin"
            # Also activate if not active
            if not target_user.is_active:
                target_user.is_active = True
            session.commit()
            
            bot.answer_callback_query(
                callback_query["id"],
                f"👑 {target_user.username} теперь администратор"
            )
            
            # Refresh user card
            handle_callback_usr_view(callback_query, user, user_id, page, filter_type)
    
    def handle_callback_usr_demote(callback_query, user, user_id, page=1, filter_type="all"):
        """Handle usr_demote callback - remove admin role."""
        if not ensure_admin(user):
            bot.answer_callback_query(callback_query["id"], "⛔ Доступ запрещен")
            return
        
        page = int(page) if page else 1
        
        # Prevent demoting yourself
        if user.id == int(user_id):
            bot.answer_callback_query(
                callback_query["id"],
                "⛔ Нельзя снять админа с самого себя!"
            )
            return
        
        with session_factory() as session:
            target_user = session.query(User).filter(User.id == int(user_id)).first()
            
            if not target_user:
                bot.answer_callback_query(
                    callback_query["id"],
                    "❌ Пользователь не найден"
                )
                return
            
            target_user.role = "user"
            session.commit()
            
            bot.answer_callback_query(
                callback_query["id"],
                f"👤 {target_user.username} теперь обычный пользователь"
            )
            
            # Refresh user card
            handle_callback_usr_view(callback_query, user, user_id, page, filter_type)
    
    def handle_callback_usr_accounts(callback_query, user, user_id, page=1, filter_type="all"):
        """Handle usr_accounts callback - show user's Instagram accounts (default: active)."""
        if not ensure_admin(user):
            bot.answer_callback_query(callback_query["id"], "⛔ Доступ запрещен")
            return
        
        # Show active accounts by default
        show_user_accounts(callback_query, user, user_id, page, filter_type, acc_page=1, show_active=True)
    
    def show_user_accounts(callback_query, user, user_id, user_page=1, user_filter="all", acc_page=1, show_active=True):
        """Show paginated accounts list."""
        user_id = int(user_id)
        user_page = int(user_page) if user_page else 1
        acc_page = int(acc_page) if acc_page else 1
        
        with session_factory() as session:
            target_user = session.query(User).filter(User.id == user_id).first()
            
            if not target_user:
                bot.answer_callback_query(
                    callback_query["id"],
                    "❌ Пользователь не найден"
                )
                return
            
            # Get paginated accounts
            accounts, total_pages, total_count = get_accounts_page(session, user_id, show_active, acc_page)
            
            # Get counts for both types
            active_count = session.query(Account).filter(
                Account.user_id == user_id,
                Account.done == True
            ).count()
            
            inactive_count = session.query(Account).filter(
                Account.user_id == user_id,
                Account.done == False
            ).count()
            
            if total_count == 0:
                status_text = "активных" if show_active else "неактивных"
                bot.answer_callback_query(
                    callback_query["id"],
                    f"📭 У пользователя нет {status_text} аккаунтов"
                )
                return
            
            # Build accounts list
            status_icon = "✅" if show_active else "⏳"
            status_text = "Активные (найденные)" if show_active else "Неактивные (на проверке)"
            
            accounts_text = (
                f"📱 <b>Аккаунты пользователя</b> @{target_user.username}\n\n"
                f"{status_icon} <b>{status_text}</b>\n"
                f"Показано: {len(accounts)} из {total_count} | Страница {acc_page}/{total_pages}\n\n"
            )
            
            # Calculate starting number
            start_num = (acc_page - 1) * ACCOUNTS_PER_PAGE + 1
            
            for idx, acc in enumerate(accounts, start_num):
                accounts_text += f"{idx}. <b><a href=\"https://www.instagram.com/{acc.account}/\">@{acc.account}</a></b>\n"
                
                if acc.from_date:
                    accounts_text += f"   📅 С: {acc.from_date}"
                    if acc.to_date:
                        accounts_text += f" → До: {acc.to_date}"
                    accounts_text += "\n"
                elif acc.to_date:
                    accounts_text += f"   📅 До: {acc.to_date}\n"
                
                if acc.period:
                    accounts_text += f"   ⏱ Период: {acc.period} дней\n"
                if acc.date_of_finish:
                    accounts_text += f"   ✅ Завершено: {acc.date_of_finish}\n"
                
                accounts_text += "\n"
            
            # Summary
            accounts_text += (
                f"📊 <b>Итого у пользователя:</b>\n"
                f"• Активных: {active_count}\n"
                f"• Неактивных: {inactive_count}\n"
                f"• Всего: {active_count + inactive_count}"
            )
            
            # Send/edit message
            keyboard = user_accounts_kb(user_id, acc_page, total_pages, show_active, user_page, user_filter)
            
            bot.edit_message_text(
                callback_query["message"]["chat"]["id"],
                callback_query["message"]["message_id"],
                accounts_text,
                keyboard
            )
            
            bot.answer_callback_query(callback_query["id"])
    
    def handle_callback_usr_acc_page(callback_query, user, user_id, acc_page, show_active, user_page, user_filter):
        """Handle accounts pagination callback."""
        if not ensure_admin(user):
            bot.answer_callback_query(callback_query["id"], "⛔ Доступ запрещен")
            return
        
        show_active = bool(int(show_active))
        show_user_accounts(callback_query, user, user_id, user_page, user_filter, acc_page, show_active)
    
    def handle_callback_usr_acc_toggle(callback_query, user, user_id, acc_page, show_active, user_page, user_filter):
        """Handle toggle between active/inactive accounts."""
        if not ensure_admin(user):
            bot.answer_callback_query(callback_query["id"], "⛔ Доступ запрещен")
            return
        
        show_active = bool(int(show_active))
        show_user_accounts(callback_query, user, user_id, user_page, user_filter, acc_page, show_active)
    
    def handle_callback_usr_delete_confirm(callback_query, user, user_id, page=1, filter_type="all"):
        """Handle usr_delete_confirm callback - ask for confirmation."""
        if not ensure_admin(user):
            bot.answer_callback_query(callback_query["id"], "⛔ Доступ запрещен")
            return
        
        page = int(page) if page else 1
        
        # Prevent deleting yourself
        if user.id == int(user_id):
            bot.answer_callback_query(
                callback_query["id"],
                "⛔ Нельзя удалить самого себя!"
            )
            return
        
        with session_factory() as session:
            target_user = session.query(User).filter(User.id == int(user_id)).first()
            
            if not target_user:
                bot.answer_callback_query(
                    callback_query["id"],
                    "❌ Пользователь не найден"
                )
                return
            
            # Get counts for confirmation
            accounts_count = session.query(Account).filter(
                Account.user_id == user_id
            ).count()
            
            warning_text = (
                f"⚠️ <b>ВНИМАНИЕ!</b>\n\n"
                f"Вы собираетесь удалить пользователя:\n"
                f"<b>@{target_user.username}</b> (ID: {target_user.id})\n\n"
                f"Это также удалит:\n"
                f"• {accounts_count} аккаунтов\n"
                f"• Все API ключи\n"
                f"• Все прокси\n"
                f"• Все IG-сессии\n\n"
                f"<b>Это действие необратимо!</b>\n\n"
                f"Вы уверены?"
            )
            
            bot.edit_message_text(
                callback_query["message"]["chat"]["id"],
                callback_query["message"]["message_id"],
                warning_text,
                confirm_user_delete_kb(user_id, page, filter_type)
            )
            
            bot.answer_callback_query(callback_query["id"])
    
    def handle_callback_usr_delete_ok(callback_query, user, user_id, page=1, filter_type="all"):
        """Handle usr_delete_ok callback - actually delete user."""
        if not ensure_admin(user):
            bot.answer_callback_query(callback_query["id"], "⛔ Доступ запрещен")
            return
        
        page = int(page) if page else 1
        
        # Prevent deleting yourself
        if user.id == int(user_id):
            bot.answer_callback_query(
                callback_query["id"],
                "⛔ Нельзя удалить самого себя!"
            )
            return
        
        with session_factory() as session:
            target_user = session.query(User).filter(User.id == int(user_id)).first()
            
            if not target_user:
                bot.answer_callback_query(
                    callback_query["id"],
                    "❌ Пользователь не найден"
                )
                return
            
            username = target_user.username
            session.delete(target_user)
            session.commit()
            
            bot.edit_message_text(
                callback_query["message"]["chat"]["id"],
                callback_query["message"]["message_id"],
                f"✅ Пользователь @{username} (ID: {user_id}) успешно удален.\n\n"
                f"Все связанные данные также удалены."
            )
            
            bot.answer_callback_query(
                callback_query["id"],
                f"✅ Пользователь {username} удален"
            )
    
    def handle_callback_usr_back(callback_query, user):
        """Handle usr_back callback - go back to user management menu."""
        if not ensure_admin(user):
            bot.answer_callback_query(callback_query["id"], "⛔ Доступ запрещен")
            return
        
        with session_factory() as session:
            total_users = session.query(User).count()
            active_users = session.query(User).filter(User.is_active == True).count()
            inactive_users = session.query(User).filter(User.is_active == False).count()
            admins = session.query(User).filter(
                User.role.in_(["admin", "superuser"])
            ).count()
        
        bot.edit_message_text(
            callback_query["message"]["chat"]["id"],
            callback_query["message"]["message_id"],
            f"👥 <b>Управление пользователями</b>\n\n"
            f"📊 <b>Статистика:</b>\n"
            f"• Всего пользователей: {total_users}\n"
            f"• Активных: {active_users}\n"
            f"• Неактивных: {inactive_users}\n"
            f"• Администраторов: {admins}\n\n"
            f"Используйте кнопки меню ниже для управления пользователями."
        )
        
        bot.answer_callback_query(callback_query["id"])
    
    def handle_callback_delete_inactive_ok(callback_query, user):
        """Handle usr_delete_inactive_ok callback - delete all inactive users."""
        if not ensure_admin(user):
            bot.answer_callback_query(callback_query["id"], "⛔ Доступ запрещен")
            return
        
        with session_factory() as session:
            # Get all inactive users
            inactive_users = session.query(User).filter(
                User.is_active == False
            ).all()
            
            if not inactive_users:
                bot.answer_callback_query(
                    callback_query["id"],
                    "📭 Нет неактивных пользователей"
                )
                return
            
            # Prevent deleting yourself (safety check)
            inactive_users = [u for u in inactive_users if u.id != user.id]
            
            count = len(inactive_users)
            
            # Delete all inactive users
            for inactive_user in inactive_users:
                session.delete(inactive_user)
            
            session.commit()
            
            bot.edit_message_text(
                callback_query["message"]["chat"]["id"],
                callback_query["message"]["message_id"],
                f"✅ <b>Удаление завершено!</b>\n\n"
                f"Удалено пользователей: <b>{count}</b>\n"
                f"Все связанные данные также удалены."
            )
            
            bot.answer_callback_query(
                callback_query["id"],
                f"✅ Удалено {count} пользователей"
            )
    
    # Register message handlers
    return {
        "Управление пользователями": handle_user_management_menu,
        "Все пользователи": handle_all_users,
        "Активные": handle_active_users,
        "Неактивные": handle_inactive_users,
        "Администраторы": handle_admin_users,
        "Удалить неактивных": handle_delete_inactive,
        "Назад в админку": handle_back_to_admin,
    }, {
        # Callback handlers with pattern matching
        "usr_page": handle_callback_usr_page,
        "usr_view": handle_callback_usr_view,
        "usr_activate": handle_callback_usr_activate,
        "usr_deactivate": handle_callback_usr_deactivate,
        "usr_promote": handle_callback_usr_promote,
        "usr_demote": handle_callback_usr_demote,
        "usr_accounts": handle_callback_usr_accounts,
        "usr_acc_page": handle_callback_usr_acc_page,
        "usr_acc_toggle": handle_callback_usr_acc_toggle,
        "usr_delete_confirm": handle_callback_usr_delete_confirm,
        "usr_delete_ok": handle_callback_usr_delete_ok,
        "usr_back": handle_callback_usr_back,
        "usr_delete_inactive_ok": handle_callback_delete_inactive_ok,
    }
