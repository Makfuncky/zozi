"""Gateway module — imports shared code from payment_engine."""

from domains.finance.services.payments.payment_engine import *

async def create_paypal_order(body: PayPalOrderRequest, current_user: dict, db: Session) -> dict:

    """Create a PayPal Orders API v2 order and return the approval URL."""

    configured, client_id, secret, base_url = _paypal_configured(db)

    if not configured:

        raise HTTPException(status_code=503, detail="PayPal not configured")

    if not _paypal_gateway_enabled(db):

        raise HTTPException(status_code=409, detail="PayPal payments are currently disabled")



    order = _get_user_order(body.order_id, current_user, db)

    if _normalized_payment_method(order) != "paypal":

        raise HTTPException(status_code=409, detail="This order is not configured for PayPal payment")

    if order.paid_at is not None:

        raise HTTPException(status_code=409, detail="Order is already paid")



    currency_code = _resolved_payment_currency(body.currency, body.country)

    charge_total = _order_charge_total_amount(order)

    converted_total = convert_from_aed(charge_total, currency_code)



    try:

        access_token = await _paypal_get_access_token(cast(str, client_id), cast(str, secret), base_url)



        payload = {

            "intent": "CAPTURE",

            "purchase_units": [

                {

                    "reference_id": str(order.id),

                    "custom_id": str(order.id),

                    "description": body.description or f"ZOZI Order #{order.id}",

                    "amount": {

                        "currency_code": currency_code,

                        "value": f"{converted_total:.2f}",

                    },

                }

            ],

            "application_context": {

                "brand_name": "ZOZI",

                "landing_page": "LOGIN",

                "user_action": "PAY_NOW",

                "return_url": body.return_url,

                "cancel_url": body.cancel_url,

            },

        }



        async with httpx.AsyncClient(timeout=15) as client:

            resp = await client.post(

                f"{base_url}/v2/checkout/orders",

                headers={

                    "Authorization": f"Bearer {access_token}",

                    "Content-Type": "application/json",

                    "Prefer": "return=representation",

                },

                json=payload,

            )

        data = resp.json()

        if resp.status_code not in (200, 201):

            logger.error("PayPal order creation failed (%s): %s", resp.status_code, data)

            raise HTTPException(

                status_code=400,

                detail=str(data.get("message") or "PayPal order creation failed"),

            )



        paypal_order_id = data.get("id")

        approve_url = next(

            (link["href"] for link in data.get("links", []) if link.get("rel") == "approve"),

            None,

        )

        if paypal_order_id:

            setattr(order, "payment_intent_id", paypal_order_id)

            db.commit()



        return {

            "paypal_order_id": paypal_order_id,

            "approve_url": approve_url,

            "status": data.get("status"),

            "currency": currency_code,

            "display_amount": float(converted_total),

        }

    except HTTPException:

        raise

    except Exception as exc:

        logger.error("PayPal order creation error: %s", exc)

        raise HTTPException(status_code=500, detail="PayPal payment service error")





async def capture_paypal_order(body: PayPalCaptureRequest, current_user: dict, db: Session) -> dict:

    """Capture an approved PayPal order (called after the customer approves on PayPal)."""

    configured, client_id, secret, base_url = _paypal_configured(db)

    if not configured:

        raise HTTPException(status_code=503, detail="PayPal not configured")



    order = _get_user_order(body.order_id, current_user, db)

    if order.paid_at is not None:

        raise HTTPException(status_code=409, detail="Order is already paid")



    try:

        access_token = await _paypal_get_access_token(cast(str, client_id), cast(str, secret), base_url)



        async with httpx.AsyncClient(timeout=15) as client:

            resp = await client.post(

                f"{base_url}/v2/checkout/orders/{body.paypal_order_id}/capture",

                headers={

                    "Authorization": f"Bearer {access_token}",

                    "Content-Type": "application/json",

                },

                json={},

            )

        data = resp.json()

        capture_status = str(data.get("status", "") or "").upper()



        if resp.status_code in (200, 201) and capture_status == "COMPLETED":

            capture_units = data.get("purchase_units", [])

            capture_id = None

            if capture_units:

                captures = capture_units[0].get("payments", {}).get("captures", [])

                if captures:

                    capture_id = captures[0].get("id")



            _apply_successful_payment(

                order,

                f"Order #{order.id} payment via PayPal was successful.",

                db,

            )

            if capture_id:

                setattr(order, "payment_intent_id", capture_id)

            db.commit()

            try:

                from domains.comms.services.transactional_email_service import enqueue_payment_confirmed_email



                enqueue_payment_confirmed_email(

                    cast(int, order.id),

                    provider="paypal",

                    message="Your PayPal payment was successful and we are preparing your order.",

                )

            except Exception:

                logger.exception("Failed to enqueue PayPal payment-confirmed email for order %s", order.id)



            return {

                "status": "confirmed",

                "order_id": order.id,

                "order_status": order.status,

                "capture_id": capture_id,

                "paypal_order_id": body.paypal_order_id,

                "paid_at": order.paid_at,

            }



        if capture_status in ("VOIDED", "DECLINED"):

            if order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:

                setattr(order, "status", "failed")

                db.add(

                    Notification(

                        user_id=order.user_id,

                        type="order_update",

                        title="Payment Failed",

                        message=f"Order #{order.id} PayPal payment failed.",

                        link=f"/orders/{order.id}",

                    )

                )

                db.commit()

            return {

                "status": "failed",

                "order_id": order.id,

                "order_status": order.status,

                "paypal_order_id": body.paypal_order_id,

                "paid_at": order.paid_at,

            }



        return {

            "status": "pending",

            "order_id": order.id,

            "order_status": order.status,

            "paypal_order_id": body.paypal_order_id,

            "capture_status": capture_status,

        }

    except HTTPException:

        raise

    except Exception as exc:

        logger.error("PayPal capture error: %s", exc)

        raise HTTPException(status_code=500, detail="PayPal payment service error")





async def handle_paypal_webhook(request: Request, db: Session) -> dict:

    """Verify and process PayPal webhook event notifications."""

    import json as _json



    body_bytes = await request.body()

    try:

        event_data = _json.loads(body_bytes)

    except Exception:

        raise HTTPException(status_code=400, detail="Invalid PayPal webhook payload")



    event_id = str(event_data.get("id") or "").strip()

    if event_id:

        existing = db.query(ProcessedWebhookEvent).filter(

            ProcessedWebhookEvent.event_id == event_id,

            ProcessedWebhookEvent.processor == "paypal",

        ).first()

        if existing:

            return {"status": "duplicate"}



    # Verify signature if webhook_id (stored as webhook_secret) is configured

    configured, client_id, secret, base_url = _paypal_configured(db)

    if configured:

        gw_record = _get_gateway_connection_record(db, "paypal")

        webhook_id = decrypt_secret(cast(str | None, getattr(gw_record, "webhook_secret", None))) if gw_record else None

        if client_id and secret and webhook_id:

            try:

                access_token = await _paypal_get_access_token(cast(str, client_id), cast(str, secret), base_url)

                verify_payload = {

                    "auth_algo": request.headers.get("paypal-auth-algo", ""),

                    "cert_url": request.headers.get("paypal-cert-url", ""),

                    "transmission_id": request.headers.get("paypal-transmission-id", ""),

                    "transmission_sig": request.headers.get("paypal-transmission-sig", ""),

                    "transmission_time": request.headers.get("paypal-transmission-time", ""),

                    "webhook_id": webhook_id,

                    "webhook_event": event_data,

                }

                async with httpx.AsyncClient(timeout=10) as http_client:

                    verify_resp = await http_client.post(

                        f"{base_url}/v1/notifications/verify-webhook-signature",

                        headers={

                            "Authorization": f"Bearer {access_token}",

                            "Content-Type": "application/json",

                        },

                        json=verify_payload,

                    )

                if verify_resp.json().get("verification_status") != "SUCCESS":

                    logger.warning("PayPal webhook signature failed: %s", verify_resp.text[:200])

                    raise HTTPException(status_code=400, detail="PayPal webhook signature invalid")

            except HTTPException:

                raise

            except Exception:

                logger.exception("PayPal webhook verification error")



    event_type = str(event_data.get("event_type", "") or "")

    resource = event_data.get("resource", {}) if isinstance(event_data.get("resource"), dict) else {}



    if event_type == "PAYMENT.CAPTURE.COMPLETED":

        capture_id = str(resource.get("id") or "").strip()

        # PayPal puts the custom_id (our order ID) on the purchase unit or resource

        custom_id = str(resource.get("custom_id") or "").strip()

        supplementary = resource.get("supplementary_data") or {}

        pp_order_id = (supplementary.get("related_ids") or {}).get("order_id", "")

        order_ref = custom_id or pp_order_id

        if order_ref and order_ref.isdigit():

            order = db.query(Order).filter(Order.id == int(order_ref)).first()

            if order and order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:

                if capture_id:

                    setattr(order, "payment_intent_id", capture_id)

                _apply_successful_payment(

                    order,

                    f"Order #{order.id} PayPal webhook: payment captured.",

                    db,

                )

                db.commit()

                try:

                    from domains.comms.services.transactional_email_service import enqueue_payment_confirmed_email



                    enqueue_payment_confirmed_email(cast(int, order.id), provider="paypal")

                except Exception:

                    logger.exception("PayPal webhook: failed to enqueue payment email for order %s", order.id)



    elif event_type in ("PAYMENT.CAPTURE.DENIED", "PAYMENT.CAPTURE.DECLINED"):

        custom_id = str(resource.get("custom_id") or "").strip()

        if custom_id and custom_id.isdigit():

            order = db.query(Order).filter(Order.id == int(custom_id)).first()

            if order and order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:

                setattr(order, "status", "failed")

                db.add(

                    Notification(

                        user_id=order.user_id,

                        type="order_update",

                        title="Payment Failed",

                        message=f"Order #{order.id} PayPal payment failed.",

                        link=f"/orders/{order.id}",

                    )

                )

                db.commit()



    elif event_type == "PAYMENT.CAPTURE.REFUNDED":

        # PayPal includes the original capture ID in resource links

        capture_id = ""

        for link in resource.get("links", []):

            if isinstance(link, dict) and link.get("rel") == "up":

                capture_id = str(link.get("href", "")).rsplit("/", 2)[-2]

                break

        if not capture_id:

            capture_id = str(resource.get("custom_id") or "").strip()

        order = db.query(Order).filter(Order.payment_intent_id == capture_id).first() if capture_id else None

        if order and order.status != "refunded":

            apply_order_status_change(order, "refunded", db)

            try:

                from domains.finance.services.treasury.cash_management_service import log_refund_bank_transaction

                log_refund_bank_transaction(

                    order,

                    db,

                    source="paypal_refund",

                    transaction_ref=str(resource.get("id") or f"paypal:refund:{order.id}"),

                    description=f"PayPal refund settled for order #{order.id}",

                    transaction_date=datetime.now(timezone.utc).replace(tzinfo=None),

                )

            except Exception:

                logger.exception("Failed to log PayPal refund bank transaction for order %s", order.id)

            db.add(

                Notification(

                    user_id=order.user_id,

                    type="order_update",

                    title="Refund Processed",

                    message=f"Your PayPal refund for Order #{order.id} has been processed.",

                    link=f"/orders/{order.id}",

                )

            )

            db.commit()

            try:

                from domains.comms.services.transactional_email_service import enqueue_refund_processed_email



                enqueue_refund_processed_email(cast(int, order.id), source="paypal")

            except Exception:

                logger.exception("Failed to enqueue PayPal refund email for order %s", order.id)



    else:

        logger.debug("Unhandled PayPal webhook event: %s", event_type)



    if event_id:

        db.add(ProcessedWebhookEvent(event_id=event_id, processor="paypal"))

        db.commit()



    return {"status": "ok"}





# ── Thawani Pay ───────────────────────────────────────────────────────────────



