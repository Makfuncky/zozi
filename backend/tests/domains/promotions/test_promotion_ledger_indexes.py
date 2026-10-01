"""Regression tests for promotion_ledger index fix (DB-018).

Verifies:
  * promotion_id column carries an index (Law 45 — no N+1, proper indexes).
  * order_id column carries an index.
"""
from __future__ import annotations


class TestPromotionLedgerIndexes:
    """promotion_ledger_entries must have indexes on promotion_id and order_id."""

    def test_promotion_id_has_index(self, db_session):
        from domains.promotions.models.promotion_ledger import PromotionLedgerEntry

        idx_names = [idx.name for idx in PromotionLedgerEntry.__table__.indexes]
        assert "ix_promotions_promotion_ledger_entries_promotion_id" in idx_names, (
            f"promotion_id index missing from PromotionLedgerEntry. "
            f"Found indexes: {idx_names}"
        )

    def test_order_id_has_index(self, db_session):
        from domains.promotions.models.promotion_ledger import PromotionLedgerEntry

        idx_names = [idx.name for idx in PromotionLedgerEntry.__table__.indexes]
        assert "ix_promotions_promotion_ledger_entries_order_id" in idx_names, (
            f"order_id index missing from PromotionLedgerEntry. "
            f"Found indexes: {idx_names}"
        )

    def test_promotion_id_column_is_indexed(self, db_session):
        from domains.promotions.models.promotion_ledger import PromotionLedgerEntry

        col = PromotionLedgerEntry.__table__.c.promotion_id
        assert any(
            col in idx.expressions for idx in PromotionLedgerEntry.__table__.indexes
        ), "promotion_id column is not covered by any index"

    def test_order_id_column_is_indexed(self, db_session):
        from domains.promotions.models.promotion_ledger import PromotionLedgerEntry

        col = PromotionLedgerEntry.__table__.c.order_id
        assert any(
            col in idx.expressions for idx in PromotionLedgerEntry.__table__.indexes
        ), "order_id column is not covered by any index"
