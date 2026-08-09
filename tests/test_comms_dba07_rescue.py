"""DBA07 rescue for the comms marketing models.

Verifies that ``PointsTransaction.user_id`` and ``UserPoints.user_id`` no
longer CASCADE into the protected ``security.users`` table.  A CASCADE into a
finance/audit/security/identity/orders/hr table can mass-delete user data when
a parent row is removed, so the contract requires ``RESTRICT``.

Canonical module: backend/models/comms/marketing.py
"""
from __future__ import annotations

import importlib

import pytest


def _import_marketing():
    # Importing the submodule pulls in the ``models`` package (which defines
    # Base) plus the comms models; this mirrors how the ORM is loaded in the
    # app and would surface any import-time breakage introduced by the fix.
    return importlib.import_module("models.comms.marketing")


def _fk_on_column(table, column_name):
    col = table.c[column_name]
    fks = list(col.foreign_keys)
    assert fks, f"{table.name}.{column_name} must declare a ForeignKey"
    return fks[0]


@pytest.mark.parametrize(
    "model_name,column_name",
    [
        ("PointsTransaction", "user_id"),
        ("UserPoints", "user_id"),
    ],
)
def test_user_fk_is_restrict_not_cascade(model_name, column_name):
    mod = _import_marketing()
    model = getattr(mod, model_name)
    fk = _fk_on_column(model.__table__, column_name)

    assert fk.ondelete == "RESTRICT", (
        f"{model_name}.{column_name} must use ondelete='RESTRICT' into the "
        f"protected users table, got ondelete={fk.ondelete!r}"
    )
    assert str(fk.target_fullname) == "security.users.id", (
        f"{model_name}.{column_name} must reference security.users.id, "
        f"got {fk.target_fullname!r}"
    )


def test_no_dangerous_cascade_into_protected_tables():
    mod = _import_marketing()
    protected = {"security", "finance", "audit", "identity", "orders", "hr"}
    violations = []
    for attr in dir(mod):
        cls = getattr(mod, attr)
        table = getattr(cls, "__table__", None)
        if table is None:
            continue
        for col in table.columns:
            for fk in col.foreign_keys:
                schema = (fk.target_fullname or "").split(".")[0]
                if schema in protected and (fk.ondelete or "").upper() == "CASCADE":
                    violations.append(f"{table.name}.{col.name} -> {fk.target_fullname}")
    assert not violations, f"dangerous CASCADE into protected tables: {violations}"


def test_marketing_models_import_cleanly():
    mod = _import_marketing()
    for name in ("PointsTransaction", "UserPoints", "FlashSale", "EmailCampaign"):
        assert hasattr(mod, name), f"marketing module missing {name}"
