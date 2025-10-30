"""
Migration: Add auto_check_interval and auto_check_enabled to User model
"""
from sqlalchemy import create_engine, text

def migrate():
    """Add auto_check_interval and auto_check_enabled columns to users table"""
    engine = create_engine('sqlite:///bot.db', echo=False)
    
    with engine.connect() as conn:
        # Check if columns already exist
        result = conn.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result.fetchall()]
        
        # Add auto_check_interval column
        if 'auto_check_interval' not in columns:
            print("[MIGRATION] Adding auto_check_interval column to users table...")
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN auto_check_interval INTEGER NOT NULL DEFAULT 5"
            ))
            conn.commit()
            print("[MIGRATION] ✅ Added auto_check_interval column (default: 5 minutes)")
        else:
            print("[MIGRATION] ⚠️ auto_check_interval column already exists")
        
        # Add auto_check_enabled column
        if 'auto_check_enabled' not in columns:
            print("[MIGRATION] Adding auto_check_enabled column to users table...")
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN auto_check_enabled BOOLEAN NOT NULL DEFAULT 1"
            ))
            conn.commit()
            print("[MIGRATION] ✅ Added auto_check_enabled column (default: True)")
        else:
            print("[MIGRATION] ⚠️ auto_check_enabled column already exists")
    
    print("[MIGRATION] ✅ Migration completed successfully!")

if __name__ == "__main__":
    migrate()

