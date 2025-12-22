"""
Circuit Breaker Pattern Implementation
Auto-disable failing model workers to prevent cascading failures
"""

import time
import threading
from typing import Dict, Optional, Callable, Any
from enum import Enum
from collections import deque
from datetime import datetime, timedelta
import json


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing - reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreakerConfig:
    """Configuration for circuit breaker"""

    def __init__(self,
                 failure_threshold: int = 5,
                 success_threshold: int = 2,
                 timeout: int = 60,
                 window_size: int = 100):
        """
        Args:
            failure_threshold: Number of failures before opening circuit
            success_threshold: Number of successes needed to close from half-open
            timeout: Seconds to wait before trying half-open
            window_size: Size of sliding window for tracking calls
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.window_size = window_size


class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures
    Automatically disables failing model workers
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_state_change = time.time()

        # Sliding window of recent calls
        self.call_history = deque(maxlen=self.config.window_size)

        # Statistics
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0
        self.total_rejections = 0
        self.state_changes = []

        self.lock = threading.Lock()

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection

        Args:
            func: Function to execute
            *args, **kwargs: Arguments to pass to function

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Original exception from func if circuit is closed
        """
        with self.lock:
            self.total_calls += 1

            # Check if we should transition from OPEN to HALF_OPEN
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to(CircuitState.HALF_OPEN)
                else:
                    self.total_rejections += 1
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is OPEN. "
                        f"Will retry in {self._time_until_retry():.0f}s"
                    )

            # If HALF_OPEN, only allow limited requests
            if self.state == CircuitState.HALF_OPEN:
                if self.success_count >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)

        # Execute the function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful call"""
        with self.lock:
            self.total_successes += 1
            self.call_history.append({
                'success': True,
                'timestamp': time.time()
            })

            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1

                if self.success_count >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)

            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0

    def _on_failure(self):
        """Handle failed call"""
        with self.lock:
            self.total_failures += 1
            self.failure_count += 1
            self.last_failure_time = time.time()

            self.call_history.append({
                'success': False,
                'timestamp': time.time()
            })

            if self.state == CircuitState.HALF_OPEN:
                # Any failure in HALF_OPEN state reopens circuit
                self._transition_to(CircuitState.OPEN)

            elif self.state == CircuitState.CLOSED:
                # Check if we've exceeded failure threshold
                if self.failure_count >= self.config.failure_threshold:
                    self._transition_to(CircuitState.OPEN)

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if not self.last_failure_time:
            return True

        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure >= self.config.timeout

    def _time_until_retry(self) -> float:
        """Calculate seconds until retry is allowed"""
        if not self.last_failure_time:
            return 0

        time_since_failure = time.time() - self.last_failure_time
        return max(0, self.config.timeout - time_since_failure)

    def _transition_to(self, new_state: CircuitState):
        """Transition to new state"""
        old_state = self.state
        self.state = new_state
        self.last_state_change = time.time()

        # Reset counters based on state
        if new_state == CircuitState.CLOSED:
            self.failure_count = 0
            self.success_count = 0
        elif new_state == CircuitState.HALF_OPEN:
            self.success_count = 0

        # Record state change
        self.state_changes.append({
            'from': old_state.value,
            'to': new_state.value,
            'timestamp': time.time(),
            'failure_count': self.failure_count,
            'success_count': self.success_count
        })

        # Keep only last 100 state changes
        if len(self.state_changes) > 100:
            self.state_changes = self.state_changes[-100:]

        print(f"⚡ Circuit breaker '{self.name}': {old_state.value} → {new_state.value}")

    def force_open(self):
        """Manually open circuit (for admin intervention)"""
        with self.lock:
            self._transition_to(CircuitState.OPEN)

    def force_close(self):
        """Manually close circuit (for admin intervention)"""
        with self.lock:
            self._transition_to(CircuitState.CLOSED)
            self.failure_count = 0

    def get_state(self) -> str:
        """Get current state"""
        return self.state.value

    def is_available(self) -> bool:
        """Check if circuit allows calls"""
        with self.lock:
            if self.state == CircuitState.OPEN:
                return self._should_attempt_reset()
            return True

    def get_stats(self) -> Dict:
        """Get circuit breaker statistics"""
        with self.lock:
            # Calculate failure rate from call history
            recent_failures = sum(1 for call in self.call_history if not call['success'])
            failure_rate = recent_failures / len(self.call_history) if self.call_history else 0

            # Time in current state
            time_in_state = time.time() - self.last_state_change

            return {
                'name': self.name,
                'state': self.state.value,
                'time_in_state': time_in_state,
                'failure_count': self.failure_count,
                'success_count': self.success_count,
                'total_calls': self.total_calls,
                'total_failures': self.total_failures,
                'total_successes': self.total_successes,
                'total_rejections': self.total_rejections,
                'failure_rate': failure_rate,
                'success_rate': 1 - failure_rate if self.call_history else 0,
                'time_until_retry': self._time_until_retry() if self.state == CircuitState.OPEN else 0,
                'recent_state_changes': self.state_changes[-5:] if self.state_changes else []
            }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreakerManager:
    """
    Manages multiple circuit breakers for different models/services
    """

    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
        self.lock = threading.Lock()

    def get_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create circuit breaker"""
        with self.lock:
            if name not in self.breakers:
                self.breakers[name] = CircuitBreaker(name, config)
            return self.breakers[name]

    def call(self, service_name: str, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection

        Args:
            service_name: Name of service/model
            func: Function to execute
            *args, **kwargs: Arguments to pass to function
        """
        breaker = self.get_breaker(service_name)
        return breaker.call(func, *args, **kwargs)

    def get_all_stats(self) -> Dict:
        """Get statistics for all circuit breakers"""
        with self.lock:
            return {
                name: breaker.get_stats()
                for name, breaker in self.breakers.items()
            }

    def get_health_status(self) -> Dict:
        """Get overall health status"""
        with self.lock:
            total = len(self.breakers)
            open_count = sum(1 for b in self.breakers.values() if b.state == CircuitState.OPEN)
            half_open_count = sum(1 for b in self.breakers.values() if b.state == CircuitState.HALF_OPEN)
            closed_count = sum(1 for b in self.breakers.values() if b.state == CircuitState.CLOSED)

            return {
                'total_breakers': total,
                'healthy': closed_count,
                'degraded': half_open_count,
                'failing': open_count,
                'overall_health': 'healthy' if open_count == 0 else 'degraded' if open_count < total else 'critical'
            }

    def force_reset_all(self):
        """Reset all circuit breakers (admin function)"""
        with self.lock:
            for breaker in self.breakers.values():
                breaker.force_close()

    def get_failing_services(self) -> list:
        """Get list of failing services"""
        with self.lock:
            return [
                name for name, breaker in self.breakers.items()
                if breaker.state == CircuitState.OPEN
            ]


# Global circuit breaker manager
_cb_manager = None

def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """Get global circuit breaker manager"""
    global _cb_manager
    if _cb_manager is None:
        _cb_manager = CircuitBreakerManager()
    return _cb_manager


# Decorator for easy circuit breaker application
def circuit_breaker(service_name: str, config: Optional[CircuitBreakerConfig] = None):
    """
    Decorator to apply circuit breaker to a function

    Usage:
        @circuit_breaker('yolo_violence')
        def detect_violence(image):
            # ... detection logic
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            manager = get_circuit_breaker_manager()
            breaker = manager.get_breaker(service_name, config)
            return breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator


if __name__ == '__main__':
    # Test circuit breaker
    import random

    # Create a function that fails randomly
    def unreliable_service():
        if random.random() < 0.7:  # 70% failure rate
            raise Exception("Service failed!")
        return "Success"

    # Create circuit breaker
    manager = get_circuit_breaker_manager()
    breaker = manager.get_breaker('test_service', CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout=5
    ))

    print("Testing circuit breaker...\n")

    # Simulate calls
    for i in range(20):
        try:
            result = breaker.call(unreliable_service)
            print(f"Call {i+1}: ✅ {result}")
        except CircuitBreakerOpenError as e:
            print(f"Call {i+1}: 🚫 Circuit OPEN - {e}")
        except Exception as e:
            print(f"Call {i+1}: ❌ Failed - {e}")

        # Show stats every 5 calls
        if (i + 1) % 5 == 0:
            stats = breaker.get_stats()
            print(f"\n📊 Stats after {i+1} calls:")
            print(f"   State: {stats['state'].upper()}")
            print(f"   Failures: {stats['total_failures']}/{stats['total_calls']}")
            print(f"   Rejections: {stats['total_rejections']}")
            print(f"   Failure rate: {stats['failure_rate']:.1%}\n")

        time.sleep(0.5)

    print("\n" + "="*60)
    print("Final Statistics:")
    print(json.dumps(breaker.get_stats(), indent=2))

