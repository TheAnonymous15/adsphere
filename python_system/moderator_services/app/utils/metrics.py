"""
Enhanced Prometheus Metrics Exporter
Comprehensive monitoring with counters, histograms, and gauges
Full Prometheus compatibility with advanced metrics
"""

import time
import psutil
import os
from typing import Dict, List, Optional
from collections import defaultdict, deque
from threading import Lock
import json
import math


class Histogram:
    """
    Histogram for tracking distributions (Prometheus-compatible)
    """

    def __init__(self, buckets: Optional[List[float]] = None):
        """
        Args:
            buckets: Upper bounds for histogram buckets
        """
        # Default buckets for latency (in seconds): 0.1, 0.5, 1, 2, 5, 10, 30, 60, 120
        self.buckets = buckets or [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, float('inf')]
        self.bucket_counts = [0] * len(self.buckets)
        self.sum = 0.0
        self.count = 0
        self.lock = Lock()

    def observe(self, value: float):
        """Add an observation"""
        with self.lock:
            self.sum += value
            self.count += 1

            # Find appropriate bucket
            for i, bucket in enumerate(self.buckets):
                if value <= bucket:
                    self.bucket_counts[i] += 1

    def get_data(self) -> Dict:
        """Get histogram data"""
        with self.lock:
            return {
                'count': self.count,
                'sum': self.sum,
                'buckets': {
                    str(bucket): count
                    for bucket, count in zip(self.buckets, self.bucket_counts)
                }
            }

    def to_prometheus(self, name: str, labels: Dict[str, str] = None) -> List[str]:
        """Export as Prometheus format"""
        labels_str = ''
        if labels:
            label_pairs = [f'{k}="{v}"' for k, v in labels.items()]
            labels_str = '{' + ','.join(label_pairs) + '}'

        lines = []

        with self.lock:
            # Histogram buckets
            for bucket, count in zip(self.buckets, self.bucket_counts):
                bucket_label = labels_str.replace('}', f',le="{bucket}"}}') if labels_str else f'{{le="{bucket}"}}'
                lines.append(f'{name}_bucket{bucket_label} {count}')

            # Sum and count
            lines.append(f'{name}_sum{labels_str} {self.sum}')
            lines.append(f'{name}_count{labels_str} {self.count}')

        return lines


class MetricsCollector:
    """
    Enhanced metrics collector with Prometheus histograms and counters
    """

    def __init__(self, max_history: int = 1000):
        self.lock = Lock()
        self.max_history = max_history

        # Counters
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0

        # By type
        self.requests_by_type = defaultdict(int)
        self.requests_by_decision = defaultdict(int)
        self.requests_by_risk_level = defaultdict(int)

        # Processing times (sliding window)
        self.processing_times = deque(maxlen=max_history)
        self.processing_times_by_type = defaultdict(lambda: deque(maxlen=100))

        # Queue metrics
        self.queue_depth = 0
        self.queue_depth_history = deque(maxlen=100)

        # Worker metrics
        self.active_workers = 0
        self.worker_stats = {}

        # FPS processed (for video)
        self.total_fps_processed = 0
        self.total_frames_processed = 0

        # Error tracking
        self.errors_by_type = defaultdict(int)
        self.recent_errors = deque(maxlen=50)

        # Start time
        self.start_time = time.time()

        # Histograms
        self.processing_time_histogram = Histogram()
        self.queue_depth_histogram = Histogram(buckets=[0, 10, 20, 50, 100, 200, 500, 1000])

    def record_request(self,
                      job_type: str,
                      processing_time: float,
                      success: bool = True,
                      decision: Optional[str] = None,
                      risk_level: Optional[str] = None,
                      frames_processed: int = 0):
        """Record a completed moderation request"""
        with self.lock:
            self.total_requests += 1

            if success:
                self.successful_requests += 1
            else:
                self.failed_requests += 1

            # By type
            self.requests_by_type[job_type] += 1

            # By decision
            if decision:
                self.requests_by_decision[decision] += 1

            # By risk level
            if risk_level:
                self.requests_by_risk_level[risk_level] += 1

            # Processing time
            self.processing_times.append(processing_time)
            self.processing_times_by_type[job_type].append(processing_time)
            self.processing_time_histogram.observe(processing_time)

            # Frames
            if frames_processed > 0:
                self.total_frames_processed += frames_processed
                if processing_time > 0:
                    fps = frames_processed / processing_time
                    self.total_fps_processed += fps

    def record_error(self, error_type: str, error_message: str, job_type: Optional[str] = None):
        """Record an error"""
        with self.lock:
            self.errors_by_type[error_type] += 1
            self.recent_errors.append({
                'type': error_type,
                'message': error_message,
                'job_type': job_type,
                'timestamp': time.time()
            })

    def update_queue_depth(self, depth: int):
        """Update current queue depth"""
        with self.lock:
            self.queue_depth = depth
            self.queue_depth_history.append(depth)
            self.queue_depth_histogram.observe(depth)

    def update_worker_stats(self, worker_id: str, stats: Dict):
        """Update worker statistics"""
        with self.lock:
            self.worker_stats[worker_id] = {
                **stats,
                'last_updated': time.time()
            }

            # Count active workers
            self.active_workers = sum(
                1 for w in self.worker_stats.values()
                if w.get('status') == 'active'
            )

    def get_metrics(self) -> Dict:
        """Get all metrics as dictionary"""
        with self.lock:
            uptime = time.time() - self.start_time

            # Calculate percentiles
            processing_times_sorted = sorted(self.processing_times) if self.processing_times else [0]

            metrics = {
                # System
                'system': {
                    'uptime_seconds': uptime,
                    'cpu_percent': psutil.cpu_percent(interval=0.1),
                    'memory_mb': psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024,
                    'memory_percent': psutil.virtual_memory().percent
                },

                # Requests
                'requests': {
                    'total': self.total_requests,
                    'successful': self.successful_requests,
                    'failed': self.failed_requests,
                    'success_rate': self.successful_requests / max(self.total_requests, 1),
                    'requests_per_second': self.total_requests / max(uptime, 1)
                },

                # By type
                'requests_by_type': dict(self.requests_by_type),
                'requests_by_decision': dict(self.requests_by_decision),
                'requests_by_risk_level': dict(self.requests_by_risk_level),

                # Processing time
                'processing_time': {
                    'mean': sum(self.processing_times) / max(len(self.processing_times), 1),
                    'min': min(processing_times_sorted),
                    'max': max(processing_times_sorted),
                    'p50': processing_times_sorted[len(processing_times_sorted) // 2],
                    'p95': processing_times_sorted[int(len(processing_times_sorted) * 0.95)] if len(processing_times_sorted) > 20 else max(processing_times_sorted),
                    'p99': processing_times_sorted[int(len(processing_times_sorted) * 0.99)] if len(processing_times_sorted) > 100 else max(processing_times_sorted)
                },

                # Queue
                'queue': {
                    'current_depth': self.queue_depth,
                    'avg_depth': sum(self.queue_depth_history) / max(len(self.queue_depth_history), 1) if self.queue_depth_history else 0,
                    'max_depth': max(self.queue_depth_history) if self.queue_depth_history else 0
                },

                # Workers
                'workers': {
                    'total': len(self.worker_stats),
                    'active': self.active_workers,
                    'inactive': len(self.worker_stats) - self.active_workers
                },

                # Video processing
                'video_processing': {
                    'total_frames': self.total_frames_processed,
                    'avg_fps': self.total_fps_processed / max(self.requests_by_type.get('video', 1), 1)
                },

                # Errors
                'errors': {
                    'total': sum(self.errors_by_type.values()),
                    'by_type': dict(self.errors_by_type),
                    'error_rate': sum(self.errors_by_type.values()) / max(self.total_requests, 1)
                }
            }

            return metrics

    def get_prometheus_metrics(self) -> str:
        """
        Export metrics in Prometheus format
        https://prometheus.io/docs/instrumenting/exposition_formats/
        """
        metrics = self.get_metrics()
        lines = []

        # Helper function
        def add_metric(name: str, value: float, help_text: str, metric_type: str = "gauge"):
            lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} {metric_type}")
            lines.append(f"{name} {value}")
            lines.append("")

        # System metrics
        add_metric("moderation_uptime_seconds", metrics['system']['uptime_seconds'], "Service uptime in seconds", "counter")
        add_metric("moderation_cpu_percent", metrics['system']['cpu_percent'], "CPU usage percentage", "gauge")
        add_metric("moderation_memory_mb", metrics['system']['memory_mb'], "Memory usage in MB", "gauge")

        # Request metrics
        add_metric("moderation_requests_total", metrics['requests']['total'], "Total requests processed", "counter")
        add_metric("moderation_requests_successful", metrics['requests']['successful'], "Successful requests", "counter")
        add_metric("moderation_requests_failed", metrics['requests']['failed'], "Failed requests", "counter")
        add_metric("moderation_requests_per_second", metrics['requests']['requests_per_second'], "Requests per second", "gauge")

        # Processing time
        add_metric("moderation_processing_time_mean", metrics['processing_time']['mean'], "Mean processing time", "gauge")
        add_metric("moderation_processing_time_p95", metrics['processing_time']['p95'], "95th percentile processing time", "gauge")
        add_metric("moderation_processing_time_p99", metrics['processing_time']['p99'], "99th percentile processing time", "gauge")

        # Queue
        add_metric("moderation_queue_depth", metrics['queue']['current_depth'], "Current queue depth", "gauge")
        add_metric("moderation_queue_depth_avg", metrics['queue']['avg_depth'], "Average queue depth", "gauge")

        # Workers
        add_metric("moderation_workers_active", metrics['workers']['active'], "Active workers", "gauge")
        add_metric("moderation_workers_total", metrics['workers']['total'], "Total workers", "gauge")

        # Video processing
        add_metric("moderation_frames_processed_total", metrics['video_processing']['total_frames'], "Total frames processed", "counter")
        add_metric("moderation_fps_avg", metrics['video_processing']['avg_fps'], "Average FPS processed", "gauge")

        # Errors
        add_metric("moderation_errors_total", metrics['errors']['total'], "Total errors", "counter")

        # By type (with labels)
        for job_type, count in metrics['requests_by_type'].items():
            lines.append(f'moderation_requests_by_type{{type="{job_type}"}} {count}')
        lines.append("")

        # By decision (with labels)
        for decision, count in metrics['requests_by_decision'].items():
            lines.append(f'moderation_decisions{{decision="{decision}"}} {count}')
        lines.append("")

        # By risk level (with labels)
        for risk_level, count in metrics['requests_by_risk_level'].items():
            lines.append(f'moderation_risk_levels{{risk_level="{risk_level}"}} {count}')
        lines.append("")

        # Processing time histogram
        lines.extend(self.processing_time_histogram.to_prometheus("moderation_processing_time_histogram"))
        lines.append("")

        # Queue depth histogram
        lines.extend(self.queue_depth_histogram.to_prometheus("moderation_queue_depth_histogram"))
        lines.append("")

        return '\n'.join(lines)

    def get_recent_errors(self, limit: int = 10) -> List[Dict]:
        """Get recent errors"""
        with self.lock:
            return list(self.recent_errors)[-limit:]

    def get_worker_details(self) -> Dict:
        """Get detailed worker statistics"""
        with self.lock:
            return dict(self.worker_stats)

    def reset_metrics(self):
        """Reset all metrics (for testing)"""
        with self.lock:
            self.total_requests = 0
            self.successful_requests = 0
            self.failed_requests = 0
            self.requests_by_type.clear()
            self.requests_by_decision.clear()
            self.requests_by_risk_level.clear()
            self.processing_times.clear()
            self.processing_times_by_type.clear()
            self.queue_depth = 0
            self.queue_depth_history.clear()
            self.active_workers = 0
            self.worker_stats.clear()
            self.total_fps_processed = 0
            self.total_frames_processed = 0
            self.errors_by_type.clear()
            self.recent_errors.clear()
            self.start_time = time.time()


# Singleton instance
_metrics_instance = None

def get_metrics_collector() -> MetricsCollector:
    """Get or create metrics collector singleton"""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = MetricsCollector()
    return _metrics_instance


# FastAPI endpoint integration
def metrics_endpoint_handler():
    """Handler for /metrics endpoint"""
    collector = get_metrics_collector()
    return collector.get_prometheus_metrics()


def metrics_json_handler():
    """Handler for /metrics/json endpoint"""
    collector = get_metrics_collector()
    return collector.get_metrics()


if __name__ == '__main__':
    # Test metrics
    collector = get_metrics_collector()

    # Simulate some requests
    for i in range(100):
        collector.record_request(
            job_type='text' if i % 2 == 0 else 'image',
            processing_time=0.1 + (i % 10) * 0.05,
            success=i % 20 != 0,
            decision='approve' if i % 3 == 0 else 'review',
            risk_level='low' if i % 2 == 0 else 'medium'
        )

    # Simulate errors
    collector.record_error('model_error', 'Model failed to load', 'image')
    collector.record_error('timeout', 'Request timeout', 'video')

    # Update queue
    collector.update_queue_depth(42)

    # Update workers
    collector.update_worker_stats('worker-1', {'status': 'active', 'jobs_processed': 50})
    collector.update_worker_stats('worker-2', {'status': 'active', 'jobs_processed': 30})

    # Print metrics
    print("=" * 60)
    print("JSON Metrics:")
    print("=" * 60)
    print(json.dumps(collector.get_metrics(), indent=2))

    print("\n" + "=" * 60)
    print("Prometheus Metrics:")
    print("=" * 60)
    print(collector.get_prometheus_metrics())
