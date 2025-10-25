#!/usr/bin/env python3
"""
Анализ логов режима api-v2 для выявления проблем.
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

async def analyze_api_v2_logs():
    """Анализ логов режима api-v2"""
    
    # Настройка базы данных
    settings = get_settings()
    engine = create_engine(settings.db_url)
    SessionLocal = sessionmaker(bind=engine)
    
    with SessionLocal() as session:
        print("🔍 Анализ логов режима api-v2")
        print("=" * 60)
        
        # Тестовый пользователь
        test_user = session.query(User).filter(User.id == 1).first()
        if not test_user:
            print("❌ Тестовый пользователь не найден")
            return
        
        print(f"👤 Тестовый пользователь: {test_user.id}")
        
        # Тестовые аккаунты с разными статусами
        test_cases = [
            ("ukudarov", "Существующий аккаунт"),
            ("instagram", "Официальный аккаунт Instagram"),
            ("nonexistent123456789", "Несуществующий аккаунт"),
            ("zuck", "Существующий аккаунт (Mark Zuckerberg)"),
            ("invalid_user_12345", "Несуществующий аккаунт")
        ]
        
        for username, description in test_cases:
            print(f"\n📊 Тест: @{username} ({description})")
            print("-" * 40)
            
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
                print(f"   ✅ Верифицирован: {result.get('is_verified', 'N/A')}")
                print(f"   🔒 Приватный: {result.get('is_private', 'N/A')}")
                print(f"   🔗 Прокси: {result.get('proxy_used', 'N/A')}")
                print(f"   📸 Скриншот: {result.get('screenshot_path', 'N/A')}")
                print(f"   ❗ Ошибка: {result.get('error', 'N/A')}")
                print(f"   🔍 Метод: {result.get('checked_via', 'N/A')}")
                
                # Анализ проблем
                if result.get('exists') is True and username in ["nonexistent123456789", "invalid_user_12345"]:
                    print("   ⚠️ ПРОБЛЕМА: API нашел несуществующий аккаунт!")
                elif result.get('exists') is False and username in ["ukudarov", "instagram", "zuck"]:
                    print("   ⚠️ ПРОБЛЕМА: API не нашел существующий аккаунт!")
                
                if result.get('error') and '403' in str(result.get('error')):
                    print("   ⚠️ ПРОБЛЕМА: 403 Forbidden - прокси заблокирован!")
                elif result.get('error') and 'screenshot' in str(result.get('error')):
                    print("   ⚠️ ПРОБЛЕМА: Ошибка создания скриншота!")
                
            except Exception as e:
                print(f"   ❌ Критическая ошибка: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n" + "=" * 60)
        print("🎯 Анализ завершен!")
        print("📝 Проверьте логи выше на наличие проблем:")
        print("   - API находит несуществующие аккаунты")
        print("   - 403 Forbidden ошибки")
        print("   - Проблемы со скриншотами")

if __name__ == "__main__":
    asyncio.run(analyze_api_v2_logs())
