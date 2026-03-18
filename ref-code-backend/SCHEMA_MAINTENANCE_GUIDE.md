# Cloud SQL Schema Maintenance Guide

**Purpose:** Ensure Cloud SQL schema stays in sync with application code and migrations.

---

## ✅ Schema Verification Checklist

Use this checklist regularly (especially after deployments):

### 1. Verify All Migrations Applied

```bash
cd backend
./verify_migrations_complete.sh
```

**Expected output:**
- ✅ All columns from migrations exist
- ✅ All indexes from migrations exist
- ✅ Full table structure matches expectations

---

### 2. Check Schema Migrations Table

```sql
SELECT id, migration_name, applied_at 
FROM schema_migrations 
ORDER BY id;
```

**Compare with:** Files in `backend/src/database/migrations/`

**Look for:**
- Missing migrations (gaps in sequence)
- Migrations applied out of order
- Unapplied recent migrations

---

### 3. Compare with Base Schema

When adding new migrations, also update:
- `backend/init_postgresql_schema.sql` (base schema file)

**Rule:** Base schema should reflect the state AFTER all migrations are applied.

---

## 🔧 How to Apply Missing Migrations

### Option A: Via Cloud Console SQL Editor
1. Go to: https://console.cloud.google.com/sql/instances/adk-multi-agents-db
2. Click "OPEN CLOUD SHELL"
3. Connect: `gcloud sql connect adk-multi-agents-db --user=adk_app_user --database=adk_agents_db`
4. Paste migration SQL
5. Verify with `\d table_name`

### Option B: Via Local Terminal (with timeout issues)
```bash
cat backend/src/database/migrations/XXX_migration.sql | \
  gcloud sql connect adk-multi-agents-db \
  --user=adk_app_user \
  --database=adk_agents_db \
  --project=adk-rag-ma
```

### Option C: Via Backend Migration Runner (Future)
```bash
# TODO: Implement automated migration runner
python backend/src/database/migrations/run_migrations.py --target=cloud
```

---

## 📋 Migration Tracking System

### Current State (as of Jan 23, 2026)

**Migrations Applied to Cloud SQL:**
- ✅ 001_initial_schema.sql
- ✅ 002_add_groups_roles.sql
- ✅ 003_add_agents_corpora.sql
- ✅ 004_add_admin_tables.sql (from Jan 10)
- ⚠️ 004_add_message_count.sql (manually applied Jan 23)
- ⚠️ 005_add_user_query_count.sql (partially applied Jan 23 - column only)
- ❓ 006_add_iap_support.sql (status unknown)
- ❓ 007-010 (newer migrations - status unknown)

**Action Required:**
1. Complete migration 005 (add index)
2. Verify migrations 006-010 status
3. Apply any missing migrations
4. Update schema_migrations table with applied migrations

---

## 🚨 Common Schema Drift Issues

### Issue 1: Code Expects Column That Doesn't Exist
**Symptoms:** 500 errors like "column X does not exist"  
**Cause:** Migration not applied to Cloud SQL  
**Fix:** Apply the specific migration

### Issue 2: Performance Degradation
**Symptoms:** Slow queries on large tables  
**Cause:** Missing indexes from migrations  
**Fix:** Verify and create missing indexes

### Issue 3: Base Schema Out of Date
**Symptoms:** New deployments/instances missing recent schema changes  
**Cause:** `init_postgresql_schema.sql` not updated  
**Fix:** Keep base schema in sync with migrations

---

## 🔄 Process for Adding New Migrations

When creating a new migration:

1. **Create migration file:**
   ```sql
   -- backend/src/database/migrations/011_new_feature.sql
   ALTER TABLE some_table ADD COLUMN new_column TYPE;
   CREATE INDEX IF NOT EXISTS idx_name ON some_table(new_column);
   ```

2. **Test locally first:**
   ```bash
   psql -d adk_agents_db_dev -f backend/src/database/migrations/011_new_feature.sql
   ```

3. **Update base schema:**
   Edit `backend/init_postgresql_schema.sql` to include changes

4. **Apply to Cloud SQL:**
   ```bash
   cat backend/src/database/migrations/011_new_feature.sql | \
     gcloud sql connect adk-multi-agents-db --user=adk_app_user --database=adk_agents_db
   ```

5. **Record in schema_migrations:**
   ```sql
   INSERT INTO schema_migrations (migration_name, applied_at) 
   VALUES ('011_new_feature.sql', CURRENT_TIMESTAMP);
   ```

6. **Commit all changes:**
   - Migration file
   - Updated base schema
   - Documentation update

---

## 📊 Quick Schema Verification Commands

### Check specific table structure:
```sql
\d user_sessions
```

### List all indexes on a table:
```sql
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'user_sessions';
```

### Find missing columns:
```sql
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'your_table'
ORDER BY ordinal_position;
```

### Check table sizes:
```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## 🎯 Best Practices

1. **Always test migrations locally first**
2. **Keep base schema file in sync with migrations**
3. **Document breaking changes clearly**
4. **Use `IF NOT EXISTS` for idempotent migrations**
5. **Track applied migrations in schema_migrations table**
6. **Verify schema after every deployment**
7. **Create indexes for frequently queried columns**
8. **Add foreign keys for referential integrity**

---

## 📞 Troubleshooting

### "Operation timed out" when connecting
- Try Cloud Console SQL Editor instead
- Check if your IP is allowlisted
- Verify Cloud SQL instance is running

### "Password authentication failed"
- Check Secret Manager for correct password
- Verify user exists: `SELECT usename FROM pg_user;`
- Ensure user has proper grants

### "Migration already applied" error
- Check schema_migrations table
- Use `IF NOT EXISTS` clauses
- Verify idempotency of migration

---

**Last Updated:** January 23, 2026  
**Maintained By:** Development Team  
**Reference:** `cascade-logs/2026-01-23/SCHEMA_DRIFT_ANALYSIS.md`
