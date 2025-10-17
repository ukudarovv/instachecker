"""Keyboard builders."""

try:
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
except ImportError:
    # Fallback for direct API usage
    ReplyKeyboardMarkup = dict
    KeyboardButton = dict


def main_menu(is_admin: bool = False) -> dict:
    """
    Create main menu keyboard with optional admin button.
    
    Args:
        is_admin: Whether to show admin button
        
    Returns:
        dict with keyboard configuration
    """
    keyboard = {
        "keyboard": [
            [{"text": "Добавить аккаунт"}, {"text": "Активные аккаунты"}],
            [{"text": "Аккаунты на проверке"}, {"text": "Проверить аккаунты"}],
            [{"text": "API"}, {"text": "Прокси"}, {"text": "Instagram"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }
    
    if is_admin:
        keyboard["keyboard"].append([{"text": "Админка"}])
    
    return keyboard


def cancel_kb() -> dict:
    """
    Create cancel keyboard.
    
    Returns:
        dict with cancel button
    """
    return {
        "keyboard": [[{"text": "Отмена"}]],
        "resize_keyboard": True,
        "one_time_keyboard": False,
        "selective": True
    }


def pagination_kb(prefix: str, page: int, total_pages: int) -> dict:
    """
    Create pagination keyboard.
    
    Args:
        prefix: 'apg' for active, 'ipg' for inactive/pending
        page: current page
        total_pages: total pages
        
    Returns:
        dict with pagination keyboard
    """
    prev_page = max(1, page - 1)
    next_page = min(total_pages, page + 1)
    
    return {
        "inline_keyboard": [[
            {"text": "⏮", "callback_data": f"{prefix}:1"},
            {"text": "◀️", "callback_data": f"{prefix}:{prev_page}"},
            {"text": f"{page}/{total_pages}", "callback_data": "noop"},
            {"text": "▶️", "callback_data": f"{prefix}:{next_page}"},
            {"text": "⏭", "callback_data": f"{prefix}:{total_pages}"}
        ]]
    }


def accounts_list_kb(prefix: str, items: list) -> dict:
    """
    Create accounts list keyboard.
    
    Args:
        prefix: 'ainfo' for active-card, 'iinfo' for pending-card
        items: list of accounts
        
    Returns:
        dict with accounts list keyboard
    """
    keyboard = []
    for acc in items:
        keyboard.append([{"text": f"@{acc.account} →", "callback_data": f"{prefix}:{acc.id}"}])
    
    return {"inline_keyboard": keyboard}


def account_card_kb(acc_id: int, back_prefix: str, page: int) -> dict:
    """
    Create account card keyboard.
    
    Args:
        acc_id: account ID
        back_prefix: 'apg' or 'ipg' (where to return)
        page: current page
        
    Returns:
        dict with account card keyboard
    """
    return {
        "inline_keyboard": [
            [
                {"text": "➕ День", "callback_data": f"addd:{acc_id}"},
                {"text": "➖ День", "callback_data": f"subd:{acc_id}"}
            ],
            [{"text": "🗑 Удалить", "callback_data": f"delc:{acc_id}"}],
            [{"text": "⬅ Назад", "callback_data": f"{back_prefix}:{page}"}]
        ]
    }


def confirm_delete_kb(acc_id: int, back_prefix: str, page: int) -> dict:
    """
    Create confirm delete keyboard.
    
    Args:
        acc_id: account ID
        back_prefix: 'apg' or 'ipg'
        page: current page
        
    Returns:
        dict with confirm delete keyboard
    """
    return {
        "inline_keyboard": [[
            {"text": "✅ Да", "callback_data": f"delok:{acc_id}:{back_prefix}:{page}"},
            {"text": "❌ Нет", "callback_data": f"delno:{acc_id}:{back_prefix}:{page}"}
        ]]
    }


def proxies_menu_kb() -> dict:
    """
    Create proxies menu keyboard.
    
    Returns:
        dict with proxies menu keyboard
    """
    return {
        "keyboard": [
            [{"text": "Мои прокси"}, {"text": "Добавить прокси"}],
            [{"text": "Тестировать прокси"}],
            [{"text": "Назад в меню"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }


def proxy_card_kb(proxy_id: int) -> dict:
    """
    Create proxy card keyboard.
    
    Args:
        proxy_id: proxy ID
        
    Returns:
        dict with proxy card keyboard
    """
    return {
        "inline_keyboard": [
            [
                {"text": "Отключить", "callback_data": f"prx_off:{proxy_id}"},
                {"text": "Включить", "callback_data": f"prx_on:{proxy_id}"}
            ],
            [
                {"text": "Приоритет −", "callback_data": f"prx_pdec:{proxy_id}"},
                {"text": "Приоритет +", "callback_data": f"prx_pinc:{proxy_id}"}
            ],
            [{"text": "Удалить", "callback_data": f"prx_del:{proxy_id}"}]
        ]
    }


def instagram_menu_kb(mini_app_url: str = None) -> dict:
    """
    Create Instagram menu keyboard.
    
    Args:
        mini_app_url: URL for Telegram Mini App (optional)
    
    Returns:
        dict with Instagram menu keyboard
    """
    keyboard = [
        [{"text": "Добавить IG-сессию"}, {"text": "Мои IG-сессии"}]
    ]
    
    # Add Mini App button if URL is provided
    if mini_app_url:
        keyboard.append([{
            "text": "🔐 Войти через Mini App",
            "web_app": {"url": mini_app_url}
        }])
    
    keyboard.extend([
        [{"text": "Проверить через IG"}],
        [{"text": "Назад в меню"}]
    ])
    
    return {
        "keyboard": keyboard,
        "resize_keyboard": True,
        "one_time_keyboard": False
    }


def ig_add_mode_kb() -> dict:
    """
    Create Instagram add mode keyboard.
    
    Returns:
        dict with Instagram add mode keyboard
    """
    return {
        "inline_keyboard": [
            [{"text": "📋 Импорт cookies (рекомендуется)", "callback_data": "ig_mode:cookies"}],
            [{"text": "🔐 Логин (Playwright)", "callback_data": "ig_mode:login"}],
            [{"text": "❌ Отмена", "callback_data": "ig_mode:cancel"}]
        ]
    }


def api_menu_kb() -> dict:
    """
    Create API menu keyboard.
    
    Returns:
        dict with API menu keyboard
    """
    return {
        "keyboard": [
            [{"text": "Мои API ключи"}, {"text": "Добавить API ключ"}],
            [{"text": "Назад в меню"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }


def api_add_cancel_kb() -> dict:
    """
    Create API key addition keyboard with cancel button.
    
    Returns:
        dict with cancel keyboard for API key addition
    """
    return {
        "keyboard": [
            [{"text": "❌ Отмена"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }


def proxy_add_cancel_kb() -> dict:
    """
    Create proxy addition keyboard with cancel button.
    
    Returns:
        dict with cancel keyboard for proxy addition
    """
    return {
        "keyboard": [
            [{"text": "❌ Отмена"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }


def api_key_card_kb(key_id: int) -> dict:
    """
    Create API key card keyboard.
    
    Args:
        key_id: API key ID
        
    Returns:
        dict with API key card keyboard
    """
    return {
        "inline_keyboard": [
            [
                {"text": "Удалить", "callback_data": f"api_del:{key_id}"}
            ]
        ]
    }


def admin_menu_kb() -> dict:
    """
    Create admin menu keyboard.
    
    Returns:
        dict with admin menu keyboard
    """
    return {
        "keyboard": [
            [{"text": "Интервал автопроверки"}],
            [{"text": "Статистика системы"}],
            [{"text": "Управление пользователями"}],
            [{"text": "Перезапуск бота"}],
            [{"text": "Назад в меню"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }


def user_management_kb() -> dict:
    """
    Create user management menu keyboard.
    
    Returns:
        dict with user management menu keyboard
    """
    return {
        "keyboard": [
            [{"text": "Все пользователи"}, {"text": "Активные"}],
            [{"text": "Неактивные"}, {"text": "Администраторы"}],
            [{"text": "Удалить неактивных"}],
            [{"text": "Назад в админку"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }


def users_list_kb(users: list, page: int = 1, total_pages: int = 1, filter_type: str = "all") -> dict:
    """
    Create users list inline keyboard with pagination.
    
    Args:
        users: list of users to display (already paginated)
        page: current page number
        total_pages: total number of pages
        filter_type: type of filter (all/active/inactive/admin)
        
    Returns:
        dict with users list inline keyboard
    """
    keyboard = []
    
    # User buttons
    for user in users:
        status_icon = "✅" if user.is_active else "❌"
        role_icon = "👑" if user.role in ["admin", "superuser"] else "👤"
        username = user.username or f"id{user.id}"
        keyboard.append([{
            "text": f"{status_icon} {role_icon} {username}",
            "callback_data": f"usr_view:{user.id}:{page}:{filter_type}"
        }])
    
    # Pagination buttons
    if total_pages > 1:
        pagination_row = []
        
        # Previous page button
        if page > 1:
            pagination_row.append({
                "text": "◀️ Назад",
                "callback_data": f"usr_page:{filter_type}:{page - 1}"
            })
        
        # Page indicator
        pagination_row.append({
            "text": f"{page}/{total_pages}",
            "callback_data": "noop"
        })
        
        # Next page button
        if page < total_pages:
            pagination_row.append({
                "text": "Вперёд ▶️",
                "callback_data": f"usr_page:{filter_type}:{page + 1}"
            })
        
        keyboard.append(pagination_row)
    
    # Back button
    keyboard.append([{
        "text": "⬅ Назад в меню",
        "callback_data": "usr_back"
    }])
    
    return {"inline_keyboard": keyboard}


def user_card_kb(user_id: int, is_active: bool, role: str, page: int = 1, filter_type: str = "all") -> dict:
    """
    Create user card keyboard with management actions.
    
    Args:
        user_id: user ID
        is_active: whether user is active
        role: user role (user/admin/superuser)
        page: current page number for back navigation
        filter_type: filter type for back navigation
        
    Returns:
        dict with user card keyboard
    """
    keyboard = []
    
    # Access control row
    if is_active:
        keyboard.append([{"text": "🚫 Отозвать доступ", "callback_data": f"usr_deactivate:{user_id}:{page}:{filter_type}"}])
    else:
        keyboard.append([{"text": "✅ Предоставить доступ", "callback_data": f"usr_activate:{user_id}:{page}:{filter_type}"}])
    
    # Role management row
    if role in ["admin", "superuser"]:
        keyboard.append([{"text": "👤 Снять админа", "callback_data": f"usr_demote:{user_id}:{page}:{filter_type}"}])
    else:
        keyboard.append([{"text": "👑 Сделать админом", "callback_data": f"usr_promote:{user_id}:{page}:{filter_type}"}])
    
    # Verify mode row
    keyboard.append([{"text": "🔄 Изменить режим проверки", "callback_data": f"usr_change_verify:{user_id}:{page}:{filter_type}"}])
    
    # Accounts row
    keyboard.append([{"text": "📱 Показать аккаунты", "callback_data": f"usr_accounts:{user_id}:{page}:{filter_type}"}])
    
    # Delete row
    keyboard.append([{"text": "🗑 Удалить пользователя", "callback_data": f"usr_delete_confirm:{user_id}:{page}:{filter_type}"}])
    
    # Back row
    keyboard.append([{"text": "⬅ Назад к списку", "callback_data": f"usr_page:{filter_type}:{page}"}])
    
    return {"inline_keyboard": keyboard}


def confirm_user_delete_kb(user_id: int, page: int = 1, filter_type: str = "all") -> dict:
    """
    Create confirm user deletion keyboard.
    
    Args:
        user_id: user ID to delete
        page: current page number
        filter_type: filter type
        
    Returns:
        dict with confirm delete keyboard
    """
    return {
        "inline_keyboard": [[
            {"text": "✅ Да, удалить", "callback_data": f"usr_delete_ok:{user_id}:{page}:{filter_type}"},
            {"text": "❌ Отмена", "callback_data": f"usr_view:{user_id}:{page}:{filter_type}"}
        ]]
    }


def confirm_delete_inactive_kb() -> dict:
    """
    Create confirm delete all inactive users keyboard.
    
    Returns:
        dict with confirm delete keyboard
    """
    return {
        "inline_keyboard": [[
            {"text": "✅ Да, удалить всех", "callback_data": "usr_delete_inactive_ok"},
            {"text": "❌ Отмена", "callback_data": "usr_back"}
        ]]
    }


def user_accounts_kb(user_id: int, page: int, total_pages: int, show_active: bool, user_page: int = 1, filter_type: str = "all") -> dict:
    """
    Create keyboard for user accounts pagination.
    
    Args:
        user_id: user ID
        page: current page of accounts
        total_pages: total pages of accounts
        show_active: True for active accounts, False for inactive
        user_page: page number to return to user list
        filter_type: filter type to return to user list
        
    Returns:
        dict with keyboard
    """
    keyboard = []
    
    # Toggle between active/inactive
    if show_active:
        keyboard.append([{
            "text": "⏳ Показать неактивные",
            "callback_data": f"usr_acc_toggle:{user_id}:1:0:{user_page}:{filter_type}"
        }])
    else:
        keyboard.append([{
            "text": "✅ Показать активные",
            "callback_data": f"usr_acc_toggle:{user_id}:1:1:{user_page}:{filter_type}"
        }])
    
    # Pagination
    if total_pages > 1:
        pagination_row = []
        
        if page > 1:
            pagination_row.append({
                "text": "◀️ Назад",
                "callback_data": f"usr_acc_page:{user_id}:{page-1}:{int(show_active)}:{user_page}:{filter_type}"
            })
        
        pagination_row.append({
            "text": f"{page}/{total_pages}",
            "callback_data": "noop"
        })
        
        if page < total_pages:
            pagination_row.append({
                "text": "Вперёд ▶️",
                "callback_data": f"usr_acc_page:{user_id}:{page+1}:{int(show_active)}:{user_page}:{filter_type}"
            })
        
        keyboard.append(pagination_row)
    
    # Back button
    keyboard.append([{
        "text": "⬅ Назад к пользователю",
        "callback_data": f"usr_view:{user_id}:{user_page}:{filter_type}"
    }])
    
    return {"inline_keyboard": keyboard}


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Legacy function for backward compatibility.
    
    Returns:
        ReplyKeyboardMarkup with main menu buttons
    """
    return main_menu(is_admin=True)