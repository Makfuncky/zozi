from __future__ import annotations

import os
from typing import Optional

from providers.payments.stripe_sdk import stripe

__all__ = [
    "resolve_stripe_secret_key",
    "resolve_stripe_webhook_secret",
    "apply_stripe_runtime_key",
    "is_stripe_configured",
    "resolve_tap_secret_key",
    "resolve_tap_webhook_secret",
    "resolve_tap_api_base_url",
    "resolve_tap_webhook_url",
    "is_tap_configured",
    "resolve_paytabs_server_key",
    "resolve_paytabs_webhook_secret",
    "resolve_paytabs_profile_id",
    "resolve_paytabs_api_base_url",
    "resolve_paytabs_callback_url",
    "is_paytabs_configured",
    "resolve_thawani_secret_key",
    "resolve_thawani_publishable_key",
    "resolve_thawani_api_base_url",
    "resolve_thawani_webhook_secret",
    "is_thawani_configured",
    "resolve_paypal_credentials",
    "is_paypal_configured",
]


def _is_non_placeholder_secret(secret: str, prefixes: tuple[str, ...]) -> bool:
    if not secret:
        return False
    return any(secret.startswith(p) for p in prefixes)


def resolve_stripe_secret_key() -> str:
    return str(
        os.getenv("STRIPE_SECRET_KEY")
        or (stripe.api_key if stripe else "")
        or ""
    ).strip()


def resolve_stripe_webhook_secret() -> str:
    return str(os.getenv("STRIPE_WEBHOOK_SECRET") or "").strip()


def apply_stripe_runtime_key() -> str:
    resolved = resolve_stripe_secret_key()
    if stripe:
        stripe.api_key = resolved
    return resolved


def is_stripe_configured() -> bool:
    key = apply_stripe_runtime_key()
    return _is_non_placeholder_secret(key, ("sk_test_", "sk_live_"))


def resolve_tap_secret_key() -> str:
    return str(os.getenv("TAP_SECRET_KEY") or "").strip()


def resolve_tap_webhook_secret() -> str:
    return str(os.getenv("TAP_WEBHOOK_SECRET") or "").strip()


def resolve_tap_api_base_url() -> str:
    return str(os.getenv("TAP_API_BASE_URL") or "https://api.tap.company").strip().rstrip("/")


def resolve_tap_webhook_url() -> str:
    return str(os.getenv("TAP_WEBHOOK_URL") or "").strip()


def is_tap_configured() -> bool:
    key = resolve_tap_secret_key()
    return _is_non_placeholder_secret(key, ("sk_test_", "sk_live_", "sk_"))


def resolve_paytabs_server_key() -> str:
    return str(os.getenv("PAYTABS_SERVER_KEY") or "").strip()


def resolve_paytabs_webhook_secret() -> str:
    return str(os.getenv("PAYTABS_WEBHOOK_SECRET") or "").strip()


def resolve_paytabs_profile_id() -> str:
    return str(os.getenv("PAYTABS_PROFILE_ID") or "").strip()


def resolve_paytabs_api_base_url() -> str:
    configured = str(os.getenv("PAYTABS_API_BASE_URL") or "").strip()
    return configured.rstrip("/") or "https://secure.paytabs.com"


def resolve_paytabs_callback_url() -> str:
    return str(os.getenv("PAYTABS_CALLBACK_URL") or "").strip()


def is_paytabs_configured() -> bool:
    server_key = resolve_paytabs_server_key()
    profile_id = resolve_paytabs_profile_id()
    return bool(server_key and profile_id)


def resolve_thawani_secret_key() -> str:
    return str(os.getenv("THAWANI_SECRET_KEY") or "").strip()


def resolve_thawani_publishable_key() -> str:
    return str(os.getenv("THAWANI_PUBLISHABLE_KEY") or "").strip()


def resolve_thawani_api_base_url() -> str:
    configured = str(os.getenv("THAWANI_API_BASE_URL") or "").strip()
    return configured.rstrip("/") or "https://uatcheckout.thawani.om/api/v1"


def resolve_thawani_webhook_secret() -> str:
    return str(os.getenv("THAWANI_WEBHOOK_SECRET") or "").strip()


def is_thawani_configured() -> bool:
    secret_key = resolve_thawani_secret_key()
    publishable_key = resolve_thawani_publishable_key()
    return bool(secret_key and publishable_key)


def resolve_paypal_credentials() -> tuple[Optional[str], Optional[str], str]:
    client_id = str(os.getenv("PAYPAL_CLIENT_ID") or "").strip() or None
    secret = str(os.getenv("PAYPAL_SECRET") or "").strip() or None
    mode = str(os.getenv("PAYPAL_MODE", "sandbox") or "sandbox").strip().lower()
    base_url = "https://api-m.paypal.com" if mode == "live" else "https://api-m.sandbox.paypal.com"
    return client_id, secret, base_url


def is_paypal_configured() -> bool:
    client_id, secret, _ = resolve_paypal_credentials()
    return bool(client_id and secret)
