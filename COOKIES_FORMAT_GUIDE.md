# 🍪 Руководство по формату Cookies для Instagram

## Формат cookies

Cookies должны быть в формате **JSON массива** с объектами. Каждый cookie - это объект с полями:

### Минимальный формат (работает):

```json
[
  {
    "name": "sessionid",
    "value": "ВАШ_SESSIONID_ЗНАЧЕНИЕ"
  },
  {
    "name": "ds_user_id",
    "value": "ВАШ_USER_ID"
  },
  {
    "name": "csrftoken",
    "value": "ВАШ_CSRF_TOKEN"
  }
]
```

### Полный формат (рекомендуется):

```json
[
  {
    "name": "sessionid",
    "value": "ВАШ_SESSIONID_ЗНАЧЕНИЕ",
    "domain": ".instagram.com",
    "path": "/",
    "expires": -1,
    "httpOnly": true,
    "secure": true,
    "sameSite": "None"
  },
  {
    "name": "ds_user_id",
    "value": "ВАШ_USER_ID",
    "domain": ".instagram.com",
    "path": "/",
    "expires": -1
  },
  {
    "name": "csrftoken",
    "value": "ВАШ_CSRF_TOKEN",
    "domain": ".instagram.com",
    "path": "/",
    "expires": -1
  }
]
```

## Обязательные поля

1. **name** - название cookie (обязательно)
2. **value** - значение cookie (обязательно)

## Опциональные поля (добавляются автоматически если отсутствуют)

- **domain** - домен (по умолчанию: `.instagram.com`)
- **path** - путь (по умолчанию: `/`)
- **expires** - время истечения (по умолчанию: `-1` - session cookie)
- **httpOnly** - только HTTP (необязательно)
- **secure** - только HTTPS (необязательно)
- **sameSite** - политика SameSite (необязательно)

## Как получить cookies из браузера

### Способ 1: Расширение браузера

1. Установите расширение **EditThisCookie** или **Cookie-Editor**
2. Откройте instagram.com и войдите в аккаунт
3. Нажмите на иконку расширения
4. Нажмите "Export" или "Экспорт"
5. Скопируйте JSON

### Способ 2: Консоль разработчика (Chrome/Edge/Firefox)

1. Откройте instagram.com и войдите в аккаунт
2. Нажмите F12 (открыть DevTools)
3. Перейдите на вкладку **Console** (Консоль)
4. Вставьте и выполните этот скрипт:

```javascript
copy(JSON.stringify(
  document.cookie.split('; ').map(c => {
    const [name, value] = c.split('=');
    return {
      name: name,
      value: value,
      domain: '.instagram.com',
      path: '/',
      expires: -1
    };
  }),
  null,
  2
));
```

5. Cookies скопированы в буфер обмена! Вставьте их в бот

### Способ 3: Из Application/Storage (Chrome/Edge)

1. Откройте instagram.com и войдите
2. Нажмите F12
3. Перейдите на вкладку **Application** (или **Storage** в Firefox)
4. Слева выберите **Cookies** → **https://www.instagram.com**
5. Вручную скопируйте значения нужных cookies
6. Создайте JSON вручную по шаблону выше

## Минимально необходимые cookies для работы

Instagram требует минимум эти cookies для успешной авторизации:

1. **sessionid** - основной cookie сессии (ОБЯЗАТЕЛЬНО!)
2. **ds_user_id** - ID пользователя
3. **csrftoken** - токен защиты от CSRF

Рекомендуется экспортировать ВСЕ cookies с instagram.com для максимальной надежности.

## Пример полного экспорта

```json
[
  {
    "name": "mid",
    "value": "XXXXXXXXXX",
    "domain": ".instagram.com",
    "path": "/",
    "expires": -1
  },
  {
    "name": "ig_did",
    "value": "XXXXXXXXXX",
    "domain": ".instagram.com",
    "path": "/",
    "expires": -1
  },
  {
    "name": "ig_nrcb",
    "value": "1",
    "domain": ".instagram.com",
    "path": "/",
    "expires": -1
  },
  {
    "name": "csrftoken",
    "value": "XXXXXXXXXX",
    "domain": ".instagram.com",
    "path": "/",
    "expires": -1
  },
  {
    "name": "ds_user_id",
    "value": "123456789",
    "domain": ".instagram.com",
    "path": "/",
    "expires": -1
  },
  {
    "name": "sessionid",
    "value": "XXXXXXXXXX%3AXXXXXXXXXX%3AXXXXXXXXXX",
    "domain": ".instagram.com",
    "path": "/",
    "expires": -1,
    "httpOnly": true,
    "secure": true
  },
  {
    "name": "rur",
    "value": "XXX",
    "domain": ".instagram.com",
    "path": "/",
    "expires": -1
  }
]
```

## Частые ошибки

### ❌ Неправильно - строка вместо массива:
```
sessionid=12345; csrftoken=abcde
```

### ❌ Неправильно - объект вместо массива:
```json
{
  "sessionid": "12345",
  "csrftoken": "abcde"
}
```

### ✅ Правильно - массив объектов:
```json
[
  {"name": "sessionid", "value": "12345"},
  {"name": "csrftoken", "value": "abcde"}
]
```

## Проверка валидности cookies

Бот автоматически проверяет:
1. Наличие `sessionid` cookie
2. Срок действия cookies
3. Возможность входа в Instagram

Если проверка не проходит, бот покажет соответствующее сообщение.

## Безопасность

⚠️ **ВАЖНО:**
- Cookies содержат данные авторизации
- Не передавайте их третьим лицам
- Бот хранит cookies в зашифрованном виде
- После добавления можете сменить пароль в Instagram (cookies продолжат работать до истечения срока)

## Срок действия

- Instagram cookies обычно живут 90-365 дней
- После истечения нужно будет добавить новые cookies
- Бот уведомит вас, если cookies устареют

