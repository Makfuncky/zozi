"""Regression test: FILE-129 — admin accounts pending-bank-accounts uses keyset pagination.

The adoption-layer ``list_pending_bank_accounts`` in the accounts domain must
never issue SQL ``OFFSET`` and must delegate to ``keyset_paginate`` (B6/R6).
"""
from __future__ import annotations

import importlib
import inspect
import pathlib
import sys

import pytest

# Load service module by bypassing the broken __init__.py star import
_svc_file = pathlib.Path(__file__).resolve().parents[3] / (
    "domains/accounts/services/users/user_management_service.py"
)
_svc_spec = importlib.util.spec_from_file_location(
    "accounts_user_management_service", _svc_file
)
_accounts_svc = importlib.util.module_from_spec(_svc_spec)
_svc_spec.loader.exec_module(_accounts_svc)
sys.modules["accounts_user_management_service"] = _accounts_svc

_accounts_router = importlib.import_module("modules.admin.routers.accounts")


def test_accounts_list_pending_bank_accounts_is_keyset_not_offset():
    """``list_pending_bank_accounts`` must use keyset pagination, not OFFSET."""
    src = inspect.getsource(_accounts_svc.list_pending_bank_accounts)
    assert ".offset(" not in src, (
        "list_pending_bank_accounts must use keyset pagination, not OFFSET"
    )
    assert "keyset_paginate" in src, (
        "list_pending_bank_accounts must delegate to keyset_paginate"
    )


def test_accounts_router_no_offset_pagination_pattern():
    """The router must not compute offset from page/offset arithmetic."""
    src = inspect.getsource(_accounts_router.list_pending_bank_accounts_route)
    assert "offset=(page - 1) * page_size" not in src, (
        "Router must not use offset=(page - 1) * page_size"
    )
    assert "cursor=" in src, (
        "Router must pass cursor parameter for keyset pagination"
    )


def test_accounts_router_require_feature_on_every_endpoint():
    """Every protected endpoint in the admin accounts router must use require_feature."""
    src = inspect.getsource(_accounts_router)
    endpoints = [
        line.strip()
        for line in src.splitlines()
        if line.strip().startswith("@router.")
    ]
    require_feature_count = src.count("require_feature(")
    assert require_feature_count >= len(endpoints), (
        f"Not every endpoint has require_feature: {require_feature_count} "
        f"gates for {len(endpoints)} endpoints"
    )
