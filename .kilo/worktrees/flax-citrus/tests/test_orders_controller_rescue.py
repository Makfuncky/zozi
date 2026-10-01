"""Tests for the Orders duplicate-shim rescue.

Verifies that the redundant root-level re-export shims
(backend/controllers/{cart,disputes,returns}_controller.py) were removed and
all importers were repointed to the canonical domain package
backend/controllers/orders/* without breaking the import chain.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"


def _import_symbols_ok() -> None:
    """Importing the canonical orders controllers must expose the symbols the
    old root shims forwarded to the routers."""
    import controllers.orders.cart_controller as cart
    import controllers.orders.disputes_controller as disputes
    import controllers.orders.returns_controller as returns

    for sym in ("get_cart", "sync_cart", "upsert_cart_item", "remove_cart_item",
                "clear_cart", "get_cart_shipping_quote", "CartItemIn",
                "CartSyncRequest", "CartShippingQuoteRequest"):
        assert hasattr(cart, sym), f"cart_controller missing {sym}"

    for sym in ("get_supplier_notification_preferences",
                "update_supplier_notification_preferences",
                "create_supplier_dispute", "list_supplier_disputes",
                "get_supplier_dispute", "list_admin_disputes",
                "get_admin_dispute", "update_admin_dispute",
                "bulk_update_admin_disputes"):
        assert hasattr(disputes, sym), f"disputes_controller missing {sym}"

    for sym in ("bulk_update_return_requests", "create_return_request",
                "get_return_request", "list_return_requests",
                "update_return_request", "list_supplier_return_requests",
                "update_supplier_return_request"):
        assert hasattr(returns, sym), f"returns_controller missing {sym}"


def test_canonical_orders_controllers_export_required_symbols() -> None:
    _import_symbols_ok()


def test_root_shims_are_gone() -> None:
    for name in ("cart_controller.py", "disputes_controller.py",
                 "returns_controller.py"):
        assert not (BACKEND / "controllers" / name).exists(), f"{name} still present"


def test_routers_repointed_to_canonical_orders() -> None:
    routers = BACKEND / "routers"
    # api_orders_routes.py -> cart
    cart_router = (routers / "api_orders_routes.py").read_text(encoding="utf-8")
    assert "import controllers.orders.cart_controller as cart_ctrl" in cart_router
    assert "import controllers.cart_controller" not in cart_router
    # api_orders_routes_3.py -> returns
    ret_router = (routers / "api_orders_routes_3.py").read_text(encoding="utf-8")
    assert "from controllers.orders.returns_controller import" in ret_router
    assert "from controllers.returns_controller import" not in ret_router
    # supplier_supplier_routes.py -> returns + disputes
    sup_router = (routers / "supplier_supplier_routes.py").read_text(encoding="utf-8")
    assert "import controllers.orders.returns_controller as returns_ctrl" in sup_router
    assert "import controllers.orders.disputes_controller as disputes_ctrl" in sup_router
    # admin_core_console.py -> disputes
    admin_router = (routers / "admin_core_console.py").read_text(encoding="utf-8")
    assert "from controllers.orders import disputes_controller" in admin_router
    assert "from controllers import disputes_controller" not in admin_router


def test_no_root_shim_imports_remain_in_codebase() -> None:
    # Compile-check: grep for any lingering root-shim imports.
    result = subprocess.run(
        [sys.executable, "-c",
         "import subprocess,sys;"
         "out=subprocess.run([sys.executable,'-m','py_compile']+__import__('glob').glob('controllers/*_controller.py'),"
         "capture_output=True,text=True);"
         "print('OK' if out.returncode==0 else out.stderr)"],
        cwd=str(BACKEND), capture_output=True, text=True,
    )
    # The above is just a safety compile; the real check is textual below.
    bad = []
    for p in BACKEND.rglob("*.py"):
        if p.is_relative_to(BACKEND / "controllers" / "orders"):
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for needle in ("import controllers.cart_controller",
                       "import controllers.disputes_controller",
                       "import controllers.returns_controller",
                       "from controllers.cart_controller",
                       "from controllers.disputes_controller",
                       "from controllers.returns_controller",
                       "from controllers import cart_controller",
                       "from controllers import disputes_controller",
                       "from controllers import returns_controller"):
            if needle in text:
                bad.append(f"{p.relative_to(BACKEND)}: {needle}")
    assert not bad, "Lingering root-shim imports found:\n" + "\n".join(bad)
