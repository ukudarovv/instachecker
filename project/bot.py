"""Main bot entrypoint."""

import time
import json
import os
import requests
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
    from .handlers.ig_menu import register_ig_menu_handlers
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
    from handlers.ig_menu import register_ig_menu_handlers
    from handlers.ig_simple_check import register_ig_simple_check_handlers
    from cron import start_cron
    # check_now_adv removed - functionality integrated directly into bot.py

# Global scheduler instance
_checker_scheduler = None


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
    
    def send_message(self, chat_id: int, text: str, reply_markup: Dict = None) -> bool:
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
            return response.json().get("ok", False)
        except requests.RequestException as e:
            print(f"Error sending message: {e}")
            # Try to send without HTML parsing if that's the issue
            try:
                data.pop("parse_mode", None)
                response = requests.post(url, json=data, timeout=10)
                response.raise_for_status()
                return response.json().get("ok", False)
            except requests.RequestException as e2:
                print(f"Error sending message (retry): {e2}")
            return False
    
    def send_photo(self, chat_id: int, photo_path: str, caption: str = None) -> bool:
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
                return response.json().get("ok", False)
        except (requests.RequestException, IOError) as e:
            print(f"Error sending photo: {e}")
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
                
                # Edit the existing message with new content
                list_text = "📋 Активные аккаунты:\n\nВыберите аккаунт:"
                combined_keyboard = {
                    "inline_keyboard": accounts_list_kb("ainfo", items)["inline_keyboard"] + 
                                    pagination_kb("apg", page, total_pages)["inline_keyboard"]
                }
                
                self.edit_message_text(chat_id, message_id, list_text, combined_keyboard)
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
                
                # Edit the existing message with new content
                list_text = "🕒 Аккаунты на проверке:\n\nВыберите аккаунт:"
                combined_keyboard = {
                    "inline_keyboard": accounts_list_kb("iinfo", items)["inline_keyboard"] + 
                                    pagination_kb("ipg", page, total_pages)["inline_keyboard"]
                }
                
                self.edit_message_text(chat_id, message_id, list_text, combined_keyboard)
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
                
                txt = format_account_card(acc)
                self.send_message(chat_id, txt, account_card_kb(acc_id, back_prefix, page))
                self.answer_callback_query(callback_query["id"])
                
            elif callback_data.startswith("addd:"):
                # Start add days FSM
                acc_id = int(callback_data.split(":")[1])
                self.fsm_states[user_id] = {
                    "state": "waiting_for_add_days",
                    "acc_id": acc_id,
                    "back_prefix": "apg",
                    "page": 1
                }
                self.send_message(chat_id, "Введите количество дней для добавления (целое > 0):")
                self.answer_callback_query(callback_query["id"])
                
            elif callback_data.startswith("subd:"):
                # Start subtract days FSM
                acc_id = int(callback_data.split(":")[1])
                self.fsm_states[user_id] = {
                    "state": "waiting_for_remove_days",
                    "acc_id": acc_id,
                    "back_prefix": "apg",
                    "page": 1
                }
                self.send_message(chat_id, "Введите количество дней для уменьшения (целое > 0):")
                self.answer_callback_query(callback_query["id"])
                
            elif callback_data.startswith("delc:"):
                # Confirm delete
                acc_id = int(callback_data.split(":")[1])
                try:
                    from .keyboards import confirm_delete_kb
                except ImportError:
                    from keyboards import confirm_delete_kb
                
                self.send_message(chat_id, "Удалить аккаунт безвозвратно?", confirm_delete_kb(acc_id, "apg", 1))
                self.answer_callback_query(callback_query["id"])
                
            elif callback_data.startswith("delok:"):
                # Confirm delete
                _, acc_id_s, back_prefix, page_s = callback_data.split(":")
                acc_id = int(acc_id_s)
                page = int(page_s)
                
                try:
                    from .services.accounts import get_account_by_id, delete_account
                except ImportError:
                    from services.accounts import get_account_by_id, delete_account
                
                acc = get_account_by_id(session, user.id, acc_id)
                if not acc:
                    self.answer_callback_query(callback_query["id"], "Не найдено/нет доступа", show_alert=True)
                    return
                
                delete_account(session, acc)
                self.send_message(chat_id, "✅ Удалено.")
                self.send_message(chat_id, "Вернитесь в список через кнопку «Активные аккаунты» или «Аккаунты на проверке».")
                self.answer_callback_query(callback_query["id"])
                
            elif callback_data.startswith("delno:"):
                # Cancel delete
                self.send_message(chat_id, "Отмена удаления.")
                self.answer_callback_query(callback_query["id"])
                
            elif callback_data.startswith("prx_off:") or callback_data.startswith("prx_on:") or callback_data.startswith("prx_pinc:") or callback_data.startswith("prx_pdec:") or callback_data.startswith("prx_del:"):
                # Handle proxy actions
                action, pid = callback_data.split(":")
                pid = int(pid)
                
                try:
                    from .models import Proxy
                    from .keyboards import proxy_card_kb
                except ImportError:
                    from models import Proxy
                    from keyboards import proxy_card_kb
                
                with session_factory() as session:
                    p = session.query(Proxy).filter(Proxy.id == pid, Proxy.user_id == user.id).one_or_none()
                    if not p:
                        self.answer_callback_query(callback_query["id"], "Не найдено/нет доступа", show_alert=True)
                        return
                    
                    if action == "prx_off":
                        p.is_active = False
                    elif action == "prx_on":
                        p.is_active = True
                    elif action == "prx_pinc":
                        p.priority = min(10, (p.priority or 5) + 1)
                    elif action == "prx_pdec":
                        p.priority = max(1, (p.priority or 5) - 1)
                    elif action == "prx_del":
                        session.delete(p)
                        session.commit()
                        self.send_message(chat_id, "🗑 Прокси удалён.")
                        self.answer_callback_query(callback_query["id"])
                        return
                    
                    session.commit()
                    session.refresh(p)
                    
                    # Format proxy info
                    creds = f"{p.username}:{p.password}@" if p.username and p.password else ""
                    proxy_text = (
                        f"🧩 Proxy #{p.id}\n"
                        f"• {p.scheme}://{creds}{p.host}\n"
                        f"• active: {p.is_active} | prio: {p.priority}\n"
                        f"• used: {p.used_count} | success: {p.success_count} | fail_streak: {p.fail_streak}\n"
                        f"• cooldown_until: {p.cooldown_until}\n"
                        f"• last_checked: {p.last_checked}"
                    )
                    
                    self.edit_message_text(chat_id, message_id, proxy_text, proxy_card_kb(p.id))
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
                ok, err = asyncio.run(test_api_key(key_value, test_username="instagram"))
                
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

    def process_message(self, message: Dict[str, Any], session_factory) -> None:
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
                
                keyboard = main_menu(is_admin=ensure_admin(user))
                self.send_message(chat_id, "Главное меню:", keyboard)
            
            elif text and text.lower() in {"меню", "menu"}:
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан. Обратись к администратору.")
                    return
                
                keyboard = main_menu(is_admin=ensure_admin(user))
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
                except ImportError:
                    from services.accounts import get_accounts_page
                    from keyboards import accounts_list_kb, pagination_kb
                
                with session_factory() as session:
                    items, total_pages = get_accounts_page(session, user.id, done=True, page=1)
                    if not items:
                        self.send_message(chat_id, "📭 Активных аккаунтов пока нет.", main_menu(is_admin=ensure_admin(user)))
                        return
                    
                    # Send main menu first
                    self.send_message(chat_id, "📋 Активные аккаунты:", main_menu(is_admin=ensure_admin(user)))
                    
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
                except ImportError:
                    from services.accounts import get_accounts_page
                    from keyboards import accounts_list_kb, pagination_kb
                
                with session_factory() as session:
                    items, total_pages = get_accounts_page(session, user.id, done=False, page=1)
                    if not items:
                        self.send_message(chat_id, "📭 Аккаунтов на проверке нет.", main_menu(is_admin=ensure_admin(user)))
                        return
                    
                    # Send main menu first
                    self.send_message(chat_id, "🕒 Аккаунты на проверке:", main_menu(is_admin=ensure_admin(user)))
                    
                    # Send combined list with pagination
                    list_text = "Выберите аккаунт:"
                    combined_keyboard = {
                        "inline_keyboard": accounts_list_kb("iinfo", items)["inline_keyboard"] + 
                                        pagination_kb("ipg", 1, total_pages)["inline_keyboard"]
                    }
                    self.send_message(chat_id, list_text, combined_keyboard)
            
            elif text == "Отмена":
                # Cancel any FSM operation
                if user_id in self.fsm_states:
                    del self.fsm_states[user_id]
                keyboard = main_menu(is_admin=ensure_admin(user))
                self.send_message(chat_id, "❌ Отменено.", keyboard)
            
            elif user_id in self.fsm_states:
                # Handle FSM states
                state_data = self.fsm_states[user_id]
                state = state_data.get("state")
                
                if state == "waiting_for_username":
                    # Process username input
                    raw = text or ""
                    
                    # Import services
                    try:
                        from .services.accounts import normalize_username
                        from .services.checker import is_valid_instagram_username, check_account_exists_placeholder
                    except ImportError:
                        from services.accounts import normalize_username
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
                    
                    # Store username and move to next step
                    self.fsm_states[user_id]["username"] = username
                    self.fsm_states[user_id]["state"] = "waiting_for_days"
                    self.send_message(chat_id, "📅 Введите количество дней работы (целое число > 0):", cancel_kb())
                
                elif state == "waiting_for_days":
                    # Process days input
                    if not text.isdigit():
                        self.send_message(chat_id, "⚠️ Нужно целое число дней. Попробуйте снова или «Отмена».", cancel_kb())
                        return
                    
                    days = int(text)
                    if days <= 0:
                        self.send_message(chat_id, "⚠️ Число дней должно быть больше нуля. Попробуйте снова или «Отмена».", cancel_kb())
                        return
                    
                    # Get stored username
                    username = self.fsm_states[user_id].get("username", "")
                    
                    # Check for duplicates
                    try:
                        from .services.accounts import find_duplicate, create_account
                    except ImportError:
                        from services.accounts import find_duplicate, create_account
                    
                    with session_factory() as session:
                        if find_duplicate(session, user.id, username):
                            del self.fsm_states[user_id]
                            keyboard = main_menu(is_admin=ensure_admin(user))
                            self.send_message(chat_id, 
                                "⚠️ Такой аккаунт уже есть у вас в списке.\n"
                                "Откройте «Активные аккаунты» или добавьте другой.", 
                                keyboard
                            )
                            return
                        
                        # Create account
                        acc = create_account(session, user.id, username, days)
                    
                    # Clear FSM state
                    del self.fsm_states[user_id]
                    
                    # Auto-check account via hybrid method
                    try:
                        from .services.hybrid_checker import check_account_hybrid
                        from .services.ig_sessions import get_active_session
                        from .utils.encryptor import OptionalFernet
                        from .config import get_settings
                    except ImportError:
                        from services.hybrid_checker import check_account_hybrid
                        from services.ig_sessions import get_active_session
                        from utils.encryptor import OptionalFernet
                        from config import get_settings
                    
                    settings = get_settings()
                    fernet = OptionalFernet(settings.encryption_key)
                    
                    with session_factory() as s:
                        ig_session = get_active_session(s, user.id)
                    
                    keyboard = main_menu(is_admin=ensure_admin(user))
                    
                    # Check if we have any way to verify
                    if not ig_session:
                        self.send_message(chat_id, 
                            f"✅ Аккаунт добавлен.\n"
                            f"• Имя: @{acc.account}\n"
                            f"• Дата старта: {acc.from_date}\n"
                            f"• Период (дней): {acc.period}\n"
                            f"• До: {acc.to_date}\n\n"
                            "⚠️ Нет Instagram сессии для автоматической проверки.\n"
                            "Добавьте IG-сессию через меню 'Instagram' для проверки.",
                            keyboard
                        )
                        return
                    
                    # Perform hybrid check
                    import asyncio
                    
                    async def check_with_timeout():
                        with session_factory() as s2:
                            return await check_account_hybrid(
                                session=s2,
                                user_id=user.id,
                                username=username,
                                ig_session=ig_session,
                                fernet=fernet
                            )
                    
                    try:
                        # Set timeout for the check (30 seconds)
                        check_result = asyncio.run(asyncio.wait_for(check_with_timeout(), timeout=30.0))
                        
                        # Build single message with account info and status
                        status_mark = "✅" if check_result["exists"] is True else ("❌" if check_result["exists"] is False else "❓")
                        status_text = "Аккаунт найден и отмечен как активный!" if check_result["exists"] is True else "Аккаунт не найден"
                        
                        message_text = (
                            f"✅ Аккаунт добавлен.\n"
                            f"• Имя: @{acc.account}\n"
                            f"• Дата старта: {acc.from_date}\n"
                            f"• Период (дней): {acc.period}\n"
                            f"• До: {acc.to_date}\n\n"
                            f"{status_mark} {status_text}"
                        )
                        
                        self.send_message(chat_id, message_text, keyboard)
                        
                        # Send screenshot if available
                        if check_result.get("screenshot_path") and os.path.exists(check_result["screenshot_path"]):
                            try:
                                screenshot_path = check_result["screenshot_path"]
                                self.send_photo(chat_id, screenshot_path, f"📸 @{username}")
                                # Delete screenshot after sending to save disk space
                                try:
                                    os.remove(screenshot_path)
                                    print(f"🗑️ Screenshot deleted: {screenshot_path}")
                                except Exception as del_err:
                                    print(f"Warning: Failed to delete screenshot: {del_err}")
                            except Exception as e:
                                print(f"Failed to send photo: {e}")
                    
                    except asyncio.TimeoutError:
                        self.send_message(chat_id, 
                            f"✅ Аккаунт добавлен.\n"
                            f"• Имя: @{acc.account}\n"
                            f"• Дата старта: {acc.from_date}\n"
                            f"• Период (дней): {acc.period}\n"
                            f"• До: {acc.to_date}\n\n"
                            "⚠️ Проверка превысила время ожидания (30 сек).",
                            keyboard
                        )
                    except Exception as e:
                        self.send_message(chat_id, 
                            f"✅ Аккаунт добавлен.\n"
                            f"• Имя: @{acc.account}\n"
                            f"• Дата старта: {acc.from_date}\n"
                            f"• Период (дней): {acc.period}\n"
                            f"• До: {acc.to_date}\n\n"
                            f"⚠️ Ошибка при проверке: {str(e)}",
                        keyboard
                    )
                
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
                        txt = format_account_card(acc)
                    
                    del self.fsm_states[user_id]
                    self.send_message(chat_id, "Обновлено:")
                    self.send_message(chat_id, txt, account_card_kb(acc.id, state_data.get("back_prefix", "apg"), state_data.get("page", 1)))
                
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
                        txt = format_account_card(acc)
                    
                    del self.fsm_states[user_id]
                    self.send_message(chat_id, "Обновлено:")
                    self.send_message(chat_id, txt, account_card_kb(acc.id, state_data.get("back_prefix", "apg"), state_data.get("page", 1)))
                
                elif state == "waiting_for_proxy_url":
                    # Process proxy URL input
                    try:
                        from .services.proxy_utils import parse_proxy_url
                        from .keyboards import proxies_menu_kb
                    except ImportError:
                        from services.proxy_utils import parse_proxy_url
                        from keyboards import proxies_menu_kb
                    
                    data = parse_proxy_url(text)
                    if not data:
                        self.send_message(chat_id, "⚠️ Неверный формат. Повторите.")
                        return
                    
                    self.fsm_states[user_id]["proxy"] = data
                    self.fsm_states[user_id]["state"] = "waiting_for_proxy_priority"
                    self.send_message(chat_id, "Укажите приоритет (1..10), где 1 — самый высокий:")
                
                elif state == "waiting_for_proxy_priority":
                    # Process proxy priority input
                    if not text.isdigit():
                        self.send_message(chat_id, "Нужно число 1..10.")
                        return
                    
                    prio = int(text)
                    if not (1 <= prio <= 10):
                        self.send_message(chat_id, "Диапазон 1..10.")
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
                    if len(key_value) < 20:
                        self.send_message(chat_id, "⚠️ Ключ слишком короткий. Пришлите действительный ключ.")
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
                    ok, err = asyncio.run(test_api_key(key_value, test_username="instagram"))
                    
                    with session_factory() as s:
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
                    from .handlers.ig_menu import register_ig_menu_handlers
                    from .keyboards import instagram_menu_kb
                except ImportError:
                    from handlers.ig_menu import register_ig_menu_handlers
                    from keyboards import instagram_menu_kb
                
                # Register handlers if not already registered
                if not hasattr(self, 'ig_menu_registered'):
                    register_ig_menu_handlers(self, session_factory)
                    register_ig_simple_check_handlers(self, session_factory)
                    self.ig_menu_registered = True
                
                # Process Instagram menu
                if hasattr(self, 'ig_menu_process_message'):
                    self.ig_menu_process_message(message, session_factory)
                else:
                    self.send_message(chat_id, "Раздел «Instagram»", reply_markup=instagram_menu_kb())
            
            elif text in ["Добавить IG-сессию", "Мои IG-сессии", "Проверить через IG", "Назад в меню"]:
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                
                # Handle "Назад в меню" first
                if text == "Назад в меню":
                    keyboard = main_menu(is_admin=ensure_admin(user))
                    self.send_message(chat_id, "Главное меню:", keyboard)
                    return
                
                # Process Instagram menu messages
                if hasattr(self, 'ig_menu_process_message'):
                    self.ig_menu_process_message(message, session_factory)
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
                            from .services.ig_sessions import get_active_session, decode_cookies
                            from .utils.encryptor import OptionalFernet
                            from .config import get_settings
                            from .services.ig_simple_checker import check_account_with_screenshot
                        except ImportError:
                            from models import Account
                            from services.ig_sessions import get_active_session, decode_cookies
                            from utils.encryptor import OptionalFernet
                            from config import get_settings
                            from services.ig_simple_checker import check_account_with_screenshot
                        
                        settings = get_settings()
                        fernet = OptionalFernet(settings.encryption_key)
                        
                        with session_factory() as session:
                            pending = session.query(Account).filter(Account.user_id == user.id, Account.done == False).all()
                            ig_session = get_active_session(session, user.id)
                        
                        if not pending:
                            self.send_message(chat_id, "📭 Нет аккаунтов на проверке.")
                            return
                        
                        if not ig_session:
                            self.send_message(chat_id, "⚠️ Нет активной Instagram-сессии. Добавьте её через меню 'Instagram'.")
                            return
                        
                        # Decode cookies
                        try:
                            cookies = decode_cookies(fernet, ig_session.cookies)
                        except Exception as e:
                            self.send_message(chat_id, f"❌ Ошибка расшифровки cookies: {e}")
                            return
                        
                        self.send_message(chat_id, f"🔍 Проверяю {len(pending)} аккаунтов через Instagram с скриншотами...")
                        
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
                                
                                # Only send message if account exists
                                if result.get("exists") is True:
                                    # Format result for existing accounts
                                    lines = [f"@{result['username']}"]
                                    if result.get("full_name"): 
                                        lines.append(f"Имя: {result['full_name']}")
                                    if result.get("followers") is not None: 
                                        lines.append(f"Подписчики: {result['followers']:,}")
                                    if result.get("following") is not None: 
                                        lines.append(f"Подписки: {result['following']:,}")
                                    if result.get("posts") is not None: 
                                        lines.append(f"Посты: {result['posts']:,}")
                                    lines.append("Статус: ✅ найден")
                                    
                                    caption = "\n".join(lines)
                                    
                                    # Send result text
                                    self.send_message(chat_id, caption)
                                
                                # Send screenshot if available
                                if result.get("screenshot_path") and os.path.exists(result["screenshot_path"]):
                                    try:
                                        screenshot_path = result["screenshot_path"]
                                        self.send_photo(chat_id, screenshot_path, f"📸 Скриншот @{acc.account}")
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
                                self.send_message(chat_id, f"❌ Ошибка при проверке @{acc.account}: {str(e)}")
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
            
            elif text in ["Интервал автопроверки", "Статистика системы", "Перезапуск бота", 
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
                    keyboard = main_menu(is_admin=ensure_admin(user))
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
                        self.send_message(chat_id, "Пришлите ваш RapidAPI ключ (строка).")
                    
                    elif text == "Проверка через API (все)":
                        self.send_message(chat_id, "⏳ Проверяю аккаунты через RapidAPI...")
                        
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
                    
                    elif text == "Проверка (API + скриншот)":
                        self.send_message(chat_id, "⏳ Проверяю аккаунты через API + Instagram (со скриншотами)...")
                        
                        try:
                            from .models import Account
                            from .services.hybrid_checker import check_account_hybrid
                            from .services.ig_sessions import get_active_session
                            from .utils.encryptor import OptionalFernet
                            from .config import get_settings
                        except ImportError:
                            from models import Account
                            from services.hybrid_checker import check_account_hybrid
                            from services.ig_sessions import get_active_session
                            from utils.encryptor import OptionalFernet
                            from config import get_settings
                        
                        settings = get_settings()
                        fernet = OptionalFernet(settings.encryption_key)
                        
                        with session_factory() as s:
                            accs = s.query(Account).filter(Account.user_id == user.id, Account.done == False).all()
                            ig_session = get_active_session(s, user.id)
                        
                        if not accs:
                            self.send_message(chat_id, "📭 Нет аккаунтов на проверке.")
                        elif not ig_session:
                            self.send_message(chat_id,
                                "⚠️ Нет активной Instagram-сессии для скриншотов.\n"
                                "Будет выполнена только проверка через API.\n"
                                "Добавьте IG-сессию через меню 'Instagram' для получения скриншотов."
                            )
                        else:
                            ok_count = nf_count = unk_count = 0
                            import asyncio
                            for a in accs:
                                with session_factory() as s2:
                                    info = asyncio.run(check_account_hybrid(
                                        session=s2,
                                        user_id=user.id,
                                        username=a.account,
                                        ig_session=ig_session,
                                        fernet=fernet
                                    ))
                                
                                if info["exists"] is True:
                                    ok_count += 1
                                elif info["exists"] is False:
                                    nf_count += 1
                                else:
                                    unk_count += 1
                                
                                mark = "✅" if info["exists"] is True else ("❌" if info["exists"] is False else "❓")
                                lines = [f"{mark} @{info['username']}"]
                                
                                if info.get("full_name"):
                                    lines.append(f"Имя: {info['full_name']}")
                                if info.get("followers") is not None:
                                    lines.append(f"Подписчики: {info['followers']:,}")
                                if info.get("following") is not None:
                                    lines.append(f"Подписки: {info['following']:,}")
                                if info.get("posts") is not None:
                                    lines.append(f"Посты: {info['posts']:,}")
                                
                                check_via = info.get("checked_via", "unknown")
                                if check_via == "api+instagram":
                                    lines.append("🔍 Проверено: API + Instagram")
                                elif check_via == "api":
                                    lines.append("🔍 Проверено: API")
                                elif check_via == "instagram_only":
                                    lines.append("🔍 Проверено: Instagram")
                                
                                if info.get("error"):
                                    lines.append(f"⚠️ {info['error']}")
                                
                                caption = "\n".join(lines)
                                self.send_message(chat_id, caption)
                                
                                if info.get("screenshot_path") and os.path.exists(info["screenshot_path"]):
                                    try:
                                        screenshot_path = info["screenshot_path"]
                                        self.send_photo(chat_id, screenshot_path, f"📸 Скриншот @{a.account}")
                                        # Delete screenshot after sending to save disk space
                                        try:
                                            os.remove(screenshot_path)
                                            print(f"🗑️ Screenshot deleted: {screenshot_path}")
                                        except Exception as del_err:
                                            print(f"Warning: Failed to delete screenshot: {del_err}")
                                    except Exception as e:
                                        print(f"Failed to send photo: {e}")
                            
                            self.send_message(chat_id, 
                                f"🎯 Готово!\n\n📊 Результаты:\n• Найдено: {ok_count}\n• Не найдено: {nf_count}\n• Ошибки: {unk_count}"
                            )

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

            elif text == "Назад в меню":
                keyboard = main_menu(is_admin=ensure_admin(user))
                self.send_message(chat_id, "Главное меню:", keyboard)

            elif text == "Мои прокси":
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                # Import services
                try:
                    from .models import Proxy
                    from .keyboards import proxy_card_kb
                except ImportError:
                    from models import Proxy
                    from keyboards import proxy_card_kb
                
                with session_factory() as session:
                    proxies = session.query(Proxy).filter(Proxy.user_id == user.id).order_by(Proxy.priority.asc()).all()
                    if not proxies:
                        self.send_message(chat_id, "📭 У вас пока нет прокси.", proxies_menu_kb())
                        return
                    for p in proxies:
                        creds = f"{p.username}:{p.password}@" if p.username and p.password else ""
                        proxy_text = (
                            f"🧩 Proxy #{p.id}\n"
                            f"• {p.scheme}://{creds}{p.host}\n"
                            f"• active: {p.is_active} | prio: {p.priority}\n"
                            f"• used: {p.used_count} | success: {p.success_count} | fail_streak: {p.fail_streak}\n"
                            f"• cooldown_until: {p.cooldown_until}\n"
                            f"• last_checked: {p.last_checked}"
                        )
                        self.send_message(chat_id, proxy_text, proxy_card_kb(p.id))

            elif text == "Добавить прокси":
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                # Start FSM for adding proxy
                self.fsm_states[user_id] = {"state": "waiting_for_proxy_url"}
                self.send_message(chat_id, 
                    "Введите прокси в формате:\n"
                    "`scheme://[user:pass@]host:port`\n"
                    "Примеры:\n"
                    "`http://1.2.3.4:8080`\n"
                    "`socks5://user:pass@5.6.7.8:1080`"
                )

            elif text == "Тестировать прокси":
                if not ensure_active(user):
                    self.send_message(chat_id, "⛔ Доступ пока не выдан.")
                    return
                self.send_message(chat_id, "⏳ Тестирую ваши активные прокси...")
                # Import services
                try:
                    from .models import Proxy
                    from .services.proxy_checker import test_proxy_connectivity
                except ImportError:
                    from models import Proxy
                    from services.proxy_checker import test_proxy_connectivity
                
                with session_factory() as session:
                    proxies = session.query(Proxy).filter(Proxy.user_id == user.id, Proxy.is_active == True).all()
                    good, bad = 0, 0
                    for p in proxies:
                        # Test proxy (simplified for now)
                        ok = True  # Placeholder - would need async implementation
                        if ok: 
                            good += 1
                        else: 
                            bad += 1
                    
                    # Import keyboards
                    try:
                        from .keyboards import proxies_menu_kb
                    except ImportError:
                        from keyboards import proxies_menu_kb
                    
                    self.send_message(chat_id, f"Готово. Успешных: {good}, неуспешных: {bad}", proxies_menu_kb())
            
            elif text == "Админка":
                if not ensure_admin(user):
                    self.send_message(chat_id, "⛔ Доступ запрещён. Нужны права администратора.")
                    return
                self.send_message(chat_id, "🛡 Админ-панель (заглушка). Разделы появятся на Этапе 6.")
            
            else:
                # Handle other messages
                if ensure_active(user):
                    self.send_message(chat_id, "Используйте кнопки меню для навигации")
                else:
                    self.send_message(chat_id, "⛔ Доступ пока не выдан. Обратись к администратору.")


def main():
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
    try:
        from .auto_checker_scheduler import AutoCheckerScheduler
        from .services.system_settings import get_auto_check_interval
    except ImportError:
        from auto_checker_scheduler import AutoCheckerScheduler
        from services.system_settings import get_auto_check_interval
    
    # Get current interval from database
    with session_factory() as session:
        interval_minutes = get_auto_check_interval(session)
    
    # Initialize and start scheduler
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
                            bot.process_message(message, session_factory)
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
