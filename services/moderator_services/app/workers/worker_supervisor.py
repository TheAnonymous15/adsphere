"""
Worker Supervisor - Auto-restart and Health Monitoring
Ensures workers stay alive and automatically restarts crashed workers
"""

import subprocess
import time
import signal
import sys
import os
import psutil
from typing import Dict, List, Optional
from datetime import datetime
import json
from threading import Thread, Lock


class WorkerProcess:
    """Represents a single worker process"""

    def __init__(self, worker_id: str, command: List[str], max_restarts: int = 5):
        self.worker_id = worker_id
        self.command = command
        self.max_restarts = max_restarts

        self.process: Optional[subprocess.Popen] = None
        self.pid: Optional[int] = None
        self.status = 'stopped'

        self.started_at: Optional[float] = None
        self.stopped_at: Optional[float] = None
        self.last_heartbeat: Optional[float] = None

        self.restart_count = 0
        self.crash_count = 0
        self.crash_history = []

        self.total_uptime = 0.0

    def start(self):
        """Start the worker process"""
        try:
            self.process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            self.pid = self.process.pid
            self.status = 'running'
            self.started_at = time.time()
            self.last_heartbeat = time.time()

            print(f"✅ Started worker {self.worker_id} (PID: {self.pid})")

        except Exception as e:
            self.status = 'failed'
            print(f"❌ Failed to start worker {self.worker_id}: {e}")
            raise

    def stop(self, timeout: int = 10):
        """Stop the worker process gracefully"""
        if not self.process:
            return

        try:
            print(f"🛑 Stopping worker {self.worker_id} (PID: {self.pid})...")

            # Try graceful shutdown first
            self.process.terminate()

            try:
                self.process.wait(timeout=timeout)
                print(f"✅ Worker {self.worker_id} stopped gracefully")
            except subprocess.TimeoutExpired:
                print(f"⚠️  Worker {self.worker_id} didn't stop, forcing...")
                self.process.kill()
                self.process.wait()
                print(f"✅ Worker {self.worker_id} killed")

            self.status = 'stopped'
            self.stopped_at = time.time()

            if self.started_at:
                uptime = self.stopped_at - self.started_at
                self.total_uptime += uptime

        except Exception as e:
            print(f"❌ Error stopping worker {self.worker_id}: {e}")

    def is_alive(self) -> bool:
        """Check if process is alive"""
        if not self.process:
            return False

        return self.process.poll() is None

    def get_return_code(self) -> Optional[int]:
        """Get process return code"""
        if not self.process:
            return None

        return self.process.poll()

    def record_crash(self, reason: str):
        """Record a crash event"""
        self.crash_count += 1
        self.crash_history.append({
            'timestamp': time.time(),
            'reason': reason,
            'uptime': time.time() - self.started_at if self.started_at else 0,
            'return_code': self.get_return_code()
        })

        # Keep only last 10 crashes
        if len(self.crash_history) > 10:
            self.crash_history = self.crash_history[-10:]

    def should_restart(self) -> bool:
        """Determine if worker should be restarted"""
        # Don't restart if manually stopped
        if self.status == 'stopped':
            return False

        # Check restart limit
        if self.restart_count >= self.max_restarts:
            print(f"⚠️  Worker {self.worker_id} reached max restarts ({self.max_restarts})")
            return False

        # Check for crash loop (3 crashes in 60 seconds)
        recent_crashes = [
            c for c in self.crash_history
            if time.time() - c['timestamp'] < 60
        ]

        if len(recent_crashes) >= 3:
            print(f"⚠️  Worker {self.worker_id} in crash loop (3 crashes in 60s)")
            return False

        return True

    def get_stats(self) -> Dict:
        """Get worker statistics"""
        uptime = 0
        if self.started_at and self.status == 'running':
            uptime = time.time() - self.started_at

        return {
            'worker_id': self.worker_id,
            'pid': self.pid,
            'status': self.status,
            'started_at': self.started_at,
            'uptime': uptime,
            'total_uptime': self.total_uptime,
            'restart_count': self.restart_count,
            'crash_count': self.crash_count,
            'last_crash': self.crash_history[-1] if self.crash_history else None
        }


class WorkerSupervisor:
    """
    Supervises multiple worker processes
    - Auto-restart on crash
    - Health monitoring
    - Graceful shutdown
    """

    def __init__(self,
                 worker_command_template: List[str],
                 num_workers: int = 2,
                 heartbeat_timeout: int = 60,
                 check_interval: int = 5):

        self.worker_command_template = worker_command_template
        self.num_workers = num_workers
        self.heartbeat_timeout = heartbeat_timeout
        self.check_interval = check_interval

        self.workers: Dict[str, WorkerProcess] = {}
        self.lock = Lock()
        self.running = False

        self.stats = {
            'started_at': None,
            'total_restarts': 0,
            'total_crashes': 0
        }

    def start(self):
        """Start all workers and monitoring"""
        print(f"🚀 Starting Worker Supervisor with {self.num_workers} workers...")

        self.running = True
        self.stats['started_at'] = time.time()

        # Start all workers
        for i in range(self.num_workers):
            worker_id = f"worker-{i+1}"
            self._start_worker(worker_id)

        # Start monitoring thread
        monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()

        print(f"✅ Supervisor started with {len(self.workers)} workers")

    def _start_worker(self, worker_id: str):
        """Start a single worker"""
        with self.lock:
            # Build command with worker ID
            command = [arg.replace('{worker_id}', worker_id) for arg in self.worker_command_template]

            worker = WorkerProcess(worker_id, command)

            try:
                worker.start()
                self.workers[worker_id] = worker
            except Exception as e:
                print(f"❌ Failed to start {worker_id}: {e}")

    def _monitor_loop(self):
        """Main monitoring loop"""
        print("👁️  Monitoring loop started")

        while self.running:
            try:
                time.sleep(self.check_interval)
                self._check_workers()
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")

    def _check_workers(self):
        """Check all workers and restart if needed"""
        with self.lock:
            for worker_id, worker in list(self.workers.items()):
                # Check if alive
                if not worker.is_alive() and worker.status == 'running':
                    return_code = worker.get_return_code()

                    print(f"💀 Worker {worker_id} died (exit code: {return_code})")

                    reason = f"Process exited with code {return_code}"
                    worker.record_crash(reason)
                    worker.status = 'crashed'

                    self.stats['total_crashes'] += 1

                    # Try to restart
                    if worker.should_restart():
                        print(f"🔄 Restarting {worker_id}...")
                        worker.restart_count += 1
                        self.stats['total_restarts'] += 1

                        try:
                            worker.start()
                            print(f"✅ {worker_id} restarted successfully")
                        except Exception as e:
                            print(f"❌ Failed to restart {worker_id}: {e}")
                            worker.status = 'failed'
                    else:
                        print(f"⛔ Not restarting {worker_id}")
                        worker.status = 'failed'

    def stop(self, timeout: int = 30):
        """Stop all workers gracefully"""
        print("🛑 Stopping all workers...")

        self.running = False

        with self.lock:
            for worker_id, worker in self.workers.items():
                worker.stop(timeout=timeout)

        print("✅ All workers stopped")

    def restart_worker(self, worker_id: str):
        """Manually restart a specific worker"""
        with self.lock:
            if worker_id in self.workers:
                worker = self.workers[worker_id]
                print(f"🔄 Manually restarting {worker_id}...")

                worker.stop()
                time.sleep(1)
                worker.start()

                print(f"✅ {worker_id} restarted")
            else:
                print(f"❌ Worker {worker_id} not found")

    def get_status(self) -> Dict:
        """Get supervisor status"""
        with self.lock:
            workers_status = {
                worker_id: worker.get_stats()
                for worker_id, worker in self.workers.items()
            }

            # Count by status
            status_counts = {}
            for worker in self.workers.values():
                status_counts[worker.status] = status_counts.get(worker.status, 0) + 1

            uptime = 0
            if self.stats['started_at']:
                uptime = time.time() - self.stats['started_at']

            return {
                'supervisor': {
                    'running': self.running,
                    'uptime': uptime,
                    'started_at': self.stats['started_at'],
                    'total_workers': len(self.workers),
                    'total_restarts': self.stats['total_restarts'],
                    'total_crashes': self.stats['total_crashes']
                },
                'status_counts': status_counts,
                'workers': workers_status
            }

    def print_status(self):
        """Print formatted status"""
        status = self.get_status()

        print("\n" + "=" * 60)
        print("WORKER SUPERVISOR STATUS")
        print("=" * 60)

        print(f"\nSupervisor:")
        print(f"  Running: {status['supervisor']['running']}")
        print(f"  Uptime: {status['supervisor']['uptime']:.1f}s")
        print(f"  Total Workers: {status['supervisor']['total_workers']}")
        print(f"  Total Restarts: {status['supervisor']['total_restarts']}")
        print(f"  Total Crashes: {status['supervisor']['total_crashes']}")

        print(f"\nStatus Counts:")
        for status_name, count in status['status_counts'].items():
            print(f"  {status_name}: {count}")

        print(f"\nWorkers:")
        for worker_id, worker_stats in status['workers'].items():
            status_icon = {
                'running': '✅',
                'stopped': '⏸️',
                'crashed': '💀',
                'failed': '❌'
            }.get(worker_stats['status'], '❓')

            print(f"  {status_icon} {worker_id} (PID: {worker_stats['pid']})")
            print(f"      Status: {worker_stats['status']}")
            print(f"      Uptime: {worker_stats['uptime']:.1f}s")
            print(f"      Restarts: {worker_stats['restart_count']}")
            print(f"      Crashes: {worker_stats['crash_count']}")

        print("=" * 60 + "\n")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n⚠️  Received signal {signum}, shutting down...")
    supervisor.stop()
    sys.exit(0)


# Global supervisor instance
supervisor: Optional[WorkerSupervisor] = None


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Worker Supervisor')
    parser.add_argument('--workers', type=int, default=2, help='Number of workers')
    parser.add_argument('--command', type=str, default='python -m app.workers.video_worker {worker_id}',
                       help='Worker command template (use {worker_id} placeholder)')
    parser.add_argument('--check-interval', type=int, default=5, help='Health check interval (seconds)')

    args = parser.parse_args()

    # Parse command
    command_parts = args.command.split()

    # Create supervisor
    supervisor = WorkerSupervisor(
        worker_command_template=command_parts,
        num_workers=args.workers,
        check_interval=args.check_interval
    )

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start supervisor
    supervisor.start()

    # Interactive mode
    print("\n📋 Commands: status, restart <worker_id>, stop, help")

    try:
        while True:
            try:
                cmd = input("\n> ").strip().lower()

                if cmd == 'status':
                    supervisor.print_status()

                elif cmd.startswith('restart '):
                    worker_id = cmd.split()[1]
                    supervisor.restart_worker(worker_id)

                elif cmd == 'stop':
                    supervisor.stop()
                    break

                elif cmd == 'help':
                    print("""
Commands:
  status              - Show supervisor status
  restart <worker_id> - Restart specific worker
  stop                - Stop all workers and exit
  help                - Show this help
                    """)

                else:
                    print(f"Unknown command: {cmd}")

            except EOFError:
                break

    except KeyboardInterrupt:
        print("\n⚠️  Interrupted, shutting down...")
        supervisor.stop()

