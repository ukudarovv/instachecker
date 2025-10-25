# Исправление тестирования API ключей

## 🐛 Проблема

После обновления API сервиса с `instagram210.p.rapidapi.com` на `instagram120.p.rapidapi.com` тестирование API ключей не проходило с ошибкой `unexpected_response`.

## 🔍 Причина

Функция `test_api_key()` в файле `project/services/api_keys.py` все еще использовала старый формат API:
- GET запрос вместо POST
- Query parameters вместо JSON payload
- Старую логику обработки ответов

## ✅ Решение

Обновлена функция `test_api_key()` в `project/services/api_keys.py`:

### Изменения:

1. **Метод запроса**: GET → POST
2. **Формат данных**: Query parameters → JSON payload
3. **Заголовки**: Добавлен `Content-Type: application/json`
4. **Логика обработки ответов**: Обновлена для нового формата

### Код до:
```python
headers = {
    "X-RapidAPI-Key": key_value,
    "X-RapidAPI-Host": settings.rapidapi_host
}
params = {"ig": test_username.lower()}

async with sess.get(settings.rapidapi_url, params=params) as resp:
    # Старая логика обработки
```

### Код после:
```python
headers = {
    "X-RapidAPI-Key": key_value,
    "X-RapidAPI-Host": settings.rapidapi_host,
    "Content-Type": "application/json"
}
payload = {"username": test_username.lower()}

async with sess.post(settings.rapidapi_url, json=payload) as resp:
    # Новая логика обработки для формата с result/success
```

## 🧪 Тестирование

API ключ `06f04a18f5msheff8a781de0c8fap12ac18jsn5cf873940a05` теперь проходит тест успешно:

```
✅ API key test PASSED
✅ Key is working correctly
```

## 📋 Обновленные файлы

- `project/services/api_keys.py` - функция `test_api_key()`
- `API_UPDATE_GUIDE.md` - добавлена информация об исправлении

## 🚀 Результат

Теперь тестирование API ключей работает корректно с новым API сервисом `instagram120.p.rapidapi.com`.
