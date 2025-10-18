#!/usr/bin/env python3
"""
Test all verification modes
"""

import asyncio
import sys
sys.path.append('project')
from models import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.async_bot_wrapper import AsyncBotWrapper
from config import get_settings

async def test_all_modes():
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
    
    # Get settings
    settings = get_settings()
    bot = AsyncBotWrapper(settings.bot_token)
    
    modes = [
        ("api+instagram", "🔑 API + 📸 Instagram"),
        ("api+proxy", "🔑 API + 🌐 Proxy"),
        ("api+proxy+instagram", "🔑 API + 🌐 Proxy + 📸 Instagram (тройная)"),
        ("instagram+proxy", "📸 Instagram + 🌐 Proxy (без API)"),
        ("instagram", "📸 Только Instagram"),
        ("proxy", "🌐 Только Proxy")
    ]
    
    message = "✅ **ВСЕ РЕЖИМЫ ПРОВЕРКИ ДОБАВЛЕНЫ!**\n\n"
    message += "**📋 Доступные режимы:**\n\n"
    
    for mode_value, mode_label in modes:
        message += f"• **{mode_label}**\n"
        message += f"  `{mode_value}`\n\n"
    
    message += "**⚙️ Как выбрать режим:**\n"
    message += "1. Перейдите в меню → ⚙️ Настройки\n"
    message += "2. Выберите \"🔄 Режим проверки\"\n"
    message += "3. Выберите нужный режим\n\n"
    
    message += "**📊 Описание режимов:**\n\n"
    message += "**С API:**\n"
    message += "• API + Instagram - быстрая API проверка + скрин через Instagram\n"
    message += "• API + Proxy - быстрая API проверка + скрин через прокси\n"
    message += "• API + Proxy + Instagram - API + прокси + логин + проверка профиля\n\n"
    
    message += "**Без API:**\n"
    message += "• Instagram + Proxy - логин через прокси + проверка профиля\n"
    message += "• Только Instagram - проверка только через Instagram\n"
    message += "• Только Proxy - проверка только через прокси (без логина)\n\n"
    
    message += "**🎯 Готово к использованию!**"
    
    await bot.send_message(user.id, message)
    print('All modes info sent!')

if __name__ == '__main__':
    asyncio.run(test_all_modes())
