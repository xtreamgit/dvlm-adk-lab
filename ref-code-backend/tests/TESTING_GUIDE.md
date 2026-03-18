# IAP Integration Testing Guide

Complete guide for testing the IAP (Identity-Aware Proxy) integration.

## Test Suite Overview

```
tests/
├── test_iap_service.py          # Unit tests for IAPService
├── test_iap_middleware.py       # Integration tests for middleware
├── test_iap_routes.py           # API endpoint tests
└── manual/
    └── test_iap_manual.sh       # Manual testing script
```

## Prerequisites

### 1. Install Test Dependencies

```bash
cd backend
pip install pytest pytest-asyncio pytest-mock httpx
```

### 2. Set Up Test Environment

```bash
# For unit tests (no real IAP needed)
export DATABASE_PATH="./data/test_users.db"

# For integration tests with IAP
export PROJECT_NUMBER="your-project-number"
export BACKEND_SERVICE_ID="your-backend-service-id"
```

## Running Tests

### Run All IAP Tests

```bash
# Run all IAP-related tests
pytest tests/test_iap*.py -v

# Run with coverage
pytest tests/test_iap*.py --cov=services.iap_service --cov=middleware.iap_auth_middleware --cov-report=html
```

### Run Specific Test Suites

#### 1. Unit Tests (IAP Service)
```bash
pytest tests/test_iap_service.py -v
```

**Tests:**
- JWT verification
- User info extraction
- IAP configuration validation
- Error handling

#### 2. Integration Tests (Middleware)
```bash
pytest tests/test_iap_middleware.py -v
```

**Tests:**
- Middleware authentication flow
- User creation from IAP
- Existing user updates
- Inactive user handling
- Optional authentication
- Hybrid authentication

#### 3. API Route Tests
```bash
pytest tests/test_iap_routes.py -v
```

**Tests:**
- `/api/iap/me` endpoint
- `/api/iap/status` endpoint
- `/api/iap/verify` endpoint
- `/api/iap/headers` endpoint

### Run Manual Tests

```bash
# Make script executable
chmod +x tests/manual/test_iap_manual.sh

# Run against local server
./tests/manual/test_iap_manual.sh

# Run against production with verbose output
BASE_URL=https://your-app.develom.com VERBOSE=true ./tests/manual/test_iap_manual.sh
```

## Test Database Migration

### Test Migration Locally

```bash
# 1. Create a test database
cd backend
cp data/users.db data/users_backup.db

# 2. Run migration
python src/database/migrations/run_migrations.py

# 3. Verify schema changes
sqlite3 data/users.db ".schema users"

# Expected to see:
# - google_id TEXT UNIQUE
# - auth_provider TEXT DEFAULT 'local'
# - hashed_password TEXT (nullable)

# 4. Test rollback if needed
mv data/users_backup.db data/users.db
```

### Verify Migration in Production

```bash
# SSH into Cloud Run instance or use Cloud Shell
gcloud run services proxy backend --region us-west1

# In another terminal, check database
curl http://localhost:8080/api/iap/status
```

## Testing Scenarios

### Scenario 1: New IAP User

**Objective:** Verify that a new user authenticated via IAP is automatically created in the database.

**Steps:**
1. Access application through Load Balancer (not direct Cloud Run URL)
2. Authenticate with Google account (e.g., newuser@develom.com)
3. Make request to `/api/iap/me`
4. Verify response contains user information
5. Check database for new user record

**Expected:**
- HTTP 200 response
- User object with `auth_provider: "iap"`
- User has `google_id` set
- User is active by default

**Test Command:**
```bash
curl https://your-app.develom.com/api/iap/me
```

### Scenario 2: Existing Local User Migrating to IAP

**Objective:** Verify existing users get their Google ID added when authenticating via IAP.

**Steps:**
1. Have existing user in database (created via `/api/auth/register`)
2. User authenticates via IAP with same email
3. Make request to `/api/iap/me`
4. Verify user record is updated with `google_id`

**Expected:**
- HTTP 200 response
- Existing user gets `google_id` populated
- `auth_provider` updated to "iap"
- User retains all existing data

**Test Command:**
```bash
# 1. Create local user
curl -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123", "email": "testuser@develom.com", "full_name": "Test User"}'

# 2. Authenticate via IAP (requires going through Load Balancer)
curl https://your-app.develom.com/api/iap/me
```

### Scenario 3: Hybrid Authentication

**Objective:** Verify endpoints support both IAP and legacy JWT authentication.

**Steps:**
1. Test endpoint with IAP header
2. Test same endpoint with JWT Bearer token
3. Both should work

**Expected:**
- IAP authentication takes priority
- JWT authentication works as fallback
- Both return valid user object

**Test Commands:**
```bash
# With IAP (through Load Balancer)
curl https://your-app.develom.com/api/users/me

# With JWT (direct or via Load Balancer)
curl http://localhost:8080/api/users/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Scenario 4: IAP Configuration Validation

**Objective:** Verify IAP is properly configured.

**Steps:**
1. Check IAP status endpoint
2. Verify environment variables are set
3. Test JWT verification

**Expected:**
- `/api/iap/status` returns `iap_enabled: true`
- IAP audience is properly formatted
- Configuration message indicates success

**Test Commands:**
```bash
# Check status
curl https://your-app.develom.com/api/iap/status

# Debug headers
curl https://your-app.develom.com/api/iap/headers

# Verify token
curl https://your-app.develom.com/api/iap/verify
```

### Scenario 5: Inactive User Rejection

**Objective:** Verify inactive users cannot access protected endpoints.

**Steps:**
1. Create user
2. Set user to inactive in database
3. Try to authenticate via IAP
4. Verify rejection

**Expected:**
- HTTP 403 Forbidden
- Error message about inactive account

**Test Commands:**
```bash
# Deactivate user in database
sqlite3 data/users.db "UPDATE users SET is_active = 0 WHERE email = 'testuser@develom.com'"

# Try to access
curl https://your-app.develom.com/api/iap/me
```

## Testing Without IAP (Local Development)

For local development without actual IAP infrastructure:

### Option 1: Mock IAP Headers

```python
# In your test client
client.get(
    "/api/iap/me",
    headers={
        "X-Goog-IAP-JWT-Assertion": "mocked.jwt.token",
        "X-Goog-Authenticated-User-Email": "accounts.google.com:dev@develom.com"
    }
)
```

### Option 2: Use Legacy JWT Authentication

```bash
# Register and login with JWT
curl -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "dev", "password": "dev123", "email": "dev@develom.com", "full_name": "Developer"}'

# Use JWT token for API calls
curl http://localhost:8080/api/users/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Option 3: Use Hybrid Endpoints

Endpoints using `get_current_user_hybrid` accept both IAP and JWT:

```bash
# These endpoints work with either authentication method
curl http://localhost:8080/api/users/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Continuous Integration

### GitHub Actions Workflow

Add to `.github/workflows/test.yml`:

```yaml
name: IAP Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-mock pytest-cov
      
      - name: Run IAP tests
        run: |
          cd backend
          pytest tests/test_iap*.py -v --cov=services.iap_service --cov=middleware.iap_auth_middleware
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Troubleshooting Test Failures

### "ImportError: No module named 'services.iap_service'"

**Cause:** Python path not set correctly.

**Solution:**
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
pytest tests/test_iap*.py
```

### "ValueError: IAP_AUDIENCE not configured"

**Cause:** Environment variables not set for tests.

**Solution:**
```bash
export PROJECT_NUMBER="123456789"
export BACKEND_SERVICE_ID="9876543210"
pytest tests/test_iap_service.py
```

### Mock Objects Not Working

**Cause:** Imports happening before mocks are set up.

**Solution:** Use `importlib.reload()` in tests:
```python
import importlib
from services import iap_service
importlib.reload(iap_service)
```

### Database Locked Errors

**Cause:** Multiple test processes accessing same database.

**Solution:**
```bash
# Use separate test database
export DATABASE_PATH="./data/test_$(date +%s).db"
pytest tests/test_iap*.py
```

## Performance Testing

### Load Testing IAP Endpoints

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test IAP status endpoint
ab -n 1000 -c 10 https://your-app.develom.com/api/iap/status

# Results should show:
# - < 100ms average response time
# - 0% failed requests
# - Consistent throughput
```

## Security Testing

### Test Invalid JWT Rejection

```bash
# Should return 401
curl https://your-app.develom.com/api/iap/me \
  -H "X-Goog-IAP-JWT-Assertion: fake.invalid.token"
```

### Test Expired Token Handling

```python
# Mock expired token in tests
mock_verify.side_effect = Exception('Token expired')
```

### Test Audience Mismatch

```python
# Mock wrong audience
mock_verify.return_value = {
    'iss': 'https://cloud.google.com/iap',
    'aud': '/projects/999/global/backendServices/999'  # Wrong!
}
```

## Monitoring Test Results

### View Test Coverage

```bash
pytest tests/test_iap*.py --cov=services.iap_service --cov=middleware.iap_auth_middleware --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### Expected Coverage Targets

- `services/iap_service.py`: > 90%
- `middleware/iap_auth_middleware.py`: > 85%
- `api/routes/iap_auth.py`: > 80%

## Next Steps

After all tests pass:

1. ✅ Run full test suite: `pytest tests/ -v`
2. ✅ Run manual tests: `./tests/manual/test_iap_manual.sh`
3. ✅ Test database migration locally
4. ✅ Deploy to staging environment
5. ✅ Run integration tests against staging
6. ✅ Deploy to production
7. ✅ Monitor logs for IAP-related errors
8. ✅ Verify user creation from IAP

## Support

For test failures or questions:
- Check logs: `gcloud logs read --service=backend --limit=100`
- Review IAP configuration: Cloud Console → Security → Identity-Aware Proxy
- Verify environment variables: `gcloud run services describe backend --region us-west1`
