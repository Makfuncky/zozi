"""Analyze backend services files and report validity stats."""
from pathlib import Path
import re

ROOT = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\services")
files = sorted(
    p for p in ROOT.rglob("*.py")
    if "__pycache__" not in p.parts and p.name != "__init__.py"
)

empty = []
has_logic = []
re_export = []
stub_only = []

for p in files:
    rel = p.relative_to(ROOT).as_posix()
    text = p.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    if not lines or all(l.strip() == "" for l in lines):
        empty.append(rel)
        continue

    # Find substantive code lines: class/def/async def bodies (not just one-line pass)
    has_class = any(re.match(r"\s*class\s+\w+", l) for l in lines)
    # Match def or async def
    has_func = any(re.match(r"\s*(async\s+)?def\s+\w+", l) for l in lines)
    # Non-import, non-docstring, non-comment, non-blank lines that aren't just pass
    code_lines = [
        l for l in lines
        if l.strip()
        and not l.strip().startswith("#")
        and not l.strip().startswith('"""')
        and not l.strip().startswith("'''")
        and not l.strip() == "pass"
        and not re.match(r"\s*import\s+", l)
        and not re.match(r"\s*from\s+", l)
    ]

    if has_class or has_func:
        has_logic.append(rel)
    elif not code_lines:
        # Only imports, docstrings, comments, blank lines
        re_export.append(rel)
    else:
        stub_only.append(rel)

print(f"Total service files (excl __init__ + __pycache__): {len(files)}")
print(f"Empty (0 bytes or blank): {len(empty)}")
print(f"Has actual logic (class/func bodies): {len(has_logic)}")
print(f"Re-export/alias only (no logic, no code): {len(re_export)}")
print(f"Stub (code lines but no class/func): {len(stub_only)}")
print()
print(f"Valid services (has logic): {len(has_logic)}")
print()
print("--- EMPTY ---")
for r in empty:
    print(r)
print()
print("--- RE-EXPORT / ALIAS ---")
for r in re_export:
    print(r)
print()
print("--- STUB (code but no class/func) ---")
for r in stub_only:
    print(r)
