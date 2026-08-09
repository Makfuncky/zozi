"""Verification that the DOM7 communication/ duplicate folders were rescued.

DOM7 advisory (SYSTEM_AUDIT_REPORT.md): non-canonical domain folder
'communication/' should be 'comms/'. The canonical content already lives
under the comms/ tree, so the redundant communication/ folders are removed:

Removed (empty / shim-only duplicates):
    backend/controllers/communication/      (empty package)
    backend/models/communication/           (empty package)
    backend/services/communication/         (1-file shim re-exporting
                                             services.comms.command_center_query_service)

Kept (canonical, still wired to a router):
    backend/controllers/comm_controller.py  (used by routers/comm.py + main.py)
    backend/controllers/comms/comm_controller.py
    backend/services/comms/command_center_query_service.py
"""
from __future__ import annotations

import importlib
import importlib.util

import pytest


def _module_exists(dotted_path: str) -> bool:
    return importlib.util.find_spec(dotted_path) is not None


def test_canonical_comms_controller_exports_required_symbols():
    import controllers.comms.comm_controller as m

    for name in (
        "create_video_room",
        "create_chat_thread",
        "send_masked_message",
        "create_incident_room",
        "get_command_center_metrics",
    ):
        assert hasattr(m, name), f"canonical comms module missing {name}"


def test_communication_duplicate_folders_are_gone():
    # The redundant backend/{controllers,models,services}/communication/ trees
    # must be removed (their content already lives under the comms/ tree).
    assert not _module_exists("controllers.communication")
    assert not _module_exists("models.communication")
    assert not _module_exists("services.communication")


def test_canonical_command_center_query_service_is_present():
    import services.comms.command_center_query_service as m

    for name in ("safe_scalar", "safe_fetch", "safe_count", "_validate_table_name"):
        assert hasattr(m, name), f"canonical command_center_query_service missing {name}"


def test_real_comm_controller_still_wired():
    # controllers/comm_controller.py is a real controller (routers/comm.py +
    # main.py), not a deletable shim. It must still import after DOM7 cleanup.
    import controllers.comm_controller as m

    for name in (
        "create_video_room",
        "create_chat_thread",
        "send_masked_message",
        "create_incident_room",
        "get_command_center_metrics",
    ):
        assert hasattr(m, name), f"comm_controller missing {name}"


def test_controllers_package_imports_without_communication_reference():
    import controllers

    # email_controller was a tolerated None placeholder tied to the deleted
    # communication package; it must not raise and must not resolve to a module.
    assert not hasattr(controllers, "email_controller")
