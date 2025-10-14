#!/usr/bin/env python3
"""
Конвертер cookies из формата расширения браузера в формат бота.

Расширения браузеров (EditThisCookie, Cookie-Editor) экспортируют cookies
в формате с дополнительными полями. Этот скрипт конвертирует их в формат,
понятный боту InstaChecker.
"""

import json
import sys
from typing import List, Dict, Any


def convert_extension_cookies(extension_cookies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Конвертирует cookies из формата расширения в формат бота.
    
    Args:
        extension_cookies: Cookies в формате расширения браузера
        
    Returns:
        Cookies в формате бота
    """
    bot_cookies = []
    
    for cookie in extension_cookies:
        # Создаем cookie для бота
        bot_cookie = {
            "name": cookie["name"],
            "value": cookie["value"],
            "domain": cookie.get("domain", ".instagram.com"),
            "path": cookie.get("path", "/")
        }
        
        # Добавляем expires если есть expirationDate
        if "expirationDate" in cookie and cookie["expirationDate"]:
            bot_cookie["expires"] = cookie["expirationDate"]
        
        # Добавляем флаги безопасности
        if cookie.get("httpOnly", False):
            bot_cookie["httpOnly"] = True
            
        if cookie.get("secure", False):
            bot_cookie["secure"] = True
            
        if "sameSite" in cookie and cookie["sameSite"]:
            # Конвертируем sameSite значения
            same_site = cookie["sameSite"]
            if same_site == "no_restriction":
                bot_cookie["sameSite"] = "None"
            elif same_site in ["lax", "strict"]:
                bot_cookie["sameSite"] = same_site.capitalize()
            elif same_site == "unspecified":
                # Опускаем unspecified
                pass
            else:
                bot_cookie["sameSite"] = same_site
        
        bot_cookies.append(bot_cookie)
    
    return bot_cookies


def main():
    """Основная функция."""
    print("=" * 60)
    print("🔄 Конвертер cookies из расширения браузера")
    print("=" * 60)
    print()
    
    if len(sys.argv) > 1:
        # Читаем из файла
        file_path = sys.argv[1]
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                extension_cookies = json.load(f)
        except FileNotFoundError:
            print(f"❌ Файл не найден: {file_path}")
            return 1
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка JSON: {e}")
            return 1
    else:
        # Интерактивный режим
        print("Вставьте JSON с cookies из расширения браузера и нажмите Enter два раза:")
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
        
        cookies_text = '\n'.join(lines)
        
        try:
            extension_cookies = json.loads(cookies_text)
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка JSON: {e}")
            return 1
    
    # Проверяем что это массив
    if not isinstance(extension_cookies, list):
        print("❌ Cookies должны быть массивом")
        return 1
    
    print(f"📦 Получено cookies из расширения: {len(extension_cookies)}")
    
    # Конвертируем
    try:
        bot_cookies = convert_extension_cookies(extension_cookies)
    except Exception as e:
        print(f"❌ Ошибка конвертации: {e}")
        return 1
    
    # Проверяем sessionid
    has_sessionid = any(c.get('name') == 'sessionid' for c in bot_cookies)
    
    print("\n" + "=" * 60)
    print("🔍 Результаты конвертации")
    print("=" * 60)
    print(f"\n📊 Конвертировано cookies: {len(bot_cookies)}")
    
    if has_sessionid:
        print("✅ sessionid найден - отлично!")
    else:
        print("⚠️ sessionid НЕ НАЙДЕН!")
        print("   Возможные причины:")
        print("   1. Вы не полностью вошли в Instagram")
        print("   2. sessionid имеет особые настройки")
        print("   ")
        print("   РЕШЕНИЕ:")
        print("   1. Перезайдите в Instagram (выйти и войти)")
        print("   2. Экспортируйте cookies заново")
        print("   3. Попробуйте другой браузер")
    
    # Показываем список cookies
    print("\n📋 Список cookies:")
    for i, cookie in enumerate(bot_cookies, 1):
        value_preview = cookie['value'][:30] + '...' if len(cookie['value']) > 30 else cookie['value']
        print(f"  {i}. {cookie['name']}: {value_preview}")
    
    # Конвертируем в JSON
    result_json = json.dumps(bot_cookies, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    if has_sessionid:
        print("✅ ГОТОВО К ИСПОЛЬЗОВАНИЮ")
    else:
        print("⚠️ ВНИМАНИЕ: sessionid отсутствует!")
    print("=" * 60)
    print()
    print("📋 Скопируйте этот JSON и вставьте в бот:")
    print("-" * 60)
    print(result_json)
    print("-" * 60)
    
    # Сохраняем в файл
    output_file = "cookies_converted_for_bot.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result_json)
        print(f"\n💾 Также сохранено в файл: {output_file}")
    except Exception as e:
        print(f"\n⚠️ Не удалось сохранить в файл: {e}")
    
    print()
    print("👉 Следующие шаги:")
    print("  1. Скопируйте JSON выше")
    print("  2. Откройте бот в Telegram")
    print("  3. Instagram → Добавить IG-сессию → Импорт cookies")
    print("  4. Вставьте cookies в бот")
    
    if not has_sessionid:
        print("\n⚠️ ВАЖНО: Если sessionid отсутствует:")
        print("  → Перезайдите в Instagram и экспортируйте заново")
        print("  → Или используйте другие cookies с sessionid")
    
    return 0 if has_sessionid else 1


if __name__ == "__main__":
    sys.exit(main())
