-- Reset alice's password in Cloud SQL to a known hash
-- This uses bcrypt hash for password "alice123"
-- Hash generated with: python3 -c "from passlib.context import CryptContext; pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto'); print(pwd_context.hash('alice123'))"

UPDATE users 
SET hashed_password = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIxF.PuhuS'
WHERE username = 'alice';

SELECT username, email, is_active, LEFT(hashed_password, 30) as pwd_prefix
FROM users 
WHERE username = 'alice';
