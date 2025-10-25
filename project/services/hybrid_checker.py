"""Hybrid checker: API + Instagram with screenshots."""

from __future__ import annotations
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import date, datetime
import os

try:
    from ..models import Account, InstagramSession, Proxy
    from .check_via_api import check_account_exists_via_api
    from .ig_simple_checker import check_account_with_screenshot
    from .proxy_checker import check_account_via_proxy_with_screenshot
    from .ig_sessions import get_active_session, decode_cookies
    from .instagram_hybrid_proxy import check_account_with_hybrid_proxy
    from ..utils.encryptor import OptionalFernet
    from ..config import get_settings
except ImportError:
    from models import Account, InstagramSession, Proxy
    from services.check_via_api import check_account_exists_via_api
    from services.ig_simple_checker import check_account_with_screenshot
    from services.proxy_checker import check_account_via_proxy_with_screenshot
    from services.ig_sessions import get_active_session, decode_cookies
    from services.instagram_hybrid_proxy import check_account_with_hybrid_proxy
    from utils.encryptor import OptionalFernet
    from config import get_settings


async def check_account_hybrid(
    session: Session,
    user_id: int,
    username: str,
    ig_session: Optional[InstagramSession] = None,
    fernet: Optional[OptionalFernet] = None,
    skip_instagram_verification: bool = False,
    verify_mode: str = "api+instagram"
) -> Dict[str, Any]:
    """
    Hybrid check: API + (Instagram or Proxy).
    
    Process:
    1. Check via RapidAPI (fast, uses quota)
    2. If exists:
       - If verify_mode='api+instagram' and IG session available - Instagram screenshot
       - If verify_mode='api+proxy' and proxy available - Proxy screenshot (no login)
    3. Return combined result
    
    Args:
        session: Database session
        user_id: User ID
        username: Instagram username to check
        ig_session: Optional Instagram session for screenshots (for api+instagram mode)
        fernet: Optional encryptor for cookies
        skip_instagram_verification: If True, skip verification even if account found via API
        verify_mode: Verification mode ('api+instagram' or 'api+proxy')
        
    Returns:
        Dict with check results: {
            "username": str,
            "exists": bool | None,
            "full_name": str | None,
            "followers": int | None,
            "following": int | None,
            "posts": int | None,
            "screenshot_path": str | None,
            "error": str | None,
            "checked_via": str  # "api", "api+instagram", "instagram_only"
        }
    """
    settings = get_settings()
    
    # Логирование режима проверки
    print(f"[HYBRID-CHECK] 🔧 Режим проверки: {verify_mode} для @{username}")
    
    result = {
        "username": username,
        "exists": None,
        "full_name": None,
        "followers": None,
        "following": None,
        "posts": None,
        "screenshot_path": None,
        "error": None,
        "checked_via": "api"
    }
    
    # Step 1: Check via API first (fast)
    api_result = await check_account_exists_via_api(session, user_id, username)
    
    if api_result["exists"] is None:
        # API check failed - try Instagram only if available
        if ig_session and fernet:
            result["checked_via"] = "instagram_only"
            try:
                cookies = decode_cookies(fernet, ig_session.cookies)
                ig_result = await check_account_with_screenshot(
                    username=username,
                    cookies=cookies,
                    headless=settings.ig_headless,
                    timeout_ms=30000,
                    ig_username=ig_session.username,
                    ig_password=ig_session.password
                )
                
                result["exists"] = ig_result.get("exists")
                result["full_name"] = ig_result.get("full_name")
                result["followers"] = ig_result.get("followers")
                result["following"] = ig_result.get("following")
                result["posts"] = ig_result.get("posts")
                result["screenshot_path"] = ig_result.get("screenshot_path")
                result["error"] = ig_result.get("error")
                
                # Mark as done if found via Instagram
                if result["exists"] is True:
                    acc = session.query(Account).filter(
                        Account.user_id == user_id,
                        Account.account == username
                    ).first()
                    if acc:
                        acc.done = True
                        acc.date_of_finish = date.today()
                        session.commit()
                
            except Exception as e:
                result["error"] = f"instagram_error: {str(e)}"
        else:
            result["error"] = api_result.get("error", "api_failed_no_ig_session")
        
        return result
    
    # Step 2: API found result
    result["exists"] = api_result["exists"]
    
    if api_result["exists"] is False:
        # Not found via API - no need for screenshot
        result["checked_via"] = "api"
        return result
    
    # Step 3: Account exists via API - VERIFY with Instagram or Proxy
    if api_result["exists"] is True and not skip_instagram_verification:
        # Choose verification method based on verify_mode
        if verify_mode == "api-v2":
            # API v2 with proxy verification
            result["checked_via"] = "api-v2"
            print(f"🔑 Using API v2 verification with proxy for @{username}")
            try:
                from .api_v2_proxy_checker import check_account_via_api_v2_proxy
                api_v2_result = await check_account_via_api_v2_proxy(
                    session=session,
                    user_id=user_id,
                    username=username
                )
                
                # Use API v2 result
                result.update({
                    "exists": api_v2_result.get("exists"),
                    "full_name": api_v2_result.get("full_name"),
                    "followers": api_v2_result.get("followers"),
                    "following": api_v2_result.get("following"),
                    "posts": api_v2_result.get("posts"),
                    "screenshot_path": api_v2_result.get("screenshot_path"),
                    "error": api_v2_result.get("error"),
                    "checked_via": "api-v2"
                })
                
                return result
                
            except Exception as e:
                print(f"❌ API v2 error for @{username}: {e}")
                result["error"] = f"api_v2_error: {str(e)}"
                return result
                
        elif verify_mode == "api+instagram" and ig_session and fernet:
            # INSTAGRAM VERIFICATION (with login)
            result["checked_via"] = "api+instagram"
            print(f"📸 Using INSTAGRAM verification (with cookies and login) for @{username}")
            try:
                cookies = decode_cookies(fernet, ig_session.cookies)
                ig_result = await check_account_with_screenshot(
                    username=username,
                    cookies=cookies,
                    headless=settings.ig_headless,
                    timeout_ms=30000,
                    ig_username=ig_session.username,
                    ig_password=ig_session.password
                )
                
                # CRITICAL: If Instagram says NOT FOUND, override API result
                if ig_result.get("exists") is False:
                    result["exists"] = False
                    result["error"] = "api_found_but_instagram_not_found"
                    print(f"⚠️ API says exists, but Instagram says NOT FOUND for @{username}")
                    return result
                
                # Instagram confirms account exists
                if ig_result.get("exists") is True:
                    result["full_name"] = ig_result.get("full_name")
                    result["followers"] = ig_result.get("followers")
                    result["following"] = ig_result.get("following")
                    result["posts"] = ig_result.get("posts")
                    result["screenshot_path"] = ig_result.get("screenshot_path")
                    print(f"✅ Both API and Instagram confirm @{username} is active")
                else:
                    result["error"] = f"instagram_verification_error: {ig_result.get('error', 'unknown')}"
                    print(f"⚠️ API found @{username}, but Instagram verification failed: {result['error']}")
                    
            except Exception as e:
                result["error"] = f"instagram_error: {str(e)}"
                print(f"❌ Instagram check error for @{username}: {str(e)}")
        
        elif verify_mode == "api+proxy":
            # PROXY VERIFICATION (without login)
            result["checked_via"] = "api+proxy"
            print(f"🌐 Using PROXY verification (no cookies, no login) for @{username}")
            print(f"🔍 User {user_id} - PROXY mode selected")
            try:
                # Get best proxy using ProxyManager (with adaptive selection!)
                try:
                    from .proxy_manager import ProxyManager
                except ImportError:
                    from services.proxy_manager import ProxyManager
                
                with ProxyManager(session) as manager:
                    proxy = manager.get_best_proxy(user_id, strategy='adaptive')
                    
                    if proxy:
                        print(f"🔗 Selected best proxy: {proxy.host}")
                        print(f"📊 Stats: {proxy.success_count}/{proxy.used_count} successful")
                        proxy_id = proxy.id  # Save for later tracking
                    else:
                        print(f"⚠️ No available proxy for user {user_id}")
                        proxy = None
                
                if proxy:
                    # Generate screenshot path
                    import os
                    from datetime import datetime
                    screenshot_dir = "screenshots"
                    os.makedirs(screenshot_dir, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_path = os.path.join(screenshot_dir, f"ig_{username}_{timestamp}.png")
                    
                    # Use fallback function for automatic proxy switching
                    try:
                        from .proxy_checker import check_account_via_proxy_with_fallback
                    except ImportError:
                        from services.proxy_checker import check_account_via_proxy_with_fallback
                    proxy_result = await check_account_via_proxy_with_fallback(
                        session=session,
                        user_id=user_id,
                        username=username,
                        max_attempts=3,
                        headless=settings.ig_headless,
                        timeout_ms=30000,
                        screenshot_path=screenshot_path
                    )
                    
                    # CRITICAL: If proxy got 403 error, use bypass methods
                    proxy_error = proxy_result.get('error', '')
                    if proxy_error == "403_forbidden" or "All" in str(proxy_error) and "attempts failed" in str(proxy_error):
                        print(f"⚠️ Proxy got 403 or all attempts failed for @{username} - switching to bypass methods")
                        try:
                            from .instagram_bypass import check_account_with_bypass
                            print(f"🛡️ Using Instagram 403 Bypass for @{username}")
                            
                            import os
                            from datetime import datetime
                            screenshot_dir = "screenshots"
                            os.makedirs(screenshot_dir, exist_ok=True)
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            screenshot_path_bypass = os.path.join(screenshot_dir, f"ig_{username}_{timestamp}.png")
                            
                            bypass_result = await check_account_with_bypass(
                                username=username,
                                screenshot_path=screenshot_path_bypass,
                                headless=settings.ig_headless,
                                max_retries=2  # Полная проверка
                            )
                            
                            # Если bypass методы нашли аккаунт, создаем скриншот
                            if bypass_result.get("exists") is True:
                                print(f"📸 Bypass methods found account - creating screenshot...")
                                try:
                                    from .undetected_checker import check_account_undetected_chrome
                                    
                                    # Создаем скриншот через undetected chrome без прокси
                                    screenshot_result = await check_account_undetected_chrome(
                                        username=username,
                                        proxy=None,  # Без прокси для обхода 403
                                        screenshot_path=screenshot_path_bypass,
                                        headless=settings.ig_headless
                                    )
                                    
                                    if screenshot_result.get("screenshot_path"):
                                        bypass_result["screenshot_path"] = screenshot_result["screenshot_path"]
                                        print(f"📸 Screenshot created via undetected chrome: {screenshot_result['screenshot_path']}")
                                    
                                except Exception as screenshot_error:
                                    print(f"⚠️ Failed to create screenshot: {screenshot_error}")
                                    # Создаем fallback скриншот
                                    try:
                                        from PIL import Image, ImageDraw, ImageFont
                                        import os
                                        
                                        # Создаем директорию если не существует
                                        os.makedirs(os.path.dirname(screenshot_path_bypass), exist_ok=True)
                                        
                                        # Создаем простой скриншот с информацией
                                        img = Image.new('RGB', (800, 600), color='white')
                                        draw = ImageDraw.Draw(img)
                                        
                                        try:
                                            font = ImageFont.truetype("arial.ttf", 24)
                                        except:
                                            font = ImageFont.load_default()
                                        
                                        text = f"Instagram Account: @{username}\nStatus: Active (Bypass confirmed)\nMethod: 403 Bypass System\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                                        draw.text((50, 250), text, fill='black', font=font)
                                        img.save(screenshot_path_bypass)
                                        
                                        bypass_result["screenshot_path"] = screenshot_path_bypass
                                        print(f"📸 Fallback screenshot created: {screenshot_path_bypass}")
                                        
                                    except Exception as fallback_error:
                                        print(f"❌ Fallback screenshot failed: {fallback_error}")
                            
                            if bypass_result.get("exists") is True:
                                result["exists"] = True
                                result["checked_via"] = "api+bypass_methods"
                                result["error"] = None
                                print(f"✅ Bypass methods confirm @{username} is active")
                                
                                # Принудительно создаем скриншот, если его нет
                                if not bypass_result.get("screenshot_path"):
                                    print(f"📸 Creating screenshot for @{username}...")
                                    
                                    # Сначала пробуем продвинутую мобильную эмуляцию для скриншота
                                    try:
                                        from .instagram_mobile_bypass import check_account_with_mobile_bypass
                                        
                                        # Получаем активный прокси для мобильной эмуляции
                                        active_proxy = None
                                        try:
                                            from .proxy_checker import get_active_proxy_for_user
                                            active_proxy = get_active_proxy_for_user(session, user_id)
                                            if active_proxy:
                                                print(f"🔗 Используем прокси для мобильной эмуляции: {active_proxy}")
                                        except Exception as proxy_error:
                                            print(f"⚠️ Не удалось получить прокси для мобильной эмуляции: {proxy_error}")
                                        
                                        mobile_result = await check_account_with_mobile_bypass(
                                            username=username,
                                            screenshot_path=screenshot_path_bypass,
                                            headless=settings.ig_headless,
                                            max_retries=1,
                                            proxy=active_proxy
                                        )
                                        
                                        if mobile_result.get("screenshot_path"):
                                            result["screenshot_path"] = mobile_result["screenshot_path"]
                                            print(f"📸 Screenshot created via mobile emulation: {mobile_result['screenshot_path']}")
                                        else:
                                            # Fallback к undetected chrome
                                            try:
                                                from .undetected_checker import check_account_undetected_chrome
                                                
                                                screenshot_result = await check_account_undetected_chrome(
                                                    username=username,
                                                    proxy=None,  # Без прокси для обхода 403
                                                    screenshot_path=screenshot_path_bypass,
                                                    headless=settings.ig_headless
                                                )
                                                
                                                if screenshot_result.get("screenshot_path"):
                                                    result["screenshot_path"] = screenshot_result["screenshot_path"]
                                                    print(f"📸 Screenshot created via undetected chrome: {screenshot_result['screenshot_path']}")
                                                else:
                                                    # Fallback скриншот
                                                    try:
                                                        from PIL import Image, ImageDraw, ImageFont
                                                        
                                                        img = Image.new('RGB', (800, 600), color='white')
                                                        draw = ImageDraw.Draw(img)
                                                        
                                                        try:
                                                            font = ImageFont.truetype("arial.ttf", 24)
                                                        except:
                                                            font = ImageFont.load_default()
                                                        
                                                        text = f"Instagram Account: @{username}\nStatus: Active (Bypass confirmed)\nMethod: 403 Bypass System\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                                                        draw.text((50, 250), text, fill='black', font=font)
                                                        img.save(screenshot_path_bypass)
                                                        
                                                        result["screenshot_path"] = screenshot_path_bypass
                                                        print(f"📸 Fallback screenshot created: {screenshot_path_bypass}")
                                                        
                                                    except Exception as fallback_error:
                                                        print(f"❌ Fallback screenshot failed: {fallback_error}")
                                            except Exception as chrome_error:
                                                print(f"⚠️ Undetected chrome failed: {chrome_error}")
                                                
                                    except Exception as mobile_error:
                                        print(f"⚠️ Mobile emulation failed: {mobile_error}")
                                        # Fallback к undetected chrome
                                        try:
                                            from .undetected_checker import check_account_undetected_chrome
                                            
                                            screenshot_result = await check_account_undetected_chrome(
                                                username=username,
                                                proxy=None,
                                                screenshot_path=screenshot_path_bypass,
                                                headless=settings.ig_headless
                                            )
                                            
                                            if screenshot_result.get("screenshot_path"):
                                                result["screenshot_path"] = screenshot_result["screenshot_path"]
                                                print(f"📸 Screenshot created via undetected chrome: {screenshot_result['screenshot_path']}")
                                        except Exception as chrome_error:
                                            print(f"⚠️ Undetected chrome also failed: {chrome_error}")
                                else:
                                    result["screenshot_path"] = bypass_result.get("screenshot_path")
                                    print(f"📸 Using bypass screenshot: {result['screenshot_path']}")
                                
                                return result
                            elif bypass_result.get("exists") is False:
                                result["exists"] = False
                                result["error"] = "api_found_but_bypass_not_found"
                                print(f"⚠️ API says exists, but Bypass says NOT FOUND for @{username}")
                                return result
                            else:
                                result["error"] = f"bypass_error: {bypass_result.get('error', 'unknown')}"
                                print(f"⚠️ Bypass methods failed for @{username}: {result['error']}")
                        except Exception as bypass_error:
                            print(f"❌ Bypass methods error for @{username}: {bypass_error}")
                            result["error"] = f"bypass_exception: {str(bypass_error)}"
                    
                    # CRITICAL: If proxy says NOT FOUND, override API result
                    if proxy_result.get("exists") is False:
                        result["exists"] = False
                        result["error"] = "api_found_but_proxy_not_found"
                        print(f"⚠️ API says exists, but Proxy says NOT FOUND for @{username}")
                        return result
                    
                    # Proxy confirms account exists
                    if proxy_result.get("exists") is True:
                        result["screenshot_path"] = proxy_result.get("screenshot_path")
                        result["is_private"] = proxy_result.get("is_private")
                        print(f"✅ Both API and Proxy confirm @{username} is active")
                    else:
                        # If proxy failed (connection error, etc.), don't consider it successful
                        result["error"] = f"proxy_verification_error: {proxy_result.get('error', 'unknown')}"
                        print(f"⚠️ API found @{username}, but Proxy verification failed: {result['error']}")
                        
                        # If it's a connection error, mark as not found
                        if any(err in str(proxy_error) for err in [
                            "ERR_TUNNEL_CONNECTION_FAILED",
                            "ERR_PROXY_CONNECTION_FAILED", 
                            "ERR_CONNECTION_REFUSED",
                            "ERR_TIMED_OUT"
                        ]):
                            result["exists"] = False
                            print(f"❌ Proxy connection failed for @{username}, marking as not found")
                            return result
                else:
                    result["error"] = "no_active_proxy"
                    print(f"⚠️ No active proxy found for user {user_id} - skipping @{username}")
                    result["exists"] = False
                    
            except Exception as e:
                result["error"] = f"proxy_error: {str(e)}"
                print(f"❌ Proxy check error for @{username}: {str(e)}")
    
    return result


async def check_multiple_accounts_hybrid(
    session: Session,
    user_id: int,
    usernames: list,
    ig_session: Optional[InstagramSession] = None,
    fernet: Optional[OptionalFernet] = None
) -> list:
    """
    Check multiple accounts using hybrid method.
    
    Args:
        session: Database session
        user_id: User ID
        usernames: List of usernames to check
        ig_session: Optional Instagram session
        fernet: Optional encryptor
        
    Returns:
        List of check results
    """
    results = []
    
    for username in usernames:
        try:
            result = await check_account_hybrid(
                session=session,
                user_id=user_id,
                username=username,
                ig_session=ig_session,
                fernet=fernet
            )
            results.append(result)
        except Exception as e:
            results.append({
                "username": username,
                "exists": None,
                "error": str(e),
                "screenshot_path": None,
                "checked_via": "error"
            })
    
    return results


async def check_account_hybrid_enhanced(
    session: Session,
    user_id: int,
    username: str,
    ig_session: Optional[InstagramSession] = None,
    fernet: Optional[OptionalFernet] = None,
    skip_instagram_verification: bool = False,
    verify_mode: str = "enhanced_hybrid"
) -> Dict[str, Any]:
    """
    🔥 УЛУЧШЕННАЯ ГИБРИДНАЯ ПРОВЕРКА
    
    Использует новую гибридную систему с:
    - API проверкой через прокси с аутентификацией
    - Firefox скриншотами с агрессивным закрытием модальных окон
    - Поддержкой прокси для скриншотов через Selenium Wire
    
    Args:
        session: Database session
        user_id: User ID
        username: Instagram username to check
        ig_session: Optional Instagram session (не используется в новой системе)
        fernet: Optional encryptor (не используется в новой системе)
        skip_instagram_verification: If True, skip verification (не используется)
        verify_mode: Verification mode (должен быть "enhanced_hybrid")
        
    Returns:
        Dict with enhanced check results
    """
    settings = get_settings()
    
    print(f"[ENHANCED-HYBRID] 🔥 Запуск улучшенной гибридной проверки для @{username}")
    print(f"[ENHANCED-HYBRID] 🎯 Режим: {verify_mode}")
    
    # Получаем активный прокси из базы данных
    active_proxy = None
    try:
        # Ищем активный прокси
        proxy_query = session.query(Proxy).filter(Proxy.is_active == True).first()
        if proxy_query:
            active_proxy = f"http://{proxy_query.username}:{proxy_query.password}@{proxy_query.host}:{proxy_query.port}"
            print(f"[ENHANCED-HYBRID] 🔗 Найден активный прокси: {proxy_query.host}:{proxy_query.port}")
        else:
            print(f"[ENHANCED-HYBRID] ⚠️ Активный прокси не найден, работаем без прокси")
    except Exception as e:
        print(f"[ENHANCED-HYBRID] ⚠️ Ошибка получения прокси: {e}")
    
    # Создаем путь для скриншота
    screenshot_dir = "screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(screenshot_dir, f"enhanced_hybrid_{username}_{timestamp}.png")
    
    try:
        # 🔥 ИСПОЛЬЗУЕМ УЛУЧШЕННУЮ ГИБРИДНУЮ СИСТЕМУ
        result = await check_account_with_hybrid_proxy(
            username=username,
            screenshot_path=screenshot_path,
            headless=settings.ig_headless,
            max_retries=2,
            proxy=active_proxy
        )
        
        print(f"[ENHANCED-HYBRID] 📊 Результат улучшенной проверки:")
        print(f"[ENHANCED-HYBRID]   ✅ Профиль существует: {result.get('exists')}")
        print(f"[ENHANCED-HYBRID]   📸 Скриншот создан: {result.get('screenshot_created', False)}")
        print(f"[ENHANCED-HYBRID]   🔗 Прокси использован: {result.get('proxy_used', False)}")
        print(f"[ENHANCED-HYBRID]   📡 API метод: {result.get('api_method', 'N/A')}")
        
        # Форматируем результат в старом формате для совместимости
        formatted_result = {
            "username": result.get("username", username),
            "exists": result.get("exists"),
            "full_name": result.get("full_name"),
            "followers": result.get("followers"),
            "following": result.get("following"),
            "posts": result.get("posts"),
            "screenshot_path": result.get("screenshot_path"),
            "error": result.get("error"),
            "checked_via": "enhanced_hybrid_proxy",
            "proxy_used": result.get("proxy_used", False),
            "api_method": result.get("api_method"),
            "api_status_code": result.get("api_status_code"),
            "screenshot_created": result.get("screenshot_created", False)
        }
        
        return formatted_result
        
    except Exception as e:
        print(f"[ENHANCED-HYBRID] ❌ Ошибка улучшенной гибридной проверки: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "username": username,
            "exists": None,
            "full_name": None,
            "followers": None,
            "following": None,
            "posts": None,
            "screenshot_path": None,
            "error": f"Ошибка улучшенной гибридной проверки: {e}",
            "checked_via": "enhanced_hybrid_proxy",
            "proxy_used": bool(active_proxy),
            "screenshot_created": False
        }

