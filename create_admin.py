"""Создание администратора после миграции."""

import sqlite3

# ЗАМЕНИТЕ НА ВАШ TELEGRAM ID!
YOUR_TELEGRAM_ID = 1972775559  # Пример: umar_qz

DB_PATH = "bot.db"


def create_admin(user_id):
    """Сделать пользователя администратором."""
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Проверяем, существует ли пользователь
        cursor.execute("SELECT id, username, is_active, role FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ Пользователь с ID {user_id} не найден в БД")
            print("\n💡 Сначала напишите /start боту, чтобы создать учетную запись")
            conn.close()
            return False
        
        user_id_db, username, is_active, role = user
        
        print(f"\n👤 Найден пользователь:")
        print(f"   ID: {user_id_db}")
        print(f"   Username: {username or 'не указан'}")
        print(f"   Активен: {'✅ Да' if is_active else '❌ Нет'}")
        print(f"   Роль: {role}")
        
        # Обновляем пользователя
        cursor.execute(
            "UPDATE users SET is_active = 1, role = 'admin' WHERE id = ?",
            (user_id,)
        )
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Пользователь {username or user_id} теперь администратор!")
        print(f"✅ Доступ активирован!")
        print(f"\n🚀 Теперь можете открыть бота и нажать 'Админка'")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Ошибка БД: {e}")
        return False


def show_all_users():
    """Показать всех пользователей."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, username, is_active, role FROM users ORDER BY id")
        users = cursor.fetchall()
        
        if not users:
            print("📭 Нет пользователей в БД")
            conn.close()
            return
        
        print(f"\n👥 Все пользователи в БД ({len(users)}):\n")
        print(f"{'ID':<12} {'Username':<25} {'Активен':<10} {'Роль':<10}")
        print("-" * 60)
        
        for user_id, username, is_active, role in users:
            active_icon = "✅" if is_active else "❌"
            role_icon = "👑" if role in ["admin", "superuser"] else "👤"
            username_display = username or "не указан"
            print(f"{user_id:<12} {username_display:<25} {active_icon:<10} {role_icon} {role}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Ошибка: {e}")


def main():
    """Главная функция."""
    print("=" * 60)
    print("👑 СОЗДАНИЕ АДМИНИСТРАТОРА")
    print("=" * 60)
    
    # Показываем всех пользователей
    show_all_users()
    
    print("\n" + "=" * 60)
    print("💡 ИНСТРУКЦИЯ:")
    print("=" * 60)
    print("1. Найдите ваш Telegram ID в списке выше")
    print("2. Или узнайте его через бота @userinfobot")
    print("3. Введите ваш ID ниже")
    print()
    
    # Запрашиваем ID
    try:
        user_input = input("Введите Telegram ID для назначения администратором: ").strip()
        
        if not user_input:
            print("❌ ID не введен")
            return
        
        user_id = int(user_input)
        
        # Создаем администратора
        print("\n" + "=" * 60)
        print("🚀 НАЗНАЧЕНИЕ АДМИНИСТРАТОРА")
        print("=" * 60)
        
        success = create_admin(user_id)
        
        if success:
            print("\n" + "=" * 60)
            print("✅ ГОТОВО!")
            print("=" * 60)
            print("\nТеперь:")
            print("1. Перезапустите бота: python run_bot.py")
            print("2. Откройте бота в Telegram")
            print("3. Нажмите кнопку 'Админка'")
            print("4. Откройте 'Управление пользователями'")
            print("\n🎉 Приятного использования!")
        
    except ValueError:
        print("❌ Некорректный ID. Введите число.")
    except KeyboardInterrupt:
        print("\n\n❌ Отменено пользователем")


if __name__ == "__main__":
    main()

