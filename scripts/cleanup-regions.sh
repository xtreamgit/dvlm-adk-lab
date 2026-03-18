#!/bin/bash
# Cleanup Script - Remove Services from us-west2 and us-east4
# Keep only us-west1 region

set -e

PROJECT_ID="adk-rag-ma"
KEEP_REGION="us-west1"
REMOVE_REGIONS=("us-west2" "us-east4")

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧹 Multi-Region Cleanup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "This script will:"
echo "  ✅ Keep services in: $KEEP_REGION"
echo "  ❌ Remove services from: ${REMOVE_REGIONS[*]}"
echo ""
read -p "Continue? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

SERVICES=("backend" "backend-agent1" "backend-agent2" "backend-agent3" "frontend")

# Step 1: Remove backends from Load Balancer
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Remove backends from Load Balancer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

for region in "${REMOVE_REGIONS[@]}"; do
    echo "Removing $region backends from Load Balancer..."
    
    for service in "${SERVICES[@]}"; do
        echo "  Removing $service-neg from $region..."
        
        # Remove backend from backend service
        gcloud compute backend-services remove-backend ${service}-backend-service \
            --network-endpoint-group=${service}-neg \
            --network-endpoint-group-region=$region \
            --global \
            --project=$PROJECT_ID \
            --quiet 2>/dev/null || echo "    (Backend not found or already removed)"
    done
done

echo "✅ Load Balancer backends removed"

# Step 2: Delete Cloud Run services
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Delete Cloud Run services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

for region in "${REMOVE_REGIONS[@]}"; do
    echo "Deleting services in $region..."
    
    for service in "${SERVICES[@]}"; do
        echo "  Deleting $service..."
        gcloud run services delete $service \
            --region=$region \
            --project=$PROJECT_ID \
            --quiet 2>/dev/null || echo "    (Service not found or already deleted)"
    done
done

echo "✅ Cloud Run services deleted"

# Step 3: Delete Network Endpoint Groups
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Delete Network Endpoint Groups"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

for region in "${REMOVE_REGIONS[@]}"; do
    echo "Deleting NEGs in $region..."
    
    for service in "${SERVICES[@]}"; do
        echo "  Deleting ${service}-neg..."
        gcloud compute network-endpoint-groups delete ${service}-neg \
            --region=$region \
            --project=$PROJECT_ID \
            --quiet 2>/dev/null || echo "    (NEG not found or already deleted)"
    done
done

echo "✅ Network Endpoint Groups deleted"

# Step 4: Verify cleanup
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Remaining Cloud Run services:"
gcloud run services list --project=$PROJECT_ID \
    --format='table(SERVICE,REGION)'

echo ""
echo "Load Balancer backends:"
gcloud compute backend-services describe backend-backend-service \
    --global --project=$PROJECT_ID \
    --format='value(backends.group)' 2>/dev/null | grep -o 'regions/[^/]*' | sort -u || echo "No backends found"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Cleanup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Summary:"
echo "  ✅ Kept services in: $KEEP_REGION"
echo "  ❌ Removed services from: ${REMOVE_REGIONS[*]}"
echo ""
echo "💡 Next steps:"
echo "  1. Test the application: https://34.49.46.115.nip.io"
echo "  2. Update deployment scripts to only use $KEEP_REGION"
echo "  3. Update documentation to reflect single-region architecture"
echo ""
