-- ⚠️  NOTE: Lines 68-72 reference chatbot_agent_types (the migrated name from
-- migration 010). After the rollback in schema_init.py, the table is chatbot_roles.
-- The constraint changes in this migration already ran on Develom and are harmless
-- after the table rename (PostgreSQL constraints follow the table object, not name).
-- DO NOT re-run this migration on databases that already ran it.
--
-- Migration 015: Add user_id FK to chatbot_users and fix FK cascades
-- Date: 2026-02-20
-- Description:
--   1. Add chatbot_users.user_id column with FK to users(id) ON DELETE CASCADE
--   2. Backfill user_id from email matching
--   3. Change all created_by/granted_by FKs on chatbot_* tables to ON DELETE SET NULL
--   4. Change remaining RESTRICT FKs on users to ON DELETE SET NULL where appropriate

BEGIN;

-- ============================================================================
-- STEP 1: Add user_id column to chatbot_users
-- ============================================================================
ALTER TABLE chatbot_users
    ADD COLUMN IF NOT EXISTS user_id INTEGER;

-- Backfill user_id from email matching
UPDATE chatbot_users cu
SET user_id = u.id
FROM users u
WHERE cu.email = u.email
  AND cu.user_id IS NULL;

-- Add FK constraint
ALTER TABLE chatbot_users
    ADD CONSTRAINT chatbot_users_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Add unique index (one chatbot_user per user)
CREATE UNIQUE INDEX IF NOT EXISTS idx_chatbot_users_user_id
    ON chatbot_users(user_id) WHERE user_id IS NOT NULL;

-- ============================================================================
-- STEP 2: Fix FK cascades — change RESTRICT to ON DELETE SET NULL
-- for all created_by / granted_by columns referencing users(id)
-- ============================================================================

-- chatbot_users.created_by
ALTER TABLE chatbot_users DROP CONSTRAINT IF EXISTS chatbot_users_created_by_fkey;
ALTER TABLE chatbot_users
    ADD CONSTRAINT chatbot_users_created_by_fkey
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;

-- chatbot_groups.created_by
ALTER TABLE chatbot_groups DROP CONSTRAINT IF EXISTS chatbot_groups_created_by_fkey;
ALTER TABLE chatbot_groups
    ADD CONSTRAINT chatbot_groups_created_by_fkey
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;

-- chatbot_corpus_access.granted_by
ALTER TABLE chatbot_corpus_access DROP CONSTRAINT IF EXISTS chatbot_corpus_access_granted_by_fkey;
ALTER TABLE chatbot_corpus_access
    ADD CONSTRAINT chatbot_corpus_access_granted_by_fkey
    FOREIGN KEY (granted_by) REFERENCES users(id) ON DELETE SET NULL;

-- chatbot_agent_access.granted_by
ALTER TABLE chatbot_agent_access DROP CONSTRAINT IF EXISTS chatbot_agent_access_granted_by_fkey;
ALTER TABLE chatbot_agent_access
    ADD CONSTRAINT chatbot_agent_access_granted_by_fkey
    FOREIGN KEY (granted_by) REFERENCES users(id) ON DELETE SET NULL;

-- chatbot_tool_access.granted_by
ALTER TABLE chatbot_tool_access DROP CONSTRAINT IF EXISTS chatbot_tool_access_granted_by_fkey;
ALTER TABLE chatbot_tool_access
    ADD CONSTRAINT chatbot_tool_access_granted_by_fkey
    FOREIGN KEY (granted_by) REFERENCES users(id) ON DELETE SET NULL;

-- chatbot_agent_types.created_by (was chatbot_roles_created_by_fkey)
ALTER TABLE chatbot_agent_types DROP CONSTRAINT IF EXISTS chatbot_roles_created_by_fkey;
ALTER TABLE chatbot_agent_types
    ADD CONSTRAINT chatbot_agent_types_created_by_fkey
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;

-- chatbot_group_agents.granted_by
ALTER TABLE chatbot_group_agents DROP CONSTRAINT IF EXISTS chatbot_group_agents_granted_by_fkey;
ALTER TABLE chatbot_group_agents
    ADD CONSTRAINT chatbot_group_agents_granted_by_fkey
    FOREIGN KEY (granted_by) REFERENCES users(id) ON DELETE SET NULL;

-- google_group_agent_mappings.created_by
ALTER TABLE google_group_agent_mappings DROP CONSTRAINT IF EXISTS google_group_agent_mappings_created_by_fkey;
ALTER TABLE google_group_agent_mappings
    ADD CONSTRAINT google_group_agent_mappings_created_by_fkey
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;

-- google_group_corpus_mappings.created_by
ALTER TABLE google_group_corpus_mappings DROP CONSTRAINT IF EXISTS google_group_corpus_mappings_created_by_fkey;
ALTER TABLE google_group_corpus_mappings
    ADD CONSTRAINT google_group_corpus_mappings_created_by_fkey
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;

COMMIT;

-- ============================================================================
-- Verification
-- ============================================================================
SELECT 'chatbot_users.user_id backfill' as check_name,
       COUNT(*) as total,
       COUNT(user_id) as with_user_id,
       COUNT(*) - COUNT(user_id) as missing_user_id
FROM chatbot_users;

SELECT conrelid::regclass AS table_name,
       conname AS constraint_name,
       pg_get_constraintdef(oid) AS definition
FROM pg_constraint
WHERE confrelid = 'users'::regclass
  AND contype = 'f'
  AND conname LIKE '%created_by%' OR conname LIKE '%granted_by%'
ORDER BY conrelid::regclass::text;
