-- ⚠️  SUPERSEDED — This migration uses table names from migration 010 which has
-- been rolled back. The tables are now chatbot_roles, chatbot_permissions, and
-- chatbot_role_permissions (the original names). DO NOT RUN on new databases.
-- Data seeded by this migration is preserved on databases that already ran it
-- (e.g. Develom) — the rollback only renames the tables/columns, not the data.
--
-- ============================================================================
-- Migration 011: Update Agent Tools and Rename corpus-manager to admin
-- ============================================================================
-- Purpose:
--   1. Update tool names to match agent_hierarchy.py naming convention
--   2. Rename 'corpus-manager' agent type to 'admin'
--   3. Populate chatbot_agent_type_tools with correct associations
--
-- Changes:
--   - Replace old tool names (corpora:query, tools:rag_query) with new names
--   - Rename agent type from 'corpus-manager' to 'admin'
--   - Create agent-to-tool associations based on hierarchy
--
-- Date: 2026-02-05
-- ============================================================================

BEGIN;

-- ============================================================================
-- STEP 1: Clear existing tools and create new ones matching agent_hierarchy.py
-- ============================================================================

-- Clear existing tool associations (if any)
DELETE FROM chatbot_agent_type_tools;

-- Clear existing tools
DELETE FROM chatbot_tools;

-- Insert new tools matching agent_hierarchy.py
-- These are the actual tool names used in the code
INSERT INTO chatbot_tools (name, description, category) VALUES
    -- Viewer tools (4 tools)
    ('rag_query', 'Query documents using RAG', 'tools'),
    ('list_corpora', 'List available corpora', 'tools'),
    ('get_corpus_info', 'Get corpus details', 'tools'),
    ('browse_documents', 'Browse document links', 'tools'),
    
    -- Contributor tools (1 additional tool)
    ('add_data', 'Add documents to corpora', 'tools'),
    
    -- Content Manager tools (1 additional tool)
    ('delete_document', 'Delete documents from corpora', 'tools'),
    
    -- Admin/Corpus Manager tools (2 additional tools)
    ('create_corpus', 'Create new corpora', 'tools'),
    ('delete_corpus', 'Delete entire corpora', 'tools');

-- ============================================================================
-- STEP 2: Rename 'corpus-manager' agent type to 'admin'
-- ============================================================================

-- Update agent type name
UPDATE chatbot_agent_types 
SET name = 'admin',
    description = 'Complete control over corpora and documents. For administrators only.'
WHERE name = 'corpus-manager';

-- Also update any variants
UPDATE chatbot_agent_types 
SET name = 'admin'
WHERE name IN ('corpus-manager-agent', 'admin-agent');

-- ============================================================================
-- STEP 3: Ensure all agent types exist with correct names
-- ============================================================================

-- Insert agent types if they don't exist (using ON CONFLICT to avoid duplicates)
INSERT INTO chatbot_agent_types (name, description) VALUES
    ('viewer', 'Read-only access for general users')
ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description;

INSERT INTO chatbot_agent_types (name, description) VALUES
    ('contributor', 'Users who can add content')
ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description;

INSERT INTO chatbot_agent_types (name, description) VALUES
    ('content-manager', 'Manage documents within existing corpora')
ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description;

INSERT INTO chatbot_agent_types (name, description) VALUES
    ('admin', 'Complete control over corpora and documents. For administrators only.')
ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description;

-- Remove any -agent suffix variants
DELETE FROM chatbot_agent_types WHERE name IN ('viewer-agent', 'contributor-agent', 'content-manager-agent', 'admin-agent');

-- ============================================================================
-- STEP 4: Populate chatbot_agent_type_tools with correct associations
-- ============================================================================

DO $$
DECLARE
    viewer_id INTEGER;
    contributor_id INTEGER;
    content_manager_id INTEGER;
    admin_id INTEGER;
    
    rag_query_id INTEGER;
    list_corpora_id INTEGER;
    get_corpus_info_id INTEGER;
    browse_documents_id INTEGER;
    add_data_id INTEGER;
    delete_document_id INTEGER;
    create_corpus_id INTEGER;
    delete_corpus_id INTEGER;
BEGIN
    -- Get agent type IDs
    SELECT id INTO viewer_id FROM chatbot_agent_types WHERE name = 'viewer';
    SELECT id INTO contributor_id FROM chatbot_agent_types WHERE name = 'contributor';
    SELECT id INTO content_manager_id FROM chatbot_agent_types WHERE name = 'content-manager';
    SELECT id INTO admin_id FROM chatbot_agent_types WHERE name = 'admin';
    
    -- Get tool IDs
    SELECT id INTO rag_query_id FROM chatbot_tools WHERE name = 'rag_query';
    SELECT id INTO list_corpora_id FROM chatbot_tools WHERE name = 'list_corpora';
    SELECT id INTO get_corpus_info_id FROM chatbot_tools WHERE name = 'get_corpus_info';
    SELECT id INTO browse_documents_id FROM chatbot_tools WHERE name = 'browse_documents';
    SELECT id INTO add_data_id FROM chatbot_tools WHERE name = 'add_data';
    SELECT id INTO delete_document_id FROM chatbot_tools WHERE name = 'delete_document';
    SELECT id INTO create_corpus_id FROM chatbot_tools WHERE name = 'create_corpus';
    SELECT id INTO delete_corpus_id FROM chatbot_tools WHERE name = 'delete_corpus';
    
    -- Viewer Agent: 4 tools
    INSERT INTO chatbot_agent_type_tools (agent_type_id, tool_id) VALUES
        (viewer_id, rag_query_id),
        (viewer_id, list_corpora_id),
        (viewer_id, get_corpus_info_id),
        (viewer_id, browse_documents_id);
    
    -- Contributor Agent: All viewer tools + add_data (5 total)
    INSERT INTO chatbot_agent_type_tools (agent_type_id, tool_id) VALUES
        (contributor_id, rag_query_id),
        (contributor_id, list_corpora_id),
        (contributor_id, get_corpus_info_id),
        (contributor_id, browse_documents_id),
        (contributor_id, add_data_id);
    
    -- Content Manager Agent: All contributor tools + delete_document (6 total)
    INSERT INTO chatbot_agent_type_tools (agent_type_id, tool_id) VALUES
        (content_manager_id, rag_query_id),
        (content_manager_id, list_corpora_id),
        (content_manager_id, get_corpus_info_id),
        (content_manager_id, browse_documents_id),
        (content_manager_id, add_data_id),
        (content_manager_id, delete_document_id);
    
    -- Admin Agent: All tools (8 total)
    INSERT INTO chatbot_agent_type_tools (agent_type_id, tool_id) VALUES
        (admin_id, rag_query_id),
        (admin_id, list_corpora_id),
        (admin_id, get_corpus_info_id),
        (admin_id, browse_documents_id),
        (admin_id, add_data_id),
        (admin_id, delete_document_id),
        (admin_id, create_corpus_id),
        (admin_id, delete_corpus_id);
    
    RAISE NOTICE 'Created agent-to-tool associations:';
    RAISE NOTICE '  viewer: 4 tools';
    RAISE NOTICE '  contributor: 5 tools';
    RAISE NOTICE '  content-manager: 6 tools';
    RAISE NOTICE '  admin: 8 tools';
END $$;

-- ============================================================================
-- STEP 5: Verification
-- ============================================================================

DO $$
DECLARE
    rec RECORD;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== Migration 011 Verification ===';
    RAISE NOTICE '';
    RAISE NOTICE 'Agent Types:';
    
    FOR rec IN 
        SELECT name, description 
        FROM chatbot_agent_types 
        ORDER BY 
            CASE name
                WHEN 'viewer' THEN 1
                WHEN 'contributor' THEN 2
                WHEN 'content-manager' THEN 3
                WHEN 'admin' THEN 4
                ELSE 5
            END
    LOOP
        RAISE NOTICE '  % - %', rec.name, rec.description;
    END LOOP;
    
    RAISE NOTICE '';
    RAISE NOTICE 'Tool Counts per Agent Type:';
    
    FOR rec IN 
        SELECT 
            cat.name as agent_type,
            COUNT(catt.tool_id) as tool_count
        FROM chatbot_agent_types cat
        LEFT JOIN chatbot_agent_type_tools catt ON cat.id = catt.agent_type_id
        GROUP BY cat.name
        ORDER BY 
            CASE cat.name
                WHEN 'viewer' THEN 1
                WHEN 'contributor' THEN 2
                WHEN 'content-manager' THEN 3
                WHEN 'admin' THEN 4
                ELSE 5
            END
    LOOP
        RAISE NOTICE '  %: % tools', rec.agent_type, rec.tool_count;
    END LOOP;
    
    RAISE NOTICE '';
    RAISE NOTICE 'All Tools:';
    
    FOR rec IN 
        SELECT name, description 
        FROM chatbot_tools 
        ORDER BY id
    LOOP
        RAISE NOTICE '  % - %', rec.name, rec.description;
    END LOOP;
    
    RAISE NOTICE '';
    RAISE NOTICE '=== Migration 011 Complete ===';
END $$;

COMMIT;
