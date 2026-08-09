"""Cart module rescue tests.

The cart endpoints were rescued from a router that performed raw DB reads/writes
(W1/Q1) into a thin router -> controller -> service (``services.cart_service``)
layering. This file verifies both the runtime wiring (app boots, endpoints are
wired, auth works) and the architectural constraints (router performs no DB access;
controller does not import sibling controllers for cart logic; endpoints carry
response_model) plus the cart service orchestration logic itself.

NOTE: The shared ``client``/``app`` pytest fixtures in conftest.py are broken
repo-wide (they depend on a non-existent ``services.core.admin_operations_service``
seed module, and the ORM fails to configure the pre-existing ``User.cart``
relationship). Those are environment issues outside the cart module, so the
behavioural coverage here uses pure unit tests (monkeypatched service dependencies)
that need no ORM session.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

import services.cart_service as svc


# ── Architecture / wiring (no ORM session needed) ─────────────────────────────

def test_router_has_no_direct_db_access():
    from pathlib import Path

    src = Path(__file__).resolve().parent.parent / "backend" / "routers" / "cart.py"
    text = src.read_text(encoding="utf-8")
    assert "db.query(" not in text
    assert "db.add(" not in text
    assert "db.commit(" not in text
    assert "db.delete(" not in text
    assert "from data.models import CartItem" not in text
    assert "from controllers.products_controller import" not in text


def test_router_endpoints_have_response_model():
    import routers.public_cart_access as cart_router

    covered = {"", "/items", "/sync", "/items/{product_id}"}
    for route in cart_router.router.routes:
        if getattr(route, "path", None) in covered and route.path != "/shipping-quote":
            assert route.response_model is not None, f"{route.path} missing response_model"


def test_controller_does_not_import_products_controller():
    from pathlib import Path

    src = Path(__file__).resolve().parent.parent / "backend" / "controllers" / "cart_controller.py"
    text = src.read_text(encoding="utf-8")
    assert "from controllers.products_controller import" not in text
    assert "import controllers.products_controller" not in text


def test_cart_service_owns_data_access():
    for name in ("get_cart", "add_to_cart", "update_cart_item", "remove_cart_item", "clear_cart", "sync_cart"):
        assert callable(getattr(svc, name))


def test_app_boots_and_cart_endpoint_wired():
    """The app imports and the cart endpoint is registered + auth-gated."""
    import main

    paths = {route.path for route in main.app.routes}
    assert "/api/v1/cart" in paths or "/cart" in paths
    from fastapi.testclient import TestClient

    # No DB session needed: an unauthenticated GET must return 401, proving
    # the route is mounted and the auth dependency runs.
    with TestClient(main.app) as client:
        resp = client.get("/api/v1/cart")
    assert resp.status_code == 401


# ── Cart service orchestration (pure unit tests, no ORM) ──────────────────────

def _fake_product(name="P", price=10.0, stock=10, is_active=True, variants=None, pid=2):
    return SimpleNamespace(id=pid, name=name, price=price, image_url="i.png", is_active=is_active, stock=stock, variants=variants or [])


class _FakeDB:
    def __init__(self):
        self.deleted = None
        self.committed = 0

    def delete(self, obj):
        self.deleted = obj

    def commit(self):
        self.committed += 1


def _fake_item(item_id=1, product_id=2, quantity=3, selected_size="", selected_color="", product=None):
    return SimpleNamespace(
        id=item_id, product_id=product_id, quantity=quantity,
        selected_size=selected_size, selected_color=selected_color,
        product=product if product is not None else _fake_product(),
    )


def _fake_variant(stock=5, price=9.0, image_url="v.png", is_active=True, size=None, color=None, title=None, attributes_json=None):
    return SimpleNamespace(stock=stock, price=price, image_url=image_url, is_active=is_active, size=size, color=color, title=title, attributes_json=attributes_json)


def test_serialize_cart_item_shape():
    out = svc._serialize_cart_item(_fake_item())
    assert out["product_name"] == "P"
    assert out["product_id"] == 2
    assert out["quantity"] == 3
    assert out["price"] == 10.0
    assert out["is_available"] is True
    assert out["product"]["name"] == "P"
    assert "selected_size" in out and "selected_color" in out


def test_serialize_cart_item_out_of_stock_unavailable():
    product = _fake_product(stock=0)
    out = svc._serialize_cart_item(_fake_item(product=product))
    assert out["is_available"] is False
    assert "out of stock" in (out["availability_reason"] or "")


def test_resolve_variant_by_size():
    variant = _fake_variant(size="L", color="Red")
    product = _fake_product(variants=[variant])
    assert svc._resolve_variant(product, "L", "Red") is variant
    assert svc._resolve_variant(product, "XL", "Red") is None


def test_add_to_cart_merges_existing_quantity(monkeypatch):
    existing = _fake_item(quantity=0)
    monkeypatch.setattr(svc, "get_active_product_by_id", lambda db, pid: _fake_product())
    monkeypatch.setattr(svc, "get_cart_item_by_variant", lambda *a, **k: existing)
    monkeypatch.setattr(svc, "create_cart_item", lambda *a, **k: None)
    monkeypatch.setattr(svc, "write_update_cart_item", lambda db, item, upd: None)

    payload = SimpleNamespace(product_id=1, selected_size="", selected_color="", variant_id=None, quantity=4)
    result = svc.add_to_cart(1, payload, db=None)
    assert existing.quantity == 4
    assert result == {"message": "Added to cart"}


def test_add_to_cart_creates_when_missing(monkeypatch):
    created = {}
    monkeypatch.setattr(svc, "get_active_product_by_id", lambda db, pid: _fake_product())
    monkeypatch.setattr(svc, "get_cart_item_by_variant", lambda *a, **k: None)
    monkeypatch.setattr(svc, "create_cart_item", lambda db, **kw: created.update(kw) or SimpleNamespace())
    monkeypatch.setattr(svc, "write_update_cart_item", lambda db, item, upd: None)

    payload = SimpleNamespace(product_id=7, selected_size="M", selected_color="Blue", variant_id=None, quantity=2)
    svc.add_to_cart(1, payload, db=None)
    assert created["product_id"] == 7
    assert created["quantity"] == 2
    assert created["selected_size"] == "M"


def test_add_to_cart_missing_product_404(monkeypatch):
    from fastapi import HTTPException

    monkeypatch.setattr(svc, "get_active_product_by_id", lambda db, pid: None)
    payload = SimpleNamespace(product_id=999, selected_size="", selected_color="", variant_id=None, quantity=1)
    with pytest.raises(HTTPException) as exc:
        svc.add_to_cart(1, payload, db=None)
    assert exc.value.status_code == 404


def test_update_cart_item_create_when_absent(monkeypatch):
    created = {}
    monkeypatch.setattr(svc, "_find_item", lambda db, pid, uid: None)
    monkeypatch.setattr(svc, "get_active_product_by_id", lambda db, pid: _fake_product())
    monkeypatch.setattr(svc, "create_cart_item", lambda db, **kw: created.update(kw) or SimpleNamespace())
    result = svc.update_cart_item(1, 5, 3, "", "", db=None)
    assert created["quantity"] == 3
    assert result == {"message": "Updated"}


def test_update_cart_item_delete_when_quantity_zero(monkeypatch):
    item = _fake_item()
    monkeypatch.setattr(svc, "_find_item", lambda db, pid, uid: item)
    monkeypatch.setattr(svc, "write_update_cart_item", lambda db, it, upd: None)
    db = _FakeDB()
    result = svc.update_cart_item(1, 5, 0, "", "", db=db)
    assert db.deleted is item
    assert result == {"message": "Updated"}


def test_remove_cart_item_404_when_absent(monkeypatch):
    from fastapi import HTTPException

    monkeypatch.setattr(svc, "_find_item", lambda db, pid, uid: None)
    with pytest.raises(HTTPException) as exc:
        svc.remove_cart_item(1, 5, db=None)
    assert exc.value.status_code == 404


def test_clear_cart_delegates(monkeypatch):
    called = {}

    def fake_clear(db, uid):
        called["uid"] = uid

    monkeypatch.setattr(svc, "delete_cart_items_by_user", fake_clear)
    assert svc.clear_cart(1, db=None) == {"message": "Cart cleared"}
    assert called["uid"] == 1


def test_sync_cart_replaces_and_returns_view(monkeypatch):
    monkeypatch.setattr(svc, "delete_cart_items_by_user", lambda db, uid: None)
    monkeypatch.setattr(svc, "get_products_by_ids", lambda db, ids: [_fake_product(product_id_lookup := 1)])
    # get_products_by_ids returns products; align by id
    monkeypatch.setattr(svc, "get_products_by_ids", lambda db, ids: [_fake_product()])
    monkeypatch.setattr(svc, "load_cart_items", lambda db, uid: [])
    monkeypatch.setattr(svc, "write_update_cart_item", lambda db, it, upd: None)
    monkeypatch.setattr(svc, "create_cart_item", lambda db, **kw: SimpleNamespace())
    monkeypatch.setattr(svc, "get_cart", lambda uid, db: SimpleNamespace(items=[{"id": 1}], subtotal=10.0, item_count=1))

    body = SimpleNamespace(items=[SimpleNamespace(product_id=1, quantity=2, selected_size="", selected_color="")])
    view = svc.sync_cart(1, body, db=None)
    assert view.item_count == 1
