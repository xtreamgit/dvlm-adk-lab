#!/bin/bash
#
# env-load.sh - Load environment variables from environments/<env>.yaml
#
# Usage:
#   source scripts/env-load.sh <env>
#   source scripts/env-load.sh tt
#   source scripts/env-load.sh develom
#   source scripts/env-load.sh usfs
#

ENV="${1:-}"

if [[ -z "$ENV" ]]; then
    echo "ERROR: Environment name required."
    echo "Usage: source scripts/env-load.sh <env>"
    echo "       where <env> is: tt | develom | usfs"
    return 1 2>/dev/null || exit 1
fi

YAML_FILE="environments/${ENV}.yaml"

if [[ ! -f "$YAML_FILE" ]]; then
    echo "ERROR: Environment config not found: $YAML_FILE"
    return 1 2>/dev/null || exit 1
fi

# Helper: extract a value from YAML by key (simple single-level key)
_yaml_val() {
    grep -E "^${1}:" "$YAML_FILE" | head -1 | sed 's/^[^:]*: *//' | tr -d '"' | tr -d "'"
}

# Helper: extract a nested value (one level deep)
_yaml_nested() {
    local parent="$1"
    local key="$2"
    # Find the parent block and extract the child key
    awk "/^${parent}:/{found=1; next} found && /^  ${key}:/{print; exit} found && /^[^ ]/{exit}" "$YAML_FILE" \
        | sed 's/^[^:]*: *//' | tr -d '"' | tr -d "'"
}

echo "Loading environment: $ENV ($YAML_FILE)"

# ---- Core project vars ----
export ENV_NAME="$ENV"
export PROJECT_ID="$(_yaml_val project_id)"
export PROJECT_NUMBER="$(_yaml_val project_number)"
export REGION="$(_yaml_val region)"
export ORGANIZATION_DOMAIN="$(_yaml_val organization_domain)"
export IAP_ADMIN_USER="$(_yaml_val iap_admin_user)"
export REPO="$(_yaml_val repo)"
export ACCOUNT_ENV="$(_yaml_val account_env)"

# ---- Artifact Registry image paths ----
export AR_REPO="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}"
export BACKEND_IMAGE="${AR_REPO}/backend:latest"
export FRONTEND_IMAGE="${AR_REPO}/frontend:latest"

# ---- Cloud SQL ----
export CLOUD_SQL_INSTANCE="$(_yaml_nested database cloud_sql_instance)"
export CLOUD_SQL_CONNECTION="$(_yaml_nested database cloud_sql_connection)"
export DB_NAME="$(_yaml_nested database name)"
export DB_USER="$(_yaml_nested database user)"
export DB_PASSWORD_SECRET="$(_yaml_nested database password_secret_name)"

# ---- Cloud Run service names (standard names) ----
export BACKEND_SERVICE="backend"
export FRONTEND_SERVICE="frontend"
export BACKEND_SERVICES="$(_yaml_val backend_services)"

# ---- Vertex AI ----
export VERTEX_AI_LOCATION="$(_yaml_nested vertex_ai location)"
export EMBEDDING_MODEL="$(_yaml_nested vertex_ai embedding_model)"

echo "  PROJECT_ID          = $PROJECT_ID"
echo "  REGION              = $REGION"
echo "  AR_REPO             = $AR_REPO"
echo "  BACKEND_IMAGE       = $BACKEND_IMAGE"
echo "  FRONTEND_IMAGE      = $FRONTEND_IMAGE"
echo "  CLOUD_SQL_CONNECTION= $CLOUD_SQL_CONNECTION"
echo "  ACCOUNT_ENV         = $ACCOUNT_ENV"
echo "  BACKEND_SERVICES    = $BACKEND_SERVICES"
echo "  DB_PASSWORD_SECRET  = $DB_PASSWORD_SECRET"
echo ""
echo "Environment '$ENV' loaded. Run: bash scripts/deploy-env.sh $ENV"
