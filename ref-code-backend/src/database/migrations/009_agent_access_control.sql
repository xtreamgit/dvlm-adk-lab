-- Migration 009: Agent Access Control System
-- Creates tables for managing agents with specific tool permissions and group assignments

-- Create chatbot_agents table to define agent types with tool configurations
CREATE TABLE IF NOT EXISTS chatbot_agents (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    agent_type VARCHAR(100) NOT NULL, -- 'viewer', 'contributor', 'content-manager', 'admin'
    tools JSONB NOT NULL, -- Array of tool names: ["rag_query", "list_corpora", ...]
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create chatbot_group_agents table to map groups to agents
CREATE TABLE IF NOT EXISTS chatbot_group_agents (
    id SERIAL PRIMARY KEY,
    group_id INTEGER REFERENCES chatbot_groups(id) ON DELETE CASCADE,
    agent_id INTEGER REFERENCES chatbot_agents(id) ON DELETE CASCADE,
    can_use BOOLEAN DEFAULT TRUE,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by INTEGER REFERENCES users(id),
    UNIQUE(group_id, agent_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_chatbot_agents_type ON chatbot_agents(agent_type);
CREATE INDEX IF NOT EXISTS idx_chatbot_agents_active ON chatbot_agents(is_active);
CREATE INDEX IF NOT EXISTS idx_chatbot_group_agents_group ON chatbot_group_agents(group_id);
CREATE INDEX IF NOT EXISTS idx_chatbot_group_agents_agent ON chatbot_group_agents(agent_id);

-- Insert the 4 agent types with their tool configurations
INSERT INTO chatbot_agents (name, display_name, description, agent_type, tools) VALUES
(
    'viewer-agent',
    'Viewer Agent',
    'Read-only access for general users. Can query documents and browse corpora but cannot modify any data.',
    'viewer',
    '["rag_query", "list_corpora", "get_corpus_info", "browse_documents"]'::jsonb
),
(
    'contributor-agent',
    'Contributor Agent',
    'Users who can add content. Has all viewer capabilities plus the ability to add documents to corpora.',
    'contributor',
    '["rag_query", "list_corpora", "get_corpus_info", "browse_documents", "add_data"]'::jsonb
),
(
    'content-manager-agent',
    'Content Manager Agent',
    'Manage documents within existing corpora. Can add and delete documents but cannot create or delete corpora.',
    'content-manager',
    '["rag_query", "list_corpora", "get_corpus_info", "browse_documents", "add_data", "delete_document"]'::jsonb
),
(
    'admin-agent',
    'Admin Agent',
    'Full corpus lifecycle management. Complete control over corpora and documents. For administrators only.',
    'admin',
    '["rag_query", "list_corpora", "get_corpus_info", "browse_documents", "add_data", "create_corpus", "delete_document", "delete_corpus"]'::jsonb
)
ON CONFLICT (name) DO NOTHING;

-- Create the 4 role-based groups
INSERT INTO chatbot_groups (name, description) VALUES
('viewer-group', 'Read-only access group with Viewer Agent capabilities'),
('contributor-group', 'Content contributor group with ability to add documents'),
('content-manager-group', 'Content management group with document lifecycle control'),
('admin-group', 'Administrative group with full corpus and document control')
ON CONFLICT (name) DO NOTHING;

-- Assign agents to their corresponding groups
-- This creates the group-to-agent mappings
INSERT INTO chatbot_group_agents (group_id, agent_id, can_use, granted_by)
SELECT 
    g.id,
    a.id,
    TRUE,
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1) -- Granted by admin user
FROM chatbot_groups g
JOIN chatbot_agents a ON (
    (g.name = 'viewer-group' AND a.name = 'viewer-agent') OR
    (g.name = 'contributor-group' AND a.name = 'contributor-agent') OR
    (g.name = 'content-manager-group' AND a.name = 'content-manager-agent') OR
    (g.name = 'admin-group' AND a.name = 'admin-agent')
)
ON CONFLICT (group_id, agent_id) DO NOTHING;

-- Add comment to document the migration
COMMENT ON TABLE chatbot_agents IS 'Defines agent types with specific tool permissions for RAG operations';
COMMENT ON TABLE chatbot_group_agents IS 'Maps chatbot groups to agents, controlling which agents users can access based on group membership';
COMMENT ON COLUMN chatbot_agents.tools IS 'JSONB array of tool names that this agent is allowed to use';
COMMENT ON COLUMN chatbot_agents.agent_type IS 'Agent type: viewer, contributor, content-manager, or admin';
