#!/bin/bash
#
# usfs-sync-and-deploy.sh — Sync USFS mirror and deploy
#
# Combines mirror sync, pull latest, and deploy into a single command.
# Run on: USFS Cloud Workstation only
#
# Usage:
#   bash scripts/usfs-sync-and-deploy.sh           # deploy from main (latest)
#   bash scripts/usfs-sync-and-deploy.sh usfs-v0.1.3  # deploy a specific tag
#

set -euo pipefail

# ---- Constants (override with env vars if your paths differ) ----
# Auto-detect working clone location (USFS mirror on workstation, canonical on Mac)
if [[ -n "${WORKING_CLONE:-}" ]]; then
    : # already set by env var
elif [[ -d "$HOME/github.com/Hector-Dejesus/adk-multi-agents-auto-mirror/.git" ]]; then
    WORKING_CLONE="$HOME/github.com/Hector-Dejesus/adk-multi-agents-auto-mirror"
elif [[ -d "$HOME/github.com/xtreamgit/adk-multi-agents-auto/.git" ]]; then
    WORKING_CLONE="$HOME/github.com/xtreamgit/adk-multi-agents-auto"
else
    echo -e "\033[0;31m[ERROR]\033[0m   Cannot auto-detect clone location."
    echo "         Set WORKING_CLONE env var, e.g.:"
    echo "           export WORKING_CLONE=~/github.com/Hector-Dejesus/adk-multi-agents-auto-mirror"
    exit 1
fi

ENV="usfs"

# ---- Colours ----
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log_info()    { echo -e "${BLUE}[INFO]${NC}    $*"; }
log_success() { echo -e "${GREEN}[OK]${NC}      $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}    $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC}   $*"; }
log_section() { echo -e "\n${BLUE}=== $* ===${NC}"; }

# ---- Optional tag argument ----
TAG="${1:-}"

# ---- Step 1: Sync the mirror ----
log_section "Step 1: Sync canonical → USFS mirror"
if [[ ! -d "$WORKING_CLONE" ]]; then
    log_error "Clone not found at $WORKING_CLONE"
    log_error "Run the one-time setup first (see docs/USFS_WORKSTATION_DEPLOY.md)"
    exit 1
fi

cd "$WORKING_CLONE"
bash scripts/usfs-smart-sync.sh
log_success "Mirror synced"

# ---- Step 2: Checkout release tag ----
log_section "Step 2: Checkout release"
git fetch origin --tags
if [[ -n "$TAG" ]]; then
    log_info "Checking out tag: $TAG"
    git checkout "$TAG"
    log_info "Commit SHA: $(git rev-parse HEAD)"
else
    log_info "Pulling latest main"
    git checkout main 2>/dev/null || true
    git pull origin main
    log_info "Commit SHA: $(git rev-parse HEAD)"
fi
log_success "Ready for deploy"

# ---- Step 3: Load env config and deploy ----
log_section "Step 3: Deploy to USFS environment"
source scripts/env-load.sh "$ENV"
bash scripts/deploy-env.sh "$ENV"

# ---- Step 4: Show access info ----
log_section "Deployment complete"
STATIC_IP=$(gcloud compute addresses describe usfs-rag-agent-ip \
    --global --project=usfs-gcp-arch-testing \
    --format='value(address)' 2>/dev/null || echo "")

if [[ -n "$STATIC_IP" ]]; then
    echo ""
    echo "  Load Balancer URL: https://${STATIC_IP}.nip.io"
    echo "  Health check:      curl -sk https://${STATIC_IP}.nip.io/api/health"
    echo ""
else
    log_warn "No load balancer detected — use Cloud Run URLs from the deploy output above"
fi
