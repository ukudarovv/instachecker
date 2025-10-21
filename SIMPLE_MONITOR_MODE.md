# ⚡ Режим "Простой мониторинг" (Simple Monitor)

## 📋 Описание

Новый режим проверки Instagram аккаунтов, основанный на логике из **app.py**.  
Простой, быстрый и эффективный метод мониторинга - без лишних сложностей.

**Дата добавления:** 20.10.2025  
**Версия:** 1.0  
**Статус:** ✅ Протестировано и работает

---

## 🎯 Что это такое?

Этот режим использует ту же логику проверки, что и в файле `app.py` - простой мониторинг-бот:
- Прямые запросы к Instagram API
- Минимальные заголовки
- Случайные User-Agents (12 вариантов)
- Простая логика: user есть = активен, user null = забанен
- Retry механизм с exponential backoff

---

## ✅ Результаты тестирования

### Тест с прокси resi.gg:

| Аккаунт | Результат | Подписчиков | Статус |
|---------|-----------|-------------|--------|
| @instagram | ✅ Активен | 695,646,886 | ✓ Verified |
| @cristiano | ✅ Активен | 666,294,567 | ✓ Verified |
| @test123456789nonexistent | ❌ Не найден | - | - |

**Успешность:** 100% (для существующих аккаунтов)  
**Время проверки:** ~8 секунд на аккаунт  
**С прокси:** ✅ Работает идеально  
**Без прокси:** ✅ Тоже работает

---

## 📊 Сравнение с другими режимами

| Критерий | simple_monitor | api+proxy | full_bypass |
|----------|----------------|-----------|-------------|
| **Скорость** | ⚡⚡⚡ Быстро (8 сек) | ⚡⚡ Средне | ⚡ Медленно |
| **Сложность** | ✅ Простой | ⚠️ Средняя | ❌ Сложный |
| **Надежность** | ✅✅✅ | ✅✅✅ | ✅✅✅✅ |
| **Прокси** | ✅ Поддержка | ✅ Обязателен | ✅ Опционально |
| **Обход 403** | ⚠️ Базовый | ✅ Хороший | ✅✅ Отличный |
| **Детали** | ✅ Подписчики, био | ✅ Базовая инфо | ✅✅ Скриншоты |
| **Как в app.py** | ✅✅✅ Да! | ❌ Нет | ❌ Нет |

---

## 🚀 Как использовать

### 1. Включить режим в боте

```
1. Откройте Telegram бота
2. Админка → Режим проверки
3. Выберите "⚡ Простой мониторинг (app.py стиль)"
4. ✅ Готово!
```

### 2. Добавить аккаунты

```
1. Главное меню → Добавить аккаунт
2. Введите Instagram username
3. Бот автоматически начнет проверку через Simple Monitor
```

### 3. Настроить прокси (опционально)

```
1. Главное меню → Прокси
2. Добавить прокси (например, resi.gg)
3. Режим автоматически будет использовать прокси
```

---

## 💡 Когда использовать?

### ✅ Подходит для:

- **Быстрого мониторинга** - нужны результаты быстро
- **Простой проверки** - не нужны скриншоты
- **Массовых проверок** - сотни аккаунтов
- **Стабильных прокси** - есть хороший прокси (resi.gg)
- **Похожего на app.py** - хотите такую же логику как в app.py

### ⚠️ НЕ подходит для:

- **Обхода жестких блокировок** - используйте `full_bypass`
- **Получения скриншотов** - используйте режимы с `instagram`
- **Максимальной скрытности** - используйте `full_bypass` с Playwright

---

## 🔧 Технические детали

### User-Agents

Режим использует 12 различных User-Agents из app.py:
```python
- Windows Chrome
- Windows Firefox
- macOS Chrome/Safari/Edge
- iOS Safari (iPhone/iPad/iPod)
- Android Chrome
- macOS Vivaldi/Firefox
```

### Заголовки запроса

```python
{
    "X-IG-App-ID": "936619743392459",
    "X-CSRFToken": "missing",
    "X-ASBD-ID": "129477",
    "X-IG-WWW-Claim": "0",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.instagram.com/",
    "User-Agent": random.choice(USER_AGENTS)
}
```

### Логика проверки

```python
1. Запрос к: https://i.instagram.com/api/v1/users/web_profile_info/?username={username}
2. Парсинг JSON ответа
3. Проверка:
   - Если data.user != null → ✅ Активен
   - Если data.user == null → ❌ Забанен/Не существует
4. Retry при ошибках (до 3 попыток)
5. Exponential backoff (2, 4, 8 секунд)
```

### Что возвращает?

```python
{
    'success': True,
    'is_active': True/False,
    'status': '✅ Active (666M followers) [✓ Verified]',
    'username': 'cristiano',
    'followers': 666294567,
    'is_verified': True,
    'is_private': False,
    'full_name': 'Cristiano Ronaldo',
    'biography': 'Soccer player...',
    'profile_pic_url': 'https://...',
    'checked_at': '2025-10-20T23:16:27'
}
```

---

## 📈 Производительность

### С прокси resi.gg:
```
✅ instagram:   8.5 секунд
✅ cristiano:   8.2 секунд
❌ несуществующий: 22 секунды (3 retry)
```

### Без прокси (прямое подключение):
```
✅ instagram:   1.5 секунды
```

### Массовая проверка (5 параллельно):
```
Время на 50 аккаунтов: ~80 секунд
Throughput: ~0.6 аккаунтов/сек
```

---

## 🔐 Безопасность и ограничения

### ✅ Безопасность:
- Random User-Agents снижают fingerprinting
- Поддержка прокси для скрытия IP
- Retry механизм избегает блокировок
- Exponential backoff снижает нагрузку

### ⚠️ Ограничения:
- **Rate Limits**: Instagram может ограничить после ~100 запросов/час
- **403 блокировки**: Возможны при агрессивном использовании
- **IP бан**: Используйте прокси для избежания
- **Нет скриншотов**: Режим не делает скриншоты профилей

### 💡 Рекомендации:
1. **Используйте прокси** (особенно resi.gg с ротацией IP)
2. **Интервал проверки**: 5-15 минут (не слишком часто)
3. **Лимит аккаунтов**: до 100-200 на один прокси/день
4. **При 403**: переключитесь на `full_bypass`

---

## 🎯 Примеры использования

### Пример 1: Базовая проверка

```python
from project.services.simple_monitor_checker import check_account_simple

is_active, status, user_data = await check_account_simple(
    username="instagram",
    proxy="http://user:pass@proxy.resi.gg:12321"
)

print(f"Status: {status}")
print(f"Followers: {user_data['edge_followed_by']['count']}")
```

### Пример 2: Детальная проверка

```python
from project.services.simple_monitor_checker import check_account_with_details

result = await check_account_with_details(
    username="cristiano",
    proxy="http://user:pass@proxy.resi.gg:12321"
)

print(f"Active: {result['is_active']}")
print(f"Verified: {result['is_verified']}")
print(f"Followers: {result['followers']:,}")
```

### Пример 3: Массовая проверка

```python
from project.services.simple_monitor_checker import batch_check_accounts

usernames = ["instagram", "cristiano", "leomessi"]
results = await batch_check_accounts(
    usernames=usernames,
    proxy="http://user:pass@proxy.resi.gg:12321",
    concurrent_limit=5
)

for username, data in results.items():
    print(f"{username}: {data['status']}")
```

---

## 📚 API Reference

### `check_account_simple(username, proxy, timeout, retry_count)`

Простая проверка аккаунта.

**Returns:** `(is_active: bool, status_text: str, user_data: dict)`

### `check_account_with_details(username, proxy)`

Детальная проверка с полной информацией.

**Returns:** `dict` с полными данными аккаунта

### `batch_check_accounts(usernames, proxy, concurrent_limit)`

Массовая проверка нескольких аккаунтов.

**Returns:** `dict[username] = result`

---

## 🐛 Troubleshooting

### Проблема: Timeout ошибки

**Решение:**
- Увеличьте timeout (по умолчанию 15 сек)
- Проверьте скорость прокси
- Используйте более быстрый прокси

### Проблема: 403 Forbidden

**Решение:**
- Переключитесь на режим `full_bypass`
- Измените прокси
- Увеличьте интервал между проверками

### Проблема: Invalid JSON

**Решение:**
- Проверьте существование аккаунта
- Retry автоматически попробует еще раз
- Если не помогает - аккаунт забанен или удален

### Проблема: 407 Proxy Auth

**Решение:**
- Проверьте логин/пароль прокси
- Формат: `http://user:pass@host:port`
- Проверьте срок действия прокси

---

## 🔄 История изменений

### v1.0 (20.10.2025)
- ✅ Создан новый режим на основе app.py
- ✅ Добавлены 12 User-Agents
- ✅ Retry механизм с exponential backoff
- ✅ Поддержка прокси
- ✅ Детальная информация о пользователях
- ✅ Batch проверка
- ✅ Интеграция в бот
- ✅ Тестирование пройдено

---

## 🎉 Итоги

**Simple Monitor** - это:
- ⚡ **Быстрый** - 8 секунд на проверку
- ✅ **Простой** - минимальная сложность
- 🎯 **Эффективный** - как app.py
- 🌐 **С прокси** - поддержка resi.gg
- 📊 **Детальный** - полная информация о пользователях
- 🔄 **Надежный** - retry механизм

---

## 📞 Поддержка

Если возникли вопросы:
1. Проверьте эту документацию
2. Запустите тест: `python test_simple_monitor.py`
3. Проверьте логи бота
4. Попробуйте другой режим проверки

---

**Создано:** 20.10.2025  
**Автор:** InstaChecker Team  
**Лицензия:** MIT  
**Статус:** ✅ Production Ready

