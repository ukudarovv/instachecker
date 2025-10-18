#!/usr/bin/env python3
"""
Test Instagram session creation function
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
    """Add Instagram session with login, password and cookies"""
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

if __name__ == '__main__':
    # Test with user 1972775559
    success = add_instagram_session(
        user_id=1972775559,
        username='test_instagram',
        password='test_password123',
        cookies_json=[
            {'name': 'sessionid', 'value': 'test_session_123', 'domain': '.instagram.com'},
            {'name': 'csrftoken', 'value': 'test_csrf_456', 'domain': '.instagram.com'}
        ]
    )
    
    if success:
        print('🎉 Test successful!')
    else:
        print('❌ Test failed!')
