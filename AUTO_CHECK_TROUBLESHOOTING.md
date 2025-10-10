# 🔧 Диагностика автопроверки

## ❌ **Проблема:** Автопроверка каждые 15 минут не запускается

## ✅ **Исправления:**

### **1. Исправлен интервал по умолчанию в auto_checker.py:**
```python
# Было:
def start_auto_checker(SessionLocal: sessionmaker, bot=None, interval_minutes: int = 5, run_immediately: bool = True):

# Стало:
def start_auto_checker(SessionLocal: sessionmaker, bot=None, interval_minutes: int = 15, run_immediately: bool = True):
```

### **2. Добавлено улучшенное логирование:**
```python
# При запуске автопроверки:
print(f"[AUTO-CHECK] Started automatic checker (every {interval_minutes} minutes, checking ALL accounts)")
print(f"[AUTO-CHECK] Next check will be at: {datetime.now() + timedelta(minutes=interval_minutes)}")

# При срабатывании cron job:
print(f"[AUTO-CHECK] Cron job triggered at {datetime.now()}")
print(f"[AUTO-CHECK] Cron job completed at {datetime.now()}")
```

---

## 🔍 **Диагностика:**

### **1. Проверка текущего интервала в БД:**
```bash
python -c "import sys; sys.path.insert(0, 'project'); from config import get_settings; from database import get_engine, get_session_factory; from services.system_settings import get_auto_check_interval; settings = get_settings(); engine = get_engine(settings.db_url); SessionLocal = get_session_factory(engine); session = SessionLocal(); print(f'Current interval: {get_auto_check_interval(session)} minutes'); session.close()"
```

**Результат:** `Current interval: 15 minutes` ✅

### **2. Проверка запущенных процессов:**
```bash
tasklist | findstr python
```

### **3. Перезапуск бота:**
```bash
# Остановка всех процессов
taskkill /f /im python.exe

# Запуск с логированием
.venv\Scripts\activate
python run_bot.py
```

---

## 📊 **Что должно происходить:**

### **При запуске бота:**
```
[AUTO-CHECK] Running initial full check immediately...
[AUTO-CHECK] Started automatic checker (every 15 minutes, checking ALL accounts)
[AUTO-CHECK] Next check will be at: 2025-10-10 15:30:00
```

### **Каждые 15 минут:**
```
[AUTO-CHECK] Cron job triggered at 2025-10-10 15:30:00
🔄 Автопроверка запущена (админу)
[AUTO-CHECK] Found 137 pending accounts to check.
[AUTO-CHECK] Checking @account1...
[AUTO-CHECK] Checking @account2...
...
✅ Автопроверка завершена (админу)
[AUTO-CHECK] Cron job completed at 2025-10-10 15:35:00
```

---

## 🚀 **Проверка работы:**

### **1. Запустите бота:**
```bash
.venv\Scripts\activate
python run_bot.py
```

### **2. Проверьте логи:**
Должны появиться сообщения:
- `[AUTO-CHECK] Started automatic checker (every 15 minutes, checking ALL accounts)`
- `[AUTO-CHECK] Next check will be at: [время]`

### **3. Дождитесь первого cron job:**
Через 15 минут должны появиться:
- `[AUTO-CHECK] Cron job triggered at [время]`
- Уведомление админу о запуске автопроверки

### **4. Проверьте уведомления админу:**
Админ должен получить:
```
🔄 Автопроверка запущена

📊 Аккаунтов к проверке: 137
⏰ Время: 15:30:00
```

---

## 🔧 **Возможные причины проблем:**

### **1. Бот запущен со старыми настройками:**
**Решение:** Перезапустить бота

### **2. Интервал по умолчанию был 5 минут:**
**Решение:** ✅ Исправлено на 15 минут

### **3. Проблемы с aiocron:**
**Решение:** Добавлено логирование для диагностики

### **4. Проблемы с event loop:**
**Решение:** Используется правильная настройка loop в aiocron

---

## 📝 **Чек-лист диагностики:**

- [ ] ✅ **Интервал в БД:** 15 минут
- [ ] ✅ **Интервал по умолчанию:** 15 минут  
- [ ] ✅ **Логирование:** Добавлено
- [ ] ✅ **Бот перезапущен:** Да
- [ ] ⏳ **Ждем первый cron job:** Через 15 минут

---

## 🎯 **Ожидаемый результат:**

После исправлений автопроверка должна:
1. ✅ **Запускаться каждые 15 минут**
2. ✅ **Уведомлять админа при запуске**
3. ✅ **Показывать логи в консоли**
4. ✅ **Проверять ВСЕ pending аккаунты**

**Следите за логами в консоли для подтверждения работы!** 📊
