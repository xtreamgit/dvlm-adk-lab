#!/bin/bash
#
# setup-tt-lb-iap.sh
# One-shot script to provision Load Balancer + IAP for the TT environment.
# Cloud Run services are assumed to already be deployed (by GitHub Actions).
#
# Steps performed:
#   1. Reserve static IP
#   2. Create Serverless NEGs for frontend + backend Cloud Run services
#   3. Create backend services and attach NEGs
#   4. Create URL map (/ → frontend, /api/* → backend)
#   5. Create managed SSL certificate
#   6. Create HTTPS proxy + forwarding rule
#   7. Create OAuth brand + client (requires interactive confirmation for redirect URIs)
#   8. Enable IAP on backend services
#   9. Grant IAP access to admin user + domain
#  10. Grant IAP SA Cloud Run invoker role
#  11. Wire PROJECT_NUMBER + BACKEND_SERVICE_ID into Cloud Run backend env vars
#  12. Create secret_key secret in Secret Manager
#  13. Seed TT database with initial agents + chatbot groups
#
# Usage:
#   gcloud config set account hdejesus@techtrend.us
#   gcloud config set project adk-rag-tt-488718
#   ./scripts/setup-tt-lb-iap.sh

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
PROJECT_ID="adk-rag-tt-488718"
PROJECT_NUMBER="980453997632"
REGION="us-west1"
ORGANIZATION_DOMAIN="techtrend.us"  # actual Google Workspace domain for IAP access
IAP_ADMIN_USER="hdejesus@techtrend.us"
SECRET_KEY="dVP_yTW5e1xjnEd5FD7YVgah7yUYUYhXapvNuJF2e0Q"

# Resource names
STATIC_IP_NAME="tt-rag-agent-ip"
SSL_CERT_NAME="tt-rag-agent-ssl-cert"
FRONTEND_NEG="tt-frontend-neg"
BACKEND_NEG="tt-backend-neg"
FRONTEND_BS="tt-frontend-backend-service"
BACKEND_BS="tt-backend-backend-service"
URL_MAP="tt-rag-agent-url-map"
HTTPS_PROXY="tt-rag-agent-https-proxy"
FORWARDING_RULE="tt-rag-agent-https-rule"

# Color helpers
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

log_info()    { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_section() { echo -e "\n${CYAN}━━━ $1 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }

# ── Sanity check ──────────────────────────────────────────────────────────────
log_section "PRE-FLIGHT"
ACTIVE_ACCOUNT=$(gcloud config get-value account 2>/dev/null)
ACTIVE_PROJECT=$(gcloud config get-value project 2>/dev/null)
log_info "Account : $ACTIVE_ACCOUNT"
log_info "Project : $ACTIVE_PROJECT"

if [[ "$ACTIVE_PROJECT" != "$PROJECT_ID" ]]; then
  echo -e "${RED}ERROR: Active project is '$ACTIVE_PROJECT', expected '$PROJECT_ID'${NC}"
  echo "Run: gcloud config set project $PROJECT_ID"
  exit 1
fi

# Verify Cloud Run services exist
log_info "Checking Cloud Run services..."
BACKEND_URL=$(gcloud run services describe backend --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)" 2>/dev/null || echo "")
FRONTEND_URL=$(gcloud run services describe frontend --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)" 2>/dev/null || echo "")

if [[ -z "$BACKEND_URL" ]]; then
  echo -e "${RED}ERROR: Cloud Run 'backend' service not found in $REGION${NC}"
  echo "Deploy it first via GitHub Actions (push a tt-v* tag)."
  exit 1
fi
if [[ -z "$FRONTEND_URL" ]]; then
  echo -e "${RED}ERROR: Cloud Run 'frontend' service not found in $REGION${NC}"
  echo "Deploy it first via GitHub Actions (push a tt-v* tag)."
  exit 1
fi
log_success "Backend  : $BACKEND_URL"
log_success "Frontend : $FRONTEND_URL"

# ── Step 1: Static IP ─────────────────────────────────────────────────────────
log_section "STEP 1: Static IP"
if gcloud compute addresses describe "$STATIC_IP_NAME" --global --project="$PROJECT_ID" >/dev/null 2>&1; then
  log_warning "Static IP '$STATIC_IP_NAME' already exists"
else
  gcloud compute addresses create "$STATIC_IP_NAME" --global --project="$PROJECT_ID" --quiet
  log_success "Static IP created"
fi
STATIC_IP=$(gcloud compute addresses describe "$STATIC_IP_NAME" --global --project="$PROJECT_ID" --format="value(address)")
LOAD_BALANCER_URL="https://${STATIC_IP}.nip.io"
log_success "Static IP : $STATIC_IP  →  $LOAD_BALANCER_URL"

# ── Step 2: Serverless NEGs ───────────────────────────────────────────────────
log_section "STEP 2: Serverless NEGs"
if gcloud compute network-endpoint-groups describe "$FRONTEND_NEG" --region="$REGION" --project="$PROJECT_ID" >/dev/null 2>&1; then
  log_warning "Frontend NEG already exists"
else
  gcloud compute network-endpoint-groups create "$FRONTEND_NEG" \
    --region="$REGION" --network-endpoint-type=serverless \
    --cloud-run-service=frontend --project="$PROJECT_ID" --quiet
  log_success "Frontend NEG created"
fi

if gcloud compute network-endpoint-groups describe "$BACKEND_NEG" --region="$REGION" --project="$PROJECT_ID" >/dev/null 2>&1; then
  log_warning "Backend NEG already exists"
else
  gcloud compute network-endpoint-groups create "$BACKEND_NEG" \
    --region="$REGION" --network-endpoint-type=serverless \
    --cloud-run-service=backend --project="$PROJECT_ID" --quiet
  log_success "Backend NEG created"
fi

# ── Step 3: Backend Services ──────────────────────────────────────────────────
log_section "STEP 3: Backend Services"
if gcloud compute backend-services describe "$FRONTEND_BS" --global --project="$PROJECT_ID" >/dev/null 2>&1; then
  log_warning "Frontend backend service already exists"
else
  gcloud compute backend-services create "$FRONTEND_BS" \
    --global --load-balancing-scheme=EXTERNAL_MANAGED \
    --protocol=HTTP --project="$PROJECT_ID" --quiet
  log_success "Frontend backend service created"
fi
gcloud compute backend-services add-backend "$FRONTEND_BS" \
  --global --network-endpoint-group="$FRONTEND_NEG" \
  --network-endpoint-group-region="$REGION" \
  --project="$PROJECT_ID" --quiet 2>/dev/null && log_success "Frontend NEG attached" || log_warning "Frontend NEG already attached"

if gcloud compute backend-services describe "$BACKEND_BS" --global --project="$PROJECT_ID" >/dev/null 2>&1; then
  log_warning "Backend backend service already exists"
else
  gcloud compute backend-services create "$BACKEND_BS" \
    --global --load-balancing-scheme=EXTERNAL_MANAGED \
    --protocol=HTTP --project="$PROJECT_ID" --quiet
  log_success "Backend backend service created"
fi
gcloud compute backend-services add-backend "$BACKEND_BS" \
  --global --network-endpoint-group="$BACKEND_NEG" \
  --network-endpoint-group-region="$REGION" \
  --project="$PROJECT_ID" --quiet 2>/dev/null && log_success "Backend NEG attached" || log_warning "Backend NEG already attached"

# ── Step 4: URL Map ───────────────────────────────────────────────────────────
log_section "STEP 4: URL Map"
FRONTEND_BS_URL="https://www.googleapis.com/compute/v1/projects/${PROJECT_ID}/global/backendServices/${FRONTEND_BS}"
BACKEND_BS_URL="https://www.googleapis.com/compute/v1/projects/${PROJECT_ID}/global/backendServices/${BACKEND_BS}"

if gcloud compute url-maps describe "$URL_MAP" --global --project="$PROJECT_ID" >/dev/null 2>&1; then
  log_warning "URL map already exists — updating path rules..."
else
  gcloud compute url-maps create "$URL_MAP" \
    --default-service="$FRONTEND_BS" \
    --global --project="$PROJECT_ID" --quiet
  log_success "URL map created"
fi

# Write/update path rules with fully-qualified resource URLs
cat > /tmp/tt-url-map.yaml << URLMAP
defaultService: ${FRONTEND_BS_URL}
hostRules:
- hosts:
  - '*'
  pathMatcher: allpaths
name: ${URL_MAP}
pathMatchers:
- defaultService: ${FRONTEND_BS_URL}
  name: allpaths
  pathRules:
  - paths:
    - /api/*
    - /docs
    - /openapi.json
    service: ${BACKEND_BS_URL}
URLMAP
gcloud compute url-maps import "$URL_MAP" \
  --global --project="$PROJECT_ID" \
  --source=/tmp/tt-url-map.yaml --quiet
log_success "URL map path rules set: /api/* → backend, /* → frontend"

# ── Step 5: SSL Certificate ───────────────────────────────────────────────────
log_section "STEP 5: SSL Certificate"
if gcloud compute ssl-certificates describe "$SSL_CERT_NAME" --global --project="$PROJECT_ID" >/dev/null 2>&1; then
  log_warning "SSL certificate already exists"
else
  gcloud compute ssl-certificates create "$SSL_CERT_NAME" \
    --domains="${STATIC_IP}.nip.io" \
    --global --project="$PROJECT_ID" --quiet
  log_success "SSL certificate created (provisioning takes 10-15 min)"
fi
SSL_STATUS=$(gcloud compute ssl-certificates describe "$SSL_CERT_NAME" --global --project="$PROJECT_ID" --format="value(managed.status)" 2>/dev/null || echo "UNKNOWN")
log_info "SSL status: $SSL_STATUS"

# ── Step 6: HTTPS Proxy + Forwarding Rule ────────────────────────────────────
log_section "STEP 6: HTTPS Proxy + Forwarding Rule"
if gcloud compute target-https-proxies describe "$HTTPS_PROXY" --global --project="$PROJECT_ID" >/dev/null 2>&1; then
  log_warning "HTTPS proxy already exists"
else
  gcloud compute target-https-proxies create "$HTTPS_PROXY" \
    --url-map="$URL_MAP" \
    --ssl-certificates="$SSL_CERT_NAME" \
    --global --project="$PROJECT_ID" --quiet
  log_success "HTTPS proxy created"
fi

if gcloud compute forwarding-rules describe "$FORWARDING_RULE" --global --project="$PROJECT_ID" >/dev/null 2>&1; then
  log_warning "Forwarding rule already exists"
else
  gcloud compute forwarding-rules create "$FORWARDING_RULE" \
    --address="$STATIC_IP_NAME" \
    --target-https-proxy="$HTTPS_PROXY" \
    --ports=443 \
    --global --project="$PROJECT_ID" --quiet
  log_success "Forwarding rule created"
fi

# ── Step 7: OAuth Brand + Client ──────────────────────────────────────────────
log_section "STEP 7: OAuth Brand + Client"
BRAND_PATH="projects/${PROJECT_NUMBER}/brands/${PROJECT_NUMBER}"

# Check if brand exists
BRAND_EXISTS=$(gcloud iap oauth-brands list --project="$PROJECT_ID" --format="value(name)" 2>/dev/null | head -1 || echo "")
if [[ -z "$BRAND_EXISTS" ]]; then
  log_info "Creating OAuth brand..."
  gcloud iap oauth-brands create \
    --application_title="TT RAG Agent" \
    --support_email="$IAP_ADMIN_USER" \
    --project="$PROJECT_ID" --quiet 2>/dev/null || log_warning "Brand creation may require manual setup in Console"
else
  log_warning "OAuth brand already exists: $BRAND_EXISTS"
  BRAND_PATH="$BRAND_EXISTS"
fi

log_info "Creating OAuth client..."
OAUTH_OUTPUT=$(gcloud iap oauth-clients create "$BRAND_PATH" \
  --display_name="TT Load Balancer IAP Client" \
  --project="$PROJECT_ID" 2>/dev/null || echo "")

if [[ -n "$OAUTH_OUTPUT" ]]; then
  CLIENT_ID=$(echo "$OAUTH_OUTPUT" | grep -o '[0-9]*-[a-zA-Z0-9]*.apps.googleusercontent.com' || echo "")
  CLIENT_SECRET=$(echo "$OAUTH_OUTPUT" | grep -o 'GOCSPX-[a-zA-Z0-9_-]*' || echo "")
  log_success "OAuth client created: $CLIENT_ID"
else
  log_warning "Could not auto-create OAuth client — checking for existing..."
  EXISTING_CLIENT=$(gcloud iap oauth-clients list "$BRAND_PATH" --project="$PROJECT_ID" --format="value(name)" 2>/dev/null | head -1 || echo "")
  if [[ -n "$EXISTING_CLIENT" ]]; then
    log_info "Using existing client: $EXISTING_CLIENT"
    CLIENT_ID=$(gcloud iap oauth-clients describe "$EXISTING_CLIENT" --project="$PROJECT_ID" --format="value(clientId)" 2>/dev/null || echo "")
    log_warning "CLIENT_SECRET not available for existing client — IAP enable step will be skipped."
    log_warning "To enable IAP manually, go to: https://console.cloud.google.com/security/iap?project=$PROJECT_ID"
    CLIENT_SECRET=""
  fi
fi

# ── Step 8: Enable IAP on Backend Services ────────────────────────────────────
log_section "STEP 8: Enable IAP"
if [[ -n "${CLIENT_ID:-}" && -n "${CLIENT_SECRET:-}" ]]; then
  gcloud compute backend-services update "$FRONTEND_BS" \
    --global --project="$PROJECT_ID" \
    --iap=enabled,oauth2-client-id="$CLIENT_ID",oauth2-client-secret="$CLIENT_SECRET" \
    --quiet
  log_success "IAP enabled on frontend backend service"

  gcloud compute backend-services update "$BACKEND_BS" \
    --global --project="$PROJECT_ID" \
    --iap=enabled,oauth2-client-id="$CLIENT_ID",oauth2-client-secret="$CLIENT_SECRET" \
    --quiet
  log_success "IAP enabled on backend backend service"
else
  log_warning "Skipping IAP enablement — CLIENT_SECRET not available."
  log_warning "Enable manually at: https://console.cloud.google.com/security/iap?project=$PROJECT_ID"
fi

# ── Step 9: IAP Access Permissions ───────────────────────────────────────────
log_section "STEP 9: IAP Access Permissions"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="user:$IAP_ADMIN_USER" \
  --role="roles/iap.httpsResourceAccessor" \
  --quiet 2>/dev/null && log_success "IAP access granted to $IAP_ADMIN_USER" || log_warning "Failed to grant IAP access to $IAP_ADMIN_USER"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="domain:$ORGANIZATION_DOMAIN" \
  --role="roles/iap.httpsResourceAccessor" \
  --quiet 2>/dev/null && log_success "IAP access granted to domain $ORGANIZATION_DOMAIN" || log_warning "Failed to grant domain IAP access"

# ── Step 10: IAP SA → Cloud Run Invoker ──────────────────────────────────────
log_section "STEP 10: IAP Service Account → Cloud Run Invoker"
gcloud beta services identity create --service=iap.googleapis.com --project="$PROJECT_ID" --quiet 2>/dev/null || true
IAP_SA="service-${PROJECT_NUMBER}@gcp-sa-iap.iam.gserviceaccount.com"
log_info "IAP SA: $IAP_SA"

for svc in backend frontend; do
  gcloud run services add-iam-policy-binding "$svc" \
    --region="$REGION" --project="$PROJECT_ID" \
    --member="serviceAccount:$IAP_SA" \
    --role="roles/run.invoker" \
    --quiet 2>/dev/null && log_success "Cloud Run invoker granted: $svc" || log_warning "Could not bind $svc (may already exist)"
done

# ── Step 11: Inject PROJECT_NUMBER + BACKEND_SERVICE_ID into Cloud Run backend ─
log_section "STEP 11: Inject IAP env vars into Cloud Run backend"
BACKEND_SERVICE_ID=$(gcloud compute backend-services describe "$BACKEND_BS" \
  --global --project="$PROJECT_ID" --format="value(id)" 2>/dev/null || echo "")

if [[ -n "$BACKEND_SERVICE_ID" ]]; then
  log_info "BACKEND_SERVICE_ID = $BACKEND_SERVICE_ID"
  gcloud run services update backend \
    --region="$REGION" --project="$PROJECT_ID" \
    --update-env-vars="PROJECT_NUMBER=${PROJECT_NUMBER},BACKEND_SERVICE_ID=${BACKEND_SERVICE_ID}" \
    --quiet
  log_success "PROJECT_NUMBER + BACKEND_SERVICE_ID injected into backend Cloud Run service"
else
  log_warning "Could not retrieve BACKEND_SERVICE_ID — skipping env var injection"
fi

# ── Step 12: Secret Manager — secret_key ─────────────────────────────────────
log_section "STEP 12: Secret Manager — tt-app-secret-key"
if gcloud secrets describe tt-app-secret-key --project="$PROJECT_ID" >/dev/null 2>&1; then
  log_warning "Secret 'tt-app-secret-key' already exists"
else
  echo -n "$SECRET_KEY" | gcloud secrets create tt-app-secret-key \
    --data-file=- \
    --replication-policy=automatic \
    --project="$PROJECT_ID" --quiet
  log_success "Secret 'tt-app-secret-key' created"
fi

# Grant backend SA access to the secret
BACKEND_SA="backend-sa@${PROJECT_ID}.iam.gserviceaccount.com"
gcloud secrets add-iam-policy-binding tt-app-secret-key \
  --member="serviceAccount:$BACKEND_SA" \
  --role="roles/secretmanager.secretAccessor" \
  --project="$PROJECT_ID" --quiet 2>/dev/null && log_success "Backend SA granted secret access" || log_warning "Could not grant secret access to $BACKEND_SA"

# ── Summary ───────────────────────────────────────────────────────────────────
log_section "COMPLETE"
echo ""
echo -e "${GREEN}Load Balancer URL : $LOAD_BALANCER_URL${NC}"
echo -e "${YELLOW}SSL cert status   : $SSL_STATUS (may take 10-15 min to become ACTIVE)${NC}"
echo ""
echo -e "${CYAN}Next steps:${NC}"
echo "  1. Wait for SSL cert to become ACTIVE (check: gcloud compute ssl-certificates describe $SSL_CERT_NAME --global)"
echo "  2. Update environments/tt.yaml → frontend.backend_url with the backend Cloud Run URL: $BACKEND_URL"
echo "  3. Update deploy-tt.yml to pass PROJECT_NUMBER + BACKEND_SERVICE_ID on every deploy"
echo "  4. Add redirect URI '$LOAD_BALANCER_URL/_gcp_gatekeeper/authenticate' to OAuth client in Cloud Console"
echo "  5. Trigger a new tt-v* tag to redeploy with updated frontend backend URL"
echo ""
echo -e "  IAP Console: ${BLUE}https://console.cloud.google.com/security/iap?project=$PROJECT_ID${NC}"
echo ""
