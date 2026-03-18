# ADK RAG Secure Enterprise Application Implementation Plan

This plan implements a production-ready, cloud-native Google ADK RAG application with three-layer security (app access, corpus access, agent access), IAP authentication, Google Cloud Identity Groups authorization, and Google Cloud Model Armor LLM safety protections.

## Project Context

- **GCP Project ID**: dvlm-adk-lab
- **Project Number**: 550184115528
- **Region**: us-west1
- **Database**: Cloud SQL PostgreSQL
- **Approach**: New application structure (clean implementation)
- **Existing Assets**: RAG functionality reference in `/ref-code-backend/` and `/ref-code-frontend/`, sample documents in `/data/`
- **UI Design**: Modern dark mode with blue/purple accent colors

## Architecture Overview

### Three-Layer Security Model

1. **Application Access (IAP)**: Google Identity + IAP OAuth 2.0 controls who can access the application
2. **Corpus Access (Group-Based)**: Google Cloud Identity Groups control which corpora users can access
3. **Agent Access (Group-Based)**: Google Cloud Identity Groups control which agents users can invoke

### Technology Stack

- **Frontend**: Next.js with TypeScript, TailwindCSS, shadcn/ui components
- **Backend**: Python FastAPI with Google ADK
- **Hosting**: Cloud Run (frontend and backend)
- **Authentication**: Identity-Aware Proxy (IAP) with OAuth 2.0
- **Authorization**: Cloud Identity Groups + application-layer enforcement
- **Database**: Cloud SQL PostgreSQL (authorization metadata, audit logs)
- **RAG Engine**: Vertex AI RAG Engine
- **Storage**: Cloud Storage (one bucket per corpus)
- **LLM Safety**: Google Cloud Model Armor (prompt/response sanitization)
- **Secrets**: Secret Manager
- **Logging**: Cloud Logging + structured audit tables

## Implementation Phases

### Phase 1: Infrastructure Foundation

#### 1.1 Enable Required GCP APIs
- Compute Engine API
- Cloud Run API
- Cloud SQL Admin API
- Cloud Storage API
- Vertex AI API
- Identity-Aware Proxy API
- Cloud Identity API
- Cloud Resource Manager API
- Secret Manager API
- Cloud Logging API
- Model Armor API

#### 1.2 Create Service Accounts
- **Backend Service Account**: `adk-rag-backend-sa@dvlm-adk-lab.iam.gserviceaccount.com`
  - Roles: Vertex AI User, Storage Object Admin (scoped), Cloud SQL Client, Model Armor User, Logging Writer
- **Frontend Service Account**: `adk-rag-frontend-sa@dvlm-adk-lab.iam.gserviceaccount.com`
  - Roles: Minimal (only logging)
- **Group Sync Service Account**: `adk-rag-group-sync-sa@dvlm-adk-lab.iam.gserviceaccount.com`
  - Roles: Cloud Identity Groups Viewer

#### 1.3 Set Up Cloud SQL PostgreSQL
- Instance name: `adk-rag-db-instance`
- Version: PostgreSQL 15
- Region: us-west1
- Machine type: db-custom-2-7680 (2 vCPU, 7.5 GB RAM)
- Storage: 20 GB SSD with automatic increase
- High availability: Regional (for production)
- Private IP: Enable VPC peering
- Backups: Automated daily backups, 7-day retention
- Database name: `adk_rag_production`

#### 1.4 Create Cloud Storage Buckets
- **Default corpus bucket**: `adk-rag-default-corpus-bucket-{project-id}`
  - Location: us-west1
  - Storage class: Standard
  - Uniform bucket-level access
  - Versioning: Enabled
  - Lifecycle: Optional archive after 90 days
- **Additional corpus buckets**: Created dynamically per corpus
  - Naming convention: `adk-rag-{corpus-name}-bucket-{project-id}`

#### 1.5 Configure Secret Manager
- Database connection string
- OAuth client credentials (if custom)
- Model Armor configuration (if needed)

### Phase 2: Google Cloud Identity Groups Setup

#### 2.1 Create App Access Groups
- `adk-rag-users@{domain}` - All application users
- `adk-rag-admins@{domain}` - Application administrators

#### 2.2 Create Corpus Access Groups
- `adk-rag-default-corpus@{domain}` - Default corpus access (all users)
- Template for additional corpus groups: `adk-rag-{corpus-name}-corpus@{domain}`

#### 2.3 Create Agent Access Groups
- `adk-rag-admin-agent@{domain}` - Admin agent access
- `adk-rag-content-manager-agent@{domain}` - Content manager agent access
- `adk-rag-contributor-agent@{domain}` - Contributor agent access
- `adk-rag-viewer-agent@{domain}` - Viewer agent access (all users)

#### 2.4 Initial Group Memberships
- Add test users to appropriate groups
- All users must be in `adk-rag-users` and `adk-rag-viewer-agent`
- All users must be in `adk-rag-default-corpus`

### Phase 3: Database Schema Implementation

#### 3.1 Core Tables

**users**
```sql
- user_id (UUID, PK)
- email (VARCHAR, UNIQUE, NOT NULL)
- display_name (VARCHAR)
- status (ENUM: active, inactive, suspended)
- last_login (TIMESTAMP)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

**groups**
```sql
- group_id (UUID, PK)
- group_email (VARCHAR, UNIQUE, NOT NULL)
- group_type (ENUM: app_access, corpus_access, agent_access)
- display_name (VARCHAR)
- description (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

**user_group_memberships**
```sql
- membership_id (UUID, PK)
- user_id (UUID, FK -> users)
- group_id (UUID, FK -> groups)
- source_of_truth (VARCHAR: 'cloud_identity')
- synced_at (TIMESTAMP)
- UNIQUE(user_id, group_id)
```

**corpora**
```sql
- corpus_id (UUID, PK)
- corpus_name (VARCHAR, UNIQUE, NOT NULL)
- description (TEXT)
- gcs_bucket (VARCHAR, UNIQUE, NOT NULL)
- vertex_rag_corpus_id (VARCHAR, UNIQUE)
- data_classification (ENUM: public, internal, confidential, restricted)
- owner_group_id (UUID, FK -> groups)
- status (ENUM: active, inactive, archived)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

**corpus_group_bindings**
```sql
- binding_id (UUID, PK)
- corpus_id (UUID, FK -> corpora)
- group_id (UUID, FK -> groups)
- permission_level (ENUM: read, write, manage, admin)
- created_at (TIMESTAMP)
- UNIQUE(corpus_id, group_id)
```

**agents**
```sql
- agent_id (UUID, PK)
- agent_name (VARCHAR, UNIQUE, NOT NULL)
- description (TEXT)
- status (ENUM: active, inactive, deprecated)
- deployment_ref (VARCHAR)
- allowed_tools_json (JSONB)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

**agent_group_bindings**
```sql
- binding_id (UUID, PK)
- agent_id (UUID, FK -> agents)
- group_id (UUID, FK -> groups)
- permission_level (ENUM: use, manage, admin)
- created_at (TIMESTAMP)
- UNIQUE(agent_id, group_id)
```

**audit_logs**
```sql
- audit_id (UUID, PK)
- user_id (UUID, FK -> users)
- user_email (VARCHAR, NOT NULL)
- session_id (VARCHAR)
- request_id (VARCHAR)
- action_type (VARCHAR, NOT NULL)
- target_type (VARCHAR)
- target_id (VARCHAR)
- authorization_result (ENUM: allowed, denied)
- model_armor_result (JSONB)
- reason (TEXT)
- timestamp (TIMESTAMP, NOT NULL)
- metadata (JSONB)
```

**sessions**
```sql
- session_id (UUID, PK)
- user_id (UUID, FK -> users)
- adk_session_id (VARCHAR)
- selected_corpus_id (UUID, FK -> corpora)
- selected_agent_id (UUID, FK -> agents)
- effective_permissions (JSONB)
- created_at (TIMESTAMP)
- last_activity (TIMESTAMP)
- expires_at (TIMESTAMP)
```

#### 3.2 Indexes
- `idx_users_email` on users(email)
- `idx_groups_email` on groups(group_email)
- `idx_groups_type` on groups(group_type)
- `idx_memberships_user` on user_group_memberships(user_id)
- `idx_memberships_group` on user_group_memberships(group_id)
- `idx_corpus_bindings_corpus` on corpus_group_bindings(corpus_id)
- `idx_corpus_bindings_group` on corpus_group_bindings(group_id)
- `idx_agent_bindings_agent` on agent_group_bindings(agent_id)
- `idx_agent_bindings_group` on agent_group_bindings(group_id)
- `idx_audit_user` on audit_logs(user_id)
- `idx_audit_timestamp` on audit_logs(timestamp)
- `idx_audit_action` on audit_logs(action_type)

### Phase 4: Backend Application Development

#### 4.1 Project Structure
```
backend/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── server.py                    # FastAPI app initialization
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                  # Authentication endpoints
│   │   │   ├── user.py                  # User profile endpoints
│   │   │   ├── corpora.py               # Corpus management
│   │   │   ├── agents.py                # Agent invocation
│   │   │   ├── documents.py             # Document operations
│   │   │   ├── admin.py                 # Admin operations
│   │   │   └── model_armor.py           # Model Armor testing endpoints
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── iap_auth.py                  # IAP identity extraction
│   │   ├── authorization.py             # Authorization middleware
│   │   └── audit_logging.py             # Audit middleware
│   ├── services/
│   │   ├── __init__.py
│   │   ├── iap_service.py               # IAP identity verification
│   │   ├── group_sync_service.py        # Cloud Identity Groups sync
│   │   ├── authorization_service.py     # Permission resolution
│   │   ├── corpus_service.py            # Corpus operations
│   │   ├── agent_service.py             # Agent management
│   │   ├── document_service.py          # Document operations
│   │   ├── model_armor_service.py       # Model Armor integration
│   │   ├── vertex_rag_service.py        # Vertex AI RAG integration
│   │   └── audit_service.py             # Audit logging
│   ├── adk/
│   │   ├── __init__.py
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── admin_agent.py           # Admin agent definition
│   │   │   ├── content_manager_agent.py # Content manager agent
│   │   │   ├── contributor_agent.py     # Contributor agent
│   │   │   └── viewer_agent.py          # Viewer agent
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── base_tool.py             # Base tool with auth
│   │   │   ├── rag_query.py             # RAG query tool
│   │   │   ├── list_corpora.py          # List corpora tool
│   │   │   ├── get_corpus_info.py       # Corpus info tool
│   │   │   ├── browse_documents.py      # Browse documents tool
│   │   │   ├── add_data.py              # Add data tool
│   │   │   ├── create_corpus.py         # Create corpus tool
│   │   │   ├── delete_document.py       # Delete document tool
│   │   │   ├── delete_corpus.py         # Delete corpus tool
│   │   │   ├── retrieve_document.py     # Retrieve document tool
│   │   │   ├── multi_corpora_query.py   # Multi-corpus query tool
│   │   │   └── set_current_corpus.py    # Set current corpus tool
│   │   └── decorators/
│   │       ├── __init__.py
│   │       ├── require_agent_access.py  # Agent access decorator
│   │       ├── require_corpus_access.py # Corpus access decorator
│   │       └── model_armor_wrapper.py   # Model Armor decorator
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                      # User models
│   │   ├── group.py                     # Group models
│   │   ├── corpus.py                    # Corpus models
│   │   ├── agent.py                     # Agent models
│   │   ├── session.py                   # Session models
│   │   └── audit.py                     # Audit models
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py                # Database connection
│   │   ├── schema.sql                   # Schema definition
│   │   └── migrations/                  # Migration scripts
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py                  # Configuration
│   └── utils/
│       ├── __init__.py
│       ├── cache.py                     # Caching utilities
│       └── logging.py                   # Logging utilities
├── tests/
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_authorization.py
│   ├── test_agents.py
│   ├── test_tools.py
│   └── test_model_armor.py
├── requirements.txt
├── Dockerfile
├── cloudbuild.yaml
└── README.md
```

#### 4.2 Key Backend Components

**IAP Authentication Middleware**
- Extract `X-Goog-IAP-JWT-Assertion` header
- Verify JWT signature using Google's public keys
- Extract user email and ID
- Attach user context to request

**Authorization Service**
- Resolve user's group memberships (cached with TTL)
- Compute effective permissions for corpora
- Compute effective permissions for agents
- Cache entitlements with 5-minute TTL
- Invalidate cache on group membership changes

**Group Sync Service**
- Scheduled job (every 15 minutes)
- Query Cloud Identity Groups API
- Sync group memberships to database
- Detect and log membership changes
- Trigger cache invalidation

**Model Armor Service**
- Direct API integration for `sanitizeUserPrompt`
- Direct API integration for `sanitizeModelResponse`
- Optional Vertex AI integrated configuration
- Configurable enforcement modes: inspect-only, inspect-and-block
- Structured logging of sanitization results

**Tool Authorization Decorator**
```python
@require_agent_access(agent_name="admin-agent")
@require_corpus_access(permission_level="write")
@model_armor_sanitize(sanitize_prompt=True, sanitize_response=True)
async def add_data_tool(user_context, corpus_id, document_data):
    # Tool implementation
    pass
```

#### 4.3 API Endpoints

**Authentication & User**
- `GET /api/v1/auth/me` - Get current user info
- `GET /api/v1/auth/me/permissions` - Get user permissions
- `POST /api/v1/auth/logout` - Logout (clear session)

**Corpora**
- `GET /api/v1/corpora` - List accessible corpora
- `GET /api/v1/corpora/{corpus_id}` - Get corpus details
- `POST /api/v1/corpora` - Create corpus (admin only)
- `DELETE /api/v1/corpora/{corpus_id}` - Delete corpus (admin only)

**Documents**
- `GET /api/v1/corpora/{corpus_id}/documents` - List documents
- `POST /api/v1/corpora/{corpus_id}/documents` - Upload document
- `GET /api/v1/corpora/{corpus_id}/documents/{doc_id}` - Get document
- `DELETE /api/v1/corpora/{corpus_id}/documents/{doc_id}` - Delete document

**Agents**
- `GET /api/v1/agents` - List accessible agents
- `GET /api/v1/agents/{agent_id}` - Get agent details
- `POST /api/v1/agents/sessions` - Create agent session
- `POST /api/v1/agents/invoke` - Invoke agent with tool call

**Model Armor Testing**
- `POST /api/v1/security/model-armor/sanitize-prompt` - Test prompt sanitization
- `POST /api/v1/security/model-armor/sanitize-response` - Test response sanitization
- `POST /api/v1/agents/invoke-secure` - Full secure agent invocation flow

**Admin**
- `GET /api/v1/admin/users` - List users
- `POST /api/v1/admin/groups/sync` - Trigger group sync
- `GET /api/v1/admin/audit-logs` - Query audit logs
- `POST /api/v1/admin/corpus-bindings` - Manage corpus-group bindings
- `POST /api/v1/admin/agent-bindings` - Manage agent-group bindings

### Phase 5: ADK Agent & Tool Implementation

#### 5.1 Agent Definitions

**Admin Agent** (`adk-rag-admin-agent`)
- Tools: rag_query, list_corpora, get_corpus_info, browse_documents, add_data, create_corpus, delete_document, delete_corpus, retrieve_document, multi_corpora_query, set_current_corpus
- Access: Members of `adk-rag-admin-agent` group

**Content Manager Agent** (`adk-rag-content-manager-agent`)
- Tools: rag_query, list_corpora, get_corpus_info, browse_documents, add_data, delete_document, retrieve_document, multi_corpora_query, set_current_corpus
- Access: Members of `adk-rag-content-manager-agent` group

**Contributor Agent** (`adk-rag-contributor-agent`)
- Tools: rag_query, list_corpora, get_corpus_info, browse_documents, add_data, multi_corpora_query, set_current_corpus
- Access: Members of `adk-rag-contributor-agent` group

**Viewer Agent** (`adk-rag-viewer-agent`)
- Tools: rag_query, list_corpora, get_corpus_info, browse_documents, multi_corpora_query, set_current_corpus
- Access: Members of `adk-rag-viewer-agent` group (all users)

#### 5.2 Tool Security Flow

Each tool must implement:
1. **Agent Authorization**: Verify user belongs to agent's access group
2. **Corpus Authorization**: Verify user has required permission level for target corpus
3. **Model Armor Prompt Sanitization**: Sanitize user input before LLM call
4. **Vertex AI RAG Operation**: Execute RAG operation
5. **Model Armor Response Sanitization**: Sanitize LLM output before returning
6. **Audit Logging**: Log authorization decision, Model Armor results, and operation outcome

#### 5.3 Tool Implementation Pattern

```python
class RagQueryTool(BaseTool):
    @require_agent_access()
    @require_corpus_access(permission_level="read")
    async def execute(self, user_context: UserContext, corpus_id: str, query: str):
        # 1. Sanitize user prompt
        sanitized_prompt = await model_armor_service.sanitize_prompt(query)
        
        if sanitized_prompt.blocked:
            await audit_service.log_blocked_prompt(user_context, query, sanitized_prompt.reason)
            raise SecurityException("Prompt blocked by Model Armor")
        
        # 2. Execute RAG query
        rag_response = await vertex_rag_service.query(corpus_id, sanitized_prompt.content)
        
        # 3. Sanitize model response
        sanitized_response = await model_armor_service.sanitize_response(rag_response)
        
        if sanitized_response.blocked:
            await audit_service.log_blocked_response(user_context, rag_response, sanitized_response.reason)
            raise SecurityException("Response blocked by Model Armor")
        
        # 4. Audit successful operation
        await audit_service.log_success(user_context, "rag_query", corpus_id, sanitized_response.metadata)
        
        return sanitized_response.content
```

### Phase 6: Frontend Application Development

#### 6.1 Project Structure
```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx                   # Root layout
│   │   ├── page.tsx                     # Home page
│   │   ├── dashboard/
│   │   │   └── page.tsx                 # Main dashboard
│   │   ├── corpora/
│   │   │   ├── page.tsx                 # Corpora list
│   │   │   └── [id]/
│   │   │       └── page.tsx             # Corpus details
│   │   ├── agents/
│   │   │   ├── page.tsx                 # Agent selection
│   │   │   └── [id]/
│   │   │       └── page.tsx             # Agent chat interface
│   │   └── admin/
│   │       ├── page.tsx                 # Admin dashboard
│   │       ├── users/
│   │       ├── groups/
│   │       └── audit/
│   ├── components/
│   │   ├── ui/                          # shadcn/ui components
│   │   ├── auth/
│   │   │   ├── UserProfile.tsx
│   │   │   └── PermissionsDisplay.tsx
│   │   ├── corpora/
│   │   │   ├── CorpusList.tsx
│   │   │   ├── CorpusCard.tsx
│   │   │   └── DocumentBrowser.tsx
│   │   ├── agents/
│   │   │   ├── AgentSelector.tsx
│   │   │   ├── ChatInterface.tsx
│   │   │   └── ToolExecutionLog.tsx
│   │   └── admin/
│   │       ├── UserManagement.tsx
│   │       ├── GroupBindings.tsx
│   │       └── AuditLogViewer.tsx
│   ├── lib/
│   │   ├── api.ts                       # API client
│   │   ├── auth.ts                      # Auth utilities
│   │   └── types.ts                     # TypeScript types
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── usePermissions.ts
│   │   └── useAgent.ts
│   └── styles/
│       └── globals.css
├── public/
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── Dockerfile
└── README.md
```

#### 6.2 Modern Dark Mode UI Design

**Color Scheme - Dark Mode with Blue/Purple Accents**

Primary Colors:
- **Background**: `#0a0a0f` (Deep dark blue-black)
- **Surface**: `#1a1a2e` (Dark slate)
- **Surface Elevated**: `#252538` (Elevated surface)
- **Border**: `#2d2d44` (Subtle borders)

Accent Colors:
- **Primary**: `#6366f1` (Indigo - primary actions)
- **Primary Hover**: `#4f46e5` (Darker indigo)
- **Secondary**: `#8b5cf6` (Purple - secondary actions)
- **Secondary Hover**: `#7c3aed` (Darker purple)
- **Accent**: `#3b82f6` (Blue - highlights)

Semantic Colors:
- **Success**: `#10b981` (Green)
- **Warning**: `#f59e0b` (Amber)
- **Error**: `#ef4444` (Red)
- **Info**: `#06b6d4` (Cyan)

Text Colors:
- **Primary Text**: `#f8fafc` (Near white)
- **Secondary Text**: `#cbd5e1` (Light gray)
- **Muted Text**: `#94a3b8` (Gray)
- **Disabled Text**: `#64748b` (Dark gray)

**TailwindCSS Configuration**
```typescript
// tailwind.config.ts
export default {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#0a0a0f',
        surface: {
          DEFAULT: '#1a1a2e',
          elevated: '#252538',
        },
        border: '#2d2d44',
        primary: {
          DEFAULT: '#6366f1',
          hover: '#4f46e5',
          light: '#818cf8',
        },
        secondary: {
          DEFAULT: '#8b5cf6',
          hover: '#7c3aed',
          light: '#a78bfa',
        },
        accent: '#3b82f6',
        text: {
          primary: '#f8fafc',
          secondary: '#cbd5e1',
          muted: '#94a3b8',
          disabled: '#64748b',
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-primary': 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
        'gradient-surface': 'linear-gradient(135deg, #1a1a2e 0%, #252538 100%)',
      },
      boxShadow: {
        'glow-primary': '0 0 20px rgba(99, 102, 241, 0.3)',
        'glow-secondary': '0 0 20px rgba(139, 92, 246, 0.3)',
      },
    },
  },
}
```

**UI Component Styling Guidelines**

Navigation & Header:
- Dark surface background with subtle gradient
- Primary accent for active navigation items
- Glowing effect on hover for interactive elements
- User profile with avatar and role badge

Cards & Containers:
- Surface elevated background
- Subtle border with hover state
- Rounded corners (8px standard, 12px for prominent cards)
- Shadow on hover for depth

Buttons:
- Primary: Gradient background (indigo to purple)
- Secondary: Outlined with accent color
- Danger: Red with appropriate hover state
- Disabled: Muted with reduced opacity

Forms & Inputs:
- Dark surface background
- Accent border on focus with glow effect
- Placeholder text in muted color
- Validation states with semantic colors

Chat Interface:
- User messages: Primary gradient background
- Agent messages: Surface elevated background
- Code blocks: Darker background with syntax highlighting
- Tool execution logs: Collapsible with accent border

Data Tables:
- Alternating row colors for readability
- Hover state with subtle highlight
- Sortable headers with icons
- Pagination with accent colors

Status Indicators:
- Success: Green with checkmark icon
- Warning: Amber with alert icon
- Error: Red with error icon
- Info: Cyan with info icon
- Loading: Animated gradient shimmer

**Typography**
- Font Family: Inter (primary), JetBrains Mono (code)
- Headings: Bold, gradient text for h1/h2
- Body: Regular weight, high contrast
- Code: Monospace with syntax highlighting

**Iconography**
- Library: Lucide React
- Style: Outlined, consistent stroke width
- Size: 16px (small), 20px (medium), 24px (large)
- Color: Matches text hierarchy

**Animations & Transitions**
- Smooth transitions (200ms ease-in-out)
- Hover effects with scale and glow
- Loading states with skeleton screens
- Page transitions with fade
- Toast notifications slide from top-right

**Accessibility**
- WCAG 2.1 AA compliant contrast ratios
- Focus indicators with visible outline
- Keyboard navigation support
- Screen reader friendly labels
- Reduced motion support

#### 6.3 Key Frontend Features

**Authentication Flow**
- IAP handles authentication automatically
- Frontend calls `/api/v1/auth/me` on load
- Display user profile and permissions with modern card design
- Redirect to error page if not authenticated

**Permission-Based UI**
- Show only accessible corpora with visual cards
- Show only accessible agents with gradient badges
- Disable actions user cannot perform (grayed out with tooltip)
- Clear visual indicators for permission levels (color-coded badges)

**Agent Chat Interface**
- Select agent from available agents (card-based selection)
- Real-time chat with agent (modern message bubbles)
- Display tool execution logs (collapsible accordions)
- Show Model Armor sanitization results in debug mode (highlighted panels)
- Error handling for blocked prompts/responses (toast notifications)

**Admin Dashboard**
- User management (data table with search and filters)
- Group membership visualization (interactive charts)
- Corpus-group binding management (drag-and-drop interface)
- Agent-group binding management (matrix view)
- Audit log viewer with filtering (timeline view with color-coded events)

### Phase 7: Model Armor Integration

#### 7.1 Direct API Integration (Testing & Learning)

**Sanitize Prompt Endpoint**
```python
@router.post("/security/model-armor/sanitize-prompt")
async def sanitize_prompt(request: SanitizePromptRequest, user: User = Depends(get_current_user)):
    result = await model_armor_service.sanitize_user_prompt(
        prompt=request.prompt,
        template_name=request.template_name or "default-prompt-template"
    )
    
    await audit_service.log_model_armor_check(
        user=user,
        check_type="prompt",
        content=request.prompt,
        result=result
    )
    
    return {
        "original_prompt": request.prompt,
        "sanitized_prompt": result.sanitized_content,
        "blocked": result.blocked,
        "modified": result.modified,
        "violations": result.violations,
        "metadata": result.metadata
    }
```

**Sanitize Response Endpoint**
```python
@router.post("/security/model-armor/sanitize-response")
async def sanitize_response(request: SanitizeResponseRequest, user: User = Depends(get_current_user)):
    result = await model_armor_service.sanitize_model_response(
        response=request.response,
        template_name=request.template_name or "default-response-template"
    )
    
    await audit_service.log_model_armor_check(
        user=user,
        check_type="response",
        content=request.response,
        result=result
    )
    
    return {
        "original_response": request.response,
        "sanitized_response": result.sanitized_content,
        "blocked": result.blocked,
        "modified": result.modified,
        "violations": result.violations,
        "metadata": result.metadata
    }
```

#### 7.2 Vertex AI Integrated Model Armor (Optional)

**Configuration for Gemini Calls**
```python
from google.cloud import aiplatform

# Configure Model Armor floor settings
model_armor_config = {
    "model_armor_enabled": True,
    "template_name": "production-safety-template",
    "enforcement_mode": "inspect-and-block",  # or "inspect-only"
    "log_to_cloud_logging": True
}

# Use with Vertex AI Gemini
response = await vertex_ai_client.generate_content(
    model="gemini-1.5-pro",
    contents=prompt,
    safety_settings=model_armor_config
)
```

#### 7.3 Model Armor Templates

**Prompt Injection Template**
- Detect attempts to override system instructions
- Detect role-playing attacks
- Detect delimiter injection
- Block or redact suspicious patterns

**Harmful Content Template**
- Detect hate speech, violence, sexual content
- Detect harassment and bullying
- Configurable severity thresholds
- Block high-severity content

**Sensitive Data Template**
- Detect PII (SSN, credit cards, phone numbers)
- Detect API keys and credentials
- Detect internal identifiers
- Redact or block based on policy

#### 7.4 Enforcement Strategy

**Development Environment**
- Mode: `inspect-only`
- Log all sanitization results
- Review false positives/negatives
- Tune templates and thresholds

**Staging Environment**
- Mode: `inspect-and-block` for high-severity violations
- Mode: `inspect-only` for medium-severity violations
- Validate user experience
- Monitor blocked request rate

**Production Environment**
- Mode: `inspect-and-block` for all violations above threshold
- Graceful error messages to users
- Escalation path for false positives
- Regular review of sanitization logs

### Phase 8: IAP Configuration

#### 8.1 OAuth Consent Screen
- Configure OAuth consent screen in GCP Console
- Application name: "ADK RAG Enterprise Application"
- Support email
- Authorized domains
- Scopes: email, profile, openid

#### 8.2 OAuth Client Creation
- Create OAuth 2.0 client ID (Web application)
- Authorized redirect URIs: Cloud Run service URLs
- Note client ID and secret (store in Secret Manager)

#### 8.3 IAP Setup
- Enable IAP for Cloud Run services
- Configure IAP with OAuth client
- Add IAP-secured Web App User role to `adk-rag-users` group
- Test IAP authentication flow

#### 8.4 Backend IAP Integration
- Install `google-auth` library
- Implement JWT verification middleware
- Extract user email from `X-Goog-IAP-JWT-Assertion` header
- Validate JWT signature using Google's public keys
- Attach user context to all requests

### Phase 9: Deployment

#### 9.1 Database Deployment
- Create Cloud SQL instance
- Run schema initialization scripts
- Create database users
- Configure connection pooling
- Set up Cloud SQL Proxy for local development

#### 9.2 Initial Data Seeding
- Create default groups in database
- Create default corpus (adk-rag-default-corpus)
- Create default corpus bucket
- Upload sample documents from `/data/` folder
- Create agent definitions
- Set up default bindings

#### 9.3 Backend Deployment to Cloud Run
- Build Docker image
- Push to Artifact Registry
- Deploy to Cloud Run (us-west1)
- Configure environment variables
- Set up Cloud SQL connection
- Configure IAP
- Set up custom domain (optional)
- Configure autoscaling (min 1, max 100 instances)

#### 9.4 Frontend Deployment to Cloud Run
- Build Next.js application
- Build Docker image
- Push to Artifact Registry
- Deploy to Cloud Run (us-west1)
- Configure environment variables (backend API URL)
- Configure IAP
- Set up custom domain (optional)
- Configure autoscaling (min 1, max 50 instances)

#### 9.5 Group Sync Job Deployment
- Deploy as Cloud Run job or Cloud Scheduler + Cloud Functions
- Schedule: Every 15 minutes
- Configure service account with Cloud Identity Groups Viewer role
- Test sync functionality

### Phase 10: Testing & Validation

#### 10.1 Authentication Testing
- Verify IAP redirects unauthenticated users
- Verify JWT extraction and validation
- Test with multiple user accounts
- Verify group membership resolution

#### 10.2 Authorization Testing
- Test app access (IAP layer)
- Test corpus access (group-based)
- Test agent access (group-based)
- Test tool-level authorization
- Test permission inheritance
- Test multi-group membership scenarios

#### 10.3 Model Armor Testing
- Test prompt sanitization with benign prompts
- Test prompt sanitization with injection attempts
- Test response sanitization with safe content
- Test response sanitization with harmful content
- Verify Cloud Logging captures sanitization results
- Test enforcement modes (inspect-only vs inspect-and-block)

#### 10.4 Agent & Tool Testing
- Test each agent with authorized users
- Test each tool with appropriate permissions
- Test unauthorized access attempts
- Verify audit logging for all operations
- Test error handling and user feedback

#### 10.5 Integration Testing
- End-to-end user flow: login → select corpus → select agent → query
- Document upload and retrieval flow
- Multi-corpus query flow
- Admin operations flow
- Group sync and permission propagation

#### 10.6 Performance Testing
- Load test with 100 concurrent users
- Test entitlement cache performance
- Test database query performance
- Test Vertex AI RAG latency
- Test Model Armor sanitization latency

### Phase 11: Security Hardening

#### 11.1 Least Privilege Review
- Audit all service account permissions
- Remove unnecessary IAM roles
- Implement resource-level IAM where possible
- Review bucket access policies

#### 11.2 Network Security
- Configure VPC for Cloud Run services
- Set up VPC Service Controls (optional)
- Configure Cloud Armor for DDoS protection
- Implement rate limiting

#### 11.3 Data Protection
- Enable CMEK for Cloud SQL (optional)
- Enable CMEK for GCS buckets (optional)
- Configure bucket versioning and lifecycle
- Set up automated backups

#### 11.4 Audit & Monitoring
- Configure Cloud Logging exports
- Set up log-based metrics
- Create alerting policies
- Configure uptime checks
- Set up error reporting

### Phase 12: Documentation & Operational Runbook

#### 12.1 Architecture Documentation
- System architecture diagram
- Data flow diagrams
- Security model documentation
- API documentation (OpenAPI/Swagger)

#### 12.2 Operational Runbook
- Deployment procedures
- Rollback procedures
- Database backup and restore
- Group membership management
- Corpus creation and management
- Agent deployment and updates
- Incident response procedures
- Monitoring and alerting guide

#### 12.3 User Documentation
- User guide for accessing the application
- Guide for using different agents
- Document upload and management guide
- FAQ and troubleshooting

#### 12.4 Developer Documentation
- Local development setup
- Testing procedures
- Code contribution guidelines
- ADK agent development guide
- Tool development guide

## Deliverables

### Code Deliverables
1. **Backend Application** (Python FastAPI + Google ADK)
   - Complete source code with all modules
   - Unit tests and integration tests
   - Dockerfile and deployment configs
   
2. **Frontend Application** (Next.js + TypeScript)
   - Complete source code with all components
   - UI/UX implementation
   - Dockerfile and deployment configs

3. **Infrastructure as Code** (Terraform)
   - GCP resource provisioning
   - IAM configuration
   - Network configuration
   - Database setup

4. **Database Schema**
   - SQL schema definitions
   - Migration scripts
   - Seed data scripts

### Documentation Deliverables
1. **Architecture Documentation**
   - Reference architecture diagram
   - Security model documentation
   - Data model documentation

2. **API Documentation**
   - OpenAPI/Swagger specifications
   - API usage examples
   - Authentication/authorization guide

3. **Deployment Guide**
   - Step-by-step deployment instructions
   - Configuration guide
   - Troubleshooting guide

4. **Operational Runbook**
   - Monitoring and alerting setup
   - Incident response procedures
   - Backup and recovery procedures

5. **User Documentation**
   - User guide
   - Admin guide
   - FAQ

### Security Deliverables
1. **Threat Model**
   - Identified threats and attack vectors
   - Mitigations and controls
   - Detection and response strategies

2. **Security Test Results**
   - Authentication test results
   - Authorization test results
   - Model Armor test results
   - Penetration test findings (if applicable)

## Implementation Timeline Estimate

- **Phase 1-2 (Infrastructure & Groups)**: 1 week
- **Phase 3 (Database Schema)**: 3 days
- **Phase 4 (Backend Development)**: 3 weeks
- **Phase 5 (ADK Agents & Tools)**: 2 weeks
- **Phase 6 (Frontend Development)**: 2 weeks
- **Phase 7 (Model Armor Integration)**: 1 week
- **Phase 8 (IAP Configuration)**: 3 days
- **Phase 9 (Deployment)**: 1 week
- **Phase 10 (Testing)**: 2 weeks
- **Phase 11 (Security Hardening)**: 1 week
- **Phase 12 (Documentation)**: 1 week

**Total Estimated Timeline**: 12-14 weeks

## Success Criteria

1. ✅ Users can authenticate via IAP with Google Identity
2. ✅ Users can only access corpora they are authorized for via group membership
3. ✅ Users can only invoke agents they are authorized for via group membership
4. ✅ All tool operations enforce authorization at runtime
5. ✅ Model Armor sanitizes all prompts before LLM invocation
6. ✅ Model Armor sanitizes all responses before returning to users
7. ✅ All operations are audited with structured logs
8. ✅ System scales to 100+ concurrent users
9. ✅ Group membership changes propagate within 15 minutes
10. ✅ Zero unauthorized access to corpora or agents
11. ✅ All sensitive operations logged to Cloud Logging
12. ✅ Application passes security review

## Risk Mitigation

### Technical Risks
- **Risk**: IAP configuration complexity
  - **Mitigation**: Follow Google's IAP documentation, test with staging environment first
  
- **Risk**: Model Armor API latency
  - **Mitigation**: Implement caching for repeated prompts, use async processing, monitor latency

- **Risk**: Group sync delays
  - **Mitigation**: Implement cache with TTL, provide manual sync trigger for admins

- **Risk**: Database performance at scale
  - **Mitigation**: Proper indexing, connection pooling, read replicas if needed

### Security Risks
- **Risk**: Stale group memberships in cache
  - **Mitigation**: Short TTL (5 minutes), event-driven invalidation, audit logging

- **Risk**: Bypass of Model Armor checks
  - **Mitigation**: Centralized decorator pattern, code review, automated testing

- **Risk**: Privilege escalation
  - **Mitigation**: Server-side enforcement, audit all permission changes, least privilege

### Operational Risks
- **Risk**: Complex deployment process
  - **Mitigation**: Terraform automation, CI/CD pipeline, comprehensive documentation

- **Risk**: Monitoring gaps
  - **Mitigation**: Comprehensive logging, alerting on critical paths, regular review

## Next Steps

1. Review and approve this implementation plan
2. Set up GCP project and enable required APIs
3. Create initial Google Cloud Identity Groups
4. Begin Phase 1: Infrastructure Foundation
5. Establish development environment and CI/CD pipeline
6. Start iterative development following the phased approach
