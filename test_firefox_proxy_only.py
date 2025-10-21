#!/usr/bin/env python3
"""
Тестирование Firefox ТОЛЬКО через прокси (без fallback).
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from project.services.instagram_mobile_bypass import InstagramMobileBypass
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Убедитесь, что вы находитесь в корневой директории проекта")
    sys.exit(1)


def test_firefox_proxy_only(username: str, proxy_host: str, proxy_port: int, proxy_user: str = None, proxy_pass: str = None):
    """Тестирование Firefox ТОЛЬКО через прокси."""
    
    print("╔═══════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                               ║")
    print("║              🦊 FIREFOX PROXY ONLY - ТЕСТИРОВАНИЕ  🦊                       ║")
    print("║                                                                               ║")
    print("╚═══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    # Формируем строку прокси
    if proxy_user and proxy_pass:
        proxy_string = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
        print(f"🔗 Прокси (с аутентификацией): {proxy_user}:***@{proxy_host}:{proxy_port}")
    else:
        proxy_string = f"http://{proxy_host}:{proxy_port}"
        print(f"🔗 Прокси (без аутентификации): {proxy_host}:{proxy_port}")
    
    print(f"🔍 Проверяем профиль: @{username}")
    print("=" * 80)
    print()
    
    # Создаем путь для скриншота
    screenshot_dir = "screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(screenshot_dir, f"firefox_proxy_{username}_{timestamp}.png")
    
    print(f"📸 Скриншот будет сохранен: {screenshot_path}")
    print()
    
    # Создаем экземпляр bypass
    bypass = InstagramMobileBypass()
    
    # Создаем Firefox драйвер с прокси (БЕЗ fallback)
    print("🔧 Создание Firefox драйвера с прокси (БЕЗ fallback)...")
    if not bypass.create_firefox_driver_no_fallback(headless=True, proxy=proxy_string):
        print("❌ Не удалось создать Firefox драйвер с прокси")
        print("⚠️ FALLBACK НЕ ИСПОЛЬЗУЕТСЯ - тест завершен")
        return None
    
    print("✅ Firefox драйвер успешно создан с прокси")
    print()
    
    try:
        # Проверяем профиль
        print(f"🌐 Проверка профиля @{username} через прокси...")
        
        # Подготовка сессии
        print("[PROXY-TEST] 🔧 Подготовка сессии...")
        if not bypass.prepare_session():
            print("❌ Не удалось подготовить сессию через прокси")
            return None
        
        print("[PROXY-TEST] ✅ Сессия подготовлена")
        
        # Переход на профиль
        url = f"https://www.instagram.com/{username}/"
        print(f"[PROXY-TEST] 🌐 Переход на: {url}")
        
        try:
            bypass.driver.get(url)
            print("[PROXY-TEST] ✅ Страница загружена")
        except Exception as e:
            print(f"[PROXY-TEST] ❌ Ошибка загрузки страницы: {e}")
            return None
        
        # Ждем загрузки
        import time
        time.sleep(5)
        
        # Закрываем модальное окно
        print("[PROXY-TEST] 🔍 Закрытие модального окна...")
        bypass.close_instagram_modal()
        
        # Делаем скриншот
        print(f"[PROXY-TEST] 📸 Создание скриншота: {screenshot_path}")
        try:
            bypass.driver.save_screenshot(screenshot_path)
            print(f"[PROXY-TEST] ✅ Скриншот сохранен: {screenshot_path}")
        except Exception as e:
            print(f"[PROXY-TEST] ❌ Ошибка создания скриншота: {e}")
        
        # Проверяем текущий URL
        current_url = bypass.driver.current_url
        print(f"[PROXY-TEST] 🔗 Текущий URL: {current_url}")
        
        # Проверяем заголовок страницы
        page_title = bypass.driver.title
        print(f"[PROXY-TEST] 📄 Заголовок страницы: {page_title}")
        
        # Проверяем, есть ли ошибки
        page_source = bypass.driver.page_source.lower()
        
        if "sorry, this page isn't available" in page_source or "страница недоступна" in page_source:
            print("[PROXY-TEST] ❌ Профиль не найден (404)")
            result = False
        elif "403" in page_source or "forbidden" in page_source:
            print("[PROXY-TEST] ❌ Ошибка 403 (доступ запрещен)")
            result = False
        elif username.lower() in page_title.lower():
            print(f"[PROXY-TEST] ✅ Профиль @{username} найден через прокси")
            result = True
        else:
            print("[PROXY-TEST] ⚠️ Не удалось определить статус профиля")
            result = None
        
        # Результаты
        print()
        print("=" * 80)
        print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ ЧЕРЕЗ ПРОКСИ")
        print("=" * 80)
        print(f"🔗 Прокси: {proxy_host}:{proxy_port}")
        print(f"🔍 Профиль: @{username}")
        
        if result is True:
            print("✅ Статус: НАЙДЕН через прокси")
        elif result is False:
            print("❌ Статус: НЕ НАЙДЕН")
        else:
            print("⚠️ Статус: НЕИЗВЕСТЕН")
        
        if os.path.exists(screenshot_path):
            print(f"📸 Скриншот: {screenshot_path}")
            print(f"📏 Размер: {os.path.getsize(screenshot_path)} байт")
        else:
            print("❌ Скриншот не создан")
        
        print()
        print("🎯 Тестирование через прокси завершено!")
        
        return result
        
    except Exception as e:
        print(f"❌ Ошибка при проверке: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        # Закрываем драйвер
        try:
            bypass.driver.quit()
            print("🔒 Firefox драйвер закрыт")
        except:
            pass


def main():
    """Главная функция."""
    if len(sys.argv) < 4:
        print("Использование: python test_firefox_proxy_only.py <username> <proxy_host> <proxy_port> [proxy_user] [proxy_pass]")
        print("Примеры:")
        print("  python test_firefox_proxy_only.py gid_halal 142.111.48.253 7030 aiiigauk pi8vftb70eic")
        print("  python test_firefox_proxy_only.py gid_halal 45.66.95.129 50100 a2T3nMke GgI5szmqoX")
        print("  python test_firefox_proxy_only.py gid_halal 142.111.48.253 7030")
        sys.exit(1)
    
    username = sys.argv[1]
    proxy_host = sys.argv[2]
    proxy_port = int(sys.argv[3])
    proxy_user = sys.argv[4] if len(sys.argv) > 4 else None
    proxy_pass = sys.argv[5] if len(sys.argv) > 5 else None
    
    print(f"🚀 Запуск тестирования Firefox ТОЛЬКО через прокси для @{username}")
    print(f"🔗 Прокси: {proxy_host}:{proxy_port}")
    if proxy_user:
        print(f"🔐 Аутентификация: {proxy_user}:***")
    print()
    
    # Запуск тестирования
    result = test_firefox_proxy_only(username, proxy_host, proxy_port, proxy_user, proxy_pass)
    
    if result is True:
        print("\n✅ ТЕСТ ПРОЙДЕН: Профиль найден через прокси")
        sys.exit(0)
    elif result is False:
        print("\n❌ ТЕСТ НЕ ПРОЙДЕН: Профиль не найден")
        sys.exit(1)
    else:
        print("\n⚠️ ТЕСТ НЕОПРЕДЕЛЕН: Не удалось определить статус")
        sys.exit(2)


if __name__ == "__main__":
    main()

