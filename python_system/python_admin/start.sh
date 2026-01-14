#!/bin/bash
# =============================================================================
# AdSphere Admin Service Startup Script
# Port: 8002
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}       AdSphere Admin Service                     ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check if virtual environment exists
VENV_PATH="../venv"
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv "$VENV_PATH"
fi

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Install dependencies if needed
if [ ! -f "$VENV_PATH/.installed" ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -q fastapi uvicorn sqlalchemy pydantic python-jose passlib python-dotenv python-multipart starlette
    touch "$VENV_PATH/.installed"
fi

# Create required directories
mkdir -p data config companies/logs templates/partials

echo ""
echo -e "${GREEN}Starting Admin Service on port 8002...${NC}"
echo -e "${BLUE}Dashboard: http://localhost:8002${NC}"
echo -e "${BLUE}API Docs:  http://localhost:8002/api/docs${NC}"
echo ""

# Run the application
python app.py

