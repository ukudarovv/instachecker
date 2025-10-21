"""
Тестовый скрипт для проверки системы обхода 403 ошибок Instagram.

Запуск:
    python test_403_bypass.py

Этот скрипт протестирует все методы обхода:
1. Быстрая проверка с мобильными заголовками
2. API endpoints
3. Мобильные API endpoints
4. Публичные источники (Google Cache, Archive.org)
5. Мобильная эмуляция (Chrome Mobile)
6. Полная скрытая проверка
"""

import asyncio
import sys

# Добавляем путь к проекту
sys.path.insert(0, '.')

from project.services.instagram_bypass import check_account_with_bypass, quick_test_bypass, InstagramBypass


async def test_individual_methods(username: str):
    """
    Тестирует каждый метод обхода отдельно
    """
    print(f"\n{'='*80}")
    print(f"🧪 ТЕСТИРОВАНИЕ ОТДЕЛЬНЫХ МЕТОДОВ ОБХОДА 403 для @{username}")
    print(f"{'='*80}\n")
    
    bypass = InstagramBypass()
    
    # Метод 1: Быстрая проверка
    print("\n" + "="*80)
    print("⚡ МЕТОД 1: Быстрая проверка (мобильные headers + no redirects)")
    print("="*80)
    result1 = bypass.quick_instagram_check(username)
    print(f"Результат: {result1}\n")
    
    # Метод 2: API endpoints
    print("\n" + "="*80)
    print("📡 МЕТОД 2: API endpoints")
    print("="*80)
    result2 = bypass.check_profile_multiple_endpoints(username)
    print(f"Результат: {result2}\n")
    
    # Метод 3: Мобильные endpoints
    print("\n" + "="*80)
    print("📱 МЕТОД 3: Мобильные API endpoints")
    print("="*80)
    result3 = bypass.check_mobile_endpoints(username)
    print(f"Результат: {result3}\n")
    
    # Метод 4: Публичные источники
    print("\n" + "="*80)
    print("🌐 МЕТОД 4: Публичные источники")
    print("="*80)
    result4 = bypass.check_public_sources(username)
    print(f"Результат: {result4}\n")
    
    # Собираем результаты
    results = {
        "quick_check": result1,
        "api_endpoints": result2,
        "mobile_endpoints": result3,
        "public_sources": result4
    }
    
    # Итоговая статистика
    print("\n" + "="*80)
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print("="*80)
    
    successful_methods = []
    for method, result in results.items():
        status = "✅ УСПЕШНО" if result is True else "❌ НЕ НАЙДЕН" if result is False else "⚠️ ОШИБКА"
        print(f"{method:20s}: {status}")
        if result is not None:
            successful_methods.append(method)
    
    print(f"\nУспешных методов: {len(successful_methods)}/{len(results)}")
    
    return results


async def test_full_bypass(username: str):
    """
    Тестирует полную систему обхода (все методы последовательно)
    """
    print(f"\n{'='*80}")
    print(f"🚀 ТЕСТИРОВАНИЕ ПОЛНОЙ СИСТЕМЫ ОБХОДА 403 для @{username}")
    print(f"{'='*80}\n")
    
    result = await check_account_with_bypass(username, max_retries=1)
    
    print(f"\n{'='*80}")
    print("📊 ИТОГОВЫЙ РЕЗУЛЬТАТ")
    print(f"{'='*80}")
    print(f"Username:       {result['username']}")
    print(f"Exists:         {result['exists']}")
    print(f"Error:          {result['error']}")
    print(f"Checked via:    {result['checked_via']}")
    print(f"Methods used:   {len(result['bypass_methods_used'])} методов")
    print(f"{'='*80}\n")
    
    return result


async def test_multiple_accounts():
    """
    Тестирует несколько аккаунтов для сравнения
    """
    # Тестовые аккаунты (замените на свои)
    test_accounts = [
        "instagram",      # Должен существовать
        "cristiano",      # Должен существовать
        "thisisafakeaccountthatdoesnotexist999",  # Не должен существовать
    ]
    
    print(f"\n{'='*80}")
    print(f"🧪 МАССОВОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ ОБХОДА 403")
    print(f"{'='*80}\n")
    print(f"Тестируемые аккаунты: {len(test_accounts)}\n")
    
    results = []
    for username in test_accounts:
        print(f"\n{'='*80}")
        print(f"Тестирование @{username}")
        print(f"{'='*80}")
        
        result = await check_account_with_bypass(username, max_retries=1)
        results.append(result)
        
        print(f"\n✅ Результат: {result['exists']}")
        print(f"{'='*80}\n")
    
    # Итоговая таблица
    print(f"\n{'='*80}")
    print("📊 СВОДНАЯ ТАБЛИЦА РЕЗУЛЬТАТОВ")
    print(f"{'='*80}")
    print(f"{'Username':<40} {'Exists':<10} {'Error'}")
    print("-" * 80)
    
    for result in results:
        username = result['username']
        exists = str(result['exists'])
        error = result['error'] or "None"
        print(f"{username:<40} {exists:<10} {error}")
    
    print(f"{'='*80}\n")


async def main():
    """
    Главная функция для запуска тестов
    """
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║                  🛡️  ТЕСТ СИСТЕМЫ ОБХОДА 403 ОШИБОК INSTAGRAM  🛡️            ║
║                                                                               ║
║  Эта система включает 6 методов обхода защиты Instagram:                     ║
║                                                                               ║
║  1️⃣  Быстрая проверка с мобильными заголовками (no redirects)                ║
║  2️⃣  API endpoints (множественные)                                           ║
║  3️⃣  Мобильные API endpoints (Instagram App)                                ║
║  4️⃣  Публичные источники (Google Cache, Archive.org)                        ║
║  5️⃣  Мобильная эмуляция (Chrome Mobile Emulation)                           ║
║  6️⃣  Полная скрытая проверка через браузер                                  ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Выбор режима тестирования
    print("\nВыберите режим тестирования:")
    print("1. Тест одного аккаунта (все методы последовательно)")
    print("2. Тест отдельных методов для одного аккаунта")
    print("3. Массовый тест нескольких аккаунтов")
    print("4. Быстрый тест (quick test)")
    
    try:
        choice = input("\nВведите номер (1-4): ").strip()
        
        if choice == "1":
            username = input("Введите Instagram username: ").strip()
            await test_full_bypass(username)
            
        elif choice == "2":
            username = input("Введите Instagram username: ").strip()
            await test_individual_methods(username)
            
        elif choice == "3":
            await test_multiple_accounts()
            
        elif choice == "4":
            username = input("Введите Instagram username: ").strip()
            await quick_test_bypass(username)
            
        else:
            print("❌ Неверный выбор")
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

