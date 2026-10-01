from __future__ import annotations

import pytest
from sqlalchemy import Column, Integer

from backend.domains.customers.models.cross_country_session import CrossCountryCustomerSession


class TestCrossCountrySessionModel:
    def test_order_id_has_index(self):
        cols = {c.name: c for c in CrossCountryCustomerSession.__table__.columns}
        assert "order_id" in cols
        assert cols["order_id"].index is True

    def test_order_id_index_in_table_indexes(self):
        order_id_cols = [
            col for idx in CrossCountryCustomerSession.__table__.indexes
            for col in idx.columns
            if col.name == "order_id"
        ]
        assert len(order_id_cols) == 1

    def test_order_id_is_nullable(self):
        cols = {c.name: c for c in CrossCountryCustomerSession.__table__.columns}
        assert cols["order_id"].nullable is True
