"""
Автоматический тест генератора профилей с реальным API.
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from project.database import get_engine, get_session_factory
from project.models import Proxy
from project.config import get_settings
from project.services.api_v2_proxy_checker import InstagramCheckerWithProxy
from test_api_with_profile_gen import generate_instagram_profile_image_improved


async def check_and_generate(username: str, session_db, use_proxy: bool = True):
    """Проверяет через API и генерирует профиль"""
    print(f"\n{'='*60}")
    print(f"🔍 Проверяем: @{username}")
    print(f"{'='*60}\n")
    
    # Получаем прокси
    proxy_list = []
    if use_proxy:
        proxies = session_db.query(Proxy).filter(Proxy.is_active == True).order_by(Proxy.priority.asc()).limit(3).all()
        if proxies:
            for p in proxies:
                proxy_list.append(f"{p.host}:{p.username}:{p.password}")
                print(f"🔗 Прокси: {p.host}")
    
    # API запрос
    checker = InstagramCheckerWithProxy(proxy_list=proxy_list)
    print(f"📡 API запрос...")
    
    try:
        api_result = await checker.check_account(username=username, max_attempts=3, use_proxy=use_proxy)
        
        print(f"\n📊 Результат API:")
        print(f"   {'✅' if api_result.get('exists') else '❌'} Существует: {api_result.get('exists')}")
        print(f"   {'🔒' if api_result.get('is_private') else '🔓'} Приватный: {api_result.get('is_private')}")
        print(f"   {'✓' if api_result.get('is_verified') else ' '} Верифицирован: {api_result.get('is_verified')}")
        print(f"   📛 Имя: {api_result.get('full_name', 'Нет')}")
        print(f"   📸 Посты: {api_result.get('posts', 0):,}")
        print(f"   👥 Подписчики: {api_result.get('followers', 0):,}")
        print(f"   ➕ Подписки: {api_result.get('following', 0):,}")
        
        if not api_result.get('exists'):
            print(f"\n❌ @{username} не существует")
            return None
        
        # Генерация
        print(f"\n🎨 Генерируем профиль...")
        img_result = await generate_instagram_profile_image_improved(
            username=api_result.get('username', username),
            full_name=api_result.get('full_name', ''),
            posts=api_result.get('posts', 0),
            followers=api_result.get('followers', 0),
            following=api_result.get('following', 0),
            is_private=api_result.get('is_private', False),
            is_verified=api_result.get('is_verified', False),
            biography=api_result.get('biography', ''),
            profile_pic_url=api_result.get('profile_pic_url', '')
        )
        
        if img_result.get('success'):
            print(f"\n✅ Готово: {img_result.get('image_path')}")
            return img_result.get('image_path')
        else:
            print(f"❌ Ошибка генерации")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None


async def auto_test():
    """Автоматический тест с реальными аккаунтами"""
    
    print("\n" + "="*60)
    print("🤖 АВТОМАТИЧЕСКИЙ ТЕСТ: API + Генерация профилей")
    print("="*60 + "\n")
    
    # Тестовые аккаунты
    test_accounts = [
        "instagram",
        "cristiano",
        "nonexistent_test_user_12345"
    ]
    
    # Инициализация БД
    try:
        settings = get_settings()
        engine = get_engine(settings.db_url)
        SessionFactory = get_session_factory(engine)
        session = SessionFactory()
        
        # Проверяем прокси
        proxy_count = session.query(Proxy).filter(Proxy.is_active == True).count()
        print(f"📊 Активных прокси: {proxy_count}")
        use_proxy = proxy_count > 0
        
        print(f"\n📋 Тестируем {len(test_accounts)} аккаунтов:\n")
        
        results = []
        
        for idx, username in enumerate(test_accounts, 1):
            print(f"\n[{idx}/{len(test_accounts)}]")
            
            try:
                result = await check_and_generate(username, session, use_proxy)
                
                if result:
                    results.append((username, "✅ Успех", result))
                    print(f"✅ @{username} - УСПЕХ")
                else:
                    results.append((username, "❌ Ошибка", None))
                    print(f"❌ @{username} - ОШИБКА")
                
            except Exception as e:
                results.append((username, f"❌ Exception: {str(e)[:50]}", None))
                print(f"❌ @{username} - ИСКЛЮЧЕНИЕ: {e}")
            
            # Задержка между запросами
            if idx < len(test_accounts):
                print("\n⏳ Задержка 3 секунды...")
                await asyncio.sleep(3)
        
        # Итоговая статистика
        print(f"\n\n{'='*60}")
        print("📊 ИТОГОВАЯ СТАТИСТИКА")
        print(f"{'='*60}\n")
        
        success_count = sum(1 for _, status, _ in results if "✅" in status)
        error_count = len(results) - success_count
        
        print(f"Всего протестировано: {len(results)}")
        print(f"✅ Успешно: {success_count}")
        print(f"❌ Ошибок: {error_count}")
        print(f"📈 Процент успеха: {(success_count/len(results)*100):.1f}%")
        
        print(f"\n📋 Детали:\n")
        for username, status, path in results:
            print(f"  @{username:30s} {status}")
            if path:
                print(f"    └─ {path}")
        
        print(f"\n{'='*60}\n")
        
        session.close()
        
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(auto_test())
    except KeyboardInterrupt:
        print("\n\n⚠️ Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

