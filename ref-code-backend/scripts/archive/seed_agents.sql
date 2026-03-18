-- Seed agents into Cloud SQL PostgreSQL
-- Insert agents if they don't exist

INSERT INTO agents (name, display_name, description, config_path, is_active, created_at)
VALUES 
    ('default-agent', 'Default Agent', 'Default general-purpose RAG agent', 'develom', true, NOW())
ON CONFLICT (name) DO NOTHING;

INSERT INTO agents (name, display_name, description, config_path, is_active, created_at)
VALUES 
    ('agent1', 'Agent 1', 'Specialized agent 1', 'agent1', true, NOW())
ON CONFLICT (name) DO NOTHING;

INSERT INTO agents (name, display_name, description, config_path, is_active, created_at)
VALUES 
    ('agent2', 'Agent 2', 'Specialized agent 2', 'agent2', true, NOW())
ON CONFLICT (name) DO NOTHING;

INSERT INTO agents (name, display_name, description, config_path, is_active, created_at)
VALUES 
    ('agent3', 'Agent 3', 'Specialized agent 3', 'agent3', true, NOW())
ON CONFLICT (name) DO NOTHING;

-- Display results
SELECT id, name, display_name, is_active FROM agents ORDER BY id;
