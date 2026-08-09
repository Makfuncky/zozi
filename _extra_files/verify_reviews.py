"""Focused verification of the reviews flow without the broken test DB.

Patches the services layer so we exercise only the controller orchestration
(authz, dedup, verified-purchase, rating recompute, username enrichment) and
the router's response_model/schema wiring.
"""
from __future__ import annotations
import sys
from unittest.mock import patch

sys.path.insert(0, r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")

from db.schemas import ReviewCreate, ReviewOut
import controllers.reviews_controller as ctrl
from routers import reviews as reviews_router


def test_validation_edge():
    # Router-level: invalid rating must be rejected by pydantic.
    try:
        ReviewCreate(rating=6, comment="too high")
        raise AssertionError("rating=6 should have failed validation")
    except Exception as e:
        assert "between 1 and 5" in str(e) or "ge" in str(e) or "le" in str(e)
    # valid
    rc = ReviewCreate(rating=4, comment="ok", title="T")
    assert rc.rating == 4 and rc.comment == "ok"


def test_create_flow():
    class FakeReview:
        id = 100
        product_id = 1
        user_id = 7
        rating = 5
        title = "Great"
        comment = "Excellent product"
        image_url = None
        is_approved = False
        is_verified_purchase = True
        created_at = "2026-08-07T00:00:00"
        country_code = "OM"
        user = None

    with patch.object(ctrl, "product_exists", return_value=True), \
         patch.object(ctrl, "find_existing_review", return_value=None), \
         patch.object(ctrl, "has_verified_purchase", return_value=True), \
         patch.object(ctrl, "service_create_review", return_value=FakeReview()), \
         patch.object(ctrl, "recompute_product_rating") as rec:
        out = ctrl.create_review(
            1, ReviewCreate(rating=5, comment="Excellent product"),
            {"id": 7, "role": "customer", "username": "alice"}, db=None,
        )
    assert out["username"] == "alice", out
    assert out["rating"] == 5 and out["comment"] == "Excellent product"
    assert out["is_verified_purchase"] is True
    rec.assert_called_once_with(None, 1)


def test_duplicate_blocked():
    with patch.object(ctrl, "product_exists", return_value=True), \
         patch.object(ctrl, "find_existing_review", return_value=object()):
        try:
            ctrl.create_review(1, ReviewCreate(rating=5),
                               {"id": 7, "role": "customer", "username": "a"}, db=None)
            raise AssertionError("duplicate should 409")
        except Exception as e:
            assert e.status_code == 409


def test_product_not_found():
    with patch.object(ctrl, "product_exists", return_value=False):
        try:
            ctrl.create_review(1, ReviewCreate(rating=5),
                               {"id": 7, "role": "customer", "username": "a"}, db=None)
            raise AssertionError("missing product should 404")
        except Exception as e:
            assert e.status_code == 404


def test_list_serialization_with_username():
    class FakeReview:
        id = 200
        product_id = 2
        user_id = 9
        rating = 3
        title = None
        comment = "meh"
        image_url = None
        is_approved = True
        is_verified_purchase = False
        created_at = "2026-08-07T00:00:00"
        country_code = "OM"

        class user:
            username = "bob"

    # simulate eager-loaded relationship
    FakeReview.user = type("U", (), {"username": "bob"})()

    with patch.object(ctrl, "service_get_product_reviews", return_value=[FakeReview()]):
        rows = ctrl.get_product_reviews(2, 0, 50, db=None)
    assert rows[0]["username"] == "bob"
    assert rows[0]["rating"] == 3


def test_router_wiring():
    paths = {(m.path, frozenset(m.methods)) for m in reviews_router.router.routes}
    # GET list (path + query), GET by product, POST by product, DELETE by id
    assert ("/products/{product_id}", frozenset({"GET"})) in paths
    assert ("/products/{product_id}", frozenset({"POST"})) in paths
    assert ("/{review_id}", frozenset({"DELETE"})) in paths
    # No PUT route must exist (test_reviews.py asserts 405)
    put_routes = [m for m in reviews_router.router.routes if "PUT" in m.methods]
    assert not any("/{review_id}" in m.path for m in put_routes), "PUT must not be routed"


def test_response_model_matches_serialize():
    # Every field returned by _serialize must exist on ReviewOut
    fields = set(ReviewOut.model_fields.keys())
    needed = {"id", "product_id", "user_id", "username", "rating", "title",
              "comment", "image_url", "is_approved", "is_verified_purchase",
              "created_at", "country_code"}
    assert needed.issubset(fields)


if __name__ == "__main__":
    test_validation_edge()
    test_create_flow()
    test_duplicate_blocked()
    test_product_not_found()
    test_list_serialization_with_username()
    test_router_wiring()
    test_response_model_matches_serialize()
    print("ALL REVIEWS FLOW CHECKS PASSED")
