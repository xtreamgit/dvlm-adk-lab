-- Migration: Add message tracking columns to user_sessions
-- Date: 2026-01-23
-- Issue: Chat UI fails with "column user_query_count does not exist"
-- Database: adk_agents_db on adk-multi-agents-db instance

-- Add message_count column
ALTER TABLE user_sessions 
ADD COLUMN IF NOT EXISTS message_count INTEGER DEFAULT 0;

-- Add user_query_count column
ALTER TABLE user_sessions 
ADD COLUMN IF NOT EXISTS user_query_count INTEGER DEFAULT 0;

-- Verify the columns were added
SELECT 
    column_name, 
    data_type, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'user_sessions' 
  AND column_name IN ('message_count', 'user_query_count')
ORDER BY column_name;
