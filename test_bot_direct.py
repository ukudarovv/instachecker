#!/usr/bin/env python3
"""
Прямой тест header скриншота с темной темой (без API проверки)
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from project.database import get_engine, get_session_factory, init_db
from project.services.main_checker import check_account_with_header_dark_theme
from project.models import User, Proxy


async def test_direct():
    """Прямой тест без API проверки"""
    
    print("=" * 80)
    print("🧪 ПРЯМОЙ ТЕСТ: Header скриншот с темной темой")
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
        
        print(f"🔍 Запускаем ПРЯМУЮ проверку: @{test_username}")
        print(f"   (БЕЗ API проверки - только Proxy + Screenshot)")
        print()
        
        try:
            # Вызываем функцию напрямую
            success, message, screenshot_path = await check_account_with_header_dark_theme(
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
                from PIL import Image
                
                size = os.path.getsize(screenshot_path) / 1024
                img = Image.open(screenshot_path)
                width, height = img.size
                
                print(f"📏 Размер файла: {size:.1f} KB")
                print(f"🖼️  Разрешение: {width}x{height} px")
                print()
                print(f"🎯 УСПЕХ! Header скриншот создан с темной темой!")
                print()
                print(f"👉 Откройте файл: {screenshot_path}")
                print()
                print("✅ Проверьте:")
                print("   • Темная тема (черный фон)")
                print("   • Белый текст")
                print("   • Только header профиля")
                print("   • Статистика видна")
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
    asyncio.run(test_direct())

