"""
OpenTelemetry distributed tracing setup for Zozi API.
Instruments FastAPI, SQLAlchemy, and outgoing HTTP requests.
Trace context is propagated via W3C traceparent headers.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from infrastructure.utils.config import settings

logger = logging.getLogger(__name__)

# OpenTelemetry is an optional, runtime-only dependency (only needed when an
# OTLP tracing endpoint is configured). Import it defensively so this module
# imports cleanly in environments where the SDK is not installed.
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

    _OTEL_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    logger.debug("opentelemetry not installed; tracing disabled")
    _OTEL_AVAILABLE = False

    # Placeholder so the rest of the module body stays importable when the SDK
    # is absent (tracing simply becomes a no-op).
    def setup_tracing(app, service_name: str = "zozi-api", otlp_endpoint=None, db_engine=None):
        logger.info("OpenTelemetry tracing disabled (SDK not installed)")
        return None



if _OTEL_AVAILABLE:

    def setup_tracing(
        app,
        service_name: str = "zozi-api",
        otlp_endpoint: Optional[str] = None,
        db_engine=None,
    ):
        otlp_endpoint = otlp_endpoint or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")

        if not otlp_endpoint:
            logger.info("OpenTelemetry tracing disabled (no OTLP endpoint configured)")
            return

        resource = Resource.create({
            "service.name": service_name,
            "service.version": settings.app_version or "1.0.0",
            "deployment.environment": settings.app_env or "development",
        })

        provider = TracerProvider(resource=resource)
        processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint))
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

        FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)

        if db_engine is not None:
            SQLAlchemyInstrumentor().instrument(engine=db_engine)

        logger.info("OpenTelemetry tracing initialized", endpoint=otlp_endpoint)


class _NoOpTracer:
    """Fallback tracer when OpenTelemetry is not installed."""

    def start_as_current_span(self, name, *args, **kwargs):
        class _NoOpSpan:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                return False

            def set_attribute(self, *args, **kwargs):
                pass

        return _NoOpSpan()


if _OTEL_AVAILABLE:
    tracer = trace.get_tracer(__name__)
else:
    tracer = _NoOpTracer()


def is_tracing_enabled() -> bool:
    """Return True when OpenTelemetry tracing is configured and active."""
    if not _OTEL_AVAILABLE:
        return False
    if os.environ.get("OTEL_DISABLED"):
        return False
    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    return bool(otlp_endpoint)

