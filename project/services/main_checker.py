"""
Main Checker - главный сервис проверки аккаунтов.
Логика: API проверка → если успешно → Proxy + скриншот.
"""

import asyncio
import os
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

try:
    from ..models import Account, Proxy
    from ..utils.encryptor import OptionalFernet
    from ..config import get_settings
    from .universal_playwright_checker import check_instagram_account_universal
    from .proxy_service import get_active_proxies
    from .check_via_api import check_account_exists_via_api
except ImportError:
    from models import Account, Proxy
    from utils.encryptor import OptionalFernet
    from config import get_settings
    from services.universal_playwright_checker import check_instagram_account_universal
    from services.proxy_service import get_active_proxies
    from services.check_via_api import check_account_exists_via_api


def build_proxy_url_from_object(proxy: Proxy) -> str:
    """
    Build proxy URL from Proxy object.
    
    Args:
        proxy: Proxy object
        
    Returns:
        Proxy URL string
    """
    if proxy.username and proxy.password:
        try:
            settings = get_settings()
            encryptor = OptionalFernet(settings.encryption_key)
            password = encryptor.decrypt(proxy.password)
            return f"{proxy.scheme}://{proxy.username}:{password}@{proxy.host}"
        except:
            return f"{proxy.scheme}://{proxy.host}"
    else:
        return f"{proxy.scheme}://{proxy.host}"


def get_best_proxy(session: Session, user_id: int) -> Optional[str]:
    """
    Get best available proxy for user.
    
    Args:
        session: Database session
        user_id: User ID
        
    Returns:
        Proxy URL or None
    """
    proxies = get_active_proxies(session, user_id)
    
    if not proxies:
        return None
    
    # Сортируем по приоритету и success rate
    best_proxy = None
    best_score = -1
    
    for proxy in proxies:
        # Пропускаем если в кулдауне
        if proxy.cooldown_until and proxy.cooldown_until > datetime.now():
            continue
        
        # Считаем score
        success_rate = 0
        if proxy.used_count > 0:
            success_rate = proxy.success_count / proxy.used_count
        
        # Score = приоритет (1-10, меньше лучше) + success_rate (0-1)
        # Инвертируем приоритет чтобы 1 было лучше 10
        score = (11 - proxy.priority) * 10 + success_rate * 100
        
        if score > best_score:
            best_score = score
            best_proxy = proxy
    
    if best_proxy:
        return build_proxy_url_from_object(best_proxy)
    
    # Если все в кулдауне - берем первый
    if proxies:
        return build_proxy_url_from_object(proxies[0])
    
    return None


async def check_account_main(
    username: str,
    session: Session,
    user_id: int,
    screenshot_path: Optional[str] = None
) -> Tuple[bool, str, Optional[str]]:
    """
    Главная функция проверки аккаунта.
    Логика: API проверка → если успешно → Proxy + скриншот.
    
    Args:
        username: Instagram username
        session: Database session
        user_id: User ID
        screenshot_path: Path for screenshot (auto-generated if None)
        
    Returns:
        Tuple of (success, message, screenshot_path)
    """
    print(f"\n[MAIN-CHECKER] 🔍 Проверка @{username}")
    
    # ШАГ 1: API проверка (быстрая)
    print(f"[MAIN-CHECKER] 📡 Шаг 1: API проверка...")
    api_result = await check_account_exists_via_api(session, user_id, username)
    api_success = api_result.get("exists", False)
    api_error = api_result.get("error")
    api_message = "найден" if api_success else "не найден"
    
    # Check for API key exhaustion
    if api_error == "all_api_keys_exhausted":
        print(f"[MAIN-CHECKER] ❌ Все API ключи исчерпаны для пользователя {user_id}")
        return False, "Все API ключи исчерпаны.", None
    elif api_error == "no_api_keys_available":
        print(f"[MAIN-CHECKER] ❌ Нет доступных API ключей для пользователя {user_id}")
        return False, "Нет доступных API ключей.", None
    
    if not api_success:
        print(f"[MAIN-CHECKER] ❌ API проверка не прошла: {api_message}")
        return False, f"API: {api_message}", None
    
    print(f"[MAIN-CHECKER] ✅ API проверка прошла успешно")
    
    # ШАГ 2: Проверяем наличие прокси
    proxy_url = get_best_proxy(session, user_id)
    
    if not proxy_url:
        print(f"[MAIN-CHECKER] ⚠️ Прокси не найден, возвращаем только API результат")
        return True, f"API: {api_message}", None
    
    print(f"[MAIN-CHECKER] 🌐 Найден прокси: {proxy_url[:50]}...")
    
    # ШАГ 3: Proxy + полный скриншот с темной темой в desktop формате
    print(f"[MAIN-CHECKER] 📸 Шаг 2: Proxy проверка + полный скриншот (темная тема, desktop)...")
    
    # Генерируем путь для скриншота если не указан
    if not screenshot_path:
        screenshots_dir = "screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(screenshots_dir, f"{username}_{timestamp}.png")
    
    # Импортируем функцию проверки с полным скриншотом
    try:
        from .ig_screenshot import check_account_with_header_screenshot
    except ImportError:
        from services.ig_screenshot import check_account_with_header_screenshot
    
    # Проверяем через чекер с обычным скриншотом в desktop формате
    proxy_result = await check_account_with_header_screenshot(
        username=username,
        proxy_url=proxy_url,
        screenshot_path=screenshot_path,
        headless=True,
        timeout_ms=60000,  # Увеличиваем timeout до 60 секунд
        dark_theme=True,  # Темная тема (черный фон)
        mobile_emulation=False,  # Desktop формат (не мобильная эмуляция)
        crop_ratio=0  # БЕЗ обрезки - полный скриншот страницы
    )
    
    # Адаптируем результат к старому формату
    proxy_success = proxy_result.get("exists", False)
    proxy_message = proxy_result.get("checked_via", "proxy_screenshot")
    screenshot = screenshot_path if os.path.exists(screenshot_path) else None
    profile_data = proxy_result  # Сохраняем полный результат
    
    # Обновляем статистику прокси
    try:
        from .proxy_service import update_proxy_stats
        
        # Находим прокси для обновления статистики
        proxies = session.query(Proxy).filter(
            Proxy.user_id == user_id,
            Proxy.is_active == True
        ).all()
        
        for proxy in proxies:
            if build_proxy_url_from_object(proxy) == proxy_url:
                update_proxy_stats(session, proxy, proxy_success)
                print(f"[MAIN-CHECKER] 📊 Статистика прокси обновлена")
                break
                
    except Exception as e:
        print(f"[MAIN-CHECKER] ⚠️ Не удалось обновить статистику прокси: {e}")
    
    # Результат: API успешно + Proxy результат
    if proxy_success:
        print(f"[MAIN-CHECKER] ✅ API + Proxy: успешно")
        return True, f"API: {api_message} | Proxy: {proxy_message}", screenshot
    else:
        print(f"[MAIN-CHECKER] ⚠️ API успешно, но Proxy не прошел: {proxy_message}")
        # Если API показал, что аккаунт существует, но Proxy не сработал,
        # все равно возвращаем скриншот (если он был создан)
        if screenshot and os.path.exists(screenshot):
            print(f"[MAIN-CHECKER] 📸 Возвращаем скриншот несмотря на проблемы с Proxy")
            return True, f"API: {api_message} | Proxy: {proxy_message}", screenshot
        else:
            print(f"[MAIN-CHECKER] ❌ Скриншот не создан из-за проблем с Proxy")
            return True, f"API: {api_message} | Proxy: {proxy_message}", None


async def check_account_on_add(
    username: str,
    session: Session,
    user_id: int
) -> Tuple[bool, str, Optional[str]]:
    """
    Проверка аккаунта при добавлении.
    Автоматически использует прокси + скриншот.
    
    Args:
        username: Instagram username
        session: Database session
        user_id: User ID
        
    Returns:
        Tuple of (success, message, screenshot_path)
    """
    print(f"[MAIN-CHECKER] 🆕 Проверка нового аккаунта @{username}")
    return await check_account_main(username, session, user_id)


async def check_account_auto(
    account: Account,
    session: Session
) -> Tuple[bool, str, Optional[str]]:
    """
    Автоматическая проверка аккаунта (по расписанию).
    Использует прокси + скриншот.
    
    Args:
        account: Account object
        session: Database session
        
    Returns:
        Tuple of (success, message, screenshot_path)
    """
    print(f"[MAIN-CHECKER] 🔄 Автопроверка аккаунта @{account.account}")
    return await check_account_main(
        username=account.account,
        session=session,
        user_id=account.user_id
    )


async def check_account_manual(
    username: str,
    session: Session,
    user_id: int
) -> Tuple[bool, str, Optional[str]]:
    """
    Ручная проверка аккаунта (кнопка "Проверить аккаунты").
    
    Args:
        username: Instagram username
        session: Database session
        user_id: User ID
        
    Returns:
        Tuple of (success, message, screenshot_path)
    """
    print(f"[MAIN-CHECKER] 👆 Ручная проверка @{username}")
    return await check_account_main(username, session, user_id)


async def check_account_with_header_dark_theme(
    username: str,
    session: Session,
    user_id: int,
    screenshot_path: Optional[str] = None
) -> Tuple[bool, str, Optional[str]]:
    """
    Проверка аккаунта через proxy БЕЗ IG сессии.
    Делает скриншот только header'а профиля с темной темой (черный фон).
    
    Args:
        username: Instagram username
        session: Database session
        user_id: User ID
        screenshot_path: Path for screenshot (auto-generated if None)
        
    Returns:
        Tuple of (success, message, screenshot_path)
    """
    print(f"\n[MAIN-CHECKER] 🌙 Проверка @{username} с header-скриншотом (темная тема)")
    
    # Проверяем наличие прокси
    proxy_url = get_best_proxy(session, user_id)
    
    if not proxy_url:
        print(f"[MAIN-CHECKER] ❌ Прокси не найден")
        return False, "Прокси не найден", None
    
    print(f"[MAIN-CHECKER] 🌐 Найден прокси: {proxy_url[:50]}...")
    
    # Генерируем путь для скриншота если не указан
    if not screenshot_path:
        screenshots_dir = "screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(screenshots_dir, f"{username}_header_dark_{timestamp}.png")
    
    # Импортируем функцию проверки
    try:
        from .ig_screenshot import check_account_with_header_screenshot
    except ImportError:
        from services.ig_screenshot import check_account_with_header_screenshot
    
    # Проверяем через proxy с header-скриншотом и темной темой
    result = await check_account_with_header_screenshot(
        username=username,
        proxy_url=proxy_url,
        screenshot_path=screenshot_path,
        headless=True,
        timeout_ms=30000,
        dark_theme=True,  # Темная тема (черный фон)
        mobile_emulation=True,  # Мобильная эмуляция (iPhone 12)
        crop_ratio=0  # БЕЗ обрезки - скриншот header элемента
    )
    
    # Обновляем статистику прокси
    try:
        from .proxy_service import update_proxy_stats
        
        # Находим прокси для обновления статистики
        proxies = session.query(Proxy).filter(
            Proxy.user_id == user_id,
            Proxy.is_active == True
        ).all()
        
        for proxy in proxies:
            if build_proxy_url_from_object(proxy) == proxy_url:
                update_proxy_stats(session, proxy, result.get("exists", False))
                print(f"[MAIN-CHECKER] 📊 Статистика прокси обновлена")
                break
                
    except Exception as e:
        print(f"[MAIN-CHECKER] ⚠️ Не удалось обновить статистику прокси: {e}")
    
    # Результат
    success = result.get("exists", False)
    screenshot = result.get("screenshot_path")
    error = result.get("error")
    
    if success:
        print(f"[MAIN-CHECKER] ✅ Успешно (header-скриншот с темной темой)")
        return True, "Профиль найден (header-скриншот с темной темой)", screenshot
    elif error:
        print(f"[MAIN-CHECKER] ❌ Ошибка: {error}")
        return False, f"Ошибка: {error}", None
    else:
        print(f"[MAIN-CHECKER] ❌ Профиль не найден")
        return False, "Профиль не найден", None
