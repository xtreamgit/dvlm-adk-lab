#!/usr/bin/env bash
# =============================================================================
# usfs-sync.sh
# Syncs the canonical repo (github.com) to the USFS mirror (code.fs.usda.gov).
# Run from the canonical clone on the USFS Cloud Workstation after each
# usfs-vX.Y.Z tag is created on the canonical repo.
# =============================================================================
set -euo pipefail

USFS_MIRROR="https://code.fs.usda.gov/Hector-Dejesus/adk-multi-agents-auto-mirror.git"

echo "=== USFS Mirror Sync ==="
echo ""

# ---- Verify we're in the right repo ----
if ! git remote get-url origin &>/dev/null; then
  echo "ERROR: Not inside a git repository."
  exit 1
fi

# ---- Verify usfs remote exists ----
if ! git remote get-url usfs &>/dev/null; then
  echo "ERROR: Remote 'usfs' not found. Run scripts/usfs-mirror-setup.sh first."
  exit 1
fi

echo "Canonical: $(git remote get-url origin)"
echo "USFS:      $(git remote get-url usfs)"
echo ""

# ---- Fetch latest from canonical ----
echo "Fetching from canonical repo..."
git checkout main
git pull origin main --ff-only
git fetch origin --tags
echo "✓ Local repo up to date with canonical"

# ---- Push to USFS mirror ----
echo ""
echo "Syncing main branch to USFS mirror..."
git push usfs main --force-with-lease
echo "✓ main synced"

echo ""
echo "Syncing tags to USFS mirror..."
git push usfs --tags
echo "✓ tags synced"

# ---- Summary ----
echo ""
echo "=== Sync Complete ==="
LATEST_USFS_TAG=$(git tag -l "usfs-*" | sort -V | tail -1)
echo "Latest USFS release tag: ${LATEST_USFS_TAG:-none}"
echo ""
echo "To deploy from USFS mirror, see: docs/USFS_WORKSTATION_DEPLOY.md"
