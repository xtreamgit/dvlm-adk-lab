-- Migration 003: Agents and Corpora Access Control
-- Description: Add agents, corpora, and access control tables
-- Date: 2025-12-31
-- Updated: 2026-01-28 - Converted to PostgreSQL syntax

-- Agents (available agents in system)
CREATE TABLE IF NOT EXISTS agents (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    config_path VARCHAR(255) NOT NULL,  -- e.g., 'agent1', 'develom'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User-Agent Access (which users can access which agents)
CREATE TABLE IF NOT EXISTS user_agent_access (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    agent_id INTEGER NOT NULL,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, agent_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

-- Corpora (RAG corpus definitions)
CREATE TABLE IF NOT EXISTS corpora (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    gcs_bucket VARCHAR(500) NOT NULL,
    vertex_corpus_id VARCHAR(500),  -- Vertex AI corpus ID
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Group-Corpus Access (which groups can access which corpora)
CREATE TABLE IF NOT EXISTS group_corpus_access (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL,
    corpus_id INTEGER NOT NULL,
    permission VARCHAR(50) DEFAULT 'read',  -- read, write, admin
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(group_id, corpus_id),
    FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
    FOREIGN KEY (corpus_id) REFERENCES corpora(id) ON DELETE CASCADE
);

-- User Sessions (enhanced for agent & corpus tracking)
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    active_agent_id INTEGER,
    active_corpora JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (active_agent_id) REFERENCES agents(id)
);

-- Session Corpus Selections (for restoration)
CREATE TABLE IF NOT EXISTS session_corpus_selections (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    corpus_id INTEGER NOT NULL,
    last_selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, corpus_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (corpus_id) REFERENCES corpora(id) ON DELETE CASCADE
);

-- Add foreign key for users.default_agent_id (if not exists)
-- Note: This constraint is already defined in the users table creation

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_agents_name ON agents(name);
CREATE INDEX IF NOT EXISTS idx_agents_active ON agents(is_active);
CREATE INDEX IF NOT EXISTS idx_user_agent_access_user ON user_agent_access(user_id);
CREATE INDEX IF NOT EXISTS idx_user_agent_access_agent ON user_agent_access(agent_id);
CREATE INDEX IF NOT EXISTS idx_corpora_name ON corpora(name);
CREATE INDEX IF NOT EXISTS idx_corpora_active ON corpora(is_active);
CREATE INDEX IF NOT EXISTS idx_group_corpus_access_group ON group_corpus_access(group_id);
CREATE INDEX IF NOT EXISTS idx_group_corpus_access_corpus ON group_corpus_access(corpus_id);
CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON user_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_active ON user_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_session_corpus_user ON session_corpus_selections(user_id);
CREATE INDEX IF NOT EXISTS idx_session_corpus_corpus ON session_corpus_selections(corpus_id);
