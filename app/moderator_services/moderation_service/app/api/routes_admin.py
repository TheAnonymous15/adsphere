"""
routes_admin.py – Administrative control endpoints

Provides system control capabilities:
- Service restart/shutdown
- Cache management
- Worker controls
- Scaling (info only, actual scaling via docker-compose)
- Health and status
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse, PlainTextResponse
import os
import signal
import asyncio
import subprocess
from datetime import datetime
from typing import Optional

router = APIRouter()

# Store service start time
SERVICE_START_TIME = datetime.now()


# =============================================================================
# SERVICE MANAGEMENT
# =============================================================================

@router.get("/status")
async def get_service_status():
    """Get comprehensive service status"""
    import psutil

    process = psutil.Process()

    return {
        "status": "running",
        "started_at": SERVICE_START_TIME.isoformat(),
        "uptime_seconds": (datetime.now() - SERVICE_START_TIME).total_seconds(),
        "pid": os.getpid(),
        "memory_mb": process.memory_info().rss / 1024 / 1024,
        "cpu_percent": process.cpu_percent(),
        "threads": process.num_threads(),
        "instance_id": os.getenv("INSTANCE_ID", "unknown"),
        "workers": os.getenv("WORKERS", "4"),
        "environment": os.getenv("ENVIRONMENT", "production")
    }


@router.post("/restart")
async def restart_service(background_tasks: BackgroundTasks):
    """
    Gracefully restart the service.
    Note: In Docker, this will trigger container restart via health check failure.
    """
    async def delayed_restart():
        await asyncio.sleep(2)  # Give time for response to be sent
        os.kill(os.getpid(), signal.SIGTERM)

    background_tasks.add_task(delayed_restart)

    return {
        "status": "restarting",
        "message": "Service will restart in 2 seconds",
        "timestamp": datetime.now().isoformat()
    }


@router.post("/shutdown")
async def shutdown_service(
    background_tasks: BackgroundTasks,
    force: bool = Query(False, description="Force immediate shutdown")
):
    """
    Gracefully shutdown the service.
    Use force=true for immediate shutdown.
    """
    if force:
        os.kill(os.getpid(), signal.SIGKILL)
    else:
        async def delayed_shutdown():
            await asyncio.sleep(2)
            os.kill(os.getpid(), signal.SIGTERM)

        background_tasks.add_task(delayed_shutdown)

    return {
        "status": "shutting_down",
        "message": "Service will shutdown in 2 seconds",
        "force": force,
        "timestamp": datetime.now().isoformat()
    }


# =============================================================================
# CACHE MANAGEMENT
# =============================================================================

@router.post("/cache/clear")
async def clear_cache(
    pattern: str = Query("*", description="Redis key pattern to clear")
):
    """Clear Redis cache"""
    try:
        from app.services.lifecycle import cache

        if hasattr(cache, 'redis') and cache.redis:
            if pattern == "*":
                await cache.redis.flushdb()
                cleared = "all"
            else:
                keys = await cache.redis.keys(pattern)
                if keys:
                    await cache.redis.delete(*keys)
                cleared = len(keys)
        else:
            # In-memory cache fallback
            if hasattr(cache, '_cache'):
                cache._cache.clear()
            cleared = "memory"

        return {
            "status": "success",
            "cleared": cleared,
            "pattern": pattern,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan-cache/clear")
async def clear_scan_cache(
    older_than_hours: int = Query(0, description="Clear entries older than N hours (0 = all)")
):
    """Clear ad scan result cache"""
    try:
        from app.services.lifecycle import cache

        pattern = "scan:*"

        if hasattr(cache, 'redis') and cache.redis:
            keys = await cache.redis.keys(pattern)
            if keys:
                await cache.redis.delete(*keys)
            cleared = len(keys) if keys else 0
        else:
            cleared = 0

        return {
            "status": "success",
            "cleared": cleared,
            "older_than_hours": older_than_hours,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    try:
        from app.services.lifecycle import cache

        stats = {
            "backend": "unknown",
            "connected": False,
            "keys": 0,
            "memory_used": "N/A"
        }

        if hasattr(cache, 'redis') and cache.redis:
            info = await cache.redis.info()
            stats = {
                "backend": "redis",
                "connected": True,
                "keys": info.get("db0", {}).get("keys", 0) if isinstance(info.get("db0"), dict) else await cache.redis.dbsize(),
                "memory_used": info.get("used_memory_human", "N/A"),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": round(info.get("keyspace_hits", 0) / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1), 1) * 100, 2)
            }

        return stats
    except Exception as e:
        return {"backend": "error", "error": str(e)}


# =============================================================================
# WORKER CONTROLS
# =============================================================================

@router.get("/worker/{worker_type}/status")
async def get_worker_status(worker_type: str):
    """Get status of a specific worker type"""
    valid_workers = ["scanner", "video", "image", "text"]

    if worker_type not in valid_workers:
        raise HTTPException(status_code=400, detail=f"Invalid worker type. Valid: {valid_workers}")

    # In Docker Compose, we can't directly control workers
    # This is informational only
    return {
        "worker_type": worker_type,
        "status": "running",  # Assume running if API is up
        "message": "Worker status check. Use docker-compose to manage workers.",
        "command": f"docker-compose -f docker-compose.prod.yml ps {worker_type}-worker"
    }


@router.post("/worker/{worker_type}/start")
async def start_worker(worker_type: str):
    """Start a worker (informational - use docker-compose)"""
    return {
        "worker_type": worker_type,
        "status": "info",
        "message": "Use docker-compose to start workers",
        "command": f"docker-compose -f docker-compose.prod.yml up -d {worker_type}-worker"
    }


@router.post("/worker/{worker_type}/stop")
async def stop_worker(worker_type: str):
    """Stop a worker (informational - use docker-compose)"""
    return {
        "worker_type": worker_type,
        "status": "info",
        "message": "Use docker-compose to stop workers",
        "command": f"docker-compose -f docker-compose.prod.yml stop {worker_type}-worker"
    }


# =============================================================================
# SCALING (Informational)
# =============================================================================

@router.get("/scale")
async def get_current_scale():
    """Get current scaling information"""
    return {
        "current_api_instances": os.getenv("REPLICAS", "unknown"),
        "message": "Use docker-compose to scale",
        "commands": {
            "scale_up": "docker-compose -f docker-compose.prod.yml up -d --scale moderation-api=8",
            "scale_down": "docker-compose -f docker-compose.prod.yml up -d --scale moderation-api=2",
            "check": "docker-compose -f docker-compose.prod.yml ps"
        }
    }


@router.post("/scale")
async def scale_service(replicas: int = Query(4, ge=1, le=20)):
    """Scale API instances (informational - use docker-compose)"""
    return {
        "requested_replicas": replicas,
        "status": "info",
        "message": "Use docker-compose to scale API instances",
        "command": f"docker-compose -f docker-compose.prod.yml up -d --scale moderation-api={replicas}"
    }


# =============================================================================
# SCANNER CONTROLS
# =============================================================================

@router.post("/scanner/run")
async def run_manual_scan(
    background_tasks: BackgroundTasks,
    mode: str = Query("incremental", enum=["incremental", "full", "priority"]),
    limit: int = Query(100, ge=1, le=10000)
):
    """Trigger a manual ad scan"""
    try:
        from app.services.scanner import AdScanner

        scanner = AdScanner()

        async def run_scan():
            if mode == "incremental":
                await scanner.scan_incremental(hours=24, limit=limit)
            elif mode == "full":
                await scanner.scan_full(limit=limit)
            elif mode == "priority":
                await scanner.scan_priority(limit=limit)

        background_tasks.add_task(run_scan)

        return {
            "status": "started",
            "mode": mode,
            "limit": limit,
            "message": "Scan started in background",
            "timestamp": datetime.now().isoformat()
        }
    except ImportError:
        return {
            "status": "info",
            "message": "Scanner module not available. Use CLI or cron job.",
            "command": "php app/cron/scanner_cron.php incremental"
        }


@router.get("/scanner/status")
async def get_scanner_status():
    """Get scanner status"""
    try:
        from app.services.scanner import AdScanner
        scanner = AdScanner()
        return await scanner.get_status()
    except:
        return {
            "status": "unknown",
            "message": "Scanner status unavailable"
        }


# =============================================================================
# LOGS
# =============================================================================

@router.get("/logs")
async def get_recent_logs(
    lines: int = Query(100, ge=1, le=1000),
    level: str = Query("all", enum=["all", "error", "warning", "info"])
):
    """Get recent log entries"""
    log_file = "/app/logs/moderation.log"

    if not os.path.exists(log_file):
        return {
            "status": "info",
            "message": "Log file not found. Logs may be in Docker stdout.",
            "command": "docker-compose -f docker-compose.prod.yml logs --tail=100 moderation-api"
        }

    try:
        with open(log_file, 'r') as f:
            all_lines = f.readlines()

        # Filter by level if specified
        if level != "all":
            all_lines = [l for l in all_lines if level.upper() in l]

        # Get last N lines
        recent = all_lines[-lines:]

        return {
            "total_lines": len(all_lines),
            "returned_lines": len(recent),
            "level_filter": level,
            "logs": recent
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SYSTEM INFO
# =============================================================================

@router.get("/system")
async def get_system_info():
    """Get system information"""
    import platform
    import psutil

    return {
        "hostname": platform.node(),
        "platform": platform.system(),
        "platform_release": platform.release(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory": {
            "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "percent_used": psutil.virtual_memory().percent
        },
        "disk": {
            "total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
            "free_gb": round(psutil.disk_usage('/').free / (1024**3), 2),
            "percent_used": psutil.disk_usage('/').percent
        }
    }

