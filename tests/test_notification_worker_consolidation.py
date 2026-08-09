"""Verify the notification worker consolidation (CG2 fix).

The broken mis-housed duplicate ``backend/settings/notification_worker.py`` was
removed. The circuit-correct worker now lives at
``backend/services/comms/notification_worker.py`` (services -> db is a legal
downward call). This test confirms the canonical worker is importable and
exposes the expected entry points.
"""

from __future__ import annotations

import importlib

import pytest


def test_notification_worker_module_importable():
    mod = importlib.import_module("services.comms.notification_worker")
    assert hasattr(mod, "main"), "worker must expose a main() entrypoint"
    assert hasattr(mod, "_poll_once"), "worker must expose _poll_once()"
    assert hasattr(mod, "_deliver_notification"), "worker must expose _deliver_notification()"


def test_settings_duplicate_gone():
    # The broken duplicate must no longer resolve as a module.
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("settings.notification_worker")


if __name__ == "__main__":
    test_notification_worker_module_importable()
    test_settings_duplicate_gone()
    print("notification_worker consolidation OK")
