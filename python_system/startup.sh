#!/bin/bash

# AdSphere Python System Startup Script
# Starts all 3 services in separate processes

echo "╔════════════════════════════════════════════════════════════╗"
echo "║    AdSphere Python System - Multi-Service Startup          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Ask user to choose between bare metal or venv
echo "Choose your environment:"
echo ""
echo "  1. Bare Metal System (Use system Python directly)"
echo "  2. Virtual Environment (Use venv)"
echo ""
read -p "Select option (1 or 2): " env_choice

echo ""

# Handle user choice
if [ "$env_choice" = "1" ]; then
    echo "✅ Running on Bare Metal (system Python)"
    USE_VENV=false
elif [ "$env_choice" = "2" ]; then
    echo "✅ Running with Virtual Environment"
    USE_VENV=true
else
    echo "❌ Invalid choice. Please select 1 or 2."
    exit 1
fi

echo ""

# Handle virtual environment if selected
if [ "$USE_VENV" = true ]; then
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "⚠️  Virtual environment not found. Creating..."
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    else
        echo "✅ Virtual environment found. Activating..."
        source venv/bin/activate
    fi
fi

# Create logs directory if it doesn't exist
if [ ! -d "logs" ]; then
    mkdir -p logs
fi

# Check if database exists
if [ ! -f "python_shared/database/adsphere.db" ]; then
    echo "⚠️  Database not found. Initializing..."
    python database.py
fi

# Kill any existing processes on ports 8001, 8003, 8004
echo "🔄 Cleaning up old processes..."
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
lsof -ti:8003 | xargs kill -9 2>/dev/null || true
lsof -ti:8004 | xargs kill -9 2>/dev/null || true

sleep 1

# Start services in background
echo ""
echo "🚀 Starting AdSphere Services..."
echo ""

# Public Service
echo "📢 Starting Public Service on Port 8001..."
python app.py public > logs/public.log 2>&1 &
PUBLIC_PID=$!
echo "   ✅ PID: $PUBLIC_PID"

sleep 2

# Company Service
echo "🏢 Starting Company Service on Port 8003..."
python app.py company > logs/company.log 2>&1 &
COMPANY_PID=$!
echo "   ✅ PID: $COMPANY_PID"

sleep 2

# Admin Service
echo "👮 Starting Admin Service on Port 8004..."
python app.py admin > logs/admin.log 2>&1 &
ADMIN_PID=$!
echo "   ✅ PID: $ADMIN_PID"

sleep 2

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║             Services Successfully Started!                 ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║  📢 Public Service   : http://localhost:8001/docs          ║"
echo "║  🏢 Company Service  : http://localhost:8003/docs          ║"
echo "║  👮 Admin Service    : http://localhost:8004/docs          ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║  Process IDs (for manual termination):                      ║"
echo "║  - Public:  $PUBLIC_PID                                    ║"
echo "║  - Company: $COMPANY_PID                                    ║"
echo "║  - Admin:   $ADMIN_PID                                      ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║  To stop all services, run: ./stop.sh                      ║"
echo "║  View logs: tail -f logs/public.log                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Press Ctrl+C to stop all services..."
echo ""

# Wait for any process to exit
wait

