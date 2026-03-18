-- ⚠️  SUPERSEDED — This rollback is now handled automatically by schema_init.py.
-- The rollback RENAME statements are in the SCHEMA_DDL list and run on every
-- server startup. No need to run this script manually.
--
-- Rollback: 010_rollback_agent_types_to_roles.sql
-- Description: Rollback migration 010 - Rename agent_types back to roles
-- This script reverses all changes made in 010_rename_roles_to_agent_types.sql
--
-- USE THIS SCRIPT IF YOU NEED TO REVERT THE MIGRATION
--
-- Changes (reversed):
-- 1. chatbot_agent_types → chatbot_roles
-- 2. chatbot_tools → chatbot_permissions
-- 3. chatbot_agent_type_tools → chatbot_role_permissions
-- 4. chatbot_group_agent_types → chatbot_group_roles
-- 5. Revert all foreign key column names

BEGIN;

-- ============================================================================
-- STEP 1: Rename chatbot_agent_types back to chatbot_roles
-- ============================================================================
ALTER TABLE chatbot_agent_types RENAME TO chatbot_roles;

-- Rename indexes
ALTER INDEX IF EXISTS idx_chatbot_agent_types_name RENAME TO idx_chatbot_roles_name;

-- ============================================================================
-- STEP 2: Rename chatbot_tools back to chatbot_permissions
-- ============================================================================
ALTER TABLE chatbot_tools RENAME TO chatbot_permissions;

-- Rename indexes
ALTER INDEX IF EXISTS idx_chatbot_tools_category RENAME TO idx_chatbot_permissions_category;

-- ============================================================================
-- STEP 3: Rename chatbot_agent_type_tools back to chatbot_role_permissions
-- ============================================================================
ALTER TABLE chatbot_agent_type_tools RENAME TO chatbot_role_permissions;

-- Rename columns in chatbot_role_permissions
ALTER TABLE chatbot_role_permissions RENAME COLUMN agent_type_id TO role_id;
ALTER TABLE chatbot_role_permissions RENAME COLUMN tool_id TO permission_id;

-- Rename indexes
ALTER INDEX IF EXISTS idx_chatbot_agent_type_tools_agent_type RENAME TO idx_chatbot_role_permissions_role;
ALTER INDEX IF EXISTS idx_chatbot_agent_type_tools_tool RENAME TO idx_chatbot_role_permissions_permission;

-- ============================================================================
-- STEP 4: Rename chatbot_group_agent_types back to chatbot_group_roles
-- ============================================================================
ALTER TABLE chatbot_group_agent_types RENAME TO chatbot_group_roles;

-- Rename columns in chatbot_group_roles
ALTER TABLE chatbot_group_roles RENAME COLUMN chatbot_agent_type_id TO chatbot_role_id;

-- Rename indexes
ALTER INDEX IF EXISTS idx_chatbot_group_agent_types_group RENAME TO idx_chatbot_group_roles_group;
ALTER INDEX IF EXISTS idx_chatbot_group_agent_types_agent_type RENAME TO idx_chatbot_group_roles_role;

-- ============================================================================
-- STEP 5: Rename sequences back
-- ============================================================================
ALTER SEQUENCE IF EXISTS chatbot_agent_types_id_seq RENAME TO chatbot_roles_id_seq;
ALTER SEQUENCE IF EXISTS chatbot_tools_id_seq RENAME TO chatbot_permissions_id_seq;
ALTER SEQUENCE IF EXISTS chatbot_agent_type_tools_id_seq RENAME TO chatbot_role_permissions_id_seq;
ALTER SEQUENCE IF EXISTS chatbot_group_agent_types_id_seq RENAME TO chatbot_group_roles_id_seq;

-- ============================================================================
-- STEP 6: Revert constraint names
-- ============================================================================
DO $$
DECLARE
    constraint_record RECORD;
BEGIN
    -- Rename foreign key constraints in chatbot_role_permissions
    FOR constraint_record IN 
        SELECT constraint_name 
        FROM information_schema.table_constraints 
        WHERE table_name = 'chatbot_role_permissions' 
        AND constraint_type = 'FOREIGN KEY'
    LOOP
        IF constraint_record.constraint_name LIKE '%agent_type%' THEN
            EXECUTE format('ALTER TABLE chatbot_role_permissions RENAME CONSTRAINT %I TO %I',
                constraint_record.constraint_name,
                replace(constraint_record.constraint_name, 'agent_type', 'role'));
        END IF;
        IF constraint_record.constraint_name LIKE '%tool%' THEN
            EXECUTE format('ALTER TABLE chatbot_role_permissions RENAME CONSTRAINT %I TO %I',
                constraint_record.constraint_name,
                replace(constraint_record.constraint_name, 'tool', 'permission'));
        END IF;
    END LOOP;

    -- Rename foreign key constraints in chatbot_group_roles
    FOR constraint_record IN 
        SELECT constraint_name 
        FROM information_schema.table_constraints 
        WHERE table_name = 'chatbot_group_roles' 
        AND constraint_type = 'FOREIGN KEY'
    LOOP
        IF constraint_record.constraint_name LIKE '%agent_type%' THEN
            EXECUTE format('ALTER TABLE chatbot_group_roles RENAME CONSTRAINT %I TO %I',
                constraint_record.constraint_name,
                replace(constraint_record.constraint_name, 'agent_type', 'role'));
        END IF;
    END LOOP;
END $$;

-- ============================================================================
-- VERIFICATION: Display reverted tables
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '=== Rollback Complete ===';
    RAISE NOTICE 'Tables reverted:';
    RAISE NOTICE '  chatbot_agent_types → chatbot_roles';
    RAISE NOTICE '  chatbot_tools → chatbot_permissions';
    RAISE NOTICE '  chatbot_agent_type_tools → chatbot_role_permissions';
    RAISE NOTICE '  chatbot_group_agent_types → chatbot_group_roles';
    RAISE NOTICE '';
    RAISE NOTICE 'Columns reverted:';
    RAISE NOTICE '  agent_type_id → role_id';
    RAISE NOTICE '  tool_id → permission_id';
    RAISE NOTICE '  chatbot_agent_type_id → chatbot_role_id';
    RAISE NOTICE '';
    RAISE NOTICE 'All data preserved. Foreign keys automatically updated.';
END $$;

COMMIT;
