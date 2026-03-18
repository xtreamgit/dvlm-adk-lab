# IAP Integration Deployment Guide

Complete guide for deploying the backend with IAP authentication support.

## Quick Start

```bash
cd backend
./deploy_iap.sh
```

## Prerequisites

### 1. Install Required Tools

- **gcloud CLI**: [Install instructions](https://cloud.google.com/sdk/docs/install)
- **Python 3.x**: For running database migrations
- **curl**: For testing endpoints

### 2. Authenticate with GCP

```bash
gcloud auth login
gcloud config set project adk-rag-ma
```

### 3. Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  compute.googleapis.com \
  iap.googleapis.com
```

## Deployment Script Usage

### Basic Deployment

```bash
./deploy_iap.sh
```

This will:
1. ✅ Validate prerequisites
2. ✅ Retrieve IAP configuration (PROJECT_NUMBER, BACKEND_SERVICE_ID)
3. ✅ Run database migration (006_add_iap_support.sql)
4. ✅ Deploy to Cloud Run with IAP environment variables
5. ✅ Run post-deployment tests

### Advanced Options

```bash
# Dry run (validate without deploying)
./deploy_iap.sh --dry-run

# Deploy to different project/region
./deploy_iap.sh --project my-project --region us-central1

# Skip database migration (if already run)
./deploy_iap.sh --skip-migration

# Skip post-deployment tests
./deploy_iap.sh --skip-tests

# Custom service name
./deploy_iap.sh --service backend-production

# Combine options
./deploy_iap.sh --project adk-rag-ma --region us-west1 --dry-run
```

### Help

```bash
./deploy_iap.sh --help
```

## Manual Deployment Steps

If you prefer to deploy manually or the script fails:

### Step 1: Get IAP Configuration

```bash
# Get project number
PROJECT_NUMBER=$(gcloud projects describe adk-rag-ma --format="value(projectNumber)")
echo "Project Number: $PROJECT_NUMBER"

# List backend services
gcloud compute backend-services list --global

# Get backend service ID (replace <backend-service-name> with actual name)
BACKEND_SERVICE_ID=$(gcloud compute backend-services describe <backend-service-name> --global --format="value(id)")
echo "Backend Service ID: $BACKEND_SERVICE_ID"
```

### Step 2: Run Database Migration

```bash
cd backend
python src/database/migrations/run_migrations.py
```

### Step 3: Deploy to Cloud Run

```bash
gcloud run deploy backend \
  --source . \
  --region us-west1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars PROJECT_NUMBER=$PROJECT_NUMBER,BACKEND_SERVICE_ID=$BACKEND_SERVICE_ID
```

### Step 4: Verify Deployment

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe backend --region us-west1 --format="value(status.url)")

# Test health endpoint
curl $SERVICE_URL/api/health

# Test IAP status
curl $SERVICE_URL/api/iap/status
```

## Environment Variables

### Required for IAP

| Variable | Description | How to Get |
|----------|-------------|------------|
| `PROJECT_NUMBER` | GCP project numeric ID | `gcloud projects describe adk-rag-ma --format="value(projectNumber)"` |
| `BACKEND_SERVICE_ID` | Backend service ID from Load Balancer | `gcloud compute backend-services describe <name> --global --format="value(id)"` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_PATH` | Path to SQLite database | `./data/users.db` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `SECRET_KEY` | JWT secret key | Generated |

### Setting Environment Variables

#### Cloud Run (Recommended)

```bash
gcloud run services update backend \
  --set-env-vars PROJECT_NUMBER=123456789,BACKEND_SERVICE_ID=9876543210 \
  --region us-west1
```

#### Using .env File (Local Development)

```bash
# Copy example file
cp .env.iap.example .env.iap

# Edit with your values
nano .env.iap

# Load in shell
source .env.iap
```

## IAP Configuration

### Create Load Balancer with IAP

IAP must be configured at the Load Balancer level, not in the application.

#### 1. Create Load Balancer

```bash
# This is typically done through Cloud Console or Terraform
# Navigate to: Network Services → Load Balancing → Create Load Balancer
```

#### 2. Enable IAP

```bash
# In Cloud Console:
# 1. Go to Security → Identity-Aware Proxy
# 2. Select your backend service
# 3. Click "Turn on IAP"
# 4. Configure OAuth consent screen
```

#### 3. Configure OAuth

- Create OAuth 2.0 Client ID
- Set authorized redirect URIs
- Add authorized users/groups

#### 4. Get Backend Service ID

```bash
# After Load Balancer is created
gcloud compute backend-services list --global
gcloud compute backend-services describe <your-backend> --global --format="value(id)"
```

## Post-Deployment Verification

### Test Checklist

#### 1. Health Check
```bash
curl https://your-app.develom.com/api/health
# Expected: 200 OK with service info
```

#### 2. IAP Status
```bash
curl https://your-app.develom.com/api/iap/status
# Expected: {"iap_enabled": true, "iap_audience": "..."}
```

#### 3. IAP Headers (Debug)
```bash
curl https://your-app.develom.com/api/iap/headers
# Expected: Shows X-Goog-* headers if coming through IAP
```

#### 4. User Authentication
```bash
# Access through browser (will trigger Google auth)
open https://your-app.develom.com/api/iap/me
# Expected: User object with your Google account info
```

### Check Logs

```bash
# View recent logs
gcloud logs read --service=backend --limit=50

# Follow logs in real-time
gcloud logs tail --service=backend

# Filter IAP-related logs
gcloud logs read --service=backend --filter="IAP" --limit=20
```

### Database Verification

```bash
# SSH into Cloud Run or use Cloud Shell
# Check database schema
sqlite3 /path/to/users.db ".schema users"

# Verify columns exist
sqlite3 /path/to/users.db "PRAGMA table_info(users);"

# Check for IAP users
sqlite3 /path/to/users.db "SELECT email, auth_provider, google_id FROM users WHERE auth_provider='iap';"
```

## Troubleshooting

### Issue: "IAP_AUDIENCE not configured"

**Cause:** Missing PROJECT_NUMBER or BACKEND_SERVICE_ID environment variables.

**Solution:**
```bash
# Verify variables are set
gcloud run services describe backend --region us-west1 --format="yaml(spec.template.spec.containers[0].env)"

# Update if missing
gcloud run services update backend \
  --set-env-vars PROJECT_NUMBER=123,BACKEND_SERVICE_ID=456 \
  --region us-west1
```

### Issue: "no such column: google_id"

**Cause:** Database migration not run.

**Solution:**
```bash
python backend/src/database/migrations/run_migrations.py
```

### Issue: Backend service ID not found

**Cause:** Load Balancer not created or IAP not configured.

**Solution:**
1. Create Load Balancer in Cloud Console
2. Enable IAP on backend service
3. Get backend service ID
4. Redeploy with correct ID

### Issue: "Invalid IAP token"

**Possible causes:**
- Request not going through Load Balancer (direct to Cloud Run URL)
- IAP not enabled on backend service
- Wrong audience configuration

**Solution:**
- Always use Load Balancer URL, not Cloud Run URL
- Verify IAP is enabled: Cloud Console → Security → IAP
- Check audience matches: `gcloud run services describe backend --region us-west1`

### Issue: Users not being created

**Cause:** Database permissions or migration issues.

**Solution:**
```bash
# Check logs for errors
gcloud logs read --service=backend --severity=ERROR --limit=20

# Verify migration ran
gcloud logs read --service=backend --filter="migration" --limit=10
```

## Rollback

If deployment fails or causes issues:

### Rollback to Previous Revision

```bash
# List revisions
gcloud run revisions list --service=backend --region us-west1

# Rollback to specific revision
gcloud run services update-traffic backend \
  --to-revisions=backend-00123-abc=100 \
  --region us-west1
```

### Remove IAP Environment Variables

```bash
gcloud run services update backend \
  --remove-env-vars PROJECT_NUMBER,BACKEND_SERVICE_ID \
  --region us-west1
```

## Monitoring

### Key Metrics to Monitor

1. **Authentication Success Rate**
   - Monitor IAP JWT verification success/failure
   - Track user creation from IAP

2. **Endpoint Performance**
   - `/api/iap/me` response time
   - `/api/iap/status` availability

3. **Error Rates**
   - 401 Unauthorized errors
   - 403 Forbidden errors (inactive users)
   - 500 Internal Server Errors

### Set Up Alerts

```bash
# Create alert for high error rate
gcloud alpha monitoring policies create \
  --notification-channels=<channel-id> \
  --display-name="Backend IAP Errors" \
  --condition-display-name="High error rate" \
  --condition-threshold-value=5 \
  --condition-threshold-duration=60s
```

## Security Best Practices

### 1. IAP Configuration

- ✅ Always use IAP with Load Balancer
- ✅ Never allow direct access to Cloud Run URLs in production
- ✅ Configure authorized users/groups carefully
- ✅ Regularly audit IAP access logs

### 2. Environment Variables

- ✅ Store sensitive values in Secret Manager
- ✅ Use least-privilege IAM roles
- ✅ Rotate JWT secrets regularly
- ✅ Never commit `.env.iap` to version control

### 3. Database Security

- ✅ Use Cloud SQL in production (not SQLite)
- ✅ Enable automatic backups
- ✅ Encrypt data at rest
- ✅ Use IAM database authentication

### 4. Monitoring & Logging

- ✅ Enable Cloud Logging
- ✅ Set up alerts for authentication failures
- ✅ Monitor for unusual access patterns
- ✅ Regular security audits

## Multi-Environment Deployment

### Development

```bash
./deploy_iap.sh --project adk-rag-ma-dev --service backend-dev --region us-west1
```

### Staging

```bash
./deploy_iap.sh --project adk-rag-ma-staging --service backend-staging --region us-west1
```

### Production

```bash
./deploy_iap.sh --project adk-rag-ma --service backend --region us-west1
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy Backend with IAP

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Cloud SDK
        uses: google-github-actions/setup-gcloud@v0
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: adk-rag-ma
      
      - name: Run tests
        run: |
          cd backend
          python -m pytest tests/test_iap*.py
      
      - name: Deploy with IAP
        run: |
          cd backend
          ./deploy_iap.sh --skip-tests
```

## Additional Resources

- [Google Cloud IAP Documentation](https://cloud.google.com/iap/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [IAP Configuration Guide](./IAP_CONFIGURATION.md)
- [Testing Guide](./tests/TESTING_GUIDE.md)

## Support

For deployment issues:
1. Check logs: `gcloud logs read --service=backend --limit=50`
2. Review [IAP Configuration Guide](./IAP_CONFIGURATION.md)
3. Test locally: `./tests/manual/test_iap_manual.sh`
4. Verify IAP setup in Cloud Console
