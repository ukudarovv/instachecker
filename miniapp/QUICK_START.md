# 🚀 Быстрый запуск Mini App

## Для локального тестирования (за 5 минут)

### 1. Установите ngrok
```bash
# Windows (через Chocolatey):
choco install ngrok

# Mac (через Homebrew):
brew install ngrok

# Linux:
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Или скачайте с: https://ngrok.com/download
```

### 2. Запустите Mini App

**Терминал 1 - Django сервер:**
```bash
cd miniapp
python manage.py runserver 8001
```

**Терминал 2 - ngrok туннель:**
```bash
ngrok http 8001
```

Вы увидите:
```
Forwarding  https://xxxx-xx-xx.ngrok-free.app -> http://localhost:8001
```

**Скопируйте HTTPS URL!**

### 3. Добавьте URL в бот

Откройте файл `env` в корне проекта и добавьте:
```env
IG_MINI_APP_URL=https://xxxx-xx-xx.ngrok-free.app
```

### 4. Перезапустите бота

```bash
cd ..
python run_bot.py
```

### 5. Тестируйте!

1. Откройте бот в Telegram
2. **Instagram** → появится кнопка **"🔐 Войти через Mini App"**
3. Нажмите - откроется Mini App
4. Войдите в Instagram
5. Нажмите "Отправить cookies"
6. Готово!

## Для продакшн (Railway - бесплатно)

### 1. Создайте аккаунт на Railway
https://railway.app/

### 2. Deploy

```bash
# Установите Railway CLI
npm i -g @railway/cli

# Login
railway login

# Deploy
cd miniapp
railway init
railway up
```

### 3. Получите URL

Railway автоматически создаст HTTPS URL:
```
https://your-app.up.railway.app
```

### 4. Обновите .env

```env
IG_MINI_APP_URL=https://your-app.up.railway.app
```

## 🎯 Готово!

Теперь в боте есть кнопка для входа через Mini App! 

⚠️ **Важно:** Из-за CORS браузер не даст автоматически извлечь cookies из Instagram. Пользователю нужно будет скопировать их вручную через консоль (F12), но Mini App предоставит удобный интерфейс для этого.

