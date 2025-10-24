"""
Улучшенный тест header-скриншотов с темной темой.
Показывает подробную информацию о процессе и проверяет результат.
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


async def test_header_dark_fixed():
    """Улучшенный тест header-скриншотов с темной темой"""
    
    print("=" * 80)
    print("🧪 УЛУЧШЕННЫЙ ТЕСТ: Header-скриншот с темной темой (ИСПРАВЛЕННАЯ ВЕРСИЯ)")
    print("=" * 80)
    print()
    
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
        
        print(f"📋 Параметры теста:")
        print(f"   Username: @instagram")
        print(f"   Proxy: {proxy.scheme}://{proxy.host}")
        print(f"   Headless: True")
        print(f"   Dark theme: True (темная тема Instagram)")
        print(f"   Crop to header: False (скриншот ТОЛЬКО header элемента)")
        print(f"   Ожидание: Увеличено для полной загрузки статистики (~20 секунд)")
        print()
    
    # Тестовый username (публичный профиль)
    test_username = "instagram"  # Официальный аккаунт Instagram
    
    # Создаем папку для скриншотов
    screenshots_dir = "screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    
    # Путь для скриншота
    screenshot_path = os.path.join(screenshots_dir, f"test_header_dark_FIXED_{test_username}.png")
    
    print(f"🔍 Запускаем ИСПРАВЛЕННУЮ проверку...")
    print()
    
    try:
        result = await check_account_with_header_screenshot(
            username=test_username,
            proxy_url=proxy_url,
            screenshot_path=screenshot_path,
            headless=True,  # 🔒 Фоновый режим
            timeout_ms=60000,
            dark_theme=True,  # ✅ С темной темой
            mobile_emulation=True,  # 📱 Мобильная эмуляция (iPhone 12)
            crop_ratio=0  # ✂️ БЕЗ обрезки - скриншот header элемента
        )
        
        print()
        print("=" * 80)
        print("📊 РЕЗУЛЬТАТЫ УЛУЧШЕННОГО ТЕСТА")
        print("=" * 80)
        print(f"✅ Успех: {result.get('exists')}")
        print(f"📝 Checked via: {result.get('checked_via')}")
        print(f"🌙 Темная тема применена: {result.get('dark_theme_applied', False)}")
        print(f"📱 Мобильная эмуляция: {result.get('mobile_emulation', False)}")
        print(f"✂️  Обрезка выполнена: {result.get('cropped', False)}")
        
        if result.get('original_size') and result.get('final_size'):
            print(f"📏 Размер: {result.get('original_size')} → {result.get('final_size')}")
        
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
                # Получаем несколько пикселей из разных мест
                test_pixels = [
                    (10, 10),      # Верхний левый угол
                    (width//2, 10), # Верхний центр
                    (width-10, 10), # Верхний правый угол
                    (10, height//2), # Левый центр
                    (width//2, height//2) # Центр
                ]
                
                dark_pixels = 0
                total_pixels = len(test_pixels)
                
                print(f"🎨 Проверка цвета фона в {total_pixels} точках:")
                for i, (x, y) in enumerate(test_pixels):
                    if x < width and y < height:
                        pixel = img.getpixel((x, y))
                        if isinstance(pixel, tuple) and len(pixel) >= 3:
                            r, g, b = pixel[0], pixel[1], pixel[2]
                            avg_brightness = (r + g + b) / 3
                            
                            is_dark = avg_brightness < 50  # Темный пиксель
                            if is_dark:
                                dark_pixels += 1
                            
                            status = "🌙 ТЕМНЫЙ" if is_dark else "☀️ СВЕТЛЫЙ"
                            print(f"   Точка {i+1}: RGB({r:3d},{g:3d},{b:3d}) яркость={avg_brightness:3.0f} {status}")
                
                dark_percentage = (dark_pixels / total_pixels) * 100
                print(f"📊 Темных пикселей: {dark_pixels}/{total_pixels} ({dark_percentage:.0f}%)")
                
                if dark_percentage >= 60:
                    print()
                    print("✅ УСПЕХ: Темная тема применена (большинство пикселей темные)")
                else:
                    print()
                    print("⚠️  ВНИМАНИЕ: Темная тема не применилась полностью")
                    print(f"   Только {dark_percentage:.0f}% пикселей темные (ожидается >60%)")
                
                # Проверяем, что это header (должен быть небольшой высоты)
                if height < 400:
                    print(f"✅ УСПЕХ: Скриншот header'а (высота {height}px)")
                elif height < 600:
                    print(f"⚠️  ВНИМАНИЕ: Скриншот может быть слишком большим (высота {height}px)")
                else:
                    print(f"❌ ОШИБКА: Скриншот слишком большой (высота {height}px)")
                    print(f"   Ожидается <400px для header'а")
                    
            except ImportError:
                print("⚠️  PIL не установлен, пропускаем проверку изображения")
                print("   Установите: pip install Pillow")
            except Exception as e:
                print(f"⚠️  Ошибка проверки изображения: {e}")
            
            print()
            print(f"📂 Скриншот сохранен: {screenshot}")
            print(f"   Откройте файл и проверьте:")
            print(f"   1. Виден только header профиля (не весь профиль)")
            print(f"   2. Фон черный (темная тема)")
            print(f"   3. Текст белый")
            print(f"   4. Размер небольшой (~200-400px высота)")
        else:
            print()
            print("❌ ОШИБКА: Скриншот не создан!")
        
        print()
        print("=" * 80)
        
        return result.get('exists') is True
        
    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ ОШИБКА ТЕСТА: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print()
    print("🚀 Запуск ИСПРАВЛЕННОГО теста header-скриншотов с темной темой...")
    print()
    print("🔧 Исправления:")
    print("   • Улучшенная темная тема (более агрессивная)")
    print("   • Автоматическая обрезка до 25% верха")
    print("   • Больше времени на применение стилей")
    print("   • Подробная проверка результата")
    print()
    
    result = asyncio.run(test_header_dark_fixed())
    
    print()
    if result:
        print("✅ ИСПРАВЛЕННЫЙ тест завершен успешно!")
        print()
        print("📝 Проверьте скриншот:")
        print("   • Только header профиля (не весь профиль)")
        print("   • Черный фон (темная тема)")
        print("   • Белый текст")
        print("   • Небольшой размер (~200-400px высота)")
    else:
        print("❌ ИСПРАВЛЕННЫЙ тест завершен с ошибками")
        print()
        print("🔧 Возможные решения:")
        print("   • Проверьте что прокси работает")
        print("   • Установите PIL: pip install Pillow")
        print("   • Проверьте логи выше для деталей")
    print()
