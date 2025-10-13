"""Simple Instagram checking handlers with screenshots."""

import os
from sqlalchemy.orm import sessionmaker
try:
    from ..utils.access import get_or_create_user, ensure_active
    from ..models import Account
    from ..services.ig_sessions import get_valid_session, decode_cookies, decode_password, update_session_cookies
    from ..utils.encryptor import OptionalFernet
    from ..config import get_settings
    from ..services.ig_simple_checker import check_account_with_screenshot
except ImportError:
    from utils.access import get_or_create_user, ensure_active
    from models import Account
    from services.ig_sessions import get_valid_session, decode_cookies, decode_password, update_session_cookies
    from utils.encryptor import OptionalFernet
    from config import get_settings
    from services.ig_simple_checker import check_account_with_screenshot


def _format_result(result: dict) -> str:
    """Format check result for display in old bot format."""
    username = result['username']
    
    # Build account info in old bot format
    account_info = f"""Имя пользователя: @https://www.instagram.com/{username}/"""
    
    # Add profile data if available
    if result.get("full_name"):
        account_info += f"\nИмя: {result['full_name']}"
    
    if result.get("followers") is not None:
        account_info += f"\nПодписчики: {result['followers']:,}"
    
    if result.get("following") is not None:
        account_info += f"\nПодписки: {result['following']:,}"
    
    if result.get("posts") is not None:
        account_info += f"\nПосты: {result['posts']:,}"
    
    # Status in old bot format
    if result.get("exists") is True:
        if result.get("is_private"):
            account_info += "\nСтатус: Аккаунт разблокирован✅ (приватный)"
        else:
            account_info += "\nСтатус: Аккаунт разблокирован✅"
    elif result.get("exists") is False:
        account_info += "\nСтатус: Заблокирован❌"
    else:
        account_info += "\nСтатус: ❓ не удалось определить"
    
    if result.get("error"):
        account_info += f"\nОшибка: {result['error']}"
    
    return account_info


def register_ig_simple_check_handlers(bot, session_factory) -> None:
    """Register simple Instagram checking handlers."""

    def process_message(message: dict, session_factory) -> None:
        """Process simple Instagram checking messages."""
        text = message.get("text", "")
        chat_id = message["chat"]["id"]
        
        if text == "Проверить через IG":
            settings = get_settings()
            fernet = OptionalFernet(settings.encryption_key)

            with session_factory() as session:
                user = get_or_create_user(session, message["from"])
                if not ensure_active(user):
                    bot.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                
                ig_session = get_valid_session(session, user.id, fernet)
                if not ig_session:
                    bot.send_message(
                        chat_id, 
                        "⚠️ Нет активной IG-сессии или сессия невалидна.\n\n"
                        "💡 Возможные причины:\n"
                        "• Логин не завершился успешно (требуется 2FA)\n"
                        "• Instagram заблокировал сессию\n"
                        "• Cookies истекли\n\n"
                        "👉 Попробуйте добавить новую сессию через меню 'Instagram'."
                    )
                    return
                
                pending = session.query(Account).filter(
                    Account.user_id == user.id, 
                    Account.done == False
                ).all()

            if not pending:
                bot.send_message(chat_id, "📭 Нет аккаунтов на проверке.")
                return

            # Decode cookies
            try:
                cookies = decode_cookies(fernet, ig_session.cookies)
            except Exception as e:
                bot.send_message(chat_id, f"❌ Ошибка расшифровки cookies: {e}")
                return
            
            # Decode password if available
            ig_password = None
            if ig_session.password:
                try:
                    ig_password = decode_password(fernet, ig_session.password)
                except Exception as e:
                    print(f"⚠️ Failed to decode password: {e}")

            bot.send_message(chat_id, f"⏳ Проверяю {len(pending)} аккаунтов через Instagram с скриншотами...")
            
            ok = nf = unk = 0
            
            # Create callback for updating cookies
            def update_cookies_callback(new_cookies):
                with session_factory() as s:
                    update_session_cookies(s, ig_session.id, new_cookies, fernet)
            
            for acc in pending:
                try:
                    import asyncio
                    result = asyncio.run(check_account_with_screenshot(
                        username=acc.account,
                        cookies=cookies,
                        headless=settings.ig_headless,
                        timeout_ms=30000,
                        ig_username=ig_session.username,
                        ig_password=ig_password,
                        session_db_update_callback=update_cookies_callback
                    ))
                    
                    # Send result text
                    result_text = _format_result(result)
                    bot.send_message(chat_id, result_text)
                    
                    # Send screenshot if available
                    if result.get("screenshot_path") and os.path.exists(result["screenshot_path"]):
                        try:
                            screenshot_path = result["screenshot_path"]
                            bot.send_photo(chat_id, screenshot_path, caption=f"📸 Скриншот @{acc.account}")
                            # Delete screenshot after sending to save disk space
                            try:
                                os.remove(screenshot_path)
                                print(f"🗑️ Screenshot deleted: {screenshot_path}")
                            except Exception as del_err:
                                print(f"Warning: Failed to delete screenshot: {del_err}")
                        except Exception as e:
                            print(f"Failed to send photo: {e}")
                    
                    # Update account status
                    if result.get("exists") is True:
                        with session_factory() as s2:
                            account = s2.query(Account).get(acc.id)
                            if account:
                                account.done = True
                                s2.commit()
                        ok += 1
                    elif result.get("exists") is False:
                        nf += 1
                    else:
                        unk += 1
                        
                except Exception as e:
                    bot.send_message(chat_id, f"❌ Ошибка при проверке @{acc.account}: {str(e)}")
                    unk += 1
            
            # Final summary
            summary = f"🎯 Готово!\n\n📊 Результаты:\n• Найдено: {ok}\n• Не найдено: {nf}\n• Ошибки: {unk}"
            bot.send_message(chat_id, summary)

    # Register handlers
    bot.ig_simple_check_process_message = process_message
