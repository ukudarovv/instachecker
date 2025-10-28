# 🚀 Quick Start: Telegram Bot Integration

## ✅ Что было сделано

### 1. Интегрирован ProxyManager
- **Файлы изменены:**
  - `project/services/triple_checker.py` ✅
  - `project/services/hybrid_checker.py` ✅
  - `project/cron/auto_checker.py` ✅
  - `project/bot.py` ✅

**Что это дает:**
- ✅ **Каждый раз разный прокси** (adaptive selection)
- ✅ Автоматическая ротация при неудачах
- ✅ Cooldown неработающих прокси (15 минут)
- ✅ Деактивация после 5 неудач подряд

### 2. Запущен ProxyHealthChecker
- **Автоматический мониторинг** каждые 5 минут
- **Деактивация** мертвых прокси
- **Реактивация** восстановленных прокси

### 3. Все готово к работе!

---

## 🎯 Как это работает

### При добавлении или проверке аккаунта:

```
1. User нажимает "Проверить аккаунт"
   ↓
2. ProxyManager.get_best_proxy(user_id, strategy='adaptive')
   → Выбирает ЛУЧШИЙ прокси на основе:
      - Success rate (70% веса)
      - Количество использований (20% веса)
      - Priority (10% веса)
   ↓
3. Используется выбранный прокси для проверки
   ↓
4. После проверки:
   ✅ Success → manager.mark_success(proxy_id)
   ❌ Failure → manager.mark_failure(proxy_id)
   ↓
5. При следующей проверке:
   → Выбирается ДРУГОЙ прокси (с учетом статистики)
```

### Каждый раз РАЗНЫЙ прокси!

**Алгоритм выбора:**
- 90% времени: выбирается **лучший** прокси
- 10% времени: **случайный** прокси (exploration)

Это обеспечивает:
- ✅ Использование успешных прокси
- ✅ Ротацию между прокси
- ✅ Проверку новых/восстановленных прокси

---

## 📥 Импорт ваших прокси (из списка DeepSeek)

### Шаг 1: Создайте файл `proxies.txt`

```bash
82.24.225.134:7975:aiiigauk:pi8vftb70eic
46.202.227.191:6185:aiiigauk:pi8vftb70eic
66.78.34.158:5777:aiiigauk:pi8vftb70eic
107.181.141.85:6482:aiiigauk:pi8vftb70eic
192.186.151.73:8574:aiiigauk:pi8vftb70eic
50.114.84.92:7331:aiiigauk:pi8vftb70eic
198.20.191.196:5266:aiiigauk:pi8vftb70eic
... (весь ваш список)
```

### Шаг 2: Импортируйте через скрипт

```bash
python batch_add_proxies.py --user-id YOUR_USER_ID --file proxies.txt --test
```

**Что произойдет:**
1. ✅ Парсинг всех прокси из файла
2. ✅ Добавление в БД (пропуск дубликатов)
3. ✅ Автоматическое тестирование каждого прокси
4. ✅ Статистика: сколько рабочих/нерабочих

**Пример вывода:**
```
📁 Reading proxies from file: proxies.txt
📥 Importing proxies for user 1...
============================================================
[PROXY-MANAGER] 📋 Parsed 100 proxies from 100 lines
[PROXY-MANAGER] ➕ Added proxy 82.24.225.134:7975
[PROXY-MANAGER] ➕ Added proxy 46.202.227.191:6185
...
============================================================
📊 Import Summary:
   ✅ Added: 100
   ⏭️  Skipped (duplicates): 0
   ❌ Errors: 0
============================================================

🧪 Testing imported proxies...
============================================================
[PROXY-HEALTH] ✅ Proxy 82.24.225.134 healthy (3.25s)
[PROXY-HEALTH] ❌ Proxy 46.202.227.191 unhealthy
...
📊 Test Results:
   ✅ Healthy: 87/100
   ❌ Unhealthy: 13/100
============================================================
```

---

## 🚀 Запуск бота

```bash
python run_bot.py
```

**Что произойдет:**
```
[INFO] Starting bot...
[INFO] Database initialized
[INFO] Bot created
[INFO] APScheduler auto-checker started (every 5 minutes)
🏥 Starting Proxy Health Checker (checks every 5 minutes)...
✅ Proxy Health Checker started in background
[INFO] Expiry notification scheduler started
[INFO] Bot started successfully
[INFO] Polling updates...
```

Бот запущен! 🎉

---

## 🧪 Тестирование в Telegram

### 1. Проверка аккаунта через бота

1. Откройте бот в Telegram
2. Нажмите **"Проверить через Proxy"** (или любой другой режим)
3. Введите username: `test_username`

**Что произойдет в логах:**
```
[HYBRID-CHECK] 🔧 Режим проверки: api+proxy для @test_username
🔗 Selected best proxy: 82.24.225.134:7975
📊 Stats: 5/8 successful
... проверка ...
✅ Marked proxy 82.24.225.134:7975 as successful
```

### 2. Следующая проверка

1. Проверьте еще один аккаунт
2. Посмотрите логи

**Должен выбраться ДРУГОЙ прокси:**
```
[HYBRID-CHECK] 🔧 Режим проверки: api+proxy для @another_user
🔗 Selected best proxy: 66.78.34.158:5777  ← ДРУГОЙ прокси!
📊 Stats: 3/5 successful
```

### 3. Просмотр статистики

Добавьте команду в бота (опционально):

```python
@bot.message_handler(lambda m: m.text == "📊 Статистика прокси")
async def show_stats(message):
    from project.services.proxy_manager import ProxyManager
    
    user_id = message.from_user.id
    
    with SessionLocal() as session:
        manager = ProxyManager(session)
        stats = manager.get_proxy_stats(user_id)
        best = manager.get_best_proxies(user_id, top_n=5)
        
        text = f"""
📊 **Статистика прокси**

Всего: {stats['total']}
✅ Активные: {stats['active']}
❌ Неактивные: {stats['inactive']}
⏸️ В cooldown: {stats['in_cooldown']}

📈 Success rate: {stats['success_rate']}%

🔝 **Топ-5 прокси:**
"""
        
        for i, proxy in enumerate(best, 1):
            text += f"\n{i}. {proxy['host']}"
            text += f"\n   ✅ {proxy['success_rate']}% успеха"
        
        await message.answer(text)
```

---

## 🔍 Мониторинг работы

### 1. Проверить, что ProxyHealthChecker работает

Посмотрите логи бота через ~5-10 минут:

```
[PROXY-HEALTH] 🔍 Starting health check...
[PROXY-HEALTH] 🔍 Checking 100 proxies for user 1...
[PROXY-HEALTH] ✅ Proxy 82.24.225.134 healthy (2.15s)
[PROXY-HEALTH] ❌ Proxy 46.202.227.191 unhealthy
...
[PROXY-HEALTH] 📊 Check complete:
[PROXY-HEALTH]   ✅ Healthy: 87
[PROXY-HEALTH]   ❌ Unhealthy: 13
[PROXY-HEALTH]   🚫 Deactivated: 2
[PROXY-HEALTH]   ⏸️ In cooldown: 5
[PROXY-HEALTH]   ⏱️ Duration: 125.3s
[PROXY-HEALTH] 😴 Sleeping for 300s...
```

### 2. Проверить статистику прокси

```bash
python -c "
from project.database import get_session_factory
from project.services.proxy_manager import ProxyManager

SessionLocal = get_session_factory()

with SessionLocal() as session:
    manager = ProxyManager(session)
    
    # Статистика
    stats = manager.get_proxy_stats(user_id=1)
    print(f'📊 Статистика:')
    print(f'   Всего: {stats[\"total\"]}')
    print(f'   Активные: {stats[\"active\"]}')
    print(f'   Success rate: {stats[\"success_rate\"]}%')
    
    # Топ-5
    print(f'\n🔝 Топ-5 прокси:')
    best = manager.get_best_proxies(1, top_n=5)
    for i, proxy in enumerate(best, 1):
        print(f'{i}. {proxy[\"host\"]}: {proxy[\"success_rate\"]}%')
"
```

---

## ❓ FAQ & Troubleshooting

### Q: Прокси не ротируются?
**A:** Проверьте логи - должна быть строка `"Selected best proxy: ..."` с **разными** IP.

### Q: Все прокси в cooldown?
**A:** Сбросьте cooldown:
```bash
python -c "
from project.database import get_session_factory
from project.services.proxy_manager import ProxyManager

SessionLocal = get_session_factory()
with SessionLocal() as session:
    manager = ProxyManager(session)
    count = manager.reset_cooldowns(user_id=1)
    print(f'✅ Reset {count} proxies')
"
```

### Q: Как вручную проверить прокси?
**A:**
```bash
python -c "
import asyncio
from project.database import get_session_factory
from project.services.proxy_manager import test_all_user_proxies

async def test():
    SessionLocal = get_session_factory()
    with SessionLocal() as session:
        results = await test_all_user_proxies(session, user_id=1)
        print(f'Working: {results[\"working\"]}/{results[\"total\"]}')

asyncio.run(test())
"
```

### Q: Прокси не добавляются из списка?
**A:** Проверьте формат. Должен быть: `ip:port:username:password` (один прокси на строку)

---

## 📊 Ожидаемое поведение

### Первые 20-30 проверок:
- ✅ Система **учится** - выбирает разные прокси
- ✅ Собирает статистику успешности
- ✅ 10% времени - случайный выбор (exploration)

### После 50+ проверок:
- ✅ Система **оптимизирована** - выбирает лучшие прокси
- ✅ Автоматическая деактивация плохих прокси
- ✅ Success rate должен быть 80-90%

### Через неделю:
- ✅ Стабильная работа с лучшими прокси
- ✅ Автоматическое восстановление прокси
- ✅ Минимум ручной работы

---

## 🎉 Готово!

Теперь ваш бот:
- ✅ **Автоматически выбирает разный прокси** при каждой проверке
- ✅ **Учится** на результатах проверок
- ✅ **Мониторит** здоровье прокси каждые 5 минут
- ✅ **Деактивирует** мертвые прокси автоматически
- ✅ **Реактивирует** восстановленные прокси

Все работает **автоматически**, без вашего участия! 🚀

---

## 📞 Следующие шаги

1. ✅ Импортируйте прокси: `python batch_add_proxies.py --user-id 1 --file proxies.txt --test`
2. ✅ Запустите бота: `python run_bot.py`
3. ✅ Проверьте несколько аккаунтов через Telegram
4. ✅ Посмотрите логи - прокси должны ротироваться
5. ✅ Подождите 5-10 минут - ProxyHealthChecker сделает первую проверку
6. ✅ Наслаждайтесь автоматической работой! 🎉

**Вопросы?** Пишите! Готов помочь с любыми проблемами! 💪





