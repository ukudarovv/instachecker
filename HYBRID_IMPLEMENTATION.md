# Реализация гибридной проверки (API + Instagram + Скриншоты)

## ✅ Выполнено

### 1. Создан сервис гибридной проверки

**Файл**: `project/services/hybrid_checker.py`

#### Функции:

##### `check_account_hybrid()`
Основная функция гибридной проверки:
```python
async def check_account_hybrid(
    session: Session,
    user_id: int,
    username: str,
    ig_session: Optional[InstagramSession] = None,
    fernet: Optional[OptionalFernet] = None
) -> Dict[str, Any]
```

**Алгоритм**:
1. Проверка через API (`check_account_exists_via_api`)
2. Если API недоступен → fallback на Instagram
3. Если найден через API → получение скриншота через Instagram
4. Объединение результатов

**Возвращаемая структура**:
```python
{
    "username": str,
    "exists": bool | None,
    "full_name": str | None,
    "followers": int | None,
    "following": int | None,
    "posts": int | None,
    "screenshot_path": str | None,
    "error": str | None,
    "checked_via": str  # "api", "api+instagram", "instagram_only"
}
```

##### `check_multiple_accounts_hybrid()`
Массовая проверка нескольких аккаунтов с обработкой ошибок для каждого.

### 2. Создан хендлер для гибридной проверки

**Файл**: `project/handlers/check_hybrid.py`

#### Функции:

##### `register_check_hybrid_handlers()`
Регистрирует хендлеры для aiogram:
- Обработчик сообщения "Проверка (API + скриншот)"
- Массовая проверка всех pending аккаунтов
- Отправка текстовых результатов и скриншотов
- Итоговая статистика

### 3. Обновлена клавиатура API меню

**Файл**: `project/keyboards.py`

Добавлена кнопка:
```python
[{"text": "Проверка (API + скриншот)"}]
```

### 4. Интегрировано в бот

**Файл**: `project/bot.py`

#### Изменения:

1. Добавлена обработка текста "Проверка (API + скриншот)"
2. Inline обработка гибридной проверки:
   - Получение аккаунтов на проверке
   - Получение Instagram сессии
   - Вызов `check_account_hybrid` для каждого
   - Отправка результатов с форматированием
   - Отправка скриншотов

3. Обработка отсутствия IG-сессии:
```python
elif not ig_session:
    self.send_message(chat_id,
        "⚠️ Нет активной Instagram-сессии для скриншотов.\n"
        "Будет выполнена только проверка через API.\n"
        "Добавьте IG-сессию через меню 'Instagram' для получения скриншотов."
    )
```

## Архитектура

```
┌─────────────────────────────────────────────────────────┐
│                   Telegram Bot                          │
│                  (project/bot.py)                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  check_account_hybrid  │
        │ (hybrid_checker.py)    │
        └────────┬───────────────┘
                 │
      ┌──────────┴──────────┐
      │                     │
      ▼                     ▼
┌────────────────┐  ┌──────────────────┐
│ check_via_api  │  │ check_with_      │
│ (RapidAPI)     │  │ screenshot       │
│                │  │ (Playwright +    │
│ - Быстро       │  │  Instagram)      │
│ - Существует?  │  │                  │
│                │  │ - Детали         │
│                │  │ - Скриншот       │
└────────────────┘  └──────────────────┘
```

## Логика работы

### Сценарий 1: Аккаунт существует, есть IG-сессия

```
User: [Проверка (API + скриншот)]
  ↓
Bot: ⏳ Проверяю через API + Instagram...
  ↓
1. API Check → ✅ Exists
  ↓
2. Instagram Check → Get details + screenshot
  ↓
Bot: ✅ @username
     Имя: Full Name
     Подписчики: 1,234
     Подписки: 567
     Посты: 89
     🔍 Проверено: API + Instagram
     [📸 Скриншот]
```

### Сценарий 2: Аккаунт не существует

```
User: [Проверка (API + скриншот)]
  ↓
Bot: ⏳ Проверяю через API + Instagram...
  ↓
1. API Check → ❌ Not exists
  ↓
2. Skip Instagram (экономим время)
  ↓
Bot: ❌ @username
     🔍 Проверено: API
```

### Сценарий 3: API недоступен, есть IG-сессия

```
User: [Проверка (API + скриншот)]
  ↓
Bot: ⏳ Проверяю через API + Instagram...
  ↓
1. API Check → ❓ Error (no_available_api_key)
  ↓
2. Fallback to Instagram only
  ↓
Bot: ✅ @username
     Имя: Full Name
     🔍 Проверено: Instagram
     [📸 Скриншот]
```

### Сценарий 4: Нет IG-сессии

```
User: [Проверка (API + скриншот)]
  ↓
Bot: ⚠️ Нет активной Instagram-сессии для скриншотов.
     Будет выполнена только проверка через API.
     Добавьте IG-сессию через меню 'Instagram'...
```

## Форматирование результатов

### Текстовое сообщение
```python
mark = "✅" if exists else ("❌" if not exists else "❓")
lines = [f"{mark} @{username}"]

if full_name:
    lines.append(f"Имя: {full_name}")
if followers is not None:
    lines.append(f"Подписчики: {followers:,}")
if following is not None:
    lines.append(f"Подписки: {following:,}")
if posts is not None:
    lines.append(f"Посты: {posts:,}")

check_via = result.get("checked_via")
if check_via == "api+instagram":
    lines.append("🔍 Проверено: API + Instagram")
elif check_via == "api":
    lines.append("🔍 Проверено: API")
elif check_via == "instagram_only":
    lines.append("🔍 Проверено: Instagram")

if error:
    lines.append(f"⚠️ {error}")
```

### Скриншот
Отправляется отдельным сообщением с caption:
```python
if screenshot_path and os.path.exists(screenshot_path):
    send_photo(screenshot_path, caption=f"📸 Скриншот @{username}")
```

## Производительность

### Замеры времени (примерные):

| Сценарий | API | Instagram | Итого |
|----------|-----|-----------|-------|
| Не существует | 1 сек | - | **1 сек** |
| Существует + IG | 1 сек | 5-10 сек | **6-11 сек** |
| Только Instagram | - | 5-10 сек | **5-10 сек** |

### Экономия времени для 100 аккаунтов:

**Традиционный подход (только Instagram)**:
- 100 × 7 сек = **700 сек** (~12 минут)

**Гибридный подход (50% существуют)**:
- 50 × 1 сек (не существуют) = 50 сек
- 50 × 7 сек (существуют) = 350 сек
- **Итого: 400 сек** (~7 минут)
- **Экономия: 43%**

## Обработка ошибок

### Типы ошибок:

1. **`no_available_api_key`** - Нет доступных API ключей
   - Действие: Fallback на Instagram

2. **`api_failed_no_ig_session`** - API недоступен и нет IG-сессии
   - Действие: Возврат ошибки

3. **`screenshot_error: ...`** - Ошибка получения скриншота
   - Действие: Возврат результата API без скриншота

4. **`instagram_error: ...`** - Ошибка Instagram проверки
   - Действие: Возврат ошибки

## Тестирование

### Ручное тестирование:

```bash
# 1. Запустить бота
python run_bot.py

# 2. В Telegram:
# - Открыть меню "API"
# - Добавить API ключ
# - Добавить Instagram сессию
# - Добавить несколько аккаунтов (существующие и нет)
# - Нажать "Проверка (API + скриншот)"
# - Проверить результаты и скриншоты
```

### Проверка граничных случаев:

1. ✅ Аккаунт существует, есть IG-сессия
2. ✅ Аккаунт не существует
3. ✅ API недоступен
4. ✅ IG-сессия недоступна
5. ✅ Оба недоступны
6. ✅ Приватный аккаунт
7. ✅ Ошибка при получении скриншота

## Расширение функционала

### Добавление кэширования:

```python
# В hybrid_checker.py
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=100)
def _get_cached_result(username: str, cache_time: datetime):
    # Return cached result if less than 1 hour old
    pass
```

### Добавление retry логики:

```python
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def check_account_hybrid_with_retry(...):
    return await check_account_hybrid(...)
```

### Добавление метрик:

```python
metrics = {
    "total_checks": 0,
    "api_checks": 0,
    "instagram_checks": 0,
    "hybrid_checks": 0,
    "errors": 0
}
```

## Файлы

Созданные файлы:
- ✅ `project/services/hybrid_checker.py` (184 строки)
- ✅ `project/handlers/check_hybrid.py` (105 строк)

Обновленные файлы:
- ✅ `project/keyboards.py` (+1 кнопка)
- ✅ `project/bot.py` (+88 строк обработки)

## Документация

- ✅ `HYBRID_CHECK_GUIDE.md` - Руководство пользователя
- ✅ `HYBRID_IMPLEMENTATION.md` - Техническая документация (этот файл)

---

**Статус**: ✅ Полностью реализовано и готово к использованию  
**Дата**: 2025-10-10  
**Версия**: 1.0

