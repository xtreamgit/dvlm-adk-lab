-- Migration: 012_google_group_mappings.sql
-- Description: Creates tables for Google Groups Bridge
-- Maps Google Groups to chatbot agent types and corpus access

-- ============================================================================
-- GOOGLE GROUP → AGENT TYPE MAPPINGS
-- Maps a Google Group email to a chatbot agent type (viewer, contributor, etc.)
-- ============================================================================
CREATE TABLE IF NOT EXISTS google_group_agent_mappings (
    id SERIAL PRIMARY KEY,
    google_group_email VARCHAR(255) NOT NULL,
    chatbot_group_id INTEGER NOT NULL REFERENCES chatbot_groups(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    UNIQUE(google_group_email)
);

CREATE INDEX IF NOT EXISTS idx_gg_agent_map_email ON google_group_agent_mappings(google_group_email);
CREATE INDEX IF NOT EXISTS idx_gg_agent_map_active ON google_group_agent_mappings(is_active);

-- ============================================================================
-- GOOGLE GROUP → CORPUS ACCESS MAPPINGS
-- Maps a Google Group email to corpus access with permission level
-- ============================================================================
CREATE TABLE IF NOT EXISTS google_group_corpus_mappings (
    id SERIAL PRIMARY KEY,
    google_group_email VARCHAR(255) NOT NULL,
    corpus_id INTEGER NOT NULL REFERENCES corpora(id) ON DELETE CASCADE,
    permission VARCHAR(50) NOT NULL DEFAULT 'query',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    UNIQUE(google_group_email, corpus_id)
);

CREATE INDEX IF NOT EXISTS idx_gg_corpus_map_email ON google_group_corpus_mappings(google_group_email);
CREATE INDEX IF NOT EXISTS idx_gg_corpus_map_corpus ON google_group_corpus_mappings(corpus_id);
CREATE INDEX IF NOT EXISTS idx_gg_corpus_map_active ON google_group_corpus_mappings(is_active);

-- ============================================================================
-- USER GOOGLE GROUP SYNC CACHE
-- Tracks last sync state per user to avoid redundant API calls
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_google_group_sync (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    google_groups JSONB,
    last_synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_source VARCHAR(50) DEFAULT 'login',
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_gg_sync_user ON user_google_group_sync(user_id);
CREATE INDEX IF NOT EXISTS idx_gg_sync_time ON user_google_group_sync(last_synced_at);
