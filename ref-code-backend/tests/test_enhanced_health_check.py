"""
Test enhanced health check endpoint with region information.
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient


def setup_test_environment():
    """Set up test environment with required stubs and paths."""
    # Mock Google Cloud imports that might not be available in test environment
    sys.modules['google.cloud'] = MagicMock()
    sys.modules['google.cloud.aiplatform'] = MagicMock()
    sys.modules['google.cloud.storage'] = MagicMock()
    sys.modules['google.genai'] = MagicMock()
    sys.modules['google.adk'] = MagicMock()
    
    # Set required environment variables for testing
    os.environ["PROJECT_ID"] = "adk-rag-ma"
    os.environ["GOOGLE_CLOUD_LOCATION"] = "us-west1"
    os.environ["VERTEXAI_LOCATION"] = "us-west1"
    os.environ["ACCOUNT_ENV"] = "develom"
    os.environ["ROOT_PATH"] = ""
    os.environ["K_SERVICE"] = "backend"
    os.environ["K_REVISION"] = "backend-00001-abc"


def build_test_client() -> TestClient:
    """Build test client with proper module imports."""
    setup_test_environment()
    
    # Ensure repo root is on sys.path
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    
    # Ensure backend directory is on sys.path
    backend_dir = repo_root / "backend"
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    
    # Fresh import to apply environment variables
    if "backend.src.api.server" in sys.modules:
        del sys.modules["backend.src.api.server"]
    
    import importlib
    server = importlib.import_module("backend.src.api.server")
    return TestClient(server.app)


def test_basic_health_check():
    """Test basic health check endpoint returns expected message."""
    client = build_test_client()
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "RAG Agent API is running"


def test_enhanced_health_check_structure():
    """Test enhanced health check endpoint returns proper structure."""
    client = build_test_client()
    response = client.get("/api/health")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields are present
    required_fields = [
        "status", "service", "revision", "service_region",
        "vertexai_region", "google_cloud_location", "account_env",
        "root_path", "project_id", "timestamp", "python_version", "agent_name"
    ]
    
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"


def test_enhanced_health_check_values():
    """Test enhanced health check endpoint returns expected values."""
    client = build_test_client()
    response = client.get("/api/health")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check specific values from environment
    assert data["status"] == "healthy"
    assert data["service"] == "backend"
    assert data["revision"] == "backend-00001-abc"
    assert data["vertexai_region"] == "us-west1"
    assert data["google_cloud_location"] == "us-west1"
    assert data["account_env"] == "develom"
    assert data["root_path"] == ""
    assert data["project_id"] == "adk-rag-ma"
    
    # Check timestamp format (ISO format)
    assert "T" in data["timestamp"]
    assert data["timestamp"].endswith("Z") or "+" in data["timestamp"]
    
    # Check python version is present
    assert len(data["python_version"]) > 0


@patch('subprocess.run')
def test_health_check_with_metadata_service_success(mock_subprocess):
    """Test health check when metadata service returns valid zone info."""
    # Mock successful metadata service response
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "projects/123456789/zones/us-west1-a"
    mock_subprocess.return_value = mock_result
    
    client = build_test_client()
    response = client.get("/api/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["service_region"] == "us-west1"


@patch('subprocess.run')
def test_health_check_with_metadata_service_failure(mock_subprocess):
    """Test health check when metadata service fails."""
    # Mock failed metadata service response
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_subprocess.return_value = mock_result
    
    client = build_test_client()
    response = client.get("/api/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["service_region"] == "unknown"


@patch('subprocess.run')
def test_health_check_with_metadata_service_exception(mock_subprocess):
    """Test health check when metadata service raises exception."""
    # Mock exception during metadata service call
    mock_subprocess.side_effect = Exception("Network error")
    
    client = build_test_client()
    response = client.get("/api/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["service_region"] == "unknown"


def test_health_check_json_serializable():
    """Test that health check response is properly JSON serializable."""
    client = build_test_client()
    response = client.get("/api/health")
    
    assert response.status_code == 200
    
    # Ensure response can be serialized to JSON without errors
    data = response.json()
    json_str = json.dumps(data)
    
    # Ensure it can be deserialized back
    parsed_data = json.loads(json_str)
    assert parsed_data == data


def test_health_check_different_environments():
    """Test health check with different environment configurations."""
    test_cases = [
        {
            "ACCOUNT_ENV": "agent1",
            "ROOT_PATH": "/agent1",
            "K_SERVICE": "backend-agent1"
        },
        {
            "ACCOUNT_ENV": "agent2", 
            "ROOT_PATH": "/agent2",
            "K_SERVICE": "backend-agent2"
        },
        {
            "ACCOUNT_ENV": "develom",
            "ROOT_PATH": "",
            "K_SERVICE": "backend"
        }
    ]
    
    for test_env in test_cases:
        # Update environment
        for key, value in test_env.items():
            os.environ[key] = value
        
        client = build_test_client()
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["account_env"] == test_env["ACCOUNT_ENV"]
        assert data["root_path"] == test_env["ROOT_PATH"]
        assert data["service"] == test_env["K_SERVICE"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
