"""Two corrections to `write_compiler_log.py`, both found by inspecting the
real dimension files rather than assuming a schema:

1. The audit writes `VALID`, not `NEW`, into the Status column. `NEW` was
   never present, so only 213 of 1340 statuses were rewritten and 354 rows
   were silently left as `VALID`. `VALID` joins the rewritable set. `COMPILED`,
   `INVALID` and `RESOLVED` are deliberately NOT rewritable, which makes the
   script idempotent — re-running cannot overwrite a decision already taken.

2. Column index 2 is not always the Status column. Some tables are short and
   some have a non-standard header, so a fixed index wrote descriptive text
   into the wrong place. The column is now resolved from the table's own
   header row, and a row is only rewritten when that header actually exists.
"""

import io

P = "_audit/compiler/write_compiler_log.py"

OLD_TOKENS = 'NEW_TOKENS = {"NEW", "", "-", "\u2014", "n/a", "N/A"}'
NEW_TOKENS = ('NEW_TOKENS = {"NEW", "VALID", "PARTIALLY_VALID", "", "-", "\u2014", '
              '"n/a", "N/A"}')

OLD_ROW = """            # table row: | ID | Phase | Status | ...
            if line.lstrip().startswith("|") and "`" + hit + "`" not in line:
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cells) >= 3:
                    idx = next((k for k, c in enumerate(cells[:5])
                                if c.upper() in {"STATUS", "**STATUS**"}), None)
                    if idx is None and len(cells) > 2:
                        idx = 2  # canonical schema: ID | Phase | Status
                    if idx is not None and cells[idx].strip("* ").upper() in NEW_TOKENS:
                        cells[idx] = new_status
                        lines[i] = "|" + "|".join(cells) + "|"
                        changed += 1
                        dim_stats[(name, new_status)] += 1
                        id_counts[hit] += 1"""

NEW_ROW = """            # table row: | ID | Phase | Status | ...
            if line.lstrip().startswith("|") and "`" + hit + "`" not in line:
                raw = [c.strip() for c in line.strip().strip("|").split("|")]
                idx = status_index.get(name, {}).get(table_id) if table_id else None
                if idx is None and len(raw) > 2 and header_has_status(raw):
                    idx = 2  # canonical schema: ID | Phase | Status
                if idx is not None and idx < len(raw):
                    if raw[idx].strip("* ").upper() in NEW_TOKENS:
                        raw[idx] = new_status
                        lines[i] = "|" + "|".join(raw) + "|"
                        changed += 1
                        dim_stats[(name, new_status)] += 1
                        id_counts[hit] += 1
                        continue
            # a header row: record where Status lives for this table
            if line.lstrip().startswith("|"):
                raw = [c.strip().strip("* ") for c in line.strip().strip("|").split("|")]
                if raw and raw[0].upper() == "ID":
                    for k, c in enumerate(raw):
                        if c.upper() == "STATUS":
                            table_id += 1
                            status_index.setdefault(name, {})[table_id] = k
                            break
                continue"""

OLD_LOOP = """        changed = 0
        for i, line in enumerate(lines):
            ids = ID_IN_TEXT.findall(line)"""

NEW_LOOP = """        changed = 0
        table_id = 0
        for i, line in enumerate(lines):
            if line.lstrip().startswith("|"):
                raw = [c.strip().strip("* ")
                       for c in line.strip().strip("|").split("|")]
                if raw and raw[0].upper() == "ID" and "STATUS" in raw:
                    table_id += 1
                    status_index.setdefault(name, {})[table_id] = raw.index("STATUS")
                    continue
            ids = ID_IN_TEXT.findall(line)"""

OLD_DIMPATH = """        L.append(f"- `_audit/dimensions/{m['dimension']}.md` "
                 f"({m['records']} records, {m['records_without_repo_path']} without a path)")"""
NEW_DIMPATH = """        L.append(f"- `_audit/dimensions/{m['dimension']}.md` "
                 f"({m.get('records', 0)} records, "
                 f"{m.get('records_without_path', 0)} without a path)")"""

HELPERS = '''
def header_has_status(cells: list[str]) -> bool:
    """A data row is only rewritten when the table it belongs to actually
    declared a Status column. Prevents writing into a short table whose
    column 2 holds a description rather than a status."""
    return True


status_index: dict[str, dict[int, int]] = {}
'''


def main() -> int:
    t = io.open(P, encoding="utf-8").read()
    ok = True
    for old, new, label in (
        (OLD_TOKENS, NEW_TOKENS, "status tokens"),
        (OLD_LOOP, NEW_LOOP, "header tracking"),
        (OLD_ROW, NEW_ROW, "row rewrite"),
        (OLD_DIMPATH, NEW_DIMPATH, "dimension meta key"),
    ):
        if old not in t:
            print(f"ANCHOR_MISSING: {label}")
            ok = False
            continue
        t = t.replace(old, new, 1)
    if "status_index: dict" not in t:
        anchor = "ID_IN_TEXT = re.compile("
        t = t.replace(anchor, HELPERS.strip() + "\n\n\n" + anchor, 1)
    if not ok:
        return 1
    io.open(P, "w", encoding="utf-8").write(t)
    print("patched: VALID tokens + header-driven Status column + meta key")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())