#!/bin/bash
#
# deploy-env.sh - Deploy backend + migrations + frontend to a target environment
#
# Usage:
#   bash scripts/deploy-env.sh <env>
#   bash scripts/deploy-env.sh tt
#   bash scripts/deploy-env.sh develom
#   bash scripts/deploy-env.sh usfs
#
# Prerequisites:
#   - gcloud CLI authenticated and project set
#   - source scripts/env-load.sh <env>  (or let this script load it)
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_success() { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*"; }
log_section() { echo -e "\n${BLUE}=== $* ===${NC}"; }

# ---- Argument handling ----
ENV="${1:-}"
if [[ -z "$ENV" ]]; then
    log_error "Environment name required."
    echo "Usage: bash scripts/deploy-env.sh <env>"
    echo "       where <env> is: tt | develom | usfs"
    exit 1
fi

# ---- Load environment config if not already loaded ----
if [[ -z "${PROJECT_ID:-}" ]]; then
    log_info "ENV vars not set — loading from environments/$ENV.yaml"
    source "$SCRIPT_DIR/env-load.sh" "$ENV"
fi

log_section "Deploying to environment: $ENV"
log_info "Project  : $PROJECT_ID"
log_info "Region   : $REGION"
log_info "Backend  : $BACKEND_IMAGE"
log_info "Frontend : $FRONTEND_IMAGE"

# ---- Step 1: Set active GCP project ----
log_section "Step 1: Set GCP project"
gcloud config set project "$PROJECT_ID"
log_success "Active project: $PROJECT_ID"

# ---- Step 2: Build and push backend image ----
log_section "Step 2: Build backend image"
gcloud builds submit "$REPO_ROOT" \
    --config="$REPO_ROOT/backend/cloudbuild.yaml" \
    --substitutions="_BACKEND_IMAGE=${BACKEND_IMAGE}" \
    --quiet
log_success "Backend image built: $BACKEND_IMAGE"

# ---- Step 3: Run database migrations ----
log_section "Step 3: Run database migrations"
if [[ -f "$REPO_ROOT/backend/run_migration_in_cloud.py" ]]; then
    log_info "Running cloud migration script..."
    python3 "$REPO_ROOT/backend/run_migration_in_cloud.py" \
        --project-id="$PROJECT_ID" \
        --region="$REGION" \
        --cloud-sql-instance="$CLOUD_SQL_CONNECTION"
elif [[ -f "$REPO_ROOT/backend/scripts/run_migrations.sh" ]]; then
    log_info "Running migration shell script..."
    bash "$REPO_ROOT/backend/scripts/run_migrations.sh"
else
    log_warn "No migration script found — skipping migrations."
    log_warn "Expected: backend/run_migration_in_cloud.py or backend/scripts/run_migrations.sh"
fi

# ---- Step 3b: Discover per-service BACKEND_SERVICE_ID for IAP ----
log_section "Step 3b: Discover per-service BACKEND_SERVICE_ID for IAP"

# ---- Step 4: Deploy backend services to Cloud Run ----
log_section "Step 4: Deploy backend services to Cloud Run"
BACKEND_SERVICES="${BACKEND_SERVICES:-backend}"
for SERVICE in $BACKEND_SERVICES; do
    # Discover per-service BACKEND_SERVICE_ID from load balancer
    BS_NAME="${SERVICE}-backend-service"
    BS_ID=$(gcloud compute backend-services describe "$BS_NAME" \
        --global --project="$PROJECT_ID" --format="value(id)" 2>/dev/null || echo "")
    if [[ -n "$BS_ID" ]]; then
        log_success "  ${SERVICE}: BACKEND_SERVICE_ID = $BS_ID"
    else
        log_warn "  ${SERVICE}: backend service '$BS_NAME' not found — IAP JWT verification will fail"
    fi

    # Derive ACCOUNT_ENV and ROOT_PATH per service
    if [[ "$SERVICE" == "backend" ]]; then
        ACCT_ENV="${ACCOUNT_ENV}"
        ROOT_PATH=""
    else
        ACCT_ENV="${SERVICE#backend-}"
        ROOT_PATH="/${SERVICE#backend-}"
    fi

    log_info "Deploying $SERVICE (ACCOUNT_ENV=$ACCT_ENV, BACKEND_SERVICE_ID=$BS_ID)..."

    # Build --set-secrets flag if DB_PASSWORD_SECRET is configured
    SECRETS_FLAG=""
    if [[ -n "${DB_PASSWORD_SECRET:-}" ]]; then
        SECRETS_FLAG="--set-secrets=DB_PASSWORD=${DB_PASSWORD_SECRET}:latest"
    else
        log_warn "  DB_PASSWORD_SECRET not set — DB_PASSWORD will not be mounted from Secret Manager"
    fi

    gcloud run deploy "$SERVICE" \
        --image="$BACKEND_IMAGE" \
        --region="$REGION" \
        --ingress=internal-and-cloud-load-balancing \
        --allow-unauthenticated \
        --cpu=1 \
        --memory=1Gi \
        --concurrency=80 \
        --min-instances=0 \
        --max-instances=10 \
        --add-cloudsql-instances="$CLOUD_SQL_CONNECTION" \
        --set-env-vars="PROJECT_ID=${PROJECT_ID},PROJECT_NUMBER=${PROJECT_NUMBER},BACKEND_SERVICE_ID=${BS_ID},REGION=${REGION},GOOGLE_CLOUD_LOCATION=${REGION},VERTEXAI_PROJECT=${PROJECT_ID},VERTEXAI_LOCATION=${REGION},DB_NAME=${DB_NAME},DB_USER=${DB_USER},CLOUD_SQL_CONNECTION_NAME=${CLOUD_SQL_CONNECTION},LOG_LEVEL=INFO,ENVIRONMENT=production,ACCOUNT_ENV=${ACCT_ENV},ROOT_PATH=${ROOT_PATH}" \
        ${SECRETS_FLAG} \
        --labels="app=adk-rag-agent,role=backend,env=${ENV}" \
        --quiet
    log_success "  $SERVICE deployed."
done

BACKEND_URL=$(gcloud run services describe "backend" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --format='value(status.url)')
export BACKEND_URL
log_success "Backend deployed: $BACKEND_URL"

# ---- Step 5: Build and push frontend image ----
log_section "Step 5: Build frontend image"

# Detect load balancer: if a static IP exists for this env, use relative URLs
# so the LB URL map routes /api/* to the backend service.
FRONTEND_BACKEND_URL="${BACKEND_URL}"
LB_IP_NAME="${LB_IP_NAME:-}"
if [[ -z "$LB_IP_NAME" ]]; then
    # Convention: <env>-rag-agent-ip (e.g., usfs-rag-agent-ip)
    LB_IP_NAME="${ENV}-rag-agent-ip"
fi
if gcloud compute addresses describe "$LB_IP_NAME" --global --project="$PROJECT_ID" >/dev/null 2>&1; then
    log_info "Load balancer detected ($LB_IP_NAME) — using relative URLs for frontend"
    FRONTEND_BACKEND_URL=""
else
    log_info "No load balancer — frontend will call backend directly at $BACKEND_URL"
fi

gcloud builds submit "$REPO_ROOT/frontend" \
    --config="$REPO_ROOT/frontend/cloudbuild.yaml" \
    --substitutions="_IMAGE_NAME=${FRONTEND_IMAGE},_BACKEND_URL=${FRONTEND_BACKEND_URL}" \
    --quiet
log_success "Frontend image built: $FRONTEND_IMAGE"

# ---- Step 6: Deploy frontend to Cloud Run ----
log_section "Step 6: Deploy frontend to Cloud Run"
gcloud run deploy "$FRONTEND_SERVICE" \
    --image="$FRONTEND_IMAGE" \
    --region="$REGION" \
    --ingress=internal-and-cloud-load-balancing \
    --allow-unauthenticated \
    --cpu=1 \
    --memory=512Mi \
    --concurrency=80 \
    --min-instances=0 \
    --max-instances=5 \
    --labels="app=adk-rag-agent,role=frontend,env=${ENV}" \
    --quiet

FRONTEND_URL=$(gcloud run services describe "$FRONTEND_SERVICE" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --format='value(status.url)')
export FRONTEND_URL
log_success "Frontend deployed: $FRONTEND_URL"

# ---- Step 7: Smoke tests ----
log_section "Step 7: Smoke tests"
log_info "Checking backend health..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BACKEND_URL}/api/health" || echo "000")
if [[ "$HTTP_STATUS" == "200" ]]; then
    log_success "Backend health check passed (HTTP $HTTP_STATUS)"
else
    log_warn "Backend health check returned HTTP $HTTP_STATUS — verify manually"
fi

log_info "Checking frontend..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${FRONTEND_URL}" || echo "000")
if [[ "$HTTP_STATUS" == "200" ]]; then
    log_success "Frontend health check passed (HTTP $HTTP_STATUS)"
else
    log_warn "Frontend returned HTTP $HTTP_STATUS — verify manually"
fi

# ---- Summary ----
log_section "Deployment Complete"
echo ""
echo "  Environment : $ENV"
echo "  Project     : $PROJECT_ID"
echo "  Region      : $REGION"
echo "  Backend URL : $BACKEND_URL"
echo "  Frontend URL: $FRONTEND_URL"
echo ""
log_success "Done."
