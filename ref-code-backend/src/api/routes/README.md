# API Routes Documentation

This directory contains the modular API route implementations for the multi-agent RAG system.

## Route Modules

### 1. Authentication Routes (`auth.py`)
**Prefix:** `/api/auth`  
**Tag:** Authentication

#### Endpoints
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `POST /api/auth/logout` - Logout (audit logging)
- `POST /api/auth/refresh` - Refresh JWT token
- `GET /api/auth/me` - Get current user info

---

### 2. User Routes (`users.py`)
**Prefix:** `/api/users`  
**Tag:** Users

#### Endpoints
- `GET /api/users/me` - Get profile with preferences
- `PUT /api/users/me` - Update user information
- `GET /api/users/me/preferences` - Get user preferences
- `PUT /api/users/me/preferences` - Update preferences
- `PUT /api/users/me/default-agent/{agent_id}` - Set default agent
- `GET /api/users/me/groups` - Get user's groups
- `GET /api/users/me/roles` - Get user's roles

---

### 3. Group Routes (`groups.py`)
**Prefix:** `/api/groups`  
**Tag:** Groups & Roles

#### Group Endpoints
- `GET /api/groups/me` - Get current user's groups
- `GET /api/groups/` - List all groups (admin)
- `GET /api/groups/{group_id}` - Get group details (admin)
- `POST /api/groups/` - Create group (admin)
- `PUT /api/groups/{group_id}` - Update group (admin)
- `PUT /api/groups/{group_id}/users/{user_id}` - Add user to group (admin)
- `DELETE /api/groups/{group_id}/users/{user_id}` - Remove user from group (admin)

#### Role Endpoints
- `GET /api/groups/roles/` - List all roles (admin)
- `GET /api/groups/roles/{role_id}` - Get role details (admin)
- `POST /api/groups/roles/` - Create role (admin)
- `PUT /api/groups/{group_id}/roles/{role_id}` - Assign role to group (admin)
- `DELETE /api/groups/{group_id}/roles/{role_id}` - Remove role from group (admin)
- `GET /api/groups/{group_id}/roles` - Get group's roles

**Required Permissions:**
- `manage:groups` - Manage groups and users
- `manage:roles` - Manage roles

---

### 4. Agent Routes (`agents.py`)
**Prefix:** `/api/agents`  
**Tag:** Agents

#### Endpoints
- `GET /api/agents/` - List all agents
- `GET /api/agents/me` - Get agents user has access to
- `GET /api/agents/default` - Get user's default agent
- `GET /api/agents/{agent_id}` - Get agent details
- `POST /api/agents/` - Create agent (admin)
- `PUT /api/agents/{agent_id}/activate` - Activate agent (admin)
- `PUT /api/agents/{agent_id}/deactivate` - Deactivate agent (admin)
- `PUT /api/agents/{agent_id}/grant/{user_id}` - Grant user access (admin)
- `DELETE /api/agents/{agent_id}/revoke/{user_id}` - Revoke user access (admin)
- `POST /api/agents/sessions/{session_id}/switch/{agent_id}` - Switch session agent

**Required Permissions:**
- `manage:agents` - Create/update agents
- `manage:agent_access` - Grant/revoke access

---

### 5. Corpus Routes (`corpora.py`)
**Prefix:** `/api/corpora`  
**Tag:** Corpora

#### Endpoints
- `GET /api/corpora/` - Get corpora user has access to
- `GET /api/corpora/all` - List all corpora (admin)
- `GET /api/corpora/{corpus_id}` - Get corpus details
- `POST /api/corpora/` - Create corpus (admin)
- `PUT /api/corpora/{corpus_id}` - Update corpus (admin)
- `POST /api/corpora/{corpus_id}/grant` - Grant group access (admin)
- `DELETE /api/corpora/{corpus_id}/revoke/{group_id}` - Revoke group access (admin)
- `GET /api/corpora/sessions/{session_id}/active` - Get active corpora in session
- `PUT /api/corpora/sessions/{session_id}/active` - Update active corpora
- `GET /api/corpora/restore-last` - Get last selected corpora

**Required Permissions:**
- `create:corpus` - Create corpus
- `update:corpus` - Update corpus
- `manage:corpus_access` - Grant/revoke access

---

## Authentication

All endpoints (except `/api/auth/register` and `/api/auth/login`) require JWT authentication.

### Getting a Token

```bash
# Register
curl -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User"
  }'

# Login
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'

# Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    ...
  }
}
```

### Using the Token

Include the token in the Authorization header:

```bash
curl -X GET http://localhost:8080/api/users/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

---

## Example Workflows

### 1. User Registration and Setup

```bash
# 1. Register user
curl -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "password": "securepass",
    "full_name": "Alice Johnson"
  }'

# 2. Login
TOKEN=$(curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "securepass"}' \
  | jq -r '.access_token')

# 3. Get available agents
curl -X GET http://localhost:8080/api/agents/me \
  -H "Authorization: Bearer $TOKEN"

# 4. Set default agent
curl -X PUT http://localhost:8080/api/users/me/default-agent/1 \
  -H "Authorization: Bearer $TOKEN"

# 5. Get available corpora
curl -X GET http://localhost:8080/api/corpora/ \
  -H "Authorization: Bearer $TOKEN"
```

### 2. Agent Switching in Session

```bash
# Get user's agents
curl -X GET http://localhost:8080/api/agents/me \
  -H "Authorization: Bearer $TOKEN"

# Switch session to different agent
curl -X POST http://localhost:8080/api/agents/sessions/session-123/switch/2 \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Corpus Selection Management

```bash
# Get available corpora
curl -X GET http://localhost:8080/api/corpora/ \
  -H "Authorization: Bearer $TOKEN"

# Update active corpora for session
curl -X PUT http://localhost:8080/api/corpora/sessions/session-123/active \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"corpus_ids": [1, 2]}'

# Get active corpora
curl -X GET http://localhost:8080/api/corpora/sessions/session-123/active \
  -H "Authorization: Bearer $TOKEN"

# Restore last session's corpora
curl -X GET http://localhost:8080/api/corpora/restore-last \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Admin: User and Access Management

```bash
# Create group
curl -X POST http://localhost:8080/api/groups/ \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "data-scientists",
    "description": "Data science team"
  }'

# Add user to group
curl -X PUT http://localhost:8080/api/groups/1/users/2 \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Grant agent access to user
curl -X PUT http://localhost:8080/api/agents/3/grant/2 \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Grant corpus access to group
curl -X POST http://localhost:8080/api/corpora/1/grant \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": 1,
    "permission": "read"
  }'
```

---

## Integration with Existing Server

To integrate these routes into the existing `server.py`:

```python
from api.routes import (
    auth_router,
    users_router,
    groups_router,
    agents_router,
    corpora_router
)

# Register routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(groups_router)
app.include_router(agents_router)
app.include_router(corpora_router)
```

---

## Error Responses

All endpoints return standard HTTP status codes:

- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Missing/invalid token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

Error response format:
```json
{
  "detail": "Error message description"
}
```

---

## OpenAPI Documentation

Once integrated, access interactive API documentation at:
- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`
- OpenAPI JSON: `http://localhost:8080/openapi.json`
