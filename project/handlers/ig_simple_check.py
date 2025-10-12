"""Simple Instagram checking handlers with screenshots."""

import os
from sqlalchemy.orm import sessionmaker
try:
    from ..utils.access import get_or_create_user, ensure_active
    from ..models import Account
    from ..services.ig_sessions import get_active_session, decode_cookies
    from ..utils.encryptor import OptionalFernet
    from ..config import get_settings
    from ..services.ig_simple_checker import check_account_with_screenshot
except ImportError:
    from utils.access import get_or_create_user, ensure_active
    from models import Account
    from services.ig_sessions import get_active_session, decode_cookies
    from utils.encryptor import OptionalFernet
    from config import get_settings
    from services.ig_simple_checker import check_account_with_screenshot


def _format_result(result: dict) -> str:
    """Format check result for display."""
    lines = [f"@{result['username']}"]
    
    if result.get("full_name"):
        lines.append(f"Имя: {result['full_name']}")
    
    if result.get("followers") is not None:
        lines.append(f"Подписчики: {result['followers']:,}")
    
    if result.get("following") is not None:
        lines.append(f"Подписки: {result['following']:,}")
    
    if result.get("posts") is not None:
        lines.append(f"Посты: {result['posts']:,}")
    
    # Status
    if result.get("exists") is True:
        lines.append("Статус: ✅ найден")
    elif result.get("exists") is False:
        lines.append("Статус: ❌ не найден")
    else:
        lines.append("Статус: ❓ не удалось определить")
    
    if result.get("error"):
        lines.append(f"Ошибка: {result['error']}")
    
    return "\n".join(lines)


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
                
                ig_session = get_active_session(session, user.id)
                if not ig_session:
                    bot.send_message(chat_id, "⚠️ Нет активной IG-сессии. Сначала добавьте её через меню 'Instagram'.")
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

            bot.send_message(chat_id, f"⏳ Проверяю {len(pending)} аккаунтов через Instagram с скриншотами...")
            
            ok = nf = unk = 0
            
            for acc in pending:
                try:
                    import asyncio
                    result = asyncio.run(check_account_with_screenshot(
                        username=acc.account,
                        cookies=cookies,
                        headless=settings.ig_headless,
                        timeout_ms=30000
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
