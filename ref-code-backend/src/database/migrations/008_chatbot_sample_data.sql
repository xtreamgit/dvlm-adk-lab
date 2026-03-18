-- Sample data for chatbot access control testing
-- Run with: PGPASSWORD=dev_password_123 psql -h localhost -p 5433 -U adk_dev_user -d adk_agents_db_dev -f src/database/migrations/008_chatbot_sample_data.sql

-- Add more chatbot groups
INSERT INTO chatbot_groups (name, description, is_active) VALUES
  ('chatbot-developers', 'Development team with full corpus access', true),
  ('chatbot-managers', 'Management team with read access', true),
  ('chatbot-guests', 'Guest users with limited access', true);

-- Add sample chatbot users (password: test123)
INSERT INTO chatbot_users (username, email, full_name, hashed_password, is_active, notes) VALUES
  ('chatuser1', 'chatuser1@example.com', 'Alice Johnson', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X.VQ9mLZEhQxO1mA6', true, 'Developer user'),
  ('chatuser2', 'chatuser2@example.com', 'Bob Smith', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X.VQ9mLZEhQxO1mA6', true, 'Manager user'),
  ('chatuser3', 'chatuser3@example.com', 'Carol Williams', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X.VQ9mLZEhQxO1mA6', true, 'Guest user'),
  ('chatuser4', 'chatuser4@example.com', 'David Brown', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X.VQ9mLZEhQxO1mA6', false, 'Inactive user');

-- Assign roles to groups
-- Group IDs: 1=default-chatbot-users, 2=chatbot-developers, 3=chatbot-managers, 4=chatbot-guests
-- Role IDs: 1=chatbot-viewer, 2=chatbot-contributor, 3=chatbot-power-user, 4=chatbot-admin
INSERT INTO chatbot_group_roles (chatbot_group_id, chatbot_role_id) VALUES
  (1, 1),  -- default-chatbot-users gets chatbot-viewer
  (2, 3),  -- chatbot-developers gets chatbot-power-user
  (3, 2),  -- chatbot-managers gets chatbot-contributor
  (4, 1);  -- chatbot-guests gets chatbot-viewer

-- Assign permissions to viewer role (1)
INSERT INTO chatbot_role_permissions (chatbot_role_id, chatbot_permission_id) VALUES
  (1, 1),  (1, 2),  (1, 6),  (1, 15), (1, 16);

-- Assign permissions to contributor role (2)
INSERT INTO chatbot_role_permissions (chatbot_role_id, chatbot_permission_id) VALUES
  (2, 1), (2, 2), (2, 3), (2, 6), (2, 9), (2, 10), (2, 11), (2, 15), (2, 16), (2, 17);

-- Assign permissions to power-user role (3)
INSERT INTO chatbot_role_permissions (chatbot_role_id, chatbot_permission_id) VALUES
  (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (3, 7), (3, 9), (3, 10), (3, 11), (3, 12), (3, 13), (3, 14), (3, 15), (3, 16), (3, 17);

-- Assign ALL permissions to admin role (4)
INSERT INTO chatbot_role_permissions (chatbot_role_id, chatbot_permission_id)
  SELECT 4, id FROM chatbot_permissions;

-- Assign users to groups
INSERT INTO chatbot_user_groups (chatbot_user_id, chatbot_group_id) VALUES
  (1, 1), (1, 2),  -- Alice: default + developers
  (2, 1), (2, 3),  -- Bob: default + managers
  (3, 1), (3, 4),  -- Carol: default + guests
  (4, 4);          -- David: guests only (inactive)

-- Grant corpus access (using actual corpus IDs from your DB)
-- Corpus IDs: 1=ai-books, 2=test-corpus, 3=design, 4=management, 5=recipes, 6=semantic-web, 7=hacker-books
INSERT INTO chatbot_corpus_access (chatbot_group_id, corpus_id, permission) VALUES
  (1, 2, 'query'),   -- default: test-corpus (query)
  (2, 1, 'admin'),   -- developers: ai-books (admin)
  (2, 2, 'admin'),   -- developers: test-corpus (admin)
  (2, 3, 'upload'),  -- developers: design (upload)
  (3, 1, 'read'),    -- managers: ai-books (read)
  (3, 4, 'read'),    -- managers: management (read)
  (4, 5, 'query');   -- guests: recipes (query)

-- Grant agent access (agent_id=1 is default_agent)
INSERT INTO chatbot_agent_access (chatbot_group_id, agent_id, can_use, can_configure) VALUES
  (1, 1, true, false),   -- default: use only
  (2, 1, true, true),    -- developers: use + configure
  (3, 1, true, false),   -- managers: use only
  (4, 1, true, false);   -- guests: use only
