"""Account management services."""

from typing import Optional, List, Tuple
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_

try:
    from ..models import Account
    from ..utils.dates import today, add_days, clamp_min_days
except ImportError:
    from models import Account
    from utils.dates import today, add_days, clamp_min_days

PAGE_SIZE = 15


def normalize_username(username: str) -> str:
    """Normalize username by removing @ and converting to lowercase."""
    return (username or "").strip().lstrip("@").lower()


def find_duplicate(session: Session, user_id: int, username: str) -> Optional[Account]:
    """Find duplicate account for user."""
    return (
        session.query(Account)
        .filter(Account.user_id == user_id, Account.account == username)
        .one_or_none()
    )


def create_account(session: Session, user_id: int, username: str, days: int) -> Account:
    """Create new account with calculated dates."""
    days = clamp_min_days(int(days))
    start = today()
    acc = Account(
        user_id=user_id,
        account=username,
        from_date=start,
        period=days,
        to_date=add_days(start, days),
        done=False,
        date_of_finish=None,
    )
    session.add(acc)
    session.commit()
    session.refresh(acc)
    return acc


def get_accounts_page(session: Session, user_id: int, done: bool, page: int) -> Tuple[List[Account], int]:
    """
    Возвращает (items, total_pages) для аккаунтов пользователя по статусу done.
    """
    q = session.query(Account).filter(and_(Account.user_id == user_id, Account.done == done))
    total = q.count()
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(1, min(page, total_pages))
    items = (
        q.order_by(Account.to_date.asc(), Account.account.asc())
         .offset((page - 1) * PAGE_SIZE)
         .limit(PAGE_SIZE)
         .all()
    )
    return items, total_pages


def get_account_by_id(session: Session, user_id: int, acc_id: int) -> Optional[Account]:
    """Get account by ID for specific user."""
    return session.query(Account).filter(and_(Account.user_id == user_id, Account.id == acc_id)).one_or_none()


def remaining_days(acc: Account, ref: Optional[date] = None) -> int:
    """Calculate remaining days for account."""
    ref = ref or today()
    if acc.to_date is None:
        return 0
    delta = (acc.to_date - ref).days + 1
    return max(0, delta)


def increase_days(session: Session, acc: Account, amount: int) -> Account:
    """Increase account period by amount."""
    amount = clamp_min_days(int(amount))
    acc.period = clamp_min_days((acc.period or 0) + amount, 1)
    acc.to_date = add_days(acc.to_date or acc.from_date, amount)
    session.commit()
    session.refresh(acc)
    return acc


def decrease_days(session: Session, acc: Account, amount: int) -> Account:
    """Decrease account period by amount."""
    amount = clamp_min_days(int(amount))
    # нельзя уйти ниже 1 дня и раньше from_date
    new_period = max(1, (acc.period or 1) - amount)
    # как минимум 1 день от from_date
    min_to = add_days(acc.from_date, 1)
    # новый to_date = from_date + new_period
    new_to = add_days(acc.from_date, new_period)
    if new_to < min_to:
        new_to = min_to
        new_period = 1
    acc.period = new_period
    acc.to_date = new_to
    session.commit()
    session.refresh(acc)
    return acc


def delete_account(session: Session, acc: Account) -> None:
    """Delete account from database."""
    session.delete(acc)
    session.commit()
