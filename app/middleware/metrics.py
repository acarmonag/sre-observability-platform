"""Prometheus metrics middleware — times every HTTP request."""
from __future__ import annotations

import time

import psutil
from prometheus_client import Counter, Gauge, Histogram
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# ── Metric definitions ────────────────────────────────────────────────────────

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

active_chaos_modes = Gauge(
    "active_chaos_modes",
    "Whether a chaos mode is currently active (1=active, 0=inactive)",
    ["mode"],
)
# Initialise all mode labels to 0 so they appear in Prometheus from the start
for _mode in ("memory_leak", "latency_spike", "error_rate", "cpu_spike"):
    active_chaos_modes.labels(mode=_mode).set(0)

memory_usage_bytes = Gauge(
    "memory_usage_bytes",
    "Current process RSS memory usage in bytes",
)

orders_created_total = Counter(
    "orders_created_total",
    "Total orders created",
)

orders_processed_total = Counter(
    "orders_processed_total",
    "Total orders processed (reached completed status)",
)

# ── Middleware ────────────────────────────────────────────────────────────────

# Paths that we don't want to track individually to avoid label explosion
_SKIP_PATHS = {"/metrics", "/health", "/favicon.ico"}


def _normalise_path(path: str) -> str:
    """Replace dynamic path segments (UUIDs, IDs) with {id} placeholder."""
    import re
    path = re.sub(r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "/{id}", path)
    path = re.sub(r"/\d+", "/{id}", path)
    return path


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        endpoint = _normalise_path(path)
        method = request.method

        start = time.perf_counter()
        try:
            response = await call_next(request)
            status_code = str(response.status_code)
        except Exception:
            status_code = "500"
            raise
        finally:
            duration = time.perf_counter() - start
            if path not in _SKIP_PATHS:
                http_requests_total.labels(
                    method=method, endpoint=endpoint, status_code=status_code
                ).inc()
                http_request_duration_seconds.labels(
                    method=method, endpoint=endpoint
                ).observe(duration)
            # Update memory gauge on every request (cheap psutil call)
            memory_usage_bytes.set(psutil.Process().memory_info().rss)

        return response


def update_chaos_gauges(active_modes: list[str]) -> None:
    """Called by chaos router to keep gauges in sync after state changes."""
    all_modes = {"memory_leak", "latency_spike", "error_rate", "cpu_spike"}
    for mode in all_modes:
        active_chaos_modes.labels(mode=mode).set(1 if mode in active_modes else 0)
