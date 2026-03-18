#!/bin/bash
#
# IAP Integration Deployment Script
# Deploys backend with IAP authentication support
#
# Usage: ./deploy_iap.sh [options]
# Options:
#   --project PROJECT_ID      GCP project ID (default: adk-rag-ma)
#   --region REGION           GCP region (default: us-west1)
#   --service SERVICE_NAME    Cloud Run service name (default: backend)
#   --dry-run                 Validate configuration without deploying
#   --skip-migration          Skip database migration
#   --skip-tests              Skip post-deployment tests
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
PROJECT_ID="${PROJECT_ID:-adk-rag-ma}"
REGION="${REGION:-us-west1}"
SERVICE_NAME="${SERVICE_NAME:-backend}"
DRY_RUN=false
SKIP_MIGRATION=false
SKIP_TESTS=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project)
            PROJECT_ID="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --service)
            SERVICE_NAME="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-migration)
            SKIP_MIGRATION=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --project PROJECT_ID      GCP project ID (default: adk-rag-ma)"
            echo "  --region REGION           GCP region (default: us-west1)"
            echo "  --service SERVICE_NAME    Cloud Run service name (default: backend)"
            echo "  --dry-run                 Validate configuration without deploying"
            echo "  --skip-migration          Skip database migration"
            echo "  --skip-tests              Skip post-deployment tests"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}IAP Integration Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Configuration:"
echo "  Project: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service: $SERVICE_NAME"
echo "  Dry Run: $DRY_RUN"
echo ""

# Function to print section headers
print_section() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to print info
print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check prerequisites
print_section "1. Checking Prerequisites"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI not found. Please install it first."
    exit 1
fi
print_success "gcloud CLI found"

# Check if authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    print_error "Not authenticated with gcloud. Run: gcloud auth login"
    exit 1
fi
print_success "Authenticated with gcloud"

# Set project
gcloud config set project "$PROJECT_ID" --quiet
print_success "Project set to $PROJECT_ID"

# Check if Python is available for migration
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    print_warning "Python not found. Database migration may fail."
    SKIP_MIGRATION=true
else
    print_success "Python found"
fi

# Get IAP configuration
print_section "2. Retrieving IAP Configuration"

# Get project number
print_info "Retrieving project number..."
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
if [ -z "$PROJECT_NUMBER" ]; then
    print_error "Failed to retrieve project number"
    exit 1
fi
print_success "Project Number: $PROJECT_NUMBER"

# Get backend service ID
print_info "Retrieving backend service ID..."
# List all backend services and find the one associated with our Cloud Run service
BACKEND_SERVICES=$(gcloud compute backend-services list --global --format="value(name)" 2>/dev/null)

if [ -z "$BACKEND_SERVICES" ]; then
    print_warning "No backend services found. IAP may not be configured yet."
    print_info "You'll need to configure IAP through Cloud Console or provide BACKEND_SERVICE_ID manually."
    BACKEND_SERVICE_ID=""
else
    # Try to find backend service by name pattern (often contains service name)
    BACKEND_SERVICE_NAME=$(echo "$BACKEND_SERVICES" | grep -i "$SERVICE_NAME" | head -n1)
    
    if [ -z "$BACKEND_SERVICE_NAME" ]; then
        print_warning "Could not auto-detect backend service. Using first available."
        BACKEND_SERVICE_NAME=$(echo "$BACKEND_SERVICES" | head -n1)
    fi
    
    if [ -n "$BACKEND_SERVICE_NAME" ]; then
        BACKEND_SERVICE_ID=$(gcloud compute backend-services describe "$BACKEND_SERVICE_NAME" --global --format="value(id)" 2>/dev/null)
        if [ -n "$BACKEND_SERVICE_ID" ]; then
            print_success "Backend Service: $BACKEND_SERVICE_NAME (ID: $BACKEND_SERVICE_ID)"
        else
            print_warning "Found backend service but couldn't retrieve ID"
            BACKEND_SERVICE_ID=""
        fi
    else
        BACKEND_SERVICE_ID=""
    fi
fi

# Construct IAP audience
if [ -n "$BACKEND_SERVICE_ID" ]; then
    IAP_AUDIENCE="/projects/$PROJECT_NUMBER/global/backendServices/$BACKEND_SERVICE_ID"
    print_success "IAP Audience: $IAP_AUDIENCE"
else
    print_warning "Backend service ID not found. IAP authentication will not work until configured."
    print_info "To manually set: export BACKEND_SERVICE_ID='your-backend-service-id'"
    IAP_AUDIENCE=""
fi

# Run database migration
if [ "$SKIP_MIGRATION" = false ]; then
    print_section "3. Running Database Migration"
    
    cd "$(dirname "$0")"
    
    if [ -f "src/database/migrations/run_migrations.py" ]; then
        print_info "Running migrations..."
        
        if command -v python3 &> /dev/null; then
            PYTHON_CMD=python3
        else
            PYTHON_CMD=python
        fi
        
        if $PYTHON_CMD src/database/migrations/run_migrations.py; then
            print_success "Database migration completed"
        else
            print_error "Database migration failed"
            print_warning "You may need to run migrations manually in production"
        fi
    else
        print_warning "Migration script not found. Skipping..."
    fi
else
    print_warning "Skipping database migration (--skip-migration flag)"
fi

# Build environment variables
print_section "4. Preparing Environment Variables"

ENV_VARS="PROJECT_NUMBER=$PROJECT_NUMBER"

if [ -n "$BACKEND_SERVICE_ID" ]; then
    ENV_VARS="$ENV_VARS,BACKEND_SERVICE_ID=$BACKEND_SERVICE_ID"
    print_success "IAP environment variables configured"
else
    print_warning "BACKEND_SERVICE_ID not set - IAP will not work"
fi

echo "Environment variables to set:"
echo "  $ENV_VARS"

# Dry run check
if [ "$DRY_RUN" = true ]; then
    print_section "Dry Run - Configuration Validated"
    print_info "Would deploy with the following configuration:"
    echo "  Project: $PROJECT_ID"
    echo "  Region: $REGION"
    echo "  Service: $SERVICE_NAME"
    echo "  Environment: $ENV_VARS"
    echo ""
    print_info "Run without --dry-run to deploy"
    exit 0
fi

# Deploy to Cloud Run
print_section "5. Deploying to Cloud Run"

print_info "Deploying $SERVICE_NAME to Cloud Run..."

DEPLOY_CMD="gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --timeout=300 \
    --cpu-boost \
    --set-env-vars $ENV_VARS"

echo "Deploy command:"
echo "$DEPLOY_CMD"
echo ""

if eval "$DEPLOY_CMD"; then
    print_success "Deployment successful"
else
    print_error "Deployment failed"
    exit 1
fi

# Get service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format="value(status.url)")
print_success "Service URL: $SERVICE_URL"

# Run post-deployment tests
if [ "$SKIP_TESTS" = false ]; then
    print_section "6. Running Post-Deployment Tests"
    
    print_info "Testing health endpoint..."
    if curl -sf "$SERVICE_URL/api/health" > /dev/null; then
        print_success "Health check passed"
    else
        print_error "Health check failed"
    fi
    
    print_info "Testing IAP status endpoint..."
    if curl -sf "$SERVICE_URL/api/iap/status" > /dev/null; then
        IAP_STATUS=$(curl -s "$SERVICE_URL/api/iap/status" | grep -o '"iap_enabled":[^,]*')
        print_success "IAP status endpoint accessible"
        echo "  $IAP_STATUS"
    else
        print_warning "IAP status endpoint not accessible"
    fi
    
    print_info "Testing IAP headers endpoint..."
    if curl -sf "$SERVICE_URL/api/iap/headers" > /dev/null; then
        print_success "IAP headers endpoint accessible"
    else
        print_warning "IAP headers endpoint not accessible"
    fi
else
    print_warning "Skipping post-deployment tests (--skip-tests flag)"
fi

# Summary
print_section "Deployment Summary"

print_success "Backend deployed successfully"
echo ""
echo "Service Details:"
echo "  Service: $SERVICE_NAME"
echo "  Region: $REGION"
echo "  URL: $SERVICE_URL"
echo ""
echo "IAP Configuration:"
echo "  Project Number: $PROJECT_NUMBER"
if [ -n "$BACKEND_SERVICE_ID" ]; then
    echo "  Backend Service ID: $BACKEND_SERVICE_ID"
    echo "  IAP Audience: $IAP_AUDIENCE"
    echo "  Status: ${GREEN}Configured${NC}"
else
    echo "  Status: ${YELLOW}Not Configured${NC}"
    echo ""
    echo "To complete IAP setup:"
    echo "  1. Create a Load Balancer with IAP enabled"
    echo "  2. Get the backend service ID"
    echo "  3. Redeploy with: BACKEND_SERVICE_ID='your-id' ./deploy_iap.sh"
fi
echo ""
echo "Next Steps:"
echo "  1. Test IAP endpoints: curl $SERVICE_URL/api/iap/status"
echo "  2. Configure IAP in Cloud Console if not already done"
echo "  3. Test authentication: curl $SERVICE_URL/api/iap/me"
echo "  4. Monitor logs: gcloud logs read --service=$SERVICE_NAME --limit=50"
echo ""
print_success "Deployment complete!"
