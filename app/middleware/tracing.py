"""OpenTelemetry tracing setup."""
from __future__ import annotations

import logging
import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.export import ConsoleSpanExporter

logger = logging.getLogger(__name__)


def setup_tracing(app: object) -> None:
    """Configure OTLP exporter pointing at Jaeger and auto-instrument FastAPI."""
    jaeger_endpoint = os.getenv("JAEGER_ENDPOINT", "http://jaeger:4317")

    resource = Resource.create(
        {
            "service.name": "sre-observability-platform",
            "service.version": "1.0.0",
            "deployment.environment": os.getenv("APP_ENV", "development"),
        }
    )

    provider = TracerProvider(resource=resource)

    try:
        otlp_exporter = OTLPSpanExporter(
            endpoint=jaeger_endpoint,
            insecure=True,
        )
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        logger.info("OTel tracing: OTLP exporter configured → %s", jaeger_endpoint)
    except Exception as exc:
        logger.warning("OTel tracing: OTLP exporter failed (%s), falling back to console", exc)
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)  # type: ignore[arg-type]
    logger.info("OTel tracing: FastAPI auto-instrumentation enabled")


def get_tracer() -> trace.Tracer:
    return trace.get_tracer("sre-observability-platform")
