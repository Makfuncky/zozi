# -*- coding: utf-8 -*-
"""Message templates for SMS and WhatsApp notifications."""
from __future__ import annotations

from typing import Any


TEMPLATES: dict[str, dict[str, Any]] = {
    "order_confirmed_sms": {
        "id": "order_confirmed_sms",
        "channel": "sms",
        "description": "Order confirmed SMS",
        "body": "Your order {order_id} has been confirmed. Total: {total}. Thank you!",
    },
    "order_confirmed_whatsapp": {
        "id": "order_confirmed_whatsapp",
        "channel": "whatsapp",
        "description": "Order confirmed WhatsApp",
        "body": "✅ Your order {order_id} has been confirmed.\nTotal: {total}\nThank you for shopping with us!",
    },
    "order_shipped_sms": {
        "id": "order_shipped_sms",
        "channel": "sms",
        "description": "Order shipped SMS",
        "body": "Your order {order_id} has been shipped. Track: {tracking_url}",
    },
    "order_shipped_whatsapp": {
        "id": "order_shipped_whatsapp",
        "channel": "whatsapp",
        "description": "Order shipped WhatsApp",
        "body": "🚚 Your order {order_id} has been shipped.\nTrack: {tracking_url}",
    },
    "order_delivered_sms": {
        "id": "order_delivered_sms",
        "channel": "sms",
        "description": "Order delivered SMS",
        "body": "Your order {order_id} has been delivered. Thank you!",
    },
    "order_delivered_whatsapp": {
        "id": "order_delivered_whatsapp",
        "channel": "whatsapp",
        "description": "Order delivered WhatsApp",
        "body": "📦 Your order {order_id} has been delivered.\nThank you for shopping with us!",
    },
    "order_cancelled_sms": {
        "id": "order_cancelled_sms",
        "channel": "sms",
        "description": "Order cancelled SMS",
        "body": "Your order {order_id} has been cancelled. Refund: {refund_amount}",
    },
    "order_cancelled_whatsapp": {
        "id": "order_cancelled_whatsapp",
        "channel": "whatsapp",
        "description": "Order cancelled WhatsApp",
        "body": "❌ Your order {order_id} has been cancelled.\nRefund: {refund_amount}",
    },
    "payment_success_sms": {
        "id": "payment_success_sms",
        "channel": "sms",
        "description": "Payment success SMS",
        "body": "Payment of {amount} received for order {order_id}. Thank you!",
    },
    "payment_success_whatsapp": {
        "id": "payment_success_whatsapp",
        "channel": "whatsapp",
        "description": "Payment success WhatsApp",
        "body": "💳 Payment of {amount} received for order {order_id}.",
    },
    "payment_failed_sms": {
        "id": "payment_failed_sms",
        "channel": "sms",
        "description": "Payment failed SMS",
        "body": "Payment failed for order {order_id}. Please try again.",
    },
    "payment_failed_whatsapp": {
        "id": "payment_failed_whatsapp",
        "channel": "whatsapp",
        "description": "Payment failed WhatsApp",
        "body": "⚠️ Payment failed for order {order_id}.\nPlease update your payment method.",
    },
    "payment_refund_sms": {
        "id": "payment_refund_sms",
        "channel": "sms",
        "description": "Payment refund SMS",
        "body": "Refund of {amount} processed for order {order_id}.",
    },
    "payment_refund_whatsapp": {
        "id": "payment_refund_whatsapp",
        "channel": "whatsapp",
        "description": "Payment refund WhatsApp",
        "body": "💰 Refund of {amount} processed for order {order_id}.",
    },
    "delivery_assigned_sms": {
        "id": "delivery_assigned_sms",
        "channel": "sms",
        "description": "Delivery assigned SMS",
        "body": "Delivery assigned for order {order_id}. Driver: {driver_name}",
    },
    "delivery_assigned_whatsapp": {
        "id": "delivery_assigned_whatsapp",
        "channel": "whatsapp",
        "description": "Delivery assigned WhatsApp",
        "body": "🚛 Delivery assigned for order {order_id}.\nDriver: {driver_name}",
    },
    "delivery_picked_up_sms": {
        "id": "delivery_picked_up_sms",
        "channel": "sms",
        "description": "Delivery picked up SMS",
        "body": "Your order {order_id} has been picked up.",
    },
    "delivery_picked_up_whatsapp": {
        "id": "delivery_picked_up_whatsapp",
        "channel": "whatsapp",
        "description": "Delivery picked up WhatsApp",
        "body": "📤 Your order {order_id} has been picked up.",
    },
    "delivery_in_transit_sms": {
        "id": "delivery_in_transit_sms",
        "channel": "sms",
        "description": "Delivery in transit SMS",
        "body": "Your order {order_id} is in transit. ETA: {eta}",
    },
    "delivery_in_transit_whatsapp": {
        "id": "delivery_in_transit_whatsapp",
        "channel": "whatsapp",
        "description": "Delivery in transit WhatsApp",
        "body": "🚦 Your order {order_id} is in transit.\nETA: {eta}",
    },
    "delivery_completed_sms": {
        "id": "delivery_completed_sms",
        "channel": "sms",
        "description": "Delivery completed SMS",
        "body": "Your order {order_id} has been delivered. Thank you!",
    },
    "delivery_completed_whatsapp": {
        "id": "delivery_completed_whatsapp",
        "channel": "whatsapp",
        "description": "Delivery completed WhatsApp",
        "body": "✅ Your order {order_id} has been delivered.",
    },
    "payout_initiated_sms": {
        "id": "payout_initiated_sms",
        "channel": "sms",
        "description": "Payout initiated SMS",
        "body": "Payout of {amount} has been initiated. Ref: {payout_id}",
    },
    "payout_initiated_whatsapp": {
        "id": "payout_initiated_whatsapp",
        "channel": "whatsapp",
        "description": "Payout initiated WhatsApp",
        "body": "💸 Payout of {amount} has been initiated.\nRef: {payout_id}",
    },
    "payout_completed_sms": {
        "id": "payout_completed_sms",
        "channel": "sms",
        "description": "Payout completed SMS",
        "body": "Payout of {amount} completed. Ref: {payout_id}",
    },
    "payout_completed_whatsapp": {
        "id": "payout_completed_whatsapp",
        "channel": "whatsapp",
        "description": "Payout completed WhatsApp",
        "body": "✅ Payout of {amount} completed.\nRef: {payout_id}",
    },
    "flash_sale_sms": {
        "id": "flash_sale_sms",
        "channel": "sms",
        "description": "Flash sale SMS",
        "body": "Flash Sale! {discount_text} on {product_name}. Shop now: {product_url}",
    },
    "flash_sale_whatsapp": {
        "id": "flash_sale_whatsapp",
        "channel": "whatsapp",
        "description": "Flash sale WhatsApp",
        "body": "🔥 Flash Sale!\n{discount_text} on {product_name}.\nShop: {product_url}",
    },
    "product_launch_sms": {
        "id": "product_launch_sms",
        "channel": "sms",
        "description": "Product launch SMS",
        "body": "New product: {product_name} is now available! {product_url}",
    },
    "product_launch_whatsapp": {
        "id": "product_launch_whatsapp",
        "channel": "whatsapp",
        "description": "Product launch WhatsApp",
        "body": "🆕 New product: {product_name}\n{product_url}",
    },
    "promo_sms": {
        "id": "promo_sms",
        "channel": "sms",
        "description": "General promotion SMS",
        "body": "Special offer: {discount_text}. Use code {promo_code}. {product_url}",
    },
    "promo_whatsapp": {
        "id": "promo_whatsapp",
        "channel": "whatsapp",
        "description": "General promotion WhatsApp",
        "body": "🎉 Special offer!\n{discount_text}\nCode: {promo_code}\n{product_url}",
    },
    "welcome_sms": {
        "id": "welcome_sms",
        "channel": "sms",
        "description": "Welcome SMS",
        "body": "Welcome to ZOZI! Start shopping now.",
    },
    "welcome_whatsapp": {
        "id": "welcome_whatsapp",
        "channel": "whatsapp",
        "description": "Welcome WhatsApp",
        "body": "👋 Welcome to ZOZI!\nStart shopping now.",
    },
    "otp_sms": {
        "id": "otp_sms",
        "channel": "sms",
        "description": "OTP SMS",
        "body": "Your OTP is {code}. Valid for 5 minutes.",
    },
    "otp_whatsapp": {
        "id": "otp_whatsapp",
        "channel": "whatsapp",
        "description": "OTP WhatsApp",
        "body": "🔐 Your OTP is {code}\nValid for 5 minutes.",
    },
}


def render_template(template_id: str, **data: Any) -> str:
    template = TEMPLATES.get(template_id)
    if not template:
        raise ValueError(f"Template not found: {template_id}")
    body = template["body"]
    try:
        return body.format(**data)
    except KeyError as exc:
        raise ValueError(f"Missing template variable: {exc}") from exc


def get_channel(template_id: str) -> str:
    template = TEMPLATES.get(template_id)
    if not template:
        return "sms"
    return template["channel"]


def list_templates(channel: str | None = None) -> list[dict[str, Any]]:
    templates = list(TEMPLATES.values())
    if channel:
        templates = [t for t in templates if t["channel"] == channel]
    return templates
