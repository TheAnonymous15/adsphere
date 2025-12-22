"""
app/services/orchestrator.py

Responsible only for init + shutdown lifecycle
Called by FastAPI main.py but implemented using
the async components from main_async
"""

from app.services.lifecycle import (
    init_services,
    shutdown_services
)

_initialized = False

async def init_orchestrator():
    """
    Called automatically at FastAPI startup event
    Ensures shared resources and workers are initialized once
    """
    global _initialized
    if _initialized:
        return

    print("🔧 [Orchestrator] initializing async moderation services...")
    await init_services()
    _initialized = True
    print("🚀 [Orchestrator] ready.")


async def shutdown_orchestrator():
    """
    Called automatically at FastAPI shutdown event
    Ensures graceful shutdown
    """
    print("🛑 [Orchestrator] stopping services...")
    await shutdown_services()
    print("✔ [Orchestrator] shutdown complete.")
