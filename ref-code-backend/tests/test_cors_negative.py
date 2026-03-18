import os
import sys
import types
import importlib
from pathlib import Path
from fastapi.testclient import TestClient

# --- Stubs to avoid external dependencies (ADK/GenAI) ---
_genai_types = types.ModuleType("google.genai.types")
class _DummyPart:
    def __init__(self, text: str = ""): self.text = text
class _DummyContent:
    def __init__(self, role: str = "user", parts=None): self.role = role; self.parts = parts or []
_genai_types.Part = _DummyPart
_genai_types.Content = _DummyContent

_adk_runners = types.ModuleType("google.adk.runners")
class _DummyRunner:
    def __init__(self, *args, **kwargs): pass
    def run_async(self, *args, **kwargs):
        async def _aiter():
            class Event:
                def is_final_response(self): return True
                @property
                def content(self):
                    class _C: parts = [_DummyPart(text="ok")]
                    return _C()
            yield Event()
        return _aiter()
_adk_runners.Runner = _DummyRunner

_adk_sessions = types.ModuleType("google.adk.sessions")
class _DummySessionService:
    def create_session(self, *args, **kwargs): pass
    def get_session(self, *args, **kwargs): return {}
_adk_sessions.InMemorySessionService = _DummySessionService

_adk_agents = types.ModuleType("google.adk.agents")
class _DummyAgent:
    def __init__(self, *args, **kwargs):
        self.name = kwargs.get("name", "Agent")
        self.tools = kwargs.get("tools", [])
_adk_agents.Agent = _DummyAgent

_adk_models = types.ModuleType("google.adk.models")
class _DummyGemini:
    def __init__(self, *args, **kwargs): pass
_adk_models.Gemini = _DummyGemini

_adk_tools = types.ModuleType("google.adk.tools")
_adk_tool_context = types.ModuleType("google.adk.tools.tool_context")
class _DummyToolContext:
    def __init__(self): self.state = {}
_adk_tool_context.ToolContext = _DummyToolContext

# Wire stubs
sys.modules.setdefault("google", types.ModuleType("google"))
sys.modules.setdefault("google.genai", types.ModuleType("google.genai"))
sys.modules["google.genai.types"] = _genai_types
sys.modules["google.adk"] = types.ModuleType("google.adk")
sys.modules["google.adk.runners"] = _adk_runners
sys.modules["google.adk.sessions"] = _adk_sessions
sys.modules["google.adk.agents"] = _adk_agents
sys.modules["google.adk.models"] = _adk_models
sys.modules["google.adk.tools"] = _adk_tools
sys.modules["google.adk.tools.tool_context"] = _adk_tool_context


def build_client(frontend_origin: str) -> TestClient:
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    backend_dir = repo_root / "backend"
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    os.environ["FRONTEND_URL"] = frontend_origin
    if "backend.src.api.server" in sys.modules:
        del sys.modules["backend.src.api.server"]
    server = importlib.import_module("backend.src.api.server")
    return TestClient(server.app)


def test_disallowed_origin_does_not_get_acao(tmp_path: Path):
    allowed = "https://frontend.example.com"
    disallowed = "https://evil.example.com"

    client = build_client(allowed)

    # Request with disallowed Origin
    r = client.get("/", headers={"Origin": disallowed})
    assert r.status_code == 200

    acao = r.headers.get("access-control-allow-origin")
    # If ACAO is present, it must not echo the disallowed origin
    if acao is not None:
        assert acao != disallowed
