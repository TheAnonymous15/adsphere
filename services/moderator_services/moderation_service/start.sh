#!/bin/bash

###############################################
# AdSphere Moderation Service - Startup Script
###############################################

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}  AdSphere Moderation Service - Pre-flight Check${NC}"
echo -e "${BLUE}=================================================${NC}"
echo ""

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
fi

# Check if .env exists
echo -e "${YELLOW}Checking .env file...${NC}"
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ .env file found${NC}"
else
    echo -e "${YELLOW}⚠ .env not found, creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env${NC}"
fi

# Create required directories
echo -e "${YELLOW}Creating required directories...${NC}"
mkdir -p logs/audit
mkdir -p cache
mkdir -p models_weights
echo -e "${GREEN}✓ Directories created${NC}"

# Check if dependencies are installed
echo -e "${YELLOW}Checking dependencies...${NC}"
if python3 -c "import fastapi" 2>/dev/null; then
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠ Installing dependencies...${NC}"
    pip3 install -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
fi

# Syntax check all Python files
echo -e "${YELLOW}Validating Python syntax...${NC}"
SYNTAX_ERRORS=0
while IFS= read -r -d '' file; do
    if ! python3 -m py_compile "$file" 2>/dev/null; then
        echo -e "${RED}✗ Syntax error in: $file${NC}"
        SYNTAX_ERRORS=$((SYNTAX_ERRORS + 1))
    fi
done < <(find app -name "*.py" -print0)

if [ $SYNTAX_ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All Python files valid${NC}"
else
    echo -e "${RED}✗ Found $SYNTAX_ERRORS syntax errors${NC}"
    exit 1
fi

# Check Redis connection (optional)
echo -e "${YELLOW}Checking Redis connection...${NC}"
if python3 -c "
from redis import Redis
import os
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
try:
    r = Redis.from_url(redis_url, socket_connect_timeout=2)
    r.ping()
    print('connected')
except:
    print('not_connected')
" | grep -q "connected"; then
    echo -e "${GREEN}✓ Redis is accessible${NC}"
else
    echo -e "${YELLOW}⚠ Redis not accessible (will use Docker)${NC}"
fi

echo ""
echo -e "${BLUE}=================================================${NC}"
echo -e "${GREEN}✓ Pre-flight check complete!${NC}"
echo -e "${BLUE}=================================================${NC}"
echo ""
echo -e "Select startup mode:"
echo -e "  ${GREEN}1${NC} - Development mode (local, with reload)"
echo -e "  ${GREEN}2${NC} - Docker mode (production-ready)"
echo -e "  ${GREEN}3${NC} - Skip startup (just validate)"
echo ""
read -p "Choose [1-3]: " choice

case $choice in
    1)
        echo -e "${YELLOW}Starting in development mode...${NC}"
        echo -e "${BLUE}API Docs: http://localhost:8002/docs${NC}"
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
        ;;
    2)
        echo -e "${YELLOW}Starting with Docker Compose...${NC}"
        docker-compose up --build
        ;;
    3)
        echo -e "${GREEN}Validation complete. Ready to deploy.${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

