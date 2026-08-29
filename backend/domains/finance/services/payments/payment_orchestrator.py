"""Payment orchestrator — gateway wizard, generic gateway, reconciliation, auto-enable, badge billing."""

from typing import Any, Optional

from fastapi import Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from domains.orders.models.order_entities import Order
from domains.finance.models.finance import GatewaySettlementSchedule

from domains.finance.services.payments.payment_engine import (
    _normalize_gateway_code,
    _optional_text,
    GatewayWizardRequest,
    GatewayWizardResponse,
    PaymentGatewayConnectionResponse,
    test_payment_gateway_connection,
)

def gateway_wizard_step(

    payload: GatewayWizardRequest,

    current_user: dict[str, Any],

    db: Session,

) -> GatewayWizardResponse:

    """Process a single step of the Gateway Wizard."""

    normalized_code = _normalize_gateway_code(payload.provider_code)

    

    if payload.step == "credentials":

        return _gateway_wizard_credentials_step(normalized_code, payload, current_user, db)

    elif payload.step == "fees":

        return _gateway_wizard_fees_step(normalized_code, payload, current_user, db)

    elif payload.step == "routing":

        return _gateway_wizard_routing_step(normalized_code, payload, current_user, db)

    elif payload.step == "test":

        return _gateway_wizard_test_step(normalized_code, payload, current_user, db)

    

    return GatewayWizardResponse(

        provider_code=normalized_code,

        display_name=payload.display_name or normalized_code.replace("_", " ").title(),

        provider_kind=payload.provider_kind,

        step=payload.step,

        next_step=None,

    )





def _gateway_wizard_credentials_step(

    provider_code: str,

    payload: GatewayWizardRequest,

    current_user: dict,

    db: Session,

) -> GatewayWizardResponse:

    """Step 1: Validate and store credentials."""

    credentials_valid = False

    

    if payload.secret_key and payload.webhook_secret:

        adapter = PaymentGatewayRegistry.get_or_raise(provider_code)

        adapter_instance = adapter()

        credentials_valid = adapter_instance.validate_credentials({

            "secret_key": payload.secret_key,

            "webhook_secret": payload.webhook_secret,

            "public_key": payload.public_key,

            "merchant_id": payload.merchant_id,

            "api_base_url": payload.api_base_url,

        })

    

    return GatewayWizardResponse(

        provider_code=provider_code,

        display_name=payload.display_name or provider_code.replace("_", " ").title(),

        provider_kind=payload.provider_kind,

        step="credentials",

        is_enabled=True,

        credentials_valid=credentials_valid,

        next_step="fees" if credentials_valid else None,

    )





def _gateway_wizard_fees_step(

    provider_code: str,

    payload: GatewayWizardRequest,

    current_user: dict,

    db: Session,

) -> GatewayWizardResponse:

    """Step 2: Configure fees."""

    return GatewayWizardResponse(

        provider_code=provider_code,

        display_name=payload.display_name or provider_code.replace("_", " ").title(),

        provider_kind=payload.provider_kind,

        step="fees",

        is_enabled=True,

        credentials_valid=True,

        fees_configured=True,

        next_step="routing",

    )





def _gateway_wizard_routing_step(

    provider_code: str,

    payload: GatewayWizardRequest,

    current_user: dict,

    db: Session,

) -> GatewayWizardResponse:

    """Step 3: Configure routing rules."""

    return GatewayWizardResponse(

        provider_code=provider_code,

        display_name=payload.display_name or provider_code.replace("_", " ").title(),

        provider_kind=payload.provider_kind,

        step="routing",

        is_enabled=True,

        credentials_valid=True,

        fees_configured=True,

        routing_configured=True,

        next_step="test",

    )





def _gateway_wizard_test_step(

    provider_code: str,

    payload: GatewayWizardRequest,

    current_user: dict,

    db: Session,

) -> GatewayWizardResponse:

    """Step 4: Test the gateway connection."""

    try:

        test_result = test_payment_gateway_connection(provider_code, db)

        return GatewayWizardResponse(

            provider_code=provider_code,

            display_name=payload.display_name or provider_code.replace("_", " ").title(),

            provider_kind=payload.provider_kind,

            step="test",

            is_enabled=True,

            credentials_valid=True,

            fees_configured=True,

            routing_configured=True,

            test_passed=test_result.test_status == "passed",

            test_message=test_result.message,

            next_step=None,

        )

    except HTTPException as exc:

        return GatewayWizardResponse(

            provider_code=provider_code,

            display_name=payload.display_name or provider_code.replace("_", " ").title(),

            provider_kind=payload.provider_kind,

            step="test",

            is_enabled=False,

            credentials_valid=True,

            fees_configured=True,

            routing_configured=True,

            test_passed=False,

            test_message=str(exc.detail),

            next_step=None,

        )





# ── Universal / generic hosted-redirect gateway adapter ────────────────────────

#

# This adapter makes ANY payment provider plug-and-play. An admin configures a

# gateway connection (provider_kind="custom") with:

#   * api_base_url / webhook_url  — provider endpoints

#   * secret_key / public_key     — credentials

#   * extra_config (JSON) describing how to build the hosted checkout redirect:

#       redirect_url_template : URL with {order_id}{amount}{currency}{reference}

#                               {callback_url}{success_url}{cancel_url}

#                               {customer_email}{customer_name}{description}

#       create_url            : (optional) server-side endpoint to call first to

#                               obtain a hosted-checkout URL (Paymob-style).

#       create_method         : GET|POST (default POST)

#       create_auth_header    : template, e.g. "Bearer {secret_key}"

#       create_body           : {logical_field: actual_field} mapping

#       redirect_url_field    : response JSON key holding the redirect URL

#       redirect_method       : GET|POST (default GET) used when create_url returns

#                               a URL the customer must POST to.

#       order_id_field        : callback JSON/form field holding the order id

#       transaction_ref_field : callback field holding the gateway reference

#       status_field          : callback field holding the status

#       success_values        : list of statuses considered successful

#                               (default ["paid","completed","success","approved",

#                                "captured","a","A","success","done"])

# The storefront redirects the customer to the resulting URL; the provider then

# calls back to /payments/generic/{code}/callback to finalize the order.





class GenericGatewayCreateRequest(BaseModel):

    gateway_code: str

    order_id: Optional[int] = None

    currency: Optional[str] = None

    country: Optional[str] = None

    description: str = "ZOZI Purchase"

    success_url: str = ""

    cancel_url: str = ""



    def model_post_init(self, __context: object) -> None:  # noqa: D401

        if not self.success_url:

            self.success_url = (

                f"{settings.frontend_url}/checkout?generic_order_id={self.order_id}"

                f"&gateway={self.gateway_code}"

            )

        if not self.cancel_url:

            self.cancel_url = (

                f"{settings.frontend_url}/checkout?generic_order_id={self.order_id}"

                f"&gateway={self.gateway_code}&generic_cancelled=true"

            )





class ConfirmGenericGatewayRequest(BaseModel):

    order_id: int

    gateway_code: str

    reference: Optional[str] = None





_GENERIC_DEFAULT_SUCCESS_VALUES = (

    "paid", "completed", "complete", "success", "successful", "approved",

    "captured", "done", "settled", "a", "A", "paid_success",

)





def _resolve_gateway_callback_base(db: Session, provider_code: str) -> str:

    record = _get_gateway_connection_record(db, provider_code)

    configured = _optional_text(getattr(record, "webhook_url", None)) if record else None

    if configured:

        return configured.rstrip("/")

    base = os.getenv("BACKEND_PUBLIC_URL") or getattr(settings, "backend_public_url", "") or getattr(settings, "frontend_url", "")

    return str(base).rstrip("/")





def _fill_gateway_template(template: str, ctx: dict[str, Any]) -> str:

    def repl(match: "re.Match[str]") -> str:

        key = match.group(1)

        value = ctx.get(key, "")

        return str(value if value is not None else "")



    return re.sub(r"\{([a-zA-Z0-9_]+)\}", repl, template)





def _build_generic_redirect(

    gateway: PaymentGatewayConnectionResponse,

    order: Order,

    reference: str,

    currency_code: str,

    converted_total: float,

    db: Session,

) -> dict[str, Any]:

    record = _get_gateway_connection_record(db, gateway.provider_code)

    extra = _json_load_dict(getattr(record, "extra_config_json", None)) if record else {}



    callback_url = f"{_resolve_gateway_callback_base(db, gateway.provider_code)}/payments/generic/{gateway.provider_code}/callback"

    ctx: dict[str, Any] = {

        "order_id": order.id,

        "amount": converted_total,

        "currency": currency_code,

        "reference": reference,

        "callback_url": callback_url,

        "success_url": "",

        "cancel_url": "",

        "customer_email": "",

        "customer_name": "",

        "description": f"ZOZI Order #{order.id}",

    }



    create_url = _optional_text(extra.get("create_url"))

    if create_url:

        create_method = str(extra.get("create_method", "POST")).upper()

        auth_header_tpl = _optional_text(extra.get("create_auth_header"))

        headers: dict[str, str] = {"content-type": "application/json", "accept": "application/json"}

        if auth_header_tpl:

            headers["Authorization"] = _fill_gateway_template(auth_header_tpl, {**ctx, "secret_key": _optional_text(getattr(record, "secret_key", None)) or ""})

        body_fields = extra.get("create_body") or {}

        body: dict[str, Any] = {}

        for logical, actual in body_fields.items():

            body[actual] = ctx.get(logical)

        body["order_id"] = order.id

        body["amount"] = converted_total

        body["currency"] = currency_code

        body["customer_email"] = getattr(order, "customer_email", None) or ctx["customer_email"]

        body["customer_name"] = getattr(order, "customer_name", None) or ctx["customer_name"]

        body["reference"] = reference

        body["callback_url"] = callback_url

        body["return_url"] = ctx["success_url"] or f"{settings.frontend_url}/checkout?generic_order_id={order.id}&gateway={gateway.provider_code}"

        try:

            with httpx.Client(timeout=20) as client:

                resp = client.request(create_method, create_url, headers=headers, json=body)

                if resp.status_code >= 400:

                    raise HTTPException(status_code=502, detail=f"Gateway '{gateway.provider_code}' create call failed ({resp.status_code})")

                data = resp.json()

        except HTTPException:

            raise

        except Exception as exc:

            logger.error("generic gateway create call error: %s", exc)

            raise HTTPException(status_code=502, detail="Gateway connection error")

        redirect_url = _optional_text(data.get(str(extra.get("redirect_url_field", "redirect_url"))))

        redirect_method = str(extra.get("redirect_method", "GET")).upper()

        if not redirect_url:

            raise HTTPException(status_code=502, detail="Gateway did not return a redirect URL")

        return {"redirect_url": redirect_url, "redirect_method": redirect_method, "reference": reference}



    template = _optional_text(extra.get("redirect_url_template")) or _optional_text(gateway.api_base_url)

    if not template:

        raise HTTPException(status_code=503, detail="Gateway redirect URL is not configured")

    return {"redirect_url": _fill_gateway_template(template, ctx), "redirect_method": "GET", "reference": reference}





def create_generic_gateway_payment(body: GenericGatewayCreateRequest, current_user: dict, db: Session) -> dict:

    """Initiate a hosted-redirect payment for any configured gateway."""

    normalized_code = _normalize_gateway_code(body.gateway_code)

    order = _get_user_order(body.order_id, current_user, db)

    if order.paid_at is not None:

        raise HTTPException(status_code=409, detail="Order is already paid")

    if order.status in INVENTORY_RELEASE_STATUSES:

        raise HTTPException(status_code=409, detail="Order is already closed")



    order_country = str(getattr(order, "shipping_country", "") or body.country or "") or None

    record = _get_gateway_connection_record(db, normalized_code, order_country)

    if record is None:

        raise HTTPException(status_code=404, detail="Gateway not found")

    if not getattr(record, "is_enabled", False) or not getattr(record, "supports_customer_checkout", False):

        raise HTTPException(status_code=409, detail="This gateway is not enabled for customer checkout")



    currency_code = _resolved_payment_currency(body.currency, body.country)

    charge_total = _order_charge_total_amount(order)

    converted_total = convert_from_aed(charge_total, currency_code)



    reference = f"gen_{order.id}_{uuid.uuid4().hex[:12]}"

    setattr(order, "payment_intent_id", reference)

    setattr(order, "payment_method", normalized_code)



    gateway = _serialize_gateway_connection(normalized_code, db, record)

    redirect = _build_generic_redirect(gateway, order, reference, currency_code, float(converted_total), db)



    db.add(Payment(

        order_id=order.id,

        amount=charge_total,

        payment_method=normalized_code,

        provider=normalized_code,

        status="pending",

        intent_id=reference,

        country_code=str(getattr(order, "shipping_country", "") or body.country or "") or None,

    ))

    db.commit()



    return {

        "gateway_code": normalized_code,

        "reference": reference,

        "redirect_url": redirect["redirect_url"],

        "redirect_method": redirect["redirect_method"],

        "currency": currency_code,

        "display_amount": float(converted_total),

        "status": "initiated",

    }





def _parse_generic_payload(raw_body: bytes, query_params) -> dict[str, Any]:

    payload: dict[str, Any] = {}

    if raw_body:

        try:

            payload = json.loads(raw_body)

        except Exception:

            try:

                parsed = parse_qs(raw_body.decode("utf-8"), keep_blank_values=True)

                payload = {k: v[-1] for k, v in parsed.items() if v}

            except Exception:

                payload = {}

    for key, value in query_params.items():

        if key not in payload:

            payload[key] = value

    return payload





def _resolve_generic_order(payload: dict[str, Any], provider_code: str, db: Session) -> Optional[Order]:

    order_id_field = str(payload.get("order_id_field", "cart_id") or "cart_id")

    order_id_value = payload.get(order_id_field) or payload.get("order_id") or payload.get("cart_id")

    tran_ref = (

        payload.get("tran_ref")

        or payload.get("reference")

        or payload.get("transaction_ref")

        or payload.get("payment_ref")

    )



    if order_id_value and str(order_id_value).isdigit():

        order = db.query(Order).filter(Order.id == int(order_id_value)).first()

        if order:

            return order

    if tran_ref:

        order = db.query(Order).filter(Order.payment_intent_id == str(tran_ref).strip()).first()

        if order:

            return order

    return None





def _peek_generic_order(provider_code: str, db: Session) -> Optional["Order"]:

    """Best-effort order lookup from the current request body for country resolution.



    Used by the callback handler to pick the correct per-country gateway config

    without duplicating the full payload parsing/resolution done later.

    """

    try:

        raw_body = getattr(_peek_generic_order, "_raw_body", None)

        query_params = getattr(_peek_generic_order, "_query_params", None)

        if raw_body is None:

            return None

        payload = _parse_generic_payload(raw_body, query_params or {})

        return _resolve_generic_order(payload, provider_code, db)

    except Exception:

        return None





async def handle_generic_gateway_callback(request: Request, provider_code: str, db: Session) -> dict:

    normalized_code = _normalize_gateway_code(provider_code)

    # Resolve the gateway connection using the order's country when available so

    # per-country gateway configs are honoured even on server-to-server callbacks.

    _peek_generic_order._raw_body = await request.body()

    _peek_generic_order._query_params = request.query_params

    callback_order = _peek_generic_order(provider_code, db)

    callback_country = str(getattr(callback_order, "shipping_country", "") or "") or None

    record = _get_gateway_connection_record(db, normalized_code, callback_country)

    if record is None:

        raise HTTPException(status_code=404, detail="Gateway not found")



    extra = _json_load_dict(getattr(record, "extra_config_json", None)) if record else {}

    webhook_secret = _optional_text(getattr(record, "webhook_secret", None))

    raw_body = await request.body()

    _payload_hash = hashlib.sha256(raw_body or b"").hexdigest()

    if webhook_secret:

        signature = request.headers.get("X-SIGNATURE") or request.headers.get("X-GATEWAY-SIGNATURE") or ""

        if not _verify_paytabs_signature(raw_body, signature, webhook_secret):

            raise HTTPException(status_code=401, detail="Invalid webhook signature")



    payload = _parse_generic_payload(raw_body, request.query_params)

    status_field = str(extra.get("status_field", "status") or "status")

    success_values = [str(v).lower() for v in (extra.get("success_values") or list(_GENERIC_DEFAULT_SUCCESS_VALUES))]

    tran_ref_field = str(extra.get("transaction_ref_field", "tran_ref") or "tran_ref")

    order_id_field = str(extra.get("order_id_field", "cart_id") or "cart_id")



    order = _resolve_generic_order(payload, normalized_code, db)

    if order is None:

        logger.warning("generic_callback %s: no order resolved", normalized_code)

        return {"status": "unknown_order"}



    resolved_status = str(payload.get(status_field) or payload.get("response_status") or "").lower()

    tran_ref = payload.get(tran_ref_field) or str(getattr(order, "payment_intent_id", "") or "").strip()

    event_id = f"{normalized_code}:{tran_ref or order.id}:{resolved_status}"

    already = db.query(ProcessedWebhookEvent).filter(

        ProcessedWebhookEvent.event_id == event_id,

        ProcessedWebhookEvent.processor == normalized_code,

    ).first()

    if already:

        return {"status": "ok"}



    success = resolved_status in success_values

    if not resolved_status:

        # No explicit status delivered (e.g. redirect-style return). Treat the

        # callback itself as an authorization to mark the order paid when the

        # gateway is configured without a status field.

        success = True



    if success and order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:

        if tran_ref:

            setattr(order, "payment_intent_id", tran_ref)

        _apply_successful_payment(order, f"Order #{order.id} payment via {normalized_code} was successful.", db)

        db.add(ProcessedWebhookEvent(event_id=event_id, processor=normalized_code, payload_hash=_payload_hash))

        db.commit()

        return {"status": "ok", "order_id": order.id, "result": "confirmed"}



    if not success and order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:

        setattr(order, "status", "failed")

        db.add(ProcessedWebhookEvent(event_id=event_id, processor=normalized_code, payload_hash=_payload_hash))

        db.commit()

        return {"status": "ok", "order_id": order.id, "result": "failed"}



    db.add(ProcessedWebhookEvent(event_id=event_id, processor=normalized_code))

    db.commit()

    return {"status": "ok", "order_id": order.id}





def _generic_verify_payment(

    extra: dict[str, Any],

    record: "PaymentGatewayConnection",

    order: Order,

    reference: str,

    db: Session,

) -> str:

    """Poll a configured provider verify endpoint and return 'success' | 'failed' | 'unknown'."""

    verify_url = _optional_text(extra.get("verify_url"))

    if not verify_url:

        return "unknown"

    normalized_code = _normalize_gateway_code(getattr(record, "provider_code", ""))

    callback_url = f"{_resolve_gateway_callback_base(db, normalized_code)}/payments/generic/{normalized_code}/callback"

    ctx: dict[str, Any] = {

        "order_id": order.id,

        "reference": reference or str(getattr(order, "payment_intent_id", "") or ""),

        "transaction_ref": reference or str(getattr(order, "payment_intent_id", "") or ""),

        "amount": float(_order_charge_total_amount(order)),

        "currency": str(getattr(order, "shipping_country", "") or ""),

        "callback_url": callback_url,

        "customer_email": getattr(order, "customer_email", None) or "",

        "customer_name": getattr(order, "customer_name", None) or "",

    }

    url = _fill_gateway_template(verify_url, ctx)

    method = str(extra.get("verify_method", "GET")).upper()

    headers: dict[str, str] = {"accept": "application/json"}

    auth_header = _optional_text(extra.get("verify_auth_header"))

    if auth_header:

        headers["Authorization"] = _fill_gateway_template(

            auth_header, {**ctx, "secret_key": _optional_text(getattr(record, "secret_key", None)) or ""}

        )

    try:

        with httpx.Client(timeout=20) as client:

            resp = client.request(method, url, headers=headers)

            if resp.status_code >= 400:

                logger.warning("generic verify %s failed: %s", normalized_code, resp.status_code)

                return "unknown"

            data = resp.json()

    except Exception as exc:

        logger.error("generic verify call error: %s", exc)

        return "unknown"



    status_field = str(extra.get("verify_status_field", "status") or "status")

    success_values = [str(v).lower() for v in (extra.get("verify_success_values") or list(_GENERIC_DEFAULT_SUCCESS_VALUES))]

    fail_values = [str(v).lower() for v in (extra.get("verify_failed_values") or ["failed", "declined", "error", "cancelled"])]

    resolved = str(data.get(status_field) or "").lower()

    if resolved in success_values:

        return "success"

    if resolved in fail_values:

        return "failed"

    return "unknown"





def confirm_generic_gateway_payment(body: ConfirmGenericGatewayRequest, current_user: dict, db: Session) -> dict:

    order = _get_user_order(body.order_id, current_user, db)

    if order.paid_at is not None:

        return {"status": "confirmed", "order_id": order.id, "order_status": order.status, "payment_status": "approved", "paid_at": order.paid_at}



    normalized_code = _normalize_gateway_code(body.gateway_code)

    order_country = str(getattr(order, "shipping_country", "") or body.country or "") or None

    record = _get_gateway_connection_record(db, normalized_code, order_country)

    if record is None:

        return {"status": "pending", "order_id": order.id, "order_status": order.status, "payment_status": "pending", "paid_at": order.paid_at}



    extra = _json_load_dict(getattr(record, "extra_config_json", None)) or {}

    reference = body.reference or str(getattr(order, "payment_intent_id", "") or "")



    # Optionally poll the provider for the authoritative payment status before

    # trusting the redirect return. This makes the plug-and-play confirm work

    # even for gateways that do not post a server-side callback.

    verify_result = _generic_verify_payment(extra, record, order, reference, db)

    if verify_result == "success":

        _apply_successful_payment(order, f"Order #{order.id} payment via {normalized_code} was successful.", db)

        db.commit()

        return {"status": "confirmed", "order_id": order.id, "order_status": order.status, "payment_status": "approved", "paid_at": order.paid_at}

    if verify_result == "failed":

        setattr(order, "status", "failed")

        db.commit()

        return {"status": "failed", "order_id": order.id, "order_status": order.status, "payment_status": "declined", "paid_at": order.paid_at}



    # If a prior callback already recorded the payment as completed, finalize.

    payment = db.query(Payment).filter(

        Payment.order_id == order.id,

        Payment.provider == normalized_code,

    ).order_by(Payment.id.desc()).first()

    if payment and payment.status == "completed":

        _apply_successful_payment(order, f"Order #{order.id} payment via {normalized_code} was successful.", db)

        db.commit()

        return {"status": "confirmed", "order_id": order.id, "order_status": order.status, "payment_status": "approved", "paid_at": order.paid_at}



    return {"status": "pending", "order_id": order.id, "order_status": order.status, "payment_status": "pending", "paid_at": order.paid_at}




# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.finance.services.payouts.payments_gateway_service import event_publisher






# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.finance.services.payouts.payments_gateway_service import event_publisher



# === MERGED from badge_billing_payment.py ===

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from domains.finance.models.finance import BankTransaction
from domains.governance.models.admin import BadgeBillingRecord
# TODO: log_bank_transaction not found in cash_management_service
# from domains.finance.services.treasury.cash_management_service import log_bank_transaction
from infrastructure.utils.datetime_utils import utcnow
from kernel.money import round_money, to_decimal
import structlog
logger = structlog.get_logger(__name__)

logger = logging.getLogger(__name__)


def parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as e:
        logger.exception("_parse_dt_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ISO datetime: {value!r}",
        )


def list_badge_billing_records(
    db: Session,
    *,
    supplier_id: Optional[int] = None,
    status: Optional[str] = None,
    country_code: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    cursor: Optional[str] = None,
):
    """Return (items, total) for the supplied filters.

    Uses keyset (cursor) pagination when ``cursor`` is provided; falls back to
    offset-based pagination for ``skip``-based navigation.
    """
    query = db.query(BadgeBillingRecord)
    if supplier_id is not None:
        query = query.filter(BadgeBillingRecord.supplier_id == supplier_id)
    if status is not None:
        query = query.filter(BadgeBillingRecord.status == status)
    if country_code is not None:
        query = query.filter(BadgeBillingRecord.country_code == country_code)

    query = query.order_by(desc(BadgeBillingRecord.created_at))
    total = query.count()

    if cursor is not None:
        from infrastructure.utils.pagination import keyset_paginate
        page_size = min(max(limit, 1), 100)
        result = keyset_paginate(
            query,
            sort_keys=[(BadgeBillingRecord.created_at, "desc")],
            cursor=cursor,
            page_size=page_size,
        )
        return result["items"], total, result.get("next_cursor"), result.get("has_next")

    items = query.offset(skip).limit(limit).all()
    return items, total, None, False


def get_badge_billing_record(db: Session, record_id: int) -> BadgeBillingRecord:
    record = (
        db.query(BadgeBillingRecord)
        .filter(BadgeBillingRecord.id == record_id)
        .first()
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Badge billing record not found",
        )
    return record


def generate_badge_billing_record(
    db: Session,
    *,
    supplier_id: int,
    amount: Decimal,
    currency: str = "USD",
    badge_level: Optional[str] = None,
    charge_type: Optional[str] = None,
    charge_source: Optional[str] = None,
    country_code: Optional[str] = None,
    billing_reference: Optional[str] = None,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
    due_at: Optional[datetime] = None,
    notes: Optional[str] = None,
    created_by: Optional[int] = None,
) -> BadgeBillingRecord:
    """Create a pending badge billing charge for a supplier."""
    amount_dec = to_decimal(amount)
    if amount_dec <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be greater than zero",
        )

    record = BadgeBillingRecord(
        supplier_id=supplier_id,
        billing_reference=billing_reference,
        badge_level=badge_level,
        charge_type=charge_type or "badge_subscription",
        charge_source=charge_source or "system",
        amount=round_money(amount_dec),
        currency=currency,
        status="pending",
        period_start=period_start,
        period_end=period_end,
        due_at=due_at,
        notes=notes,
        created_by=created_by,
        country_code=country_code,
    )
    db.add(record)
    db.flush()
    db.commit()
    return record


def pay_badge_billing_record(
    db: Session,
    record_id: int,
    *,
    amount: Decimal,
    payment_method: str,
    currency: Optional[str] = None,
    country_code: Optional[str] = None,
    notes: Optional[str] = None,
    updated_by: Optional[int] = None,
) -> tuple[BadgeBillingRecord, BankTransaction]:
    """Record a payment against a badge billing record.

    Creates a reconcilable bank transaction via the canonical cash-management
    helper and links it to the billing record, transitioning the record to
    ``paid``.
    """
    record = get_badge_billing_record(db, record_id)
    if record.status == "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Badge billing record is already paid",
        )

    amount_dec = to_decimal(amount)
    if amount_dec <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount must be greater than zero",
        )

    txn = log_bank_transaction(
        source="badge_billing",
        transaction_type="inflow",
        category="badge_billing",
        amount=amount_dec,
        db=db,
        currency=currency or record.currency or "USD",
        supplier_id=record.supplier_id,
        description=(
            f"Badge billing payment for record #{record.id}"
            + (f" (ref {record.billing_reference})" if record.billing_reference else "")
        ),
        transaction_ref=f"BB-{record.billing_reference or record.id}",
        country_code=country_code or record.country_code,
    )

    record.bank_transaction_id = txn.id
    record.payment_method = payment_method
    record.paid_at = utcnow()
    record.billed_at = record.billed_at or utcnow()
    record.status = "paid"
    if notes is not None:
        record.notes = notes
    if updated_by is not None:
        record.updated_by = updated_by

    db.add(record)
    db.flush()
    db.commit()
    return record, txn



# === MERGED from gateway_reconciliation_service.py ===

logger = logging.getLogger(__name__)

GATEWAY_FEE_RATES = {
    "tap": Decimal("0.025"),
    "stripe": Decimal("0.029"),
    "thawani": Decimal("0.020"),
    "omannet": Decimal("0.015"),
    "mada": Decimal("0.015"),
}


def _get_gateway_name(db: Session, gateway_id: int) -> str:
    gw = db.query(PaymentGatewayConnection).get(gateway_id)
    return gw.name if gw else "unknown"


def _calculate_gateway_fee(gateway_id: int, gross_amount: Decimal, db: Session) -> Decimal:
    gw = db.query(PaymentGatewayConnection).get(gateway_id)
    gw_name = (gw.name or "tap") if gw else "tap"
    rate = GATEWAY_FEE_RATES.get(gw_name.lower(), Decimal("0.025"))
    return (gross_amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def match_gateway_settlement(
    db: Session,
    settlement_id: int,
    country_code: str = None,
) -> dict:
    settlement = db.query(GatewaySettlementSchedule).get(settlement_id)
    if not settlement:
        raise ValueError(f"Settlement #{settlement_id} not found")

    if settlement.status == "reconciled":
        return {"status": "already_reconciled", "settlement_id": settlement_id}

    gateway_name = _get_gateway_name(db, settlement.gateway_id)
    matching_orders = _find_orders_for_settlement(db, settlement)
    expected_gross = sum(Decimal(str(o.total or 0)) for o in matching_orders)
    expected_fee = _calculate_gateway_fee(settlement.gateway_id, expected_gross, db)
    expected_net = expected_gross - expected_fee

    gateway_amount = settlement.amount or Decimal("0")
    gateway_fee = settlement.gateway_fee or expected_fee
    gateway_net = settlement.net_amount or (gateway_amount - gateway_fee)

    amount_diff = abs(gateway_amount - expected_gross)
    fee_diff = abs(gateway_fee - expected_fee)

    if amount_diff <= Decimal("0.01") and fee_diff <= Decimal("0.01"):
        result = _auto_post_gateway_settlement(
            db, settlement, matching_orders, gateway_amount, gateway_fee, gateway_net,
            settlement.country_code, gateway_name,
        )
        settlement.status = "reconciled"
        db.commit()
        return {
            "status": "reconciled",
            "settlement_id": settlement_id,
            "journal_entry_id": result.get("journal_entry_id"),
            "gateway_amount": float(gateway_amount),
            "gateway_fee": float(gateway_fee),
            "net_deposited": float(gateway_net),
            "orders_matched": len(matching_orders),
        }
    else:
        settlement.status = "exception"
        db.commit()
        return {
            "status": "exception",
            "settlement_id": settlement_id,
            "expected_gross": float(expected_gross),
            "gateway_amount": float(gateway_amount),
            "difference": float(amount_diff),
            "fee_difference": float(fee_diff),
        }


def _find_orders_for_settlement(db: Session, settlement: GatewaySettlementSchedule):
    gateway = db.query(PaymentGatewayConnection).get(settlement.gateway_id)
    settlement_days = 2
    if gateway and gateway.settlement_cycle == "daily":
        settlement_days = 1

    window_start = settlement.settlement_date - timedelta(days=settlement_days + 1)
    window_end = settlement.settlement_date

    return db.query(Order).filter(
        Order.payment_method.in_(["card", "online"]),
        Order.status.in_(["paid", "delivered", "completed"]),
        Order.created_at >= window_start,
        Order.created_at <= window_end,
        Order.country_code == settlement.country_code,
    ).limit(1000).all()


def _auto_post_gateway_settlement(
    db: Session, settlement, orders, gross_amount, fee, net_amount,
    country_code, gateway_name,
) -> dict:
    cc = country_code or settlement.country_code
    lines = [
        JournalLineInput(account_code="1010", side="debit", amount=net_amount,
                         description=f"Gateway settlement net deposit - {gateway_name}"),
        JournalLineInput(account_code="5010", side="debit", amount=fee,
                         description=f"Gateway fee - {gateway_name} ({fee/gross_amount*100:.1f}%)"),
        JournalLineInput(account_code="1020", side="credit", amount=gross_amount,
                         description=f"Gateway clearing - settlement #{settlement.id}"),
    ]
    entry_data = JournalEntryCreate(
        entry_date=settlement.settlement_date or _utcnow(),
        reference_type="gateway_settlement",
        reference_id=settlement.id,
        reference_number=f"GS-{settlement.id:06d}",
        description=f"Gateway settlement - {gateway_name} - {gross_amount}",
        currency=settlement.currency or "OMR",
        country_code=cc,
        lines=lines,
    )
    result = gl.create_journal_entry(db, entry_data)
    return {"journal_entry_id": result.id, "status": "posted"}


def reconcile_cod_deposit(
    db: Session,
    order_id: int,
    deposited_amount: Decimal,
    country_code: str = None,
) -> dict:
    order = db.query(Order).get(order_id)
    if not order:
        raise ValueError(f"Order #{order_id} not found")
    if order.payment_method != "cod":
        raise ValueError(f"Order #{order_id} is not COD")

    expected = Decimal(str(order.total or 0))
    deposited = Decimal(str(deposited_amount))

    if deposited == expected:
        entry_data = JournalEntryCreate(
            entry_date=_utcnow(),
            reference_type="cod_reconciliation",
            reference_id=order.id,
            reference_number=f"COD-{order.id:06d}",
            description=f"COD deposit reconciled - Order #{order.id}",
            currency=order.currency or "OMR",
            country_code=country_code or order.country_code,
            lines=[
                JournalLineInput(account_code="1010", side="debit", amount=deposited,
                                 description=f"COD cash received - Order #{order.id}"),
                JournalLineInput(account_code="1030", side="credit", amount=deposited,
                                 description=f"COD receivable cleared - Order #{order.id}"),
            ],
        )
        result = gl.create_journal_entry(db, entry_data)
        _log_reconciliation(db, "cod_match", order_id, {
            "expected": float(expected), "deposited": float(deposited),
            "journal_entry_id": result.id,
        }, country_code)
        return {"status": "reconciled", "order_id": order_id,
                "expected": float(expected), "deposited": float(deposited),
                "journal_entry_id": result.id}
    else:
        variance = deposited - expected
        _log_reconciliation(db, "cod_exception", order_id, {
            "expected": float(expected), "deposited": float(deposited),
            "variance": float(variance),
        }, country_code)
        return {"status": "exception", "order_id": order_id,
                "expected": float(expected), "deposited": float(deposited),
                "variance": float(variance)}


def run_gateway_3way_reconciliation(db: Session, country_code: str = None) -> dict:
    results = {"processed": 0, "reconciled": 0, "exceptions": 0, "items": []}

    q = db.query(GatewaySettlementSchedule).filter(
        GatewaySettlementSchedule.status.in_(["pending", "captured"]),
        GatewaySettlementSchedule.status != "reconciled",
    )
    if country_code:
        q = q.filter(GatewaySettlementSchedule.country_code == country_code)

    for settlement in q.limit(1000).all():
        results["processed"] += 1
        try:
            result = match_gateway_settlement(db, settlement.id, country_code)
            if result["status"] == "reconciled":
                results["reconciled"] += 1
            else:
                results["exceptions"] += 1
            results["items"].append(result)
        except Exception as e:
            logger.warning("Gateway reconciliation failed for #%s: %s", settlement.id, e)
            results["exceptions"] += 1
            results["items"].append({"status": "error", "settlement_id": settlement.id,
                                      "error": str(e)})

    _log_reconciliation(db, "gateway_3way_batch", 0, results, country_code)
    return results


def reconcile_all_cod_deposits(db: Session, country_code: str = None) -> dict:
    results = {"processed": 0, "reconciled": 0, "exceptions": 0}

    orders = db.query(Order).filter(
        Order.payment_method == "cod",
        Order.status == "delivered",
        Order.paid_at.is_(None),
    )
    if country_code:
        orders = orders.filter(Order.country_code == country_code)

    results["processed"] = orders.count()

    for order in orders.limit(1000).all():
        try:
            expected = Decimal(str(order.total or 0))
            entry_data = JournalEntryCreate(
                entry_date=_utcnow(),
                reference_type="cod_batch_reconciliation",
                reference_id=order.id,
                reference_number=f"COD-REC-{order.id:06d}",
                description=f"COD batch reconciliation - Order #{order.id}",
                currency=order.currency or "OMR",
                country_code=country_code or order.country_code,
                lines=[
                    JournalLineInput(account_code="1010", side="debit", amount=expected,
                                     description=f"COD cash received - Order #{order.id}"),
                    JournalLineInput(account_code="1030", side="credit", amount=expected,
                                     description=f"COD receivable cleared - Order #{order.id}"),
                ],
            )
            gl.create_journal_entry(db, entry_data)
            results["reconciled"] += 1
        except Exception as e:
            logger.warning("COD reconciliation failed for order %s: %s", order.id, e)
            results["exceptions"] += 1

    db.commit()
    return results


def _log_reconciliation(db: Session, kind: str, entity_id: int, detail: dict,
                         country_code: str = None):
    try:
        db.add(FinanceAutomationLog(kind=kind, records_processed=1,
                                     records_changed=1, detail={**detail, "entity_id": entity_id},
                                     country_code=country_code))
        db.add(FinanceAuditLog(action="reconciliation", entity_type="gateway_settlement",
                                entity_id=entity_id, detail=detail, country_code=country_code))
        db.commit()
    except Exception as e:
        logger.warning("Reconciliation log failed: %s", e)
        db.rollback()



# === MERGED from gateway_auto_enable.py ===

"""Gateway auto-enable service for country-specific payment routing.

Automatically enables payment gateways based on country configuration
from the auto-populate service.
"""

import logging
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from domains.country.models.countries import CountryConfig
from domains.country.models.countries import CountryGatewayCredentials
from domains.country.ports import GATEWAY_REGISTRY

logger = logging.getLogger(__name__)


class GatewayAutoEnableService:
    """Service for automatically enabling gateways based on country config."""

    def __init__(self, db: Session):
        self.db = db

    def get_eligible_gateways(self, country_code: str) -> List[Dict[str, Any]]:
        """Get gateways eligible for a country based on config."""
        country = (
            self.db.query(CountryConfig)
            .filter(CountryConfig.code == country_code.upper())
            .first()
        )

        if not country:
            return []

        currencies = []
        if country.currencies:
            currencies = country.currencies if isinstance(country.currencies, list) else []
        elif country.currency:
            currencies = [country.currency]

        region = country.region or ""
        internet_pen = float(country.internet_penetration_pct) if country.internet_penetration_pct else 50

        gateway_rankings = self.calculate_gateway_rankings(
            country_code, currencies, region, internet_pen
        )

        return [
            {
                "gateway_id": gw["gateway_id"],
                "name": gw["name"],
                "type": gw["type"],
                "enabled": True,
                "credential_ref": None,
                "supports_cod": gw["gateway_id"] in ["tap", "thawani", "omannet"],
                "supports_installments": gw["gateway_id"] in ["stripe", "tap", "hyperpay"],
                "fee_percentage": gw["avg_fee"],
                "fee_fixed": 0.30,
                "integration_feasibility_score": gw["score"],
                "recommendation": "highly_recommended" if gw["score"] >= 75 else "recommended" if gw["score"] >= 50 else "consider",
            }
            for gw in gateway_rankings
        ]

    def calculate_gateway_rankings(
        self,
        country_code: str,
        currencies: List[str],
        region: str = None,
        internet_pen: float = 50,
    ) -> List[Dict[str, Any]]:
        """Calculate gateway rankings for a country."""
        scores = []
        for gw_id, gw in GATEWAY_REGISTRY.items():
            score = 0
            if country_code.upper() in gw["regions"] or "GLOBAL" in gw["regions"]:
                score += 40
            for curr in currencies:
                if curr in gw["currencies"] or "*" in gw["currencies"]:
                    score += 25
                    break
            if internet_pen > 80:
                score += 15
            elif internet_pen > 50:
                score += 10
            else:
                score += 5
            score += max(0, 10 - (gw["avg_fee"] - 1.5))
            score += max(0, 10 - (gw["setup_days"] / 3))
            if score > 50:
                scores.append({
                    "gateway_id": gw_id,
                    "score": score,
                    "name": gw["name"],
                    "type": gw["type"],
                    "avg_fee": gw["avg_fee"],
                    "setup_days": gw["setup_days"],
                })
        return sorted(scores, key=lambda x: x["score"], reverse=True)

    def enable_gateways_for_country(
        self, country_code: str, user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Enable eligible gateways for a country."""
        gateways = self.get_eligible_gateways(country_code)

        for gw in gateways:
            existing = (
                self.db.query(CountryGatewayCredentials)
                .filter(
                    CountryGatewayCredentials.country_code == country_code.upper(),
                    CountryGatewayCredentials.gateway_name == gw["gateway_id"],
                )
                .first()
            )

            if not existing:
                cred = CountryGatewayCredentials(
                    country_code=country_code.upper(),
                    gateway_name=gw["gateway_id"],
                    environment="test",
                    credentials={},
                    is_active=True,
                )
                self.db.add(cred)

        self.db.commit()
        return gateways

    def get_enabled_gateways(self, country_code: str) -> List[Dict[str, Any]]:
        """Get list of enabled gateways for a country."""
        credentials = (
            self.db.query(CountryGatewayCredentials)
            .filter(
                CountryGatewayCredentials.country_code == country_code.upper(),
                CountryGatewayCredentials.is_active == True,
            )
            .limit(1000)
            .all()
        )

        return [
            {
                "gateway_id": c.gateway_name,
                "gateway_name": c.gateway_name,
                "environment": c.environment,
                "is_active": c.is_active,
            }
            for c in credentials
        ]


def auto_enable_gateways(db: Session, country_code: str, user_id: Optional[int] = None) -> List[str]:
    """Convenience function to auto-enable gateways for a country."""
    service = GatewayAutoEnableService(db)
    gateways = service.enable_gateways_for_country(country_code, user_id)
    return [g["gateway_id"] for g in gateways]


# === RELIABILITY: Health & Metrics ===


def get_gateway_health() -> dict:
    """Return health status of all payment gateways for monitoring."""
    from infrastructure.database.database import check_connection_health, get_pool_metrics

    db_healthy = check_connection_health()
    pool_metrics = get_pool_metrics()
    breaker_stats = get_all_breaker_stats()

    return {
        "database": "healthy" if db_healthy else "unhealthy",
        "connection_pool": pool_metrics,
        "circuit_breakers": breaker_stats,
        "gateway_calls_total": _gateway_call_count,
        "gateway_errors_total": _gateway_error_count,
        "error_rate": (
            round(_gateway_error_count / _gateway_call_count, 4)
            if _gateway_call_count > 0
            else 0.0
        ),
    }
