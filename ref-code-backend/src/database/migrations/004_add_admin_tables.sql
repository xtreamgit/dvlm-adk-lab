-- Migration 004: Admin Tables
-- Description: Add admin-specific tables for corpus management and auditing
-- Date: 2026-01-08
-- Updated: 2026-01-28 - Converted to PostgreSQL syntax

-- Audit log for all corpus changes
CREATE TABLE IF NOT EXISTS corpus_audit_log (
    id SERIAL PRIMARY KEY,
    corpus_id INTEGER,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL, -- 'created', 'updated', 'deleted', 'granted_access', 'revoked_access', 'synced', 'activated', 'deactivated'
    changes JSONB, -- JSON: Store before/after snapshot
    metadata JSONB, -- JSON: Additional context (IP, user agent, etc)
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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_synced_at TIMESTAMP,
    last_synced_by INTEGER,
    document_count INTEGER DEFAULT 0,
    last_document_count_update TIMESTAMP,
    sync_status VARCHAR(50) DEFAULT 'active', -- 'active', 'syncing', 'error', 'deleted'
    sync_error_message TEXT,
    tags JSONB DEFAULT '[]'::jsonb, -- JSON: For categorization
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
