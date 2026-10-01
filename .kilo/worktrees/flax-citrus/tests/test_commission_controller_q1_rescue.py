"""Q1 rescue test — commission_controller.

Verifies the controller no longer calls ``db.query()`` / ``db.execute()`` /
``db.get()`` directly and delegates every read to ``services.db_read``.
"""
from q1_rescue_utils import assert_no_session_reads, assert_imports_db_read


def test_no_session_reads():
    assert_no_session_reads("controllers/commission_controller.py")


def test_delegates_to_db_read():
    assert_imports_db_read("controllers/commission_controller.py")
