"""
FastAPI server for the RAG Agent with user interface support.
"""

import uuid
import logging
import warnings
import os
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone
from contextlib import contextmanager
from pathlib import Path

# Auto-load environment variables from .env.local if it exists
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / '.env.local'
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"✅ Loaded environment variables from {env_path}")
else:
    print(f"⚠️  No .env.local found at {env_path}")

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Import new modular API routes
# Add src to path for proper imports
import sys
backend_src = os.path.join(os.path.dirname(os.path.dirname(__file__)))
if backend_src not in sys.path:
    sys.path.insert(0, backend_src)

# Now import after sys.path is set
from middleware.iap_auth_middleware import get_current_user_iap as get_current_user_from_middleware
from models.user import User

# Import agent manager for dynamic agent loading (after path setup)
try:
    from services.agent_manager import AgentManager
    AGENT_MANAGER_AVAILABLE = True
    print("✅ AgentManager imported successfully")
except ImportError as e:
    AGENT_MANAGER_AVAILABLE = False
    print(f"⚠️  AgentManager not available: {e}")
    print("   Using static agent loading instead")

# Import database connection utilities (after path setup)
from database.connection import init_database, get_db_connection
from database.schema_init import initialize_schema

try:
    from api.routes import (
        users_router,
        agents_router,
        corpora_router,
        admin_router,
        iap_auth_router,
        documents_router,
        chatbot_admin_router,
        google_groups_admin_router,
        model_armor_router
    )
    NEW_ROUTES_AVAILABLE = True
    print("✅ New API routes loaded successfully")
except ImportError as e:
    NEW_ROUTES_AVAILABLE = False
    print(f"⚠️  New API routes not available: {e}")
    print("   Run migrations and setup first: python src/database/migrations/run_migrations.py")

# Configure logging based on environment
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL))

# Suppress ADK warnings - these come from google.genai.types module
# The warning is hardcoded in the library and can't be suppressed via logging
# We need to suppress it at the warnings module level with the exact category
if not os.getenv("SHOW_ADK_WARNINGS", "false").lower() == "true":
    # Suppress the specific warning from google.genai.types
    warnings.filterwarnings("ignore", category=UserWarning, module="google.genai.types")
    warnings.filterwarnings("ignore", message=".*non-text parts in the response.*")
    logging.getLogger("google.genai.types").setLevel(logging.ERROR)

# Database configuration (now handled in connection.py)

# Initialize database on startup
logger = logging.getLogger(__name__)
logger.info("🔍 Initializing PostgreSQL database schema...")
# Initialize PostgreSQL schema (idempotent - safe to run on every startup)
# CRITICAL: if this raises, the process exits with code 1 so Cloud Run marks
# the revision as failed and stops routing traffic to it.
try:
    initialize_schema()
except Exception as _schema_err:
    allow_no_db = os.getenv("ALLOW_START_WITHOUT_DB", "false").lower() == "true"
    if allow_no_db:
        logger.error(
            "⚠️  Database schema initialization failed, but ALLOW_START_WITHOUT_DB=true so startup will continue. "
            "Most API routes will fail until the database is reachable.",
            extra={"error": str(_schema_err)[:500]},
        )
    else:
        logger.critical(
            f"❌ FATAL: Database schema initialization failed — aborting startup.\n"
            f"   Error: {_schema_err}\n"
            f"   Fix DB_PASSWORD secret and CLOUD_SQL_CONNECTION_NAME then redeploy."
        )
        import sys
        sys.exit(1)

# Sync corpora from Vertex AI on startup
def sync_corpora_on_startup():
    """Sync corpora from Vertex AI to database on application startup."""
    try:
        from services.corpus_sync_service import CorpusSyncService
        from config.config_loader import load_config
        
        account = os.getenv('ACCOUNT_ENV', 'develom')
        config = load_config(account)
        project_id = config.PROJECT_ID
        location = config.LOCATION
        
        CorpusSyncService.sync_on_startup(project_id, location)
    except Exception as e:
        logger.error(f"⚠️  Corpus sync on startup failed (non-critical): {e}")
        logger.error("   Application will continue with existing database data")

sync_corpora_on_startup()

# Clean up expired/inactive sessions on startup and periodically
def cleanup_sessions_on_startup():
    """Expire stale sessions on application startup."""
    try:
        from services.session_service import SessionService
        count = SessionService.cleanup_expired_sessions()
        if count > 0:
            logger.info(f"🧹 Startup: cleaned up {count} expired/inactive sessions")
        else:
            logger.info("🧹 Startup: no expired sessions to clean up")
    except Exception as e:
        logger.error(f"⚠️  Session cleanup on startup failed (non-critical): {e}")

cleanup_sessions_on_startup()


async def _periodic_session_cleanup():
    """Background task: expire stale sessions every hour."""
    import asyncio
    from services.session_service import SessionService
    while True:
        await asyncio.sleep(3600)  # 1 hour
        try:
            count = SessionService.cleanup_expired_sessions()
            if count > 0:
                logger.info(f"🧹 Periodic: cleaned up {count} expired/inactive sessions")
        except Exception as e:
            logger.error(f"⚠️  Periodic session cleanup failed: {e}")


# Pydantic models for API requests/responses
class UserProfile(BaseModel):
    name: str
    preferences: Optional[str] = None

class ChatMessage(BaseModel):
    message: str
    user_profile: Optional[UserProfile] = None
    corpora: Optional[List[str]] = None

class ChatResponse(BaseModel):
    response: str
    timestamp: datetime
    session_id: str

class SessionInfo(BaseModel):
    session_id: str
    user_profile: Optional[UserProfile] = None
    username: Optional[str] = None
    created_at: datetime
    last_activity: datetime

# In-memory session storage (in production, use Redis or database)
sessions: Dict[str, Dict] = {}

# Initialize ADK session service and runner
# Import after vertexai.init() to ensure proper initialization
import sys
import os

# Add config directory to path
backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
config_path = os.path.join(backend_root, 'config')
if config_path not in sys.path:
    sys.path.insert(0, config_path)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from config_loader import load_config

# Get account environment (defaults to 'develom')
account_env = os.environ.get("ACCOUNT_ENV", "develom")
print(f"🔧 Loading agent for account: {account_env}")

# Load account-specific configuration
config = load_config(account_env)

# Resolve effective configuration without overwriting existing environment
# This ensures deployment-provided env vars take precedence, while still
# making values available for downstream modules that read from os.environ
effective_project = os.getenv("PROJECT_ID") or config.PROJECT_ID
effective_location = os.getenv("GOOGLE_CLOUD_LOCATION") or config.LOCATION

# Populate env only if missing (do not override)
os.environ.setdefault("PROJECT_ID", effective_project)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", effective_location)

print(f"📋 Config resolved: PROJECT_ID={effective_project}, LOCATION={effective_location}")

# Log resolved environment for observability
logging.info(
    "backend_startup",
    extra={
        "account_env": account_env,
        "project_id": effective_project,
        "location": effective_location,
        "root_path": os.getenv("ROOT_PATH", ""),
    },
)

# Initialize AgentManager for dynamic agent loading
root_agent = None
if AGENT_MANAGER_AVAILABLE:
    agent_manager = AgentManager(
        project_id=effective_project,
        location=effective_location
    )
    print(f"✅ AgentManager initialized for dynamic agent loading")
    # Load default agent for backward compatibility and health checks (optional)
    try:
        root_agent, _ = agent_manager.get_agent_by_id(1)  # Default agent
        print(f"✅ Loaded default agent: {root_agent.name} with {len(root_agent.tools)} tools")
    except Exception as e:
        print(f"⚠️  Could not load default agent from AgentManager: {e}")
        print("   This is OK - agents will be loaded dynamically from database")
        print("   To add agents, use the admin panel or API endpoints")
        # Load agent from config as fallback
        from services.agent_loader import load_agent_config, create_agent_from_config
        agent_config = load_agent_config(account_env)
        root_agent = create_agent_from_config(agent_config, effective_project, effective_location)
        print(f"✅ Loaded agent from config as fallback: {root_agent.name}")
else:
    # AgentManager is required - no fallback
    print("❌ AgentManager not available")
    print("   Please run database migrations: python src/database/migrations/run_migrations.py")
    raise RuntimeError("AgentManager is required but not available")

session_service = InMemorySessionService()
runner = Runner(agent=root_agent, app_name="rag_agent_api", session_service=session_service)

# Support running behind a load balancer with per-agent path prefixes
# ROOT_PATH is set per Cloud Run service (e.g., /agent1, /agent2, /agent3)
app = FastAPI(
    title="RAG Agent API",
    description="REST API for the Vertex AI RAG Agent",
    version="1.0.0",
    root_path=os.getenv("ROOT_PATH", ""),
)

# Configure CORS for frontend access
frontend_url = os.getenv("FRONTEND_URL", "")
allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
if frontend_url:
    allowed_origins.append(frontend_url)

# Debug logging for CORS configuration
print(f"CORS Configuration:")
print(f"  FRONTEND_URL env var: {frontend_url}")
print(f"  Allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def start_periodic_tasks():
    import asyncio
    asyncio.create_task(_periodic_session_cleanup())

# ============================================================================
# Register New Modular API Routes
# ============================================================================
if NEW_ROUTES_AVAILABLE:
    app.include_router(users_router)
    app.include_router(agents_router)
    app.include_router(corpora_router)
    app.include_router(admin_router)
    app.include_router(iap_auth_router)
    app.include_router(documents_router)
    app.include_router(chatbot_admin_router)
    app.include_router(google_groups_admin_router)
    app.include_router(model_armor_router)
    print("🚀 API Routes Registered (IAP-only auth):")
    print("  ✅ /api/users/*       - User Management (profile, preferences)")
    print("  ✅ /api/agents/*      - Agent Management (switching, access)")
    print("  ✅ /api/corpora/*     - Corpus Management (access, selection)")
    print("  ✅ /api/admin/*       - Admin Panel (corpus management, audit)")
    print("  ✅ /api/iap/*         - IAP Authentication (Google Cloud IAP)")
    print("  ✅ /api/documents/*   - Document Retrieval (view, access)")
    print("  ✅ /api/admin/chatbot/* - Chatbot User Management (separate access control)")
    print("  ✅ /api/admin/google-groups/* - Google Groups Bridge (mapping & sync)")
    print("  ✅ /api/security/model-armor/* - Model Armor sanitization APIs")
    print("="*70 + "\n")
else:
    print("⚠️  API routes not available")
    print("   To enable features, run: python src/database/migrations/run_migrations.py\n")

@app.get("/")
async def root():
    """Basic health check endpoint."""
    return {"message": "RAG Agent API is running"}

@app.get("/api/health")
async def health_check():
    """Enhanced health check endpoint with region, deployment, and DB connectivity info."""
    import platform
    import subprocess

    # Get Cloud Run revision info
    revision = os.getenv("K_REVISION", "unknown")
    service = os.getenv("K_SERVICE", "unknown")

    # Get region info from metadata service (Cloud Run specific)
    try:
        result = subprocess.run(
            ["curl", "-s", "-H", "Metadata-Flavor: Google",
             "http://metadata.google.internal/computeMetadata/v1/instance/zone"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout:
            zone_parts = result.stdout.strip().split('/')
            zone = zone_parts[-1] if zone_parts else ""
            service_region = '-'.join(zone.split('-')[:-1])
        else:
            service_region = "unknown"
    except Exception:
        service_region = "unknown"

    # ── DB connectivity check ──────────────────────────────────────────────
    db_status = "unknown"
    db_error = None
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = "unreachable"
        db_error = str(e).split('\n')[0][:200]
        logger.error(f"Health check: DB unreachable — {db_error}")

    overall_status = "healthy" if db_status == "connected" else "unhealthy"
    status_code = 200 if db_status == "connected" else 503

    payload = {
        "status": overall_status,
        "db": db_status,
        "service": service,
        "revision": revision,
        "service_region": service_region,
        "vertexai_region": os.getenv("VERTEXAI_LOCATION", "unknown"),
        "google_cloud_location": os.getenv("GOOGLE_CLOUD_LOCATION", "unknown"),
        "account_env": os.getenv("ACCOUNT_ENV", "unknown"),
        "root_path": os.getenv("ROOT_PATH", ""),
        "project_id": os.getenv("PROJECT_ID", "unknown"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "agent_name": getattr(root_agent, 'name', 'unknown') if 'root_agent' in globals() else 'not_loaded',
    }
    if db_error:
        payload["db_error"] = db_error

    from fastapi.responses import JSONResponse
    return JSONResponse(content=payload, status_code=status_code)

@app.post("/api/sessions", response_model=SessionInfo)
async def create_session(user_profile: Optional[UserProfile] = None, current_user: User = Depends(get_current_user_from_middleware)):
    """Create a new user session with agent selection."""
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    try:
        # Get user's default agent if AgentManager available
        agent_id = None
        agent_name = None
        agent_display_name = None
        
        if agent_manager:
            try:
                _, agent_data = agent_manager.get_agent_for_user(current_user.id)
                agent_id = agent_data['id']
                agent_name = agent_data['name']
                agent_display_name = agent_data['display_name']
                logging.info(f"Assigned agent {agent_name} (id={agent_id}) to session {session_id}")
            except Exception as e:
                logging.warning(f"Could not assign agent to session: {e}. Using default.")
        
        # Create ADK session
        session_service.create_session(
            app_name="rag_agent_api",
            user_id="api_user",
            session_id=session_id,
        )

        # Persist session to database using SessionService
        from services.session_service import SessionService
        from models.session import SessionCreate
        
        session_create_data = SessionCreate(
            session_id=session_id,
            user_id=current_user.id,
            active_agent_id=agent_id
        )
        SessionService.create_session(session_create_data)

        # Store session information with agent details (in-memory for quick access)
        sessions[session_id] = {
            "session_id": session_id,
            "user_profile": user_profile.model_dump() if user_profile else None,
            "username": current_user.email,
            "user_id": current_user.id,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "agent_display_name": agent_display_name,
            "created_at": now,
            "last_activity": now,
            "chat_history": [],
        }

        logging.info(
            "session_created",
            extra={
                "session_id": session_id,
                "account_env": account_env,
                "username": current_user.email,
                "agent_id": agent_id,
                "agent_name": agent_name,
            },
        )

        return SessionInfo(
            session_id=session_id,
            user_profile=user_profile,
            username=current_user.email,
            created_at=now,
            last_activity=now,
        )
    except Exception as e:
        logging.error(
            f"session_creation_failed: {e}",
            extra={
                "session_id": session_id,
                "account_env": account_env,
                "username": current_user.email,
            },
        )
        raise

@app.get("/api/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str, current_user: User = Depends(get_current_user_from_middleware)):
    """Get session information."""
    if session_id not in sessions:
        # Create a new session if it doesn't exist (handles server restarts)
        now = datetime.now(timezone.utc)
        session_service.create_session(
            app_name="rag_agent_api", 
            user_id="api_user", 
            session_id=session_id
        )
        sessions[session_id] = {
            "session_id": session_id,
            "user_profile": None,
            "username": current_user.email,
            "created_at": now,
            "last_activity": now,
            "chat_history": []
        }
    
    session = sessions[session_id]
    return SessionInfo(
        session_id=session_id,
        user_profile=UserProfile(**session["user_profile"]) if session["user_profile"] else None,
        username=session["username"],
        created_at=session["created_at"],
        last_activity=session["last_activity"]
    )

@app.put("/api/sessions/{session_id}/profile")
async def update_user_profile(session_id: str, user_profile: UserProfile, current_user: User = Depends(get_current_user_from_middleware)):
    """Update user profile for a session."""
    if session_id not in sessions:
        # Create a new session if it doesn't exist (handles server restarts)
        now = datetime.now()
        session_service.create_session(
            app_name="rag_agent_api", 
            user_id="api_user", 
            session_id=session_id
        )
        sessions[session_id] = {
            "session_id": session_id,
            "user_profile": None,
            "username": current_user.email,
            "created_at": now,
            "last_activity": now,
            "chat_history": []
        }
    
    sessions[session_id]["user_profile"] = user_profile.model_dump()
    sessions[session_id]["last_activity"] = datetime.now(timezone.utc)
    
    return {"message": "Profile updated successfully"}

@app.post("/api/sessions/{session_id}/chat", response_model=ChatResponse)
async def chat_with_agent(session_id: str, chat_message: ChatMessage, current_user: User = Depends(get_current_user_from_middleware)):
    """Send a message to the RAG agent and get a response."""
    if session_id not in sessions:
        # Create a new session if it doesn't exist (handles server restarts)
        now = datetime.now()
        
        # Get user's default agent if AgentManager available
        agent_id = None
        agent_name = None
        agent_display_name = None
        
        if agent_manager:
            try:
                _, agent_data = agent_manager.get_agent_for_user(current_user.id)
                agent_id = agent_data['id']
                agent_name = agent_data['name']
                agent_display_name = agent_data['display_name']
                logging.info(f"Assigned agent {agent_name} (id={agent_id}) to session {session_id}")
            except Exception as e:
                logging.warning(f"Could not assign agent to session: {e}. Using default.")
        
        session_service.create_session(
            app_name="rag_agent_api", 
            user_id="api_user", 
            session_id=session_id
        )
        sessions[session_id] = {
            "session_id": session_id,
            "user_profile": None,
            "username": current_user.email,
            "user_id": current_user.id,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "agent_display_name": agent_display_name,
            "created_at": now,
            "last_activity": now,
            "chat_history": []
        }
    
    # Update last activity
    sessions[session_id]["last_activity"] = datetime.now(timezone.utc)
    
    # Store the user message in chat history
    user_message_entry = {
        "role": "user",
        "content": chat_message.message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    sessions[session_id]["chat_history"].append(user_message_entry)
    
    # Update last activity and increment message counters in database
    from database.connection import get_db_connection
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE user_sessions 
            SET last_activity = %s,
                message_count = COALESCE(message_count, 0) + 2,
                user_query_count = COALESCE(user_query_count, 0) + 1
            WHERE session_id = %s
        """, (datetime.now(timezone.utc), session_id))
        conn.commit()
    
    # Prepare context from user profile if available
    user_context = ""
    if chat_message.user_profile:
        user_context = f"User Profile:\nName: {chat_message.user_profile.name}\n"
        if chat_message.user_profile.preferences:
            user_context += f"Preferences: {chat_message.user_profile.preferences}\n"
        user_context += "\n\n"
    
    # ========== Corpus Access Validation ==========
    # Validate that the user has access to the requested corpora (server-side enforcement)
    from database.repositories.corpus_repository import CorpusRepository
    
    requested_corpora = chat_message.corpora or []
    logging.info(f"[CORPUS] Received corpora from frontend: {requested_corpora}")
    
    # Require at least one corpus to be selected
    if not requested_corpora:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please select at least one corpus before sending a message."
        )
    
    # Get the user's accessible corpora names from the database
    user_id = current_user.id
    accessible_corpora_rows = CorpusRepository.get_user_corpora(user_id, active_only=True)
    accessible_corpus_names = {row['name'] for row in accessible_corpora_rows}
    
    # Filter requested corpora to only those the user has access to
    validated_corpora = [c for c in requested_corpora if c in accessible_corpus_names]
    unauthorized_corpora = [c for c in requested_corpora if c not in accessible_corpus_names]
    
    if unauthorized_corpora:
        logging.warning(
            f"[CORPUS] User {current_user.email} (id={user_id}) attempted to access "
            f"unauthorized corpora: {unauthorized_corpora}. Allowed: {list(accessible_corpus_names)}"
        )
    
    # If all requested corpora were unauthorized, reject the request
    if not validated_corpora:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have access to the selected corpora. "
                   f"Your accessible corpora: {sorted(accessible_corpus_names)}"
        )
    
    # Build corpus instruction for the LLM using only validated corpora
    corpus_list = ", ".join(validated_corpora)
    logging.info(f"[CORPUS] User {current_user.email} querying {len(validated_corpora)} validated corpora: {corpus_list}")
    user_context += f"\n{'='*80}\n"
    user_context += f"CRITICAL INSTRUCTION - READ THIS CAREFULLY:\n"
    user_context += f"The user has selected {len(validated_corpora)} corpora: {corpus_list}\n"
    user_context += f"You MUST use rag_multi_query with corpus_names={validated_corpora}\n"
    user_context += f"DO NOT use rag_query. DO NOT search only 'ai-books'.\n"
    user_context += f"Search ALL {len(validated_corpora)} corpora simultaneously.\n"
    user_context += f"{'='*80}\n\n"
    
    # Combine user context with the message
    full_message = user_context + chat_message.message

    # Optional: sanitize user prompt with Model Armor (disabled by default)
    if os.getenv("MODEL_ARMOR_CHAT_ENABLED", "false").lower() == "true":
        try:
            from services.model_armor_service import ModelArmorService
            if ModelArmorService.is_enabled():
                cfg = ModelArmorService.default_config()
                if cfg.get("project_id") and cfg.get("location") and cfg.get("template_id"):
                    sanitize_result = ModelArmorService.sanitize_user_prompt(
                        text=full_message,
                        project_id=cfg["project_id"],
                        location=cfg["location"],
                        template_id=cfg["template_id"],
                    )
                    match_state = (
                        sanitize_result.get("sanitizationResult", {})
                        .get("filterMatchState")
                    )
                    if match_state and match_state != "NO_MATCH_FOUND":
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail={
                                "message": "Prompt blocked by Model Armor",
                                "filterMatchState": match_state,
                            },
                        )
        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"Model Armor prompt sanitization failed: {e}")
    
    try:
        # Get the agent for this session
        session_agent = root_agent  # Default
        agent_id = sessions[session_id].get("agent_id")
        
        logging.info(f"Chat endpoint - session {session_id}: agent_id={agent_id}, agent_manager={'available' if agent_manager else 'not available'}")
        
        if agent_manager and agent_id:
            try:
                session_agent, agent_data = agent_manager.get_agent_by_id(agent_id)
                logging.info(f"Loaded agent '{agent_data['name']}' with {len(session_agent.tools)} tools for session {session_id}")
            except Exception as e:
                logging.error(f"Could not load session agent: {e}. Using default.", exc_info=True)
        
        # Create a runner with the session-specific agent
        session_runner = Runner(
            agent=session_agent,
            app_name="rag_agent_api",
            session_service=session_service
        )
        
        # Ensure ADK session exists - only create if it doesn't exist
        try:
            adk_session = session_service.get_session(
                app_name="rag_agent_api", 
                user_id="api_user", 
                session_id=session_id
            )
        except:
            # Only create if session doesn't exist
            adk_session = session_service.create_session(
                app_name="rag_agent_api", 
                user_id="api_user", 
                session_id=session_id
            )
        
        # Inject user identity and accessible corpora into ADK session state
        # so that tools can enforce corpus-level access control
        adk_session.state["user_id"] = current_user.id
        adk_session.state["user_email"] = current_user.email
        adk_session.state["accessible_corpus_names"] = sorted(accessible_corpus_names)
        
        # Create user content for ADK
        user_content = types.Content(
            role='user', 
            parts=[types.Part(text=full_message)]
        )
        
        # Run the agent and collect response with retry logic for rate limits
        response_text = ""
        max_retries = 3
        
        for attempt in range(max_retries + 1):
            try:
                async for event in session_runner.run_async(
                    user_id="api_user", 
                    session_id=session_id, 
                    new_message=user_content
                ):
                    if event.is_final_response() and event.content and event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                response_text += part.text
                break  # Success, exit retry loop
                
            except Exception as e:
                error_str = str(e)
                # Check if it's a 429 rate limit error
                if "429" in error_str and "RESOURCE_EXHAUSTED" in error_str:
                    if attempt < max_retries:
                        import asyncio
                        wait_time = (2 ** attempt) + (0.1 * attempt)  # 1s, 2.1s, 4.2s
                        logger.warning(
                            f"Rate limit hit for agent chat (attempt {attempt + 1}/{max_retries + 1}). "
                            f"Retrying in {wait_time:.1f}s..."
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Rate limit exceeded after {max_retries + 1} attempts for agent chat")
                        raise HTTPException(
                            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Service temporarily unavailable due to rate limiting. Please try again in a few moments."
                        )
                else:
                    # Not a rate limit error, re-raise immediately
                    raise
        
        # Optional: sanitize model response with Model Armor (disabled by default)
        if os.getenv("MODEL_ARMOR_CHAT_ENABLED", "false").lower() == "true":
            try:
                from services.model_armor_service import ModelArmorService
                if ModelArmorService.is_enabled():
                    cfg = ModelArmorService.default_config()
                    if cfg.get("project_id") and cfg.get("location") and cfg.get("template_id"):
                        sanitize_result = ModelArmorService.sanitize_model_response(
                            text=response_text,
                            project_id=cfg["project_id"],
                            location=cfg["location"],
                            template_id=cfg["template_id"],
                        )
                        match_state = (
                            sanitize_result.get("sanitizationResult", {})
                            .get("filterMatchState")
                        )
                        if match_state and match_state != "NO_MATCH_FOUND":
                            response_text = "Response blocked by Model Armor."
            except Exception as e:
                logging.error(f"Model Armor response sanitization failed: {e}")

        # Store the agent response in chat history
        agent_message_entry = {
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        sessions[session_id]["chat_history"].append(agent_message_entry)
        
        # Update last activity for agent response
        from database.connection import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE user_sessions 
                SET last_activity = %s
                WHERE session_id = %s
            """, (datetime.now(timezone.utc), session_id))
            conn.commit()
        
        return ChatResponse(
            response=response_text,
            timestamp=datetime.now(timezone.utc),
            session_id=session_id
        )
        
    except Exception as e:
        import traceback
        error_details = f"Error processing request: {str(e)}"
        traceback_details = traceback.format_exc()
        print(f"CHAT ERROR: {error_details}")
        print(f"CHAT TRACEBACK: {traceback_details}")
        raise HTTPException(status_code=500, detail=error_details)

@app.get("/api/sessions/{session_id}/history")
async def get_chat_history(session_id: str, current_user: User = Depends(get_current_user_from_middleware)):
    """Get chat history for a session."""
    if session_id not in sessions:
        # Return empty history instead of 404 when session doesn't exist
        # This handles cases where server restarted and sessions were cleared
        return {"chat_history": []}
    
    return {"chat_history": sessions[session_id]["chat_history"]}

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str, current_user: User = Depends(get_current_user_from_middleware)):
    """Delete a session."""
    if session_id not in sessions:
        # Return success even if session doesn't exist (idempotent operation)
        return {"message": "Session deleted successfully"}
    
    del sessions[session_id]
    return {"message": "Session deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
