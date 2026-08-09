"""Tests for the Commerce duplicate-shim rescue.

Verifies the redundant root-level re-export shims
(backend/controllers/{coupons,promotion}_controller.py) were removed and their
single importer (routers/admin_core_console.py) was repointed to the canonical
domain package backend/controllers/commerce/* without breaking the import chain.
"""
from __future__ import annotations

from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"


def test_canonical_commerce_controllers_export_required_symbols() -> None:
    import controllers.commerce.coupons_controller as coupons
    import controllers.commerce.promotion_controller as promotion

    for sym in ("get_promotion_config", "update_promotion_config",
                "list_promotion_tiers", "create_promotion_tier",
                "update_promotion_tier", "delete_promotion_tier",
                "preview_order_tier_discount"):
        assert hasattr(promotion, sym), f"promotion_controller missing {sym}"
    assert hasattr(coupons, "create_coupon") or hasattr(coupons, "list_coupons") \
        or hasattr(coupons, "get_coupon"), "coupons_controller appears empty"


def test_root_commerce_shims_are_gone() -> None:
    for name in ("coupons_controller.py", "promotion_controller.py"):
        assert not (BACKEND / "controllers" / name).exists(), f"{name} still present"


def test_admin_core_console_repointed_to_canonical_commerce() -> None:
    text = (BACKEND / "routers" / "admin_core_console.py").read_text(encoding="utf-8")
    assert "from controllers.commerce.promotion_controller import" in text
    assert "from controllers.promotion_controller import" not in text


def test_no_root_commerce_shim_imports_remain() -> None:
    bad = []
    for p in BACKEND.rglob("*.py"):
        if p.is_relative_to(BACKEND / "controllers" / "commerce"):
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for needle in ("import controllers.coupons_controller",
                       "import controllers.promotion_controller",
                       "from controllers.coupons_controller",
                       "from controllers.promotion_controller",
                       "from controllers import coupons_controller",
                       "from controllers import promotion_controller"):
            if needle in text:
                bad.append(f"{p.relative_to(BACKEND)}: {needle}")
    assert not bad, "Lingering root-shim imports found:\n" + "\n".join(bad)
