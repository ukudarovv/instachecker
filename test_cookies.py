#!/usr/bin/env python3
"""
Тестовый скрипт для проверки валидности Instagram cookies.

Использование:
    python test_cookies.py cookies.json
    
Или интерактивно:
    python test_cookies.py
"""

import json
import sys
from typing import List, Dict, Any


def validate_cookies(cookies: List[Dict[str, Any]]) -> tuple[bool, str, List[str]]:
    """
    Валидация cookies Instagram.
    
    Returns:
        (is_valid, message, warnings)
    """
    warnings = []
    
    # Check 1: Must be a list
    if not isinstance(cookies, list):
        return False, f"❌ Cookies должны быть массивом (list), получен {type(cookies).__name__}", warnings
    
    if len(cookies) == 0:
        return False, "❌ Список cookies пустой", warnings
    
    # Check 2: Each cookie must be a dict with name and value
    for i, cookie in enumerate(cookies):
        if not isinstance(cookie, dict):
            return False, f"❌ Cookie #{i+1} должен быть объектом (dict), получен {type(cookie).__name__}", warnings
        
        if "name" not in cookie:
            return False, f"❌ Cookie #{i+1} не содержит поле 'name'", warnings
        
        if "value" not in cookie:
            return False, f"❌ Cookie #{i+1} (name='{cookie.get('name', '?')}') не содержит поле 'value'", warnings
        
        # Check for domain and path
        if "domain" not in cookie:
            warnings.append(f"⚠️ Cookie '{cookie['name']}' не содержит 'domain' (будет использовано '.instagram.com')")
        
        if "path" not in cookie:
            warnings.append(f"⚠️ Cookie '{cookie['name']}' не содержит 'path' (будет использовано '/')")
    
    # Check 3: Must have sessionid
    has_sessionid = any(c.get('name') == 'sessionid' for c in cookies)
    if not has_sessionid:
        return False, "❌ КРИТИЧЕСКАЯ ОШИБКА: Отсутствует cookie 'sessionid'!\n   Без sessionid вход в Instagram НЕ РАБОТАЕТ!", warnings
    
    # Check 4: Recommended cookies
    recommended_cookies = ['sessionid', 'csrftoken', 'ds_user_id', 'mid']
    missing_recommended = []
    
    for rec_cookie in recommended_cookies:
        if not any(c.get('name') == rec_cookie for c in cookies):
            missing_recommended.append(rec_cookie)
    
    if missing_recommended:
        warnings.append(f"⚠️ Отсутствуют рекомендуемые cookies: {', '.join(missing_recommended)}")
    
    # Check 5: Check for suspicious values
    sessionid_cookie = next((c for c in cookies if c.get('name') == 'sessionid'), None)
    if sessionid_cookie:
        sessionid_value = sessionid_cookie.get('value', '')
        if len(sessionid_value) < 20:
            warnings.append(f"⚠️ sessionid выглядит подозрительно коротким (длина: {len(sessionid_value)})")
        if not '%3A' in sessionid_value:
            warnings.append("⚠️ sessionid не содержит '%3A' - возможно неверное значение")
    
    return True, "✅ Cookies валидны!", warnings


def print_cookies_info(cookies: List[Dict[str, Any]]) -> None:
    """Печать информации о cookies."""
    print("\n" + "=" * 60)
    print("📊 Информация о cookies")
    print("=" * 60)
    print(f"\n📦 Всего cookies: {len(cookies)}\n")
    
    # Group cookies by importance
    critical = []
    recommended = []
    optional = []
    
    critical_names = ['sessionid']
    recommended_names = ['csrftoken', 'ds_user_id', 'mid']
    
    for cookie in cookies:
        name = cookie.get('name', 'unknown')
        if name in critical_names:
            critical.append(cookie)
        elif name in recommended_names:
            recommended.append(cookie)
        else:
            optional.append(cookie)
    
    # Print critical cookies
    if critical:
        print("🔴 Критические cookies (обязательные):")
        for c in critical:
            value_preview = c.get('value', '')[:30] + '...' if len(c.get('value', '')) > 30 else c.get('value', '')
            print(f"  ✅ {c['name']}: {value_preview}")
        print()
    
    # Print recommended cookies
    if recommended:
        print("🟡 Рекомендуемые cookies:")
        for c in recommended:
            value_preview = c.get('value', '')[:30] + '...' if len(c.get('value', '')) > 30 else c.get('value', '')
            print(f"  ✅ {c['name']}: {value_preview}")
        print()
    
    # Print optional cookies
    if optional:
        print(f"🟢 Дополнительные cookies ({len(optional)}):")
        for c in optional:
            value_preview = c.get('value', '')[:20] + '...' if len(c.get('value', '')) > 20 else c.get('value', '')
            print(f"  • {c['name']}: {value_preview}")
        print()


def main():
    """Основная функция."""
    print("=" * 60)
    print("🍪 Instagram Cookies Validator")
    print("=" * 60)
    print()
    
    # Check if file is provided as argument
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                cookies_json = f.read()
        except FileNotFoundError:
            print(f"❌ Файл не найден: {file_path}")
            return 1
        except Exception as e:
            print(f"❌ Ошибка чтения файла: {e}")
            return 1
    else:
        # Interactive mode
        print("Вставьте JSON с cookies и нажмите Enter два раза:")
        print("(или укажите путь к файлу как аргумент)")
        print()
        
        lines = []
        empty_count = 0
        while True:
            try:
                line = input()
                if not line.strip():
                    empty_count += 1
                    if empty_count >= 2:
                        break
                else:
                    empty_count = 0
                    lines.append(line)
            except EOFError:
                break
        
        if not lines:
            print("❌ Cookies не введены")
            return 1
        
        cookies_json = '\n'.join(lines)
    
    # Parse JSON
    try:
        cookies = json.loads(cookies_json)
    except json.JSONDecodeError as e:
        print("=" * 60)
        print("❌ ОШИБКА: Неверный JSON формат")
        print("=" * 60)
        print(f"\n{str(e)}\n")
        print("Убедитесь что:")
        print("• JSON валиден")
        print("• Начинается с [ и заканчивается ]")
        print("• Все кавычки правильно закрыты")
        print()
        return 1
    
    # Validate cookies
    is_valid, message, warnings = validate_cookies(cookies)
    
    # Print results
    print("\n" + "=" * 60)
    print("🔍 Результаты валидации")
    print("=" * 60)
    print()
    print(message)
    print()
    
    if warnings:
        print("⚠️  Предупреждения:")
        for warning in warnings:
            print(f"  {warning}")
        print()
    
    if is_valid:
        print_cookies_info(cookies)
        
        print("=" * 60)
        print("✅ ГОТОВО К ИСПОЛЬЗОВАНИЮ")
        print("=" * 60)
        print()
        print("👉 Следующие шаги:")
        print("  1. Скопируйте эти cookies")
        print("  2. Откройте бот в Telegram")
        print("  3. Выберите: Instagram → Добавить IG-сессию → Импорт cookies")
        print("  4. Вставьте cookies в бот")
        print()
        return 0
    else:
        print("=" * 60)
        print("❌ COOKIES НЕ ВАЛИДНЫ")
        print("=" * 60)
        print()
        print("📖 Как исправить:")
        print("  1. Убедитесь что вы вошли в Instagram в браузере")
        print("  2. Используйте скрипт для экспорта cookies (см. COOKIES_QUICKSTART.md)")
        print("  3. Или используйте расширение EditThisCookie")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())

