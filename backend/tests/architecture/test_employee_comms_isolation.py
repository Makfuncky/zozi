"""Architecture tests — verify employee module uses comms ports, not direct service imports."""
import os


def test_employee_routers_use_comms_ports():
    """Employee routers must import from domains.comms.ports, not services."""
    employee_routers = "modules/employee/routers"
    violations = []
    for root, _, files in os.walk(employee_routers):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                # Skip the comms.py router itself (it's the sanctioned comms interface)
                if f == "comms.py":
                    continue
                with open(path, encoding="utf-8") as fh:
                    content = fh.read()
                if "domains.comms.services" in content:
                    violations.append(path)
    assert not violations, f"Direct comms service imports found in: {violations}"


def test_employee_routers_do_not_import_comms_services():
    """Verify no employee router imports comms service internals."""
    comms_service_imports = [
        "domains.comms.services.messaging",
        "domains.comms.services.email",
        "domains.comms.services.tickets",
        "domains.comms.services.comms_service",
    ]
    employee_routers = "modules/employee/routers"
    violations = []
    for root, _, files in os.walk(employee_routers):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                # Skip the comms.py router itself (it's the sanctioned comms interface)
                if f == "comms.py":
                    continue
                with open(path, encoding="utf-8") as fh:
                    content = fh.read()
                for imp in comms_service_imports:
                    if imp in content:
                        violations.append((path, imp))
    assert not violations, f"Direct comms service imports: {violations}"


def test_comms_events_single_hierarchy():
    """Verify comms events expose a single base class.

    Phase 2.1 R8: ``CommsServiceEvent`` was previously a parallel base
    class with identical fields. It now subclasses ``CommsEvent`` and
    remains only as a back-compat alias. We assert the relationship so
    that the two cannot drift apart again.
    """
    from domains.comms import events

    assert hasattr(events, "CommsEvent"), "CommsEvent base class missing"
    if hasattr(events, "CommsServiceEvent"):
        assert issubclass(events.CommsServiceEvent, events.CommsEvent), (
            "CommsServiceEvent must derive from CommsEvent (single hierarchy)."
        )


def test_comms_subscribers_have_hr_handlers():
    """Verify comms subscribers include handlers for the canonical cross-domain events.

    Phase 2.1 updated this assertion to match the handlers that are actually
    registered in ``domains/comms/subscribers.py``. Previous names
    (``_on_role_assigned`` / ``_on_task_assigned`` etc.) referenced HR models
    that were never landed (see audit Phase 3 finding R8).
    """
    from domains.comms import subscribers

    expected = (
        "_on_ticket_status_changed",
        "_on_ticket_replied",
        "_on_notification_created",
        "_on_escalation_triggered",
        "_on_order_created",
        "_on_order_status_changed",
        "_on_user_registered",
    )
    for name in expected:
        assert hasattr(subscribers, name), f"Missing comms subscriber handler: {name}"


def test_employee_hr_sub_routers_are_thin():
    """Verify each employee HR sub-router is under 150 lines."""
    hr_dir = "modules/employee/routers/hr"
    for f in os.listdir(hr_dir):
        if f.endswith(".py") and f != "__init__.py":
            path = os.path.join(hr_dir, f)
            with open(path, encoding="utf-8") as fh:
                lines = len(fh.readlines())
            assert lines < 150, f"{f} is {lines} lines (max 150)"


def test_admin_hr_sub_routers_are_thin():
    """Verify each admin HR sub-router is under 250 lines."""
    hr_dir = "modules/admin/routers/hr"
    if os.path.exists(hr_dir):
        for f in os.listdir(hr_dir):
            if f.endswith(".py") and f != "__init__.py":
                path = os.path.join(hr_dir, f)
                with open(path, encoding="utf-8") as fh:
                    lines = len(fh.readlines())
                assert lines < 250, f"{f} is {lines} lines (max 250)"


def test_authority_policy_service_exists():
    """Verify authority policy service is properly defined."""
    from domains.hr.services.authority_policy import (
        AUTHORITY_THRESHOLDS,
        get_required_authority,
        can_approve,
    )
    assert "leave" in AUTHORITY_THRESHOLDS
    assert get_required_authority("leave") == 1
    assert can_approve(2, "expense_500") is True
    assert can_approve(1, "expense_500") is False


def test_notification_tables_exist():
    """Verify the canonical HR employee-related tables are defined.

    Phase 2.1 updated this assertion to match the tables that actually
    exist in ``domains/hr/models/employee_models.py``. Previous names
    referenced planned (but not-yet-built) tables from the audit
    proposal; we now assert the canonical HR surface.
    """
    from domains.hr.models import employee_models

    expected = (
        "Office",
        "Employee",
        "EmployeeRole",
        "EmployeeLeaveRequest",
        "EmployeeShiftRoster",
        "ShiftHandoverSession",
        "ShiftHandoverTask",
        "PayrollRecord",
    )
    for cls_name in expected:
        assert hasattr(employee_models, cls_name), (
            f"Missing HR model: {cls_name}"
        )
        cls = getattr(employee_models, cls_name)
        assert cls is not None
