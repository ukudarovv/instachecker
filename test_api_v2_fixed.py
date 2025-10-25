#!/usr/bin/env python3
"""
Тест исправленного режима api-v2.
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.join(os.path.dirname(__file__), 'project'))

from project.services.api_v2_proxy_checker import check_account_via_api_v2_proxy
from project.models import User, Account
from project.config import get_settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

async def test_api_v2_fixed():
    """Тест исправленного режима api-v2"""
    
    # Настройка базы данных
    settings = get_settings()
    engine = create_engine(settings.db_url)
    SessionLocal = sessionmaker(bind=engine)
    
    with SessionLocal() as session:
        print("🔧 Тест исправленного режима api-v2")
        print("=" * 60)
        
        # Тестовый пользователь
        test_user = session.query(User).filter(User.id == 1).first()
        if not test_user:
            print("❌ Тестовый пользователь не найден")
            return
        
        print(f"👤 Тестовый пользователь: {test_user.id}")
        
        # Тестируем только существующий аккаунт
        username = "ukudarov"
        print(f"\n📊 Тестирование @{username}...")
        
        try:
            result = await check_account_via_api_v2_proxy(
                session=session,
                user_id=test_user.id,
                username=username
            )
            
            print(f"📋 Результат:")
            print(f"   ✅ Существует: {result.get('exists')}")
            print(f"   📛 Имя: {result.get('full_name', 'N/A')}")
            print(f"   👥 Подписчики: {result.get('followers', 'N/A')}")
            print(f"   👥 Подписки: {result.get('following', 'N/A')}")
            print(f"   📸 Посты: {result.get('posts', 'N/A')}")
            print(f"   🔗 Прокси: {result.get('proxy_used', 'N/A')}")
            print(f"   📸 Скриншот: {result.get('screenshot_path', 'N/A')}")
            print(f"   ❗ Ошибка: {result.get('error', 'N/A')}")
            print(f"   🔍 Метод: {result.get('checked_via', 'N/A')}")
            
            # Проверяем, что аккаунт помечен как выполненный
            account = session.query(Account).filter(
                Account.user_id == test_user.id,
                Account.account == username
            ).first()
            
            if account and account.done:
                print(f"   ✅ Аккаунт помечен как выполненный: {account.done}")
                print(f"   📅 Дата завершения: {account.date_of_finish}")
            else:
                print(f"   ❌ Аккаунт НЕ помечен как выполненный")
            
            # Проверяем скриншот
            if result.get('screenshot_path') and os.path.exists(result['screenshot_path']):
                file_size = os.path.getsize(result['screenshot_path'])
                print(f"   📸 Скриншот создан: {result['screenshot_path']} ({file_size} bytes)")
            else:
                print(f"   ❌ Скриншот не создан")
                
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n" + "=" * 60)
        print("🎯 Тест завершен!")

if __name__ == "__main__":
    asyncio.run(test_api_v2_fixed())
