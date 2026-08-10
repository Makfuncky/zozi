"""Reorder the injected ``from services.db_read import ...`` line so it always
comes AFTER any ``from __future__ import`` line (otherwise it is a SyntaxError).
Text-based: safe because the injected line is unique and self-contained.
"""
import pathlib

BACKEND = pathlib.Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
LAYER_DIRS = (BACKEND / "routers", BACKEND / "controllers", BACKEND / "middleware")
IMPORT_PREFIX = "from services.db_read import"

fixed = 0
for layer in LAYER_DIRS:
    if not layer.exists():
        continue
    for path in sorted(layer.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        db_read_lines = [(i, ln) for i, ln in enumerate(lines) if ln.strip().startswith(IMPORT_PREFIX)]
        if not db_read_lines:
            continue
        future_idx = -1
        for i, ln in enumerate(lines):
            if ln.strip().startswith("from __future__ import"):
                future_idx = i
        # remove injected lines
        keep = [ln for i, ln in enumerate(lines) if i not in {idx for idx, _ in db_read_lines}]
        injected = [ln.strip() for _, ln in db_read_lines]
        insert_at = future_idx + 1
        new_lines = keep[:insert_at] + injected + keep[insert_at:]
        path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        fixed += 1
        print(f"reordered {path.relative_to(BACKEND)}")
print(f"\nfixed={fixed}")
