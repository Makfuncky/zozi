"""Q1 rescue test for the logistics partner controller.

Verifies that ``controllers/logistics_partner_controller.py`` no longer reads
directly from the DB session (``db.query`` / ``db.execute`` / ``db.get``) and
instead delegates to ``services.db_read``. No database or app boot is required.
"""
from __future__ import annotations

from q1_rescue_utils import (
    assert_imports_db_read,
    assert_no_session_reads,
)

CONTROLLER_REL = "controllers/logistics_partner_controller.py"


def test_controller_has_no_session_reads() -> None:
    assert_no_session_reads(CONTROLLER_REL)


def test_controller_imports_db_read() -> None:
    assert_imports_db_read(CONTROLLER_REL)
