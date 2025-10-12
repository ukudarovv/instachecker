"""Add password field to instagram_sessions table."""

import sqlite3
import sys

def migrate_add_password(db_path: str = "bot.db"):
    """Add password column to instagram_sessions table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if password column already exists
        cursor.execute("PRAGMA table_info(instagram_sessions)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'password' in columns:
            print("✅ Column 'password' already exists in instagram_sessions table")
            return True
        
        # Add password column
        print("Adding 'password' column to instagram_sessions table...")
        cursor.execute("""
            ALTER TABLE instagram_sessions 
            ADD COLUMN password TEXT
        """)
        
        conn.commit()
        print("✅ Migration completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "bot.db"
    print(f"Running migration on database: {db_path}")
    
    success = migrate_add_password(db_path)
    sys.exit(0 if success else 1)

