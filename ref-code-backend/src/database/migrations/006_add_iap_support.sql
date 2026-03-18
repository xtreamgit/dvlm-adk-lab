-- Migration 006: Add IAP Support
-- Purpose: Add Google IAP authentication support
-- Created: 2026-01-10
-- Updated: 2026-01-28 - Converted to PostgreSQL syntax
-- Note: This migration handles the schema change carefully to preserve existing datauthentication
-- Date: 2026-01-10
--
-- Note: SQLite doesn't support adding UNIQUE columns or making columns nullable via ALTER TABLE.
-- We need to recreate the table with the new schema and copy the data.

-- Create new users table with updated schema including IAP support
CREATE TABLE IF NOT EXISTS users_new (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255),  -- Now nullable for IAP users
    google_id VARCHAR(255) UNIQUE,  -- Google user ID from IAP
    auth_provider VARCHAR(50) DEFAULT 'local',  -- 'local' or 'google'
    is_active BOOLEAN DEFAULT TRUE,
    default_agent_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    FOREIGN KEY (default_agent_id) REFERENCES agents(id)
);

-- Copy existing data to new table (only existing columns, new ones get defaults)
INSERT INTO users_new (id, username, email, full_name, hashed_password, google_id, 
                       auth_provider, is_active, default_agent_id, created_at, updated_at, last_login)
SELECT id, username, email, full_name, hashed_password, NULL,
       'local', is_active, default_agent_id, created_at, updated_at, last_login
FROM users;

-- Drop old table and rename new one
DROP TABLE users;
ALTER TABLE users_new RENAME TO users;

-- Recreate indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
CREATE INDEX IF NOT EXISTS idx_users_auth_provider ON users(auth_provider);

-- Migration complete
