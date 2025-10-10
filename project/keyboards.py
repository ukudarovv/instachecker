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


def instagram_menu_kb() -> dict:
    """
    Create Instagram menu keyboard.
    
    Returns:
        dict with Instagram menu keyboard
    """
    return {
        "keyboard": [
            [{"text": "Добавить IG-сессию"}, {"text": "Мои IG-сессии"}],
            [{"text": "Проверить через IG"}],
            [{"text": "Назад в меню"}]
        ],
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
            [{"text": "Импорт cookies", "callback_data": "ig_mode:cookies"}],
            [{"text": "Логин (Playwright)", "callback_data": "ig_mode:login"}]
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
            [{"text": "Проверка через API (все)"}],
            [{"text": "Проверка (API + скриншот)"}],
            [{"text": "Назад в меню"}]
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
                {"text": "Удалить", "callback_data": f"api_del:{key_id}"},
                {"text": "Тест", "callback_data": f"api_test:{key_id}"}
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
            [{"text": "Перезапуск бота"}],
            [{"text": "Назад в меню"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Legacy function for backward compatibility.
    
    Returns:
        ReplyKeyboardMarkup with main menu buttons
    """
    return main_menu(is_admin=True)