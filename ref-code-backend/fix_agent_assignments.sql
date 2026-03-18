-- Fix Agent Assignments
-- This script creates proper agent records and assigns users to the correct agents
-- based on their chatbot_agent_types assignments

-- ============================================================================
-- STEP 1: Create agent records for agent1, agent2, agent3
-- ============================================================================

-- Insert agent1 (Research Assistant - Read-only, 3 tools)
INSERT INTO agents (name, display_name, description, config_path, is_active, created_at, updated_at)
VALUES (
    'agent1',
    'Research Assistant Agent',
    'Read-only research agent with query and information retrieval capabilities',
    'agent1',
    true,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
)
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    config_path = EXCLUDED.config_path,
    updated_at = CURRENT_TIMESTAMP;

-- Insert agent2 (Content Curator - Create & Manage, 5 tools)
INSERT INTO agents (name, display_name, description, config_path, is_active, created_at, updated_at)
VALUES (
    'agent2',
    'Content Curator Agent',
    'Content management agent with create and upload capabilities',
    'agent2',
    true,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
)
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    config_path = EXCLUDED.config_path,
    updated_at = CURRENT_TIMESTAMP;

-- Insert agent3 (Administrator - Full access, 7 tools)
INSERT INTO agents (name, display_name, description, config_path, is_active, created_at, updated_at)
VALUES (
    'agent3',
    'Administrator Agent',
    'Full administrative agent with complete corpus management capabilities including deletion rights',
    'agent3',
    true,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
)
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    config_path = EXCLUDED.config_path,
    updated_at = CURRENT_TIMESTAMP;

-- Update default_agent to use develom config
UPDATE agents 
SET config_path = 'develom',
    display_name = 'Default RAG Agent',
    description = 'Default general-purpose RAG agent with full corpus management capabilities'
WHERE name = 'default_agent';

-- ============================================================================
-- STEP 2: Map chatbot_agent_types to actual agents
-- ============================================================================

-- Create a mapping based on agent type:
-- viewer -> agent1 (3 tools)
-- contributor -> agent2 (5 tools)
-- content-manager -> agent2 (5 tools)
-- admin -> agent3 (7 tools)

-- ============================================================================
-- STEP 3: Grant access to users based on their chatbot_agent_type
-- ============================================================================

-- Grant access to users with 'admin' agent type -> agent3
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

-- Grant access to users with 'content-manager' agent type -> agent2
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
WHERE cat.name = 'content-manager'
  AND u.is_active = true
  AND cu.is_active = true
ON CONFLICT (user_id, agent_id) DO NOTHING;

-- Grant access to users with 'contributor' agent type -> agent2
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
WHERE cat.name = 'contributor'
  AND u.is_active = true
  AND cu.is_active = true
ON CONFLICT (user_id, agent_id) DO NOTHING;

-- Grant access to users with 'viewer' agent type -> agent1
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

-- ============================================================================
-- STEP 4: Set default_agent_id for users based on highest priority agent type
-- ============================================================================

-- Set default agent for users with admin access (highest priority)
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

-- Set default agent for users with content-manager access (if not already set)
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
    WHERE cat.name = 'content-manager'
      AND u2.is_active = true
      AND cu.is_active = true
);

-- Set default agent for users with contributor access (if not already set)
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
    WHERE cat.name = 'contributor'
      AND u2.is_active = true
      AND cu.is_active = true
);

-- Set default agent for users with viewer access (if not already set)
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

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Show all agents
SELECT id, name, display_name, config_path, is_active FROM agents ORDER BY id;

-- Show user-agent assignments
SELECT 
    u.username,
    u.email,
    a.name as agent_name,
    a.display_name,
    a.config_path,
    CASE a.name
        WHEN 'agent1' THEN '3 tools (read-only)'
        WHEN 'agent2' THEN '5 tools (create/manage)'
        WHEN 'agent3' THEN '7 tools (admin)'
        WHEN 'default_agent' THEN '9 tools (full)'
        ELSE 'unknown'
    END as capabilities
FROM users u
LEFT JOIN agents a ON u.default_agent_id = a.id
WHERE u.is_active = true
ORDER BY a.name DESC, u.username;

-- Show detailed access
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
