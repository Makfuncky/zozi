import pathlib

f = pathlib.Path("backend/controllers/supplier/supplier_controller.py")
lines = f.read_text(encoding="utf-8").splitlines(keepends=True)

# Remove the orphaned badge constants block (now dead after dedupe).
# Matches from the section comment through the last constant assignment.
start = None
end = None
for i, ln in enumerate(lines):
    if ln.strip().startswith("#") and "Credibility Badge" in ln:
        start = i
    if "_BADGE_AMOUNT_QUANT = Decimal" in ln:
        end = i
        break
if start is None or end is None:
    raise SystemExit("orphan block not found")
# include the trailing newline lines until next non-empty region; keep one blank line
j = end + 1
while j < len(lines) and lines[j].strip() == "":
    j += 1
del lines[start:j]
f.write_text("".join(lines), encoding="utf-8")
print("removed lines", start, "..", j - 1, "; new count", len(lines))
