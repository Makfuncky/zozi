"""Tests for the Core/Supplier/Logistics duplicate-shim rescue.

Verifies the redundant root-level re-export shims
(backend/controllers/{banner,supplier,logistics_partner}_controller.py) were
removed and all importers repointed to the canonical domain packages
(backend/controllers/{core,supplier,logistics}/*) without breaking the import
chain.

Note: `BannerCreate` is NOT re-exported by the canonical core banner controller
(it lives in data.schemas), so importers now import it directly from there.
"""
from __future__ import annotations

from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"


def test_canonical_targets_export_required_symbols() -> None:
    import controllers.core.banner_controller as banner
    import controllers.supplier.supplier_controller as supplier
    import controllers.logistics.logistics_partner_controller as logistics

    for sym in ("get_banners", "get_banner_by_id", "create_banner",
                "update_banner", "delete_banner", "BannerUpdate",
                "get_banners_page", "upload_banner_image"):
        assert hasattr(banner, sym), f"banner_controller missing {sym}"

    for sym in ("get_supplier_products", "update_supplier_order_status",
                "process_product_image", "process_image_with_tools",
                "persist_supplier_product", "list_public_suppliers",
                "admin_set_supplier_badge", "refresh_supplier_badge",
                "UNSET"):
        assert hasattr(supplier, sym), f"supplier_controller missing {sym}"

    for sym in ("list_partners", "create_partner", "update_partner",
                "delete_partner", "list_public_partners",
                "get_my_partner_profile"):
        assert hasattr(logistics, sym), f"logistics_partner_controller missing {sym}"


def test_root_shims_are_gone() -> None:
    for name in ("banner_controller.py", "supplier_controller.py",
                 "logistics_partner_controller.py"):
        assert not (BACKEND / "controllers" / name).exists(), f"{name} still present"


def test_banner_importers_repointed() -> None:
    for fn in ("admin_core_console.py", "admin_core_routes.py", "api_core_routes.py"):
        text = (BACKEND / "routers" / fn).read_text(encoding="utf-8")
        assert "from controllers.core.banner_controller import" in text
        assert "from controllers.banner_controller import" not in text
        # BannerCreate now sourced from data.schemas in the two routers that use it
        if fn != "admin_core_console.py":
            assert "from data.schemas import BannerCreate" in text


def test_supplier_importers_repointed() -> None:
    for fn in ("api_media_bulk.py", "public_supplier_routes.py",
               "supplier_supplier_routes.py"):
        text = (BACKEND / "routers" / fn).read_text(encoding="utf-8")
        assert "controllers.supplier.supplier_controller" in text
        assert "controllers.supplier_controller" not in text or \
            "controllers.supplier.supplier_controller" in text


def test_logistics_importers_repointed() -> None:
    console = (BACKEND / "routers" / "admin_core_console.py").read_text(encoding="utf-8")
    assert "import controllers.logistics.logistics_partner_controller as _lpc" in console
    lp = (BACKEND / "routers" / "logistics_partner.py").read_text(encoding="utf-8")
    assert "import controllers.logistics.logistics_partner_controller as ctrl" in lp


def test_no_root_shim_imports_remain() -> None:
    bad = []
    for p in BACKEND.rglob("*.py"):
        if p.is_relative_to(BACKEND / "controllers" / "core") or \
           p.is_relative_to(BACKEND / "controllers" / "supplier") or \
           p.is_relative_to(BACKEND / "controllers" / "logistics"):
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for needle in ("import controllers.banner_controller",
                       "import controllers.supplier_controller",
                       "import controllers.logistics_partner_controller",
                       "from controllers.banner_controller",
                       "from controllers.supplier_controller",
                       "from controllers.logistics_partner_controller",
                       "from controllers import banner_controller",
                       "from controllers import supplier_controller",
                       "from controllers import logistics_partner_controller"):
            if needle in text:
                bad.append(f"{p.relative_to(BACKEND)}: {needle}")
    assert not bad, "Lingering root-shim imports found:\n" + "\n".join(bad)
