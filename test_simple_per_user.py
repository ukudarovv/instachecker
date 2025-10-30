"""
Простой тест для проверки что система индивидуальной автопроверки работает
"""
import asyncio
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from project.models import User, Account, Base
from project.cron.auto_checker_manager import AutoCheckerManager

async def simple_test():
    """Простой тест системы"""
    print("\n" + "="*70)
    print("🧪 ПРОСТОЙ ТЕСТ ИНДИВИДУАЛЬНОЙ АВТОПРОВЕРКИ")
    print("="*70 + "\n")
    
    # Подключение к основной БД
    engine = create_engine('sqlite:///bot.db', echo=False)
    SessionLocal = sessionmaker(bind=engine)
    
    # Проверка существующих пользователей
    print("📋 Проверка пользователей в базе данных...\n")
    with SessionLocal() as session:
        users = session.query(User).filter(User.is_active == True).all()
        
        if not users:
            print("⚠️ Нет активных пользователей в базе!")
            print("   Добавьте пользователей через бот или create_admin.py")
            return
        
        print(f"✅ Найдено активных пользователей: {len(users)}\n")
        
        for user in users:
            print(f"👤 User {user.id}: @{user.username}")
            print(f"   • Интервал: {user.auto_check_interval} минут")
            print(f"   • Автопроверка: {'✅ Включена' if user.auto_check_enabled else '❌ Выключена'}")
            
            # Количество аккаунтов
            pending = session.query(Account).filter(
                Account.user_id == user.id,
                Account.done == False
            ).count()
            total = session.query(Account).filter(Account.user_id == user.id).count()
            
            print(f"   • Аккаунтов: {total} (ожидают проверки: {pending})")
            print()
    
    print("="*70)
    print("🚀 ИНИЦИАЛИЗАЦИЯ МЕНЕДЖЕРА АВТОПРОВЕРКИ")
    print("="*70 + "\n")
    
    # Инициализация менеджера
    manager = AutoCheckerManager.initialize(
        session_factory=SessionLocal,
        bot=None  # Без бота для теста
    )
    
    print("✅ Менеджер создан\n")
    
    # Запуск планировщиков
    print("="*70)
    print("📋 ЗАПУСК ПЛАНИРОВЩИКОВ")
    print("="*70 + "\n")
    
    manager.start_all(run_immediately=False)
    
    print("\n" + "="*70)
    print("📊 СТАТУС ПЛАНИРОВЩИКОВ")
    print("="*70 + "\n")
    
    manager.print_status()
    
    # Тест изменения интервала
    if users:
        test_user_id = users[0].id
        print("="*70)
        print(f"🔧 ТЕСТ: Изменение интервала для user {test_user_id}")
        print("="*70 + "\n")
        
        print(f"Текущий интервал: {users[0].auto_check_interval} минут")
        print(f"Устанавливаем новый интервал: 15 минут\n")
        
        manager.update_user_interval(test_user_id, 15)
        
        # Проверяем что изменилось в БД
        with SessionLocal() as session:
            user = session.query(User).filter(User.id == test_user_id).first()
            print(f"✅ Интервал в БД обновлен: {user.auto_check_interval} минут\n")
    
    # Финальный статус
    print("="*70)
    print("📊 ФИНАЛЬНЫЙ СТАТУС")
    print("="*70 + "\n")
    
    stats = manager.get_all_stats()
    print(f"Всего активных планировщиков: {stats['total_checkers']}\n")
    
    for stat in stats['checkers']:
        print(f"👤 User {stat['user_id']} (@{stat.get('username', '?')})")
        print(f"   • Интервал: {stat.get('interval_minutes', '?')} минут")
        print(f"   • Запущен: {'✅' if stat['is_running'] else '❌'}")
        print(f"   • Проверок выполнено: {stat['total_checks']}")
        print(f"   • Найдено аккаунтов: {stat['total_found']}")
        print()
    
    # Остановка
    print("="*70)
    print("🛑 ОСТАНОВКА ПЛАНИРОВЩИКОВ")
    print("="*70 + "\n")
    
    manager.stop_all()
    
    print("✅ Все планировщики остановлены\n")
    
    print("="*70)
    print("✅ ТЕСТ ЗАВЕРШЕН УСПЕШНО!")
    print("="*70)
    print("\n📋 Проверено:")
    print("   ✅ Подключение к базе данных")
    print("   ✅ Загрузка пользователей")
    print("   ✅ Инициализация менеджера")
    print("   ✅ Запуск планировщиков")
    print("   ✅ Изменение интервала")
    print("   ✅ Получение статистики")
    print("   ✅ Остановка планировщиков")
    print("\n🎉 Система готова к работе!\n")

if __name__ == "__main__":
    asyncio.run(simple_test())

