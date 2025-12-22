"""
main.py – FastAPI microservice entrypoint
Multimodal moderation service with async batching + workers
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

# Routers
from app.api import (
    routes_moderation,
    routes_health,
    routes_ws,        # websocket dispatcher
)

# Shared service lifecycle
from app.services.lifecycle import (
    init_services,
    shutdown_services,
)

import logging


# -----------------------------------------------------------
# Logging setup – structured + production safe
# -----------------------------------------------------------
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


# -----------------------------------------------------------
# FastAPI container
# -----------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Enterprise-grade multimodal AI moderation platform",
    docs_url="/docs",
    redoc_url="/redoc",
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
# ROUTES SETUP
# -----------------------------------------------------------

# Moderation REST API
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
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "mode": "asynchronous inference",
    }
