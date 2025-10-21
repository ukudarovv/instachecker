# Условное отображение кнопки Instagram

## Что изменилось

Кнопка **"Instagram"** в главном меню теперь отображается только когда режим проверки (`verify_mode`) содержит слово "instagram".

## Логика работы

### Когда кнопка Instagram видна:
- ✅ `instagram` - Только Instagram
- ✅ `api+instagram` - API + Instagram
- ✅ `instagram+proxy` - Instagram + Proxy (без API)
- ✅ `api+proxy+instagram` - API + Proxy + Instagram (тройная)

### Когда кнопка Instagram скрыта:
- ❌ `api+proxy` - API + Proxy
- ❌ `proxy` - Только Proxy
- ❌ `full_bypass` - Полный обход защиты
- ❌ Любой другой режим без слова "instagram"

## Измененные файлы

### Основные файлы:
1. **project/keyboards.py**
   - Функция `main_menu()` теперь принимает параметр `verify_mode`
   - Кнопка Instagram добавляется условно: `if verify_mode and "instagram" in verify_mode.lower()`

2. **project/bot.py**
   - Все вызовы `main_menu()` обновлены для передачи `verify_mode`
   - Добавлен импорт `get_global_verify_mode` где необходимо

### Обработчики (handlers):
3. **project/handlers/admin_menu.py** - 2 вызова обновлены
4. **project/handlers/ig_menu.py** - 1 вызов обновлен
5. **project/handlers/ig_menu_simple.py** - 1 вызов обновлен
6. **project/handlers/common.py** - 2 вызова обновлены
7. **project/handlers/accounts_add.py** - 1 вызов обновлен
8. **project/handlers/api_menu.py** - 1 вызов обновлен

## Как это работает

```python
# Пример в keyboards.py
def main_menu(is_admin: bool = False, verify_mode: str = None) -> dict:
    third_row = [{"text": "API"}, {"text": "Прокси"}]
    
    # Кнопка Instagram показывается только если режим содержит "instagram"
    if verify_mode and "instagram" in verify_mode.lower():
        third_row.append({"text": "Instagram"})
    
    keyboard = {
        "keyboard": [
            [{"text": "Добавить аккаунт"}, {"text": "Активные аккаунты"}],
            [{"text": "Аккаунты на проверке"}, {"text": "Проверить аккаунты"}],
            third_row  # Динамическая строка с кнопками
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }
    
    if is_admin:
        keyboard["keyboard"].append([{"text": "Админка"}])
    
    return keyboard
```

```python
# Пример вызова в bot.py
with session_factory() as session:
    verify_mode = get_global_verify_mode(session)
    keyboard = main_menu(is_admin=ensure_admin(user), verify_mode=verify_mode)
    self.send_message(chat_id, "Главное меню:", keyboard)
```

## Преимущества

1. **Логичный интерфейс** - пользователи видят только те кнопки, которые соответствуют текущему режиму проверки
2. **Избежание ошибок** - нет доступа к функциям Instagram, если они не используются
3. **Чистый UI** - меню адаптируется под конфигурацию системы
4. **Гибкость** - легко добавить дополнительные условия для других кнопок

## Настройка режима проверки

Режим проверки можно изменить через:
1. **Админ-панель** → **Режим проверки**
2. Бот автоматически обновит меню при следующем открытии

## Обратная совместимость

- Legacy функция `get_main_menu_keyboard()` продолжает работать
- Если `verify_mode=None`, кнопка Instagram не отображается
- Все существующие обработчики обновлены для совместимости

## Тестирование

Для проверки:
1. Откройте **Админку** → **Режим проверки**
2. Выберите режим **с** Instagram (например, "Только Instagram")
3. Вернитесь в главное меню - кнопка Instagram должна появиться
4. Смените режим на **без** Instagram (например, "Только Proxy")
5. Вернитесь в главное меню - кнопка Instagram должна исчезнуть

---
**Дата:** 20.10.2025  
**Статус:** ✅ Реализовано и протестировано

