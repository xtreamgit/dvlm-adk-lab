# Database Sync Guide

## Overview

This guide explains how to keep your local development database in sync with the cloud production database. This is essential for consistent development, especially for the **Permission Matrix** which manages group access to corpora.

## The Problem

Your local PostgreSQL database and cloud Cloud SQL database can drift apart:
- Different groups
- Different corpora  
- Different permission assignments (Permission Matrix)
- Different user-group memberships

This causes confusion when the Admin Panel shows different data locally vs in production.

## The Solution

Use the `sync_database_data.py` script to synchronize data between environments.

---

## Prerequisites

### 1. Local PostgreSQL Running

```bash
# Check if local PostgreSQL is running
docker ps | grep postgres

# If not running, start it
cd backend
docker-compose up -d postgres
```

### 2. Cloud SQL Proxy (for cloud access)

```bash
# Install Cloud SQL Proxy
brew install cloud-sql-proxy

# Start proxy in a separate terminal
cloud-sql-proxy adk-rag-ma:us-west1:adk-multi-agents-db \
  --port 5432 \
  --credentials-file=/Users/hector/github.com/xtreamgit/adk-multi-agents/backend/backend-sa-key.json
```

This makes the cloud database accessible at `localhost:5432`.

### 3. Set Environment Variables

```bash
# Local database (already in .env.local)
export DB_HOST=localhost
export DB_PORT=5433
export DB_NAME=adk_agents_db_dev
export DB_USER=adk_dev_user
export DB_PASSWORD=dev_password_123

# Cloud database (via proxy)
export CLOUD_DB_HOST=127.0.0.1
export CLOUD_DB_PORT=5432
export CLOUD_DB_NAME=adk_agents_db
export CLOUD_DB_USER=adk_app_user
export CLOUD_DB_PASSWORD=your_cloud_password  # Get from gcloud secrets
```

To get cloud password:
```bash
gcloud secrets versions access latest --secret=db-password --project=adk-rag-ma
```

---

## Usage

### Recommended: Sync Cloud → Local

This is the **safest** approach for local development. It pulls production data to your local environment:

```bash
cd backend

# DRY RUN - see what would change without making changes
python sync_database_data.py --from-cloud --dry-run

# ACTUAL SYNC - apply changes to local database
python sync_database_data.py --from-cloud
```

**What this syncs:**
- ✅ Groups (admin-users, default-users, etc.)
- ✅ Corpora (ai-books, design, management, etc.)
- ✅ **Permission Matrix** (group → corpus access)
- ✅ Active/inactive status

**What this does NOT sync:**
- ❌ Users (for security - passwords stay separate)
- ❌ Chat history
- ❌ Sessions
- ❌ Audit logs

### Advanced: Sync Local → Cloud

⚠️ **USE WITH CAUTION** - This modifies production data!

```bash
# DRY RUN first (always!)
python sync_database_data.py --to-cloud --dry-run

# ACTUAL SYNC (will prompt for confirmation)
python sync_database_data.py --to-cloud
```

---

## Common Workflows

### Workflow 1: Fresh Local Development Setup

When starting development on a new machine or after resetting local database:

```bash
# 1. Start local PostgreSQL
docker-compose up -d postgres

# 2. Initialize schema
psql -h localhost -p 5433 -U adk_dev_user -d adk_agents_db_dev -f init_postgresql_schema.sql

# 3. Start Cloud SQL Proxy (separate terminal)
cloud-sql-proxy adk-rag-ma:us-west1:adk-multi-agents-db --port 5432

# 4. Sync data from cloud
python sync_database_data.py --from-cloud

# 5. Done! Your local DB now matches production
```

### Workflow 2: Permission Matrix Changes in Cloud

When permissions change in production (e.g., new group gets access to a corpus):

```bash
# Pull latest permissions to local
python sync_database_data.py --from-cloud

# Now your local Permission Matrix matches production
```

### Workflow 3: Testing New Permissions Locally

When you want to test permission changes locally before deploying:

```bash
# 1. Make changes in local database (via Admin Panel at localhost:3000/admin)
# 2. Test locally
# 3. If satisfied, sync to cloud:
python sync_database_data.py --to-cloud --dry-run  # Review first
python sync_database_data.py --to-cloud            # Apply if OK
```

### Workflow 4: Weekly Sync (Recommended)

Keep local and cloud in sync weekly:

```bash
# Every Monday morning:
cd backend
python sync_database_data.py --from-cloud

# This ensures your local dev environment stays current
```

---

## Troubleshooting

### Error: "Failed to connect to local database"

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check connection manually
psql -h localhost -p 5433 -U adk_dev_user -d adk_agents_db_dev
```

### Error: "Failed to connect to cloud database"

```bash
# Ensure Cloud SQL Proxy is running
lsof -i :5432

# Check proxy logs for errors
# Restart proxy if needed
```

### Error: "Password authentication failed"

```bash
# For cloud database, get password from Secret Manager:
gcloud secrets versions access latest --secret=db-password --project=adk-rag-ma

# Export it:
export CLOUD_DB_PASSWORD="the_password_here"
```

### Sync shows unexpected differences

This is normal! Common causes:
- New corpus added via Vertex AI console
- Permissions changed by another admin in production
- Groups added/removed

**Solution:** Review the dry-run output carefully before syncing.

---

## Understanding the Output

### Dry Run Example

```bash
$ python sync_database_data.py --from-cloud --dry-run

==================================================
Syncing Groups
==================================================

ℹ️  Source groups: 8
ℹ️  Destination groups: 6
⚠️  Would add 2 groups: developers, viewers

==================================================
Syncing Corpora
==================================================

ℹ️  Source corpora: 6
ℹ️  Destination corpora: 4
⚠️  Would add 2 corpora: recipes, semantic-web

==================================================
Syncing Permission Matrix
==================================================

ℹ️  Source permissions: 24
ℹ️  Destination permissions: 16
⚠️  Would add 8 permissions
    + developers -> ai-books (read)
    + developers -> design (read)
    ...
```

This shows:
- 2 new groups exist in cloud but not local
- 2 new corpora exist in cloud but not local
- 8 permission assignments would be added

### Actual Sync Example

```bash
$ python sync_database_data.py --from-cloud

==================================================
Syncing Groups
==================================================

✅ Added/Updated: developers
✅ Added/Updated: viewers
✅ Groups synced

==================================================
Permission Matrix synced
==================================================

✅ Added: developers -> ai-books (read)
✅ Added: viewers -> ai-books (read)
...

✅ ✨ Local database synced with cloud!
```

---

## Best Practices

1. **Always use --dry-run first** to preview changes
2. **Sync FROM cloud TO local** for daily development
3. **Backup before syncing TO cloud** (script doesn't backup automatically)
4. **Document permission changes** before syncing to cloud
5. **Run sync after deploying schema changes** to keep data consistent

---

## Alternative: Manual Sync via SQL

If you prefer manual control:

### Export cloud permissions:
```bash
gcloud sql connect adk-multi-agents-db --database=adk_agents_db --user=adk_app_user <<EOF
COPY (
  SELECT g.name as group_name, c.name as corpus_name, gca.permission
  FROM group_corpus_access gca
  JOIN groups g ON gca.group_id = g.id
  JOIN corpora c ON gca.corpus_id = c.id
) TO STDOUT WITH CSV HEADER;
EOF > cloud_permissions.csv
```

### Import to local:
```bash
# (Requires custom SQL script to map group/corpus names to IDs)
```

But the Python script is **much easier**! 😊

---

## Related Scripts

- `sync_corpora_from_vertex.py` - Syncs corpus **definitions** from Vertex AI
- `sync_database_schemas.sh` - Syncs database **schema** (table structure)
- `sync_database_data.py` - Syncs database **data** (this guide)

Use all three for complete synchronization!

---

## Quick Reference

```bash
# See what would change (safe)
python sync_database_data.py --from-cloud --dry-run

# Sync cloud → local (recommended for dev)
python sync_database_data.py --from-cloud

# Sync local → cloud (use with caution)
python sync_database_data.py --to-cloud --dry-run  # Review first!
python sync_database_data.py --to-cloud            # Apply
```

---

## Questions?

Check the script source code for implementation details:
- `backend/sync_database_data.py`

Or run with `--help`:
```bash
python sync_database_data.py --help
```
