"""Tests for FILE-63: supplier_shared.py __all__ and supplier_service.py explicit imports."""

import ast
import importlib
import os
import sys

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend"))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

# Paths
_SUPPLIER_SHARED_PATH = os.path.join(
    _BACKEND_ROOT, "domains", "suppliers", "services", "supplier_shared.py"
)
_SUPPLIER_SERVICE_PATH = os.path.join(
    _BACKEND_ROOT, "domains", "suppliers", "services", "supplier_service.py"
)


def _parse_supplier_shared():
    """Parse supplier_shared.py without importing it (avoids broken import chain)."""
    with open(_SUPPLIER_SHARED_PATH, encoding="utf-8") as fh:
        source = fh.read()
    tree = ast.parse(source)
    return source, tree


def _get_module_names(tree):
    """Get all names defined at module top-level (functions, classes, assignments)."""
    names = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef):
            names.add(node.name)
        elif isinstance(node, ast.AsyncFunctionDef):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AugAssign):
            if isinstance(node.target, ast.Name):
                names.add(node.target.id)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                names.add(node.target.id)
    return names


def test_supplier_shared_has_all():
    """supplier_shared.py must define __all__ listing only public names."""
    source, tree = _parse_supplier_shared()
    # Check that __all__ is assigned at module level
    all_assignments = [
        node for node in ast.iter_child_nodes(tree)
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets)
    ]
    assert len(all_assignments) == 1, "supplier_shared.py must have exactly one __all__ assignment"
    all_value = ast.literal_eval(all_assignments[0].value)
    assert isinstance(all_value, list), "__all__ must be a list"
    assert len(all_value) > 0, "__all__ must not be empty"


def test_all_excludes_private_names():
    """__all__ must not contain underscore-prefixed (private) names."""
    source, tree = _parse_supplier_shared()
    all_assignments = [
        node for node in ast.iter_child_nodes(tree)
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets)
    ]
    all_value = ast.literal_eval(all_assignments[0].value)
    private = [name for name in all_value if name.startswith("_")]
    assert private == [], f"__all__ contains private names: {private}"


def test_all_names_are_defined_in_module():
    """Every name in __all__ must actually be defined in supplier_shared.py."""
    source, tree = _parse_supplier_shared()
    all_assignments = [
        node for node in ast.iter_child_nodes(tree)
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets)
    ]
    all_value = ast.literal_eval(all_assignments[0].value)
    defined_names = _get_module_names(tree)
    missing = [name for name in all_value if name not in defined_names]
    assert missing == [], f"Names in __all__ but not defined in module: {missing}"


def test_supplier_service_no_wildcard_from_shared():
    """supplier_service.py must not use 'import *' from supplier_shared."""
    with open(_SUPPLIER_SERVICE_PATH, encoding="utf-8") as fh:
        source = fh.read()

    assert "from domains.suppliers.services.supplier_shared import *" not in source, (
        "supplier_service.py must not use wildcard import from supplier_shared"
    )
    assert "from domains.suppliers.services.supplier_shared import (" in source, (
        "supplier_service.py must use explicit named imports from supplier_shared"
    )


def test_supplier_service_explicit_imports_only_public_names():
    """Explicit imports in supplier_service.py must match names in supplier_shared.__all__."""
    source, tree = _parse_supplier_shared()
    all_assignments = [
        node for node in ast.iter_child_nodes(tree)
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets)
    ]
    all_value = ast.literal_eval(all_assignments[0].value)

    with open(_SUPPLIER_SERVICE_PATH, encoding="utf-8") as fh:
        service_source = fh.read()

    import_start = service_source.index("from domains.suppliers.services.supplier_shared import (")
    import_end = service_source.index(")", import_start)
    import_block = service_source[import_start:import_end]
    imported_names = [
        line.strip().rstrip(",")
        for line in import_block.split("\n")[1:]
        if line.strip() and not line.strip().startswith("#")
    ]

    not_in_all = [name for name in imported_names if name not in all_value]
    assert not_in_all == [], (
        f"Imported names not in supplier_shared.__all__: {not_in_all}"
    )


def test_wildcard_import_does_not_leak_private_names():
    """A wildcard import from supplier_shared must not expose private (underscore) names."""
    source, tree = _parse_supplier_shared()
    all_assignments = [
        node for node in ast.iter_child_nodes(tree)
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets)
    ]
    all_value = ast.literal_eval(all_assignments[0].value)

    leaked_private = [name for name in all_value if name.startswith("_")]
    assert leaked_private == [], (
        f"Wildcard import would leak private names: {leaked_private}"
    )


def test_supplier_service_no_private_names_leaked_from_shared():
    """supplier_service.py must not import any private names from supplier_shared."""
    source, tree = _parse_supplier_shared()
    all_assignments = [
        node for node in ast.iter_child_nodes(tree)
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets)
    ]
    all_value = ast.literal_eval(all_assignments[0].value)

    with open(_SUPPLIER_SERVICE_PATH, encoding="utf-8") as fh:
        service_source = fh.read()

    import_start = service_source.index("from domains.suppliers.services.supplier_shared import (")
    import_end = service_source.index(")", import_start)
    import_block = service_source[import_start:import_end]
    imported_names = [
        line.strip().rstrip(",")
        for line in import_block.split("\n")[1:]
        if line.strip() and not line.strip().startswith("#")
    ]

    private_imported = [name for name in imported_names if name.startswith("_")]
    assert private_imported == [], (
        f"supplier_service.py imports private names from supplier_shared: {private_imported}"
    )
