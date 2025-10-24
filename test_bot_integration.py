#!/usr/bin/env python3
"""
Тест интеграции header скриншота с темной темой в основную проверку бота
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from project.database import get_engine, get_session_factory, init_db
from project.services.main_checker import check_account_main
from project.models import User, Proxy


async def test_integration():
    """Тестируем интеграцию новой функции в основную проверку бота"""
    
    print("=" * 80)
    print("🧪 ТЕСТ ИНТЕГРАЦИИ: Header скриншот с темной темой в боте")
    print("=" * 80)
    print()
    
    # Инициализация БД
    db_url = "sqlite:///bot.db"
    engine = get_engine(db_url)
    init_db(engine)
    session_factory = get_session_factory(engine)
    
    with session_factory() as session:
        # Получаем первого пользователя
        user = session.query(User).first()
        if not user:
            print("❌ Нет пользователей в БД!")
            return
        
        print(f"👤 Пользователь: {user.id}")
        
        # Проверяем наличие прокси
        proxy = session.query(Proxy).filter(
            Proxy.user_id == user.id,
            Proxy.is_active == True
        ).first()
        
        if not proxy:
            print("❌ Нет активных прокси у пользователя!")
            return
        
        print(f"🌐 Прокси: {proxy.scheme}://{proxy.host}")
        print()
        
        # Тестовый аккаунт
        test_username = "instagram"
        
        print(f"🔍 Запускаем проверку аккаунта: @{test_username}")
        print()
        
        try:
            # Вызываем основную функцию проверки
            success, message, screenshot_path = await check_account_main(
                username=test_username,
                session=session,
                user_id=user.id
            )
            
            print()
            print("=" * 80)
            print("📊 РЕЗУЛЬТАТЫ")
            print("=" * 80)
            print(f"✅ Успех: {success}")
            print(f"📝 Сообщение: {message}")
            print(f"📸 Скриншот: {screenshot_path}")
            
            if screenshot_path and os.path.exists(screenshot_path):
                size = os.path.getsize(screenshot_path) / 1024
                print(f"📏 Размер файла: {size:.1f} KB")
                print()
                print(f"🎯 УСПЕХ! Скриншот создан: {screenshot_path}")
                print()
                print("👉 Откройте файл и проверьте:")
                print("   • Темная тема (черный фон) ✓")
                print("   • Белый текст ✓")
                print("   • Скриншот только header'а ✓")
                print("   • Статистика видна (публикации, подписчики) ✓")
            else:
                print("⚠️ Скриншот не был создан")
            
            print()
            print("=" * 80)
            
        except Exception as e:
            print()
            print(f"❌ ОШИБКА: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_integration())

