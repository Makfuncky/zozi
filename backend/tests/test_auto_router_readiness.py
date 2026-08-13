"""Regression test: the orders and HR controllers are auto-router-ready.

These two controllers were decorated with ``core.route_contract`` decorators so
``routers/generated/auto_router.py`` can generate their FastAPI surface. This
test runs the REAL generator logic (scan -> validate -> generate -> forbid-check)
to prove the controllers are ready to auto-generate routers, without writing any
files to disk.
"""
import routers.generated.auto_router as ar

DOMAINS = ["orders_controller", "hr_controller"]


def _modules():
    return [m for m in ar.scan_controllers() if any(d in m["module"] for d in DOMAINS)]


def test_auto_router_discovers_decorated_controllers():
    modules = _modules()
    names = {m["module"] for m in modules}
    assert "controllers.orders_controller" in names, "orders_controller not discovered"
    assert "controllers.hr_controller" in names, "hr_controller not discovered"
    assert all(len(m["routes"]) > 0 for m in modules), "decorated controller has 0 routes"


def test_auto_router_generated_routes_are_valid():
    modules = _modules()
    errors = ar.validate(modules)
    for mi in modules:
        gen = ar.generate_router_file(mi)
        errors.extend(ar.check_forbidden(gen, mi["module"]))
    assert not errors, "Auto-router found problems:\n" + "\n".join(errors)


def test_auto_router_generated_files_are_self_contained():
    """Every symbol the generated router re-imports from the controller must exist."""
    import importlib

    modules = _modules()
    for mi in modules:
        gen = ar.generate_router_file(mi)
        # Pull the `from <module> import a, b, c` re-export line.
        for line in gen.splitlines():
            if line.startswith("from controllers") and " import " in line:
                head, _, tail = line.partition(" import ")
                mod = head.replace("from ", "", 1).strip()
                syms = [s.strip() for s in tail.split(",") if s.strip()]
                target = importlib.import_module(mod)
                missing = [s for s in syms if not hasattr(target, s)]
                assert not missing, f"{mod} missing symbols for {mi['module']}: {missing}"
