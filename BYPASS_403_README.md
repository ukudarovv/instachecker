# 🛡️ Instagram 403 Bypass System

> **Комплексная система обхода блокировок Instagram с 6 методами проверки**

---

## 🎯 Что это?

Instagram активно блокирует автоматические запросы, возвращая:
- ❌ `403 Forbidden` - доступ запрещен
- ❌ `ERR_TOO_MANY_REDIRECTS` - слишком много перенаправлений
- ❌ `Rate Limiting` - ограничение частоты запросов

**Эта система решает все эти проблемы через 6 различных методов обхода.**

---

## ⚡ Быстрый старт

### 1. Установка

```bash
pip install undetected-chromedriver beautifulsoup4 requests selenium
```

### 2. Тестирование

```bash
python test_403_bypass.py
```

### 3. Использование

```python
import asyncio
from project.services.instagram_bypass import check_account_with_bypass

async def main():
    result = await check_account_with_bypass("username")
    print(f"Exists: {result['exists']}")

asyncio.run(main())
```

---

## 🎯 6 Методов обхода

| # | Метод | Время | Надежность | Описание |
|---|-------|-------|------------|----------|
| 1 | **Quick Mobile Check** | 1-2s | ⭐⭐⭐ | Мобильные headers + no redirects |
| 2 | **API Endpoints** | 2-5s | ⭐⭐⭐⭐ | Множественные публичные API |
| 3 | **Mobile Endpoints** | 2-5s | ⭐⭐⭐⭐ | Официальное приложение Instagram |
| 4 | **Public Sources** | 10-15s | ⭐⭐ | Google Cache, Archive.org |
| 5 | **Mobile Emulation** | 15-25s | ⭐⭐⭐⭐⭐ | Chrome Mobile Device Emulation |
| 6 | **Stealth Browser** | 30-60s | ⭐⭐⭐⭐⭐ | Полная имитация человека |

### Как это работает?

1. **Последовательная проверка** - методы запускаются один за другим
2. **Остановка на успехе** - как только один метод сработал, остальные не запускаются
3. **Fallback система** - если быстрые методы не сработали, используются медленные но надежные
4. **Максимальная эффективность** - сочетание скорости и надежности

---

## 📚 Документация

### 📖 Основные документы

| Документ | Описание |
|----------|----------|
| [BYPASS_403_QUICK_START.md](BYPASS_403_QUICK_START.md) | ⚡ Быстрый старт за 30 секунд |
| [INSTAGRAM_403_BYPASS_GUIDE.md](INSTAGRAM_403_BYPASS_GUIDE.md) | 📘 Полное руководство с примерами |
| [test_403_bypass.py](test_403_bypass.py) | 🧪 Тестовый скрипт |

### 🔍 Быстрый доступ

- **Быстрый старт** → [BYPASS_403_QUICK_START.md](BYPASS_403_QUICK_START.md)
- **Детали методов** → [INSTAGRAM_403_BYPASS_GUIDE.md](INSTAGRAM_403_BYPASS_GUIDE.md)
- **Примеры кода** → Смотрите ниже
- **Тестирование** → `python test_403_bypass.py`

---

## 💡 Примеры использования

### Пример 1: Базовая проверка

```python
import asyncio
from project.services.instagram_bypass import check_account_with_bypass

async def check_user(username):
    result = await check_account_with_bypass(username)
    
    if result['exists']:
        print(f"✅ {username} существует")
    elif result['exists'] is False:
        print(f"❌ {username} не найден")
    else:
        print(f"⚠️ Ошибка: {result['error']}")

asyncio.run(check_user("cristiano"))
```

**Вывод:**
```
[BYPASS] 🚀 Ультимативная проверка @cristiano (макс. 2 попыток)
[BYPASS] 🎯 Включены все методы обхода 403 ошибок
[BYPASS] ⚡ Метод 1: Быстрая проверка (мобильные headers + no redirects)
[BYPASS] ✅ Найден через быстрый метод
[BYPASS] ✅ Профиль @cristiano НАЙДЕН через систему обхода 403
✅ cristiano существует
```

---

### Пример 2: Проверка списка аккаунтов

```python
import asyncio
from project.services.instagram_bypass import check_account_with_bypass

async def check_multiple(usernames):
    results = []
    
    for username in usernames:
        print(f"\n{'='*50}")
        print(f"Проверка: {username}")
        print(f"{'='*50}")
        
        result = await check_account_with_bypass(username, max_retries=1)
        results.append(result)
        
        # Задержка между проверками
        await asyncio.sleep(3)
    
    # Показать сводку
    print(f"\n{'='*50}")
    print("📊 СВОДНАЯ ТАБЛИЦА")
    print(f"{'='*50}")
    
    for result in results:
        status = "✅" if result['exists'] else "❌" if result['exists'] is False else "⚠️"
        print(f"{status} {result['username']}")

# Использование
usernames = ["cristiano", "leomessi", "instagram", "fake_account_12345"]
asyncio.run(check_multiple(usernames))
```

---

### Пример 3: Использование отдельных методов

```python
from project.services.instagram_bypass import InstagramBypass

bypass = InstagramBypass()

# Метод 1: Быстрая проверка (1-2 секунды)
print("🔍 Быстрая проверка...")
result1 = bypass.quick_instagram_check("username")
print(f"Результат: {result1}")

# Метод 2: API endpoints (2-5 секунд)
print("\n🔍 API endpoints...")
result2 = bypass.check_profile_multiple_endpoints("username")
print(f"Результат: {result2}")

# Метод 3: Публичные источники (10-15 секунд)
print("\n🔍 Публичные источники...")
result3 = bypass.check_public_sources("username")
print(f"Результат: {result3}")

# Метод 4: Мобильная эмуляция (15-25 секунд)
print("\n🔍 Мобильная эмуляция...")
result4 = bypass.check_with_mobile_emulation("username")
print(f"Результат: {result4}")
```

---

### Пример 4: Интеграция с основной системой InstaChecker

```python
from project.services.undetected_checker import check_account_with_full_bypass

async def check_with_instachecker(session, user_id, username):
    """
    Проверка через интегрированную систему InstaChecker
    Автоматически использует прокси пользователя
    """
    result = await check_account_with_full_bypass(
        session=session,
        user_id=user_id,
        username=username,
        headless=True,
        screenshot_path=f"screenshots/{username}.png"
    )
    
    return result
```

---

## 🧪 Тестирование

### Запуск тестового скрипта

```bash
python test_403_bypass.py
```

### Режимы тестирования

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║         🛡️  ТЕСТ СИСТЕМЫ ОБХОДА 403 ОШИБОК INSTAGRAM  🛡️                     ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Выберите режим тестирования:
1. Тест одного аккаунта (все методы последовательно)
2. Тест отдельных методов для одного аккаунта
3. Массовый тест нескольких аккаунтов
4. Быстрый тест (quick test)
```

---

## 📊 Эффективность методов

### По скорости (от быстрого к медленному)

1. ⚡ **Quick Mobile Check** - 1-2 сек
2. ⚡ **API Endpoints** - 2-5 сек
3. ⚡ **Mobile Endpoints** - 2-5 сек
4. 🐌 **Public Sources** - 10-15 сек
5. 🐌 **Mobile Emulation** - 15-25 сек
6. 🐌 **Stealth Browser** - 30-60 сек

### По надежности (от надежного к менее надежному)

1. ⭐⭐⭐⭐⭐ **Stealth Browser** - максимальная имитация
2. ⭐⭐⭐⭐⭐ **Mobile Emulation** - эмуляция мобильного устройства
3. ⭐⭐⭐⭐ **API Endpoints** - официальные API
4. ⭐⭐⭐⭐ **Mobile Endpoints** - мобильное приложение
5. ⭐⭐⭐ **Quick Mobile Check** - быстрая проверка
6. ⭐⭐ **Public Sources** - кэшированные данные

### Рекомендации

- **Для скорости**: используйте `max_retries=1` (методы 1-3)
- **Для надежности**: используйте `max_retries=3` (все методы)
- **Для баланса**: используйте `max_retries=2` (методы 1-5)

---

## 🛠️ Конфигурация

### Настройка количества попыток

```python
# Быстрая проверка (только методы 1-3)
result = await check_account_with_bypass(username, max_retries=1)

# Средняя проверка (методы 1-5)
result = await check_account_with_bypass(username, max_retries=2)

# Полная проверка (все методы 1-6)
result = await check_account_with_bypass(username, max_retries=3)
```

### Настройка задержек

В `project/services/instagram_bypass.py`:

```python
# Задержка между попытками (по умолчанию 5-15 секунд)
delay = random.uniform(5, 15)

# Увеличить для большей безопасности:
delay = random.uniform(10, 30)
```

---

## ⚠️ Важные рекомендации

### ✅ Правильное использование

1. **Задержки** - минимум 3 секунды между проверками
2. **Лимиты** - не более 10-20 проверок в минуту
3. **Прокси** - для массовых проверок обязательно
4. **Residential прокси** - предпочтительнее datacenter прокси
5. **Rotation** - меняйте IP для каждой проверки

### ❌ Избегайте

1. ❌ Слишком частые запросы (< 1 сек между проверками)
2. ❌ Массовые проверки без прокси
3. ❌ Использование одного IP для > 100 проверок
4. ❌ Игнорирование ошибок и повторные запросы без задержек

---

## 🔧 Устранение неполадок

### Проблема: Все методы возвращают None

**Причины:**
- Instagram заблокировал ваш IP
- Слишком частые запросы
- Проблемы с интернетом

**Решение:**
```python
# Используйте прокси
from project.services.undetected_checker import check_account_with_full_bypass

# Увеличьте задержки
await asyncio.sleep(10)

# Попробуйте VPN
```

---

### Проблема: 403 ошибка на всех методах

**Решение:**
```python
# 1. Используйте residential прокси
result = await check_account_with_full_bypass(
    session=session,
    user_id=user_id,
    username=username
)

# 2. Увеличьте max_retries
result = await check_account_with_bypass(username, max_retries=3)

# 3. Добавьте задержки
await asyncio.sleep(random.uniform(10, 30))
```

---

### Проблема: Chrome driver не запускается

**Решение:**
```bash
# Переустановите undetected-chromedriver
pip uninstall undetected-chromedriver
pip install undetected-chromedriver

# Обновите Chrome до последней версии
# Windows: chrome://settings/help
# Linux: sudo apt update && sudo apt upgrade google-chrome-stable
```

---

## 📦 Структура файлов

```
InstaChecker/
├── project/
│   └── services/
│       ├── instagram_bypass.py      # 🛡️ Основная система обхода
│       ├── undetected_checker.py    # 🔗 Интеграция с InstaChecker
│       ├── proxy_checker.py         # 🌐 Проверка через прокси
│       └── hybrid_checker.py        # 🔄 Гибридная проверка
│
├── test_403_bypass.py               # 🧪 Тестовый скрипт
├── BYPASS_403_README.md             # 📖 Этот файл
├── BYPASS_403_QUICK_START.md        # ⚡ Быстрый старт
└── INSTAGRAM_403_BYPASS_GUIDE.md    # 📘 Полное руководство
```

---

## 🎓 Дополнительные примеры

### Пример: Обработка ошибок

```python
import asyncio
from project.services.instagram_bypass import check_account_with_bypass

async def safe_check(username):
    try:
        result = await check_account_with_bypass(username, max_retries=2)
        
        if result['exists'] is True:
            return {"username": username, "status": "exists", "error": None}
        elif result['exists'] is False:
            return {"username": username, "status": "not_found", "error": None}
        else:
            return {"username": username, "status": "unknown", "error": result['error']}
            
    except Exception as e:
        return {"username": username, "status": "error", "error": str(e)}

# Использование
result = asyncio.run(safe_check("username"))
print(result)
```

---

### Пример: Логирование результатов

```python
import asyncio
import json
from datetime import datetime
from project.services.instagram_bypass import check_account_with_bypass

async def check_and_log(username, log_file="bypass_results.json"):
    result = await check_account_with_bypass(username)
    
    # Добавляем timestamp
    result['timestamp'] = datetime.now().isoformat()
    
    # Сохраняем в файл
    try:
        with open(log_file, 'r') as f:
            logs = json.load(f)
    except FileNotFoundError:
        logs = []
    
    logs.append(result)
    
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2)
    
    return result

# Использование
asyncio.run(check_and_log("username"))
```

---

### Пример: Статистика методов

```python
from collections import Counter
from project.services.instagram_bypass import InstagramBypass

def test_methods_stats(usernames):
    """Статистика эффективности каждого метода"""
    bypass = InstagramBypass()
    stats = {
        'quick_check': {'success': 0, 'fail': 0, 'error': 0},
        'api_endpoints': {'success': 0, 'fail': 0, 'error': 0},
        'mobile_endpoints': {'success': 0, 'fail': 0, 'error': 0},
        'public_sources': {'success': 0, 'fail': 0, 'error': 0},
    }
    
    for username in usernames:
        # Метод 1
        result = bypass.quick_instagram_check(username)
        if result is True:
            stats['quick_check']['success'] += 1
        elif result is False:
            stats['quick_check']['fail'] += 1
        else:
            stats['quick_check']['error'] += 1
        
        # Метод 2
        result = bypass.check_profile_multiple_endpoints(username)
        if result is True:
            stats['api_endpoints']['success'] += 1
        elif result is False:
            stats['api_endpoints']['fail'] += 1
        else:
            stats['api_endpoints']['error'] += 1
        
        # ... и так далее
    
    # Показать статистику
    print("\n📊 СТАТИСТИКА МЕТОДОВ")
    print("="*60)
    for method, data in stats.items():
        total = sum(data.values())
        success_rate = (data['success'] / total * 100) if total > 0 else 0
        print(f"{method:20s}: {success_rate:.1f}% успеха ({data['success']}/{total})")

# Использование
usernames = ["cristiano", "leomessi", "instagram"]
test_methods_stats(usernames)
```

---

## 🔗 Полезные ссылки

- [Undetected ChromeDriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver)
- [Selenium Documentation](https://selenium-python.readthedocs.io/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Requests Documentation](https://requests.readthedocs.io/)

---

## 📝 Changelog

### v2.0 (2025-10-19) - Текущая версия

- ✅ Добавлена быстрая проверка с мобильными заголовками
- ✅ Добавлена проверка через публичные источники (Google Cache, Archive.org)
- ✅ Добавлена мобильная эмуляция Chrome (Mobile Device Emulation)
- ✅ Улучшена система последовательной проверки методов
- ✅ Добавлен полный тестовый скрипт с 4 режимами
- ✅ Создана подробная документация
- ✅ Оптимизированы задержки между попытками

### v1.0 (Предыдущая версия)

- ✅ Базовая проверка через API endpoints
- ✅ Мобильные API endpoints
- ✅ Скрытый браузер (Stealth Browser)
- ✅ Интеграция с InstaChecker

---

## 🤝 Поддержка

Если возникли проблемы:

1. 📖 Прочитайте [BYPASS_403_QUICK_START.md](BYPASS_403_QUICK_START.md)
2. 📘 Изучите [INSTAGRAM_403_BYPASS_GUIDE.md](INSTAGRAM_403_BYPASS_GUIDE.md)
3. 🧪 Запустите `python test_403_bypass.py`
4. 🔍 Проверьте логи на наличие ошибок
5. 🛠️ Убедитесь, что все зависимости установлены

---

## ⚡ Быстрые ссылки

| Документ | Для чего |
|----------|----------|
| [BYPASS_403_QUICK_START.md](BYPASS_403_QUICK_START.md) | Начать работу за 30 секунд |
| [INSTAGRAM_403_BYPASS_GUIDE.md](INSTAGRAM_403_BYPASS_GUIDE.md) | Подробное изучение всех методов |
| [test_403_bypass.py](test_403_bypass.py) | Протестировать систему |
| [project/services/instagram_bypass.py](project/services/instagram_bypass.py) | Исходный код |

---

**Сделано с ❤️ для обхода блокировок Instagram**

