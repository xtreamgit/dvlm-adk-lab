-- Data import for Cloud SQL
-- Generated from: 2026-01-13T17:24:56.283545
-- Database: adk_agents_db
-- Note: No transaction wrapper - each insert is independent

-- Table: users
INSERT INTO users ("username", "email", "full_name", "hashed_password", "is_active", "default_agent_id", "created_at", "updated_at", "last_login") VALUES ('admin', 'admin@develom.com', 'Admin User - admin', '$2b$12$b4H1t1fmUmfN3lmK2DPUy.vUSMsHu5lc9LWiFcYTb9oQq1I2eNCra', TRUE, 1, '2025-12-31T23:48:38.052975+00:00', '2026-01-09T21:46:45.096674+00:00', '2026-01-10T20:05:19.261525+00:00');
INSERT INTO users ("username", "email", "full_name", "hashed_password", "is_active", "default_agent_id", "created_at", "updated_at", "last_login") VALUES ('alice', 'alice@example.com', 'Alice Developer', '$2b$12$vdKQtMBpVJvAptANBhlV5uoES7MQrdFHzNYUFG1ZPBYNA4HVnaeaq', TRUE, 1, '2026-01-01T18:43:11.156214+00:00', '2026-01-09T21:46:44.839756+00:00', '2026-01-10T01:14:03.414354+00:00');
INSERT INTO users ("username", "email", "full_name", "hashed_password", "is_active", "default_agent_id", "created_at", "updated_at", "last_login") VALUES ('charlie', 'charlie@example.com', 'Charlie Viewer', '$2b$12$MA3fq4EJAEOw/zz7R/RHIOVxXAU9mBrG9z0RKXFw9sCBu7Xw2fO/S', TRUE, 3, '2026-01-01T18:43:11.474913+00:00', '2026-01-01T18:43:11.474913+00:00', '2026-01-09T01:50:17.224527+00:00');
INSERT INTO users ("username", "email", "full_name", "hashed_password", "is_active", "default_agent_id", "created_at", "updated_at", "last_login") VALUES ('bob', 'bob@example.com', 'Bob Manager', '$2b$12$qEe5/ZMIrYu1lw.a0pl3melcc7Uk6./lHO/eltcuXygEp9sxaGtdO', TRUE, 2, '2026-01-01T18:43:56.557588+00:00', '2026-01-01T18:43:56.557588+00:00', '2026-01-08T23:54:01.882215+00:00');
INSERT INTO users ("username", "email", "full_name", "hashed_password", "is_active", "default_agent_id", "created_at", "updated_at", "last_login") VALUES ('testuser', 'test@example.com', 'Test User', '$2b$12$maH/O7i5YEA/nL0YtfsX0eftdXzFKXqU.zVidTgqwlK4lMJexito.', TRUE, NULL, '2026-01-09T06:38:04.364866+00:00', '2026-01-09T06:38:04.364866+00:00', NULL);
INSERT INTO users ("username", "email", "full_name", "hashed_password", "is_active", "default_agent_id", "created_at", "updated_at", "last_login") VALUES ('andrew', 'andrew.stratton@usda.gov', 'Andrew Stratton', '$2b$12$Y96v8wXlGzwLwWpjLtmTxOC1o/ejxr2Fr0iDbW0SLAyD1ngCTDTEq', TRUE, NULL, '2026-01-10T20:12:00.144864+00:00', '2026-01-10T20:12:00.144864+00:00', NULL);

-- Table: user_profiles
INSERT INTO user_profiles ("user_id", "theme", "language", "timezone", "preferences") VALUES (1, 'light', 'en', 'UTC', '{"selected_corpora": ["management", "design", "ai-books"]}');
INSERT INTO user_profiles ("user_id", "theme", "language", "timezone", "preferences") VALUES (2, 'light', 'en', 'UTC', '{"selected_corpora": ["ai-books", "design", "management"]}');
INSERT INTO user_profiles ("user_id", "theme", "language", "timezone", "preferences") VALUES (3, 'light', 'en', 'UTC', NULL);
INSERT INTO user_profiles ("user_id", "theme", "language", "timezone", "preferences") VALUES (4, 'light', 'en', 'UTC', NULL);
INSERT INTO user_profiles ("user_id", "theme", "language", "timezone", "preferences") VALUES (5, 'light', 'en', 'UTC', NULL);
INSERT INTO user_profiles ("user_id", "theme", "language", "timezone", "preferences") VALUES (6, 'light', 'en', 'UTC', NULL);

-- Table: groups
INSERT INTO groups ("name", "description", "created_at", "is_active") VALUES ('default-users', 'Default group for all users', '2025-12-31T23:40:41.130214+00:00', TRUE);
INSERT INTO groups ("name", "description", "created_at", "is_active") VALUES ('admin-users', 'Administrative users with elevated privileges', '2025-12-31T23:40:41.133970+00:00', TRUE);
INSERT INTO groups ("name", "description", "created_at", "is_active") VALUES ('develom-group', 'Develom organization users', '2025-12-31T23:40:41.136943+00:00', TRUE);
INSERT INTO groups ("name", "description", "created_at", "is_active") VALUES ('developers', 'Software developers with full access', '2026-01-01T18:43:11.515651+00:00', TRUE);
INSERT INTO groups ("name", "description", "created_at", "is_active") VALUES ('managers', 'Managers with oversight access', '2026-01-01T18:43:11.547268+00:00', TRUE);
INSERT INTO groups ("name", "description", "created_at", "is_active") VALUES ('viewers', 'Users with read-only access', '2026-01-01T18:43:11.577979+00:00', TRUE);

-- Table: roles
INSERT INTO roles ("name", "description", "permissions", "created_at") VALUES ('user', 'Standard user role', '["read:own_profile", "update:own_profile", "read:own_corpora", "chat:own_agents", "read:agents", "switch:agents"]', '2025-12-31T23:40:41.140682+00:00');
INSERT INTO roles ("name", "description", "permissions", "created_at") VALUES ('corpus_admin', 'Corpus administrator', '["create:corpus", "update:corpus", "delete:corpus", "manage:corpus_access", "read:all_corpora"]', '2025-12-31T23:40:41.144258+00:00');
INSERT INTO roles ("name", "description", "permissions", "created_at") VALUES ('system_admin', 'System administrator with full access', '["*"]', '2025-12-31T23:40:41.147724+00:00');

-- Table: user_groups
INSERT INTO user_groups ("user_id", "group_id", "assigned_at") VALUES (1, 2, '2025-12-31 23:48:38');
INSERT INTO user_groups ("user_id", "group_id", "assigned_at") VALUES (1, 1, '2025-12-31 23:48:38');
INSERT INTO user_groups ("user_id", "group_id", "assigned_at") VALUES (2, 4, '2026-01-01 18:48:14');
INSERT INTO user_groups ("user_id", "group_id", "assigned_at") VALUES (4, 5, '2026-01-01 18:48:14');
INSERT INTO user_groups ("user_id", "group_id", "assigned_at") VALUES (3, 6, '2026-01-01 18:48:14');
INSERT INTO user_groups ("user_id", "group_id", "assigned_at") VALUES (2, 2, '2026-01-09 01:18:03');
INSERT INTO user_groups ("user_id", "group_id", "assigned_at") VALUES (6, 2, '2026-01-10 20:12:00');

-- Table: group_roles
INSERT INTO group_roles ("group_id", "role_id", "assigned_at") VALUES (1, 1, '2025-12-31 23:40:41');
INSERT INTO group_roles ("group_id", "role_id", "assigned_at") VALUES (2, 3, '2025-12-31 23:40:41');
INSERT INTO group_roles ("group_id", "role_id", "assigned_at") VALUES (3, 1, '2025-12-31 23:40:41');

-- Table: agents
INSERT INTO agents ("name", "display_name", "description", "config_path", "is_active", "created_at") VALUES ('default-agent', 'Default Agent', 'Default general-purpose RAG agent', 'develom', TRUE, '2025-12-31T23:40:19.539887+00:00');
INSERT INTO agents ("name", "display_name", "description", "config_path", "is_active", "created_at") VALUES ('agent1', 'Agent 1', 'Specialized agent 1', 'agent1', TRUE, '2025-12-31T23:40:19.545101+00:00');
INSERT INTO agents ("name", "display_name", "description", "config_path", "is_active", "created_at") VALUES ('agent2', 'Agent 2', 'Specialized agent 2', 'agent2', TRUE, '2025-12-31T23:40:19.548455+00:00');
INSERT INTO agents ("name", "display_name", "description", "config_path", "is_active", "created_at") VALUES ('agent3', 'Agent 3', 'Specialized agent 3', 'agent3', TRUE, '2025-12-31T23:40:19.551838+00:00');
INSERT INTO agents ("name", "display_name", "description", "config_path", "is_active", "created_at") VALUES ('tt-agent', 'TT Agent', 'TT specialized agent', 'tt', TRUE, '2025-12-31T23:40:19.555000+00:00');
INSERT INTO agents ("name", "display_name", "description", "config_path", "is_active", "created_at") VALUES ('usfs-agent', 'USFS Agent', 'USFS specialized agent', 'usfs', TRUE, '2025-12-31T23:40:19.558992+00:00');

-- Table: corpora
INSERT INTO corpora ("name", "display_name", "description", "gcs_bucket", "vertex_corpus_id", "is_active", "created_at") VALUES ('develom-general', 'Develom General Knowledge', 'General knowledge base for Develom organization', 'develom-documents', NULL, FALSE, '2025-12-31T23:40:41.156070+00:00');
INSERT INTO corpora ("name", "display_name", "description", "gcs_bucket", "vertex_corpus_id", "is_active", "created_at") VALUES ('ai-books', 'AI Books Collection', 'Collection of AI and technology books', 'ipad-book-collection', 'projects/adk-rag-ma/locations/us-west1/ragCorpora/2305843009213693952', TRUE, '2025-12-31T23:40:41.160041+00:00');
INSERT INTO corpora ("name", "display_name", "description", "gcs_bucket", "vertex_corpus_id", "is_active", "created_at") VALUES ('test-corpus', 'Test Corpus', 'Test corpus for development', 'test-bucket', 'projects/adk-rag-ma/locations/us-west1/ragCorpora/6917529027641081856', TRUE, '2026-01-02 21:47:26');
INSERT INTO corpora ("name", "display_name", "description", "gcs_bucket", "vertex_corpus_id", "is_active", "created_at") VALUES ('design', 'design', 'Synced from Vertex AI on 2026-01-07T21:43:00.123602', 'gs://adk-rag-ma-design', 'projects/adk-rag-ma/locations/us-west1/ragCorpora/3379951520341557248', TRUE, '2026-01-08T05:43:00.123618+00:00');
INSERT INTO corpora ("name", "display_name", "description", "gcs_bucket", "vertex_corpus_id", "is_active", "created_at") VALUES ('management', 'management', 'Synced from Vertex AI on 2026-01-07T21:43:00.126967', 'gs://adk-rag-ma-management', 'projects/adk-rag-ma/locations/us-west1/ragCorpora/6838716034162098176', TRUE, '2026-01-08T05:43:00.126980+00:00');
INSERT INTO corpora ("name", "display_name", "description", "gcs_bucket", "vertex_corpus_id", "is_active", "created_at") VALUES ('usfs-corpora', 'usfs-corpora', 'Synced from Vertex AI on 2026-01-07T21:43:00.130858', 'gs://adk-rag-ma-usfs-corpora', 'projects/adk-rag-ma/locations/us-west1/ragCorpora/137359788634800128', FALSE, '2026-01-08T05:43:00.130871+00:00');
INSERT INTO corpora ("name", "display_name", "description", "gcs_bucket", "vertex_corpus_id", "is_active", "created_at") VALUES ('fiction', 'fiction', 'Synced from Vertex AI on 2026-01-08T11:36:05.531300', 'gs://adk-rag-ma-fiction', 'projects/adk-rag-ma/locations/us-west1/ragCorpora/7991637538768945152', FALSE, '2026-01-08T19:36:05.531312+00:00');
INSERT INTO corpora ("name", "display_name", "description", "gcs_bucket", "vertex_corpus_id", "is_active", "created_at") VALUES ('recipes', 'recipes', 'Synced from Vertex AI on 2026-01-08T12:55:42.546437', 'gs://adk-rag-ma-recipes', 'projects/adk-rag-ma/locations/us-west1/ragCorpora/4532873024948404224', TRUE, '2026-01-08T20:55:42.546450+00:00');
INSERT INTO corpora ("name", "display_name", "description", "gcs_bucket", "vertex_corpus_id", "is_active", "created_at") VALUES ('semantic-web', 'semantic-web', 'Synced from Vertex AI', '', 'projects/adk-rag-ma/locations/us-west1/ragCorpora/4749045807062188032', TRUE, '2026-01-09T05:21:30.037150+00:00');

-- Table: user_agent_access
INSERT INTO user_agent_access ("user_id", "agent_id", "granted_at") VALUES (1, 2, '2025-12-31 23:48:38');
INSERT INTO user_agent_access ("user_id", "agent_id", "granted_at") VALUES (1, 3, '2025-12-31 23:48:38');
INSERT INTO user_agent_access ("user_id", "agent_id", "granted_at") VALUES (1, 4, '2025-12-31 23:48:38');
INSERT INTO user_agent_access ("user_id", "agent_id", "granted_at") VALUES (1, 1, '2025-12-31 23:48:38');
INSERT INTO user_agent_access ("user_id", "agent_id", "granted_at") VALUES (1, 5, '2025-12-31 23:48:38');
INSERT INTO user_agent_access ("user_id", "agent_id", "granted_at") VALUES (1, 6, '2025-12-31 23:48:38');
INSERT INTO user_agent_access ("user_id", "agent_id", "granted_at") VALUES (2, 1, '2026-01-02 17:58:24');
INSERT INTO user_agent_access ("user_id", "agent_id", "granted_at") VALUES (4, 2, '2026-01-02 17:58:24');
INSERT INTO user_agent_access ("user_id", "agent_id", "granted_at") VALUES (3, 3, '2026-01-02 17:58:24');

-- Table: group_corpus_access
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (1, 1, 'read', '2025-12-31 23:40:41');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (3, 1, 'write', '2025-12-31 23:40:41');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (3, 2, 'read', '2025-12-31 23:40:41');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (2, 1, 'admin', '2025-12-31 23:40:41');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (2, 2, 'admin', '2025-12-31 23:40:41');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (4, 1, 'admin', '2026-01-01 18:52:18');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (4, 2, 'admin', '2026-01-01 18:52:18');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (5, 1, 'admin', '2026-01-01 18:52:18');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (5, 2, 'admin', '2026-01-01 18:52:18');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (6, 1, 'read', '2026-01-01 18:52:18');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (6, 2, 'read', '2026-01-01 18:52:18');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (2, 3, 'admin', '2026-01-02 21:49:30');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (3, 3, 'write', '2026-01-02 21:49:30');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (6, 3, 'read', '2026-01-02 21:49:30');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (4, 3, 'admin', '2026-01-02 21:56:14');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (5, 3, 'admin', '2026-01-02 21:56:14');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (2, 4, 'admin', '2026-01-08 15:38:21');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (3, 4, 'read', '2026-01-08 15:38:21');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (4, 4, 'admin', '2026-01-08 15:38:21');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (5, 4, 'admin', '2026-01-08 15:38:21');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (6, 4, 'read', '2026-01-08 15:38:21');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (2, 5, 'admin', '2026-01-08 15:38:21');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (3, 5, 'read', '2026-01-08 15:38:21');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (4, 5, 'admin', '2026-01-08 15:38:21');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (5, 5, 'admin', '2026-01-08 15:38:21');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (6, 5, 'read', '2026-01-08 15:38:21');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (2, 6, 'admin', '2026-01-08 15:38:21');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (3, 6, 'read', '2026-01-08 15:38:21');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (4, 6, 'admin', '2026-01-08 15:38:21');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (5, 6, 'admin', '2026-01-08 15:38:21');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (6, 6, 'read', '2026-01-08 15:38:21');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (4, 7, 'read', '2026-01-08 19:38:45');
INSERT INTO group_corpus_access ("group_id", "corpus_id", "permission", "granted_at") VALUES (4, 8, 'read', '2026-01-08 20:56:12');

-- Table: corpus_metadata
INSERT INTO corpus_metadata ("corpus_id", "created_by", "created_at", "last_synced_at", "last_synced_by", "document_count", "last_document_count_update", "sync_status", "sync_error_message", "tags", "notes") VALUES (2, NULL, '2026-01-09T02:30:46.005640', NULL, NULL, 0, NULL, 'active', NULL, NULL, NULL);
INSERT INTO corpus_metadata ("corpus_id", "created_by", "created_at", "last_synced_at", "last_synced_by", "document_count", "last_document_count_update", "sync_status", "sync_error_message", "tags", "notes") VALUES (3, NULL, '2026-01-09T02:37:11.428108', NULL, NULL, 0, NULL, 'active', NULL, NULL, NULL);
INSERT INTO corpus_metadata ("corpus_id", "created_by", "created_at", "last_synced_at", "last_synced_by", "document_count", "last_document_count_update", "sync_status", "sync_error_message", "tags", "notes") VALUES (4, NULL, '2026-01-09T02:37:11.436151', NULL, NULL, 0, NULL, 'active', NULL, NULL, NULL);
INSERT INTO corpus_metadata ("corpus_id", "created_by", "created_at", "last_synced_at", "last_synced_by", "document_count", "last_document_count_update", "sync_status", "sync_error_message", "tags", "notes") VALUES (5, NULL, '2026-01-09T02:37:11.444093', NULL, NULL, 0, NULL, 'active', NULL, NULL, NULL);
INSERT INTO corpus_metadata ("corpus_id", "created_by", "created_at", "last_synced_at", "last_synced_by", "document_count", "last_document_count_update", "sync_status", "sync_error_message", "tags", "notes") VALUES (8, NULL, '2026-01-09T02:37:11.451655', NULL, NULL, 0, NULL, 'active', NULL, NULL, NULL);
INSERT INTO corpus_metadata ("corpus_id", "created_by", "created_at", "last_synced_at", "last_synced_by", "document_count", "last_document_count_update", "sync_status", "sync_error_message", "tags", "notes") VALUES (9, 2, '2026-01-09T05:21:30.041852', NULL, NULL, 0, NULL, 'active', NULL, 'semantic, web, html', '');
INSERT INTO corpus_metadata ("corpus_id", "created_by", "created_at", "last_synced_at", "last_synced_by", "document_count", "last_document_count_update", "sync_status", "sync_error_message", "tags", "notes") VALUES (1, NULL, '2026-01-10T20:44:14.362680', NULL, NULL, 0, NULL, 'active', NULL, NULL, NULL);
INSERT INTO corpus_metadata ("corpus_id", "created_by", "created_at", "last_synced_at", "last_synced_by", "document_count", "last_document_count_update", "sync_status", "sync_error_message", "tags", "notes") VALUES (7, NULL, '2026-01-10T20:44:14.385250', NULL, NULL, 0, NULL, 'active', NULL, NULL, NULL);
INSERT INTO corpus_metadata ("corpus_id", "created_by", "created_at", "last_synced_at", "last_synced_by", "document_count", "last_document_count_update", "sync_status", "sync_error_message", "tags", "notes") VALUES (6, NULL, '2026-01-10T20:44:14.399491', NULL, NULL, 0, NULL, 'active', NULL, NULL, NULL);

-- Table: corpus_audit_log
INSERT INTO corpus_audit_log ("corpus_id", "user_id", "action", "changes", "metadata", "timestamp") VALUES (9, 2, 'created', '{"source": "vertex_ai_sync"}', '{"operation": "sync"}', '2026-01-09T05:21:30.044382');
INSERT INTO corpus_audit_log ("corpus_id", "user_id", "action", "changes", "metadata", "timestamp") VALUES (9, 2, 'updated', '{"before": {"id": 6, "corpus_id": 9, "created_by": 2, "created_at": "2026-01-09T05:21:30.041852", "last_synced_at": null, "last_synced_by": null, "document_count": 0, "last_document_count_update": null, "sync_status": "active", "sync_error_message": null, "tags": null, "notes": null, "created_by_name": "alice", "last_synced_by_name": null}, "after": {"id": 6, "corpus_id": 9, "created_by": 2, "created_at": "2026-01-09T05:21:30.041852", "last_synced_at": null, "last_synced_by": null, "document_count": 0, "last_document_count_update": null, "sync_status": "active", "sync_error_message": null, "tags": "semantic, web, html", "notes": "", "created_by_name": "alice", "last_synced_by_name": null}, "fields": ["tags", "notes"]}', '{"operation": "update_metadata"}', '2026-01-09T05:27:36.928697');
INSERT INTO corpus_audit_log ("corpus_id", "user_id", "action", "changes", "metadata", "timestamp") VALUES (2, 2, 'granted_access', '{"group_id": 3, "permission": "read"}', '{"operation": "grant_permission"}', '2026-01-09T05:51:40.726622');
INSERT INTO corpus_audit_log ("corpus_id", "user_id", "action", "changes", "metadata", "timestamp") VALUES (8, 2, 'granted_access', '{"group_id": 2, "permission": "read"}', '{"operation": "grant_permission"}', '2026-01-09T05:53:51.828754');
INSERT INTO corpus_audit_log ("corpus_id", "user_id", "action", "changes", "metadata", "timestamp") VALUES (8, 2, 'revoked_access', '{"group_id": 2}', '{"operation": "revoke_permission"}', '2026-01-09T05:53:54.151794');
INSERT INTO corpus_audit_log ("corpus_id", "user_id", "action", "changes", "metadata", "timestamp") VALUES (NULL, 2, 'created_user', '{"new_user_id": 5, "username": "testuser", "groups": []}', '{"operation": "user_create"}', '2026-01-09T06:38:04.374833');
INSERT INTO corpus_audit_log ("corpus_id", "user_id", "action", "changes", "metadata", "timestamp") VALUES (9, 2, 'updated', '{"before": {"id": 6, "corpus_id": 9, "created_by": 2, "created_at": "2026-01-09T05:21:30.041852", "last_synced_at": null, "last_synced_by": null, "document_count": 0, "last_document_count_update": null, "sync_status": "active", "sync_error_message": null, "tags": "semantic, web, html", "notes": "", "created_by_name": "alice", "last_synced_by_name": null}, "after": {"id": 6, "corpus_id": 9, "created_by": 2, "created_at": "2026-01-09T05:21:30.041852", "last_synced_at": null, "last_synced_by": null, "document_count": 0, "last_document_count_update": null, "sync_status": "active", "sync_error_message": null, "tags": "semantic, web, html", "notes": "", "created_by_name": "alice", "last_synced_by_name": null}, "fields": ["tags", "notes"]}', '{"operation": "update_metadata"}', '2026-01-09T07:11:51.003527');
INSERT INTO corpus_audit_log ("corpus_id", "user_id", "action", "changes", "metadata", "timestamp") VALUES (NULL, 1, 'deleted_user', '{"target_user_id": 5, "username": "testuser"}', '{"operation": "user_delete"}', '2026-01-09T23:04:58.606942');
INSERT INTO corpus_audit_log ("corpus_id", "user_id", "action", "changes", "metadata", "timestamp") VALUES (NULL, 1, 'deleted_user', '{"target_user_id": 5, "username": "testuser"}', '{"operation": "user_delete"}', '2026-01-09T23:05:10.458779');
INSERT INTO corpus_audit_log ("corpus_id", "user_id", "action", "changes", "metadata", "timestamp") VALUES (NULL, 1, 'created_user', '{"new_user_id": 6, "username": "andrew", "groups": [2]}', '{"operation": "user_create"}', '2026-01-10T20:12:00.153817');

-- Table: user_sessions
INSERT INTO user_sessions ("session_id", "user_id", "active_agent_id", "active_corpora", "created_at", "last_activity", "expires_at", "is_active", "message_count", "user_query_count") VALUES ('8ed85514-1227-4f14-abfb-9b4693810e12', 2, 1, NULL, '2026-01-09T22:50:01.801117+00:00', '2026-01-09T22:50:01.801117+00:00', '2026-01-10T22:50:01.801131+00:00', TRUE, 0, 0);
INSERT INTO user_sessions ("session_id", "user_id", "active_agent_id", "active_corpora", "created_at", "last_activity", "expires_at", "is_active", "message_count", "user_query_count") VALUES ('5b2878b9-59bd-4631-8dea-0d0b4be7e314', 1, 1, NULL, '2026-01-09T23:00:23.362922+00:00', '2026-01-09T23:00:23.362922+00:00', '2026-01-10T23:00:23.362941+00:00', TRUE, 0, 0);
INSERT INTO user_sessions ("session_id", "user_id", "active_agent_id", "active_corpora", "created_at", "last_activity", "expires_at", "is_active", "message_count", "user_query_count") VALUES ('a395ec49-9b19-4f63-b7af-a6a6c7e8ef1c', 1, 1, NULL, '2026-01-09T23:05:43.888406+00:00', '2026-01-09T23:05:43.888406+00:00', '2026-01-10T23:05:43.888423+00:00', TRUE, 0, 0);
INSERT INTO user_sessions ("session_id", "user_id", "active_agent_id", "active_corpora", "created_at", "last_activity", "expires_at", "is_active", "message_count", "user_query_count") VALUES ('3d58981d-e2fc-4363-8ef6-7a8944432403', 1, 1, NULL, '2026-01-09T23:06:11.212189+00:00', '2026-01-09T23:06:11.212189+00:00', '2026-01-10T23:06:11.212203+00:00', TRUE, 0, 0);
INSERT INTO user_sessions ("session_id", "user_id", "active_agent_id", "active_corpora", "created_at", "last_activity", "expires_at", "is_active", "message_count", "user_query_count") VALUES ('07b18a22-8aea-4bec-ac44-769598396329', 2, 1, NULL, '2026-01-09T23:14:30.337640+00:00', '2026-01-09T23:14:30.337640+00:00', '2026-01-10T23:14:30.337662+00:00', TRUE, 0, 0);
INSERT INTO user_sessions ("session_id", "user_id", "active_agent_id", "active_corpora", "created_at", "last_activity", "expires_at", "is_active", "message_count", "user_query_count") VALUES ('7bd49b22-d12a-4642-ab72-879ee1b90a78', 1, 1, NULL, '2026-01-09T23:15:01.690760+00:00', '2026-01-09T23:15:01.690760+00:00', '2026-01-10T23:15:01.690776+00:00', TRUE, 0, 0);
INSERT INTO user_sessions ("session_id", "user_id", "active_agent_id", "active_corpora", "created_at", "last_activity", "expires_at", "is_active", "message_count", "user_query_count") VALUES ('58983816-cf43-49fa-807c-6cfb54334893', 1, 1, NULL, '2026-01-10T00:37:37.526356+00:00', '2026-01-10T00:37:37.526356+00:00', '2026-01-11T00:37:37.526370+00:00', TRUE, 0, 0);
INSERT INTO user_sessions ("session_id", "user_id", "active_agent_id", "active_corpora", "created_at", "last_activity", "expires_at", "is_active", "message_count", "user_query_count") VALUES ('16c3faaa-9341-4fc5-8451-53f210291aa6', 1, 1, NULL, '2026-01-10T00:39:45.755796+00:00', '2026-01-10T00:39:45.755796+00:00', '2026-01-11T00:39:45.755807+00:00', TRUE, 0, 0);
INSERT INTO user_sessions ("session_id", "user_id", "active_agent_id", "active_corpora", "created_at", "last_activity", "expires_at", "is_active", "message_count", "user_query_count") VALUES ('d521ebc1-648c-4f00-8eef-e38165c5a770', 1, 1, NULL, '2026-01-10T00:47:09.422202+00:00', '2026-01-10T00:47:09.422202+00:00', '2026-01-11T00:47:09.422214+00:00', TRUE, 0, 0);
INSERT INTO user_sessions ("session_id", "user_id", "active_agent_id", "active_corpora", "created_at", "last_activity", "expires_at", "is_active", "message_count", "user_query_count") VALUES ('fd0699fd-9486-4814-9669-15053738b870', 1, 1, NULL, '2026-01-10T02:02:13.649988+00:00', '2026-01-10T02:02:16.601252+00:00', '2026-01-11T02:02:13.649997+00:00', TRUE, 2, 0);
INSERT INTO user_sessions ("session_id", "user_id", "active_agent_id", "active_corpora", "created_at", "last_activity", "expires_at", "is_active", "message_count", "user_query_count") VALUES ('913a3eb3-2658-4a10-8a64-c7d2b5ccf600', 1, 1, NULL, '2026-01-10T02:03:55.337956+00:00', '2026-01-10T02:03:56.608582+00:00', '2026-01-11T02:03:55.337969+00:00', TRUE, 2, 0);
INSERT INTO user_sessions ("session_id", "user_id", "active_agent_id", "active_corpora", "created_at", "last_activity", "expires_at", "is_active", "message_count", "user_query_count") VALUES ('14579683-2c46-48bb-ae11-b8bc06234e46', 1, 1, NULL, '2026-01-10T02:17:56.549248+00:00', '2026-01-10T02:18:26.973107+00:00', '2026-01-11T02:17:56.549259+00:00', TRUE, 6, 0);
INSERT INTO user_sessions ("session_id", "user_id", "active_agent_id", "active_corpora", "created_at", "last_activity", "expires_at", "is_active", "message_count", "user_query_count") VALUES ('c0d65c25-a52f-4924-ba97-751e25ab9c28', 1, 1, NULL, '2026-01-10T19:03:23.082583+00:00', '2026-01-10T19:12:15.780614+00:00', '2026-01-11T19:03:23.082593+00:00', TRUE, 6, 3);
INSERT INTO user_sessions ("session_id", "user_id", "active_agent_id", "active_corpora", "created_at", "last_activity", "expires_at", "is_active", "message_count", "user_query_count") VALUES ('e571a015-d69c-4481-808a-219dd6337211', 1, 1, NULL, '2026-01-10T19:12:55.841529+00:00', '2026-01-10T19:13:04.802858+00:00', '2026-01-11T19:12:55.841543+00:00', TRUE, 2, 1);
INSERT INTO user_sessions ("session_id", "user_id", "active_agent_id", "active_corpora", "created_at", "last_activity", "expires_at", "is_active", "message_count", "user_query_count") VALUES ('5ce72ed1-b746-41cf-b9fb-c03a8c43e2e8', 1, 1, NULL, '2026-01-10T20:05:40.626172+00:00', '2026-01-10T20:41:12.613419+00:00', '2026-01-11T20:05:40.626190+00:00', TRUE, 4, 2);

-- Table: schema_migrations
INSERT INTO schema_migrations ("id", "migration_name", "applied_at") VALUES (1, '001_initial_schema.sql', '2025-12-31 23:36:50');
INSERT INTO schema_migrations ("id", "migration_name", "applied_at") VALUES (2, '002_add_groups_roles.sql', '2025-12-31 23:36:50');
INSERT INTO schema_migrations ("id", "migration_name", "applied_at") VALUES (3, '003_add_agents_corpora.sql', '2025-12-31 23:36:50');
INSERT INTO schema_migrations ("id", "migration_name", "applied_at") VALUES (4, '004_add_admin_tables.sql', '2026-01-10 01:55:32');
INSERT INTO schema_migrations ("id", "migration_name", "applied_at") VALUES (5, '005_add_user_query_count.sql', '2026-01-10 02:12:01');

-- Reset sequences
SELECT setval('users_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM users), false);
SELECT setval('user_profiles_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM user_profiles), false);
SELECT setval('groups_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM groups), false);
SELECT setval('roles_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM roles), false);
SELECT setval('user_groups_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM user_groups), false);
SELECT setval('group_roles_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM group_roles), false);
SELECT setval('agents_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM agents), false);
SELECT setval('corpora_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM corpora), false);
SELECT setval('user_agent_access_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM user_agent_access), false);
SELECT setval('group_corpus_access_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM group_corpus_access), false);
SELECT setval('corpus_metadata_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM corpus_metadata), false);
SELECT setval('corpus_audit_log_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM corpus_audit_log), false);
SELECT setval('corpus_sync_schedule_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM corpus_sync_schedule), false);
SELECT setval('user_sessions_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM user_sessions), false);
SELECT setval('session_corpus_selections_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM session_corpus_selections), false);
