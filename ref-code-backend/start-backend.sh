#!/bin/bash
# Backend startup script with automatic environment loading
# This ensures consistent backend launches with proper configuration

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting ADK Multi-Agent Backend...${NC}"

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    echo -e "${YELLOW}Warning: .env.local not found. Backend will use default configuration.${NC}"
fi

# Kill any existing uvicorn processes
pkill -f "uvicorn.*server:app" 2>/dev/null || true

# Start the backend
# Note: .env.local is automatically loaded by server.py using python-dotenv
cd "$(dirname "$0")"
python -m uvicorn src.api.server:app --reload --port 8000 2>&1 | tee ../backend.log &

BACKEND_PID=$!
echo -e "${GREEN}✅ Backend started with PID: $BACKEND_PID${NC}"
echo -e "${GREEN}   Server: http://localhost:8000${NC}"
echo -e "${GREEN}   Logs: backend.log${NC}"
echo -e "${GREEN}   Environment: Auto-loaded from .env.local${NC}"
