# 📱 Настройка Telegram Mini App для Instagram

## 🎯 Что это дает?

Кнопка **"🔐 Войти через Mini App"** в разделе Instagram бота, которая открывает веб-интерфейс для входа в Instagram прямо из Telegram.

## ⚡ Быстрый запуск (5 минут)

### Шаг 1: Установите ngrok (для локального тестирования)

**Windows:**
```bash
# Скачайте с https://ngrok.com/download
# Или через Chocolatey:
choco install ngrok
```

**Linux/Mac:**
```bash
# Mac:
brew install ngrok

# Linux:
snap install ngrok
```

### Шаг 2: Запустите ngrok

**Откройте НОВЫЙ терминал:**
```bash
ngrok http 8001
```

Вы увидите:
```
Forwarding  https://abcd-12-34-56.ngrok-free.app -> http://localhost:8001
```

**Скопируйте HTTPS URL** (начинается с https://)

### Шаг 3: Добавьте URL в env

Откройте файл `env` и добавьте:
```env
IG_MINI_APP_URL=https://abcd-12-34-56.ngrok-free.app
```

### Шаг 4: Запустите всё

**Windows:**
```bash
start_with_miniapp.bat
```

**Linux/Mac:**
```bash
chmod +x start_with_miniapp.sh
./start_with_miniapp.sh
```

### Шаг 5: Используйте в боте!

1. Откройте бот в Telegram
2. Перейдите в **Instagram**
3. Увидите кнопку **"🔐 Войти через Mini App"** 
4. Нажмите - откроется Mini App!

## 📱 Как использовать Mini App

1. **Нажмите** "🔐 Войти через Mini App" в боте
2. **Откроется** страница с Instagram внутри Telegram
3. **Войдите** в свой Instagram аккаунт
4. **Откройте консоль** (F12) в WebView
5. **Вставьте скрипт**:
```javascript
copy(JSON.stringify(document.cookie.split(';').map(c=>{const[n,...v]=c.trim().split('=');return{name:n,value:v.join('='),domain:'.instagram.com',path:'/',expires:-1}}),null,2))
```
6. **Нажмите** кнопку "📤 Отправить cookies" в Mini App
7. **Вставьте** скопированные cookies (Ctrl+V)
8. **Готово!** Сессия сохранена автоматически

## 🌐 Деплой на продакшн (без ngrok)

### Railway (рекомендуется, бесплатно)

```bash
cd miniapp

# Установите Railway CLI
npm i -g @railway/cli

# Login и deploy
railway login
railway init
railway up
```

Получите URL: `https://your-app.up.railway.app`

### Render (бесплатно)

1. Создайте аккаунт на https://render.com
2. "New" → "Web Service"
3. Подключите GitHub репозиторий
4. Root Directory: `miniapp`
5. Build: `pip install -r requirements.txt`
6. Start: `gunicorn miniapp.wsgi:application --bind 0.0.0.0:$PORT`

### Затем обновите env:
```env
IG_MINI_APP_URL=https://your-app.up.railway.app
```

## 🔧 Troubleshooting

### ngrok показывает ошибку "ERR_NGROK_3200"
- Зарегистрируйтесь на ngrok.com
- Получите authtoken
- Выполните: `ngrok config add-authtoken YOUR_TOKEN`

### Mini App не открывается
- Убедитесь, что используете HTTPS URL (не HTTP)
- Проверьте, что Django сервер запущен
- Проверьте, что ngrok запущен

### Кнопка не появляется в боте
- Проверьте, что `IG_MINI_APP_URL` добавлен в `env`
- Перезапустите бота
- URL должен начинаться с `https://`

### Cookies не сохраняются
- Убедитесь, что скопировали правильный JSON
- Проверьте наличие sessionid в cookies
- Посмотрите логи Django сервера

## 📊 Статус Mini App

Откройте бота и проверьте раздел Instagram:

✅ **С Mini App URL:**
```
[Добавить IG-сессию] [Мои IG-сессии]
[🔐 Войти через Mini App]  ← Эта кнопка
[Проверить через IG]
[Назад в меню]
```

❌ **Без Mini App URL:**
```
[Добавить IG-сессию] [Мои IG-сессии]
[Проверить через IG]
[Назад в меню]
```

## 🎯 Итог

Теперь у вас есть:
- ✅ Django Mini App для удобного входа
- ✅ Автоматическое сохранение cookies в базу бота
- ✅ Красивый интерфейс в стиле Telegram
- ✅ Скрипты для запуска (Windows и Linux)

**Используйте ngrok для тестирования**, затем **деплойте на Railway/Render** для продакшн! 🚀

