import ast
from pathlib import Path


def test_startup_register_services_no_dead_imports():
    source = Path("backend/lifespan.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_startup_register_services":
            func_source = ast.get_source_segment(source, node) or ""
            assert "services.unknown" not in func_source
            assert "services._registry" not in func_source
            assert "services.registry" not in func_source


def test_fulfillment_service_import_path():
    source = Path("backend/lifespan.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_startup_register_event_listeners":
            func_source = ast.get_source_segment(source, node) or ""
            assert "domains.orders.services.core.logistics" in func_source
            assert "domains.orders.services.fulfillment_service" not in func_source
