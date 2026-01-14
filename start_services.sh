#!/bin/bash
# =============================================================================
# AdSphere Microservices Startup Script
# =============================================================================
#
# Starts all 3 PHP services on different ports:
#   - Public:  localhost:8001 (browse ads)
#   - Admin:   localhost:8002 (platform admin)
#   - Company: localhost:8003 (company portal)
#
# Usage:
#   ./start_services.sh         # Start all services
#   ./start_services.sh stop    # Stop all services
#   ./start_services.sh status  # Check status
#   ./start_services.sh public  # Start only public
#   ./start_services.sh admin   # Start only admin
#   ./start_services.sh company # Start only company
#
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# PID files
PID_DIR="$SCRIPT_DIR/.pids"
mkdir -p "$PID_DIR"

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║              AdSphere Microservices Manager                       ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

start_service() {
    local name=$1
    local port=$2
    local dir=$3

    if [ -f "$PID_DIR/$name.pid" ]; then
        local pid=$(cat "$PID_DIR/$name.pid")
        if kill -0 $pid 2>/dev/null; then
            echo -e "${YELLOW}⚠️  $name already running on port $port (PID: $pid)${NC}"
            return
        fi
    fi

    echo -e "${BLUE}🚀 Starting $name on port $port...${NC}"

    # Handle moderator service differently (Python/FastAPI)
    if [ "$name" = "moderator" ]; then
        # Check if Python and uvicorn are available
        if command -v python3 &> /dev/null; then
            cd "$SCRIPT_DIR/services/moderator_services/moderation_service"
            python3 -m uvicorn app.main:app --host 0.0.0.0 --port $port > "$PID_DIR/$name.log" 2>&1 &
            local pid=$!
            cd "$SCRIPT_DIR"
        else
            echo -e "${YELLOW}⚠️  Python3 not found, skipping moderator service${NC}"
            return
        fi
    else
        # PHP services
        php -c "$SCRIPT_DIR/services/php.ini" -S localhost:$port -t "$SCRIPT_DIR/services/$dir" "$SCRIPT_DIR/services/$dir/index.php" > "$PID_DIR/$name.log" 2>&1 &
        local pid=$!
    fi

    echo $pid > "$PID_DIR/$name.pid"
    sleep 1

    if kill -0 $pid 2>/dev/null; then
        echo -e "${GREEN}✅ $name started on http://localhost:$port (PID: $pid)${NC}"
    else
        echo -e "${RED}❌ Failed to start $name${NC}"
        cat "$PID_DIR/$name.log"
    fi
}

stop_service() {
    local name=$1
    local port=$2

    if [ -f "$PID_DIR/$name.pid" ]; then
        local pid=$(cat "$PID_DIR/$name.pid")
        if kill -0 $pid 2>/dev/null; then
            echo -e "${YELLOW}🛑 Stopping $name (PID: $pid)...${NC}"
            kill $pid 2>/dev/null
            rm -f "$PID_DIR/$name.pid"
            echo -e "${GREEN}✅ $name stopped${NC}"
        else
            rm -f "$PID_DIR/$name.pid"
            echo -e "${YELLOW}⚠️  $name was not running${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  $name is not running${NC}"
    fi
}

check_status() {
    echo ""
    echo -e "${BLUE}Service Status:${NC}"
    echo "─────────────────────────────────────────"

    for service in public admin company moderator; do
        if [ -f "$PID_DIR/$service.pid" ]; then
            local pid=$(cat "$PID_DIR/$service.pid")
            if kill -0 $pid 2>/dev/null; then
                local port=""
                case $service in
                    public) port=8001 ;;
                    admin) port=8002 ;;
                    company) port=8003 ;;
                    moderator) port=8004 ;;
                esac
                echo -e "${GREEN}✅ $service: Running on port $port (PID: $pid)${NC}"
            else
                echo -e "${RED}❌ $service: Not running (stale PID file)${NC}"
            fi
        else
            echo -e "${YELLOW}⚪ $service: Not running${NC}"
        fi
    done
    echo ""
}

start_all() {
    echo ""
    start_service "public" 8001 "public"
    start_service "admin" 8002 "admin"
    start_service "company" 8003 "company"
    start_service "moderator" 8004 "moderator_services"
    echo ""
    echo -e "${GREEN}All services started!${NC}"
    echo ""
    echo "Access URLs:"
    echo "  📢 Public:   http://localhost:8001"
    echo "  🔴 Admin:    http://localhost:8002"
    echo "  🔵 Company:  http://localhost:8003"
    echo "  🤖 Moderator: http://localhost:8004"
    echo ""
}

stop_all() {
    echo ""
    stop_service "public" 8001
    stop_service "admin" 8002
    stop_service "company" 8003
    stop_service "moderator" 8004
    echo ""
}

case "${1:-start}" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    restart)
        stop_all
        sleep 1
        start_all
        ;;
    status)
        check_status
        ;;
    public)
        start_service "public" 8001 "public"
        ;;
    admin)
        start_service "admin" 8002 "admin"
        ;;
    company)
        start_service "company" 8003 "company"
        ;;
    moderator)
        start_service "moderator" 8004 "moderator_services"
        ;;
    logs)
        service=${2:-public}
        if [ -f "$PID_DIR/$service.log" ]; then
            tail -f "$PID_DIR/$service.log"
        else
            echo "No logs found for $service"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|public|admin|company|moderator|logs [service]}"
        exit 1
        ;;
esac

