import os, re, glob

HR_SERVICES = os.path.join(os.path.dirname(__file__), "..", "backend", "services", "hr")
HR_SERVICES = os.path.abspath(HR_SERVICES)

added = 0
skipped = 0
for path in glob.glob(os.path.join(HR_SERVICES, "*.py")):
    base = os.path.basename(path)
    if base == "__init__.py":
        continue
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    if "getLogger" in src:
        skipped += 1
        continue
    lines = src.splitlines()
    # Find insertion index: after `from __future__ import annotations` if present
    insert_at = 0
    for i, ln in enumerate(lines):
        if ln.startswith("from __future__"):
            insert_at = i + 1
            break
    else:
        # place after a leading module docstring (first line a string)
        if lines and (lines[0].startswith('"""') or lines[0].startswith("'''")):
            insert_at = 1
    block = ["import logging", "logger = logging.getLogger(__name__)", ""]
    new_lines = lines[:insert_at] + block + lines[insert_at:]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))
    added += 1

print(f"OB101 enhancement: added logger to {added} HR service files, skipped {skipped} (already had logger)")
