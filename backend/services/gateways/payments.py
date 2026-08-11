"""Payment orchestration service.

This is the single orchestration layer between the HTTP boundary
(``controllers/payments``) and the gateway adapters (``providers/payments``).

Responsibilities (keep this layer thin):
  * Select the appropriate gateway provider (by code / country).
  * Delegate gateway-specific operations to ``providers.payments.*`` adapters,
    which own their own settings and SDK/HTTP logic.
  * Hold cross-cutting payment concerns (provider mode checks, response
    shaping) so controllers and routers stay minimal.

The service does NOT contain gateway secrets or SDK calls directly — those
live in ``providers/payments``.
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from providers.payments import config as config_provider
from providers.payments import generic as generic_provider
from providers.payments import paypal as paypal_provider
from providers.payments import paytabs as paytabs_provider
from providers.payments import stripe as stripe_provider
from providers.payments import tap as tap_provider
from providers.payments import thawani as thawani_provider
from providers.payments.base import (
    get_provider,
    is_gateway_configured,
    resolve_gateway_settings,
    dispatch_provider_operation,
    OPERATION_CREATE,
    OPERATION_CONFIRM,
    OPERATION_WEBHOOK,
)
import structlog
logger = structlog.get_logger(__name__)


class PaymentService:
    """Orchestrates payment operations across gateway providers."""

    # ── Provider selection ──────────────────────────────────────────────────

    @staticmethod
    def get_provider(code: str):
        return get_provider(code)

    @staticmethod
    def list_providers() -> list:
        return _list_provider_definitions()

    @staticmethod
    def resolve_settings(code: str, db: Optional[Session] = None):
        return resolve_gateway_settings(code, db)

    @staticmethod
    def is_configured(code: str, db: Optional[Session] = None) -> bool:
        return is_gateway_configured(code, db)

    # ── Generic registry-driven dispatch (gateway-agnostic) ──────────────────
    # A new gateway becomes usable through these methods the moment it is
    # registered in ``providers/payments/config.py`` — no per-gateway code is
    # needed here, in the controller, or in the router.

    @staticmethod
    async def dispatch_create(gateway_code: str, body, current_user: dict, db: Session) -> dict:
        return await dispatch_provider_operation(gateway_code, OPERATION_CREATE, body, current_user, db)

    @staticmethod
    async def dispatch_confirm(gateway_code: str, body, current_user: dict, db: Session) -> dict:
        return await dispatch_provider_operation(gateway_code, OPERATION_CONFIRM, body, current_user, db)

    @staticmethod
    async def dispatch_webhook(gateway_code: str, request, db: Session) -> dict:
        return await dispatch_provider_operation(gateway_code, OPERATION_WEBHOOK, request, db)

    # ── Stripe ─────────────────────────────────────────────────────────────

    @staticmethod
    def create_payment_intent(body, current_user: dict, db: Session) -> dict:
        return stripe_provider.create_payment_intent(body, current_user, db)

    @staticmethod
    def create_stripe_checkout_session(body, current_user: dict, db: Session) -> dict:
        return stripe_provider.create_stripe_checkout_session(body, current_user, db)

    @staticmethod
    def confirm_card_payment(body, current_user: dict, db: Session) -> dict:
        return stripe_provider.confirm_card_payment(body, current_user, db)

    @staticmethod
    async def handle_stripe_webhook(request, db: Session) -> dict:
        return await stripe_provider.handle_stripe_webhook(request, db)

    # ── Tap ────────────────────────────────────────────────────────────────

    @staticmethod
    async def create_tap_charge(body, current_user: dict, db: Session) -> dict:
        return await tap_provider.create_tap_charge(body, current_user, db)

    @staticmethod
    async def confirm_tap_payment(body, current_user: dict, db: Session) -> dict:
        return await tap_provider.confirm_tap_payment(body, current_user, db)

    @staticmethod
    async def handle_tap_webhook(request, db: Session) -> dict:
        return await tap_provider.handle_tap_webhook(request, db)

    # ── PayTabs ────────────────────────────────────────────────────────────

    @staticmethod
    async def create_paytabs_charge(body, current_user: dict, db: Session) -> dict:
        return await paytabs_provider.create_paytabs_charge(body, current_user, db)

    @staticmethod
    async def confirm_paytabs_payment(body, current_user: dict, db: Session) -> dict:
        return await paytabs_provider.confirm_paytabs_payment(body, current_user, db)

    @staticmethod
    async def handle_paytabs_callback(request, db: Session) -> dict:
        return await paytabs_provider.handle_paytabs_callback(request, db)

    # ── PayPal ─────────────────────────────────────────────────────────────

    @staticmethod
    async def create_paypal_order(body, current_user: dict, db: Session) -> dict:
        return await paypal_provider.create_paypal_order(body, current_user, db)

    @staticmethod
    async def capture_paypal_order(body, current_user: dict, db: Session) -> dict:
        return await paypal_provider.capture_paypal_order(body, current_user, db)

    @staticmethod
    async def handle_paypal_webhook(request, db: Session) -> dict:
        return await paypal_provider.handle_paypal_webhook(request, db)

    # ── Thawani ────────────────────────────────────────────────────────────

    @staticmethod
    async def create_thawani_session(body, current_user: dict, db: Session) -> dict:
        return await thawani_provider.create_thawani_session(body, current_user, db)

    @staticmethod
    async def confirm_thawani_payment(body, current_user: dict, db: Session) -> dict:
        return await thawani_provider.confirm_thawani_payment(body, current_user, db)

    @staticmethod
    async def handle_thawani_webhook(request, db: Session) -> dict:
        return await thawani_provider.handle_thawani_webhook(request, db)

    # ── Generic hosted-redirect gateway (plug-and-play any provider) ────────

    @staticmethod
    async def create_generic_gateway_payment(body, current_user: dict, db: Session) -> dict:
        return await generic_provider.create_generic_gateway_payment(body, current_user, db)

    @staticmethod
    async def confirm_generic_gateway_payment(body, current_user: dict, db: Session) -> dict:
        return await generic_provider.confirm_generic_gateway_payment(body, current_user, db)

    @staticmethod
    async def handle_generic_gateway_callback(request, provider_code: str, db: Session) -> dict:
        return await generic_provider.handle_generic_gateway_callback(request, provider_code, db)

    # ── Admin / gateway configuration (delegated to config adapter) ─────────

    @staticmethod
    def get_payment_methods_status(db: Session, country_code: Optional[str] = None) -> dict:
        return config_provider.get_payment_methods_status(db, country_code=country_code)

    @staticmethod
    def get_payment_provider_runtime_config(db: Session) -> Any:
        return config_provider.get_payment_provider_runtime_config(db)

    @staticmethod
    def update_payment_provider_runtime_config(payload, current_user: dict, db: Session) -> Any:
        return config_provider.update_payment_provider_runtime_config(payload, current_user, db)

    @staticmethod
    def list_payment_gateway_connections(db: Session) -> list:
        return config_provider.list_payment_gateway_connections(db)

    @staticmethod
    def upsert_payment_gateway_connection(provider_code: str, payload, current_user: dict, db: Session) -> Any:
        return config_provider.upsert_payment_gateway_connection(provider_code, payload, current_user, db)

    @staticmethod
    def test_payment_gateway_connection(provider_code: str, db: Session) -> Any:
        return config_provider.test_payment_gateway_connection(provider_code, db)

    @staticmethod
    def build_payment_finance_quote(payload, db: Session) -> Any:
        return config_provider.build_payment_finance_quote(payload, db)

    @staticmethod
    def gateway_wizard_step(payload, current_user: dict, db: Session) -> Any:
        return config_provider.gateway_wizard_step(payload, current_user, db)


def _list_provider_definitions() -> list:
    from providers.payments.base import list_providers

    return list_providers()


# Module-level instance used by the controller boundary.
payment_service = PaymentService()
