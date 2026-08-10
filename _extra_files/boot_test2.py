"""Boot test: import main, count routes, and surface any failed routers."""
import importlib
import logging

logging.basicConfig(level=logging.ERROR)

import main

# Replicate _load_routers import loop but capture failures explicitly.
router_names = main._load_routers.__code__  # noqa: F841
# Easiest: read the tuple from main by re-executing the list via module inspection.
# Instead, just count routes and report.
routes = [getattr(r, "path", None) for r in main.app.routes]
print("TOTAL_ROUTES", len(routes))

# Detect failed routers by trying each import that _load_routers would do.
import ast

src = open("main.py", encoding="utf-8").read()
tree = ast.parse(src)
names = []
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id == "router_names":
                if isinstance(node.value, ast.List):
                    for el in node.value.elts:
                        if isinstance(el, ast.Tuple) and len(el.elts) == 2:
                            names.append((el.elts[0].value, el.elts[1].value))

failed = []
for name, prefix in names:
    try:
        importlib.import_module(f"routers.{name}")
    except ImportError:
        try:
            importlib.import_module(f"controllers.{name}")
        except ImportError as e:
            failed.append((name, str(e)))

print("REGISTERED_ROUTERS", len(names))
print("FAILED_ROUTERS", len(failed))
for n, e in failed:
    print("FAIL", n, e)
