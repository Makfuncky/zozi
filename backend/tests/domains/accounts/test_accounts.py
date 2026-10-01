"""Tests for accounts domain: GDPR service and user account operations."""
from __future__ import annotations

import pytest


@pytest.mark.integration
def test_gdpr_export_returns_data_structure(db_session):
    """GDPR data export should return a dict with user data fields."""
    pytest.skip("Implement GDPR export test with seeded user")


@pytest.mark.integration
def test_gdpr_deletion_cascades(db_session):
    """GDPR deletion should remove or anonymize all user data."""
    pytest.skip("Implement GDPR deletion test with seeded user")


@pytest.mark.integration
def test_account_deactivation_preserves_audit_trail(db_session):
    """Deactivating an account must retain audit records."""
    pytest.skip("Implement account deactivation audit test")
