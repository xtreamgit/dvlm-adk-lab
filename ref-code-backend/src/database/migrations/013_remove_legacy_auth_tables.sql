-- Migration 013: Remove Legacy Auth Tables
-- Date: 2026-02-18
-- Description: Remove groups, user_groups, roles, group_roles tables and their dependencies
--              These are replaced by Google Groups Bridge (chatbot_groups, chatbot_user_groups)

BEGIN;

-- Drop dependent tables first (those with foreign keys to legacy tables)
DROP TABLE IF EXISTS group_corpus_access CASCADE;
DROP TABLE IF EXISTS group_corpora CASCADE;

-- Drop legacy RBAC tables in correct order (respect foreign keys)
DROP TABLE IF EXISTS group_roles CASCADE;
DROP TABLE IF EXISTS user_groups CASCADE;
DROP TABLE IF EXISTS roles CASCADE;
DROP TABLE IF EXISTS groups CASCADE;

-- Add migration record (if schema_migrations table exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'schema_migrations'
    ) THEN
        INSERT INTO schema_migrations (version, description, applied_at)
        VALUES (13, 'Remove legacy auth tables (groups, user_groups, roles, group_roles)', CURRENT_TIMESTAMP);
    END IF;
END $$;

COMMIT;

-- Verification query
SELECT 
    'Legacy tables removed' as status,
    COUNT(*) as remaining_legacy_tables
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('groups', 'user_groups', 'roles', 'group_roles', 'group_corpora', 'group_corpus_access');
