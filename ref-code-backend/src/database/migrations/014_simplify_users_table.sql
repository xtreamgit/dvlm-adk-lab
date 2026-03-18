-- Migration 014: Simplify Users Table
-- Date: 2026-02-18
-- Description: Remove legacy authentication columns from users table
--              IAP handles all authentication, so username/password/auth_provider are no longer needed
--              Email is now the primary user identifier

BEGIN;

-- Remove legacy authentication columns
ALTER TABLE users DROP COLUMN IF EXISTS hashed_password CASCADE;
ALTER TABLE users DROP COLUMN IF EXISTS username CASCADE;
ALTER TABLE users DROP COLUMN IF EXISTS auth_provider CASCADE;

-- Ensure email is unique and not null (should already be the case)
-- Add constraint if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'users_email_key' 
        AND conrelid = 'users'::regclass
    ) THEN
        ALTER TABLE users ADD CONSTRAINT users_email_key UNIQUE (email);
    END IF;
END $$;

-- Update email column to be NOT NULL if it isn't already
ALTER TABLE users ALTER COLUMN email SET NOT NULL;

-- Add migration record (if schema_migrations table exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'schema_migrations'
    ) THEN
        INSERT INTO schema_migrations (version, description, applied_at)
        VALUES (14, 'Simplify users table - remove legacy auth columns', CURRENT_TIMESTAMP);
    END IF;
END $$;

COMMIT;

-- Verification query
SELECT 
    'Users table simplified' as status,
    COUNT(*) as remaining_auth_columns
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name = 'users'
  AND column_name IN ('hashed_password', 'username', 'auth_provider');
