#!/usr/bin/env bash
# =============================================================================
# usfs-mirror-setup.sh
# One-time setup: adds the USFS mirror remote and does the initial sync.
# Run this from the USFS Cloud Workstation after cloning the canonical repo.
# =============================================================================
set -euo pipefail

CANONICAL_REPO="https://github.com/xtreamgit/adk-multi-agents-auto.git"
USFS_MIRROR="https://code.fs.usda.gov/Hector-Dejesus/adk-multi-agents-auto-mirror.git"

echo "=== USFS Mirror One-Time Setup ==="
echo ""

# ---- Step 1: Verify we're in the right repo ----
if ! git remote get-url origin &>/dev/null; then
  echo "ERROR: Not inside a git repository."
  echo "Clone the canonical repo first:"
  echo "  gh repo clone xtreamgit/adk-multi-agents-auto"
  exit 1
fi

CURRENT_ORIGIN=$(git remote get-url origin)
if [[ "$CURRENT_ORIGIN" != *"adk-multi-agents-auto"* ]]; then
  echo "ERROR: origin does not look like adk-multi-agents-auto."
  echo "Current origin: $CURRENT_ORIGIN"
  exit 1
fi

echo "✓ Repo verified: $CURRENT_ORIGIN"

# ---- Step 2: Add USFS remote (idempotent, auto-corrects stale URL) ----
if git remote get-url usfs &>/dev/null; then
  CURRENT_USFS_URL=$(git remote get-url usfs)
  if [[ "$CURRENT_USFS_URL" != "$USFS_MIRROR" ]]; then
    echo "⚠  Remote 'usfs' URL is stale: $CURRENT_USFS_URL"
    git remote set-url usfs "$USFS_MIRROR"
    echo "✓ Updated remote 'usfs' → $USFS_MIRROR"
  else
    echo "✓ Remote 'usfs' already exists: $CURRENT_USFS_URL"
  fi
else
  git remote add usfs "$USFS_MIRROR"
  echo "✓ Added remote 'usfs': $USFS_MIRROR"
fi

# ---- Step 3: Fetch latest from canonical ----
echo ""
echo "Fetching latest from canonical repo..."
git checkout main
git pull origin main
git fetch origin --tags
echo "✓ Canonical repo up to date"

# ---- Step 4: Verify USFS auth ----
echo ""
echo "Verifying USFS GitHub Enterprise authentication..."
if ! gh auth status -h code.fs.usda.gov &>/dev/null; then
  echo "WARNING: Not authenticated to code.fs.usda.gov."
  echo "Run: gh auth login -h code.fs.usda.gov"
  echo "Then re-run this script."
  exit 1
fi
echo "✓ Authenticated to code.fs.usda.gov"

# ---- Step 5: Initial push to USFS mirror ----
echo ""
echo "Pushing main branch to USFS mirror..."
git push usfs main
echo "✓ main pushed"

echo ""
echo "Pushing all tags to USFS mirror..."
git push usfs --tags
echo "✓ tags pushed"

# ---- Done ----
echo ""
echo "=== USFS Mirror Setup Complete ==="
echo ""
echo "Remotes:"
git remote -v
echo ""
echo "For ongoing syncs, run: scripts/usfs-sync.sh"
