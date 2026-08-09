"""Boot regression — every router in ``main.py``'s ``router_names`` must import.

Guards against the intermittent import-order breakage that occurred when
``services/orders/order_payment_functions`` was moved to ``services/finance``
and the old module path was only *name*-re-exported via the package
``__init__``. On some boots 8 routers then failed with ``ModuleNotFoundError``
(the app silently dropped their routes), while on others they loaded fine.

If any router cannot be imported, the app would drop routes at startup — so
this test fails loudly instead of letting the breakage go unnoticed.
"""

from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

# Ensure the backend package root is importable regardless of cwd.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("APP_ENV", "test")


def _router_names_from_main() -> list[str]:
    """Extract router module names from ``backend/main.py`` via AST.

    Parsing (not importing) keeps collection fast and avoids triggering the
    full app assembly just to enumerate the router list.
    """
    main_path = _BACKEND_ROOT / "main.py"
    tree = ast.parse(main_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "router_names" for t in node.targets):
            continue
        if not isinstance(node.value, ast.List):
            continue
        names: list[str] = []
        for elt in node.value.elts:
            if isinstance(elt, ast.Tuple) and elt.elts:
                first = elt.elts[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    names.append(first.value)
        return names
    return []


def test_all_routers_import_cleanly() -> None:
    import importlib

    names = _router_names_from_main()
    assert len(names) > 100, f"sanity check failed: expected 100+ routers, got {len(names)}"

    failures: list[tuple[str, str]] = []
    seen: set[str] = set()
    for name in names:
        if name in seen:  # main.py registers some routers under two prefixes
            continue
        seen.add(name)
        try:
            importlib.import_module(f"routers.{name}")
        except ImportError:
            # main.py falls back to controllers.{name} for legacy entries
            try:
                importlib.import_module(f"controllers.{name}")
            except Exception as exc:  # noqa: BLE001 - report the first error
                failures.append((name, str(exc)[:200]))
        except Exception as exc:  # noqa: BLE001 - report the first error
            failures.append((name, str(exc)[:200]))

    assert not failures, (
        f"{len(failures)} router(s) failed to import at boot:\n"
        + "\n".join(f"  {name}: {err}" for name, err in failures)
    )
