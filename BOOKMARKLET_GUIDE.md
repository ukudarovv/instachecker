# 🚀 Букмарклет для автоматического экспорта cookies

## Что это?

**Букмарклет** - это закладка в браузере с JavaScript кодом, которая выполняется одним кликом на любой странице Instagram.

## 📥 Установка (в 3 клика)

### Способ 1: Перетаскивание (самый простой)

1. **Откройте эту страницу** в браузере
2. **Перетащите эту ссылку** в панель закладок:
   
   <a href="javascript:(function(){const c=document.cookie.split(';').map(x=>{const[n,...r]=x.trim().split('=');return{name:n,value:r.join('='),domain:'.instagram.com',path:'/',expires:-1}}).filter(x=>x.name&&x.value);const j=JSON.stringify(c,null,2);const w=window.open('','_blank','width=600,height=800');w.document.write('<html><head><title>Instagram Cookies</title><style>body{font-family:monospace;padding:20px;background:#f5f5f5}pre{background:white;padding:20px;border-radius:8px;overflow:auto}button{background:#4CAF50;color:white;border:none;padding:15px 30px;font-size:16px;border-radius:5px;cursor:pointer;margin:10px 0}button:hover{background:#45a049}</style></head><body><h2>✅ Экспортировано '+c.length+' cookies</h2><button onclick=\"navigator.clipboard.writeText(document.getElementById(\'json\').textContent).then(()=>alert(\'✅ Скопировано!\'))\">📋 Копировать</button><pre id=\"json\">'+j+'</pre></body></html>');navigator.clipboard.writeText(j).then(()=>alert('✅ Cookies скопированы в буфер обмена!'))})();">📤 Export IG Cookies</a>

3. **Готово!** Теперь откройте Instagram и кликните на эту закладку

### Способ 2: Создание вручную

1. **Создайте новую закладку** в браузере (Ctrl+D или ⌘+D)
2. **Название**: `Export IG Cookies` (или любое)
3. **URL**: вставьте этот код:

```javascript
javascript:(function(){const c=document.cookie.split(';').map(x=>{const[n,...r]=x.trim().split('=');return{name:n,value:r.join('='),domain:'.instagram.com',path:'/',expires:-1}}).filter(x=>x.name&&x.value);const j=JSON.stringify(c,null,2);const w=window.open('','_blank','width=600,height=800');w.document.write('<html><head><title>Instagram Cookies</title><style>body{font-family:monospace;padding:20px;background:#f5f5f5}pre{background:white;padding:20px;border-radius:8px;overflow:auto}button{background:#4CAF50;color:white;border:none;padding:15px 30px;font-size:16px;border-radius:5px;cursor:pointer;margin:10px 0}button:hover{background:#45a049}</style></head><body><h2>✅ Экспортировано '+c.length+' cookies</h2><button onclick="navigator.clipboard.writeText(document.getElementById(\'json\').textContent).then(()=>alert(\'✅ Скопировано!\'))">📋 Копировать</button><pre id="json">'+j+'</pre></body></html>');navigator.clipboard.writeText(j).then(()=>alert('✅ Cookies скопированы в буфер обмена!'))})();
```

4. **Сохраните** закладку

## 🎯 Использование

1. **Откройте Instagram** и войдите в аккаунт
2. **Кликните на закладку** "Export IG Cookies"
3. **Cookies автоматически скопированы** в буфер обмена!
4. **Вставьте в бот** (Ctrl+V или ⌘+V)

## ✨ Что делает букмарклет?

1. ✅ Автоматически извлекает все cookies со страницы
2. ✅ Форматирует их в JSON
3. ✅ Копирует в буфер обмена
4. ✅ Открывает окно с предпросмотром
5. ✅ Проверяет наличие sessionid

## 🔧 Альтернативный букмарклет (компактный)

Если первый не работает, попробуйте этот:

```javascript
javascript:(function(){navigator.clipboard.writeText(JSON.stringify(document.cookie.split(';').map(c=>{const[n,...v]=c.trim().split('=');return{name:n,value:v.join('='),domain:'.instagram.com',path:'/',expires:-1}}),null,2));alert('✅ Cookies скопированы!')})()
```

## 📱 Мобильная версия

На мобильных устройствах букмарклеты работают по-другому:

### iOS (Safari)
1. Создайте закладку любой страницы
2. Отредактируйте её
3. Замените URL на код букмарклета
4. Сохраните

### Android (Chrome)
1. Добавьте страницу в закладки
2. Найдите её в списке закладок
3. Нажмите "Изменить"
4. Замените URL на код букмарклета

## 🎨 Букмарклет с красивым UI

Расширенная версия с интерфейсом:

```javascript
javascript:(function(){const c=document.cookie.split(';').map(x=>{const[n,...r]=x.trim().split('=');return{name:n,value:r.join('='),domain:'.instagram.com',path:'/',expires:-1}}).filter(x=>x.name&&x.value);if(c.length===0){alert('❌ Cookies не найдены!');return}const h=c.some(x=>x.name==='sessionid');if(!h){alert('⚠️ sessionid не найден!');return}const j=JSON.stringify(c,null,2);const d=document.createElement('div');d.style.cssText='position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:white;padding:30px;border-radius:15px;box-shadow:0 10px 50px rgba(0,0,0,0.3);z-index:999999;max-width:600px;max-height:80vh;overflow:auto';d.innerHTML='<h2 style="margin:0 0 20px">✅ '+c.length+' Cookies</h2><button onclick="navigator.clipboard.writeText(this.nextElementSibling.textContent);alert(\'✅ Скопировано!\')" style="background:#4CAF50;color:white;border:none;padding:12px 24px;border-radius:8px;cursor:pointer;font-size:14px;margin-bottom:15px">📋 Копировать</button><pre style="background:#f5f5f5;padding:15px;border-radius:8px;overflow:auto;font-size:11px">'+j+'</pre><button onclick="this.parentElement.remove()" style="background:#f44336;color:white;border:none;padding:12px 24px;border-radius:8px;cursor:pointer;font-size:14px;margin-top:15px;width:100%">❌ Закрыть</button>';document.body.appendChild(d);navigator.clipboard.writeText(j)})()
```

## 🎓 Преимущества букмарклета

- ⚡ **Мгновенный** - экспорт за 1 клик
- 🔒 **Безопасный** - работает локально в браузере
- 🎯 **Точный** - всегда актуальные cookies
- 📱 **Универсальный** - работает на всех устройствах
- 🚀 **Быстрый** - не нужно открывать консоль

## 💡 Советы

1. **Используйте на desktop** - удобнее копировать
2. **Добавьте эмодзи** в название закладки для быстрого поиска
3. **Создайте папку** "Instagram Tools" для организации
4. **Обновляйте cookies** раз в месяц для надежности

## 🔧 Troubleshooting

### Букмарклет не работает
- Убедитесь, что вы **на странице Instagram**
- Проверьте, что URL начинается с `javascript:`
- Попробуйте компактную версию

### Cookies не копируются
- Разрешите **доступ к буферу обмена** в настройках браузера
- Используйте кнопку "Копировать" в открывшемся окне

### Нет sessionid
- **Выйдите и войдите** в Instagram заново
- Попробуйте в **режиме инкогнито**
- Проверьте, что **не используете VPN**

---

## 🎯 Итого: 3 способа экспорта

1. **Букмарклет** (рекомендую) - 1 клик ⚡
2. **Консоль браузера** - универсально 🔧
3. **Расширение** - для частого использования 🔄

Выбирайте тот, который удобнее!

