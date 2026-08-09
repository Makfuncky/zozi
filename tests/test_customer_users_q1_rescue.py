"""Q1 rescue test — admin users controller (controllers/customer/users.py).

Controllers must never reach into the ORM session via ``db.query()`` /
``db.execute()`` / ``db.get()``. Every read is delegated to the shared
``services.db_read`` layer.
"""
from q1_rescue_utils import assert_no_session_reads, assert_imports_db_read


def test_no_session_reads():
    assert_no_session_reads("controllers/customer/users.py")


def test_delegates_to_db_read():
    assert_imports_db_read("controllers/customer/users.py")
