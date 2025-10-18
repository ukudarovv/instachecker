#!/usr/bin/env python3
"""
Test triple checker functionality
"""

import asyncio
import sys
sys.path.append('project')
from models import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.triple_checker import check_account_triple
from services.ig_sessions import get_active_session
from utils.encryptor import OptionalFernet
from config import get_settings
from utils.async_bot_wrapper import AsyncBotWrapper

async def test_triple_checker():
    engine = create_engine('sqlite:///bot.db')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Get user
    user = session.query(User).filter(User.id == 1972775559).first()
    if not user:
        print('User not found')
        return
    
    print(f'User: {user.username} (ID: {user.id})')
    print(f'Current verify_mode: {user.verify_mode}')
    
    # Set to triple check mode
    user.verify_mode = 'api+proxy+instagram'
    session.commit()
    print(f'✅ Updated verify_mode to: api+proxy+instagram')
    
    # Get Instagram session
    settings = get_settings()
    fernet = OptionalFernet(settings.encryption_key)
    ig_session = get_active_session(session, user.id)
    
    if not ig_session:
        print('❌ No Instagram session found')
        return
    
    print(f'✅ Found Instagram session: @{ig_session.username}')
    
    # Test triple check with ukudarov account
    test_username = 'ukudarov'
    print(f'\n🔍 Testing triple check for @{test_username}...')
    
    result = await check_account_triple(
        session=session,
        user_id=user.id,
        username=test_username,
        ig_session=ig_session,
        fernet=fernet
    )
    
    print(f'\n📊 **Triple Check Results:**')
    print(f'  Username: @{result["username"]}')
    print(f'  API Active: {result.get("api_active")}')
    print(f'  Profile Exists: {result.get("profile_exists")}')
    print(f'  Exists: {result.get("exists")}')
    print(f'  Checked Via: {result.get("checked_via")}')
    print(f'  Screenshot: {result.get("screenshot_path")}')
    print(f'  Error: {result.get("error")}')
    print(f'  Warning: {result.get("warning")}')
    
    # Send result to user
    bot = AsyncBotWrapper(settings.bot_token)
    
    if result.get('exists') is True:
        message = f'✅ **Тройная проверка пройдена!**\\n\\n'
        message += f'👤 @{test_username}\\n'
        message += f'📡 API: Активен ✅\\n'
        message += f'🌐 Профиль: Найден ✅\\n'
        message += f'🔍 Метод: {result.get("checked_via")}\\n\\n'
        message += f'📸 Скриншот отправляется...'
        
        await bot.send_message(user.id, message)
        
        # Send screenshot
        if result.get('screenshot_path'):
            import os
            if os.path.exists(result['screenshot_path']):
                await bot.send_photo(user.id, result['screenshot_path'])
                print('📸 Screenshot sent!')
            else:
                print('⚠️ Screenshot file not found')
    elif result.get('warning'):
        message = f'⚠️ **Предупреждение для @{test_username}**\\n\\n'
        message += f'📡 API: Активен ✅\\n'
        message += f'🌐 Профиль: Не найден ❌\\n\\n'
        message += f'**Детали:** {result.get("warning")}'
        
        await bot.send_message(user.id, message)
        print('⚠️ Warning sent!')
    else:
        message = f'❌ **Проверка не пройдена для @{test_username}**\\n\\n'
        message += f'Ошибка: {result.get("error", "неизвестная ошибка")}'
        
        await bot.send_message(user.id, message)
        print('❌ Error notification sent!')

if __name__ == '__main__':
    asyncio.run(test_triple_checker())
