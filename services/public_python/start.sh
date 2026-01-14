#!/bin/bash

# AdSphere Public Service (Python) - Startup Script
# Port 8001

echo "╔════════════════════════════════════════════════════════════╗"
echo "║    AdSphere Public Service (Python) - Port 8001           ║"
echo "╚════════════════════════════════════════════════════════════╝"

cd "$(dirname "$0")"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed"
    exit 1
fi

# Install dependencies if needed
if [ ! -f ".deps_installed" ]; then
    echo "📦 Installing dependencies..."
    pip3 install fastapi uvicorn jinja2 sqlalchemy aiofiles python-multipart -q
    touch .deps_installed
    echo "✅ Dependencies installed"
fi

# Kill existing process on port 8001
echo "🔄 Checking for existing processes on port 8001..."
lsof -ti:8001 | xargs kill -9 2>/dev/null || true

# Start the service
echo "🚀 Starting Public Service on Port 8001..."
echo ""
echo "Access the service at:"
echo "  → Home:     http://localhost:8001/"
echo "  → Browse:   http://localhost:8001/browse"
echo "  → API Docs: http://localhost:8001/docs"
echo ""

python3 app.py

