from __future__ import annotations

from typing import Any, Optional

from domains.catalog.services.promotion_admin_write_service import create_banner
from domains.catalog.services.promotion_admin_write_service import create_banner_by_country
from domains.catalog.services.promotion_admin_write_service import create_coupon
from domains.catalog.services.promotion_admin_write_service import create_coupon_by_country
from domains.catalog.services.promotion_admin_write_service import create_flash_sale as create_flash_sale__from_promotion_admin
from domains.catalog.services.promotion_admin_write_service import delete_banner
from domains.catalog.services.promotion_admin_write_service import delete_banner_by_country
from domains.catalog.services.promotion_admin_write_service import update_banner
from domains.catalog.services.promotion_admin_write_service import update_banner_by_country
from domains.catalog.services.promotion_admin_write_service import update_flash_sale as update_flash_sale__from_promotion_admin
from domains.catalog.services.promotion_admin_write_service import update_promotion_config as update_promotion_config__from_promotion_admin
import structlog
from infrastructure.routing.route_contract import post, put, delete

logger = structlog.get_logger(__name__)


@put("/api/v1/admin/promotions/config/{config_id}", deps=["admin", "db"], tags=["promotions"])
def update_config(config_id: int, engine_enabled: Optional[bool], stacking_mode: Optional[str], db, current_user: dict = None) -> dict:
    return update_promotion_config(db, config_id=config_id, engine_enabled=engine_enabled, stacking_mode=stacking_mode)


@post("/api/v1/admin/promotions/coupons", deps=["admin", "db"], tags=["promotions"])
def create_coupon(
    code: str,
    discount_type: str = "percentage",
    discount_value: float = 0,
    minimum_order: Optional[float] = None,
    maximum_discount: Optional[float] = None,
    usage_limit: Optional[int] = None,
    starts_at: Optional[str] = None,
    expires_at: Optional[str] = None,
    is_active: bool = True,
    country_code: Optional[str] = None,
    db=None,
    current_user: dict = None,
):
    return create_coupon(db, code=code, discount_type=discount_type, discount_value=discount_value,
                         minimum_order=minimum_order, maximum_discount=maximum_discount, usage_limit=usage_limit,
                         starts_at=starts_at, expires_at=expires_at, is_active=is_active, country_code=country_code)


@post("/api/v1/admin/{code}/coupons", deps=["admin", "db"], tags=["promotions"])
def create_coupon_by_country(
    code: str,
    coupon_code: str,
    discount_type: str = "percentage",
    discount_value: float = 0,
    minimum_order: Optional[float] = None,
    maximum_discount: Optional[float] = None,
    usage_limit: Optional[int] = None,
    starts_at: Optional[str] = None,
    expires_at: Optional[str] = None,
    is_active: bool = True,
    db=None,
    current_user: dict = None,
):
    return create_coupon_by_country(db, code=code, coupon_code=coupon_code, discount_type=discount_type,
                                    discount_value=discount_value, minimum_order=minimum_order,
                                    maximum_discount=maximum_discount, usage_limit=usage_limit,
                                    starts_at=starts_at, expires_at=expires_at, is_active=is_active)


@post("/api/v1/admin/promotions/flash-sales", deps=["admin", "db"], tags=["promotions"])
def create_flash_sale(
    title: str,
    discount_pct: float,
    starts_at: str,
    ends_at: str,
    description: Optional[str] = None,
    is_active: bool = True,
    country_code: Optional[str] = None,
    db=None,
    current_user: dict = None,
):
    return create_flash_sale(db, title=title, discount_pct=discount_pct, starts_at=starts_at, ends_at=ends_at,
                             description=description, is_active=is_active, country_code=country_code)


@put("/api/v1/admin/promotions/flash-sales/{sale_id}", deps=["admin", "db"], tags=["promotions"])
def update_flash_sale(
    sale_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    discount_pct: Optional[float] = None,
    starts_at: Optional[str] = None,
    ends_at: Optional[str] = None,
    is_active: Optional[bool] = None,
    country_code: Optional[str] = None,
    db=None,
    current_user: dict = None,
):
    return update_flash_sale(db, sale_id=sale_id, title=title, description=description, discount_pct=discount_pct,
                             starts_at=starts_at, ends_at=ends_at, is_active=is_active, country_code=country_code)


@post("/api/v1/admin/promotions/banners", deps=["admin", "db"], tags=["promotions"])
def create_banner(
    title: str,
    subtitle: Optional[str] = None,
    image_url: Optional[str] = None,
    link: Optional[str] = None,
    cta_label: Optional[str] = None,
    cta_url: Optional[str] = None,
    banner_type: str = "hero",
    is_active: bool = True,
    sort_order: int = 0,
    bg_color: Optional[str] = None,
    text_color: Optional[str] = None,
    subtitle_color: Optional[str] = None,
    btn_bg_color: Optional[str] = None,
    btn_text_color: Optional[str] = None,
    badge_text: Optional[str] = None,
    badge_color: Optional[str] = None,
    effect: Optional[str] = None,
    layout_json: Optional[str] = None,
    video_url: Optional[str] = None,
    country_code: Optional[str] = None,
    db=None,
    current_user: dict = None,
) -> dict:
    return create_banner(db, title=title, subtitle=subtitle, image_url=image_url, link=link, cta_label=cta_label,
                         cta_url=cta_url, banner_type=banner_type, is_active=is_active, sort_order=sort_order,
                         bg_color=bg_color, text_color=text_color, subtitle_color=subtitle_color,
                         btn_bg_color=btn_bg_color, btn_text_color=btn_text_color, badge_text=badge_text,
                         badge_color=badge_color, effect=effect, layout_json=layout_json, video_url=video_url,
                         country_code=country_code)


@put("/api/v1/admin/promotions/banners/{banner_id}", deps=["admin", "db"], tags=["promotions"])
def update_banner(
    banner_id: int,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    image_url: Optional[str] = None,
    link: Optional[str] = None,
    cta_label: Optional[str] = None,
    cta_url: Optional[str] = None,
    banner_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    sort_order: Optional[int] = None,
    bg_color: Optional[str] = None,
    text_color: Optional[str] = None,
    subtitle_color: Optional[str] = None,
    btn_bg_color: Optional[str] = None,
    btn_text_color: Optional[str] = None,
    badge_text: Optional[str] = None,
    badge_color: Optional[str] = None,
    effect: Optional[str] = None,
    layout_json: Optional[str] = None,
    video_url: Optional[str] = None,
    country_code: Optional[str] = None,
    db=None,
    current_user: dict = None,
) -> dict:
    return update_banner(db, banner_id=banner_id, title=title, subtitle=subtitle, image_url=image_url, link=link,
                         cta_label=cta_label, cta_url=cta_url, banner_type=banner_type, is_active=is_active,
                         sort_order=sort_order, bg_color=bg_color, text_color=text_color, subtitle_color=subtitle_color,
                         btn_bg_color=btn_bg_color, btn_text_color=btn_text_color, badge_text=badge_text,
                         badge_color=badge_color, effect=effect, layout_json=layout_json, video_url=video_url,
                         country_code=country_code)


@delete("/api/v1/admin/promotions/banners/{banner_id}", deps=["admin", "db"], tags=["promotions"])
def delete_banner(banner_id: int, admin_id: Any = None, db=None, current_user: dict = None) -> dict:
    return delete_banner(db, banner_id=banner_id, admin_id=admin_id)


@post("/api/v1/admin/{code}/banners", deps=["admin", "db"], tags=["promotions"])
def create_banner_by_country(
    code: str,
    title: str,
    subtitle: Optional[str] = None,
    image_url: Optional[str] = None,
    link: Optional[str] = None,
    cta_label: Optional[str] = None,
    cta_url: Optional[str] = None,
    banner_type: str = "hero",
    is_active: bool = True,
    sort_order: int = 0,
    bg_color: Optional[str] = None,
    text_color: Optional[str] = None,
    subtitle_color: Optional[str] = None,
    btn_bg_color: Optional[str] = None,
    btn_text_color: Optional[str] = None,
    badge_text: Optional[str] = None,
    badge_color: Optional[str] = None,
    effect: Optional[str] = None,
    layout_json: Optional[str] = None,
    video_url: Optional[str] = None,
    db=None,
    current_user: dict = None,
) -> dict:
    return create_banner_by_country(db, code=code, title=title, subtitle=subtitle, image_url=image_url, link=link,
                                    cta_label=cta_label, cta_url=cta_url, banner_type=banner_type, is_active=is_active,
                                    sort_order=sort_order, bg_color=bg_color, text_color=text_color,
                                    subtitle_color=subtitle_color, btn_bg_color=btn_bg_color, btn_text_color=btn_text_color,
                                    badge_text=badge_text, badge_color=badge_color, effect=effect, layout_json=layout_json,
                                    video_url=video_url)


@put("/api/v1/admin/{code}/banners/{banner_id}", deps=["admin", "db"], tags=["promotions"])
def update_banner_by_country(
    code: str,
    banner_id: int,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    image_url: Optional[str] = None,
    link: Optional[str] = None,
    cta_label: Optional[str] = None,
    cta_url: Optional[str] = None,
    banner_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    sort_order: Optional[int] = None,
    bg_color: Optional[str] = None,
    text_color: Optional[str] = None,
    subtitle_color: Optional[str] = None,
    btn_bg_color: Optional[str] = None,
    btn_text_color: Optional[str] = None,
    badge_text: Optional[str] = None,
    badge_color: Optional[str] = None,
    effect: Optional[str] = None,
    layout_json: Optional[str] = None,
    video_url: Optional[str] = None,
    db=None,
    current_user: dict = None,
) -> dict:
    return update_banner_by_country(db, code=code, banner_id=banner_id, title=title, subtitle=subtitle,
                                    image_url=image_url, link=link, cta_label=cta_label, cta_url=cta_url,
                                    banner_type=banner_type, is_active=is_active, sort_order=sort_order, bg_color=bg_color,
                                    text_color=text_color, subtitle_color=subtitle_color, btn_bg_color=btn_bg_color,
                                    btn_text_color=btn_text_color, badge_text=badge_text, badge_color=badge_color,
                                    effect=effect, layout_json=layout_json, video_url=video_url)


@delete("/api/v1/admin/{code}/banners/{banner_id}", deps=["admin", "db"], tags=["promotions"])
def delete_banner_by_country(code: str, banner_id: int, admin_id: Any = None, db=None, current_user: dict = None) -> dict:
    return delete_banner_by_country(db, code=code, banner_id=banner_id, admin_id=admin_id)
