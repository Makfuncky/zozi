"""Scan alembic migration files and map the dependency chain."""
import pathlib, re

versions = pathlib.Path("alembic/versions")
for f in sorted(versions.glob("*.py")):
    data = f.read_bytes()
    if b"\x00" in data:
        print(f"CORRUPT {f.name}")
        continue
    text = data.decode("utf-8", errors="replace")
    rev = re.search(r'revision\s*=\s*["\']([^"\']+)', text)
    down = re.search(r'down_revision\s*=\s*["\']([^"\']+)', text)
    down2 = re.search(r'down_revision\s*=\s*\(([^)]+)\)', text)
    r = rev.group(1) if rev else "?"
    if down:
        d = down.group(1)
    elif down2:
        d = down2.group(1)
    else:
        d = "None"
    print(f"{r} <- {d}  ({f.name})")

