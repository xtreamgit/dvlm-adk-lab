-- Update agent display names to new naming convention
UPDATE agents SET 
  display_name = 'Admin Agent',
  description = 'Full administrative agent with all capabilities including multi-corpus queries, document retrieval, and complete corpus lifecycle management'
WHERE name = 'default_agent';

UPDATE agents SET 
  display_name = 'Viewer Agent',
  description = 'Read-only viewer agent with query and information retrieval capabilities'
WHERE name = 'agent1';

UPDATE agents SET 
  display_name = 'Contributor Agent',
  description = 'Contributor agent with creation and query capabilities but no deletion rights'
WHERE name = 'agent2';

UPDATE agents SET 
  display_name = 'Content Manager Agent',
  description = 'Content manager agent with corpus management capabilities including deletion rights'
WHERE name = 'agent3';

-- Grant hector and alice access to Admin Agent (default_agent, id=1)
INSERT INTO user_agent_access (user_id, agent_id, granted_at)
SELECT u.id, a.id, CURRENT_TIMESTAMP
FROM users u, agents a 
WHERE u.username IN ('hector', 'alice') AND a.name = 'default_agent'
ON CONFLICT (user_id, agent_id) DO NOTHING;

-- Set hector and alice default to Admin Agent
UPDATE users SET default_agent_id = (SELECT id FROM agents WHERE name = 'default_agent')
WHERE username IN ('hector', 'alice');

-- Verify results
SELECT id, name, display_name FROM agents ORDER BY id;
SELECT u.username, u.default_agent_id, a.display_name 
FROM users u LEFT JOIN agents a ON u.default_agent_id = a.id 
WHERE u.is_active = true ORDER BY u.username;
