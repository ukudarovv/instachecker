# 🚀 Быстрый старт: Добавление Instagram через Cookies

## Проблема решена! ✅

Теперь бот правильно обрабатывает cookies и логинится в Instagram.

## Что было исправлено?

1. ✅ Улучшена обработка cookies в Playwright
2. ✅ Добавлена валидация формата cookies
3. ✅ Добавлены подробные инструкции
4. ✅ Созданы скрипты для экспорта cookies
5. ✅ Добавлена конвертация cookies из объекта в массив

## 📋 Как правильно добавить IG-сессию через cookies?

### Вариант 1: Через скрипт в браузере (РЕКОМЕНДУЕТСЯ)

1. Откройте https://instagram.com в браузере
2. Войдите в ваш аккаунт Instagram
3. Нажмите **F12** (откроется консоль разработчика)
4. Перейдите на вкладку **Console**
5. Скопируйте и вставьте этот скрипт:

```javascript
copy(JSON.stringify(document.cookie.split('; ').map(c=>{const[name,value]=c.split('=');return{name,value:decodeURIComponent(value),domain:'.instagram.com',path:'/'}}),null,2))
```

6. Нажмите **Enter**
7. Cookies автоматически скопированы в буфер обмена!
8. Вставьте их в Telegram бот

### Вариант 2: Через расширение браузера

1. Установите расширение **EditThisCookie** или **Cookie-Editor**
2. Откройте instagram.com и войдите
3. Нажмите на иконку расширения
4. Нажмите **Export** (экспорт)
5. Скопируйте JSON
6. Вставьте в бот

### Вариант 3: Через Python скрипт

Если у вас cookies в формате объекта `{}`, используйте конвертер:

```bash
python convert_cookies_format.py
```

Вставьте ваши cookies, скрипт конвертирует их в правильный формат.

## ❌ Частые ошибки

### Ошибка 1: Неправильный формат

**Неправильно** (объект):
```json
{
  "sessionid": "значение",
  "csrftoken": "значение"
}
```

**Правильно** (массив объектов):
```json
[
  {"name": "sessionid", "value": "значение"},
  {"name": "csrftoken", "value": "значение"}
]
```

### Ошибка 2: Отсутствует sessionid

Самый важный cookie - `sessionid`. Без него логин НЕ РАБОТАЕТ!

Убедитесь что в ваших cookies есть:
```json
{"name": "sessionid", "value": "..."}
```

### Ошибка 3: Cookies из другого домена

Cookies должны быть с домена `.instagram.com`, а не:
- ❌ `.facebook.com`
- ❌ `.meta.com`
- ❌ другие домены

## 🔍 Проверка cookies

После добавления бот автоматически проверит:
- ✅ Наличие `sessionid`
- ✅ Срок действия cookies
- ✅ Возможность входа в Instagram

Если что-то не так, бот сообщит об ошибке.

## 📖 Пример правильных cookies

```json
[
  {
    "name": "mid",
    "value": "Zc...",
    "domain": ".instagram.com",
    "path": "/"
  },
  {
    "name": "csrftoken",
    "value": "abc...",
    "domain": ".instagram.com",
    "path": "/"
  },
  {
    "name": "ds_user_id",
    "value": "123456789",
    "domain": ".instagram.com",
    "path": "/"
  },
  {
    "name": "sessionid",
    "value": "123456789%3Aabc...",
    "domain": ".instagram.com",
    "path": "/"
  }
]
```

## 🎯 Ваш случай

У вас были cookies в формате:
```json
{
  "sessionid": "77284452384%3Avz9eMbLZ2WeM5z%3A6%3AAYjT7J1UweH2I9dTMPo4pEoVTcaNtE5LF5JxYpSVPg",
  "csrftoken": "8bzweXhiR2nH4CT5pZYS7YcJPtMmydjI",
  ...
}
```

Правильный формат для вашего случая (см. выше в чате) - я уже конвертировал их для вас!

## 🛠️ Инструменты

- `convert_cookies_format.py` - Python скрипт для конвертации
- `instagram_cookies_export.js` - JavaScript для экспорта из браузера
- `INSTAGRAM_COOKIES_BOOKMARKLET.md` - Букмарклет для браузера
- `COOKIES_FORMAT_GUIDE.md` - Подробное руководство

## ⚡ Быстрый тест

После добавления cookies проверьте:

1. Перейдите в меню **Instagram**
2. Выберите **Мои IG-сессии**
3. Убедитесь что сессия создана и активна ✅
4. Попробуйте **Проверить через IG**

Если все работает - видите скриншоты аккаунтов - значит всё отлично!

## 🆘 Если не работает

1. Проверьте что sessionid присутствует
2. Убедитесь что вы вошли в Instagram в браузере
3. Попробуйте другой браузер (Chrome, Firefox, Edge)
4. Используйте расширение EditThisCookie вместо скрипта
5. Проверьте что cookies не истекли (зайдите в Instagram)

## 🔐 Безопасность

- Cookies хранятся в зашифрованном виде в базе данных
- Используется шифрование Fernet (AES)
- Не передавайте cookies третьим лицам
- После добавления можете сменить пароль IG (cookies продолжат работать)

---

**Готово!** Теперь вы можете проверять Instagram аккаунты через бот! 🎉

