# Telegram Mini App для Instagram Login

## 🎯 Что это?

Telegram Mini App, которое позволяет пользователям входить в Instagram прямо внутри Telegram и автоматически получать cookies для бота.

## 🚀 Быстрый старт

### 1. Запуск локального сервера (для тестирования)

```bash
cd telegram_mini_app
python server.py 8000
```

Сервер запустится на `http://localhost:8000`

### 2. Настройка в BotFather

1. Откройте [@BotFather](https://t.me/BotFather)
2. Отправьте `/mybots`
3. Выберите вашего бота
4. Нажмите `Bot Settings` → `Menu Button`
5. Выберите `Configure Menu Button`
6. Отправьте URL вашего Mini App: `https://yourdomain.com`
7. Отправьте текст кнопки: `🔐 Войти в Instagram`

### 3. Деплой на продакшн

⚠️ **Telegram требует HTTPS для Mini Apps!**

#### Вариант A: GitHub Pages (бесплатно)

1. Создайте репозиторий на GitHub
2. Загрузите `index.html` в корень репозитория
3. Включите GitHub Pages в настройках репозитория
4. Используйте URL: `https://yourusername.github.io/repo-name/`

#### Вариант B: Vercel (бесплатно)

1. Установите Vercel CLI:
```bash
npm i -g vercel
```

2. Деплой:
```bash
cd telegram_mini_app
vercel --prod
```

3. Скопируйте полученный URL

#### Вариант C: Netlify (бесплатно)

1. Перетащите папку `telegram_mini_app` на [netlify.com/drop](https://app.netlify.com/drop)
2. Скопируйте полученный URL

#### Вариант D: Свой сервер

1. Установите Nginx
2. Получите SSL сертификат (Let's Encrypt)
3. Настройте Nginx для раздачи статических файлов
4. Укажите domain в BotFather

## 🔧 Интеграция с ботом

### Обновите обработчик в боте

Добавьте в `project/handlers/ig_menu.py`:

```python
# Handle Web App data
@dp.message_handler(content_types=['web_app_data'])
async def handle_web_app_data(message: types.Message):
    """Handle data from Telegram Mini App."""
    try:
        data = json.loads(message.web_app_data.data)
        
        if data.get('action') == 'instagram_cookies':
            cookies = data.get('cookies')
            
            if not cookies or len(cookies) == 0:
                await message.answer("❌ Не удалось получить cookies")
                return
            
            # Check for sessionid
            has_sessionid = any(c.get('name') == 'sessionid' for c in cookies)
            if not has_sessionid:
                await message.answer("⚠️ В cookies отсутствует sessionid. Войдите в Instagram в Mini App.")
                return
            
            # Save session
            settings = get_settings()
            fernet = OptionalFernet(settings.encryption_key)
            
            with SessionLocal() as s:
                user = get_or_create_user(s, message.from_user)
                
                # Extract username from cookies or ask user
                ig_username = data.get('username', 'webapp_user')
                
                obj = save_session(
                    session=s,
                    user_id=user.id,
                    ig_username=ig_username,
                    cookies_json=cookies,
                    fernet=fernet,
                )
            
            await message.answer(
                f"✅ Сессия из Mini App сохранена! (id={obj.id})\n\n"
                f"🎉 Теперь можете проверять аккаунты через Instagram.",
                reply_markup=instagram_menu_kb()
            )
            
    except Exception as e:
        print(f"Error handling web app data: {e}")
        await message.answer(f"❌ Ошибка обработки данных: {str(e)}")
```

### Обновите клавиатуру

В `project/keyboards.py` добавьте:

```python
def instagram_menu_kb() -> dict:
    """Instagram menu with Mini App button."""
    return {
        "keyboard": [
            [{"text": "Мои IG-сессии"}],
            [{"text": "Добавить IG-сессию"}],
            [
                {
                    "text": "🔐 Войти через Mini App",
                    "web_app": {"url": "https://yourdomain.com"}
                }
            ],
            [{"text": "Проверить через IG"}],
            [{"text": "Назад в меню"}]
        ],
        "resize_keyboard": True
    }
```

## 📱 Как это работает?

1. **Пользователь нажимает** кнопку "🔐 Войти через Mini App"
2. **Открывается WebView** с Instagram внутри Telegram
3. **Пользователь входит** в Instagram как обычно
4. **Нажимает "Готово"** в Mini App
5. **Cookies автоматически** отправляются в бот
6. **Бот сохраняет** сессию в базу данных

## ⚠️ Ограничения

### Проблема CORS

Из-за политики Same-Origin Policy браузер **не позволяет** Mini App напрямую получать cookies из iframe с Instagram.

### Решения:

**Решение 1: Попросить пользователя скопировать cookies вручную**
- После входа в Instagram
- Открыть консоль (F12)
- Выполнить скрипт экспорта
- Вставить в поле ввода

**Решение 2: Использовать прокси-сервер**
- Настроить свой прокси
- Проксировать запросы к Instagram
- Перехватывать cookies на сервере

**Решение 3: Browser Extension (лучший вариант)**
- Создать расширение для браузера
- Расширение может читать cookies
- Отправлять в бот через Web App

## 🎨 Кастомизация

### Изменить тему

В `index.html` используйте CSS переменные Telegram:

```css
--tg-theme-bg-color
--tg-theme-text-color
--tg-theme-hint-color
--tg-theme-link-color
--tg-theme-button-color
--tg-theme-button-text-color
```

### Добавить логотип

```html
<div class="logo">
    <img src="your-logo.png" alt="Logo">
</div>
```

## 🔒 Безопасность

1. **HTTPS обязателен** - Telegram требует HTTPS для Mini Apps
2. **Валидация данных** - проверяйте `initData` от Telegram
3. **Шифрование** - используйте шифрование для хранения cookies
4. **Ограничение доступа** - проверяйте права пользователя

## 📚 Документация

- [Telegram Mini Apps](https://core.telegram.org/bots/webapps)
- [Telegram Web App API](https://core.telegram.org/bots/webapps#initializing-mini-apps)
- [BotFather Menu Button](https://core.telegram.org/bots/webapps#launching-mini-apps-from-the-menu-button)

## 🐛 Troubleshooting

### Mini App не открывается
- Проверьте, что URL использует HTTPS
- Убедитесь, что URL доступен из интернета
- Проверьте настройки в BotFather

### Cookies не отправляются
- Из-за CORS это нормально
- Используйте ручное копирование через консоль
- Или настройте прокси-сервер

### Ошибка "Invalid initData"
- Убедитесь, что проверяете подпись данных
- Используйте правильный bot token для проверки

## 💡 Альтернативные решения

Если Mini App не подходит из-за CORS:

1. **Букмарклет** - закладка в браузере для экспорта cookies
2. **Browser Extension** - расширение для автоматического экспорта
3. **Desktop App** - Electron приложение с доступом к cookies
4. **Ручной импорт** - скрипт в консоли браузера (текущее решение)

## 🎯 Рекомендация

**Текущее решение с ручным импортом cookies через консоль** остается самым надежным и простым способом из-за ограничений браузера с CORS.

Mini App можно использовать как **удобный интерфейс** для входа, но финальный этап (копирование cookies) все равно будет ручным.

