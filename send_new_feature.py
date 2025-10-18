#!/usr/bin/env python3
"""
Send new feature announcement
"""

import asyncio
import sys
sys.path.append('project')
from utils.async_bot_wrapper import AsyncBotWrapper
from config import get_settings

async def send_new_feature_message():
    settings = get_settings()
    bot = AsyncBotWrapper(settings.bot_token)
    
    message = '''🚀 **НОВАЯ ФУНКЦИЯ: Полная настройка Instagram сессии!**

**🔐 Что нового:**
• Добавлена кнопка "🚀 Полная настройка (логин + пароль + куки)"
• Можно указать username, password и cookies одновременно
• Удобный формат ввода всех данных

**📋 Как использовать:**
1. Перейдите в Instagram → Добавить IG-сессию
2. Выберите "🚀 Полная настройка"
3. Введите данные в формате:
```
username: your_username
password: your_password
cookies: [{"name": "sessionid", "value": "abc123", "domain": ".instagram.com"}]
```

**✅ Преимущества:**
• Все данные сохраняются за один раз
• Поддержка логина, пароля и куков
• Автоматическая валидация формата
• Шифрование всех данных

**🎯 Готово к использованию!**'''
    
    await bot.send_message(1972775559, message)
    print('New feature message sent!')

if __name__ == '__main__':
    asyncio.run(send_new_feature_message())
