# ⚡ Быстрый старт: Обход 403 ошибок Instagram

## 🚀 Запуск за 30 секунд

### 1. Установка зависимостей

```bash
pip install undetected-chromedriver beautifulsoup4 requests selenium
```

### 2. Тестирование системы

```bash
python test_403_bypass.py
```

### 3. Использование в коде

```python
import asyncio
from project.services.instagram_bypass import check_account_with_bypass

async def main():
    result = await check_account_with_bypass("username")
    print(f"Exists: {result['exists']}")

asyncio.run(main())
```

---

## 📋 Методы обхода (6 штук)

| # | Метод | Скорость | Надежность |
|---|-------|----------|------------|
| 1 | Quick Mobile Check | ⚡⚡⚡ | ⭐⭐⭐ |
| 2 | API Endpoints | ⚡⚡⚡ | ⭐⭐⭐⭐ |
| 3 | Mobile Endpoints | ⚡⚡⭐ | ⭐⭐⭐⭐ |
| 4 | Public Sources | 🐌⭐⭐ | ⭐⭐ |
| 5 | Mobile Emulation | 🐌🐌⭐ | ⭐⭐⭐⭐⭐ |
| 6 | Stealth Browser | 🐌🐌🐌 | ⭐⭐⭐⭐⭐ |

---

## 🎯 Основные команды

### Базовая проверка (быстро)
```python
result = await check_account_with_bypass("username", max_retries=1)
```

### Полная проверка (надежно)
```python
result = await check_account_with_bypass("username", max_retries=3)
```

### Проверка с прокси
```python
from project.services.undetected_checker import check_account_with_full_bypass

result = await check_account_with_full_bypass(
    session=db_session,
    user_id=user_id,
    username="username"
)
```

---

## 🔧 Режимы тестирования

```bash
python test_403_bypass.py
```

1. **Полная проверка одного аккаунта** → Все методы последовательно
2. **Отдельные методы** → Каждый метод отдельно
3. **Массовый тест** → Несколько аккаунтов
4. **Быстрый тест** → Упрощенная проверка

---

## 💡 Примеры использования

### Пример 1: Проверка одного аккаунта
```python
import asyncio
from project.services.instagram_bypass import check_account_with_bypass

async def check():
    result = await check_account_with_bypass("cristiano")
    print(result['exists'])  # True/False/None

asyncio.run(check())
```

### Пример 2: Проверка списка
```python
usernames = ["cristiano", "leomessi", "instagram"]

for username in usernames:
    result = await check_account_with_bypass(username, max_retries=1)
    print(f"{username}: {result['exists']}")
    await asyncio.sleep(3)  # Задержка
```

### Пример 3: Отдельный метод
```python
from project.services.instagram_bypass import InstagramBypass

bypass = InstagramBypass()

# Быстрая проверка (1-2 сек)
result = bypass.quick_instagram_check("username")

# API проверка (2-5 сек)
result = bypass.check_profile_multiple_endpoints("username")

# Мобильная эмуляция (15-25 сек)
result = bypass.check_with_mobile_emulation("username")
```

---

## 🛠️ Устранение проблем

### Проблема: Все методы возвращают None
**Решение:**
- Используйте прокси
- Увеличьте задержки
- Попробуйте VPN

### Проблема: 403 на всех методах
**Решение:**
- Residential прокси
- `max_retries=3`
- Задержки 10-30 сек

### Проблема: Chrome не запускается
**Решение:**
```bash
pip uninstall undetected-chromedriver
pip install undetected-chromedriver
```

---

## 📊 Результат проверки

```python
{
    "username": "cristiano",
    "exists": True,  # True/False/None
    "error": None,
    "checked_via": "bypass_403_all_methods",
    "bypass_methods_used": [
        "quick_mobile_check",
        "api_endpoints",
        "mobile_endpoints",
        "public_sources",
        "mobile_emulation",
        "stealth_browser"
    ]
}
```

---

## ⚠️ Рекомендации

1. **Задержки** - минимум 3 секунды между проверками
2. **Лимиты** - не более 20 проверок в минуту
3. **Прокси** - для массовых проверок обязательно
4. **max_retries=1** - для скорости
5. **max_retries=3** - для надежности

---

## 📚 Полная документация

Смотрите `INSTAGRAM_403_BYPASS_GUIDE.md` для:
- Детального описания каждого метода
- Продвинутых примеров
- Конфигурации
- Устранения неполадок

---

## 🎓 Быстрые шаблоны

### Шаблон 1: Проверка с логированием
```python
async def check_with_log(username):
    print(f"Checking {username}...")
    result = await check_account_with_bypass(username)
    
    if result['exists']:
        print(f"✅ {username} exists")
    elif result['exists'] is False:
        print(f"❌ {username} not found")
    else:
        print(f"⚠️ {username} error: {result['error']}")
    
    return result
```

### Шаблон 2: Массовая проверка
```python
async def check_list(usernames):
    results = []
    for username in usernames:
        try:
            result = await check_account_with_bypass(username, max_retries=1)
            results.append(result)
            print(f"{username}: {'✅' if result['exists'] else '❌'}")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"{username}: ⚠️ Error: {e}")
    return results
```

### Шаблон 3: Retry с прокси
```python
async def check_with_retry(username, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            result = await check_account_with_bypass(username)
            if result['exists'] is not None:
                return result
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            await asyncio.sleep(10)
    return {"username": username, "exists": None, "error": "All retries failed"}
```

---

## 🔗 Ссылки

- Полное руководство: `INSTAGRAM_403_BYPASS_GUIDE.md`
- Тестовый скрипт: `test_403_bypass.py`
- Исходный код: `project/services/instagram_bypass.py`

