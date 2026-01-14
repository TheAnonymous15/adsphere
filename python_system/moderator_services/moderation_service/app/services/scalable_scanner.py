"""
Scalable Realtime Ad Scanner
=============================

High-performance, scalable ad scanner designed to handle millions of ads.

Features:
- Async/concurrent processing with configurable worker pools
- Redis-based distributed caching (with in-memory fallback)
- Batch processing for database efficiency
- Circuit breaker pattern for resilience
- Rate limiting and backpressure
- Metrics and monitoring
- Database connection pooling
- Priority queue for urgent scans

Architecture:
    ┌─────────────────┐
    │  Scanner API    │
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │  Work Queue     │ ← Priority-based (urgent, normal, low)
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │  Worker Pool    │ ← Configurable (default: CPU count)
    │  (Async)        │
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │  Batch Loader   │ ← Efficient DB/file reads
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │  Moderation     │
    │  Pipeline       │
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │  Result Cache   │ ← Redis or In-Memory
    └─────────────────┘
"""

import asyncio
import hashlib
import json
import os
import sqlite3
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import threading

# Try to import Redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class ScannerConfig:
    """Configuration for the realtime scanner"""
    # Worker pool settings
    max_workers: int = 8  # Concurrent workers
    batch_size: int = 50  # Ads per batch
    queue_max_size: int = 10000  # Max pending jobs

    # Cache settings
    cache_backend: str = "memory"  # "redis" or "memory"
    cache_ttl_seconds: int = 86400  # 24 hours
    cache_max_size: int = 100000  # Max cached results (memory only)

    # Redis settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 1
    redis_password: Optional[str] = None

    # Rate limiting
    max_requests_per_second: int = 100
    max_concurrent_scans: int = 1000

    # Circuit breaker
    circuit_breaker_threshold: int = 10  # Failures before opening
    circuit_breaker_timeout: int = 60  # Seconds to wait before retry

    # Database
    db_pool_size: int = 5
    db_path: str = ""

    # Timeouts
    scan_timeout_seconds: int = 30
    batch_timeout_seconds: int = 120


# =============================================================================
# PRIORITY QUEUE
# =============================================================================

class ScanPriority(Enum):
    URGENT = 0  # Report/complaint triggered
    HIGH = 1    # New ad
    NORMAL = 2  # Periodic rescan
    LOW = 3     # Background scan


@dataclass(order=True)
class ScanJob:
    """A scan job in the queue"""
    priority: int
    ad_id: str = field(compare=False)
    ad_data: Dict = field(compare=False, default_factory=dict)
    created_at: float = field(compare=False, default_factory=time.time)
    retries: int = field(compare=False, default=0)
    callback: Optional[Callable] = field(compare=False, default=None)


# =============================================================================
# CACHE BACKENDS
# =============================================================================

class CacheBackend:
    """Abstract cache backend"""

    async def get(self, key: str) -> Optional[Dict]:
        raise NotImplementedError

    async def set(self, key: str, value: Dict, ttl: int = None) -> bool:
        raise NotImplementedError

    async def delete(self, key: str) -> bool:
        raise NotImplementedError

    async def exists(self, key: str) -> bool:
        raise NotImplementedError

    async def clear(self) -> int:
        raise NotImplementedError

    async def stats(self) -> Dict:
        raise NotImplementedError


class MemoryCache(CacheBackend):
    """In-memory LRU cache with TTL"""

    def __init__(self, max_size: int = 100000, default_ttl: int = 86400):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, Tuple[Dict, float]] = {}
        self._access_order: deque = deque()
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0

    async def get(self, key: str) -> Optional[Dict]:
        async with self._lock:
            if key in self._cache:
                value, expires_at = self._cache[key]
                if time.time() < expires_at:
                    self._hits += 1
                    # Move to end (most recently used)
                    if key in self._access_order:
                        self._access_order.remove(key)
                    self._access_order.append(key)
                    return value
                else:
                    # Expired
                    del self._cache[key]
            self._misses += 1
            return None

    async def set(self, key: str, value: Dict, ttl: int = None) -> bool:
        async with self._lock:
            # Evict if at capacity
            while len(self._cache) >= self.max_size:
                if self._access_order:
                    oldest = self._access_order.popleft()
                    self._cache.pop(oldest, None)
                else:
                    break

            expires_at = time.time() + (ttl or self.default_ttl)
            self._cache[key] = (value, expires_at)

            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            return True

    async def delete(self, key: str) -> bool:
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                return True
            return False

    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None

    async def clear(self) -> int:
        async with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._access_order.clear()
            return count

    async def stats(self) -> Dict:
        async with self._lock:
            total = self._hits + self._misses
            return {
                "backend": "memory",
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": self._hits / total if total > 0 else 0,
            }


class RedisCache(CacheBackend):
    """Redis-based distributed cache"""

    def __init__(self, config: ScannerConfig):
        self.config = config
        self._client = None
        self._prefix = "scanner:"
        self._connected = False

    def _get_client(self):
        if self._client is None:
            self._client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                password=self.config.redis_password,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
            )
            try:
                self._client.ping()
                self._connected = True
            except:
                self._connected = False
        return self._client

    async def get(self, key: str) -> Optional[Dict]:
        try:
            client = self._get_client()
            data = client.get(f"{self._prefix}{key}")
            if data:
                return json.loads(data)
        except Exception as e:
            pass
        return None

    async def set(self, key: str, value: Dict, ttl: int = None) -> bool:
        try:
            client = self._get_client()
            ttl = ttl or self.config.cache_ttl_seconds
            return client.setex(
                f"{self._prefix}{key}",
                ttl,
                json.dumps(value)
            )
        except:
            return False

    async def delete(self, key: str) -> bool:
        try:
            client = self._get_client()
            return client.delete(f"{self._prefix}{key}") > 0
        except:
            return False

    async def exists(self, key: str) -> bool:
        try:
            client = self._get_client()
            return client.exists(f"{self._prefix}{key}") > 0
        except:
            return False

    async def clear(self) -> int:
        try:
            client = self._get_client()
            keys = client.keys(f"{self._prefix}*")
            if keys:
                return client.delete(*keys)
        except:
            pass
        return 0

    async def stats(self) -> Dict:
        try:
            client = self._get_client()
            info = client.info("stats")
            return {
                "backend": "redis",
                "connected": self._connected,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
            }
        except:
            return {"backend": "redis", "connected": False}


# =============================================================================
# CIRCUIT BREAKER
# =============================================================================

class CircuitBreaker:
    """Circuit breaker for resilience"""

    def __init__(self, threshold: int = 10, timeout: int = 60):
        self.threshold = threshold
        self.timeout = timeout
        self._failures = 0
        self._last_failure = 0
        self._state = "closed"  # closed, open, half-open
        self._lock = threading.Lock()

    def can_execute(self) -> bool:
        with self._lock:
            if self._state == "closed":
                return True
            elif self._state == "open":
                if time.time() - self._last_failure > self.timeout:
                    self._state = "half-open"
                    return True
                return False
            else:  # half-open
                return True

    def record_success(self):
        with self._lock:
            self._failures = 0
            self._state = "closed"

    def record_failure(self):
        with self._lock:
            self._failures += 1
            self._last_failure = time.time()
            if self._failures >= self.threshold:
                self._state = "open"

    @property
    def state(self) -> str:
        return self._state


# =============================================================================
# RATE LIMITER
# =============================================================================

class RateLimiter:
    """Token bucket rate limiter"""

    def __init__(self, rate: int = 100, burst: int = 200):
        self.rate = rate  # Tokens per second
        self.burst = burst  # Max tokens
        self._tokens = burst
        self._last_update = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> bool:
        async with self._lock:
            now = time.time()
            elapsed = now - self._last_update
            self._tokens = min(self.burst, self._tokens + elapsed * self.rate)
            self._last_update = now

            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    async def wait(self, tokens: int = 1):
        while not await self.acquire(tokens):
            await asyncio.sleep(0.01)


# =============================================================================
# METRICS COLLECTOR
# =============================================================================

@dataclass
class ScannerMetrics:
    """Metrics for monitoring"""
    total_scans: int = 0
    successful_scans: int = 0
    failed_scans: int = 0
    total_flagged: int = 0
    total_blocked: int = 0

    # Timing
    total_scan_time_ms: float = 0
    avg_scan_time_ms: float = 0
    min_scan_time_ms: float = float('inf')
    max_scan_time_ms: float = 0

    # Throughput
    scans_per_second: float = 0
    peak_scans_per_second: float = 0

    # Queue
    queue_size: int = 0
    queue_peak: int = 0

    # Cache
    cache_hits: int = 0
    cache_misses: int = 0

    # Errors
    errors: List[str] = field(default_factory=list)

    # Timestamps
    started_at: Optional[str] = None
    last_scan_at: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "total_scans": self.total_scans,
            "successful_scans": self.successful_scans,
            "failed_scans": self.failed_scans,
            "total_flagged": self.total_flagged,
            "total_blocked": self.total_blocked,
            "timing": {
                "total_ms": self.total_scan_time_ms,
                "avg_ms": self.avg_scan_time_ms,
                "min_ms": self.min_scan_time_ms if self.min_scan_time_ms != float('inf') else 0,
                "max_ms": self.max_scan_time_ms,
            },
            "throughput": {
                "current_per_second": self.scans_per_second,
                "peak_per_second": self.peak_scans_per_second,
            },
            "queue": {
                "current_size": self.queue_size,
                "peak_size": self.queue_peak,
            },
            "cache": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0,
            },
            "errors_count": len(self.errors),
            "recent_errors": self.errors[-10:],  # Last 10 errors
            "started_at": self.started_at,
            "last_scan_at": self.last_scan_at,
        }


# =============================================================================
# SCALABLE REALTIME SCANNER
# =============================================================================

class ScalableRealtimeScanner:
    """
    High-performance, scalable ad scanner.

    Usage:
        scanner = ScalableRealtimeScanner(config)
        await scanner.start()

        # Scan ads
        result = await scanner.scan_ads(mode="incremental", limit=100)

        # Or add to queue for async processing
        await scanner.enqueue(ad_id="AD-123", priority=ScanPriority.HIGH)

        await scanner.stop()
    """

    def __init__(self, config: ScannerConfig = None, pipeline=None):
        self.config = config or ScannerConfig()
        self.pipeline = pipeline

        # Components
        self.cache: CacheBackend = None
        self.rate_limiter = RateLimiter(
            rate=self.config.max_requests_per_second,
            burst=self.config.max_requests_per_second * 2
        )
        self.circuit_breaker = CircuitBreaker(
            threshold=self.config.circuit_breaker_threshold,
            timeout=self.config.circuit_breaker_timeout
        )
        self.metrics = ScannerMetrics()

        # Work queue
        self._queue: asyncio.PriorityQueue = None
        self._workers: List[asyncio.Task] = []
        self._running = False
        self._shutdown_event: asyncio.Event = None

        # Thread pool for CPU-bound tasks
        self._thread_pool: ThreadPoolExecutor = None

        # Database connection pool
        self._db_pool: List[sqlite3.Connection] = []
        self._db_lock = asyncio.Lock()

        # Active scans tracking
        self._active_scans: Set[str] = set()
        self._active_lock = asyncio.Lock()

    async def start(self):
        """Start the scanner workers"""
        if self._running:
            return

        self._running = True
        self._shutdown_event = asyncio.Event()
        self._queue = asyncio.PriorityQueue(maxsize=self.config.queue_max_size)

        # Initialize cache
        if self.config.cache_backend == "redis" and REDIS_AVAILABLE:
            self.cache = RedisCache(self.config)
        else:
            self.cache = MemoryCache(
                max_size=self.config.cache_max_size,
                default_ttl=self.config.cache_ttl_seconds
            )

        # Initialize thread pool
        self._thread_pool = ThreadPoolExecutor(max_workers=self.config.max_workers)

        # Initialize database pool
        await self._init_db_pool()

        # Start workers
        for i in range(self.config.max_workers):
            worker = asyncio.create_task(self._worker(i))
            self._workers.append(worker)

        self.metrics.started_at = datetime.utcnow().isoformat()
        print(f"[Scanner] Started with {self.config.max_workers} workers")

    async def stop(self):
        """Gracefully stop the scanner"""
        if not self._running:
            return

        self._running = False
        self._shutdown_event.set()

        # Wait for workers to finish
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)

        # Close thread pool
        if self._thread_pool:
            self._thread_pool.shutdown(wait=True)

        # Close database connections
        for conn in self._db_pool:
            try:
                conn.close()
            except:
                pass

        print("[Scanner] Stopped")

    async def _init_db_pool(self):
        """Initialize database connection pool"""
        if not self.config.db_path:
            # Try to find the database within python_system
            possible_paths = [
                Path(__file__).parent.parent.parent.parent.parent.parent / "python_shared" / "database" / "adsphere.db",
                Path(__file__).parent.parent.parent.parent.parent.parent / "database" / "adsphere.db",
            ]
            for path in possible_paths:
                if path.exists():
                    self.config.db_path = str(path)
                    break

        if self.config.db_path and Path(self.config.db_path).exists():
            for _ in range(self.config.db_pool_size):
                try:
                    conn = sqlite3.connect(
                        self.config.db_path,
                        check_same_thread=False,
                        timeout=10
                    )
                    conn.row_factory = sqlite3.Row
                    self._db_pool.append(conn)
                except Exception as e:
                    print(f"[Scanner] Failed to create DB connection: {e}")

    async def _get_db_connection(self) -> Optional[sqlite3.Connection]:
        """Get a connection from the pool"""
        async with self._db_lock:
            if self._db_pool:
                return self._db_pool.pop()
        return None

    async def _return_db_connection(self, conn: sqlite3.Connection):
        """Return a connection to the pool"""
        async with self._db_lock:
            self._db_pool.append(conn)

    async def _worker(self, worker_id: int):
        """Worker coroutine that processes scan jobs"""
        print(f"[Scanner] Worker {worker_id} started")

        while self._running:
            try:
                # Wait for a job with timeout
                try:
                    job = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # Check circuit breaker
                if not self.circuit_breaker.can_execute():
                    # Re-queue the job
                    await self._queue.put(job)
                    await asyncio.sleep(1)
                    continue

                # Rate limit
                await self.rate_limiter.wait()

                # Process the job
                try:
                    start_time = time.time()
                    result = await self._process_job(job)
                    elapsed_ms = (time.time() - start_time) * 1000

                    # Update metrics
                    self._update_metrics(elapsed_ms, result)
                    self.circuit_breaker.record_success()

                    # Execute callback if provided
                    if job.callback:
                        try:
                            job.callback(result)
                        except:
                            pass

                except Exception as e:
                    self.circuit_breaker.record_failure()
                    self.metrics.failed_scans += 1
                    self.metrics.errors.append(f"Worker {worker_id}: {str(e)}")

                    # Retry logic
                    if job.retries < 3:
                        job.retries += 1
                        job.priority += 1  # Lower priority on retry
                        await self._queue.put(job)

                finally:
                    self._queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[Scanner] Worker {worker_id} error: {e}")

        print(f"[Scanner] Worker {worker_id} stopped")

    async def _process_job(self, job: ScanJob) -> Dict:
        """Process a single scan job"""
        ad_id = job.ad_id
        ad_data = job.ad_data

        # Check if already being scanned
        async with self._active_lock:
            if ad_id in self._active_scans:
                return {"skipped": True, "reason": "already_scanning"}
            self._active_scans.add(ad_id)

        try:
            # Check cache first
            cache_key = f"scan:{ad_id}"
            cached = await self.cache.get(cache_key)
            if cached:
                self.metrics.cache_hits += 1
                return cached

            self.metrics.cache_misses += 1

            # Perform scan
            if self.pipeline:
                result = await self._scan_with_pipeline(ad_data)
            else:
                result = await self._scan_basic(ad_data)

            # Cache result
            await self.cache.set(cache_key, result)

            return result

        finally:
            async with self._active_lock:
                self._active_scans.discard(ad_id)

    async def _scan_with_pipeline(self, ad: Dict) -> Dict:
        """Scan using the moderation pipeline"""
        title = ad.get('title', '')
        description = ad.get('description', '')
        category = ad.get('category', 'general')

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self._thread_pool,
            lambda: self.pipeline.moderate_text(
                title=title,
                description=description,
                category=category,
                user_context={
                    'ad_id': ad.get('id', ad.get('ad_id')),
                    'source': 'scalable_scanner'
                }
            )
        )
        return result

    async def _scan_basic(self, ad: Dict) -> Dict:
        """Basic scan without full pipeline (fallback)"""
        title = ad.get('title', '')
        description = ad.get('description', '')
        text = f"{title} {description}".lower()

        # Simple keyword check
        dangerous_keywords = {
            'weapons', 'drugs', 'illegal', 'kill', 'murder', 'bomb',
            'terrorist', 'child porn', 'exploit', 'fraud', 'scam'
        }

        flags = []
        for keyword in dangerous_keywords:
            if keyword in text:
                flags.append(keyword)

        decision = 'approve'
        risk_level = 'low'

        if len(flags) >= 3:
            decision = 'block'
            risk_level = 'critical'
        elif len(flags) >= 1:
            decision = 'review'
            risk_level = 'high'

        return {
            'decision': decision,
            'risk_level': risk_level,
            'flags': flags,
            'reasons': [f"Contains keyword: {f}" for f in flags],
            'global_score': len(flags) * 0.3,
        }

    def _update_metrics(self, elapsed_ms: float, result: Dict):
        """Update scanner metrics"""
        self.metrics.total_scans += 1
        self.metrics.successful_scans += 1
        self.metrics.total_scan_time_ms += elapsed_ms
        self.metrics.avg_scan_time_ms = self.metrics.total_scan_time_ms / self.metrics.total_scans
        self.metrics.min_scan_time_ms = min(self.metrics.min_scan_time_ms, elapsed_ms)
        self.metrics.max_scan_time_ms = max(self.metrics.max_scan_time_ms, elapsed_ms)
        self.metrics.last_scan_at = datetime.utcnow().isoformat()

        if result.get('decision') == 'block':
            self.metrics.total_blocked += 1
            self.metrics.total_flagged += 1
        elif result.get('decision') == 'review' or result.get('flags'):
            self.metrics.total_flagged += 1

        # Update queue metrics
        self.metrics.queue_size = self._queue.qsize() if self._queue else 0
        self.metrics.queue_peak = max(self.metrics.queue_peak, self.metrics.queue_size)

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    async def enqueue(
        self,
        ad_id: str,
        ad_data: Dict = None,
        priority: ScanPriority = ScanPriority.NORMAL,
        callback: Callable = None
    ) -> bool:
        """Add an ad to the scan queue"""
        if not self._running:
            return False

        try:
            job = ScanJob(
                priority=priority.value,
                ad_id=ad_id,
                ad_data=ad_data or {},
                callback=callback
            )
            await self._queue.put(job)
            return True
        except asyncio.QueueFull:
            return False

    async def scan_single(self, ad_id: str, ad_data: Dict = None) -> Dict:
        """Scan a single ad immediately (bypass queue)"""
        if not ad_data:
            # Try to load from database
            ad_data = await self._load_ad_by_id(ad_id)

        if not ad_data:
            return {"error": "Ad not found"}

        job = ScanJob(
            priority=ScanPriority.URGENT.value,
            ad_id=ad_id,
            ad_data=ad_data
        )

        return await self._process_job(job)

    async def scan_batch(
        self,
        mode: str = "incremental",
        limit: int = 100,
        company_id: str = None,
        category: str = None,
        skip_cached: bool = True
    ) -> Dict:
        """Scan a batch of ads"""
        start_time = time.time()

        # Load ads
        ads = await self._load_ads(
            mode=mode,
            limit=limit,
            company_id=company_id,
            category=category
        )

        results = []
        flagged = []
        blocked = []
        cache_hits = 0
        cache_misses = 0
        errors = []

        # Process in batches
        batch_size = self.config.batch_size
        for i in range(0, len(ads), batch_size):
            batch = ads[i:i + batch_size]

            # Process batch concurrently
            tasks = []
            for ad in batch:
                ad_id = ad.get('id', ad.get('ad_id', ''))

                # Check cache if skip_cached
                if skip_cached:
                    cached = await self.cache.get(f"scan:{ad_id}")
                    if cached:
                        cache_hits += 1
                        results.append(cached)
                        if cached.get('decision') == 'block':
                            blocked.append(cached)
                            flagged.append(cached)
                        elif cached.get('decision') == 'review':
                            flagged.append(cached)
                        continue

                cache_misses += 1
                tasks.append(self._scan_ad(ad))

            # Wait for batch with timeout
            if tasks:
                try:
                    batch_results = await asyncio.wait_for(
                        asyncio.gather(*tasks, return_exceptions=True),
                        timeout=self.config.batch_timeout_seconds
                    )

                    for j, result in enumerate(batch_results):
                        if isinstance(result, Exception):
                            errors.append(str(result))
                            continue

                        ad_id = batch[j + (len(batch) - len(tasks))].get('id', '')
                        result['ad_id'] = ad_id
                        results.append(result)

                        # Cache
                        await self.cache.set(f"scan:{ad_id}", result)

                        # Categorize
                        if result.get('decision') == 'block':
                            blocked.append(result)
                            flagged.append(result)
                        elif result.get('decision') == 'review' or result.get('flags'):
                            flagged.append(result)

                except asyncio.TimeoutError:
                    errors.append(f"Batch {i//batch_size} timed out")

        elapsed_ms = (time.time() - start_time) * 1000

        return {
            "success": True,
            "mode": mode,
            "total_ads_scanned": len(results),
            "clean_ads": len(results) - len(flagged),
            "flagged_ads": len(flagged),
            "blocked_ads": len(blocked),
            "results": results[:100],  # Limit response size
            "flagged_details": flagged,
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "scan_time_ms": round(elapsed_ms, 2),
            "ads_per_second": round(len(results) / (elapsed_ms / 1000), 2) if elapsed_ms > 0 else 0,
            "errors": errors,
            "last_scan_timestamp": datetime.utcnow().isoformat(),
        }

    async def _scan_ad(self, ad: Dict) -> Dict:
        """Scan a single ad"""
        if self.pipeline:
            return await self._scan_with_pipeline(ad)
        return await self._scan_basic(ad)

    async def _load_ad_by_id(self, ad_id: str) -> Optional[Dict]:
        """Load a single ad by ID"""
        conn = await self._get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM ads WHERE id = ? OR ad_id = ?",
                    (ad_id, ad_id)
                )
                row = cursor.fetchone()
                if row:
                    return dict(row)
            finally:
                await self._return_db_connection(conn)
        return None

    async def _load_ads(
        self,
        mode: str,
        limit: int,
        company_id: str = None,
        category: str = None
    ) -> List[Dict]:
        """Load ads from database/filesystem"""
        ads = []

        # Try database first
        conn = await self._get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()

                query = "SELECT * FROM ads WHERE status = 'active'"
                params = []

                if company_id:
                    query += " AND company_id = ?"
                    params.append(company_id)
                if category:
                    query += " AND category = ?"
                    params.append(category)

                query += f" ORDER BY created_at DESC LIMIT {limit}"

                cursor.execute(query, params)

                for row in cursor.fetchall():
                    ads.append(dict(row))

            except Exception as e:
                print(f"[Scanner] DB error: {e}")
            finally:
                await self._return_db_connection(conn)

        # Fallback to filesystem
        if not ads:
            ads = await self._load_ads_from_files(limit, company_id, category)

        return ads

    async def _load_ads_from_files(
        self,
        limit: int,
        company_id: str = None,
        category: str = None
    ) -> List[Dict]:
        """Load ads from filesystem (fallback)"""
        ads = []

        base_paths = [
            Path(__file__).parent.parent.parent.parent.parent.parent / "python_shared" / "data" / "companies",
            Path(__file__).parent.parent.parent.parent.parent.parent / "data" / "companies",
        ]

        for base_path in base_paths:
            if not base_path.exists():
                continue

            for meta_file in base_path.rglob("*/ads/*/meta.json"):
                if len(ads) >= limit:
                    break

                try:
                    with open(meta_file, 'r') as f:
                        ad_data = json.load(f)

                        if company_id and ad_data.get('company') != company_id:
                            continue
                        if category and ad_data.get('category') != category:
                            continue

                        ads.append(ad_data)
                except:
                    pass

            if ads:
                break

        return ads

    def get_metrics(self) -> Dict:
        """Get current scanner metrics"""
        return self.metrics.to_dict()

    async def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return await self.cache.stats()

    def get_status(self) -> Dict:
        """Get scanner status"""
        return {
            "running": self._running,
            "workers": len(self._workers),
            "queue_size": self._queue.qsize() if self._queue else 0,
            "active_scans": len(self._active_scans),
            "circuit_breaker": self.circuit_breaker.state,
            "config": {
                "max_workers": self.config.max_workers,
                "batch_size": self.config.batch_size,
                "cache_backend": self.config.cache_backend,
            }
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_scanner_instance: Optional[ScalableRealtimeScanner] = None
_scanner_lock = asyncio.Lock()


async def get_scanner(pipeline=None) -> ScalableRealtimeScanner:
    """Get or create the scanner singleton"""
    global _scanner_instance

    async with _scanner_lock:
        if _scanner_instance is None:
            config = ScannerConfig(
                max_workers=os.cpu_count() or 4,
                batch_size=50,
                cache_backend="redis" if REDIS_AVAILABLE else "memory",
            )
            _scanner_instance = ScalableRealtimeScanner(config, pipeline)
            await _scanner_instance.start()

        return _scanner_instance


async def shutdown_scanner():
    """Shutdown the scanner"""
    global _scanner_instance

    if _scanner_instance:
        await _scanner_instance.stop()
        _scanner_instance = None

