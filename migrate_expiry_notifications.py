"""Add expiry_notifications table for tracking sent notifications."""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from project.config import get_settings
from project.database import get_engine
from project.models import Base

def main():
    """Run migration."""
    print("=" * 80)
    print("МИГРАЦИЯ: Добавление таблицы expiry_notifications")
    print("=" * 80)
    print()
    
    settings = get_settings()
    engine = get_engine(settings.db_url)
    
    print("Создание таблицы expiry_notifications...")
    
    try:
        # Create only the new table
        Base.metadata.create_all(engine, checkfirst=True)
        print("✅ Таблица expiry_notifications создана успешно!")
    except Exception as e:
        print(f"❌ Ошибка создания таблицы: {e}")
        return
    
    print()
    print("=" * 80)
    print("МИГРАЦИЯ ЗАВЕРШЕНА")
    print("=" * 80)

if __name__ == "__main__":
    main()

