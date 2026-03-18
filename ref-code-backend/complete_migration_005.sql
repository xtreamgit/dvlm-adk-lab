-- Complete Migration 005: Add missing index
-- The column was added but the index might be missing
-- Date: 2026-01-23

-- Create the index for performance on user query count queries
CREATE INDEX IF NOT EXISTS idx_sessions_user_query_count ON user_sessions(user_query_count);

-- Verify the index exists
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'user_sessions' 
  AND indexname = 'idx_sessions_user_query_count';
