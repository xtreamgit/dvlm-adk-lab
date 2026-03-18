"""
IAP Authentication routes for Google Cloud Identity-Aware Proxy integration.

These routes handle IAP-authenticated requests and user synchronization.
"""

import logging
from fastapi import APIRouter, HTTPException, status, Request, Depends

from services.iap_service import IAPService
from models.user import User
from middleware.iap_auth_middleware import get_current_user_iap

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/iap", tags=["IAP Authentication"])


@router.get("/me", response_model=User)
async def get_iap_user(current_user: User = Depends(get_current_user_iap)):
    """
    Get current IAP-authenticated user information.
    
    This endpoint verifies the IAP JWT and returns the authenticated user.
    If the user doesn't exist in the local database, it will be automatically created.
    
    Returns:
        User object with all user information
    """
    return current_user


@router.get("/status")
async def get_iap_status():
    """
    Check IAP configuration status.
    
    Returns information about IAP configuration and whether it's enabled.
    """
    is_enabled = IAPService.is_iap_enabled()
    audience = IAPService.get_iap_audience()
    
    return {
        "iap_enabled": is_enabled,
        "iap_audience": audience if is_enabled else None,
        "message": "IAP is properly configured" if is_enabled else "IAP is not configured (missing PROJECT_NUMBER or BACKEND_SERVICE_ID)"
    }


@router.get("/verify")
async def verify_iap_token(request: Request):
    """
    Verify IAP JWT token from request headers.
    
    This is a diagnostic endpoint to test IAP token verification.
    Returns the decoded token payload if valid.
    """
    iap_jwt = request.headers.get("X-Goog-IAP-JWT-Assertion")
    
    if not iap_jwt:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No IAP JWT found in headers. Make sure request is coming through IAP."
        )
    
    try:
        decoded_token = IAPService.verify_iap_jwt(iap_jwt)
        user_info = IAPService.extract_user_info(decoded_token)
        
        return {
            "valid": True,
            "user_info": user_info,
            "token_payload": {
                "iss": decoded_token.get("iss"),
                "aud": decoded_token.get("aud"),
                "sub": decoded_token.get("sub"),
                "email": decoded_token.get("email"),
                "exp": decoded_token.get("exp")
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid IAP token: {str(e)}"
        )


@router.get("/headers")
async def get_iap_headers(request: Request):
    """
    Debug endpoint to view IAP-related headers.
    
    Returns all X-Goog-* headers injected by IAP.
    Useful for debugging IAP configuration.
    """
    iap_headers = {
        key: value 
        for key, value in request.headers.items() 
        if key.lower().startswith('x-goog-')
    }
    
    if not iap_headers:
        return {
            "message": "No IAP headers found. Request may not be coming through IAP.",
            "all_headers": dict(request.headers)
        }
    
    return {
        "iap_headers": iap_headers,
        "has_jwt": "x-goog-iap-jwt-assertion" in iap_headers
    }
