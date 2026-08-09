"""
End-to-end Stripe test-mode checkout validation for Zozi.

Flow:
1. Validate Stripe env variables are configured.
2. Boot FastAPI app in-process via TestClient.
3. Create admin + customer users and log them in.
4. Create a product as admin.
5. Create a card order as customer.
6. Create Stripe PaymentIntent via backend endpoint.
7. Confirm intent on Stripe test rail using `pm_card_visa`.
8. Finalize order through `/payments/confirm-card-payment`.
9. Verify order state is confirmed + paid_at populated.

Run:
    python scripts/validate_stripe_testmode_checkout.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import stripe
from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def _read_env_value(path: Path, key: str) -> str:
    if not path.exists():
        return ""
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip() == key:
            return v.strip()
    return ""


def _looks_real_stripe_key(value: str, prefix: str) -> bool:
    if not value or not value.startswith(prefix):
        return False
    lowered = value.lower()
    bad_markers = ("your_", "replace", "change", "...", "example")
    return not any(marker in lowered for marker in bad_markers)


def _require_env() -> tuple[str, str, str]:
    backend_env = BACKEND_DIR / ".env"
    frontend_env = REPO_ROOT / "frontend" / "web_app" / ".env.local"

    stripe_secret = _read_env_value(backend_env, "STRIPE_SECRET_KEY")
    stripe_webhook_secret = _read_env_value(backend_env, "STRIPE_WEBHOOK_SECRET")
    publishable = _read_env_value(frontend_env, "NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY")

    problems: list[str] = []
    if not _looks_real_stripe_key(stripe_secret, "sk_test_"):
        problems.append("STRIPE_SECRET_KEY in backend/.env is missing or not a valid test key.")
    if not _looks_real_stripe_key(publishable, "pk_test_"):
        problems.append("NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY in frontend/web_app/.env.local is missing or not a valid test key.")
    if problems:
        print("Stripe test-mode validation blocked:")
        for item in problems:
            print(f"- {item}")
        raise SystemExit(2)

    if not stripe_webhook_secret.startswith("whsec_"):
        print(
            "Warning: STRIPE_WEBHOOK_SECRET is missing or invalid; "
            "webhook-signature verification is not validated in this checkout E2E run."
        )

    return stripe_secret, stripe_webhook_secret, publishable


def _expect_ok(response, expected: tuple[int, ...] = (200, 201), label: str = "request") -> dict[str, Any]:
    if response.status_code not in expected:
        body = response.text
        raise RuntimeError(f"{label} failed ({response.status_code}): {body}")
    try:
        return response.json()
    except Exception:
        raise RuntimeError(f"{label} returned non-JSON response: {response.text}")


def _register_if_needed(client: TestClient, payload: dict[str, Any]) -> None:
    response = client.post("/auth/register", json=payload)
    if response.status_code in (200, 201):
        return
    detail = ""
    try:
        detail = str(response.json())
    except Exception:
        detail = response.text
    if response.status_code == 400 and "already" in detail.lower():
        return
    raise RuntimeError(f"register failed ({response.status_code}): {detail}")


def _login_headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post("/auth/login", data={"username": email, "password": password})
    data = _expect_ok(response, expected=(200,), label=f"login {email}")
    token = data.get("access_token")
    if not token:
        raise RuntimeError(f"login for {email} did not return access_token")
    return {"Authorization": f"Bearer {token}"}


def _create_product(client: TestClient, admin_headers: dict[str, str], unique_id: str) -> int:
    me = _expect_ok(client.get("/auth/me", headers=admin_headers), label="admin /auth/me")
    supplier_id = me.get("id")
    if not supplier_id:
        raise RuntimeError("admin user id missing")

    product_payload = {
        "name": f"Stripe E2E Widget {unique_id}",
        "description": "Stripe test mode checkout validation product",
        "price": 50.0,
        "category": "General",
        "stock": 20,
        "image_url": "http://img.test/stripe-e2e.png",
        "supplier_id": supplier_id,
    }
    created = _expect_ok(
        client.post("/products/", json=product_payload, headers=admin_headers),
        label="create product",
    )
    product_id = created.get("id")
    if not product_id:
        raise RuntimeError("product id missing in create product response")
    return int(product_id)


def _create_order(client: TestClient, user_headers: dict[str, str], product_id: int) -> int:
    payload = {
        "items": [{"product_id": product_id, "quantity": 1}],
        "shipping_address": "Stripe Test Street, Dubai, 00000, UAE",
        "payment_method": "card",
    }
    created = _expect_ok(client.post("/orders/", json=payload, headers=user_headers), expected=(201,), label="create order")
    order_id = created.get("id")
    if not order_id:
        raise RuntimeError("order id missing")
    return int(order_id)


def main() -> int:
    print("Validating Stripe env setup...")
    stripe_secret, stripe_webhook_secret, publishable_key = _require_env()
    print(
        "Stripe env configured:",
        json.dumps(
            {
                "secret_prefix": stripe_secret[:10],
                "publishable_prefix": publishable_key[:10],
                "webhook_prefix": stripe_webhook_secret[:8],
            }
        ),
    )

    from main import app  # imported only after sys.path injection
    from utils.config import settings

    # Keep runtime settings consistent in case app was imported with stale process vars.
    stripe.api_key = settings.stripe_secret_key or stripe_secret
    if settings.stripe_api_version:
        stripe.api_version = settings.stripe_api_version

    with TestClient(app) as client:
        unique_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        admin_email = f"stripe_admin_{unique_id}@zozi.test"
        user_email = f"stripe_user_{unique_id}@zozi.test"
        password = "TestPass123!"

        print("Registering users...")
        _register_if_needed(
            client,
            {
                "email": admin_email,
                "username": f"stripe_admin_{unique_id}",
                "password": password,
                "role": "admin",
            },
        )
        _register_if_needed(
            client,
            {
                "email": user_email,
                "username": f"stripe_user_{unique_id}",
                "password": password,
                "role": "customer",
            },
        )

        print("Logging in users...")
        admin_headers = _login_headers(client, admin_email, password)
        user_headers = _login_headers(client, user_email, password)

        print("Creating product and order...")
        product_id = _create_product(client, admin_headers, unique_id)
        order_id = _create_order(client, user_headers, product_id)

        print("Creating payment intent via backend...")
        intent_resp = _expect_ok(
            client.post(
                "/payments/create-payment-intent",
                json={"order_id": order_id, "currency": "AED", "country": "AE"},
                headers=user_headers,
            ),
            label="create payment intent",
        )
        payment_intent_id = intent_resp.get("payment_intent_id")
        if not payment_intent_id:
            raise RuntimeError("payment_intent_id missing from backend create-payment-intent response")

        print(f"Confirming Stripe PaymentIntent {payment_intent_id} in test mode...")
        confirmed_intent = stripe.PaymentIntent.confirm(
            payment_intent_id,
            payment_method="pm_card_visa",
        )
        if str(getattr(confirmed_intent, "status", "")).lower() not in {"succeeded", "processing"}:
            raise RuntimeError(f"Stripe intent status after confirm is {getattr(confirmed_intent, 'status', None)}")

        print("Finalizing order via backend confirm-card-payment...")
        final_status = None
        for attempt in range(5):
            confirm_resp = _expect_ok(
                client.post(
                    "/payments/confirm-card-payment",
                    json={"order_id": order_id, "payment_intent_id": payment_intent_id},
                    headers=user_headers,
                ),
                label="confirm-card-payment",
            )
            final_status = confirm_resp.get("status")
            if final_status == "confirmed":
                break
            if final_status == "failed":
                raise RuntimeError("Backend confirm-card-payment reported failed")
            time.sleep(1.0)

        print("Checking order state...")
        order = _expect_ok(client.get(f"/orders/{order_id}", headers=user_headers), label="get order")
        if order.get("status") != "confirmed":
            raise RuntimeError(f"Order status expected confirmed, got {order.get('status')}")
        if not order.get("paid_at"):
            raise RuntimeError("Order paid_at was not set")

        print("Stripe test-mode checkout validation PASSED.")
        print(
            json.dumps(
                {
                    "order_id": order_id,
                    "payment_intent_id": payment_intent_id,
                    "backend_confirm_status": final_status,
                    "order_status": order.get("status"),
                },
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    os.chdir(REPO_ROOT)
    raise SystemExit(main())
