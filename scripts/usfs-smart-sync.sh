#!/usr/bin/env bash
# =============================================================================
# usfs-smart-sync.sh
# Bi-directional sync between canonical repo (github.com) and USFS mirror
# (code.fs.usda.gov) with status table, safety checks, and auto-detection.
#
# Usage:
#   bash scripts/usfs-smart-sync.sh [OPTIONS]
#
# Options:
#   --status      Show status table only (no changes)
#   --dry-run     Show what would happen without making changes
#   --reverse     Sync USFS mirror → canonical (for hotfixes)
#   --skip-auth   Skip authentication checks
#   --force       Force sync even if branches are divergent (dangerous)
#   --help        Show this help message
#
# Run from: Mac or USFS Cloud Workstation (auto-detects environment)
# =============================================================================
set -euo pipefail

# ---- Constants ----
CANONICAL_REPO="https://github.com/xtreamgit/adk-multi-agents-auto.git"
USFS_MIRROR="https://code.fs.usda.gov/Hector-Dejesus/adk-multi-agents-auto-mirror.git"

# USFS Workstation paths (two-clone model)
# Sync clone: used by this script to sync between canonical and mirror
USFS_SYNC_CLONE="$HOME/github.com/Hector-Dejesus/adk-multi-agents-auto-mirror"
# Deploy clone: used for deploying to GCP (checkout release tags here)
USFS_DEPLOY_CLONE="$HOME/github.com/Hector-Dejesus/usfs-deploy/adk-multi-agents-auto-mirror"

# Mac paths (canonical repo location)
MAC_CANONICAL_CLONE="$HOME/github.com/xtreamgit/adk-multi-agents-auto"

# Remote name mapping (set by detect_environment)
# Mac:  CANONICAL_REMOTE=origin,    MIRROR_REMOTE=usfs
# USFS: CANONICAL_REMOTE=canonical, MIRROR_REMOTE=origin
CANONICAL_REMOTE=""
MIRROR_REMOTE=""

# ---- Colors ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ---- Logging ----
log_info()    { echo -e "${BLUE}[INFO]${NC}    $*"; }
log_success() { echo -e "${GREEN}[OK]${NC}      $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}    $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC}   $*"; }
log_section() { echo -e "\n${BOLD}${CYAN}=== $* ===${NC}"; }

# ---- Flags ----
STATUS_ONLY=false
DRY_RUN=false
REVERSE=false
SKIP_AUTH=false
FORCE=false

# ---- Parse arguments ----
while [[ $# -gt 0 ]]; do
    case "$1" in
        --status)    STATUS_ONLY=true; shift ;;
        --dry-run)   DRY_RUN=true; shift ;;
        --reverse)   REVERSE=true; shift ;;
        --skip-auth) SKIP_AUTH=true; shift ;;
        --force)     FORCE=true; shift ;;
        --help|-h)
            head -25 "$0" | tail -20
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help to see available options."
            exit 1
            ;;
    esac
done

# ---- Environment Detection ----
detect_environment() {
    if [[ -d "$USFS_SYNC_CLONE/.git" ]]; then
        ENVIRONMENT="usfs"
        WORKING_CLONE="$USFS_SYNC_CLONE"
        log_info "Detected environment: USFS Cloud Workstation"
        log_info "Sync clone: $WORKING_CLONE"
        
        # Detect which remote points to code.fs.usda.gov (the mirror)
        MIRROR_REMOTE=""
        while IFS= read -r remote_name; do
            remote_url=$(git -C "$WORKING_CLONE" remote get-url "$remote_name" 2>/dev/null)
            if [[ "$remote_url" == *"code.fs.usda.gov"* ]]; then
                MIRROR_REMOTE="$remote_name"
                break
            fi
        done < <(git -C "$WORKING_CLONE" remote)
        
        if [[ -z "$MIRROR_REMOTE" ]]; then
            log_warn "No remote pointing to code.fs.usda.gov found. Defaulting to 'usfs'."
            MIRROR_REMOTE="usfs"
        fi
        log_info "Mirror remote: $MIRROR_REMOTE → $(git -C "$WORKING_CLONE" remote get-url "$MIRROR_REMOTE" 2>/dev/null)"
        
        # Detect which remote points to github.com (canonical)
        CANONICAL_REMOTE=""
        while IFS= read -r remote_name; do
            remote_url=$(git -C "$WORKING_CLONE" remote get-url "$remote_name" 2>/dev/null)
            if [[ "$remote_url" == *"github.com"* ]]; then
                CANONICAL_REMOTE="$remote_name"
                break
            fi
        done < <(git -C "$WORKING_CLONE" remote)
        
        # Ensure a canonical remote exists (points to github.com)
        if [[ -z "$CANONICAL_REMOTE" ]]; then
            log_info "Adding 'canonical' remote → $CANONICAL_REPO"
            git -C "$WORKING_CLONE" remote add canonical "$CANONICAL_REPO"
            CANONICAL_REMOTE="canonical"
        fi
        log_info "Canonical remote: $CANONICAL_REMOTE → $(git -C "$WORKING_CLONE" remote get-url "$CANONICAL_REMOTE" 2>/dev/null)"
        
        # Check deploy clone
        if [[ -d "$USFS_DEPLOY_CLONE/.git" ]]; then
            log_info "Deploy clone: $USFS_DEPLOY_CLONE"
        else
            log_warn "Deploy clone not found at: $USFS_DEPLOY_CLONE"
            log_warn "To set up: git clone $USFS_MIRROR $USFS_DEPLOY_CLONE"
        fi
    elif [[ -d "$MAC_CANONICAL_CLONE/.git" ]]; then
        ENVIRONMENT="mac"
        WORKING_CLONE="$MAC_CANONICAL_CLONE"
        CANONICAL_REMOTE="origin"
        MIRROR_REMOTE="usfs"
        log_info "Detected environment: Mac (canonical repo)"
    else
        log_error "Cannot detect environment."
        log_error "Expected clone at one of:"
        log_error "  - $USFS_SYNC_CLONE (USFS Workstation)"
        log_error "  - $MAC_CANONICAL_CLONE (Mac)"
        exit 1
    fi
}

# ---- Authentication Check ----
check_auth() {
    if [[ "$SKIP_AUTH" == "true" ]]; then
        log_info "Skipping authentication checks (--skip-auth)"
        return 0
    fi

    log_section "Checking Authentication"

    # Check github.com
    if gh auth status -h github.com &>/dev/null; then
        log_success "Authenticated to github.com"
    else
        log_error "Not authenticated to github.com"
        log_error "Run: gh auth login -h github.com"
        exit 1
    fi

    # Check code.fs.usda.gov (only on USFS workstation or if usfs remote exists)
    if [[ "$ENVIRONMENT" == "usfs" ]] || git remote get-url usfs &>/dev/null 2>&1; then
        if gh auth status -h code.fs.usda.gov &>/dev/null; then
            log_success "Authenticated to code.fs.usda.gov"
        else
            log_warn "Not authenticated to code.fs.usda.gov"
            log_warn "Run: gh auth login -h code.fs.usda.gov"
            if [[ "$ENVIRONMENT" == "usfs" ]]; then
                exit 1
            fi
        fi
    fi
}

# ---- Global state for USFS reachability ----
USFS_REMOTE_EXISTS=false
USFS_REACHABLE=false

# ---- Fetch All Remotes ----
fetch_remotes() {
    log_section "Fetching Remotes"
    
    cd "$WORKING_CLONE"
    
    # Fetch canonical (github.com)
    log_info "Fetching $CANONICAL_REMOTE (canonical — github.com)..."
    if git fetch "$CANONICAL_REMOTE" --tags --quiet 2>/dev/null; then
        log_success "Fetched $CANONICAL_REMOTE"
    else
        log_error "Could not fetch from $CANONICAL_REMOTE ($CANONICAL_REPO)"
        exit 1
    fi
    
    # Fetch mirror (code.fs.usda.gov)
    if git remote get-url "$MIRROR_REMOTE" &>/dev/null; then
        USFS_REMOTE_EXISTS=true
        log_info "Fetching $MIRROR_REMOTE (mirror — code.fs.usda.gov)..."
        if git fetch "$MIRROR_REMOTE" --tags --quiet 2>/dev/null; then
            USFS_REACHABLE=true
            log_success "Fetched $MIRROR_REMOTE"
        else
            USFS_REACHABLE=false
            log_warn "Could not reach USFS mirror (code.fs.usda.gov is USFS network only)"
        fi
    else
        USFS_REMOTE_EXISTS=false
        if [[ "$ENVIRONMENT" == "mac" ]]; then
            log_warn "Remote '$MIRROR_REMOTE' not configured. Run scripts/usfs-mirror-setup.sh first."
        else
            log_error "Mirror remote '$MIRROR_REMOTE' not found. Clone may be misconfigured."
            exit 1
        fi
    fi
}

# ---- Get Commit Info ----
get_commit_sha() {
    local ref="$1"
    git rev-parse --short "$ref" 2>/dev/null || echo "N/A"
}

get_commit_date() {
    local ref="$1"
    git log -1 --format="%ci" "$ref" 2>/dev/null | cut -d' ' -f1 || echo "N/A"
}

get_branch_or_tag() {
    local ref="$1"
    git describe --tags --exact-match "$ref" 2>/dev/null || \
        git symbolic-ref --short "$ref" 2>/dev/null || \
        echo "detached"
}

# ---- Compare Commits ----
compare_commits() {
    cd "$WORKING_CLONE"
    
    CANONICAL_SHA=$(get_commit_sha "$CANONICAL_REMOTE/main")
    LOCAL_SHA=$(get_commit_sha "HEAD")
    
    if [[ "$USFS_REACHABLE" == "true" ]]; then
        MIRROR_SHA=$(get_commit_sha "$MIRROR_REMOTE/main" 2>/dev/null || echo "N/A")
    elif [[ "$USFS_REMOTE_EXISTS" == "true" ]]; then
        MIRROR_SHA="UNREACHABLE"
    else
        MIRROR_SHA="N/A"
    fi
    
    # Deploy clone info (USFS only)
    DEPLOY_SHA="N/A"
    DEPLOY_REF="N/A"
    if [[ "$ENVIRONMENT" == "usfs" ]] && [[ -d "$USFS_DEPLOY_CLONE/.git" ]]; then
        DEPLOY_SHA=$(cd "$USFS_DEPLOY_CLONE" && get_commit_sha "HEAD")
        DEPLOY_REF=$(cd "$USFS_DEPLOY_CLONE" && get_branch_or_tag "HEAD")
    fi
}

# ---- Determine Sync State ----
determine_state() {
    cd "$WORKING_CLONE"
    
    if [[ "$MIRROR_SHA" == "N/A" ]]; then
        SYNC_STATE="NO_MIRROR"
        return
    fi
    
    if [[ "$MIRROR_SHA" == "UNREACHABLE" ]]; then
        SYNC_STATE="UNREACHABLE"
        return
    fi
    
    if [[ "$CANONICAL_SHA" == "$MIRROR_SHA" ]]; then
        SYNC_STATE="IN_SYNC"
    elif git merge-base --is-ancestor "$MIRROR_REMOTE/main" "$CANONICAL_REMOTE/main" 2>/dev/null; then
        SYNC_STATE="CANONICAL_AHEAD"
        COMMITS_AHEAD=$(git rev-list --count "$MIRROR_REMOTE/main".."$CANONICAL_REMOTE/main")
    elif git merge-base --is-ancestor "$CANONICAL_REMOTE/main" "$MIRROR_REMOTE/main" 2>/dev/null; then
        SYNC_STATE="MIRROR_AHEAD"
        COMMITS_AHEAD=$(git rev-list --count "$CANONICAL_REMOTE/main".."$MIRROR_REMOTE/main")
    else
        SYNC_STATE="DIVERGENT"
    fi
}

# ---- Display Status Table ----
display_status_table() {
    log_section "Sync Status"
    
    # Get short paths for display (truncate if too long)
    local sync_short="${WORKING_CLONE/#$HOME/~}"
    if [[ ${#sync_short} -gt 43 ]]; then
        sync_short="...${sync_short: -40}"
    fi
    local deploy_short="${USFS_DEPLOY_CLONE/#$HOME/~}"
    if [[ ${#deploy_short} -gt 43 ]]; then
        deploy_short="...${deploy_short: -40}"
    fi
    
    echo ""
    echo "╔════════════════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                    USFS SYNC STATUS                                        ║"
    echo "╠════════════════════════════════════════════════════╦══════════╦══════════╦═════════════════╣"
    echo "║ Repository                                         ║ Branch   ║ Commit   ║ Status          ║"
    echo "╠════════════════════════════════════════════════════╬══════════╬══════════╬═════════════════╣"
    
    # Canonical (GitHub)
    printf "║ %-50s ║ %-8s ║ %-8s ║ " "Canonical (github.com)" "main" "$CANONICAL_SHA"
    echo -e "${GREEN}✓ Source${NC}         ║"
    
    # USFS Mirror
    if [[ "$ENVIRONMENT" == "usfs" ]]; then
        printf "║ %-50s ║ %-8s ║ %-8s ║ " "USFS Mirror (code.fs.usda.gov)" "main" "$MIRROR_SHA"
    else
        printf "║ %-50s ║ %-8s ║ %-8s ║ " "USFS Mirror (USFS network only)" "main" "$MIRROR_SHA"
    fi
    case "$SYNC_STATE" in
        IN_SYNC)         echo -e "${GREEN}✓ In sync${NC}        ║" ;;
        CANONICAL_AHEAD) echo -e "${YELLOW}⚠ Behind ($COMMITS_AHEAD)${NC}       ║" ;;
        MIRROR_AHEAD)    echo -e "${CYAN}↑ Ahead ($COMMITS_AHEAD)${NC}        ║" ;;
        DIVERGENT)       echo -e "${RED}✗ Divergent${NC}      ║" ;;
        NO_MIRROR)       echo -e "${YELLOW}⚠ Not configured${NC} ║" ;;
        UNREACHABLE)     echo -e "${YELLOW}⚠ Not reachable${NC}  ║" ;;
    esac
    
    # Sync Clone with path
    printf "║ %-50s ║ %-8s ║ %-8s ║ " "Sync: $sync_short" "$(git branch --show-current)" "$LOCAL_SHA"
    if [[ "$LOCAL_SHA" == "$CANONICAL_SHA" ]]; then
        echo -e "${GREEN}✓ Up to date${NC}     ║"
    else
        echo -e "${YELLOW}⚠ Needs pull${NC}     ║"
    fi
    
    # Deploy Clone (USFS only)
    if [[ "$ENVIRONMENT" == "usfs" ]]; then
        printf "║ %-50s ║ %-8s ║ %-8s ║ " "Deploy: $deploy_short" "$DEPLOY_REF" "$DEPLOY_SHA"
        if [[ "$DEPLOY_SHA" == "N/A" ]]; then
            echo -e "${YELLOW}⚠ Not set up${NC}     ║"
        elif [[ "$DEPLOY_SHA" == "$CANONICAL_SHA" ]]; then
            echo -e "${GREEN}✓ Latest${NC}         ║"
        else
            echo -e "${YELLOW}⚠ Needs update${NC}   ║"
        fi
    fi
    
    echo "╠════════════════════════════════════════════════════╩══════════╩══════════╩═════════════════╣"
    
    # Environment info
    printf "║ Environment: %-80s ║\n" "$ENVIRONMENT"
    
    # Next step hint based on state
    echo "╠════════════════════════════════════════════════════════════════════════════════════════════╣"
    case "$SYNC_STATE" in
        IN_SYNC)
            if [[ "$ENVIRONMENT" == "usfs" ]] && [[ "$DEPLOY_SHA" != "$CANONICAL_SHA" ]]; then
                echo -e "║ ${YELLOW}Next:${NC} Update deploy clone: cd $deploy_short && git pull                              ║"
            else
                echo -e "║ ${GREEN}✓ All synced!${NC} To deploy USFS: cd deploy clone → bash scripts/deploy-env.sh usfs       ║"
            fi
            ;;
        CANONICAL_AHEAD)
            if [[ "$ENVIRONMENT" == "usfs" ]]; then
                echo -e "║ ${YELLOW}Next:${NC} Run this script without --status to sync canonical → mirror                     ║"
            else
                echo -e "║ ${YELLOW}Next:${NC} Run this script from USFS workstation to sync canonical → mirror                ║"
            fi
            ;;
        MIRROR_AHEAD)
            echo -e "║ ${CYAN}Next:${NC} Run with --reverse to push USFS hotfix back to canonical                          ║"
            ;;
        DIVERGENT)
            echo -e "║ ${RED}Action required:${NC} Branches diverged. Investigate or use --force (destructive)            ║"
            ;;
        NO_MIRROR)
            echo -e "║ ${YELLOW}Next:${NC} Run scripts/usfs-mirror-setup.sh to configure the usfs remote                    ║"
            ;;
        UNREACHABLE)
            echo -e "║ ${YELLOW}Next:${NC} Run this script from USFS Cloud Workstation (inside USFS network)                ║"
            ;;
    esac
    
    echo "╚════════════════════════════════════════════════════════════════════════════════════════════╝"
    echo ""
}

# ---- Sync Canonical → Mirror ----
sync_canonical_to_mirror() {
    log_section "Syncing Canonical → USFS Mirror"
    
    cd "$WORKING_CLONE"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would pull from $CANONICAL_REMOTE (github.com)"
        log_info "[DRY-RUN] Would push main to $MIRROR_REMOTE (code.fs.usda.gov)"
        log_info "[DRY-RUN] Would push tags to $MIRROR_REMOTE"
        if [[ "$ENVIRONMENT" == "usfs" ]] && [[ -d "$USFS_DEPLOY_CLONE/.git" ]]; then
            log_info "[DRY-RUN] Would update deploy clone at $USFS_DEPLOY_CLONE"
        fi
        return
    fi
    
    # Pull latest from canonical (github.com)
    log_info "Pulling latest from $CANONICAL_REMOTE (github.com)..."
    git checkout main --quiet
    git pull "$CANONICAL_REMOTE" main --ff-only --quiet
    log_success "Local main updated from canonical"
    
    # Push to mirror (code.fs.usda.gov)
    log_info "Pushing main to $MIRROR_REMOTE (code.fs.usda.gov)..."
    git push "$MIRROR_REMOTE" main --force-with-lease
    log_success "main pushed to mirror"
    
    log_info "Pushing tags to $MIRROR_REMOTE..."
    git push "$MIRROR_REMOTE" --tags
    log_success "Tags pushed to mirror"
    
    # Update deploy clone if on USFS
    if [[ "$ENVIRONMENT" == "usfs" ]] && [[ -d "$USFS_DEPLOY_CLONE/.git" ]]; then
        log_info "Updating deploy clone..."
        cd "$USFS_DEPLOY_CLONE"
        git fetch origin --tags --quiet
        git checkout main --quiet 2>/dev/null || true
        git pull origin main --ff-only --quiet 2>/dev/null || log_warn "Deploy clone may need manual update"
        log_success "Deploy clone updated"
        cd "$WORKING_CLONE"
    fi
}

# ---- Sync Mirror → Canonical ----
sync_mirror_to_canonical() {
    log_section "Syncing USFS Mirror → Canonical (Reverse)"
    
    cd "$WORKING_CLONE"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would pull from $MIRROR_REMOTE/main"
        log_info "[DRY-RUN] Would push to $CANONICAL_REMOTE main"
        return
    fi
    
    # Confirmation for reverse sync
    echo ""
    log_warn "You are about to push USFS mirror changes to canonical (github.com)."
    log_warn "This should only be done for hotfixes made directly on USFS."
    read -rp "Are you sure you want to continue? (y/N): " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        log_info "Aborted by user."
        exit 0
    fi
    
    # Merge mirror/main into local main
    log_info "Merging $MIRROR_REMOTE/main into local main..."
    git checkout main --quiet
    git merge "$MIRROR_REMOTE/main" --ff-only
    log_success "Merged $MIRROR_REMOTE/main"
    
    # Push to canonical
    log_info "Pushing to $CANONICAL_REMOTE (github.com)..."
    git push "$CANONICAL_REMOTE" main
    log_success "Pushed to canonical"
    
    log_info "Pushing tags to $CANONICAL_REMOTE..."
    git push "$CANONICAL_REMOTE" --tags
    log_success "Tags pushed to canonical"
}

# ---- Main ----
main() {
    echo ""
    echo -e "${BOLD}${BLUE}╔═══════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${BLUE}║       USFS Smart Sync Tool            ║${NC}"
    echo -e "${BOLD}${BLUE}╚═══════════════════════════════════════╝${NC}"
    echo ""
    
    # Detect environment
    detect_environment
    
    # Check auth
    check_auth
    
    # Fetch remotes
    fetch_remotes
    
    # Compare commits
    compare_commits
    
    # Determine sync state
    determine_state
    
    # Display status table
    display_status_table
    
    # If status only, exit here
    if [[ "$STATUS_ONLY" == "true" ]]; then
        exit 0
    fi
    
    # Handle sync based on state
    case "$SYNC_STATE" in
        IN_SYNC)
            log_success "Branches are in sync."
            # Still push any tags that exist on canonical but not on mirror
            if [[ "$USFS_REACHABLE" == "true" ]]; then
                cd "$WORKING_CLONE"
                MISSING_TAGS=$(git tag --list | while read -r tag; do
                    git rev-parse "refs/tags/$tag" &>/dev/null || continue
                    git ls-remote "$MIRROR_REMOTE" "refs/tags/$tag" | grep -q . || echo "$tag"
                done)
                if [[ -n "$MISSING_TAGS" ]]; then
                    log_info "Pushing missing tags to mirror..."
                    git push "$MIRROR_REMOTE" --tags
                    log_success "Tags pushed to mirror"
                else
                    log_success "Tags already in sync. No action needed."
                fi
                # Update deploy clone if on USFS
                if [[ "$ENVIRONMENT" == "usfs" ]] && [[ -d "$USFS_DEPLOY_CLONE/.git" ]]; then
                    log_info "Updating deploy clone..."
                    cd "$USFS_DEPLOY_CLONE"
                    git fetch origin --tags --quiet
                    git checkout main --quiet 2>/dev/null || true
                    git pull origin main --ff-only --quiet 2>/dev/null || log_warn "Deploy clone may need manual update"
                    log_success "Deploy clone updated"
                fi
            fi
            ;;
        
        CANONICAL_AHEAD)
            if [[ "$REVERSE" == "true" ]]; then
                log_warn "Canonical is ahead of mirror. --reverse has no effect."
            else
                sync_canonical_to_mirror
            fi
            ;;
        
        MIRROR_AHEAD)
            if [[ "$REVERSE" == "true" ]]; then
                sync_mirror_to_canonical
            else
                log_warn "USFS mirror is ahead of canonical by $COMMITS_AHEAD commit(s)."
                log_warn "This usually means a hotfix was made on USFS."
                log_info "To push these changes to canonical, run:"
                echo ""
                echo "    bash scripts/usfs-smart-sync.sh --reverse"
                echo ""
            fi
            ;;
        
        DIVERGENT)
            log_error "Branches have diverged! Manual intervention required."
            log_error "This means both repos have different commits not in the other."
            echo ""
            log_info "To investigate, run:"
            echo "    git log --oneline $CANONICAL_REMOTE/main..$MIRROR_REMOTE/main  # Commits only in mirror"
            echo "    git log --oneline $MIRROR_REMOTE/main..$CANONICAL_REMOTE/main  # Commits only in canonical"
            echo ""
            if [[ "$FORCE" == "true" ]]; then
                log_warn "Force flag detected. Forcing canonical → mirror..."
                git push "$MIRROR_REMOTE" main --force
                log_success "Forced push complete (mirror overwritten)"
            else
                log_info "Use --force to overwrite mirror with canonical (destructive)"
            fi
            ;;
        
        NO_MIRROR)
            log_error "USFS mirror remote not configured."
            log_info "Run: bash scripts/usfs-mirror-setup.sh"
            exit 1
            ;;
        
        UNREACHABLE)
            log_warn "USFS mirror is not reachable from this location."
            log_info "code.fs.usda.gov is only accessible from the USFS network."
            log_info "To sync, run this script from the USFS Cloud Workstation."
            ;;
    esac
    
    echo ""
    log_success "Done!"
}

main "$@"
