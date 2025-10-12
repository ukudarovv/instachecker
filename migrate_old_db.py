"""Миграция данных из старой БД в новую."""

import sqlite3
import sys
from datetime import datetime

# Пути к базам данных
OLD_DB = "bu/date.db"
NEW_DB = "bot.db"


def check_old_db_structure():
    """Проверка структуры старой БД."""
    print("🔍 Проверка структуры старой базы данных...\n")
    
    try:
        conn = sqlite3.connect(OLD_DB)
        cursor = conn.cursor()
        
        # Получаем список таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"📊 Найдено таблиц: {len(tables)}\n")
        
        for table in tables:
            table_name = table[0]
            print(f"📋 Таблица: {table_name}")
            
            # Получаем структуру таблицы
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print("   Колонки:")
            for col in columns:
                col_id, col_name, col_type, not_null, default_val, pk = col
                pk_marker = " [PK]" if pk else ""
                print(f"   - {col_name}: {col_type}{pk_marker}")
            
            # Получаем количество записей
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   📈 Записей: {count}\n")
        
        conn.close()
        return tables
        
    except sqlite3.Error as e:
        print(f"❌ Ошибка при чтении старой БД: {e}")
        return []


def check_new_db_structure():
    """Проверка структуры новой БД."""
    print("\n🔍 Проверка структуры новой базы данных...\n")
    
    try:
        conn = sqlite3.connect(NEW_DB)
        cursor = conn.cursor()
        
        # Получаем список таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"📊 Найдено таблиц: {len(tables)}\n")
        
        for table in tables:
            table_name = table[0]
            print(f"📋 Таблица: {table_name}")
            
            # Получаем количество записей
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   📈 Записей: {count}")
        
        conn.close()
        return tables
        
    except sqlite3.Error as e:
        print(f"❌ Ошибка при чтении новой БД: {e}")
        return []


def preview_old_data():
    """Предварительный просмотр данных из старой БД."""
    print("\n👀 Предварительный просмотр данных из старой БД...\n")
    
    try:
        conn = sqlite3.connect(OLD_DB)
        cursor = conn.cursor()
        
        # Получаем список таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            print(f"📋 Таблица: {table_name}")
            
            # Показываем первые 3 записи
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            rows = cursor.fetchall()
            
            if rows:
                # Получаем названия колонок
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [col[1] for col in cursor.fetchall()]
                
                print(f"   Колонки: {', '.join(columns)}")
                print(f"   Первые записи:")
                for i, row in enumerate(rows, 1):
                    print(f"   {i}. {row}")
            else:
                print("   (пусто)")
            print()
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Ошибка: {e}")


def migrate_users():
    """Миграция пользователей."""
    print("\n👥 Миграция пользователей...\n")
    
    try:
        old_conn = sqlite3.connect(OLD_DB)
        new_conn = sqlite3.connect(NEW_DB)
        
        old_cursor = old_conn.cursor()
        new_cursor = new_conn.cursor()
        
        # Проверяем, есть ли таблица users в старой БД
        old_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not old_cursor.fetchone():
            print("⚠️ Таблица 'users' не найдена в старой БД")
            old_conn.close()
            new_conn.close()
            return 0
        
        # Получаем структуру таблицы
        old_cursor.execute("PRAGMA table_info(users)")
        old_columns = {col[1]: col for col in old_cursor.fetchall()}
        
        # Получаем всех пользователей из старой БД
        old_cursor.execute("SELECT * FROM users")
        old_users = old_cursor.fetchall()
        
        # Получаем названия колонок
        old_cursor.execute("PRAGMA table_info(users)")
        column_names = [col[1] for col in old_cursor.fetchall()]
        
        migrated = 0
        skipped = 0
        
        for user_data in old_users:
            user_dict = dict(zip(column_names, user_data))
            user_id = user_dict.get('id')
            
            if not user_id:
                continue
            
            # Проверяем, есть ли уже такой пользователь
            new_cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if new_cursor.fetchone():
                print(f"   ⏭ Пользователь {user_id} уже существует")
                skipped += 1
                continue
            
            # Подготавливаем данные для вставки
            username = user_dict.get('username', f'user_{user_id}')
            is_active = user_dict.get('is_active', 0)
            role = user_dict.get('role', 'user')
            verify_mode = user_dict.get('verify_mode', 'api')
            
            # Вставляем пользователя
            new_cursor.execute(
                "INSERT INTO users (id, username, is_active, role, verify_mode) VALUES (?, ?, ?, ?, ?)",
                (user_id, username, is_active, role, verify_mode)
            )
            
            print(f"   ✅ Мигрирован пользователь: {username} (ID: {user_id})")
            migrated += 1
        
        new_conn.commit()
        old_conn.close()
        new_conn.close()
        
        print(f"\n📊 Итого: мигрировано {migrated}, пропущено {skipped}")
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
        
        # Проверяем, есть ли таблица accounts в старой БД
        old_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts'")
        if not old_cursor.fetchone():
            print("⚠️ Таблица 'accounts' не найдена в старой БД")
            old_conn.close()
            new_conn.close()
            return 0
        
        # Получаем все аккаунты из старой БД
        old_cursor.execute("SELECT * FROM accounts")
        old_accounts = old_cursor.fetchall()
        
        # Получаем названия колонок
        old_cursor.execute("PRAGMA table_info(accounts)")
        column_names = [col[1] for col in old_cursor.fetchall()]
        
        migrated = 0
        skipped = 0
        errors = 0
        
        for account_data in old_accounts:
            account_dict = dict(zip(column_names, account_data))
            
            user_id = account_dict.get('user_id')
            account_name = account_dict.get('account')
            
            if not user_id or not account_name:
                errors += 1
                continue
            
            # Проверяем, существует ли пользователь в новой БД
            new_cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not new_cursor.fetchone():
                print(f"   ⚠️ Пользователь {user_id} не найден, пропускаем аккаунт {account_name}")
                skipped += 1
                continue
            
            # Проверяем, есть ли уже такой аккаунт
            new_cursor.execute(
                "SELECT id FROM accounts WHERE user_id = ? AND account = ?",
                (user_id, account_name)
            )
            if new_cursor.fetchone():
                print(f"   ⏭ Аккаунт @{account_name} уже существует у пользователя {user_id}")
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
            
            print(f"   ✅ Мигрирован аккаунт: @{account_name} (user_id: {user_id})")
            migrated += 1
        
        new_conn.commit()
        old_conn.close()
        new_conn.close()
        
        print(f"\n📊 Итого: мигрировано {migrated}, пропущено {skipped}, ошибок {errors}")
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
        
        # Проверяем, есть ли таблица api в старой БД
        old_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='api'")
        if not old_cursor.fetchone():
            print("⚠️ Таблица 'api' не найдена в старой БД")
            old_conn.close()
            new_conn.close()
            return 0
        
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
                continue
            
            # Проверяем, существует ли пользователь
            new_cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not new_cursor.fetchone():
                print(f"   ⚠️ Пользователь {user_id} не найден, пропускаем ключ")
                skipped += 1
                continue
            
            # Проверяем, есть ли уже такой ключ
            new_cursor.execute("SELECT id FROM api WHERE key = ?", (key_value,))
            if new_cursor.fetchone():
                print(f"   ⏭ API ключ уже существует")
                skipped += 1
                continue
            
            # Подготавливаем данные
            qty_req = key_dict.get('qty_req', 0)
            ref_date = key_dict.get('ref_date')
            is_work = key_dict.get('is_work', 1)
            
            # Вставляем ключ
            new_cursor.execute(
                "INSERT INTO api (user_id, key, qty_req, ref_date, is_work) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, key_value, qty_req, ref_date, is_work)
            )
            
            masked_key = key_value[:4] + "..." + key_value[-4:] if len(key_value) > 8 else "***"
            print(f"   ✅ Мигрирован API ключ: {masked_key} (user_id: {user_id})")
            migrated += 1
        
        new_conn.commit()
        old_conn.close()
        new_conn.close()
        
        print(f"\n📊 Итого: мигрировано {migrated}, пропущено {skipped}")
        return migrated
        
    except sqlite3.Error as e:
        print(f"❌ Ошибка при миграции API ключей: {e}")
        return 0


def main():
    """Главная функция."""
    print("=" * 60)
    print("🔄 МИГРАЦИЯ ДАННЫХ ИЗ СТАРОЙ БД В НОВУЮ")
    print("=" * 60)
    
    # Проверяем структуру БД
    old_tables = check_old_db_structure()
    if not old_tables:
        print("❌ Не удалось прочитать старую БД")
        return
    
    new_tables = check_new_db_structure()
    if not new_tables:
        print("❌ Не удалось прочитать новую БД")
        return
    
    # Предварительный просмотр
    preview_old_data()
    
    # Запрашиваем подтверждение
    print("\n" + "=" * 60)
    print("⚠️  ВНИМАНИЕ!")
    print("=" * 60)
    print("Будет выполнена миграция данных из старой БД в новую.")
    print("Существующие записи в новой БД не будут перезаписаны.")
    print()
    
    response = input("Продолжить миграцию? (да/нет): ").strip().lower()
    
    if response not in ['да', 'yes', 'y', 'д']:
        print("\n❌ Миграция отменена")
        return
    
    print("\n" + "=" * 60)
    print("🚀 НАЧАЛО МИГРАЦИИ")
    print("=" * 60)
    
    # Миграция данных
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
    print("=" * 60)
    
    # Проверяем новую БД после миграции
    print("\n🔍 Проверка новой БД после миграции...\n")
    check_new_db_structure()


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

