from q1_rescue_utils import assert_no_session_reads, assert_imports_db_read


def test_no_session_reads():
    assert_no_session_reads("controllers/orders_controller.py")


def test_delegates_to_db_read():
    assert_imports_db_read("controllers/orders_controller.py")
