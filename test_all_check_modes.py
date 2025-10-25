#!/usr/bin/env python3
"""
🔥 Тестирование всех режимов проверки с улучшенной гибридной системой
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from project.services.instagram_hybrid_proxy import check_account_with_hybrid_proxy
    from project.services.hybrid_checker import check_account_hybrid_enhanced
    from project.services.ig_simple_checker import check_account_with_enhanced_hybrid
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Убедитесь, что вы находитесь в корневой директории проекта")
    sys.exit(1)


async def test_all_modes(username: str, proxy: str = None):
    """Тестирование всех режимов проверки."""
    
    print("╔═══════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                               ║")
    print("║              🔥 ТЕСТИРОВАНИЕ ВСЕХ РЕЖИМОВ ПРОВЕРКИ  🔥                      ║")
    print("║                                                                               ║")
    print("╚═══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    print("=" * 80)
    print(f"🔍 Тестирование всех режимов проверки для @{username}")
    if proxy:
        if '@' in proxy:
            proxy_display = proxy.split('@')[0].split(':')[0] + ':***@' + proxy.split('@')[1]
        else:
            proxy_display = proxy
        print(f"🔗 Прокси: {proxy_display}")
    else:
        print("🔗 Прокси: Не указан")
    print("=" * 80)
    print()
    
    # Создаем пути для скриншотов
    screenshot_dir = "screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    results = {}
    
    # Тест 1: Прямая гибридная система
    print("🧪 ТЕСТ 1: Прямая гибридная система")
    print("-" * 50)
    
    try:
        screenshot_path_1 = os.path.join(screenshot_dir, f"direct_hybrid_{username}_{timestamp}.png")
        
        result_1 = await check_account_with_hybrid_proxy(
            username=username,
            screenshot_path=screenshot_path_1,
            headless=True,
            max_retries=2,
            proxy=proxy
        )
        
        results["direct_hybrid"] = result_1
        print(f"✅ Прямая гибридная система: {result_1.get('exists')}")
        print(f"📸 Скриншот: {result_1.get('screenshot_created', False)}")
        
    except Exception as e:
        print(f"❌ Ошибка прямой гибридной системы: {e}")
        results["direct_hybrid"] = {"error": str(e)}
    
    print()
    
    # Тест 2: Hybrid Checker Enhanced
    print("🧪 ТЕСТ 2: Hybrid Checker Enhanced")
    print("-" * 50)
    
    try:
        # Создаем мок сессию для тестирования
        class MockSession:
            def query(self, model):
                return MockQuery()
        
        class MockQuery:
            def filter(self, condition):
                return self
            def first(self):
                if proxy and '@' in proxy:
                    # Парсим прокси для мока
                    auth_part, server_part = proxy.split('@')
                    username_part, password_part = auth_part.split(':')
                    host, port = server_part.split(':')
                    
                    class MockProxy:
                        def __init__(self):
                            self.username = username_part
                            self.password = password_part
                            self.host = host
                            self.port = int(port)
                            self.is_active = True
                    
                    return MockProxy()
                return None
        
        mock_session = MockSession()
        
        result_2 = await check_account_hybrid_enhanced(
            session=mock_session,
            user_id=12345,
            username=username,
            verify_mode="enhanced_hybrid"
        )
        
        results["hybrid_checker_enhanced"] = result_2
        print(f"✅ Hybrid Checker Enhanced: {result_2.get('exists')}")
        print(f"📸 Скриншот: {result_2.get('screenshot_created', False)}")
        
    except Exception as e:
        print(f"❌ Ошибка Hybrid Checker Enhanced: {e}")
        results["hybrid_checker_enhanced"] = {"error": str(e)}
    
    print()
    
    # Тест 3: IG Simple Checker Enhanced
    print("🧪 ТЕСТ 3: IG Simple Checker Enhanced")
    print("-" * 50)
    
    try:
        screenshot_path_3 = os.path.join(screenshot_dir, f"ig_simple_enhanced_{username}_{timestamp}.png")
        
        result_3 = await check_account_with_enhanced_hybrid(
            username=username,
            screenshot_path=screenshot_path_3,
            headless=True,
            max_retries=2,
            proxy=proxy
        )
        
        results["ig_simple_enhanced"] = result_3
        print(f"✅ IG Simple Checker Enhanced: {result_3.get('exists')}")
        print(f"📸 Скриншот: {result_3.get('screenshot_created', False)}")
        
    except Exception as e:
        print(f"❌ Ошибка IG Simple Checker Enhanced: {e}")
        results["ig_simple_enhanced"] = {"error": str(e)}
    
    print()
    
    # Результаты
    print("=" * 80)
    print("📊 РЕЗУЛЬТАТЫ ВСЕХ ТЕСТОВ")
    print("=" * 80)
    
    for test_name, result in results.items():
        print(f"\n🎯 {test_name.upper().replace('_', ' ')}:")
        
        if "error" in result:
            print(f"❌ Ошибка: {result['error']}")
        else:
            print(f"✅ Профиль существует: {result.get('exists')}")
            print(f"📸 Скриншот создан: {result.get('screenshot_created', False)}")
            print(f"🔗 Прокси использован: {result.get('proxy_used', False)}")
            print(f"📡 API метод: {result.get('api_method', 'N/A')}")
            print(f"🌐 Проверено через: {result.get('checked_via', 'N/A')}")
            
            if result.get("screenshot_path"):
                if os.path.exists(result["screenshot_path"]):
                    size = os.path.getsize(result["screenshot_path"])
                    print(f"📁 Скриншот: {result['screenshot_path']} ({size} байт)")
                else:
                    print(f"❌ Скриншот не найден: {result['screenshot_path']}")
    
    print()
    print("=" * 80)
    print("🎉 ТЕСТИРОВАНИЕ ВСЕХ РЕЖИМОВ ЗАВЕРШЕНО!")
    print("=" * 80)
    
    # Статистика
    successful_tests = sum(1 for result in results.values() if "error" not in result)
    total_tests = len(results)
    
    print(f"\n📈 СТАТИСТИКА:")
    print(f"✅ Успешных тестов: {successful_tests}/{total_tests}")
    print(f"📸 Скриншотов создано: {sum(1 for result in results.values() if result.get('screenshot_created', False))}")
    print(f"🔗 Прокси использован: {sum(1 for result in results.values() if result.get('proxy_used', False))}")
    
    return results


def main():
    """Главная функция."""
    if len(sys.argv) < 2:
        print("Использование: python test_all_check_modes.py <username> [proxy]")
        print("\nПримеры:")
        print("  # Без прокси:")
        print("  python test_all_check_modes.py gid_halal")
        print("\n  # С прокси:")
        print("  python test_all_check_modes.py gid_halal http://user:pass@host:port")
        print("  python test_all_check_modes.py gid_halal http://aiiigauk:pi8vftb70eic@142.111.48.253:7030")
        print("\n💡 Тестируемые режимы:")
        print("  1. Прямая гибридная система (instagram_hybrid_proxy)")
        print("  2. Hybrid Checker Enhanced (hybrid_checker)")
        print("  3. IG Simple Checker Enhanced (ig_simple_checker)")
        print("\n🔥 Все режимы используют улучшенную гибридную систему!")
        sys.exit(1)
    
    username = sys.argv[1]
    proxy = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"🚀 Запуск тестирования всех режимов проверки для @{username}")
    if proxy:
        print(f"🔗 Прокси будет использован во всех режимах")
    print(f"🔥 Все режимы используют улучшенную гибридную систему")
    print()
    
    # Запуск асинхронного тестирования
    results = asyncio.run(test_all_modes(username, proxy))
    
    # Код возврата
    successful_tests = sum(1 for result in results.values() if "error" not in result)
    if successful_tests == len(results):
        sys.exit(0)
    elif successful_tests > 0:
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()



