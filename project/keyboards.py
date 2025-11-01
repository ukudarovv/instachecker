"""Keyboard builders."""

try:
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
except ImportError:
    # Fallback for direct API usage
    ReplyKeyboardMarkup = dict
    KeyboardButton = dict


def main_menu(is_admin: bool = False, verify_mode: str = None) -> dict:
    """
    Create main menu keyboard with optional admin button.
    
    Args:
        is_admin: Whether to show admin button
        verify_mode: Current verification mode (to show/hide buttons)
                    - API button is shown ONLY if verify_mode is "api+proxy"
                    - API button is hidden for all other modes
                    - Instagram button is shown if verify_mode contains "instagram"
        
    Returns:
        dict with keyboard configuration
    """
    # Build third row based on verify_mode
    third_row = []
    
    # Show API button ONLY if verify_mode is "api+proxy"
    # Hide API button for all other modes
    if verify_mode and verify_mode.lower() == "api+proxy":
        third_row.append({"text": "API"})
    
    # Always show Proxy button
    third_row.append({"text": "Прокси"})
    
    # Show Instagram button only if verify_mode contains "instagram"
    if verify_mode and "instagram" in verify_mode.lower():
        third_row.append({"text": "Instagram"})
    
    keyboard = {
        "keyboard": [
            [{"text": "Добавить аккаунт"}, {"text": "Активные аккаунты"}],
            [{"text": "Аккаунты на проверке"}],
            [{"text": "Массовое добавление"}, {"text": "Массовое удаление"}],
            third_row
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }
    
    if is_admin:
        keyboard["keyboard"].append([{"text": "Админка"}])
    
    return keyboard


def settings_menu_kb() -> dict:
    """
    Create settings menu keyboard.
    
    Returns:
        dict with settings keyboard configuration
    """
    keyboard = {
        "keyboard": [
            [{"text": "🔄 Режим проверки"}],
            [{"text": "⬅️ Назад в меню"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }
    return keyboard


def admin_verify_mode_selection_kb(current_mode: str) -> dict:
    """
    Create admin verify mode selection keyboard.
    
    Args:
        current_mode: Current global verification mode
    
    Returns:
        dict with inline keyboard for admin mode selection
    """
    modes = [
        # ("api+instagram", "🔑 API + 📸 Instagram (🚀 Undetected)"),
        ("api+proxy", "🔑 API + 🌐 Proxy (🚀 Undetected)"),
        # ("api+proxy+instagram", "🔑 API + 🌐 Proxy + 📸 Instagram (тройная)"),
        # ("instagram+proxy", "📸 Instagram + 🌐 Proxy (без API)"),
        # ("instagram", "📸 Только Instagram (🚀 Undetected)"),
        # ("proxy", "🌐 Только Proxy (🚀 Undetected)"),
        # ("simple_monitor", "⚡ Простой мониторинг (app.py стиль)"),
        # ("full_bypass", "🛡️ Полный обход защиты (все методы)"),
        ("api-v2", "🔑 API v2 + 🌐 Proxy (новый)")
    ]
    
    keyboard = []
    for mode_value, mode_label in modes:
        # Add checkmark to current mode
        if mode_value == current_mode:
            button_text = f"✅ {mode_label}"
        else:
            button_text = mode_label
        
        keyboard.append([{"text": button_text, "callback_data": f"admin_verify_mode:{mode_value}"}])
    
    
    return {
        "inline_keyboard": keyboard
    }


def verify_mode_selection_kb(current_mode: str) -> dict:
    """
    Create verification mode selection keyboard.
    
    Args:
        current_mode: Current verification mode
    
    Returns:
        dict with inline keyboard for mode selection
    """
    modes = [
        # ("api+instagram", "🔑 API + 📸 Instagram"),
        ("api+proxy", "🔑 API + 🌐 Proxy"),
        # ("api+proxy+instagram", "🔑 API + 🌐 Proxy + 📸 Instagram (тройная)"),
        # ("instagram+proxy", "📸 Instagram + 🌐 Proxy (без API)"),
        # ("instagram", "📸 Только Instagram"),
        # ("proxy", "🌐 Только Proxy"),
        # ("simple_monitor", "⚡ Простой мониторинг (как app.py)"),
        # ("full_bypass", "🛡️ Полный обход защиты (все методы)"),
        ("api-v2", "🔑 API v2 + 🌐 Proxy (новый)")
    ]
    
    keyboard = []
    for mode_value, mode_label in modes:
        # Add checkmark to current mode
        if mode_value == current_mode:
            button_text = f"✅ {mode_label}"
        else:
            button_text = mode_label
        
        keyboard.append([{
            "text": button_text,
            "callback_data": f"set_verify_mode:{mode_value}"
        }])
    
    # Add back button
    keyboard.append([{"text": "⬅️ Закрыть", "callback_data": "close_settings"}])
    
    return {"inline_keyboard": keyboard}


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
            [{"text": "Массовое добавление"}, {"text": "Тестировать прокси"}],
            [{"text": "Назад в меню"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }


def proxies_list_kb(items: list) -> dict:
    """
    Create proxies list keyboard (inline).
    
    Args:
        items: list of proxies
        
    Returns:
        dict with proxies list keyboard
    """
    keyboard = []
    for proxy in items:
        status = "✅" if proxy.is_active else "❌"
        label = f"{status} {proxy.scheme}://{proxy.host[:30]}"
        keyboard.append([{
            "text": label,
            "callback_data": f"pinfo:{proxy.id}"
        }])
    
    return {"inline_keyboard": keyboard}


def proxy_card_kb(proxy_id: int, page: int = 1) -> dict:
    """
    Create proxy card keyboard.
    
    Args:
        proxy_id: proxy ID
        page: current page number
        
    Returns:
        dict with proxy card keyboard
    """
    return {
        "inline_keyboard": [
            [
                {"text": "🧪 Проверить с аккаунтом", "callback_data": f"ptest:{proxy_id}:{page}"}
            ],
            [
                {"text": "✅ Активировать", "callback_data": f"pactive:{proxy_id}:{page}"},
                {"text": "❌ Деактивировать", "callback_data": f"pinactive:{proxy_id}:{page}"}
            ],
            [
                {"text": "🗑️ Удалить", "callback_data": f"pdelask:{proxy_id}:{page}"}
            ],
            [
                {"text": "⬅️ К списку", "callback_data": f"ppg:{page}"}
            ]
        ]
    }


def proxy_test_mode_kb() -> dict:
    """
    Create simplified proxy test mode selection keyboard.
    
    Returns:
        dict with test mode keyboard
    """
    return {
        "inline_keyboard": [
            [
                {"text": "📸 Тест скриншота", "callback_data": "ptest_screenshot"},
                {"text": "🎯 Выбрать прокси", "callback_data": "ptest_select"}
            ]
        ]
    }


def proxy_selection_for_test_kb(proxies: list) -> dict:
    """
    Create proxy selection keyboard for testing.
    
    Args:
        proxies: List of active proxies
        
    Returns:
        dict with proxy selection keyboard
    """
    keyboard = []
    
    for proxy in proxies:
        label = f"{proxy.scheme}://{proxy.host[:40]}"
        keyboard.append([
            {"text": label, "callback_data": f"ptest_one:{proxy.id}"}
        ])
    
    # Убираем кнопку "Отмена" из inline клавиатуры
    # Кнопка "Отмена" будет в обычной клавиатуре при вводе username
    
    return {"inline_keyboard": keyboard}


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
            [{"text": "🚀 Полная настройка (логин + пароль + куки)", "callback_data": "ig_mode:complete"}],
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
            [{"text": "Режим проверки"}],
            [{"text": "Отчеты по трафику"}],
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


def mass_add_menu_kb() -> dict:
    """
    Create keyboard for mass addition menu.
    
    Returns:
        dict with keyboard configuration
    """
    keyboard = {
        "keyboard": [
            [{"text": "📝 Массовое добавление аккаунтов"}],
            [{"text": "🌐 Массовое добавление прокси"}],
            [{"text": "🏠 Главное меню"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }
    
    return keyboard


def mass_delete_menu_kb() -> dict:
    """
    Create keyboard for mass deletion menu.
    
    Returns:
        dict with keyboard configuration
    """
    keyboard = {
        "keyboard": [
            [{"text": "🗑️ Удалить активные аккаунты"}],
            [{"text": "🗑️ Удалить неактивные аккаунты"}],
            [{"text": "🗑️ Удалить все аккаунты"}],
            [{"text": "🏠 Главное меню"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }
    
    return keyboard


def mass_delete_confirm_kb() -> dict:
    """
    Create keyboard for mass deletion confirmation.
    
    Returns:
        dict with keyboard configuration
    """
    keyboard = {
        "keyboard": [
            [{"text": "✅ Да, удалить"}],
            [{"text": "❌ Отмена"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }
    
    return keyboard


def back_to_main_kb() -> dict:
    """
    Create keyboard with back to main menu button.
    
    Returns:
        dict with keyboard configuration
    """
    keyboard = {
        "keyboard": [
            [{"text": "🏠 Главное меню"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }
    
    return keyboard


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Legacy function for backward compatibility.
    
    Returns:
        ReplyKeyboardMarkup with main menu buttons
    """
    return main_menu(is_admin=True)


def account_period_kb() -> dict:
    """Keyboard for selecting account period."""
    return {
        "keyboard": [
            [{"text": "📅 7 дней"}, {"text": "📅 14 дней"}],
            [{"text": "📅 30 дней"}, {"text": "📅 60 дней"}],
            [{"text": "❌ Отмена"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }