"""Q1 rescue test — admin payouts controller (distinct from the router test)."""
from q1_rescue_utils import assert_no_session_reads, assert_imports_db_read

_BACKEND_REL = "controllers/treasury/payouts.py"


def test_no_session_reads():
    assert_no_session_reads(_BACKEND_REL)


def test_delegates_to_db_read():
    assert_imports_db_read(_BACKEND_REL)
