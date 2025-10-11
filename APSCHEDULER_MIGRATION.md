# 🔄 Миграция на APScheduler

## ✅ **Что изменилось:**

Автопроверка переделана с **Threading + asyncio** на **APScheduler** для более стабильной работы.

---

## 🎯 **Преимущества APScheduler:**

### **1. Надежность:**
- ✅ **Проверенная библиотека** — используется в промышленных проектах
- ✅ **Автоматическое восстановление** после ошибок
- ✅ **Предотвращение дублирования** задач (max_instances=1)
- ✅ **Объединение пропущенных запусков** (coalesce=True)

### **2. Производительность:**
- ✅ **Меньше нагрузка** на CPU
- ✅ **Нет создания лишних потоков**
- ✅ **Эффективное использование** asyncio event loop

### **3. Управляемость:**
- ✅ **Точное время** следующего запуска
- ✅ **Легко изменить интервал** без перезапуска
- ✅ **Простая отладка** и мониторинг

---

## 📦 **Установка:**

### **На локальной машине (Windows):**

```bash
# Активируйте venv
.venv\Scripts\activate

# Обновите зависимости
pip install -r requirements.txt

# Запустите бота
python run_bot.py
```

### **На Linux сервере:**

```bash
# Перейдите в проект
cd ~/test_bot/instachecker

# Активируйте venv
source venv/bin/activate

# Обновите зависимости
pip install -r requirements.txt

# Запустите бота
python3 run_bot.py
```

---

## 🔧 **Что было удалено:**

- ❌ **project/auto_checker_threaded.py** — старый Threading подход
- ❌ **project/utils/bot_proxy.py** — больше не нужен
- ❌ **Сложная логика** с межпотоковым взаимодействием

---

## ✨ **Что добавлено:**

- ✅ **project/auto_checker_scheduler.py** — новый планировщик на APScheduler
- ✅ **APScheduler==3.10.4** в requirements.txt
- ✅ **aiohttp==3.9.5** для асинхронных HTTP запросов

---

## 🚀 **Как работает новый планировщик:**

### **1. Инициализация (при запуске бота):**

```python
_checker_scheduler = AutoCheckerScheduler(
    bot_token=settings.bot_token,
    SessionLocal=session_factory,
    interval_minutes=5,  # Интервал проверки
    run_immediately=True,  # Первая проверка сразу
)
_checker_scheduler.start()
```

### **2. Планирование задач:**

```python
# APScheduler создает задачу с интервалом
scheduler.add_job(
    self._check_job,  # Функция проверки
    trigger=IntervalTrigger(minutes=5),  # Каждые 5 минут
    max_instances=1,  # Только одна проверка одновременно
    coalesce=True,  # Пропущенные запуски объединяются
)
```

### **3. Выполнение проверки:**

```python
async def _check_job(self):
    await check_pending_accounts(
        SessionLocal=self._SessionLocal,
        bot=self._async_bot,  # AsyncBotWrapper для Telegram
        max_accounts=999999,
        notify_admin=True
    )
```

### **4. Логи при работе:**

```
[AUTO-CHECK-SCHEDULER] Initialized (interval: 5 minutes)
[AUTO-CHECK-SCHEDULER] Scheduler started (every 5 minutes)
[AUTO-CHECK-SCHEDULER] Next check scheduled at: 2025-10-11 17:30:00
[AUTO-CHECK-SCHEDULER] Running immediate initial check...
[AUTO-CHECK-SCHEDULER] Starting check at 2025-10-11 17:25:00
[AUTO-CHECK] Found 40 pending accounts to check.
[AUTO-CHECK] Checking @username1...
[AUTO-CHECK] ✅ @username1 - FOUND
[AUTO-CHECK-SCHEDULER] Check completed at 2025-10-11 17:28:00
```

---

## 📊 **Сравнение подходов:**

| Параметр | Threading + asyncio | APScheduler |
|----------|-------------------|-------------|
| **Надежность** | ⚠️ Средняя | ✅ Высокая |
| **Сложность кода** | ⚠️ Сложный | ✅ Простой |
| **Отладка** | ⚠️ Сложная | ✅ Легкая |
| **Производительность** | ⚠️ Средняя | ✅ Высокая |
| **Дублирование задач** | ⚠️ Возможно | ✅ Защита |
| **Интервалы < 5 мин** | ✅ Работает | ✅ Работает |
| **Мониторинг** | ⚠️ Ограничен | ✅ Полный |

---

## 🔍 **Проверка работы:**

### **1. Логи при запуске:**

```
2025-10-11 17:25:00,000 | INFO | bot | Starting bot...
2025-10-11 17:25:00,100 | INFO | bot | Database initialized
2025-10-11 17:25:00,150 | INFO | bot | Bot created
[AUTO-CHECK-SCHEDULER] Initialized (interval: 5 minutes)
[AUTO-CHECK-SCHEDULER] Scheduler started (every 5 minutes)
2025-10-11 17:25:00,200 | INFO | bot | APScheduler auto-checker started (every 5 minutes)
2025-10-11 17:25:00,250 | INFO | bot | Next check scheduled at: 2025-10-11 17:30:00
2025-10-11 17:25:00,300 | INFO | bot | Starting polling...
[AUTO-CHECK-SCHEDULER] Running immediate initial check...
```

### **2. Логи при проверке:**

```
[AUTO-CHECK-SCHEDULER] Starting check at 2025-10-11 17:30:00
[AUTO-CHECK] 2025-10-11 17:30:00.123 - Starting automatic check...
[AUTO-CHECK] Found 40 pending accounts to check.
[AUTO-CHECK] Checking @username1...
[AUTO-CHECK] ✅ @username1 - FOUND
[AUTO-CHECK] Completed!
  • Checked: 40
  • Found: 5
  • Not found: 35
  • Errors: 0
[AUTO-CHECK-SCHEDULER] Check completed at 2025-10-11 17:33:00
```

### **3. Уведомления админу:**

```
🔄 Автопроверка запущена

📊 Аккаунтов к проверке: 40
⏰ Время: 17:30:00
```

```
✅ Автопроверка завершена

📊 Результаты:
• Проверено: 40
• Найдено: 5
• Не найдено: 35
• Ошибок: 0

⏰ Завершено: 17:33:00
```

---

## ⚙️ **Изменение интервала:**

Интервал автопроверки настраивается через **админ-меню бота**:

1. Откройте бота в Telegram
2. Нажмите **"Админ панель"**
3. Выберите **"Интервал автопроверки"**
4. Введите новый интервал в минутах (например: `3`)
5. **Перезапустите бота** для применения изменений

---

## 🐛 **Отладка проблем:**

### **Проблема: Автопроверка не запускается**

```bash
# Проверьте, установлен ли APScheduler
pip show APScheduler

# Если нет, установите:
pip install APScheduler==3.10.4
```

### **Проблема: Ошибки при проверке аккаунтов**

```bash
# Проверьте, установлены ли браузеры Playwright
playwright install chromium
playwright install-deps chromium
```

### **Проблема: Scheduler не останавливается**

```bash
# Убедитесь, что бот остановлен корректно
# Нажмите Ctrl+C в терминале
# Подождите сообщение: "APScheduler auto-checker stopped"
```

---

## 📝 **Коммит изменений в Git:**

```bash
# На локальной машине
git add .
git commit -m "Migrate auto-checker to APScheduler for better reliability"
git push

# На сервере
cd ~/test_bot/instachecker
git pull
source venv/bin/activate
pip install -r requirements.txt
python3 run_bot.py
```

---

## 🎉 **Результат:**

- ✅ **Стабильная автопроверка** каждые 5 минут
- ✅ **Никаких пропущенных запусков**
- ✅ **Точное расписание**
- ✅ **Простая отладка**
- ✅ **Меньше нагрузка на сервер**

**APScheduler — это промышленный стандарт для планирования задач в Python!** 🚀

