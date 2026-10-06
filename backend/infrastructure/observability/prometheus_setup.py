"""
Prometheus metrics instrumentation for Zozi API.
Exposes /metrics endpoint and auto-instruments FastAPI endpoints.

Instrumentation mechanism (frozen): ``prometheus-fastapi-instrumentator``
(TECHNOLOGY_STACK.md §9, "Always mount in production. Do NOT install
prometheus-client standalone"). Nothing here imports ``prometheus_client``
directly.

Why /metrics is mounted unconditionally (OBS2-013)
--------------------------------------------------
This module used to build the instrumentator with
``should_respect_env_var=True, env_var_name="PROMETHEUS_ENABLED"``. The
installed library implements that as::

    # prometheus_fastapi_instrumentator/instrumentation.py:355-360
    def _should_instrumentate(self) -> bool:
        return os.getenv(self.env_var_name, "False").lower() in ["true", "1"]

    # prometheus_fastapi_instrumentator/instrumentation.py:281-282 (expose)
    if self.should_respect_env_var and not self._should_instrumentate():
        return self

so with the variable unset — the default, and the only state a deployer
following TECHNOLOGY_STACK.md §20 is ever in — **neither** the route nor the
instrumentator's metric families were created: ``/metrics`` returned 404 and
all five alert rules in ``monitoring/alerts.yml`` were permanently dead with no
visible symptom. ``PROMETHEUS_ENABLED`` was also absent from the canonical
environment-variable table, so it was an undocumented off-switch for the
platform's entire SLO surface. Law 94 and Law 316 make emission mandatory, so
the endpoint is now mounted in every environment and PROTECTED instead of
absent. Protection replaces disablement; nothing was switched off.

How /metrics is protected (app layer, not the edge)
----------------------------------------------------
Law 36/Law 287/Law 43 apply, and the security invariant for this block is that
an unauthenticated ``/metrics`` on the public internet leaks route names,
per-endpoint latencies and internal topology. Cloudflare is the only ingress in
production, so protection is enforced IN THE APP as well and does not rely on
the edge at all.

* ``development`` and ``test`` (Law 205 APP_ENV): open, so local work, the
  architecture tests and the contract verify command behave as before.
* every other environment: the caller MUST present
  ``Authorization: Bearer <token>``. Anything else gets 403.
* the expected token is DERIVED, never configured as a new secret and never
  hard-coded (Law 32)::

      token = HMAC-SHA256(key=settings.secret_key, msg="zozi:metrics-scrape:v1")

  ``secret_key`` is the already-declared, already-required-in-production
  setting (TECHNOLOGY_STACK.md §20, ``SECRET_KEY``). Domain separation means
  the JWT signing key is never itself a scrape credential, and the derived
  token grants nothing else. Comparison uses :func:`hmac.compare_digest`, so it
  is constant-time.
* if no token can be derived in a non-development environment the endpoint
  fails CLOSED with 503 and an actionable message instead of quietly serving
  the body. (``config.py`` already refuses to boot production without
  ``SECRET_KEY``, so this path is a belt-and-braces guard.)
* rejections are logged at WARNING with the peer address and never with the
  token presented (Law 43, Law 282).

Required Prometheus scraper configuration (this is the other half of OBS2-013 —
an endpoint the scraper cannot reach is as bad as one nobody should reach)::

    scrape_configs:
      - job_name: zozi-backend
        metrics_path: /metrics
        scheme: https
        authorization:
          type: Bearer
          # derive with, inside the app container:
          #   python -c "import hmac,hashlib,os;\
          #     print(hmac.new(os.environ['SECRET_KEY'].encode(),\
          #     b'zozi:metrics-scrape:v1',hashlib.sha256).hexdigest())"
          credentials: <that 64-hex value>
        static_configs:
          - targets: ["api.zozi.com"]

Metric names are owned by ``infrastructure/observability/metrics.py`` and by
``middleware/logging_middleware.py``; this module only mounts and guards the
endpoint, and renames nothing.
"""
from __future__ import annotations

import hashlib
import hmac
import logging

from fastapi import FastAPI
from starlette.types import ASGIApp, Receive, Scope, Send

try:
    from prometheus_fastapi_instrumentator import Instrumentator
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False

from infrastructure.utils.config import settings

logger = logging.getLogger(__name__)

# --- named constants (Law 66: no magic numbers) -----------------------------

#: Path the instrumentator is mounted on. Single source of truth for both the
#: mount and the guard, so the two can never disagree.
METRICS_ENDPOINT = "/metrics"

#: Law 205 APP_ENV values where the endpoint stays open. Development is not a
#: routable production surface; test is not a deployed surface at all.
OPEN_METRICS_ENVIRONMENTS = frozenset({"development", "test"})

#: Domain-separation label for the derived scrape token. Changing this string
#: invalidates every scraper credential, so it is versioned.
_SCRAPE_TOKEN_CONTEXT = "zozi:metrics-scrape:v1"

#: Cap on how much of a rejected request we echo back. Prevents a caller from
#: using the error path to reflect arbitrary bytes.
_MAX_LOGGED_PATH = 200


def _app_env() -> str:
    return str(getattr(settings, "app_env", "") or "").strip().lower()


def metrics_are_public() -> bool:
    """True when ``/metrics`` is served without a bearer token.

    Law 205 drives this: only ``development`` and ``test`` are open.
    """
    return _app_env() in OPEN_METRICS_ENVIRONMENTS


def expected_scrape_token() -> str:
    """Derive the Prometheus bearer token for this deployment.

    Derived from ``settings.secret_key`` with an explicit context label so the
    scrape token is a distinct secret from the JWT signing key: observing or
    leaking the scrape token never compromises session signing, and holding the
    scrape token grants nothing but the metrics body. Returns ``""`` when no
    key material is configured, which the guard treats as "cannot authenticate".
    """
    key = str(getattr(settings, "secret_key", "") or "").strip()
    if not key:
        return ""
    return hmac.new(
        key.encode("utf-8"),
        _SCRAPE_TOKEN_CONTEXT.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _presented_token(authorization: str) -> str:
    """Extract the bearer value from an Authorization header.

    Returns ``""`` when the header is absent or is not a Bearer scheme, so a
    malformed header simply fails authentication instead of raising.
    """
    value = (authorization or "").strip()
    if not value:
        return ""
    scheme, _, credential = value.partition(" ")
    if scheme.strip().lower() != "bearer":
        return ""
    return credential.strip()


class MetricsAuthGuard:
    """Pure-ASGI guard for the metrics endpoint.

    Implemented as raw ASGI rather than ``BaseHTTPMiddleware`` so it adds no
    response buffering and cannot interfere with the streaming/background-task
    handling the request pipeline already depends on. It inspects and, only on
    rejection, short-circuits; on success it is a pass-through and touches
    nothing.
    """

    def __init__(self, app: ASGIApp, endpoint: str = METRICS_ENDPOINT) -> None:
        self.app = app
        self.endpoint = endpoint

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http" or scope.get("path") != self.endpoint:
            await self.app(scope, receive, send)
            return

        if metrics_are_public():
            await self.app(scope, receive, send)
            return

        headers = {
            k.decode("latin-1").lower(): v.decode("latin-1")
            for k, v in scope.get("headers", [])
        }
        expected = expected_scrape_token()
        presented = _presented_token(headers.get("authorization", ""))

        if not expected:
            # Fail closed, never open. A deployment with no key material must
            # not accidentally serve the topology.
            logger.error(
                "metrics_endpoint_unauthenticated_and_unconfigurable",
                extra={
                    "path": self.endpoint,
                    "app_env": _app_env(),
                    "reason": "no secret_key configured, cannot derive a scrape token",
                },
            )
            await self._reject(scope, send, 503, "metrics scrape is not configured")
            return

        if not presented or not hmac.compare_digest(presented, expected):
            peer = self._peer(headers, scope)
            logger.warning(
                "metrics_scrape_rejected",
                extra={
                    "path": self.endpoint,
                    "peer": peer,
                    "app_env": _app_env(),
                    "reason": "missing or invalid bearer token",
                },
            )
            await self._reject(scope, send, 403, "forbidden")
            return

        await self.app(scope, receive, send)

    @staticmethod
    def _peer(headers: dict[str, str], scope: Scope) -> str:
        client = scope.get("client")
        return (headers.get("x-forwarded-for") or (client[0] if client else "unknown"))[:64]

    @staticmethod
    async def _reject(scope: Scope, send: Send, status: int, detail: str) -> None:
        body = f'{{"detail":"{detail}"}}'.encode("utf-8")
        await send({
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("latin-1")),
            ],
        })
        await send({"type": "http.response.body", "body": body})


def setup_metrics(app: FastAPI):
    """Mount and guard ``/metrics``. Returns the instrumentator, or None.

    Kept as the historical entry point name so any existing caller keeps
    working unchanged; ``setup_prometheus`` remains the name main.py uses.
    """
    return setup_prometheus(app)


def setup_prometheus(app: FastAPI):
    if not HAS_PROMETHEUS:
        logger.warning(
            "prometheus_fastapi_instrumentator is not installed; /metrics is not mounted"
        )
        return None

    app_env = _app_env()
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=False,
    )

    instrumentator.instrument(app).expose(
        app,
        endpoint=METRICS_ENDPOINT,
        include_in_schema=False,
    )

    app.add_middleware(MetricsAuthGuard, endpoint=METRICS_ENDPOINT)

    logger.info(
        "metrics_endpoint_mounted",
        extra={
            "path": METRICS_ENDPOINT,
            "app_env": app_env,
            "auth_required": not metrics_are_public(),
            "in_schema": False,
        },
    )

    return instrumentator