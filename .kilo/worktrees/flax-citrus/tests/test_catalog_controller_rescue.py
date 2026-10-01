"""Tests for the Catalog duplicate-shim rescue.

Verifies the redundant root-level re-export shims
(backend/controllers/{products,search,product_verification}_controller.py) were
removed and all importers repointed to the canonical domain package
backend/controllers/catalog/* without breaking the import chain.
"""
from __future__ import annotations

from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"


def test_canonical_catalog_controllers_export_required_symbols() -> None:
    import controllers.catalog.products_controller as products
    import controllers.catalog.search_controller as search
    import controllers.catalog.product_verification_controller as verification

    for sym in ("get_products", "get_product", "get_product_by_barcode",
                "get_supplier_names", "get_recommended_products",
                "autocomplete_products", "update_product_return_window"):
        assert hasattr(products, sym), f"products_controller missing {sym}"
    for sym in ("smart_search", "smart_search_from_parsed", "extract_terms",
                "parse_query", "COLOR_ALIASES"):
        assert hasattr(search, sym), f"search_controller missing {sym}"
    for sym in ("list_verifications", "create_verification",
                "bulk_update_verifications", "update_verification",
                "get_verification"):
        assert hasattr(verification, sym), f"product_verification_controller missing {sym}"

    # bump_product_cache_version lives in data.catalog_product_utils (not canonical)
    from data.catalog_product_utils import bump_product_cache_version
    assert callable(bump_product_cache_version)


def test_root_catalog_shims_are_gone() -> None:
    for name in ("products_controller.py", "search_controller.py",
                 "product_verification_controller.py"):
        assert not (BACKEND / "controllers" / name).exists(), f"{name} still present"


def test_routers_repointed_to_canonical_catalog() -> None:
    chatbot = (BACKEND / "controllers" / "ai" / "chatbot_controller.py").read_text(encoding="utf-8")
    assert "import controllers.catalog.search_controller as search_ctrl" in chatbot
    assert "import controllers.search_controller" not in chatbot

    commerce2 = (BACKEND / "routers" / "api_commerce_routes_2.py").read_text(encoding="utf-8")
    assert "from controllers.catalog.products_controller import get_products" in commerce2

    cat4 = (BACKEND / "routers" / "api_catalog_routes_4.py").read_text(encoding="utf-8")
    assert "from controllers.catalog.products_controller import (" in cat4
    assert "from data.catalog_product_utils import bump_product_cache_version" in cat4
    assert "from controllers.products_controller import" not in cat4

    cat3 = (BACKEND / "routers" / "api_catalog_routes_3.py").read_text(encoding="utf-8")
    assert "import controllers.catalog.product_verification_controller as ctrl" in cat3

    sup = (BACKEND / "routers" / "supplier_supplier_routes.py").read_text(encoding="utf-8")
    assert "import controllers.catalog.products_controller as products_ctrl" in sup


def test_no_root_catalog_shim_imports_remain() -> None:
    bad = []
    for p in BACKEND.rglob("*.py"):
        if p.is_relative_to(BACKEND / "controllers" / "catalog"):
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for needle in ("import controllers.products_controller",
                       "import controllers.search_controller",
                       "import controllers.product_verification_controller",
                       "from controllers.products_controller",
                       "from controllers.search_controller",
                       "from controllers.product_verification_controller",
                       "from controllers import products_controller",
                       "from controllers import search_controller",
                       "from controllers import product_verification_controller"):
            if needle in text:
                bad.append(f"{p.relative_to(BACKEND)}: {needle}")
    assert not bad, "Lingering root-shim imports found:\n" + "\n".join(bad)
