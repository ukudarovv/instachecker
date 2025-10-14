# 🔖 Instagram Cookies Bookmarklet

## Что это?

Букмарклет - это закладка в браузере с JavaScript кодом, которая позволяет экспортировать cookies Instagram одним кликом.

## Как установить букмарклет?

### Метод 1: Перетащить в панель закладок

1. Убедитесь что панель закладок видна (Ctrl+Shift+B в Chrome/Edge)
2. Создайте новую закладку
3. В поле URL вставьте код ниже (весь код одной строкой)
4. Назовите закладку "📋 Export IG Cookies"
5. Сохраните

### Метод 2: Создать вручную

1. Нажмите Ctrl+D (создать закладку)
2. В поле URL вставьте код ниже
3. Назовите "📋 Export IG Cookies"
4. Сохраните

## Код букмарклета

```javascript
javascript:(function(){if(!window.location.hostname.includes('instagram.com')){alert('❌ Откройте instagram.com');return}const c=document.cookie.split('; ').map(s=>{const[n,v]=s.split('=');return{name:n,value:decodeURIComponent(v),domain:'.instagram.com',path:'/'}});const h=c.some(x=>x.name==='sessionid');const j=JSON.stringify(c,null,2);if(!h){alert('⚠️ sessionid не найден!\nВойдите в Instagram и попробуйте снова.');return}try{navigator.clipboard.writeText(j).then(()=>{alert('✅ '+c.length+' cookies скопированы!\n\nВставьте в Telegram бот.')}).catch(()=>{prompt('Скопируйте:',j)})}catch(e){prompt('Скопируйте:',j)}})();
```

## Как использовать?

1. Откройте instagram.com в браузере
2. Войдите в ваш аккаунт
3. Нажмите на закладку "📋 Export IG Cookies"
4. Cookies автоматически скопируются в буфер обмена
5. Вставьте их в Telegram бот

## Альтернатива: Скрипт для консоли

Если букмарклет не работает, используйте полный скрипт из файла `instagram_cookies_export.js`:

1. Откройте instagram.com
2. Нажмите F12 (DevTools)
3. Перейдите на вкладку Console
4. Скопируйте содержимое файла `instagram_cookies_export.js`
5. Вставьте в консоль и нажмите Enter
6. Cookies будут скопированы автоматически

## Или самый простой скрипт (одна строка)

Вставьте в консоль браузера на instagram.com:

```javascript
copy(JSON.stringify(document.cookie.split('; ').map(c=>{const[name,value]=c.split('=');return{name,value:decodeURIComponent(value),domain:'.instagram.com',path:'/'}}),null,2))
```

После выполнения cookies будут в буфере обмена - просто вставьте в бот!

## Безопасность

⚠️ **ВАЖНО:**
- Букмарклет работает только на instagram.com
- Не передаёт данные никуда, кроме буфера обмена
- Код открытый, можете проверить сами
- Cookies содержат данные авторизации - не делитесь ими!

## Проверка работы

После экспорта cookies должны выглядеть так:

```json
[
  {
    "name": "sessionid",
    "value": "ваше_значение",
    "domain": ".instagram.com",
    "path": "/"
  },
  ...
]
```

Обязательно должен быть cookie с именем `sessionid` - это главный cookie для авторизации!

