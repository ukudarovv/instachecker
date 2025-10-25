# Обновление API сервиса Instagram

## 🎯 Что изменилось

API сервис был обновлен с `instagram210.p.rapidapi.com` на `instagram120.p.rapidapi.com`.

### Основные изменения:

1. **Новый хост**: `instagram120.p.rapidapi.com`
2. **Новый URL**: `https://instagram120.p.rapidapi.com/api/instagram/profile`
3. **Новый метод**: POST вместо GET
4. **Новый формат запроса**: JSON payload вместо query parameters
5. **Новый формат ответа**: Структурированный JSON с полями `result` и `success`

## 📋 Обновленные файлы

### 1. `project/config.py`
```python
# Было:
self.rapidapi_host: str = os.getenv("RAPIDAPI_HOST", "instagram210.p.rapidapi.com")
self.rapidapi_url: str = os.getenv("RAPIDAPI_URL", "https://instagram210.p.rapidapi.com/ig_profile")

# Стало:
self.rapidapi_host: str = os.getenv("RAPIDAPI_HOST", "instagram120.p.rapidapi.com")
self.rapidapi_url: str = os.getenv("RAPIDAPI_URL", "https://instagram120.p.rapidapi.com/api/instagram/profile")
```

### 2. `project/services/check_via_api.py`
- Изменен метод с GET на POST
- Добавлен Content-Type: application/json
- Изменен формат запроса с query parameters на JSON payload
- Обновлена логика обработки ответов

### 3. `project/services/api_keys.py`
- Обновлена функция `test_api_key()` для нового API
- Изменен метод тестирования с GET на POST
- Обновлена логика проверки ответов для нового формата

### 4. `env.example`
```env
# Было:
RAPIDAPI_HOST=instagram210.p.rapidapi.com
RAPIDAPI_URL=https://instagram210.p.rapidapi.com/ig_profile

# Стало:
RAPIDAPI_HOST=instagram120.p.rapidapi.com
RAPIDAPI_URL=https://instagram120.p.rapidapi.com/api/instagram/profile
```

## 🔄 Формат запроса и ответа

### Запрос (POST):
```json
{
  "username": "instagram"
}
```

### Ответ при успехе:
```json
{
  "result": {
    "id": "25025320",
    "username": "instagram",
    "is_private": false,
    "profile_pic_url": "...",
    "biography": "Discover what's new on Instagram 🔎✨",
    "full_name": "Instagram",
    "edge_owner_to_timeline_media": {
      "count": 8202
    },
    "edge_followed_by": {
      "count": 695819267
    },
    "edge_follow": {
      "count": 267
    }
  }
}
```

### Ответ при ошибке:
```json
{
  "response": 10,
  "response_type": "page not found",
  "content_type": "video",
  "success": false,
  "message": "The page not found."
}
```

## ✅ Тестирование

API был протестирован с тремя тестовыми случаями:
1. ✅ Активный аккаунт (@instagram) - найден
2. ✅ Несуществующий аккаунт - не найден
3. ✅ Другой активный аккаунт (@cristiano) - найден

## 🚀 Как применить обновления

1. **Обновите .env файл** (если используете):
   ```env
   RAPIDAPI_HOST=instagram120.p.rapidapi.com
   RAPIDAPI_URL=https://instagram120.p.rapidapi.com/api/instagram/profile
   ```

2. **Перезапустите бота** для применения изменений

3. **Проверьте работу** через меню "Проверка через API"

## 🔧 Совместимость

- ✅ Обратная совместимость с существующими API ключами
- ✅ Автоматическая ротация ключей при исчерпании лимитов
- ✅ Обработка ошибок и квот
- ✅ Логирование для отладки

## 📊 Преимущества нового API

1. **Более детальная информация**: Получаем полную информацию о профиле
2. **Лучшая структура**: Четкое разделение успешных и ошибочных ответов
3. **Дополнительные данные**: Количество подписчиков, публикаций, статус приватности
4. **Улучшенная обработка ошибок**: Более информативные сообщения об ошибках
