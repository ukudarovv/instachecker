#!/usr/bin/env python3
"""
Быстрая проверка Instagram аккаунта с обходом 403 ошибок.

Использование:
    python quick_check.py username
    python quick_check.py username --retries 3
    python quick_check.py username --method quick
    python quick_check.py username --verbose
"""

import asyncio
import sys
import argparse
from project.services.instagram_bypass import check_account_with_bypass, InstagramBypass


def print_result(result):
    """Красивый вывод результата"""
    print("\n" + "="*60)
    print("📊 РЕЗУЛЬТАТ ПРОВЕРКИ")
    print("="*60)
    
    username = result['username']
    exists = result['exists']
    error = result['error']
    
    # Статус
    if exists is True:
        print(f"✅ Аккаунт @{username} НАЙДЕН")
    elif exists is False:
        print(f"❌ Аккаунт @{username} НЕ НАЙДЕН")
    else:
        print(f"⚠️ Не удалось определить статус @{username}")
    
    # Детали
    print(f"\nUsername:       {username}")
    print(f"Exists:         {exists}")
    print(f"Checked via:    {result['checked_via']}")
    
    if error:
        print(f"Error:          {error}")
    
    if result.get('bypass_methods_used'):
        print(f"Methods used:   {len(result['bypass_methods_used'])}")
    
    print("="*60 + "\n")


async def quick_check_cli(username, retries=2, method=None, verbose=False):
    """
    CLI интерфейс для быстрой проверки
    
    Args:
        username: Instagram username
        retries: Количество попыток (1-3)
        method: Конкретный метод или None для всех
        verbose: Подробный вывод
    """
    if not verbose:
        # Отключаем детальные логи
        import logging
        logging.getLogger().setLevel(logging.ERROR)
    
    print(f"\n{'='*60}")
    print(f"🔍 Проверка @{username}")
    print(f"{'='*60}")
    print(f"Max retries: {retries}")
    print(f"Method: {method or 'all'}")
    print(f"Verbose: {verbose}")
    print("="*60 + "\n")
    
    if method:
        # Использование конкретного метода
        bypass = InstagramBypass()
        
        print(f"[INFO] Использование метода: {method}\n")
        
        if method == "quick":
            result_value = bypass.quick_instagram_check(username)
        elif method == "api":
            result_value = bypass.check_profile_multiple_endpoints(username)
        elif method == "mobile":
            result_value = bypass.check_mobile_endpoints(username)
        elif method == "public":
            result_value = bypass.check_public_sources(username)
        elif method == "mobile_emulation":
            result_value = bypass.check_with_mobile_emulation(username)
        else:
            print(f"❌ Неизвестный метод: {method}")
            print("Доступные методы: quick, api, mobile, public, mobile_emulation")
            return
        
        result = {
            "username": username,
            "exists": result_value,
            "error": None if result_value is not None else f"Метод {method} не сработал",
            "checked_via": f"method_{method}",
            "bypass_methods_used": [method]
        }
    else:
        # Использование всех методов
        result = await check_account_with_bypass(username, max_retries=retries)
    
    print_result(result)
    
    return result


def main():
    """Главная функция CLI"""
    parser = argparse.ArgumentParser(
        description='🛡️ Быстрая проверка Instagram аккаунта с обходом 403 ошибок',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python quick_check.py cristiano
  python quick_check.py username --retries 3
  python quick_check.py username --method quick
  python quick_check.py username --verbose
  python quick_check.py username --method api --verbose

Доступные методы:
  quick           - Быстрая проверка с мобильными заголовками (1-2s)
  api             - API endpoints (2-5s)
  mobile          - Мобильные API endpoints (2-5s)
  public          - Публичные источники (10-15s)
  mobile_emulation - Мобильная эмуляция (15-25s)
  
  (По умолчанию используются все методы последовательно)
        """
    )
    
    parser.add_argument(
        'username',
        help='Instagram username для проверки'
    )
    
    parser.add_argument(
        '-r', '--retries',
        type=int,
        default=2,
        choices=[1, 2, 3],
        help='Количество попыток (1-3). По умолчанию: 2'
    )
    
    parser.add_argument(
        '-m', '--method',
        type=str,
        choices=['quick', 'api', 'mobile', 'public', 'mobile_emulation'],
        help='Использовать конкретный метод вместо всех'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Подробный вывод'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Instagram 403 Bypass v2.0'
    )
    
    args = parser.parse_args()
    
    # Баннер
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║              🛡️  INSTAGRAM 403 BYPASS - БЫСТРАЯ ПРОВЕРКА  🛡️                 ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Запуск
    try:
        result = asyncio.run(quick_check_cli(
            username=args.username,
            retries=args.retries,
            method=args.method,
            verbose=args.verbose
        ))
        
        # Exit code
        if result['exists'] is True:
            sys.exit(0)  # Найден
        elif result['exists'] is False:
            sys.exit(1)  # Не найден
        else:
            sys.exit(2)  # Ошибка
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Прервано пользователем")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()

