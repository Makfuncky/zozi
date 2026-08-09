"""Regression guard: keep orders cart_shipping_service functions within the QUAL3 line limit."""
import pathlib


def _find_backend():
    here = pathlib.Path(__file__).resolve().parent
    for candidate in (here.parent / "backend", here.parent.parent / "backend"):
        if (candidate / "services" / "orders" / "cart_shipping_service.py").exists():
            return candidate
    raise FileNotFoundError("backend/services/orders/cart_shipping_service.py not found")


MODULE = _find_backend() / "services" / "orders" / "cart_shipping_service.py"
LIMIT = 120


def _top_level_function_lengths(src):
    import ast
    tree = ast.parse(src)
    return {
        n.name: (n.end_lineno - n.lineno + 1)
        for n in tree.body
        if isinstance(n, ast.FunctionDef)
    }


def test_quote_supplier_groups_within_limit():
    lengths = _top_level_function_lengths(MODULE.read_text(encoding="utf-8"))
    assert "quote_supplier_groups" in lengths
    assert lengths["quote_supplier_groups"] <= LIMIT, lengths["quote_supplier_groups"]


def test_all_orders_cart_functions_within_limit():
    lengths = _top_level_function_lengths(MODULE.read_text(encoding="utf-8"))
    over = {name: ln for name, ln in lengths.items() if ln > LIMIT}
    assert not over, over
