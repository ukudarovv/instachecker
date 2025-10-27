-- Add from_date_time column to accounts table
-- This column stores the exact datetime when the account was added

ALTER TABLE accounts ADD COLUMN from_date_time DATETIME;

-- Update existing records: set from_date_time to the beginning of from_date
UPDATE accounts 
SET from_date_time = datetime(from_date || ' 00:00:00')
WHERE from_date_time IS NULL AND from_date IS NOT NULL;

