"""Cart module rescue tests.

Scope of this file: verify the cart module now follows the architecture circuit
(ARCHITECTURE_DIAGRAM.md §10):

  routers/cart.py  ->  controllers/cart_controller  ->  services (data ownership)

Specifically it asserts:
  * the router performs NO direct DB access (no db.query/add/commit/delete)
    and never instantiates ORM models (the W1/CG1 violations that previously
    lived in this router are gone),
  * the cart endpoints are mounted and auth-gated (GET /api/v1/cart -> 401
    without credentials; 200 with a stubbed user),
  * the router delegates every operation to ``controllers.cart_controller``
    and preserves the web client's response contract,
  * the controller's serialization / ref-based quantity logic is correct.

These tests deliberately avoid importing ``main`` (the app currently has an
unrelated dangling import on main.py:169 from the earlier rename) and avoid the
broken repo-wide ``client`` integration fixture.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

import controllers.cart_controller as cart_ctrl
from routers import cart as cart_router


# ── 1. Router is thin (no W1 / CG1) ───────────────────────────────────────────

def test_router_has_no_direct_db_access():
    text = open(cart_router.__file__, encoding="utf-8").read()
    assert "db.query(" not in text
    assert "db.add(" not in text
    assert "db.commit(" not in text
    assert "db.delete(" not in text
    # Routers must not instantiate ORM models directly.
    assert "from models import CartItem" not in text
    assert "CartItem(" not in text
    assert "Product(" not in text


def test_router_delegates_to_controller_only():
    """Every endpoint handler must call a cart_controller function."""
    src = open(cart_router.__file__, encoding="utf-8").read()
    for fn in ("get_cart_view", "upsert_cart_item", "set_cart_item_quantity",
               "clear_cart", "sync_cart", "get_cart_shipping_quote"):
        assert f"cart_ctrl.{fn}" in src, f"router does not delegate {fn}"


# ── 2. HTTP wiring (mounted + auth + delegation) ─────────────────────────────

def _mounted_client(user_id: int = 1):
    app = FastAPI()
    app.include_router(cart_router.router, prefix="/api/v1/cart")
    user = SimpleNamespace(id=user_id)

    def _auth():
        return user

    class _FakeDB:
        pass

    # Override the exact callables the router bound at import time.
    app.dependency_overrides[cart_router.get_current_user] = _auth
    app.dependency_overrides[cart_router.get_db] = lambda: _FakeDB()
    return app, user


def test_cart_route_mounted_and_auth_gated():
    app = FastAPI()
    app.include_router(cart_router.router, prefix="/api/v1/cart")

    def _raise401():
        raise HTTPException(status_code=401, detail="Not authenticated")

    app.dependency_overrides[cart_router.get_current_user] = _raise401
    with TestClient(app) as client:
        resp = client.get("/api/v1/cart")
    assert resp.status_code == 401


def test_get_cart_delegates_and_returns_view(monkeypatch):
    called = {}

    def fake_view(uid, db):
        called["uid"] = uid
        return {"items": [{"id": 1, "product_id": 2, "quantity": 3}], "subtotal": 30.0, "item_count": 1}

    monkeypatch.setattr(cart_ctrl, "get_cart_view", fake_view)
    app, user = _mounted_client()
    with TestClient(app) as client:
        resp = client.get("/api/v1/cart")
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"][0]["id"] == 1
    assert body["subtotal"] == 30.0
    assert body["item_count"] == 1
    assert called["uid"] == user.id


def test_add_to_cart_returns_message(monkeypatch):
    captured = {}

    def fake_upsert(uid, pid, qty, size, color, db):
        captured.update(uid=uid, pid=pid, qty=qty, size=size, color=color)

    monkeypatch.setattr(cart_ctrl, "upsert_cart_item", fake_upsert)
    app, user = _mounted_client()
    with TestClient(app) as client:
        resp = client.post("/api/v1/cart/items", json={"product_id": 7, "quantity": 2})
    assert resp.status_code == 200
    assert resp.json() == {"message": "Added to cart"}
    assert captured["uid"] == user.id
    assert captured["pid"] == 7
    assert captured["qty"] == 2


def test_update_cart_item_delegates_with_ref(monkeypatch):
    captured = {}

    def fake_set(uid, ref, qty, size, color, db):
        captured.update(uid=uid, ref=ref, qty=qty)

    monkeypatch.setattr(cart_ctrl, "set_cart_item_quantity", fake_set)
    app, user = _mounted_client()
    with TestClient(app) as client:
        resp = client.put("/api/v1/cart/items/42", json={"quantity": 5})
    assert resp.status_code == 200
    assert resp.json() == {"message": "Updated"}
    assert captured["ref"] == 42
    assert captured["qty"] == 5


def test_remove_cart_item_delegates_with_zero_qty(monkeypatch):
    captured = {}

    def fake_set(uid, ref, qty, size, color, db):
        captured.update(uid=uid, ref=ref, qty=qty)

    monkeypatch.setattr(cart_ctrl, "set_cart_item_quantity", fake_set)
    app, user = _mounted_client()
    with TestClient(app) as client:
        resp = client.delete("/api/v1/cart/items/99")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Removed"}
    assert captured["ref"] == 99
    assert captured["qty"] == 0


def test_clear_cart_delegates(monkeypatch):
    captured = {}

    def fake_clear(uid, db):
        captured["uid"] = uid

    monkeypatch.setattr(cart_ctrl, "clear_cart", fake_clear)
    app, user = _mounted_client()
    with TestClient(app) as client:
        resp = client.delete("/api/v1/cart")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Cart cleared"}
    assert captured["uid"] == user.id


# ── 3. Controller serialization logic (no ORM session needed) ─────────────────

def _fake_product(name="P", price=10.0, stock=10, is_active=True, variants=None, pid=2):
    return SimpleNamespace(id=pid, name=name, price=price, image_url="i.png",
                           is_active=is_active, stock=stock, variants=variants or [])


def _fake_item(item_id=1, product_id=2, quantity=3, selected_size="", selected_color="", product=None):
    return SimpleNamespace(id=item_id, product_id=product_id, quantity=quantity,
                           selected_size=selected_size, selected_color=selected_color,
                           product=product if product is not None else _fake_product())


def test_serialize_cart_item_rich_shape(monkeypatch):
    monkeypatch.setattr(cart_ctrl, "resolve_product_variant", lambda p, s, c: None)
    out = cart_ctrl._serialize_cart_item(_fake_item())
    assert out["product_name"] == "P"
    assert out["product_id"] == 2
    assert out["quantity"] == 3
    assert out["price"] == 10.0
    assert out["is_available"] is True
    assert out["product"]["name"] == "P"
    assert "selected_size" in out and "selected_color" in out


def test_serialize_cart_item_out_of_stock_unavailable(monkeypatch):
    monkeypatch.setattr(cart_ctrl, "resolve_product_variant", lambda p, s, c: None)
    product = _fake_product(stock=0)
    out = cart_ctrl._serialize_cart_item(_fake_item(product=product))
    assert out["is_available"] is False
    assert "out of stock" in (out["availability_reason"] or "")


def test_get_cart_view_subtotal_and_count(monkeypatch):
    items = [_fake_item(item_id=1, product_id=2, quantity=3, product=_fake_product(price=10.0)),
             _fake_item(item_id=2, product_id=3, quantity=1, product=_fake_product(price=5.0))]
    monkeypatch.setattr(cart_ctrl, "_load_cart_items", lambda uid, db: items)
    view = cart_ctrl.get_cart_view(1, db=None)
    assert view["item_count"] == 2
    assert view["subtotal"] == 35.0
    assert len(view["items"]) == 2


def test_set_cart_item_quantity_removes_when_zero(monkeypatch):
    item = _fake_item(item_id=5, product_id=2, quantity=3)
    store = {"items": [item], "committed": 0}

    class FakeDB:
        def query(self, model):
            return self

        def filter(self, *a, **k):
            return self

        def first(self):
            return store["items"][0] if store["items"] else None

        def delete(self, obj):
            store["items"].remove(obj)

        def commit(self):
            store["committed"] += 1

    monkeypatch.setattr(cart_ctrl, "_load_cart_items", lambda uid, db: store["items"])
    monkeypatch.setattr(cart_ctrl, "get_cart", lambda uid, db: list(store["items"]))
    result = cart_ctrl.set_cart_item_quantity(1, 5, 0, "", "", FakeDB())
    assert store["items"] == []  # line removed
    assert store["committed"] == 1
