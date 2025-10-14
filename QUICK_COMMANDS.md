# 🚀 Быстрые команды

## Для пользователя

### 1. Экспорт cookies из браузера

Откройте instagram.com, нажмите F12 → Console, вставьте:

```javascript
copy(JSON.stringify(document.cookie.split('; ').map(c=>{const[name,value]=c.split('=');return{name,value:decodeURIComponent(value),domain:'.instagram.com',path:'/'}}),null,2))
```

### 2. Конвертация формата cookies

Если у вас cookies в формате объекта `{}`:

```bash
python convert_cookies_format.py
```

### 3. Проверка cookies

```bash
python test_cookies.py cookies.json
```

## Для разработчика

### Тестирование

```bash
# Проверка линтера
python -m flake8 project/services/ig_simple_checker.py
python -m flake8 project/handlers/ig_menu.py
python -m flake8 project/bot.py

# Запуск бота
python start_bot.py
```

### Git

```bash
# Коммит изменений
git add .
git commit -m "Fix Instagram cookies handling

- Fixed Playwright cookie handling
- Added cookies validation
- Created comprehensive documentation
- Added conversion and validation tools

Closes #[issue-number]"

# Push
git push origin master
```

## Структура файлов

```
📁 Документация (начните отсюда):
  📄 ИТОГОВАЯ_СВОДКА.md          ← НАЧНИТЕ ОТСЮДА!
  📄 COOKIES_QUICKSTART.md
  📄 README_INSTAGRAM_COOKIES.md

📁 Инструменты:
  📄 instagram_cookies_export.js
  🐍 convert_cookies_format.py
  🐍 test_cookies.py

📁 Измененный код:
  🐍 project/services/ig_simple_checker.py
  🐍 project/handlers/ig_menu.py
  🐍 project/bot.py
```

## Быстрые тесты

### Тест 1: Правильный формат
```bash
echo '[{"name":"sessionid","value":"test123"}]' > test.json
python test_cookies.py test.json
rm test.json
```

### Тест 2: Конвертация
```python
python convert_cookies_format.py
# Вставьте: {"sessionid": "123", "csrftoken": "abc"}
# Получите: [{"name": "sessionid", "value": "123", ...}, ...]
```

## Полезные ссылки

- **Instagram:** https://instagram.com
- **EditThisCookie:** https://chrome.google.com/webstore/detail/editthiscookie/
- **Cookie-Editor:** https://addons.mozilla.org/firefox/addon/cookie-editor/

## Горячие клавиши

- **F12** - Открыть DevTools
- **Ctrl+Shift+C** - Инспектор элементов
- **Ctrl+L** - Очистить консоль
- **Ctrl+V** - Вставить

## Чеклист

- [ ] Войти в Instagram в браузере
- [ ] Экспортировать cookies (скрипт выше)
- [ ] Добавить в бот (Instagram → Добавить IG-сессию)
- [ ] Проверить статус (Мои IG-сессии → ✅)
- [ ] Протестировать (Проверить через IG)
- [ ] Готово! 🎉

## Поддержка

При проблемах проверьте:
1. `ИТОГОВАЯ_СВОДКА.md` - итоговое резюме
2. `COOKIES_QUICKSTART.md` - быстрый старт
3. `README_INSTAGRAM_COOKIES.md` - полное руководство
4. Логи бота

---

**Всё готово! Начинайте работу! 🚀**

