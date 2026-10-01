"""Q1 rescue test — admin order management controller.

NOTE: the historical path ``controllers/admin/orders.py`` no longer exists in
the working tree; the admin controller package was reorganised and this module
now lives at ``controllers/orders/orders.py`` (still docstring'd "Admin order
management controller"). SYSTEM_AUDIT_REPORT.md tracks the Q1 finding under the
new path, so that is what this test guards.
"""
from q1_rescue_utils import assert_no_session_reads, assert_imports_db_read


def test_no_session_reads():
    assert_no_session_reads("controllers/orders/orders.py")


def test_delegates_to_db_read():
    assert_imports_db_read("controllers/orders/orders.py")
