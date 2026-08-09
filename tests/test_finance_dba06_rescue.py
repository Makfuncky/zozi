"""Verification for the finance-module DBA06 rescue.

Any ``ForeignKey`` whose target table lives in a different schema than the
declaring table is a cross-schema (DBA06) violation and must be removed.  The
tests assert that every finance model keeps only same-schema FKs (e.g.
``logistics_partner_payouts.partner_id -> logistics.logistics_partners``) while
all cross-schema FKs (to ``core.users``, ``country.country_configs``, etc.) are
gone, and that the ORM registry configures (relationships use ``primaryjoin``).
"""
from __future__ import annotations

import models.finance.commission as commission_mod
import models.finance.payments as payments_mod
from db.base import Base
from sqlalchemy.orm import configure_mappers

_FINANCE_TABLES = {
    "commission_agreements", "product_commission_overrides", "commission_ledger_entries",
    "commission_category_rates", "commission_rules",
    "payments", "payment_reconciliation_runs", "coupons", "banners",
    "payment_gateway_connections", "payouts", "logistics_partner_payouts",
    "erp_transactions", "payroll_records",
}


def _table(name: str):
    for t in Base.metadata.tables.values():
        if t.name == name:
            return t
    raise KeyError(name)


def _cross_schema_fks(table):
    bad = []
    for fkc in table.foreign_key_constraints:
        for fk in fkc.elements:
            tgt_schema = fk.column.table.schema
            if tgt_schema and tgt_schema != table.schema:
                bad.append(f"{tgt_schema}.{fk.column.table.name}.{fk.column.name}")
    return bad


def test_finance_models_have_no_cross_schema_fk():
    for name in _FINANCE_TABLES:
        fks = _cross_schema_fks(_table(name))
        assert fks == [], f"{name}: cross-schema FKs {fks}"


def test_relationships_configure():
    configure_mappers()
    assert commission_mod.CommissionCategoryRate.country is not None
    assert payments_mod.Payment.country is not None
    assert payments_mod.Coupon.country is not None
    assert payments_mod.Banner.country is not None
    assert payments_mod.Payout.supplier is not None
    assert payments_mod.Payout.country is not None
    assert payments_mod.LogisticsPartnerPayout.partner is not None
    assert payments_mod.LogisticsPartnerPayout.country is not None
