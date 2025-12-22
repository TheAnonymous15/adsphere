"""
Async video processing worker using Redis Streams
Handles long-running video moderation jobs
"""
import redis
import time
import json
import traceback
from typing import Dict
from app.core.config import settings
from app.services.video_moderation_pipeline import VideoModerationPipeline
from app.utils.logging import app_logger


class VideoWorker:
    """
    Async worker for video moderation jobs.

    Uses Redis Streams for job queue:
    - Job states: queued → running → completed/failed
    - Consumer groups for horizontal scaling
    - At-least-once delivery
    """

    STREAM_NAME = "video_moderation_jobs"
    GROUP_NAME = "video_workers"
    CONSUMER_NAME = None  # Set per worker instance

    def __init__(self, redis_url: str = None, worker_id: str = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self.worker_id = worker_id or f"worker-{time.time()}"
        self.CONSUMER_NAME = self.worker_id

        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        self.pipeline = VideoModerationPipeline()

        # Create consumer group if not exists
        try:
            self.redis_client.xgroup_create(
                self.STREAM_NAME,
                self.GROUP_NAME,
                id='0',
                mkstream=True
            )
            app_logger.info(f"Created consumer group: {self.GROUP_NAME}")
        except redis.ResponseError as e:
            if 'BUSYGROUP' not in str(e):
                raise

        app_logger.info(f"Video worker {self.worker_id} initialized")

    def run(self, batch_size: int = 1, block_ms: int = 5000):
        """
        Start worker loop.

        Args:
            batch_size: Number of jobs to read per iteration
            block_ms: Milliseconds to block waiting for jobs
        """
        app_logger.info(f"Worker {self.worker_id} starting...")

        while True:
            try:
                # Read from stream
                messages = self.redis_client.xreadgroup(
                    groupname=self.GROUP_NAME,
                    consumername=self.CONSUMER_NAME,
                    streams={self.STREAM_NAME: '>'},
                    count=batch_size,
                    block=block_ms
                )

                if not messages:
                    continue

                for stream_name, stream_messages in messages:
                    for msg_id, msg_data in stream_messages:
                        self._process_job(msg_id, msg_data)

            except KeyboardInterrupt:
                app_logger.info(f"Worker {self.worker_id} shutting down...")
                break
            except Exception as e:
                app_logger.error(f"Worker error: {e}", error=str(e), traceback=traceback.format_exc())
                time.sleep(1)

    def _process_job(self, msg_id: str, msg_data: Dict):
        """Process a single video moderation job"""
        job_id = msg_data.get('job_id')
        video_path = msg_data.get('video_path')

        app_logger.info(f"Processing job {job_id}", job_id=job_id, video_path=video_path)

        try:
            # Update status to running
            self._update_job_status(job_id, 'running', progress=0.0)

            # Run moderation pipeline
            result = self.pipeline.moderate_video(video_path)

            # Store result
            self._store_result(job_id, result)

            # Update status to completed
            self._update_job_status(job_id, 'completed', progress=100.0)

            # Acknowledge message
            self.redis_client.xack(self.STREAM_NAME, self.GROUP_NAME, msg_id)

            app_logger.info(
                f"Job {job_id} completed",
                job_id=job_id,
                decision=result.get('decision'),
                risk_level=result.get('risk_level')
            )

        except Exception as e:
            app_logger.error(
                f"Job {job_id} failed",
                job_id=job_id,
                error=str(e),
                traceback=traceback.format_exc()
            )

            # Update status to failed
            self._update_job_status(job_id, 'failed', error=str(e))

            # Acknowledge to prevent retry loop (or don't ack for retry)
            self.redis_client.xack(self.STREAM_NAME, self.GROUP_NAME, msg_id)

    def _update_job_status(self, job_id: str, status: str, progress: float = None, error: str = None):
        """Update job status in Redis"""
        status_key = f"job:status:{job_id}"

        status_data = {
            'status': status,
            'updated_at': time.time()
        }

        if progress is not None:
            status_data['progress'] = progress

        if error:
            status_data['error'] = error

        self.redis_client.hset(status_key, mapping=status_data)
        self.redis_client.expire(status_key, 86400)  # Keep for 24 hours

    def _store_result(self, job_id: str, result: Dict):
        """Store moderation result"""
        result_key = f"job:result:{job_id}"
        self.redis_client.set(result_key, json.dumps(result), ex=86400)  # 24 hour TTL


class JobQueue:
    """
    Job queue manager for submitting video moderation jobs.
    """

    STREAM_NAME = "video_moderation_jobs"

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)

    def submit_job(self, job_id: str, video_path: str, metadata: Dict = None) -> str:
        """
        Submit video moderation job to queue.

        Args:
            job_id: Unique job identifier
            video_path: Path to video file
            metadata: Additional metadata

        Returns:
            Message ID from Redis Stream
        """
        job_data = {
            'job_id': job_id,
            'video_path': video_path,
            'submitted_at': time.time()
        }

        if metadata:
            job_data['metadata'] = json.dumps(metadata)

        # Add to stream
        msg_id = self.redis_client.xadd(self.STREAM_NAME, job_data)

        # Initialize status
        self._init_job_status(job_id)

        app_logger.info(f"Job {job_id} submitted", job_id=job_id, msg_id=msg_id)

        return msg_id

    def get_job_status(self, job_id: str) -> Dict:
        """Get current job status"""
        status_key = f"job:status:{job_id}"
        status_data = self.redis_client.hgetall(status_key)

        if not status_data:
            return {'status': 'not_found'}

        return {
            'status': status_data.get('status', 'unknown'),
            'progress': float(status_data.get('progress', 0.0)),
            'error': status_data.get('error'),
            'updated_at': float(status_data.get('updated_at', 0))
        }

    def get_job_result(self, job_id: str) -> Dict:
        """Get moderation result for completed job"""
        result_key = f"job:result:{job_id}"
        result_json = self.redis_client.get(result_key)

        if not result_json:
            return None

        return json.loads(result_json)

    def _init_job_status(self, job_id: str):
        """Initialize job status"""
        status_key = f"job:status:{job_id}"
        self.redis_client.hset(status_key, mapping={
            'status': 'queued',
            'progress': 0.0,
            'created_at': time.time(),
            'updated_at': time.time()
        })
        self.redis_client.expire(status_key, 86400)


# CLI entry point for running worker
if __name__ == '__main__':
    import sys
    worker_id = sys.argv[1] if len(sys.argv) > 1 else None
    worker = VideoWorker(worker_id=worker_id)
    worker.run()

