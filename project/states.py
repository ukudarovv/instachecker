"""FSM States."""

try:
    from aiogram.dispatcher.filters.state import State, StatesGroup
except ImportError:
    # Fallback for direct API usage
    class State:
        pass
    
    class StatesGroup:
        pass


class AddAccountStates(StatesGroup):
    """States for adding account FSM."""
    waiting_for_username = State()
    waiting_for_days = State()


class AddDaysStates(StatesGroup):
    """States for adding days FSM."""
    waiting_for_amount = State()


class RemoveDaysStates(StatesGroup):
    """States for removing days FSM."""
    waiting_for_amount = State()


class AddProxyStates(StatesGroup):
    """States for adding proxy FSM."""
    waiting_for_url = State()      # строка вида scheme://[user:pass@]host:port
    waiting_for_priority = State() # целое 1..10


class IGAddSessionStates(StatesGroup):
    """States for adding Instagram session FSM."""
    choose_mode = State()          # "Импорт cookies" или "Логин по паролю"
    waiting_cookies = State()
    waiting_username = State()
    waiting_password = State()
    waiting_2fa_code = State()     # если решишь реализовать интерактивно — можно задействовать
    choose_proxy = State()         # опционально — привязать прокси


class AddApiKeyStates(StatesGroup):
    """States for adding API key FSM."""
    waiting_for_key = State()


class AdminStates(StatesGroup):
    """States for admin actions FSM."""
    waiting_for_interval = State()
    waiting_for_restart_confirm = State()