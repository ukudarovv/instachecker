#!/usr/bin/env python3
"""
Тест нового метода проверки API v2 с прокси.
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.join(os.path.dirname(__file__), 'project'))

from project.services.api_v2_proxy_checker import check_account_via_api_v2_proxy
from project.models import Proxy, User, Account
from project.config import get_settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date

async def test_api_v2():
    """Тест нового метода проверки API v2"""
    
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
        
        # Проверяем наличие прокси
        proxies = session.query(Proxy).filter(
            Proxy.user_id == test_user.id,
            Proxy.is_active == True
        ).all()
        
        if not proxies:
            print("❌ Нет доступных прокси для тестирования")
            return
        
        print(f"✅ Найдено {len(proxies)} прокси для тестирования")
        
        # Тестовые аккаунты
        test_accounts = [
            "instagram",  # Существующий
            "zuck",       # Существующий
            "nonexistent123456789",  # Не существующий
        ]
        
        print(f"\n🔍 Тестирование API v2 для {len(test_accounts)} аккаунтов...")
        
        for username in test_accounts:
            print(f"\n📊 Тестирование @{username}...")
            
            try:
                result = await check_account_via_api_v2_proxy(
                    session=session,
                    user_id=test_user.id,
                    username=username
                )
                
                print(f"📋 Результат для @{username}:")
                print(f"   ✅ Существует: {result.get('exists')}")
                print(f"   📛 Имя: {result.get('full_name', 'N/A')}")
                print(f"   👥 Подписчики: {result.get('followers', 0):,}")
                print(f"   📸 Посты: {result.get('posts', 0)}")
                print(f"   🔗 Прокси: {result.get('proxy_used', 'N/A')}")
                print(f"   📸 Скриншот: {result.get('screenshot_path', 'N/A')}")
                print(f"   ❗ Ошибка: {result.get('error', 'N/A')}")
                print(f"   🎯 Метод: {result.get('checked_via', 'N/A')}")
                
            except Exception as e:
                print(f"❌ Ошибка при тестировании @{username}: {e}")
        
        print(f"\n✅ Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(test_api_v2())
