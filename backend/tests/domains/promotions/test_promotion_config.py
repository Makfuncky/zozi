"""Regression tests for PromotionEngineConfig duplicate-column fix (DB-014).

Verifies:
  * PromotionEngineConfig declares exactly one `country_code` Column.
  * No duplicate column names exist on the model.
  * The `country_code` Column retains its expected ForeignKey and index.
"""
from __future__ import annotations

import pytest

from domains.promotions.models.promotion_config import PromotionEngineConfig


class TestPromotionEngineConfigNoDuplicateCountryCode:
    """DB-014 regression: exactly one country_code Column, no duplicates."""

    def test_country_code_column_count_is_one(self):
        """PromotionEngineConfig must declare country_code exactly once."""
        col_names = [c.name for c in PromotionEngineConfig.__table__.columns]
        assert col_names.count("country_code") == 1, (
            f"PromotionEngineConfig declares country_code {col_names.count('country_code')} times; "
            "expected exactly 1"
        )

    def test_no_duplicate_column_names(self):
        """No column name may appear more than once on the model."""
        col_names = [c.name for c in PromotionEngineConfig.__table__.columns]
        duplicates = [name for name in set(col_names) if col_names.count(name) > 1]
        assert not duplicates, f"Duplicate columns found: {duplicates}"

    def test_country_code_has_expected_foreign_key(self):
        """The single country_code Column must point to country.country_configs.code."""
        col = PromotionEngineConfig.__table__.c.country_code
        fk_targets = [fk.column.name for fk in col.foreign_keys]
        assert "code" in fk_targets, (
            f"country_code ForeignKey targets {fk_targets}, expected 'code'"
        )

    def test_country_code_is_indexed(self):
        """country_code must have an index for RLS filtering."""
        indexes = [idx.name for idx in PromotionEngineConfig.__table__.indexes]
        assert any("country_code" in idx for idx in indexes), (
            "country_code must be indexed"
        )
