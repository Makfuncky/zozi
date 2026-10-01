"""Regression tests for the auth router refactor (security domain, violations W1/LC1/CG1).

These verify that ``routers/auth.py`` no longer touches models or the session
directly: all DB work is delegated to ``controllers/auth_controller`` ->
``services/auth_write_service``.
"""
from __future__ import annotations

import ast
import os

import pytest

BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
AUTH_ROUTER = os.path.join(BACKEND, "routers", "auth.py")


@pytest.fixture(scope="module")
def auth_tree():
    with open(AUTH_ROUTER, "r", encoding="utf-8") as fh:
        src = fh.read()
    return src, ast.parse(src)


def test_router_does_not_import_models(auth_tree):
    src, _ = auth_tree
    assert "from data.models import" not in src
    assert "import models" not in src


def test_router_has_no_forbidden_session_writes(auth_tree):
    src, tree = auth_tree
    session_names = {"db", "session"}
    write_verbs = {"add", "commit", "delete", "merge", "execute"}
    read_verbs = {"query"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            receiver = node.func.value
            if isinstance(receiver, ast.Name) and receiver.id in session_names:
                verb = node.func.attr
                assert verb not in write_verbs, f"router performs session.{verb}() at line {node.lineno}"
                assert verb not in read_verbs, f"router performs session.{verb}() at line {node.lineno}"


def test_router_has_no_db_query_pattern(auth_tree):
    src, _ = auth_tree
    assert "db.query" not in src
    assert "session.query" not in src


def test_router_delegates_to_controller(auth_tree):
    src, _ = auth_tree
    # The router must route DB work through the controller delegation helpers.
    for helper in (
        "auth_find_user",
        "auth_get_user_by_id",
        "auth_create_registration_user",
        "auth_persist_last_login",
        "auth_record_login_history",
    ):
        assert helper in src, f"router does not delegate via {helper}"


def test_controller_exposes_delegation_helpers():
    import controllers.auth_controller as ctrl

    for helper in (
        "auth_find_user",
        "auth_get_user_by_id",
        "auth_create_registration_user",
        "auth_persist_last_login",
        "auth_record_login_history",
    ):
        assert hasattr(ctrl, helper), f"controller missing {helper}"


def test_service_exposes_write_helpers():
    import services.auth_write_service as svc

    for helper in (
        "find_user_by_identifier",
        "get_user_by_id",
        "create_registration_user",
        "record_login_history_commit",
    ):
        assert hasattr(svc, helper), f"service missing {helper}"


def test_app_boots_with_auth_router():
    import main  # noqa: F401  (import side-effect verifies router wiring)

    assert main.app is not None
