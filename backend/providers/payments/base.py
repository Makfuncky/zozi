"""Payment gateway provider contract and registry.

Architecture (proper layered protocol)
=====================================
    routers/payments.py        → routing only (minimal)
    controllers/payments.py    → HTTP boundary (minimal: validate, auth, call service)
    services/payments.py       → orchestration (provider selection, delegates to providers)
    providers/payments/        → GATEWAY SETTINGS + adapters (each gateway owns its config)

Every payment gateway lives under ``providers/payments/<gateway>.py`` and is
responsible for **owning its own settings/config resolution** (API keys, webhook
secrets, modes, base URLs) via the shared helpers in
``providers.payments.config`` and the ``PaymentGatewayConnection`` database
record. No global ``settings`` object is the source of truth for gateway
secrets — providers resolve them from the DB connection + environment.

This module defines the uniform contract a gateway must satisfy and a registry
so the service/controller layers can select a provider by code/country without
importing concrete gateway modules directly.
"""
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session
import structlog
logger = structlog.get_logger(__name__)


# Standard operation names a gateway may register. Keeping these constant lets
# the service/controller/router layers dispatch by gateway code without ever
# importing a concrete gateway module.
OPERATION_CREATE = "create"
OPERATION_CONFIRM = "confirm"
OPERATION_WEBHOOK = "webhook"


@dataclass
class GatewaySettings:
    """Resolved configuration for a single payment gateway.

    This is the canonical "settings" object a gateway exposes. It is built by
    the gateway's own settings resolver (from ``PaymentGatewayConnection`` +
    environment) so gateway secrets never leak into the global app settings.
    """

    provider_code: str
    provider_kind: str
    display_name: str
    is_enabled: bool
    mode: str = "test"
    public_key: Optional[str] = None
    secret_key: Optional[str] = None
    webhook_secret: Optional[str] = None
    api_base_url: Optional[str] = None
    webhook_url: Optional[str] = None
    supports_customer_checkout: bool = False
    supports_payouts: bool = False
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def is_live(self) -> bool:
        return self.mode == "live"

    def is_usable(self) -> bool:
        return self.is_enabled and bool(self.secret_key)


@dataclass(frozen=True)
class GatewayDefinition:
    """Registration metadata for a gateway provider.

    ``operations`` maps a standard operation name (``OPERATION_CREATE``,
    ``OPERATION_CONFIRM``, ``OPERATION_WEBHOOK``) to the concrete callable
    implemented by the gateway adapter module. This is what lets the
    service/controller/router layers stay gateway-agnostic: adding a new
    gateway only requires a provider module + a ``register_provider`` entry
    with its operations — no edits to services, controllers, or routers.
    """

    code: str
    kind: str
    label: str
    module: str
    settings_resolver: Callable[[Optional[Session]], Optional[GatewaySettings]]
    is_configured: Callable[[Optional[Session]], Any]
    operations: dict[str, Callable] = field(default_factory=dict)


class PaymentGatewayProvider(ABC):
    """Contract every gateway adapter under ``providers/payments`` must satisfy."""

    code: str = ""
    kind: str = ""

    @abstractmethod
    def resolve_settings(self, db: Optional[Session] = None) -> Optional[GatewaySettings]:
        """Return the gateway's resolved settings (owns its own config)."""

    @abstractmethod
    def is_configured(self, db: Optional[Session] = None) -> bool:
        """Return whether the gateway has usable credentials configured."""

    @abstractmethod
    def supports_payment_method(self, method: str) -> bool:
        """Return whether the gateway can process the given payment method."""


# ── Registry ─────────────────────────────────────────────────────────────────

PAYMENT_PROVIDER_REGISTRY: dict[str, GatewayDefinition] = {}


def register_provider(definition: GatewayDefinition) -> None:
    PAYMENT_PROVIDER_REGISTRY[definition.code] = definition


def get_provider(code: str) -> Optional[GatewayDefinition]:
    return PAYMENT_PROVIDER_REGISTRY.get(code)


def list_providers() -> list[GatewayDefinition]:
    return list(PAYMENT_PROVIDER_REGISTRY.values())


def resolve_gateway_settings(code: str, db: Optional[Session] = None) -> Optional[GatewaySettings]:
    definition = get_provider(code)
    if definition is None:
        return None
    return definition.settings_resolver(db)


def is_gateway_configured(code: str, db: Optional[Session] = None) -> bool:
    definition = get_provider(code)
    if definition is None:
        return False
    result = definition.is_configured(db)
    if isinstance(result, tuple):
        return bool(result[0])
    return bool(result)


def get_gateway_operation(code: str, operation: str) -> Optional[Callable]:
    """Return the registered callable for ``operation`` on gateway ``code``."""
    definition = get_provider(code)
    if definition is None:
        return None
    return (definition.operations or {}).get(operation)


async def dispatch_provider_operation(code: str, operation: str, *args, **kwargs) -> Any:
    """Invoke a gateway operation by code, resolving it solely via the registry.

    This is the single dispatch point used by ``services``/``controllers``/
    ``routers`` so they never import concrete gateway modules. Awaiting is
    transparent: handlers may be sync or async.
    """
    handler = get_gateway_operation(code, operation)
    if handler is None:
        raise NotImplementedError(
            f"Payment gateway '{code}' does not support operation '{operation}'"
        )
    result = handler(*args, **kwargs)
    if asyncio.iscoroutine(result):
        result = await result
    return result
