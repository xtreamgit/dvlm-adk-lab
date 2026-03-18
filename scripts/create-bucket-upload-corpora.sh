#!/usr/bin/env bash
# =============================================================================
# Create a GCS bucket and upload PDF corpora data
# =============================================================================
# Usage:
#   ./scripts/create-bucket-upload-corpora.sh \
#       --project PROJECT_ID \
#       --bucket BUCKET_NAME \
#       --data-dir ./data/ \
#       [--region REGION] \
#       [--dry-run]
#
# Example:
#   ./scripts/create-bucket-upload-corpora.sh \
#       --project adk-rag-tt-488718 \
#       --bucket Adk-RAG-Span-corp1 \
#       --data-dir ./data/
# =============================================================================

set -euo pipefail

# ─── Defaults ────────────────────────────────────────────────────────────────
PROJECT=""
BUCKET=""
DATA_DIR=""
REGION="us-west1"
DRY_RUN=false

# ─── Colors ──────────────────────────────────────────────────────────────────
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
CYAN="\033[0;36m"
BOLD="\033[1m"
NC="\033[0m"

log_info()    { echo -e "  ${CYAN}ℹ${NC}  $1"; }
log_success() { echo -e "  ${GREEN}✅${NC} $1"; }
log_warning() { echo -e "  ${YELLOW}⚠️${NC}  $1"; }
log_error()   { echo -e "  ${RED}❌${NC} $1"; }

# ─── Parse Args ──────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --project)  PROJECT="$2";  shift 2 ;;
        --bucket)   BUCKET="$2";   shift 2 ;;
        --data-dir) DATA_DIR="$2"; shift 2 ;;
        --region)   REGION="$2";   shift 2 ;;
        --dry-run)  DRY_RUN=true;  shift ;;
        -h|--help)
            echo "Usage: $0 --project PROJECT_ID --bucket BUCKET_NAME --data-dir DATA_DIR [--region REGION] [--dry-run]"
            exit 0
            ;;
        *) log_error "Unknown arg: $1"; exit 1 ;;
    esac
done

# ─── Validate ────────────────────────────────────────────────────────────────
if [[ -z "$PROJECT" || -z "$BUCKET" || -z "$DATA_DIR" ]]; then
    log_error "Required: --project, --bucket, --data-dir"
    echo "Usage: $0 --project PROJECT_ID --bucket BUCKET_NAME --data-dir DATA_DIR [--region REGION] [--dry-run]"
    exit 1
fi

if [[ ! -d "$DATA_DIR" ]]; then
    log_error "Data directory not found: $DATA_DIR"
    exit 1
fi

# Count PDF files
PDF_COUNT=$(find "$DATA_DIR" -maxdepth 1 -name "*.pdf" -type f | wc -l | tr -d ' ')
if [[ "$PDF_COUNT" -eq 0 ]]; then
    log_error "No PDF files found in $DATA_DIR"
    exit 1
fi

# ─── Summary ─────────────────────────────────────────────────────────────────
BUCKET_URI="gs://${BUCKET}"

echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  GCS Bucket Creation & Corpora Upload${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo ""
log_info "Project:    ${PROJECT}"
log_info "Bucket:     ${BUCKET_URI}"
log_info "Region:     ${REGION}"
log_info "Data dir:   ${DATA_DIR}"
log_info "PDF files:  ${PDF_COUNT}"
if $DRY_RUN; then
    log_warning "DRY RUN — no changes will be made"
fi
echo ""

# ─── Step 1: Create bucket ───────────────────────────────────────────────────
echo -e "${CYAN}${BOLD}── Step 1: Create GCS Bucket ──${NC}"

if gsutil ls -p "$PROJECT" "$BUCKET_URI" &>/dev/null; then
    log_warning "Bucket already exists: ${BUCKET_URI}"
else
    if $DRY_RUN; then
        log_info "[DRY RUN] Would create: ${BUCKET_URI}"
    else
        gsutil mb -p "$PROJECT" -l "$REGION" -b on "$BUCKET_URI"
        log_success "Created bucket: ${BUCKET_URI}"
    fi
fi

# ─── Step 2: Upload PDF files ────────────────────────────────────────────────
echo ""
echo -e "${CYAN}${BOLD}── Step 2: Upload PDF Corpora Data ──${NC}"

UPLOADED=0
SKIPPED=0

for pdf in "$DATA_DIR"/*.pdf; do
    filename=$(basename "$pdf")
    dest="${BUCKET_URI}/${filename}"

    if $DRY_RUN; then
        log_info "[DRY RUN] Would upload: ${filename}"
        ((UPLOADED++))
    else
        # Check if file already exists in bucket
        if gsutil -q stat "$dest" 2>/dev/null; then
            log_info "Already exists, skipping: ${filename}"
            ((SKIPPED++))
        else
            gsutil cp "$pdf" "$dest"
            log_success "Uploaded: ${filename}"
            ((UPLOADED++))
        fi
    fi
done

# ─── Summary ─────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  Complete${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo ""
log_info "Uploaded: ${UPLOADED}"
log_info "Skipped:  ${SKIPPED}"
log_info "Bucket:   ${BUCKET_URI}"
echo ""

if ! $DRY_RUN; then
    echo -e "${CYAN}${BOLD}── Bucket Contents ──${NC}"
    gsutil ls -l "$BUCKET_URI" | tail -5
    echo "  ..."
    TOTAL=$(gsutil ls "$BUCKET_URI" | wc -l | tr -d ' ')
    log_info "Total objects in bucket: ${TOTAL}"
fi

echo ""
log_success "Done!"
