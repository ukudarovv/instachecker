"""Main bot entrypoint."""

import asyncio
import time
import json
import os
import requests
from datetime import datetime, date, timedelta
from typing import Dict, Any

try:
    from .config import get_settings
    from .database import get_engine, get_session_factory, init_db
    from .utils.logging_setup import setup_logging
    from .models import User
    from .handlers.common import register_common_handlers
    from .handlers.admin import register_admin_handlers
    from .handlers.accounts_add import register_add_account_handlers
    from .handlers.accounts_lists import register_accounts_list_handlers
    from .handlers.accounts_actions import register_accounts_actions_handlers
    from .handlers.proxy_menu import register_proxy_menu_handlers
    from .handlers.proxy_add import register_proxy_add_handlers
    from .handlers.ig_menu_simple import register_ig_menu_handlers
    from .handlers.ig_simple_check import register_ig_simple_check_handlers
    from .cron import start_cron
    # check_now_adv removed - functionality integrated directly into bot.py
except ImportError:
    # If relative imports fail, try absolute imports
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from config import get_settings
    from database import get_engine, get_session_factory, init_db
    from utils.logging_setup import setup_logging
    from models import User
    from handlers.common import register_common_handlers
    from handlers.admin import register_admin_handlers
    from handlers.accounts_add import register_add_account_handlers
    from handlers.accounts_lists import register_accounts_list_handlers
    from handlers.accounts_actions import register_accounts_actions_handlers
    from handlers.proxy_menu import register_proxy_menu_handlers
    from handlers.proxy_add import register_proxy_add_handlers
    from handlers.ig_menu_simple import register_ig_menu_handlers
    from handlers.ig_simple_check import register_ig_simple_check_handlers
    from cron import start_cron
    # check_now_adv removed - functionality integrated directly into bot.py

# Global scheduler instances
_checker_scheduler = None
_expiry_scheduler = None


class TelegramBot:
    """Simple Telegram bot using direct API calls."""
    
    def __init__(self, token: str):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.last_update_id = 0
        # FSM state storage (user_id -> state_data)
        self.fsm_states = {}
    
    def get_updates(self) -> Dict[str, Any]:
        """Get updates from Telegram API."""
        url = f"{self.api_url}/getUpdates"
        params = {
            "offset": self.last_update_id + 1,
            "timeout": 30
        }
        
        try:
            response = requests.get(url, params=params, timeout=35)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error getting updates: {e}")
            return {"ok": False, "result": []}
    
    def send_message(self, chat_id: int, text: str, reply_markup: Dict = None) -> Dict:
        """Send message to chat."""
        url = f"{self.api_url}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        
        try:
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            if result.get("ok", False):
                return result.get("result", {})
            else:
                return {"message_id": None}
        except requests.RequestException as e:
            print(f"Error sending message: {e}")
            # Try to send without HTML parsing if that's the issue
            try:
                data.pop("parse_mode", None)
                response = requests.post(url, json=data, timeout=10)
                response.raise_for_status()
                result = response.json()
                if result.get("ok", False):
                    return result.get("result", {})
                else:
                    return {"message_id": None}
            except requests.RequestException as e2:
                print(f"Error sending message (retry): {e2}")
            return {"message_id": None}
    
    async def send_photo(self, chat_id: int, photo_path: str, caption: str = None) -> bool:
        """Send photo to chat."""
        url = f"{self.api_url}/sendPhoto"
        data = {"chat_id": chat_id}
        
        if caption:
            data["caption"] = caption
            data["parse_mode"] = "HTML"
        
        try:
            with open(photo_path, 'rb') as photo:
                files = {'photo': photo}
                response = requests.post(url, data=data, files=files, timeout=30)
                response.raise_for_status()
                result = response.json()
                print(f"[BOT] 📸 Photo send result: {result}")
                return result.get("ok", False)
        except (requests.RequestException, IOError) as e:
            print(f"[BOT] ❌ Error sending photo: {e}")
            return False
    
    def edit_message_text(self, chat_id: int, message_id: int, text: str, reply_markup: dict = None) -> bool:
        """Edit message text."""
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML"
        }
        
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        
        try:
            response = requests.post(f"{self.api_url}/editMessageText", json=data)
            return response.json().get("ok", False)
        except requests.RequestException as e:
            print(f"Error editing message: {e}")
            return False
    
    def delete_message(self, chat_id: int, message_id: int) -> bool:
        """Delete message."""
        data = {
            "chat_id": chat_id,
            "message_id": message_id
        }
        
        try:
            response = requests.post(f"{self.api_url}/deleteMessage", json=data)
            return response.json().get("ok", False)
        except requests.RequestException as e:
            print(f"Error deleting message: {e}")
            return False
    
    def process_web_app_data(self, message: Dict[str, Any], session_factory) -> None:
        """Process data from Telegram Mini App."""
        try:
            chat_id = message["chat"]["id"]
            user_id = message["from"]["id"]
            web_app_data = message.get("web_app_data", {})
            data_string = web_app_data.get("data", "{}")
            
            print(f"📱 Received Web App data from user {user_id}")
            
            # Parse JSON data
            try:
                data = json.loads(data_string)
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON from Web App: {e}")
                self.send_message(chat_id, "❌ Ошибка обработки данных из Mini App")
                return
            
            # Handle Instagram cookies from Mini App
            if data.get("action") == "instagram_cookies":
                cookies = data.get("cookies", [])
                
                if not cookies or len(cookies) == 0:
                    self.send_message(chat_id, "❌ Не удалось получить cookies из Mini App")
                    return
                
                # Validate and normalize cookies
                try:
                    if not isinstance(cookies, list):
                        self.send_message(chat_id, "❌ Неверный формат cookies из Mini App")
                        return
                    
                    # Normalize cookies - ensure all have required fields
                    normalized_cookies = []
                    for cookie in cookies:
                        if not isinstance(cookie, dict) or "name" not in cookie or "value" not in cookie:
                            continue  # Skip invalid cookies
                        
                        normalized_cookie = {
                            "name": cookie["name"],
                            "value": cookie["value"],
                            "domain": cookie.get("domain", ".instagram.com"),
                            "path": cookie.get("path", "/"),
                        }
                        
                        # Keep optional fields if present
                        for field in ["expires", "httpOnly", "secure", "sameSite"]:
                            if field in cookie:
                                normalized_cookie[field] = cookie[field]
                        
                        normalized_cookies.append(normalized_cookie)
                    
                    cookies = normalized_cookies
                    
                    # Check for sessionid
                    has_sessionid = any(c.get('name') == 'sessionid' for c in cookies)
                    if not has_sessionid:
                        self.send_message(
                            chat_id,
                            "⚠️ В cookies отсутствует sessionid.\n\n"
                            "Это означает, что вы не полностью вошли в Instagram.\n"
                            "Попробуйте снова."
                        )
                        return
                    
                    print(f"✅ Validated {len(cookies)} cookies from Mini App, sessionid present")
                    
                except Exception as e:
                    print(f"❌ Error validating cookies from Mini App: {e}")
                    self.send_message(chat_id, f"❌ Ошибка валидации cookies: {str(e)}")
                    return
                
                # Import required modules
                try:
                    from .utils.access import get_or_create_user
                    from .services.ig_sessions import save_session
                    from .utils.encryptor import OptionalFernet
                    from .config import get_settings
                    from .keyboards import instagram_menu_kb
                except ImportError:
                    from utils.access import get_or_create_user
                    from services.ig_sessions import save_session
                    from utils.encryptor import OptionalFernet
                    from config import get_settings
                    from keyboards import instagram_menu_kb
                
                settings = get_settings()
                fernet = OptionalFernet(settings.encryption_key)
                
                # Extract or ask for username
                ig_username = data.get('username', 'webapp_user')
                
                # Save session
                with session_factory() as s:
                    user = get_or_create_user(s, type('User', (), {
                        'id': user_id,
                        'username': message.get("from", {}).get("username", "")
                    })())
                    
                    obj = save_session(
                        session=s,
                        user_id=user.id,
                        ig_username=ig_username,
                        cookies_json=cookies,
                        fernet=fernet,
                    )
                
                self.send_message(
                    chat_id,
                    f"✅ Сессия из Mini App сохранена! (id={obj.id})\n\n"
                    f"🍪 Получено {len(cookies)} cookies\n"
                    f"📱 Username: @{ig_username}\n\n"
                    f"🎉 Теперь можете проверять аккаунты через Instagram!",
                    reply_markup=instagram_menu_kb(mini_app_url=settings.ig_mini_app_url if settings.ig_mini_app_url else None)
                )
                
                print(f"✅ Instagram session saved from Mini App for user {user_id}")
                
        except Exception as e:
            print(f"❌ Error processing Web App data: {e}")
            self.send_message(chat_id, f"❌ Ошибка обработки данных: {str(e)}")
    
    def answer_callback_query(self, callback_query_id: str, text: str = None, show_alert: bool = False) -> bool:
        """Answer callback query."""
        data = {
            "callback_query_id": callback_query_id
        }
        
        if text:
            data["text"] = text
        if show_alert:
            data["show_alert"] = True
        
        try:
            response = requests.post(f"{self.api_url}/answerCallbackQuery", json=data)
            return response.json().get("ok", False)
        except requests.RequestException as e:
            print(f"Error answering callback query: {e}")
            return False
    
    def process_callback_query(self, callback_query: Dict[str, Any], session_factory) -> None:
        """Process callback query from inline keyboards."""
        user_id = callback_query["from"]["id"]
        chat_id = callback_query["message"]["chat"]["id"]
        callback_data = callback_query["data"]
        message_id = callback_query["message"]["message_id"]
        
        print(f"[DEBUG] Processing callback: {callback_data} for user {user_id}")
        
        
        # Import access helpers
        try:
            from .utils.access import get_or_create_user, ensure_active, ensure_admin
        except ImportError:
            from utils.access import get_or_create_user, ensure_active, ensure_admin
        
        # Get or create user
        with session_factory() as session:
            user = get_or_create_user(session, callback_query["from"])
            if not ensure_active(user):
                self.answer_callback_query(callback_query["id"], "⛔ Доступ пока не выдан.")
                return
            
            # Handle different callback types
            if callback_data.startswith("apg:"):
                # Active accounts pagination
                page = int(callback_data.split(":")[1])
                try:
                    from .services.accounts import get_accounts_page
                    from .keyboards import accounts_list_kb, pagination_kb
                except ImportError:
                    from services.accounts import get_accounts_page
                    from keyboards import accounts_list_kb, pagination_kb
                
                items, total_pages = get_accounts_page(session, user.id, done=True, page=page)
                
                # Delete the previous message (could be account card or old list)
                self.delete_message(chat_id, message_id)
                
                # Send new list
                list_text = "📋 Активные аккаунты:\n\nВыберите аккаунт:"
                combined_keyboard = {
                    "inline_keyboard": accounts_list_kb("ainfo", items)["inline_keyboard"] + 
                                    pagination_kb("apg", page, total_pages)["inline_keyboard"]
                }
                
                self.send_message(chat_id, list_text, combined_keyboard)
                self.answer_callback_query(callback_query["id"])
                
            elif callback_data.startswith("ipg:"):
                # Pending accounts pagination
                page = int(callback_data.split(":")[1])
                try:
                    from .services.accounts import get_accounts_page
                    from .keyboards import accounts_list_kb, pagination_kb
                except ImportError:
                    from services.accounts import get_accounts_page
                    from keyboards import accounts_list_kb, pagination_kb
                
                items, total_pages = get_accounts_page(session, user.id, done=False, page=page)
                
                # Delete the previous message (could be account card or old list)
                self.delete_message(chat_id, message_id)
                
                # Send new list
                list_text = "🕒 Аккаунты на проверке:\n\nВыберите аккаунт:"
                combined_keyboard = {
                    "inline_keyboard": accounts_list_kb("iinfo", items)["inline_keyboard"] + 
                                    pagination_kb("ipg", page, total_pages)["inline_keyboard"]
                }
                
                self.send_message(chat_id, list_text, combined_keyboard)
                self.answer_callback_query(callback_query["id"])
                
            elif callback_data.startswith("ainfo:") or callback_data.startswith("iinfo:"):
                # Account card
                prefix, acc_id_s = callback_data.split(":")
                acc_id = int(acc_id_s)
                back_prefix = "apg" if prefix == "ainfo" else "ipg"
                page = 1
                
                try:
                    from .services.accounts import get_account_by_id
                    from .services.formatting import format_account_card
                    from .keyboards import account_card_kb
                except ImportError:
                    from services.accounts import get_account_by_id
                    from services.formatting import format_account_card
                    from keyboards import account_card_kb
                
                acc = get_account_by_id(session, user.id, acc_id)
                if not acc:
                    self.answer_callback_query(callback_query["id"], "Не найдено/нет доступа", show_alert=True)
                    return
                
                # Delete the list message
                self.delete_message(chat_id, message_id)
                
                txt = format_account_card(acc)
                self.send_message(chat_id, txt, account_card_kb(acc_id, back_prefix, page))
                self.answer_callback_query(callback_query["id"])
                
            elif callback_data.startswith("addd:"):
                # Start add days FSM
                acc_id = int(callback_data.split(":")[1])
                
                # Delete the account info message
                try:
                    self.delete_message(chat_id, callback_query["message"]["message_id"])
                except:
                    pass  # Ignore if message can't be deleted
                
                # Create keyboard with Cancel button
                cancel_keyboard = {
                    "keyboard": [
                        [{"text": "❌ Отмена"}]
                    ],
                    "resize_keyboard": True,
                    "one_time_keyboard": True
                }
                message = self.send_message(chat_id, "Введите количество дней для добавления (целое > 0):", cancel_keyboard)
                
                # Store the message ID for later deletion
                self.fsm_states[user_id] = {
                    "state": "waiting_for_add_days",
                    "acc_id": acc_id,
                    "back_prefix": "apg",
                    "page": 1,
                    "message_id": message.get("message_id")  # Store message ID for deletion
                }
                self.answer_callback_query(callback_query["id"])
                
            elif callback_data.startswith("subd:"):
                # Start subtract days FSM
                acc_id = int(callback_data.split(":")[1])
                
                # Delete the account info message
                try:
                    self.delete_message(chat_id, callback_query["message"]["message_id"])
                except:
                    pass  # Ignore if message can't be deleted
                
                # Create keyboard with Cancel button
                cancel_keyboard = {
                    "keyboard": [
                        [{"text": "❌ Отмена"}]
                    ],
                    "resize_keyboard": True,
                    "one_time_keyboard": True
                }
                message = self.send_message(chat_id, "Введите количество дней для уменьшения (целое > 0):", cancel_keyboard)
                
                # Store the message ID for later deletion
                self.fsm_states[user_id] = {
                    "state": "waiting_for_remove_days",
                    "acc_id": acc_id,
                    "back_prefix": "apg",
                    "page": 1,
                    "message_id": message.get("message_id")  # Store message ID for deletion
                }
                self.answer_callback_query(callback_query["id"])
                
            elif callback_data.startswith("delc:"):
                # Confirm delete - edit current message
                acc_id = int(callback_data.split(":")[1])
                try:
                    from .keyboards import confirm_delete_kb
                    from .services.accounts import get_account_by_id
                except ImportError:
                    from keyboards import confirm_delete_kb
                    from services.accounts import get_account_by_id
                
                # Determine back_prefix from account status
                acc = get_account_by_id(session, user.id, acc_id)
                if not acc:
                    self.answer_callback_query(callback_query["id"], "Не найдено/нет доступа", show_alert=True)
                    return
                
                back_prefix = "apg" if acc.done else "ipg"
                
                # Edit message to show confirmation
                self.edit_message_text(
                    chat_id, 
                    message_id, 
                    "❓ Удалить аккаунт безвозвратно?", 
                    confirm_delete_kb(acc_id, back_prefix, 1)
                )
                self.answer_callback_query(callback_query["id"])
                
            elif callback_data.startswith("delok:"):
                # Confirm delete
                _, acc_id_s, back_prefix, page_s = callback_data.split(":")
                acc_id = int(acc_id_s)
                page = int(page_s)
                
                try:
                    from .services.accounts import get_account_by_id, delete_account, get_accounts_page
                    from .keyboards import accounts_list_kb, pagination_kb
                except ImportError:
                    from services.accounts import get_account_by_id, delete_account, get_accounts_page
                    from keyboards import accounts_list_kb, pagination_kb
                
                acc = get_account_by_id(session, user.id, acc_id)
                if not acc:
                    self.answer_callback_query(callback_query["id"], "Не найдено/нет доступа", show_alert=True)
                    return
                
                username = acc.account
                is_done = acc.done  # Remember if account was active or pending
                delete_account(session, acc)
                
                # Delete confirmation message
                self.delete_message(chat_id, message_id)
                
                # Show popup notification
                self.answer_callback_query(callback_query["id"], f"✅ Аккаунт @{username} удален", show_alert=True)
                
                # Show the appropriate list again
                items, total_pages = get_accounts_page(session, user.id, done=is_done, page=1)
                
                if items:
                    # Determine list type and callback prefix
                    if is_done:
                        list_text = "📋 Активные аккаунты:\n\nВыберите аккаунт:"
                        callback_prefix = "ainfo"
                        page_prefix = "apg"
                    else:
                        list_text = "🕒 Аккаунты на проверке:\n\nВыберите аккаунт:"
                        callback_prefix = "iinfo"
                        page_prefix = "ipg"
                    
                    combined_keyboard = {
                        "inline_keyboard": accounts_list_kb(callback_prefix, items)["inline_keyboard"] + 
                                        pagination_kb(page_prefix, 1, total_pages)["inline_keyboard"]
                    }
                    self.send_message(chat_id, list_text, combined_keyboard)
                else:
                    # No more accounts in this category
                    try:
                        from .utils.access import ensure_admin
                        from .keyboards import main_menu
                        from .services.system_settings import get_global_verify_mode
                    except ImportError:
                        from utils.access import ensure_admin
                        from keyboards import main_menu
                        from services.system_settings import get_global_verify_mode
                    
                    is_admin = ensure_admin(user)
                    verify_mode = get_global_verify_mode(session)
                    if is_done:
                        self.send_message(chat_id, "📭 Активных аккаунтов больше нет.", main_menu(is_admin=is_admin, verify_mode=verify_mode))
                    else:
                        self.send_message(chat_id, "📭 Аккаунтов на проверке больше нет.", main_menu(is_admin=is_admin, verify_mode=verify_mode))
                
            elif callback_data.startswith("delno:"):
                # Cancel delete - restore account card
                _, acc_id_s, back_prefix, page_s = callback_data.split(":")
                acc_id = int(acc_id_s)
                page = int(page_s)
                
                try:
                    from .services.accounts import get_account_by_id
                    from .services.formatting import format_account_card
                    from .keyboards import account_card_kb
                except ImportError:
                    from services.accounts import get_account_by_id
                    from services.formatting import format_account_card
                    from keyboards import account_card_kb
                
                acc = get_account_by_id(session, user.id, acc_id)
                if not acc:
                    self.answer_callback_query(callback_query["id"], "Не найдено/нет доступа", show_alert=True)
                    return
                
                # Restore account card
                txt = format_account_card(acc)
                self.edit_message_text(
                    chat_id,
                    message_id,
                    txt,
                    account_card_kb(acc_id, back_prefix, page)
                )
                self.answer_callback_query(callback_query["id"])
                
            # Proxy pagination
            elif callback_data.startswith("ppg:"):
                # Navigate to proxy page
                _, page_s = callback_data.split(":")
                page = int(page_s)
                
                try:
                    from .services.proxy_service import get_proxies_page, count_proxies
                    from .services.proxy_formatting import format_proxies_list_header
                    from .keyboards import proxies_list_kb, pagination_kb
                except ImportError:
                    from services.proxy_service import get_proxies_page, count_proxies
                    from services.proxy_formatting import format_proxies_list_header
                    from keyboards import proxies_list_kb, pagination_kb
                
                with session_factory() as session:
                    proxies, total_pages = get_proxies_page(session, user.id, page=page, per_page=10)
                    stats = count_proxies(session, user.id)
                    
                    header = format_proxies_list_header(
                        page=page,
                        total_pages=total_pages,
                        total_count=stats['total'],
                        active_count=stats['active']
                    )
                    
                    combined_keyboard = {
                        "inline_keyboard": proxies_list_kb(proxies)["inline_keyboard"] + 
                                        pagination_kb("ppg", page, total_pages)["inline_keyboard"]
                    }
                    
                    self.edit_message_text(chat_id, message_id, header, combined_keyboard)
                    self.answer_callback_query(callback_query["id"])
            
            # Show proxy card
            elif callback_data.startswith("pinfo:"):
                _, pid_s = callback_data.split(":")
                pid = int(pid_s)
                
                try:
                    from .services.proxy_service import get_proxy_by_id
                    from .services.proxy_formatting import format_proxy_card
                    from .keyboards import proxy_card_kb
                except ImportError:
                    from services.proxy_service import get_proxy_by_id
                    from services.proxy_formatting import format_proxy_card
                    from keyboards import proxy_card_kb
                
                with session_factory() as session:
                    proxy = get_proxy_by_id(session, user.id, pid)
                    
                    if not proxy:
                        self.answer_callback_query(callback_query["id"], "Не найдено/нет доступа", show_alert=True)
                        return
                    
                    card_text = format_proxy_card(proxy)
                    self.edit_message_text(chat_id, message_id, card_text, proxy_card_kb(pid, page=1))
                    self.answer_callback_query(callback_query["id"])
            
            # Activate/Deactivate proxy
            elif callback_data.startswith("pactive:") or callback_data.startswith("pinactive:"):
                parts = callback_data.split(":")
                action = parts[0]
                pid = int(parts[1])
                page = int(parts[2])
                
                try:
                    from .services.proxy_service import get_proxy_by_id
                    from .services.proxy_formatting import format_proxy_card
                    from .keyboards import proxy_card_kb
                except ImportError:
                    from services.proxy_service import get_proxy_by_id
                    from services.proxy_formatting import format_proxy_card
                    from keyboards import proxy_card_kb
                
                with session_factory() as session:
                    proxy = get_proxy_by_id(session, user.id, pid)
                    
                    if not proxy:
                        self.answer_callback_query(callback_query["id"], "Не найдено/нет доступа", show_alert=True)
                        return
                    
                    if action == "pactive":
                        proxy.is_active = True
                        msg = "✅ Прокси активирован"
                    else:
                        proxy.is_active = False
                        msg = "❌ Прокси деактивирован"
                    
                    session.commit()
                    session.refresh(proxy)
                    
                    card_text = format_proxy_card(proxy)
                    self.edit_message_text(chat_id, message_id, card_text, proxy_card_kb(pid, page))
                    self.answer_callback_query(callback_query["id"], msg)
            
            # Delete proxy confirmation
            elif callback_data.startswith("pdelask:"):
                parts = callback_data.split(":")
                pid = int(parts[1])
                page = int(parts[2])
                
                try:
                    from .services.proxy_service import get_proxy_by_id
                except ImportError:
                    from services.proxy_service import get_proxy_by_id
                
                with session_factory() as session:
                    proxy = get_proxy_by_id(session, user.id, pid)
                    
                    if not proxy:
                        self.answer_callback_query(callback_query["id"], "Не найдено/нет доступа", show_alert=True)
                        return
                    
                    confirm_text = (
                        f"❗ <b>Удалить прокси?</b>\n\n"
                        f"🌐 {proxy.scheme}://{proxy.host}\n\n"
                        f"⚠️ Это действие нельзя отменить!"
                    )
                    
                    confirm_kb = {
                        "inline_keyboard": [
                            [
                                {"text": "✅ Да, удалить", "callback_data": f"pdelok:{pid}:{page}"},
                                {"text": "❌ Отмена", "callback_data": f"pdelno:{pid}:{page}"}
                            ]
                        ]
                    }
                    
                    self.edit_message_text(chat_id, message_id, confirm_text, confirm_kb)
                    self.answer_callback_query(callback_query["id"])
            
            # Confirm delete proxy
            elif callback_data.startswith("pdelok:"):
                parts = callback_data.split(":")
                pid = int(parts[1])
                page = int(parts[2])
                
                try:
                    from .services.proxy_service import get_proxy_by_id, delete_proxy, get_proxies_page, count_proxies
                    from .services.proxy_formatting import format_proxies_list_header
                    from .keyboards import proxies_list_kb, pagination_kb, proxies_menu_kb
                except ImportError:
                    from services.proxy_service import get_proxy_by_id, delete_proxy, get_proxies_page, count_proxies
                    from services.proxy_formatting import format_proxies_list_header
                    from keyboards import proxies_list_kb, pagination_kb, proxies_menu_kb
                
                with session_factory() as session:
                    proxy = get_proxy_by_id(session, user.id, pid)
                    
                    if not proxy:
                        self.answer_callback_query(callback_query["id"], "Не найдено/нет доступа", show_alert=True)
                        return
                    
                    proxy_url = f"{proxy.scheme}://{proxy.host}"
                    delete_proxy(session, proxy)
                
                # Delete message
                self.delete_message(chat_id, message_id)
                
                # Show popup
                self.answer_callback_query(callback_query["id"], f"✅ Прокси {proxy_url} удален", show_alert=True)
                
                # Show updated list
                with session_factory() as session:
                    proxies, total_pages = get_proxies_page(session, user.id, page=1, per_page=10)
                    
                    if proxies:
                        stats = count_proxies(session, user.id)
                        header = format_proxies_list_header(
                            page=1,
                            total_pages=total_pages,
                            total_count=stats['total'],
                            active_count=stats['active']
                        )
                        
                        combined_keyboard = {
                            "inline_keyboard": proxies_list_kb(proxies)["inline_keyboard"] + 
                                            pagination_kb("ppg", 1, total_pages)["inline_keyboard"]
                        }
                        
                        self.send_message(chat_id, header, combined_keyboard)
                    else:
                        self.send_message(chat_id, "📭 У вас больше нет прокси.", proxies_menu_kb())
            
            # Cancel delete proxy
            elif callback_data.startswith("pdelno:"):
                parts = callback_data.split(":")
                pid = int(parts[1])
                page = int(parts[2])
                
                try:
                    from .services.proxy_service import get_proxy_by_id
                    from .services.proxy_formatting import format_proxy_card
                    from .keyboards import proxy_card_kb
                except ImportError:
                    from services.proxy_service import get_proxy_by_id
                    from services.proxy_formatting import format_proxy_card
                    from keyboards import proxy_card_kb
                
                with session_factory() as session:
                    proxy = get_proxy_by_id(session, user.id, pid)
                    
                    if not proxy:
                        self.answer_callback_query(callback_query["id"], "Не найдено/нет доступа", show_alert=True)
                        return
                    
                    card_text = format_proxy_card(proxy)
                    self.edit_message_text(chat_id, message_id, card_text, proxy_card_kb(pid, page))
                    self.answer_callback_query(callback_query["id"], "Отменено")
            
            # Proxy test from card
            elif callback_data.startswith("ptest:"):
                parts = callback_data.split(":")
                pid = int(parts[1])
                page = int(parts[2])
                
                # Start FSM for username input
                self.fsm_states[user_id] = {
                    "state": "waiting_proxy_test_username",
                    "proxy_id": pid,
                    "page": page,
                    "test_all": False
                }
                
                try:
                    from .keyboards import cancel_kb
                except ImportError:
                    from keyboards import cancel_kb
                
                message = (
                    f"🧪 <b>Тестирование прокси</b>\n\n"
                    f"Введите Instagram username для проверки:\n\n"
                    f"💡 Примеры:\n"
                    f"  • instagram\n"
                    f"  • cristiano\n"
                    f"  • leomessi\n\n"
                    f"Бот проверит доступность аккаунта через прокси и сделает скриншот."
                )
                
                # Create keyboard with Cancel button
                cancel_keyboard = {
                    "keyboard": [
                        [{"text": "❌ Отмена"}]
                    ],
                    "resize_keyboard": True,
                    "one_time_keyboard": True
                }
                self.edit_message_text(chat_id, message_id, message, cancel_keyboard)
                self.answer_callback_query(callback_query["id"])
            
            # Test mode selection - all proxies
            elif callback_data == "ptest_all":
                # Start FSM for username input
                self.fsm_states[user_id] = {
                    "state": "waiting_proxy_test_username",
                    "test_all": True
                }
                
                try:
                    from .keyboards import cancel_kb
                    from .models import Proxy
                except ImportError:
                    from keyboards import cancel_kb
                    from models import Proxy
                
                with session_factory() as session:
                    active_count = session.query(Proxy).filter(
                        Proxy.user_id == user.id,
                        Proxy.is_active == True
                    ).count()
                
                message = (
                    f"🧪 <b>Тестирование всех прокси</b>\n\n"
                    f"📊 Будет протестировано: {active_count} прокси\n"
                    f"🖥️ Режим: Desktop (стандартное тестирование)\n\n"
                    f"<b>Введите Instagram username для проверки:</b>\n\n"
                    f"💡 Примеры:\n"
                    f"  • instagram (рекомендуется)\n"
                    f"  • cristiano\n"
                    f"  • nasa\n\n"
                    f"Бот проверит каждый прокси на этом аккаунте и покажет результаты."
                )
                
                # Create keyboard with Cancel button
                cancel_keyboard = {
                    "keyboard": [
                        [{"text": "❌ Отмена"}]
                    ],
                    "resize_keyboard": True,
                    "one_time_keyboard": True
                }
                self.edit_message_text(chat_id, message_id, message, cancel_keyboard)
                self.answer_callback_query(callback_query["id"])
            
            # Test mode selection - select specific proxy
            elif callback_data == "ptest_select":
                print(f"[DEBUG] Processing ptest_select callback for user {user_id}")
                try:
                    from .models import Proxy
                    from .keyboards import proxy_selection_for_test_kb, proxies_menu_kb
                    print(f"[DEBUG] Imports successful")
                except ImportError as e:
                    print(f"[DEBUG] Import error: {e}")
                    from models import Proxy
                    from keyboards import proxy_selection_for_test_kb, proxies_menu_kb
                
                with session_factory() as session:
                    active_proxies = session.query(Proxy).filter(
                        Proxy.user_id == user.id,
                        Proxy.is_active == True
                    ).order_by(Proxy.priority.asc()).all()
                    print(f"[DEBUG] Found {len(active_proxies)} active proxies")
                    
                    if not active_proxies:
                        print(f"[DEBUG] No active proxies found")
                        self.answer_callback_query(callback_query["id"], "Нет активных прокси", show_alert=True)
                        return
                
                message = (
                    f"🎯 <b>Выбор прокси для тестирования</b>\n\n"
                    f"Выберите прокси из списка:"
                )
                print(f"[DEBUG] Message created: {message}")
                
                keyboard = proxy_selection_for_test_kb(active_proxies)
                print(f"[DEBUG] Keyboard created with {len(active_proxies)} proxies")
                
                print(f"[DEBUG] Attempting to send new message to chat {chat_id}")
                result = self.send_message(chat_id, message, keyboard)
                print(f"[DEBUG] Send message result: {result}")
                
                self.answer_callback_query(callback_query["id"])
                print(f"[DEBUG] Callback query answered")
            
            # Test specific proxy (after selection)
            elif callback_data.startswith("ptest_one:"):
                print(f"[DEBUG] Processing ptest_one callback: {callback_data} for user {user_id}")
                _, pid_s = callback_data.split(":")
                pid = int(pid_s)
                print(f"[DEBUG] Selected proxy ID: {pid}")
                
                # Start FSM for username input
                self.fsm_states[user_id] = {
                    "state": "waiting_proxy_test_username",
                    "proxy_id": pid,
                    "test_all": False
                }
                print(f"[DEBUG] FSM state set: {self.fsm_states[user_id]}")
                
                try:
                    from .keyboards import cancel_kb
                    print(f"[DEBUG] Imports successful")
                except ImportError as e:
                    print(f"[DEBUG] Import error: {e}")
                    from keyboards import cancel_kb
                
                message = (
                    f"🧪 <b>Тестирование прокси</b>\n\n"
                    f"Введите Instagram username для проверки:\n\n"
                    f"💡 Примеры:\n"
                    f"  • instagram (рекомендуется)\n"
                    f"  • cristiano\n"
                    f"  • nasa\n\n"
                    f"Бот проверит аккаунт через прокси и сделает скриншот."
                )
                print(f"[DEBUG] Message created: {message[:100]}...")
                
                # Create keyboard with Cancel button
                cancel_keyboard = {
                    "keyboard": [
                        [{"text": "❌ Отмена"}]
                    ],
                    "resize_keyboard": True,
                    "one_time_keyboard": True
                }
                print(f"[DEBUG] Keyboard created: {cancel_keyboard}")
                
                print(f"[DEBUG] Attempting to send new message to chat {chat_id}")
                result = self.send_message(chat_id, message, cancel_keyboard)
                print(f"[DEBUG] Send message result: {result}")
                
                self.answer_callback_query(callback_query["id"])
                print(f"[DEBUG] Callback query answered")
            
            # Enhanced proxy test modes
            elif callback_data == "ptest_quick":
                # Quick test mode
                self.fsm_states[user_id] = {
                    "state": "waiting_proxy_test_username",
                    "test_all": True,
                    "test_mode": "quick"
                }
                
                try:
                    from .keyboards import cancel_kb
                    from .models import Proxy
                except ImportError:
                    from keyboards import cancel_kb
                    from models import Proxy
                
                with session_factory() as session:
                    active_count = session.query(Proxy).filter(
                        Proxy.user_id == user.id,
                        Proxy.is_active == True
                    ).count()
                
                message = (
                    f"🧪 <b>Быстрая проверка прокси</b>\n\n"
                    f"📊 Будет протестировано: {active_count} прокси\n"
                    f"⚡ Режим: Базовая связность (Desktop)\n\n"
                    f"<b>Введите Instagram username для проверки:</b>\n\n"
                    f"💡 Примеры:\n"
                    f"  • instagram (рекомендуется)\n"
                    f"  • cristiano\n"
                    f"  • nasa\n\n"
                    f"Бот проверит каждый прокси на этом аккаунте и покажет результаты."
                )
                
                # Create keyboard with Cancel button
                cancel_keyboard = {
                    "keyboard": [
                        [{"text": "❌ Отмена"}]
                    ],
                    "resize_keyboard": True,
                    "one_time_keyboard": True
                }
                self.edit_message_text(chat_id, message_id, message, cancel_keyboard)
                self.answer_callback_query(callback_query["id"])
            
            elif callback_data == "ptest_screenshot":
                print(f"[DEBUG] Processing ptest_screenshot callback for user {user_id}")
                # Screenshot test mode
                self.fsm_states[user_id] = {
                    "state": "waiting_proxy_test_username",
                    "test_all": True,
                    "test_mode": "screenshot"
                }
                print(f"[DEBUG] FSM state set: {self.fsm_states[user_id]}")
                
                try:
                    from .keyboards import cancel_kb
                    from .models import Proxy
                    print(f"[DEBUG] Imports successful")
                except ImportError as e:
                    print(f"[DEBUG] Import error: {e}")
                    from keyboards import cancel_kb
                    from models import Proxy
                
                with session_factory() as session:
                    active_count = session.query(Proxy).filter(
                        Proxy.user_id == user.id,
                        Proxy.is_active == True
                    ).count()
                print(f"[DEBUG] Active proxies count: {active_count}")
                
                message = (
                    f"📸 <b>Тест скриншота прокси</b>\n\n"
                    f"📊 Будет протестировано: {active_count} прокси\n"
                    f"📸 Режим: Создание скриншота профиля (Desktop)\n\n"
                    f"<b>Введите Instagram username для проверки:</b>\n\n"
                    f"💡 Примеры:\n"
                    f"  • instagram (рекомендуется)\n"
                    f"  • cristiano\n"
                    f"  • nasa\n\n"
                    f"Бот проверит каждый прокси на этом аккаунте и покажет результаты."
                )
                print(f"[DEBUG] Message created: {message[:100]}...")
                
                # Create keyboard with Cancel button
                cancel_keyboard = {
                    "keyboard": [
                        [{"text": "❌ Отмена"}]
                    ],
                    "resize_keyboard": True,
                    "one_time_keyboard": True
                }
                print(f"[DEBUG] Keyboard created: {cancel_keyboard}")
                
                print(f"[DEBUG] Attempting to send new message to chat {chat_id}")
                result = self.send_message(chat_id, message, cancel_keyboard)
                print(f"[DEBUG] Send message result: {result}")
                
                self.answer_callback_query(callback_query["id"])
                print(f"[DEBUG] Callback query answered")
            
            # Cancel proxy test
            elif callback_data == "ptest_cancel":
                try:
                    from .keyboards import proxies_menu_kb
                except ImportError:
                    from keyboards import proxies_menu_kb
                
                self.edit_message_text(chat_id, message_id, "❌ Тестирование отменено", proxies_menu_kb())
                self.answer_callback_query(callback_query["id"])
            
            elif callback_data.startswith("ig_mode:") or callback_data.startswith("ig_session:") or callback_data.startswith("ig_delete:") or callback_data == "ig_back" or callback_data == "ig_sessions":
                # Instagram callbacks
                if hasattr(self, 'ig_menu_process_callback_query'):
                    self.ig_menu_process_callback_query(callback_query, session_factory)
                else:
                    self.answer_callback_query(callback_query["id"])
            
            elif callback_data.startswith("api_del:") or callback_data.startswith("api_test:"):
                # API key actions
                action, sid = callback_data.split(":")
                sid = int(sid)
                
                try:
                    from .models import APIKey
                    from .services.api_keys import test_api_key
                    from .keyboards import api_key_card_kb
                except ImportError:
                    from models import APIKey
                    from services.api_keys import test_api_key
                    from keyboards import api_key_card_kb
                
                with session_factory() as s:
                    key = s.query(APIKey).filter(
                        APIKey.id == sid,
                        APIKey.user_id == user.id
                    ).one_or_none()
                    
                    if not key:
                        self.answer_callback_query(callback_query["id"], "Не найдено/нет доступа", show_alert=True)
                        return
                    
                    if action == "api_del":
                        s.delete(key)
                        s.commit()
                        self.edit_message_text(chat_id, message_id, "🗑 Ключ удалён.")
                        self.answer_callback_query(callback_query["id"])
                        return
                    elif action == "api_test":
                        self.answer_callback_query(callback_query["id"], "Тестирую...")
                        key_value = key.key
                
                # Test outside of session context
                import asyncio
                import concurrent.futures
                # Run async function in thread pool to avoid event loop conflict
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, test_api_key(key_value, test_username="instagram"))
                    try:
                        ok, err = future.result(timeout=30)  # 30 second timeout
                    except Exception as e:
                        ok, err = False, str(e)
                
                with session_factory() as s:
                    k2 = s.query(APIKey).get(sid)
                    if k2:
                        k2.is_work = ok
                        s.commit()
                        s.refresh(k2)
                        masked = k2.key[:4] + "..." + k2.key[-4:] if k2.key and len(k2.key) > 8 else "***"
                        key_text = (
                            f"🔑 id={k2.id}\n"
                            f"• key: {masked}\n"
                            f"• is_work: {'✅' if k2.is_work else '❌'}\n"
                            f"• qty_req (сегодня): {k2.qty_req or 0}\n"
                            f"• ref_date: {k2.ref_date or 'N/A'}"
                        )
                        self.edit_message_text(chat_id, message_id, key_text, api_key_card_kb(k2.id))
                
                self.answer_callback_query(callback_query["id"], "OK" if ok else (err or "fail"))
            
            elif callback_data.startswith("expiry_soon:") or callback_data.startswith("expiry_expired:"):
                # Show account info from expiry notification
                acc_id = int(callback_data.split(":")[1])
                
                try:
                    from .services.accounts import get_account_by_id
                    from .services.formatting import format_account_card
                except ImportError:
                    from services.accounts import get_account_by_id
                    from services.formatting import format_account_card
                
                with session_factory() as s:
                    acc = get_account_by_id(s, user.id, acc_id)
                    
                    if not acc or acc.user_id != user.id:
                        self.answer_callback_query(callback_query["id"], "❌ Аккаунт не найден", show_alert=True)
                        return
                    
                    # Format account info
                    info_text = format_account_card(acc)
                    
                    # Create keyboard with action buttons
                    keyboard = {
                        "inline_keyboard": [
                            [
                                {"text": "➕ День", "callback_data": f"addd:{acc_id}"},
                                {"text": "➖ День", "callback_data": f"subd:{acc_id}"}
                            ],
                            [{"text": "🗑 Удалить", "callback_data": f"delc:{acc_id}"}],
                            [{"text": "⬅ Назад", "callback_data": "close_expiry_info"}]
                        ]
                    }
                    
                    # Edit message with account info
                    self.edit_message_text(chat_id, message_id, info_text, keyboard)
                    self.answer_callback_query(callback_query["id"])
            
            elif callback_data.startswith("admin_verify_mode:"):
                # Admin wants to change global verification mode
                new_mode = callback_data.split(":")[1]
                
                
                # Check admin permissions
                if not ensure_admin(user):
                    self.answer_callback_query(callback_query["id"], "⛔ Доступ запрещен", show_alert=True)
                    return
                
                # Update global mode
                try:
                    from .services.system_settings import set_global_verify_mode, get_global_verify_mode
                except ImportError:
                    from services.system_settings import set_global_verify_mode, get_global_verify_mode
                
                with session_factory() as session:
                    # Логируем смену режима
                    old_mode = get_global_verify_mode(session)
                    set_global_verify_mode(session, new_mode)
                    print(f"[ADMIN] 🔄 Режим проверки изменен администратором {user.username} (ID: {user_id})")
                    print(f"[ADMIN] 📊 Старый режим: {old_mode} → Новый режим: {new_mode}")
                    print(f"[ADMIN] 🌍 Изменение применяется ко всем пользователям")
                
                # Get mode name for display
                mode_names = {
                    "api+instagram": "API + Instagram",
                    "api+proxy": "API + Proxy", 
                    "api+proxy+instagram": "API + Proxy + Instagram",
                    "instagram+proxy": "Instagram + Proxy",
                    "instagram": "Только Instagram",
                    "proxy": "Только Proxy"
                }
                mode_name = mode_names.get(new_mode, new_mode)
                
                # Update message
                try:
                    from .keyboards import admin_verify_mode_selection_kb
                except ImportError:
                    from keyboards import admin_verify_mode_selection_kb
                
                self.edit_message_text(
                    chat_id,
                    message_id,
                    f"🔧 **Режим проверки**\n\n"
                    f"Текущий режим: **{new_mode}**\n\n"
                    f"Выберите новый режим проверки для всех пользователей:",
                    reply_markup=admin_verify_mode_selection_kb(new_mode)
                )
                
                self.answer_callback_query(callback_query["id"], f"✅ Глобальный режим изменен на {mode_name}")
            
            elif callback_data.startswith("set_verify_mode:"):
                # User wants to change verification mode (DISABLED - only admins can change)
                self.answer_callback_query(callback_query["id"], "⛔ Только администраторы могут изменять режим проверки", show_alert=True)
            
            elif callback_data == "close_settings":
                # Close settings menu - go back to main menu
                try:
                    from .keyboards import main_menu
                    from .utils.access import ensure_admin
                    from .services.system_settings import get_global_verify_mode
                except ImportError:
                    from keyboards import main_menu
                    from utils.access import ensure_admin
                    from services.system_settings import get_global_verify_mode
                verify_mode = get_global_verify_mode(session)
                self.edit_message_text(chat_id, message_id, "Главное меню:", main_menu(ensure_admin(user), verify_mode=verify_mode))
                self.answer_callback_query(callback_query["id"], "✅ Настройки закрыты")
            
            elif callback_data == "show_inactive_accounts" or callback_data == "close_expiry_info":
                # Show inactive accounts list or close info
                if callback_data == "show_inactive_accounts":
                    # Show inactive accounts list (same as "Неактивные аккаунты" menu)
                    try:
                        from .services.accounts import get_accounts_page
                    except ImportError:
                        from services.accounts import get_accounts_page
                    
                    with session_factory() as s:
                        page = 1
                        accounts, total_pages = get_accounts_page(s, user.id, done=False, page=page)
                        
                        if not accounts:
                            self.edit_message_text(chat_id, message_id, "📋 Неактивных аккаунтов пока нет.")
                            self.answer_callback_query(callback_query["id"])
                            return
                        
                        try:
                            from .keyboards import accounts_list_kb, pagination_kb
                        except ImportError:
                            from keyboards import accounts_list_kb, pagination_kb
                        
                        # Create accounts list keyboard
                        keyboard = accounts_list_kb("iinfo", accounts)
                        
                        
                        # Add pagination if needed
                        if total_pages > 1:
                            try:
                                from .keyboards import pagination_kb
                            except ImportError:
                                from keyboards import pagination_kb
                            
                            pagination = pagination_kb("ipg", page, total_pages)
                            keyboard["inline_keyboard"].extend(pagination["inline_keyboard"])
                        
                        self.edit_message_text(
                            chat_id, 
                            message_id,
                            f"📋 Неактивные аккаунты (на проверке)\nСтраница {page}/{total_pages}\nВсего: {len(accounts)}",
                            keyboard
                        )
                        self.answer_callback_query(callback_query["id"])
                else:
                    # Close info - delete message or edit back to notification
                    self.delete_message(chat_id, message_id)
                    self.answer_callback_query(callback_query["id"], "✅ Закрыто")
            
            elif callback_data.startswith("usr_"):
                # User management callbacks (admin only)
                if not ensure_admin(user):
                    self.answer_callback_query(callback_query["id"], "⛔ Доступ запрещен")
                    return
                
                # Import admin handlers
                try:
                    from .handlers.admin_menu import register_admin_menu_handlers
                except ImportError:
                    from handlers.admin_menu import register_admin_menu_handlers
                
                text_handlers, fsm_handlers, callback_handlers = register_admin_menu_handlers(self, session_factory)
                
                # Parse callback data
                parts = callback_data.split(":")
                callback_type = parts[0]
                
                # Handle different user management callbacks
                if callback_type in callback_handlers:
                    if callback_type == "usr_back" or callback_type == "usr_delete_inactive_ok":
                        # Callbacks without parameters
                        callback_handlers[callback_type](callback_query, user)
                    elif callback_type == "usr_page":
                        # usr_page:filter_type:page
                        if len(parts) >= 3:
                            filter_type = parts[1]
                            page = parts[2]
                            callback_handlers[callback_type](callback_query, user, filter_type, page)
                        else:
                            self.answer_callback_query(callback_query["id"], "❌ Некорректный запрос")
                    elif callback_type == "usr_acc_page":
                        # usr_acc_page:user_id:acc_page:show_active:user_page:user_filter
                        if len(parts) >= 6:
                            target_user_id = parts[1]
                            acc_page = parts[2]
                            show_active = parts[3]
                            user_page = parts[4]
                            user_filter = parts[5]
                            callback_handlers[callback_type](callback_query, user, target_user_id, acc_page, show_active, user_page, user_filter)
                        else:
                            self.answer_callback_query(callback_query["id"], "❌ Некорректный запрос")
                    elif callback_type == "usr_acc_toggle":
                        # usr_acc_toggle:user_id:acc_page:show_active:user_page:user_filter
                        if len(parts) >= 6:
                            target_user_id = parts[1]
                            acc_page = parts[2]
                            show_active = parts[3]
                            user_page = parts[4]
                            user_filter = parts[5]
                            callback_handlers[callback_type](callback_query, user, target_user_id, acc_page, show_active, user_page, user_filter)
                        else:
                            self.answer_callback_query(callback_query["id"], "❌ Некорректный запрос")
                    else:
                        # Callbacks with user_id and optional page/filter
                        # Format: usr_action:user_id:page:filter_type
                        if len(parts) >= 2:
                            target_user_id = parts[1]
                            page = parts[2] if len(parts) > 2 else 1
                            filter_type = parts[3] if len(parts) > 3 else "all"
                            callback_handlers[callback_type](callback_query, user, target_user_id, page, filter_type)
                        else:
                            self.answer_callback_query(callback_query["id"], "❌ Некорректный запрос")
                else:
                    self.answer_callback_query(callback_query["id"])
                
            else:
                self.answer_callback_query(callback_query["id"])

    async def process_message(self, message: Dict[str, Any], session_factory) -> None:
        """Process incoming message."""
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        user_id = message.get("from", {}).get("id")
        username = message.get("from", {}).get("username", "")
        
        if not chat_id or not user_id:
            return
        
        # Import access helpers
        try:
            from .utils.access import get_or_create_user, ensure_active, ensure_admin
            from .keyboards import main_menu, cancel_kb
        except ImportError:
            from utils.access import get_or_create_user, ensure_active, ensure_admin
            from keyboards import main_menu, cancel_kb
        
        with session_factory() as session:
            # Get or create user
            user = get_or_create_user(session, type('User', (), {
                'id': user_id,
                'username': username
            })())
            
            if text == "/start":
                if not ensure_active(user):
                    self.send_message(chat_id, 
                        "👋 Привет! Твоя учётная запись создана.\n"
                        "Попроси администратора выдать доступ, после чего станет доступно меню."
                    )
                    return
                
                try:
                    from .services.system_settings import get_global_verify_mode
                except ImportError:
                    from services.system_settings import get_global_verify_mode
                verify_mode = get_global_verify_mode(session)
                keyboard = main_menu(is_admin=ensure_admin(user), verify_mode=verify_mode)
                self.send_message(chat_id, "Главное меню:", keyboard)
            
            elif text and text.lower() in {"меню", "menu"}:
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан. Обратись к администратору.")
                    return
                
                try:
                    from .services.system_settings import get_global_verify_mode
                except ImportError:
                    from services.system_settings import get_global_verify_mode
                verify_mode = get_global_verify_mode(session)
                keyboard = main_menu(is_admin=ensure_admin(user), verify_mode=verify_mode)
                self.send_message(chat_id, "Главное меню:", keyboard)
            
            elif text == "Добавить аккаунт":
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                
                # Start FSM for adding account
                self.fsm_states[user_id] = {"state": "waiting_for_username"}
                self.send_message(chat_id, "🆔 Введите Instagram username (можно с @):", cancel_kb())

            elif text == "Активные аккаунты":
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                # Import services
                try:
                    from .services.accounts import get_accounts_page
                    from .keyboards import accounts_list_kb, pagination_kb
                    from .services.system_settings import get_global_verify_mode
                except ImportError:
                    from services.accounts import get_accounts_page
                    from keyboards import accounts_list_kb, pagination_kb
                    from services.system_settings import get_global_verify_mode
                
                with session_factory() as session:
                    verify_mode = get_global_verify_mode(session)
                    items, total_pages = get_accounts_page(session, user.id, done=True, page=1)
                    if not items:
                        self.send_message(chat_id, "📭 Активных аккаунтов пока нет.", main_menu(is_admin=ensure_admin(user), verify_mode=verify_mode))
                        return
                    
                    # Send main menu first
                    self.send_message(chat_id, "📋 Активные аккаунты:", main_menu(is_admin=ensure_admin(user), verify_mode=verify_mode))
                    
                    # Send combined list with pagination
                    list_text = "Выберите аккаунт:"
                    combined_keyboard = {
                        "inline_keyboard": accounts_list_kb("ainfo", items)["inline_keyboard"] + 
                                        pagination_kb("apg", 1, total_pages)["inline_keyboard"]
                    }
                    self.send_message(chat_id, list_text, combined_keyboard)

            elif text == "Аккаунты на проверке":
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                # Import services
                try:
                    from .services.accounts import get_accounts_page
                    from .keyboards import accounts_list_kb, pagination_kb
                    from .services.system_settings import get_global_verify_mode
                except ImportError:
                    from services.accounts import get_accounts_page
                    from keyboards import accounts_list_kb, pagination_kb
                    from services.system_settings import get_global_verify_mode
                
                with session_factory() as session:
                    verify_mode = get_global_verify_mode(session)
                    items, total_pages = get_accounts_page(session, user.id, done=False, page=1)
                    if not items:
                        self.send_message(chat_id, "📭 Аккаунтов на проверке нет.", main_menu(is_admin=ensure_admin(user), verify_mode=verify_mode))
                        return
                    
                    # Send main menu first
                    self.send_message(chat_id, "🕒 Аккаунты на проверке:", main_menu(is_admin=ensure_admin(user), verify_mode=verify_mode))
                    
                    # Send combined list with pagination
                    list_text = "Выберите аккаунт:"
                    combined_keyboard = {
                        "inline_keyboard": accounts_list_kb("iinfo", items)["inline_keyboard"] + 
                                        pagination_kb("ipg", 1, total_pages)["inline_keyboard"]
                    }
                    self.send_message(chat_id, list_text, combined_keyboard)
            
            elif text == "Отмена" or text == "❌ Отмена":
                # Cancel any FSM operation
                if user_id in self.fsm_states:
                    state_data = self.fsm_states[user_id]
                    state = state_data.get("state", "")
                    
                    # Check if canceling from proxy test - return to proxies menu
                    if state == "waiting_proxy_test_username":
                        del self.fsm_states[user_id]
                        try:
                            from .keyboards import proxies_menu_kb
                        except ImportError:
                            from keyboards import proxies_menu_kb
                        self.send_message(chat_id, "❌ Тестирование отменено.", proxies_menu_kb())
                        return
                    
                    # Check if canceling from days operations - return to account info
                    elif state in ["waiting_for_add_days", "waiting_for_remove_days"]:
                        acc_id = state_data.get("acc_id")
                        back_prefix = state_data.get("back_prefix", "apg")
                        page = state_data.get("page", 1)
                        message_id = state_data.get("message_id")
                        
                        # Delete the "Enter days" message if it exists
                        if message_id:
                            try:
                                self.delete_message(chat_id, message_id)
                            except:
                                pass  # Ignore if message can't be deleted
                        
                        # Clear FSM state
                        del self.fsm_states[user_id]
                        
                        # Return to account info
                        try:
                            from .services.accounts import get_account_by_id
                            from .services.formatting import format_account_card
                            from .keyboards import account_card_kb
                        except ImportError:
                            from services.accounts import get_account_by_id
                            from services.formatting import format_account_card
                            from keyboards import account_card_kb
                        
                        with session_factory() as session:
                            # Get user object
                            user = get_or_create_user(session, type('User', (), {
                                'id': user_id,
                                'username': username
                            })())
                            acc = get_account_by_id(session, user.id, acc_id)
                            if acc:
                                # Use original format_account_card function
                                txt = format_account_card(acc)
                                
                                # Send account info without cancellation message
                                self.send_message(chat_id, txt, account_card_kb(acc.id, back_prefix, page))
                            else:
                                # Account not found, just send cancellation message
                                self.send_message(chat_id, "❌ Операция отменена. Аккаунт не найден.")
                    else:
                        # Default cancel behavior for other states - return to main menu
                        try:
                            from .services.system_settings import get_global_verify_mode
                        except ImportError:
                            from services.system_settings import get_global_verify_mode
                        with session_factory() as session:
                            verify_mode = get_global_verify_mode(session)
                        keyboard = main_menu(is_admin=ensure_admin(user), verify_mode=verify_mode)
                        self.send_message(chat_id, "❌ Отменено.", keyboard)
                    
                    del self.fsm_states[user_id]
                else:
                    # No FSM state, show main menu
                    try:
                        from .services.system_settings import get_global_verify_mode
                    except ImportError:
                        from services.system_settings import get_global_verify_mode
                    with session_factory() as session:
                        verify_mode = get_global_verify_mode(session)
                    keyboard = main_menu(is_admin=ensure_admin(user), verify_mode=verify_mode)
                    self.send_message(chat_id, "❌ Отменено.", keyboard)
            
            elif user_id in self.fsm_states:
                # Handle FSM states
                state_data = self.fsm_states[user_id]
                state = state_data.get("state")
                
                if state == "waiting_for_username":
                    # Process username input and create account immediately with 30 days
                    raw = text or ""
                    
                    # Import services
                    try:
                        from .services.accounts import normalize_username, find_duplicate, create_account
                        from .services.checker import is_valid_instagram_username, check_account_exists_placeholder
                    except ImportError:
                        from services.accounts import normalize_username, find_duplicate, create_account
                        from services.checker import is_valid_instagram_username, check_account_exists_placeholder
                    
                    username = normalize_username(raw)
                    if not is_valid_instagram_username(username):
                        self.send_message(chat_id, 
                            "⚠️ Неверный формат. Допустимы: буквы, цифры, точка, нижнее подчёркивание, до 30 символов.\n"
                            "Попробуйте снова или нажмите «Отмена».", 
                            cancel_kb()
                        )
                        return
                    
                    if not check_account_exists_placeholder(username):
                        self.send_message(chat_id, "⚠️ Похоже, такого аккаунта не существует. Введите другой или «Отмена».", cancel_kb())
                        return
                    
                    # Check for duplicates and create account immediately
                    with session_factory() as session:
                        try:
                            from .services.system_settings import get_global_verify_mode
                        except ImportError:
                            from services.system_settings import get_global_verify_mode
                        
                        verify_mode = get_global_verify_mode(session)
                        
                        if find_duplicate(session, user.id, username):
                            del self.fsm_states[user_id]
                            # Get verify_mode for keyboard
                            try:
                                from .services.system_settings import get_global_verify_mode
                            except ImportError:
                                from services.system_settings import get_global_verify_mode
                            verify_mode = get_global_verify_mode(session)
                            keyboard = main_menu(is_admin=ensure_admin(user), verify_mode=verify_mode)
                            self.send_message(chat_id, 
                                "⚠️ Такой аккаунт уже есть у вас в списке.\n"
                                "Откройте «Активные аккаунты» или добавьте другой.", 
                                keyboard
                            )
                            return
                        
                        # Create account with 30 days by default
                        acc = create_account(session, user.id, username, 30)
                        
                        # Get verify_mode for keyboard
                        try:
                            from .services.system_settings import get_global_verify_mode
                        except ImportError:
                            from services.system_settings import get_global_verify_mode
                        verify_mode_for_menu = get_global_verify_mode(session)
                    
                    # Clear FSM state
                    del self.fsm_states[user_id]
                    
                    # Send success message
                    keyboard = main_menu(is_admin=ensure_admin(user), verify_mode=verify_mode_for_menu)
                    self.send_message(chat_id, 
                        f"✅ Аккаунт <a href='https://www.instagram.com/{username}/'>@{username}</a> добавлен!\n\n"
                        f"📅 Период разблокировки: 30 дней\n"
                        f"📅 С: {acc.from_date.strftime('%d.%m.%Y')}\n"
                        f"📅 До: {acc.to_date.strftime('%d.%m.%Y')}\n\n"
                        f"🔄 Разблокировка запущена...",
                        keyboard
                    )
                    
                    # Auto-check account via main checker in separate thread
                    try:
                        from .services.main_checker import check_account_main
                        from .utils.encryptor import OptionalFernet
                        from .config import get_settings
                    except ImportError:
                        from services.main_checker import check_account_main
                        from utils.encryptor import OptionalFernet
                        from config import get_settings
                    
                    def auto_check_new_account():
                        try:
                            import asyncio
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            
                            settings = get_settings()
                            fernet = OptionalFernet(settings.encryption_key)
                            
                            with session_factory() as session:
                                # Get user's verify_mode
                                verify_mode = user.verify_mode or "api+instagram"
                                
                                ig_session = None
                                if verify_mode == "api+instagram":
                                    ig_session = get_active_session(session, user.id)
                                
                                if verify_mode == "api+instagram" and not ig_session:
                                    # Skip check if Instagram mode but no session
                                    self.send_message(user.id, f"ℹ️ <a href='https://www.instagram.com/{username}/'>@{username}</a> добавлен. Для проверки нужна IG-сессия.")
                                else:
                                    result = loop.run_until_complete(check_account_main(
                                        username=username,
                                        session=session,
                                        user_id=user.id,
                                        screenshot_path=f"screenshots/{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                                    ))
                                    
                                    # Send result based on check outcome
                                    success, message, screenshot_path = result
                                    
                                    if success:
                                        # Send success message with screenshot if available
                                        success_message = f"✅ <a href='https://www.instagram.com/{username}/'>@{username}</a> найден!\n📸 {message}"
                                        self.send_message(user.id, success_message)
                                        
                                        # Send screenshot if available
                                        if screenshot_path:
                                            import os
                                            print(f"[AUTO-CHECK] 📸 Screenshot path found: {screenshot_path}")
                                            
                                            if os.path.exists(screenshot_path):
                                                print(f"[AUTO-CHECK] 📸 Screenshot file exists, size: {os.path.getsize(screenshot_path)} bytes")
                                                try:
                                                    print(f"[AUTO-CHECK] 📸 Sending screenshot to user {user.id}...")
                                                    # Send photo
                                                    success = loop.run_until_complete(self.send_photo(
                                                        user.id,
                                                        screenshot_path,
                                                        f'📸 <a href="https://www.instagram.com/{username}/">@{username}</a>'
                                                    ))
                                                    
                                                    if success:
                                                        print(f"[AUTO-CHECK] 📸 Screenshot sent successfully!")
                                                        # Delete screenshot after sending (TEMPORARILY DISABLED)
                                                        # os.remove(screenshot_path)
                                                        # print(f"[AUTO-CHECK] 📸 Screenshot deleted: {screenshot_path}")
                                                        print(f"[AUTO-CHECK] 📸 Screenshot kept: {screenshot_path}")
                                                    else:
                                                        print(f"[AUTO-CHECK] ⚠️ Screenshot send returned False")
                                                except Exception as e:
                                                    print(f"[AUTO-CHECK] ❌ Failed to send photo: {e}")
                                                    import traceback
                                                    traceback.print_exc()
                                            else:
                                                print(f"[AUTO-CHECK] ⚠️ Screenshot file NOT found: {screenshot_path}")
                                    else:
                                        # Not found
                                        not_found_message = f"❌ <a href='https://www.instagram.com/{username}/'>@{username}</a> не найден"
                                        self.send_message(user.id, not_found_message)
                            
                            loop.close()
                        except Exception as e:
                            print(f"Auto-check error for @{username}: {e}")
                            # Send error message to user
                            self.send_message(user.id, f"⚠️ Ошибка при автопроверке @{username}: {str(e)}")
                    
                    import threading
                    threading.Thread(target=auto_check_new_account, daemon=True).start()
                
                
                elif state == "waiting_for_add_days":
                    # Process add days input
                    if not text.isdigit():
                        self.send_message(chat_id, "Нужно целое число > 0. Повторите.")
                        return
                    
                    amount = int(text)
                    if amount <= 0:
                        self.send_message(chat_id, "Нужно целое число > 0. Повторите.")
                        return
                    
                    acc_id = state_data.get("acc_id")
                    try:
                        from .services.accounts import get_account_by_id, increase_days
                        from .services.formatting import format_account_card
                        from .keyboards import account_card_kb
                    except ImportError:
                        from services.accounts import get_account_by_id, increase_days
                        from services.formatting import format_account_card
                        from keyboards import account_card_kb
                    
                    with session_factory() as session:
                        acc = get_account_by_id(session, user.id, acc_id)
                        if not acc:
                            del self.fsm_states[user_id]
                            self.send_message(chat_id, "Аккаунт не найден.")
                            return
                        
                        acc = increase_days(session, acc, amount)
                        if acc:
                            txt = format_account_card(acc)
                            
                            del self.fsm_states[user_id]
                            self.send_message(chat_id, f"✅ Обновлено:\n\n{txt}", account_card_kb(acc.id, state_data.get("back_prefix", "apg"), state_data.get("page", 1)))
                        else:
                            del self.fsm_states[user_id]
                            self.send_message(chat_id, "❌ Ошибка при обновлении аккаунта.")
                
                elif state == "waiting_for_remove_days":
                    # Process remove days input
                    if not text.isdigit():
                        self.send_message(chat_id, "Нужно целое число > 0. Повторите.")
                        return
                    
                    amount = int(text)
                    if amount <= 0:
                        self.send_message(chat_id, "Нужно целое число > 0. Повторите.")
                        return
                    
                    acc_id = state_data.get("acc_id")
                    try:
                        from .services.accounts import get_account_by_id, decrease_days
                        from .services.formatting import format_account_card
                        from .keyboards import account_card_kb
                    except ImportError:
                        from services.accounts import get_account_by_id, decrease_days
                        from services.formatting import format_account_card
                        from keyboards import account_card_kb
                    
                    with session_factory() as session:
                        acc = get_account_by_id(session, user.id, acc_id)
                        if not acc:
                            del self.fsm_states[user_id]
                            self.send_message(chat_id, "Аккаунт не найден.")
                            return
                        
                        acc = decrease_days(session, acc, amount)
                        if acc:
                            txt = format_account_card(acc)
                            
                            del self.fsm_states[user_id]
                            self.send_message(chat_id, f"✅ Обновлено:\n\n{txt}", account_card_kb(acc.id, state_data.get("back_prefix", "apg"), state_data.get("page", 1)))
                        else:
                            del self.fsm_states[user_id]
                            self.send_message(chat_id, "❌ Ошибка при обновлении аккаунта.")
                
                elif state == "waiting_for_proxy_url":
                    # Check for cancel
                    if text == "❌ Отмена":
                        del self.fsm_states[user_id]
                        try:
                            from .keyboards import proxies_menu_kb
                        except ImportError:
                            from keyboards import proxies_menu_kb
                        self.send_message(chat_id, "Добавление прокси отменено.", proxies_menu_kb())
                        return
                    
                    # Process proxy URL input
                    try:
                        from .services.proxy_parser import parse_proxy_url
                        from .keyboards import proxies_menu_kb
                    except ImportError:
                        from services.proxy_parser import parse_proxy_url
                        from keyboards import proxies_menu_kb
                    
                    data = parse_proxy_url(text)
                    if not data:
                        try:
                            from .keyboards import proxy_add_cancel_kb
                        except ImportError:
                            from keyboards import proxy_add_cancel_kb
                        self.send_message(chat_id, "⚠️ Неверный формат. Повторите.", proxy_add_cancel_kb())
                        return
                    
                    self.fsm_states[user_id]["proxy"] = data
                    self.fsm_states[user_id]["state"] = "waiting_for_proxy_priority"
                    
                    # Import keyboard
                    try:
                        from .keyboards import proxy_add_cancel_kb
                    except ImportError:
                        from keyboards import proxy_add_cancel_kb
                    
                    self.send_message(chat_id, "Укажите приоритет (1..10), где 1 — самый высокий:", proxy_add_cancel_kb())
                
                elif state == "waiting_for_proxy_priority":
                    # Check for cancel
                    if text == "❌ Отмена":
                        del self.fsm_states[user_id]
                        try:
                            from .keyboards import proxies_menu_kb
                        except ImportError:
                            from keyboards import proxies_menu_kb
                        self.send_message(chat_id, "Добавление прокси отменено.", proxies_menu_kb())
                        return
                    
                    # Process proxy priority input
                    if not text.isdigit():
                        try:
                            from .keyboards import proxy_add_cancel_kb
                        except ImportError:
                            from keyboards import proxy_add_cancel_kb
                        self.send_message(chat_id, "Нужно число 1..10.", proxy_add_cancel_kb())
                        return
                    
                    prio = int(text)
                    if not (1 <= prio <= 10):
                        try:
                            from .keyboards import proxy_add_cancel_kb
                        except ImportError:
                            from keyboards import proxy_add_cancel_kb
                        self.send_message(chat_id, "Диапазон 1..10.", proxy_add_cancel_kb())
                        return
                    
                    proxy = self.fsm_states[user_id].get("proxy")
                    del self.fsm_states[user_id]
                    
                    # Import services
                    try:
                        from .services.proxy_utils import save_proxy
                        from .keyboards import proxies_menu_kb
                    except ImportError:
                        from services.proxy_utils import save_proxy
                        from keyboards import proxies_menu_kb
                    
                    with session_factory() as session:
                        p = save_proxy(session, user.id, proxy, prio)
                    
                    self.send_message(chat_id, "✅ Прокси добавлен.", proxies_menu_kb())
                
                elif state == "waiting_for_proxy_list":
                    # Batch proxy import
                    try:
                        from .services.proxy_parser import parse_proxy_list, validate_proxy_data, deduplicate_proxies
                        from .services.proxy_service import get_active_proxies
                        from .models import Proxy
                        from .utils.encryptor import OptionalFernet
                        from .config import get_settings
                        from .keyboards import proxies_menu_kb
                    except ImportError:
                        from services.proxy_parser import parse_proxy_list, validate_proxy_data, deduplicate_proxies
                        from services.proxy_service import get_active_proxies
                        from models import Proxy
                        from utils.encryptor import OptionalFernet
                        from config import get_settings
                        from keyboards import proxies_menu_kb
                    
                    # Parse list
                    valid_proxies, parse_errors = parse_proxy_list(text)
                    
                    if not valid_proxies and not parse_errors:
                        self.send_message(chat_id, "⚠️ Не найдено ни одного прокси. Попробуйте снова или нажмите «Отмена».")
                        return
                    
                    # Get existing proxies
                    with session_factory() as session:
                        existing = session.query(Proxy).filter(Proxy.user_id == user.id).all()
                        existing_data = [
                            {'scheme': p.scheme, 'host': p.host}
                            for p in existing
                        ]
                        
                        # Deduplicate
                        unique_proxies, duplicates = deduplicate_proxies(existing_data, valid_proxies)
                    
                    # Validate all
                    validated = []
                    validation_errors = []
                    
                    for proxy_data in unique_proxies:
                        is_valid, error = validate_proxy_data(proxy_data)
                        if is_valid:
                            validated.append(proxy_data)
                        else:
                            validation_errors.append(f"{proxy_data['host']}: {error}")
                    
                    # Save validated proxies
                    added_count = 0
                    
                    if validated:
                        settings = get_settings()
                        encryptor = OptionalFernet(settings.encryption_key)
                        
                        with session_factory() as session:
                            for proxy_data in validated:
                                proxy = Proxy(
                                    user_id=user.id,
                                    scheme=proxy_data['scheme'],
                                    host=proxy_data['host'],
                                    username=proxy_data.get('username'),
                                    password=encryptor.encrypt(proxy_data['password']) if proxy_data.get('password') else None,
                                    is_active=True,
                                    priority=5  # Default priority
                                )
                                session.add(proxy)
                                added_count += 1
                            
                            session.commit()
                    
                    # Clear FSM
                    del self.fsm_states[user_id]
                    
                    # Format result message
                    result_parts = [
                        f"📦 <b>Результаты массового добавления:</b>\n"
                    ]
                    
                    if added_count > 0:
                        result_parts.append(f"✅ Добавлено: {added_count}")
                    
                    if duplicates > 0:
                        result_parts.append(f"⚠️ Дубликатов (пропущено): {duplicates}")
                    
                    if parse_errors:
                        result_parts.append(f"❌ Ошибок парсинга: {len(parse_errors)}")
                        if len(parse_errors) <= 5:
                            for err in parse_errors:
                                result_parts.append(f"  • {err}")
                        else:
                            for err in parse_errors[:3]:
                                result_parts.append(f"  • {err}")
                            result_parts.append(f"  ... и еще {len(parse_errors) - 3}")
                    
                    if validation_errors:
                        result_parts.append(f"❌ Ошибок валидации: {len(validation_errors)}")
                        if len(validation_errors) <= 5:
                            for err in validation_errors:
                                result_parts.append(f"  • {err}")
                        else:
                            for err in validation_errors[:3]:
                                result_parts.append(f"  • {err}")
                            result_parts.append(f"  ... и еще {len(validation_errors) - 3}")
                    
                    result_message = "\n".join(result_parts)
                    
                    if added_count > 0:
                        result_message += f"\n\n💡 Прокси добавлены с приоритетом 5. Измените при необходимости."
                    
                    self.send_message(chat_id, result_message, proxies_menu_kb())
                
                elif state == "waiting_for_account_period":
                    # Handle period selection
                    period_map = {
                        "📅 7 дней": 7,
                        "📅 14 дней": 14,
                        "📅 30 дней": 30,
                        "📅 60 дней": 60
                    }
                    
                    if text in period_map:
                        period = period_map[text]
                        # Store period and move to account list input
                        self.fsm_states[user_id]["period"] = period
                        self.fsm_states[user_id]["state"] = "waiting_for_account_list"
                        
                        try:
                            from .keyboards import cancel_kb
                        except ImportError:
                            from keyboards import cancel_kb
                        
                        self.send_message(chat_id, 
                            f"📝 **Массовое добавление аккаунтов** (период: {period} дней)\n\n"
                            "Отправьте список аккаунтов в формате:\n"
                            "```\n"
                            "username1; username2; username3\n"
                            "```\n\n"
                            "Аккаунты через точку с запятой, можно с @ или без.",
                            cancel_kb()
                        )
                    elif text == "❌ Отмена":
                        del self.fsm_states[user_id]
                        try:
                            from .keyboards import main_menu
                            from .services.system_settings import get_global_verify_mode
                        except ImportError:
                            from keyboards import main_menu
                            from services.system_settings import get_global_verify_mode
                        
                        with session_factory() as session:
                            verify_mode = get_global_verify_mode(session)
                        self.send_message(chat_id, "❌ Отменено.", main_menu(is_admin=ensure_admin(user), verify_mode=verify_mode))
                    else:
                        self.send_message(chat_id, "❌ Выберите период из предложенных вариантов.")
                
                elif state == "waiting_for_account_list":
                    # Handle cancellation
                    if text == "❌ Отмена":
                        del self.fsm_states[user_id]
                        try:
                            from .keyboards import main_menu
                            from .services.system_settings import get_global_verify_mode
                        except ImportError:
                            from keyboards import main_menu
                            from services.system_settings import get_global_verify_mode
                        
                        with session_factory() as session:
                            verify_mode = get_global_verify_mode(session)
                        self.send_message(chat_id, "❌ Отменено.", main_menu(is_admin=ensure_admin(user), verify_mode=verify_mode))
                        return
                    
                    # Batch account import
                    try:
                        from .models import Account
                        from .keyboards import main_menu, cancel_kb
                        from .utils.encryptor import OptionalFernet
                        from .config import get_settings
                        from .services.system_settings import get_global_verify_mode
                    except ImportError:
                        from models import Account
                        from keyboards import main_menu, cancel_kb
                        from utils.encryptor import OptionalFernet
                        from config import get_settings
                        from services.system_settings import get_global_verify_mode
                    
                    # Get verify_mode
                    with session_factory() as session:
                        verify_mode = get_global_verify_mode(session)
                    
                    # Parse account list (semicolon-separated)
                    usernames = [username.strip() for username in text.split(';') if username.strip()]
                    accounts = []
                    errors = []
                    auto_fixed_usernames = []  # Track auto-fixed usernames
                    
                    for username_input in usernames:
                        # Clean username
                        username = username_input.replace('@', '').strip().lower()
                        if not username:
                            continue
                        
                        # Auto-fix username: remove trailing underscores and dots
                        original_username = username
                        while username.endswith('_') or username.endswith('.'):
                            username = username.rstrip('_.')
                        
                        # Also remove leading underscores and dots
                        while username.startswith('_') or username.startswith('.'):
                            username = username.lstrip('_.')
                        
                        # If username was modified, add info message
                        if username != original_username:
                            print(f"[MASS-ADD] 🔧 Auto-fixed username: {original_username} → {username}")
                            auto_fixed_usernames.append(f"{original_username} → {username}")
                        
                        if not username:
                            errors.append(f"Username стал пустым после очистки: {username_input}")
                            continue
                        
                        # Validate username (Instagram rules)
                        if len(username) < 1 or len(username) > 30:
                            errors.append(f"Некорректная длина username: {username_input}")
                            continue
                        
                        # Check for valid characters (letters, numbers, dots, underscores)
                        import re
                        if not re.match(r'^[a-zA-Z0-9._]+$', username):
                            errors.append(f"Некорректные символы в username: {username_input}")
                            continue
                        
                        # Check for consecutive dots (Instagram doesn't allow this)
                        if '..' in username:
                            errors.append(f"Некорректный формат username: {username_input}")
                            continue
                        
                        # Check for starting/ending with dot or underscore
                        if username.startswith('.') or username.endswith('.') or username.startswith('_') or username.endswith('_'):
                            errors.append(f"Username не может начинаться/заканчиваться точкой или подчеркиванием: {username_input}")
                            continue
                        
                        # Check for duplicates in input
                        if username in [acc['username'] for acc in accounts]:
                            errors.append(f"Дубликат в списке: {username_input}")
                            continue
                        
                        accounts.append({
                            'username': username,
                            'original': username_input
                        })
                    
                    # Check if there are any valid accounts
                    if not accounts:
                        # Increment retry counter
                        if 'retry_count' not in self.fsm_states[user_id]:
                            self.fsm_states[user_id]['retry_count'] = 0
                        self.fsm_states[user_id]['retry_count'] += 1
                        
                        # Get selected period
                        period = self.fsm_states[user_id].get("period", 30)
                        
                        # Show error message with retry option
                        error_message = (
                            f"❌ <b>Не найдено валидных аккаунтов</b>\n\n"
                            f"<b>Ошибки валидации:</b>\n"
                        )
                        
                        if len(errors) <= 5:
                            for err in errors:
                                error_message += f"• {err}\n"
                        else:
                            for err in errors[:3]:
                                error_message += f"• {err}\n"
                            error_message += f"• ... и еще {len(errors) - 3} ошибок\n"
                        
                        error_message += (
                            f"\n<b>Попытка {self.fsm_states[user_id]['retry_count']}</b>\n\n"
                            f"📝 <b>Правильный формат:</b>\n"
                            f"<code>username1; username2; username3</code>\n\n"
                            f"💡 <b>Примеры:</b>\n"
                            f"<code>user1; user2; user3</code>\n"
                            f"<code>@user1; @user2; @user3</code>\n\n"
                            f"Попробуйте еще раз или нажмите «Отмена» для выхода."
                        )
                        
                        self.send_message(chat_id, error_message, cancel_kb())
                        return
                    
                    # Check if there are validation errors but some valid accounts
                    if errors and accounts:
                        # Increment retry counter
                        if 'retry_count' not in self.fsm_states[user_id]:
                            self.fsm_states[user_id]['retry_count'] = 0
                        self.fsm_states[user_id]['retry_count'] += 1
                        
                        # Get selected period
                        period = self.fsm_states[user_id].get("period", 30)
                        
                        # Show error message with retry option
                        error_message = (
                            f"⚠️ <b>Найдены ошибки валидации</b>\n\n"
                            f"✅ <b>Валидных аккаунтов:</b> {len(accounts)}\n"
                            f"❌ <b>Ошибок:</b> {len(errors)}\n\n"
                            f"<b>Ошибки валидации:</b>\n"
                        )
                        
                        if len(errors) <= 5:
                            for err in errors:
                                error_message += f"• {err}\n"
                        else:
                            for err in errors[:3]:
                                error_message += f"• {err}\n"
                            error_message += f"• ... и еще {len(errors) - 3} ошибок\n"
                        
                        error_message += (
                            f"\n<b>Попытка {self.fsm_states[user_id]['retry_count']}</b>\n\n"
                            f"📝 <b>Правильный формат:</b>\n"
                            f"<code>username1; username2; username3</code>\n\n"
                            f"💡 <b>Примеры:</b>\n"
                            f"<code>user1; user2; user3</code>\n"
                            f"<code>@user1; @user2; @user3</code>\n\n"
                            f"Попробуйте еще раз или нажмите «Отмена» для выхода."
                        )
                        
                        self.send_message(chat_id, error_message, cancel_kb())
                        return
                    
                    # Get selected period
                    period = self.fsm_states[user_id].get("period", 30)
                    
                    # Save accounts to database
                    settings = get_settings()
                    fernet = OptionalFernet(settings.encryption_key)
                    
                    added_count = 0
                    duplicates = 0
                    
                    with session_factory() as session:
                        for account_data in accounts:
                            username = account_data['username']
                            
                            # Check if account already exists
                            existing = session.query(Account).filter(
                                Account.user_id == user.id,
                                Account.account == username
                            ).first()
                            
                            if existing:
                                duplicates += 1
                                continue
                            
                            # Create new account with selected period
                            now = datetime.now()
                            account = Account(
                                user_id=user.id,
                                account=username,
                                from_date=date.today(),
                                from_date_time=now,  # Точное время добавления
                                to_date=date.today() + timedelta(days=period),
                                period=period,
                                done=False
                            )
                            
                            session.add(account)
                            added_count += 1
                        
                        session.commit()
                    
                    # Clear FSM
                    del self.fsm_states[user_id]
                    
                    # Format result message
                    result_parts = [
                        f"📝 <b>Результаты массового добавления аккаунтов:</b>\n"
                    ]
                    
                    if added_count > 0:
                        result_parts.append(f"✅ Добавлено: {added_count}")
                    
                    if duplicates > 0:
                        result_parts.append(f"⚠️ Дубликатов (пропущено): {duplicates}")
                    
                    if errors:
                        result_parts.append(f"❌ Ошибок: {len(errors)}")
                        if len(errors) <= 5:
                            for err in errors:
                                result_parts.append(f"  • {err}")
                        else:
                            for err in errors[:3]:
                                result_parts.append(f"  • {err}")
                            result_parts.append(f"  ... и еще {len(errors) - 3}")
                    
                    result_message = "\n".join(result_parts)
                    
                    # Add info about auto-fixed usernames
                    if auto_fixed_usernames:
                        result_message += f"\n\n🔧 <b>Автоматически исправлены username:</b>\n"
                        for fix in auto_fixed_usernames:
                            result_message += f"  • {fix}\n"
                    
                    if added_count > 0:
                        result_message += f"\n\n💡 Аккаунты добавлены на {period} дней. Измените при необходимости."
                        
                        # Start automatic check for added accounts
                        print(f"[MASS-ADD] 🚀 Starting auto-check for {added_count} accounts")
                        try:
                            import asyncio
                            from .services.main_checker import check_account_main
                            
                            async def auto_check_added_accounts():
                                """Auto-check newly added accounts in background."""
                                print(f"[AUTO-CHECK] 🔍 Starting auto-check for user {user.id}")
                                try:
                                    with session_factory() as session:
                                        # Get recently added accounts for this user
                                        recent_accounts = session.query(Account).filter(
                                            Account.user_id == user.id,
                                            Account.done == False
                                        ).order_by(Account.id.desc()).limit(added_count).all()
                                        
                                        print(f"[AUTO-CHECK] 📋 Found {len(recent_accounts)} accounts to check")
                                        
                                        checked_count = 0
                                        found_count = 0
                                        
                                        for acc in recent_accounts:
                                            print(f"[AUTO-CHECK] 🔍 Checking @{acc.account}")
                                            try:
                                                success, message, screenshot_path = await check_account_main(
                                                    username=acc.account,
                                                    session=session,
                                                    user_id=user.id,
                                                    screenshot_path=f"screenshots/{acc.account}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                                                )
                                                print(f"[AUTO-CHECK] 📊 Result for @{acc.account}: {success} - {message}")
                                                
                                                if success:
                                                    found_count += 1
                                                    # Mark as done
                                                    acc.done = True
                                                    acc.date_of_finish = date.today()
                                                
                                                checked_count += 1
                                                
                                                # Small delay between checks
                                                await asyncio.sleep(2)
                                                
                                            except Exception as e:
                                                print(f"[AUTO-CHECK] ❌ Error checking @{acc.account}: {e}")
                                                continue
                                        
                                        session.commit()
                                        
                                        # Send results
                                        if found_count > 0:
                                            result_message += f"\n\n🔍 <b>Автопроверка завершена:</b>\n✅ Найдено: {found_count}\n❌ Не найдено: {checked_count - found_count}"
                                        
                                        self.send_message(chat_id, result_message)
                                        
                                except Exception as e:
                                    print(f"[AUTO-CHECK] ❌ Error in auto-check: {e}")
                                    self.send_message(chat_id, result_message)
                            
                            # Start auto-check in background thread
                            import threading
                            
                            def run_auto_check():
                                """Run auto-check in separate thread."""
                                try:
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)
                                    loop.run_until_complete(auto_check_added_accounts())
                                except Exception as e:
                                    print(f"[AUTO-CHECK] ❌ Thread error: {e}")
                                finally:
                                    loop.close()
                            
                            # Start in background thread
                            thread = threading.Thread(target=run_auto_check, daemon=True)
                            thread.start()
                            
                        except Exception as e:
                            print(f"[AUTO-CHECK] ❌ Failed to start auto-check: {e}")
                            self.send_message(chat_id, result_message, main_menu(is_admin=ensure_admin(user), verify_mode=verify_mode))
                    else:
                        self.send_message(chat_id, result_message, main_menu(is_admin=ensure_admin(user), verify_mode=verify_mode))
                
                elif state == "waiting_for_delete_list":
                    # Handle cancellation
                    if text == "❌ Отмена":
                        del self.fsm_states[user_id]
                        try:
                            from .keyboards import main_menu
                            from .services.system_settings import get_global_verify_mode
                        except ImportError:
                            from keyboards import main_menu
                            from services.system_settings import get_global_verify_mode
                        
                        with session_factory() as session:
                            verify_mode = get_global_verify_mode(session)
                        self.send_message(chat_id, "❌ Отменено.", main_menu(is_admin=ensure_admin(user), verify_mode=verify_mode))
                        return
                    
                    # Parse account list (semicolon-separated)
                    usernames = [username.strip() for username in text.split(';') if username.strip()]
                    
                    if not usernames:
                        self.send_message(chat_id, "❌ Список аккаунтов пуст. Попробуйте еще раз.")
                        return
                    
                    # Get deletion type from FSM state
                    delete_type = self.fsm_states[user_id].get("delete_type", "all")
                    
                    # Store usernames and move to confirmation state
                    self.fsm_states[user_id]["usernames"] = usernames
                    self.fsm_states[user_id]["state"] = "waiting_for_delete_confirm"
                    
                    try:
                        from .keyboards import mass_delete_confirm_kb
                    except ImportError:
                        from keyboards import mass_delete_confirm_kb
                    
                    # Show confirmation message
                    type_names = {
                        "active": "активные",
                        "inactive": "неактивные", 
                        "all": "все"
                    }
                    
                    self.send_message(chat_id, 
                        f"⚠️ <b>Подтверждение удаления</b>\n\n"
                        f"Вы собираетесь удалить {len(usernames)} {type_names.get(delete_type, 'аккаунтов')}:\n\n"
                        f"<code>{'; '.join(usernames[:10])}</code>\n"
                        f"{'... и еще ' + str(len(usernames) - 10) if len(usernames) > 10 else ''}\n\n"
                        f"<b>Это действие нельзя отменить!</b>\n\n"
                        f"Подтвердите удаление:",
                        mass_delete_confirm_kb()
                    )
                
                elif state == "waiting_for_delete_confirm":
                    # Handle confirmation
                    if text == "✅ Да, удалить":
                        # Perform mass deletion
                        try:
                            from .services.accounts import mass_delete_accounts_by_usernames
                            from .keyboards import main_menu
                            from .services.system_settings import get_global_verify_mode
                        except ImportError:
                            from services.accounts import mass_delete_accounts_by_usernames
                            from keyboards import main_menu
                            from services.system_settings import get_global_verify_mode
                        
                        # Get verify_mode
                        with session_factory() as session:
                            verify_mode = get_global_verify_mode(session)
                        
                        # Get stored data
                        usernames = self.fsm_states[user_id].get("usernames", [])
                        delete_type = self.fsm_states[user_id].get("delete_type", "all")
                        
                        # Perform mass deletion
                        with session_factory() as session:
                            deleted_count, not_found_usernames = mass_delete_accounts_by_usernames(
                                session, user.id, usernames, delete_type
                            )
                        
                        # Clear FSM
                        del self.fsm_states[user_id]
                        
                        # Format result message
                        result_parts = [
                            f"🗑️ <b>Результаты массового удаления аккаунтов:</b>\n"
                        ]
                        
                        if deleted_count > 0:
                            result_parts.append(f"✅ Удалено: {deleted_count}")
                        
                        if not_found_usernames:
                            result_parts.append(f"⚠️ Не найдено: {len(not_found_usernames)}")
                            if len(not_found_usernames) <= 5:
                                for username in not_found_usernames:
                                    result_parts.append(f"  • {username}")
                            else:
                                for username in not_found_usernames[:3]:
                                    result_parts.append(f"  • {username}")
                                result_parts.append(f"  ... и еще {len(not_found_usernames) - 3}")
                        
                        result_message = "\n".join(result_parts)
                        
                        if deleted_count > 0:
                            result_message += f"\n\n💡 Удалены аккаунты типа: {delete_type}"
                        
                        self.send_message(chat_id, result_message, main_menu(is_admin=ensure_admin(user), verify_mode=verify_mode))
                    
                    elif text == "❌ Отмена":
                        del self.fsm_states[user_id]
                        try:
                            from .keyboards import main_menu
                            from .services.system_settings import get_global_verify_mode
                        except ImportError:
                            from keyboards import main_menu
                            from services.system_settings import get_global_verify_mode
                        
                        with session_factory() as session:
                            verify_mode = get_global_verify_mode(session)
                        self.send_message(chat_id, "❌ Отменено.", main_menu(is_admin=ensure_admin(user), verify_mode=verify_mode))
                
                elif state == "waiting_proxy_test_username":
                    # Handle username input for proxy testing
                    username = (text or "").strip().lower().replace("@", "")
                    
                    if not username:
                        # Create keyboard with Cancel button
                        cancel_keyboard = {
                            "keyboard": [
                                [{"text": "❌ Отмена"}]
                            ],
                            "resize_keyboard": True,
                            "one_time_keyboard": True
                        }
                        self.send_message(chat_id, "⚠️ Введите корректный username или нажмите «Отмена».", cancel_keyboard)
                        return
                    
                    # Import services
                    try:
                        from .services.accounts import normalize_username
                        from .services.checker import is_valid_instagram_username
                        from .services.proxy_service import get_proxy_by_id
                        from .services.proxy_tester import test_proxy_with_screenshot, test_multiple_proxies, format_batch_test_results
                        from .models import Proxy
                        from .keyboards import proxies_menu_kb
                        from .config import get_settings
                    except ImportError:
                        from services.accounts import normalize_username
                        from services.checker import is_valid_instagram_username
                        from services.proxy_service import get_proxy_by_id
                        from services.proxy_tester import test_proxy_with_screenshot, test_multiple_proxies, format_batch_test_results
                        from models import Proxy
                        from keyboards import proxies_menu_kb
                        from config import get_settings
                    
                    # Validate username
                    username = normalize_username(username)
                    if not is_valid_instagram_username(username):
                        # Create keyboard with Cancel button
                        cancel_keyboard = {
                            "keyboard": [
                                [{"text": "❌ Отмена"}]
                            ],
                            "resize_keyboard": True,
                            "one_time_keyboard": True
                        }
                        self.send_message(chat_id, "⚠️ Неверный формат username. Попробуйте снова или нажмите «Отмена».", cancel_keyboard)
                        return
                    
                    # Get state data
                    test_all = state_data.get("test_all", False)
                    proxy_id = state_data.get("proxy_id")
                    page = state_data.get("page", 1)
                    test_mode = state_data.get("test_mode", "default")
                    
                    # Clear FSM
                    del self.fsm_states[user_id]
                    
                    if test_all:
                        # Test all active proxies
                        mode_messages = {
                            "quick": "🧪 Быстрая проверка прокси (Desktop)",
                            "screenshot": "📸 Тест скриншота прокси (Desktop)",
                            "default": "🧪 Тестирование прокси (Desktop)"
                        }
                        
                        mode_message = mode_messages.get(test_mode, "🧪 Тестирование прокси")
                        
                        self.send_message(
                            chat_id,
                            f"⏳ Запускаю {mode_message.lower()} на аккаунте @{username}...\n\n"
                            f"Это может занять некоторое время."
                        )
                        
                        with session_factory() as session:
                            active_proxies = session.query(Proxy).filter(
                                Proxy.user_id == user.id,
                                Proxy.is_active == True
                            ).order_by(Proxy.priority.asc()).all()
                        
                        # Test in background thread
                        import threading
                        
                        def run_batch_test():
                            try:
                                import asyncio
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                
                                # Choose testing method based on mode
                                if test_mode == "quick":
                                    # Use basic connectivity test
                                    try:
                                        from .services.enhanced_proxy_tester import test_proxy_connectivity
                                    except ImportError:
                                        from services.enhanced_proxy_tester import test_proxy_connectivity
                                    
                                    results = {}
                                    for proxy in active_proxies:
                                        success, message, response_time = loop.run_until_complete(
                                            test_proxy_connectivity(proxy)
                                        )
                                        results[proxy.id] = {
                                            'success': success,
                                            'message': message,
                                            'response_time': response_time
                                        }
                                    
                                    # Format quick results
                                    summary = f"🧪 <b>Быстрая проверка прокси</b>\n\n"
                                    summary += f"📊 Всего прокси: {len(active_proxies)}\n"
                                    working_count = sum(1 for r in results.values() if r['success'])
                                    summary += f"✅ Работающих: {working_count}\n\n"
                                    
                                    for proxy in active_proxies:
                                        result = results.get(proxy.id, {})
                                        status = "✅" if result.get('success') else "❌"
                                        summary += f"{status} {proxy.host}: {result.get('message', 'Ошибка')}\n"
                                    
                                    self.send_message(chat_id, summary, proxies_menu_kb())
                                    
                                elif test_mode == "screenshot":
                                    # Use screenshot test
                                    try:
                                        from .services.enhanced_proxy_tester import test_proxy_screenshot
                                    except ImportError:
                                        from services.enhanced_proxy_tester import test_proxy_screenshot
                                    
                                    results = {}
                                    for proxy in active_proxies:
                                        success, message, screenshot_path = loop.run_until_complete(
                                            test_proxy_screenshot(proxy, username)
                                        )
                                        results[proxy.id] = {
                                            'success': success,
                                            'message': message,
                                            'screenshot_path': screenshot_path
                                        }
                                    
                                    # Format screenshot results
                                    summary = f"📸 <b>Тест скриншота прокси</b>\n\n"
                                    summary += f"📊 Всего прокси: {len(active_proxies)}\n"
                                    working_count = sum(1 for r in results.values() if r['success'])
                                    summary += f"✅ Работающих: {working_count}\n\n"
                                    
                                    for proxy in active_proxies:
                                        result = results.get(proxy.id, {})
                                        status = "✅" if result.get('success') else "❌"
                                        summary += f"{status} {proxy.host}: {result.get('message', 'Ошибка')}\n"
                                    
                                    self.send_message(chat_id, summary, proxies_menu_kb())
                                    
                                    # Send screenshots
                                    for proxy in active_proxies:
                                        result = results.get(proxy.id, {})
                                        if result.get('screenshot_path') and os.path.exists(result['screenshot_path']):
                                            loop.run_until_complete(self.send_photo(
                                                chat_id,
                                                result['screenshot_path'],
                                                caption=f"📸 {proxy.scheme}://{proxy.host}\n\n{result['message']}"
                                            ))
                                            # Clean up screenshot
                                            try:
                                                os.remove(result['screenshot_path'])
                                            except:
                                                pass
                                
                                else:
                                    # Default testing (original logic)
                                    results = loop.run_until_complete(
                                        test_multiple_proxies(active_proxies, username, with_screenshot=True)
                                    )
                                
                                # Send results
                                summary = format_batch_test_results(results, active_proxies)
                                self.send_message(chat_id, summary, proxies_menu_kb())
                                
                                # Send individual results with screenshots
                                for proxy in active_proxies:
                                    result = results.get(proxy.id, {})
                                    if result.get('screenshot') and os.path.exists(result['screenshot']):
                                        loop.run_until_complete(self.send_photo(
                                            chat_id,
                                            result['screenshot'],
                                            caption=f"📸 {proxy.scheme}://{proxy.host}\n\n{result['message']}"
                                        ))
                                        # Clean up screenshot
                                        try:
                                            os.remove(result['screenshot'])
                                        except:
                                            pass
                                    else:
                                        self.send_message(
                                            chat_id,
                                            f"🌐 {proxy.scheme}://{proxy.host}\n\n{result['message']}"
                                        )
                                
                                loop.close()
                                
                            except Exception as e:
                                self.send_message(chat_id, f"❌ Ошибка при тестировании: {str(e)}")
                        
                        test_thread = threading.Thread(target=run_batch_test, daemon=True)
                        test_thread.start()
                    
                    else:
                        # Test single proxy - получаем прокси сначала
                        with session_factory() as session:
                            proxy = get_proxy_by_id(session, user.id, proxy_id)
                            
                            if not proxy:
                                self.send_message(chat_id, "❌ Прокси не найден", proxies_menu_kb())
                                return
                        
                        self.send_message(
                            chat_id,
                            f"⏳ <b>Начинаю тестирование прокси</b>\n\n"
                            f"🔍 Проверяю аккаунт: @{username}\n"
                            f"🌐 Через прокси: {proxy.scheme}://{proxy.host}\n"
                            f"📸 Делаю скриншот профиля...\n\n"
                            f"⏰ Это может занять 10-30 секунд"
                        )
                        
                        # Test in background thread
                        import threading
                        
                        def run_single_test():
                            try:
                                import asyncio
                                
                                # Получаем прокси внутри функции
                                with session_factory() as session:
                                    proxy = get_proxy_by_id(session, user.id, proxy_id)
                                    
                                    if not proxy:
                                        self.send_message(chat_id, "❌ Прокси не найден", proxies_menu_kb())
                                        return
                                
                                # Уведомление о начале проверки
                                self.send_message(chat_id, "🔄 <b>Проверка запущена</b>\n\nПодключаюсь к Instagram через прокси...")
                                
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                
                                success, message, screenshot_path = loop.run_until_complete(
                                    test_proxy_with_screenshot(proxy, username)
                                )
                                
                                if success:
                                    if screenshot_path and os.path.exists(screenshot_path):
                                        # Send with screenshot
                                        loop.run_until_complete(self.send_photo(
                                            chat_id,
                                            screenshot_path,
                                            caption=f"✅ <b>Тестирование успешно!</b>\n\n📸 Скриншот профиля @{username}\n\n{message}"
                                        ))
                                        # Clean up
                                        try:
                                            os.remove(screenshot_path)
                                        except:
                                            pass
                                    else:
                                        # Send without screenshot
                                        self.send_message(chat_id, f"✅ <b>Тестирование успешно!</b>\n\n{message}")
                                else:
                                    # Send error message
                                    self.send_message(chat_id, f"❌ <b>Тестирование не удалось</b>\n\n{message}")
                                
                                # Back to menu
                                self.send_message(chat_id, "🏠 Возвращаюсь в меню прокси", proxies_menu_kb())
                                
                                loop.close()
                                
                            except Exception as e:
                                self.send_message(chat_id, f"❌ Ошибка при тестировании: {str(e)}")
                                self.send_message(chat_id, "Меню:", proxies_menu_kb())
                        
                        test_thread = threading.Thread(target=run_single_test, daemon=True)
                        test_thread.start()
                
                # Admin FSM states
                elif state in ["waiting_for_interval", "waiting_for_restart_confirm"]:
                    # Import admin handlers
                    try:
                        from .handlers.admin_menu import register_admin_menu_handlers
                    except ImportError:
                        from handlers.admin_menu import register_admin_menu_handlers
                    
                    text_handlers, fsm_handlers, callback_handlers = register_admin_menu_handlers(self, session_factory)
                    if state in fsm_handlers:
                        fsm_handlers[state](message, user)
                
                # API key FSM state
                elif state == "waiting_api_key":
                    key_value = (text or "").strip()
                    
                    # Check for cancel command
                    if key_value.lower() in ['/cancel', 'отмена', 'cancel', '❌ отмена']:
                        del self.fsm_states[user_id]
                        try:
                            from .keyboards import api_menu_kb
                        except ImportError:
                            from keyboards import api_menu_kb
                        self.send_message(chat_id, "❌ Добавление API ключа отменено.", api_menu_kb())
                        return
                    
                    if len(key_value) < 20:
                        try:
                            from .keyboards import api_add_cancel_kb
                        except ImportError:
                            from keyboards import api_add_cancel_kb
                        self.send_message(chat_id, "⚠️ Ключ слишком короткий. Пришлите действительный ключ.", api_add_cancel_kb())
                        return
                    
                    self.send_message(chat_id, "⏳ Проверяю ключ тестовым запросом...")
                    
                    try:
                        from .models import APIKey
                        from .services.api_keys import test_api_key
                        from .keyboards import api_menu_kb
                    except ImportError:
                        from models import APIKey
                        from services.api_keys import test_api_key
                        from keyboards import api_menu_kb
                    
                    import asyncio
                    import concurrent.futures
                    # Run async function in thread pool to avoid event loop conflict
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, test_api_key(key_value, test_username="instagram"))
                        try:
                            ok, err = future.result(timeout=30)  # 30 second timeout
                        except Exception as e:
                            ok, err = False, str(e)
                    
                    with session_factory() as s:
                        # Check if key already exists
                        existing_key = s.query(APIKey).filter(APIKey.key == key_value).first()
                        if existing_key:
                            self.send_message(chat_id, f"⚠️ Ключ уже существует (id={existing_key.id}).", api_menu_kb())
                            del self.fsm_states[user_id]
                            return
                        
                        obj = APIKey(
                            user_id=user.id,
                            key=key_value,
                            qty_req=0,
                            is_work=ok,
                        )
                        s.add(obj)
                        s.commit()
                        s.refresh(obj)
                    
                    del self.fsm_states[user_id]
                    if ok:
                        self.send_message(chat_id, f"✅ Ключ добавлен и валиден (id={obj.id}).", api_menu_kb())
                    else:
                        self.send_message(chat_id, f"⚠️ Ключ добавлен, но тест не пройден ({err or 'unknown'}).", api_menu_kb())
                
                # Instagram FSM states
                elif state in ["waiting_cookies", "waiting_username", "waiting_password"]:
                    # Process Instagram session flow
                    if hasattr(self, 'ig_menu_process_instagram_flow'):
                        self.ig_menu_process_instagram_flow(message, session_factory)
                    else:
                        # Fallback processing
                        if state == "waiting_cookies":
                            try:
                                import json
                                cookies = json.loads(text)
                                if not isinstance(cookies, list):
                                    raise ValueError
                                self.fsm_states[user_id]["cookies"] = cookies
                                self.fsm_states[user_id]["state"] = "waiting_username"
                                self.send_message(chat_id, "Укажите IG username для этой сессии:")
                            except Exception:
                                self.send_message(chat_id, "⚠️ Неверный JSON. Пришлите **список** cookie-объектов.")
                        elif state == "waiting_username":
                            ig_username = (text or "").strip().lstrip("@")
                            self.fsm_states[user_id]["ig_username"] = ig_username
                            if self.fsm_states[user_id].get("mode") == "cookies":
                                # Save session with cookies
                                try:
                                    from .services.ig_sessions import save_session
                                    from .utils.encryptor import OptionalFernet
                                    from .config import get_settings
                                except ImportError:
                                    from services.ig_sessions import save_session
                                    from utils.encryptor import OptionalFernet
                                    from config import get_settings
                                
                                settings = get_settings()
                                fernet = OptionalFernet(settings.encryption_key)
                                cookies = self.fsm_states[user_id].get("cookies")
                                
                                with session_factory() as s:
                                    obj = save_session(
                                        session=s,
                                        user_id=user.id,
                                        ig_username=ig_username,
                                        cookies_json=cookies,
                                        fernet=fernet,
                                    )
                                
                                del self.fsm_states[user_id]
                                self.send_message(chat_id, f"✅ Сессия @{ig_username} импортирована (id={obj.id}).")
                            else:
                                self.fsm_states[user_id]["state"] = "waiting_password"
                                self.send_message(chat_id, "Теперь введите пароль IG:")
                        elif state == "waiting_password":
                            # Handle password login (simplified)
                            del self.fsm_states[user_id]
                            self.send_message(chat_id, "⚠️ Логин по паролю пока не реализован. Используйте импорт cookies.")
            
            elif text == "Активные аккаунты":
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                self.send_message(chat_id, "📋 Список активных аккаунтов — появится на Этапе 3.")
            
            elif text == "Аккаунты на проверке":
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                self.send_message(chat_id, "🕒 Список аккаунтов на проверке — Этап 3.")
            
            elif text == "Instagram":
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                
                # Import Instagram menu handlers
                try:
                    from .handlers.ig_menu_simple import register_ig_menu_handlers
                    from .keyboards import instagram_menu_kb
                except ImportError:
                    from handlers.ig_menu_simple import register_ig_menu_handlers
                    from keyboards import instagram_menu_kb
                
                # Register handlers if not already registered
                if not hasattr(self, 'ig_menu_registered'):
                    register_ig_menu_handlers(self, session_factory)
                    register_ig_simple_check_handlers(self, session_factory)
                    self.ig_menu_registered = True
                
                # Process Instagram menu
                if hasattr(self, 'ig_menu_process_message'):
                    await self.ig_menu_process_message(message, session_factory)
                else:
                    self.send_message(chat_id, "Раздел «Instagram»", reply_markup=instagram_menu_kb())
            
            elif text in ["Добавить IG-сессию", "Мои IG-сессии", "Проверить через IG", "Назад в меню"]:
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                
                # Handle "Назад в меню" first
                if text == "Назад в меню":
                    try:
                        from .services.system_settings import get_global_verify_mode
                    except ImportError:
                        from services.system_settings import get_global_verify_mode
                    with session_factory() as session:
                        verify_mode = get_global_verify_mode(session)
                    keyboard = main_menu(is_admin=ensure_admin(user), verify_mode=verify_mode)
                    self.send_message(chat_id, "Главное меню:", keyboard)
                    return
                
                # Process Instagram menu messages
                if hasattr(self, 'ig_menu_process_message'):
                    await self.ig_menu_process_message(message, session_factory)
                elif hasattr(self, 'ig_simple_check_process_message'):
                    self.ig_simple_check_process_message(message, session_factory)
            
            elif text == "Проверить аккаунты":
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                
                # Start manual check in separate thread
                import threading
                
                def run_manual_check():
                    """Run manual check in separate thread."""
                    try:
                        # Import required modules
                        try:
                            from .models import Account
                            from .services.main_checker import check_account_main
                            from .utils.encryptor import OptionalFernet
                            from .config import get_settings
                        except ImportError:
                            from models import Account
                            from services.main_checker import check_account_main
                            from utils.encryptor import OptionalFernet
                            from config import get_settings
                        
                        settings = get_settings()
                        fernet = OptionalFernet(settings.encryption_key)
                        
                        # Get user's verify_mode
                        verify_mode = user.verify_mode or "api+instagram"
                        
                        with session_factory() as session:
                            pending = session.query(Account).filter(Account.user_id == user.id, Account.done == False).all()
                            # Only get Instagram session for api+instagram mode
                            if verify_mode == "api+instagram":
                                ig_session = get_active_session(session, user.id)
                            else:
                                ig_session = None
                        
                        if not pending:
                            self.send_message(chat_id, "📭 Нет аккаунтов на проверке.")
                            return
                        
                        # Check Instagram session only for api+instagram mode
                        if verify_mode == "api+instagram" and not ig_session:
                            self.send_message(chat_id, "⚠️ Нет активной Instagram-сессии. Добавьте её через меню 'Instagram'.")
                            return
                        
                        # Decode cookies only for api+instagram mode
                        cookies = None
                        if verify_mode == "api+instagram":
                            try:
                                cookies = decode_cookies(fernet, ig_session.cookies)
                            except Exception as e:
                                self.send_message(chat_id, f"❌ Ошибка расшифровки cookies: {e}")
                                return
                        
                        # Determine verification method based on user's mode
                        if verify_mode == "api+instagram":
                            method_text = "Instagram с скриншотами"
                        else:  # api+proxy
                            method_text = "Proxy с скриншотами"
                        
                        self.send_message(chat_id, f"🔍 Проверяю {len(pending)} аккаунтов через {method_text}...")
                        
                        ok = nf = unk = 0
                        for acc in pending:
                            try:
                                import asyncio
                                
                                # Use hybrid checker with user's verify_mode
                                result = asyncio.run(check_account_main(
                                    username=acc.account,
                                    session=session,
                                    user_id=user.id,
                                    screenshot_path=f"screenshots/{acc.account}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                                ))
                                
                                # Only send message if account exists
                                success, message, screenshot_path = result
                                
                                if success:
                                    # Calculate real time completed (days, hours, minutes)
                                    completed_text = "неизвестно"  # Default fallback for old accounts
                                    
                                    # Для старых аккаунтов без даты - установим текущее время как from_date_time
                                    if not acc.from_date and not acc.from_date_time:
                                        with session_factory() as update_session:
                                            db_acc = update_session.query(Account).filter(Account.id == acc.id).first()
                                            if db_acc:
                                                now = datetime.now()
                                                db_acc.from_date = date.today()
                                                db_acc.from_date_time = now
                                                db_acc.to_date = date.today() + timedelta(days=30)
                                                db_acc.period = 30
                                                update_session.commit()
                                                # Update local object
                                                acc.from_date = date.today()
                                                acc.from_date_time = now
                                                acc.to_date = date.today() + timedelta(days=30)
                                                acc.period = 30
                                    
                                    # Используем from_date_time если доступно, иначе from_date
                                    if hasattr(acc, 'from_date_time') and acc.from_date_time:
                                        start_datetime = acc.from_date_time
                                    elif acc.from_date:
                                        if isinstance(acc.from_date, datetime):
                                            start_datetime = acc.from_date
                                        else:
                                            # If only date, assume start of day
                                            start_datetime = datetime.combine(acc.from_date, datetime.min.time())
                                    else:
                                        start_datetime = None
                                    
                                    if start_datetime:
                                        current_datetime = datetime.now()
                                        time_diff = current_datetime - start_datetime
                                        total_seconds = int(time_diff.total_seconds())
                                        
                                        # Calculate days, hours, minutes
                                        days = total_seconds // 86400
                                        remaining_seconds = total_seconds % 86400
                                        hours = remaining_seconds // 3600
                                        minutes = (remaining_seconds % 3600) // 60
                                        
                                        # Format result: "X дней Y часов Z минут"
                                        parts = []
                                        if days > 0:
                                            parts.append(f"{days} {'день' if days == 1 else 'дней' if days > 4 else 'дня'}")
                                        if hours > 0:
                                            parts.append(f"{hours} {'час' if hours == 1 else 'часов' if hours > 4 else 'часа'}")
                                        if minutes > 0 or not parts:  # Show minutes if present or if no days/hours
                                            parts.append(f"{minutes} {'минута' if minutes == 1 else 'минут' if minutes > 4 else 'минуты'}")
                                        
                                        completed_text = " ".join(parts)
                                    
                                    # Format result in old bot format
                                    # Format start date with time if available
                                    if hasattr(acc, 'from_date_time') and acc.from_date_time:
                                        start_date_str = acc.from_date_time.strftime("%d.%m.%Y в %H:%M")
                                    elif acc.from_date:
                                        start_date_str = acc.from_date.strftime("%d.%m.%Y")
                                    else:
                                        start_date_str = "N/A"
                                    
                                    caption = f"""Имя пользователя: <a href="https://www.instagram.com/{acc.account}/">{acc.account}</a>
Начало работ: {start_date_str}
Заявлено: {acc.period} дней
Завершено за: {completed_text}
Конец работ: {acc.to_date.strftime("%d.%m.%Y") if acc.to_date else "N/A"}
Статус: Аккаунт разблокирован✅"""
                                    
                                    # Send result text
                                    self.send_message(chat_id, caption)
                                
                                # Send screenshot if available
                                if screenshot_path and os.path.exists(screenshot_path):
                                    try:
                                        asyncio.run(self.send_photo(chat_id, screenshot_path, f'📸 Скриншот <a href="https://www.instagram.com/{acc.account}/">@{acc.account}</a>'))
                                        # Delete screenshot after sending to save disk space (TEMPORARILY DISABLED)
                                        try:
                                            # os.remove(screenshot_path)
                                            # print(f"🗑️ Screenshot deleted: {screenshot_path}")
                                            print(f"🗑️ Screenshot kept: {screenshot_path}")
                                        except Exception as del_err:
                                            print(f"Warning: Failed to delete screenshot: {del_err}")
                                    except Exception as e:
                                        print(f"Failed to send photo: {e}")
                                
                                # Update account status
                                if success:
                                    with session_factory() as s2:
                                        account = s2.query(Account).get(acc.id)
                                        if account:
                                            account.done = True
                                            s2.commit()
                                    ok += 1
                                else:
                                    nf += 1
                            
                            except Exception as e:
                                self.send_message(chat_id, f"❌ Ошибка при проверке <a href=\"https://www.instagram.com/{acc.account}/\">@{acc.account}</a>: {str(e)}")
                                unk += 1
                        
                        # Final summary
                        summary = f"🎯 Готово!\n\n📊 Результаты:\n• Найдено: {ok}\n• Не найдено: {nf}\n• Ошибки: {unk}"
                        self.send_message(chat_id, summary)
                        
                    except Exception as e:
                        self.send_message(chat_id, f"❌ Критическая ошибка при проверке: {str(e)}")
                        print(f"Error in manual check thread: {e}")
                
                # Start check in background thread
                self.send_message(chat_id, "⏳ Запускаю проверку в фоновом режиме...")
                check_thread = threading.Thread(target=run_manual_check, daemon=True)
                check_thread.start()
            
            elif text == "Админка":
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                if not ensure_admin(user):
                    self.send_message(chat_id, "⛔ Доступ запрещен. Требуются права администратора.")
                    return
                # Import admin handlers
                try:
                    from .handlers.admin_menu import register_admin_menu_handlers
                except ImportError:
                    from handlers.admin_menu import register_admin_menu_handlers
                
                text_handlers, fsm_handlers, callback_handlers = register_admin_menu_handlers(self, session_factory)
                if "Админка" in text_handlers:
                    text_handlers["Админка"](message, user)
            
            elif text in ["Интервал автопроверки", "Режим проверки", "Статистика системы", "Перезапуск бота", 
                          "Управление пользователями", "Все пользователи", "Активные", 
                          "Неактивные", "Администраторы", "Удалить неактивных", "Назад в админку"]:
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                if not ensure_admin(user):
                    self.send_message(chat_id, "⛔ Доступ запрещен.")
                    return
                # Import admin handlers
                try:
                    from .handlers.admin_menu import register_admin_menu_handlers
                except ImportError:
                    from handlers.admin_menu import register_admin_menu_handlers
                
                text_handlers, fsm_handlers, callback_handlers = register_admin_menu_handlers(self, session_factory)
                if text in text_handlers:
                    text_handlers[text](message, user)
            
            elif text == "API":
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                # Import keyboards
                try:
                    from .keyboards import api_menu_kb
                except ImportError:
                    from keyboards import api_menu_kb
                self.send_message(chat_id, "Раздел «API ключи»", api_menu_kb())
            
            elif text in ["Мои API ключи", "Добавить API ключ", "Проверка через API (все)", "Проверка (API + скриншот)", "Назад в меню"]:
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                
                # Handle "Назад в меню" first
                if text == "Назад в меню":
                    try:
                        from .services.system_settings import get_global_verify_mode
                    except ImportError:
                        from services.system_settings import get_global_verify_mode
                    with session_factory() as session:
                        verify_mode = get_global_verify_mode(session)
                    keyboard = main_menu(is_admin=ensure_admin(user), verify_mode=verify_mode)
                    self.send_message(chat_id, "Главное меню:", keyboard)
                    return
                
                # Process API menu messages
                if hasattr(self, 'api_menu_process_message'):
                    self.api_menu_process_message(message, session_factory)
                elif hasattr(self, 'check_hybrid_process_message'):
                    self.check_hybrid_process_message(message, session_factory)
                else:
                    # Fallback - inline processing
                    if text == "Мои API ключи":
                        try:
                            from .models import APIKey
                            from .services.api_keys import list_keys_for_user
                            from .keyboards import api_key_card_kb, api_menu_kb
                        except ImportError:
                            from models import APIKey
                            from services.api_keys import list_keys_for_user
                            from keyboards import api_key_card_kb, api_menu_kb
                        
                        with session_factory() as s:
                            keys = list_keys_for_user(s, user.id)
                            if not keys:
                                self.send_message(chat_id, "📭 У вас ещё нет ключей.", api_menu_kb())
                            else:
                                for k in keys:
                                    masked = k.key[:4] + "..." + k.key[-4:] if k.key and len(k.key) > 8 else "***"
                                    key_text = (
                                        f"🔑 id={k.id}\n"
                                        f"• key: {masked}\n"
                                        f"• is_work: {'✅' if k.is_work else '❌'}\n"
                                        f"• qty_req (сегодня): {k.qty_req or 0}\n"
                                        f"• ref_date: {k.ref_date or 'N/A'}"
                                    )
                                    self.send_message(chat_id, key_text, api_key_card_kb(k.id))
                    
                    elif text == "Добавить API ключ":
                        self.fsm_states[user_id] = {"state": "waiting_api_key"}
                        try:
                            from .keyboards import api_add_cancel_kb
                        except ImportError:
                            from keyboards import api_add_cancel_kb
                        self.send_message(chat_id, "Пришлите ваш RapidAPI ключ (строка).", api_add_cancel_kb())
                    
                    elif text == "Проверка через API (все)":
                        try:
                            from .models import Account
                            from .services.check_via_api import check_account_exists_via_api
                        except ImportError:
                            from models import Account
                            from services.check_via_api import check_account_exists_via_api
                        
                        with session_factory() as s:
                            accs = s.query(Account).filter(Account.user_id == user.id, Account.done == False).all()
                        
                        if not accs:
                            self.send_message(chat_id, "📭 Нет аккаунтов на проверке.")
                        else:
                            # Run API check in separate thread
                            import threading
                            
                            def run_api_check():
                                """Run API check in separate thread."""
                                try:
                                    ok_count = nf_count = unk_count = 0
                                    import asyncio
                                    for a in accs:
                                        with session_factory() as s2:
                                            info = asyncio.run(check_account_exists_via_api(s2, user.id, a.account))
                                        
                                        if info["exists"] is True:
                                            ok_count += 1
                                        elif info["exists"] is False:
                                            nf_count += 1
                                        else:
                                            unk_count += 1
                                        
                                        mark = "✅" if info["exists"] is True else ("❌" if info["exists"] is False else "❓")
                                        error_msg = f" — {info.get('error')}" if info.get('error') else " — ok"
                                        self.send_message(chat_id, f"{mark} @{info['username']}{error_msg}")
                                    
                                    self.send_message(chat_id, 
                                        f"Готово: найдено — {ok_count}, не найдено — {nf_count}, неизвестно — {unk_count}."
                                    )
                                except Exception as e:
                                    self.send_message(chat_id, f"❌ Ошибка при проверке: {str(e)}")
                                    print(f"Error in API check thread: {e}")
                            
                            # Start check in background
                            self.send_message(chat_id, f"⏳ Запускаю проверку {len(accs)} аккаунтов через RapidAPI в фоновом режиме...")
                            check_thread = threading.Thread(target=run_api_check, daemon=True)
                            check_thread.start()
                    
                    elif text == "Проверка (API + скриншот)":
                        try:
                            from .models import Account
                            from .services.main_checker import check_account_main
                            from .utils.encryptor import OptionalFernet
                            from .config import get_settings
                        except ImportError:
                            from models import Account
                            from services.main_checker import check_account_main
                            from utils.encryptor import OptionalFernet
                            from config import get_settings
                        
                        settings = get_settings()
                        fernet = OptionalFernet(settings.encryption_key)
                        
                        # Get user's verify_mode
                        verify_mode = user.verify_mode or "api+instagram"
                        
                        with session_factory() as s:
                            accs = s.query(Account).filter(Account.user_id == user.id, Account.done == False).all()
                            # Only get Instagram session for api+instagram mode
                            if verify_mode == "api+instagram":
                                ig_session = get_active_session(s, user.id)
                            else:
                                ig_session = None
                        
                        if not accs:
                            self.send_message(chat_id, "📭 Нет аккаунтов на проверке.")
                        elif verify_mode == "api+instagram" and not ig_session:
                            self.send_message(chat_id,
                                "⚠️ Нет активной Instagram-сессии для скриншотов.\n"
                                "Будет выполнена только проверка через API.\n"
                                "Добавьте IG-сессию через меню 'Instagram' для получения скриншотов."
                            )
                        else:
                            # Run hybrid check in separate thread
                            import threading
                            
                            def run_hybrid_check():
                                """Run hybrid check in separate thread."""
                                try:
                                    ok_count = nf_count = unk_count = 0
                                    import asyncio
                                    # Get user's verify_mode
                                    verify_mode = user.verify_mode or "api+instagram"
                                    
                                    for a in accs:
                                        with session_factory() as s2:
                                            info = asyncio.run(check_account_main(
                                                username=a.account,
                                                session=s2,
                                                user_id=user.id,
                                                screenshot_path=f"screenshots/{a.account}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                                            ))
                                        
                                        success, message, screenshot_path = info
                                        
                                        if success:
                                            ok_count += 1
                                        else:
                                            nf_count += 1
                                        
                                        # Calculate real time completed (days, hours, minutes)
                                        completed_text = "неизвестно"  # Default fallback for old accounts
                                        
                                        # Для старых аккаунтов без даты - установим текущее время как from_date_time
                                        if not a.from_date and not a.from_date_time:
                                            with session_factory() as update_session:
                                                db_acc = update_session.query(Account).filter(Account.id == a.id).first()
                                                if db_acc:
                                                    now = datetime.now()
                                                    db_acc.from_date = date.today()
                                                    db_acc.from_date_time = now
                                                    db_acc.to_date = date.today() + timedelta(days=30)
                                                    db_acc.period = 30
                                                    update_session.commit()
                                                    # Update local object
                                                    a.from_date = date.today()
                                                    a.from_date_time = now
                                                    a.to_date = date.today() + timedelta(days=30)
                                                    a.period = 30
                                        
                                        # Используем from_date_time если доступно, иначе from_date
                                        if hasattr(a, 'from_date_time') and a.from_date_time:
                                            start_datetime = a.from_date_time
                                        elif a.from_date:
                                            if isinstance(a.from_date, datetime):
                                                start_datetime = a.from_date
                                            else:
                                                # If only date, assume start of day
                                                start_datetime = datetime.combine(a.from_date, datetime.min.time())
                                        else:
                                            start_datetime = None
                                        
                                        if start_datetime:
                                            current_datetime = datetime.now()
                                            time_diff = current_datetime - start_datetime
                                            total_seconds = int(time_diff.total_seconds())
                                            
                                            # Calculate days, hours, minutes
                                            days = total_seconds // 86400
                                            remaining_seconds = total_seconds % 86400
                                            hours = remaining_seconds // 3600
                                            minutes = (remaining_seconds % 3600) // 60
                                            
                                            # Format result: "X дней Y часов Z минут"
                                            parts = []
                                            if days > 0:
                                                parts.append(f"{days} {'день' if days == 1 else 'дней' if days > 4 else 'дня'}")
                                            if hours > 0:
                                                parts.append(f"{hours} {'час' if hours == 1 else 'часов' if hours > 4 else 'часа'}")
                                            if minutes > 0 or not parts:  # Show minutes if present or if no days/hours
                                                parts.append(f"{minutes} {'минута' if minutes == 1 else 'минут' if minutes > 4 else 'минуты'}")
                                            
                                            completed_text = " ".join(parts)
                                        
                                        # Format result in old bot format
                                        # Format start date with time if available
                                        if hasattr(a, 'from_date_time') and a.from_date_time:
                                            start_date_str = a.from_date_time.strftime("%d.%m.%Y в %H:%M")
                                        elif a.from_date:
                                            start_date_str = a.from_date.strftime("%d.%m.%Y")
                                        else:
                                            start_date_str = "N/A"
                                        
                                        caption = f"""Имя пользователя: <a href="https://www.instagram.com/{info['username']}/">{info['username']}</a>
Начало работ: {start_date_str}
Заявлено: {a.period} дней
Завершено за: {completed_text}
Конец работ: {a.to_date.strftime("%d.%m.%Y") if a.to_date else "N/A"}"""
                                        
                                        if info["exists"] is True:
                                            caption += "\nСтатус: Аккаунт разблокирован✅"
                                        elif info["exists"] is False:
                                            caption += "\nСтатус: Заблокирован❌"
                                        else:
                                            caption += "\nСтатус: ❓ не удалось определить"
                                        
                                        if info.get("error"):
                                            caption += f"\nОшибка: {info['error']}"
                                        
                                        self.send_message(chat_id, caption)
                                        
                                        if info.get("screenshot_path") and os.path.exists(info["screenshot_path"]):
                                            try:
                                                screenshot_path = info["screenshot_path"]
                                                asyncio.run(self.send_photo(chat_id, screenshot_path, f'📸 Скриншот <a href="https://www.instagram.com/{a.account}/">@{a.account}</a>'))
                                                # Delete screenshot after sending to save disk space (TEMPORARILY DISABLED)
                                                try:
                                                    # os.remove(screenshot_path)
                                                    # print(f"🗑️ Screenshot deleted: {screenshot_path}")
                                                    print(f"🗑️ Screenshot kept: {screenshot_path}")
                                                except Exception as del_err:
                                                    print(f"Warning: Failed to delete screenshot: {del_err}")
                                            except Exception as e:
                                                print(f"Failed to send photo: {e}")
                                    
                                    self.send_message(chat_id, 
                                        f"🎯 Готово!\n\n📊 Результаты:\n• Найдено: {ok_count}\n• Не найдено: {nf_count}\n• Ошибки: {unk_count}"
                                    )
                                except Exception as e:
                                    self.send_message(chat_id, f"❌ Ошибка при проверке: {str(e)}")
                                    print(f"Error in hybrid check thread: {e}")
                            
                            # Start check in background
                            self.send_message(chat_id, f"⏳ Запускаю гибридную проверку {len(accs)} аккаунтов в фоновом режиме...")
                            check_thread = threading.Thread(target=run_hybrid_check, daemon=True)
                            check_thread.start()

            elif text == "Прокси":
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                # Import keyboards
                try:
                    from .keyboards import proxies_menu_kb
                except ImportError:
                    from keyboards import proxies_menu_kb
                self.send_message(chat_id, "Раздел «Прокси»", proxies_menu_kb())

            elif text in ["Назад в меню", "🏠 Главное меню"]:
                try:
                    from .services.system_settings import get_global_verify_mode
                except ImportError:
                    from services.system_settings import get_global_verify_mode
                with session_factory() as session:
                    verify_mode = get_global_verify_mode(session)
                keyboard = main_menu(is_admin=ensure_admin(user), verify_mode=verify_mode)
                self.send_message(chat_id, "Главное меню:", keyboard)

            elif text == "Мои прокси":
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                
                # Import services
                try:
                    from .services.proxy_service import get_proxies_page, count_proxies
                    from .services.proxy_formatting import format_proxies_list_header
                    from .keyboards import proxies_list_kb, pagination_kb, proxies_menu_kb
                except ImportError:
                    from services.proxy_service import get_proxies_page, count_proxies
                    from services.proxy_formatting import format_proxies_list_header
                    from keyboards import proxies_list_kb, pagination_kb, proxies_menu_kb
                
                with session_factory() as session:
                    # Get first page
                    proxies, total_pages = get_proxies_page(session, user.id, page=1, per_page=10)
                    
                    if not proxies:
                        self.send_message(chat_id, "📭 У вас пока нет прокси.", proxies_menu_kb())
                        return
                    
                    # Get statistics
                    stats = count_proxies(session, user.id)
                    
                    # Format header
                    header = format_proxies_list_header(
                        page=1,
                        total_pages=total_pages,
                        total_count=stats['total'],
                        active_count=stats['active']
                    )
                    
                    # Send main menu first
                    self.send_message(chat_id, "🌐 Прокси:", proxies_menu_kb())
                    
                    # Create combined keyboard (list + pagination)
                    combined_keyboard = {
                        "inline_keyboard": proxies_list_kb(proxies)["inline_keyboard"] + 
                                        pagination_kb("ppg", 1, total_pages)["inline_keyboard"]
                    }
                    
                    # Send list with pagination
                    self.send_message(chat_id, header, combined_keyboard)

            elif text == "Добавить прокси":
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                # Start FSM for adding proxy
                self.fsm_states[user_id] = {"state": "waiting_for_proxy_url"}
                
                # Import keyboard
                try:
                    from .keyboards import proxy_add_cancel_kb
                except ImportError:
                    from keyboards import proxy_add_cancel_kb
                
                self.send_message(chat_id, 
                    "Введите прокси в формате:\n"
                    "`scheme://[user:pass@]host:port`\n"
                    "или\n"
                    "`host:port:user:pass`\n\n"
                    "Примеры:\n"
                    "`http://1.2.3.4:8080`\n"
                    "`socks5://user:pass@5.6.7.8:1080`\n"
                    "`example.com:8080:user:pass`",
                    proxy_add_cancel_kb()
                )

            elif text == "Массовое добавление":
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                
                # Start FSM for batch account import
                self.fsm_states[user_id] = {"state": "waiting_for_account_list"}
                
                try:
                    from .keyboards import cancel_kb
                except ImportError:
                    from keyboards import cancel_kb
                
                message = (
                    "📝 **Массовое добавление аккаунтов**\n\n"
                    "Отправьте список аккаунтов в формате:\n"
                    "```\n"
                    "username1; username2; username3\n"
                    "```\n\n"
                    "Аккаунты через точку с запятой, можно с @ или без."
                )
                
                self.send_message(chat_id, message, cancel_kb())
            
            elif text == "Массовое удаление":
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                
                # Start FSM for mass deletion of all accounts
                self.fsm_states[user_id] = {"state": "waiting_for_delete_list", "delete_type": "all"}
                
                try:
                    from .keyboards import cancel_kb
                except ImportError:
                    from keyboards import cancel_kb
                
                self.send_message(chat_id, 
                    "🗑️ **Массовое удаление всех аккаунтов**\n\n"
                    "Отправьте список аккаунтов в формате:\n"
                    "```\n"
                    "username1; username2; username3\n"
                    "```\n\n"
                    "Аккаунты через точку с запятой, можно с @ или без.\n"
                    "Будут удалены все указанные аккаунты (активные и неактивные).",
                    cancel_kb()
                )
            
            elif text == "📝 Массовое добавление аккаунтов":
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                
                # Start FSM for batch account import
                self.fsm_states[user_id] = {"state": "waiting_for_account_list"}
                
                try:
                    from .keyboards import cancel_kb
                except ImportError:
                    from keyboards import cancel_kb
                
                # Start FSM for period selection
                self.fsm_states[user_id] = {"state": "waiting_for_account_period"}
                
                try:
                    from .keyboards import account_period_kb
                except ImportError:
                    from keyboards import account_period_kb
                
                self.send_message(chat_id, 
                    "📝 **Массовое добавление аккаунтов**\n\n"
                    "Сначала выберите период для аккаунтов:",
                    account_period_kb()
                )
            
            elif text == "🌐 Массовое добавление прокси":
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                
                # Start FSM for batch proxy import
                self.fsm_states[user_id] = {"state": "waiting_for_proxy_list"}
                
                try:
                    from .services.proxy_parser import format_proxy_examples
                    from .keyboards import cancel_kb
                except ImportError:
                    from services.proxy_parser import format_proxy_examples
                    from keyboards import cancel_kb
                
                examples = format_proxy_examples()
                
                message = (
                    "📦 <b>Массовое добавление прокси</b>\n\n"
                    "Отправьте список прокси (один на строку или через ;):\n\n"
                    f"{examples}\n\n"
                    "💡 <b>Форматы ввода:</b>\n"
                    "• По строкам: каждый прокси с новой строки\n"
                    "• Через точку с запятой: proxy1;proxy2;proxy3\n\n"
                    "Или нажмите «Отмена» для выхода."
                )
                
                self.send_message(chat_id, message, cancel_kb())

            elif text == "🗑️ Удалить активные аккаунты":
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                
                # Start FSM for mass deletion of active accounts
                self.fsm_states[user_id] = {"state": "waiting_for_delete_list", "delete_type": "active"}
                
                try:
                    from .keyboards import cancel_kb
                except ImportError:
                    from keyboards import cancel_kb
                
                self.send_message(chat_id, 
                    "🗑️ **Массовое удаление активных аккаунтов**\n\n"
                    "Отправьте список аккаунтов в формате:\n"
                    "```\n"
                    "username1; username2; username3\n"
                    "```\n\n"
                    "Аккаунты через точку с запятой, можно с @ или без.\n"
                    "Будут удалены только активные аккаунты.",
                    cancel_kb()
                )

            elif text == "🗑️ Удалить неактивные аккаунты":
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                
                # Start FSM for mass deletion of inactive accounts
                self.fsm_states[user_id] = {"state": "waiting_for_delete_list", "delete_type": "inactive"}
                
                try:
                    from .keyboards import cancel_kb
                except ImportError:
                    from keyboards import cancel_kb
                
                self.send_message(chat_id, 
                    "🗑️ **Массовое удаление неактивных аккаунтов**\n\n"
                    "Отправьте список аккаунтов в формате:\n"
                    "```\n"
                    "username1; username2; username3\n"
                    "```\n\n"
                    "Аккаунты через точку с запятой, можно с @ или без.\n"
                    "Будут удалены только неактивные аккаунты.",
                    cancel_kb()
                )

            elif text == "🗑️ Удалить все аккаунты":
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                
                # Start FSM for mass deletion of all accounts
                self.fsm_states[user_id] = {"state": "waiting_for_delete_list", "delete_type": "all"}
                
                try:
                    from .keyboards import cancel_kb
                except ImportError:
                    from keyboards import cancel_kb
                
                self.send_message(chat_id, 
                    "🗑️ **Массовое удаление всех аккаунтов**\n\n"
                    "Отправьте список аккаунтов в формате:\n"
                    "```\n"
                    "username1; username2; username3\n"
                    "```\n\n"
                    "Аккаунты через точку с запятой, можно с @ или без.\n"
                    "Будут удалены все указанные аккаунты (активные и неактивные).",
                    cancel_kb()
                )

            elif text == "Тестировать прокси":
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                
                # Check if user has any active proxies
                try:
                    from .models import Proxy
                    from .keyboards import proxy_selection_for_test_kb, proxies_menu_kb
                except ImportError:
                    from models import Proxy
                    from keyboards import proxy_selection_for_test_kb, proxies_menu_kb
                
                with session_factory() as session:
                    active_proxies = session.query(Proxy).filter(
                        Proxy.user_id == user.id,
                        Proxy.is_active == True
                    ).order_by(Proxy.priority.asc()).all()
                    
                    if not active_proxies:
                        self.send_message(
                            chat_id,
                            "📭 У вас нет активных прокси для тестирования.\n\n"
                            "Добавьте прокси или активируйте существующие.",
                            proxies_menu_kb()
                        )
                        return
                
                # Show proxy selection directly (без выбора режима)
                message = (
                    f"🧪 <b>Выбор прокси для тестирования</b>\n\n"
                    f"📊 Доступно: {len(active_proxies)} прокси\n\n"
                    f"Выберите прокси для тестирования:"
                )
                
                keyboard = proxy_selection_for_test_kb(active_proxies)
                self.send_message(chat_id, message, keyboard)
            
            
            
            elif text == "⬅️ Назад в меню":
                try:
                    from .keyboards import main_menu
                    from .services.system_settings import get_global_verify_mode
                except ImportError:
                    from keyboards import main_menu
                    from services.system_settings import get_global_verify_mode
                with session_factory() as session:
                    verify_mode = get_global_verify_mode(session)
                self.send_message(chat_id, "Главное меню:", main_menu(ensure_admin(user), verify_mode=verify_mode))
            
            elif text == "Админка":
                if not ensure_admin(user):
                    self.send_message(chat_id, "⛔ Доступ запрещён. Нужны права администратора.")
                    return
                self.send_message(chat_id, "🛡 Админ-панель (заглушка). Разделы появятся на Этапе 6.")
            
            elif text and (text.startswith("/user_autocheck") or text == "/user_autocheck_list"):
                # Обработка команд управления автопроверкой пользователей
                try:
                    from .handlers.admin_auto_check import register_admin_auto_check_handlers
                except ImportError:
                    from handlers.admin_auto_check import register_admin_auto_check_handlers
                
                handlers = register_admin_auto_check_handlers(self, session_factory)
                
                # Find matching handler
                for cmd, handler in handlers.items():
                    if text.startswith(cmd) or text == cmd:
                        handler(message, user)
                        break
                else:
                    self.send_message(chat_id, "❌ Неизвестная команда. Используйте /user_autocheck_list для списка команд.")
            
            elif text and text.startswith("/traffic_stats"):
                # Обработка команды /traffic_stats для статистики трафика
                try:
                    from .services.traffic_monitor import get_traffic_monitor
                except ImportError:
                    from services.traffic_monitor import get_traffic_monitor
                
                try:
                    monitor = get_traffic_monitor()
                    total_stats = monitor.get_total_stats()
                    
                    if total_stats['total_requests'] == 0:
                        self.send_message(chat_id, "📊 Статистика трафика пуста. Запросы через прокси еще не выполнялись.")
                        return
                    
                    # Форматируем статистику
                    stats_text = f"📊 <b>СТАТИСТИКА ТРАФИКА</b>\n\n"
                    stats_text += f"📊 <b>Общий трафик:</b> {monitor._format_bytes(total_stats['total_traffic'])}\n"
                    stats_text += f"🔢 <b>Всего запросов:</b> {total_stats['total_requests']}\n"
                    stats_text += f"✅ <b>Успешных:</b> {total_stats['successful_requests']}\n"
                    stats_text += f"❌ <b>Неудачных:</b> {total_stats['failed_requests']}\n"
                    stats_text += f"📈 <b>Успешность:</b> {total_stats['success_rate']}%\n"
                    stats_text += f"⏱️ <b>Среднее время:</b> {total_stats['average_duration_ms']:.0f}ms\n"
                    stats_text += f"📊 <b>Средний трафик:</b> {monitor._format_bytes(total_stats['average_traffic_per_request'])}\n"
                    stats_text += f"🌐 <b>Прокси использовано:</b> {total_stats['proxies_used']}\n"
                    
                    if monitor.proxy_traffic:
                        stats_text += f"\n📊 <b>ПО ПРОКСИ:</b>\n"
                        for proxy_ip, proxy_stats in list(monitor.proxy_traffic.items())[:10]:  # Показываем первые 10
                            proxy_stats_detailed = monitor.get_proxy_stats(proxy_ip)
                            stats_text += f"\n🌐 <b>{proxy_ip}:</b>\n"
                            stats_text += f"  📊 Трафик: {monitor._format_bytes(proxy_stats['total_traffic'])}\n"
                            stats_text += f"  🔢 Запросов: {proxy_stats['total_requests']}\n"
                            stats_text += f"  ✅ Успешность: {proxy_stats_detailed['success_rate']}%\n"
                    
                    self.send_message(chat_id, stats_text)
                except Exception as e:
                    self.send_message(chat_id, f"❌ Ошибка получения статистики: {e}")
                    print(f"[BOT] ❌ Error in /traffic_stats: {e}")
                    import traceback
                    traceback.print_exc()
            
            else:
                # Handle other messages
                if ensure_active(user):
                    self.send_message(chat_id, "Используйте кнопки меню для навигации")
                else:
                    self.send_message(chat_id, "⛔ Доступ пока не выдан. Обратись к администратору.")


async def main():
    """Main function to start the bot."""
    # Setup logging
    settings = get_settings()
    logger = setup_logging(settings.log_level)
    
    logger.info("Starting bot...")
    
    # Initialize database
    engine = get_engine(settings.db_url)
    session_factory = get_session_factory(engine)
    init_db(engine)
    logger.info("Database initialized")
    
    # Create bot
    bot = TelegramBot(settings.bot_token)
    logger.info("Bot created")
    
    # Start APScheduler-based auto-checker
    # Auto-check interval is read from database (can be changed via admin menu)
    global _checker_scheduler
    global _expiry_scheduler
    try:
        from .auto_checker_scheduler import AutoCheckerScheduler
        from .expiry_scheduler import ExpiryNotificationScheduler
        from .services.system_settings import get_auto_check_interval
    except ImportError:
        from auto_checker_scheduler import AutoCheckerScheduler
        from expiry_scheduler import ExpiryNotificationScheduler
        from services.system_settings import get_auto_check_interval
    
    # Get current interval from database
    with session_factory() as session:
        interval_minutes = get_auto_check_interval(session)
    
    # Initialize and start auto-checker
    _checker_scheduler = AutoCheckerScheduler(
        bot_token=settings.bot_token,
        SessionLocal=session_factory,
        interval_minutes=interval_minutes,
        run_immediately=True,
    )
    _checker_scheduler.start()
    logger.info(f"APScheduler auto-checker started (every {interval_minutes} minutes)")
    
    # Get next run time
    next_run = _checker_scheduler.get_next_run_time()
    if next_run:
        logger.info(f"Next check scheduled at: {next_run}")
    
    # 🏥 Start Proxy Health Checker (background monitoring)
    try:
        from .services.proxy_health_checker import start_proxy_health_checker
    except ImportError:
        from services.proxy_health_checker import start_proxy_health_checker
    
    logger.info("🏥 Starting Proxy Health Checker (checks every 5 minutes)...")
    asyncio.create_task(start_proxy_health_checker())
    logger.info("✅ Proxy Health Checker started in background")
    
    # Initialize and start expiry notification scheduler (daily at 10:00 AM)
    from datetime import time as datetime_time
    _expiry_scheduler = ExpiryNotificationScheduler(
        bot_token=settings.bot_token,
        SessionLocal=session_factory,
        notification_time=datetime_time(10, 0)  # 10:00 AM
    )
    _expiry_scheduler.start()
    logger.info("Expiry notification scheduler started (daily at 10:00 AM)")
    
    # Get next expiry notification time
    next_expiry = _expiry_scheduler.get_next_run_time()
    if next_expiry:
        logger.info(f"Next expiry notification scheduled at: {next_expiry}")
    
    # Start polling
    logger.info("Starting polling...")
    
    while True:
        try:
            updates = bot.get_updates()
            
            if updates.get("ok") and updates.get("result"):
                for update in updates["result"]:
                    bot.last_update_id = update["update_id"]
                    
                    if "message" in update:
                        message = update["message"]
                        
                        # Check for web_app_data (from Mini App)
                        if "web_app_data" in message:
                            bot.process_web_app_data(message, session_factory)
                        else:
                            await bot.process_message(message, session_factory)
                    elif "callback_query" in update:
                        bot.process_callback_query(update["callback_query"], session_factory)
            
            time.sleep(1)  # Small delay between requests
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            # Stop scheduler
            try:
                _checker_scheduler.stop()
                logger.info("APScheduler auto-checker stopped")
            except Exception as e:
                logger.error(f"Error stopping auto-checker: {e}")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(5)  # Wait before retrying


if __name__ == "__main__":
    main()
