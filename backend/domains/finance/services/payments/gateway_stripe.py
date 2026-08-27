"""Gateway module — imports shared code from payment_engine."""

from domains.finance.services.payments.payment_engine import (  # noqa: F401
    PaymentIntentRequest,
    StripeCheckoutSessionRequest,
    ConfirmCardPaymentRequest,
    _stripe_configured,
    _apply_stripe_runtime_key,
    _payment_provider_mode_allows,
    _get_user_order,
    _normalized_payment_method,
    _resolved_payment_currency,
    _order_charge_total_amount,
    _payment_intent_matches_order,
    _payment_intent_status,
    _payment_intent_id,
    _stripe_object_get,
    _stripe_metadata_map,
    _order_gateway_metadata,
    _apply_successful_payment,
    _safe_stripe_call,
    _check_payment_idempotency_key,
    _store_payment_idempotency_result,
    INVENTORY_RELEASE_STATUSES,
    REUSABLE_STRIPE_INTENT_STATUSES,
    logger,
    request_context,
    get_correlation_id,
    log_service_error,
    stripe,
    HTTPException,
    Request,
    Session,
    cast,
    Optional,
    dict,
    str,
    int,
    Decimal,
    Order,
    OrderItem,
    ProcessedWebhookEvent,
    Notification,
    convert_from_aed,
    money_to_minor_units_for_currency,
)

def create_payment_intent(body: PaymentIntentRequest, current_user: dict, db: Session) -> dict:
    with request_context(user_id=str(current_user.get("id"))):
        logger.info(
            "create_payment_intent_started",
            order_id=body.order_id,
            user_id=current_user.get("id"),
            correlation_id=get_correlation_id(),
        )
        try:
            return _create_payment_intent_inner(body, current_user, db)
        except HTTPException:
            raise
        except Exception as exc:
            log_service_error("payments", "create_payment_intent", exc, order_id=body.order_id)
            raise HTTPException(status_code=500, detail="Payment service error") from exc


def _create_payment_intent_inner(body: PaymentIntentRequest, current_user: dict, db: Session) -> dict:

    idempotency_key = getattr(body, "idempotency_key", None)
    if idempotency_key:
        cached = _check_payment_idempotency_key(idempotency_key)
        if cached is not None:
            logger.info("Idempotent payment intent replay for key=%s", idempotency_key)
            return cached

    if not _stripe_configured(db):

        raise HTTPException(status_code=503, detail="Payment service not configured")

    if not _payment_provider_mode_allows("stripe", db):

        raise HTTPException(status_code=409, detail="Stripe card payments are currently disabled by admin")

    _apply_stripe_runtime_key(db)



    order = _get_user_order(body.order_id, current_user, db)

    if _normalized_payment_method(order) != "card":

        raise HTTPException(status_code=409, detail="This order is not configured for card payment")

    if order.status in INVENTORY_RELEASE_STATUSES:

        raise HTTPException(status_code=409, detail="Order is already closed")

    if order.paid_at is not None:

        raise HTTPException(status_code=409, detail="Order is already paid")

    currency_code = _resolved_payment_currency(body.currency, body.country)

    charge_total = _order_charge_total_amount(order)

    converted_total = convert_from_aed(charge_total, currency_code)

    amount_minor = money_to_minor_units_for_currency(charge_total, currency_code)

    metadata: dict = {"user_id": str(current_user["id"])}

    metadata["order_id"] = str(order.id)

    metadata["base_currency"] = "AED"

    metadata["display_currency"] = currency_code

    metadata["zozi_amount_minor"] = str(amount_minor)

    metadata.update(_order_gateway_metadata(order))

    existing_payment_intent_id = cast(Optional[str], getattr(order, "payment_intent_id", None))



    if existing_payment_intent_id:

        try:

            existing_intent = stripe.PaymentIntent.retrieve(existing_payment_intent_id)

            existing_status = _payment_intent_status(existing_intent)

            existing_currency = str(_stripe_object_get(existing_intent, "currency", "") or "").upper()

            existing_client_secret = cast(Optional[str], _stripe_object_get(existing_intent, "client_secret", None))

            valid_existing, reason = _payment_intent_matches_order(

                existing_intent,

                order=order,

                expected_user_id=int(current_user["id"]),

                require_metadata=False,

            )

            if (

                existing_status in REUSABLE_STRIPE_INTENT_STATUSES

                and existing_currency == currency_code.upper()

                and existing_client_secret

                and valid_existing

            ):

                return {

                    "client_secret": existing_client_secret,

                    "payment_intent_id": _payment_intent_id(existing_intent) or existing_payment_intent_id,

                    "currency": currency_code,

                    "display_amount": float(converted_total),

                }

            if existing_status == "succeeded":

                _apply_successful_payment(

                    order,

                    f"Order #{order.id} payment was successful. We are preparing your order.",

                    db,

                )

                db.commit()

                raise HTTPException(status_code=409, detail="Order is already paid")

            if not valid_existing:

                logger.warning(

                    "Stored payment_intent_id failed validation for order %s: %s",

                    order.id,

                    reason,

                )

        except HTTPException:

            raise

        except Exception as exc:

            if exc.__class__.__module__.startswith("stripe"):

                logger.warning(

                    "Could not reuse Stripe payment intent %s for order %s: %s",

                    existing_payment_intent_id,

                    order.id,

                    getattr(exc, "user_message", str(exc)),

                )

            else:

                raise



    try:

        idempotency_key = (

            f"order:{order.id}:prev:{existing_payment_intent_id or 'none'}:"

            f"currency:{currency_code.lower()}"

        )

        def _create_intent():
            return stripe.PaymentIntent.create(
                amount=amount_minor,
                currency=currency_code.lower(),
                automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
                metadata=metadata,
                idempotency_key=idempotency_key,
            )

        intent = _safe_stripe_call("PaymentIntent.create", order.id, _create_intent)

        setattr(order, "payment_intent_id", intent.id)

        db.commit()

        logger.info(
            "payment_intent_created",
            order_id=order.id,
            payment_intent_id=intent.id,
            currency=currency_code,
            amount_minor=amount_minor,
            correlation_id=get_correlation_id(),
        )

        return {

            "client_secret": intent.client_secret,

            "payment_intent_id": intent.id,

            "currency": currency_code,

            "display_amount": float(converted_total),

        }

    except Exception as exc:

        if exc.__class__.__module__.startswith("stripe"):

            raise HTTPException(status_code=400, detail=str(getattr(exc, "user_message", str(exc))))

        raise HTTPException(status_code=500, detail="Payment service error")





def create_stripe_checkout_session(body: StripeCheckoutSessionRequest, current_user: dict, db: Session) -> dict:

    if not _stripe_configured(db):

        raise HTTPException(status_code=503, detail="Payment service not configured")

    if not _payment_provider_mode_allows("stripe", db):

        raise HTTPException(status_code=409, detail="Stripe card payments are currently disabled by admin")

    _apply_stripe_runtime_key(db)



    order = _get_user_order(body.order_id, current_user, db)

    if _normalized_payment_method(order) != "card":

        raise HTTPException(status_code=409, detail="This order is not configured for card payment")

    if order.status in INVENTORY_RELEASE_STATUSES:

        raise HTTPException(status_code=409, detail="Order is already closed")

    if order.paid_at is not None:

        raise HTTPException(status_code=409, detail="Order is already paid")



    currency_code = _resolved_payment_currency(body.currency, body.country)

    charge_total = _order_charge_total_amount(order)

    converted_total = convert_from_aed(charge_total, currency_code)

    amount_minor = money_to_minor_units_for_currency(charge_total, currency_code)

    metadata: dict[str, str] = {

        "user_id": str(current_user["id"]),

        "order_id": str(order.id),

        "base_currency": "AED",

        "display_currency": currency_code,

        "zozi_amount_minor": str(amount_minor),

        **_order_gateway_metadata(order),

    }



    try:

        def _create_session():
            return stripe.checkout.Session.create(
                mode="payment",
                success_url=body.success_url,
                cancel_url=body.cancel_url,
                client_reference_id=str(order.id),
                customer_email=str(current_user.get("email") or "").strip() or None,
                metadata=metadata,
                payment_method_types=["card"],
                line_items=[
                    {
                        "quantity": 1,
                        "price_data": {
                            "currency": currency_code.lower(),
                            "unit_amount": amount_minor,
                            "product_data": {
                                "name": f"ZOZI Order #{order.id}",
                                "description": f"Marketplace checkout for order #{order.id}",
                            },
                        },
                    }
                ],
            )

        session = _safe_stripe_call("checkout.Session.create", order.id, _create_session)

        session_id = str(_stripe_object_get(session, "id", "") or "").strip()

        if session_id:

            setattr(order, "payment_intent_id", session_id)

        db.commit()

        result = {

            "client_secret": intent.client_secret,

            "payment_intent_id": intent.id,

            "currency": currency_code,

            "display_amount": float(converted_total),

        }
        if idempotency_key:
            _store_payment_idempotency_result(idempotency_key, result)
        return result

    except Exception as exc:

        if exc.__class__.__module__.startswith("stripe"):

            raise HTTPException(status_code=400, detail=str(getattr(exc, "user_message", str(exc))))

        raise HTTPException(status_code=500, detail="Payment service error")





def confirm_card_payment(body: ConfirmCardPaymentRequest, current_user: dict, db: Session) -> dict:

    """

    Confirm card payment synchronously after frontend card confirmation.



    This reduces checkout latency by finalizing the order without waiting for

    asynchronous webhook delivery while remaining idempotent with webhook flow.

    """

    order = _get_user_order(body.order_id, current_user, db)

    if _normalized_payment_method(order) != "card":

        raise HTTPException(status_code=409, detail="This order is not configured for card payment")

    if order.status in INVENTORY_RELEASE_STATUSES:

        raise HTTPException(status_code=409, detail="Order is already closed")



    if body.payment_intent_id and order.payment_intent_id and body.payment_intent_id != order.payment_intent_id:

        raise HTTPException(status_code=409, detail="payment_intent_id does not match this order")



    if order.paid_at is not None:

        return {

            "status": "confirmed",

            "order_id": order.id,

            "order_status": order.status,

            "payment_intent_id": body.payment_intent_id or cast(Optional[str], getattr(order, "payment_intent_id", None)),

            "payment_status": "succeeded",

            "paid_at": order.paid_at,

        }



    if not _stripe_configured(db):

        raise HTTPException(status_code=503, detail="Payment service not configured")

    _apply_stripe_runtime_key(db)



    payment_intent_id = body.payment_intent_id or order.payment_intent_id

    checkout_session_id = (body.checkout_session_id or "").strip()

    if checkout_session_id:

        try:

            session = stripe.checkout.Session.retrieve(checkout_session_id)

        except Exception as exc:

            if exc.__class__.__module__.startswith("stripe"):

                raise HTTPException(status_code=400, detail=str(getattr(exc, "user_message", str(exc))))

            raise HTTPException(status_code=502, detail="Unable to verify checkout session") from exc



        session_client_reference = str(_stripe_object_get(session, "client_reference_id", "") or "").strip()

        if session_client_reference and session_client_reference != str(order.id):

            raise HTTPException(status_code=409, detail="checkout_session_id does not belong to this order")



        session_metadata = _stripe_metadata_map(session)

        if session_metadata.get("order_id") and session_metadata.get("order_id") != str(order.id):

            raise HTTPException(status_code=409, detail="checkout_session_id does not belong to this order")



        session_payment_intent = _stripe_object_get(session, "payment_intent", None)

        if isinstance(session_payment_intent, dict):

            payment_intent_id = str(_stripe_object_get(session_payment_intent, "id", "") or "").strip() or payment_intent_id

        else:

            payment_intent_id = str(session_payment_intent or payment_intent_id or "").strip() or None



    if not payment_intent_id:

        raise HTTPException(status_code=422, detail="payment_intent_id is required")



    try:

        intent = stripe.PaymentIntent.retrieve(payment_intent_id)

    except Exception as exc:

        if exc.__class__.__module__.startswith("stripe"):

            raise HTTPException(status_code=400, detail=str(getattr(exc, "user_message", str(exc))))

        raise HTTPException(status_code=502, detail="Unable to verify payment intent") from exc



    strict_metadata_match = not bool(order.payment_intent_id)

    valid_intent, validation_reason = _payment_intent_matches_order(

        intent,

        order=order,

        expected_user_id=int(current_user["id"]),

        require_metadata=strict_metadata_match,

    )

    if not valid_intent:

        logger.warning(

            "Stripe confirmation rejected for order=%s payment_intent=%s reason=%s",

            order.id,

            payment_intent_id,

            validation_reason,

        )

        raise HTTPException(status_code=409, detail="payment_intent_id does not belong to this order")



    if getattr(order, "payment_intent_id", None) != payment_intent_id:

        setattr(order, "payment_intent_id", payment_intent_id)



    intent_status = _payment_intent_status(intent)



    if intent_status == "succeeded":

        _apply_successful_payment(

            order,

            f"Order #{order.id} payment was successful. We are preparing your order.",

            db,

        )

        db.commit()

        return {

            "status": "confirmed",

            "order_id": order.id,

            "order_status": order.status,

            "payment_intent_id": payment_intent_id,

            "payment_status": intent_status,

            "paid_at": order.paid_at,

        }



    if intent_status in {"requires_payment_method", "canceled"}:

        setattr(order, "status", "failed")

        db.commit()

        return {

            "status": "failed",

            "order_id": order.id,

            "order_status": order.status,

            "payment_intent_id": payment_intent_id,

            "payment_status": intent_status,

            "paid_at": order.paid_at,

        }



    return {

        "status": "pending_verification",

        "order_id": order.id,

        "order_status": order.status,

        "payment_intent_id": payment_intent_id,

        "payment_status": intent_status or "pending",

        "paid_at": order.paid_at,

    }





# ── Stripe webhook ────────────────────────────────────────────────────────────



async def handle_stripe_webhook(request: Request, db: Session) -> dict:

    webhook_secret = _resolve_stripe_webhook_secret(db)

    if not webhook_secret:

        raise HTTPException(status_code=503, detail="Webhook secret not configured")

    _apply_stripe_runtime_key(db)



    payload = await request.body()

    sig_header = request.headers.get("stripe-signature")

    if not sig_header:

        raise HTTPException(status_code=400, detail="Missing stripe-signature header")



    try:

        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)

    except ValueError:

        raise HTTPException(status_code=400, detail="Invalid payload")

    except Exception as exc:

        if exc.__class__.__name__ == "SignatureVerificationError":

            raise HTTPException(status_code=400, detail="Invalid signature")

        raise



    event_type = event["type"]

    obj = event["data"]["object"]

    stripe_event_id = event.get("id", "")



    # ── Idempotency: skip events we have already processed ────────────────────

    if stripe_event_id:

        already_processed = db.query(ProcessedWebhookEvent).filter(

            ProcessedWebhookEvent.event_id == stripe_event_id,

            ProcessedWebhookEvent.processor == "stripe",

        ).first()

        if already_processed:

            logger.info("Stripe webhook duplicate ignored: event_id=%s", stripe_event_id)

            return {"status": "ok"}



    if event_type == "payment_intent.succeeded":

        pi_id = _payment_intent_id(obj)

        metadata = _stripe_metadata_map(obj)

        metadata_order_id = metadata.get("order_id")

        order = db.query(Order).filter(Order.payment_intent_id == pi_id).first()

        if not order and metadata_order_id and metadata_order_id.isdigit():

            order = db.query(Order).filter(Order.id == int(metadata_order_id)).first()

            if order and not getattr(order, "payment_intent_id", None):

                setattr(order, "payment_intent_id", pi_id)

        if order:

            valid_intent, validation_reason = _payment_intent_matches_order(

                obj,

                order=order,

                expected_user_id=int(cast(int, order.user_id)),

                require_metadata=False,

            )

            if not valid_intent:

                logger.error(

                    "payment_intent.succeeded rejected for order %s pi=%s reason=%s",

                    order.id,

                    pi_id,

                    validation_reason,

                )

            elif order.status in INVENTORY_RELEASE_STATUSES:

                logger.warning(

                    "payment_intent.succeeded ignored for terminal order %s in status %s",

                    order.id,

                    order.status,

                )

            elif order.paid_at is not None:

                logger.info(

                    "payment_intent.succeeded duplicate ignored for already processed order %s status=%s",

                    order.id,

                    order.status,

                )

            else:

                _apply_successful_payment(

                    order,

                    f"Order #{order.id} payment was successful. We are preparing your order.",

                    db,

                )

                db.commit()

                try:

                    from domains.comms.services.transactional_email_service import enqueue_payment_confirmed_email



                    enqueue_payment_confirmed_email(cast(int, order.id), provider="stripe", message="Your Stripe payment was successful and we are preparing your order.")

                except Exception:

                    logger.exception("Failed to enqueue Stripe payment-confirmed email for order %s", order.id)

                logger.info("payment_intent.succeeded: order %s status=%s", order.id, order.status)

        else:

            logger.warning("payment_intent.succeeded: no order for pi=%s", pi_id)



    elif event_type == "payment_intent.payment_failed":

        pi_id = _payment_intent_id(obj)

        metadata = _stripe_metadata_map(obj)

        metadata_order_id = metadata.get("order_id")

        last_error = _stripe_object_get(obj, "last_payment_error", {}) or {}

        error_msg = (

            last_error.get("message", "Payment failed")

            if isinstance(last_error, dict)

            else str(_stripe_object_get(last_error, "message", "Payment failed"))

        )

        order = db.query(Order).filter(Order.payment_intent_id == pi_id).first()

        if not order and metadata_order_id and metadata_order_id.isdigit():

            order = db.query(Order).filter(Order.id == int(metadata_order_id)).first()

            if order and not getattr(order, "payment_intent_id", None):

                setattr(order, "payment_intent_id", pi_id)

        if order:

            valid_intent, validation_reason = _payment_intent_matches_order(

                obj,

                order=order,

                expected_user_id=int(cast(int, order.user_id)),

                require_metadata=False,

            )

            if not valid_intent:

                logger.error(

                    "payment_intent.payment_failed rejected for order %s pi=%s reason=%s",

                    order.id,

                    pi_id,

                    validation_reason,

                )

            elif order.paid_at is not None or order.status in INVENTORY_RELEASE_STATUSES:

                logger.warning(

                    "payment_intent.payment_failed ignored for order %s in status %s paid_at=%s",

                    order.id,

                    order.status,

                    order.paid_at,

                )

            else:

                setattr(order, "status", "failed")

                db.add(

                    Notification(

                        user_id=order.user_id,

                        type="order_update",

                        title="Payment Failed",

                        message=f"Order #{order.id} payment failed: {error_msg}. Please try again.",

                        link=f"/orders/{order.id}",

                    )

                )

                db.commit()

                try:

                    from domains.comms.services.transactional_email_service import enqueue_payment_failed_email



                    enqueue_payment_failed_email(cast(int, order.id), provider="stripe", message=error_msg)

                except Exception:

                    logger.exception("Failed to enqueue Stripe payment-failed email for order %s", order.id)

                logger.info("payment_intent.payment_failed: order %s failed", order.id)



    elif event_type == "charge.refunded":

        pi_id = obj.get("payment_intent")

        if pi_id:

            order = db.query(Order).filter(Order.payment_intent_id == pi_id).first()

            if order:

                restored_inventory = apply_order_status_change(order, "refunded", db)

                try:

                    from domains.finance.services.treasury.cash_management_service import log_refund_bank_transaction
                    from domains.finance.services.treasury.cash_management_service import log_refund_bank_transaction

                    refund_items = obj.get("refunds", {}).get("data", [])

                    refund_ref = refund_items[0].get("id") if refund_items else None

                    log_refund_bank_transaction(

                        order,

                        db,

                        source="stripe_refund",

                        transaction_ref=refund_ref or f"{pi_id}:refund",

                        description=f"Stripe refund settled for order #{order.id}",

                        transaction_date=datetime.now(timezone.utc).replace(tzinfo=None),

                    )

                except Exception:

                    logger.exception("Failed to log Stripe refund bank transaction for order %s", order.id)

                db.add(

                    Notification(

                        user_id=order.user_id,

                        type="order_update",

                        title="Refund Processed",

                        message=f"Your refund for Order #{order.id} has been processed.",

                        link=f"/orders/{order.id}",

                    )

                )

                db.commit()

                try:

                    from domains.comms.services.transactional_email_service import enqueue_refund_processed_email



                    enqueue_refund_processed_email(cast(int, order.id), source="stripe")

                except Exception:

                    logger.exception("Failed to enqueue Stripe refund email for order %s", order.id)

                logger.info(

                    "charge.refunded: order %s refunded restored_inventory=%s",

                    order.id,

                    restored_inventory,

                )



    else:

        logger.debug("Unhandled Stripe event: %s", event_type)



    # Record event as processed (idempotency guard)

    if stripe_event_id:

        db.add(ProcessedWebhookEvent(event_id=stripe_event_id, processor="stripe"))

        db.commit()



    return {"status": "ok"}





# ── Tap Payments ──────────────────────────────────────────────────────────────



