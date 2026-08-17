"""SEC105 rescue test — verifies the hardcoded demo credential was removed.

The audit flagged ``services/misc_write_service.py::reset_demo_data`` for embedding
a literal password (``Demo@12345``) in source. The fix:
  * seeds demo users from env-var driven ``db.seed._seed_password`` (SEED_*_PASSWORD),
  * refuses to run at all when APP_ENV == "production".

This test locks both behaviours so the violation cannot regress.
"""
import pathlib
import re

import pytest

from domains.media.services.misc_write_service import reset_demo_data
from infrastructure.utils.config import settings

_MISC_WRITE_SERVICE = (
    pathlib.Path(__file__).resolve().parents[1] / "services" / "misc_write_service.py"
)

# Mirrors the audit's SEC105 literal detector (ENH_SECRET_ASSIGN_RE).
_HARDCODED_CREDENTIAL_RE = re.compile(
    r"(?i)\b(api[_-]?key|apikey|secret|secret[_-]?key|token|auth[_-]?token|"
    r"access[_-]?token|password|passwd|pwd)\b\s*[:=]\s*['\"][^'\"]{12,}['\"]"
)


def test_no_hardcoded_credential_literal_in_source():
    text = _MISC_WRITE_SERVICE.read_text(encoding="utf-8")
    assert "Demo@12345" not in text, "literal demo password still present in source"
    match = _HARDCODED_CREDENTIAL_RE.search(text)
    assert match is None, f"hardcoded credential literal still present: {match.group(0)!r}"


def test_reset_demo_data_refuses_production(db_session):
    original = settings.app_env
    settings.app_env = "production"
    try:
        with pytest.raises(RuntimeError):
            reset_demo_data(db_session)
    finally:
        settings.app_env = original


def test_reset_demo_data_seeds_via_env_password(db_session, monkeypatch):
    monkeypatch.setenv("SEED_ADMIN_PASSWORD", "EnvSourcedP@ssw0rd!")
    monkeypatch.setenv("SEED_SUPPLIER_PASSWORD", "EnvSourcedP@ssw0rd!")
    monkeypatch.setenv("SEED_CUSTOMER_PASSWORD", "EnvSourcedP@ssw0rd!")
    result = reset_demo_data(db_session)
    assert result["reseeded"] == 3

