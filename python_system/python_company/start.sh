#!/bin/bash

#############################################
# AdSphere Company Portal Startup Script
# Port: 8003
#############################################

echo "🏢 Starting AdSphere Company Portal..."
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check for required packages
echo "📦 Checking dependencies..."
python3 -c "import fastapi, uvicorn, jinja2, sqlalchemy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📥 Installing required packages..."
    pip3 install fastapi uvicorn jinja2 sqlalchemy python-multipart aiofiles bcrypt --quiet
fi

# Create necessary directories
mkdir -p templates metadata data analytics logs

# Start the server
echo ""
echo "🚀 Starting server on http://localhost:8003"
echo "   Press Ctrl+C to stop"
echo ""

python3 -c "
import uvicorn
import sys
sys.path.insert(0, '.')
from app import app
uvicorn.run(app, host='0.0.0.0', port=8003, log_level='info')
"

