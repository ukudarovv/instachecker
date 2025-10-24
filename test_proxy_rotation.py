"""
🧪 Тест ротации прокси

Этот скрипт показывает, что при каждой проверке выбирается РАЗНЫЙ прокси.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from project.database import get_session_factory
from project.services.proxy_manager import ProxyManager


def test_proxy_rotation(user_id: int, iterations: int = 10):
    """
    Тест ротации прокси
    
    Args:
        user_id: ID пользователя
        iterations: Количество итераций
    """
    print(f"\n{'='*70}")
    print(f"🧪 ТЕСТ РОТАЦИИ ПРОКСИ (user_id={user_id})")
    print(f"{'='*70}\n")
    
    SessionLocal = get_session_factory()
    
    selected_proxies = []
    
    with SessionLocal() as session:
        manager = ProxyManager(session)
        
        # Показать статистику ДО
        stats = manager.get_proxy_stats(user_id)
        print(f"📊 Статистика ДО тестирования:")
        print(f"   Всего прокси: {stats['total']}")
        print(f"   Активных: {stats['active']}")
        print(f"   Success rate: {stats['success_rate']}%")
        print(f"\n{'='*70}\n")
        
        # Симуляция N проверок
        print(f"🔄 Симулирую {iterations} проверок...\n")
        
        for i in range(iterations):
            proxy = manager.get_best_proxy(user_id, strategy='adaptive')
            
            if not proxy:
                print(f"[{i+1:2d}] ❌ Нет доступных прокси!")
                break
            
            selected_proxies.append(proxy.host)
            
            # Показываем выбранный прокси
            success_rate = (proxy.success_count / proxy.used_count * 100) if proxy.used_count > 0 else 0
            print(f"[{i+1:2d}] 🔗 Выбран: {proxy.host:<25} | "
                  f"Успех: {proxy.success_count}/{proxy.used_count} ({success_rate:5.1f}%) | "
                  f"Приоритет: {proxy.priority}")
            
            # Симулируем успешную проверку (80% успеха)
            import random
            if random.random() < 0.8:
                manager.mark_success(proxy.id)
            else:
                manager.mark_failure(proxy.id, apply_cooldown=False)
        
        print(f"\n{'='*70}\n")
        
        # Анализ ротации
        unique_proxies = len(set(selected_proxies))
        total_proxies = len(selected_proxies)
        
        print(f"📊 РЕЗУЛЬТАТЫ РОТАЦИИ:")
        print(f"   Всего проверок: {total_proxies}")
        print(f"   Уникальных прокси: {unique_proxies}")
        print(f"   Ротация: {unique_proxies/total_proxies*100:.1f}%")
        
        if unique_proxies == total_proxies:
            print(f"   ✅ ОТЛИЧНО! Каждый раз новый прокси!")
        elif unique_proxies > total_proxies * 0.7:
            print(f"   ✅ ХОРОШО! Высокая ротация прокси")
        elif unique_proxies > total_proxies * 0.5:
            print(f"   ⚠️ НОРМА. Средняя ротация прокси")
        else:
            print(f"   ⚠️ Низкая ротация. Проверьте кол-во активных прокси")
        
        # Частота использования
        print(f"\n   📈 Частота использования:")
        from collections import Counter
        counter = Counter(selected_proxies)
        for proxy_host, count in counter.most_common(5):
            print(f"      {proxy_host}: {count}x")
        
        print(f"\n{'='*70}\n")
        
        # Показать статистику ПОСЛЕ
        stats_after = manager.get_proxy_stats(user_id)
        print(f"📊 Статистика ПОСЛЕ тестирования:")
        print(f"   Success rate: {stats_after['success_rate']}%")
        print(f"   Всего использований: {stats_after['total_uses']}")
        
        # Топ-5 лучших прокси
        print(f"\n🔝 Топ-5 лучших прокси:")
        best = manager.get_best_proxies(user_id, top_n=5)
        for i, proxy in enumerate(best, 1):
            print(f"   {i}. {proxy['host']:<25} | "
                  f"{proxy['success_rate']:5.1f}% | "
                  f"Использован: {proxy['used_count']}x")
        
        print(f"\n{'='*70}\n")
        print(f"✅ Тест завершен!")
        print(f"{'='*70}\n")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test proxy rotation')
    parser.add_argument('--user-id', type=int, required=True, help='User ID')
    parser.add_argument('--iterations', type=int, default=10, help='Number of iterations (default: 10)')
    
    args = parser.parse_args()
    
    test_proxy_rotation(args.user_id, args.iterations)


if __name__ == '__main__':
    main()



