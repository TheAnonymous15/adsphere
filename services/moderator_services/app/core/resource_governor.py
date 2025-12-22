"""
Resource Governor
Automatically balance CPU load across workers and models
Prevent resource exhaustion and optimize throughput
"""

import psutil
import time
import threading
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import deque
from enum import Enum
import json


class ResourcePriority(Enum):
    """Priority levels for resource allocation"""
    CRITICAL = 0   # Must have resources
    HIGH = 1       # High priority
    NORMAL = 2     # Normal priority
    LOW = 3        # Can be throttled
    BACKGROUND = 4 # Can be paused


@dataclass
class ResourceQuota:
    """Resource limits for a worker/service"""
    max_cpu_percent: float
    max_memory_mb: float
    max_concurrent_jobs: int
    priority: ResourcePriority


class ResourceMonitor:
    """Monitors system resource usage"""

    def __init__(self, update_interval: int = 1):
        self.update_interval = update_interval
        self.cpu_history = deque(maxlen=60)  # Last 60 readings
        self.memory_history = deque(maxlen=60)
        self.running = False
        self.thread: Optional[threading.Thread] = None

        # Current readings
        self.current_cpu_percent = 0.0
        self.current_memory_percent = 0.0
        self.current_memory_mb = 0.0
        self.cpu_count = psutil.cpu_count()

    def start(self):
        """Start monitoring"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()
            print("✓ Resource monitor started")

    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        print("✓ Resource monitor stopped")

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=self.update_interval)
                self.current_cpu_percent = cpu_percent
                self.cpu_history.append({
                    'timestamp': time.time(),
                    'value': cpu_percent
                })

                # Memory usage
                memory = psutil.virtual_memory()
                self.current_memory_percent = memory.percent
                self.current_memory_mb = memory.used / 1024 / 1024
                self.memory_history.append({
                    'timestamp': time.time(),
                    'value': memory.percent,
                    'mb': self.current_memory_mb
                })

            except Exception as e:
                print(f"⚠ Error in resource monitor: {e}")

            time.sleep(self.update_interval)

    def get_current_usage(self) -> Dict:
        """Get current resource usage"""
        return {
            'cpu_percent': self.current_cpu_percent,
            'memory_percent': self.current_memory_percent,
            'memory_mb': self.current_memory_mb,
            'cpu_count': self.cpu_count
        }

    def get_average_usage(self, window_seconds: int = 10) -> Dict:
        """Get average usage over time window"""
        cutoff_time = time.time() - window_seconds

        # CPU average
        recent_cpu = [
            r['value'] for r in self.cpu_history
            if r['timestamp'] > cutoff_time
        ]
        avg_cpu = sum(recent_cpu) / len(recent_cpu) if recent_cpu else 0

        # Memory average
        recent_memory = [
            r['value'] for r in self.memory_history
            if r['timestamp'] > cutoff_time
        ]
        avg_memory = sum(recent_memory) / len(recent_memory) if recent_memory else 0

        return {
            'avg_cpu_percent': avg_cpu,
            'avg_memory_percent': avg_memory,
            'window_seconds': window_seconds
        }

    def is_under_pressure(self,
                         cpu_threshold: float = 80.0,
                         memory_threshold: float = 85.0) -> bool:
        """Check if system is under resource pressure"""
        usage = self.get_current_usage()
        return (
            usage['cpu_percent'] > cpu_threshold or
            usage['memory_percent'] > memory_threshold
        )


class WorkerResourceTracker:
    """Tracks resource usage for individual workers"""

    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.current_jobs = 0
        self.cpu_usage = 0.0
        self.memory_mb = 0.0
        self.last_update = time.time()

        # Quotas
        self.quota = ResourceQuota(
            max_cpu_percent=25.0,  # Per worker
            max_memory_mb=1024.0,
            max_concurrent_jobs=5,
            priority=ResourcePriority.NORMAL
        )

    def update_usage(self, cpu_percent: float, memory_mb: float):
        """Update resource usage"""
        self.cpu_usage = cpu_percent
        self.memory_mb = memory_mb
        self.last_update = time.time()

    def is_available(self) -> bool:
        """Check if worker can accept more jobs"""
        return (
            self.current_jobs < self.quota.max_concurrent_jobs and
            self.cpu_usage < self.quota.max_cpu_percent and
            self.memory_mb < self.quota.max_memory_mb
        )

    def get_capacity(self) -> float:
        """Get available capacity (0-1)"""
        job_capacity = 1 - (self.current_jobs / self.quota.max_concurrent_jobs)
        cpu_capacity = 1 - (self.cpu_usage / self.quota.max_cpu_percent)
        memory_capacity = 1 - (self.memory_mb / self.quota.max_memory_mb)

        return min(job_capacity, cpu_capacity, memory_capacity)


class ResourceGovernor:
    """
    Automatically balances CPU load across workers
    Implements adaptive throttling and load shedding
    """

    def __init__(self,
                 cpu_target: float = 70.0,
                 memory_target: float = 75.0,
                 check_interval: int = 5):
        """
        Args:
            cpu_target: Target CPU usage percentage
            memory_target: Target memory usage percentage
            check_interval: Seconds between resource checks
        """
        self.cpu_target = cpu_target
        self.memory_target = memory_target
        self.check_interval = check_interval

        self.monitor = ResourceMonitor()
        self.workers: Dict[str, WorkerResourceTracker] = {}
        self.lock = threading.Lock()

        # Throttling state
        self.throttle_level = 0  # 0 = no throttle, 1 = max throttle
        self.load_shedding_active = False

        # Statistics
        self.total_throttles = 0
        self.total_load_sheds = 0
        self.throttle_history = deque(maxlen=100)

        # Control thread
        self.running = False
        self.control_thread: Optional[threading.Thread] = None

    def start(self):
        """Start resource governor"""
        self.monitor.start()
        self.running = True
        self.control_thread = threading.Thread(target=self._control_loop, daemon=True)
        self.control_thread.start()
        print("✓ Resource governor started")

    def stop(self):
        """Stop resource governor"""
        self.running = False
        self.monitor.stop()
        if self.control_thread:
            self.control_thread.join(timeout=2)
        print("✓ Resource governor stopped")

    def register_worker(self,
                       worker_id: str,
                       quota: Optional[ResourceQuota] = None) -> WorkerResourceTracker:
        """Register a worker for resource tracking"""
        with self.lock:
            tracker = WorkerResourceTracker(worker_id)
            if quota:
                tracker.quota = quota

            self.workers[worker_id] = tracker
            print(f"✓ Registered worker {worker_id} for resource governance")

            return tracker

    def unregister_worker(self, worker_id: str):
        """Unregister a worker"""
        with self.lock:
            if worker_id in self.workers:
                del self.workers[worker_id]

    def update_worker_usage(self, worker_id: str, cpu_percent: float, memory_mb: float):
        """Update worker resource usage"""
        with self.lock:
            if worker_id in self.workers:
                self.workers[worker_id].update_usage(cpu_percent, memory_mb)

    def _control_loop(self):
        """Main control loop for resource management"""
        while self.running:
            try:
                self._adjust_throttling()
            except Exception as e:
                print(f"⚠ Error in resource governor: {e}")

            time.sleep(self.check_interval)

    def _adjust_throttling(self):
        """Adjust throttling based on resource usage"""
        usage = self.monitor.get_current_usage()
        avg_usage = self.monitor.get_average_usage(window_seconds=30)

        cpu_percent = avg_usage['avg_cpu_percent']
        memory_percent = avg_usage['avg_memory_percent']

        old_throttle = self.throttle_level

        # Calculate desired throttle level
        if cpu_percent > self.cpu_target or memory_percent > self.memory_target:
            # Increase throttle
            cpu_overage = max(0, cpu_percent - self.cpu_target) / 100
            memory_overage = max(0, memory_percent - self.memory_target) / 100

            self.throttle_level = min(1.0, max(cpu_overage, memory_overage))

            # Enable load shedding if critical
            if cpu_percent > 90 or memory_percent > 90:
                self.load_shedding_active = True
                self.total_load_sheds += 1
        else:
            # Decrease throttle
            self.throttle_level = max(0, self.throttle_level - 0.1)
            self.load_shedding_active = False

        # Record throttle change
        if old_throttle != self.throttle_level:
            self.throttle_history.append({
                'timestamp': time.time(),
                'old_level': old_throttle,
                'new_level': self.throttle_level,
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent
            })

            if self.throttle_level > 0:
                self.total_throttles += 1
                print(f"⚡ Throttle adjusted: {old_throttle:.2f} → {self.throttle_level:.2f} "
                      f"(CPU: {cpu_percent:.1f}%, Mem: {memory_percent:.1f}%)")

    def can_accept_job(self, priority: ResourcePriority = ResourcePriority.NORMAL) -> bool:
        """
        Check if system can accept a new job

        Args:
            priority: Job priority level

        Returns:
            True if job can be accepted
        """
        # Critical jobs always accepted
        if priority == ResourcePriority.CRITICAL:
            return True

        # Load shedding - only accept critical
        if self.load_shedding_active:
            return False

        # Check throttle level vs priority
        if priority == ResourcePriority.HIGH:
            return self.throttle_level < 0.8
        elif priority == ResourcePriority.NORMAL:
            return self.throttle_level < 0.5
        elif priority == ResourcePriority.LOW:
            return self.throttle_level < 0.3
        else:  # BACKGROUND
            return self.throttle_level == 0

    def get_best_worker(self,
                       exclude: Optional[List[str]] = None) -> Optional[str]:
        """
        Get best available worker for a new job

        Args:
            exclude: Workers to exclude from selection

        Returns:
            Worker ID or None if no worker available
        """
        with self.lock:
            exclude = exclude or []

            # Get available workers
            available = [
                (worker_id, tracker)
                for worker_id, tracker in self.workers.items()
                if worker_id not in exclude and tracker.is_available()
            ]

            if not available:
                return None

            # Sort by capacity (highest first)
            available.sort(key=lambda x: x[1].get_capacity(), reverse=True)

            # Return best worker
            return available[0][0]

    def allocate_worker(self,
                       priority: ResourcePriority = ResourcePriority.NORMAL) -> Optional[Tuple[str, bool]]:
        """
        Allocate a worker for a job

        Returns:
            Tuple of (worker_id, should_throttle) or None if no worker available
        """
        if not self.can_accept_job(priority):
            return None

        worker_id = self.get_best_worker()
        if not worker_id:
            return None

        # Update job count
        with self.lock:
            self.workers[worker_id].current_jobs += 1

        # Determine if job should be throttled
        should_throttle = self.throttle_level > 0.3

        return (worker_id, should_throttle)

    def release_worker(self, worker_id: str):
        """Release a worker after job completion"""
        with self.lock:
            if worker_id in self.workers:
                self.workers[worker_id].current_jobs = max(
                    0,
                    self.workers[worker_id].current_jobs - 1
                )

    def get_stats(self) -> Dict:
        """Get resource governor statistics"""
        with self.lock:
            usage = self.monitor.get_current_usage()
            avg_usage = self.monitor.get_average_usage()

            return {
                'current_usage': usage,
                'average_usage': avg_usage,
                'throttle_level': self.throttle_level,
                'load_shedding_active': self.load_shedding_active,
                'total_workers': len(self.workers),
                'available_workers': sum(1 for w in self.workers.values() if w.is_available()),
                'total_active_jobs': sum(w.current_jobs for w in self.workers.values()),
                'total_throttles': self.total_throttles,
                'total_load_sheds': self.total_load_sheds,
                'recent_throttles': list(self.throttle_history)[-5:] if self.throttle_history else []
            }

    def get_worker_stats(self) -> Dict:
        """Get per-worker statistics"""
        with self.lock:
            return {
                worker_id: {
                    'current_jobs': tracker.current_jobs,
                    'cpu_usage': tracker.cpu_usage,
                    'memory_mb': tracker.memory_mb,
                    'capacity': tracker.get_capacity(),
                    'available': tracker.is_available(),
                    'priority': tracker.quota.priority.name
                }
                for worker_id, tracker in self.workers.items()
            }


# Singleton instance
_resource_governor = None

def get_resource_governor() -> ResourceGovernor:
    """Get global resource governor"""
    global _resource_governor
    if _resource_governor is None:
        _resource_governor = ResourceGovernor()
    return _resource_governor


if __name__ == '__main__':
    # Test resource governor
    import random

    governor = ResourceGovernor(
        cpu_target=70.0,
        memory_target=75.0,
        check_interval=2
    )

    governor.start()

    # Register some workers
    for i in range(4):
        governor.register_worker(
            f"worker-{i+1}",
            ResourceQuota(
                max_cpu_percent=25.0,
                max_memory_mb=1024.0,
                max_concurrent_jobs=5,
                priority=ResourcePriority.NORMAL
            )
        )

    print("\nSimulating workload...\n")

    # Simulate workload
    for i in range(20):
        # Try to allocate worker
        result = governor.allocate_worker(ResourcePriority.NORMAL)

        if result:
            worker_id, should_throttle = result
            throttle_msg = " (throttled)" if should_throttle else ""
            print(f"Job {i+1}: Allocated to {worker_id}{throttle_msg}")

            # Simulate worker usage
            cpu = random.uniform(10, 30)
            memory = random.uniform(200, 500)
            governor.update_worker_usage(worker_id, cpu, memory)

            # Release after "processing"
            time.sleep(0.5)
            governor.release_worker(worker_id)
        else:
            print(f"Job {i+1}: ❌ No worker available (load shedding or throttled)")

        # Show stats every 5 jobs
        if (i + 1) % 5 == 0:
            stats = governor.get_stats()
            print(f"\n📊 System Stats:")
            print(f"   CPU: {stats['current_usage']['cpu_percent']:.1f}%")
            print(f"   Memory: {stats['current_usage']['memory_percent']:.1f}%")
            print(f"   Throttle: {stats['throttle_level']:.2f}")
            print(f"   Load Shedding: {stats['load_shedding_active']}")
            print(f"   Active Jobs: {stats['total_active_jobs']}\n")

        time.sleep(0.5)

    print("\n" + "="*60)
    print("Final Statistics:")
    print(json.dumps(governor.get_stats(), indent=2, default=str))

    governor.stop()

