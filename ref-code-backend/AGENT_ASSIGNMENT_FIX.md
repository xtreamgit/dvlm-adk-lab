# Agent Assignment Fix - February 11, 2026

## Problem Identified

Users (including Hector) were experiencing **agent1 (read-only)** behavior despite the database showing they had **admin** agent type assigned. Users could not create corpora or access admin tools.

## Root Cause

The application has **two separate agent assignment systems** that were not connected:

### System 1: Chatbot Agent Types (NOT being used by code)
- Tables: `chatbot_users` → `chatbot_user_groups` → `chatbot_group_agent_types` → `chatbot_agent_types`
- Status: Properly configured, showed users with correct agent types
- **Problem:** The application code doesn't use this system!

### System 2: Actual Agent System (Used by code)
- Tables: `users` → `user_agent_access` → `agents`
- Status: **Incomplete!** Only had 1 agent (`default_agent`), no user assignments
- **Problem:** This is what the code actually uses, but it wasn't configured!

## Code Flow (How Agent Assignment Actually Works)

```python
# From server.py:705
agent_manager.get_agent_for_user(current_user.id)
    ↓
# From agent_manager.py:82-94
user = UserRepository.get_by_id(user_id)
default_agent_id = user.get('default_agent_id')  # Was NULL for everyone!
    ↓
# From agent_manager.py:108-110
config_path = agent_data['config_path']  # Determines which .json to load
agent = self.get_agent_by_config_path(config_path)
```

**The issue:** `users.default_agent_id` was NULL for everyone, so no agent was being assigned!

## Solution Applied

Created SQL script (`fix_agent_assignments.sql`) that:

### 1. Created Missing Agent Records
```sql
INSERT INTO agents (name, display_name, config_path, ...)
VALUES 
  ('agent1', 'Research Assistant Agent', 'agent1', ...),
  ('agent2', 'Content Curator Agent', 'agent2', ...),
  ('agent3', 'Administrator Agent', 'agent3', ...);
```

### 2. Mapped Chatbot Agent Types to Actual Agents
- `viewer` → `agent1` (3 tools: rag_query, list_corpora, get_corpus_info)
- `contributor` → `agent2` (5 tools: + create_corpus, add_data)
- `content-manager` → `agent2` (5 tools)
- `admin` → `agent3` (7 tools: + delete_document, delete_corpus)

### 3. Granted User Access
```sql
INSERT INTO user_agent_access (user_id, agent_id)
SELECT u.id, agent3.id
FROM users u
JOIN chatbot_users cu ON u.username = cu.username
JOIN ... (chatbot_agent_types system)
WHERE cat.name = 'admin';
```

### 4. Set Default Agents
```sql
UPDATE users u
SET default_agent_id = (SELECT id FROM agents WHERE name = 'agent3')
WHERE u.id IN (SELECT ... users with admin agent type);
```

## Results

### Before Fix
| Username | Default Agent | Config Path | Tools Available |
|----------|---------------|-------------|-----------------|
| hector | NULL | N/A | None (fallback to agent1) |
| alice | NULL | N/A | None (fallback to agent1) |
| All others | NULL | N/A | None |

### After Fix
| Username | Default Agent | Config Path | Tools Available |
|----------|---------------|-------------|-----------------|
| **hector** | **agent3** | **agent3** | **7 tools (admin)** ✅ |
| **alice** | **agent3** | **agent3** | **7 tools (admin)** ✅ |
| Others | NULL | N/A | No agent assigned |

## Agent Capabilities by Type

### Agent1 (Research Assistant) - 3 Tools
- `rag_query` - Query documents
- `list_corpora` - List available corpora
- `get_corpus_info` - Get corpus details
- **Cannot:** Create, upload, or delete

### Agent2 (Content Curator) - 5 Tools
- All agent1 tools, plus:
- `create_corpus` - Create new corpora
- `add_data` - Upload documents
- **Cannot:** Delete documents or corpora

### Agent3 (Administrator) - 7 Tools
- All agent2 tools, plus:
- `delete_document` - Delete specific documents
- `delete_corpus` - Delete entire corpora
- **Full access** to all corpus management

## Verification

Run this query to verify current assignments:
```sql
SELECT 
    u.username,
    a.name as agent,
    a.config_path,
    CASE a.name
        WHEN 'agent1' THEN '3 tools (read-only)'
        WHEN 'agent2' THEN '5 tools (create/manage)'
        WHEN 'agent3' THEN '7 tools (admin)'
        ELSE 'unknown'
    END as capabilities
FROM users u
LEFT JOIN agents a ON u.default_agent_id = a.id
WHERE u.is_active = true;
```

## Next Steps

1. **Restart backend service** to ensure new agent assignments are loaded
2. **Test with Hector's account** - should now be able to create corpora
3. **Assign remaining users** to appropriate agents based on their roles
4. **Consider consolidating** the two agent systems in the future

## Files Modified

- Created: `backend/fix_agent_assignments.sql`
- Modified: Database tables `agents`, `user_agent_access`, `users`

## Impact

- **Hector** now has full admin capabilities (agent3)
- **Alice** now has full admin capabilities (agent3)
- Other users need to be assigned to agents based on their chatbot_agent_types
- System now correctly uses the agent configuration files (agent1.json, agent2.json, agent3.json)
