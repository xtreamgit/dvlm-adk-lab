-- Grant Admin Access to Users
-- Creates admin role and grants to specified users

-- 1. Create admin role if it doesn't exist
INSERT INTO roles (name, description)
VALUES ('admin', 'Administrator with full system access')
ON CONFLICT (name) DO NOTHING;

-- 2. Create admins group if it doesn't exist
INSERT INTO groups (name, description)
VALUES ('admins', 'Administrators group with elevated privileges')
ON CONFLICT (name) DO NOTHING;

-- 3. Link admin role to admins group
INSERT INTO group_roles (group_id, role_id)
SELECT g.id, r.id FROM groups g, roles r
WHERE g.name = 'admins' AND r.name = 'admin'
ON CONFLICT DO NOTHING;

-- 4. Also link admin role to existing admin-users group
INSERT INTO group_roles (group_id, role_id)
SELECT g.id, r.id FROM groups g, roles r
WHERE g.name = 'admin-users' AND r.name = 'admin'
ON CONFLICT DO NOTHING;

-- 5. Add admin user to admins group (if not already in admin-users)
INSERT INTO user_groups (user_id, group_id)
SELECT u.id, g.id FROM users u, groups g
WHERE u.username = 'admin' AND g.name = 'admins'
ON CONFLICT DO NOTHING;

-- 6. Add alice to admins group (for testing)
INSERT INTO user_groups (user_id, group_id)
SELECT u.id, g.id FROM users u, groups g
WHERE u.username = 'alice' AND g.name = 'admins'
ON CONFLICT DO NOTHING;

-- 7. Verify the changes
\echo ''
\echo '=== VERIFICATION: Users with Admin Role ==='
SELECT 
    u.username,
    u.email,
    g.name as group_name,
    r.name as role_name
FROM users u
JOIN user_groups ug ON u.id = ug.user_id
JOIN groups g ON ug.group_id = g.id
JOIN group_roles gr ON g.id = gr.group_id
JOIN roles r ON gr.role_id = r.id
WHERE r.name = 'admin'
ORDER BY u.username;

\echo ''
\echo '=== SUCCESS ==='
\echo 'Admin role created and granted to users'
\echo 'Users with admin access can now use /api/admin/* endpoints'
