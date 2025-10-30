"""
Тест API v2 proxy checker с новыми параметрами DESIGN
"""
import asyncio
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from project.services.api_v2_proxy_checker import check_account_via_api_v2_proxy

# Создаем сессию БД
engine = create_engine('sqlite:///bot.db', echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def test_check_account():
    """Тест проверки аккаунта через API v2"""
    session = SessionLocal()
    
    try:
        print("="*70)
        print("🧪 ТЕСТ API V2 PROXY CHECKER С НОВЫМИ ПАРАМЕТРАМИ DESIGN")
        print("="*70)
        
        # Тестовый username
        test_username = "ukudarov"
        test_user_id = 1
        
        print(f"\n📝 Проверяю аккаунт: @{test_username}")
        print("-"*70)
        
        # Вызываем проверку
        result = await check_account_via_api_v2_proxy(
            session=session,
            user_id=test_user_id,
            username=test_username,
            max_attempts=2
        )
        
        print("\n📊 Результат проверки:")
        print(f"   Существует: {result.get('exists')}")
        print(f"   Верифицирован: {result.get('is_verified')}")
        print(f"   Приватный: {result.get('is_private')}")
        print(f"   Подписчиков: {result.get('followers')}")
        print(f"   Подписок: {result.get('following')}")
        print(f"   Постов: {result.get('posts')}")
        
        if result.get('screenshot_path'):
            print(f"\n✅ Шапка профиля сгенерирована:")
            print(f"   📁 {result['screenshot_path']}")
        else:
            print(f"\n⚠️ Шапка профиля не сгенерирована")
            if result.get('error'):
                print(f"   Ошибка: {result['error']}")
        
        print("\n" + "="*70)
        return result
        
    finally:
        session.close()

if __name__ == "__main__":
    try:
        result = asyncio.run(test_check_account())
        sys.exit(0 if result.get('success') or result.get('exists') else 1)
    except KeyboardInterrupt:
        print("\n⏸️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

