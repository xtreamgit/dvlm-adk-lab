# Database Migrations

This directory contains SQL migration scripts for the database schema.

## Migration Files

- `001_initial_schema.sql` - Initial users table with enhancements
- `002_add_groups_roles.sql` - Groups, roles, and user-group relationships
- `003_add_agents_corpora.sql` - Agents, corpora, and access control

## Running Migrations

### Manual Execution

```bash
# From backend directory
cd backend

# Run all migrations in order
sqlite3 /app/data/users.db < src/database/migrations/001_initial_schema.sql
sqlite3 /app/data/users.db < src/database/migrations/002_add_groups_roles.sql
sqlite3 /app/data/users.db < src/database/migrations/003_add_agents_corpora.sql
```

### Automated Migration

```bash
# Use the migration runner script
python src/database/migrations/run_migrations.py
```

## Migration Strategy

1. **Non-destructive**: All migrations use `IF NOT EXISTS` to avoid breaking existing data
2. **Idempotent**: Safe to run multiple times
3. **Ordered**: Must be run in numerical order (001, 002, 003...)
4. **Backward Compatible**: Existing code continues to work during migration

## Development vs Production

### Development (SQLite)
- Migrations run against local SQLite database
- Fast iteration and testing
- File: `/app/data/users.db` (in container) or `backend/users.db` (local)

### Production (Cloud SQL - Future)
- Will use PostgreSQL instead of SQLite
- Better JSON support with native JSONB type
- Better concurrent access and performance
- Migration scripts will need PostgreSQL equivalents

## Notes

- SQLite stores JSON as TEXT - we parse it in the application layer
- Foreign key constraints are enforced if `PRAGMA foreign_keys = ON`
- Indexes are created for all common query patterns
