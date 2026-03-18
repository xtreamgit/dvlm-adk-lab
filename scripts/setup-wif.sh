#!/bin/bash
#
# setup-wif.sh - Set up Workload Identity Federation for GitHub Actions
#
# Run this once per GCP project to allow GitHub Actions to authenticate
# without long-lived service account keys.
#
# Usage:
#   bash scripts/setup-wif.sh tt
#   bash scripts/setup-wif.sh develom
#
# After running, copy the printed outputs into GitHub Environment secrets:
#   WIF_PROVIDER  → TT_WIF_PROVIDER or DEVELOM_WIF_PROVIDER
#   DEPLOY_SA     → TT_DEPLOY_SA or DEVELOM_DEPLOY_SA
#

set -euo pipefail

ENV="${1:-}"
if [[ -z "$ENV" ]]; then
    echo "Usage: bash scripts/setup-wif.sh <env>"
    echo "       where <env> is: tt | develom"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/env-load.sh" "$ENV"

GITHUB_ORG="xtreamgit"
GITHUB_REPO="adk-multi-agents-auto"

POOL_ID="github-actions-pool"
PROVIDER_ID="github-actions-provider"
SA_NAME="github-actions-deploy"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo ""
echo "=== Setting up Workload Identity Federation ==="
echo "  Project  : $PROJECT_ID"
echo "  Env      : $ENV"
echo "  SA Email : $SA_EMAIL"
echo ""

# ---- Step 1: Enable required APIs ----
echo "[1/6] Enabling required APIs..."
gcloud services enable iamcredentials.googleapis.com \
    --project="$PROJECT_ID" --quiet
gcloud services enable sts.googleapis.com \
    --project="$PROJECT_ID" --quiet
echo "  APIs enabled."

# ---- Step 2: Create service account ----
echo "[2/6] Creating deploy service account..."
if gcloud iam service-accounts describe "$SA_EMAIL" \
    --project="$PROJECT_ID" &>/dev/null; then
    echo "  Service account already exists: $SA_EMAIL"
else
    gcloud iam service-accounts create "$SA_NAME" \
        --project="$PROJECT_ID" \
        --display-name="GitHub Actions Deploy SA (${ENV})" \
        --description="Used by GitHub Actions to deploy to ${ENV}"
    echo "  Created: $SA_EMAIL"
    echo "  Waiting for SA propagation..."
    for i in $(seq 1 12); do
        if gcloud iam service-accounts describe "$SA_EMAIL" \
            --project="$PROJECT_ID" &>/dev/null; then
            echo "  SA is ready."
            break
        fi
        echo "  Attempt $i/12: SA not yet visible, waiting 5s..."
        sleep 5
    done
fi

# ---- Step 3: Grant roles to service account ----
echo "[3/6] Granting IAM roles to service account..."
for ROLE in \
    "roles/run.admin" \
    "roles/cloudbuild.builds.editor" \
    "roles/artifactregistry.writer" \
    "roles/cloudsql.client" \
    "roles/iam.serviceAccountUser" \
    "roles/storage.objectAdmin"; do
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="$ROLE" \
        --quiet
    echo "  Granted: $ROLE"
done

# ---- Step 4: Create Workload Identity Pool ----
echo "[4/6] Creating Workload Identity Pool..."
if gcloud iam workload-identity-pools describe "$POOL_ID" \
    --project="$PROJECT_ID" \
    --location="global" &>/dev/null; then
    echo "  Pool already exists: $POOL_ID"
else
    gcloud iam workload-identity-pools create "$POOL_ID" \
        --project="$PROJECT_ID" \
        --location="global" \
        --display-name="GitHub Actions Pool" \
        --description="Pool for GitHub Actions OIDC authentication"
    echo "  Created pool: $POOL_ID"
fi

POOL_RESOURCE="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}"

# ---- Step 5: Create OIDC Provider ----
echo "[5/6] Creating OIDC Provider..."
if gcloud iam workload-identity-pools providers describe "$PROVIDER_ID" \
    --project="$PROJECT_ID" \
    --location="global" \
    --workload-identity-pool="$POOL_ID" &>/dev/null; then
    echo "  Provider already exists: $PROVIDER_ID"
else
    gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_ID" \
        --project="$PROJECT_ID" \
        --location="global" \
        --workload-identity-pool="$POOL_ID" \
        --display-name="GitHub OIDC Provider" \
        --issuer-uri="https://token.actions.githubusercontent.com" \
        --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
        --attribute-condition="assertion.repository=='${GITHUB_ORG}/${GITHUB_REPO}'"
    echo "  Created provider: $PROVIDER_ID"
fi

# ---- Step 6: Bind service account to WIF pool ----
echo "[6/6] Binding service account to Workload Identity Pool..."
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
    --project="$PROJECT_ID" \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/${POOL_RESOURCE}/attribute.repository/${GITHUB_ORG}/${GITHUB_REPO}" \
    --quiet
echo "  Binding complete."

# ---- Output: copy these into GitHub Secrets ----
WIF_PROVIDER="${POOL_RESOURCE}/providers/${PROVIDER_ID}"

echo ""
echo "============================================================"
echo "  WIF SETUP COMPLETE — Add these to GitHub Environment: $ENV"
echo "============================================================"
echo ""
if [[ "$ENV" == "tt" ]]; then
    echo "  Secret name : TT_WIF_PROVIDER"
    echo "  Secret value: ${WIF_PROVIDER}"
    echo ""
    echo "  Secret name : TT_DEPLOY_SA"
    echo "  Secret value: ${SA_EMAIL}"
elif [[ "$ENV" == "develom" ]]; then
    echo "  Secret name : DEVELOM_WIF_PROVIDER"
    echo "  Secret value: ${WIF_PROVIDER}"
    echo ""
    echo "  Secret name : DEVELOM_DEPLOY_SA"
    echo "  Secret value: ${SA_EMAIL}"
fi
echo ""
echo "  GitHub Environments settings:"
echo "  https://github.com/${GITHUB_ORG}/${GITHUB_REPO}/settings/environments"
echo "============================================================"
