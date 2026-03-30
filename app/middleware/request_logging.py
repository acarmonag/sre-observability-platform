"""Structured JSON request logging middleware."""
from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("sre.requests")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())
        start = time.perf_counter()

        # Attach request_id so route handlers can use it
        request.state.request_id = request_id

        # Lazy import to avoid circular dependency at module load time
        from app.services.chaos_service import chaos_service  # noqa: PLC0415
        active_modes = chaos_service.active_modes()

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": 500,
                    "duration_ms": round(duration_ms, 2),
                    "chaos_modes_active": active_modes,
                    "error": str(exc),
                },
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000

        log_level = logging.WARNING if active_modes else logging.INFO
        if status_code >= 500:
            log_level = logging.ERROR
        elif status_code >= 400:
            log_level = logging.WARNING

        logger.log(
            log_level,
            "%s %s %d",
            request.method,
            request.url.path,
            status_code,
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
                "chaos_modes_active": active_modes,
            },
        )

        response.headers["X-Request-ID"] = request_id
        return response
