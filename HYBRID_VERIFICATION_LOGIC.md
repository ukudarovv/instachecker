# Новая логика гибридной проверки аккаунтов

## Проблема

Раньше бот помечал аккаунт как активный (done=True), если API говорил "аккаунт существует", даже если Instagram показывал "страница недоступна".

Это приводило к ложным срабатываниям:
- API может иметь устаревший кэш
- Аккаунт мог быть удален/заблокирован после обновления API
- Instagram - более надежный источник правды

## Новая логика (двухэтапная верификация)

### Шаг 1: Проверка через API
```
API проверка → Быстрая, использует квоту
```

**Результаты:**
- ❌ **Не найден** → Конец проверки, аккаунт не активен
- ✅ **Найден** → Переходим к Шагу 2
- ❓ **Ошибка** → Пробуем только Instagram

### Шаг 2: Верификация через Instagram (КРИТИЧНО)

Если API говорит "найден", **обязательно** проверяем через Instagram:

```python
if api_result["exists"] is True:
    # Проверяем через Instagram
    ig_result = await check_account_with_screenshot(...)
    
    if ig_result["exists"] is False:
        # ПЕРЕОПРЕДЕЛЯЕМ результат API
        result["exists"] = False  # Аккаунт НЕ активен
        # done остается False
        return result
    
    if ig_result["exists"] is True:
        # ОБА подтверждают - аккаунт активен
        result["exists"] = True
        account.done = True  # Помечаем как выполненный
        return result
```

## Сценарии

### Сценарий 1: API и Instagram согласны (аккаунт существует)
```
API: ✅ Найден
Instagram: ✅ Найден
→ Результат: ✅ Активен (done=True)
→ Отправляем уведомление пользователю
```

### Сценарий 2: API говорит найден, Instagram - нет (КЛЮЧЕВОЙ)
```
API: ✅ Найден
Instagram: ❌ Страница недоступна
→ Результат: ❌ НЕ активен (done=False)
→ Аккаунт остается в очереди на проверку
→ Уведомление НЕ отправляется
```

### Сценарий 3: API не нашел
```
API: ❌ Не найден
Instagram: (не проверяем)
→ Результат: ❌ НЕ активен (done=False)
→ Без скриншота, экономим время
```

### Сценарий 4: API ошибка, есть Instagram сессия
```
API: ❓ Ошибка
Instagram: ✅ Найден
→ Результат: ✅ Активен (done=True)
→ Полагаемся только на Instagram
```

### Сценарий 5: Instagram проверка упала с ошибкой
```
API: ✅ Найден
Instagram: ❓ Ошибка (timeout, rate limit, etc)
→ Результат: ✅ Найден (по API)
→ Но с пометкой об ошибке
→ done=False (безопаснее перепроверить)
```

## Изменения в коде

### 1. `project/services/hybrid_checker.py`

#### Добавлена верификация через Instagram:
```python
# CRITICAL: If Instagram says NOT FOUND, override API result
if ig_result.get("exists") is False:
    result["exists"] = False
    result["error"] = "api_found_but_instagram_not_found"
    print(f"⚠️ API says exists, but Instagram says NOT FOUND for @{username}")
    return result  # Не помечаем как done
```

#### Instagram подтверждает результат:
```python
if ig_result.get("exists") is True:
    # Merge Instagram data
    result["full_name"] = ig_result.get("full_name")
    # ... другие данные
    print(f"✅ Both API and Instagram confirm @{username} is active")
```

### 2. `project/cron/auto_checker.py`

#### Явное маркирование как done только при подтверждении:
```python
if result.get("exists") is True:
    # Mark account as done ONLY if truly found
    account.done = True
    account.date_of_finish = date.today()
    s.commit()
    print(f"[AUTO-CHECK] ✅ Marked @{acc.account} as done")
```

#### Улучшенное логирование для случаев расхождения:
```python
if "api_found_but_instagram_not_found" in error_detail:
    print(f"[AUTO-CHECK] ❌ @{acc.account} - NOT FOUND (API said exists, but Instagram confirms NOT FOUND)")
```

## Преимущества новой логики

### ✅ Надежность
- Instagram - финальный источник правды
- Нет ложных срабатываний из-за устаревшего кэша API

### ✅ Экономия ресурсов
- API проверка быстрая (первый фильтр)
- Instagram проверка только для потенциально активных

### ✅ Точность
- Двойная верификация для найденных аккаунтов
- Только реально активные помечаются как done=True

### ✅ Прозрачность
- Подробное логирование каждого шага
- Видно, какой метод использовался: `checked_via`
  - `"api"` - только API (не найден)
  - `"api+instagram"` - оба метода (найден и подтвержден)
  - `"instagram_only"` - только Instagram (API упал)

## Логи

### Успешная верификация:
```
[AUTO-CHECK] ✅ @username - FOUND (verified via api+instagram)
[AUTO-CHECK] ✅ Marked @username as done
✅ Both API and Instagram confirm @username is active
```

### API нашел, Instagram не подтвердил:
```
⚠️ API says exists, but Instagram says NOT FOUND for @username
[AUTO-CHECK] ❌ @username - NOT FOUND (API said exists, but Instagram confirms NOT FOUND)
[AUTO-CHECK] ⏳ @username remains pending (done=False)
```

### Ошибка Instagram проверки:
```
⚠️ API found @username, but Instagram verification failed: timeout
[AUTO-CHECK] ❓ @username - ERROR: instagram_verification_error: timeout
[AUTO-CHECK] ⏳ @username remains pending (done=False)
```

## Тестирование

### Тест 1: API и Instagram согласны
```python
# Ожидаемо: done=True, уведомление отправлено
```

### Тест 2: API говорит "найден", Instagram - "не найден"
```python
# Ожидаемо: done=False, уведомление НЕ отправлено
# Аккаунт останется в очереди на повторную проверку
```

### Тест 3: Только Instagram работает
```python
# API упал → Instagram проверка
# Если найден → done=True
```

## Миграция

Изменения обратно совместимы:
- Если нет Instagram сессии - работает как раньше (только API)
- Если есть Instagram сессия - включается двойная верификация
- Старые аккаунты не затронуты

## Рекомендации

1. **Убедитесь, что у пользователей есть Instagram сессии**
   - Без них проверка только через API (менее надежно)

2. **Мониторьте логи на наличие расхождений**
   - Частые расхождения → проблема с API или Instagram

3. **При большом количестве "api_found_but_instagram_not_found"**
   - Возможно, API кэш сильно устарел
   - Рассмотрите уменьшение веса API проверки

4. **Rate limiting**
   - Instagram проверка медленнее API
   - Используйте задержки между запросами

