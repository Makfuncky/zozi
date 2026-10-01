import pytest

from sqlalchemy import inspect

from domains.comms.models.incident import IncidentWarRoom


def test_incident_has_audit_columns():
    cols = {c.name for c in inspect(IncidentWarRoom).columns}
    assert "created_at" in cols
    assert "updated_at" in cols
    assert "country_code" in cols
    assert "is_deleted" in cols
