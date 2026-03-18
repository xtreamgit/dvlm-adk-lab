# Schema Migration Guide: Roles → Agent Types

## Overview

This migration refactors the database schema from "roles" and "permissions" terminology to "agent types" and "tools" terminology to better reflect the actual purpose of these entities in the application.

## Migration Details

### Tables Renamed

| Old Name | New Name | Purpose |
|----------|----------|---------|
| `chatbot_roles` | `chatbot_agent_types` | Defines types of agents (viewer, contributor, power-user, admin) |
| `chatbot_permissions` | `chatbot_tools` | Defines tools that agents can use (rag_query, document_upload, etc.) |
| `chatbot_role_permissions` | `chatbot_agent_type_tools` | Links agent types to their available tools |
| `chatbot_group_roles` | `chatbot_group_agent_types` | Assigns agent types to chatbot groups |

### Columns Renamed

| Table | Old Column | New Column |
|-------|------------|------------|
| `chatbot_agent_type_tools` | `role_id` | `agent_type_id` |
| `chatbot_agent_type_tools` | `permission_id` | `tool_id` |
| `chatbot_group_agent_types` | `chatbot_role_id` | `chatbot_agent_type_id` |

### Indexes Renamed

All indexes have been renamed to match the new table and column names.

### Sequences Renamed

All sequences have been renamed to match the new table names.

## Safety Features

✅ **Non-Destructive**: All data is preserved during migration  
✅ **Automatic FK Updates**: PostgreSQL automatically updates foreign key constraints  
✅ **Transactional**: Migration runs in a transaction (can be rolled back)  
✅ **Rollback Script**: Full rollback script provided for safety  
✅ **Backup Created**: Database backup created before migration  

## Execution Steps

### 1. Pre-Migration Checklist

- [x] Database backup created: `backup_adk_agents_db_dev_20260204_163932.sql.gz`
- [x] Checkpoint commit created: `c869ad1`
- [x] Migration script created: `010_rename_roles_to_agent_types.sql`
- [x] Rollback script created: `010_rollback_agent_types_to_roles.sql`
- [ ] Docker container running: `adk-postgres-dev`

### 2. Execute Migration

```bash
cd backend
./run_schema_migration.sh
```

This will:
1. Confirm you want to proceed
2. Execute the migration SQL script
3. Display success/failure message
4. Show next steps

### 3. Post-Migration Tasks

After successful migration, you need to update the codebase:

#### Backend Updates Required:

1. **API Routes** (`src/api/routes/chatbot_admin.py`)
   - Update table names in SQL queries
   - Update column names in SQL queries
   - Update response field names

2. **Database Models** (if any ORM models exist)
   - Update model class names
   - Update field names
   - Update relationship names

3. **Service Layer** (if any service files reference these tables)
   - Update method names
   - Update variable names

#### Frontend Updates Required:

1. **TypeScript Types**
   - Rename `ChatbotRole` → `ChatbotAgentType`
   - Rename `Permission` → `Tool`
   - Update field names in interfaces

2. **API Calls**
   - Update endpoint paths (if needed)
   - Update request/response field names

3. **UI Components**
   - Update display labels
   - Update variable names

### 4. Testing

After code updates:

1. Restart backend server
2. Test agent type management (CRUD operations)
3. Test tool assignment to agent types
4. Test group assignment to agent types
5. Test chatbot user authentication and permissions

## Rollback Procedure

If you need to revert the migration:

```bash
cd backend
./rollback_schema_migration.sh
```

**Warning**: Type `ROLLBACK` to confirm. This will revert all schema changes.

After rollback:
1. Revert any code changes made
2. Restart backend server
3. Test the application

## Migration Files

- **Migration**: `src/database/migrations/010_rename_roles_to_agent_types.sql`
- **Rollback**: `src/database/migrations/010_rollback_agent_types_to_roles.sql`
- **Execute Script**: `run_schema_migration.sh`
- **Rollback Script**: `rollback_schema_migration.sh`
- **Backup**: `database_backups/backup_adk_agents_db_dev_20260204_163932.sql.gz`

## Verification Queries

After migration, verify the changes:

```sql
-- List all tables with 'chatbot' prefix
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE 'chatbot%'
ORDER BY table_name;

-- Check chatbot_agent_types table
SELECT * FROM chatbot_agent_types;

-- Check chatbot_tools table
SELECT * FROM chatbot_tools;

-- Check relationships
SELECT 
    at.name as agent_type,
    t.name as tool
FROM chatbot_agent_type_tools att
JOIN chatbot_agent_types at ON att.agent_type_id = at.id
JOIN chatbot_tools t ON att.tool_id = t.id
ORDER BY at.name, t.name;
```

## Troubleshooting

### Migration Fails

1. Check error message in terminal
2. Verify Docker container is running
3. Check database connection
4. Review migration SQL for syntax errors
5. Rollback and try again

### Code Doesn't Work After Migration

1. Verify all table names updated in code
2. Verify all column names updated in code
3. Check for hardcoded table/column names
4. Restart backend server
5. Clear browser cache

### Need to Revert

1. Run rollback script: `./rollback_schema_migration.sh`
2. Revert code changes via git
3. Restart backend server

## Support

If you encounter issues:

1. Check the backup: `database_backups/latest_backup.sql.gz`
2. Review git history: `git log --oneline`
3. Check checkpoint commit: `c869ad1`
4. Restore from backup if needed

## Timeline

- **Backup Created**: 2026-02-04 16:39:32
- **Checkpoint Commit**: c869ad1
- **Migration Created**: 2026-02-04 (pending execution)
- **Migration Executed**: (pending)
- **Code Updated**: (pending)
- **Testing Complete**: (pending)
