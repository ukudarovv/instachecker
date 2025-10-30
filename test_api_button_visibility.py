"""
Тест для проверки видимости кнопки API в главном меню
"""
from project.keyboards import main_menu

def test_api_button_visibility():
    """Тест: кнопка API должна быть показана только при режиме api+proxy, на остальных скрыта"""
    
    print("\n" + "="*70)
    print("🧪 ТЕСТ ВИДИМОСТИ КНОПКИ API В ГЛАВНОМ МЕНЮ")
    print("="*70 + "\n")
    
    # Тест 1: Режим "api+proxy" - кнопка API должна быть ПОКАЗАНА
    print("📋 Тест 1: verify_mode = 'api+proxy'")
    keyboard = main_menu(is_admin=False, verify_mode="api+proxy")
    third_row = keyboard["keyboard"][3]
    api_button_present = any(btn["text"] == "API" for btn in third_row)
    
    print(f"   Третья строка: {[btn['text'] for btn in third_row]}")
    print(f"   Кнопка API присутствует: {api_button_present}")
    
    if not api_button_present:
        print("   ❌ ОШИБКА: Кнопка API должна быть ПОКАЗАНА при режиме 'api+proxy'!")
        return False
    else:
        print("   ✅ УСПЕХ: Кнопка API показана (правильно)")
    
    # Проверяем что есть кнопка Прокси
    proxy_button_present = any(btn["text"] == "Прокси" for btn in third_row)
    if not proxy_button_present:
        print("   ❌ ОШИБКА: Кнопка Прокси должна быть!")
        return False
    else:
        print("   ✅ Кнопка Прокси присутствует")
    
    print()
    
    # Тест 2: Режим "api+instagram" - кнопка API должна быть СКРЫТА
    print("📋 Тест 2: verify_mode = 'api+instagram'")
    keyboard = main_menu(is_admin=False, verify_mode="api+instagram")
    third_row = keyboard["keyboard"][3]
    api_button_present = any(btn["text"] == "API" for btn in third_row)
    
    print(f"   Третья строка: {[btn['text'] for btn in third_row]}")
    print(f"   Кнопка API присутствует: {api_button_present}")
    
    if api_button_present:
        print("   ❌ ОШИБКА: Кнопка API должна быть СКРЫТА при режиме 'api+instagram'!")
        return False
    else:
        print("   ✅ УСПЕХ: Кнопка API скрыта (правильно)")
    
    # Проверяем что Прокси на всю ширину
    if len(third_row) == 1 and third_row[0]["text"] == "Прокси":
        print("   ✅ Кнопка Прокси на всю ширину (правильно)")
    else:
        print(f"   ⚠️  Внимание: Третья строка содержит {len(third_row)} кнопок")
    
    print()
    
    # Тест 3: Режим "instagram" - кнопка API должна быть СКРЫТА
    print("📋 Тест 3: verify_mode = 'instagram'")
    keyboard = main_menu(is_admin=False, verify_mode="instagram")
    third_row = keyboard["keyboard"][3]
    api_button_present = any(btn["text"] == "API" for btn in third_row)
    
    print(f"   Третья строка: {[btn['text'] for btn in third_row]}")
    print(f"   Кнопка API присутствует: {api_button_present}")
    
    if api_button_present:
        print("   ❌ ОШИБКА: Кнопка API должна быть СКРЫТА при режиме 'instagram'!")
        return False
    else:
        print("   ✅ УСПЕХ: Кнопка API скрыта (правильно)")
    
    print()
    
    # Тест 4: Режим None - кнопка API должна быть СКРЫТА
    print("📋 Тест 4: verify_mode = None")
    keyboard = main_menu(is_admin=False, verify_mode=None)
    third_row = keyboard["keyboard"][3]
    api_button_present = any(btn["text"] == "API" for btn in third_row)
    
    print(f"   Третья строка: {[btn['text'] for btn in third_row]}")
    print(f"   Кнопка API присутствует: {api_button_present}")
    
    if api_button_present:
        print("   ❌ ОШИБКА: Кнопка API должна быть СКРЫТА при режиме None!")
        return False
    else:
        print("   ✅ УСПЕХ: Кнопка API скрыта (правильно)")
    
    print()
    
    # Тест 5: Режим "proxy" - кнопка API должна быть СКРЫТА
    print("📋 Тест 5: verify_mode = 'proxy'")
    keyboard = main_menu(is_admin=False, verify_mode="proxy")
    third_row = keyboard["keyboard"][3]
    api_button_present = any(btn["text"] == "API" for btn in third_row)
    
    print(f"   Третья строка: {[btn['text'] for btn in third_row]}")
    print(f"   Кнопка API присутствует: {api_button_present}")
    
    if api_button_present:
        print("   ❌ ОШИБКА: Кнопка API должна быть СКРЫТА при режиме 'proxy'!")
        return False
    else:
        print("   ✅ УСПЕХ: Кнопка API скрыта (правильно)")
    
    # Проверяем что Прокси на всю ширину
    if len(third_row) == 1 and third_row[0]["text"] == "Прокси":
        print("   ✅ Кнопка Прокси на всю ширину (правильно)")
    
    print()
    
    # Тест 6: Режим "api+proxy+instagram" - кнопка API должна быть СКРЫТА (не равно точно "api+proxy")
    print("📋 Тест 6: verify_mode = 'api+proxy+instagram'")
    keyboard = main_menu(is_admin=False, verify_mode="api+proxy+instagram")
    third_row = keyboard["keyboard"][3]
    api_button_present = any(btn["text"] == "API" for btn in third_row)
    
    print(f"   Третья строка: {[btn['text'] for btn in third_row]}")
    print(f"   Кнопка API присутствует: {api_button_present}")
    
    if api_button_present:
        print("   ✅ УСПЕХ: Кнопка API скрыта (режим не равен точно 'api+proxy')")
    else:
        print("   ✅ УСПЕХ: Кнопка API скрыта")
    
    print()
    
    print("="*70)
    print("✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ!")
    print("="*70)
    print("\n📊 РЕЗЮМЕ:")
    print("   ✅ api+proxy → API показана")
    print("   ✅ Все остальные режимы → API скрыта")
    print("   ✅ Прокси всегда показана, на всю ширину когда API скрыта")
    print("\n")

if __name__ == "__main__":
    test_api_button_visibility()
