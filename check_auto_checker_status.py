#!/usr/bin/env python3
"""Проверка статуса автопроверки и данных в БД."""

import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from project.database import get_engine, get_session_factory
from project.models import User, Account

def check_status():
    """Проверка статуса автопроверки."""
    print("=" * 80)
    print("🔍 ДИАГНОСТИКА АВТОПРОВЕРКИ")
    print("=" * 80)
    
    # Загружаем переменные окружения
    load_dotenv()
    
    # Создаем сессию
    db_url = os.getenv("DB_URL", "sqlite:///bot.db")
    engine = get_engine(db_url)
    session_factory = get_session_factory(engine)
    
    with session_factory() as session:
        # 1. Проверка пользователей
        print("\n1️⃣ ПОЛЬЗОВАТЕЛИ:")
        all_users = session.query(User).all()
        print(f"   Всего пользователей: {len(all_users)}")
        
        active_users = session.query(User).filter(User.is_active == True).all()
        print(f"   Активных пользователей: {len(active_users)}")
        
        auto_check_enabled_users = session.query(User).filter(
            User.is_active == True,
            User.auto_check_enabled == True
        ).all()
        print(f"   С включенной автопроверкой: {len(auto_check_enabled_users)}")
        
        if auto_check_enabled_users:
            print("\n   Детали пользователей с автопроверкой:")
            for user in auto_check_enabled_users:
                accounts_count = session.query(Account).filter(
                    Account.user_id == user.id
                ).count()
                pending_count = session.query(Account).filter(
                    Account.user_id == user.id,
                    Account.done == False
                ).count()
                print(f"   • User {user.id} (@{user.username or 'N/A'}):")
                print(f"     - Активен: {user.is_active}")
                print(f"     - Автопроверка включена: {user.auto_check_enabled}")
                print(f"     - Интервал: {user.auto_check_interval} минут")
                print(f"     - Всего аккаунтов: {accounts_count}")
                print(f"     - Аккаунтов на проверке: {pending_count}")
        
        # 2. Проверка аккаунтов
        print("\n2️⃣ АККАУНТЫ:")
        all_accounts = session.query(Account).all()
        print(f"   Всего аккаунтов: {len(all_accounts)}")
        
        done_accounts = session.query(Account).filter(Account.done == True).all()
        print(f"   Выполненных (done=True): {len(done_accounts)}")
        
        pending_accounts = session.query(Account).filter(Account.done == False).all()
        print(f"   На проверке (done=False): {len(pending_accounts)}")
        
        if pending_accounts:
            print("\n   Аккаунты на проверке:")
            for acc in pending_accounts[:10]:  # Показываем первые 10
                user = session.query(User).filter(User.id == acc.user_id).first()
                print(f"   • @{acc.account} (user_id: {acc.user_id}, username: {user.username if user else 'N/A'})")
            if len(pending_accounts) > 10:
                print(f"   ... и еще {len(pending_accounts) - 10} аккаунтов")
        
        # 3. Рекомендации
        print("\n3️⃣ РЕКОМЕНДАЦИИ:")
        if not auto_check_enabled_users:
            print("   ⚠️ Нет активных пользователей с включенной автопроверкой!")
            print("   💡 Включите автопроверку для пользователей или активируйте их")
        
        if not pending_accounts:
            print("   ⚠️ Нет аккаунтов для проверки (все уже помечены как done=True)")
            print("   💡 Добавьте новые аккаунты через бота или измените done=False для существующих")
        
        if auto_check_enabled_users and pending_accounts:
            print("   ✅ Есть пользователи с автопроверкой и аккаунты для проверки")
            print("   🔍 Проверьте логи бота - там должны быть сообщения [USER-AUTO-CHECK]")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    check_status()

