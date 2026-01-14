# app/services/lifecycle.py

import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.infra.queue_client import QueueClient
from app.services.cache_layer import ModerationCache
from app.workers.batch_coordinator import BatchCoordinator, _load_models

queue = None
cache = None
coordinator = None
_executor = ThreadPoolExecutor(max_workers=1)


async def init_services():
    global queue, cache, coordinator

    queue = QueueClient()
    cache = ModerationCache()
    coordinator = BatchCoordinator()

    # load model weights to avoid cold start during first job
    # Use the standalone _load_models function in a thread pool
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(_executor, _load_models)

    # start batch + workers in background
    asyncio.create_task(coordinator.run_workers())


async def shutdown_services():
    global queue, cache, coordinator

    if queue:
        await queue.close()

    if cache:
        await cache.close()

    if coordinator:
        await coordinator.shutdown()


def get_batch_coordinator() -> BatchCoordinator:
    """
    Accessor to avoid globals in code that imports lifecycle
    """
    return coordinator
