-- Update password hashes in Cloud SQL with fresh bcrypt hashes
-- Generated from backend/scripts/fix_cloudsql_passwords.py

UPDATE users SET hashed_password = '$2b$12$8uwPP/tCIx8BJE9LeYudbu./ODStaWtPGK33HwbwW4t8f2LhM8fri' WHERE username = 'alice';
UPDATE users SET hashed_password = '$2b$12$SJuiqfsEmi8FGTRSA1v4Xe/cRMg3iVUhLg0R758paUKlVdNMHA7Hi' WHERE username = 'bob';
UPDATE users SET hashed_password = '$2b$12$5X3kiRCiVyq8LhbpI9.tS.7RKQST6WhssE4YYVPBfNn5owsCWH116' WHERE username = 'admin';

-- Verify the updates
SELECT username, email, LEFT(hashed_password, 30) as pwd_prefix, is_active FROM users WHERE username IN ('alice', 'bob', 'admin');
