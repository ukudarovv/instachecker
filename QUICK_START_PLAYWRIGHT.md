# 🚀 Быстрый старт с Playwright

## 📦 Установка (1 минута)

```bash
# Установка Playwright
pip install playwright

# Установка Chromium браузера
playwright install chromium
```

## ✅ Проверка установки

```bash
# Быстрый тест без прокси
python test_playwright_instagram.py gid_halal

# Результат: ✅ Профиль найден, скриншот создан
```

## 🔗 Тест с прокси

```bash
# Тест с прокси (жестко заданный в коде)
python test_playwright_with_proxy.py gid_halal

# Результат: ✅ Профиль найден через прокси!
```

## 💻 Использование в коде

### Вариант 1: Напрямую через Playwright

```python
from project.services.instagram_playwright import check_account_with_playwright

# Без прокси
result = await check_account_with_playwright(
    username="gid_halal",
    screenshot_path="screenshot.png",
    headless=True
)

# С прокси
result = await check_account_with_playwright(
    username="gid_halal",
    screenshot_path="screenshot.png",
    headless=True,
    proxy="http://user:pass@host:port"
)

print(f"✅ Профиль существует: {result['exists']}")
print(f"📸 Скриншот: {result['screenshot_path']}")
```

### Вариант 2: Через гибридную систему (рекомендуется)

```python
from project.services.instagram_hybrid_proxy import check_account_with_hybrid_proxy

result = await check_account_with_hybrid_proxy(
    username="gid_halal",
    screenshot_path="screenshot.png",
    proxy="http://user:pass@host:port"
)

# Автоматически использует:
# 1. API проверку через прокси
# 2. Playwright скриншот (с fallback на Firefox)
```

## 🎯 Что дальше?

1. **Все работает!** - Playwright интегрирован и протестирован
2. **Прокси работает!** - Нативная поддержка аутентификации
3. **Модальные окна закрываются!** - Агрессивное JavaScript удаление
4. **Fallback есть!** - Автоматический переход на Firefox при ошибках

## 📊 Результаты

### Тест без прокси:
```
✅ Профиль @gid_halal найден
📊 Статус код: 200
📸 Скриншот: 47 KB (отличное качество)
⏱️ Время: ~5 секунд
```

### Тест с прокси:
```
✅ Профиль @gid_halal найден
📊 Статус код: 200
📸 Скриншот: 19 KB (хорошее качество)
🔗 Прокси: Работает с аутентификацией
⏱️ Время: ~8 секунд
```

## 🎉 Готово!

**Playwright успешно интегрирован и работает!**

Для более подробной информации смотрите [PLAYWRIGHT_SUCCESS.md](PLAYWRIGHT_SUCCESS.md)

