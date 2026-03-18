#!/bin/bash
# Setup branching strategy for parallel Cascade development
# Run this once to initialize the develop branch and configure git

set -e

echo "🌿 Setting up Git branching strategy for parallel development..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

echo -e "${BLUE}📍 Current branch:${NC}"
git branch --show-current
echo ""

# Create develop branch if it doesn't exist
if git show-ref --verify --quiet refs/heads/develop; then
    echo -e "${GREEN}✅ develop branch already exists${NC}"
else
    echo -e "${YELLOW}Creating develop branch from main...${NC}"
    git checkout main
    git pull origin main
    git checkout -b develop
    git push -u origin develop
    echo -e "${GREEN}✅ Created develop branch${NC}"
fi

echo ""
echo -e "${BLUE}🔧 Configuring git aliases...${NC}"

# Add helpful git aliases
git config --global alias.newfeature '!f() { git checkout develop && git pull && git checkout -b feature/$1; }; f'
git config --global alias.newfix '!f() { git checkout develop && git pull && git checkout -b fix/$1; }; f'
git config --global alias.st 'status -sb'
git config --global alias.branches 'branch -a'
git config --global alias.lg "log --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit"

echo -e "${GREEN}✅ Git aliases configured${NC}"
echo ""
echo "Available aliases:"
echo "  git newfeature <name>  - Create new feature branch"
echo "  git newfix <name>      - Create new fix branch"
echo "  git st                 - Short status"
echo "  git branches           - List all branches"
echo "  git lg                 - Pretty log graph"
echo ""

# Display current branches
echo -e "${BLUE}📋 Current branches:${NC}"
git branch -a
echo ""

echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Review: GIT_BRANCHING_STRATEGY.md"
echo "2. Check: cascade-logs/ACTIVE_BRANCHES.md"
echo "3. Start a new feature:"
echo "   ${BLUE}git newfeature my-awesome-feature${NC}"
echo ""
echo "4. Or create manually:"
echo "   ${BLUE}git checkout develop${NC}"
echo "   ${BLUE}git checkout -b feature/my-awesome-feature${NC}"
echo ""
