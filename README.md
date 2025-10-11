# 📸 Instagram Checker Bot

Telegram бот для проверки существования Instagram аккаунтов с автоматической автопроверкой каждые 5 минут.

## 🚀 Основные возможности

- ✅ **Проверка Instagram аккаунтов** через API и Instagram
- 📸 **Автоматические скриншоты** профилей
- 🔄 **Автопроверка каждые 5 минут** с APScheduler
- 🔑 **Управление API ключами** (RapidAPI)
- 🌐 **Поддержка прокси** с тестированием
- 👨‍💼 **Админ панель** с настройками
- 🗄️ **База данных** с моделями пользователей, аккаунтов, ключей

## 🛠️ Технологии

- **Python 3.8+**
- **SQLAlchemy** - ORM для работы с БД
- **Telegram Bot API** - прямой HTTP API
- **Playwright** - автоматизация браузера для скриншотов
- **aiohttp** - асинхронные HTTP запросы
- **APScheduler** - надежный планировщик задач
- **RapidAPI** - внешний API для проверки профилей

## 📦 Установка

### 1. Клонирование репозитория
```bash
git clone https://github.com/ukudarovv/instachecker.git
cd instachecker
```

### 2. Создание виртуального окружения
```bash
python -m venv .venv
```

### 3. Активация окружения
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 4. Установка зависимостей
```bash
pip install -r requirements.txt
playwright install
```

### 5. Настройка переменных окружения
Скопируйте `env.example` в `.env` и заполните:
```bash
cp env.example .env
```

## ⚙️ Конфигурация

### Основные настройки (.env):
```env
# Telegram Bot
BOT_TOKEN=your_bot_token_here

# Database
DATABASE_URL=sqlite:///./instachecker.db

# RapidAPI
RAPIDAPI_HOST=instagram210.p.rapidapi.com
RAPIDAPI_URL=https://instagram210.p.rapidapi.com/ig_profile
API_DAILY_LIMIT=950
RAPIDAPI_TIMEOUT_SECONDS=10

# Auto-check
AUTO_CHECK_INTERVAL_MINUTES=5

# Instagram
INSTAGRAM_HEADLESS=true
INSTAGRAM_TIMEOUT_MS=30000
```

## 🚀 Запуск

### Простой запуск:
```bash
python run_bot.py
```

### С автоперезапуском:
```bash
# Windows
start.bat

# Linux/Mac
./start.sh
```

## 📊 Архитектура

### APScheduler Auto-Checker
- ⏰ **APScheduler** для надежного планирования проверок
- 🔄 **AsyncIOScheduler** для асинхронных операций
- 📬 **Прямые отправки** в Telegram через aiohttp
- ⏰ **Периодичность**: каждые 5 минут (настраивается)
- 🛡️ **Защита от дублирования** задач (max_instances=1)
- 🔄 **Автоматическое восстановление** после ошибок

### Основные компоненты:
- `project/bot.py` - основной файл бота
- `project/auto_checker_scheduler.py` - APScheduler автопроверка
- `project/utils/async_bot_wrapper.py` - асинхронная обертка бота
- `project/cron/auto_checker.py` - логика проверки аккаунтов

## 🎯 Функционал

### Для пользователей:
- ➕ **Добавление аккаунтов** для проверки
- 🔍 **Ручная проверка** аккаунтов
- 📸 **Получение скриншотов** профилей
- 📊 **Просмотр статистики** аккаунтов

### Для админов:
- ⚙️ **Настройка интервала** автопроверки
- 🔄 **Перезапуск бота**
- 📊 **Просмотр статистики** системы
- 🔑 **Управление API ключами**

### API ключи:
- ➕ **Добавление** RapidAPI ключей
- 🧪 **Тестирование** ключей
- 📊 **Отслеживание использования**
- 🔄 **Автосброс** счетчиков ежедневно

## 🗄️ База данных

### Модели:
- **User** - пользователи бота
- **Account** - Instagram аккаунты для проверки
- **API** - API ключи RapidAPI
- **Proxy** - прокси серверы
- **InstagramSession** - сессии Instagram
- **SystemSettings** - системные настройки

## 🔧 Разработка

### Структура проекта:
```
project/
├── bot.py                    # Основной файл бота
├── models.py                 # Модели базы данных
├── config.py                 # Конфигурация
├── keyboards.py              # Клавиатуры Telegram
├── states.py                 # FSM состояния
├── handlers/                 # Обработчики команд
├── services/                 # Бизнес-логика
├── utils/                    # Утилиты
├── cron/                     # Автопроверка
└── auto_checker_threaded.py  # ThreadSafe автопроверка
```

### Тестирование:
```bash
# Тест бота
python test_bot.py

# Тест автопроверки
python test_debug_check.py

# Тест прокси
python test_proxy_connection.py
```

## 📝 Логирование

Бот ведет подробные логи:
- 🔄 **Запуск автопроверки**
- ✅ **Найденные аккаунты**
- ❌ **Несуществующие аккаунты**
- ⚠️ **Ошибки проверки**
- 📊 **Статистика завершения**

## 🛡️ Безопасность

- 🔐 **Шифрование** Instagram cookies
- 🔑 **Безопасное хранение** API ключей
- 🌐 **Поддержка прокси** для анонимности
- ⏰ **Rate limiting** для API запросов

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи в консоли
2. Убедитесь в правильности настроек `.env`
3. Проверьте доступность всех зависимостей

## 📄 Лицензия

MIT License

---

**🎉 Проект готов к использованию!**

Автопроверка работает каждые 5 минут с APScheduler — надежным промышленным планировщиком задач.

---

## 🔄 **Обновление с Threading на APScheduler**

Если у вас уже установлена предыдущая версия, обновитесь:

```bash
# Linux
./update_to_apscheduler.sh

# Windows
update_to_apscheduler.bat
```

Подробности в [APSCHEDULER_MIGRATION.md](APSCHEDULER_MIGRATION.md)