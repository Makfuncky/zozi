"""Q1 rescue test for ``backend/controllers/returns_controller.py``.

Q1 forbids controllers from calling ``db.query()`` / ``db.execute()`` /
``db.get()`` directly; reads must delegate to ``services.db_read``.
"""
from q1_rescue_utils import assert_no_session_reads, assert_imports_db_read


def test_no_session_reads():
    assert_no_session_reads("controllers/returns_controller.py")


def test_delegates_to_db_read():
    assert_imports_db_read("controllers/returns_controller.py")
