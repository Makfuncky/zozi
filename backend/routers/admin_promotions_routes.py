"""admin promotions router.

Country-scoped promotion management (coupons, banners, flash sales) for the
admin front-end. The `country_router` is mounted under `/admin` by `main.py`
and exposes `/{code}/...` paths, mirroring the convention used by the other
admin routers (e.g. `admin_catalog_operations`).
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from sqlalchemy.orm import Session

from db.database import get_db
from utils.dependencies import require_admin
from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context
import controllers.promotion_admin_controller as promo_ctrl

router = APIRouter(prefix="/api/v1/promotions")

country_router = APIRouter()


@router.get("/admin_promotions_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "admin_promotions_routes", "prefix": "/api/v1/promotions"}


try:
    _CTRL_PUBLIC = [
        n for n in dir(promo_ctrl)
        if not n.startswith("_") and callable(getattr(promo_ctrl, n))
    ]
except Exception:
    _CTRL_PUBLIC = []


@router.get("/admin_promotions_routes/status")
def status():
    """Report whether a backing controller is importable."""
    return {"router": "admin_promotions_routes",
            "controller": "controllers.promotion_admin_controller",
            "public_functions": _CTRL_PUBLIC}


# ── Country-scoped promotion endpoints ─────────────────────────────────────
# Mounted under /admin by main.py, so paths begin with /{code}.

def _country_ctx(code: str, db: Session):
    cc = get_country_or_404(code.upper(), db)
    set_rls_context({code.upper()}, is_restricted=True)
    return cc


@country_router.post("/{code}/coupons")
def create_coupon_for_country(
    code: str = Path(..., description="ISO country code"),
    coupon_code: str = Body(...),
    discount_type: str = Body("percentage"),
    discount_value: float = Body(0),
    minimum_order: Optional[float] = Body(None),
    maximum_discount: Optional[float] = Body(None),
    usage_limit: Optional[int] = Body(None),
    starts_at: Optional[str] = Body(None),
    expires_at: Optional[str] = Body(None),
    is_active: bool = Body(True),
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
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


@country_router.post("/{code}/banners")
def create_banner_for_country(
    code: str = Path(..., description="ISO country code"),
    title: str = Body(...),
    subtitle: Optional[str] = Body(None),
    image_url: Optional[str] = Body(None),
    link: Optional[str] = Body(None),
    cta_label: Optional[str] = Body(None),
    cta_url: Optional[str] = Body(None),
    banner_type: str = Body("hero"),
    is_active: bool = Body(True),
    sort_order: int = Body(0),
    bg_color: Optional[str] = Body(None),
    text_color: Optional[str] = Body(None),
    subtitle_color: Optional[str] = Body(None),
    btn_bg_color: Optional[str] = Body(None),
    btn_text_color: Optional[str] = Body(None),
    badge_text: Optional[str] = Body(None),
    badge_color: Optional[str] = Body(None),
    effect: Optional[str] = Body(None),
    layout_json: Optional[str] = Body(None),
    video_url: Optional[str] = Body(None),
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
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


@country_router.put("/{code}/banners/{banner_id}")
def update_banner_for_country(
    code: str = Path(..., description="ISO country code"),
    banner_id: int = Path(...),
    title: Optional[str] = Body(None),
    subtitle: Optional[str] = Body(None),
    image_url: Optional[str] = Body(None),
    link: Optional[str] = Body(None),
    cta_label: Optional[str] = Body(None),
    cta_url: Optional[str] = Body(None),
    banner_type: Optional[str] = Body(None),
    is_active: Optional[bool] = Body(None),
    sort_order: Optional[int] = Body(None),
    bg_color: Optional[str] = Body(None),
    text_color: Optional[str] = Body(None),
    subtitle_color: Optional[str] = Body(None),
    btn_bg_color: Optional[str] = Body(None),
    btn_text_color: Optional[str] = Body(None),
    badge_text: Optional[str] = Body(None),
    badge_color: Optional[str] = Body(None),
    effect: Optional[str] = Body(None),
    layout_json: Optional[str] = Body(None),
    video_url: Optional[str] = Body(None),
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
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


@country_router.delete("/{code}/banners/{banner_id}")
def delete_banner_for_country(
    code: str = Path(..., description="ISO country code"),
    banner_id: int = Path(...),
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete a country-scoped banner."""
    _country_ctx(code, db)
    try:
        return promo_ctrl.delete_banner_by_country(code=code.upper(), banner_id=banner_id, db=db)
    finally:
        clear_rls_context()
