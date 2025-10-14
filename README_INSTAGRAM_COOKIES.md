# 🍪 Полное руководство по Instagram Cookies

## 📚 Оглавление

1. [Введение](#введение)
2. [Быстрый старт](#быстрый-старт)
3. [Формат cookies](#формат-cookies)
4. [Способы получения cookies](#способы-получения-cookies)
5. [Валидация cookies](#валидация-cookies)
6. [Частые ошибки](#частые-ошибки)
7. [Безопасность](#безопасность)
8. [Устранение неполадок](#устранение-неполадок)
9. [Инструменты](#инструменты)

---

## Введение

Instagram cookies используются для авторизации в Instagram без ввода логина и пароля. Это самый надёжный способ добавить Instagram сессию в бот, особенно если у вас включена двухфакторная аутентификация (2FA).

### Преимущества метода с cookies:

✅ Работает с любыми аккаунтами (даже с 2FA)  
✅ Не требует ввода пароля  
✅ Быстрое добавление сессии  
✅ Надёжнее автоматического логина  
✅ Cookies шифруются и безопасно хранятся  

---

## Быстрый старт

### Шаг 1: Экспорт cookies из браузера

1. Откройте https://instagram.com в браузере
2. Войдите в ваш аккаунт Instagram
3. Нажмите **F12** (откроется консоль разработчика)
4. Перейдите на вкладку **Console**
5. Вставьте этот скрипт:

```javascript
copy(JSON.stringify(document.cookie.split('; ').map(c=>{const[name,value]=c.split('=');return{name,value:decodeURIComponent(value),domain:'.instagram.com',path:'/'}}),null,2))
```

6. Нажмите **Enter**
7. Cookies скопированы в буфер обмена! ✅

### Шаг 2: Добавление в бот

1. Откройте бот в Telegram
2. Выберите: **Instagram** → **Добавить IG-сессию** → **📋 Импорт cookies**
3. Бот отправит вам инструкцию и готовый скрипт
4. Вставьте скопированные cookies в бот
5. Укажите Instagram username для подписи
6. Готово! 🎉

---

## Формат cookies

### Правильный формат (массив объектов)

```json
[
  {
    "name": "sessionid",
    "value": "123456789%3Aabc...",
    "domain": ".instagram.com",
    "path": "/"
  },
  {
    "name": "csrftoken",
    "value": "abc123...",
    "domain": ".instagram.com",
    "path": "/"
  },
  {
    "name": "ds_user_id",
    "value": "123456789",
    "domain": ".instagram.com",
    "path": "/"
  }
]
```

### Обязательные поля для каждого cookie

| Поле | Описание | Обязательно |
|------|----------|-------------|
| `name` | Название cookie | ✅ Да |
| `value` | Значение cookie | ✅ Да |
| `domain` | Домен (по умолчанию `.instagram.com`) | ⚠️ Рекомендуется |
| `path` | Путь (по умолчанию `/`) | ⚠️ Рекомендуется |

### Опциональные поля

| Поле | Описание | Пример |
|------|----------|--------|
| `expires` | Unix timestamp истечения | `1735689600` |
| `httpOnly` | Только для HTTP запросов | `true` |
| `secure` | Только для HTTPS | `true` |
| `sameSite` | Политика SameSite | `"None"`, `"Lax"`, `"Strict"` |

### ❌ Неправильные форматы

**Объект вместо массива:**
```json
{
  "sessionid": "123...",
  "csrftoken": "abc..."
}
```
→ Нужно конвертировать в массив! Используйте `convert_cookies_format.py`

**Строка вместо JSON:**
```
sessionid=123; csrftoken=abc
```
→ Неверный формат, используйте скрипт для экспорта

---

## Способы получения cookies

### Способ 1: JavaScript скрипт в консоли (РЕКОМЕНДУЕТСЯ)

**Преимущества:** Быстро, надёжно, работает везде

1. Откройте instagram.com
2. F12 → Console
3. Вставьте скрипт (см. [Быстрый старт](#быстрый-старт))
4. Cookies в буфере обмена!

**Скрипт (короткая версия):**
```javascript
copy(JSON.stringify(document.cookie.split('; ').map(c=>{const[name,value]=c.split('=');return{name,value:decodeURIComponent(value),domain:'.instagram.com',path:'/'}}),null,2))
```

### Способ 2: Расширение браузера

**Преимущества:** Визуальный интерфейс, удобно для новичков

1. Установите **EditThisCookie** (Chrome/Edge) или **Cookie-Editor** (Firefox)
2. Откройте instagram.com и войдите
3. Нажмите на иконку расширения
4. Нажмите **Export** (экспорт)
5. Скопируйте JSON

**Ссылки на расширения:**
- Chrome: [EditThisCookie](https://chrome.google.com/webstore/detail/editthiscookie/)
- Firefox: [Cookie-Editor](https://addons.mozilla.org/firefox/addon/cookie-editor/)

### Способ 3: Букмарклет (закладка в браузере)

**Преимущества:** Экспорт одним кликом

См. `INSTAGRAM_COOKIES_BOOKMARKLET.md` для инструкции

### Способ 4: DevTools Application (вручную)

**Преимущества:** Полный контроль

1. F12 → **Application** (или **Storage** в Firefox)
2. Слева: **Cookies** → **https://www.instagram.com**
3. Вручную скопируйте значения нужных cookies
4. Создайте JSON по шаблону

---

## Валидация cookies

### Автоматическая валидация в боте

Бот автоматически проверяет:

✅ Формат (массив объектов)  
✅ Обязательные поля (`name`, `value`)  
✅ Наличие `sessionid` cookie  
✅ Корректность значений  

### Ручная проверка

Используйте тестовый скрипт:

```bash
# Интерактивная проверка
python test_cookies.py

# Проверка из файла
python test_cookies.py cookies.json
```

Скрипт проверит:
- ✅ Формат JSON
- ✅ Структуру cookies
- ✅ Наличие sessionid
- ⚠️ Рекомендуемые cookies
- ⚠️ Подозрительные значения

### Критически важные cookies

| Cookie | Важность | Описание |
|--------|----------|----------|
| **sessionid** | 🔴 КРИТИЧНО | Основной cookie авторизации. БЕЗ НЕГО НЕ РАБОТАЕТ! |
| csrftoken | 🟡 Важно | Токен защиты от CSRF |
| ds_user_id | 🟡 Важно | ID пользователя Instagram |
| mid | 🟢 Рекомендуется | Machine ID |

---

## Частые ошибки

### ❌ Ошибка 1: Неправильный формат (объект вместо массива)

**Симптом:**
```
⚠️ Ошибка формата: Cookies должны быть списком (массивом)
```

**Решение:**
Используйте конвертер:
```bash
python convert_cookies_format.py
```

### ❌ Ошибка 2: Отсутствует sessionid

**Симптом:**
```
⚠️ В cookies отсутствует sessionid
```

**Причины:**
- Вы не вошли в Instagram в браузере
- Cookies экспортированы с другого домена
- Cookies неполные

**Решение:**
1. Убедитесь что вы ВОШЛИ в Instagram
2. Используйте скрипт из инструкции
3. Экспортируйте ВСЕ cookies, не выборочно

### ❌ Ошибка 3: Истёкшие cookies

**Симптом:**
```
❌ Session expired and failed to re-login
```

**Решение:**
1. Зайдите в Instagram в браузере заново
2. Экспортируйте свежие cookies
3. Добавьте в бот

### ❌ Ошибка 4: Неверный JSON

**Симптом:**
```
⚠️ Неверный JSON формат: Expecting ',' delimiter
```

**Решение:**
- Не редактируйте JSON вручную
- Используйте скрипт для экспорта
- Проверьте что все кавычки закрыты

---

## Безопасность

### 🔐 Как хранятся cookies?

1. **Шифрование:** Cookies шифруются алгоритмом Fernet (AES-128)
2. **Ключ шифрования:** Хранится в переменной окружения `ENCRYPTION_KEY`
3. **База данных:** Зашифрованные cookies в SQLite/PostgreSQL
4. **Передача:** Cookies передаются только через HTTPS (Telegram API)

### 🛡️ Рекомендации по безопасности

✅ **DO:**
- Используйте сильный `ENCRYPTION_KEY` (минимум 32 символа)
- Регулярно обновляйте cookies (раз в месяц)
- Не храните cookies в открытом виде
- Используйте отдельный аккаунт для бота (опционально)

❌ **DON'T:**
- Не передавайте cookies третьим лицам
- Не публикуйте cookies в открытом доступе
- Не используйте основной аккаунт (если важна безопасность)
- Не храните cookies в незашифрованных файлах

### 🔄 Смена пароля

**Вопрос:** Можно ли сменить пароль Instagram после добавления cookies?

**Ответ:** Да! Cookies продолжат работать до истечения срока (обычно 90-365 дней). Но лучше обновить cookies после смены пароля.

---

## Устранение неполадок

### Проблема: Бот не может войти в Instagram

**Диагностика:**
```bash
# Проверьте cookies
python test_cookies.py cookies.json

# Проверьте логи бота
tail -f bot.log
```

**Возможные причины:**
1. Cookies истекли → Экспортируйте заново
2. Нет sessionid → Проверьте формат
3. Instagram заблокировал IP → Используйте прокси
4. Неправильный формат → Используйте скрипт

### Проблема: "Session expired" при проверке

**Решение:**
1. Откройте Instagram в браузере
2. Проверьте что вы вошли
3. Экспортируйте cookies заново
4. Обновите сессию в боте

### Проблема: Бот пишет "Нет активной IG-сессии"

**Решение:**
1. Проверьте: Instagram → Мои IG-сессии
2. Убедитесь что сессия активна (✅)
3. Если неактивна (❌) → Добавьте новую сессию

---

## Инструменты

### Скрипты в репозитории

| Файл | Назначение |
|------|------------|
| `instagram_cookies_export.js` | JavaScript для экспорта cookies |
| `convert_cookies_format.py` | Конвертер формата cookies |
| `test_cookies.py` | Валидатор cookies |

### Использование

**Экспорт cookies:**
```bash
# Скопируйте instagram_cookies_export.js
# Вставьте в консоль браузера на instagram.com
```

**Конвертация формата:**
```bash
python convert_cookies_format.py
# Вставьте cookies в формате объекта
# Получите массив
```

**Проверка cookies:**
```bash
python test_cookies.py cookies.json
```

### Документация

| Файл | Описание |
|------|----------|
| `COOKIES_FORMAT_GUIDE.md` | Подробный гайд по формату |
| `COOKIES_QUICKSTART.md` | Краткая инструкция |
| `INSTAGRAM_COOKIES_BOOKMARKLET.md` | Букмарклет для браузера |
| `COOKIES_FIX_SUMMARY.md` | Описание исправлений |
| `README_INSTAGRAM_COOKIES.md` | Это руководство |

---

## Примеры

### Пример 1: Минимальный набор cookies

```json
[
  {
    "name": "sessionid",
    "value": "77284452384%3Avz9eMbLZ2WeM5z%3A6%3AAYjT7J1UweH2I9dTMPo4pEoVTcaNtE5LF5JxYpSVPg"
  },
  {
    "name": "csrftoken",
    "value": "8bzweXhiR2nH4CT5pZYS7YcJPtMmydjI"
  },
  {
    "name": "ds_user_id",
    "value": "77284452384"
  }
]
```

### Пример 2: Полный набор cookies

```json
[
  {
    "name": "mid",
    "value": "aGKXUAALAAE1QQJO1zfQVuhxombA",
    "domain": ".instagram.com",
    "path": "/"
  },
  {
    "name": "ig_did",
    "value": "14894DB6-D5C3-4ACD-9103-691104070D02",
    "domain": ".instagram.com",
    "path": "/"
  },
  {
    "name": "ig_nrcb",
    "value": "1",
    "domain": ".instagram.com",
    "path": "/"
  },
  {
    "name": "datr",
    "value": "UJdiaOuoU-NK_7OkF20TE-Rk",
    "domain": ".instagram.com",
    "path": "/"
  },
  {
    "name": "csrftoken",
    "value": "8bzweXhiR2nH4CT5pZYS7YcJPtMmydjI",
    "domain": ".instagram.com",
    "path": "/"
  },
  {
    "name": "ds_user_id",
    "value": "77284452384",
    "domain": ".instagram.com",
    "path": "/"
  },
  {
    "name": "sessionid",
    "value": "77284452384%3Avz9eMbLZ2WeM5z%3A6%3AAYjT7J1UweH2I9dTMPo4pEoVTcaNtE5LF5JxYpSVPg",
    "domain": ".instagram.com",
    "path": "/",
    "httpOnly": true,
    "secure": true
  },
  {
    "name": "rur",
    "value": "\"CLN\\05477284452384\\0541791975038:01fe57fa75b7b5ffdeb3d3551201f9e5b076a08e8c0cd60cd82d5f5248b3ca834de0d511\"",
    "domain": ".instagram.com",
    "path": "/"
  }
]
```

---

## FAQ

**Q: Сколько действуют cookies?**  
A: Обычно 90-365 дней. После истечения нужно экспортировать заново.

**Q: Можно ли использовать cookies с разных устройств?**  
A: Да, но лучше экспортировать с одного устройства для консистентности.

**Q: Что делать если Instagram заблокировал аккаунт?**  
A: Разблокируйте через приложение Instagram, затем экспортируйте cookies заново.

**Q: Можно ли добавить несколько сессий?**  
A: Да, бот поддерживает несколько IG-сессий. Будет использована первая активная.

**Q: Безопасно ли хранить cookies в боте?**  
A: Да, если используется шифрование (`ENCRYPTION_KEY` в `.env`).

---

## Поддержка

Если у вас остались вопросы:

1. Прочитайте `COOKIES_FORMAT_GUIDE.md`
2. Проверьте cookies через `test_cookies.py`
3. Посмотрите логи бота
4. Создайте issue в репозитории

---

**Готово!** Теперь вы эксперт по Instagram cookies! 🎉

*Последнее обновление: 14 октября 2025*

