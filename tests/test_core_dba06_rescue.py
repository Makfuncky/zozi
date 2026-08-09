"""Verification for the core/user DBA06 rescue.

The ``Referral`` and ``ReferralPointEvent`` models live in the ``customer`` schema,
so their ``ForeignKey("core.users.id")`` declarations are cross-schema (DBA06) and
must be removed.  The remaining core/user.py tables live in the ``core`` schema and
keep their same-schema FKs (not DBA06).  Relationships use explicit ``primaryjoin``.
"""
from __future__ import annotations

import models.core.user as user_mod
from db.base import Base
from sqlalchemy.orm import configure_mappers

# Any FK whose target lives in one of these schemas is cross-schema (DBA06).
_CROSS_SCHEMA_PREFIXES = (
    "core.", "finance.", "logistics.", "country.", "hr.", "security.",
    "treasury.", "supplier.", "customer.", "audit.", "communication.",
    "ai.", "analytics.", "configuration.", "trading.",
)


def _table(name: str):
    for t in Base.metadata.tables.values():
        if t.name == name:
            return t
    raise KeyError(name)


def _cross_schema_fks(table):
    bad = []
    for fkc in table.foreign_key_constraints:
        for fk in fkc.elements:
            tgt = fk.target_fullname  # e.g. "core.users.id"
            if any(tgt.startswith(p) for p in _CROSS_SCHEMA_PREFIXES):
                bad.append(tgt)
    return bad


def test_referral_has_no_cross_schema_fk():
    assert _cross_schema_fks(_table("referrals")) == []


def test_referral_point_event_has_no_cross_schema_fk():
    assert _cross_schema_fks(_table("referral_point_events")) == []


def test_relationships_configure():
    configure_mappers()
    assert user_mod.Referral.referrer is not None
    assert user_mod.Referral.referred is not None
    assert user_mod.ReferralPointEvent.user is not None
    assert user_mod.ReferralPointEvent.referred_user is not None
