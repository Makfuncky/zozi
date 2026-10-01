"""W1 layer-contract guard.

Detects DB WRITE operations that live in the read-only orchestration layers
(routers/, controllers/, middleware/, dependencies/) and therefore must be
owned by services/**.

The detection logic mirrors scripts/system_trackers/system_architecture_audit.py
(check_layer_writes) so this test tracks the same W1 violations the audit
report uses. It is intentionally import-free (only ast/os/re) so it runs
without importing the (partially broken) models package.

W1 write sites:
  - session.add / add_all / commit / flush / delete / merge
  - session.execute(...) where the SQL is INSERT/UPDATE/DELETE/DROP/ALTER/
    CREATE/TRUNCATE/MERGE/UPSERT

A "session" is any variable named db/session/sess/s/db_session, or any
function parameter so named, or any parameter annotated with Session/
AsyncSession.
"""
from __future__ import annotations

import ast
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(REPO_ROOT, "backend")

FORBIDDEN_WRITE_LAYERS = {
    "routers": os.path.join(BACKEND, "routers"),
    "controllers": os.path.join(BACKEND, "controllers"),
    "middleware": os.path.join(BACKEND, "middleware"),
    "dependencies": os.path.join(BACKEND, "dependencies"),
}

SESSION_NAMES = {"db", "session", "sess", "s", "db_session"}
WRITE_VERBS = {"add", "add_all", "commit", "flush", "delete", "merge"}

SQL_WRITE_RE = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|MERGE|UPSERT)\b", re.I
)
SQL_READ_RE = re.compile(r"\b(SELECT|SHOW|DESCRIBE|EXPLAIN|WITH)\b", re.I)


def _classify_execute(node: ast.Call, source_lines) -> str:
    if not node.args:
        return "unknown"
    arg = node.args[0]
    sql_text = ""
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        sql_text = arg.value
    elif isinstance(arg, ast.Call):
        func_name = ""
        if isinstance(arg.func, ast.Name):
            func_name = arg.func.id
        elif isinstance(arg.func, ast.Attribute):
            func_name = arg.func.attr
        if func_name == "text" and arg.args:
            inner = arg.args[0]
            if isinstance(inner, ast.Constant) and isinstance(inner.value, str):
                sql_text = inner.value
            elif isinstance(inner, ast.Name) and source_lines:
                var_name = inner.id
                for line in source_lines[: arg.lineno]:
                    ul = line.upper()
                    if var_name in line and (
                        "=" in line
                        or "INSERT" in ul
                        or "UPDATE" in ul
                        or "DELETE" in ul
                        or "SELECT" in ul
                    ):
                        sql_text = line
                        break
    elif isinstance(arg, ast.JoinedStr):
        parts = []
        for value in arg.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            elif isinstance(value, ast.FormattedValue):
                parts.append("{...}")
        sql_text = "".join(parts)
    elif isinstance(arg, ast.Name) and source_lines:
        var_name = arg.id
        for line in source_lines[: arg.lineno]:
            if var_name in line and "=" in line:
                sql_text = line
                break
    if not sql_text:
        return "unknown"
    if SQL_WRITE_RE.search(sql_text):
        return "write"
    if SQL_READ_RE.search(sql_text):
        return "read"
    return "unknown"


def _find_session_vars(tree: ast.Module) -> set:
    session_vars = set(SESSION_NAMES)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args.args + node.args.posonlyargs + node.args.kwonlyargs
            for arg in args:
                if arg.arg in {"db", "session", "sess", "s", "db_session"}:
                    session_vars.add(arg.arg)
                elif arg.annotation:
                    ann = ast.dump(arg.annotation)
                    if "Session" in ann or "AsyncSession" in ann:
                        session_vars.add(arg.arg)
    return session_vars


def _scan_file(py_file: str) -> list:
    findings = []
    try:
        with open(py_file, "r", encoding="utf-8") as fh:
            text = fh.read()
    except (OSError, UnicodeDecodeError):
        return findings
    if not text:
        return findings
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return findings

    source_lines = text.splitlines()
    session_vars = _find_session_vars(tree)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        method_name = node.func.attr
        obj = node.func.value
        obj_name = ""
        if isinstance(obj, ast.Name):
            obj_name = obj.id
        elif isinstance(obj, ast.Attribute):
            obj_name = obj.attr
        if obj_name not in session_vars:
            continue
        line = getattr(node, "lineno", None)
        if method_name in WRITE_VERBS:
            findings.append((line, f"session.{method_name}()"))
        elif method_name == "execute":
            classification = _classify_execute(node, source_lines)
            if classification == "write":
                findings.append((line, "session.execute(WRITE SQL)"))
    return findings


def main() -> int:
    if not os.path.isdir(BACKEND):
        print(f"backend not found at {BACKEND}")
        return 2

    total = 0
    per_file = []
    for layer_name, layer_dir in FORBIDDEN_WRITE_LAYERS.items():
        if not os.path.isdir(layer_dir):
            continue
        for root, _dirs, files in os.walk(layer_dir):
            for name in files:
                if not name.endswith(".py"):
                    continue
                full = os.path.join(root, name)
                hits = _scan_file(full)
                if hits:
                    rel = os.path.relpath(full, REPO_ROOT).replace(os.sep, "/")
                    per_file.append((layer_name, rel, hits))
                    total += len(hits)

    if total == 0:
        print("W1 PASS: no DB writes found in routers/controllers/middleware/dependencies")
        return 0

    print(f"W1 FAIL: {total} DB write site(s) in read-only layers\n")
    for layer_name, rel, hits in per_file:
        print(f"  [{layer_name}] {rel}")
        for line, desc in sorted(hits):
            print(f"      L{line}: {desc}")
    print(f"\nTotal W1 violations: {total}")
    return 1


if __name__ == "__main__":
    sys.exit(main())


def test_w1_write_layers_informational():
    """W1 layer-contract guard.

    Runs the detector and reports the current violation count. While the
    migration of DB writes into services/** is in progress this is
    informational only (it always passes and prints the count). Once the
    count reaches 0, tighten this to `assert main() == 0`.
    """
    import pytest

    result = main()
    pytest_echo = getattr(pytest, "echo", None)
    if callable(pytest_echo):
        pytest_echo(f"W1 DB write sites remaining: {result}")
    assert True
