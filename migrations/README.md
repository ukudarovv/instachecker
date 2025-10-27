# Database Migrations

## How to apply migrations

### On the server (Linux):

1. Stop the bot:
```bash
sudo systemctl stop instagram-bot
```

2. Navigate to the bot directory:
```bash
cd /root/bot
```

3. Apply the migration:
```bash
python3 apply_migration.py
```

4. Start the bot:
```bash
sudo systemctl start instagram-bot
```

### Local (Windows):

1. Run the migration script:
```bash
python apply_migration.py
```

## Available Migrations

### add_from_date_time_column.sql
Adds `from_date_time` column to `accounts` table for precise time tracking of when accounts were added.

**Changes:**
- Adds `from_date_time` DATETIME column
- Updates existing records to set `from_date_time` to beginning of `from_date`

