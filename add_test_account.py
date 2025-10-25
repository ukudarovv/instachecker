#!/usr/bin/env python3
"""
Добавление тестового аккаунта в базу данных.
"""

import sys
import os
from datetime import date

# Добавляем путь к проекту
sys.path.append(os.path.join(os.path.dirname(__file__), 'project'))

from project.models import User, Account
from project.config import get_settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def add_test_account():
    """Добавление тестового аккаунта в базу данных"""
    
    # Настройка базы данных
    settings = get_settings()
    engine = create_engine(settings.db_url)
    SessionLocal = sessionmaker(bind=engine)
    
    with SessionLocal() as session:
        print("➕ Добавление тестового аккаунта в базу данных")
        print("=" * 60)
        
        # Тестовый пользователь
        test_user = session.query(User).filter(User.id == 1).first()
        if not test_user:
            print("❌ Тестовый пользователь не найден")
            return
        
        print(f"👤 Тестовый пользователь: {test_user.id}")
        
        # Добавляем тестовый аккаунт
        username = "ukudarov"
        
        # Проверяем, есть ли уже такой аккаунт
        existing_account = session.query(Account).filter(
            Account.user_id == test_user.id,
            Account.account == username
        ).first()
        
        if existing_account:
            print(f"⚠️ Аккаунт @{username} уже существует в базе данных")
            print(f"   📝 ID: {existing_account.id}")
            print(f"   📝 Выполнен: {existing_account.done}")
            print(f"   📝 Дата завершения: {existing_account.date_of_finish}")
        else:
            # Создаем новый аккаунт
            new_account = Account(
                user_id=test_user.id,
                account=username,
                done=False,
                date_of_finish=None
            )
            
            session.add(new_account)
            session.commit()
            
            print(f"✅ Аккаунт @{username} добавлен в базу данных")
            print(f"   📝 ID: {new_account.id}")
            print(f"   📝 Пользователь: {new_account.user_id}")
            print(f"   📝 Аккаунт: {new_account.account}")
            print(f"   📝 Выполнен: {new_account.done}")
            print(f"   📝 Дата завершения: {new_account.date_of_finish}")
        
        print(f"\n" + "=" * 60)
        print("🎯 Готово!")

if __name__ == "__main__":
    add_test_account()
