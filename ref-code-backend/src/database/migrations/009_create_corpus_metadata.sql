-- Migration 009: Corpus Metadata
-- Description: Add corpus_metadata table for admin panel tracking
-- Date: 2026-01-19

-- Corpus Metadata (for admin panel - tracks sync status, tags, etc.)
CREATE TABLE IF NOT EXISTS corpus_metadata (
    id SERIAL PRIMARY KEY,
    corpus_id INTEGER NOT NULL UNIQUE,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_synced_at TIMESTAMP,
    last_synced_by INTEGER,
    sync_status VARCHAR(50) DEFAULT 'active',
    sync_error_message TEXT,
    document_count INTEGER DEFAULT 0,
    last_document_count_update TIMESTAMP,
    tags TEXT,  -- JSON stored as TEXT
    notes TEXT,
    FOREIGN KEY (corpus_id) REFERENCES corpora(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (last_synced_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_corpus_metadata_corpus ON corpus_metadata(corpus_id);
CREATE INDEX IF NOT EXISTS idx_corpus_metadata_status ON corpus_metadata(sync_status);
CREATE INDEX IF NOT EXISTS idx_corpus_metadata_created_by ON corpus_metadata(created_by);
CREATE INDEX IF NOT EXISTS idx_corpus_metadata_last_synced ON corpus_metadata(last_synced_at);

-- Populate metadata for existing corpora
INSERT INTO corpus_metadata (corpus_id, created_at, sync_status)
SELECT id, created_at, 'active'
FROM corpora
WHERE id NOT IN (SELECT corpus_id FROM corpus_metadata)
ON CONFLICT (corpus_id) DO NOTHING;
