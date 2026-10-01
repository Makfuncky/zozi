"""Verification for the supplier/onboarding DBA06 rescue.

The tables in this file live in three different schemas (``hr``, ``security``,
``media``).  Any FK whose target schema differs from the declaring table's schema
is a cross-schema (DBA06) violation and must be removed; same-schema FKs (e.g.
``onboarding_steps.pipeline_id -> hr.onboarding_pipelines``) are kept.  Relationships
use explicit ``primaryjoin``.
"""
from __future__ import annotations

import models.supplier.onboarding as onboarding_mod
from db.base import Base
from sqlalchemy.orm import configure_mappers

_ONBOARDING_TABLES = {
    "onboarding_pipelines", "onboarding_steps", "document_verifications",
    "ocr_results", "kyc_verifications",
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


def test_onboarding_models_have_no_cross_schema_fk():
    for name in _ONBOARDING_TABLES:
        fks = _cross_schema_fks(_table(name))
        assert fks == [], f"{name}: cross-schema FKs {fks}"


def test_relationships_configure():
    configure_mappers()
    assert onboarding_mod.OnboardingPipeline.user is not None
    assert onboarding_mod.DocumentVerification.pipeline is not None
    assert onboarding_mod.DocumentVerification.verifier is not None
    assert onboarding_mod.OCRResult.document_verification is not None
    assert onboarding_mod.KYCVerification.user is not None
    assert onboarding_mod.KYCVerification.reviewer is not None
