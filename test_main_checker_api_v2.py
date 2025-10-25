#!/usr/bin/env python3
"""
Тест main_checker с режимом api-v2.
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.join(os.path.dirname(__file__), 'project'))

from project.services.main_checker import check_account_main
from project.models import User, Account
from project.config import get_settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

async def test_main_checker_api_v2():
    """Тест main_checker с режимом api-v2"""
    
    # Настройка базы данных
    settings = get_settings()
    engine = create_engine(settings.db_url)
    SessionLocal = sessionmaker(bind=engine)
    
    with SessionLocal() as session:
        # Создаем тестового пользователя
        test_user = session.query(User).filter(User.id == 1).first()
        if not test_user:
            print("❌ Тестовый пользователь не найден")
            return
        
        print(f"✅ Тестовый пользователь: {test_user.id}")
        
        # Тестовые аккаунты
        test_accounts = [
            "ukudarov",  # Существующий
            "instagram",  # Существующий
            "nonexistent123456789",  # Не существующий
        ]
        
        print(f"\n🔍 Тестирование main_checker с режимом api-v2...")
        
        for username in test_accounts:
            print(f"\n📊 Тестирование @{username}...")
            
            try:
                success, message, screenshot_path = await check_account_main(
                    username=username,
                    session=session,
                    user_id=test_user.id
                )
                
                print(f"📋 Результат для @{username}:")
                print(f"   ✅ Успех: {success}")
                print(f"   📝 Сообщение: {message}")
                print(f"   📸 Скриншот: {screenshot_path or 'N/A'}")
                
            except Exception as e:
                print(f"❌ Ошибка при тестировании @{username}: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n✅ Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(test_main_checker_api_v2())
