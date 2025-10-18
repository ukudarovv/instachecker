#!/usr/bin/env python3
import asyncio
import sys
sys.path.append('project')
from models import User, Account, Proxy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.hybrid_checker import check_account_hybrid
from utils.async_bot_wrapper import AsyncBotWrapper
from config import get_settings

async def test_proxy_fallback():
    engine = create_engine('sqlite:///bot.db')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Get user
    user = session.query(User).filter(User.id == 1972775559).first()
    if not user:
        print('User not found')
        return
    
    # Get user's accounts
    accounts = session.query(Account).filter(Account.user_id == user.id, Account.done == False).all()
    print(f'User {user.id} has {len(accounts)} pending accounts')
    
    # Check proxies
    proxies = session.query(Proxy).filter(Proxy.user_id == user.id, Proxy.is_active == True).all()
    print(f'User has {len(proxies)} active proxies')
    
    if accounts:
        # Test with first account
        test_account = accounts[0]
        print(f'Testing proxy fallback for: @{test_account.account}')
        
        # Get settings
        settings = get_settings()
        fernet = None
        
        # Try hybrid check with proxy fallback
        result = await check_account_hybrid(
            session=session,
            user_id=user.id,
            username=test_account.account,
            ig_session=None,
            fernet=fernet,
            verify_mode='api+proxy'
        )
        
        print(f'Proxy fallback result: {result}')
        
        # Send result to user
        bot = AsyncBotWrapper(settings.bot_token)
        
        if result.get('exists') is True:
            message = f'✅ @{test_account.account} активен! (proxy fallback)'
            if result.get('proxy_used'):
                message += f'\n🔗 Прокси: {result["proxy_used"]}'
            if result.get('attempts'):
                message += f'\n🔄 Попыток: {result["attempts"]}'
            await bot.send_message(user.id, message)
            
            # Send screenshot if available
            if result.get('screenshot_path'):
                import os
                if os.path.exists(result['screenshot_path']):
                    await bot.send_photo(user.id, result['screenshot_path'])
                    print('Screenshot sent')
        elif result.get('exists') is False:
            message = f'❌ @{test_account.account} не найден (proxy fallback)'
            await bot.send_message(user.id, message)
        else:
            error_msg = result.get('error', 'неизвестная ошибка')
            message = f'⚠️ @{test_account.account} - ошибка: {error_msg}'
            await bot.send_message(user.id, message)
        
        print('Proxy fallback result sent to user')
    else:
        print('No pending accounts found')

if __name__ == '__main__':
    asyncio.run(test_proxy_fallback())
