"""Health check and Prometheus metrics exposition."""
from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

router = APIRouter(tags=["observability"])

_START_TIME = time.time()
APP_VERSION = "1.0.0"


@router.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "healthy",
        "uptime_seconds": round(time.time() - _START_TIME, 1),
        "version": APP_VERSION,
    }


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics() -> PlainTextResponse:
    data = generate_latest()
    return PlainTextResponse(content=data, media_type=CONTENT_TYPE_LATEST)
