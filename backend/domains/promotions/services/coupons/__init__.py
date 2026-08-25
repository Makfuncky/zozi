"""promotions domain — coupon business logic."""
from __future__ import annotations

from domains.promotions.services.coupons.coupon_service import *
from domains.promotions.services.coupons.customer_coupons_create_service import *
from domains.promotions.services.coupons.customer_coupons_mgmt_service import *
from domains.promotions.services.coupons.commerce_coupons_read_service import *
from domains.promotions.services.coupons.commerce_coupons_write_service import *
from domains.promotions.services.coupons.coupons_legacy_write_service import *

__all__: list[str] = []
