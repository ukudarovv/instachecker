# Безопасность параллельной обработки с разными режимами

## 🔒 Как система избегает конфликтов

### 1️⃣ **Изоляция пользователей**

Каждый пользователь обрабатывается в отдельной асинхронной задаче:

```python
# В auto_checker.py
async def check_user_accounts(user_id: int, user_accounts: list, ...):
    """Check accounts for a specific user in a separate thread."""
    
    # Каждый пользователь получает свою собственную сессию
    with SessionLocal() as session:
        user = session.query(User).get(user_id)
        verify_mode = user.verify_mode or "api+instagram"
        
        # Режим проверки индивидуален для каждого пользователя
        ...
```

### 2️⃣ **Независимые ресурсы**

Каждый пользователь использует только свои ресурсы:

- **API ключи**: Привязаны к `user_id`
- **Instagram сессии**: Привязаны к `user_id`
- **Прокси**: Привязаны к `user_id`

```python
# Получение ресурсов пользователя
ig_session = get_priority_valid_session(session, user_id, fernet)
proxy = session.query(Proxy).filter(
    Proxy.user_id == user_id,
    Proxy.is_active == True
).first()
```

### 3️⃣ **Параллельная обработка без блокировок**

Все пользователи обрабатываются параллельно через `asyncio.gather`:

```python
# Создание задач для каждого пользователя
tasks = []
for user_id, user_accounts in accounts_by_user.items():
    task = check_user_accounts(user_id, user_accounts, SessionLocal, fernet, bot)
    tasks.append(task)

# Параллельное выполнение
results = await asyncio.gather(*tasks, return_exceptions=True)
```

### 4️⃣ **Валидация ресурсов**

Перед проверкой система проверяет наличие необходимых ресурсов:

```python
# Для режимов с Instagram
if verify_mode in ["api+instagram", "instagram", "instagram+proxy", "api+proxy+instagram"]:
    ig_session = get_priority_valid_session(session, user_id, fernet)
    if not ig_session:
        print(f"[AUTO-CHECK] ❌ No valid IG session for user {user_id}")
        return {"checked": 0, "found": 0, "not_found": 0, "errors": len(user_accounts)}

# Для режимов с Proxy
if verify_mode in ["api+proxy", "proxy", "instagram+proxy", "api+proxy+instagram"]:
    proxy = session.query(Proxy).filter(
        Proxy.user_id == user_id,
        Proxy.is_active == True
    ).first()
    
    if not proxy:
        print(f"[AUTO-CHECK] ⏭️ User {user_id} has no active proxy - SKIPPING")
        return {"checked": 0, "found": 0, "not_found": 0, "errors": 0}
```

## 🎯 Сценарии использования

### Сценарий 1: Разные пользователи, разные режимы

```
Пользователь A: api+instagram
Пользователь B: api+proxy
Пользователь C: instagram+proxy
```

**Результат:** ✅ Все работает параллельно без конфликтов
- A использует свои API ключи и Instagram сессию
- B использует свои API ключи и прокси
- C использует свою Instagram сессию и прокси

### Сценарий 2: Одинаковые режимы, разные ресурсы

```
Пользователь A: api+proxy (Proxy 1)
Пользователь B: api+proxy (Proxy 2)
Пользователь C: api+proxy (Proxy 3)
```

**Результат:** ✅ Все работает параллельно без конфликтов
- Каждый пользователь использует свой прокси
- Каждый пользователь использует свои API ключи
- Проверки не пересекаются

### Сценарий 3: Пользователь без необходимых ресурсов

```
Пользователь A: api+proxy (но нет прокси)
```

**Результат:** ⏭️ Пользователь пропускается
- Система выводит: `User A has no active proxy - SKIPPING`
- Другие пользователи продолжают работу
- Ошибка не влияет на других

## 🔍 Детали реализации

### База данных

Все ресурсы привязаны к пользователю через `user_id`:

```sql
-- API Keys
CREATE TABLE api (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    key TEXT UNIQUE NOT NULL,
    ...
);

-- Instagram Sessions
CREATE TABLE instagram_sessions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    username TEXT NOT NULL,
    ...
);

-- Proxies
CREATE TABLE proxies (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    scheme TEXT NOT NULL,
    host TEXT NOT NULL,
    ...
);
```

### Асинхронность

- **asyncio.gather**: Запускает задачи параллельно
- **Отдельные сессии**: Каждая задача создает свою database session
- **Изоляция ошибок**: `return_exceptions=True` предотвращает каскадные ошибки

### Логирование

Каждое действие логируется с `user_id`:

```
[AUTO-CHECK] 🧵 Starting check for user 1972775559 with 2 accounts
[AUTO-CHECK] 👤 User 1972775559 mode: api+instagram
[AUTO-CHECK] 📡 Phase 1: API checks for user 1972775559...
```

## ✅ Гарантии безопасности

1. **Изоляция данных**: Каждый пользователь видит только свои ресурсы
2. **Независимость**: Ошибка одного пользователя не влияет на других
3. **Параллелизм**: Все пользователи обрабатываются одновременно
4. **Валидация**: Система проверяет ресурсы перед началом проверки
5. **Graceful degradation**: Пользователи без ресурсов пропускаются

## 🧪 Тестирование

Запустите тест для проверки конфликтов:

```bash
python test_concurrent_modes.py
```

Тест проверит:
- Наличие необходимых ресурсов у каждого пользователя
- Корректность распределения режимов
- Возможные конфликты

## 📊 Мониторинг

В логах можно отслеживать:
- Какой пользователь и с каким режимом запускается
- Какие ресурсы используются
- Какие пользователи пропускаются

Пример логов:

```
[AUTO-CHECK] 🧵 Starting check for user 911484504 with 31 accounts
[AUTO-CHECK] 👤 User 911484504 mode: api+proxy
[AUTO-CHECK] ⏭️ User 911484504 has no active proxy - SKIPPING

[AUTO-CHECK] 🧵 Starting check for user 1972775559 with 2 accounts
[AUTO-CHECK] 👤 User 1972775559 mode: api+instagram
[AUTO-CHECK] 📡 Phase 1: API checks for user 1972775559...
```

## 🎯 Вывод

Система спроектирована с учетом безопасности параллельной обработки:
- ✅ Нет конфликтов между пользователями
- ✅ Каждый пользователь использует свой режим
- ✅ Ресурсы изолированы по user_id
- ✅ Ошибки не распространяются
- ✅ Параллельная обработка безопасна

