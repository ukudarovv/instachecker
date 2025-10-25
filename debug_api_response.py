#!/usr/bin/env python3
"""
Отладка API ответов для выявления проблемы.
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.join(os.path.dirname(__file__), 'project'))

from project.services.check_via_api import check_account_exists_via_api
from project.models import User, Account
from project.config import get_settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

async def debug_api_response():
    """Отладка API ответов"""
    
    # Настройка базы данных
    settings = get_settings()
    engine = create_engine(settings.db_url)
    SessionLocal = sessionmaker(bind=engine)
    
    with SessionLocal() as session:
        print("🔍 Отладка API ответов")
        print("=" * 60)
        
        # Тестовый пользователь
        test_user = session.query(User).filter(User.id == 1).first()
        if not test_user:
            print("❌ Тестовый пользователь не найден")
            return
        
        print(f"👤 Тестовый пользователь: {test_user.id}")
        
        # Тестовые аккаунты
        test_accounts = [
            "ukudarov",  # Существующий
            "nonexistent123456789",  # Несуществующий
            "invalid_user_12345",  # Несуществующий
        ]
        
        for username in test_accounts:
            print(f"\n📊 Тест API для @{username}")
            print("-" * 40)
            
            try:
                result = await check_account_exists_via_api(
                    session=session,
                    user_id=test_user.id,
                    username=username
                )
                
                print(f"📋 Результат API:")
                print(f"   ✅ Существует: {result.get('exists')}")
                print(f"   ❗ Ошибка: {result.get('error', 'N/A')}")
                
                # Анализ проблемы
                if result.get('exists') is True and username in ["nonexistent123456789", "invalid_user_12345"]:
                    print("   🚨 ПРОБЛЕМА: API нашел несуществующий аккаунт!")
                    print("   🔍 Нужно проверить логику сравнения username в API")
                elif result.get('exists') is False and username == "ukudarov":
                    print("   🚨 ПРОБЛЕМА: API не нашел существующий аккаунт!")
                
            except Exception as e:
                print(f"   ❌ Критическая ошибка: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n" + "=" * 60)
        print("🎯 Отладка завершена!")
        print("📝 Проверьте логи выше на наличие проблем с API")

if __name__ == "__main__":
    asyncio.run(debug_api_response())
