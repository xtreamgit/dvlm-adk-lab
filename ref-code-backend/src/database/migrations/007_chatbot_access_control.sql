-- Migration: 007_chatbot_access_control.sql
-- Description: Creates separate tables for chatbot user access control
-- This separates chatbot users (who interact with the chatbot) from
-- app managers (who administer the application)

-- ============================================================================
-- CHATBOT USERS TABLE
-- Users who can interact with the chatbot (separate from app managers)
-- ============================================================================
CREATE TABLE IF NOT EXISTS chatbot_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    created_by INTEGER REFERENCES users(id),  -- App manager who created this chatbot user
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_chatbot_users_username ON chatbot_users(username);
CREATE INDEX IF NOT EXISTS idx_chatbot_users_email ON chatbot_users(email);
CREATE INDEX IF NOT EXISTS idx_chatbot_users_is_active ON chatbot_users(is_active);

-- ============================================================================
-- CHATBOT GROUPS TABLE
-- Groups for organizing chatbot users and granting access
-- ============================================================================
CREATE TABLE IF NOT EXISTS chatbot_groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_chatbot_groups_name ON chatbot_groups(name);
CREATE INDEX IF NOT EXISTS idx_chatbot_groups_is_active ON chatbot_groups(is_active);

-- ============================================================================
-- CHATBOT ROLES TABLE
-- Roles define sets of permissions for chatbot users
-- ============================================================================
CREATE TABLE IF NOT EXISTS chatbot_roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_chatbot_roles_name ON chatbot_roles(name);

-- ============================================================================
-- CHATBOT PERMISSIONS TABLE
-- Granular permissions that can be assigned to roles
-- ============================================================================
CREATE TABLE IF NOT EXISTS chatbot_permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,  -- 'corpora', 'agents', 'tools', 'general'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chatbot_permissions_category ON chatbot_permissions(category);

-- ============================================================================
-- CHATBOT ROLE PERMISSIONS (Many-to-Many)
-- Links roles to their permissions
-- ============================================================================
CREATE TABLE IF NOT EXISTS chatbot_role_permissions (
    id SERIAL PRIMARY KEY,
    role_id INTEGER NOT NULL REFERENCES chatbot_roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES chatbot_permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(role_id, permission_id)
);

CREATE INDEX IF NOT EXISTS idx_chatbot_role_permissions_role ON chatbot_role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_chatbot_role_permissions_permission ON chatbot_role_permissions(permission_id);

-- ============================================================================
-- CHATBOT USER GROUPS (Many-to-Many)
-- Links chatbot users to their groups
-- ============================================================================
CREATE TABLE IF NOT EXISTS chatbot_user_groups (
    id SERIAL PRIMARY KEY,
    chatbot_user_id INTEGER NOT NULL REFERENCES chatbot_users(id) ON DELETE CASCADE,
    chatbot_group_id INTEGER NOT NULL REFERENCES chatbot_groups(id) ON DELETE CASCADE,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chatbot_user_id, chatbot_group_id)
);

CREATE INDEX IF NOT EXISTS idx_chatbot_user_groups_user ON chatbot_user_groups(chatbot_user_id);
CREATE INDEX IF NOT EXISTS idx_chatbot_user_groups_group ON chatbot_user_groups(chatbot_group_id);

-- ============================================================================
-- CHATBOT GROUP ROLES (Many-to-Many)
-- Links groups to their roles
-- ============================================================================
CREATE TABLE IF NOT EXISTS chatbot_group_roles (
    id SERIAL PRIMARY KEY,
    chatbot_group_id INTEGER NOT NULL REFERENCES chatbot_groups(id) ON DELETE CASCADE,
    chatbot_role_id INTEGER NOT NULL REFERENCES chatbot_roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chatbot_group_id, chatbot_role_id)
);

CREATE INDEX IF NOT EXISTS idx_chatbot_group_roles_group ON chatbot_group_roles(chatbot_group_id);
CREATE INDEX IF NOT EXISTS idx_chatbot_group_roles_role ON chatbot_group_roles(chatbot_role_id);

-- ============================================================================
-- CHATBOT CORPUS ACCESS
-- Granular corpus access for chatbot groups
-- ============================================================================
CREATE TABLE IF NOT EXISTS chatbot_corpus_access (
    id SERIAL PRIMARY KEY,
    chatbot_group_id INTEGER NOT NULL REFERENCES chatbot_groups(id) ON DELETE CASCADE,
    corpus_id INTEGER NOT NULL REFERENCES corpora(id) ON DELETE CASCADE,
    permission VARCHAR(50) NOT NULL DEFAULT 'query',  -- 'query', 'read', 'upload', 'delete', 'admin'
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by INTEGER REFERENCES users(id),
    UNIQUE(chatbot_group_id, corpus_id)
);

CREATE INDEX IF NOT EXISTS idx_chatbot_corpus_access_group ON chatbot_corpus_access(chatbot_group_id);
CREATE INDEX IF NOT EXISTS idx_chatbot_corpus_access_corpus ON chatbot_corpus_access(corpus_id);

-- ============================================================================
-- CHATBOT AGENT ACCESS
-- Granular agent access for chatbot groups
-- ============================================================================
CREATE TABLE IF NOT EXISTS chatbot_agent_access (
    id SERIAL PRIMARY KEY,
    chatbot_group_id INTEGER NOT NULL REFERENCES chatbot_groups(id) ON DELETE CASCADE,
    agent_id INTEGER NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    can_use BOOLEAN DEFAULT TRUE,
    can_configure BOOLEAN DEFAULT FALSE,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by INTEGER REFERENCES users(id),
    UNIQUE(chatbot_group_id, agent_id)
);

CREATE INDEX IF NOT EXISTS idx_chatbot_agent_access_group ON chatbot_agent_access(chatbot_group_id);
CREATE INDEX IF NOT EXISTS idx_chatbot_agent_access_agent ON chatbot_agent_access(agent_id);

-- ============================================================================
-- CHATBOT TOOL ACCESS
-- Granular tool access for chatbot groups (tools within agents)
-- ============================================================================
CREATE TABLE IF NOT EXISTS chatbot_tool_access (
    id SERIAL PRIMARY KEY,
    chatbot_group_id INTEGER NOT NULL REFERENCES chatbot_groups(id) ON DELETE CASCADE,
    tool_name VARCHAR(255) NOT NULL,  -- Tool identifier (e.g., 'rag_query', 'document_upload')
    agent_id INTEGER REFERENCES agents(id) ON DELETE CASCADE,  -- Optional: tool specific to an agent
    is_allowed BOOLEAN DEFAULT TRUE,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by INTEGER REFERENCES users(id),
    UNIQUE(chatbot_group_id, tool_name, agent_id)
);

CREATE INDEX IF NOT EXISTS idx_chatbot_tool_access_group ON chatbot_tool_access(chatbot_group_id);
CREATE INDEX IF NOT EXISTS idx_chatbot_tool_access_tool ON chatbot_tool_access(tool_name);

-- ============================================================================
-- INSERT DEFAULT PERMISSIONS
-- ============================================================================
INSERT INTO chatbot_permissions (name, description, category) VALUES
    -- Corpora permissions
    ('corpora:query', 'Can query corpora for information', 'corpora'),
    ('corpora:read', 'Can read/view corpus documents', 'corpora'),
    ('corpora:upload', 'Can upload documents to corpora', 'corpora'),
    ('corpora:delete', 'Can delete documents from corpora', 'corpora'),
    ('corpora:admin', 'Full admin access to corpora', 'corpora'),
    -- Agent permissions
    ('agents:use', 'Can use/interact with agents', 'agents'),
    ('agents:configure', 'Can configure agent settings', 'agents'),
    ('agents:create', 'Can create new agents', 'agents'),
    -- Tool permissions
    ('tools:rag_query', 'Can use RAG query tool', 'tools'),
    ('tools:document_search', 'Can use document search tool', 'tools'),
    ('tools:document_upload', 'Can use document upload tool', 'tools'),
    ('tools:document_delete', 'Can use document delete tool', 'tools'),
    ('tools:web_search', 'Can use web search tool', 'tools'),
    ('tools:code_execution', 'Can use code execution tool', 'tools'),
    -- General permissions
    ('general:chat', 'Can use the chatbot', 'general'),
    ('general:history', 'Can view chat history', 'general'),
    ('general:export', 'Can export chat conversations', 'general')
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- INSERT DEFAULT ROLES
-- ============================================================================
INSERT INTO chatbot_roles (name, description) VALUES
    ('chatbot-viewer', 'Can only query and read from assigned corpora'),
    ('chatbot-contributor', 'Can query, read, and upload to assigned corpora'),
    ('chatbot-power-user', 'Full access to assigned corpora and agents'),
    ('chatbot-admin', 'Administrative access to all chatbot features')
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- ASSIGN PERMISSIONS TO DEFAULT ROLES
-- ============================================================================

-- chatbot-viewer role
INSERT INTO chatbot_role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM chatbot_roles r, chatbot_permissions p
WHERE r.name = 'chatbot-viewer' AND p.name IN (
    'corpora:query', 'corpora:read', 'agents:use', 'tools:rag_query', 
    'tools:document_search', 'general:chat', 'general:history'
)
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- chatbot-contributor role
INSERT INTO chatbot_role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM chatbot_roles r, chatbot_permissions p
WHERE r.name = 'chatbot-contributor' AND p.name IN (
    'corpora:query', 'corpora:read', 'corpora:upload', 'agents:use',
    'tools:rag_query', 'tools:document_search', 'tools:document_upload',
    'general:chat', 'general:history', 'general:export'
)
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- chatbot-power-user role
INSERT INTO chatbot_role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM chatbot_roles r, chatbot_permissions p
WHERE r.name = 'chatbot-power-user' AND p.name IN (
    'corpora:query', 'corpora:read', 'corpora:upload', 'corpora:delete',
    'agents:use', 'agents:configure', 'tools:rag_query', 'tools:document_search',
    'tools:document_upload', 'tools:document_delete', 'tools:web_search',
    'general:chat', 'general:history', 'general:export'
)
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- chatbot-admin role (all permissions)
INSERT INTO chatbot_role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM chatbot_roles r, chatbot_permissions p
WHERE r.name = 'chatbot-admin'
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- ============================================================================
-- INSERT DEFAULT GROUP
-- ============================================================================
INSERT INTO chatbot_groups (name, description) VALUES
    ('default-chatbot-users', 'Default group for all chatbot users')
ON CONFLICT (name) DO NOTHING;

-- Assign chatbot-viewer role to default group
INSERT INTO chatbot_group_roles (chatbot_group_id, chatbot_role_id)
SELECT g.id, r.id FROM chatbot_groups g, chatbot_roles r
WHERE g.name = 'default-chatbot-users' AND r.name = 'chatbot-viewer'
ON CONFLICT (chatbot_group_id, chatbot_role_id) DO NOTHING;
