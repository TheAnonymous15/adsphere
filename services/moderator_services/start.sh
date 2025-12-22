#!/bin/bash
# =============================================================================
# AdSphere Moderation Service - Quick Start Script
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║          AdSphere Moderation Service - Quick Start               ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Function to use docker compose (v2) or docker-compose (v1)
docker_compose() {
    if docker compose version &> /dev/null; then
        docker compose "$@"
    else
        docker-compose "$@"
    fi
}

# Parse arguments
MODE=${1:-"start"}
SCALE_API=${2:-4}
PROFILE=""

case "$MODE" in
    start)
        echo -e "${GREEN}🚀 Starting Moderation Service (${SCALE_API} API instances)...${NC}"
        docker_compose -f docker-compose.prod.yml up -d --scale moderation-api=$SCALE_API
        ;;

    start-dev)
        echo -e "${GREEN}🚀 Starting Moderation Service in DEV mode...${NC}"
        docker_compose -f docker-compose.prod.yml --profile dev up -d --scale moderation-api=2
        ;;

    start-monitoring)
        echo -e "${GREEN}🚀 Starting with Prometheus + Grafana monitoring...${NC}"
        docker_compose -f docker-compose.prod.yml --profile monitoring up -d --scale moderation-api=$SCALE_API
        ;;

    stop)
        echo -e "${YELLOW}🛑 Stopping Moderation Service...${NC}"
        docker_compose -f docker-compose.prod.yml down
        ;;

    restart)
        echo -e "${YELLOW}🔄 Restarting Moderation Service...${NC}"
        docker_compose -f docker-compose.prod.yml down
        docker_compose -f docker-compose.prod.yml up -d --scale moderation-api=$SCALE_API
        ;;

    scale)
        SCALE_API=${2:-4}
        SCALE_SCANNER=${3:-2}
        SCALE_VIDEO=${4:-2}
        echo -e "${GREEN}📈 Scaling services: API=${SCALE_API}, Scanner=${SCALE_SCANNER}, Video=${SCALE_VIDEO}${NC}"
        docker_compose -f docker-compose.prod.yml up -d \
            --scale moderation-api=$SCALE_API \
            --scale scanner-worker=$SCALE_SCANNER \
            --scale video-worker=$SCALE_VIDEO
        ;;

    logs)
        SERVICE=${2:-"moderation-api"}
        echo -e "${BLUE}📋 Showing logs for ${SERVICE}...${NC}"
        docker_compose -f docker-compose.prod.yml logs -f $SERVICE
        ;;

    status)
        echo -e "${BLUE}📊 Service Status:${NC}"
        docker_compose -f docker-compose.prod.yml ps
        echo ""
        echo -e "${BLUE}📊 Health Check:${NC}"
        curl -s http://localhost:8002/health | python3 -m json.tool 2>/dev/null || echo "Service not responding"
        ;;

    health)
        echo -e "${BLUE}🏥 Health Check:${NC}"
        echo ""
        echo "API Health:"
        curl -s http://localhost:8002/health | python3 -m json.tool 2>/dev/null || echo "❌ API not responding"
        echo ""
        echo "Redis:"
        docker_compose -f docker-compose.prod.yml exec -T redis redis-cli ping 2>/dev/null || echo "❌ Redis not responding"
        echo ""
        echo "Metrics:"
        curl -s http://localhost:8002/metrics | head -20 2>/dev/null || echo "❌ Metrics not available"
        ;;

    build)
        echo -e "${GREEN}🔨 Building Docker images...${NC}"
        docker_compose -f docker-compose.prod.yml build --no-cache
        ;;

    clean)
        echo -e "${YELLOW}🧹 Cleaning up...${NC}"
        docker_compose -f docker-compose.prod.yml down -v --remove-orphans
        docker system prune -f
        ;;

    *)
        echo "Usage: $0 {start|start-dev|start-monitoring|stop|restart|scale|logs|status|health|build|clean}"
        echo ""
        echo "Commands:"
        echo "  start [N]              Start with N API instances (default: 4)"
        echo "  start-dev              Start in development mode with Redis GUI"
        echo "  start-monitoring       Start with Prometheus + Grafana"
        echo "  stop                   Stop all services"
        echo "  restart [N]            Restart with N API instances"
        echo "  scale N S V            Scale API=N, Scanner=S, Video=V workers"
        echo "  logs [service]         Show logs (default: moderation-api)"
        echo "  status                 Show service status"
        echo "  health                 Run health checks"
        echo "  build                  Rebuild Docker images"
        echo "  clean                  Stop and remove all containers/volumes"
        echo ""
        echo "Examples:"
        echo "  $0 start 8             # Start with 8 API instances"
        echo "  $0 scale 8 4 4         # Scale: 8 API, 4 Scanner, 4 Video workers"
        echo "  $0 logs scanner-worker # Show scanner worker logs"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✅ Done!${NC}"
echo ""
echo "Service URLs:"
echo "  API:        http://localhost:8002"
echo "  WebSocket:  ws://localhost:8002/ws/moderate"
echo "  Health:     http://localhost:8002/health"
echo "  Metrics:    http://localhost:8002/metrics"
echo "  Docs:       http://localhost:8002/docs"
if [[ "$MODE" == *"monitoring"* ]]; then
    echo "  Prometheus: http://localhost:9090"
    echo "  Grafana:    http://localhost:3000 (admin/admin)"
fi
if [[ "$MODE" == *"dev"* ]]; then
    echo "  Redis GUI:  http://localhost:8081"
fi

