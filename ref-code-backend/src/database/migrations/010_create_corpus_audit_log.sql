-- Migration 010: Corpus Audit Log
-- Description: Add corpus_audit_log table for admin panel activity tracking
-- Date: 2026-01-19

-- Corpus Audit Log (for admin panel - tracks all corpus changes)
CREATE TABLE IF NOT EXISTS corpus_audit_log (
    id SERIAL PRIMARY KEY,
    corpus_id INTEGER,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL,
    changes TEXT,  -- JSON stored as TEXT
    metadata TEXT,  -- JSON stored as TEXT
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (corpus_id) REFERENCES corpora(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_audit_corpus ON corpus_audit_log(corpus_id);
CREATE INDEX IF NOT EXISTS idx_audit_user ON corpus_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON corpus_audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON corpus_audit_log(timestamp);
