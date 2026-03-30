"""SRE Observability Platform — FastAPI application entry point."""
from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from pythonjsonlogger import jsonlogger

from app.middleware.metrics import PrometheusMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware
from app.routers import chaos, health, orders, products


# ── Structured JSON logging setup ────────────────────────────────────────────

def _setup_logging() -> None:
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Silence noisy third-party loggers
    for noisy in ("uvicorn.access", "opentelemetry"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


_setup_logging()
logger = logging.getLogger("sre.app")


# ── FastAPI app ───────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "Starting SRE Observability Platform",
        extra={"version": "1.0.0", "env": os.getenv("APP_ENV", "development")},
    )
    yield
    logger.info("Shutting down SRE Observability Platform")


app = FastAPI(
    title="SRE Observability Platform",
    description=(
        "A production-grade FastAPI service with full LGTM observability stack. "
        "Includes intentional failure injection (chaos engineering) for SRE training."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Middleware — order matters: outermost runs first on request, last on response
app.add_middleware(PrometheusMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Routers
app.include_router(health.router)
app.include_router(orders.router)
app.include_router(products.router)
app.include_router(chaos.router)


@app.get("/", include_in_schema=False)
async def root() -> dict:
    return {
        "service": "sre-observability-platform",
        "version": "1.0.0",
        "docs": "/docs",
        "metrics": "/metrics",
        "health": "/health",
    }


# ── OpenTelemetry instrumentation (must run at import time, before app starts) ─
# FastAPIInstrumentor.instrument_app() must be called before uvicorn starts the app
# so it is called here at module level after the app object is constructed.
def _setup_tracing() -> None:
    from app.middleware.tracing import setup_tracing  # noqa: PLC0415
    setup_tracing(app)


_setup_tracing()
