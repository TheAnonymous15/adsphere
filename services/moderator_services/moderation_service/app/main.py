"""
main.py – FastAPI microservice entrypoint
Multimodal moderation service with async batching + workers

Scalability Features:
- Horizontal scaling via multiple instances
- Redis-based distributed caching
- Prometheus metrics for monitoring
- Health checks for load balancers
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import time
import uuid
import os

from app.core.config import settings

# Routers
from app.api import (
    routes_moderation,
    routes_health,
    routes_ws,        # websocket dispatcher
)

# Try to import admin routes (may fail if psutil not installed)
try:
    from app.api import routes_admin
    ADMIN_ROUTES_AVAILABLE = True
except ImportError:
    ADMIN_ROUTES_AVAILABLE = False

# Try to import search routes
try:
    from app.services.search_assisatnt.search_service import router as search_router
    SEARCH_ROUTES_AVAILABLE = True
except ImportError as e:
    print(f"Search routes not available: {e}")
    SEARCH_ROUTES_AVAILABLE = False

# Shared service lifecycle
from app.services.lifecycle import (
    init_services,
    shutdown_services,
)

import logging

from app.api.routes_architecture import router as architecture_router
from app.api.routes_docs import router as docs_router


# -----------------------------------------------------------
# Instance ID for tracking in distributed environment
# -----------------------------------------------------------
INSTANCE_ID = os.getenv("INSTANCE_ID", str(uuid.uuid4())[:8])


# -----------------------------------------------------------
# Metrics tracking (simple in-memory, use Prometheus for production)
# -----------------------------------------------------------
class Metrics:
    def __init__(self):
        self.requests_total = 0
        self.requests_by_endpoint = {}
        self.errors_total = 0
        self.latency_sum = 0
        self.latency_count = 0
        self.start_time = time.time()

    def record_request(self, endpoint: str, latency: float, error: bool = False):
        self.requests_total += 1
        self.requests_by_endpoint[endpoint] = self.requests_by_endpoint.get(endpoint, 0) + 1
        self.latency_sum += latency
        self.latency_count += 1
        if error:
            self.errors_total += 1

    def get_avg_latency(self):
        return self.latency_sum / self.latency_count if self.latency_count > 0 else 0

    def to_prometheus(self):
        """Export metrics in Prometheus format"""
        uptime = time.time() - self.start_time
        lines = [
            f'# HELP moderation_requests_total Total number of requests',
            f'# TYPE moderation_requests_total counter',
            f'moderation_requests_total{{instance="{INSTANCE_ID}"}} {self.requests_total}',
            f'',
            f'# HELP moderation_errors_total Total number of errors',
            f'# TYPE moderation_errors_total counter',
            f'moderation_errors_total{{instance="{INSTANCE_ID}"}} {self.errors_total}',
            f'',
            f'# HELP moderation_latency_seconds Average request latency',
            f'# TYPE moderation_latency_seconds gauge',
            f'moderation_latency_seconds{{instance="{INSTANCE_ID}"}} {self.get_avg_latency():.6f}',
            f'',
            f'# HELP moderation_uptime_seconds Service uptime',
            f'# TYPE moderation_uptime_seconds gauge',
            f'moderation_uptime_seconds{{instance="{INSTANCE_ID}"}} {uptime:.2f}',
        ]

        # Per-endpoint metrics
        for endpoint, count in self.requests_by_endpoint.items():
            lines.append(f'moderation_requests_by_endpoint{{instance="{INSTANCE_ID}",endpoint="{endpoint}"}} {count}')

        return '\n'.join(lines)

metrics = Metrics()


# -----------------------------------------------------------
# Logging setup – structured + production safe
# -----------------------------------------------------------
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=f"%(asctime)s - [{INSTANCE_ID}] - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# -----------------------------------------------------------
# API Documentation
# -----------------------------------------------------------
from app.api.api_docs import (
    TAGS_METADATA,
    API_DESCRIPTION,
    API_LICENSE,
    API_CONTACT,
)


# -----------------------------------------------------------
# FastAPI container with comprehensive documentation
# -----------------------------------------------------------
app = FastAPI(
    title="🛡️ AdSphere Moderation API",
    version=settings.VERSION,
    description=API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=TAGS_METADATA,
    license_info=API_LICENSE,
    contact=API_CONTACT,
    swagger_ui_parameters={
        "deepLinking": True,
        "displayRequestDuration": True,
        "docExpansion": "list",
        "operationsSorter": "method",
        "filter": True,
        "tagsSorter": "alpha",
        "defaultModelsExpandDepth": 3,
        "defaultModelExpandDepth": 3,
        "showExtensions": True,
        "showCommonExtensions": True,
        "tryItOutEnabled": True,
        "persistAuthorization": True,
        "syntaxHighlight.theme": "monokai",
    },
    redoc_url_parameters={
        "expandResponses": "200,201",
        "hideDownloadButton": False,
        "hideHostname": False,
    },
)


# -----------------------------------------------------------
# CORS config – only whitelist allowed origins
# -----------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------
# REQUEST TRACKING MIDDLEWARE
# -----------------------------------------------------------
@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Track request metrics for monitoring"""
    start_time = time.time()

    try:
        response = await call_next(request)
        latency = time.time() - start_time

        # Record metrics
        endpoint = request.url.path
        is_error = response.status_code >= 400
        metrics.record_request(endpoint, latency, is_error)

        # Add instance ID to response headers
        response.headers["X-Instance-ID"] = INSTANCE_ID
        response.headers["X-Response-Time"] = f"{latency:.3f}s"

        return response
    except Exception as e:
        latency = time.time() - start_time
        metrics.record_request(request.url.path, latency, error=True)
        raise


# -----------------------------------------------------------
# ROUTES SETUP
# -----------------------------------------------------------

# Moderation REST API - all endpoints under /moderate
# Endpoints: /moderate/text/process, /moderate/image/process, /moderate/video/process
app.include_router(
    routes_moderation.router,
    prefix="/moderate",
    tags=["moderation"],
)


# Health + version check
app.include_router(
    routes_health.router,
    tags=["health"],
)

# WebSocket moderation entrypoint
app.include_router(
    routes_ws.router,
    prefix="/ws",
    tags=["websocket"],
)

# Admin/Control endpoints
if ADMIN_ROUTES_AVAILABLE:
    app.include_router(
        routes_admin.router,
        prefix="/admin",
        tags=["admin"],
    )

# AI-powered Search endpoints
if SEARCH_ROUTES_AVAILABLE:
    app.include_router(
        search_router,
        tags=["search"],
    )

# Add architecture docs route
app.include_router(architecture_router)

# Add detailed documentation route
app.include_router(docs_router)


# -----------------------------------------------------------
# APPLICATION LIFECYCLE – shared dependency graph
# -----------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    """
    Initialize async microservices used by the moderation engine:

        - batching + queue coordinator
        - async GPU/CPU worker pools
        - Redis queue client
        - async moderation cache layer
        - session/model preloading
    """
    await init_services()


@app.on_event("shutdown")
async def shutdown_event():
    """
    Gracefully shutdown moderation stack:

        - drain batching queues
        - flush worker buffers
        - close Redis connections
        - release GPU memory + async pools
    """
    await shutdown_services()



# -----------------------------------------------------------
# ROOT ENDPOINT – lightweight API index
# -----------------------------------------------------------
@app.get("/")
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "instance_id": INSTANCE_ID,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
        "mode": "asynchronous inference",
        "scalability": {
            "horizontal": True,
            "load_balanced": True,
            "stateless": True
        }
    }


# -----------------------------------------------------------
# METRICS ENDPOINT – Prometheus compatible
# -----------------------------------------------------------
@app.get("/metrics", response_class=PlainTextResponse)
async def get_metrics():
    """
    Export metrics in Prometheus format.

    Scrape this endpoint with Prometheus:
    ```yaml
    - job_name: 'moderation-api'
      static_configs:
        - targets: ['localhost:8002']
      metrics_path: /metrics
    ```
    """
    return metrics.to_prometheus()


# -----------------------------------------------------------
# INSTANCE INFO ENDPOINT
# -----------------------------------------------------------
@app.get("/instance")
async def get_instance_info():
    """Get information about this specific instance"""
    import os
    import platform

    return {
        "instance_id": INSTANCE_ID,
        "hostname": platform.node(),
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "cpu_count": os.cpu_count(),
        "pid": os.getpid(),
        "uptime_seconds": time.time() - metrics.start_time,
        "requests_handled": metrics.requests_total,
        "avg_latency_ms": metrics.get_avg_latency() * 1000
    }
