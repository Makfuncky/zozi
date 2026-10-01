"""Phase 2H — Fix 4: mixin reuse test.

Asserts that the refactored ``WishlistItem`` model uses the canonical
AuditMixin / SoftDeleteMixin / TenantMixin / VersionMixin from
``infrastructure.database.mixins``.

This is a single-model proof — the full migration of all 658 models to
mixins is tracked separately. The purpose of this test is to lock the
pattern in: any future model that opts into the mixins should be tested
the same way.

Implementation note: the tests inspect ``Base.metadata.tables`` (the
authoritative SQLAlchemy source) rather than the class's ``__table__``
attribute. Several other test modules force a re-import of
``domains.catalog.models.products`` (via the global ``del sys.modules``
performed by ``test_architecture_gates::TestAppBoot``), which leaves
``WishlistItem`` as a stale partial class with no ``__table__`` even
though the table IS still registered in ``Base.metadata``. Reading from
``Base.metadata`` is therefore the only test-isolation-safe access path.
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def _wishlist_table():
    """Return the live ``catalog.wishlist_items`` Table from Base.metadata.

    Other tests in the same suite (1) trigger ``_remove_broken_fk_tables``
    (in ``tests/conftest.py``) which deletes tables with dangling FKs,
    (2) re-import ``main`` (in ``test_architecture_gates::TestAppBoot``)
    which leaves ``WishlistItem`` as a stale partial class. Either
    failure mode strips one of the two access paths; this helper tries
    them in the order most likely to succeed for a given fixture order.
    """
    import importlib

    cls = importlib.import_module("domains.catalog.models.products").WishlistItem
    table = getattr(cls, "__table__", None)
    if table is not None:
        return table

    from infrastructure.database.base import Base

    table = Base.metadata.tables.get("catalog.wishlist_items")
    if table is not None:
        return table

    pytest.skip(
        "WishlistItem.__table__ and catalog.wishlist_items both unavailable; "
        "the test order strips both access paths. See audit Phase 2.1 R7."
    )


def _wishlist_mro():
    """Return the WishlistItem class MRO; force a fresh import if needed."""
    import importlib

    mod = importlib.import_module("domains.catalog.models.products")
    return mod.WishlistItem.__mro__


def test_wishlist_item_uses_canonical_mixins() -> None:
    from infrastructure.database.mixins import (
        AuditMixin,
        SoftDeleteMixin,
        TenantMixin,
        VersionMixin,
    )

    mro = _wishlist_mro()
    for mixin in (AuditMixin, SoftDeleteMixin, TenantMixin, VersionMixin):
        assert mixin in mro, (
            f"WishlistItem must inherit {mixin.__name__}; got MRO={[c.__name__ for c in mro]}"
        )


def test_wishlist_item_columns_present() -> None:
    table = _wishlist_table()
    column_names = {c.name for c in table.columns}
    # AuditMixin
    assert "created_at" in column_names
    assert "updated_at" in column_names
    assert "created_by_id" in column_names
    assert "updated_by_id" in column_names
    # SoftDeleteMixin
    assert "is_deleted" in column_names
    assert "deleted_at" in column_names
    assert "deleted_by_id" in column_names
    # TenantMixin
    assert "country_code" in column_names
    # VersionMixin
    assert "version" in column_names
    # Original
    assert "user_id" in column_names
    assert "product_id" in column_names


def test_wishlist_item_schema() -> None:
    table = _wishlist_table()
    assert table.schema == "catalog"


def test_wishlist_item_soft_delete_helper() -> None:
    """Verifies ``SoftDeleteMixin`` is a real class with the right columns.

    Avoids constructing instances because the mixin is abstract-declarative;
    instance attribute access returns the Column descriptor until the model
    is mapped. The presence of the expected columns and the callable
    ``soft_delete`` / ``restore`` is the contract we care about.
    """
    from infrastructure.database.mixins import SoftDeleteMixin

    expected = {"is_deleted", "deleted_at", "deleted_by_id"}
    found = {c.name for c in SoftDeleteMixin.__table__.columns} if hasattr(SoftDeleteMixin, "__table__") else set()
    # The mixin is __abstract__ = True so __table__ won't exist on it; the
    # proof is that the columns appear on the *consumer* class.
    table = _wishlist_table()
    consumer_cols = {c.name for c in table.columns}
    assert expected.issubset(consumer_cols), (
        f"SoftDeleteMixin columns {expected} must be present on WishlistItem; got {consumer_cols}"
    )
    # Helper methods exist
    assert callable(getattr(SoftDeleteMixin, "soft_delete", None))
    assert callable(getattr(SoftDeleteMixin, "restore", None))
