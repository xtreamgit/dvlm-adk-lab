"""
IAP authentication middleware for FastAPI.
Verifies IAP JWT and creates/updates user in local database.

This is the SOLE authentication middleware for the application.
- Production: Verifies IAP JWT injected by Google Load Balancer
- Local dev: When IAP_DEV_MODE=true, bypasses JWT and uses a configured dev user
"""

import os
from fastapi import Request, HTTPException, status
from typing import Optional
import logging
from datetime import datetime, timezone

from services.iap_service import IAPService
from services.user_service import UserService
from services.google_groups_bridge import GoogleGroupsBridge
from models.user import User

logger = logging.getLogger(__name__)

# Header names for IAP
IAP_JWT_HEADER = "X-Goog-IAP-JWT-Assertion"
IAP_EMAIL_HEADER = "X-Goog-Authenticated-User-Email"
IAP_ID_HEADER = "X-Goog-Authenticated-User-ID"

# Local development mode: bypass IAP JWT verification
IAP_DEV_MODE = os.getenv("IAP_DEV_MODE", "false").lower() == "true"
IAP_DEV_USER_EMAIL = os.getenv("IAP_DEV_USER_EMAIL", "dev@develom.com")

# Allow direct API access mode: for when backend is accessed directly (not through IAP)
# but frontend is IAP-protected. Backend will accept requests without IAP headers.
ALLOW_DIRECT_API_ACCESS = os.getenv("ALLOW_DIRECT_API_ACCESS", "false").lower() == "true"

if IAP_DEV_MODE:
    logger.warning("⚠️  IAP_DEV_MODE is ON — IAP JWT verification is BYPASSED")
    logger.warning(f"   Dev user email: {IAP_DEV_USER_EMAIL}")

if ALLOW_DIRECT_API_ACCESS:
    logger.warning("⚠️  ALLOW_DIRECT_API_ACCESS is ON — Backend accepts direct API calls without IAP headers")
    logger.warning("   This mode is for when frontend is IAP-protected but backend is accessed directly")


async def _get_or_create_dev_user() -> User:
    """
    Get or create the dev mode user. Used only when IAP_DEV_MODE=true.
    """
    allow_no_db = os.getenv("ALLOW_START_WITHOUT_DB", "false").lower() == "true"
    try:
        user = UserService.get_user_by_email(IAP_DEV_USER_EMAIL)
        if not user:
            user = UserService.create_user_from_iap(
                email=IAP_DEV_USER_EMAIL,
                google_id="dev-mode-id",
                full_name=IAP_DEV_USER_EMAIL.split("@")[0].replace(".", " ").title()
            )
            logger.info(f"Dev mode: created user for {IAP_DEV_USER_EMAIL}")
        else:
            UserService.update_last_login(user.id)
        return user
    except Exception as e:
        if not allow_no_db:
            raise
        now = datetime.now(timezone.utc)
        logger.warning(
            "Dev mode: database unavailable, returning synthetic user because ALLOW_START_WITHOUT_DB=true",
            extra={"error": str(e)[:300], "email": IAP_DEV_USER_EMAIL},
        )
        return User(
            id=-1,
            email=IAP_DEV_USER_EMAIL,
            full_name=IAP_DEV_USER_EMAIL.split("@")[0].replace(".", " ").title(),
            is_active=True,
            default_agent_id=None,
            google_id="dev-mode-id",
            created_at=now,
            updated_at=now,
            last_login=now,
        )


async def get_current_user_iap(request: Request) -> User:
    """
    FastAPI dependency to get current user from IAP headers.
    
    Flow:
    1. If IAP_DEV_MODE, return configured dev user (no JWT needed)
    2. Extract IAP JWT from header
    3. Verify JWT signature and audience
    4. Extract user email from verified JWT
    5. Get or create user in local database
    6. Return User object with groups/permissions
    
    Raises:
        HTTPException 401: If IAP JWT is missing or invalid
        HTTPException 403: If user is inactive
        
    Returns:
        User object from local database
    """
    # Dev mode bypass — no IAP JWT required
    if IAP_DEV_MODE:
        user = await _get_or_create_dev_user()
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Dev user account is inactive."
            )
        # Google Groups Bridge sync (non-fatal)
        await _run_bridge_sync(user)
        return user

    # Production: extract and verify IAP JWT header
    iap_jwt = request.headers.get(IAP_JWT_HEADER)
    
    if not iap_jwt:
        # If ALLOW_DIRECT_API_ACCESS is enabled, fall back to dev user mode
        if ALLOW_DIRECT_API_ACCESS:
            logger.info("No IAP JWT header, using ALLOW_DIRECT_API_ACCESS mode")
            user = await _get_or_create_dev_user()
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is inactive."
                )
            # Google Groups Bridge sync (non-fatal)
            await _run_bridge_sync(user)
            return user
        
        logger.warning("Missing IAP JWT header - request not from IAP?")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing IAP authentication. Access must be through Load Balancer.",
        )
    
    try:
        # Verify IAP JWT
        decoded_token = IAPService.verify_iap_jwt(iap_jwt)
        user_info = IAPService.extract_user_info(decoded_token)
        
        email = user_info['email']
        google_id = user_info['google_id']
        name = user_info['name']
        
        logger.info(f"IAP authenticated user: {email}")
        
        # Get or create user in local database
        user = UserService.get_user_by_email(email)
        
        if not user:
            # Create new user from IAP authentication
            user = UserService.create_user_from_iap(
                email=email,
                google_id=google_id,
                full_name=name
            )
            logger.info(f"New user created from IAP: {email}")
        else:
            # Update last login
            UserService.update_last_login(user.id)
            
            # Update google_id if not set
            if not hasattr(user, 'google_id') or not user.google_id:
                UserService.update_google_id(user.id, google_id)
                logger.info(f"Updated google_id for existing user: {email}")
        
        # Ensure chatbot_user record exists (required for corpus access queries)
        UserService.ensure_chatbot_user(user.id, email, name)
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Inactive user attempted access: {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is inactive. Please contact an administrator."
            )
        
        # Google Groups Bridge sync (non-fatal)
        await _run_bridge_sync(user)
        
        return user
        
    except ValueError as e:
        logger.error(f"IAP JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid IAP token: {str(e)}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


async def _run_bridge_sync(user: User):
    """
    Run Google Groups Bridge sync if enabled.
    Non-fatal: if sync fails, user retains existing permissions.
    """
    if not GoogleGroupsBridge.is_enabled():
        return
    try:
        result = await GoogleGroupsBridge.sync_user_access(user.id, user.email)
        if result.get("status") == "synced":
            logger.info(f"Bridge sync completed for {user.email}: {result.get('chatbot_group')}")
    except Exception as e:
        logger.warning(f"Google Groups Bridge sync failed for {user.email}: {e}")


async def get_current_user_optional_iap(request: Request) -> Optional[User]:
    """
    Optional IAP authentication - returns None if not authenticated.
    Useful for endpoints that work with or without authentication.
    """
    if IAP_DEV_MODE:
        try:
            return await _get_or_create_dev_user()
        except Exception:
            return None

    iap_jwt = request.headers.get(IAP_JWT_HEADER)
    
    if not iap_jwt:
        return None
    
    try:
        return await get_current_user_iap(request)
    except HTTPException:
        return None


