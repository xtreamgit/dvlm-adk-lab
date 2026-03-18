-- Fix user_sessions table - add missing columns
-- Date: 2026-01-23
-- Issue: Chat UI failing due to missing message_count and user_query_count columns

-- Add missing columns to user_sessions table
ALTER TABLE user_sessions 
ADD COLUMN IF NOT EXISTS message_count INTEGER DEFAULT 0;

ALTER TABLE user_sessions 
ADD COLUMN IF NOT EXISTS user_query_count INTEGER DEFAULT 0;

-- Verify the changes
SELECT 
    column_name, 
    data_type, 
    column_default,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'user_sessions'
ORDER BY ordinal_position;
