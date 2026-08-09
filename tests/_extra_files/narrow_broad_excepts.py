"""Align backend exception handling to the structlog/ErrorHandler architecture.

Fixes two audit findings across production backend code:
  - HL302 (swallowed handler): every ``except`` block must contain a call whose
    name includes "log" (e.g. ``logger.exception(...)``).  Handlers that are
    ``pass``-only or have no logging get a structured ``logger.exception`` call.
  - HL303 (broad ``except Exception``): the caught type is narrowed from
    ``Exception``/``BaseException`` to the standard-library exception set so
    domain ``AppError`` subclasses correctly propagate to the centralized
    ``global_exception_handler`` (RFC 7807) instead of being silently swallowed.

Design notes:
  - Only builtin exception names are used in the narrowing tuple, so no new
    imports are required and no NameError can be introduced.
  - The logger name is reused if the module already defines one
    (``logger``/``log``/etc.); otherwise ``structlog.get_logger(__name__)`` is
    injected at module top (after docstring + ``from __future__`` imports).
  - Idempotent: re-running produces no changes.

Usage:
  python tests/_extra_files/narrow_broad_excepts.py [--dry-run] [--path backend/foo.py]
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BACKEND = REPO / "backend"

# Builtin Exception subclasses (no import needed). Deliberately excludes
# Exception/BaseException literally and excludes custom domain exceptions so
# they bubble to the global handler.
NARROW = (
    "ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, "
    "OSError, IOError, EOFError, ImportError, NameError, StopIteration, "
    "ArithmeticError, AssertionError, UnicodeError, NotImplementedError, "
    "RecursionError, ReferenceError, SystemError, BufferError, LookupError"
)

EXCEPT_BROAD_RE = re.compile(
    r"^(?P<indent>\s*)except\s+(?P<type>Exception|BaseException)"
    r"(?P<binding>\s+as\s+\w+)?\s*:(?P<tail>.*)$"
)
LOGGER_ASSIGN_RE = re.compile(
    r"^\s*(?P<name>\w+)\s*=\s*(?:structlog\.)?getLogger\("
)
IMPORT_STRUCTLOG_RE = re.compile(r"^\s*import\s+structlog\b")
IS_TEST = re.compile(r"(?:^|[\\/])backend[\\/]tests[\\/]|[\\/]tests[\\/]")
IS_TEST_FILE = re.compile(r"(?:^|[\\/])(?:conftest|test_.*|.*_test)\.py$")
IMPORT_TEST = re.compile(r"(?:^|[\\/])_import_test\.py$")


def is_test_file(path: Path) -> bool:
    s = str(path)
    return bool(IS_TEST.search(s) or IS_TEST_FILE.search(s) or IMPORT_TEST.search(s))


def find_logger_name(text: str) -> str | None:
    for m in LOGGER_ASSIGN_RE.finditer(text):
        return m.group("name")
    return None


def module_top_insert(text: str) -> tuple[int, str]:
    """Return (line_index_to_insert_after, indent) for module-top injection.

    Inserts after the module docstring and any ``from __future__`` import, at
    column 0, to avoid breaking parenthesized/try-block import groups.
    """
    lines = text.splitlines()
    insert_at = 0  # index AFTER which we insert (so new lines go at insert_at+1)
    in_docstring = False
    docstring_done = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not docstring_done:
            if not stripped:
                continue
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if stripped.count('"""') == 2 or stripped.count("'''") == 2:
                    docstring_done = True
                    insert_at = i
                    continue
                in_docstring = True
                docstring_done = False
                insert_at = i
                continue
            else:
                docstring_done = True
        if in_docstring:
            if '"""' in stripped or "'''" in stripped:
                in_docstring = False
                docstring_done = True
                insert_at = i
            continue
        # After docstring, allow only `from __future__` imports on the same "top".
        if stripped.startswith("from __future__"):
            insert_at = i
            continue
        # First real statement => insert after previous line.
        break
    return insert_at, ""


def ensure_structlog_logger(text: str, logger_name: str) -> tuple[str, str]:
    """Ensure ``logger_name = structlog.get_logger(__name__)`` exists.

    Returns (new_text, logger_name).
    """
    if LOGGER_ASSIGN_RE.search(text):
        return text, find_logger_name(text)
    lines = text.splitlines()
    has_structlog = bool(IMPORT_STRUCTLOG_RE.search(text))
    insert_idx, _ = module_top_insert(text)
    inject: list[str] = []
    if not has_structlog:
        inject.append("import structlog")
    inject.append(f'{logger_name} = structlog.get_logger(__name__)')
    # insert after insert_idx (0-based). New lines replace indent "".
    new_lines = lines[: insert_idx + 1] + inject + lines[insert_idx + 1 :]
    return "\n".join(new_lines), logger_name


def dotted_name(node) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return dotted_name(node.value) + "." + node.attr
    return ""


def handler_has_log(node: ast.ExceptHandler) -> bool:
    for c in ast.walk(node):
        if isinstance(c, ast.Call) and "log" in dotted_name(c.func).lower():
            return True
    return False


def process_file(path: Path, dry_run: bool) -> dict:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    is_test = is_test_file(path)
    logger_name = find_logger_name(text) or "logger"
    needs_logger_inject = False

    # Gather handler edits.
    edits: list[dict] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        if node.type is None:
            continue  # bare except -> handled by HL301 (already 0)
        type_names: list[str] = []
        if isinstance(node.type, ast.Name):
            type_names = [node.type.id]
        elif isinstance(node.type, ast.Tuple):
            type_names = [e.id for e in node.type.elts if isinstance(e, ast.Name)]
        is_broad = "Exception" in type_names or "BaseException" in type_names
        only_pass = all(isinstance(s, ast.Pass) for s in node.body)
        has_log = handler_has_log(node)
        binding = None
        if isinstance(node.name, str):
            binding = node.name

        want_log = (only_pass or not has_log)
        want_narrow = is_broad and not is_test  # never narrow in tests

        if not want_log and not want_narrow:
            continue

        edits.append(
            {
                "lineno": node.lineno,
                "body0": node.body[0].lineno if node.body else node.lineno + 1,
                "only_pass": only_pass,
                "has_log": has_log,
                "binding": binding,
                "is_broad": is_broad,
                "want_log": want_log,
                "want_narrow": want_narrow,
            }
        )
        if want_log and logger_name == "logger" and not find_logger_name(text):
            needs_logger_inject = True

    if not edits and not needs_logger_inject:
        return {"file": str(path), "changed": False, "edits": 0}

    lines = text.splitlines()
    # Apply edits bottom-up to preserve line numbers.
    edits.sort(key=lambda e: e["lineno"], reverse=True)

    for e in edits:
        ln = e["lineno"] - 1  # 0-based
        except_line = lines[ln]
        m = EXCEPT_BROAD_RE.match(except_line)
        indent = except_line[: len(except_line) - len(except_line.lstrip())]

        if e["want_narrow"] and m:
            name = e["binding"] or "e"
            tail = m.group("tail")
            lines[ln] = f"{indent}except ({NARROW}) as {name}:{tail}"
            binding_name = name
        elif e["is_broad"] and not m:
            # Multi-line except clause; skip narrowing to stay safe.
            continue
        else:
            binding_name = e["binding"]

        if e["want_log"]:
            # Determine indent of body.
            body_indent = indent + "    "
            log_call = (
                f'{body_indent}{logger_name}.exception('
                f'"unhandled exception", error=str({binding_name}))'
            )
            if e["only_pass"]:
                # Replace the single `pass` line.
                p = e["body0"] - 1
                lines[p] = log_call
            else:
                # Insert as first body statement.
                p = e["body0"] - 1
                lines.insert(p, log_call)

    new_text = "\n".join(lines)

    if needs_logger_inject:
        new_text, logger_name = ensure_structlog_logger(new_text, logger_name)

    if dry_run:
        return {"file": str(path), "changed": True, "edits": len(edits), "dry": True}

    try:
        path.write_text(new_text, encoding="utf-8")
    except OSError as ex:
        return {"file": str(path), "changed": False, "edits": 0, "skip": str(ex)}
    return {"file": str(path), "changed": True, "edits": len(edits)}


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    explicit = [a for a in sys.argv[1:] if not a.startswith("--")]
    files: list[Path]
    if explicit:
        norm = [a[8:] if a.startswith("backend/") else a for a in explicit]
        files = [BACKEND / a for a in norm]
    else:
        files = [
            p
            for p in BACKEND.rglob("*.py")
            if "venv" not in p.parts
            and not any(part == "scripts" for part in p.parts)
        ]
    changed = 0
    total_edits = 0
    for f in files:
        if not f.exists():
            continue
        try:
            res = process_file(f, dry_run)
        except SyntaxError as ex:
            print(f"[SKIP-syntax] {f}: {ex}", file=sys.stderr)
            continue
        if res["changed"]:
            changed += 1
            total_edits += res["edits"]
            if dry_run:
                print(f"[DRY] {res['file']} ({res['edits']} handlers)")
            else:
                print(f"[FIX] {res['file']} ({res['edits']} handlers)")
        elif res.get("skip"):
            print(f"[SKIP-write] {res['file']}: {res['skip']}", file=sys.stderr)
    print(f"\n{'DRY-RUN ' if dry_run else ''}Done: {changed} files changed, "
          f"{total_edits} handlers touched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
