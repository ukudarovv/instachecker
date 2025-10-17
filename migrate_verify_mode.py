"""Update verify_mode values to new format."""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from project.config import get_settings
from project.database import get_engine, get_session_factory
from project.models import User

def main():
    """Run migration."""
    print("=" * 80)
    print("МИГРАЦИЯ: Обновление значений verify_mode")
    print("=" * 80)
    print()
    
    settings = get_settings()
    engine = get_engine(settings.db_url)
    SessionLocal = get_session_factory(engine)
    
    with SessionLocal() as session:
        # Get all users
        users = session.query(User).all()
        
        print(f"Найдено пользователей: {len(users)}")
        print()
        
        updated = 0
        for user in users:
            old_mode = user.verify_mode
            
            # Update old values to new format
            if old_mode == "api":
                user.verify_mode = "api+instagram"
                updated += 1
                print(f"✓ User {user.id} (@{user.username}): '{old_mode}' → 'api+instagram'")
            elif old_mode == "instagram":
                user.verify_mode = "api+instagram"
                updated += 1
                print(f"✓ User {user.id} (@{user.username}): '{old_mode}' → 'api+instagram'")
            elif old_mode == "proxy":
                user.verify_mode = "api+proxy"
                updated += 1
                print(f"✓ User {user.id} (@{user.username}): '{old_mode}' → 'api+proxy'")
            elif old_mode is None or old_mode == "":
                user.verify_mode = "api+instagram"
                updated += 1
                print(f"✓ User {user.id} (@{user.username}): NULL → 'api+instagram'")
            else:
                print(f"- User {user.id} (@{user.username}): '{old_mode}' (не требует обновления)")
        
        if updated > 0:
            session.commit()
            print()
            print(f"✅ Обновлено пользователей: {updated}")
        else:
            print()
            print("✅ Все пользователи уже имеют правильные значения")
    
    print()
    print("=" * 80)
    print("МИГРАЦИЯ ЗАВЕРШЕНА")
    print("=" * 80)
    print()
    print("📝 Доступные режимы проверки:")
    print("   • api+instagram - API проверка + Instagram с логином")
    print("   • api+proxy     - API проверка + Proxy без логина")

if __name__ == "__main__":
    main()

