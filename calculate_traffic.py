"""
Калькулятор потребления трафика для автопроверки.
Расчет на основе тестовых данных.
"""

# Средние значения из реальных измерений (после оптимизации)
# max_attempts = 1 (одна попытка вместо трех)
AVG_TRAFFIC_ACTIVE = 5000  # bytes (~5 KB) - API check + screenshot
AVG_TRAFFIC_INACTIVE = 1900  # bytes (~1.9 KB) - API check only (1 attempt)

def format_bytes(bytes_count):
    """Форматирование размера."""
    if bytes_count < 1024:
        return f"{bytes_count} B"
    elif bytes_count < 1024 * 1024:
        return f"{bytes_count / 1024:.2f} KB"
    elif bytes_count < 1024 * 1024 * 1024:
        return f"{bytes_count / (1024 * 1024):.2f} MB"
    else:
        return f"{bytes_count / (1024 * 1024 * 1024):.2f} GB"


def calculate_traffic(
    num_accounts=10,
    interval_minutes=2,
    active_ratio=0.5,  # 50% аккаунтов активны
    hours=None,
    days=None,
    months=None
):
    """
    Рассчитать потребление трафика.
    
    Args:
        num_accounts: Количество аккаунтов
        interval_minutes: Интервал проверки в минутах
        active_ratio: Доля активных аккаунтов (0.0 - 1.0)
        hours/days/months: Период для расчета
    """
    # Количество активных и неактивных
    active_accounts = int(num_accounts * active_ratio)
    inactive_accounts = num_accounts - active_accounts
    
    # Трафик за одну проверку всех аккаунтов
    traffic_per_check = (active_accounts * AVG_TRAFFIC_ACTIVE + 
                         inactive_accounts * AVG_TRAFFIC_INACTIVE)
    
    # Количество проверок в зависимости от периода
    checks_per_hour = 60 / interval_minutes
    
    results = []
    
    # Расчет за час
    if hours or not (days or months):
        period_hours = hours or 1
        total_checks = checks_per_hour * period_hours
        total_traffic = traffic_per_check * total_checks
        
        results.append({
            'period': f"{period_hours} час(ов)",
            'checks': int(total_checks),
            'traffic': total_traffic
        })
    
    # Расчет за день
    if days or not (hours or months):
        period_days = days or 1
        total_checks = checks_per_hour * 24 * period_days
        total_traffic = traffic_per_check * total_checks
        
        results.append({
            'period': f"{period_days} день(дней)",
            'checks': int(total_checks),
            'traffic': total_traffic
        })
    
    # Расчет за месяц
    if months:
        period_months = months
        total_checks = checks_per_hour * 24 * 30 * period_months
        total_traffic = traffic_per_check * total_checks
        
        results.append({
            'period': f"{period_months} месяц(ев)",
            'checks': int(total_checks),
            'traffic': total_traffic
        })
    
    return {
        'accounts': num_accounts,
        'active_accounts': active_accounts,
        'inactive_accounts': inactive_accounts,
        'interval_minutes': interval_minutes,
        'traffic_per_check': traffic_per_check,
        'checks_per_hour': checks_per_hour,
        'results': results
    }


def print_report(calc):
    """Вывести отчет о расчете."""
    print("=" * 70)
    print("📊 РАСЧЕТ ПОТРЕБЛЕНИЯ ТРАФИКА АВТОПРОВЕРКИ")
    print("=" * 70)
    
    print(f"\n📋 Параметры:")
    print(f"  • Всего аккаунтов: {calc['accounts']}")
    print(f"    - Активных: {calc['active_accounts']} (~{AVG_TRAFFIC_ACTIVE/1024:.2f} KB на проверку)")
    print(f"    - Неактивных: {calc['inactive_accounts']} (~{AVG_TRAFFIC_INACTIVE/1024:.2f} KB на проверку)")
    print(f"  • Интервал проверки: {calc['interval_minutes']} минут")
    print(f"  • Проверок в час: {calc['checks_per_hour']:.1f}")
    print(f"  • Трафик за одну проверку всех аккаунтов: {format_bytes(int(calc['traffic_per_check']))}")
    
    print(f"\n📊 Потребление трафика:")
    for result in calc['results']:
        print(f"\n  ⏱️  За {result['period']}:")
        print(f"    • Проверок: {result['checks']:,}")
        print(f"    • Трафик: {format_bytes(int(result['traffic']))}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("СЦЕНАРИЙ 1: 10 аккаунтов, проверка каждые 2 минуты")
    print("Предположение: 50% аккаунтов активны, 50% неактивны")
    print("="*70)
    
    calc = calculate_traffic(
        num_accounts=10,
        interval_minutes=2,
        active_ratio=0.5,
        hours=1,
        days=1,
        months=1
    )
    print_report(calc)
    
    print("\n" + "="*70)
    print("СЦЕНАРИЙ 2: Все 10 аккаунтов активны (худший случай)")
    print("="*70)
    
    calc = calculate_traffic(
        num_accounts=10,
        interval_minutes=2,
        active_ratio=1.0,  # 100% активны
        hours=1,
        days=1,
        months=1
    )
    print_report(calc)
    
    print("\n" + "="*70)
    print("СЦЕНАРИЙ 3: Все 10 аккаунтов неактивны (лучший случай)")
    print("="*70)
    
    calc = calculate_traffic(
        num_accounts=10,
        interval_minutes=2,
        active_ratio=0.0,  # 0% активны
        hours=1,
        days=1,
        months=1
    )
    print_report(calc)
    
    print("\n" + "="*70)
    print("ДОПОЛНИТЕЛЬНЫЕ СЦЕНАРИИ")
    print("="*70)
    
    # Разные интервалы
    print("\n📌 Влияние интервала (10 аккаунтов, 50% активны, за 1 день):")
    for interval in [1, 2, 5, 10, 15, 30, 60]:
        calc = calculate_traffic(
            num_accounts=10,
            interval_minutes=interval,
            active_ratio=0.5,
            days=1
        )
        traffic_day = calc['results'][0]['traffic']
        print(f"  • Каждые {interval:2d} мин: {format_bytes(int(traffic_day)):>12} в день")
    
    print("\n")

