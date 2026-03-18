# Backend Scripts

This directory contains utility scripts for database setup, seeding, and user management.

## Setup Scripts

### 1. Run Database Migrations

```bash
cd backend
python src/database/migrations/run_migrations.py
```

This creates all necessary database tables.

### 2. Seed Agents

```bash
cd backend
python scripts/seed_agents.py
```

Creates initial agent entries based on existing config folders:
- default-agent (develom)
- agent1
- agent2
- agent3
- tt-agent
- usfs-agent

### 3. Seed Default Data

```bash
cd backend
python scripts/seed_default_group.py
```

Creates:
- **Groups**: default-users, admin-users, develom-group
- **Roles**: user, corpus_admin, system_admin
- **Corpora**: develom-general, ai-books
- Assigns roles to groups
- Grants corpus access to groups

### 4. Create Admin User

```bash
cd backend
python scripts/create_admin_user.py
```

Interactive script that:
- Creates a new admin user
- Adds user to admin-users and default-users groups
- Grants access to all agents
- Sets default-agent as default

**Non-interactive mode:**
```bash
python scripts/create_admin_user.py --username admin --email admin@example.com
# Password will be prompted
```

## Complete Setup Flow

```bash
# 1. Run migrations
python src/database/migrations/run_migrations.py

# 2. Seed agents
python scripts/seed_agents.py

# 3. Seed default data (groups, roles, corpora)
python scripts/seed_default_group.py

# 4. Create admin user
python scripts/create_admin_user.py
```

## Testing the Setup

```python
# Test user authentication
from services import AuthService, UserService

# Authenticate user
user = AuthService.authenticate_user("admin", "your_password")
print(f"Authenticated: {user.username}")

# Get user agents
from services import AgentService
agents = AgentService.get_user_agents(user.id)
print(f"User has access to {len(agents)} agents")

# Get user corpora
from services import CorpusService
corpora = CorpusService.get_user_corpora(user.id)
print(f"User has access to {len(corpora)} corpora")
```

## Environment Variables

These scripts use the following environment variables:

- `DATABASE_PATH` - Path to SQLite database (default: `/app/data/users.db`)
- `SECRET_KEY` - JWT secret key
- `ACCESS_TOKEN_EXPIRE_DAYS` - Token expiration (default: 30)

## Notes

- All scripts are idempotent - safe to run multiple times
- Existing records are skipped, not overwritten
- Scripts must be run from the `backend` directory
- Migrations run automatically before seeding
