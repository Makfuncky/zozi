"""Stripe Connect provider.

Owns the Stripe SDK calls for connected-account payout dispatch
(``Account.create`` / ``Account.modify`` / ``Transfer.create``) so the finance
transfer service orchestrates through these helpers instead of touching the Stripe
SDK directly. This keeps the vendor SDK calls in the provider layer.
"""
from __future__ import annotations

import logging
from typing import Any

from providers.payments.stripe_sdk import stripe

logger = logging.getLogger(__name__)


def configure_stripe_connect(api_key: str | None = None, api_version: str | None = None) -> None:
    """Set the Stripe API key/version from the supplied values."""
    key = (api_key or "").strip()
    if not key:
        raise RuntimeError("STRIPE_SECRET_KEY must be configured for Stripe Connect payout dispatch.")
    stripe.api_key = key
    version = (api_version or "").strip()
    if version:
        stripe.api_version = version


def create_connect_account(**kwargs: Any) -> Any:
    return stripe.Account.create(**kwargs)


def modify_connect_account(account_id: str, **kwargs: Any) -> Any:
    return stripe.Account.modify(account_id, **kwargs)


def create_connect_transfer(**kwargs: Any) -> Any:
    return stripe.Transfer.create(**kwargs)


__all__ = [
    "configure_stripe_connect",
    "create_connect_account",
    "modify_connect_account",
    "create_connect_transfer",
]
