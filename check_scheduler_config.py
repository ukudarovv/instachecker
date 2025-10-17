"""Check scheduler configuration."""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("ПРОВЕРКА КОНФИГУРАЦИИ ПЛАНИРОВЩИКОВ")
print("=" * 80)
print()

print("1. Проверка импортов...")
try:
    from project.expiry_scheduler import ExpiryNotificationScheduler
    print("   ✅ ExpiryNotificationScheduler найден")
except Exception as e:
    print(f"   ❌ Ошибка импорта ExpiryNotificationScheduler: {e}")

try:
    from project.auto_checker_scheduler import AutoCheckerScheduler
    print("   ✅ AutoCheckerScheduler найден")
except Exception as e:
    print(f"   ❌ Ошибка импорта AutoCheckerScheduler: {e}")

print()
print("2. Проверка auto_checker.py...")
try:
    with open("project/cron/auto_checker.py", "r", encoding="utf-8") as f:
        content = f.read()
        if "check_and_send_expiry_notifications" in content:
            # Проверяем, что это закомментировано или в NOTE
            if "NOTE: Expiry notifications are now handled by separate daily scheduler" in content:
                print("   ✅ Уведомления отключены в auto_checker.py (есть NOTE)")
            else:
                print("   ⚠️ ВНИМАНИЕ: check_and_send_expiry_notifications найдена в auto_checker.py!")
                print("   Проверьте, что она не вызывается!")
        else:
            print("   ✅ check_and_send_expiry_notifications не найдена в auto_checker.py")
except Exception as e:
    print(f"   ❌ Ошибка чтения файла: {e}")

print()
print("3. Проверка bot.py...")
try:
    with open("project/bot.py", "r", encoding="utf-8") as f:
        content = f.read()
        if "ExpiryNotificationScheduler" in content:
            print("   ✅ ExpiryNotificationScheduler используется в bot.py")
        else:
            print("   ❌ ExpiryNotificationScheduler НЕ найден в bot.py!")
            
        if "_expiry_scheduler" in content:
            print("   ✅ Глобальная переменная _expiry_scheduler найдена")
        else:
            print("   ❌ Глобальная переменная _expiry_scheduler НЕ найдена!")
except Exception as e:
    print(f"   ❌ Ошибка чтения файла: {e}")

print()
print("4. Проверка базы данных...")
try:
    from project.config import get_settings
    from project.database import get_engine
    from sqlalchemy import inspect
    
    settings = get_settings()
    engine = get_engine(settings.db_url)
    inspector = inspect(engine)
    
    if "expiry_notifications" in inspector.get_table_names():
        print("   ✅ Таблица expiry_notifications существует")
    else:
        print("   ❌ Таблица expiry_notifications НЕ найдена!")
        print("   Запустите: python migrate_expiry_notifications.py")
except Exception as e:
    print(f"   ❌ Ошибка проверки БД: {e}")

print()
print("=" * 80)
print("ИТОГОВАЯ КОНФИГУРАЦИЯ")
print("=" * 80)
print()
print("📋 Ожидаемое поведение:")
print("   ✅ Автопроверка аккаунтов - каждые N минут (без уведомлений о сроках)")
print("   ✅ Уведомления о сроках - один раз в день в 10:00")
print()
print("🔧 Если уведомления все еще отправляются при автопроверке:")
print("   1. Перезапустите бота")
print("   2. Проверьте логи на наличие [EXPIRY-CHECK]")
print("   3. Убедитесь, что тесты не запущены")
print()
print("📝 Для просмотра следующего запуска планировщика:")
print("   - Посмотрите логи бота при старте")
print("   - Найдите строку: 'Next expiry notification scheduled at: ...'")

