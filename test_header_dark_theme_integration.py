#!/usr/bin/env python3
"""
Тест интеграции функции check_account_with_header_dark_theme.
Проверяет, что функция работает с новыми параметрами (увеличение высоты, без обрезки по бокам).
"""

import asyncio
import os
import sys
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from project.database import get_engine, get_session_factory, init_db
from project.models import Proxy
from project.services.main_checker import check_account_with_header_dark_theme

async def test_header_dark_theme_integration():
    """Тест функции header скриншота с темной темой"""
    
    print("=" * 80)
    print("🧪 ТЕСТ: Header скриншот с темной темой (интеграция)")
    print("=" * 80)
    
    # Инициализация базы данных
    db_url = "sqlite:///bot.db"
    engine = get_engine(db_url)
    init_db(engine)
    session_factory = get_session_factory(engine)
    
    # Создаем сессию
    with session_factory() as session:
        # Тестовые данные
        test_username = "instagram"
        test_user_id = 1
        
        print(f"\n👤 Пользователь: {test_user_id}")
        print(f"🔍 Проверяем: @{test_username}")
        
        # Проверяем наличие прокси
        proxies = session.query(Proxy).filter(
            Proxy.user_id == test_user_id,
            Proxy.is_active == True
        ).all()
        
        if not proxies:
            print("❌ Прокси не найдены для тестирования")
            return
        
        print(f"🌐 Найдено прокси: {len(proxies)}")
        
        # Запускаем проверку header скриншота
        print(f"\n🚀 Запускаем header скриншот с темной темой...")
        
        try:
            success, message, screenshot_path = await check_account_with_header_dark_theme(
                username=test_username,
                session=session,
                user_id=test_user_id
            )
            
            print(f"\n📊 РЕЗУЛЬТАТЫ")
            print("=" * 80)
            print(f"✅ Успех: {success}")
            print(f"📝 Сообщение: {message}")
            print(f"📸 Скриншот: {screenshot_path}")
            
            if screenshot_path and os.path.exists(screenshot_path):
                file_size = os.path.getsize(screenshot_path) / 1024
                print(f"📏 Размер файла: {file_size:.1f} KB")
                
                # Получаем размеры изображения
                try:
                    from PIL import Image
                    with Image.open(screenshot_path) as img:
                        width, height = img.size
                        print(f"🖼️  Разрешение: {width}x{height} px")
                        
                        # Проверяем, что ширина полная (без обрезки по бокам)
                        if width >= 1000:  # Ожидаем полную ширину
                            print(f"✅ Ширина полная: {width}px (без обрезки по бокам)")
                        else:
                            print(f"⚠️ Ширина обрезана: {width}px")
                        
                        # Проверяем, что высота увеличена
                        if height >= 450:  # Ожидаем увеличенную высоту
                            print(f"✅ Высота увеличена: {height}px (+15px сверху и снизу)")
                        else:
                            print(f"⚠️ Высота стандартная: {height}px")
                            
                except ImportError:
                    print("⚠️ PIL не установлен, размеры не определены")
                except Exception as e:
                    print(f"⚠️ Ошибка получения размеров: {e}")
            
            if success:
                print(f"\n🎯 УСПЕХ! Header скриншот с темной темой работает!")
                if screenshot_path:
                    print(f"👉 Откройте файл: {screenshot_path}")
                    print(f"✅ Проверьте:")
                    print(f"   • Темная тема (черный фон)")
                    print(f"   • Белый текст")
                    print(f"   • Только header профиля")
                    print(f"   • Статистика видна")
                    print(f"   • Увеличенная высота (+15px сверху и снизу)")
                    print(f"   • Полная ширина (без обрезки по бокам)")
            else:
                print(f"\n❌ ОШИБКА: {message}")
                
        except Exception as e:
            print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(test_header_dark_theme_integration())
