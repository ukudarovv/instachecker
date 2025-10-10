"""Account formatting services."""

try:
    from ..services.accounts import remaining_days
    from ..models import Account
except ImportError:
    from services.accounts import remaining_days
    from models import Account


def format_account_card(acc: Account) -> str:
    """Format account card for display."""
    status = "✅ Завершён" if acc.done else "🕒 На проверке / В работе"
    return (
        "👤 Аккаунт\n"
        f"• username: @{acc.account}\n"
        f"• с: {acc.from_date}\n"
        f"• период (дней): {acc.period}\n"
        f"• до: {acc.to_date}\n"
        f"• осталось: {remaining_days(acc)}\n"
        f"• статус: {status}"
    )
