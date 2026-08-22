"""Regression guard: keep orders_controller.quote_supplier_groups within the QUAL3 line limit."""
import pathlib


def _find_backend():
    here = pathlib.Path(__file__).resolve().parent
    for parent in [here, *here.parents]:
        if (parent / "domains" / "orders" / "services" / "orders_controller.py").exists():
            return parent
    raise FileNotFoundError("backend/domains/orders/services/orders_controller.py not found")


MODULE = _find_backend() / "domains" / "orders" / "services" / "orders_controller.py"
LIMIT = 120
PINNED = [
    "quote_supplier_groups",
    "_match_supplier_shipping_zones_ctrl",
    "_quote_approved_partner_shipment_ctrl",
    "_build_zone_shipment_quote_ctrl",
    "_build_fallback_shipment_quote_ctrl",
]


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


def test_refactored_controller_helpers_within_limit():
    lengths = _top_level_function_lengths(MODULE.read_text(encoding="utf-8"))
    over = {name: lengths[name] for name in PINNED if lengths.get(name, 0) > LIMIT}
    assert not over, over
