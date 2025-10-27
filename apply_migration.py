#!/usr/bin/env python3
"""Apply migration to add from_date_time column to accounts table."""

import sqlite3
import os
import sys

def apply_migration():
    """Apply the migration to add from_date_time column."""
    
    # Database path
    db_path = "bot.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        sys.exit(1)
    
    print(f"📦 Connecting to database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(accounts)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'from_date_time' in columns:
            print("✅ Column 'from_date_time' already exists. Nothing to do.")
            conn.close()
            return
        
        print("📝 Adding 'from_date_time' column to accounts table...")
        
        # Add the column
        cursor.execute("ALTER TABLE accounts ADD COLUMN from_date_time DATETIME")
        
        # Update existing records
        print("🔄 Updating existing records...")
        cursor.execute("""
            UPDATE accounts 
            SET from_date_time = datetime(from_date || ' 00:00:00')
            WHERE from_date_time IS NULL AND from_date IS NOT NULL
        """)
        
        # Commit changes
        conn.commit()
        
        print(f"✅ Migration completed successfully!")
        print(f"   - Column 'from_date_time' added")
        print(f"   - Updated {cursor.rowcount} existing records")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error applying migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("Migration: Add from_date_time column to accounts table")
    print("=" * 60)
    apply_migration()
    print("=" * 60)

