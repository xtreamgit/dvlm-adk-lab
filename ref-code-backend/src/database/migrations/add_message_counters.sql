-- Migration: Add message counters to user_sessions table
-- This tracks the number of messages and user queries per session
-- SQLite compatible version (uses ALTER TABLE directly, ignores duplicates)

-- Add message_count column if it doesn't exist
-- SQLite will error if column exists, migration runner handles this
ALTER TABLE user_sessions ADD COLUMN message_count INTEGER DEFAULT 0;

-- Add user_query_count column if it doesn't exist
-- SQLite will error if column exists, migration runner handles this
ALTER TABLE user_sessions ADD COLUMN user_query_count INTEGER DEFAULT 0;

-- Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_user_sessions_message_count ON user_sessions(message_count);
