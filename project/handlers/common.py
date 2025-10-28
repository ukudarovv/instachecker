"""Common message handlers."""

try:
    from aiogram import types
    from aiogram.dispatcher import FSMContext
except ImportError:
    # Fallback for direct API usage
    types = None
    FSMContext = None

from sqlalchemy.orm import Session

try:
    from ..database import get_session_factory, get_engine
    from ..models import User
    from ..keyboards import main_menu
    from ..utils.access import get_or_create_user, ensure_active, ensure_admin
    from ..config import get_settings
except ImportError:
    from database import get_session_factory, get_engine
    from models import User
    from keyboards import main_menu
    from utils.access import get_or_create_user, ensure_active, ensure_admin
    from config import get_settings


def register_common_handlers(dp, SessionLocal):
    """Register all common handlers."""
    
    @dp.message_handler(commands=["start"])
    async def cmd_start(message):
        """Handle /start command."""
        with SessionLocal() as session:
            try:
                from ..services.system_settings import get_global_verify_mode
            except ImportError:
                from services.system_settings import get_global_verify_mode
            
            user = get_or_create_user(session, message.from_user)
            if not ensure_active(user):
                await message.answer(
                    "👋 Привет! Твоя учётная запись создана.\n"
                    "Попроси администратора выдать доступ, после чего станет доступно меню."
                )
                return
            verify_mode = get_global_verify_mode(session)
            await message.answer(
                "Главное меню:",
                reply_markup=main_menu(is_admin=ensure_admin(user), verify_mode=verify_mode)
            )

    @dp.message_handler(lambda m: m.text and m.text.lower() in {"меню", "menu"})
    async def show_menu(message):
        """Handle Menu button."""
        with SessionLocal() as session:
            try:
                from ..services.system_settings import get_global_verify_mode
            except ImportError:
                from services.system_settings import get_global_verify_mode
            
            user = get_or_create_user(session, message.from_user)
            if not ensure_active(user):
                await message.answer("⛔ Доступ пока не выдан. Обратись к администратору.")
                return
            verify_mode = get_global_verify_mode(session)
            await message.answer(
                "Главное меню:",
                reply_markup=main_menu(is_admin=ensure_admin(user), verify_mode=verify_mode)
            )

    # Заглушки для пунктов меню (пока только верификация доступа)
    @dp.message_handler(lambda m: m.text == "Добавить аккаунт")
    async def add_account_entry(message):
        with SessionLocal() as session:
            user = get_or_create_user(session, message.from_user)
            if not ensure_active(user):
                await message.answer("⛔ Доступ пока не выдан.")
                return
            await message.answer("➕ Добавление аккаунта — скоро здесь будет мастер (Этап 2).")

    @dp.message_handler(lambda m: m.text == "Активные аккаунты")
    async def active_accounts(message):
        with SessionLocal() as session:
            user = get_or_create_user(session, message.from_user)
            if not ensure_active(user):
                await message.answer("⛔ Доступ пока не выдан.")
                return
            await message.answer("📋 Список активных аккаунтов — появится на Этапе 3.")

    @dp.message_handler(lambda m: m.text == "Аккаунты на проверке")
    async def pending_accounts(message):
        with SessionLocal() as session:
            user = get_or_create_user(session, message.from_user)
            if not ensure_active(user):
                await message.answer("⛔ Доступ пока не выдан.")
                return
            await message.answer("🕒 Список аккаунтов на проверке — Этап 3.")

    @dp.message_handler(lambda m: m.text == "Проверить аккаунты")
    async def check_accounts(message):
        with SessionLocal() as session:
            user = get_or_create_user(session, message.from_user)
            if not ensure_active(user):
                await message.answer("⛔ Доступ пока не выдан.")
                return
            await message.answer("🔍 Проверка аккаунтов — будет реализована на Этапе 4.")
    
    @dp.message_handler(commands=["traffic_stats"])
    async def traffic_stats(message):
        """Показать статистику трафика."""
        try:
            from ..services.traffic_monitor import get_traffic_monitor
        except ImportError:
            from services.traffic_monitor import get_traffic_monitor
        
        monitor = get_traffic_monitor()
        total_stats = monitor.get_total_stats()
        
        if total_stats['total_requests'] == 0:
            await message.answer("📊 Статистика трафика пуста. Запросы через прокси еще не выполнялись.")
            return
        
        # Форматируем статистику
        stats_text = f"""📊 **СТАТИСТИКА ТРАФИКА**

📊 **Общий трафик:** {monitor._format_bytes(total_stats['total_traffic'])}
🔢 **Всего запросов:** {total_stats['total_requests']}
✅ **Успешных:** {total_stats['successful_requests']}
❌ **Неудачных:** {total_stats['failed_requests']}
📈 **Успешность:** {total_stats['success_rate']}%
📊 **Средний трафик на запрос:** {monitor._format_bytes(total_stats['average_traffic_per_request'])}
🌐 **Прокси использовано:** {total_stats['proxies_used']}

📊 **ПО ПРОКСИ:**"""
        
        # Добавляем статистику по каждому прокси
        for proxy_ip, proxy_stats in monitor.proxy_traffic.items():
            proxy_stats_detailed = monitor.get_proxy_stats(proxy_ip)
            stats_text += f"""
🌐 **{proxy_ip}:**
  📊 Трафик: {monitor._format_bytes(proxy_stats['total_traffic'])}
  🔢 Запросов: {proxy_stats['total_requests']}
  ✅ Успешность: {proxy_stats_detailed['success_rate']}%"""
        
        await message.answer(stats_text, parse_mode="Markdown")

    @dp.message_handler(lambda m: m.text == "API")
    async def api_menu(message):
        with SessionLocal() as session:
            user = get_or_create_user(session, message.from_user)
            if not ensure_active(user):
                await message.answer("⛔ Доступ пока не выдан.")
                return
            await message.answer("🔑 Управление API-ключами — Этап 5.")


# Legacy function for backward compatibility
def register_handlers(dp):
    """Legacy function for backward compatibility."""
    settings = get_settings()
    engine = get_engine(settings.db_url)
    session_factory = get_session_factory(engine)
    register_common_handlers(dp, session_factory)
