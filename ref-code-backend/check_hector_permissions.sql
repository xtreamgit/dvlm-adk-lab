-- Check hector user's permissions and group memberships

-- 1. Check hector user details
SELECT id, username, email, is_active, auth_provider 
FROM users 
WHERE username = 'hector';

-- 2. Check hector's group memberships
SELECT u.username, g.name as group_name, g.id as group_id
FROM users u
JOIN user_groups ug ON u.id = ug.user_id
JOIN groups g ON ug.group_id = g.id
WHERE u.username = 'hector';

-- 3. Check available corpora
SELECT id, name, display_name, is_active 
FROM corpora 
WHERE is_active = true;

-- 4. Check corpus access (which groups have access to which corpora)
SELECT 
    c.id as corpus_id,
    c.name as corpus_name,
    g.id as group_id,
    g.name as group_name
FROM corpora c
JOIN corpus_group_access cga ON c.id = cga.corpus_id
JOIN groups g ON cga.group_id = g.id
WHERE c.is_active = true
ORDER BY c.name, g.name;

-- 5. Grant hector access to ai-books corpus via users group
-- First, ensure hector is in the 'users' group
INSERT INTO user_groups (user_id, group_id)
SELECT u.id, g.id 
FROM users u, groups g 
WHERE u.username = 'hector' 
  AND g.name = 'users'
  AND NOT EXISTS (
    SELECT 1 FROM user_groups ug2 
    WHERE ug2.user_id = u.id AND ug2.group_id = g.id
  );

-- Then grant users group access to ai-books corpus if not already granted
INSERT INTO corpus_group_access (corpus_id, group_id, permission)
SELECT c.id, g.id, 'read'
FROM corpora c, groups g
WHERE c.name = 'ai-books'
  AND g.name = 'users'
  AND NOT EXISTS (
    SELECT 1 FROM corpus_group_access cga2
    WHERE cga2.corpus_id = c.id AND cga2.group_id = g.id
  );

-- Verify the fix
SELECT 
    u.username,
    c.name as corpus_name,
    g.name as group_name
FROM users u
JOIN user_groups ug ON u.id = ug.user_id
JOIN groups g ON ug.group_id = g.id
JOIN corpus_group_access cga ON g.id = cga.group_id
JOIN corpora c ON cga.corpus_id = c.id
WHERE u.username = 'hector'
  AND c.is_active = true;
