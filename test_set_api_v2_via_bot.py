#!/usr/bin/env python3
"""
Тест установки режима api-v2 через бота.
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

def test_set_api_v2_via_bot():
    """Тест установки режима api-v2 через бота"""
    
    # Настройка базы данных
    settings = get_settings()
    engine = create_engine(settings.db_url)
    SessionLocal = sessionmaker(bind=engine)
    
    with SessionLocal() as session:
        print("🔧 Тестирование установки режима api-v2 через бота...")
        
        # Получаем текущий режим
        current_mode = get_global_verify_mode(session)
        print(f"📊 Текущий режим: {current_mode}")
        
        # Устанавливаем режим api-v2
        print("🔄 Устанавливаем режим api-v2...")
        try:
            set_global_verify_mode(session, "api-v2")
            print("✅ Режим api-v2 установлен успешно")
        except Exception as e:
            print(f"❌ Ошибка при установке режима: {e}")
            return
        
        # Проверяем, что режим установлен
        new_mode = get_global_verify_mode(session)
        print(f"📊 Новый режим: {new_mode}")
        
        if new_mode == "api-v2":
            print("🎉 Режим api-v2 успешно установлен и активен!")
            print("✅ Теперь в боте можно выбрать '🔑 API v2 + 🌐 Proxy (новый)'")
        else:
            print(f"⚠️ Ожидался режим api-v2, но получен: {new_mode}")
        
        # Возвращаем обратно api+instagram для тестов
        print("\n🔄 Возвращаем режим api+instagram...")
        set_global_verify_mode(session, "api+instagram")
        final_mode = get_global_verify_mode(session)
        print(f"📊 Финальный режим: {final_mode}")

if __name__ == "__main__":
    test_set_api_v2_via_bot()
