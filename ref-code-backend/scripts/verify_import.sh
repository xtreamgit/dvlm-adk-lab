#!/bin/bash
# Verify data was imported successfully
echo "🔍 Verifying Data Import"
echo "========================"
echo ""

gcloud sql connect adk-multi-agents-db \
  --database=adk_agents_db \
  --user=adk_app_user \
  --project=adk-rag-ma \
  --quiet <<'EOF'
SELECT 'Users:' as table_name, COUNT(*) as row_count FROM users
UNION ALL
SELECT 'Groups:', COUNT(*) FROM groups
UNION ALL
SELECT 'Corpora:', COUNT(*) FROM corpora
UNION ALL
SELECT 'User Groups:', COUNT(*) FROM user_groups
UNION ALL
SELECT 'Group Corpus Access:', COUNT(*) FROM group_corpus_access
UNION ALL
SELECT 'User Sessions:', COUNT(*) FROM user_sessions
UNION ALL
SELECT 'Agents:', COUNT(*) FROM agents
UNION ALL
SELECT 'Roles:', COUNT(*) FROM roles;

\echo ''
\echo 'Sample Users:'
SELECT username, email FROM users ORDER BY id LIMIT 5;

\echo ''
\echo 'Sample Groups:'
SELECT name, description FROM groups ORDER BY id;

\echo ''
\echo 'Active Corpora:'
SELECT name, vertex_corpus_id FROM corpora WHERE is_active = TRUE ORDER BY name;
EOF
