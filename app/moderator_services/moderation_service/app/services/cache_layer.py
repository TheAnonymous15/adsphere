"""
ModerationCache
Async cache layer for multimodal moderation workload.

Supports:
- fast lookups for repeated images/videos/audio/text
- async locking to prevent duplicate work on the same content
- configurable TTL
- pluggable backend: in-memory or Redis
"""

import asyncio
import hashlib
import time
from typing import Optional, Any


class ModerationCache:
    """
    Async cache used by batching coordinator + orchestrator.

    Cache keys = SHA256 hash of full asset bytes
    Values     = moderation result object/dict
    """

    def __init__(
        self,
        ttl_seconds: int = 3600,
        backend: str = "memory",
        redis_client=None
    ):
        self.ttl = ttl_seconds
        self.backend = backend
        self.redis = redis_client  # only used if backend == redis

        # memory cache
        self._store = {}
        self._expiry = {}

        # locks per-key to avoid duplicate work
        self._locks = {}

        # global shutdown flag
        self._closed = False

    # ----------------------------
    # Hashing utilities
    # ----------------------------

    @staticmethod
    def hash_asset(asset_bytes: bytes) -> str:
        return hashlib.sha256(asset_bytes).hexdigest()

    # ----------------------------
    # Internal helpers
    # ----------------------------

    def _cleanup_expired(self):
        now = time.time()
        expired = [k for k, exp in self._expiry.items() if exp < now]
        for k in expired:
            self._store.pop(k, None)
            self._expiry.pop(k, None)
            self._locks.pop(k, None)

    async def _get_lock(self, key: str) -> asyncio.Lock:
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    # ----------------------------
    # Core async API
    # ----------------------------

    async def get(self, key: str) -> Optional[Any]:
        """
        Return cached moderation result or None
        Performs TTL eviction automatically.
        """

        if self._closed:
            return None

        self._cleanup_expired()

        if self.backend == "redis" and self.redis:
            val = await self.redis.get(key)
            if val:
                return val

        val = self._store.get(key)
        return val

    async def put(self, key: str, value: Any):
        """
        Stores result + TTL metadata
        """

        if self._closed:
            return

        expiry = time.time() + self.ttl

        if self.backend == "redis" and self.redis:
            await self.redis.set(key, value, ex=self.ttl)
            return

        self._store[key] = value
        self._expiry[key] = expiry

    # ----------------------------
    # Duplicate compute prevention
    # ----------------------------

    async def acquire_lock(self, key: str):
        """
        Used by coordinator to avoid computing same key twice
        """
        lock = await self._get_lock(key)
        await lock.acquire()

    async def release_lock(self, key: str):
        """
        Releases key lock safely
        """
        lock = await self._get_lock(key)
        if lock.locked():
            lock.release()

    # ----------------------------
    # graceful shutdown
    # ----------------------------

    async def close(self):
        self._closed = True
        self._store.clear()
        self._expiry.clear()
        self._locks.clear()
