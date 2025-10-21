#!/usr/bin/env python3
"""
Скрипт для быстрого добавления тестовых прокси в бот.
Используйте это для тестирования функции массового добавления.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from project.database import get_engine, get_session_factory
from project.config import get_settings
from project.models import Proxy, User
from project.utils.encryptor import OptionalFernet
from project.services.proxy_parser import parse_proxy_list, validate_proxy_data, deduplicate_proxies


# Список тестовых прокси (можете изменить на свои)
TEST_PROXIES = """
# Резидентный прокси resi.gg (рабочий)
http://74276e667af9:d9754cc35e1e@proxy.resi.gg:12321

# Примеры других форматов (замените на свои реальные)
# http://user:pass@proxy2.com:8080
# socks5://user:pass@proxy3.com:1080
# 192.168.1.1:3128
# proxy4.com:8080:user:pass
"""


def batch_add_proxies(proxy_list_text: str):
    """Массовое добавление прокси из списка."""
    
    print("="*80)
    print("📦 МАССОВОЕ ДОБАВЛЕНИЕ ПРОКСИ")
    print("="*80)
    
    # Получаем настройки
    settings = get_settings()
    engine = get_engine(settings.db_url)
    SessionFactory = get_session_factory(engine)
    
    # Парсим список
    print(f"\n📝 Парсинг списка...")
    valid_proxies, parse_errors = parse_proxy_list(proxy_list_text)
    
    print(f"  ✅ Распарсено: {len(valid_proxies)}")
    if parse_errors:
        print(f"  ⚠️ Ошибок парсинга: {len(parse_errors)}")
        for err in parse_errors[:3]:
            print(f"    • {err}")
        if len(parse_errors) > 3:
            print(f"    ... и еще {len(parse_errors) - 3}")
    
    if not valid_proxies:
        print("\n❌ Не найдено валидных прокси!")
        return False
    
    # Получаем пользователя
    with SessionFactory() as session:
        user = session.query(User).filter(
            (User.role.in_(['admin', 'superuser'])) | (User.is_active == True)
        ).first()
        
        if not user:
            print("\n❌ Не найдено активных пользователей!")
            return False
        
        print(f"\n👤 Пользователь: {user.username or user.telegram_id}")
        
        # Получаем существующие прокси
        existing = session.query(Proxy).filter(Proxy.user_id == user.id).all()
        existing_data = [
            {'scheme': p.scheme, 'host': p.host}
            for p in existing
        ]
        
        print(f"  📊 Существующих прокси: {len(existing)}")
        
        # Дедупликация
        unique_proxies, duplicates = deduplicate_proxies(existing_data, valid_proxies)
        
        if duplicates > 0:
            print(f"  ⚠️ Найдено дубликатов: {duplicates}")
        
        # Валидация
        print(f"\n🔍 Валидация...")
        validated = []
        validation_errors = []
        
        for proxy_data in unique_proxies:
            is_valid, error = validate_proxy_data(proxy_data)
            if is_valid:
                validated.append(proxy_data)
            else:
                validation_errors.append(f"{proxy_data['host']}: {error}")
        
        print(f"  ✅ Валидных для добавления: {len(validated)}")
        
        if validation_errors:
            print(f"  ❌ Ошибок валидации: {len(validation_errors)}")
            for err in validation_errors[:3]:
                print(f"    • {err}")
            if len(validation_errors) > 3:
                print(f"    ... и еще {len(validation_errors) - 3}")
        
        if not validated:
            print("\n⚠️ Нет валидных прокси для добавления!")
            return False
        
        # Сохраняем
        print(f"\n💾 Сохранение в базу данных...")
        
        encryptor = OptionalFernet(settings.encryption_key)
        added_count = 0
        
        for proxy_data in validated:
            proxy = Proxy(
                user_id=user.id,
                scheme=proxy_data['scheme'],
                host=proxy_data['host'],
                username=proxy_data.get('username'),
                password=encryptor.encrypt(proxy_data['password']) if proxy_data.get('password') else None,
                is_active=True,
                priority=5
            )
            session.add(proxy)
            added_count += 1
            print(f"  • {proxy_data['scheme']}://{proxy_data['host']}")
        
        session.commit()
        
        print(f"\n{'='*80}")
        print(f"📊 ИТОГОВЫЙ ОТЧЕТ")
        print(f"{'='*80}")
        print(f"✅ Добавлено: {added_count}")
        if duplicates > 0:
            print(f"⚠️ Дубликатов (пропущено): {duplicates}")
        if parse_errors:
            print(f"❌ Ошибок парсинга: {len(parse_errors)}")
        if validation_errors:
            print(f"❌ Ошибок валидации: {len(validation_errors)}")
        
        print(f"\n💡 Все прокси добавлены с приоритетом 5 (по умолчанию)")
        print(f"💡 Откройте бота: Главное меню → Прокси → Мои прокси")
        
        return True


def main():
    """Главная функция."""
    print("\n" + "="*80)
    print("🔍 ТЕСТ МАССОВОГО ДОБАВЛЕНИЯ ПРОКСИ")
    print("="*80)
    print("\n💡 Этот скрипт добавит тестовые прокси в бот")
    print("💡 Вы можете изменить список в переменной TEST_PROXIES\n")
    
    try:
        success = batch_add_proxies(TEST_PROXIES)
        
        if success:
            print("\n✅ Прокси успешно добавлены!")
            print("\n📱 Следующие шаги:")
            print("  1. Запустите бота: python run_bot.py")
            print("  2. Откройте в Telegram")
            print("  3. Главное меню → Прокси → Мои прокси")
            print("  4. Проверьте добавленные прокси")
            print("\n🚀 Готово!")
        else:
            print("\n❌ Не удалось добавить прокси")
            print("💡 Проверьте список TEST_PROXIES в файле")
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

