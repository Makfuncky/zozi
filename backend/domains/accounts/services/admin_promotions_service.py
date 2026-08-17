"""Auto-migrated service logic from routers/admin_promotions.py."""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Path, Query

from sqlalchemy.orm import Session

from modules.admin.routers.admin_controller import (
    archive_entity,
    bulk_archive_entities,
    bulk_restore_entities,
    restore_entity,
)

from infrastructure.database.database import get_db

from infrastructure.database.schemas import ArchiveRequest, BulkActionRequest

from models import (
    Banner,
    Coupon,
    FlashSale,
    PromotionEngineConfig,
    PromotionOrderTier,
    User,
)

from infrastructure.utils.country_rls import enforce_country_access

from infrastructure.utils.dependencies import require_admin
from services.admin.admin_commerce_configuration_service import _banner_to_dict
from services.admin.admin_commerce_configuration_service import _user_ctx







def create_coupon(code: str, discount_type: str, discount_value: float, minimum_order: Optional[float], maximum_discount: Optional[float], usage_limit: Optional[int], starts_at: Optional[str], expires_at: Optional[str], is_active: bool, country_code: Optional[str], _: User, db: Session):
    """Create a coupon (optionally scoped to a country)."""
    from datetime import datetime


    existing = db.query(Coupon).filter(Coupon.code == code).first()
    if existing:
        raise HTTPException(400, detail="Coupon code already exists")

    coupon = Coupon(
        code=code,
        discount_type=discount_type,
        discount_value=discount_value,
        minimum_order=minimum_order,
        maximum_discount=maximum_discount,
        usage_limit=usage_limit,
        starts_at=datetime.fromisoformat(starts_at) if starts_at else None,
        expires_at=datetime.fromisoformat(expires_at) if expires_at else None,
        is_active=is_active,
        country_code=country_code.upper() if country_code else None,
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon




























from services.admin.admin_commerce_configuration_service import get_promotion_config  # [MIGRATION COMPAT] re-export relocated symbol













from services.admin.admin_commerce_configuration_service import update_promotion_config  # [MIGRATION COMPAT] re-export relocated symbol










from services.admin.admin_commerce_configuration_service import list_coupons  # [MIGRATION COMPAT] re-export relocated symbol












from services.admin.admin_commerce_configuration_service import archive_coupon  # [MIGRATION COMPAT] re-export relocated symbol














from services.admin.admin_commerce_configuration_service import restore_coupon  # [MIGRATION COMPAT] re-export relocated symbol
from services.admin.admin_commerce_configuration_service import bulk_archive_coupons  # [MIGRATION COMPAT] re-export relocated symbol


# === auto-wiring re-exports (migration repair) ===
from services.admin.admin_commerce_configuration_service import (
    archive_banner,
    archive_flash_sale,
    bulk_archive_banners,
    bulk_archive_flash_sales,
    bulk_restore_banners,
    bulk_restore_coupons,
    bulk_restore_flash_sales,
    create_banner_by_country,
    create_banner_promotion,
    create_coupon_by_country,
    create_flash_sale,
    delete_banner_by_country,
    delete_banner_promotion,
    list_banners_by_country,
    list_banners_promotions,
    list_coupons_by_country,
    list_flash_sales,
    list_flash_sales_by_country,
    list_promotion_tiers,
    restore_banner,
    restore_flash_sale,
    update_banner_by_country,
    update_banner_promotion,
    update_flash_sale
)


