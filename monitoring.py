try:
    from prometheus_client import Counter, Histogram, start_http_server
    _PROM_AVAILABLE = True
except Exception:
    # Provide no-op fallbacks so the app can run without prometheus installed
    _PROM_AVAILABLE = False
    class _NoopMetric:
        def labels(self, *args, **kwargs):
            return self
        def inc(self, *args, **kwargs):
            return None
        def observe(self, *args, **kwargs):
            return None
    def start_http_server(port=8000):
        # no-op server; logs a message instead
        import logging
        logging.getLogger(__name__).info(f"Prometheus not installed; monitoring disabled (port {port})")
    Counter = lambda *args, **kwargs: _NoopMetric()
    Histogram = lambda *args, **kwargs: _NoopMetric()

import time
import logging

REQUEST_COUNT = Counter('request_count', 'Total number of requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency', ['method', 'endpoint'])


def start_monitoring(port=8000):
    try:
        start_http_server(port)
        logging.getLogger(__name__).info(f"Monitoring server started on port {port}")
    except Exception:
        logging.getLogger(__name__).warning("Monitoring server not started; prometheus may be unavailable")


def track_request(method, endpoint):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
            except Exception:
                pass
            result = func(*args, **kwargs)
            try:
                REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
            except Exception:
                pass
            return result
        wrapper.__name__ = getattr(func, '__name__', 'wrapped')
        return wrapper
    return decorator
