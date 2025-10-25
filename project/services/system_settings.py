"""System settings service."""

from sqlalchemy.orm import Session
from typing import Optional

try:
    from ..models import SystemSettings
except ImportError:
    from models import SystemSettings


def get_setting(session: Session, key: str, default: str = None) -> Optional[str]:
    """
    Get system setting value by key.
    
    Args:
        session: Database session
        key: Setting key
        default: Default value if not found
        
    Returns:
        Setting value or default
    """
    setting = session.query(SystemSettings).filter(SystemSettings.key == key).first()
    return setting.value if setting else default


def set_setting(session: Session, key: str, value: str) -> SystemSettings:
    """
    Set system setting value.
    
    Args:
        session: Database session
        key: Setting key
        value: Setting value
        
    Returns:
        SystemSettings object
    """
    setting = session.query(SystemSettings).filter(SystemSettings.key == key).first()
    
    if setting:
        setting.value = value
    else:
        setting = SystemSettings(key=key, value=value)
        session.add(setting)
    
    session.commit()
    session.refresh(setting)
    return setting


def get_auto_check_interval(session: Session) -> int:
    """
    Get auto-check interval in minutes.
    
    Args:
        session: Database session
        
    Returns:
        Interval in minutes (default: 5)
    """
    value = get_setting(session, "auto_check_interval_minutes", "5")
    try:
        return int(value)
    except:
        return 5


def set_auto_check_interval(session: Session, minutes: int) -> SystemSettings:
    """
    Set auto-check interval in minutes.
    
    Args:
        session: Database session
        minutes: Interval in minutes
        
    Returns:
        SystemSettings object
    """
    if minutes < 1:
        minutes = 1
    if minutes > 1440:  # Max 1 day
        minutes = 1440
    
    return set_setting(session, "auto_check_interval_minutes", str(minutes))


def get_global_verify_mode(session: Session) -> str:
    """
    Get global verification mode.
    
    Args:
        session: Database session
        
    Returns:
        Global verification mode (default: api+instagram)
    """
    return get_setting(session, "global_verify_mode", "api+instagram")


def set_global_verify_mode(session: Session, mode: str) -> SystemSettings:
    """
    Set global verification mode.
    
    Args:
        session: Database session
        mode: Verification mode
        
    Returns:
        SystemSettings object
    """
    valid_modes = [
        "api+instagram", "api+proxy", "api+proxy+instagram",
        "instagram+proxy", "instagram", "proxy", "simple_monitor", "full_bypass",
        "api-v2"
    ]
    
    if mode not in valid_modes:
        raise ValueError(f"Invalid verification mode: {mode}")
    
    return set_setting(session, "global_verify_mode", mode)