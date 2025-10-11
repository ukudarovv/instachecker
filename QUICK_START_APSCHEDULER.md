# ⚡ Быстрый старт с APScheduler

## 🎯 **Что изменилось?**

Автопроверка Instagram аккаунтов теперь работает на **APScheduler** вместо Threading.

**Почему это важно:**
- ✅ **Надежнее** - не пропускает проверки
- ✅ **Быстрее** - меньше нагрузка на CPU
- ✅ **Проще** - легче отлаживать

---

## 🚀 **Для новых установок**

### **Windows:**

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/ukudarovv/instachecker.git
cd instachecker

# 2. Создайте venv
python -m venv .venv
.venv\Scripts\activate

# 3. Установите зависимости
pip install -r requirements.txt
playwright install chromium

# 4. Настройте .env
copy env.example .env
# Отредактируйте .env (добавьте BOT_TOKEN)

# 5. Запустите
python run_bot.py
```

### **Linux:**

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/ukudarovv/instachecker.git
cd instachecker

# 2. Создайте venv
python3 -m venv venv
source venv/bin/activate

# 3. Установите зависимости
pip install -r requirements.txt
playwright install chromium
playwright install-deps chromium

# 4. Настройте .env
cp env.example .env
nano .env  # Добавьте BOT_TOKEN

# 5. Запустите
python3 run_bot.py
```

---

## 🔄 **Для обновления существующих установок**

### **Windows:**

```bash
# Быстрый способ
update_to_apscheduler.bat

# ИЛИ вручную:
git pull
.venv\Scripts\activate
pip install -r requirements.txt
python run_bot.py
```

### **Linux:**

```bash
# Быстрый способ
./update_to_apscheduler.sh

# ИЛИ вручную:
git pull
source venv/bin/activate
pip install -r requirements.txt
python3 run_bot.py
```

---

## 📝 **Проверка работы**

После запуска вы должны увидеть:

```
2025-10-11 18:00:00 | INFO | bot | Starting bot...
2025-10-11 18:00:00 | INFO | bot | Bot created
[AUTO-CHECK-SCHEDULER] Initialized (interval: 5 minutes)
[AUTO-CHECK-SCHEDULER] Scheduler started (every 5 minutes)
2025-10-11 18:00:00 | INFO | bot | APScheduler auto-checker started (every 5 minutes)
2025-10-11 18:00:00 | INFO | bot | Next check scheduled at: 2025-10-11 18:05:00
[AUTO-CHECK-SCHEDULER] Running immediate initial check...
```

**Если видите это — всё работает! ✅**

---

## ⚙️ **Настройка интервала проверки**

1. Откройте бота в Telegram
2. Нажмите **"Админ панель"**
3. Выберите **"Интервал автопроверки"**
4. Введите новый интервал (например: `3` для 3 минут)
5. **Перезапустите бота**

---

## 🐛 **Если что-то не работает**

### **Ошибка: "ModuleNotFoundError: No module named 'apscheduler'"**

```bash
# Windows
.venv\Scripts\activate
pip install APScheduler==3.10.4

# Linux
source venv/bin/activate
pip install APScheduler==3.10.4
```

### **Ошибка: "BOT_TOKEN not found"**

```bash
# Проверьте .env файл
# Windows
type .env

# Linux
cat .env

# Должно быть:
BOT_TOKEN=ваш_токен_тут
```

### **Ошибка: "Playwright chromium not found"**

```bash
# Windows & Linux
playwright install chromium

# Только Linux (системные зависимости)
sudo playwright install-deps chromium
```

### **Автопроверка не запускается**

```bash
# Проверьте логи
# Должны быть строки с [AUTO-CHECK-SCHEDULER]

# Если их нет - проверьте settings:
python -c "from project.services.system_settings import get_auto_check_interval; from project.database import get_engine, get_session_factory; from project.config import get_settings; settings = get_settings(); engine = get_engine(settings.db_url); SessionLocal = get_session_factory(engine); session = SessionLocal(); print(f'Interval: {get_auto_check_interval(session)} minutes')"
```

---

## 📚 **Полезные ссылки**

- **Детальная миграция:** [APSCHEDULER_MIGRATION.md](APSCHEDULER_MIGRATION.md)
- **Changelog:** [CHANGELOG_APSCHEDULER.md](CHANGELOG_APSCHEDULER.md)
- **Linux сервер:** [LINUX_SERVER_UPDATE.md](LINUX_SERVER_UPDATE.md)
- **Основной README:** [README.md](README.md)

---

## 💡 **Частые вопросы**

### **Q: Нужно ли удалять старые файлы?**
A: Нет, старые файлы остаются для обратной совместимости.

### **Q: Как изменить интервал на что-то отличное от 5 минут?**
A: Через админ-панель в Telegram боте.

### **Q: Работает ли это на Windows/Linux/Mac?**
A: Да, APScheduler работает на всех платформах.

### **Q: Нужно ли мигрировать базу данных?**
A: Нет, структура БД не изменилась.

### **Q: Можно ли вернуться к старой версии?**
A: Да, через `git reset --hard e934265`.

### **Q: Как проверить, что APScheduler работает?**
A: Смотрите логи - должны быть строки `[AUTO-CHECK-SCHEDULER]`.

---

## 🎉 **Готово!**

Теперь у вас работает **стабильная автопроверка** с APScheduler!

**Если нужна помощь:**
- 📖 Читайте полную документацию
- 🐛 Создавайте Issue на GitHub
- 💬 Пишите в поддержку

**Приятного использования!** 🚀

