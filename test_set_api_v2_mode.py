#!/usr/bin/env python3
"""
Тест установки режима api-v2 в системе.
"""

import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.join(os.path.dirname(__file__), 'project'))

from project.models import User, SystemSettings
from project.config import get_settings
from project.services.system_settings import set_global_verify_mode, get_global_verify_mode
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def test_set_api_v2_mode():
    """Тест установки режима api-v2"""
    
    # Настройка базы данных
    settings = get_settings()
    engine = create_engine(settings.db_url)
    SessionLocal = sessionmaker(bind=engine)
    
    with SessionLocal() as session:
        print("🔧 Установка режима проверки api-v2...")
        
        # Устанавливаем режим api-v2
        try:
            set_global_verify_mode(session, "api-v2")
            print("✅ Режим api-v2 установлен успешно")
        except Exception as e:
            print(f"❌ Ошибка при установке режима: {e}")
            return
        
        # Проверяем, что режим установлен
        current_mode = get_global_verify_mode(session)
        print(f"📊 Текущий режим проверки: {current_mode}")
        
        if current_mode == "api-v2":
            print("🎉 Режим api-v2 успешно установлен и активен!")
        else:
            print(f"⚠️ Ожидался режим api-v2, но получен: {current_mode}")

if __name__ == "__main__":
    test_set_api_v2_mode()
