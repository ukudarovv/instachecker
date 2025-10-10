# 🐛 Исправление: Кнопка "Назад в меню" в разделах API и Instagram

## Проблема

Кнопка "Назад в меню" не работала при нажатии из разделов:
- ❌ API меню
- ❌ Instagram меню

## Причина

В `project/bot.py` обработка кнопок этих разделов была сгруппирована в условиях:

```python
elif text in ["Мои API ключи", "Добавить API ключ", "Проверка через API (все)", "Проверка (API + скриншот)"]:
    # Обработка...
```

Кнопка "Назад в меню" хотя и была в списке кнопок клавиатуры, но не была явно обработана внутри блока, поэтому просто игнорировалась.

## Решение

### 1. API меню (строки 992-1001)

**Было:**
```python
elif text in ["Мои API ключи", "Добавить API ключ", "Проверка через API (все)", "Проверка (API + скриншот)"]:
    if not ensure_active(user):
        self.send_message(chat_id, "⛔ Доступ пока не выдан.")
        return
    # Process API menu messages
    if hasattr(self, 'api_menu_process_message'):
        self.api_menu_process_message(message, session_factory)
    # ...
```

**Стало:**
```python
elif text in ["Мои API ключи", "Добавить API ключ", "Проверка через API (все)", "Проверка (API + скриншот)", "Назад в меню"]:
    if not ensure_active(user):
        self.send_message(chat_id, "⛔ Доступ пока не выдан.")
        return
    
    # Handle "Назад в меню" first
    if text == "Назад в меню":
        keyboard = main_menu(is_admin=ensure_admin(user))
        self.send_message(chat_id, "Главное меню:", keyboard)
        return
    
    # Process API menu messages
    if hasattr(self, 'api_menu_process_message'):
        self.api_menu_process_message(message, session_factory)
    # ...
```

### 2. Instagram меню (строки 863-872)

**Было:**
```python
elif text in ["Добавить IG-сессию", "Мои IG-сессии", "Проверить через IG", "Назад в меню"]:
    if not ensure_active(user):
        self.send_message(chat_id, "⛔ Доступ пока не выдан.")
        return
    
    # Process Instagram menu messages
    if hasattr(self, 'ig_menu_process_message'):
        self.ig_menu_process_message(message, session_factory)
    # ...
```

**Стало:**
```python
elif text in ["Добавить IG-сессию", "Мои IG-сессии", "Проверить через IG", "Назад в меню"]:
    if not ensure_active(user):
        self.send_message(chat_id, "⛔ Доступ пока не выдан.")
        return
    
    # Handle "Назад в меню" first
    if text == "Назад в меню":
        keyboard = main_menu(is_admin=ensure_admin(user))
        self.send_message(chat_id, "Главное меню:", keyboard)
        return
    
    # Process Instagram menu messages
    if hasattr(self, 'ig_menu_process_message'):
        self.ig_menu_process_message(message, session_factory)
    # ...
```

## Изменения

### Файл: `project/bot.py`

#### Изменение 1: API меню
- **Строка 992**: Добавлен `"Назад в меню"` в список условия
- **Строки 997-1001**: Добавлена явная обработка кнопки с `return`

#### Изменение 2: Instagram меню
- **Строки 868-872**: Добавлена явная обработка кнопки с `return`

## Проверка

✅ Синтаксис Python - OK
✅ Линтер - без ошибок
✅ Логика работы:
- Пользователь в меню API → нажимает "Назад в меню" → возврат в главное меню
- Пользователь в меню Instagram → нажимает "Назад в меню" → возврат в главное меню

## Тестирование

### Шаги для проверки:

1. Запустите бота
2. Откройте меню "API"
3. Нажмите "Назад в меню"
4. **Ожидаемо**: Возврат в главное меню ✅

5. Откройте меню "Instagram"
6. Нажмите "Назад в меню"
7. **Ожидаемо**: Возврат в главное меню ✅

## Примечание

Меню "Прокси" не требует исправления, так как там используются отдельные обработчики для каждой кнопки, и общий обработчик "Назад в меню" (строка 1182) работает корректно.

---

**Статус**: ✅ Исправлено  
**Дата**: 2025-10-10  
**Затронутые файлы**: `project/bot.py`  
**Строк изменено**: 10

