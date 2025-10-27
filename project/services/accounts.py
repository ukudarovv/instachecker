"""Account management services."""

from typing import Optional, List, Tuple
from datetime import date, datetime
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


def create_account(session: Session, user_id: int, username: str, days: int = 30) -> Account:
    """Create new account with calculated dates. Default period is 30 days."""
    days = clamp_min_days(int(days))
    start = today()
    start_datetime = datetime.now()  # Сохраняем точное время добавления
    acc = Account(
        user_id=user_id,
        account=username,
        from_date=start,
        from_date_time=start_datetime,
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
    Сортировка: от старых к новым (по ID).
    """
    q = session.query(Account).filter(and_(Account.user_id == user_id, Account.done == done))
    total = q.count()
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(1, min(page, total_pages))
    items = (
        q.order_by(Account.id.asc())
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


def get_expired_accounts(session: Session) -> List[Account]:
    """
    Get accounts that have expired (to_date < today) and are not done.
    These accounts need user action - extend or delete.
    """
    from datetime import date
    today_date = date.today()
    
    return (
        session.query(Account)
        .filter(
            Account.done == False,
            Account.to_date < today_date
        )
        .order_by(Account.to_date.asc())
        .all()
    )


def get_accounts_expiring_soon(session: Session, days_ahead: int = 3) -> List[Account]:
    """
    Get accounts that will expire in the next N days.
    Used for advance notifications.
    """
    from datetime import date, timedelta
    today_date = date.today()
    future_date = today_date + timedelta(days=days_ahead)
    
    return (
        session.query(Account)
        .filter(
            Account.done == False,
            Account.to_date >= today_date,
            Account.to_date <= future_date
        )
        .order_by(Account.to_date.asc())
        .all()
    )


def mass_delete_accounts_by_usernames(session: Session, user_id: int, usernames: List[str], delete_type: str = "all") -> Tuple[int, List[str]]:
    """
    Mass delete accounts by usernames list.
    
    Args:
        session: Database session
        user_id: User ID
        usernames: List of usernames to delete
        delete_type: Type of deletion - "active", "inactive", or "all"
        
    Returns:
        Tuple of (deleted_count, not_found_usernames)
    """
    deleted_count = 0
    not_found_usernames = []
    
    for username in usernames:
        normalized_username = normalize_username(username)
        
        # Find account by username and user_id
        account = (
            session.query(Account)
            .filter(Account.user_id == user_id, Account.account == normalized_username)
            .one_or_none()
        )
        
        if not account:
            not_found_usernames.append(username)
            continue
            
        # Check deletion type
        if delete_type == "active" and not account.done:
            session.delete(account)
            deleted_count += 1
        elif delete_type == "inactive" and account.done:
            session.delete(account)
            deleted_count += 1
        elif delete_type == "all":
            session.delete(account)
            deleted_count += 1
        else:
            # Account doesn't match the deletion criteria
            continue
    
    session.commit()
    return deleted_count, not_found_usernames


def mass_delete_all_accounts(session: Session, user_id: int, delete_type: str = "all") -> int:
    """
    Mass delete all accounts for user by type.
    
    Args:
        session: Database session
        user_id: User ID
        delete_type: Type of deletion - "active", "inactive", or "all"
        
    Returns:
        Number of deleted accounts
    """
    query = session.query(Account).filter(Account.user_id == user_id)
    
    if delete_type == "active":
        query = query.filter(Account.done == False)
    elif delete_type == "inactive":
        query = query.filter(Account.done == True)
    # For "all", no additional filter needed
    
    accounts = query.all()
    deleted_count = len(accounts)
    
    for account in accounts:
        session.delete(account)
    
    session.commit()
    return deleted_count