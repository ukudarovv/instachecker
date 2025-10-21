# 🛡️ Руководство по обходу 403 ошибок Instagram

## Проблема

Instagram активно блокирует автоматические запросы, возвращая:
- **403 Forbidden** - доступ запрещен
- **ERR_TOO_MANY_REDIRECTS** - слишком много перенаправлений
- **Rate Limiting** - ограничение частоты запросов

## Решение

Интегрированная система обхода с **6 различными методами**, работающими последовательно.

---

## 🎯 Методы обхода

### 1️⃣ Быстрая проверка (Quick Mobile Check)
**Скорость:** ⚡ Очень быстро (1-2 сек)  
**Надежность:** ⭐⭐⭐

Использует мобильные User-Agent и отключает редиректы для анализа статус кодов.

```python
from project.services.instagram_bypass import InstagramBypass

bypass = InstagramBypass()
result = bypass.quick_instagram_check("username")
# True - найден, False - не найден, None - ошибка
```

**Особенности:**
- Мобильные заголовки (iPhone, Android)
- `allow_redirects=False` для анализа 302 редиректов
- Проверка статус кодов: 200, 302, 404

---

### 2️⃣ API Endpoints
**Скорость:** ⚡ Быстро (2-5 сек)  
**Надежность:** ⭐⭐⭐⭐

Проверка через множественные публичные API endpoints Instagram.

```python
result = bypass.check_profile_multiple_endpoints("username")
```

**Endpoints:**
- `https://www.instagram.com/api/v1/users/web_profile_info/`
- `https://i.instagram.com/api/v1/users/web_profile_info/`
- `https://www.instagram.com/{username}/?__a=1&__d=dis`
- GraphQL endpoints

---

### 3️⃣ Мобильные API Endpoints
**Скорость:** ⚡ Быстро (2-5 сек)  
**Надежность:** ⭐⭐⭐⭐

Использует заголовки официального приложения Instagram.

```python
result = bypass.check_mobile_endpoints("username")
```

**Заголовки:**
```python
{
    'User-Agent': 'Instagram 269.0.0.18.75 (iPhone13,4; iOS 16_5; ...)',
    'X-IG-App-ID': '124024574287414',
    'X-IG-Capabilities': '3brTvx8=',
    'X-IG-Connection-Type': 'WIFI',
}
```

---

### 4️⃣ Публичные источники
**Скорость:** 🐌 Медленно (10-15 сек)  
**Надежность:** ⭐⭐

Проверка через кэшированные данные и поисковые системы.

```python
result = bypass.check_public_sources("username")
```

**Источники:**
- **Google Cache** - `webcache.googleusercontent.com`
- **Archive.org** - Wayback Machine
- **Google Search** - `site:instagram.com username`

---

### 5️⃣ Мобильная эмуляция (Chrome Mobile)
**Скорость:** 🐌 Медленно (15-25 сек)  
**Надежность:** ⭐⭐⭐⭐⭐

Полная эмуляция мобильного устройства через Chrome DevTools Protocol.

```python
result = bypass.check_with_mobile_emulation("username")
```

**Параметры эмуляции:**
```python
{
    "deviceMetrics": {
        "width": 375,
        "height": 812,
        "pixelRatio": 3.0
    },
    "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5...)"
}
```

---

### 6️⃣ Полная скрытая проверка (Stealth Browser)
**Скорость:** 🐌🐌 Очень медленно (30-60 сек)  
**Надежность:** ⭐⭐⭐⭐⭐

Максимальная имитация реального пользователя с undetected-chromedriver.

```python
driver = bypass.create_fully_undetected_driver()
result = bypass.check_profile_stealth(driver, "username")
driver.quit()
```

**Особенности:**
- Скрытие всех признаков автоматизации
- Эмуляция человеческого поведения (скроллинг, клики, движение мыши)
- Множественные косвенные URL для обхода защиты
- Принятие cookies и задержки

---

## 🚀 Использование

### Базовое использование

```python
import asyncio
from project.services.instagram_bypass import check_account_with_bypass

async def main():
    result = await check_account_with_bypass(
        username="cristiano",
        max_retries=2  # Количество попыток
    )
    
    print(f"Username: {result['username']}")
    print(f"Exists: {result['exists']}")
    print(f"Methods used: {result['bypass_methods_used']}")

asyncio.run(main())
```

### Интеграция в существующую систему

```python
# В undetected_checker.py уже интегрировано:
from project.services.undetected_checker import check_account_with_full_bypass

result = await check_account_with_full_bypass(
    session=db_session,
    user_id=user_id,
    username="username",
    headless=True,
    screenshot_path="screenshots/profile.png"
)
```

---

## 🧪 Тестирование

### Запуск тестового скрипта

```bash
python test_403_bypass.py
```

### Режимы тестирования

1. **Полная проверка одного аккаунта**
   - Все методы последовательно
   - Останавливается на первом успешном

2. **Отдельные методы**
   - Тестирует каждый метод отдельно
   - Показывает статистику успеха

3. **Массовый тест**
   - Проверяет несколько аккаунтов
   - Сводная таблица результатов

4. **Быстрый тест**
   - Упрощенная проверка
   - Для отладки

### Пример тестирования

```python
from project.services.instagram_bypass import InstagramBypass

bypass = InstagramBypass()

# Тест 1: Быстрая проверка
result1 = bypass.quick_instagram_check("username")

# Тест 2: API endpoints
result2 = bypass.check_profile_multiple_endpoints("username")

# Тест 3: Публичные источники
result3 = bypass.check_public_sources("username")

# Тест 4: Мобильная эмуляция
result4 = bypass.check_with_mobile_emulation("username")
```

---

## 📊 Статистика эффективности

| Метод | Скорость | Надежность | Рекомендуется |
|-------|----------|------------|---------------|
| Quick Mobile Check | ⚡⚡⚡ | ⭐⭐⭐ | Первая попытка |
| API Endpoints | ⚡⚡⚡ | ⭐⭐⭐⭐ | Первая попытка |
| Mobile Endpoints | ⚡⚡⚡ | ⭐⭐⭐⭐ | Вторая попытка |
| Public Sources | 🐌 | ⭐⭐ | Резервный метод |
| Mobile Emulation | 🐌🐌 | ⭐⭐⭐⭐⭐ | При 403 ошибках |
| Stealth Browser | 🐌🐌🐌 | ⭐⭐⭐⭐⭐ | Последняя попытка |

---

## ⚙️ Конфигурация

### Настройка количества попыток

```python
# 1 попытка - быстрые методы (1-4)
result = await check_account_with_bypass(username, max_retries=1)

# 2 попытки - + мобильная эмуляция (1-5)
result = await check_account_with_bypass(username, max_retries=2)

# 3 попытки - все методы (1-6)
result = await check_account_with_bypass(username, max_retries=3)
```

### Настройка задержек

Задержки между попытками: `5-15 секунд` (случайные)

Изменить в `instagram_bypass.py`:
```python
delay = random.uniform(5, 15)  # Увеличить при необходимости
```

---

## 🔧 Требования

### Python пакеты

```bash
pip install undetected-chromedriver
pip install beautifulsoup4
pip install requests
pip install selenium
```

### Опционально (для улучшения)

```bash
pip install selenium-stealth
```

---

## 🛠️ Устранение неполадок

### Проблема: Все методы возвращают None

**Причины:**
- Instagram полностью заблокировал ваш IP
- Слишком частые запросы
- Проблемы с интернет-соединением

**Решение:**
1. Используйте прокси (residential прокси предпочтительнее)
2. Увеличьте задержки между попытками
3. Уменьшите частоту запросов

### Проблема: 403 ошибка на всех методах

**Решение:**
- Используйте residential прокси
- Попробуйте VPN
- Увеличьте `max_retries` до 3
- Добавьте случайные задержки

### Проблема: Chrome driver не запускается

**Решение:**
```bash
# Переустановите undetected-chromedriver
pip uninstall undetected-chromedriver
pip install undetected-chromedriver

# Обновите Chrome до последней версии
```

---

## 📈 Рекомендации по использованию

### Для проверки одного аккаунта
```python
# Используйте max_retries=1 для скорости
result = await check_account_with_bypass(username, max_retries=1)
```

### Для массовой проверки
```python
# Используйте max_retries=2 для баланса
for username in usernames:
    result = await check_account_with_bypass(username, max_retries=2)
    await asyncio.sleep(5)  # Задержка между аккаунтами
```

### При частых блокировках
```python
# Используйте max_retries=3 и прокси
result = await check_account_with_bypass(username, max_retries=3)
```

---

## 🔒 Безопасность

### Рекомендации:

1. **Не запускайте слишком часто** - Instagram может заблокировать IP
2. **Используйте задержки** - между проверками разных аккаунтов
3. **Residential прокси** - если планируете массовую проверку
4. **Rotation прокси** - меняйте IP для каждой проверки
5. **Rate limiting** - не более 10-20 проверок в минуту

---

## 🎓 Примеры использования

### Пример 1: Простая проверка

```python
import asyncio
from project.services.instagram_bypass import check_account_with_bypass

async def check_user(username):
    result = await check_account_with_bypass(username)
    if result['exists']:
        print(f"✅ {username} exists!")
    else:
        print(f"❌ {username} not found")

asyncio.run(check_user("cristiano"))
```

### Пример 2: Проверка списка аккаунтов

```python
import asyncio
from project.services.instagram_bypass import check_account_with_bypass

async def check_multiple(usernames):
    results = []
    for username in usernames:
        result = await check_account_with_bypass(username, max_retries=1)
        results.append(result)
        await asyncio.sleep(3)  # Задержка 3 секунды
    return results

usernames = ["cristiano", "leomessi", "instagram"]
results = asyncio.run(check_multiple(usernames))

# Показать результаты
for result in results:
    print(f"{result['username']}: {result['exists']}")
```

### Пример 3: Интеграция с прокси

```python
from project.services.instagram_bypass import InstagramBypass
import undetected_chromedriver as uc

bypass = InstagramBypass()

# Настройка прокси
proxy = "http://username:password@proxy.example.com:8080"

options = uc.ChromeOptions()
options.add_argument(f'--proxy-server={proxy}')

driver = uc.Chrome(options=options)
result = bypass.check_profile_stealth(driver, "username")
driver.quit()
```

---

## 📚 Дополнительные ресурсы

- [Undetected ChromeDriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver)
- [Selenium Documentation](https://selenium-python.readthedocs.io/)
- [Instagram Web API](https://stackoverflow.com/questions/tagged/instagram-api)

---

## 🤝 Поддержка

Если возникли проблемы:
1. Запустите `python test_403_bypass.py` для диагностики
2. Проверьте логи на наличие ошибок
3. Убедитесь, что все зависимости установлены
4. Попробуйте использовать прокси

---

## 📝 Changelog

### v2.0 (текущая версия)
- ✅ Добавлена быстрая проверка с мобильными заголовками
- ✅ Добавлена проверка через публичные источники
- ✅ Добавлена мобильная эмуляция Chrome
- ✅ Улучшена система последовательной проверки
- ✅ Добавлен тестовый скрипт

### v1.0 (предыдущая версия)
- ✅ Базовая проверка через API
- ✅ Мобильные endpoints
- ✅ Скрытый браузер

