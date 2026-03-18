-- Migration 008: Create document_access_log table
-- Purpose: Audit trail for document retrieval and access
-- Created: 2026-01-16

CREATE TABLE IF NOT EXISTS document_access_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    corpus_id INTEGER NOT NULL REFERENCES corpora(id) ON DELETE CASCADE,
    document_name VARCHAR(255) NOT NULL,
    document_file_id VARCHAR(255),
    access_type VARCHAR(50) DEFAULT 'view',
    success BOOLEAN NOT NULL,
    error_message TEXT,
    source_uri TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_document_access_user ON document_access_log(user_id, accessed_at);
CREATE INDEX IF NOT EXISTS idx_document_access_corpus ON document_access_log(corpus_id, accessed_at);
CREATE INDEX IF NOT EXISTS idx_document_access_time ON document_access_log(accessed_at);
CREATE INDEX IF NOT EXISTS idx_document_access_success ON document_access_log(success, accessed_at);

-- Comments
-- TABLE: Audit trail for all document retrieval and access attempts
-- COLUMN access_type: Type of access: view, download, preview
-- COLUMN success: Whether the access attempt was successful
-- COLUMN error_message: Error message if access failed
