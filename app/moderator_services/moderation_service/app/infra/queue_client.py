"""
Redis Async Queue Client - Safe for asyncio workers
"""
import json
from typing import Dict, Optional, Any
from datetime import datetime
from redis.asyncio import Redis

from app.core.config import settings


class QueueClient:
    """
    Async Redis Streams queue client for moderation tasks
    """

    def __init__(self):
        self.redis = Redis.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
            decode_responses=True
        )

        self.VIDEO_QUEUE = "moderation:video:queue"
        self.IMAGE_QUEUE = "moderation:image:queue"
        self.RESULTS_PREFIX = "moderation:result:"
        self.STATUS_PREFIX = "moderation:status:"

    # -----------------------------
    # ENQUEUE JOBS
    # -----------------------------

    async def enqueue_video_job(self, job_id: str, video_path: str, metadata: Dict):
        payload = {
            "job_id": job_id,
            "video_path": video_path,
            "metadata": json.dumps(metadata),
            "created_at": datetime.utcnow().isoformat(),
        }

        await self.redis.xadd(self.VIDEO_QUEUE, payload)
        await self.set_job_status(job_id, "queued")
        return True

    async def enqueue_image_job(self, job_id: str, image_paths: list, metadata: Dict):
        payload = {
            "job_id": job_id,
            "image_paths": json.dumps(image_paths),
            "metadata": json.dumps(metadata),
            "created_at": datetime.utcnow().isoformat(),
        }

        await self.redis.xadd(self.IMAGE_QUEUE, payload)
        await self.set_job_status(job_id, "queued")
        return True

    # -----------------------------
    # STATUS + RESULTS
    # -----------------------------

    async def set_job_status(self, job_id: str, status: str, ttl: int = 86400):
        key = f"{self.STATUS_PREFIX}{job_id}"
        await self.redis.setex(key, ttl, status)

    async def get_job_status(self, job_id: str) -> Optional[str]:
        key = f"{self.STATUS_PREFIX}{job_id}"
        return await self.redis.get(key)

    async def store_result(self, job_id: str, result: Dict, ttl: int = 86400):
        key = f"{self.RESULTS_PREFIX}{job_id}"
        await self.redis.setex(key, ttl, json.dumps(result))

    async def get_result(self, job_id: str) -> Optional[Dict]:
        key = f"{self.RESULTS_PREFIX}{job_id}"
        raw = await self.redis.get(key)
        return json.loads(raw) if raw else None

    # -----------------------------
    # JOB CONSUMPTION
    # -----------------------------

    async def consume_jobs(
        self,
        queue_name: str,
        consumer_group: str,
        consumer_name: str,
        count: int = 1,
        block_ms: int = 5000,
    ):

        # create group if needed
        try:
            await self.redis.xgroup_create(
                queue_name,
                consumer_group,
                id="0",
                mkstream=True
            )
        except Exception:
            pass  # group exists

        resp = await self.redis.xreadgroup(
            consumer_group,
            consumer_name,
            {queue_name: '>'},
            count=count,
            block=block_ms
        )

        jobs = []
        if resp:
            for stream_name, stream_messages in resp:
                for msg_id, data in stream_messages:
                    jobs.append({"id": msg_id, "data": data})
        return jobs

    async def acknowledge_job(self, queue_name: str, consumer_group: str, message_id: str):
        await self.redis.xack(queue_name, consumer_group, message_id)

    # -----------------------------
    # LIFECYCLE
    # -----------------------------

    async def health_check(self):
        try:
            return await self.redis.ping()
        except Exception:
            return False

    async def close(self):
        await self.redis.close()

