#!/bin/bash

# Setup test data for agent type hierarchy testing
# Creates chatbot user, group, and agent type assignments for alice

CONTAINER_NAME="adk-postgres-dev"
DB_NAME="adk_agents_db_dev"
DB_USER="adk_dev_user"

echo "🔧 Setting up test data for agent type hierarchy..."
echo ""

# Execute SQL commands
docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME << 'EOF'

-- Step 1: Get alice's user ID
DO $$
DECLARE
    v_user_id INTEGER;
    v_chatbot_user_id INTEGER;
    v_group_id INTEGER;
    v_contributor_type_id INTEGER;
BEGIN
    -- Get alice's user ID from users table
    SELECT id INTO v_user_id FROM users WHERE username = 'alice';
    
    IF v_user_id IS NULL THEN
        RAISE NOTICE '❌ User alice not found in users table';
        RETURN;
    END IF;
    
    RAISE NOTICE '✅ Found user alice (id: %)', v_user_id;
    
    -- Step 2: Create or get chatbot user for alice
    INSERT INTO chatbot_users (username, email, full_name, is_active, created_by)
    VALUES ('alice', 'alice@example.com', 'Alice Test User', TRUE, v_user_id)
    ON CONFLICT (username) DO UPDATE SET is_active = TRUE
    RETURNING id INTO v_chatbot_user_id;
    
    RAISE NOTICE '✅ Chatbot user alice ready (id: %)', v_chatbot_user_id;
    
    -- Step 3: Create agent types if they don't exist
    RAISE NOTICE '';
    RAISE NOTICE '📋 Creating agent types...';
    
    INSERT INTO chatbot_agent_types (name, description, created_by)
    VALUES 
        ('viewer', 'Read-only access for general users', v_user_id),
        ('contributor', 'Users who can add content', v_user_id),
        ('content-manager', 'Manage documents within existing corpora', v_user_id),
        ('corpus-manager', 'Full corpus lifecycle management', v_user_id)
    ON CONFLICT (name) DO NOTHING;
    
    RAISE NOTICE '   ✅ Agent types created/verified';
    
    -- Step 4: Create chatbot group
    INSERT INTO chatbot_groups (name, description, is_active, created_by)
    VALUES ('Test Contributors', 'Test group for contributor agent type', TRUE, v_user_id)
    ON CONFLICT (name) DO UPDATE SET is_active = TRUE
    RETURNING id INTO v_group_id;
    
    RAISE NOTICE '';
    RAISE NOTICE '✅ Chatbot group ready: Test Contributors (id: %)', v_group_id;
    
    -- Step 5: Get contributor agent type ID
    SELECT id INTO v_contributor_type_id FROM chatbot_agent_types WHERE name = 'contributor';
    
    -- Step 6: Assign alice to the group
    INSERT INTO chatbot_user_groups (chatbot_user_id, chatbot_group_id)
    VALUES (v_chatbot_user_id, v_group_id)
    ON CONFLICT (chatbot_user_id, chatbot_group_id) DO NOTHING;
    
    RAISE NOTICE '✅ Assigned alice to group Test Contributors';
    
    -- Step 7: Assign contributor agent type to the group
    INSERT INTO chatbot_group_agent_types (chatbot_group_id, chatbot_agent_type_id)
    VALUES (v_group_id, v_contributor_type_id)
    ON CONFLICT (chatbot_group_id, chatbot_agent_type_id) DO NOTHING;
    
    RAISE NOTICE '✅ Assigned contributor agent type to group Test Contributors';
    
END $$;

-- Verify the setup
\echo ''
\echo '======================================================================'
\echo '🔍 Verifying setup...'
\echo '======================================================================'
\echo ''

SELECT 
    cu.username as "User",
    cg.name as "Group",
    cat.name as "Agent Type"
FROM chatbot_users cu
JOIN chatbot_user_groups cug ON cu.id = cug.chatbot_user_id
JOIN chatbot_groups cg ON cug.chatbot_group_id = cg.id
JOIN chatbot_group_agent_types cgat ON cg.id = cgat.chatbot_group_id
JOIN chatbot_agent_types cat ON cgat.chatbot_agent_type_id = cat.id
WHERE cu.username = 'alice';

\echo ''
\echo '======================================================================'
\echo '✅ Test data setup complete!'
\echo '======================================================================'
\echo ''
\echo '📦 Tools available to alice (contributor):'
\echo '   • rag_query'
\echo '   • list_corpora'
\echo '   • get_corpus_info'
\echo '   • browse_documents'
\echo '   • add_data'
\echo ''

EOF

echo "✅ Done!"
