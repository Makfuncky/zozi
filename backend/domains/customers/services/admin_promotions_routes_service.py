"""Auto-migrated service logic from routers/admin_promotions_routes.py."""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Path, Query, Body

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from infrastructure.utils.dependencies import require_admin

from infrastructure.utils.country_rls import get_country_or_404

from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context

import modules.commerce.routers.promotion_admin_controller as promo_ctrl


def _country_ctx(code: str, db: Session):
    cc = get_country_or_404(code.upper(), db)
    set_rls_context({code.upper()}, is_restricted=True)
    return cc

def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "admin_promotions_routes", "prefix": "/api/v1/promotions"}

def status():
    """Report whether a backing controller is importable."""
    return {"router": "admin_promotions_routes",
            "controller": "controllers.commerce.promotion_admin_controller",
            "public_functions": _CTRL_PUBLIC}

def create_coupon_for_country(code: str, coupon_code: str, discount_type: str, discount_value: float, minimum_order: Optional[float], maximum_discount: Optional[float], usage_limit: Optional[int], starts_at: Optional[str], expires_at: Optional[str], is_active: bool, _, db: Session):
    """Create a coupon scoped to a country."""
    _country_ctx(code, db)
    try:
        return promo_ctrl.create_coupon_by_country(
            code=code.upper(), coupon_code=coupon_code, discount_type=discount_type,
            discount_value=discount_value, minimum_order=minimum_order,
            maximum_discount=maximum_discount, usage_limit=usage_limit,
            starts_at=starts_at, expires_at=expires_at, is_active=is_active, db=db,
        )
    finally:
        clear_rls_context()

def create_banner_for_country(code: str, title: str, subtitle: Optional[str], image_url: Optional[str], link: Optional[str], cta_label: Optional[str], cta_url: Optional[str], banner_type: str, is_active: bool, sort_order: int, bg_color: Optional[str], text_color: Optional[str], subtitle_color: Optional[str], btn_bg_color: Optional[str], btn_text_color: Optional[str], badge_text: Optional[str], badge_color: Optional[str], effect: Optional[str], layout_json: Optional[str], video_url: Optional[str], _, db: Session):
    """Create a banner scoped to a country."""
    _country_ctx(code, db)
    try:
        return promo_ctrl.create_banner_by_country(
            code=code.upper(), title=title, subtitle=subtitle, image_url=image_url,
            link=link, cta_label=cta_label, cta_url=cta_url, banner_type=banner_type,
            is_active=is_active, sort_order=sort_order, bg_color=bg_color,
            text_color=text_color, subtitle_color=subtitle_color, btn_bg_color=btn_bg_color,
            btn_text_color=btn_text_color, badge_text=badge_text, badge_color=badge_color,
            effect=effect, layout_json=layout_json, video_url=video_url, db=db,
        )
    finally:
        clear_rls_context()

def update_banner_for_country(code: str, banner_id: int, title: Optional[str], subtitle: Optional[str], image_url: Optional[str], link: Optional[str], cta_label: Optional[str], cta_url: Optional[str], banner_type: Optional[str], is_active: Optional[bool], sort_order: Optional[int], bg_color: Optional[str], text_color: Optional[str], subtitle_color: Optional[str], btn_bg_color: Optional[str], btn_text_color: Optional[str], badge_text: Optional[str], badge_color: Optional[str], effect: Optional[str], layout_json: Optional[str], video_url: Optional[str], _, db: Session):
    """Update a country-scoped banner."""
    _country_ctx(code, db)
    try:
        return promo_ctrl.update_banner_by_country(
            code=code.upper(), banner_id=banner_id, title=title, subtitle=subtitle,
            image_url=image_url, link=link, cta_label=cta_label, cta_url=cta_url,
            banner_type=banner_type, is_active=is_active, sort_order=sort_order,
            bg_color=bg_color, text_color=text_color, subtitle_color=subtitle_color,
            btn_bg_color=btn_bg_color, btn_text_color=btn_text_color, badge_text=badge_text,
            badge_color=badge_color, effect=effect, layout_json=layout_json, video_url=video_url, db=db,
        )
    finally:
        clear_rls_context()

def delete_banner_for_country(code: str, banner_id: int, _, db: Session):
    """Delete a country-scoped banner."""
    _country_ctx(code, db)
    try:
        return promo_ctrl.delete_banner_by_country(code=code.upper(), banner_id=banner_id, db=db)
    finally:
        clear_rls_context()


