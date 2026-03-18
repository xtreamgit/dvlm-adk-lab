-- Cloud Database Schema Migration
-- Purpose: Add missing admin panel tables and fix schema differences
-- Target: Cloud SQL PostgreSQL (adk_agents_db)
-- Date: 2026-01-22

-- =============================================================================
-- ADMIN PANEL TABLES
-- =============================================================================

-- 1. Corpus Audit Log (for /admin/audit endpoint)
CREATE TABLE IF NOT EXISTS corpus_audit_log (
    id SERIAL PRIMARY KEY,
    corpus_id INTEGER,
    user_id INTEGER,
    action VARCHAR(50) NOT NULL,
    changes TEXT,
    metadata TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (corpus_id) REFERENCES corpora(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 2. Corpus Metadata (for corpus sync tracking and admin panel display)
CREATE TABLE IF NOT EXISTS corpus_metadata (
    id SERIAL PRIMARY KEY,
    corpus_id INTEGER UNIQUE NOT NULL,
    tags TEXT[],
    notes TEXT,
    document_count INTEGER DEFAULT 0,
    last_sync TIMESTAMP,
    sync_status VARCHAR(50) DEFAULT 'unknown',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (corpus_id) REFERENCES corpora(id) ON DELETE CASCADE
);

-- 3. Corpus Sync Schedule (for automated corpus synchronization)
CREATE TABLE IF NOT EXISTS corpus_sync_schedule (
    id SERIAL PRIMARY KEY,
    corpus_id INTEGER UNIQUE NOT NULL,
    schedule_cron VARCHAR(100),
    is_enabled BOOLEAN DEFAULT FALSE,
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (corpus_id) REFERENCES corpora(id) ON DELETE CASCADE
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Audit log indexes
CREATE INDEX IF NOT EXISTS idx_audit_corpus ON corpus_audit_log(corpus_id);
CREATE INDEX IF NOT EXISTS idx_audit_user ON corpus_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON corpus_audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON corpus_audit_log(timestamp);

-- Corpus metadata indexes
CREATE INDEX IF NOT EXISTS idx_corpus_metadata_corpus ON corpus_metadata(corpus_id);
CREATE INDEX IF NOT EXISTS idx_corpus_metadata_status ON corpus_metadata(sync_status);

-- Sync schedule indexes
CREATE INDEX IF NOT EXISTS idx_sync_schedule_corpus ON corpus_sync_schedule(corpus_id);
CREATE INDEX IF NOT EXISTS idx_sync_schedule_enabled ON corpus_sync_schedule(is_enabled);

-- =============================================================================
-- ADDITIONAL SCHEMA FIXES (if needed)
-- =============================================================================

-- Ensure user_profiles has all required columns
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_profiles' AND column_name = 'theme'
    ) THEN
        ALTER TABLE user_profiles ADD COLUMN theme VARCHAR(50) DEFAULT 'light';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_profiles' AND column_name = 'language'
    ) THEN
        ALTER TABLE user_profiles ADD COLUMN language VARCHAR(10) DEFAULT 'en';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_profiles' AND column_name = 'timezone'
    ) THEN
        ALTER TABLE user_profiles ADD COLUMN timezone VARCHAR(50) DEFAULT 'UTC';
    END IF;
END $$;

-- Ensure corpora table has vertex_corpus_id column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'corpora' AND column_name = 'vertex_corpus_id'
    ) THEN
        ALTER TABLE corpora ADD COLUMN vertex_corpus_id VARCHAR(255);
    END IF;
END $$;

-- Ensure agents table has all required columns for agent configuration
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'agents' AND column_name = 'instructions'
    ) THEN
        ALTER TABLE agents ADD COLUMN instructions TEXT;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'agents' AND column_name = 'model'
    ) THEN
        ALTER TABLE agents ADD COLUMN model VARCHAR(255) DEFAULT 'gemini-2.0-flash-exp';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'agents' AND column_name = 'temperature'
    ) THEN
        ALTER TABLE agents ADD COLUMN temperature FLOAT DEFAULT 0.7;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'agents' AND column_name = 'top_p'
    ) THEN
        ALTER TABLE agents ADD COLUMN top_p FLOAT DEFAULT 0.95;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'agents' AND column_name = 'top_k'
    ) THEN
        ALTER TABLE agents ADD COLUMN top_k INTEGER DEFAULT 40;
    END IF;
END $$;

-- =============================================================================
-- DATA INITIALIZATION
-- =============================================================================

-- Initialize corpus_metadata for existing corpora
INSERT INTO corpus_metadata (corpus_id, sync_status, document_count)
SELECT id, 'unknown', 0
FROM corpora
WHERE id NOT IN (SELECT corpus_id FROM corpus_metadata)
ON CONFLICT (corpus_id) DO NOTHING;

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Check admin tables exist
DO $$ 
DECLARE
    audit_count INTEGER;
    metadata_count INTEGER;
    schedule_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO audit_count FROM information_schema.tables WHERE table_name = 'corpus_audit_log';
    SELECT COUNT(*) INTO metadata_count FROM information_schema.tables WHERE table_name = 'corpus_metadata';
    SELECT COUNT(*) INTO schedule_count FROM information_schema.tables WHERE table_name = 'corpus_sync_schedule';
    
    RAISE NOTICE 'Admin tables created:';
    RAISE NOTICE '  corpus_audit_log: %', CASE WHEN audit_count > 0 THEN 'YES ✓' ELSE 'NO ✗' END;
    RAISE NOTICE '  corpus_metadata: %', CASE WHEN metadata_count > 0 THEN 'YES ✓' ELSE 'NO ✗' END;
    RAISE NOTICE '  corpus_sync_schedule: %', CASE WHEN schedule_count > 0 THEN 'YES ✓' ELSE 'NO ✗' END;
END $$;

-- Migration complete
