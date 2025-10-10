"""Advanced account checking with profile parsing and screenshots."""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from .proxy_utils import select_best_proxy, mark_success, mark_failure, is_available
from .ig_profile_extract import extract_profile_info
from .ig_screenshot import screenshot_profile_header
import logging

logger = logging.getLogger(__name__)


def _proxy_to_url(p) -> str:
    """Convert Proxy model to URL string."""
    auth = f"{p.username}:{p.password}@" if p.username and p.password else ""
    return f"{p.scheme}://{auth}{p.host}"


def _log_proxy_status(p, attempt: int, total_attempts: int) -> None:
    """Log detailed proxy status."""
    logger.info(f"🔄 Попытка {attempt}/{total_attempts}")
    logger.info(f"📡 Прокси ID: {p.id}")
    logger.info(f"   Тип: {p.scheme.upper()}")
    logger.info(f"   Хост: {p.host}")
    logger.info(f"   Авторизация: {'Да' if p.username else 'Нет'}")
    logger.info(f"   Приоритет: {p.priority}")
    logger.info(f"   Использований: {p.used_count}")
    logger.info(f"   Успехов: {p.success_count}")
    logger.info(f"   Провалов подряд: {p.fail_streak}")
    
    if p.cooldown_until:
        logger.info(f"   ❄️ В кулдауне до: {p.cooldown_until}")
    else:
        logger.info(f"   ✅ Доступен для использования")
    
    print(f"\n🔄 Попытка {attempt}/{total_attempts} - Прокси #{p.id} ({p.scheme}://{p.host})")
    print(f"   Статистика: {p.success_count} успехов, {p.fail_streak} провалов подряд")


async def check_username_with_details(
    session: Session,
    user_id: int,
    username: str,
    wait_selector: str,
    fallback_selector: str,
    headless: bool,
    timeout_ms: int
) -> Dict[str, Any]:
    """
    Advanced username checking with profile parsing and screenshots.
    
    Returns:
    {
      "username": str,
      "exists": bool|None,
      "full_name": str|None,
      "avatar_url": str|None,
      "followers": int|None,
      "following": int|None,
      "posts": int|None,
      "screenshot_path": str|None,
      "error": str|None
    }
    С ротацией прокси и телеметрией.
    """
    logger.info(f"🎯 Начинаем проверку аккаунта: @{username}")
    print(f"\n{'='*70}")
    print(f"🎯 ПРОВЕРКА АККАУНТА: @{username}")
    print(f"{'='*70}")
    
    tried = set()
    last_error = None
    max_attempts = 4
    
    for attempt in range(1, max_attempts + 1):
        logger.info(f"\n{'='*50}")
        logger.info(f"Попытка {attempt}/{max_attempts}")
        logger.info(f"{'='*50}")
        
        p = select_best_proxy(session, user_id)
        
        if not p:
            logger.warning("❌ Нет доступных прокси")
            print(f"❌ Попытка {attempt}/{max_attempts}: Нет доступных прокси")
            break
            
        if p.id in tried:
            logger.warning(f"⚠️ Прокси #{p.id} уже использован")
            print(f"⚠️ Попытка {attempt}/{max_attempts}: Все прокси использованы")
            break
            
        tried.add(p.id)
        
        # Детальное логирование прокси
        _log_proxy_status(p, attempt, max_attempts)
        
        proxy_url = _proxy_to_url(p)
        logger.info(f"🌐 Proxy URL: {p.scheme}://{p.host}")
        
        # Проверяем доступность
        if not is_available(p):
            logger.warning(f"❄️ Прокси #{p.id} в кулдауне")
            print(f"   ❄️ Прокси в кулдауне, пропускаем...")
            continue
        
        logger.info(f"📊 Отправляем запрос через прокси...")
        print(f"   📡 Подключаемся к Instagram...")
        
        # Извлекаем информацию профиля
        info = await extract_profile_info(username, proxy_url)
        
        # Логируем результат
        if info.get("exists") is True:
            logger.info(f"✅ УСПЕХ! Профиль найден")
            print(f"   ✅ УСПЕХ! Профиль @{username} найден")
            print(f"   📊 Подписчики: {info.get('followers', 'N/A')}")
            print(f"   📊 Подписки: {info.get('following', 'N/A')}")
            print(f"   📊 Посты: {info.get('posts', 'N/A')}")
            mark_success(session, p)
            
            # Скриншот
            logger.info(f"📸 Делаем скриншот...")
            print(f"   📸 Делаем скриншот профиля...")
            spath = await screenshot_profile_header(
                username=username,
                proxy_url=proxy_url,
                wait_selector=wait_selector,
                fallback_selector=fallback_selector,
                headless=headless,
                timeout_ms=timeout_ms,
            )
            if spath:
                logger.info(f"✅ Скриншот сохранен: {spath}")
                print(f"   ✅ Скриншот сохранен")
            else:
                logger.warning(f"⚠️ Не удалось сделать скриншот")
                print(f"   ⚠️ Скриншот не получен")
            
            info["screenshot_path"] = spath
            return info
            
        elif info.get("exists") is False:
            logger.info(f"✅ Определено: профиль не существует")
            print(f"   ✅ Профиль @{username} не существует (404)")
            mark_success(session, p)
            info["screenshot_path"] = None
            return info
            
        else:
            # Неопределённый результат
            error = info.get("error", "unknown")
            logger.warning(f"❌ Неудача: {error}")
            print(f"   ❌ Ошибка: {error}")
            mark_failure(session, p)
            last_error = error
            
            # Логируем статистику после провала
            session.refresh(p)
            logger.info(f"📊 Обновленная статистика прокси #{p.id}:")
            logger.info(f"   Провалов подряд: {p.fail_streak}")
            if p.cooldown_until:
                logger.info(f"   ❄️ Отправлен в кулдаун до: {p.cooldown_until}")
                print(f"   ❄️ Прокси отправлен в кулдаун на 15 минут")
            
            continue
    
    # Все попытки провалились
    logger.error(f"❌ Все попытки провалились для @{username}")
    print(f"\n❌ Не удалось проверить @{username} после {max_attempts} попыток")
    print(f"{'='*70}\n")
    
    return {
        "username": username, "exists": None, "full_name": None, "avatar_url": None,
        "followers": None, "following": None, "posts": None, "screenshot_path": None,
        "error": last_error or "no_proxy_or_all_failed"
    }
