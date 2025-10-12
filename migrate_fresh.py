"""Полная миграция данных из старой БД в новую с очисткой."""

import sqlite3
import sys
from datetime import datetime

# Пути к базам данных
OLD_DB = "bu/date.db"
NEW_DB = "bot.db"


def backup_new_db():
    """Создание резервной копии новой БД."""
    import shutil
    import time
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_name = f"bot_backup_{timestamp}.db"
    
    try:
        shutil.copy2(NEW_DB, backup_name)
        print(f"✅ Резервная копия создана: {backup_name}")
        return backup_name
    except Exception as e:
        print(f"❌ Ошибка создания резервной копии: {e}")
        return None


def clear_new_db_data():
    """Очистка данных в новой БД (оставляем структуру)."""
    print("\n🗑️ Очистка данных в новой БД...\n")
    
    try:
        conn = sqlite3.connect(NEW_DB)
        cursor = conn.cursor()
        
        # Удаляем данные из таблиц (в правильном порядке - сначала зависимые)
        tables_to_clear = [
            "accounts",
            "api", 
            "proxies",
            "instagram_sessions",
            "users"
        ]
        
        for table in tables_to_clear:
            cursor.execute(f"DELETE FROM {table}")
            deleted = cursor.rowcount
            print(f"   🗑️ Очищена таблица {table}: удалено {deleted} записей")
        
        # Оставляем system_settings
        print(f"   ℹ️ Таблица system_settings оставлена без изменений")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Новая БД очищена")
        
    except sqlite3.Error as e:
        print(f"❌ Ошибка при очистке новой БД: {e}")
        sys.exit(1)


def migrate_users():
    """Миграция пользователей."""
    print("\n👥 Миграция пользователей...\n")
    
    try:
        old_conn = sqlite3.connect(OLD_DB)
        new_conn = sqlite3.connect(NEW_DB)
        
        old_cursor = old_conn.cursor()
        new_cursor = new_conn.cursor()
        
        # Получаем всех пользователей из старой БД
        old_cursor.execute("SELECT * FROM users")
        old_users = old_cursor.fetchall()
        
        # Получаем названия колонок
        old_cursor.execute("PRAGMA table_info(users)")
        column_names = [col[1] for col in old_cursor.fetchall()]
        
        migrated = 0
        
        for user_data in old_users:
            user_dict = dict(zip(column_names, user_data))
            user_id = user_dict.get('id')
            
            if not user_id:
                continue
            
            # Подготавливаем данные для вставки
            username = user_dict.get('username', f'user_{user_id}')
            is_active = user_dict.get('is_active', 0)
            
            # Конвертируем is_admin в role
            is_admin = user_dict.get('is_admin', 0)
            role = "admin" if is_admin else "user"
            
            verify_mode = user_dict.get('verify_mode', 'api')
            
            # Вставляем пользователя
            new_cursor.execute(
                "INSERT INTO users (id, username, is_active, role, verify_mode) VALUES (?, ?, ?, ?, ?)",
                (user_id, username, is_active, role, verify_mode)
            )
            
            role_icon = "👑" if role == "admin" else "👤"
            status_icon = "✅" if is_active else "❌"
            print(f"   {status_icon} {role_icon} Мигрирован: {username} (ID: {user_id})")
            migrated += 1
        
        new_conn.commit()
        old_conn.close()
        new_conn.close()
        
        print(f"\n📊 Итого мигрировано: {migrated}")
        return migrated
        
    except sqlite3.Error as e:
        print(f"❌ Ошибка при миграции пользователей: {e}")
        return 0


def migrate_accounts():
    """Миграция аккаунтов."""
    print("\n📱 Миграция аккаунтов...\n")
    
    try:
        old_conn = sqlite3.connect(OLD_DB)
        new_conn = sqlite3.connect(NEW_DB)
        
        old_cursor = old_conn.cursor()
        new_cursor = new_conn.cursor()
        
        # Получаем все аккаунты из старой БД
        old_cursor.execute("SELECT * FROM accounts")
        old_accounts = old_cursor.fetchall()
        
        # Получаем названия колонок
        old_cursor.execute("PRAGMA table_info(accounts)")
        column_names = [col[1] for col in old_cursor.fetchall()]
        
        migrated = 0
        skipped = 0
        
        for account_data in old_accounts:
            account_dict = dict(zip(column_names, account_data))
            
            user_id = account_dict.get('user_id')
            account_name = account_dict.get('account')
            
            if not user_id or not account_name:
                skipped += 1
                continue
            
            # Проверяем, существует ли пользователь в новой БД
            new_cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not new_cursor.fetchone():
                print(f"   ⚠️ Пользователь {user_id} не найден, пропускаем @{account_name}")
                skipped += 1
                continue
            
            # Подготавливаем данные для вставки
            from_date = account_dict.get('from_date')
            period = account_dict.get('period')
            to_date = account_dict.get('to_date')
            date_of_finish = account_dict.get('date_of_finish')
            done = account_dict.get('done', 0)
            
            # Вставляем аккаунт (без id, он auto-increment)
            new_cursor.execute(
                "INSERT INTO accounts (user_id, account, from_date, period, to_date, date_of_finish, done) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, account_name, from_date, period, to_date, date_of_finish, done)
            )
            
            status_icon = "✅" if done else "⏳"
            if migrated < 20 or migrated % 50 == 0:  # Показываем первые 20 и каждый 50-й
                print(f"   {status_icon} @{account_name} (user: {user_id})")
            migrated += 1
        
        new_conn.commit()
        old_conn.close()
        new_conn.close()
        
        print(f"\n📊 Итого: мигрировано {migrated}, пропущено {skipped}")
        return migrated
        
    except sqlite3.Error as e:
        print(f"❌ Ошибка при миграции аккаунтов: {e}")
        return 0


def migrate_api_keys():
    """Миграция API ключей."""
    print("\n🔑 Миграция API ключей...\n")
    
    try:
        old_conn = sqlite3.connect(OLD_DB)
        new_conn = sqlite3.connect(NEW_DB)
        
        old_cursor = old_conn.cursor()
        new_cursor = new_conn.cursor()
        
        # Получаем все API ключи из старой БД
        old_cursor.execute("SELECT * FROM api")
        old_keys = old_cursor.fetchall()
        
        # Получаем названия колонок
        old_cursor.execute("PRAGMA table_info(api)")
        column_names = [col[1] for col in old_cursor.fetchall()]
        
        migrated = 0
        skipped = 0
        
        for key_data in old_keys:
            key_dict = dict(zip(column_names, key_data))
            
            user_id = key_dict.get('user_id')
            key_value = key_dict.get('key')
            
            if not user_id or not key_value:
                skipped += 1
                continue
            
            # Проверяем, существует ли пользователь
            new_cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not new_cursor.fetchone():
                print(f"   ⚠️ Пользователь {user_id} не найден, пропускаем ключ")
                skipped += 1
                continue
            
            # Подготавливаем данные
            qty_req = key_dict.get('qty_req', 0)
            ref_date = key_dict.get('ref_date')
            is_work = key_dict.get('is_work', 1)
            
            # Вставляем ключ
            try:
                new_cursor.execute(
                    "INSERT INTO api (user_id, key, qty_req, ref_date, is_work) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (user_id, key_value, qty_req, ref_date, is_work)
                )
                
                masked_key = key_value[:4] + "..." + key_value[-4:] if len(key_value) > 8 else "***"
                status_icon = "✅" if is_work else "❌"
                print(f"   {status_icon} {masked_key} (user: {user_id})")
                migrated += 1
            except sqlite3.IntegrityError:
                # Ключ уже существует (UNIQUE constraint)
                skipped += 1
                continue
        
        new_conn.commit()
        old_conn.close()
        new_conn.close()
        
        print(f"\n📊 Итого: мигрировано {migrated}, пропущено {skipped}")
        return migrated
        
    except sqlite3.Error as e:
        print(f"❌ Ошибка при миграции API ключей: {e}")
        return 0


def show_statistics():
    """Показать статистику обеих БД."""
    print("\n📊 СТАТИСТИКА БАЗ ДАННЫХ:")
    print("=" * 60)
    
    # Старая БД
    try:
        old_conn = sqlite3.connect(OLD_DB)
        old_cursor = old_conn.cursor()
        
        print("\n🗂️ СТАРАЯ БД (bu/date.db):")
        old_cursor.execute("SELECT COUNT(*) FROM users")
        print(f"   👥 Пользователей: {old_cursor.fetchone()[0]}")
        old_cursor.execute("SELECT COUNT(*) FROM accounts")
        print(f"   📱 Аккаунтов: {old_cursor.fetchone()[0]}")
        old_cursor.execute("SELECT COUNT(*) FROM api")
        print(f"   🔑 API ключей: {old_cursor.fetchone()[0]}")
        
        old_conn.close()
    except Exception as e:
        print(f"❌ Ошибка чтения старой БД: {e}")
    
    # Новая БД
    try:
        new_conn = sqlite3.connect(NEW_DB)
        new_cursor = new_conn.cursor()
        
        print("\n🆕 НОВАЯ БД (bot.db):")
        new_cursor.execute("SELECT COUNT(*) FROM users")
        print(f"   👥 Пользователей: {new_cursor.fetchone()[0]}")
        new_cursor.execute("SELECT COUNT(*) FROM accounts")
        print(f"   📱 Аккаунтов: {new_cursor.fetchone()[0]}")
        new_cursor.execute("SELECT COUNT(*) FROM api")
        print(f"   🔑 API ключей: {new_cursor.fetchone()[0]}")
        new_cursor.execute("SELECT COUNT(*) FROM proxies")
        print(f"   🌐 Прокси: {new_cursor.fetchone()[0]}")
        new_cursor.execute("SELECT COUNT(*) FROM instagram_sessions")
        print(f"   📸 IG-сессий: {new_cursor.fetchone()[0]}")
        
        new_conn.close()
    except Exception as e:
        print(f"❌ Ошибка чтения новой БД: {e}")
    
    print("=" * 60)


def main():
    """Главная функция."""
    print("=" * 60)
    print("🔄 ПОЛНАЯ МИГРАЦИЯ ДАННЫХ (С ОЧИСТКОЙ)")
    print("=" * 60)
    
    # Показываем текущую статистику
    show_statistics()
    
    # Предупреждение
    print("\n" + "=" * 60)
    print("⚠️  ВНИМАНИЕ! ВАЖНО!")
    print("=" * 60)
    print()
    print("Эта операция:")
    print("1. Создаст резервную копию новой БД")
    print("2. УДАЛИТ все данные из новой БД:")
    print("   - Пользователей")
    print("   - Аккаунты")
    print("   - API ключи")
    print("   - Прокси")
    print("   - Instagram сессии")
    print("3. Перенесёт данные из старой БД:")
    print("   - Пользователей")
    print("   - Аккаунты")
    print("   - API ключи")
    print()
    print("⚠️ system_settings и proxies/instagram_sessions останутся!")
    print()
    
    response = input("Продолжить полную миграцию? (да/нет): ").strip().lower()
    
    if response not in ['да', 'yes', 'y', 'д']:
        print("\n❌ Миграция отменена")
        return
    
    # Создаем резервную копию
    print("\n" + "=" * 60)
    print("💾 СОЗДАНИЕ РЕЗЕРВНОЙ КОПИИ")
    print("=" * 60)
    backup = backup_new_db()
    if not backup:
        print("❌ Не удалось создать резервную копию. Миграция отменена.")
        return
    
    # Очищаем новую БД
    print("\n" + "=" * 60)
    print("🗑️ ОЧИСТКА НОВОЙ БД")
    print("=" * 60)
    clear_new_db_data()
    
    # Миграция данных
    print("\n" + "=" * 60)
    print("🚀 МИГРАЦИЯ ДАННЫХ")
    print("=" * 60)
    
    users_migrated = migrate_users()
    accounts_migrated = migrate_accounts()
    keys_migrated = migrate_api_keys()
    
    # Итоги
    print("\n" + "=" * 60)
    print("✅ МИГРАЦИЯ ЗАВЕРШЕНА!")
    print("=" * 60)
    print(f"👥 Пользователей: {users_migrated}")
    print(f"📱 Аккаунтов: {accounts_migrated}")
    print(f"🔑 API ключей: {keys_migrated}")
    print(f"\n📊 Всего мигрировано: {users_migrated + accounts_migrated + keys_migrated} записей")
    print(f"💾 Резервная копия: {backup}")
    print("=" * 60)
    
    # Финальная статистика
    show_statistics()
    
    print("\n✅ Миграция успешно завершена!")
    print(f"💡 Резервная копия сохранена в: {backup}")
    print("🚀 Перезапустите бота для применения изменений!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Миграция прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

