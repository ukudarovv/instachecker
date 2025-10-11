# 🐧 Обновление на Linux сервере

## 📋 **Пошаговая инструкция обновления до APScheduler**

### **Шаг 1: Подключитесь к серверу**

```bash
ssh root@your-server-ip
```

---

### **Шаг 2: Остановите бота**

```bash
# Найдите процесс бота
ps aux | grep python

# Остановите его (замените PID на реальный)
kill <PID>

# Или принудительно
pkill -f "python.*run_bot.py"

# Подождите пару секунд
sleep 2
```

---

### **Шаг 3: Перейдите в директорию проекта**

```bash
cd ~/test_bot/instachecker
```

---

### **Шаг 4: Обновите код из GitHub**

```bash
# Получите последнюю версию
git fetch origin

# Переключитесь на master ветку
git checkout master

# Стяните изменения
git pull origin master
```

**Ожидаемый вывод:**
```
remote: Enumerating objects...
remote: Counting objects...
remote: Compressing objects...
Unpacking objects: 100% (11/11), done.
From https://github.com/ukudarovv/instachecker
   e934265..ad3126d  master     -> origin/master
Updating e934265..ad3126d
Fast-forward
 APSCHEDULER_MIGRATION.md         | 410 +++++++++
 CHANGELOG_APSCHEDULER.md         | 302 +++++++
 project/auto_checker_scheduler.py| 123 +++
 project/bot.py                   |  25 +-
 README.md                        |  26 +-
 requirements.txt                 |   2 +
 update_to_apscheduler.bat        |  54 ++
 update_to_apscheduler.sh         |  48 ++
 8 files changed, 762 insertions(+), 30 deletions(-)
```

---

### **Шаг 5: Активируйте виртуальное окружение**

```bash
source venv/bin/activate
```

**Проверка:** В начале строки должно появиться `(venv)`

---

### **Шаг 6: Обновите зависимости**

```bash
# Обновите pip
pip install --upgrade pip

# Установите новые зависимости
pip install -r requirements.txt
```

**Важные строки в выводе:**
```
Collecting APScheduler==3.10.4
  Downloading APScheduler-3.10.4-py3-none-any.whl
Collecting aiohttp==3.9.5
  Downloading aiohttp-3.9.5-cp311-cp311-manylinux_2_17_x86_64.whl
Installing collected packages: APScheduler, aiohttp
Successfully installed APScheduler-3.10.4 aiohttp-3.9.5
```

---

### **Шаг 7: Проверьте установку**

```bash
# Проверьте APScheduler
python3 -c "import apscheduler; print(f'✅ APScheduler: {apscheduler.__version__}')"

# Проверьте aiohttp
python3 -c "import aiohttp; print(f'✅ aiohttp: {aiohttp.__version__}')"

# Проверьте наличие нового файла
ls -la project/auto_checker_scheduler.py
```

**Ожидаемый вывод:**
```
✅ APScheduler: 3.10.4
✅ aiohttp: 3.9.5
-rw-r--r-- 1 root root 4567 Oct 11 18:00 project/auto_checker_scheduler.py
```

---

### **Шаг 8: Запустите бота**

```bash
python3 run_bot.py
```

**Ожидаемые логи:**
```
2025-10-11 18:00:00,000 | INFO | bot | Starting bot...
2025-10-11 18:00:00,100 | INFO | bot | Database initialized
2025-10-11 18:00:00,150 | INFO | bot | Bot created
[AUTO-CHECK-SCHEDULER] Initialized (interval: 5 minutes)
[AUTO-CHECK-SCHEDULER] Scheduler started (every 5 minutes)
2025-10-11 18:00:00,200 | INFO | bot | APScheduler auto-checker started (every 5 minutes)
2025-10-11 18:00:00,250 | INFO | bot | Next check scheduled at: 2025-10-11 18:05:00
2025-10-11 18:00:00,300 | INFO | bot | Starting polling...
[AUTO-CHECK-SCHEDULER] Running immediate initial check...
[AUTO-CHECK-SCHEDULER] Starting check at 2025-10-11 18:00:00
```

---

### **Шаг 9: Проверьте работу в фоне (опционально)**

Если хотите запустить в фоне с автоперезапуском:

```bash
# Остановите текущий процесс (Ctrl+C)

# Установите screen (если еще не установлен)
apt-get install -y screen

# Создайте новую сессию screen
screen -S instachecker

# Запустите бота в screen
python3 run_bot.py

# Отсоединитесь от screen (нажмите Ctrl+A, затем D)
# Бот продолжит работать в фоне

# Чтобы вернуться к боту:
screen -r instachecker
```

---

### **Шаг 10: Проверьте автопроверку через 5 минут**

Подождите 5 минут и проверьте логи:

```bash
# Если бот работает в screen:
screen -r instachecker

# Вы должны увидеть:
[AUTO-CHECK-SCHEDULER] Starting check at 2025-10-11 18:05:00
[AUTO-CHECK] Found X pending accounts to check.
[AUTO-CHECK] Checking @username1...
[AUTO-CHECK] ✅ @username1 - FOUND
[AUTO-CHECK-SCHEDULER] Check completed at 2025-10-11 18:08:00
```

---

## 🔧 **Альтернативный способ: Использовать готовый скрипт**

```bash
# Сделайте скрипт исполняемым
chmod +x update_to_apscheduler.sh

# Запустите его
./update_to_apscheduler.sh
```

Скрипт автоматически выполнит все шаги!

---

## 🐛 **Решение проблем**

### **Проблема 1: "git pull" не работает**

```bash
# Сбросьте локальные изменения (ОСТОРОЖНО!)
git reset --hard HEAD
git pull origin master
```

### **Проблема 2: "pip install" ошибки компиляции**

```bash
# Установите системные зависимости
apt-get update
apt-get install -y python3-dev gcc

# Попробуйте снова
pip install -r requirements.txt
```

### **Проблема 3: Бот не запускается**

```bash
# Проверьте .env файл
cat .env

# Убедитесь, что BOT_TOKEN заполнен
grep BOT_TOKEN .env

# Проверьте синтаксис Python
python3 -m py_compile project/bot.py
python3 -m py_compile project/auto_checker_scheduler.py
```

### **Проблема 4: Playwright браузеры не установлены**

```bash
# Установите браузеры
playwright install chromium

# Установите системные зависимости
playwright install-deps chromium
```

### **Проблема 5: Автопроверка не запускается**

```bash
# Проверьте интервал в БД
python3 << 'EOF'
from project.database import get_engine, get_session_factory
from project.config import get_settings
from project.services.system_settings import get_auto_check_interval

settings = get_settings()
engine = get_engine(settings.db_url)
SessionLocal = get_session_factory(engine)

with SessionLocal() as session:
    interval = get_auto_check_interval(session)
    print(f"Auto-check interval: {interval} minutes")
EOF
```

---

## ✅ **Проверка успешного обновления**

Чек-лист для проверки:

- [ ] Бот запустился без ошибок
- [ ] В логах есть строка `[AUTO-CHECK-SCHEDULER] Initialized`
- [ ] В логах есть строка `APScheduler auto-checker started`
- [ ] Видно время следующей проверки `Next check scheduled at:`
- [ ] Запустилась немедленная проверка `Running immediate initial check...`
- [ ] Через 5 минут запустилась автоматическая проверка
- [ ] Админ получил уведомление о начале проверки
- [ ] Пользователи получают уведомления о найденных аккаунтах
- [ ] Скриншоты отправляются корректно

---

## 📊 **Мониторинг работы**

### **Проверка процесса:**

```bash
# Посмотрите запущенные процессы бота
ps aux | grep "python.*run_bot"

# Посмотрите использование ресурсов
top -p $(pgrep -f "python.*run_bot")
```

### **Проверка логов в реальном времени:**

```bash
# Если бот запущен не в screen, перенаправьте вывод в файл:
python3 run_bot.py > bot.log 2>&1 &

# Следите за логами
tail -f bot.log
```

### **Проверка работы планировщика:**

```bash
# Посмотрите последние логи автопроверки
grep "AUTO-CHECK-SCHEDULER" bot.log | tail -20
```

---

## 🔄 **Откат на предыдущую версию (если нужно)**

Если что-то пошло не так:

```bash
# Остановите бота
pkill -f "python.*run_bot"

# Откатитесь на предыдущий коммит
git reset --hard e934265

# Переустановите старые зависимости
pip install -r requirements.txt

# Запустите бота
python3 run_bot.py
```

---

## 🎉 **Готово!**

Если все чек-боксы отмечены — обновление прошло успешно!

Автопроверка теперь работает на **APScheduler** — надежном промышленном планировщике задач.

**Наслаждайтесь стабильной работой!** 🚀

