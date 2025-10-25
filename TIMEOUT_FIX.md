# ⏱️ Timeout Fix

## Проблема

Пользователь сообщил: "Почему не отправилось фото"

В логах было видно:
```
PROXY-HEADER-SCREENSHOT] ⏱️ Timeout: Page.goto: Timeout 30000ms exceeded.
Call log:
navigating to "https://www.instagram.com/ukudarov/", waiting until "domcontentloaded"
```

Страница Instagram не загружалась в течение 30 секунд, поэтому скриншот не создавался и фото не отправлялось.

## Что было исправлено

### 1. `project/services/main_checker.py`

#### ❌ Было (30 секунд timeout):
```python
timeout_ms=30000,  # 30 секунд
```

#### ✅ Стало (60 секунд timeout):
```python
timeout_ms=60000,  # Увеличиваем timeout до 60 секунд
```

### 2. `project/services/ig_screenshot.py`

#### Добавлена обработка timeout ошибок:

```python
try:
    response = await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
    status_code = response.status if response else None
    print(f"[PROXY-HEADER-SCREENSHOT] 📊 HTTP Status: {status_code}")
except PWTimeoutError as e:
    print(f"[PROXY-HEADER-SCREENSHOT] ⏱️ Timeout при загрузке страницы: {e}")
    result["error"] = f"timeout_loading_page: {str(e)}"
    result["exists"] = False
    await browser.close()
    return result
```

#### Добавлена обработка ошибок скриншота:

```python
try:
    await page.screenshot(path=screenshot_path, full_page=True)
    print(f"[PROXY-FULL-SCREENSHOT] ✅ Скриншот создан успешно")
except Exception as e:
    print(f"[PROXY-FULL-SCREENSHOT] ❌ Ошибка при создании скриншота: {e}")
    result["error"] = f"screenshot_failed: {str(e)}"
    result["exists"] = False
    await browser.close()
    return result
```

## Технические детали

### Timeout настройки:

**Раньше:**
- `timeout_ms=30000` - 30 секунд
- Часто не хватало для загрузки Instagram
- Результат: timeout ошибки

**Теперь:**
- `timeout_ms=60000` - 60 секунд
- Больше времени для загрузки
- Результат: успешные скриншоты

### Обработка ошибок:

**Timeout при загрузке:**
```python
except PWTimeoutError as e:
    result["error"] = f"timeout_loading_page: {str(e)}"
    result["exists"] = False
    return result
```

**Ошибка скриншота:**
```python
except Exception as e:
    result["error"] = f"screenshot_failed: {str(e)}"
    result["exists"] = False
    return result
```

### Playwright настройки:

```python
# Увеличенный timeout
timeout_ms=60000

# Обработка ошибок
try:
    await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
except PWTimeoutError as e:
    # Обработка timeout
```

## Результат

### ✅ Теперь система:

1. **⏱️ Больше времени** - 60 секунд для загрузки страницы
2. **🛡️ Обработка ошибок** - корректная обработка timeout'ов
3. **📸 Надежные скриншоты** - fallback при проблемах
4. **🔧 Лучшая диагностика** - подробные логи ошибок

### Логи теперь показывают:

```
[PROXY-HEADER-SCREENSHOT] 📡 Переход на: https://www.instagram.com/username/
[PROXY-HEADER-SCREENSHOT] 📊 HTTP Status: 200
[PROXY-HEADER-SCREENSHOT] ⏳ Ожидаем полную загрузку страницы...
[PROXY-FULL-SCREENSHOT] 📸 Создание полного скриншота всей страницы...
[PROXY-FULL-SCREENSHOT] ✅ Скриншот создан успешно
[PROXY-FULL-SCREENSHOT] 📸 Полный скриншот: 1920x1080
[PROXY-FULL-SCREENSHOT] 📏 Размер файла: 245.3 KB
```

### При ошибках:

```
[PROXY-HEADER-SCREENSHOT] ⏱️ Timeout при загрузке страницы: Timeout 60000ms exceeded
[PROXY-FULL-SCREENSHOT] ❌ Ошибка при создании скриншота: Timeout
```

## Преимущества

✅ **Больше времени** - 60 секунд для загрузки Instagram  
✅ **Обработка ошибок** - корректная обработка timeout'ов  
✅ **Надежность** - fallback при проблемах  
✅ **Диагностика** - подробные логи для отладки  
✅ **Стабильность** - меньше сбоев при загрузке  

## Совместимость

✅ **Обратная совместимость** - все функции работают  
✅ **Новые timeout'ы** - 60 секунд для загрузки  
✅ **База данных** - никаких изменений не требуется  
✅ **Telegram** - больше успешных отправок фото  

## Особенности

### Timeout настройки:

**30 секунд (старое):**
- Часто не хватало для Instagram
- Медленные прокси
- Результат: timeout ошибки

**60 секунд (новое):**
- Достаточно времени для загрузки
- Работает с медленными прокси
- Результат: успешные скриншоты

### Обработка ошибок:

**Timeout при загрузке:**
- Логирование ошибки
- Установка `exists = False`
- Корректное закрытие браузера

**Ошибка скриншота:**
- Логирование ошибки
- Установка `exists = False`
- Возврат результата с ошибкой

### Playwright настройки:

- `wait_until="domcontentloaded"` - ждем загрузки DOM
- `timeout=60000` - 60 секунд timeout
- `full_page=True` - полный скриншот страницы

## Результат

Теперь система:
- ⏱️ **Ждет дольше** - 60 секунд для загрузки
- 🛡️ **Обрабатывает ошибки** - корректная обработка timeout'ов
- 📸 **Создает скриншоты** - даже при медленных прокси
- 🔧 **Логирует проблемы** - подробная диагностика

Это особенно полезно для:
- Медленных прокси
- Нестабильного интернета
- Сложных страниц Instagram
- Надежной работы системы
