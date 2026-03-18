-- Check Admin Permissions for Users
-- This script checks which users have admin access

-- 1. Show all users and their roles
\echo '=== ALL USERS AND THEIR ROLES ==='
SELECT 
    u.id,
    u.username,
    u.email,
    u.is_active,
    COALESCE(string_agg(DISTINCT r.name, ', '), 'No roles') as roles,
    COALESCE(string_agg(DISTINCT g.name, ', '), 'No groups') as groups
FROM users u
LEFT JOIN user_groups ug ON u.id = ug.user_id
LEFT JOIN groups g ON ug.group_id = g.id
LEFT JOIN group_roles gr ON g.id = gr.group_id
LEFT JOIN roles r ON gr.role_id = r.id
GROUP BY u.id, u.username, u.email, u.is_active
ORDER BY u.username;

-- 2. Show available roles
\echo ''
\echo '=== AVAILABLE ROLES ==='
SELECT id, name, description FROM roles ORDER BY name;

-- 3. Show available groups
\echo ''
\echo '=== AVAILABLE GROUPS ==='
SELECT id, name, description FROM groups ORDER BY name;

-- 4. Check if admin role and admins group exist
\echo ''
\echo '=== ADMIN INFRASTRUCTURE CHECK ==='
SELECT 
    'admin role' as item,
    CASE WHEN EXISTS (SELECT 1 FROM roles WHERE name = 'admin') THEN 'EXISTS' ELSE 'MISSING' END as status
UNION ALL
SELECT 
    'admins group' as item,
    CASE WHEN EXISTS (SELECT 1 FROM groups WHERE name = 'admins') THEN 'EXISTS' ELSE 'MISSING' END as status;

-- 5. Show who has admin access (if admin role exists)
\echo ''
\echo '=== USERS WITH ADMIN ROLE ==='
SELECT 
    u.username,
    u.email,
    g.name as admin_group
FROM users u
JOIN user_groups ug ON u.id = ug.user_id
JOIN groups g ON ug.group_id = g.id
JOIN group_roles gr ON g.id = gr.group_id
JOIN roles r ON gr.role_id = r.id
WHERE r.name = 'admin'
ORDER BY u.username;
