"""Proxy service for managing proxies."""

from sqlalchemy.orm import Session
from typing import List, Tuple, Optional
from datetime import datetime, timedelta

try:
    from ..models import Proxy
except ImportError:
    from models import Proxy


def get_proxies_page(
    session: Session,
    user_id: int,
    page: int = 1,
    per_page: int = 10,
    active_only: bool = False
) -> Tuple[List[Proxy], int]:
    """
    Get paginated list of user's proxies.
    
    Args:
        session: Database session
        user_id: User ID
        page: Page number (1-based)
        per_page: Items per page
        active_only: Show only active proxies
        
    Returns:
        Tuple of (proxies_list, total_pages)
    """
    query = session.query(Proxy).filter(Proxy.user_id == user_id)
    
    if active_only:
        query = query.filter(Proxy.is_active == True)
    
    # Order by: active first, then by last_checked desc
    query = query.order_by(
        Proxy.is_active.desc(),
        Proxy.last_checked.desc()
    )
    
    total = query.count()
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages
    
    offset = (page - 1) * per_page
    proxies = query.offset(offset).limit(per_page).all()
    
    return proxies, total_pages


def get_proxy_by_id(session: Session, user_id: int, proxy_id: int) -> Optional[Proxy]:
    """
    Get proxy by ID (only if belongs to user).
    
    Args:
        session: Database session
        user_id: User ID
        proxy_id: Proxy ID
        
    Returns:
        Proxy or None
    """
    return session.query(Proxy).filter(
        Proxy.id == proxy_id,
        Proxy.user_id == user_id
    ).first()


def delete_proxy(session: Session, proxy: Proxy) -> bool:
    """
    Delete proxy.
    
    Args:
        session: Database session
        proxy: Proxy object
        
    Returns:
        True if deleted
    """
    try:
        session.delete(proxy)
        session.commit()
        return True
    except Exception:
        session.rollback()
        return False


def toggle_proxy_active(session: Session, proxy: Proxy) -> bool:
    """
    Toggle proxy active status.
    
    Args:
        session: Database session
        proxy: Proxy object
        
    Returns:
        New active status
    """
    try:
        proxy.is_active = not proxy.is_active
        session.commit()
        return proxy.is_active
    except Exception:
        session.rollback()
        return proxy.is_active


def update_proxy_stats(
    session: Session,
    proxy: Proxy,
    success: bool,
    cooldown_seconds: int = 0
) -> None:
    """
    Update proxy statistics after use.
    
    Args:
        session: Database session
        proxy: Proxy object
        success: Was the request successful
        cooldown_seconds: Cooldown duration in seconds
    """
    try:
        proxy.used_count += 1
        proxy.last_checked = datetime.now()
        
        if success:
            proxy.success_count += 1
            proxy.fail_streak = 0
            proxy.cooldown_until = None
        else:
            proxy.fail_streak += 1
            if cooldown_seconds > 0:
                proxy.cooldown_until = datetime.now() + timedelta(seconds=cooldown_seconds)
        
        session.commit()
    except Exception:
        session.rollback()


def get_active_proxies(session: Session, user_id: int) -> List[Proxy]:
    """
    Get all active proxies for user.
    
    Args:
        session: Database session
        user_id: User ID
        
    Returns:
        List of active proxies
    """
    return session.query(Proxy).filter(
        Proxy.user_id == user_id,
        Proxy.is_active == True
    ).order_by(Proxy.priority.asc()).all()


def count_proxies(session: Session, user_id: int) -> dict:
    """
    Count user's proxies by status.
    
    Args:
        session: Database session
        user_id: User ID
        
    Returns:
        dict with counts: {'total', 'active', 'inactive'}
    """
    query = session.query(Proxy).filter(Proxy.user_id == user_id)
    
    total = query.count()
    active = query.filter(Proxy.is_active == True).count()
    inactive = total - active
    
    return {
        'total': total,
        'active': active,
        'inactive': inactive
    }

