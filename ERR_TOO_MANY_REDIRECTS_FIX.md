# Исправление ошибки ERR_TOO_MANY_REDIRECTS

## Проблема

Из логов видно ошибку:
```
net::ERR_TOO_MANY_REDIRECTS at https://www.instagram.com/[username]/
```

Это означает, что Instagram блокирует запросы из-за:
1. **Слишком частых обращений** - rate limiting
2. **Детекции автоматизации** - одинаковые User-Agent
3. **Подозрительной активности** - множественные параллельные запросы

## Внесенные исправления

### 1. `project/services/ig_simple_checker.py`

#### Добавлена ротация User-Agent
```python
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit...",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36..."
]
user_agent=random.choice(user_agents)
```

#### Добавлены дополнительные HTTP заголовки
```python
extra_http_headers={
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9...",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}
```

#### Добавлены флаги браузера против детекции
```python
args=[
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-web-security",
    "--disable-features=VizDisplayCompositor",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding"
]
```

#### Добавлена retry логика с обработкой редиректов
```python
max_retries = 3
for attempt in range(max_retries):
    try:
        # Clear redirects
        await page.evaluate("() => { window.history.replaceState(null, '', '/'); }")
        
        # Navigate with networkidle
        await page.goto(url, wait_until="networkidle", timeout=timeout_ms)
        
        # Wait 5 seconds for page load
        await page.wait_for_timeout(5000)
        
        # Check for unwanted redirects
        if current_url != url and username not in current_url:
            # Retry logic...
            
    except Exception as e:
        if "ERR_TOO_MANY_REDIRECTS" in str(e):
            # Wait 15 seconds and retry
            await page.wait_for_timeout(15000)
            continue
```

### 2. `project/cron/auto_checker.py`

#### Критически уменьшена параллельность
```python
semaphore = asyncio.Semaphore(1)  # Только 1 проверка за раз
```

#### Значительно увеличена задержка
```python
await asyncio.sleep(30)  # 30 секунд между проверками
```

## Ожидаемые результаты

### ✅ Устранение ERR_TOO_MANY_REDIRECTS
- Retry логика обрабатывает редиректы
- Очистка истории перед каждой попыткой
- Увеличенные таймауты

### ✅ Снижение детекции автоматизации
- Случайные User-Agent
- Реалистичные HTTP заголовки
- Дополнительные флаги браузера

### ✅ Минимизация rate limiting
- Только 1 проверка одновременно
- 30 секунд между проверками
- 5 секунд ожидания загрузки страницы

## Мониторинг

### Успешная проверка:
```
🔍 Attempt 1/3 to navigate to @username
🔍 Current URL after navigation: https://www.instagram.com/username/
✅ Profile @username found with data
```

### Retry при редиректах:
```
🔍 Attempt 1/3 to navigate to @username
⚠️ Too many redirects on attempt 1: ERR_TOO_MANY_REDIRECTS
🔄 Waiting 15 seconds before retry...
🔍 Attempt 2/3 to navigate to @username
✅ Profile @username found with data
```

### Полная блокировка:
```
🔍 Attempt 1/3 to navigate to @username
⚠️ Too many redirects on attempt 1: ERR_TOO_MANY_REDIRECTS
🔄 Waiting 15 seconds before retry...
🔍 Attempt 2/3 to navigate to @username
⚠️ Too many redirects on attempt 2: ERR_TOO_MANY_REDIRECTS
🔄 Waiting 15 seconds before retry...
🔍 Attempt 3/3 to navigate to @username
⚠️ Too many redirects on attempt 3: ERR_TOO_MANY_REDIRECTS
❌ ERR_TOO_MANY_REDIRECTS after 3 attempts
```

## Производительность

### Время проверки:
- **Раньше**: ~10-15 секунд на аккаунт (3 параллельно)
- **Теперь**: ~40-45 секунд на аккаунт (1 последовательно)
- **Задержка**: 30 секунд между аккаунтами

### Расчет времени:
- 100 аккаунтов = 100 × 45 секунд = 75 минут
- 200 аккаунтов = 200 × 45 секунд = 150 минут (2.5 часа)

## Рекомендации

### 1. Если проблема сохраняется:
```python
# Увеличить задержку до 60 секунд
await asyncio.sleep(60)

# Или увеличить интервал автопроверки до 10-15 минут
interval_minutes = 10
```

### 2. Использовать прокси (опционально):
```python
# Добавить в browser.new_context()
proxy={"server": "http://proxy-server:port"}
```

### 3. Ротировать Instagram сессии:
- Использовать разные аккаунты для проверок
- Распределять нагрузку между сессиями

### 4. Мониторинг блокировок:
```bash
# В логах ищите:
grep "ERR_TOO_MANY_REDIRECTS" /var/log/instagram-bot.log
grep "Too many redirects" /var/log/instagram-bot.log
```

## Временные меры

Если ошибки продолжаются:

1. **Остановить автопроверку на 1-2 часа**
2. **Увеличить интервал до 30-60 минут**
3. **Использовать только API проверки** (временно)
4. **Проверить качество Instagram сессий**

## Альтернативные решения

### Вариант 1: Только API проверки
```python
# В hybrid_checker.py временно отключить Instagram проверки
if False and ig_session and fernet:  # Отключено
```

### Вариант 2: Увеличить интервал
```python
# В auto_checker.py
interval_minutes = 30  # Проверка каждые 30 минут
```

### Вариант 3: Проверка только в рабочее время
```python
# Проверять только с 9:00 до 18:00
if datetime.now().hour < 9 or datetime.now().hour > 18:
    return  # Пропустить проверку
```
