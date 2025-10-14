# 🍪 Как получить ВСЕ cookies Instagram (включая httpOnly)

## ⚠️ Важная информация

JavaScript на странице (`document.cookie`) **НЕ МОЖЕТ** получить доступ к cookies с флагом `httpOnly: true`.

Instagram часто устанавливает `sessionid` с флагом `httpOnly`, что означает что простой JavaScript скрипт его НЕ УВИДИТ.

## ✅ 3 способа получить ВСЕ cookies

---

## Способ 1: Через расширение браузера (САМЫЙ ПРОСТОЙ) 🌟

### Для Chrome/Edge/Brave

1. **Установите расширение "EditThisCookie"**
   - Ссылка: https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg

2. **Откройте instagram.com и войдите**

3. **Нажмите на иконку EditThisCookie** (справа от адресной строки)

4. **Нажмите кнопку "Export"** (иконка экспорта)

5. **Выберите формат JSON**

6. **Скопируйте результат**

7. **Вставьте в бот**

### Для Firefox

1. **Установите "Cookie-Editor"**
   - Ссылка: https://addons.mozilla.org/firefox/addon/cookie-editor/

2. **Откройте instagram.com и войдите**

3. **Нажмите на иконку Cookie-Editor**

4. **Нажмите "Export"**

5. **Выберите "JSON (Netscape)"**

6. **Скопируйте и вставьте в бот**

---

## Способ 2: Через DevTools Application (ВСЕГДА РАБОТАЕТ) ⭐

Этот способ работает в **любом** браузере без установки расширений.

### Пошаговая инструкция:

1. **Откройте instagram.com и войдите в аккаунт**

2. **Нажмите F12** (откроется DevTools)

3. **Перейдите на вкладку "Application"**
   - В Chrome/Edge: **Application**
   - В Firefox: **Storage**

4. **В левой панели найдите: Cookies → https://www.instagram.com**

5. **Вы увидите таблицу со ВСЕМИ cookies**

6. **Теперь есть 2 варианта:**

### Вариант A: Копирование через JavaScript в консоли

1. Перейдите на вкладку **Console** (не закрывая DevTools)

2. Вставьте этот улучшенный скрипт:

```javascript
(async () => {
    // Получаем cookies через cookieStore API (показывает httpOnly)
    try {
        const cookies = await cookieStore.getAll({domain: 'instagram.com'});
        const formatted = cookies.map(c => ({
            name: c.name,
            value: c.value,
            domain: c.domain,
            path: c.path,
            expires: c.expires ? Math.floor(c.expires / 1000) : -1,
            secure: c.secure || false,
            sameSite: c.sameSite || 'None'
        }));
        
        const json = JSON.stringify(formatted, null, 2);
        await navigator.clipboard.writeText(json);
        
        console.log('✅ Получено cookies:', formatted.length);
        console.log('✅ Скопировано в буфер!');
        console.log('sessionid:', formatted.find(c => c.name === 'sessionid') ? '✅ Есть' : '❌ Нет');
        
    } catch(e) {
        console.error('❌ cookieStore API не поддерживается');
        console.error('   Используйте Способ 2B (вручную) или расширение');
    }
})();
```

3. Если скрипт сработал → cookies в буфере! Вставьте в бот.

4. Если ошибка → используйте Вариант B ниже.

### Вариант B: Ручное копирование из Application tab

1. **Вернитесь на вкладку Application → Cookies → instagram.com**

2. **Вы видите таблицу с колонками:**
   - Name
   - Value
   - Domain
   - Path
   - Expires
   - HttpOnly
   - Secure
   - SameSite

3. **Создайте JSON вручную по этому шаблону:**

```json
[
  {
    "name": "СКОПИРУЙТЕ_ИМЯ_ИЗ_КОЛОНКИ_NAME",
    "value": "СКОПИРУЙТЕ_ЗНАЧЕНИЕ_ИЗ_КОЛОНКИ_VALUE",
    "domain": ".instagram.com",
    "path": "/"
  }
]
```

4. **Для каждого cookie в таблице:**
   - Кликните на строку
   - Скопируйте Name
   - Скопируйте Value
   - Добавьте в JSON

5. **ОБЯЗАТЕЛЬНО скопируйте эти cookies:**
   - ✅ `sessionid` (КРИТИЧНО!)
   - ✅ `csrftoken`
   - ✅ `ds_user_id`
   - ✅ `mid`
   - ✅ Все остальные для надёжности

### Пример результата:

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
    "path": "/"
  }
]
```

---

## Способ 3: Через автоматическое расширение (ПРОДВИНУТЫЙ)

Создайте простое расширение Chrome для автоматического экспорта.

### 1. Создайте файл `manifest.json`:

```json
{
  "manifest_version": 3,
  "name": "Instagram Cookie Exporter",
  "version": "1.0",
  "permissions": ["cookies", "activeTab"],
  "host_permissions": ["*://*.instagram.com/*"],
  "action": {
    "default_popup": "popup.html"
  }
}
```

### 2. Создайте `popup.html`:

```html
<!DOCTYPE html>
<html>
<head>
  <title>Export Cookies</title>
  <style>
    body { width: 300px; padding: 20px; }
    button { width: 100%; padding: 10px; }
  </style>
</head>
<body>
  <h3>Instagram Cookies</h3>
  <button id="export">Export All Cookies</button>
  <div id="result"></div>
  <script src="popup.js"></script>
</body>
</html>
```

### 3. Создайте `popup.js`:

```javascript
document.getElementById('export').addEventListener('click', async () => {
  const cookies = await chrome.cookies.getAll({domain: '.instagram.com'});
  
  const formatted = cookies.map(c => ({
    name: c.name,
    value: c.value,
    domain: c.domain,
    path: c.path,
    expires: c.expirationDate ? Math.floor(c.expirationDate) : -1,
    httpOnly: c.httpOnly,
    secure: c.secure,
    sameSite: c.sameSite
  }));
  
  const json = JSON.stringify(formatted, null, 2);
  
  await navigator.clipboard.writeText(json);
  
  document.getElementById('result').innerHTML = 
    `✅ Скопировано ${formatted.length} cookies!`;
});
```

### 4. Загрузите расширение:

1. Chrome → Расширения → Режим разработчика → Загрузить распакованное
2. Выберите папку с файлами
3. Откройте instagram.com
4. Нажмите на иконку расширения
5. Export All Cookies

---

## ✅ Проверка результата

После экспорта проверьте что в JSON есть:

```javascript
// Вставьте в консоль для проверки
const cookies = [/* ваши cookies */];

console.log('Всего cookies:', cookies.length);
console.log('sessionid:', cookies.find(c => c.name === 'sessionid') ? '✅' : '❌');
console.log('csrftoken:', cookies.find(c => c.name === 'csrftoken') ? '✅' : '❌');
console.log('ds_user_id:', cookies.find(c => c.name === 'ds_user_id') ? '✅' : '❌');
```

Должно быть:
- ✅ sessionid: ✅
- ✅ csrftoken: ✅
- ✅ ds_user_id: ✅

---

## 🎯 Рекомендации

### Для новичков:
→ **Способ 1** (расширение EditThisCookie)

### Для опытных:
→ **Способ 2** (DevTools Application)

### Для автоматизации:
→ **Способ 3** (своё расширение)

---

## ❓ FAQ

**Q: Почему `document.cookie` не показывает все cookies?**  
A: Из соображений безопасности cookies с флагом `httpOnly` недоступны для JavaScript на странице.

**Q: Как узнать есть ли у cookie флаг httpOnly?**  
A: Откройте DevTools → Application → Cookies, там есть колонка "HttpOnly" с галочкой.

**Q: Можно ли получить httpOnly cookies через обычный JS?**  
A: Нет, только через расширение браузера или DevTools вручную.

**Q: Безопасно ли использовать расширения?**  
A: Используйте только проверенные расширения с хорошими отзывами (EditThisCookie, Cookie-Editor).

---

## 🔐 Безопасность

⚠️ **Важно:**
- Cookies содержат данные авторизации
- Не передавайте их третьим лицам
- Бот хранит их в зашифрованном виде
- Используйте официальные расширения
- Не публикуйте cookies в открытом доступе

---

## 📞 Поддержка

Если не получается:

1. Попробуйте все 3 способа
2. Проверьте что вы вошли в Instagram
3. Используйте расширение (самый простой способ)
4. Создайте issue в репозитории

---

**Успехов! 🎉**

