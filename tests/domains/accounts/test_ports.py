"""Tests for accounts domain ports read-only contract."""

import ast
import pathlib

import pytest

PORTS_PATH = pathlib.Path(__file__).resolve().parent.parent.parent.parent / "backend" / "domains" / "accounts" / "ports.py"


def test_ports_read_only():
    """ports.py must contain only read-only interfaces."""
    source = PORTS_PATH.read_text(encoding="utf-8")

    # No direct write operations in the source
    for forbidden in ("db.add", "db.delete", "db.commit"):
        assert forbidden not in source, f"ports.py contains write operation: {forbidden}"

    # All top-level functions must be read-only helpers
    tree = ast.parse(source)
    top_functions = [
        node.name
        for node in ast.iter_child_nodes(tree)
        if isinstance(node, ast.FunctionDef)
    ]

    read_only_prefixes = ("get_", "list_", "_keyset_")
    for func_name in top_functions:
        assert func_name.startswith(read_only_prefixes) or func_name == "__getattr__", (
            f"Function {func_name} in ports.py is not a read-only helper"
        )
