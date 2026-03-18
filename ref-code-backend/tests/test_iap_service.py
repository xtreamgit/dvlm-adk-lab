"""
Unit tests for IAP service.
Tests IAP JWT verification and user info extraction.
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
from unittest.mock import patch, MagicMock
from services.iap_service import IAPService


class TestIAPService:
    """Test suite for IAPService."""
    
    def test_extract_user_info_success(self):
        """Test extracting user info from decoded JWT."""
        decoded_jwt = {
            'email': 'user@develom.com',
            'sub': 'google-user-id-12345',
            'name': 'Test User'
        }
        
        user_info = IAPService.extract_user_info(decoded_jwt)
        
        assert user_info['email'] == 'user@develom.com'
        assert user_info['google_id'] == 'google-user-id-12345'
        assert user_info['name'] == 'Test User'
    
    def test_extract_user_info_without_name(self):
        """Test extracting user info when name is not in JWT."""
        decoded_jwt = {
            'email': 'user@develom.com',
            'sub': 'google-user-id-12345'
        }
        
        user_info = IAPService.extract_user_info(decoded_jwt)
        
        assert user_info['email'] == 'user@develom.com'
        assert user_info['google_id'] == 'google-user-id-12345'
        assert user_info['name'] == 'user'  # Should extract from email
    
    @patch.dict('os.environ', {
        'PROJECT_NUMBER': '123456789',
        'BACKEND_SERVICE_ID': '9876543210'
    })
    def test_get_iap_audience_configured(self):
        """Test getting IAP audience when properly configured."""
        # Re-import to pick up environment variables
        import importlib
        from services import iap_service
        importlib.reload(iap_service)
        
        audience = iap_service.IAPService.get_iap_audience()
        
        assert audience == '/projects/123456789/global/backendServices/9876543210'
    
    @patch.dict('os.environ', {}, clear=True)
    def test_get_iap_audience_not_configured(self):
        """Test getting IAP audience when not configured."""
        # Re-import to pick up environment variables
        import importlib
        from services import iap_service
        importlib.reload(iap_service)
        
        audience = iap_service.IAPService.get_iap_audience()
        
        assert audience is None
    
    @patch.dict('os.environ', {
        'PROJECT_NUMBER': '123456789',
        'BACKEND_SERVICE_ID': '9876543210'
    })
    def test_is_iap_enabled_true(self):
        """Test IAP enabled check when configured."""
        import importlib
        from services import iap_service
        importlib.reload(iap_service)
        
        is_enabled = iap_service.IAPService.is_iap_enabled()
        
        assert is_enabled is True
    
    @patch.dict('os.environ', {}, clear=True)
    def test_is_iap_enabled_false(self):
        """Test IAP enabled check when not configured."""
        import importlib
        from services import iap_service
        importlib.reload(iap_service)
        
        is_enabled = iap_service.IAPService.is_iap_enabled()
        
        assert is_enabled is False
    
    @patch('services.iap_service.id_token.verify_oauth2_token')
    @patch.dict('os.environ', {
        'PROJECT_NUMBER': '123456789',
        'BACKEND_SERVICE_ID': '9876543210'
    })
    def test_verify_iap_jwt_success(self, mock_verify):
        """Test successful IAP JWT verification."""
        # Re-import to pick up environment variables
        import importlib
        from services import iap_service
        importlib.reload(iap_service)
        
        # Mock successful verification
        mock_verify.return_value = {
            'iss': 'https://cloud.google.com/iap',
            'aud': '/projects/123456789/global/backendServices/9876543210',
            'sub': 'google-user-id-12345',
            'email': 'user@develom.com',
            'exp': 1234567890
        }
        
        result = iap_service.IAPService.verify_iap_jwt('valid.jwt.token')
        
        assert result['email'] == 'user@develom.com'
        assert result['sub'] == 'google-user-id-12345'
        mock_verify.assert_called_once()
    
    @patch('services.iap_service.id_token.verify_oauth2_token')
    @patch.dict('os.environ', {
        'PROJECT_NUMBER': '123456789',
        'BACKEND_SERVICE_ID': '9876543210'
    })
    def test_verify_iap_jwt_invalid_issuer(self, mock_verify):
        """Test IAP JWT verification with invalid issuer."""
        import importlib
        from services import iap_service
        importlib.reload(iap_service)
        
        # Mock verification with wrong issuer
        mock_verify.return_value = {
            'iss': 'https://evil.com',
            'aud': '/projects/123456789/global/backendServices/9876543210',
            'sub': 'google-user-id-12345',
            'email': 'user@develom.com'
        }
        
        with pytest.raises(ValueError, match='Invalid issuer'):
            iap_service.IAPService.verify_iap_jwt('invalid.jwt.token')
    
    @patch('services.iap_service.id_token.verify_oauth2_token')
    @patch.dict('os.environ', {
        'PROJECT_NUMBER': '123456789',
        'BACKEND_SERVICE_ID': '9876543210'
    })
    def test_verify_iap_jwt_expired(self, mock_verify):
        """Test IAP JWT verification with expired token."""
        import importlib
        from services import iap_service
        importlib.reload(iap_service)
        
        # Mock expired token
        mock_verify.side_effect = Exception('Token expired')
        
        with pytest.raises(ValueError, match='Invalid IAP token'):
            iap_service.IAPService.verify_iap_jwt('expired.jwt.token')
    
    @patch.dict('os.environ', {}, clear=True)
    def test_verify_iap_jwt_not_configured(self):
        """Test IAP JWT verification when IAP not configured."""
        import importlib
        from services import iap_service
        importlib.reload(iap_service)
        
        with pytest.raises(ValueError, match='IAP_AUDIENCE not configured'):
            iap_service.IAPService.verify_iap_jwt('any.jwt.token')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
