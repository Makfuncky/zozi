"""Repair indentation of calculate_confidence_score in confidence_scoring.py.

The earlier edit added `try:` / `finally:` but left the function body at the
pre-try indentation. Strategy: add 4 spaces to every line between the
`if not rest_data:` line (exclusive) and the `finally:` line (exclusive), so
the `if` body, scoring logic, and final return all sit inside the `try:`.
"""

import io

path = "services/country/confidence_scoring.py"
src = io.open(path, encoding="utf-8", newline="").read()
lines = src.split("\n")

try_idx = None
if_idx = None
fin_idx = None
for i, ln in enumerate(lines):
    if ln.strip() == "try:":
        try_idx = i
    elif ln.strip().startswith("if not rest_data:"):
        if_idx = i
    elif ln.strip() == "finally:":
        fin_idx = i

assert try_idx is not None, "try: not found"
assert if_idx is not None, "if not rest_data: not found"
assert fin_idx is not None, "finally: not found"
assert try_idx < if_idx < fin_idx, f"unexpected order {try_idx} < {if_idx} < {fin_idx}"

out = lines[:]
for i in range(if_idx + 1, fin_idx):
    ln = lines[i]
    if ln.strip() == "":
        out[i] = "    "  # whitespace-only line inside try
    else:
        out[i] = "    " + ln

# sanity: recompile
new_src = "\n".join(out)
compile(new_src, path, "exec")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(new_src)
print(f"OK: re-indented {fin_idx - if_idx - 1} lines; file compiles")
