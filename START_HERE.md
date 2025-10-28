# 🚀 НАЧНИТЕ ОТСЮДА

## ✅ Система интегрирована!

Ваш Telegram бот теперь **автоматически выбирает разный прокси** при каждой проверке аккаунта!

---

## 🎯 3 команды для запуска

### 1️⃣ Импорт прокси

Создайте файл `proxies.txt` с вашим списком:
```
82.24.225.134:7975:aiiigauk:pi8vftb70eic
46.202.227.191:6185:aiiigauk:pi8vftb70eic
66.78.34.158:5777:aiiigauk:pi8vftb70eic
... (весь список)
```

Импортируйте:
```bash
python batch_add_proxies.py --user-id 1 --file proxies.txt --test
```

### 2️⃣ Проверка ротации (опционально)

```bash
python test_proxy_rotation.py --user-id 1 --iterations 10
```

Должно показать:
```
✅ Уникальных прокси: 10/10
✅ ОТЛИЧНО! Каждый раз новый прокси!
```

### 3️⃣ Запуск бота

```bash
python run_bot.py
```

**Готово!** 🎉

---

## 📱 Проверка в Telegram

1. Откройте бота
2. Проверьте любой аккаунт
3. Посмотрите логи - должны быть **разные IP**:

```
🔗 Selected best proxy: 82.24.225.134:7975
```

Следующая проверка:
```
🔗 Selected best proxy: 66.78.34.158:5777  ← ДРУГОЙ!
```

---

## 🎯 Как это работает

- **Каждая проверка** → **разный прокси**
- **Автоматический выбор** лучших прокси
- **Автоматическая деактивация** нерабочих
- **Мониторинг** каждые 5 минут

---

## 📚 Полная документация

- **`README_INTEGRATION.md`** - Краткая сводка ← **Прочтите это!**
- **`QUICK_START_TELEGRAM_BOT.md`** - Подробный гайд
- **`INTEGRATION_COMPLETE_CHECKLIST.md`** - Детальный чек-лист

---

## ❓ Проблемы?

### Прокси не ротируются?
```bash
python test_proxy_rotation.py --user-id 1 --iterations 10
```
Если показывает один и тот же прокси - добавьте больше прокси.

### Все прокси в cooldown?
```bash
python -c "
from project.database import get_session_factory
from project.services.proxy_manager import ProxyManager
SessionLocal = get_session_factory()
with SessionLocal() as session:
    manager = ProxyManager(session)
    count = manager.reset_cooldowns(user_id=1)
    print(f'Reset {count} proxies')
"
```

### ProxyHealthChecker не работает?
Проверьте логи при запуске - должна быть строка:
```
🏥 Starting Proxy Health Checker...
```

---

## ✅ Быстрая проверка

```bash
# Статистика
python -c "
from project.database import get_session_factory
from project.services.proxy_manager import ProxyManager
SessionLocal = get_session_factory()
with SessionLocal() as session:
    manager = ProxyManager(session)
    stats = manager.get_proxy_stats(user_id=1)
    print(f'Активных: {stats[\"active\"]}/{stats[\"total\"]}')
    print(f'Success rate: {stats[\"success_rate\"]}%')
"
```

---

**Всё работает!** 🚀 Наслаждайтесь автоматической ротацией прокси! 🎉





