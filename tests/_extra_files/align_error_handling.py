"""
Architecture-aligned error-handling fixer for the Zozi backend.

Problem: the SYSTEM_AUDIT_REPORT.md flags HL301/302/303 (swallowed / broad
exceptions). These are NOT false positives - the codebase has a real
error-handling architecture that swallowed handlers violate:

  * structlog is the canonical logger (utils/logging_config.py,
    utils/error_handler.py). The global exception handler logs with
    `logger.exception("...", **context)`; well-behaved modules do the same
    inline (see ai_upload_write_service, email_gateway, etc.).
  * Swallowed `except X: pass` / `except X: return fallback` silently drops
    the error so it never reaches structlog / Sentry / the RFC 7807 handler.

Fix (behavior-preserving): every swallowed handler gets an architecture-aligned
log statement using the module's structlog logger, capturing the exception:

  except SomeError:            ->  except SomeError as e:
      pass                         logger.exception("func_failed", error=str(e))

Broadening to `as e` only binds the already-caught exception; nothing else
changes. Degrade `return` paths are kept (cache-miss / best-effort are valid
architecture choices) - we only add observability.

Special cases (still aligned, less noisy):
  * ImportError / ModuleNotFoundError (optional deps): logger.warning
    (matches ErrorHandler._init_sentry precedent).
  * WebSocketDisconnect: logger.debug (protocol-level, not an error).
  * Control-flow exceptions (CancelledError, KeyboardInterrupt,
    SystemExit, GeneratorExit, StopIteration*, BrokenPipeError): left alone -
    these are intentional control flow, not swallowed errors.
"""
import ast
import os
import re
import sys

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"

TARGET_DIRS = [
    "data", "services", "utils", "providers", "routers",
    "controllers", "middleware", "db", "jobs", "events", "tools",
]
TARGET_TOP = ["main.py", "lifespan.py", "zozi_mcp"]

CONTROL_FLOW = {
    "KeyboardInterrupt", "SystemExit", "GeneratorExit",
    "StopIteration", "StopAsyncIteration", "CancelledError",
    "asyncio.CancelledError", "BrokenPipeError",
}

# ---------- helpers ---------------------------------------------------------

def collect_files():
    files = []
    for d in TARGET_DIRS:
        full = os.path.join(ROOT, d)
        if not os.path.isdir(full):
            continue
        for root, _dirs, names in os.walk(full):
            for n in names:
                if n.endswith(".py"):
                    p = os.path.join(root, n)
                    if "test" in p.lower():
                        continue
                    files.append(p)
    for n in TARGET_TOP:
        p = os.path.join(ROOT, n)
        if os.path.isfile(p) and "test" not in p.lower():
            files.append(p)
    return files


def module_logger_info(tree):
    """Return (logger_var_name, needs_structlog_import, add_logger_line)."""
    structlog_imported = False
    logger_vars = []  # module-level names assigned from a get_logger call
    for node in tree.body:
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name == "structlog":
                    structlog_imported = True
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] == "structlog":
                structlog_imported = True
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            target = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if isinstance(target, ast.Name):
                val = node.value
                if isinstance(val, ast.Call):
                    f = val.func
                    fn = dotted(f)
                    if fn.endswith("get_logger"):
                        logger_vars.append(target.id)
    if "logger" in logger_vars:
        return "logger", False, False
    if logger_vars:
        return logger_vars[0], False, False
    # no module-level logger -> add one
    return "logger", (not structlog_imported), True


def dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return dotted(node.value) + "." + node.attr
    return ""


def is_log_call(node):
    if not isinstance(node, ast.Call):
        return False
    fn = dotted(node.func).lower()
    return "log" in fn


def has_reraise(body):
    for n in ast.walk_nodes_list(body) if hasattr(ast, "walk_nodes_list") else body:
        pass
    # check for `raise` with no arg (reraise) anywhere in body
    for n in ast.walk(ast.Module(body=list(body))):
        if isinstance(n, ast.Raise) and n.exc is None:
            return True
    return False


def handler_is_swallowed(h):
    if not h.body:
        return True
    if all(isinstance(s, ast.Pass) for s in h.body):
        return True
    if any(isinstance(s, (ast.Return, ast.Continue, ast.Break)) for s in h.body) and \
       not any(is_log_call(s) for s in h.body):
        # still swallowed if it doesn't log
        pass
    # generic check: any log call anywhere in body?
    for n in ast.walk(ast.Module(body=list(h.body))):
        if isinstance(n, ast.Call) and is_log_call(n):
            return False
    return True


def except_type_names(h):
    """Return set of exception type names referenced in the handler type."""
    names = set()
    t = h.type
    if t is None:
        names.add("Exception")  # bare except
        return names
    if isinstance(t, ast.Tuple):
        for elt in t.elts:
            names.add(dotted(elt))
    else:
        names.add(dotted(t))
    return names


def _top_insert_line(tree):
    """1-indexed line AFTER which to insert module-level import/logger.

    Skips the module docstring and any `from __future__ import ...` (which must
    remain the first statement) and inserts at column 0 at the very top.
    """
    consumed = 0
    body = tree.body
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str):
        consumed = body[0].end_lineno
    for node in body:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            consumed = max(consumed, node.end_lineno)
        elif isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant) and isinstance(node.value.value, str):
            consumed = max(consumed, node.end_lineno)
        else:
            break
    return consumed


def snake(name):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


# ---------- per-file transform ---------------------------------------------

def fix_file(path):
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    lines = src.split("\n")
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return 0

    logger_var, need_structlog, add_logger = module_logger_info(tree)
    edits = []  # (sort_key, kind, lineno, payload)
    patch_count = 0

    # Recursively walk, tracking enclosing function name.
    def visit(node, func_name):
        nonlocal patch_count
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                visit(child, child.name)
            elif isinstance(child, ast.Try):
                for h in child.handlers:
                    if not handler_is_swallowed(h):
                        continue
                    # control-flow exceptions -> leave alone
                    types = except_type_names(h)
                    if types & CONTROL_FLOW:
                        continue

                    # determine variable name to bind
                    if h.name:
                        var = h.name
                    else:
                        var = "e"
                        # rewrite except line to add `as e`
                        hl = h.lineno
                        orig = lines[hl - 1]
                        new_line = rewrite_except(orig, var)
                        if new_line != orig:
                            edits.append((hl, "replace", hl, new_line))
                    # build log statement
                    event = (func_name + "_failed") if func_name else (snake(os.path.splitext(os.path.basename(path))[0]) + "_operation_failed")
                    indent = body_indent(lines, h)
                    if types & {"ImportError", "ModuleNotFoundError"}:
                        log = f'{indent}{logger_var}.warning("optional_dependency_unavailable", error=str({var}))'
                    elif "WebSocketDisconnect" in types:
                        log = f'{indent}{logger_var}.debug("websocket_disconnect", error=str({var}))'
                    else:
                        log = f'{indent}{logger_var}.exception("{event}", error=str({var}))'

                    first = h.body[0] if h.body else None
                    if first is not None and isinstance(first, ast.Pass):
                        edits.append((first.lineno, "replace", first.lineno, log))
                    else:
                        insert_at = (first.lineno if first else h.lineno + 1)
                        edits.append((insert_at, "insert", insert_at, log))
                    patch_count += 1
                # recurse into try/except/else/finally bodies
                for sub in (child.body + child.orelse + child.finalbody):
                    visit(sub, func_name)
            else:
                visit(child, func_name)

    visit(tree, None)

    if patch_count == 0 and not add_logger:
        return 0

    # group edits by type; apply bottom-to-top to keep line numbers valid
    # replace edits
    replace_edits = sorted([e for e in edits if e[1] == "replace"], key=lambda x: x[2], reverse=True)
    insert_edits = sorted([e for e in edits if e[1] == "insert"], key=lambda x: x[2], reverse=True)

    for _k, _kind, lineno, newtext in replace_edits:
        lines[lineno - 1] = newtext
    for _k, _kind, lineno, newtext in insert_edits:
        lines.insert(lineno - 1, newtext)

    # add module-level logger if needed, always at the TOP of the module
    # (after any module docstring and any `from __future__ import ...`), at
    # column 0. Inserting next to the last import is unsafe because multi-line
    # parenthesized imports and try blocks would swallow the statement.
    if add_logger:
        ins = _top_insert_line(tree)  # 1-indexed line AFTER which to insert
        idx = ins  # 0-indexed insertion point
        if need_structlog:
            lines.insert(idx, "logger = structlog.get_logger(__name__)")
            lines.insert(idx, "import structlog")
        else:
            lines.insert(idx, "logger = structlog.get_logger(__name__)")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return patch_count


def rewrite_except(line, var):
    m = re.match(r'^(\s*)except\b(.*?)(\s+as\s+\w+)?(\s*):(.*)$', line)
    if not m:
        return line
    ind, rest, aspart, colon, tail = m.groups()
    if aspart:
        return line
    rest_stripped = rest.strip()
    if rest_stripped == "":
        return f"{ind}except Exception as {var}:{tail}"
    return f"{ind}except{rest} as {var}:{tail}"


def body_indent(lines, h):
    if h.body:
        fl = lines[h.body[0].lineno - 1]
        return fl[:len(fl) - len(fl.lstrip())]
    # fall back to except-line indent + 4
    el = lines[h.lineno - 1]
    base = el[:len(el) - len(el.lstrip())]
    return base + "    "


def main():
    files = collect_files()
    total = 0
    changed = 0
    for p in files:
        try:
            n = fix_file(p)
        except Exception as e:
            print(f"ERROR {p}: {e}")
            n = 0
        if n:
            changed += 1
            total += n
            print(f"patched {n:3d}  {os.path.relpath(p, ROOT)}")
    print(f"\nTOTAL: {total} handlers patched across {changed} files.")


if __name__ == "__main__":
    main()
