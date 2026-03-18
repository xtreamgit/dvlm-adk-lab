import os
import sys
import types
from pathlib import Path
from fastapi.testclient import TestClient
import importlib


# --- Lightweight stubs to avoid importing heavy Google libs during tests ---
# Stub google.genai.types
genai_types = types.ModuleType("google.genai.types")
class _DummyPart:
    def __init__(self, text: str = ""): self.text = text
class _DummyContent:
    def __init__(self, role: str = "user", parts=None): self.role = role; self.parts = parts or []
genai_types.Part = _DummyPart
genai_types.Content = _DummyContent

# Stub google.adk
adk_runners = types.ModuleType("google.adk.runners")
class _DummyRunner:
    def __init__(self, *args, **kwargs): pass
    async def run_async(self, *args, **kwargs):
        async def _aiter():
            class Event:
                def is_final_response(self): return True
                @property
                def content(self):
                    class _C: parts = [_DummyPart(text="ok")]
                    return _C()
            yield Event()
        return _aiter()
adk_runners.Runner = _DummyRunner

adk_sessions = types.ModuleType("google.adk.sessions")
class _DummySessionService:
    def create_session(self, *args, **kwargs): pass
    def get_session(self, *args, **kwargs): return {}
adk_sessions.InMemorySessionService = _DummySessionService

# Stub google.adk.agents and google.adk.models used by account agent configs
adk_agents = types.ModuleType("google.adk.agents")
class _DummyAgent:
    def __init__(self, *args, **kwargs):
        self.name = kwargs.get("name", "Agent")
        self.tools = kwargs.get("tools", [])
adk_agents.Agent = _DummyAgent

adk_models = types.ModuleType("google.adk.models")
class _DummyGemini:
    def __init__(self, *args, **kwargs): pass
adk_models.Gemini = _DummyGemini

# Stub google.adk.tools.tool_context
adk_tools = types.ModuleType("google.adk.tools")
adk_tool_context = types.ModuleType("google.adk.tools.tool_context")
class _DummyToolContext:
    def __init__(self):
        self.state = {}
adk_tool_context.ToolContext = _DummyToolContext

# Wire stubs into sys.modules
sys.modules.setdefault("google", types.ModuleType("google"))
sys.modules.setdefault("google.genai", types.ModuleType("google.genai"))
sys.modules["google.genai.types"] = genai_types
sys.modules["google.adk"] = types.ModuleType("google.adk")
sys.modules["google.adk.runners"] = adk_runners
sys.modules["google.adk.sessions"] = adk_sessions
sys.modules["google.adk.agents"] = adk_agents
sys.modules["google.adk.models"] = adk_models
sys.modules["google.adk.tools"] = adk_tools
sys.modules["google.adk.tools.tool_context"] = adk_tool_context


def build_client(frontend_origin: str | None = None) -> TestClient:
    # Configure CORS origin for the app under test
    if frontend_origin:
        os.environ["FRONTEND_URL"] = frontend_origin
    # Import after stubs and env are set
    # Ensure repo root is on sys.path so that "backend" package resolves
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    # Ensure backend directory is also on sys.path so that "src" package resolves
    backend_dir = repo_root / "backend"
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    # Ensure a fresh import so env is applied to module-level CORS setup
    if "backend.src.api.server" in sys.modules:
        del sys.modules["backend.src.api.server"]
    server = importlib.import_module("backend.src.api.server")
    return TestClient(server.app)


def test_health_root_ok():
    client = build_client(frontend_origin="https://frontend.example.com")
    r = client.get("/")
    assert r.status_code == 200
    assert r.json().get("message") == "RAG Agent API is running"


def test_cors_allows_configured_frontend():
    origin = "https://frontend.example.com"
    client = build_client(frontend_origin=origin)
    # Verify server configuration contains the origin
    server = importlib.import_module("backend.src.api.server")
    assert origin in server.allowed_origins
    # Make a simple GET with Origin header and check response success
    r = client.get("/", headers={"Origin": origin})
    assert r.status_code == 200
    # If CORS header is present, it must match the origin and not be wildcard
    acao = r.headers.get("access-control-allow-origin")
    if acao is not None:
        assert acao == origin
