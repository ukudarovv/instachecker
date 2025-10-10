"""RBAC access control helpers."""

from typing import Iterable
from sqlalchemy.orm import Session

try:
    from ..models import User
except ImportError:
    from models import User


def get_or_create_user(session: Session, tg_user) -> User:
    """
    Возвращает пользователя по Telegram, создаёт, если нет.
    По умолчанию: is_active=False, role='user', verify_mode='api'.
    """
    # Handle both dict (from API) and object (from aiogram) formats
    if isinstance(tg_user, dict):
        user_id = tg_user.get("id")
        username = tg_user.get("username")
    else:
        user_id = tg_user.id
        username = tg_user.username
    
    username = username or f"id{user_id}"
    obj = session.query(User).filter(User.id == user_id).one_or_none()
    if obj:
        # при желании можно синхронизировать username
        if obj.username != username and username:
            obj.username = username
            session.commit()
        return obj
    obj = User(
        id=user_id,
        username=username,
        is_active=False,
        role="user",
        verify_mode="api",
    )
    session.add(obj)
    session.commit()
    return obj


def has_role(user: User, roles: Iterable[str]) -> bool:
    """Check if user has one of the specified roles."""
    return user.role in set(roles)


def is_active(user: User) -> bool:
    """Check if user is active."""
    return bool(user.is_active)


def ensure_active(user: User) -> bool:
    """True если активен, иначе False."""
    return is_active(user)


def ensure_admin(user: User) -> bool:
    """Admin or superuser."""
    return has_role(user, {"admin", "superuser"}) and is_active(user)
