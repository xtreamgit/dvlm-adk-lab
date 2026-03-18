-- PostgreSQL Migration: Add Admin Panel Tables
-- Description: Add corpus_metadata, corpus_audit_log, and corpus_sync_schedule tables
-- Date: 2026-01-14

-- Audit log for all corpus changes
CREATE TABLE IF NOT EXISTS corpus_audit_log (
    id SERIAL PRIMARY KEY,
    corpus_id INTEGER,
    user_id INTEGER,
    action VARCHAR(50) NOT NULL, -- 'created', 'updated', 'deleted', 'granted_access', 'revoked_access', 'synced', 'activated', 'deactivated'
    changes JSONB, -- Store before/after snapshot
    metadata JSONB, -- Additional context (IP, user agent, etc)
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (corpus_id) REFERENCES corpora(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Enhanced corpus metadata
CREATE TABLE IF NOT EXISTS corpus_metadata (
    id SERIAL PRIMARY KEY,
    corpus_id INTEGER UNIQUE NOT NULL,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_synced_at TIMESTAMP,
    last_synced_by INTEGER,
    document_count INTEGER DEFAULT 0,
    last_document_count_update TIMESTAMP,
    sync_status VARCHAR(50) DEFAULT 'active', -- 'active', 'syncing', 'error', 'deleted'
    sync_error_message TEXT,
    tags JSONB, -- For categorization
    notes TEXT, -- Admin notes
    FOREIGN KEY (corpus_id) REFERENCES corpora(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (last_synced_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Scheduled sync jobs (for future automation)
CREATE TABLE IF NOT EXISTS corpus_sync_schedule (
    id SERIAL PRIMARY KEY,
    corpus_id INTEGER,
    frequency VARCHAR(50), -- 'hourly', 'daily', 'weekly'
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (corpus_id) REFERENCES corpora(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_audit_corpus ON corpus_audit_log(corpus_id);
CREATE INDEX IF NOT EXISTS idx_audit_user ON corpus_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON corpus_audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_action ON corpus_audit_log(action);
CREATE INDEX IF NOT EXISTS idx_corpus_metadata_corpus ON corpus_metadata(corpus_id);
CREATE INDEX IF NOT EXISTS idx_corpus_metadata_status ON corpus_metadata(sync_status);
CREATE INDEX IF NOT EXISTS idx_sync_schedule_corpus ON corpus_sync_schedule(corpus_id);
CREATE INDEX IF NOT EXISTS idx_sync_schedule_active ON corpus_sync_schedule(is_active);

-- Add permission column to group_corpora if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'group_corpora' AND column_name = 'permission'
    ) THEN
        ALTER TABLE group_corpora ADD COLUMN permission VARCHAR(50) DEFAULT 'read';
    END IF;
END $$;

-- Create user_sessions table if it doesn't exist (for admin dashboard)
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    agent_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_session_id ON user_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(is_active);
