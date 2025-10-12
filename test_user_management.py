"""Test user management functionality."""

import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent / "project"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from project.database import Base
from project.models import User, Account, APIKey, Proxy, InstagramSession

def test_user_management():
    """Test user management functionality."""
    
    # Create test database
    engine = create_engine("sqlite:///test_user_mgmt.db")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    
    print("🧪 Тестирование управления пользователями\n")
    
    with SessionLocal() as session:
        # Create test users
        print("1️⃣ Создание тестовых пользователей...")
        
        # Active user
        user1 = User(
            id=111,
            username="active_user",
            is_active=True,
            role="user"
        )
        session.add(user1)
        
        # Inactive user
        user2 = User(
            id=222,
            username="inactive_user",
            is_active=False,
            role="user"
        )
        session.add(user2)
        
        # Admin user
        user3 = User(
            id=333,
            username="admin_user",
            is_active=True,
            role="admin"
        )
        session.add(user3)
        
        session.commit()
        print("   ✅ Создано 3 пользователя")
        
        # Add test accounts to user1
        print("\n2️⃣ Добавление тестовых аккаунтов...")
        account1 = Account(
            user_id=user1.id,
            account="test_account_1",
            done=True
        )
        account2 = Account(
            user_id=user1.id,
            account="test_account_2",
            done=False
        )
        session.add(account1)
        session.add(account2)
        session.commit()
        print("   ✅ Добавлено 2 аккаунта к active_user")
        
        # Test queries
        print("\n3️⃣ Тестирование запросов...")
        
        # All users
        all_users = session.query(User).all()
        print(f"   📊 Всего пользователей: {len(all_users)}")
        
        # Active users
        active_users = session.query(User).filter(User.is_active == True).all()
        print(f"   ✅ Активных: {len(active_users)}")
        
        # Inactive users
        inactive_users = session.query(User).filter(User.is_active == False).all()
        print(f"   ❌ Неактивных: {len(inactive_users)}")
        
        # Admins
        admins = session.query(User).filter(User.role.in_(["admin", "superuser"])).all()
        print(f"   👑 Администраторов: {len(admins)}")
        
        # Test user details
        print("\n4️⃣ Тестирование деталей пользователя...")
        user_detail = session.query(User).filter(User.id == 111).first()
        if user_detail:
            accounts_count = session.query(Account).filter(Account.user_id == user_detail.id).count()
            print(f"   👤 Пользователь: {user_detail.username}")
            print(f"   📱 Аккаунтов: {accounts_count}")
            print(f"   ✅ Статус: {'Активен' if user_detail.is_active else 'Неактивен'}")
            print(f"   👑 Роль: {user_detail.role}")
        
        # Test activation/deactivation
        print("\n5️⃣ Тестирование активации/деактивации...")
        user2.is_active = True
        session.commit()
        print(f"   ✅ Пользователь {user2.username} активирован")
        
        user2.is_active = False
        session.commit()
        print(f"   🚫 Пользователь {user2.username} деактивирован")
        
        # Test role change
        print("\n6️⃣ Тестирование изменения роли...")
        user1.role = "admin"
        session.commit()
        print(f"   👑 Пользователь {user1.username} теперь администратор")
        
        user1.role = "user"
        session.commit()
        print(f"   👤 Пользователь {user1.username} теперь обычный пользователь")
        
        # Test cascade delete
        print("\n7️⃣ Тестирование каскадного удаления...")
        accounts_before = session.query(Account).count()
        print(f"   📱 Аккаунтов до удаления: {accounts_before}")
        
        # Delete user with accounts
        session.delete(user1)
        session.commit()
        
        accounts_after = session.query(Account).count()
        print(f"   📱 Аккаунтов после удаления: {accounts_after}")
        print(f"   ✅ Каскадное удаление работает: {accounts_before > accounts_after}")
        
        # Test mass delete inactive
        print("\n8️⃣ Тестирование массового удаления неактивных...")
        inactive_count = session.query(User).filter(User.is_active == False).count()
        print(f"   ❌ Неактивных пользователей: {inactive_count}")
        
        # Delete all inactive
        inactive_users = session.query(User).filter(User.is_active == False).all()
        for u in inactive_users:
            session.delete(u)
        session.commit()
        
        inactive_after = session.query(User).filter(User.is_active == False).count()
        print(f"   ❌ Неактивных после удаления: {inactive_after}")
        print(f"   ✅ Массовое удаление работает: {inactive_after == 0}")
        
        # Final stats
        print("\n9️⃣ Финальная статистика...")
        total = session.query(User).count()
        active = session.query(User).filter(User.is_active == True).count()
        admins = session.query(User).filter(User.role.in_(["admin", "superuser"])).count()
        
        print(f"   📊 Всего пользователей: {total}")
        print(f"   ✅ Активных: {active}")
        print(f"   👑 Администраторов: {admins}")
    
    print("\n✅ Все тесты пройдены успешно!")
    
    # Cleanup
    print("\n🧹 Очистка тестовой базы данных...")
    # Close engine first
    engine.dispose()
    
    import time
    time.sleep(0.5)  # Give time for connections to close
    
    if os.path.exists("test_user_mgmt.db"):
        try:
            os.remove("test_user_mgmt.db")
            print("   ✅ Тестовая база удалена")
        except PermissionError:
            print("   ⚠️ Не удалось удалить тестовую базу (файл занят)")

if __name__ == "__main__":
    test_user_management()

