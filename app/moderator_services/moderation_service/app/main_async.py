"""
main_async.py
Async entrypoint coordinating queues, batching, caching + workers
"""

import asyncio
import signal
import uvicorn

from app.infra.queue_client import QueueClient
from app.services.cache_layer import ModerationCache
from app.workers.batch_coordinator import BatchCoordinator

# shared singletons
queue = QueueClient()
cache = ModerationCache()
coordinator = BatchCoordinator()

async def dispatch_loop():
    while True:
        task = await queue.get_task()  # blocks until new moderation job

        asset_hash = cache.hash_asset(task.asset_bytes)

        # FAST PATH: cached full pipeline result
        cached = await cache.get(asset_hash)
        if cached:
            await queue.submit_result(task.id, cached)
            continue

        # async schedule into batching buffer
        fut = await coordinator.schedule(task.id, task.asset_bytes)

        # wait for pipeline to finish (async)
        result = await fut

        await cache.put(asset_hash, result)

        await queue.submit_result(task.id, result)


async def start_workers():
    """
    Bootstraps deep models async and starts processing loops.
    Runs forever until cancelled.
    """
    await coordinator.load_models()     # async load OCR + caption + action model
    await coordinator.run_workers()     # async pool for model execution


async def start_server():
    config = uvicorn.Config(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
    server = uvicorn.Server(config)
    await server.serve()


async def shutdown():
    await queue.close()
    await coordinator.shutdown()
    await cache.close()


async def main():
    loop = asyncio.get_event_loop()

    # graceful shutdown signals
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))

    await asyncio.gather(
        start_server(),     # http API
        dispatch_loop(),    # distributes moderation jobs
        start_workers(),    # async pipelines + GPU workers
    )


if __name__ == "__main__":
    asyncio.run(main())
