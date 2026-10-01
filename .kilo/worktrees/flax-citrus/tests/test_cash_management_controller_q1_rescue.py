"""Q1 rescue test — cash_management_controller.

Controllers must never reach into the ORM session via ``db.query()`` /
``db.execute()`` / ``db.get()``. Every read is delegated to the shared
``services.db_read`` layer.
"""
from q1_rescue_utils import assert_no_session_reads, assert_imports_db_read


def test_no_session_reads():
    assert_no_session_reads("controllers/cash_management_controller.py")


def test_delegates_to_db_read():
    assert_imports_db_read("controllers/cash_management_controller.py")
