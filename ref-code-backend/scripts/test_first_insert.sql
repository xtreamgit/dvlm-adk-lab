-- Test first insert
INSERT INTO users ("username", "email", "full_name", "hashed_password", "is_active", "default_agent_id", "created_at", "updated_at", "last_login") 
VALUES ('admin', 'admin@develom.com', 'Admin User - admin', '$2b$12$b4H1t1fmUmfN3lmK2DPUy.vUSMsHu5lc9LWiFcYTb9oQq1I2eNCra', TRUE, 1, '2025-12-31T23:48:38.052975+00:00', '2026-01-09T21:46:45.096674+00:00', '2026-01-10T20:05:19.261525+00:00');

SELECT * FROM users;
