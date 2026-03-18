# Chat UI Fix - Apply Database Migration

## Problem
Chat UI fails with CORS 500 error due to missing columns in `user_sessions` table:
- `message_count`
- `user_query_count`

## Solution
Add the missing columns to the Cloud SQL database.

---

## Option 1: Via Google Cloud Console (Recommended - Fastest)

1. **Open Cloud SQL Console:**
   - Go to: https://console.cloud.google.com/sql/instances/adk-multi-agents-db/overview?project=adk-rag-ma
   
2. **Open SQL Editor:**
   - Click "OPEN CLOUD SHELL" (top right)
   - Or click the Cloud Shell icon in the top navigation bar

3. **Connect to database:**
   ```bash
   gcloud sql connect adk-multi-agents-db --user=adk_app_user --database=adk_agents_db --project=adk-rag-ma
   ```
   - When prompted for password, enter the `adk_app_user` password from Secret Manager

4. **Run this SQL:**
   ```sql
   ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS message_count INTEGER DEFAULT 0;
   ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS user_query_count INTEGER DEFAULT 0;
   ```

5. **Verify:**
   ```sql
   \d user_sessions
   ```
   - Should show both new columns

6. **Exit:**
   ```sql
   \q
   ```

---

## Option 2: Via SQL from Cloud Shell

Just run these commands in Cloud Shell:

```bash
cat <<'EOF' | gcloud sql connect adk-multi-agents-db --user=adk_app_user --database=adk_agents_db --project=adk-rag-ma
ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS message_count INTEGER DEFAULT 0;
ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS user_query_count INTEGER DEFAULT 0;
SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'user_sessions' AND column_name IN ('message_count', 'user_query_count');
\q
EOF
```

---

## After applying the fix:

Test the chat UI:
1. Go to https://34.49.46.115.nip.io
2. Try to enter a query in the chat field
3. Should work without CORS errors

The migration file is saved at:
`backend/migrations/004_add_session_counters.sql`
