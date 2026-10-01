"""Promotions domain features."""
from __future__ import annotations

FEATURES = {
    "promotions.coupons.read": "Read coupons",
    "promotions.coupons.write": "Create/update coupons",
    "promotions.coupons.redeem": "Redeem coupons",
    "promotions.promotions.read": "Read promotions",
    "promotions.promotions.write": "Create/update promotions",
    "promotions.promotions.activate": "Activate promotions",
    "promotions.banners.read": "Read banners",
    "promotions.banners.write": "Manage banners",
    "promotions.bogo.read": "Read BOGO offers",
    "promotions.bogo.write": "Manage BOGO offers",
    "promotions.coins.read": "Read loyalty coins",
    "promotions.coins.write": "Manage loyalty coins",
    "promotions.coins.redeem": "Redeem loyalty coins",
    "promotions.marketing.email": "Send email campaigns",
    "promotions.marketing.whatsapp": "Send WhatsApp campaigns",
    "promotions.marketing.sms": "Send SMS campaigns",
    # ── Legacy / additional atoms (from services/features.py) ─────────────────
    "promotions.coupons.manage": "Create, update, and manage discount coupons and promo codes",
    "promotions.campaigns.read": "View promotion campaigns and their performance",
    "promotions.campaigns.manage": "Create and manage promotion campaigns and marketing automation",
    "promotions.engine.configure": "Configure promotion engine rules, eligibility, and discount stacking",
    "promotions.discounts.read": "View active discounts and pricing rules",
    "promotions.discounts.manage": "Create and manage discount rules and automatic price adjustments",
    "promotions.analytics": "View promotion performance analytics and conversion metrics",
}
