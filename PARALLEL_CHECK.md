# 🚀 Параллельная проверка аккаунтов

## Обзор

Реализована параллельная проверка аккаунтов в автопроверке. Теперь несколько аккаунтов проверяются одновременно, что значительно ускоряет процесс.

---

## ⚡ Как это работает

### Архитектура

```
Автопроверка запущена
  ↓
Получено N аккаунтов для проверки
  ↓
Создается Semaphore (макс 3 параллельных)
  ↓
Запускаются задачи параллельно:
  ├─ Проверка @account1 ──┐
  ├─ Проверка @account2 ──┤→ asyncio.gather()
  └─ Проверка @account3 ──┘
  ↓
Ожидание завершения всех
  ↓
Отправка результатов админу
```

### Ограничение параллелизма

```python
semaphore = asyncio.Semaphore(3)  # Макс 3 одновременно

async def check_with_semaphore(acc):
    async with semaphore:
        await check_single_account(acc)
        await asyncio.sleep(2)  # Задержка между проверками
```

**Зачем ограничение?**
- Избежать блокировки от Instagram
- Не перегружать систему
- Контролировать использование ресурсов

---

## 🔧 Параметры

### Максимальная параллельность

**Текущее значение:** 3 одновременных проверки

**Где настроить:**
```python
# project/cron/auto_checker.py, строка 154
semaphore = asyncio.Semaphore(3)  # Измените на нужное значение
```

**Рекомендации:**
- `1` - Последовательная проверка (медленно, безопасно)
- `2-3` - Оптимально (баланс скорости и безопасности) ⭐
- `5` - Быстро (риск блокировки)
- `10+` - Очень быстро (высокий риск блокировки)

### Задержка между проверками

**Текущее значение:** 2 секунды

**Где настроить:**
```python
# project/cron/auto_checker.py, строка 160
await asyncio.sleep(2)  # Измените на нужное значение
```

---

## 📊 Производительность

### Сравнение скорости

**Последовательная проверка (было):**
```
140 аккаунтов × 10 сек = 1400 сек = ~23 минуты
```

**Параллельная проверка (стало):**
```
140 аккаунтов ÷ 3 потока × 10 сек = ~467 сек = ~8 минут
```

**Ускорение: в 3 раза!** 🚀

### Пример работы

**5 аккаунтов, 3 параллельно:**

```
0 сек:  Start @acc1, @acc2, @acc3
10 сек: @acc1 done → Start @acc4
10 сек: @acc2 done → Start @acc5
10 сек: @acc3 done
20 сек: @acc4 done
20 сек: @acc5 done

Total: ~20 секунд вместо 50
```

---

## 🔄 Как работает параллелизм

### 1. Создание задач

```python
async def check_single_account(acc):
    # Проверка одного аккаунта
    result = await check_account_hybrid(...)
    # Отправка уведомлений
    # Обработка скриншотов
```

### 2. Ограничение с помощью Semaphore

```python
semaphore = asyncio.Semaphore(3)

async def check_with_semaphore(acc):
    async with semaphore:  # Только 3 одновременно
        await check_single_account(acc)
        await asyncio.sleep(2)  # Защита от rate limit
```

### 3. Параллельное выполнение

```python
tasks = [check_with_semaphore(acc) for acc in accounts]
await asyncio.gather(*tasks, return_exceptions=True)
```

### 4. Обработка результатов

```python
# Счетчики обновляются с nonlocal
nonlocal checked, found, not_found, errors
checked += 1
found += 1  # или not_found, errors
```

---

## 🛡️ Безопасность

### Защита от блокировки

1. **Semaphore** - не более 3 одновременно
2. **Задержка** - 2 секунды между запусками
3. **Таймауты** - в hybrid_checker (30 сек)
4. **Обработка ошибок** - return_exceptions=True

### Обработка ошибок

```python
try:
    await check_single_account(acc)
except Exception as e:
    errors += 1
    print(f"Error checking @{acc.account}: {e}")
```

Ошибки не останавливают другие проверки!

---

## 📈 Оптимизация

### Текущие настройки

| Параметр | Значение | Описание |
|----------|----------|----------|
| Параллелизм | 3 | Макс одновременных проверок |
| Задержка | 2 сек | Между запусками |
| При запуске | ВСЕ | max_accounts=999999 |
| Каждые 5 мин | 5 | max_accounts=5 |

### Как настроить под себя

**Для быстрой проверки (риск блокировки):**
```python
semaphore = asyncio.Semaphore(5)
await asyncio.sleep(1)
```

**Для безопасной проверки (медленно):**
```python
semaphore = asyncio.Semaphore(1)
await asyncio.sleep(5)
```

**Оптимально (рекомендуется):**
```python
semaphore = asyncio.Semaphore(3)  # ⭐
await asyncio.sleep(2)
```

---

## 🔍 Мониторинг

### Логи

```
[AUTO-CHECK] Running initial full check immediately...
[AUTO-CHECK] Found 140 pending accounts to check.
[AUTO-CHECK] Checking @account1...
[AUTO-CHECK] Checking @account2...
[AUTO-CHECK] Checking @account3...
[AUTO-CHECK] ✅ @account1 - FOUND
[AUTO-CHECK] 📸 Screenshot sent and deleted for @account1
[AUTO-CHECK] Checking @account4...
...
[AUTO-CHECK] Completed!
  • Checked: 140
  • Found: 50
  • Not found: 85
  • Errors: 5
```

### Что отслеживать

1. **Время выполнения** - должно быть в 3 раза быстрее
2. **Ошибки** - не должно быть много
3. **Rate limiting** - если много ошибок → увеличить задержку
4. **Скриншоты** - должны отправляться и удаляться

---

## ⚠️ Важные моменты

### 1. Thread Safety

Используется `nonlocal` для счетчиков:
```python
nonlocal checked, found, not_found, errors
```

### 2. Database Sessions

Каждая задача создает свою сессию:
```python
with SessionLocal() as s:
    ig_session = get_active_session(s, acc.user_id)
```

### 3. Event Loop

Начальная проверка запускается в отдельном потоке:
```python
check_thread = threading.Thread(target=run_initial_check, daemon=True)
check_thread.start()
```

---

## 📝 Пример использования

### Сценарий 1: Запуск бота

```
python start_bot.py
  ↓
[AUTO-CHECK] Running initial full check immediately...
[AUTO-CHECK] Found 140 pending accounts to check.
  ↓
Проверка 140 аккаунтов параллельно (3 потока)
  ↓
~8 минут → Все проверено
  ↓
✅ Автопроверка завершена
📊 Результаты отправлены админу
```

### Сценарий 2: Периодическая проверка

```
Каждые 5 минут:
  ↓
[AUTO-CHECK] Found 5 pending accounts to check.
  ↓
Проверка 5 аккаунтов параллельно (3 потока)
  ↓
~20 секунд → Все проверено
  ↓
✅ Автопроверка завершена
```

---

## 🎯 Преимущества

1. ✅ **В 3 раза быстрее** - параллельная проверка
2. ✅ **Безопасно** - ограничение через Semaphore
3. ✅ **Надежно** - обработка ошибок
4. ✅ **Масштабируемо** - легко настроить параллелизм
5. ✅ **Эффективно** - asyncio.gather()

---

## 🚀 Готово к использованию!

Бот запущен с параллельной проверкой:

- ⚡ 3 одновременных проверки
- 🔒 Защита от rate limiting
- 📊 Уведомления админу
- 🔄 Автоматический перезапуск

**Наслаждайтесь скоростью!** 🎉

