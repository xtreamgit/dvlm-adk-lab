-- Fix Agent Assignments for Cloud SQL (Production)
-- Schema differs from local: no updated_at column on agents table

-- STEP 1: Create agent records for agent1, agent2, agent3
INSERT INTO agents (name, display_name, description, config_path, is_active, created_at)
VALUES (
    'agent1',
    'Research Assistant Agent',
    'Read-only research agent with query and information retrieval capabilities',
    'agent1',
    true,
    CURRENT_TIMESTAMP
)
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    config_path = EXCLUDED.config_path;

INSERT INTO agents (name, display_name, description, config_path, is_active, created_at)
VALUES (
    'agent2',
    'Content Curator Agent',
    'Content management agent with create and upload capabilities',
    'agent2',
    true,
    CURRENT_TIMESTAMP
)
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    config_path = EXCLUDED.config_path;

INSERT INTO agents (name, display_name, description, config_path, is_active, created_at)
VALUES (
    'agent3',
    'Administrator Agent',
    'Full administrative agent with complete corpus management capabilities including deletion rights',
    'agent3',
    true,
    CURRENT_TIMESTAMP
)
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    config_path = EXCLUDED.config_path;

-- Update default_agent to use develom config
UPDATE agents 
SET config_path = 'develom',
    display_name = 'Default RAG Agent',
    description = 'Default general-purpose RAG agent with full corpus management capabilities'
WHERE name = 'default_agent';

-- Verify agents exist
SELECT id, name, display_name, config_path FROM agents ORDER BY id;

-- STEP 2: Grant access to admin users -> agent3
INSERT INTO user_agent_access (user_id, agent_id, granted_at)
SELECT DISTINCT 
    u.id as user_id,
    (SELECT id FROM agents WHERE name = 'agent3') as agent_id,
    CURRENT_TIMESTAMP
FROM users u
JOIN chatbot_users cu ON u.username = cu.username
JOIN chatbot_user_groups cug ON cu.id = cug.chatbot_user_id
JOIN chatbot_groups cg ON cug.chatbot_group_id = cg.id
JOIN chatbot_group_agent_types cgat ON cg.id = cgat.chatbot_group_id
JOIN chatbot_agent_types cat ON cgat.chatbot_agent_type_id = cat.id
WHERE cat.name = 'admin'
  AND u.is_active = true
  AND cu.is_active = true
ON CONFLICT (user_id, agent_id) DO NOTHING;

-- Grant access to content-manager users -> agent2
INSERT INTO user_agent_access (user_id, agent_id, granted_at)
SELECT DISTINCT 
    u.id as user_id,
    (SELECT id FROM agents WHERE name = 'agent2') as agent_id,
    CURRENT_TIMESTAMP
FROM users u
JOIN chatbot_users cu ON u.username = cu.username
JOIN chatbot_user_groups cug ON cu.id = cug.chatbot_user_id
JOIN chatbot_groups cg ON cug.chatbot_group_id = cg.id
JOIN chatbot_group_agent_types cgat ON cg.id = cgat.chatbot_group_id
JOIN chatbot_agent_types cat ON cgat.chatbot_agent_type_id = cat.id
WHERE cat.name IN ('content-manager', 'contributor')
  AND u.is_active = true
  AND cu.is_active = true
ON CONFLICT (user_id, agent_id) DO NOTHING;

-- Grant access to viewer users -> agent1
INSERT INTO user_agent_access (user_id, agent_id, granted_at)
SELECT DISTINCT 
    u.id as user_id,
    (SELECT id FROM agents WHERE name = 'agent1') as agent_id,
    CURRENT_TIMESTAMP
FROM users u
JOIN chatbot_users cu ON u.username = cu.username
JOIN chatbot_user_groups cug ON cu.id = cug.chatbot_user_id
JOIN chatbot_groups cg ON cug.chatbot_group_id = cg.id
JOIN chatbot_group_agent_types cgat ON cg.id = cgat.chatbot_group_id
JOIN chatbot_agent_types cat ON cgat.chatbot_agent_type_id = cat.id
WHERE cat.name = 'viewer'
  AND u.is_active = true
  AND cu.is_active = true
ON CONFLICT (user_id, agent_id) DO NOTHING;

-- STEP 3: Set default_agent_id for admin users -> agent3
UPDATE users u
SET default_agent_id = (SELECT id FROM agents WHERE name = 'agent3')
WHERE u.id IN (
    SELECT DISTINCT u2.id
    FROM users u2
    JOIN chatbot_users cu ON u2.username = cu.username
    JOIN chatbot_user_groups cug ON cu.id = cug.chatbot_user_id
    JOIN chatbot_groups cg ON cug.chatbot_group_id = cg.id
    JOIN chatbot_group_agent_types cgat ON cg.id = cgat.chatbot_group_id
    JOIN chatbot_agent_types cat ON cgat.chatbot_agent_type_id = cat.id
    WHERE cat.name = 'admin'
      AND u2.is_active = true
      AND cu.is_active = true
);

-- Set default for content-manager users -> agent2 (if not already set)
UPDATE users u
SET default_agent_id = (SELECT id FROM agents WHERE name = 'agent2')
WHERE u.default_agent_id IS NULL
  AND u.id IN (
    SELECT DISTINCT u2.id
    FROM users u2
    JOIN chatbot_users cu ON u2.username = cu.username
    JOIN chatbot_user_groups cug ON cu.id = cug.chatbot_user_id
    JOIN chatbot_groups cg ON cug.chatbot_group_id = cg.id
    JOIN chatbot_group_agent_types cgat ON cg.id = cgat.chatbot_group_id
    JOIN chatbot_agent_types cat ON cgat.chatbot_agent_type_id = cat.id
    WHERE cat.name IN ('content-manager', 'contributor')
      AND u2.is_active = true
      AND cu.is_active = true
);

-- Set default for viewer users -> agent1 (if not already set)
UPDATE users u
SET default_agent_id = (SELECT id FROM agents WHERE name = 'agent1')
WHERE u.default_agent_id IS NULL
  AND u.id IN (
    SELECT DISTINCT u2.id
    FROM users u2
    JOIN chatbot_users cu ON u2.username = cu.username
    JOIN chatbot_user_groups cug ON cu.id = cug.chatbot_user_id
    JOIN chatbot_groups cg ON cug.chatbot_group_id = cg.id
    JOIN chatbot_group_agent_types cgat ON cg.id = cgat.chatbot_group_id
    JOIN chatbot_agent_types cat ON cgat.chatbot_agent_type_id = cat.id
    WHERE cat.name = 'viewer'
      AND u2.is_active = true
      AND cu.is_active = true
);

-- VERIFICATION
SELECT id, name, display_name, config_path, is_active FROM agents ORDER BY id;

SELECT 
    u.username,
    u.email,
    a.name as agent_name,
    a.display_name,
    a.config_path
FROM users u
LEFT JOIN agents a ON u.default_agent_id = a.id
WHERE u.is_active = true
ORDER BY a.name DESC NULLS LAST, u.username;

SELECT 
    u.username,
    a.name as agent_name,
    a.config_path,
    uaa.granted_at
FROM user_agent_access uaa
JOIN users u ON uaa.user_id = u.id
JOIN agents a ON uaa.agent_id = a.id
WHERE u.is_active = true
ORDER BY u.username, a.name;
