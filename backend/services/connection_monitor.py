import time
import logging
import threading
from typing import Dict, List
from collections import defaultdict

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    logging.warning("psutil not available - system monitoring disabled")

logger = logging.getLogger(__name__)

class ConnectionMonitor:
    """Monitor connection health and provide diagnostics"""

    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.connection_stats = defaultdict(int)
        self.response_times = []
        self.active_connections = 0
        self._lock = threading.Lock()

    def record_request(self, method: str, path: str, status_code: int, duration: float):
        """Record a request for monitoring"""
        with self._lock:
            self.request_count += 1
            self.connection_stats[f"{method}_{path}"] += 1

            if status_code >= 400:
                self.error_count += 1

            # Keep last 1000 response times for rolling average
            self.response_times.append(duration)
            if len(self.response_times) > 1000:
                self.response_times.pop(0)

    def get_connection_health(self) -> Dict:
        """Get current connection health metrics"""
        with self._lock:
            avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0

            return {
                "uptime": time.time() - self.start_time,
                "total_requests": self.request_count,
                "error_count": self.error_count,
                "error_rate": (self.error_count / self.request_count * 100) if self.request_count > 0 else 0,
                "average_response_time": avg_response_time,
                "active_connections": self.active_connections,
                "memory_usage": self._get_memory_usage(),
                "cpu_usage": self._get_cpu_usage(),
                "timestamp": time.time()
            }

    def get_request_stats(self) -> Dict:
        """Get detailed request statistics"""
        with self._lock:
            return {
                "endpoint_stats": dict(self.connection_stats),
                "total_requests": self.request_count,
                "error_count": self.error_count,
                "success_rate": ((self.request_count - self.error_count) / self.request_count * 100) if self.request_count > 0 else 100
            }

    def increment_active_connections(self):
        """Increment active connection count"""
        with self._lock:
            self.active_connections += 1

    def decrement_active_connections(self):
        """Decrement active connection count"""
        with self._lock:
            self.active_connections = max(0, self.active_connections - 1)

    def _get_memory_usage(self) -> Dict:
        """Get memory usage statistics"""
        try:
            memory = psutil.virtual_memory()
            process = psutil.Process()
            return {
                "system_percent": memory.percent,
                "system_used_gb": memory.used / (1024**3),
                "system_total_gb": memory.total / (1024**3),
                "process_mb": process.memory_info().rss / (1024**2)
            }
        except Exception as e:
            logger.error(f"Failed to get memory usage: {e}")
            return {"error": str(e)}

    def _get_cpu_usage(self) -> Dict:
        """Get CPU usage statistics"""
        try:
            return {
                "system_percent": psutil.cpu_percent(interval=1),
                "process_percent": psutil.Process().cpu_percent(interval=1)
            }
        except Exception as e:
            logger.error(f"Failed to get CPU usage: {e}")
            return {"error": str(e)}

# Global connection monitor instance
_connection_monitor = ConnectionMonitor()

def get_connection_monitor():
    """Get the global connection monitor instance"""
    return _connection_monitor
