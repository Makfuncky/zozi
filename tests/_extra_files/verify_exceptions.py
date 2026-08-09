"""Independent verifier for ERROR-HANDLING findings (HL301/302/303).

Re-parses backend code with the `ast` module and classifies every except
handler by what its body actually does. This is independent of the audit
runner in scripts/ (which we must NOT modify) and lets us separate genuine
silent failures from heuristic false positives.

Classification for each handler:
  HL301  -> bare `except:` (no type)
  empty  -> body is empty or `pass`-only with no other statements
  log    -> contains a call whose dotted name contains "log" (logger.error, ...)
  trace  -> contains `traceback` reference (traceback.format_exc, logging exc_info)
  reraise-> contains a bare or explicit `raise`
  return -> contains `return`
  control-> contains `continue`/`break`
  fallback-> contains an assignment or `.get(...)` style fallback (best-effort)
  other  -> none of the above (genuinely suspicious: swallows silently)

A handler is considered "genuinely silent" if it has empty body OR
(other and not log and not trace and not reraise and not return and not control)
-- i.e. it catches but does nothing observable.
"""
import ast
import os
import sys

BACKEND = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
SKIP_DIRS = {"venv", "__pycache__", ".git", "node_modules"}


def dotted_name(node):
    if isinstance(node, ast.Attribute):
        return dotted_name(node.value) + "." + node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def has_log_call(tree):
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            fn = n.func
            if isinstance(fn, (ast.Attribute, ast.Name)):
                name = dotted_name(fn).lower()
                if "log" in name:
                    return True
    return False


def has_traceback(tree):
    for n in ast.walk(tree):
        if isinstance(n, (ast.Attribute, ast.Name)):
            if "traceback" in n.id if isinstance(n, ast.Name) else "traceback" in n.attr:
                return True
    return False


def handler_flags(body):
    """Return set of flags describing what an except-handler body does."""
    flags = set()
    body_tree = ast.Module(body=body, type_ignores=[])
    if has_log_call(body_tree):
        flags.add("log")
    if has_traceback(body_tree):
        flags.add("trace")
    for n in ast.walk(body_tree):
        if isinstance(n, ast.Raise):
            flags.add("reraise")
        if isinstance(n, ast.Return):
            flags.add("return")
        if isinstance(n, (ast.Continue, ast.Break)):
            flags.add("control")
        if isinstance(n, (ast.Assign, ast.AugAssign)):
            flags.add("assign")
    return flags


def body_source(src_lines, handler):
    start = handler.lineno - 1
    end = handler.body[-1].lineno if handler.body else handler.lineno
    return " | ".join(l.strip() for l in src_lines[start:end])


def analyze_file(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        src = f.read()
    src_lines = src.splitlines()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    results = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        for handler in node.handlers:
            flags = handler_flags(handler.body)
            bare = handler.type is None
            empty = len(handler.body) == 0 or (
                len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass)
            )
            ex_type = "bare" if bare else dotted_name(handler.type)
            # detect a Call to any helper (best-effort) -> "doing something"
            has_call = any(isinstance(n, ast.Call) for n in ast.walk(
                ast.Module(body=handler.body, type_ignores=[])))
            genuine_silent = empty or (
                "log" not in flags
                and "trace" not in flags
                and "reraise" not in flags
                and "return" not in flags
                and "control" not in flags
                and "assign" not in flags
                and not has_call
            )
            results.append({
                "path": path,
                "lineno": handler.lineno,
                "ex_type": ex_type,
                "flags": flags,
                "bare": bare,
                "empty": empty,
                "has_call": has_call,
                "genuine_silent": genuine_silent,
                "src": body_source(src_lines, handler),
            })
    return results


def main():
    all_results = []
    for root, dirs, files in os.walk(BACKEND):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            if fn.endswith(".py"):
                full = os.path.join(root, fn)
                all_results.extend(analyze_file(full))

    bare = [r for r in all_results if r["bare"]]
    genuine = [r for r in all_results if r["genuine_silent"] and not r["bare"]]
    by_ex = {}
    for r in all_results:
        by_ex.setdefault(r["ex_type"], 0)
        by_ex[r["ex_type"]] += 1

    print("TOTAL except handlers:", len(all_results))
    print("HL301 bare except:", len(bare))
    print("Genuine silent (non-bare, non-handled):", len(genuine))
    print("\nException-type histogram (top):")
    for k, v in sorted(by_ex.items(), key=lambda x: -x[1])[:25]:
        print(f"  {k}: {v}")

    rel = lambda p: os.path.relpath(p, BACKEND)
    if bare:
        print("\n=== BARE EXCEPT (HL301) ===")
        for r in bare:
            print(f"  {rel(r['path'])}:{r['lineno']}")
    if genuine:
        print("\n=== GENUINE SILENT (HL302/303 real) ===")
        for r in genuine:
            print(f"  {rel(r['path'])}:{r['lineno']}  except {r['ex_type']}  flags={sorted(r['flags'])}  call={r['has_call']}")
            print(f"      body: {r['src'][:160]}")

    # Save full list for review
    out = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\tests\_extra_files\except_handlers.txt"
    with open(out, "w", encoding="utf-8") as f:
        for r in all_results:
            tag = "BARE" if r["bare"] else ("SILENT" if r["genuine_silent"] else "ok")
            f.write(f"{tag}\t{rel(r['path'])}:{r['lineno']}\texcept {r['ex_type']}\t{sorted(r['flags'])}\tcall={r['has_call']}\t{r['src'][:120]}\n")
    print("\nWrote full handler list to", out)


if __name__ == "__main__":
    main()
