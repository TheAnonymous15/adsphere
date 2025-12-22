"""
Rate Limiting System for Moderation API
Prevents abuse with IP-based and API key-based throttling
Supports burst and sustained rate limits
"""

import time
import hashlib
import json
import os
from typing import Dict, Optional, Tuple
from collections import defaultdict
from threading import Lock
import redis


class RateLimiter:
    """
    Multi-tier rate limiting system
    - IP-based rate limits (burst + sustained)
    - API key quotas (daily/hourly)
    - Persistent storage (Redis or SQLite fallback)
    """

    def __init__(self, redis_url: Optional[str] = None, use_redis: bool = True):
        self.use_redis = use_redis and redis_url
        self.lock = Lock()

        # In-memory fallback
        self.ip_requests = defaultdict(list)  # IP -> [timestamp, timestamp, ...]
        self.api_key_usage = defaultdict(lambda: {'hourly': [], 'daily': 0, 'reset_time': 0})

        # Redis client
        if self.use_redis:
            try:
                self.redis = redis.from_url(redis_url, decode_responses=True)
                self.redis.ping()
                print("✓ Rate limiter using Redis backend")
            except Exception as e:
                print(f"⚠ Redis unavailable, falling back to in-memory: {e}")
                self.use_redis = False

        # Rate limit configurations
        self.IP_BURST_LIMIT = 10  # 10 requests per minute
        self.IP_BURST_WINDOW = 60  # 1 minute

        self.IP_SUSTAINED_LIMIT = 100  # 100 requests per hour
        self.IP_SUSTAINED_WINDOW = 3600  # 1 hour

        self.API_KEY_HOURLY_LIMIT = 1000  # 1000 requests per hour
        self.API_KEY_DAILY_LIMIT = 10000  # 10000 requests per day

        # Free tier (no API key)
        self.FREE_TIER_LIMIT = 50  # 50 requests per hour per IP

    def check_ip_rate_limit(self, ip_address: str) -> Tuple[bool, Optional[str]]:
        """
        Check if IP is within rate limits
        Returns: (allowed, error_message)
        """
        current_time = time.time()

        if self.use_redis:
            return self._check_ip_redis(ip_address, current_time)
        else:
            return self._check_ip_memory(ip_address, current_time)

    def _check_ip_memory(self, ip: str, current_time: float) -> Tuple[bool, Optional[str]]:
        """In-memory IP rate limit check"""
        with self.lock:
            # Clean old entries
            self.ip_requests[ip] = [
                ts for ts in self.ip_requests[ip]
                if current_time - ts < self.IP_SUSTAINED_WINDOW
            ]

            requests = self.ip_requests[ip]

            # Burst check (last 1 minute)
            burst_count = sum(1 for ts in requests if current_time - ts < self.IP_BURST_WINDOW)
            if burst_count >= self.IP_BURST_LIMIT:
                retry_after = int(self.IP_BURST_WINDOW - (current_time - requests[-self.IP_BURST_LIMIT]))
                return False, f"Rate limit exceeded: {self.IP_BURST_LIMIT} requests/minute. Retry after {retry_after}s"

            # Sustained check (last 1 hour)
            sustained_count = len(requests)
            if sustained_count >= self.IP_SUSTAINED_LIMIT:
                oldest = requests[0]
                retry_after = int(self.IP_SUSTAINED_WINDOW - (current_time - oldest))
                return False, f"Rate limit exceeded: {self.IP_SUSTAINED_LIMIT} requests/hour. Retry after {retry_after}s"

            # Record this request
            self.ip_requests[ip].append(current_time)

            return True, None

    def _check_ip_redis(self, ip: str, current_time: float) -> Tuple[bool, Optional[str]]:
        """Redis-based IP rate limit check"""
        ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16]

        # Burst window key
        burst_key = f"ratelimit:ip:{ip_hash}:burst"
        sustained_key = f"ratelimit:ip:{ip_hash}:sustained"

        try:
            # Burst check
            burst_count = self.redis.incr(burst_key)
            if burst_count == 1:
                self.redis.expire(burst_key, self.IP_BURST_WINDOW)

            if burst_count > self.IP_BURST_LIMIT:
                ttl = self.redis.ttl(burst_key)
                return False, f"Rate limit exceeded: {self.IP_BURST_LIMIT} requests/minute. Retry after {ttl}s"

            # Sustained check
            sustained_count = self.redis.incr(sustained_key)
            if sustained_count == 1:
                self.redis.expire(sustained_key, self.IP_SUSTAINED_WINDOW)

            if sustained_count > self.IP_SUSTAINED_LIMIT:
                ttl = self.redis.ttl(sustained_key)
                return False, f"Rate limit exceeded: {self.IP_SUSTAINED_LIMIT} requests/hour. Retry after {ttl}s"

            return True, None

        except Exception as e:
            print(f"⚠ Redis error in rate limiter: {e}")
            # Fail open (allow request) on Redis errors
            return True, None

    def check_api_key_quota(self, api_key: str) -> Tuple[bool, Optional[str], Dict]:
        """
        Check API key quota limits
        Returns: (allowed, error_message, usage_info)
        """
        current_time = time.time()

        if self.use_redis:
            return self._check_api_key_redis(api_key, current_time)
        else:
            return self._check_api_key_memory(api_key, current_time)

    def _check_api_key_memory(self, api_key: str, current_time: float) -> Tuple[bool, Optional[str], Dict]:
        """In-memory API key quota check"""
        with self.lock:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
            usage = self.api_key_usage[key_hash]

            # Reset daily counter if needed
            if current_time > usage['reset_time']:
                usage['daily'] = 0
                usage['reset_time'] = current_time + 86400  # 24 hours

            # Clean hourly requests
            usage['hourly'] = [
                ts for ts in usage['hourly']
                if current_time - ts < 3600
            ]

            hourly_count = len(usage['hourly'])
            daily_count = usage['daily']

            # Check limits
            if hourly_count >= self.API_KEY_HOURLY_LIMIT:
                return False, f"Hourly quota exceeded: {self.API_KEY_HOURLY_LIMIT}/hour", {
                    'hourly_used': hourly_count,
                    'hourly_limit': self.API_KEY_HOURLY_LIMIT,
                    'daily_used': daily_count,
                    'daily_limit': self.API_KEY_DAILY_LIMIT
                }

            if daily_count >= self.API_KEY_DAILY_LIMIT:
                return False, f"Daily quota exceeded: {self.API_KEY_DAILY_LIMIT}/day", {
                    'hourly_used': hourly_count,
                    'hourly_limit': self.API_KEY_HOURLY_LIMIT,
                    'daily_used': daily_count,
                    'daily_limit': self.API_KEY_DAILY_LIMIT
                }

            # Record usage
            usage['hourly'].append(current_time)
            usage['daily'] += 1

            return True, None, {
                'hourly_used': hourly_count + 1,
                'hourly_limit': self.API_KEY_HOURLY_LIMIT,
                'daily_used': daily_count + 1,
                'daily_limit': self.API_KEY_DAILY_LIMIT,
                'hourly_remaining': self.API_KEY_HOURLY_LIMIT - hourly_count - 1,
                'daily_remaining': self.API_KEY_DAILY_LIMIT - daily_count - 1
            }

    def _check_api_key_redis(self, api_key: str, current_time: float) -> Tuple[bool, Optional[str], Dict]:
        """Redis-based API key quota check"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]

        hourly_key = f"quota:api:{key_hash}:hourly"
        daily_key = f"quota:api:{key_hash}:daily"

        try:
            # Hourly quota
            hourly_count = self.redis.incr(hourly_key)
            if hourly_count == 1:
                self.redis.expire(hourly_key, 3600)

            # Daily quota
            daily_count = self.redis.incr(daily_key)
            if daily_count == 1:
                self.redis.expire(daily_key, 86400)

            # Check limits
            if hourly_count > self.API_KEY_HOURLY_LIMIT:
                return False, f"Hourly quota exceeded: {self.API_KEY_HOURLY_LIMIT}/hour", {
                    'hourly_used': hourly_count,
                    'hourly_limit': self.API_KEY_HOURLY_LIMIT,
                    'daily_used': daily_count,
                    'daily_limit': self.API_KEY_DAILY_LIMIT
                }

            if daily_count > self.API_KEY_DAILY_LIMIT:
                return False, f"Daily quota exceeded: {self.API_KEY_DAILY_LIMIT}/day", {
                    'hourly_used': hourly_count,
                    'hourly_limit': self.API_KEY_HOURLY_LIMIT,
                    'daily_used': daily_count,
                    'daily_limit': self.API_KEY_DAILY_LIMIT
                }

            return True, None, {
                'hourly_used': hourly_count,
                'hourly_limit': self.API_KEY_HOURLY_LIMIT,
                'daily_used': daily_count,
                'daily_limit': self.API_KEY_DAILY_LIMIT,
                'hourly_remaining': self.API_KEY_HOURLY_LIMIT - hourly_count,
                'daily_remaining': self.API_KEY_DAILY_LIMIT - daily_count
            }

        except Exception as e:
            print(f"⚠ Redis error in quota check: {e}")
            # Fail open on Redis errors
            return True, None, {
                'hourly_used': 0,
                'hourly_limit': self.API_KEY_HOURLY_LIMIT,
                'daily_used': 0,
                'daily_limit': self.API_KEY_DAILY_LIMIT
            }

    def check_request(self, ip_address: str, api_key: Optional[str] = None) -> Tuple[bool, Optional[str], Dict]:
        """
        Main entry point - check both IP and API key limits
        Returns: (allowed, error_message, metadata)
        """
        metadata = {}

        # Always check IP rate limit
        ip_allowed, ip_error = self.check_ip_rate_limit(ip_address)
        if not ip_allowed:
            return False, ip_error, {'type': 'ip_rate_limit'}

        # If API key provided, check quota
        if api_key:
            quota_allowed, quota_error, usage_info = self.check_api_key_quota(api_key)
            metadata.update(usage_info)
            if not quota_allowed:
                return False, quota_error, metadata
        else:
            # Free tier - stricter limits
            metadata['tier'] = 'free'

        return True, None, metadata

    def reset_ip(self, ip_address: str):
        """Admin function to reset IP rate limit"""
        if self.use_redis:
            ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()[:16]
            self.redis.delete(f"ratelimit:ip:{ip_hash}:burst")
            self.redis.delete(f"ratelimit:ip:{ip_hash}:sustained")
        else:
            with self.lock:
                if ip_address in self.ip_requests:
                    del self.ip_requests[ip_address]

    def reset_api_key(self, api_key: str):
        """Admin function to reset API key quota"""
        if self.use_redis:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
            self.redis.delete(f"quota:api:{key_hash}:hourly")
            self.redis.delete(f"quota:api:{key_hash}:daily")
        else:
            with self.lock:
                key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
                if key_hash in self.api_key_usage:
                    del self.api_key_usage[key_hash]

    def get_stats(self) -> Dict:
        """Get rate limiter statistics"""
        if self.use_redis:
            return {
                'backend': 'redis',
                'connected': True
            }
        else:
            with self.lock:
                return {
                    'backend': 'memory',
                    'tracked_ips': len(self.ip_requests),
                    'tracked_api_keys': len(self.api_key_usage)
                }


# Singleton instance
_rate_limiter_instance = None

def get_rate_limiter(redis_url: Optional[str] = None) -> RateLimiter:
    """Get or create rate limiter singleton"""
    global _rate_limiter_instance
    if _rate_limiter_instance is None:
        _rate_limiter_instance = RateLimiter(redis_url=redis_url)
    return _rate_limiter_instance

