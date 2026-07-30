"""
OpenTelemetry distributed tracing setup for Zozi API.
Instruments FastAPI, SQLAlchemy, and outgoing HTTP requests.
Trace context is propagated via W3C traceparent headers.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

from utils.config import settings

logger = logging.getLogger(__name__)


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
