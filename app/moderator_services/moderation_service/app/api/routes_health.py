"""
Health check and readiness endpoints
"""
from fastapi import APIRouter, Response, status
from app.core.config import settings
import time
import psutil
import os

router = APIRouter()

start_time = time.time()


@router.get("/health")
async def health_check():
    """
    Basic health check - returns 200 if service is alive
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "uptime_seconds": int(time.time() - start_time)
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness check - verifies all dependencies are available
    Used by load balancers and orchestrators
    """
    checks = {
        "redis": _check_redis(),
        "models": _check_models(),
        "disk_space": _check_disk_space()
    }

    all_ready = all(checks.values())

    if all_ready:
        return {
            "status": "ready",
            "checks": checks
        }
    else:
        return Response(
            content={
                "status": "not_ready",
                "checks": checks
            },
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


@router.get("/metrics")
async def metrics():
    """
    Basic metrics endpoint
    """
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()

    return {
        "uptime_seconds": int(time.time() - start_time),
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "memory_available_mb": memory.available / (1024 * 1024),
        "process_count": len(psutil.pids())
    }


def _check_redis() -> bool:
    """Check if Redis is accessible"""
    try:
        from redis import Redis
        from app.core.config import settings

        r = Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        r.ping()
        return True
    except Exception:
        return False


def _check_models() -> bool:
    """Check if required model directories exist"""
    models_dir = settings.MODELS_DIR
    return os.path.exists(models_dir) and os.path.isdir(models_dir)


def _check_disk_space() -> bool:
    """Check if sufficient disk space is available"""
    try:
        disk = psutil.disk_usage('/')
        return disk.percent < 90  # Alert if disk > 90% full
    except Exception:
        return True  # Don't fail if we can't check

