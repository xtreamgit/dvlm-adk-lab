"""
Integration tests for IAP authentication middleware.
Tests middleware behavior with different authentication scenarios.
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
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from models.user import User
from middleware.iap_auth_middleware import (
    get_current_user_iap,
    get_current_user_optional_iap,
    get_current_user_hybrid
)


@pytest.fixture
def app():
    """Create test FastAPI app."""
    app = FastAPI()
    
    @app.get("/iap-required")
    async def iap_required_route(user: User = Depends(get_current_user_iap)):
        return {"email": user.email, "auth_provider": user.auth_provider}
    
    @app.get("/iap-optional")
    async def iap_optional_route(user: User = Depends(get_current_user_optional_iap)):
        if user:
            return {"authenticated": True, "email": user.email}
        return {"authenticated": False}
    
    @app.get("/hybrid")
    async def hybrid_route(user: User = Depends(get_current_user_hybrid)):
        return {"email": user.email, "auth_provider": user.auth_provider}
    
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestIAPMiddleware:
    """Test suite for IAP authentication middleware."""
    
    @patch('middleware.iap_auth_middleware.IAPService.verify_iap_jwt')
    @patch('middleware.iap_auth_middleware.IAPService.extract_user_info')
    @patch('middleware.iap_auth_middleware.UserService.get_user_by_email')
    @patch('middleware.iap_auth_middleware.UserService.update_last_login')
    def test_get_current_user_iap_existing_user(
        self, mock_update_login, mock_get_user, mock_extract, mock_verify, client
    ):
        """Test IAP authentication with existing user."""
        # Mock JWT verification
        mock_verify.return_value = {
            'iss': 'https://cloud.google.com/iap',
            'email': 'user@develom.com',
            'sub': 'google-123'
        }
        
        # Mock user info extraction
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
        
        # Make request with IAP headers
        response = client.get(
            "/iap-required",
            headers={"X-Goog-IAP-JWT-Assertion": "valid.jwt.token"}
        )
        
        assert response.status_code == 200
        assert response.json()['email'] == 'user@develom.com'
        mock_verify.assert_called_once()
        mock_update_login.assert_called_once()
    
    @patch('middleware.iap_auth_middleware.IAPService.verify_iap_jwt')
    @patch('middleware.iap_auth_middleware.IAPService.extract_user_info')
    @patch('middleware.iap_auth_middleware.UserService.get_user_by_email')
    @patch('middleware.iap_auth_middleware.UserService.create_user_from_iap')
    def test_get_current_user_iap_new_user(
        self, mock_create_user, mock_get_user, mock_extract, mock_verify, client
    ):
        """Test IAP authentication creates new user."""
        # Mock JWT verification
        mock_verify.return_value = {
            'iss': 'https://cloud.google.com/iap',
            'email': 'newuser@develom.com',
            'sub': 'google-456'
        }
        
        # Mock user info extraction
        mock_extract.return_value = {
            'email': 'newuser@develom.com',
            'google_id': 'google-456',
            'name': 'New User'
        }
        
        # Mock no existing user
        mock_get_user.return_value = None
        
        # Mock created user
        mock_new_user = User(
            id=2,
            username='newuser',
            email='newuser@develom.com',
            full_name='New User',
            google_id='google-456',
            auth_provider='iap',
            is_active=True,
            created_at='2026-01-10T00:00:00',
            updated_at='2026-01-10T00:00:00'
        )
        mock_create_user.return_value = mock_new_user
        
        # Make request with IAP headers
        response = client.get(
            "/iap-required",
            headers={"X-Goog-IAP-JWT-Assertion": "valid.jwt.token"}
        )
        
        assert response.status_code == 200
        assert response.json()['email'] == 'newuser@develom.com'
        mock_create_user.assert_called_once_with(
            email='newuser@develom.com',
            google_id='google-456',
            full_name='New User'
        )
    
    def test_get_current_user_iap_missing_header(self, client):
        """Test IAP authentication fails without JWT header."""
        response = client.get("/iap-required")
        
        assert response.status_code == 401
        assert 'Missing IAP authentication' in response.json()['detail']
    
    @patch('middleware.iap_auth_middleware.IAPService.verify_iap_jwt')
    def test_get_current_user_iap_invalid_token(self, mock_verify, client):
        """Test IAP authentication fails with invalid token."""
        # Mock verification failure
        mock_verify.side_effect = ValueError('Invalid token signature')
        
        response = client.get(
            "/iap-required",
            headers={"X-Goog-IAP-JWT-Assertion": "invalid.jwt.token"}
        )
        
        assert response.status_code == 401
        assert 'Invalid IAP token' in response.json()['detail']
    
    @patch('middleware.iap_auth_middleware.IAPService.verify_iap_jwt')
    @patch('middleware.iap_auth_middleware.IAPService.extract_user_info')
    @patch('middleware.iap_auth_middleware.UserService.get_user_by_email')
    def test_get_current_user_iap_inactive_user(
        self, mock_get_user, mock_extract, mock_verify, client
    ):
        """Test IAP authentication fails for inactive user."""
        # Mock JWT verification
        mock_verify.return_value = {'iss': 'https://cloud.google.com/iap'}
        mock_extract.return_value = {
            'email': 'inactive@develom.com',
            'google_id': 'google-789',
            'name': 'Inactive User'
        }
        
        # Mock inactive user
        mock_user = User(
            id=3,
            username='inactive',
            email='inactive@develom.com',
            full_name='Inactive User',
            is_active=False,  # Inactive!
            created_at='2026-01-10T00:00:00',
            updated_at='2026-01-10T00:00:00'
        )
        mock_get_user.return_value = mock_user
        
        response = client.get(
            "/iap-required",
            headers={"X-Goog-IAP-JWT-Assertion": "valid.jwt.token"}
        )
        
        assert response.status_code == 403
        assert 'inactive' in response.json()['detail'].lower()
    
    def test_get_current_user_optional_iap_no_header(self, client):
        """Test optional IAP authentication works without header."""
        response = client.get("/iap-optional")
        
        assert response.status_code == 200
        assert response.json()['authenticated'] is False
    
    @patch('middleware.iap_auth_middleware.IAPService.verify_iap_jwt')
    @patch('middleware.iap_auth_middleware.IAPService.extract_user_info')
    @patch('middleware.iap_auth_middleware.UserService.get_user_by_email')
    @patch('middleware.iap_auth_middleware.UserService.update_last_login')
    def test_get_current_user_optional_iap_with_header(
        self, mock_update_login, mock_get_user, mock_extract, mock_verify, client
    ):
        """Test optional IAP authentication works with valid header."""
        mock_verify.return_value = {'iss': 'https://cloud.google.com/iap'}
        mock_extract.return_value = {
            'email': 'user@develom.com',
            'google_id': 'google-123',
            'name': 'Test User'
        }
        
        mock_user = User(
            id=1,
            username='testuser',
            email='user@develom.com',
            full_name='Test User',
            is_active=True,
            created_at='2026-01-10T00:00:00',
            updated_at='2026-01-10T00:00:00'
        )
        mock_get_user.return_value = mock_user
        
        response = client.get(
            "/iap-optional",
            headers={"X-Goog-IAP-JWT-Assertion": "valid.jwt.token"}
        )
        
        assert response.status_code == 200
        assert response.json()['authenticated'] is True
        assert response.json()['email'] == 'user@develom.com'
    
    @patch('middleware.iap_auth_middleware.IAPService.verify_iap_jwt')
    @patch('middleware.iap_auth_middleware.IAPService.extract_user_info')
    @patch('middleware.iap_auth_middleware.UserService.get_user_by_email')
    @patch('middleware.iap_auth_middleware.UserService.update_last_login')
    def test_hybrid_auth_with_iap(
        self, mock_update_login, mock_get_user, mock_extract, mock_verify, client
    ):
        """Test hybrid authentication prioritizes IAP."""
        mock_verify.return_value = {'iss': 'https://cloud.google.com/iap'}
        mock_extract.return_value = {
            'email': 'user@develom.com',
            'google_id': 'google-123',
            'name': 'Test User'
        }
        
        mock_user = User(
            id=1,
            username='testuser',
            email='user@develom.com',
            full_name='Test User',
            auth_provider='iap',
            is_active=True,
            created_at='2026-01-10T00:00:00',
            updated_at='2026-01-10T00:00:00'
        )
        mock_get_user.return_value = mock_user
        
        response = client.get(
            "/hybrid",
            headers={"X-Goog-IAP-JWT-Assertion": "valid.jwt.token"}
        )
        
        assert response.status_code == 200
        assert response.json()['email'] == 'user@develom.com'
        assert response.json()['auth_provider'] == 'iap'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
