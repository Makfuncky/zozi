"""Commission models — is_deleted index verification (DB-017, Law 53).

Verifies that every commission model's ``is_deleted`` column carries
``index=True`` so soft-delete filters are performant at scale.
"""
from __future__ import annotations

import pytest

from domains.catalog.models.commission import (
    CommissionGroup,
    CommissionProfile,
    CommissionRule,
    CommissionTransaction,
)


_MODELS = (
    CommissionGroup,
    CommissionProfile,
    CommissionRule,
    CommissionTransaction,
)


@pytest.mark.parametrize("model", _MODELS, ids=[m.__name__ for m in _MODELS])
def test_is_deleted_column_is_indexed(model):
    """Each commission model must index is_deleted for soft-delete filter performance."""
    col = model.__table__.columns.get("is_deleted")
    assert col is not None, f"{model.__name__} missing is_deleted column"
    assert col.index is True, (
        f"{model.__name__}.is_deleted must have index=True (DB-017 / Law 53)"
    )
