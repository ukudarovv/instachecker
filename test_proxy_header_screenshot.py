"""
Тестовый скрипт для проверки скриншотов header'а с темной темой через proxy БЕЗ IG сессии.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from project.services.ig_screenshot import check_account_with_header_screenshot
from project.database import get_session_factory, init_db
from project.models import Proxy


async def test_header_screenshot_with_proxy():
    """Тест скриншота header'а через proxy с темной темой"""
    
    print("=" * 70)
    print("🧪 ТЕСТ: Скриншот header'а профиля через proxy с темной темой")
    print("=" * 70)
    
    # Инициализируем базу данных
    from project.database import get_engine
    
    # Используем стандартный путь к базе
    db_url = "sqlite:///bot.db"
    engine = get_engine(db_url)
    init_db(engine)
    session_factory = get_session_factory(engine)
    
    # Получаем первый активный прокси из базы
    with session_factory() as session:
        proxy = session.query(Proxy).filter(
            Proxy.is_active == True
        ).first()
        
        if not proxy:
            print("\n❌ ОШИБКА: Нет активных прокси в базе данных!")
            print("   Добавьте прокси через бота или скрипт add_test_proxy.py")
            return False
        
        # Формируем proxy URL
        if proxy.username and proxy.password:
            proxy_url = f"{proxy.scheme}://{proxy.username}:{proxy.password}@{proxy.host}"
        else:
            proxy_url = f"{proxy.scheme}://{proxy.host}"
        
        print(f"\n📋 Параметры теста:")
        print(f"   Username: @instagram")
        print(f"   Proxy: {proxy.scheme}://{proxy.host}")
        print(f"   Headless: True")
        print(f"   Dark theme: True")
        print()
    
    # Тестовый username (публичный профиль)
    test_username = "instagram"  # Официальный аккаунт Instagram
    
    # Создаем папку для скриншотов
    screenshots_dir = "screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    
    # Путь для скриншота
    screenshot_path = os.path.join(screenshots_dir, f"test_header_dark_{test_username}.png")
    
    print(f"🔍 Запускаем проверку...")
    print()
    
    try:
        result = await check_account_with_header_screenshot(
            username=test_username,
            proxy_url=proxy_url,
            screenshot_path=screenshot_path,
            headless=True,
            timeout_ms=60000,
            dark_theme=True  # Темная тема (черный фон)
        )
        
        print()
        print("=" * 70)
        print("📊 РЕЗУЛЬТАТЫ ТЕСТА")
        print("=" * 70)
        print(f"✅ Успех: {result.get('exists')}")
        print(f"📝 Checked via: {result.get('checked_via')}")
        print(f"📸 Скриншот: {result.get('screenshot_path')}")
        
        if result.get('error'):
            print(f"⚠️  Ошибка: {result.get('error')}")
        
        screenshot = result.get('screenshot_path')
        if screenshot and os.path.exists(screenshot):
            # Проверяем размер файла
            size = os.path.getsize(screenshot) / 1024  # KB
            print(f"📏 Размер файла: {size:.1f} KB")
            
            # Проверяем размер изображения
            try:
                from PIL import Image
                img = Image.open(screenshot)
                width, height = img.size
                print(f"🖼️  Размер изображения: {width}x{height} px")
                
                # Проверяем цвет фона (должен быть черный для темной темы)
                # Получаем пиксель из верхнего левого угла
                pixel = img.getpixel((10, 10))
                
                # Проверяем, что фон темный (близко к черному)
                if isinstance(pixel, tuple) and len(pixel) >= 3:
                    r, g, b = pixel[0], pixel[1], pixel[2]
                    avg_brightness = (r + g + b) / 3
                    
                    print(f"🎨 Цвет фона (RGB): ({r}, {g}, {b})")
                    print(f"💡 Яркость фона: {avg_brightness:.1f}/255")
                    
                    if avg_brightness < 50:  # Темный фон
                        print()
                        print("✅ УСПЕХ: Темная тема применена (черный фон)")
                    else:
                        print()
                        print("⚠️  ВНИМАНИЕ: Фон не черный (темная тема не применилась?)")
                
                # Проверяем, что это header (должен быть небольшой высоты)
                if height < 600:
                    print(f"✅ УСПЕХ: Скриншот header'а (высота {height}px)")
                else:
                    print(f"⚠️  ВНИМАНИЕ: Скриншот выглядит как полная страница (высота {height}px)")
                    
            except ImportError:
                print("⚠️  PIL не установлен, пропускаем проверку изображения")
            
            print()
            print(f"📂 Скриншот сохранен: {screenshot}")
            print(f"   Откройте файл, чтобы убедиться, что:")
            print(f"   1. Виден только header профиля (не весь профиль)")
            print(f"   2. Фон черный (темная тема)")
            print(f"   3. Текст белый")
        else:
            print()
            print("❌ ОШИБКА: Скриншот не создан!")
        
        print()
        print("=" * 70)
        
        return result.get('exists') is True
        
    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ ОШИБКА ТЕСТА: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print()
    print("🚀 Запуск теста скриншота header'а с темной темой через proxy...")
    print()
    
    result = asyncio.run(test_header_screenshot_with_proxy())
    
    print()
    if result:
        print("✅ Тест завершен успешно!")
        print()
        print("📝 Проверьте скриншот:")
        print("   • Только header профиля (не весь профиль)")
        print("   • Черный фон (темная тема)")
        print("   • Белый текст")
    else:
        print("❌ Тест завершен с ошибками")
    print()

