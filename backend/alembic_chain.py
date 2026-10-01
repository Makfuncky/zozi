import os
import re

versions_dir = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\alembic\versions"
revisions = []
for f in sorted(os.listdir(versions_dir)):
    if f.endswith(".py") and not f.startswith("__"):
        path = os.path.join(versions_dir, f)
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()[:40]
        rev = None
        down = None
        doc = ""
        for line in lines:
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            # Match revision field - must be exact field assignment
            if line.startswith("revision") and "revision" in line and "down_revision" not in line:
                m = re.search(r"['\"]([^'\"]+)['\"]", line)
                if m and rev is None:
                    rev = m.group(1)
            # Match down_revision field
            if line.startswith("down_revision"):
                m = re.search(r"['\"]([^'\"]+)['\"]", line)
                if m and down is None:
                    down = m.group(1)
                elif "None" in line and down is None:
                    down = None
        # Extract docstring from first 15 lines
        content = "".join(lines[:15])
        doc_match = re.search(r'"""(.+?)"""', content, re.DOTALL)
        if doc_match:
            doc = doc_match.group(1).strip().split("\n")[0][:80]
        revisions.append((rev, down, doc))

# Print chain
for rev, down, doc in revisions:
    print(f"{rev} <- {down} | {doc}")
