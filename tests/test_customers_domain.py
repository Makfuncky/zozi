"""Tests for the customers-domain architectural repair (Phase E).

Verifies the specific changes made to the customers domain. Pure-function
logic is tested by extracting the real function source and executing it in
isolation (avoids triggering pre-existing broken imports in unrelated
domains that are out of scope for this repair). Structural compliance
(Law 3 imports, FK rules, event wiring) is tested by reading source.
"""
import ast
import os
import unittest
from unittest.mock import MagicMock, patch

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


def _exec_func(src_path, func_name, injected=None):
    """Extract a top-level function/method from a source file and exec it in
    an isolated namespace, avoiding the modules cross-domain imports."""
    base = os.path.join(os.path.dirname(__file__), "..", "backend")
    rel = src_path.replace("/", os.sep).replace("\\", os.sep)
    if not rel.endswith(".py"):
        rel += ".py"
    path = os.path.join(base, rel)
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    node = None
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name == func_name:
            node = n
            break
        if isinstance(n, ast.ClassDef):
            for item in n.body:
                if isinstance(item, ast.FunctionDef) and item.name == func_name:
                    node = item
                    break
            if node is not None:
                break
    assert node is not None, f"function {func_name} not found in {path}"
    # Drop type annotations so the extracted function executes without needing
    # the cross-domain types it references (Session, Dict, model classes, etc.).
    for arg in node.args.args:
        arg.annotation = None
    for arg in node.args.posonlyargs:
        arg.annotation = None
    for arg in node.args.kwonlyargs:
        arg.annotation = None
    if node.args.vararg:
        node.args.vararg.annotation = None
    if node.args.kwarg:
        node.args.kwarg.annotation = None
    node.returns = None
    # For instance methods, drop the `self` parameter.
    if node.args.args and node.args.args[0].arg == "self":
        node.args.args = node.args.args[1:]
    module_node = ast.Module(body=[node], type_ignores=[])
    ast.fix_missing_locations(module_node)
    code = compile(module_node, path, "exec")
    ns = {"__name__": "__test__"}
    if injected:
        ns.update(injected)
    exec(code, ns)
    return ns[func_name]


class TestReferralCodePure(unittest.TestCase):
    """B.1/B.3: _code_for_user is deterministic, unique, URL-safe."""

    def setUp(self):
        self._code_for_user = _exec_func(
            "domains/customers/services/referrals_service",
            "_code_for_user",
            injected={"base64": __import__("base64")},
        )

    def test_deterministic(self):
        self.assertEqual(self._code_for_user(42), self._code_for_user(42))

    def test_unique_per_user(self):
        codes = {self._code_for_user(i) for i in range(1, 500)}
        self.assertEqual(len(codes), 499)

    def test_url_safe(self):
        for uid in [1, 2, 999999, 12345678]:
            code = self._code_for_user(uid)
            self.assertNotIn("+", code)
            self.assertNotIn("/", code)
            self.assertNotIn("=", code)
            self.assertTrue(code)

    def test_returns_string(self):
        self.assertIsInstance(self._code_for_user(1), str)


class TestGetReferralConfig(unittest.TestCase):
    """B.1/B.5: config falls back to safe defaults; maps row attrs."""

    def setUp(self):
        self.promotion_cfg = MagicMock()
        self.get_referral_config = _exec_func(
            "domains/customers/services/referrals_service",
            "get_referral_config",
            injected={"PromotionEngineConfig": self.promotion_cfg},
        )

    def _mock_db(self, row=None):
        db = MagicMock()
        db.query.return_value.order_by.return_value.first.return_value = row
        return db

    def test_no_row_defaults(self):
        cfg = self.get_referral_config(self._mock_db(None))
        self.assertEqual(cfg["enabled"], False)
        self.assertEqual(cfg["referrer_points"], 0)
        self.assertEqual(cfg["referee_points"], 0)

    def test_row_maps_attrs(self):
        row = MagicMock()
        row.allow_referral_rewards = True
        row.referral_referrer_points = 50
        row.referral_referee_points = 25
        row.referral_monthly_cap = 10
        row.referral_verification_delay_days = 7
        cfg = self.get_referral_config(self._mock_db(row))
        self.assertEqual(cfg["enabled"], True)
        self.assertEqual(cfg["referrer_points"], 50)
        self.assertEqual(cfg["referee_points"], 25)


class TestGetOrCreateReferralCode(unittest.TestCase):
    """D4: returns deterministic code WITHOUT persisting a placeholder."""

    def setUp(self):
        self.referral = MagicMock()
        self.promotion_cfg = MagicMock()
        self._code_for_user = _exec_func(
            "domains/customers/services/referrals_service",
            "_code_for_user",
            injected={"base64": __import__("base64")},
        )
        self.get_or_create_referral_code = _exec_func(
            "domains/customers/services/referrals_service",
            "get_or_create_referral_code",
            injected={"Referral": self.referral, "PromotionEngineConfig": self.promotion_cfg,
                     "_code_for_user": self._code_for_user},
        )

    def _mock_db(self, existing=None):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = existing
        return db

    def test_no_existing_no_write(self):
        result = self.get_or_create_referral_code(7, self._mock_db(None))
        self.assertTrue(result["referral_code"])
        self.assertEqual(result["status"], "active")

    def test_existing_returns_status(self):
        existing = MagicMock()
        existing.status = "pending"
        result = self.get_or_create_referral_code(7, self._mock_db(existing))
        self.assertEqual(result["status"], "pending")

    def test_source_does_not_persist(self):
        base = os.path.join(os.path.dirname(__file__), "..", "backend")
        with open(os.path.join(base, "domains", "customers", "services",
                               "referrals_service.py"), encoding="utf-8") as f:
            src = f.read()
        self.assertNotIn("db.add(", src)
        self.assertNotIn("db.commit()", src)
        self.assertNotIn("db.refresh(", src)

    def test_deterministic_code(self):
        self.assertTrue(self._code_for_user(7))
        self.assertNotEqual(self._code_for_user(7), self._code_for_user(8))


class TestReviewsValidation(unittest.TestCase):
    """B.5/D2: rating validated; no created_by attribute passed."""

    def test_invalid_rating_raises(self):
        from sqlalchemy.orm import Session
        from typing import Optional
        fn = _exec_func(
            "domains/customers/services/reviews_service",
            "create_review",
            injected={"Session": Session, "Optional": Optional, "Review": MagicMock()},
        )
        with self.assertRaises(ValueError):
            fn(db=MagicMock(), product_id=1, user_id=1, rating=0)
        with self.assertRaises(ValueError):
            fn(db=MagicMock(), product_id=1, user_id=1, rating=6)

    def test_no_created_by_in_source(self):
        base = os.path.join(os.path.dirname(__file__), "..", "backend")
        with open(os.path.join(base, "domains", "customers", "services",
                               "reviews_service.py"), encoding="utf-8") as f:
            src = f.read()
        self.assertNotIn("created_by=", src)


class TestHealthEngine(unittest.TestCase):
    """D7/B.1: missing user raises 404; pure helpers safe."""

    def test_missing_user_raises_404_source(self):
        base = os.path.join(os.path.dirname(__file__), "..", "backend")
        with open(os.path.join(base, "domains", "customers", "services",
                               "customer_health_engine.py"), encoding="utf-8") as f:
            src = f.read()
        self.assertIn("raise HTTPException(status_code=404", src)
        self.assertNotIn('return {"error": "Customer not found"}', src)

    def test_purchase_frequency_single(self):
        f = _exec_func(
            "domains/customers/services/customer_health_engine",
            "_calculate_purchase_frequency",
        )
        self.assertEqual(f([MagicMock()]), 1.0)

    def test_refund_ratio_empty(self):
        f = _exec_func(
            "domains/customers/services/customer_health_engine",
            "_calculate_refund_ratio",
        )
        self.assertEqual(f([], []), 0.0)


class TestModelSingleOwnership(unittest.TestCase):
    """D1: single canonical Referral/ReferralPointEvent class + schema rules."""

    def test_referral_single(self):
        from domains.accounts.models.user import Referral as A
        from domains.customers.models.customer_schema_models import Referral as C
        self.assertIs(A, C)

    def test_point_event_single(self):
        from domains.accounts.models.user import ReferralPointEvent as A
        from domains.customers.models.customer_schema_models import ReferralPointEvent as C
        self.assertIs(A, C)

    def test_fk_target(self):
        from domains.customers.models.customer_schema_models import Referral
        fks = {c.name: list(c.foreign_keys)[0].target_fullname
               for c in Referral.__table__.columns if c.foreign_keys}
        self.assertEqual(fks["referrer_id"], "accounts.users.id")
        self.assertEqual(fks["referred_id"], "accounts.users.id")

    def test_ondelete_set(self):
        """DBA07: FKs have explicit ondelete RESTRICT."""
        from domains.customers.models.customer_schema_models import Referral, ReferralPointEvent
        for model in [Referral, ReferralPointEvent]:
            for c in model.__table__.columns:
                for fk in c.foreign_keys:
                    self.assertEqual(fk.ondelete, "RESTRICT",
                                     f"{model.__name__}.{c.name} missing ondelete")

    def test_referred_user_id_indexed(self):
        """DBA08: referred_user_id FK is indexed."""
        from domains.customers.models.customer_schema_models import ReferralPointEvent
        indexed = {idx.columns.keys()[0] for idx in ReferralPointEvent.__table__.indexes}
        self.assertIn("referred_user_id", indexed)

    def test_schema(self):
        from domains.customers.models.customer_schema_models import Referral, ReferralPointEvent
        self.assertEqual(Referral.__table__.schema, "customer")
        self.assertEqual(ReferralPointEvent.__table__.schema, "customer")


class TestPortsCompliance(unittest.TestCase):
    """NS8/Law 3: cross-domain reads route through ports."""

    def _src(self, modname):
        import importlib.util
        spec = importlib.util.find_spec(modname)
        self.assertIsNotNone(spec, f"module {modname} not found")
        with open(spec.origin, encoding="utf-8") as f:
            return f.read()

    def test_cart_reads_from_orders_ports(self):
        src = self._src("domains.customers.services.cart_service")
        self.assertIn("from domains.orders.ports import get_active_product_by_id", src)
        self.assertIn("from domains.orders.ports import load_cart_items", src)
        self.assertIn("from domains.logistics.ports import quote_shipping_for_destination", src)

    def test_cart_writes_from_orders_ports(self):
        src = self._src("domains.customers.services.cart_service")
        self.assertIn("from domains.orders.ports import create_cart_item", src)
        self.assertIn("from domains.orders.ports import delete_cart_items_by_user", src)
        self.assertIn("from domains.orders.ports import write_update_cart_item", src)

    def test_no_direct_cart_service_imports(self):
        src = self._src("domains.customers.services.cart_service")
        self.assertNotIn("from domains.orders.services.cart_write_service import", src)

    def test_wishlist_uses_catalog_ports(self):
        src = self._src("domains.customers.services.wishlist_service")
        self.assertNotIn("catalog.models", src)
        self.assertIn("catalog.ports", src)

    def test_health_uses_ports(self):
        src = self._src("domains.customers.services.customer_health_engine")
        self.assertNotIn("accounts.models.user", src)
        self.assertNotIn("orders.models.orders", src)
        self.assertIn("accounts.ports", src)
        self.assertIn("orders.ports", src)

    def test_referrals_uses_customers_ports(self):
        src = self._src("domains.customers.services.referrals_service")
        self.assertIn("customers.ports", src)
        self.assertNotIn("accounts.ports import Referral", src)

    def test_reviews_no_dead_imports(self):
        src = self._src("domains.customers.services.reviews_service")
        self.assertNotIn("orders.models.orders", src)

    def test_customers_ports_cart_from_accounts_ports(self):
        src = self._src("domains.customers.ports")
        self.assertIn("from domains.accounts.ports import Cart", src)
        self.assertNotIn("from domains.accounts.models.core import Cart", src)


class TestEventWiring(unittest.TestCase):
    """D8: subscribers registered at package import."""

    def test_no_dead_event(self):
        from domains.customers import events
        self.assertFalse(hasattr(events, "EVENT_CUSTOMER_UPDATED"))
        self.assertTrue(hasattr(events, "EVENT_CUSTOMER_CREATED"))

    def test_subscribers_callable(self):
        from domains.customers.subscribers import register_customers_subscribers, handle_customer_created
        self.assertTrue(callable(register_customers_subscribers))
        self.assertTrue(callable(handle_customer_created))


class TestNoDeadFiles(unittest.TestCase):
    """Anti-drift: required files present, services non-trivial."""

    def test_required_files(self):
        base = os.path.join(os.path.dirname(__file__), "..", "backend", "domains", "customers")
        for f in ["events.py", "subscribers.py", "features.py", "ports.py"]:
            self.assertTrue(os.path.exists(os.path.join(base, f)), f"missing {f}")

    def test_services_non_trivial(self):
        svc = os.path.join(os.path.dirname(__file__), "..", "backend", "domains", "customers", "services")
        for name in os.listdir(svc):
            if not name.endswith(".py") or name == "__init__.py":
                continue
            with open(os.path.join(svc, name)) as f:
                lines = [ln for ln in f if ln.strip() and not ln.strip().startswith("#")]
            self.assertGreater(len(lines), 5, f"{name} hollow")


if __name__ == "__main__":
    unittest.main(verbosity=2)
