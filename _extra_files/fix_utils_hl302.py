#!/usr/bin/env python3
"""Add logging to un-logged exception handlers in backend/utils/*.py (HL302 fix).

Detector rule (scripts/system_trackers/system_architecture_audit.py):
  a handler is "swallowed" if its body is only `pass` OR contains NO Call whose
  dotted name contains "log". Broad `except Exception/BaseException` handlers
  that DO log are flagged HL303 instead.

This script:
  1. Finds every ExceptHandler whose subtree has no log call.
  2. Inserts `logger.debug(...)` (narrow/expected fallback) or
     `logger.exception(...)` (broad or bare) as the first body statement,
     expanding single-line `except X: <stmt>` forms.
  3. Ensures a module-level `logger = logging.getLogger(__name__)` exists.
  4. Validates with ast.parse after every file write.
"""
from __future__ import annotations

import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent / "backend"

# All utils files flagged HL302 (swallowed) by the audit.
TARGETS = [
    "utils/auth.py",
    "utils/backup.py",
    "utils/circuit_breaker.py",
    "utils/config.py",
    "utils/dependencies.py",
    "utils/error_handler.py",
    "utils/ip_utils.py",
    "utils/middleware_helpers.py",
    "utils/money.py",
    "utils/order_tracking.py",
    "utils/prometheus_setup.py",
    "utils/redis_client.py",
    "utils/soft_delete.py",
]


def dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return ""


def has_log_call(handler: ast.ExceptHandler) -> bool:
    for c in ast.walk(handler):
        if isinstance(c, ast.Call) and "log" in dotted_name(c.func).lower():
            return True
    return False


def handler_kind(handler: ast.ExceptHandler) -> tuple[str, bool]:
    """Return (level, is_broad)."""
    if handler.type is None:
        return "exception", True  # bare except
    names = []
    if isinstance(handler.type, ast.Name):
        names = [handler.type.id]
    elif isinstance(handler.type, ast.Tuple):
        names = [el.id for el in handler.type.elts if isinstance(el, ast.Name)]
    broad = any(n in ("Exception", "BaseException") for n in names)
    return ("exception" if broad else "debug"), broad


def module_logger_name(tree: ast.Module, src: str) -> str | None:
    """Return the module-level logger variable name if one exists."""
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id in ("logger", "log"):
                    # confirm RHS is a getLogger call
                    if isinstance(node.value, ast.Call) and "getLogger" in dotted_name(node.value.func):
                        return t.id
    return None


def ensure_logger(tree: ast.Module, lines: list[str]) -> tuple[list[str], str]:
    """Ensure `logger = logging.getLogger(__name__)` exists at module level."""
    name = module_logger_name(tree, "\n".join(lines))
    if name:
        return lines, name

    # Pick insertion point: after the last top-level import statement.
    insert_after = 0
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            insert_after = node.end_lineno  # type: ignore[attr-defined]
        else:
            break  # imports are consecutive at the top
    indent = ""
    has_logging_import = any(
        isinstance(n, ast.Import) and any(a.name == "logging" for a in n.names)
        for n in tree.body
        if isinstance(n, ast.Import)
    )
    if not has_logging_import:
        lines.insert(insert_after, "import logging")
        insert_after += 1
    lines.insert(insert_after, "logger = logging.getLogger(__name__)")
    return lines, "logger"


def line_indent(line: str) -> str:
    return line[: len(line) - len(line.lstrip())]


def process(path: pathlib.Path) -> tuple[int, int, str]:
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    lines = src.split("\n")

    # Collect edits as (sort_key, action, payload)
    edits = []  # (lineno, indent, text, mode)
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        if has_log_call(node):
            continue
        level, _broad = handler_kind(node)
        msg = f"{path.name}:{node.lineno} exception"
        stmt = f'logger.{level}("{msg}")'
        body = node.body
        if not body:
            continue
        first = body[0]
        if first.lineno == node.lineno:
            # single-line handler: `except X: <stmt>` — expand to multi-line
            line = lines[first.lineno - 1]
            colon = line.find(":")
            if colon == -1:
                continue
            head = line[: colon + 1]
            rest = line[colon + 1 :].strip()
            base_indent = line_indent(line)
            body_indent = base_indent + "    "
            new_line = head
            extra = [body_indent + stmt]
            if rest and rest != "pass":
                extra.append(base_indent + rest)
            edits.append((first.lineno - 1, "replace", (line, new_line, extra)))
        else:
            indent = line_indent(lines[first.lineno - 1])
            edits.append((first.lineno - 1, "insert", (indent + stmt,)))

    # Apply edits bottom-up so line numbers stay valid.
    edits.sort(key=lambda e: e[0], reverse=True)
    for _lineno, mode, payload in edits:
        idx = _lineno
        if mode == "insert":
            text = payload[0]
            lines.insert(idx, text)
        else:
            _old, new_head, extra = payload
            lines[idx] = new_head
            for j, extra_line in enumerate(reversed(extra)):
                lines.insert(idx + 1, extra_line)

    # Ensure logger exists (after edits so we can re-parse).
    new_src = "\n".join(lines)
    tree2 = ast.parse(new_src)
    lines, logger_name = ensure_logger(tree2, lines)
    lines = [ln if ln != "logger = logging.getLogger(__name__)" else f"{logger_name} = logging.getLogger(__name__)" for ln in lines]

    final_src = "\n".join(lines)
    ast.parse(final_src)  # raises if broken
    path.write_text(final_src, encoding="utf-8")
    return len(edits), 1, logger_name


def main() -> None:
    total_handlers = 0
    fixed_files = 0
    for rel in TARGETS:
        path = ROOT / rel
        if not path.exists():
            print(f"  MISSING {rel}")
            continue
        try:
            n_handlers, _loggers, logger_name = process(path)
            if n_handlers:
                fixed_files += 1
                total_handlers += n_handlers
                print(f"  {rel}: {n_handlers} handler(s) logged (logger={logger_name})")
            else:
                print(f"  {rel}: no un-logged handlers (skip)")
        except SyntaxError as e:
            print(f"  FAILED {rel}: {e}")
            sys.exit(1)
    print(f"\nFixed {fixed_files} files, {total_handlers} handlers.")


if __name__ == "__main__":
    main()
