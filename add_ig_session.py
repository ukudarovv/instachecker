#!/usr/bin/env python3
"""
Функция для добавления Instagram сессии с логином, паролем и куками
"""

import sys
sys.path.append('project')
from models import User, InstagramSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.encryptor import OptionalFernet
from config import get_settings
import json

def add_instagram_session(user_id: int, username: str, password: str, cookies_json: list = None):
    """
    Добавить Instagram сессию с логином, паролем и куками
    
    Args:
        user_id: ID пользователя
        username: Имя пользователя Instagram
        password: Пароль Instagram
        cookies_json: Список куков в формате JSON (опционально)
    """
    # Connect to database
    engine = create_engine('sqlite:///bot.db')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Get user
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        print(f'❌ User {user_id} not found')
        return False
    
    # Get settings and fernet
    settings = get_settings()
    fernet = OptionalFernet(settings.encryption_key)
    
    # Prepare cookies
    if cookies_json is None:
        cookies_json = []
    
    # Encrypt cookies
    cookies_raw = json.dumps(cookies_json, ensure_ascii=False)
    cookies_encrypted = fernet.encrypt(cookies_raw)
    
    # Encrypt password
    password_encrypted = fernet.encrypt(password)
    
    # Create Instagram session
    ig_session = InstagramSession(
        user_id=user_id,
        username=username,
        password=password_encrypted,
        cookies=cookies_encrypted,
        is_active=True
    )
    
    session.add(ig_session)
    session.commit()
    
    print(f'✅ Instagram session created for @{username}')
    print(f'   User ID: {user_id}')
    print(f'   Username: {username}')
    print(f'   Password: {"*" * len(password)}')
    print(f'   Cookies: {len(cookies_json)} items')
    print(f'   Active: True')
    
    return True

def add_instagram_session_interactive():
    """Интерактивная функция для добавления Instagram сессии"""
    print("🔐 Добавление Instagram сессии")
    print("=" * 40)
    
    try:
        user_id = int(input("Введите ID пользователя: "))
        username = input("Введите имя пользователя Instagram: ")
        password = input("Введите пароль Instagram: ")
        
        print("\n📋 Куки (опционально):")
        print("Введите куки в формате JSON или нажмите Enter для пропуска")
        print("Пример: [{'name': 'sessionid', 'value': 'abc123', 'domain': '.instagram.com'}]")
        
        cookies_input = input("Куки: ").strip()
        cookies_json = []
        
        if cookies_input:
            try:
                cookies_json = json.loads(cookies_input)
                print(f"✅ Загружено {len(cookies_json)} куков")
            except json.JSONDecodeError:
                print("❌ Ошибка в формате JSON, куки не добавлены")
        
        # Add session
        success = add_instagram_session(user_id, username, password, cookies_json)
        
        if success:
            print("\n🎉 Instagram сессия успешно добавлена!")
        else:
            print("\n❌ Ошибка при добавлении сессии")
            
    except ValueError:
        print("❌ Неверный формат ID пользователя")
    except KeyboardInterrupt:
        print("\n❌ Операция отменена")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == '__main__':
    add_instagram_session_interactive()
