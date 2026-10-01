import sys
import os

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend"))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from domains.catalog.models.commission import (
    CommissionGroup,
    CommissionProfile,
    CommissionRule,
    CommissionTransaction,
)


def test_commission_group_is_deleted_indexed():
    assert CommissionGroup.__table__.c.is_deleted.index is True


def test_commission_profile_is_deleted_indexed():
    assert CommissionProfile.__table__.c.is_deleted.index is True


def test_commission_rule_is_deleted_indexed():
    assert CommissionRule.__table__.c.is_deleted.index is True


def test_commission_transaction_is_deleted_indexed():
    assert CommissionTransaction.__table__.c.is_deleted.index is True
