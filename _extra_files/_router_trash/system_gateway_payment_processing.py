"""Payments routes restored around the recovered payments controller."""
from typing import Optional

from data.controllers_payments_controller import (
    ConfirmCardPaymentRequest,
    ConfirmGenericGatewayRequest,
    ConfirmPayTabsPaymentRequest,
    ConfirmTapPaymentRequest,
    ConfirmThawaniPaymentRequest,
    GatewayWizardRequest,
    GenericGatewayCreateRequest,
    PaymentFinanceQuoteRequest,
    PaymentGatewayConnectionRequest,
    PaymentIntentRequest,
    PaymentProviderRuntimeConfigRequest,
    PayPalCaptureRequest,
    PayPalOrderRequest,
    PayTabsChargeRequest,
    StripeCheckoutSessionRequest,
    TapChargeRequest,
    ThawaniCheckoutRequest,
    build_payment_finance_quote,
    capture_paypal_order,
    confirm_card_payment,
    confirm_generic_gateway_payment,
    confirm_paytabs_payment,
    confirm_tap_payment,
    confirm_thawani_payment,
    create_generic_gateway_payment,
    create_payment_intent,
    create_paypal_order,
    create_paytabs_charge,
    create_stripe_checkout_session,
    create_tap_charge,
    create_thawani_session,
    gateway_wizard_step,
    get_payment_methods_status,
    create_payment,
    confirm_payment,
    handle_gateway_webhook,
    GatewayDispatchRequest,
    get_payment_provider_runtime_config,
    handle_generic_gateway_callback,
    handle_paypal_webhook,
    handle_paytabs_callback,
    handle_stripe_webhook,
    handle_tap_webhook,
    handle_thawani_webhook,
    list_payment_gateway_connections,
    test_payment_gateway_connection,
    update_payment_provider_runtime_config,
    upsert_payment_gateway_connection,
)
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from controllers.auth_controller import get_current_user
from db.database import get_db
from data.models_payments import Payment
from services.db_read import all_rows, count
import structlog
logger = structlog.get_logger(__name__)

router = APIRouter()
public_router = APIRouter()


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


@router.get("/", response_model=dict)
def list_payments(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=500), status: Optional[str] = Query(None), db: Session = Depends(get_db), _: dict = Depends(_require_admin)):
    filters = []
    if status:
        filters.append(Payment.status == status)
    total = count(db, Payment, filters)
    items = all_rows(db, Payment, filters, order_by=Payment.created_at.desc(), offset=(page - 1) * page_size, limit=page_size)
    return {"items": [{"id": p.id, "order_id": p.order_id, "amount": float(p.amount), "payment_method": p.payment_method, "provider": p.provider, "status": p.status, "created_at": p.created_at.isoformat() if p.created_at else None} for p in items], "total": total, "page": page, "per_page": page_size}


@router.get("/methods", response_model=dict)
def payment_methods(request: Request, _: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_payment_methods_status(db, country_code=_resolve_request_country(request))


@router.get("/config/runtime", response_model=dict)
def payment_runtime_config(_: dict = Depends(_require_admin), db: Session = Depends(get_db)):
    return get_payment_provider_runtime_config(db)


@router.put("/config/runtime", response_model=dict)
def update_runtime_config(
    payload: PaymentProviderRuntimeConfigRequest,
    current_user: dict = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    return update_payment_provider_runtime_config(payload, current_user, db)


@router.get("/config/gateways", response_model=dict)
def list_gateway_connections(_: dict = Depends(_require_admin), db: Session = Depends(get_db)):
    return list_payment_gateway_connections(db)


@router.put("/config/gateways/{provider_code}", response_model=dict)
def save_gateway_connection(
    provider_code: str,
    payload: PaymentGatewayConnectionRequest,
    current_user: dict = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    normalized = payload.model_copy(update={"provider_code": provider_code})
    return upsert_payment_gateway_connection(provider_code, normalized, current_user, db)


@router.post("/config/gateways/{provider_code}/test", response_model=dict)
def test_gateway_connection(provider_code: str, _: dict = Depends(_require_admin), db: Session = Depends(get_db)):
    return test_payment_gateway_connection(provider_code, db)


@router.post("/config/finance-quote", response_model=dict)
def finance_quote(
    payload: PaymentFinanceQuoteRequest,
    _: dict = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    return build_payment_finance_quote(payload, db)


@router.post("/create-payment-intent", response_model=dict)
def create_payment_intent_route(
    payload: PaymentIntentRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_payment_intent(payload, current_user, db)


@router.post("/stripe/create-checkout-session", response_model=dict)
def create_stripe_checkout_session_route(
    payload: StripeCheckoutSessionRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_stripe_checkout_session(payload, current_user, db)


@router.post("/confirm-card-payment", response_model=dict)
def confirm_card_payment_route(
    payload: ConfirmCardPaymentRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return confirm_card_payment(payload, current_user, db)


@router.post("/tap/create", response_model=dict)
async def create_tap_charge_route(
    payload: TapChargeRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await create_tap_charge(payload, current_user, db)


@router.post("/tap/confirm", response_model=dict)
async def confirm_tap_payment_route(
    payload: ConfirmTapPaymentRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await confirm_tap_payment(payload, current_user, db)


@router.post("/paytabs/create", response_model=dict)
async def create_paytabs_charge_route(
    payload: PayTabsChargeRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await create_paytabs_charge(payload, current_user, db)


@router.post("/paytabs/confirm", response_model=dict)
async def confirm_paytabs_payment_route(
    payload: ConfirmPayTabsPaymentRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await confirm_paytabs_payment(payload, current_user, db)


@router.post("/paypal/create", response_model=dict)
async def create_paypal_order_route(
    payload: PayPalOrderRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await create_paypal_order(payload, current_user, db)


@router.post("/paypal/capture", response_model=dict)
async def capture_paypal_order_route(
    payload: PayPalCaptureRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await capture_paypal_order(payload, current_user, db)


@router.post("/thawani/create-session", response_model=dict)
async def create_thawani_session_route(
    payload: ThawaniCheckoutRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await create_thawani_session(payload, current_user, db)


@router.post("/thawani/confirm", response_model=dict)
async def confirm_thawani_payment_route(
    payload: ConfirmThawaniPaymentRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await confirm_thawani_payment(payload, current_user, db)


@router.post("/admin/gateway-wizard", response_model=dict)
def gateway_wizard(
    payload: GatewayWizardRequest,
    current_user: dict = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    return gateway_wizard_step(payload, current_user, db)


# ── Universal / generic hosted-redirect gateway (plug-and-play any provider) ──

@router.post("/generic/create", response_model=dict)
async def create_generic_gateway_payment_route(
    payload: GenericGatewayCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_generic_gateway_payment(payload, current_user, db)


@router.post("/generic/confirm", response_model=dict)
async def confirm_generic_gateway_payment_route(
    payload: ConfirmGenericGatewayRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return confirm_generic_gateway_payment(payload, current_user, db)


@public_router.post("/webhook", response_model=dict)
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    return await handle_stripe_webhook(request, db)


@public_router.post("/tap/webhook", response_model=dict)
async def tap_webhook(request: Request, db: Session = Depends(get_db)):
    return await handle_tap_webhook(request, db)


@public_router.post("/paytabs/callback", response_model=dict)
async def paytabs_callback(request: Request, db: Session = Depends(get_db)):
    return await handle_paytabs_callback(request, db)


@public_router.post("/paypal/webhook", response_model=dict)
async def paypal_webhook(request: Request, db: Session = Depends(get_db)):
    return await handle_paypal_webhook(request, db)


@public_router.post("/thawani/webhook", response_model=dict)
async def thawani_webhook(request: Request, db: Session = Depends(get_db)):
    return await handle_thawani_webhook(request, db)


# Generic gateway callbacks are keyed by provider_code so each plug-and-play
# gateway gets its own webhook endpoint: /payments/generic/{code}/callback
@public_router.post("/generic/{provider_code}/callback", response_model=dict)
async def generic_gateway_callback(provider_code: str, request: Request, db: Session = Depends(get_db)):
    return await handle_generic_gateway_callback(request, provider_code, db)


# ── Generic registry-driven routes (gateway-agnostic) ───────────────────────
# These let a *newly registered* gateway be used via /{gateway}/create,
# /{gateway}/confirm and /{gateway}/webhook without editing this router. The
# built-in gateways keep their explicit, typed endpoints above for backward
# compatibility; those are the canonical paths for storefront integration.
# Dispatch is resolved purely through the provider registry, so the HTTP
# boundary stays minimal as more gateways are added.

@router.post("/{gateway_code}/create", response_model=dict)
async def create_gateway_payment_route(
    gateway_code: str,
    payload: GatewayDispatchRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await create_payment(gateway_code, payload, current_user, db)


@router.post("/{gateway_code}/confirm", response_model=dict)
async def confirm_gateway_payment_route(
    gateway_code: str,
    payload: GatewayDispatchRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await confirm_payment(gateway_code, payload, current_user, db)


@public_router.post("/{gateway_code}/webhook", response_model=dict)
async def gateway_webhook_route(gateway_code: str, request: Request, db: Session = Depends(get_db)):
    return await handle_gateway_webhook(gateway_code, request, db)


