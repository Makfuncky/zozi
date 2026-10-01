"""Customer finance router — consolidated from 2 source files."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Body, status
from sqlalchemy.orm import Session

from rbac import get_current_user
from rbac.dependencies import require_feature
from infrastructure.database.database import get_db

from domains.finance.services.payments.payment_engine import (
    get_payment_methods_status,
    get_payment_provider_runtime_config,
    update_payment_provider_runtime_config,
    list_payment_gateway_connections,
    upsert_payment_gateway_connection,
    test_payment_gateway_connection,
    build_payment_finance_quote,
    list_payments as svc_list_payments,
    PaymentIntentRequest,
    StripeCheckoutSessionRequest,
    ConfirmCardPaymentRequest,
    PaymentProviderRuntimeConfigRequest,
    PaymentGatewayConnectionRequest,
    PaymentFinanceQuoteRequest,
    TapChargeRequest,
    ConfirmTapPaymentRequest,
    PayTabsChargeRequest,
    ConfirmPayTabsPaymentRequest,
    PayPalOrderRequest,
    PayPalCaptureRequest,
    ThawaniCheckoutRequest,
    GatewayWizardRequest,
)
from domains.finance.services.payments.gateway_stripe import (
    create_payment_intent,
    create_stripe_checkout_session,
    confirm_card_payment,
    handle_stripe_webhook,
)
from domains.finance.services.payments.gateway_tap import (
    create_tap_charge,
    confirm_tap_payment,
    create_paytabs_charge,
    confirm_paytabs_payment,
    create_thawani_session,
    ConfirmThawaniPaymentRequest,
    handle_tap_webhook,
    handle_paytabs_callback,
    handle_thawani_webhook,
)
from domains.finance.services.payments.gateway_paypal import (
    create_paypal_order,
    capture_paypal_order,
    handle_paypal_webhook,
)
from domains.finance.services.payments.payment_orchestrator import (
    gateway_wizard_step,
    create_generic_gateway_payment,
    confirm_generic_gateway_payment,
    handle_generic_gateway_callback,
    GenericGatewayCreateRequest,
    ConfirmGenericGatewayRequest,
)
from domains.promotions.ports import get_referral_config
from domains.accounts.ports import get_referral_dashboard

router = APIRouter(prefix="/api/v1/customer/finance", tags=["customer", "finance"])


def _resolve_request_country(request: Request) -> Optional[str]:
    """Resolve the shopper's country for country-aware gateway selection.

    The CountryContextMiddleware populates ``request.state.country_code`` from
    the ``X-Country-Code`` header (auto-attached by the storefront) or IP
    geolocation. Returns the normalized code, or None for a global fallback.
    """
    country = getattr(request.state, "country_code", None)
    if not country:
        return None
    country = str(country).strip().upper()
    return country or None


def _require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if str(current_user.get("role") or "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/")
def list_payments(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=500), status: Optional[str] = Query(None), db: Session = Depends(get_db), _: dict = Depends(_require_admin),
    _rf_gate: None = Depends(require_feature("finance.ledger.read"))
):
    return svc_list_payments(db, page=page, page_size=page_size, status=status)


@router.get("/methods")
def payment_methods(request: Request, _: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.read"))
):
    return get_payment_methods_status(db, country_code=_resolve_request_country(request))


@router.get("/config/runtime")
def payment_runtime_config(_: dict = Depends(_require_admin), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.read"))
):
    return get_payment_provider_runtime_config(db)


@router.put("/config/runtime")
def update_runtime_config(
    payload: PaymentProviderRuntimeConfigRequest,
    current_user: dict = Depends(_require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.write")),
):
    return update_payment_provider_runtime_config(payload, current_user, db)


@router.get("/config/gateways")
def list_gateway_connections(_: dict = Depends(_require_admin), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.read"))
):
    return list_payment_gateway_connections(db)


@router.put("/config/gateways/{provider_code}")
def save_gateway_connection(
    provider_code: str,
    payload: PaymentGatewayConnectionRequest,
    current_user: dict = Depends(_require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.write")),
):
    normalized = payload.model_copy(update={"provider_code": provider_code})
    return upsert_payment_gateway_connection(provider_code, normalized, current_user, db)


@router.post("/config/gateways/{provider_code}/test")
def test_gateway_connection(provider_code: str, _: dict = Depends(_require_admin), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.write"))
):
    return test_payment_gateway_connection(provider_code, db)


@router.post("/config/finance-quote")
def finance_quote(
    payload: PaymentFinanceQuoteRequest,
    _: dict = Depends(_require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.read")),
):
    return build_payment_finance_quote(payload, db)


@router.post("/create-payment-intent")
def create_payment_intent_route(
    payload: PaymentIntentRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.write")),
):
    return create_payment_intent(payload, current_user, db)


@router.post("/stripe/create-checkout-session")
def create_stripe_checkout_session_route(
    payload: StripeCheckoutSessionRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.write")),
):
    return create_stripe_checkout_session(payload, current_user, db)


@router.post("/confirm-card-payment")
def confirm_card_payment_route(
    payload: ConfirmCardPaymentRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.write")),
):
    return confirm_card_payment(payload, current_user, db)


@router.post("/tap/create")
async def create_tap_charge_route(
    payload: TapChargeRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.write")),
):
    return await create_tap_charge(payload, current_user, db)


@router.post("/tap/confirm")
async def confirm_tap_payment_route(
    payload: ConfirmTapPaymentRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.write")),
):
    return await confirm_tap_payment(payload, current_user, db)


@router.post("/paytabs/create")
async def create_paytabs_charge_route(
    payload: PayTabsChargeRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.write")),
):
    return await create_paytabs_charge(payload, current_user, db)


@router.post("/paytabs/confirm")
async def confirm_paytabs_payment_route(
    payload: ConfirmPayTabsPaymentRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.write")),
):
    return await confirm_paytabs_payment(payload, current_user, db)


@router.post("/paypal/create")
async def create_paypal_order_route(
    payload: PayPalOrderRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.write")),
):
    return await create_paypal_order(payload, current_user, db)


@router.post("/paypal/capture")
async def capture_paypal_order_route(
    payload: PayPalCaptureRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.write")),
):
    return await capture_paypal_order(payload, current_user, db)


@router.post("/thawani/create-session")
async def create_thawani_session_route(
    payload: ThawaniCheckoutRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.write")),
):
    return await create_thawani_session(payload, current_user, db)


@router.post("/thawani/confirm")
async def confirm_thawani_payment_route(
    payload: ConfirmThawaniPaymentRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.write")),
):
    return await confirm_thawani_payment(payload, current_user, db)


@router.post("/admin/gateway-wizard")
def gateway_wizard(
    payload: GatewayWizardRequest,
    current_user: dict = Depends(_require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.write")),
):
    return gateway_wizard_step(payload, current_user, db)


# ── Universal / generic hosted-redirect gateway (plug-and-play any provider) ──

@router.post("/generic/create")
async def create_generic_gateway_payment_route(
    payload: GenericGatewayCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.write")),
):
    return create_generic_gateway_payment(payload, current_user, db)


@router.post("/generic/confirm")
async def confirm_generic_gateway_payment_route(
    payload: ConfirmGenericGatewayRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.write")),
):
    return confirm_generic_gateway_payment(payload, current_user, db)


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.write"))
):
    return await handle_stripe_webhook(request, db)


@router.post("/tap/webhook")
async def tap_webhook(request: Request, db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.write"))
):
    return await handle_tap_webhook(request, db)


@router.post("/paytabs/callback")
async def paytabs_callback(request: Request, db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.write"))
):
    return await handle_paytabs_callback(request, db)


@router.post("/paypal/webhook")
async def paypal_webhook(request: Request, db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.write"))
):
    return await handle_paypal_webhook(request, db)


@router.post("/thawani/webhook")
async def thawani_webhook(request: Request, db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.write"))
):
    return await handle_thawani_webhook(request, db)


# Generic gateway callbacks are keyed by provider_code so each plug-and-play
# gateway gets its own webhook endpoint: /payments/generic/{code}/callback
@router.post("/generic/{provider_code}/callback")
async def generic_gateway_callback(provider_code: str, request: Request, db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.write"))
):
    return await handle_generic_gateway_callback(request, provider_code, db)


# === From referrals.py ===

@router.get("/config")
def referral_config(db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.read"))
):
    """Public, read-only referral feature configuration."""
    config = get_referral_config(db)
    return {
        "enabled": bool(config.get("enabled", False)),
        "referrer_points": config.get("referrer_points", 0),
        "referee_points": config.get("referee_points", 0),
        "monthly_cap": config.get("monthly_cap", 0),
        "verification_delay_days": config.get("verification_delay_days", 0),
    }


@router.get("/my-code")
def get_referral_code(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.read"))
):
    dashboard = get_referral_dashboard(current_user, db)
    return {
        "referral_code": dashboard.referral_code,
        "referral_link": dashboard.referral_link,
    }
