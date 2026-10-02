"""Verify event_workers.py has no TODO placeholders and real handler logic."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

import os

os.environ.setdefault("APP_ENV", "test")

EVENT_WORKERS_PATH = _BACKEND_ROOT / "jobs" / "event_workers.py"


def test_no_todo_placeholders():
    source = EVENT_WORKERS_PATH.read_text(encoding="utf-8")
    assert "TODO" not in source, "event_workers.py contains TODO placeholders"


def test_handler_functions_call_real_services():
    source = EVENT_WORKERS_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    handler_names = []
    service_import_names = {
        "create_payment_intent", "update_order_status", "finalize_inventory_atomic",
        "deliver_email", "send_sms", "send_whatsapp_message",
        "FulfillmentService",
    }

    found_service_calls = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("handle_"):
            handler_names.append(node.name)
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    func = child.func
                    if isinstance(func, ast.Attribute):
                        attr_name = func.attr
                        if attr_name in service_import_names:
                            found_service_calls.add(attr_name)
                    elif isinstance(func, ast.Name):
                        if func.id in service_import_names:
                            found_service_calls.add(func.id)

    assert handler_names, "No handler functions found in event_workers.py"
    assert found_service_calls, "Handlers do not call any real service functions"


def test_run_all_workers_defined():
    source = EVENT_WORKERS_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    function_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    assert "run_all_workers" in function_names, "run_all_workers is not defined"
    assert "stop_all_workers" in function_names, "stop_all_workers is not defined"


def test_event_subscriber_start_stopsubscribes():
    from infrastructure.events.subscriber import EventSubscriber
    from infrastructure.messaging.events.event_bus import _subscribers

    test_handler = lambda event: None
    subscriber = EventSubscriber("test-group", {"test.event": test_handler})
    subscriber.start()
    assert any(entry[0] is test_handler for entry in _subscribers.get("test.event", [])), \
        "Handler was not registered with event_bus"
    subscriber.stop()
    assert all(entry[0] is not test_handler for entry in _subscribers.get("test.event", [])), \
        "Handler was not unregistered from event_bus"


def test_create_workers_registers_handlers():
    from jobs.event_workers import run_all_workers, stop_all_workers
    from infrastructure.messaging.events.event_bus import _subscribers

    workers = run_all_workers()
    try:
        expected_event_types = {
            "orders.order.created",
            "orders.order.shipped",
            "orders.order.delivered",
            "orders.order.cancelled",
            "customers.customer.registered",
            "suppliers.supplier.verified",
            "suppliers.supplier.rejected",
            "payment.authorized",
            "payment.failed",
        }
        registered_types = set(_subscribers.keys())
        missing = expected_event_types - registered_types
        assert not missing, f"Event workers did not register handlers for: {missing}"
    finally:
        stop_all_workers(workers)
