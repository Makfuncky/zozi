"""Gateway module — imports shared code from payment_engine."""

from domains.finance.services.payments.payment_engine import (  # noqa: F401
    TapChargeRequest,
    ConfirmTapPaymentRequest,
    PayTabsChargeRequest,
    ConfirmPayTabsPaymentRequest,
    ThawaniCheckoutRequest,
    ConfirmThawaniPaymentRequest,
    _tap_configured,
    _resolve_tap_secret_key,
    _resolve_tap_webhook_secret,
    _resolve_tap_api_base_url,
    _resolve_tap_webhook_url,
    _paytabs_configured,
    _resolve_paytabs_server_key,
    _resolve_paytabs_webhook_secret,
    _resolve_paytabs_profile_id,
    _resolve_paytabs_api_base_url,
    _resolve_paytabs_callback_url,
    _verify_paytabs_signature,
    _paytabs_response_status,
    _paytabs_response_message,
    _paytabs_transaction_reference,
    _paytabs_customer_details,
    _paytabs_shipping_details,
    _payment_provider_mode_allows,
    _get_user_order,
    _normalized_payment_method,
    _resolved_payment_currency,
    _order_charge_total_amount,
    _order_gateway_metadata,
    _apply_successful_payment,
    apply_order_status_change,
    _build_tap_customer,
    _thawani_configured,
    _thawani_checkout_enabled,
    _resolve_thawani_secret_key,
    _resolve_thawani_publishable_key,
    _resolve_thawani_api_base_url,
    _resolve_thawani_webhook_secret,
    _safe_http_call,
    _tap_breaker,
    _paytabs_breaker,
    _thawani_breaker,
    INVENTORY_RELEASE_STATUSES,
    PAYTABS_PAYMENT_METHOD,
    PAYTABS_SUCCESS_RESPONSE_STATUSES,
    PAYTABS_PENDING_RESPONSE_STATUSES,
    PAYTABS_FAILURE_RESPONSE_STATUSES,
    THAWANI_PAYMENT_METHOD,
    DEFAULT_THAWANI_UAT_PAY_BASE,
    DEFAULT_THAWANI_LIVE_PAY_BASE,
    DEFAULT_PAYTABS_REQUEST_PATH,
    DEFAULT_PAYTABS_QUERY_PATH,
    logger,
    HTTPException,
    Request,
    Session,
    Optional,
    dict,
    Any,
    cast,
    Decimal,
    Order,
    OrderItem,
    convert_from_aed,
    hmac,
    hashlib,
    httpx,
    json,
    parse_qs,
    datetime,
    timezone,
)

async def create_tap_charge(body: TapChargeRequest, current_user: dict, db: Session) -> dict:

    configured, tap_key = _tap_configured(db)

    if not configured:

        raise HTTPException(status_code=503, detail="Tap Payments not configured")

    if not _payment_provider_mode_allows("tap", db):

        raise HTTPException(status_code=409, detail="Tap payments are currently disabled by admin")



    webhook_url = _resolve_tap_webhook_url(db)

    if not webhook_url:

        raise HTTPException(status_code=503, detail="Tap webhook URL not configured")

    tap_api_base_url = _resolve_tap_api_base_url(db)



    order = _get_user_order(body.order_id, current_user, db)

    if _normalized_payment_method(order) != "tap":

        raise HTTPException(status_code=409, detail="This order is not configured for Tap payment")

    if order.paid_at is not None:

        raise HTTPException(status_code=409, detail="Order is already paid")

    currency_code = _resolved_payment_currency(body.currency, body.country)

    charge_total = _order_charge_total_amount(order)

    converted_total = convert_from_aed(charge_total, currency_code)

    redirect_url = body.success_url.strip() or f"{settings.frontend_url}/checkout?tap_order_id={order.id}"

    preferred_language = str(current_user.get("preferred_language") or "en").lower()

    lang_code = "ar" if preferred_language.startswith("ar") else "en"



    payload = {

        "amount": float(converted_total),

        "currency": currency_code,

        "customer_initiated": True,

        "threeDSecure": True,

        "save_card": False,

        "description": body.description or f"ZOZI Order #{order.id}",

        "customer": _build_tap_customer(order, current_user),

        "order": {"id": str(order.id)},

        "metadata": {

            "order_id": str(order.id),

            "user_id": str(current_user["id"]),

            "payment_method": "tap",

            "shipping_country": str(getattr(order, "shipping_country", "") or ""),

            **_order_gateway_metadata(order),

        },

        "source": {"id": "src_all"},

        "redirect": {"url": redirect_url},

        "post": {"url": webhook_url},

        "reference": {

            "transaction": f"zozi_order_{order.id}",

            "order": str(order.id),

        },

    }



    try:

        async with httpx.AsyncClient(timeout=15) as client:

            resp = await client.post(

                f"{tap_api_base_url}/v2/charges",

                headers={

                    "Authorization": f"Bearer {tap_key}",

                    "Content-Type": "application/json",

                    "accept": "application/json",

                    "lang_code": lang_code,

                },

                json=payload,

            )

        data = resp.json()

        if resp.status_code not in (200, 201):

            logger.error("Tap charge creation failed: %s", data)

            errors = data.get("errors", [{}])

            raise HTTPException(

                status_code=400,

                detail=errors[0].get("description", "Tap payment failed") if errors else "Tap payment failed",

            )



        charge_id = data.get("id")

        redirect_url = data.get("transaction", {}).get("url") or data.get("redirect", {}).get("url")

        if charge_id:

            setattr(order, "payment_intent_id", charge_id)

            db.commit()

        return {

            "charge_id": charge_id,

            "redirect_url": redirect_url,

            "status": data.get("status"),

            "currency": currency_code,

            "display_amount": float(converted_total),

        }

    except HTTPException:

        raise

    except Exception as exc:

        logger.error("Tap charge error: %s", exc)

        raise HTTPException(status_code=500, detail="Tap payment service error")





def _tap_error_detail(payload: dict[str, Any], default: str) -> str:

    errors = payload.get("errors", []) if isinstance(payload, dict) else []

    if isinstance(errors, list) and errors:

        first_error = errors[0]

        if isinstance(first_error, dict):

            description = first_error.get("description")

            if description:

                return str(description)

    message = payload.get("message") if isinstance(payload, dict) else None

    return str(message or default)





def _finalize_tap_charge_status(order: Order, charge_payload: dict[str, Any], db: Session) -> dict[str, Any]:

    charge_id = str(charge_payload.get("id") or getattr(order, "payment_intent_id", "") or "").strip()

    if charge_id and not getattr(order, "payment_intent_id", None):

        setattr(order, "payment_intent_id", charge_id)



    status = str(charge_payload.get("status", "") or "").upper()



    if status == "CAPTURED":

        if order.status not in INVENTORY_RELEASE_STATUSES and order.paid_at is None:

            _apply_successful_payment(

                order,

                f"Order #{order.id} payment via Tap was successful.",

                db,

            )

            db.commit()

            try:

                from domains.comms.ports import enqueue_payment_confirmed_email, enqueue_payment_failed_email, enqueue_refund_processed_email

                enqueue_payment_confirmed_email(cast(int, order.id), provider="tap", message="Your Tap payment was successful and we are preparing your order.")

            except Exception:

                logger.exception("Failed to enqueue Tap payment-confirmed email for order %s", order.id)



        return {

            "status": "confirmed",

            "order_id": order.id,

            "order_status": order.status if order.status not in INVENTORY_RELEASE_STATUSES else order.status,

            "charge_id": charge_id,

            "payment_status": status,

            "paid_at": order.paid_at,

        }



    if status == "FAILED":

        if order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:

            setattr(order, "status", "failed")

            from domains.comms.ports import create_notification, Notification

            create_notification(
                db,
                Notification(
                    user_id=order.user_id,
                    type="order_update",
                    title="Payment Failed",
                    message=f"Order #{order.id} Tap payment failed.",
                    link=f"/orders/{order.id}",
                ),
            )

            db.commit()

            try:




                enqueue_payment_failed_email(cast(int, order.id), provider="tap", message="Your Tap payment could not be completed.")

            except Exception:

                logger.exception("Failed to enqueue Tap payment-failed email for order %s", order.id)



        return {

            "status": "failed",

            "order_id": order.id,

            "order_status": order.status,

            "charge_id": charge_id,

            "payment_status": status,

            "paid_at": order.paid_at,

        }



    if status == "REFUNDED":

        if order.status != "refunded":

            apply_order_status_change(order, "refunded", db)

            try:

                from domains.finance.services.treasury.cash_management_service import log_refund_bank_transaction
                from domains.finance.services.treasury.cash_management_service import log_refund_bank_transaction

                log_refund_bank_transaction(

                    order,

                    db,

                    source="tap_refund",

                    transaction_ref=f"{charge_id}:REFUNDED",

                    description=f"Tap refund settled for order #{order.id}",

                    transaction_date=datetime.now(timezone.utc).replace(tzinfo=None),

                )

            except Exception:

                logger.exception("Failed to log Tap refund bank transaction for order %s", order.id)

            from domains.comms.ports import create_notification, Notification

            create_notification(
                db,
                Notification(
                    user_id=order.user_id,
                    type="order_update",
                    title="Refund Processed",
                    message=f"Your Tap refund for Order #{order.id} has been processed.",
                    link=f"/orders/{order.id}",
                ),
            )

            db.commit()

            try:




                enqueue_refund_processed_email(cast(int, order.id), source="tap")

            except Exception:

                logger.exception("Failed to enqueue Tap refund email for order %s", order.id)



        return {

            "status": "refunded",

            "order_id": order.id,

            "order_status": order.status,

            "charge_id": charge_id,

            "payment_status": status,

            "paid_at": order.paid_at,

        }



    return {

        "status": "pending_verification",

        "order_id": order.id,

        "order_status": order.status,

        "charge_id": charge_id,

        "payment_status": status or "pending",

        "paid_at": order.paid_at,

    }





async def confirm_tap_payment(body: ConfirmTapPaymentRequest, current_user: dict, db: Session) -> dict:

    configured, tap_key = _tap_configured(db)

    if not configured:

        raise HTTPException(status_code=503, detail="Tap Payments not configured")

    tap_api_base_url = _resolve_tap_api_base_url(db)



    order = _get_user_order(body.order_id, current_user, db)

    if _normalized_payment_method(order) != "tap":

        raise HTTPException(status_code=409, detail="This order is not configured for Tap payment")



    charge_id = (body.charge_id or cast(Optional[str], getattr(order, "payment_intent_id", None)) or "").strip()

    if not charge_id:

        raise HTTPException(status_code=422, detail="charge_id is required")



    if order.paid_at is not None:

        return {

            "status": "confirmed",

            "order_id": order.id,

            "order_status": order.status,

            "charge_id": charge_id,

            "payment_status": "CAPTURED",

            "paid_at": order.paid_at,

        }



    try:

        async with httpx.AsyncClient(timeout=15) as client:

            resp = await client.get(

                f"{tap_api_base_url}/v2/charges/{charge_id}",

                headers={

                    "Authorization": f"Bearer {tap_key}",

                    "accept": "application/json",

                },

            )

        data = resp.json()

        if resp.status_code != 200:

            raise HTTPException(status_code=400, detail=_tap_error_detail(data, "Tap payment verification failed"))

        return _finalize_tap_charge_status(order, data, db)

    except HTTPException:

        raise

    except Exception as exc:

        logger.error("Tap payment confirmation error: %s", exc)

        raise HTTPException(status_code=500, detail="Tap payment verification error")





async def _query_paytabs_transaction(tran_ref: str | None, cart_id: str | None, db: Session) -> dict[str, Any]:

    configured, server_key, profile_id = _paytabs_configured(db)

    if not configured:

        raise HTTPException(status_code=503, detail="PayTabs is not configured")

    payload: dict[str, Any] = {"profile_id": profile_id}

    if tran_ref:

        payload["tran_ref"] = tran_ref

    if cart_id:

        payload["cart_id"] = cart_id

    if not tran_ref and not cart_id:

        raise HTTPException(status_code=422, detail="tran_ref or cart_id is required")



    async with httpx.AsyncClient(timeout=15) as client:

        response = await client.post(

            f"{_resolve_paytabs_api_base_url(db)}{DEFAULT_PAYTABS_QUERY_PATH}",

            headers={"authorization": server_key, "content-type": "application/json"},

            json=payload,

        )

    data = response.json()

    if response.status_code not in (200, 201):

        raise HTTPException(status_code=400, detail=_paytabs_response_message(data))

    return data





def _finalize_paytabs_transaction(order: Order, payload: dict[str, Any], db: Session) -> dict[str, Any]:

    tran_ref = _paytabs_transaction_reference(payload) or str(getattr(order, "payment_intent_id", "") or "").strip()

    if tran_ref and not getattr(order, "payment_intent_id", None):

        setattr(order, "payment_intent_id", tran_ref)



    response_status = _paytabs_response_status(payload)



    if response_status in PAYTABS_SUCCESS_RESPONSE_STATUSES:

        if order.status not in INVENTORY_RELEASE_STATUSES and order.paid_at is None:

            _apply_successful_payment(order, f"Order #{order.id} payment via PayTabs was successful.", db)

            db.commit()

            try:




                enqueue_payment_confirmed_email(cast(int, order.id), provider="paytabs", message="Your PayTabs payment was successful and we are preparing your order.")

            except Exception:

                logger.exception("Failed to enqueue PayTabs payment-confirmed email for order %s", order.id)



        return {

            "status": "confirmed",

            "order_id": order.id,

            "order_status": order.status,

            "tran_ref": tran_ref,

            "payment_status": response_status,

            "paid_at": order.paid_at,

        }



    if response_status in PAYTABS_FAILURE_RESPONSE_STATUSES:

        if order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:

            setattr(order, "status", "failed")

            from domains.comms.ports import create_notification, Notification

            create_notification(
                db,
                Notification(
                    user_id=order.user_id,
                    type="order_update",
                    title="Payment Failed",
                    message=f"Order #{order.id} PayTabs payment failed.",
                    link=f"/orders/{order.id}",
                ),
            )

            db.commit()

            try:




                enqueue_payment_failed_email(cast(int, order.id), provider="paytabs", message=_paytabs_response_message(payload))

            except Exception:

                logger.exception("Failed to enqueue PayTabs payment-failed email for order %s", order.id)



        return {

            "status": "failed",

            "order_id": order.id,

            "order_status": order.status,

            "tran_ref": tran_ref,

            "payment_status": response_status,

            "paid_at": order.paid_at,

        }



    return {

        "status": "pending_verification",

        "order_id": order.id,

        "order_status": order.status,

        "tran_ref": tran_ref,

        "payment_status": response_status or "pending",

        "paid_at": order.paid_at,

    }





async def create_paytabs_charge(body: PayTabsChargeRequest, current_user: dict, db: Session) -> dict:

    configured, server_key, profile_id = _paytabs_configured(db)

    if not configured:

        raise HTTPException(status_code=503, detail="PayTabs is not configured")

    if not _payment_provider_mode_allows(PAYTABS_PAYMENT_METHOD, db):

        raise HTTPException(status_code=409, detail="PayTabs payments are currently disabled by admin")



    callback_url = _resolve_paytabs_callback_url(db)

    if not callback_url:

        raise HTTPException(status_code=503, detail="PayTabs callback URL not configured")



    order = _get_user_order(body.order_id, current_user, db)

    if _normalized_payment_method(order) != PAYTABS_PAYMENT_METHOD:

        raise HTTPException(status_code=409, detail="This order is not configured for PayTabs payment")

    if order.paid_at is not None:

        raise HTTPException(status_code=409, detail="Order is already paid")



    currency_code = _resolved_payment_currency(body.currency, body.country)

    charge_total = _order_charge_total_amount(order)

    converted_total = convert_from_aed(charge_total, currency_code)

    redirect_url = body.success_url.strip() or f"{settings.frontend_url}/checkout?paytabs_order_id={order.id}"

    preferred_language = str(current_user.get("preferred_language") or "en").lower()

    payload = {

        "profile_id": int(profile_id) if str(profile_id).isdigit() else profile_id,

        "tran_type": "sale",

        "tran_class": "ecom",

        "cart_id": str(order.id),

        "cart_currency": currency_code,

        "cart_amount": float(converted_total),

        "cart_description": body.description or f"ZOZI Order #{order.id}",

        "paypage_lang": "ar" if preferred_language.startswith("ar") else "en",

        "customer_details": _paytabs_customer_details(order, current_user),

        "shipping_details": _paytabs_shipping_details(order, current_user),

        "callback": callback_url,

        "return": redirect_url,

    }



    try:

        async with httpx.AsyncClient(timeout=15) as client:

            response = await client.post(

                f"{_resolve_paytabs_api_base_url(db)}{DEFAULT_PAYTABS_REQUEST_PATH}",

                headers={"authorization": server_key, "content-type": "application/json"},

                json=payload,

            )

        data = response.json()

        if response.status_code not in (200, 201):

            raise HTTPException(status_code=400, detail=_paytabs_response_message(data))



        tran_ref = _paytabs_transaction_reference(data)

        if tran_ref:

            setattr(order, "payment_intent_id", tran_ref)

            db.commit()



        return {

            "transaction_reference": tran_ref or None,

            "redirect_url": data.get("redirect_url"),

            "status": _paytabs_response_status(data) or "initiated",

            "currency": currency_code,

            "display_amount": float(converted_total),

        }

    except HTTPException:

        raise

    except Exception as exc:

        logger.error("PayTabs charge error: %s", exc)

        raise HTTPException(status_code=500, detail="PayTabs payment service error")





async def confirm_paytabs_payment(body: ConfirmPayTabsPaymentRequest, current_user: dict, db: Session) -> dict:

    order = _get_user_order(body.order_id, current_user, db)

    if _normalized_payment_method(order) != PAYTABS_PAYMENT_METHOD:

        raise HTTPException(status_code=409, detail="This order is not configured for PayTabs payment")



    if order.paid_at is not None:

        return {

            "status": "confirmed",

            "order_id": order.id,

            "order_status": order.status,

            "tran_ref": str(getattr(order, "payment_intent_id", "") or "").strip() or body.tran_ref,

            "payment_status": "approved",

            "paid_at": order.paid_at,

        }



    payload = await _query_paytabs_transaction(body.tran_ref or cast(Optional[str], getattr(order, "payment_intent_id", None)), str(order.id), db)

    return _finalize_paytabs_transaction(order, payload, db)





def _verify_tap_signature(raw_body: bytes, sig_header: str, db: Session | None = None) -> bool:

    """

    Verify an incoming Tap webhook request.



    Tap signs each webhook POST with an HMAC-SHA256 digest calculated over the

    raw request body, using TAP_WEBHOOK_SECRET as the key.  The digest is

    delivered in the 'hashstring' header (Tap docs, 2024 API reference).



    Returns True when the signature is valid, False otherwise.

    If TAP_WEBHOOK_SECRET is not configured the function returns False so that

    the caller can reject the request with an appropriate HTTP error.

    """

    secret = _resolve_tap_webhook_secret(db)

    if not secret:

        return False

    expected = hmac.new(

        secret.encode("utf-8"),

        raw_body,

        hashlib.sha256,

    ).hexdigest()

    return hmac.compare_digest(expected, sig_header)





async def handle_tap_webhook(request: Request, db: Session) -> dict:

    raw_body = await request.body()



    # ── Signature verification ────────────────────────────────────────────────

    tap_webhook_secret = _resolve_tap_webhook_secret(db)

    if tap_webhook_secret:

        sig_header = request.headers.get("hashstring", "")

        if not sig_header or not _verify_tap_signature(raw_body, sig_header, db):

            logger.warning("tap_webhook: invalid or missing signature")

            raise HTTPException(status_code=400, detail="Invalid Tap webhook signature")

    else:

        # Secret not configured — log a warning but do NOT silently accept.

        # In production, TAP_WEBHOOK_SECRET must be set.

        logger.warning(

            "tap_webhook: TAP_WEBHOOK_SECRET is not configured; "

            "signature verification is skipped. Set TAP_WEBHOOK_SECRET in production."

        )



    try:

        import json

        data = json.loads(raw_body)

    except Exception:

        raise HTTPException(status_code=400, detail="Invalid JSON")



    charge_id = data.get("id")

    status = data.get("status", "").upper()



    if not charge_id:

        return {"status": "ignored"}



    # ── Idempotency: skip events we have already processed ────────────────────

    # Tap does not supply a unique event ID separate from the charge ID, so we

    # use "{charge_id}:{status}" as the composite idempotency key.

    tap_event_id = f"{charge_id}:{status}"

    already_processed = db.query(ProcessedWebhookEvent).filter(

        ProcessedWebhookEvent.event_id == tap_event_id,

        ProcessedWebhookEvent.processor == "tap",

    ).first()

    if already_processed:

        logger.info("tap_webhook duplicate ignored: event_id=%s", tap_event_id)

        return {"status": "ok"}



    order = db.query(Order).filter(Order.payment_intent_id == charge_id).first()

    if not order:

        logger.warning("tap_webhook: no order for charge %s", charge_id)

        return {"status": "unknown_order"}

    _finalize_tap_charge_status(order, data, db)



    # Record event as processed (idempotency guard)

    from domains.governance.ports import create_processed_webhook_event

    create_processed_webhook_event(db, event_id=tap_event_id, processor="tap")

    db.commit()

    logger.info("tap_webhook: charge %s order %s status=%s", charge_id, order.id, status)

    return {"status": "ok"}





async def handle_paytabs_callback(request: Request, db: Session) -> dict:

    raw_body = await request.body()

    signature = request.headers.get("X-PAYTABS-SIGNATURE", "")

    webhook_secret = _resolve_paytabs_webhook_secret(db)

    

    if webhook_secret and not _verify_paytabs_signature(raw_body, signature, webhook_secret):

        logger.warning("paytabs_callback: invalid signature")

        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    

    payload: dict[str, Any] = {}



    if raw_body:

        try:

            payload = json.loads(raw_body)

        except Exception:

            try:

                parsed = parse_qs(raw_body.decode("utf-8"), keep_blank_values=True)

                payload = {key: values[-1] for key, values in parsed.items() if values}

            except Exception:

                payload = {}



    for key, value in request.query_params.items():

        if key not in payload:

            payload[key] = value



    tran_ref = _paytabs_transaction_reference(payload)

    cart_id = str(payload.get("cart_id") or "").strip()

    if not tran_ref and not cart_id:

        return {"status": "ignored"}



    order = None

    if cart_id.isdigit():

        order = db.query(Order).filter(Order.id == int(cart_id)).first()

    if order is None and tran_ref:

        order = db.query(Order).filter(Order.payment_intent_id == tran_ref).first()

    if order is None:

        logger.warning("paytabs_callback: no order for tran_ref=%s cart_id=%s", tran_ref, cart_id)

        return {"status": "unknown_order"}



    queried = await _query_paytabs_transaction(tran_ref or None, cart_id or str(order.id), db)

    response_status = _paytabs_response_status(queried) or "pending"

    paytabs_event_id = f"{_paytabs_transaction_reference(queried) or tran_ref or cart_id}:{response_status}"

    already_processed = db.query(ProcessedWebhookEvent).filter(

        ProcessedWebhookEvent.event_id == paytabs_event_id,

        ProcessedWebhookEvent.processor == PAYTABS_PAYMENT_METHOD,

    ).first()

    if already_processed:

        logger.info("paytabs_callback duplicate ignored: event_id=%s", paytabs_event_id)

        return {"status": "ok"}



    _finalize_paytabs_transaction(order, queried, db)

    from domains.governance.ports import create_processed_webhook_event

    create_processed_webhook_event(db, event_id=paytabs_event_id, processor=PAYTABS_PAYMENT_METHOD)

    db.commit()

    logger.info("paytabs_callback: tran_ref=%s order=%s status=%s", _paytabs_transaction_reference(queried) or tran_ref, order.id, response_status)

    return {"status": "ok"}





# ── PayPal Payments ───────────────────────────────────────────────────────────





async def create_thawani_session(body: ThawaniCheckoutRequest, current_user: dict, db: Session) -> dict:

    """Create a Thawani hosted-checkout session and return the redirect URL."""

    configured, secret_key, publishable_key, api_base_url = _thawani_configured(db)

    if not configured:

        raise HTTPException(status_code=503, detail="Thawani Pay is not configured")

    if not _thawani_checkout_enabled(db):

        raise HTTPException(status_code=409, detail="Thawani Pay is currently disabled")



    order = _get_user_order(body.order_id, current_user, db)

    if _normalized_payment_method(order) != THAWANI_PAYMENT_METHOD:

        raise HTTPException(status_code=409, detail="This order is not configured for Thawani payment")

    if order.paid_at is not None:

        raise HTTPException(status_code=409, detail="Order is already paid")



    # Convert amount to OMR (from base AED) then to baisa (×1000), must be int

    charge_total = _order_charge_total_amount(order)

    omr_amount = convert_from_aed(charge_total, "OMR")

    unit_amount_baisa = max(1, int(round(float(omr_amount) * 1000)))



    is_uat = "uatcheckout" in api_base_url

    pay_base = DEFAULT_THAWANI_UAT_PAY_BASE if is_uat else DEFAULT_THAWANI_LIVE_PAY_BASE



    payload = {

        "client_reference_id": str(order.id),

        "mode": "payment",

        "products": [

            {

                "name": body.description or f"ZOZI Order #{order.id}",

                "unit_amount": unit_amount_baisa,

                "quantity": 1,

            }

        ],

        "success_url": body.success_url,

        "cancel_url": body.cancel_url,

        "metadata": {

            "Customer name": f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip(),

            "order id": str(order.id),

        },

    }



    try:

        async with httpx.AsyncClient(timeout=15) as client:

            resp = await client.post(

                f"{api_base_url}/checkout/session",

                headers={

                    "thawani-api-key": secret_key,

                    "Content-Type": "application/json",

                },

                json=payload,

            )

        data = resp.json()

        if resp.status_code not in (200, 201) or not data.get("success"):

            logger.error("Thawani session creation failed (%s): %s", resp.status_code, data)

            raise HTTPException(

                status_code=400,

                detail=str(data.get("description") or "Thawani checkout session creation failed"),

            )



        session_id = str((data.get("data") or {}).get("session_id") or "").strip()

        if not session_id:

            raise HTTPException(status_code=400, detail="Thawani did not return a session_id")



        checkout_url = f"{pay_base}/pay/{session_id}?key={publishable_key}"



        setattr(order, "payment_intent_id", session_id)

        db.commit()



        return {

            "session_id": session_id,

            "checkout_url": checkout_url,

            "currency": "OMR",

            "display_amount": float(omr_amount),

            "unit_amount_baisa": unit_amount_baisa,

        }

    except HTTPException:

        raise

    except Exception as exc:

        logger.error("Thawani session creation error: %s", exc)

        raise HTTPException(status_code=500, detail="Thawani payment service error")





async def handle_thawani_webhook(request: Request, db: Session) -> dict:

    """Verify and process Thawani webhook event notifications."""

    import json as _json



    body_bytes = await request.body()

    body_str = body_bytes.decode("utf-8", errors="replace")



    # ── Signature verification ────────────────────────────────────────────────

    thawani_timestamp = request.headers.get("thawani-timestamp", "")

    thawani_signature = request.headers.get("thawani-signature", "")



    webhook_secret = _resolve_thawani_webhook_secret(db)

    if webhook_secret:

        if not thawani_timestamp or not thawani_signature:

            logger.warning("thawani_webhook: missing signature headers")

            raise HTTPException(status_code=400, detail="Missing Thawani webhook signature headers")

        expected_sig = hmac.new(

            webhook_secret.encode("utf-8"),

            f"{body_str}-{thawani_timestamp}".encode("utf-8"),

            hashlib.sha256,

        ).hexdigest()

        if not hmac.compare_digest(expected_sig, thawani_signature):

            logger.warning("thawani_webhook: invalid signature")

            raise HTTPException(status_code=400, detail="Invalid Thawani webhook signature")

    else:

        logger.warning(

            "thawani_webhook: THAWANI_WEBHOOK_SECRET is not configured; "

            "signature verification is skipped. Set thawani_webhook_secret in production."

        )



    try:

        event_data = _json.loads(body_bytes)

    except Exception:

        raise HTTPException(status_code=400, detail="Invalid Thawani webhook payload")



    event_type = str(event_data.get("type") or event_data.get("event_type") or "").strip()

    data = event_data.get("data") or {}

    if not isinstance(data, dict):

        data = {}



    # ── Idempotency key: use invoice or session_id + event type ──────────────

    invoice_id = str(data.get("invoice") or data.get("id") or "").strip()

    session_id_field = str(data.get("session_id") or data.get("checkout_session_id") or "").strip()

    idempotency_key = f"thawani:{event_type}:{invoice_id or session_id_field}"



    if invoice_id or session_id_field:

        existing = db.query(ProcessedWebhookEvent).filter(

            ProcessedWebhookEvent.event_id == idempotency_key,

            ProcessedWebhookEvent.processor == THAWANI_PAYMENT_METHOD,

        ).first()

        if existing:

            return {"status": "duplicate"}



    # ── Resolve order ─────────────────────────────────────────────────────────

    order = None



    # For checkout.* events: client_reference_id is our order ID

    client_ref = str(data.get("client_reference_id") or "").strip()

    if client_ref and client_ref.isdigit():

        order = db.query(Order).filter(Order.id == int(client_ref)).first()



    # For payment.* events: checkout_invoice links back; try payment_intent_id match

    if order is None:

        checkout_invoice = str(data.get("checkout_invoice") or "").strip()

        if checkout_invoice:

            order = db.query(Order).filter(Order.payment_intent_id == checkout_invoice).first()



    # Fallback: match by session_id stored as payment_intent_id

    if order is None and session_id_field:

        order = db.query(Order).filter(Order.payment_intent_id == session_id_field).first()



    # ── Process event ─────────────────────────────────────────────────────────

    if event_type in ("checkout.session.completed", "session.completed"):

        payment_status = str(data.get("payment_status") or "").strip().lower()

        if payment_status == "paid" and order:

            if order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:

                _apply_successful_payment(

                    order,

                    f"Order #{order.id} payment via Thawani Pay was successful.",

                    db,

                )

                db.commit()

            try:




                enqueue_payment_confirmed_email(

                    cast(int, order.id),

                    provider="thawani",

                    message="Your Thawani Pay payment was successful and we are preparing your order.",

                )

            except Exception:

                logger.exception("Failed to enqueue Thawani payment-confirmed email for order %s", order.id if order else "unknown")



    elif event_type in ("payment.succeeded",):

        if order and order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:

            _apply_successful_payment(

                order,

                f"Order #{order.id} Thawani webhook: payment succeeded.",

                db,

            )

            db.commit()

            try:




                enqueue_payment_confirmed_email(cast(int, order.id), provider="thawani")

            except Exception:

                logger.exception("Thawani webhook: failed to enqueue payment email for order %s", order.id)



    elif event_type in ("payment.failed",):

        if order and order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:

            setattr(order, "status", "failed")

            from domains.comms.ports import create_notification, Notification

            create_notification(
                db,
                Notification(
                    user_id=order.user_id,
                    type="order_update",
                    title="Payment Failed",
                    message=f"Order #{order.id} Thawani payment failed.",
                    link=f"/orders/{order.id}",
                ),
            )

            db.commit()



    else:

        logger.debug("Unhandled Thawani webhook event: %s", event_type)



    if invoice_id or session_id_field:

        from domains.governance.ports import create_processed_webhook_event

        create_processed_webhook_event(db, event_id=idempotency_key, processor=THAWANI_PAYMENT_METHOD)

        db.commit()



    return {"status": "ok"}





class ConfirmThawaniPaymentRequest(BaseModel):

    order_id: int





async def confirm_thawani_payment(body: ConfirmThawaniPaymentRequest, current_user: dict, db: Session) -> dict:

    """Poll Thawani session status after the customer returns from the hosted checkout page.



    Called by the frontend when the customer lands back on our success URL.  The

    function re-queries Thawani's retrieve-session endpoint to get the authoritative

    payment_status and — if the status is 'paid' — applies the successful payment

    (idempotent: safe to call multiple times).



    Returns a dict with keys:

        status  "confirmed" | "pending" | "failed"

        order_id, order_status, session_id, paid_at

    """

    order = _get_user_order(body.order_id, current_user, db)



    # Already confirmed — return immediately

    if order.paid_at is not None:

        return {

            "status": "confirmed",

            "order_id": order.id,

            "order_status": order.status,

            "session_id": str(getattr(order, "payment_intent_id", "") or "").strip(),

            "paid_at": order.paid_at,

        }



    session_id = str(getattr(order, "payment_intent_id", "") or "").strip()

    if not session_id:

        return {

            "status": "pending",

            "order_id": order.id,

            "order_status": order.status,

            "session_id": None,

            "paid_at": None,

        }



    configured, secret_key, _pub_key, api_base_url = _thawani_configured(db)

    if not configured:

        return {

            "status": "pending",

            "order_id": order.id,

            "order_status": order.status,

            "session_id": session_id,

            "paid_at": None,

        }



    try:

        async with httpx.AsyncClient(timeout=10) as client:

            resp = await client.get(

                f"{api_base_url}/checkout/session/{session_id}",

                headers={"thawani-api-key": secret_key},

            )

        data = resp.json()

        session_data = data.get("data") or {}

        if not isinstance(session_data, dict):

            session_data = {}

        payment_status = str(session_data.get("payment_status") or "").strip().lower()

    except Exception as exc:

        logger.error("Thawani confirm: session retrieve error: %s", exc)

        return {

            "status": "pending",

            "order_id": order.id,

            "order_status": order.status,

            "session_id": session_id,

            "paid_at": None,

        }



    if payment_status == "paid":

        if order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:

            _apply_successful_payment(

                order,

                f"Order #{order.id} Thawani confirm: payment_status=paid.",

                db,

            )

            db.commit()

            try:




                enqueue_payment_confirmed_email(

                    cast(int, order.id),

                    provider="thawani",

                    message="Your Thawani Pay payment was successful and we are preparing your order.",

                )

            except Exception:

                logger.exception("Thawani confirm: failed to enqueue email for order %s", order.id)

        return {

            "status": "confirmed",

            "order_id": order.id,

            "order_status": order.status,

            "session_id": session_id,

            "paid_at": order.paid_at,

        }



    if payment_status in ("cancelled", "failed", "refunded"):

        if order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:

            setattr(order, "status", "failed")

            db.commit()

        return {

            "status": "failed",

            "order_id": order.id,

            "order_status": order.status,

            "session_id": session_id,

            "paid_at": None,

        }



    return {

        "status": "pending",

        "order_id": order.id,

        "order_status": order.status,

        "session_id": session_id,

        "paid_at": None,

    }





# ── Gateway Wizard Controller ───────────────────────────────────────────────────



