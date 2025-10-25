#!/usr/bin/env python3
"""
Тест клавиатур с режимом api-v2.
"""

import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.join(os.path.dirname(__file__), 'project'))

from project.keyboards import admin_verify_mode_selection_kb, verify_mode_selection_kb

def test_keyboards():
    """Тест клавиатур с режимом api-v2"""
    
    print("🔧 Тестирование клавиатур с режимом api-v2...")
    
    # Тест админ-клавиатуры
    print("\n📋 Админ-клавиатура (admin_verify_mode_selection_kb):")
    admin_kb = admin_verify_mode_selection_kb("api+instagram")
    print("Режимы в админ-клавиатуре:")
    for button_row in admin_kb["inline_keyboard"]:
        for button in button_row:
            print(f"  - {button['text']} -> {button['callback_data']}")
    
    # Проверяем, есть ли api-v2 в админ-клавиатуре
    admin_modes = [button['callback_data'].split(':')[1] for button_row in admin_kb["inline_keyboard"] for button in button_row]
    if "api-v2" in admin_modes:
        print("✅ Режим api-v2 найден в админ-клавиатуре!")
    else:
        print("❌ Режим api-v2 НЕ найден в админ-клавиатуре!")
    
    # Тест пользовательской клавиатуры
    print("\n📋 Пользовательская клавиатура (verify_mode_selection_kb):")
    user_kb = verify_mode_selection_kb("api+instagram")
    print("Режимы в пользовательской клавиатуре:")
    for button_row in user_kb["inline_keyboard"]:
        for button in button_row:
            print(f"  - {button['text']} -> {button['callback_data']}")
    
    # Проверяем, есть ли api-v2 в пользовательской клавиатуре
    user_modes = []
    for button_row in user_kb["inline_keyboard"]:
        for button in button_row:
            if ':' in button['callback_data']:
                user_modes.append(button['callback_data'].split(':')[1])
    
    if "api-v2" in user_modes:
        print("✅ Режим api-v2 найден в пользовательской клавиатуре!")
    else:
        print("❌ Режим api-v2 НЕ найден в пользовательской клавиатуре!")
    
    print(f"\n🎯 Итого:")
    print(f"  - Админ-клавиатура: {'✅' if 'api-v2' in admin_modes else '❌'}")
    print(f"  - Пользовательская клавиатура: {'✅' if 'api-v2' in user_modes else '❌'}")

if __name__ == "__main__":
    test_keyboards()
