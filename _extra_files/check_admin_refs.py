"""Final gate before deleting controllers/admin/: find every reference."""
import glob
import re

PATTERNS = [
    r"from controllers\.admin(?:\.|\s| import|_controller)",
    r"import controllers\.admin",
    r"controllers\.admin\.",
    r"controllers/admin",
]

hits = []
for path in glob.glob("backend/**/*.py", recursive=True):
    if "__pycache__" in path or "venv" in path:
        continue
    src = open(path, encoding="utf-8", errors="ignore").read()
    for pat in PATTERNS:
        for m in re.finditer(pat, src):
            line = src.count("\n", 0, m.start()) + 1
            hits.append((path, line, m.group(0)))

for p, line, text in hits:
    print(f"{p}:{line}: {text}")
print(f"total references: {len(hits)}")
