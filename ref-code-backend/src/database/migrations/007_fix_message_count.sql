-- Migration 007: Fix message_count column (add if missing)
-- This fixes the issue where migration 004 was empty and the column was never added

-- Attempt to add message_count column
-- If it already exists, this will error but the error will be caught by the migration runner
ALTER TABLE user_sessions ADD COLUMN message_count INTEGER DEFAULT 0;
