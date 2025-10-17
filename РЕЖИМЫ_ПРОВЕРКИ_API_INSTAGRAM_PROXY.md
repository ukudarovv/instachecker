
# Режимы проверки аккаунтов: API + Instagram / API + Proxy

## 🎯 Цель

Добавлена возможность переключения между двумя режимами проверки аккаунтов:

1. **API + Instagram** - Двухэтапная проверка с авторизацией в Instagram
2. **API + Proxy** - Двухэтапная проверка через proxy без авторизации

## 📋 Режимы проверки

### 1. **API + Instagram** (api+instagram)

**Этап 1**: Быстрая проверка через RapidAPI  
**Этап 2**: Если аккаунт найден - проверка через Instagram **с логином**

**Преимущества**:
- ✅ Точная проверка с полной информацией (подписчики, публикации и т.д.)
- ✅ Скриншот страницы профиля
- ✅ Доступ к приватным профилям (если есть подписка)

**Требования**:
- Instagram сессия (cookies)
- Логин/пароль для переавторизации

**Используется**:
- `check_account_with_screenshot()` из `project/services/ig_simple_checker.py`

---

### 2. **API + Proxy** (api+proxy)

**Этап 1**: Быстрая проверка через RapidAPI  
**Этап 2**: Если аккаунт найден - проверка через proxy **без логина**

**Преимущества**:
- ✅ Не требует Instagram аккаунта
- ✅ Скриншот публичной страницы
- ✅ Простота настройки

**Требования**:
- Активный proxy (настроенный в системе)

**Используется**:
- `check_account_via_proxy_with_screenshot()` из `project/services/proxy_checker.py`

---

## 🔧 Техническая реализация

### 1. Модель User

**Файл**: `project/models.py`

Добавлено поле `verify_mode`:

```python
class User(Base):
    # ...
    verify_mode = Column(String, default="api+instagram", nullable=False)  
    # Значения: 'api+instagram' | 'api+proxy'
```

---

### 2. Proxy Checker (без логина)

**Файл**: `project/services/proxy_checker.py`

Новая функция для проверки через proxy без авторизации:

```python
async def check_account_via_proxy(
    username: str,
    proxy: Optional[Proxy] = None,
    headless: bool = True,
    timeout_ms: int = 30000
) -> Dict[str, Any]:
    """
    Check if Instagram account exists using proxy without login.
    Just opens the public profile page.
    """
    # Открывает https://www.instagram.com/{username}/
    # Проверяет наличие/отсутствие аккаунта по тексту страницы
    # Определяет приватность профиля
```

**Логика определения**:
- Страница с текстом "Sorry, this page isn't available" = аккаунт не найден
- Текст "This Account is Private" = аккаунт приватный
- Наличие profile picture или header = аккаунт публичный

---

### 3. Hybrid Checker

**Файл**: `project/services/hybrid_checker.py`

Обновлена функция `check_account_hybrid`:

```python
async def check_account_hybrid(
    session: Session,
    user_id: int,
    username: str,
    ig_session: Optional[InstagramSession] = None,
    fernet: Optional[OptionalFernet] = None,
    skip_instagram_verification: bool = False,
    verify_mode: str = "api+instagram"  # НОВЫЙ ПАРАМЕТР
) -> Dict[str, Any]:
```

**Логика**:

```python
# Шаг 1: API проверка (быстро)
api_result = await check_account_exists_via_api(...)

# Шаг 2: Если найдено - выбираем метод верификации
if api_result["exists"] is True:
    if verify_mode == "api+instagram":
        # Instagram проверка с логином
        ig_result = await check_account_with_screenshot(...)
    elif verify_mode == "api+proxy":
        # Proxy проверка без логина
        proxy_result = await check_account_via_proxy_with_screenshot(...)
```

---

### 4. Auto Checker

**Файл**: `project/cron/auto_checker.py`

Обновлена логика автопроверки:

```python
# Получаем verify_mode пользователя
user = s.query(User).get(acc.user_id)
verify_mode = user.verify_mode or "api+instagram"

# Получаем нужную сессию/proxy
if verify_mode == "api+instagram":
    ig_session = get_priority_valid_session(s, acc.user_id, fernet)
else:  # api+proxy
    ig_session = None  # Proxy не нужна IG сессия

# Передаем verify_mode в проверку
result = await check_account_hybrid(
    session=s,
    user_id=acc.user_id,
    username=acc.account,
    ig_session=ig_session,
    fernet=fernet,
    verify_mode=verify_mode
)
```

**Логи**:

```
[AUTO-CHECK] API check @username (mode: api+instagram)...
[AUTO-CHECK] ✓ @username - API says ACTIVE (will verify with Instagram)
```

или

```
[AUTO-CHECK] API check @username (mode: api+proxy)...
[AUTO-CHECK] ✓ @username - API says ACTIVE (will verify with Proxy)
```

---

### 5. Админ-меню

**Файлы**: 
- `project/keyboards.py` - добавлена кнопка
- `project/handlers/user_management.py` - обработчики

**Кнопка в карточке пользователя**:
```
🔄 Изменить режим проверки
```

**Меню выбора режима**:
```
🔄 Изменение режима проверки

Пользователь: @username
Текущий режим: api+instagram

Выберите новый режим проверки:

[🔑 API + 📸 Instagram (с логином)]
[🔑 API + 🌐 Proxy (без логина)]
[⬅ Назад]
```

**Обработчики**:
- `handle_callback_usr_change_verify` - показывает меню выбора
- `handle_callback_usr_set_verify` - сохраняет выбранный режим

---

## 📊 Сравнение режимов

| Параметр | API + Instagram | API + Proxy |
|----------|----------------|-------------|
| **Скорость API** | 1 сек | 1 сек |
| **Скорость верификации** | 5 сек | 5 сек |
| **Требует IG аккаунт** | ✅ Да | ❌ Нет |
| **Требует Proxy** | ❌ Нет | ✅ Да |
| **Скриншоты** | ✅ Да | ✅ Да |
| **Полные данные** | ✅ Да | ❌ Частично |
| **Приватные профили** | ✅ Да (если есть подписка) | ❌ Нет |
| **Риск блокировки IG** | Средний | Низкий |

---

## 🔄 Миграция

**Файл**: `migrate_verify_mode.py`

Обновляет старые значения `verify_mode`:

```
'api' → 'api+instagram'
'instagram' → 'api+instagram'
'proxy' → 'api+proxy'
NULL → 'api+instagram'
```

**Запуск**:
```bash
python migrate_verify_mode.py
```

**Результат**:
```
✅ Обновлено пользователей: 11
```

---

## 📝 Примеры использования

### Сценарий 1: Пользователь с Instagram сессией

**Настройка**: `api+instagram`

```
[AUTO-CHECK] API check @username (mode: api+instagram)...
[AUTO-CHECK] ✓ @username - API says ACTIVE (will verify with Instagram)
[AUTO-CHECK] Instagram verify @username...
✅ Both API and Instagram confirm @username is active
📸 Screenshot saved: screenshots/ig_username_20251017_120000.png
```

---

### Сценарий 2: Пользователь без Instagram, но с Proxy

**Настройка**: `api+proxy`

```
[AUTO-CHECK] API check @username (mode: api+proxy)...
[AUTO-CHECK] ✓ @username - API says ACTIVE (will verify with Proxy)
[AUTO-CHECK] Proxy verify @username...
[PROXY-CHECK] Opening https://www.instagram.com/username/...
✅ Both API and Proxy confirm @username is active
📸 Screenshot saved: screenshots/ig_username_20251017_120000.png
```

---

### Сценарий 3: Смена режима в админке

1. Админ открывает карточку пользователя
2. Нажимает "🔄 Изменить режим проверки"
3. Видит текущий режим: `api+instagram`
4. Выбирает: "🔑 API + 🌐 Proxy (без логина)"
5. Получает уведомление: "✅ Режим изменен на 🔑 API + 🌐 Proxy"
6. Теперь все проверки для этого пользователя используют proxy

---

## ✅ Преимущества новой системы

✅ **Гибкость** - каждый пользователь выбирает удобный режим  
✅ **API всегда первый** - быстрая предварительная проверка  
✅ **Минимум задержек** - только 1 секунда для API  
✅ **Proxy без логина** - не требует Instagram аккаунта  
✅ **Простое переключение** - через админ-меню  
✅ **Автоматическая миграция** - старые значения обновляются  

---

## 🚀 Итого

Система теперь поддерживает два режима проверки:

1. **API + Instagram** - для точной проверки с полными данными
2. **API + Proxy** - для простой проверки без авторизации

**Все проверки начинаются с API** (быстро), затем используется выбранный метод верификации!

**Дата реализации**: 17 октября 2025

