# IAP Configuration Guide

This document explains how to configure and use Identity-Aware Proxy (IAP) authentication with the adk-multi-agents backend.

## Overview

IAP authentication has been integrated into the backend to provide secure, enterprise-grade authentication using Google Cloud Identity-Aware Proxy. Users are authenticated at the Load Balancer level before requests reach the backend.

## Architecture

```
User → Load Balancer → IAP (Google-managed) → Backend Service
                         ↓
                    JWT Verification
                         ↓
                    User Sync to Database
                         ↓
                    Existing RBAC System
```

## Environment Variables

The following environment variables must be set for IAP to work correctly:

### Required Variables

```bash
# Project number (numeric ID, not project ID)
PROJECT_NUMBER=123456789

# Backend service ID from Load Balancer
# Format: Backend service ID (not name)
BACKEND_SERVICE_ID=1234567890123456789

# Example IAP audience constructed from above:
# /projects/123456789/global/backendServices/1234567890123456789
```

### How to Get These Values

#### 1. Get PROJECT_NUMBER

```bash
# Get project number from gcloud
gcloud projects describe adk-rag-ma --format="value(projectNumber)"
```

#### 2. Get BACKEND_SERVICE_ID

```bash
# List backend services
gcloud compute backend-services list --global

# Get specific backend service details
gcloud compute backend-services describe <backend-service-name> --global --format="value(id)"
```

## Deployment Configuration

### Cloud Run Environment Variables

Set these in your Cloud Run service configuration:

```bash
gcloud run services update backend \
  --set-env-vars PROJECT_NUMBER=123456789 \
  --set-env-vars BACKEND_SERVICE_ID=1234567890123456789 \
  --region us-west1
```

### Infrastructure Script Integration

The `infrastructure/deploy-all.sh` script should automatically configure these. Verify by checking:

```bash
# Check current environment variables
gcloud run services describe backend --region us-west1 --format="value(spec.template.spec.containers[0].env)"
```

## API Endpoints

### IAP Authentication Endpoints

#### Get Current IAP User
```
GET /api/iap/me
```
Returns the current IAP-authenticated user. Creates user in database if doesn't exist.

**Headers:**
- `X-Goog-IAP-JWT-Assertion`: IAP JWT token (automatically injected by IAP)

**Response:**
```json
{
  "id": 1,
  "username": "user",
  "email": "user@develom.com",
  "full_name": "User Name",
  "google_id": "1234567890",
  "auth_provider": "iap",
  "is_active": true,
  "created_at": "2026-01-10T...",
  "updated_at": "2026-01-10T...",
  "last_login": "2026-01-10T..."
}
```

#### Check IAP Status
```
GET /api/iap/status
```
Returns IAP configuration status.

**Response:**
```json
{
  "iap_enabled": true,
  "iap_audience": "/projects/123456789/global/backendServices/...",
  "message": "IAP is properly configured"
}
```

#### Verify IAP Token
```
GET /api/iap/verify
```
Diagnostic endpoint to test IAP JWT verification.

**Response:**
```json
{
  "valid": true,
  "user_info": {
    "email": "user@develom.com",
    "google_id": "1234567890",
    "name": "User Name"
  },
  "token_payload": {
    "iss": "https://cloud.google.com/iap",
    "aud": "/projects/.../global/backendServices/...",
    "sub": "1234567890",
    "email": "user@develom.com",
    "exp": 1234567890
  }
}
```

#### Debug IAP Headers
```
GET /api/iap/headers
```
Shows all IAP-related headers for debugging.

**Response:**
```json
{
  "iap_headers": {
    "x-goog-iap-jwt-assertion": "eyJhbGc...",
    "x-goog-authenticated-user-email": "accounts.google.com:user@develom.com",
    "x-goog-authenticated-user-id": "accounts.google.com:1234567890"
  },
  "has_jwt": true
}
```

## Using IAP Authentication in Your Routes

### Option 1: IAP Only (Recommended for New Routes)

```python
from fastapi import APIRouter, Depends
from middleware.iap_auth_middleware import get_current_user_iap
from models.user import User

router = APIRouter()

@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user_iap)):
    """This route requires IAP authentication."""
    return {"message": f"Hello {current_user.email}"}
```

### Option 2: Hybrid Authentication (For Gradual Migration)

```python
from fastapi import APIRouter, Depends
from middleware.iap_auth_middleware import get_current_user_hybrid
from models.user import User

router = APIRouter()

@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user_hybrid)):
    """This route accepts both IAP and legacy JWT authentication."""
    return {"message": f"Hello {current_user.email}"}
```

### Option 3: Optional IAP (Public with Optional Auth)

```python
from fastapi import APIRouter, Depends
from middleware.iap_auth_middleware import get_current_user_optional_iap
from models.user import User
from typing import Optional

router = APIRouter()

@router.get("/public")
async def public_route(current_user: Optional[User] = Depends(get_current_user_optional_iap)):
    """This route works with or without authentication."""
    if current_user:
        return {"message": f"Hello {current_user.email}"}
    return {"message": "Hello anonymous user"}
```

## Database Migration

Run the database migration to add IAP support:

```bash
cd backend
python src/database/migrations/run_migrations.py
```

This will:
- Add `google_id` column to users table
- Add `auth_provider` column to users table
- Make `hashed_password` nullable (IAP users don't need passwords)
- Create indexes for performance

## Testing IAP Integration

### 1. Local Testing (Without IAP)

For local development without IAP, use the legacy JWT authentication:

```bash
# Login with JWT
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'
```

### 2. Testing with IAP (Production)

Access your application through the Load Balancer URL:

```bash
# Check IAP status
curl https://your-app.develom.com/api/iap/status

# Get current user (will redirect to Google login if not authenticated)
curl https://your-app.develom.com/api/iap/me
```

### 3. Debug IAP Headers

```bash
# View IAP headers (must be authenticated through IAP)
curl https://your-app.develom.com/api/iap/headers
```

## Migration Strategy

### Phase 1: Deploy IAP Infrastructure (Already Done!)

Your `infrastructure/deploy-all.sh` already configures IAP.

### Phase 2: Update Environment Variables (Current Step)

Set `PROJECT_NUMBER` and `BACKEND_SERVICE_ID` in Cloud Run.

### Phase 3: Run Database Migration

Execute `006_add_iap_support.sql` migration.

### Phase 4: Update Routes (Optional - Gradual)

Update existing routes to use `get_current_user_hybrid` for gradual migration:

```python
# Old way (JWT only)
from middleware.auth_middleware import get_current_user

# New way (IAP + JWT hybrid)
from middleware.iap_auth_middleware import get_current_user_hybrid as get_current_user
```

### Phase 5: Monitor and Verify

- Check `/api/iap/status` to verify configuration
- Monitor user creation logs
- Verify IAP users can access resources

## Security Considerations

### Critical: Always Verify JWT

**Never trust headers without verifying the JWT!**

```python
# ❌ WRONG - Anyone can set HTTP headers
email = request.headers.get("X-Goog-Authenticated-User-Email")

# ✅ CORRECT - Always verify the signed JWT
decoded_token = IAPService.verify_iap_jwt(iap_jwt)
email = decoded_token.get("email")
```

### IAP JWT Verification

The `IAPService.verify_iap_jwt()` method:
1. Fetches Google's public keys
2. Verifies JWT signature
3. Validates audience matches your backend service
4. Validates issuer is `https://cloud.google.com/iap`
5. Checks token expiration

### Audience Validation

The IAP audience **must** match:
```
/projects/{PROJECT_NUMBER}/global/backendServices/{BACKEND_SERVICE_ID}
```

If it doesn't match, authentication will fail.

## Troubleshooting

### Error: "IAP_AUDIENCE not configured"

**Cause:** Missing `PROJECT_NUMBER` or `BACKEND_SERVICE_ID` environment variables.

**Solution:**
```bash
gcloud run services update backend \
  --set-env-vars PROJECT_NUMBER=$(gcloud projects describe adk-rag-ma --format="value(projectNumber)") \
  --region us-west1
```

### Error: "Invalid IAP token: Invalid issuer"

**Cause:** JWT is not from IAP or request didn't go through Load Balancer.

**Solution:**
- Ensure requests go through Load Balancer, not directly to Cloud Run
- Check IAP is enabled on backend service
- Verify OAuth client configuration

### Error: "Missing IAP authentication"

**Cause:** Request didn't include IAP JWT header.

**Solution:**
- Access via Load Balancer URL (not Cloud Run URL directly)
- Verify IAP is enabled
- Check if user has `roles/iap.httpsResourceAccessor` permission

### Users Not Being Created

**Cause:** Database migration not run or permission issues.

**Solution:**
```bash
# Run migration
python backend/src/database/migrations/run_migrations.py

# Check logs
gcloud logs read --service=backend --limit=50
```

## Additional Resources

- [Google Cloud IAP Documentation](https://cloud.google.com/iap/docs)
- [IAP JWT Verification](https://cloud.google.com/iap/docs/signed-headers-howto)
- [Load Balancer Setup](https://cloud.google.com/load-balancing/docs)

## Support

For issues with IAP integration:
1. Check `/api/iap/status` endpoint
2. View Cloud Run logs: `gcloud logs read --service=backend`
3. Verify IAP configuration in Cloud Console
4. Test with `/api/iap/verify` endpoint
