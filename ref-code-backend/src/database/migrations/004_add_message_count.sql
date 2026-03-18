-- Migration: Add message_count column to user_sessions table
-- This column tracks the total number of chat messages in a session

-- SQLite doesn't support adding multiple columns in one statement or adding with DEFAULT,
-- so we need to add them separately
ALTER TABLE user_sessions ADD COLUMN message_count INTEGER DEFAULT 0;
