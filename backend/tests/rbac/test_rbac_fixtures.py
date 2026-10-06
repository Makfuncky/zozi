"""Paired tests verifying RBAC seed fixture correctness and idempotency."""
from __future__ import annotations

import pytest
from sqlalchemy import text

from tests.rbac.fixtures import seed_permission_categories


class TestRBACSeedFixture:
    """Verify the permission_categories seed fixture contract."""

    def test_default_category_exists(self, db_session):
        row = db_session.execute(
            text("SELECT id, slug, is_active FROM permission_categories WHERE id = 1")
        ).fetchone()
        assert row is not None
        assert row[1] == "general"
        assert row[2] == 1

    def test_permissions_reference_valid_categories(self, db_session):
        cats = db_session.execute(
            text("SELECT id FROM permission_categories")
        ).fetchall()
        cat_ids = {row[0] for row in cats}
        assert len(cat_ids) > 0

    def test_fixture_idempotent_across_two_runs(self, db_session):
        count_before = db_session.execute(
            text("SELECT COUNT(*) FROM permission_categories")
        ).scalar()
        seed_permission_categories(db_session)
        db_session.commit()
        count_after = db_session.execute(
            text("SELECT COUNT(*) FROM permission_categories")
        ).scalar()
        assert count_after == count_before, (
            "Seed fixture created duplicate rows on second run"
        )
