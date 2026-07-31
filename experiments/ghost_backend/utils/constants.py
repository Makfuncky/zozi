"""Application-wide constants."""
from __future__ import annotations

ORDER_STATUSES = [
    "pending", "confirmed", "processing", "shipped", "out_for_delivery",
    "delivered", "cancelled", "returned", "refunded",
]

PAYMENT_STATUSES = ["pending", "paid", "failed", "refunded"]

USER_ROLES = ["customer", "supplier", "admin", "staff", "logistics_partner"]

MODERATION_STATUSES = ["pending", "approved", "rejected"]

RETURN_STATUSES = ["requested", "approved", "rejected", "received", "refunded"]

SHIPMENT_STATUSES = [
    "pending", "picked_up", "in_transit", "out_for_delivery",
    "delivered", "failed", "returned",
]

COUPON_TYPES = ["percentage", "fixed"]

PAYOUT_STATUSES = ["pending", "processing", "completed", "failed"]

ALLOWED_UPLOAD_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif", "application/pdf"]

ALLOWED_UPLOAD_FOLDERS = ["products", "banners", "avatars", "documents", "suppliers"]
