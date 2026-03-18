-- Migration 005: Add user_query_count to user_sessions
-- Description: Track number of user queries separately from total messages
-- Date: 2026-01-09
-- Purpose: Distinguish between user queries and total messages (which includes agent responses)

-- Add user_query_count column to user_sessions
ALTER TABLE user_sessions ADD COLUMN user_query_count INTEGER DEFAULT 0;

-- Create index for performance on user query count queries
CREATE INDEX IF NOT EXISTS idx_sessions_user_query_count ON user_sessions(user_query_count);
