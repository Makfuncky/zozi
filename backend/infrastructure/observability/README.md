# Observability

The `infrastructure.observability` package contains the cross-cutting
observability concerns of the Zozi backend: logging, metrics, tracing, and
error handling.

## Tracing

OpenTelemetry distributed tracing lives in `tracing.py`. The module
**imports cleanly** even when the OpenTelemetry SDK is not installed --
it falls back to a no-op tracer so that domain services can still use
`tracer.start_as_current_span(...)` without crashing.

### Activation

Tracing is opt-in. The SDK is configured at process startup by calling
`setup_tracing(app, db_engine=engine)`, typically from `main.py` after
the FastAPI app and SQLAlchemy engine have been created.

| Environment variable          | Effect                                                              |
|-------------------------------|---------------------------------------------------------------------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | When set, OTLP spans are exported to this HTTP endpoint.           |
| `OTEL_SERVICE_NAME`           | Overrides the default `service.name` resource attribute.            |
| `OTEL_DISABLED=1`             | Disables tracing entirely, even if the SDK is installed.            |
| `APP_ENV=production`          | Suppresses the console fallback so production logs stay clean.      |

When no `OTEL_EXPORTER_OTLP_ENDPOINT` is configured **and** the
application is not in production, the module installs a
`SimpleSpanProcessor(ConsoleSpanExporter())` so trace output is visible
in the local terminal.

### Using the tracer in domain services

Import the singleton tracer and use it as a context manager:

```python
from infrastructure.observability.tracing import tracer

def create_order(order, current_user, db, request=None):
    with tracer.start_as_current_span("orders.create_order") as span:
        span.set_attribute("orders.user_id", str(current_user.get("id") or ""))
        # ... business logic ...
```

The `tracer` is a singleton (`opentelemetry.trace.get_tracer("zozi.backend")`),
so importing it from anywhere in the codebase is cheap. Wrapping a
critical method with a span is a one-liner; the only cost is the
attribute writes and the optional export, both of which are no-ops when
no exporter is configured.

### What is instrumented

When `setup_tracing(...)` is called the following are auto-instrumented:

- The FastAPI application (incoming HTTP requests get a span per
  request, with `http.method`, `http.route`, and `http.status_code`
  attributes).
- The SQLAlchemy engine (each query gets a child span with the
  statement).

Critical domain methods (orders, payments, finance) are wrapped
manually with `tracer.start_as_current_span(...)` so that the most
business-relevant traces are clearly named (`orders.create_order`,
`payments.stripe.create_payment_intent`, `finance.apply_order_status_change`,
...).

### Tests

Smoke tests live in `tests/observability/test_tracing.py`. They verify
that the module imports, that the tracer can be used as a context
manager, and that the `OTEL_DISABLED` env-var is honoured.
