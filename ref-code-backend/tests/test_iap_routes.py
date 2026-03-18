"""
Integration tests for IAP API routes.
Tests /api/iap/* endpoints.
"""

import sys
import os
from pathlib import Path

# Add src directory to path
backend_dir = Path(__file__).parent.parent
src_dir = backend_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from models.user import User


@pytest.fixture
def mock_iap_enabled():
    """Mock IAP as properly configured."""
    with patch.dict('os.environ', {
        'PROJECT_NUMBER': '123456789',
        'BACKEND_SERVICE_ID': '9876543210'
    }):
        yield


@pytest.fixture
def mock_iap_disabled():
    """Mock IAP as not configured."""
    with patch.dict('os.environ', {}, clear=True):
        yield


class TestIAPRoutes:
    """Test suite for IAP API routes."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test client."""
        # Import after environment is set
        from api.server import app
        self.client = TestClient(app)
    
    @patch('middleware.iap_auth_middleware.IAPService.verify_iap_jwt')
    @patch('middleware.iap_auth_middleware.IAPService.extract_user_info')
    @patch('middleware.iap_auth_middleware.UserService.get_user_by_email')
    @patch('middleware.iap_auth_middleware.UserService.update_last_login')
    def test_get_iap_me_success(
        self, mock_update_login, mock_get_user, mock_extract, mock_verify
    ):
        """Test GET /api/iap/me with valid IAP authentication."""
        # Mock JWT verification
        mock_verify.return_value = {
            'iss': 'https://cloud.google.com/iap',
            'email': 'user@develom.com',
            'sub': 'google-123'
        }
        
        # Mock user info
        mock_extract.return_value = {
            'email': 'user@develom.com',
            'google_id': 'google-123',
            'name': 'Test User'
        }
        
        # Mock existing user
        mock_user = User(
            id=1,
            username='testuser',
            email='user@develom.com',
            full_name='Test User',
            google_id='google-123',
            auth_provider='iap',
            is_active=True,
            created_at='2026-01-10T00:00:00',
            updated_at='2026-01-10T00:00:00'
        )
        mock_get_user.return_value = mock_user
        
        response = self.client.get(
            "/api/iap/me",
            headers={"X-Goog-IAP-JWT-Assertion": "valid.jwt.token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['email'] == 'user@develom.com'
        assert data['google_id'] == 'google-123'
        assert data['auth_provider'] == 'iap'
    
    def test_get_iap_me_missing_header(self):
        """Test GET /api/iap/me without IAP header."""
        response = self.client.get("/api/iap/me")
        
        assert response.status_code == 401
        assert 'Missing IAP authentication' in response.json()['detail']
    
    @patch('api.routes.iap_auth.IAPService.is_iap_enabled')
    @patch('api.routes.iap_auth.IAPService.get_iap_audience')
    def test_get_iap_status_enabled(self, mock_get_audience, mock_is_enabled, mock_iap_enabled):
        """Test GET /api/iap/status when IAP is enabled."""
        mock_is_enabled.return_value = True
        mock_get_audience.return_value = '/projects/123456789/global/backendServices/9876543210'
        
        response = self.client.get("/api/iap/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data['iap_enabled'] is True
        assert data['iap_audience'] == '/projects/123456789/global/backendServices/9876543210'
        assert 'properly configured' in data['message']
    
    @patch('api.routes.iap_auth.IAPService.is_iap_enabled')
    @patch('api.routes.iap_auth.IAPService.get_iap_audience')
    def test_get_iap_status_disabled(self, mock_get_audience, mock_is_enabled, mock_iap_disabled):
        """Test GET /api/iap/status when IAP is not configured."""
        mock_is_enabled.return_value = False
        mock_get_audience.return_value = None
        
        response = self.client.get("/api/iap/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data['iap_enabled'] is False
        assert data['iap_audience'] is None
        assert 'not configured' in data['message']
    
    @patch('api.routes.iap_auth.IAPService.verify_iap_jwt')
    @patch('api.routes.iap_auth.IAPService.extract_user_info')
    def test_verify_iap_token_success(self, mock_extract, mock_verify):
        """Test GET /api/iap/verify with valid token."""
        mock_verify.return_value = {
            'iss': 'https://cloud.google.com/iap',
            'aud': '/projects/123/global/backendServices/456',
            'sub': 'google-123',
            'email': 'user@develom.com',
            'exp': 1234567890
        }
        
        mock_extract.return_value = {
            'email': 'user@develom.com',
            'google_id': 'google-123',
            'name': 'Test User'
        }
        
        response = self.client.get(
            "/api/iap/verify",
            headers={"X-Goog-IAP-JWT-Assertion": "valid.jwt.token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['valid'] is True
        assert data['user_info']['email'] == 'user@develom.com'
        assert data['token_payload']['iss'] == 'https://cloud.google.com/iap'
    
    def test_verify_iap_token_missing_header(self):
        """Test GET /api/iap/verify without JWT header."""
        response = self.client.get("/api/iap/verify")
        
        assert response.status_code == 401
        assert 'No IAP JWT found' in response.json()['detail']
    
    @patch('api.routes.iap_auth.IAPService.verify_iap_jwt')
    def test_verify_iap_token_invalid(self, mock_verify):
        """Test GET /api/iap/verify with invalid token."""
        mock_verify.side_effect = ValueError('Invalid signature')
        
        response = self.client.get(
            "/api/iap/verify",
            headers={"X-Goog-IAP-JWT-Assertion": "invalid.jwt.token"}
        )
        
        assert response.status_code == 401
        assert 'Invalid IAP token' in response.json()['detail']
    
    def test_get_iap_headers_with_iap(self):
        """Test GET /api/iap/headers with IAP headers present."""
        response = self.client.get(
            "/api/iap/headers",
            headers={
                "X-Goog-IAP-JWT-Assertion": "test.jwt.token",
                "X-Goog-Authenticated-User-Email": "accounts.google.com:user@develom.com",
                "X-Goog-Authenticated-User-ID": "accounts.google.com:123456"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'iap_headers' in data
        assert data['has_jwt'] is True
        assert 'x-goog-iap-jwt-assertion' in data['iap_headers']
    
    def test_get_iap_headers_without_iap(self):
        """Test GET /api/iap/headers without IAP headers."""
        response = self.client.get("/api/iap/headers")
        
        assert response.status_code == 200
        data = response.json()
        assert 'No IAP headers found' in data['message']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
