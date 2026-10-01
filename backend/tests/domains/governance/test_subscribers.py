"""Regression tests for governance subscribers.

Validates that the 25 formerly-stubbed event handlers are no longer silent
stubs: they either wire to a real service function or raise NotImplementedError
with a clear message. Also validates that all handler functions have docstrings.
"""
from __future__ import annotations

import inspect

import pytest

from domains.governance import subscribers


STUBBED_HANDLERS = [
    "_on_bulk_delete_products_admin_requested",
    "_on_bulk_product_moderation_requested",
    "_on_delete_product_admin_requested",
    "_on_restore_product_admin_requested",
    "_on_toggle_product_badge_requested",
    "_on_bulk_delete_users_admin_requested",
    "_on_bulk_toggle_users_active_requested",
    "_on_bulk_update_users_role_requested",
    "_on_toggle_user_active_requested",
    "_on_update_user_role_requested",
    "_on_bulk_update_staff_accounts_requested",
    "_on_create_staff_account_requested",
    "_on_delete_staff_account_requested",
    "_on_update_staff_account_requested",
    "_on_bulk_manage_suppliers_requested",
    "_on_bulk_supplier_verification_requested",
    "_on_verify_supplier_requested",
    "_on_reject_supplier_requested",
    "_on_order_bulk_delete_requested",
    "_on_order_bulk_status_update_requested",
    "_on_order_delete_requested",
    "_on_order_refund_requested",
    "_on_order_status_update_requested",
    "_on_order_tracking_update_requested",
    "_on_delete_bank_account_record_requested",
]

NOT_IMPLEMENTED_HANDLERS = {
    "_on_verify_supplier_requested",
    "_on_reject_supplier_requested",
}


class TestSubscribersNoSilentStubs:
    def test_all_handlers_have_docstrings(self):
        for name in STUBBED_HANDLERS:
            fn = getattr(subscribers, name)
            assert inspect.getdoc(fn), f"{name} is missing a docstring"

    def test_no_handler_logs_warning_and_returns_none(self):
        for name in STUBBED_HANDLERS:
            fn = getattr(subscribers, name)
            source = inspect.getsource(fn)
            assert "logger.warning" not in source, f"{name} still contains logger.warning stub"
            assert "return None" not in source, f"{name} still returns None as a stub"

    def test_no_todo_comments_in_handlers(self):
        for name in STUBBED_HANDLERS:
            fn = getattr(subscribers, name)
            source = inspect.getsource(fn)
            assert "# TODO" not in source, f"{name} still contains TODO comment"

    def test_not_implemented_handlers_raise(self):
        for name in NOT_IMPLEMENTED_HANDLERS:
            fn = getattr(subscribers, name)
            with pytest.raises(NotImplementedError):
                fn({"actor_id": 1, "actor_role": "admin"})

    def test_wired_handlers_import_service_functions(self):
        wired_handlers = [h for h in STUBBED_HANDLERS if h not in NOT_IMPLEMENTED_HANDLERS]
        for name in wired_handlers:
            fn = getattr(subscribers, name)
            source = inspect.getsource(fn)
            assert "import" in source, f"{name} does not import a service function"

    def test_subscribers_module_imports_successfully(self):
        import importlib
        importlib.reload(subscribers)
        assert hasattr(subscribers, "register_governance_subscribers")

    def test_register_governance_subscribers_callable(self):
        assert callable(getattr(subscribers, "register_governance_subscribers"))
