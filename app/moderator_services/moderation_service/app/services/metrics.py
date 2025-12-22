"""
metrics.py – Prometheus metrics registry
"""
from prometheus_client import Counter, Gauge

startup_counter = Counter("app_startups_total", "Application startups")
shutdown_counter = Counter("app_shutdowns_total", "Application shutdowns")

queue_overflow_counter = Counter(
    "queue_overflow_total", "Rejected requests due to queue overflow"
)

queue_depth_gauge = Gauge(
    "queue_depth", "Current queued items"
)

worker_pool_gauge = Gauge(
    "worker_pool_size", "Total worker coroutines allocated"
)

partial_chunks_counter = Counter(
    "partial_chunks_sent_total",
    "Partial streaming WebSocket chunks"
)

binary_frames_counter = Counter(
    "binary_frames_sent_total",
    "Binary WebSocket frames sent"
)

tasks_dispatched_counter = Counter(
    "tasks_dispatched_total",
    "Total tasks dispatched to coordinator"
)

