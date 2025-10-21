"""Formatting service for proxies."""

from datetime import datetime
from typing import Optional

try:
    from ..models import Proxy
    from ..utils.encryptor import OptionalFernet
    from ..config import get_settings
except ImportError:
    from models import Proxy
    from utils.encryptor import OptionalFernet
    from config import get_settings


def format_proxy_card(proxy: Proxy, show_password: bool = False) -> str:
    """
    Format proxy card for display.
    
    Args:
        proxy: Proxy object
        show_password: Show password in plain text
        
    Returns:
        Formatted string
    """
    # Status
    status_icon = "✅" if proxy.is_active else "❌"
    status_text = "Активен" if proxy.is_active else "Неактивен"
    
    # Build proxy URL
    if proxy.username:
        if show_password and proxy.password:
            try:
                settings = get_settings()
                encryptor = OptionalFernet(settings.encryption_key)
                password = encryptor.decrypt(proxy.password)
                creds = f"{proxy.username}:{password}@"
            except:
                creds = f"{proxy.username}:***@"
        else:
            creds = f"{proxy.username}:***@"
    else:
        creds = ""
    
    proxy_url = f"{proxy.scheme}://{creds}{proxy.host}"
    
    # Statistics
    success_rate = 0
    if proxy.used_count > 0:
        success_rate = int((proxy.success_count / proxy.used_count) * 100)
    
    # Cooldown status
    cooldown_text = ""
    if proxy.cooldown_until:
        if proxy.cooldown_until > datetime.now():
            cooldown_text = f"\n⏸️ Кулдаун до: {proxy.cooldown_until.strftime('%H:%M:%S')}"
        else:
            cooldown_text = "\n✅ Кулдаун истёк"
    
    # Last checked
    last_checked = "Никогда"
    if proxy.last_checked:
        last_checked = proxy.last_checked.strftime('%d.%m.%Y %H:%M:%S')
    
    card = (
        f"🌐 <b>Прокси #{proxy.id}</b>\n\n"
        f"📍 URL: <code>{proxy_url}</code>\n"
        f"📊 Статус: {status_icon} {status_text}\n"
        f"⭐ Приоритет: {proxy.priority}/10\n\n"
        f"📈 <b>Статистика:</b>\n"
        f"• Использований: {proxy.used_count}\n"
        f"• Успешных: {proxy.success_count} ({success_rate}%)\n"
        f"• Серия неудач: {proxy.fail_streak}\n\n"
        f"🕐 Последняя проверка: {last_checked}"
        f"{cooldown_text}"
    )
    
    return card


def format_proxy_short(proxy: Proxy) -> str:
    """
    Format proxy in short form for lists.
    
    Args:
        proxy: Proxy object
        
    Returns:
        Short formatted string
    """
    status_icon = "✅" if proxy.is_active else "❌"
    success_rate = 0
    if proxy.used_count > 0:
        success_rate = int((proxy.success_count / proxy.used_count) * 100)
    
    # Truncate host if too long
    host = proxy.host
    if len(host) > 30:
        host = host[:27] + "..."
    
    return f"{status_icon} {proxy.scheme}://{host} ({success_rate}% success)"


def format_proxies_list_header(
    page: int,
    total_pages: int,
    total_count: int,
    active_count: int
) -> str:
    """
    Format header for proxies list.
    
    Args:
        page: Current page
        total_pages: Total pages
        total_count: Total proxies count
        active_count: Active proxies count
        
    Returns:
        Formatted header
    """
    inactive_count = total_count - active_count
    
    header = (
        f"🌐 <b>Мои прокси</b>\n\n"
        f"📊 Всего: {total_count} | ✅ Активных: {active_count} | ❌ Неактивных: {inactive_count}\n"
        f"📄 Страница {page}/{total_pages}\n\n"
        f"Выберите прокси для просмотра деталей:"
    )
    
    return header


def format_test_result(
    success: bool,
    message: str,
    response_time: Optional[float] = None,
    ip: Optional[str] = None
) -> str:
    """
    Format proxy test result.
    
    Args:
        success: Test success
        message: Result message
        response_time: Response time in seconds
        ip: Detected IP
        
    Returns:
        Formatted result
    """
    if success:
        result = f"✅ <b>Прокси работает!</b>\n\n"
        if ip:
            result += f"🌐 IP: <code>{ip}</code>\n"
        if response_time:
            result += f"⏱️ Время ответа: {response_time:.2f}s\n"
        result += f"\n{message}"
    else:
        result = f"❌ <b>Прокси не работает</b>\n\n{message}"
    
    return result

