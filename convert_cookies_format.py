#!/usr/bin/env python3
"""
Скрипт для конвертации cookies из формата объекта в формат массива для бота.

Использование:
    python convert_cookies_format.py

Или импортируйте функцию:
    from convert_cookies_format import convert_cookies
    result = convert_cookies(your_cookies_object)
"""

import json
import sys


def convert_cookies(cookies_input):
    """
    Конвертирует cookies из формата объекта в формат массива.
    
    Args:
        cookies_input: dict или str - cookies в формате объекта
        
    Returns:
        list - cookies в формате массива для бота
    """
    # Если строка - парсим JSON
    if isinstance(cookies_input, str):
        try:
            cookies_input = json.loads(cookies_input)
        except json.JSONDecodeError as e:
            raise ValueError(f"Неверный JSON: {e}")
    
    # Если уже массив - возвращаем как есть (возможно уже правильный формат)
    if isinstance(cookies_input, list):
        print("⚠️ Cookies уже в формате массива")
        return cookies_input
    
    # Если не словарь - ошибка
    if not isinstance(cookies_input, dict):
        raise ValueError(f"Cookies должны быть объектом или массивом, получен {type(cookies_input).__name__}")
    
    # Конвертируем из объекта в массив
    cookies_array = []
    for name, value in cookies_input.items():
        cookie_obj = {
            "name": name,
            "value": str(value),  # Конвертируем в строку на всякий случай
            "domain": ".instagram.com",
            "path": "/"
        }
        cookies_array.append(cookie_obj)
    
    return cookies_array


def main():
    """Основная функция для CLI использования."""
    print("=" * 60)
    print("🍪 Конвертер формата cookies для InstaChecker")
    print("=" * 60)
    print()
    print("Вставьте ваши cookies в формате JSON и нажмите Enter два раза:")
    print("(можно вставить как объект {} или массив [])")
    print()
    
    # Читаем многострочный ввод
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
        print("❌ Ошибка: cookies не введены")
        return 1
    
    cookies_text = '\n'.join(lines)
    
    try:
        # Конвертируем cookies
        result = convert_cookies(cookies_text)
        
        # Проверяем наличие sessionid
        has_sessionid = any(c.get('name') == 'sessionid' for c in result)
        
        print()
        print("=" * 60)
        print("✅ Конвертация завершена!")
        print("=" * 60)
        print()
        print(f"📊 Всего cookies: {len(result)}")
        
        if has_sessionid:
            print("✅ sessionid найден - всё отлично!")
        else:
            print("⚠️ ВНИМАНИЕ: sessionid НЕ найден!")
            print("   Без sessionid вход в Instagram НЕ СРАБОТАЕТ")
        
        print()
        print("📋 Скопируйте этот текст и отправьте в бот:")
        print("-" * 60)
        
        # Выводим результат в красивом формате
        result_json = json.dumps(result, ensure_ascii=False, indent=2)
        print(result_json)
        
        print("-" * 60)
        print()
        
        # Сохраняем в файл для удобства
        output_file = "cookies_converted.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result_json)
        
        print(f"💾 Также сохранено в файл: {output_file}")
        print()
        
        return 0
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Ошибка: {e}")
        print("=" * 60)
        print()
        print("Проверьте формат введенных данных")
        return 1


if __name__ == "__main__":
    sys.exit(main())

