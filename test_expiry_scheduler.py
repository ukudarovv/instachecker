"""Test expiry notification scheduler."""

import sys
import os
import asyncio
from datetime import time

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from project.config import get_settings
from project.database import get_session_factory, get_engine
from project.expiry_scheduler import ExpiryNotificationScheduler


async def main():
    """Test expiry scheduler."""
    print("=" * 80)
    print("ТЕСТ ПЛАНИРОВЩИКА УВЕДОМЛЕНИЙ О СРОКАХ")
    print("=" * 80)
    print()
    
    settings = get_settings()
    engine = get_engine(settings.db_url)
    SessionLocal = get_session_factory(engine)
    
    print("1. Создание планировщика...")
    scheduler = ExpiryNotificationScheduler(
        bot_token=settings.bot_token,
        SessionLocal=SessionLocal,
        notification_time=time(10, 0)  # 10:00 AM
    )
    
    print("2. Запуск планировщика...")
    scheduler.start()
    
    print("3. Проверка статуса...")
    print(f"   Запущен: {scheduler.is_running()}")
    
    next_run = scheduler.get_next_run_time()
    if next_run:
        print(f"   Следующий запуск: {next_run}")
        print(f"   Это будет в: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print()
    print("4. Ручной запуск проверки для тестирования...")
    print("   (обычно запускается автоматически в 10:00)")
    print()
    
    # Manually trigger notification check for testing
    from project.services.expiry_notifications import check_and_send_expiry_notifications
    from project.utils.async_bot_wrapper import AsyncBotWrapper
    
    async_bot = AsyncBotWrapper(settings.bot_token)
    
    try:
        await check_and_send_expiry_notifications(SessionLocal, async_bot)
        print()
        print("✅ Тест успешно выполнен!")
    except Exception as e:
        print(f"❌ Ошибка при тесте: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("5. Остановка планировщика...")
    scheduler.stop()
    print("   Планировщик остановлен")
    
    print()
    print("=" * 80)
    print("ТЕСТ ЗАВЕРШЕН")
    print("=" * 80)
    print()
    print("📝 Примечания:")
    print("   - Планировщик запускается автоматически при старте бота")
    print("   - Уведомления отправляются ежедневно в 10:00")
    print("   - Каждое уведомление отправляется только один раз в день")
    print("   - История отправок хранится в таблице expiry_notifications")


if __name__ == "__main__":
    asyncio.run(main())

