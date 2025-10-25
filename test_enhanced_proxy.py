#!/usr/bin/env python3
"""
Тест улучшенного тестирования прокси.
"""

import asyncio
import os
from datetime import datetime
from project.services.enhanced_proxy_tester import (
    test_proxy_connectivity,
    test_proxy_speed,
    test_proxy_instagram_access,
    test_proxy_screenshot,
    test_proxy_comprehensive,
    format_comprehensive_results
)

# Mock Proxy class for testing
class MockProxy:
    def __init__(self, host, scheme="http", username=None, password=None):
        self.id = 1
        self.host = host
        self.scheme = scheme
        self.username = username
        self.password = password

async def test_enhanced_proxy():
    """Тест улучшенного тестирования прокси."""
    
    print("🧪 Тест улучшенного тестирования прокси")
    print("=" * 50)
    
    # Создаем тестовый прокси (без реального прокси для демонстрации)
    test_proxy = MockProxy("127.0.0.1:8080")
    test_username = "instagram"
    
    print(f"🌐 Тестируем прокси: {test_proxy.host}")
    print(f"👤 Тестовый аккаунт: @{test_username}")
    print("-" * 50)
    
    try:
        # Тест 1: Базовая связность
        print("🔗 Тест 1: Базовая связность...")
        connectivity_success, connectivity_msg, response_time = await test_proxy_connectivity(test_proxy)
        print(f"Результат: {connectivity_success}")
        print(f"Сообщение: {connectivity_msg}")
        if response_time:
            print(f"Время отклика: {response_time:.2f}s")
        print()
        
        # Тест 2: Скорость
        print("⚡ Тест 2: Скорость...")
        speed_success, speed_msg, speed_data = await test_proxy_speed(test_proxy)
        print(f"Результат: {speed_success}")
        print(f"Сообщение: {speed_msg}")
        if speed_data:
            print(f"Данные: {speed_data}")
        print()
        
        # Тест 3: Доступ к Instagram
        print("📱 Тест 3: Доступ к Instagram...")
        instagram_success, instagram_msg, profile_data = await test_proxy_instagram_access(test_proxy, test_username)
        print(f"Результат: {instagram_success}")
        print(f"Сообщение: {instagram_msg}")
        if profile_data:
            print(f"Данные профиля: {profile_data}")
        print()
        
        # Тест 4: Скриншот
        print("📸 Тест 4: Скриншот...")
        screenshot_success, screenshot_msg, screenshot_path = await test_proxy_screenshot(test_proxy, test_username)
        print(f"Результат: {screenshot_success}")
        print(f"Сообщение: {screenshot_msg}")
        if screenshot_path:
            print(f"Путь к скриншоту: {screenshot_path}")
        print()
        
        # Комплексный тест
        print("🧪 Комплексный тест...")
        comprehensive_results = await test_proxy_comprehensive(test_proxy, test_username)
        
        print("\n" + "=" * 50)
        print("📊 РЕЗУЛЬТАТЫ КОМПЛЕКСНОГО ТЕСТА:")
        print("=" * 50)
        
        # Форматируем результаты
        formatted_message = format_comprehensive_results(comprehensive_results)
        print(formatted_message)
        
        # Детальная статистика
        print("\n📈 ДЕТАЛЬНАЯ СТАТИСТИКА:")
        print(f"Общий балл: {comprehensive_results['overall_score']:.1f}%")
        print(f"Успешных тестов: {comprehensive_results['successful_tests']}/{comprehensive_results['total_tests']}")
        
        for test_name, test_result in comprehensive_results['tests'].items():
            status = "✅" if test_result['success'] else "❌"
            print(f"{status} {test_name}: {test_result['success']}")
        
        return comprehensive_results
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_multiple_proxies():
    """Тест нескольких прокси."""
    
    print("\n🧪 Тест нескольких прокси")
    print("=" * 50)
    
    # Создаем несколько тестовых прокси
    test_proxies = [
        MockProxy("127.0.0.1:8080"),
        MockProxy("127.0.0.1:8081"),
        MockProxy("127.0.0.1:8082")
    ]
    
    print(f"🌐 Тестируем {len(test_proxies)} прокси")
    print("-" * 50)
    
    try:
        from project.services.enhanced_proxy_tester import test_multiple_proxies_enhanced, format_batch_results_enhanced
        
        # Тестируем несколько прокси
        batch_results = await test_multiple_proxies_enhanced(test_proxies, "instagram")
        
        print("\n" + "=" * 50)
        print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ НЕСКОЛЬКИХ ПРОКСИ:")
        print("=" * 50)
        
        # Форматируем результаты
        formatted_message = format_batch_results_enhanced(batch_results)
        print(formatted_message)
        
        return batch_results
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании нескольких прокси: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🚀 Запуск тестов улучшенного тестирования прокси")
    print("=" * 50)
    
    # Тест одного прокси
    single_result = asyncio.run(test_enhanced_proxy())
    
    # Тест нескольких прокси
    batch_result = asyncio.run(test_multiple_proxies())
    
    print("\n" + "=" * 50)
    print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ:")
    print("=" * 50)
    
    if single_result:
        print(f"✅ Тест одного прокси: Успешно")
        print(f"📊 Общий балл: {single_result['overall_score']:.1f}%")
    else:
        print("❌ Тест одного прокси: Неудачно")
    
    if batch_result:
        print(f"✅ Тест нескольких прокси: Успешно")
        print(f"📊 Успешность: {batch_result['success_rate']:.1f}%")
    else:
        print("❌ Тест нескольких прокси: Неудачно")
