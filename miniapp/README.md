# 📱 Instagram Login Mini App для Telegram

## 🎯 Что это?

Django веб-приложение, которое интегрируется с Telegram ботом как Mini App. Позволяет пользователям входить в Instagram прямо из Telegram и автоматически сохранять cookies в бот.

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
cd miniapp
pip install -r requirements.txt
```

### 2. Запуск сервера

**Windows:**
```bash
start_miniapp.bat
```

**Linux/Mac:**
```bash
chmod +x start_miniapp.sh
./start_miniapp.sh
```

**Или вручную:**
```bash
python manage.py runserver 0.0.0.0:8001
```

Сервер запустится на `http://localhost:8001`

### 3. Настройка для локального тестирования

Для тестирования Mini App локально используйте **ngrok**:

```bash
# Установите ngrok: https://ngrok.com/download
ngrok http 8001
```

Вы получите URL вида: `https://xxxx-xx-xx-xx-xx.ngrok-free.app`

### 4. Добавьте URL в .env бота

В файле `env` (корень проекта):
```env
IG_MINI_APP_URL=https://xxxx-xx-xx-xx-xx.ngrok-free.app
```

### 5. Перезапустите бота

```bash
python run_bot.py
```

## 📱 Как использовать

1. Откройте бот в Telegram
2. Перейдите в раздел **"Instagram"**
3. Нажмите **"🔐 Войти через Mini App"**
4. Войдите в Instagram в открывшемся окне
5. Нажмите кнопку **"📤 Отправить cookies в бот"**
6. Готово! Сессия сохранена

## 🌐 Деплой на продакшн

⚠️ **Telegram требует HTTPS для Mini Apps!**

### Вариант 1: Railway (рекомендуется, бесплатный план)

1. Создайте аккаунт на [railway.app](https://railway.app)
2. Нажмите "New Project" → "Deploy from GitHub repo"
3. Выберите ваш репозиторий
4. Укажите root directory: `miniapp`
5. Railway автоматически обнаружит Django
6. Получите URL: `https://your-app.railway.app`

### Вариант 2: Render (бесплатный план)

1. Создайте аккаунт на [render.com](https://render.com)
2. "New" → "Web Service"
3. Подключите GitHub репозиторий
4. Настройки:
   - Root Directory: `miniapp`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn miniapp.wsgi:application --bind 0.0.0.0:$PORT`
5. Получите URL: `https://your-app.onrender.com`

### Вариант 3: Heroku

1. Установите Heroku CLI
2. Создайте `Procfile` в папке `miniapp`:
```
web: gunicorn miniapp.wsgi:application --bind 0.0.0.0:$PORT
```
3. Deploy:
```bash
cd miniapp
heroku create your-app-name
git push heroku master
```

### Вариант 4: Свой сервер (VPS)

1. Установите Django и gunicorn
2. Настройте Nginx как reverse proxy
3. Получите SSL сертификат (Let's Encrypt)
4. Запустите:
```bash
gunicorn miniapp.wsgi:application --bind 0.0.0.0:8001 --daemon
```

## ⚙️ Настройка в production

### 1. Обновите settings.py

```python
# В miniapp/miniapp/settings.py

DEBUG = False  # Отключите debug
ALLOWED_HOSTS = ['your-domain.com', 'your-app.railway.app']

# Добавьте secret key из переменной окружения
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'fallback-key')
```

### 2. Настройте переменные окружения

На вашем хостинге добавьте:
- `DJANGO_SECRET_KEY` - секретный ключ Django
- `BOT_TOKEN` - токен вашего Telegram бота
- `BOT_DB_PATH` - путь к базе данных бота

### 3. Обновите .env бота

```env
IG_MINI_APP_URL=https://your-app.railway.app
```

## 🔧 Как это работает

### Архитектура

```
Telegram Bot
     ↓
Пользователь нажимает "🔐 Войти через Mini App"
     ↓
Открывается Django приложение в WebView
     ↓
Пользователь входит в Instagram (iframe)
     ↓
Нажимает "Отправить cookies"
     ↓
Mini App отправляет POST на /save_cookies/
     ↓
Django сохраняет cookies в bot.db
     ↓
Отправляет подтверждение обратно в Telegram
     ↓
Сессия готова к использованию!
```

### API Endpoints

**GET /**
- Возвращает главную страницу Mini App
- Показывает iframe с Instagram

**POST /save_cookies/**
- Принимает cookies от Mini App
- Сохраняет в базу данных бота
- Возвращает результат

Request:
```json
{
  "telegram_user_id": 12345,
  "ig_username": "your_username",
  "cookies": [...]
}
```

Response:
```json
{
  "success": true,
  "session_id": 1,
  "ig_username": "your_username",
  "cookies_count": 15
}
```

## ⚠️ Ограничение CORS

Из-за Same-Origin Policy браузер не позволяет Mini App читать cookies из Instagram iframe.

**Решения:**

1. **Ручное копирование** (текущая реализация)
   - Пользователь копирует cookies через консоль
   - Вставляет в бот
   
2. **Browser Extension** (будущая возможность)
   - Расширение может читать cookies
   - Отправляет напрямую в бот API

## 🧪 Тестирование

### Локальное тестирование с ngrok

```bash
# Terminal 1: Start Django
cd miniapp
python manage.py runserver 8001

# Terminal 2: Start ngrok
ngrok http 8001

# Terminal 3: Start bot with Mini App URL
export IG_MINI_APP_URL=https://xxxx.ngrok-free.app
cd ..
python run_bot.py
```

## 📊 Статистика

- ✅ Автоматическое сохранение cookies в базу
- ✅ Проверка валидности (sessionid)
- ✅ Интеграция с существующей БД
- ✅ Красивый UI в стиле Telegram
- ✅ Обработка ошибок

## 🔒 Безопасность

1. **HTTPS обязателен** - Telegram требует HTTPS
2. **Проверка initData** - валидация запросов от Telegram (TODO)
3. **Шифрование cookies** - cookies шифруются в БД
4. **CORS настроен** - доступ только от Telegram

## 💡 Альтернативы

Если CORS остается проблемой:

1. **Прямой импорт через бот** - скрипт в консоли (текущее основное решение)
2. **Букмарклет** - закладка в браузере
3. **Browser Extension** - полная автоматизация
4. **Desktop App** - Electron приложение

## 🎯 Итог

Mini App создает **удобный интерфейс** для входа в Instagram прямо из Telegram, но из-за CORS финальный шаг (получение cookies) требует участия пользователя через консоль браузера.

Самый надежный способ остается: **импорт cookies через скрипт в консоли**.

