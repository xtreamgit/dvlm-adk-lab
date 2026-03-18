-- Grant admin access to hector@develom.com (user ID 8)

-- Add hector to admin-users group
INSERT INTO user_groups (user_id, group_id)
SELECT 8, g.id FROM groups g
WHERE g.name = 'admin-users'
ON CONFLICT DO NOTHING;

-- Add hector to admins group
INSERT INTO user_groups (user_id, group_id)
SELECT 8, g.id FROM groups g
WHERE g.name = 'admins'
ON CONFLICT DO NOTHING;

-- Verify
\echo ''
\echo '=== Hector Admin Access ==='
SELECT 
    u.username,
    u.email,
    g.name as group_name,
    r.name as role_name
FROM users u
JOIN user_groups ug ON u.id = ug.user_id
JOIN groups g ON ug.group_id = g.id
LEFT JOIN group_roles gr ON g.id = gr.group_id
LEFT JOIN roles r ON gr.role_id = r.id
WHERE u.id = 8
ORDER BY g.name;
