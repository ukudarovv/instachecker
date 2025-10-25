#!/usr/bin/env python3
"""
Проверка аккаунта в базе данных.
"""

import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.join(os.path.dirname(__file__), 'project'))

from project.models import User, Account
from project.config import get_settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def check_account_in_db():
    """Проверка аккаунта в базе данных"""
    
    # Настройка базы данных
    settings = get_settings()
    engine = create_engine(settings.db_url)
    SessionLocal = sessionmaker(bind=engine)
    
    with SessionLocal() as session:
        print("🔍 Проверка аккаунта в базе данных")
        print("=" * 60)
        
        # Тестовый пользователь
        test_user = session.query(User).filter(User.id == 1).first()
        if not test_user:
            print("❌ Тестовый пользователь не найден")
            return
        
        print(f"👤 Тестовый пользователь: {test_user.id}")
        
        # Проверяем все аккаунты пользователя
        accounts = session.query(Account).filter(Account.user_id == test_user.id).all()
        print(f"📊 Всего аккаунтов у пользователя: {len(accounts)}")
        
        for account in accounts:
            print(f"   📝 @{account.account} - done: {account.done}, date: {account.date_of_finish}")
        
        # Проверяем конкретный аккаунт
        username = "ukudarov"
        account = session.query(Account).filter(
            Account.user_id == test_user.id,
            Account.account == username
        ).first()
        
        if account:
            print(f"\n✅ Аккаунт @{username} найден в базе:")
            print(f"   📝 ID: {account.id}")
            print(f"   📝 Пользователь: {account.user_id}")
            print(f"   📝 Аккаунт: {account.account}")
            print(f"   📝 Выполнен: {account.done}")
            print(f"   📝 Дата завершения: {account.date_of_finish}")
        else:
            print(f"\n❌ Аккаунт @{username} НЕ найден в базе данных!")
            print("💡 Нужно добавить аккаунт в базу данных перед проверкой")

if __name__ == "__main__":
    check_account_in_db()
