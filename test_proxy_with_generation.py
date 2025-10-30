"""
Тест функции тестирования прокси с генерацией профиля (БЕЗ БРАУЗЕРА)
"""
import asyncio
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from project.models import Proxy
from project.services.proxy_tester import test_proxy_with_screenshot

# Создаем сессию БД
engine = create_engine('sqlite:///bot.db', echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def test_proxy_generation():
    """Тест прокси с генерацией профиля"""
    session = SessionLocal()
    
    try:
        print("="*70)
        print("🧪 ТЕСТ: Проверка прокси с генерацией профиля (БЕЗ БРАУЗЕРА)")
        print("="*70)
        
        # Получаем активный прокси
        proxy = session.query(Proxy).filter(
            Proxy.is_active == True,
            Proxy.user_id == 1
        ).first()
        
        if not proxy:
            print("\n❌ Нет активных прокси в БД")
            return False
        
        print(f"\n📡 Прокси: {proxy.scheme}://{proxy.host}")
        print(f"👤 Тестовый аккаунт: @instagram")
        print(f"🚀 Метод: API + Генерация (без браузера)")
        print("-"*70)
        
        # Тестируем прокси
        success, message, screenshot_path = await test_proxy_with_screenshot(
            proxy=proxy,
            test_username="instagram"
        )
        
        print("\n" + "="*70)
        print("📊 РЕЗУЛЬТАТ ТЕСТА:")
        print("="*70)
        
        if success:
            print("✅ Успех!")
            print(f"\n{message}")
            if screenshot_path:
                print(f"\n📁 Путь к файлу: {screenshot_path}")
        else:
            print("❌ Ошибка!")
            print(f"\n{message}")
        
        print("\n" + "="*70)
        
        return success
        
    except Exception as e:
        print(f"\n❌ Ошибка теста: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()

async def test_multiple_accounts():
    """Тест нескольких аккаунтов"""
    session = SessionLocal()
    
    try:
        print("\n" + "="*70)
        print("🧪 ТЕСТ: Несколько аккаунтов")
        print("="*70)
        
        proxy = session.query(Proxy).filter(
            Proxy.is_active == True,
            Proxy.user_id == 1
        ).first()
        
        if not proxy:
            print("\n❌ Нет активных прокси в БД")
            return
        
        test_accounts = ["instagram", "cristiano", "leomessi"]
        results = []
        
        for username in test_accounts:
            print(f"\n📝 Тестируем @{username}...")
            success, message, screenshot_path = await test_proxy_with_screenshot(
                proxy=proxy,
                test_username=username
            )
            results.append({
                "username": username,
                "success": success,
                "path": screenshot_path
            })
            print(f"   {'✅' if success else '❌'} {username}")
            await asyncio.sleep(2)  # Пауза между запросами
        
        print("\n" + "="*70)
        print("📊 ИТОГИ:")
        print("="*70)
        successful = sum(1 for r in results if r["success"])
        print(f"✅ Успешно: {successful}/{len(test_accounts)}")
        print(f"❌ Ошибок: {len(test_accounts) - successful}/{len(test_accounts)}")
        
        for result in results:
            status = "✅" if result["success"] else "❌"
            print(f"   {status} @{result['username']}")
            if result["path"]:
                print(f"      📁 {result['path']}")
        
        print("="*70)
        
    finally:
        session.close()

async def main():
    """Главная функция"""
    print("\n" + "🎨"*35)
    print(" "*10 + "ТЕСТИРОВАНИЕ ПРОКСИ С ГЕНЕРАЦИЕЙ")
    print("🎨"*35)
    
    # Тест 1: Один аккаунт
    result1 = await test_proxy_generation()
    
    if result1:
        # Тест 2: Несколько аккаунтов
        response = input("\n\n⚡ Протестировать еще несколько аккаунтов? (y/n): ")
        if response.lower() == 'y':
            await test_multiple_accounts()
    
    print("\n" + "🎉"*35)
    print(" "*15 + "ТЕСТЫ ЗАВЕРШЕНЫ")
    print("   Теперь прокси тестируются БЕЗ браузера!")
    print("   Используется API + генерация шапки профиля")
    print("🎉"*35 + "\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏸️  Прервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

