"""W1 regression test for routers/admin_video.py."""
import ast
import importlib

WRITE_VERBS = {
    "add", "add_all", "commit", "flush", "delete", "merge",
    "bulk_save_objects", "bulk_insert_mappings", "bulk_update_mappings",
    "bulk_update", "begin", "begin_nested",
}


def _write_calls_in(path: str):
    tree = ast.parse(open(path, encoding="utf-8").read())
    return [
        (n.lineno, n.func.attr)
        for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
        and n.func.attr in WRITE_VERBS
    ]


def test_admin_video_router_no_db_writes():
    hits = _write_calls_in("backend/routers/admin_video.py")
    assert hits == [], f"W1: router still writes to DB at {hits}"


def test_admin_video_controller_no_db_writes():
    hits = _write_calls_in("backend/controllers/admin_video_controller.py")
    assert hits == [], f"W1: controller still writes to DB at {hits}"


def test_admin_video_wiring():
    router = importlib.import_module("routers.admin_video_governance")
    controller = importlib.import_module("controllers.admin_video_controller")
    service = importlib.import_module("services.comms.video_room_write_service")
    assert hasattr(router, "router")
    assert hasattr(controller, "ensure_room_country")
    assert hasattr(service, "ensure_video_room_country")
