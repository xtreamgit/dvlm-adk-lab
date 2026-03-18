#!/bin/bash
#
# setup-usfs-loadbalancer.sh — One-time USFS Load Balancer setup
#
# Creates an External HTTPS Load Balancer with managed SSL (nip.io)
# and path-based routing (/ → frontend, /api/* → backend).
#
# Based on infrastructure/lib/loadbalancer.sh, adapted for USFS
# single-agent environment.
#
# Usage:  bash scripts/setup-usfs-loadbalancer.sh
# Run on: USFS Cloud Workstation only
#

set -euo pipefail

# ---- USFS environment constants ----
PROJECT_ID="usfs-gcp-arch-testing"
REGION="us-east4"
IP_NAME="usfs-rag-agent-ip"
SSL_CERT_NAME="usfs-rag-agent-ssl-cert"
URL_MAP_NAME="usfs-rag-agent-url-map"
HTTPS_PROXY_NAME="usfs-rag-agent-https-proxy"
FORWARDING_RULE_NAME="usfs-rag-agent-forwarding-rule"
FRONTEND_NEG="frontend-neg"
BACKEND_NEG="backend-neg"
FRONTEND_BACKEND_SVC="frontend-backend-service"
BACKEND_BACKEND_SVC="backend-backend-service"
FRONTEND_CR_SERVICE="frontend"
BACKEND_CR_SERVICE="backend"

# ---- Colours ----
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log_info()    { echo -e "${BLUE}[INFO]${NC}    $*"; }
log_success() { echo -e "${GREEN}[OK]${NC}      $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}    $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC}   $*"; }
log_section() { echo -e "\n${BLUE}=== $* ===${NC}"; }

# ---- Pre-flight checks ----
log_section "Pre-flight checks"
ACTIVE_PROJECT=$(gcloud config get-value project 2>/dev/null || true)
if [[ "$ACTIVE_PROJECT" != "$PROJECT_ID" ]]; then
    log_info "Setting active project to $PROJECT_ID"
    gcloud config set project "$PROJECT_ID" --quiet
fi
log_success "Project: $PROJECT_ID | Region: $REGION"

# ---- Step 1: Reserve global static IP ----
log_section "Step 1: Reserve global static IP"
if gcloud compute addresses describe "$IP_NAME" --global --project="$PROJECT_ID" >/dev/null 2>&1; then
    log_warn "Static IP '$IP_NAME' already exists"
else
    gcloud compute addresses create "$IP_NAME" \
        --global \
        --project="$PROJECT_ID" \
        --quiet
    log_success "Static IP created"
fi

STATIC_IP=$(gcloud compute addresses describe "$IP_NAME" \
    --global \
    --project="$PROJECT_ID" \
    --format="value(address)")
LOAD_BALANCER_URL="https://${STATIC_IP}.nip.io"
log_info "Static IP: $STATIC_IP"
log_info "Load Balancer URL: $LOAD_BALANCER_URL"

# ---- Step 2: Create managed SSL certificate (nip.io) ----
log_section "Step 2: Create managed SSL certificate"
if gcloud compute ssl-certificates describe "$SSL_CERT_NAME" --global --project="$PROJECT_ID" >/dev/null 2>&1; then
    log_warn "SSL certificate '$SSL_CERT_NAME' already exists"
else
    gcloud compute ssl-certificates create "$SSL_CERT_NAME" \
        --domains="${STATIC_IP}.nip.io" \
        --global \
        --project="$PROJECT_ID" \
        --quiet
    log_success "SSL certificate created (provisioning in progress — takes 10-20 min)"
fi

SSL_STATUS=$(gcloud compute ssl-certificates describe "$SSL_CERT_NAME" \
    --global \
    --project="$PROJECT_ID" \
    --format="value(managed.status)" 2>/dev/null || echo "UNKNOWN")
log_info "SSL Certificate Status: $SSL_STATUS"

# ---- Step 3: Create serverless NEGs ----
log_section "Step 3: Create serverless NEGs"

# Frontend NEG
if gcloud compute network-endpoint-groups describe "$FRONTEND_NEG" --region="$REGION" --project="$PROJECT_ID" >/dev/null 2>&1; then
    log_warn "Frontend NEG already exists"
else
    gcloud compute network-endpoint-groups create "$FRONTEND_NEG" \
        --region="$REGION" \
        --network-endpoint-type=serverless \
        --cloud-run-service="$FRONTEND_CR_SERVICE" \
        --project="$PROJECT_ID" \
        --quiet
    log_success "Frontend NEG created"
fi

# Backend NEG
if gcloud compute network-endpoint-groups describe "$BACKEND_NEG" --region="$REGION" --project="$PROJECT_ID" >/dev/null 2>&1; then
    log_warn "Backend NEG already exists"
else
    gcloud compute network-endpoint-groups create "$BACKEND_NEG" \
        --region="$REGION" \
        --network-endpoint-type=serverless \
        --cloud-run-service="$BACKEND_CR_SERVICE" \
        --project="$PROJECT_ID" \
        --quiet
    log_success "Backend NEG created"
fi

# ---- Step 4: Create LB backend services + attach NEGs ----
log_section "Step 4: Create LB backend services"

# Frontend backend service
if gcloud compute backend-services describe "$FRONTEND_BACKEND_SVC" --global --project="$PROJECT_ID" >/dev/null 2>&1; then
    log_warn "Frontend backend service already exists"
else
    gcloud compute backend-services create "$FRONTEND_BACKEND_SVC" \
        --global \
        --load-balancing-scheme=EXTERNAL_MANAGED \
        --protocol=HTTP \
        --port-name=http \
        --project="$PROJECT_ID" \
        --quiet
    log_success "Frontend backend service created"
fi

gcloud compute backend-services add-backend "$FRONTEND_BACKEND_SVC" \
    --global \
    --network-endpoint-group="$FRONTEND_NEG" \
    --network-endpoint-group-region="$REGION" \
    --project="$PROJECT_ID" \
    --quiet 2>/dev/null || log_info "Frontend NEG already attached"

# Backend backend service
if gcloud compute backend-services describe "$BACKEND_BACKEND_SVC" --global --project="$PROJECT_ID" >/dev/null 2>&1; then
    log_warn "Backend backend service already exists"
else
    gcloud compute backend-services create "$BACKEND_BACKEND_SVC" \
        --global \
        --load-balancing-scheme=EXTERNAL_MANAGED \
        --protocol=HTTP \
        --port-name=http \
        --project="$PROJECT_ID" \
        --quiet
    log_success "Backend backend service created"
fi

gcloud compute backend-services add-backend "$BACKEND_BACKEND_SVC" \
    --global \
    --network-endpoint-group="$BACKEND_NEG" \
    --network-endpoint-group-region="$REGION" \
    --project="$PROJECT_ID" \
    --quiet 2>/dev/null || log_info "Backend NEG already attached"

# ---- Step 5: Create URL map with path-based routing ----
log_section "Step 5: Create URL map"
if gcloud compute url-maps describe "$URL_MAP_NAME" --global --project="$PROJECT_ID" >/dev/null 2>&1; then
    log_warn "URL map '$URL_MAP_NAME' already exists"
else
    gcloud compute url-maps create "$URL_MAP_NAME" \
        --default-service="$FRONTEND_BACKEND_SVC" \
        --global \
        --project="$PROJECT_ID" \
        --quiet
    log_success "URL map created"
fi

gcloud compute url-maps add-path-matcher "$URL_MAP_NAME" \
    --path-matcher-name=api-matcher \
    --default-service="$FRONTEND_BACKEND_SVC" \
    --path-rules="/api/*=$BACKEND_BACKEND_SVC" \
    --global \
    --project="$PROJECT_ID" \
    --quiet 2>/dev/null || log_warn "Path matcher may already exist"

log_success "URL map configured (/ → frontend, /api/* → backend)"

# ---- Step 6: Create HTTPS proxy ----
log_section "Step 6: Create HTTPS proxy"
if gcloud compute target-https-proxies describe "$HTTPS_PROXY_NAME" --global --project="$PROJECT_ID" >/dev/null 2>&1; then
    log_warn "HTTPS proxy already exists"
else
    gcloud compute target-https-proxies create "$HTTPS_PROXY_NAME" \
        --ssl-certificates="$SSL_CERT_NAME" \
        --url-map="$URL_MAP_NAME" \
        --global \
        --project="$PROJECT_ID" \
        --quiet
    log_success "HTTPS proxy created"
fi

# ---- Step 7: Create forwarding rule ----
log_section "Step 7: Create forwarding rule"
if gcloud compute forwarding-rules describe "$FORWARDING_RULE_NAME" --global --project="$PROJECT_ID" >/dev/null 2>&1; then
    log_warn "Forwarding rule already exists"
else
    gcloud compute forwarding-rules create "$FORWARDING_RULE_NAME" \
        --address="$IP_NAME" \
        --target-https-proxy="$HTTPS_PROXY_NAME" \
        --global \
        --ports=443 \
        --load-balancing-scheme=EXTERNAL_MANAGED \
        --project="$PROJECT_ID" \
        --quiet
    log_success "Forwarding rule created"
fi

# ---- Finalize: Update backend CORS ----
log_section "Finalize: Update backend CORS"
gcloud run services update "$BACKEND_CR_SERVICE" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --update-env-vars="FRONTEND_URL=${LOAD_BALANCER_URL}" \
    --quiet
log_success "Backend CORS updated with LB URL"

# ---- Summary ----
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  USFS Load Balancer Setup Complete${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Project        : $PROJECT_ID"
echo "  Region         : $REGION"
echo "  Static IP      : $STATIC_IP"
echo "  LB URL         : $LOAD_BALANCER_URL"
echo "  SSL Status     : $SSL_STATUS"
echo ""
echo -e "  Routing:"
echo "    /        → frontend (Cloud Run)"
echo "    /api/*   → backend  (Cloud Run)"
echo ""

if [[ "$SSL_STATUS" != "ACTIVE" ]]; then
    echo -e "${YELLOW}  SSL certificate is still provisioning (10-20 min).${NC}"
    echo -e "${YELLOW}  Check status:${NC}"
    echo "    gcloud compute ssl-certificates describe $SSL_CERT_NAME --global --project=$PROJECT_ID --format='value(managed.status)'"
    echo ""
fi

echo "  Test backend:"
echo "    curl -sk ${LOAD_BALANCER_URL}/api/health"
echo ""
echo "  Open in browser (once SSL is ACTIVE):"
echo "    ${LOAD_BALANCER_URL}"
echo ""
