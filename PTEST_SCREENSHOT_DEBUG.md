# Отладка проблемы с режимом "Тест скриншота"

## 🐛 Проблема

При выборе режима "📸 Тест скриншота" не появляется сообщение с запросом username.

## 🔍 Анализ

### ✅ Код обработчика выглядит правильно:

```python
elif callback_data == "ptest_screenshot":
    # Screenshot test mode
    self.fsm_states[user_id] = {
        "state": "waiting_proxy_test_username",
        "test_all": True,
        "test_mode": "screenshot"
    }
    
    # ... создание сообщения и клавиатуры ...
    
    self.edit_message_text(chat_id, message_id, message, cancel_keyboard)
    self.answer_callback_query(callback_query["id"])
```

### 🔍 Возможные причины:

1. **Бот не перезапущен** после изменений
2. **Ошибка в `edit_message_text`**
3. **Проблема с импортами**
4. **Callback не обрабатывается**

## ✅ Решения

### 1. Перезапустите бота

**Важно**: После любых изменений в коде необходимо перезапустить бота.

```bash
# Остановите бота (Ctrl+C)
# Затем запустите заново
python run_bot.py
```

### 2. Проверьте логи бота

При нажатии на кнопку "📸 Тест скриншота" в логах должно появиться:

```
✅ Callback matches ptest_screenshot
✅ FSM state set: {'state': 'waiting_proxy_test_username', 'test_all': True, 'test_mode': 'screenshot'}
✅ Message created with username request
```

### 3. Проверьте импорты

Убедитесь, что все импорты работают:

```python
try:
    from .keyboards import cancel_kb
    from .models import Proxy
except ImportError:
    from keyboards import cancel_kb
    from models import Proxy
```

### 4. Альтернативное решение

Если проблема сохраняется, можно заменить `edit_message_text` на `send_message`:

```python
# Вместо:
self.edit_message_text(chat_id, message_id, message, cancel_keyboard)

# Использовать:
self.send_message(chat_id, message, cancel_keyboard)
```

## 🧪 Тестирование

### 1. Проверьте callback обработку

Добавьте отладочные сообщения в код:

```python
elif callback_data == "ptest_screenshot":
    print(f"[DEBUG] Processing ptest_screenshot callback for user {user_id}")
    
    # ... остальной код ...
    
    print(f"[DEBUG] Sending message to chat {chat_id}")
    self.edit_message_text(chat_id, message_id, message, cancel_keyboard)
    print(f"[DEBUG] Message sent successfully")
```

### 2. Проверьте FSM состояние

После нажатия кнопки проверьте FSM состояние:

```python
# В логах должно быть:
print(f"[DEBUG] FSM state: {self.fsm_states.get(user_id, 'NOT_FOUND')}")
```

## 🚀 Ожидаемое поведение

После нажатия кнопки "📸 Тест скриншота" должно появиться сообщение:

```
📸 Тест скриншота прокси

📊 Будет протестировано: X прокси
📸 Режим: Создание скриншота профиля (Desktop)

Введите Instagram username для проверки:

💡 Примеры:
  • instagram (рекомендуется)
  • cristiano
  • nasa

Бот проверит каждый прокси на этом аккаунте и покажет результаты.
```

С кнопкой "❌ Отмена" внизу.

## 📋 Следующие шаги

1. **Перезапустите бота**
2. **Попробуйте снова** выбрать "📸 Тест скриншота"
3. **Проверьте логи** на наличие ошибок
4. **Если проблема сохраняется** - проверьте импорты и код обработчика
