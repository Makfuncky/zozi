"""
Surgical fixup for the 7 files broken by align_error_handling.py's module-level
logger injection. The original injector placed `import structlog` /
`logger = structlog.get_logger(__name__)` at the end of the last top-level
import, which landed inside multi-line parenthesized imports or try blocks.

This script removes the misplaced injected lines and re-inserts them at the
correct top-level position (after the module docstring and any
`from __future__ import ...`), at column 0.
"""
import ast

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"

FILES = [
    r"controllers\admin\users.py",
    r"controllers\disputes_controller.py",
    r"controllers\logistics_controller.py",
    r"controllers\returns_controller.py",
    r"services\import_service.py",
    r"services\onboarding_pipeline.py",
    r"controllers\commission_controller.py",
]


def top_insert_line(tree):
    """1-indexed line AFTER which to insert (after docstring + __future__)."""
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


def main():
    for rel in FILES:
        path = ROOT + "\\" + rel
        with open(path, encoding="utf-8") as f:
            src = f.read()
        lines = src.split("\n")
        cleaned = []
        removed = 0
        for ln in lines:
            s = ln.strip()
            if s in ("import structlog", "logger = structlog.get_logger(__name__)"):
                removed += 1
                continue
            cleaned.append(ln)
        tree = ast.parse("\n".join(cleaned))
        ins = top_insert_line(tree)  # 1-indexed
        idx = ins  # 0-indexed insertion point (after line `ins`)
        # insert logger first, then import at the same index so that `import
        # structlog` ends up BEFORE the logger assignment (correct runtime order)
        cleaned.insert(idx, "logger = structlog.get_logger(__name__)")
        cleaned.insert(idx, "import structlog")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(cleaned))
        print(f"fixed {rel} (removed {removed} injected lines, reinserted at top)")


if __name__ == "__main__":
    main()
