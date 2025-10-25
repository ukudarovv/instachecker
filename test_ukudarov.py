#!/usr/bin/env python3
"""
Тест проверки аккаунта ukudarov через API v2.
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

async def test_ukudarov():
    """Тест проверки аккаунта ukudarov"""
    
    print("🔍 Проверка аккаунта @ukudarov через API v2...")
    
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
        
        # Показываем доступные прокси
        for i, proxy in enumerate(proxies[:3]):  # Показываем первые 3
            print(f"   📡 Прокси {i+1}: {proxy.host}")
        
        print(f"\n🎯 Проверяем аккаунт @ukudarov...")
        
        try:
            result = await check_account_via_api_v2_proxy(
                session=session,
                user_id=test_user.id,
                username="ukudarov"
            )
            
            print(f"\n📋 Результат для @ukudarov:")
            print(f"   ✅ Существует: {result.get('exists')}")
            print(f"   📛 Имя: {result.get('full_name', 'N/A')}")
            followers = result.get('followers', 0) or 0
            following = result.get('following', 0) or 0
            posts = result.get('posts', 0) or 0
            print(f"   👥 Подписчики: {followers:,}")
            print(f"   👥 Подписки: {following:,}")
            print(f"   📸 Посты: {posts}")
            print(f"   ✅ Верифицирован: {result.get('is_verified', False)}")
            print(f"   🔒 Приватный: {result.get('is_private', False)}")
            print(f"   🔗 Прокси: {result.get('proxy_used', 'N/A')}")
            print(f"   📸 Скриншот: {result.get('screenshot_path', 'N/A')}")
            print(f"   ❗ Ошибка: {result.get('error', 'N/A')}")
            print(f"   🎯 Метод: {result.get('checked_via', 'N/A')}")
            
            # Дополнительная информация
            if result.get('screenshot_path') and os.path.exists(result.get('screenshot_path')):
                file_size = os.path.getsize(result.get('screenshot_path')) / 1024
                print(f"   📏 Размер скриншота: {file_size:.1f} KB")
            
            # Проверяем статус в базе данных
            account = session.query(Account).filter(
                Account.user_id == test_user.id,
                Account.account == "ukudarov"
            ).first()
            
            if account:
                print(f"   📊 Статус в БД: {'Выполнен' if account.done else 'В процессе'}")
                if account.date_of_finish:
                    print(f"   📅 Дата завершения: {account.date_of_finish}")
            else:
                print(f"   📊 Статус в БД: Аккаунт не найден в БД")
                
        except Exception as e:
            print(f"❌ Ошибка при проверке @ukudarov: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n✅ Проверка завершена!")

if __name__ == "__main__":
    asyncio.run(test_ukudarov())
