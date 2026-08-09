"""Repair the API2 renamer regression: it replaced the `def`/`class` keyword
with the new public name. This restores `def <old>(` for every corrupted
function-definition line in the previously-broken files.
"""
import re

files = [l.strip() for l in open(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\bad_files.txt", encoding="utf-8") if l.strip()]
pat = re.compile(r"^(\s*)([A-Za-z_]\w*)\s+(_[A-Za-z_]\w*)\s*([\(:])")

fixed = 0
for fn in files:
    try:
        lines = open(fn, encoding="utf-8").read().splitlines(keepends=True)
    except FileNotFoundError:
        print("MISSING", fn)
        continue
    out = []
    for ln in lines:
        m = pat.match(ln)
        if m and m.group(2) == m.group(3).lstrip("_"):
            # The renamer replaced the `def` keyword with the PUBLIC name
            # (group 2) and left the stale private name (group 3). Restore to
            # `def <public>` so it matches the already-renamed references.
            out.append(pat.sub(r"\1def \2\4", ln, count=1))
            fixed += 1
        else:
            out.append(ln)
    open(fn, "w", encoding="utf-8").write("".join(out))
print("Lines repaired:", fixed)
