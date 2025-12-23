"""
Search Cache - High-performance caching for AI search results
First touch point before hitting the model to reduce latency and load.

Cache Hierarchy:
1. In-memory LRU cache (fastest, limited size)
2. Redis (if available, distributed)
3. SQLite database (persistent, local)
4. JSON file (fallback, portable)

Usage:
    from cache import SearchCache

    cache = SearchCache()

    # Check cache first
    result = await cache.get("hungry")
    if result:
        return result  # Cache hit!

    # Cache miss - query model
    result = model.match("hungry")

    # Store in cache
    await cache.set("hungry", result)
"""

import os
import sys
import json
import time
import hashlib
import asyncio
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from functools import lru_cache
from collections import OrderedDict
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try Redis import
try:
    import redis
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available. Using local cache only.")


# ==============================================================================
# CONFIGURATION
# ==============================================================================

class CacheConfig:
    """Cache configuration settings."""

    # Redis settings
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 1))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
    REDIS_PREFIX = "adsphere:search:"

    # TTL settings (in seconds)
    CACHE_TTL = int(os.getenv("SEARCH_CACHE_TTL", 86400 * 7))  # 7 days default
    MEMORY_CACHE_TTL = 3600  # 1 hour for in-memory

    # Size limits
    MEMORY_CACHE_SIZE = 10000  # Max entries in memory

    # File paths
    BASE_DIR = Path(__file__).parent.parent.parent.parent.parent
    CACHE_DIR = BASE_DIR / "cache" / "search"
    DB_PATH = CACHE_DIR / "search_cache.db"
    JSON_PATH = CACHE_DIR / "search_cache.json"

    @classmethod
    def ensure_dirs(cls):
        """Ensure cache directories exist."""
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# IN-MEMORY LRU CACHE
# ==============================================================================

class LRUCache:
    """Thread-safe LRU cache with TTL support."""

    def __init__(self, max_size: int = 10000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[str, float] = {}
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache."""
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None

            # Check TTL
            if time.time() - self.timestamps.get(key, 0) > self.ttl:
                self._remove(key)
                self.misses += 1
                return None

            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]

    def set(self, key: str, value: Any) -> None:
        """Set item in cache."""
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            else:
                if len(self.cache) >= self.max_size:
                    # Remove oldest
                    oldest = next(iter(self.cache))
                    self._remove(oldest)

            self.cache[key] = value
            self.timestamps[key] = time.time()

    def _remove(self, key: str) -> None:
        """Remove item from cache."""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)

    def clear(self) -> int:
        """Clear all items."""
        with self.lock:
            count = len(self.cache)
            self.cache.clear()
            self.timestamps.clear()
            return count

    def stats(self) -> Dict:
        """Get cache statistics."""
        with self.lock:
            total = self.hits + self.misses
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": self.hits / total if total > 0 else 0
            }


# ==============================================================================
# SQLITE CACHE
# ==============================================================================

class SQLiteCache:
    """SQLite-based persistent cache."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        CacheConfig.ensure_dirs()

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_cache (
                query_hash TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                results TEXT NOT NULL,
                created_at REAL NOT NULL,
                accessed_at REAL NOT NULL,
                access_count INTEGER DEFAULT 1,
                ttl INTEGER DEFAULT 604800
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_query ON search_cache(query)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created ON search_cache(created_at)
        """)

        conn.commit()
        conn.close()

    def _hash_query(self, query: str) -> str:
        """Generate hash for query."""
        return hashlib.sha256(query.lower().strip().encode()).hexdigest()[:32]

    def get(self, query: str) -> Optional[List[Dict]]:
        """Get cached results for query."""
        query_hash = self._hash_query(query)

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                SELECT results, created_at, ttl FROM search_cache
                WHERE query_hash = ?
            """, (query_hash,))

            row = cursor.fetchone()

            if row:
                results_json, created_at, ttl = row

                # Check TTL
                if time.time() - created_at > ttl:
                    # Expired, delete
                    cursor.execute("DELETE FROM search_cache WHERE query_hash = ?", (query_hash,))
                    conn.commit()
                    conn.close()
                    return None

                # Update access stats
                cursor.execute("""
                    UPDATE search_cache 
                    SET accessed_at = ?, access_count = access_count + 1
                    WHERE query_hash = ?
                """, (time.time(), query_hash))
                conn.commit()
                conn.close()

                return json.loads(results_json)

            conn.close()
            return None

        except Exception as e:
            logger.error(f"SQLite cache get error: {e}")
            return None

    def set(self, query: str, results: List[Dict], ttl: int = None) -> bool:
        """Store results in cache."""
        query_hash = self._hash_query(query)
        ttl = ttl or CacheConfig.CACHE_TTL

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO search_cache 
                (query_hash, query, results, created_at, accessed_at, access_count, ttl)
                VALUES (?, ?, ?, ?, ?, 1, ?)
            """, (
                query_hash,
                query.lower().strip(),
                json.dumps(results),
                time.time(),
                time.time(),
                ttl
            ))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"SQLite cache set error: {e}")
            return False

    def delete(self, query: str) -> bool:
        """Delete entry from cache."""
        query_hash = self._hash_query(query)

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("DELETE FROM search_cache WHERE query_hash = ?", (query_hash,))
            conn.commit()
            deleted = cursor.rowcount > 0
            conn.close()
            return deleted
        except Exception as e:
            logger.error(f"SQLite cache delete error: {e}")
            return False

    def clear(self) -> int:
        """Clear all cached entries."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM search_cache")
            count = cursor.fetchone()[0]
            cursor.execute("DELETE FROM search_cache")
            conn.commit()
            conn.close()
            return count
        except Exception as e:
            logger.error(f"SQLite cache clear error: {e}")
            return 0

    def cleanup_expired(self) -> int:
        """Remove expired entries."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM search_cache 
                WHERE (created_at + ttl) < ?
            """, (time.time(),))

            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            return deleted
        except Exception as e:
            logger.error(f"SQLite cleanup error: {e}")
            return 0

    def stats(self) -> Dict:
        """Get cache statistics."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM search_cache")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT SUM(access_count) FROM search_cache")
            total_hits = cursor.fetchone()[0] or 0

            cursor.execute("""
                SELECT query, access_count FROM search_cache 
                ORDER BY access_count DESC LIMIT 10
            """)
            top_queries = cursor.fetchall()

            conn.close()

            return {
                "total_entries": total,
                "total_hits": total_hits,
                "top_queries": [{"query": q, "hits": h} for q, h in top_queries]
            }
        except Exception as e:
            logger.error(f"SQLite stats error: {e}")
            return {}


# ==============================================================================
# JSON FILE CACHE (Fallback)
# ==============================================================================

class JSONCache:
    """JSON file-based cache (fallback/portable)."""

    def __init__(self, json_path: Path):
        self.json_path = json_path
        self.lock = threading.RLock()
        self._load()

    def _load(self) -> None:
        """Load cache from file."""
        CacheConfig.ensure_dirs()

        if self.json_path.exists():
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except:
                self.data = {"entries": {}, "metadata": {"created": time.time()}}
        else:
            self.data = {"entries": {}, "metadata": {"created": time.time()}}

    def _save(self) -> None:
        """Save cache to file."""
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"JSON cache save error: {e}")

    def _normalize_key(self, query: str) -> str:
        """Normalize query for use as key."""
        return query.lower().strip()

    def get(self, query: str) -> Optional[List[Dict]]:
        """Get cached results."""
        with self.lock:
            key = self._normalize_key(query)
            entry = self.data["entries"].get(key)

            if not entry:
                return None

            # Check TTL
            if time.time() - entry.get("created", 0) > entry.get("ttl", CacheConfig.CACHE_TTL):
                del self.data["entries"][key]
                self._save()
                return None

            # Update access stats
            entry["accessed"] = time.time()
            entry["hits"] = entry.get("hits", 0) + 1
            self._save()

            return entry.get("results")

    def set(self, query: str, results: List[Dict], ttl: int = None) -> bool:
        """Store results in cache."""
        with self.lock:
            key = self._normalize_key(query)

            self.data["entries"][key] = {
                "query": query,
                "results": results,
                "created": time.time(),
                "accessed": time.time(),
                "hits": 1,
                "ttl": ttl or CacheConfig.CACHE_TTL
            }

            self._save()
            return True

    def delete(self, query: str) -> bool:
        """Delete entry."""
        with self.lock:
            key = self._normalize_key(query)
            if key in self.data["entries"]:
                del self.data["entries"][key]
                self._save()
                return True
            return False

    def clear(self) -> int:
        """Clear all entries."""
        with self.lock:
            count = len(self.data["entries"])
            self.data["entries"] = {}
            self._save()
            return count

    def stats(self) -> Dict:
        """Get cache statistics."""
        with self.lock:
            entries = self.data["entries"]
            total_hits = sum(e.get("hits", 0) for e in entries.values())

            # Top queries by hits
            sorted_entries = sorted(
                entries.items(),
                key=lambda x: x[1].get("hits", 0),
                reverse=True
            )[:10]

            return {
                "total_entries": len(entries),
                "total_hits": total_hits,
                "top_queries": [
                    {"query": k, "hits": v.get("hits", 0)}
                    for k, v in sorted_entries
                ]
            }


# ==============================================================================
# REDIS CACHE
# ==============================================================================

class RedisCache:
    """Redis-based distributed cache."""

    def __init__(self):
        self.client = None
        self.async_client = None
        self._connect()

    def _connect(self) -> bool:
        """Connect to Redis."""
        if not REDIS_AVAILABLE:
            return False

        try:
            self.client = redis.Redis(
                host=CacheConfig.REDIS_HOST,
                port=CacheConfig.REDIS_PORT,
                db=CacheConfig.REDIS_DB,
                password=CacheConfig.REDIS_PASSWORD,
                decode_responses=True,
                socket_timeout=5
            )
            # Test connection
            self.client.ping()
            logger.info(f"✅ Connected to Redis at {CacheConfig.REDIS_HOST}:{CacheConfig.REDIS_PORT}")
            return True
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self.client = None
            return False

    def _key(self, query: str) -> str:
        """Generate Redis key."""
        normalized = query.lower().strip()
        return f"{CacheConfig.REDIS_PREFIX}{normalized}"

    def get(self, query: str) -> Optional[List[Dict]]:
        """Get from Redis."""
        if not self.client:
            return None

        try:
            key = self._key(query)
            data = self.client.get(key)

            if data:
                # Update access stats
                self.client.hincrby(f"{key}:meta", "hits", 1)
                self.client.hset(f"{key}:meta", "accessed", time.time())
                return json.loads(data)

            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    def set(self, query: str, results: List[Dict], ttl: int = None) -> bool:
        """Store in Redis."""
        if not self.client:
            return False

        try:
            key = self._key(query)
            ttl = ttl or CacheConfig.CACHE_TTL

            # Store results
            self.client.setex(key, ttl, json.dumps(results))

            # Store metadata
            self.client.hset(f"{key}:meta", mapping={
                "query": query,
                "created": time.time(),
                "accessed": time.time(),
                "hits": 1
            })
            self.client.expire(f"{key}:meta", ttl)

            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    def delete(self, query: str) -> bool:
        """Delete from Redis."""
        if not self.client:
            return False

        try:
            key = self._key(query)
            self.client.delete(key, f"{key}:meta")
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    def clear(self) -> int:
        """Clear all search cache entries."""
        if not self.client:
            return 0

        try:
            pattern = f"{CacheConfig.REDIS_PREFIX}*"
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return 0

    def stats(self) -> Dict:
        """Get Redis cache stats."""
        if not self.client:
            return {"available": False}

        try:
            pattern = f"{CacheConfig.REDIS_PREFIX}*"
            keys = [k for k in self.client.keys(pattern) if not k.endswith(":meta")]

            return {
                "available": True,
                "total_entries": len(keys),
                "redis_info": {
                    "host": CacheConfig.REDIS_HOST,
                    "port": CacheConfig.REDIS_PORT,
                    "db": CacheConfig.REDIS_DB
                }
            }
        except Exception as e:
            return {"available": False, "error": str(e)}


# ==============================================================================
# MAIN SEARCH CACHE (Unified Interface)
# ==============================================================================

class SearchCache:
    """
    Unified search cache with multi-tier storage.

    Cache hierarchy (checked in order):
    1. In-memory LRU (fastest)
    2. Redis (distributed, if available)
    3. SQLite (persistent)
    4. JSON file (fallback)

    Write-through: writes to ALL available tiers
    """

    def __init__(self):
        # Initialize cache tiers
        self.memory = LRUCache(
            max_size=CacheConfig.MEMORY_CACHE_SIZE,
            ttl=CacheConfig.MEMORY_CACHE_TTL
        )

        self.redis = RedisCache() if REDIS_AVAILABLE else None
        self.sqlite = SQLiteCache(CacheConfig.DB_PATH)
        self.json = JSONCache(CacheConfig.JSON_PATH)

        # Stats tracking
        self.total_requests = 0
        self.tier_hits = {"memory": 0, "redis": 0, "sqlite": 0, "json": 0, "miss": 0}

        logger.info("🚀 SearchCache initialized")
        logger.info(f"   Memory: {CacheConfig.MEMORY_CACHE_SIZE} entries")
        logger.info(f"   Redis: {'✅ Available' if self.redis and self.redis.client else '❌ Not available'}")
        logger.info(f"   SQLite: {CacheConfig.DB_PATH}")
        logger.info(f"   JSON: {CacheConfig.JSON_PATH}")

    def get(self, query: str) -> Optional[List[Dict]]:
        """
        Get cached results for query.
        Checks all tiers in order and promotes cache hits to faster tiers.
        """
        self.total_requests += 1
        query = query.lower().strip()

        # Tier 1: Memory
        result = self.memory.get(query)
        if result:
            self.tier_hits["memory"] += 1
            return result

        # Tier 2: Redis
        if self.redis:
            result = self.redis.get(query)
            if result:
                self.tier_hits["redis"] += 1
                # Promote to memory
                self.memory.set(query, result)
                return result

        # Tier 3: SQLite
        result = self.sqlite.get(query)
        if result:
            self.tier_hits["sqlite"] += 1
            # Promote to faster tiers
            self.memory.set(query, result)
            if self.redis:
                self.redis.set(query, result)
            return result

        # Tier 4: JSON (fallback)
        result = self.json.get(query)
        if result:
            self.tier_hits["json"] += 1
            # Promote to faster tiers
            self.memory.set(query, result)
            if self.redis:
                self.redis.set(query, result)
            self.sqlite.set(query, result)
            return result

        # Cache miss
        self.tier_hits["miss"] += 1
        return None

    def set(self, query: str, results: List[Dict], ttl: int = None) -> bool:
        """
        Store results in ALL cache tiers (write-through).
        """
        query = query.lower().strip()
        ttl = ttl or CacheConfig.CACHE_TTL

        # Write to all tiers
        self.memory.set(query, results)

        if self.redis:
            self.redis.set(query, results, ttl)

        self.sqlite.set(query, results, ttl)
        self.json.set(query, results, ttl)

        return True

    def delete(self, query: str) -> bool:
        """Delete from all cache tiers."""
        query = query.lower().strip()

        # Could use memory._remove but this is cleaner
        self.memory.cache.pop(query, None)
        self.memory.timestamps.pop(query, None)

        if self.redis:
            self.redis.delete(query)

        self.sqlite.delete(query)
        self.json.delete(query)

        return True

    def clear(self) -> Dict[str, int]:
        """Clear all cache tiers."""
        return {
            "memory": self.memory.clear(),
            "redis": self.redis.clear() if self.redis else 0,
            "sqlite": self.sqlite.clear(),
            "json": self.json.clear()
        }

    def stats(self) -> Dict:
        """Get comprehensive cache statistics."""
        total = self.total_requests or 1

        return {
            "total_requests": self.total_requests,
            "hit_rate": 1 - (self.tier_hits["miss"] / total),
            "tier_hits": self.tier_hits,
            "tier_hit_rates": {
                k: v / total for k, v in self.tier_hits.items()
            },
            "tiers": {
                "memory": self.memory.stats(),
                "redis": self.redis.stats() if self.redis else {"available": False},
                "sqlite": self.sqlite.stats(),
                "json": self.json.stats()
            }
        }

    def warmup(self, queries: List[str], matcher_func) -> int:
        """
        Warm up cache with common queries.

        Args:
            queries: List of queries to pre-cache
            matcher_func: Function to call for cache misses

        Returns:
            Number of queries cached
        """
        cached = 0
        for query in queries:
            if not self.get(query):
                try:
                    results = matcher_func(query)
                    if results:
                        self.set(query, results)
                        cached += 1
                except Exception as e:
                    logger.error(f"Warmup failed for '{query}': {e}")

        logger.info(f"Cache warmup complete: {cached}/{len(queries)} queries cached")
        return cached

    def cleanup(self) -> Dict[str, int]:
        """Cleanup expired entries in persistent stores."""
        return {
            "sqlite": self.sqlite.cleanup_expired(),
            # JSON cleanup happens on read
        }


# ==============================================================================
# ASYNC WRAPPER (for FastAPI)
# ==============================================================================

class AsyncSearchCache:
    """Async wrapper for SearchCache (for use with FastAPI)."""

    def __init__(self):
        self._cache = SearchCache()
        self._lock = asyncio.Lock()

    async def get(self, query: str) -> Optional[List[Dict]]:
        """Async get from cache."""
        # Run sync cache in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._cache.get, query)

    async def set(self, query: str, results: List[Dict], ttl: int = None) -> bool:
        """Async set in cache."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._cache.set, query, results, ttl)

    async def delete(self, query: str) -> bool:
        """Async delete from cache."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._cache.delete, query)

    async def stats(self) -> Dict:
        """Async get stats."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._cache.stats)


# ==============================================================================
# SINGLETON INSTANCES
# ==============================================================================

_cache_instance: Optional[SearchCache] = None
_async_cache_instance: Optional[AsyncSearchCache] = None


def get_cache() -> SearchCache:
    """Get singleton SearchCache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SearchCache()
    return _cache_instance


def get_async_cache() -> AsyncSearchCache:
    """Get singleton AsyncSearchCache instance."""
    global _async_cache_instance
    if _async_cache_instance is None:
        _async_cache_instance = AsyncSearchCache()
    return _async_cache_instance


# ==============================================================================
# CLI TEST
# ==============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  SEARCH CACHE TEST")
    print("=" * 60)

    cache = SearchCache()

    # Test set/get
    print("\n📝 Testing set/get...")
    test_results = [
        {"slug": "food", "name": "Food", "score": 0.98, "match_type": "exact_keyword"}
    ]

    cache.set("hungry", test_results)
    result = cache.get("hungry")

    if result == test_results:
        print("✅ Set/Get working correctly")
    else:
        print("❌ Set/Get failed")

    # Test cache hierarchy
    print("\n📊 Testing cache hierarchy...")

    # Should hit memory
    result = cache.get("hungry")
    print(f"   Memory hit: {cache.tier_hits['memory'] > 0}")

    # Clear memory, should hit next tier
    cache.memory.clear()
    result = cache.get("hungry")
    tier = "redis" if cache.redis and cache.redis.client else "sqlite"
    print(f"   {tier.capitalize()} hit after memory clear: {result is not None}")

    # Stats
    print("\n📈 Cache Statistics:")
    stats = cache.stats()
    print(f"   Total requests: {stats['total_requests']}")
    print(f"   Hit rate: {stats['hit_rate']:.2%}")
    print(f"   Tier hits: {stats['tier_hits']}")

    print("\n✅ Cache test complete!")

