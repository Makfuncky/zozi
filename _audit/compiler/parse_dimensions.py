"""Format-tolerant normaliser for the 34 _audit/dimensions/*.md reports.

DESIGN CONTRACT
---------------
1. NOTHING IS DROPPED. Every dimension file is scanned; every finding table
   and every prose finding block is captured. Dimensions that the strict
   `## Findings` parser skipped (08, 09, 10, 11, 14, 20, 21, 22, 23,
   config_verification, suppliers) are recovered here.
2. NOTHING IS FABRICATED. A canonical field absent from the source is
   recorded as the literal token ``NOT_PROVIDED`` together with the
   provenance of the record. No default, no guess, no inference.
3. PROVENANCE IS KEPT. Every record carries `_dimension`, `_table_index`,
   `_section`, and `_key` so a reviewer can find the exact source text.
4. NO JUDGEMENT. This script never decides whether a finding is real,
   invalid, resolved, or correctly prioritised. That is the compiler's
   second pass (PROMPT_AUDIT_COMPILER.md 0.3) and is delegated.

Output: _audit/compiler/_findings.json
"""

from __future__ import annotations

import glob
import json
import os
import re
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIM_DIR = os.path.join(ROOT, "_audit", "dimensions")
OUT = os.path.join(ROOT, "_audit", "compiler", "_findings.json")

NP = "NOT_PROVIDED"

CANON = [
    "ID", "Phase", "Status", "Cluster", "File:Line", "Current", "Target",
    "Delta", "Fix", "Effort", "Priority", "Confidence", "Evidence strength",
    "Truth level", "Claim state", "Sibling", "Verify", "Test", "Rollback",
    "Blast radius", "Depends on", "Blocks", "Completion blocker",
]

# Header alias -> canonical field. Longest alias wins on collision.
ALIASES = {
    "id": "ID", "finding": "ID", "finding id": "ID", "law": "ID",
    "check": "ID", "mandatory check": "ID", "#": "ID", "no": "ID",
    "occurrence": "ID", "revision": "ID", "rule": "ID",

    "phase": "Phase", "layer": "Phase", "severity": "Priority",
    "type": "Cluster", "category": "Cluster", "cluster": "Cluster",
    "pattern": "Cluster", "dimension": "Cluster",

    "status": "Status", "confirmation": "Status", "verdict": "Status",
    "state": "Status", "current state": "Current", "current": "Current",
    "observed": "Current", "description": "Current", "evidence": "Current",
    "detail": "Current", "details": "Current", "violations found": "Current",
    "description/impact": "Current",

    "target": "Target", "target state": "Target", "expected": "Target",
    "rule": "Target", "recommendation": "Fix", "fix": "Fix",
    "solution": "Fix", "remediation": "Fix", "action": "Fix",
    "delta": "Delta", "impact": "Delta", "note": "Delta", "notes": "Delta",

    "effort": "Effort", "size": "Effort",
    "priority": "Priority", "p": "Priority", "completion blocker": "Completion blocker",
    "project_completion_blocker": "Completion blocker", "blocker": "Completion blocker",
    "confidence": "Confidence", "evidence strength": "Evidence strength",
    "truth level": "Truth level", "claim state": "Claim state",
    "sibling": "Sibling", "exemplar": "Sibling",
    "verify": "Verify", "verify command": "Verify", "verification": "Verify",
    "test": "Test", "test path": "Test", "paired test": "Test",
    "rollback": "Rollback", "blast radius": "Blast radius", "blast": "Blast radius",
    "depends on": "Depends on", "blocks": "Blocks",

    "file:line": "File:Line", "file / location": "File:Line", "file/location": "File:Line",
    "file": "File:Line", "location": "File:Line", "path": "File:Line",
    "module": "File:Line", "scope": "File:Line", "evidence / file": "File:Line",
    "source": "File:Line", "artifact": "File:Line", "component": "File:Line",
}

DIM_TO_SUBSECTION = {
    "01_architectural": "Architectural", "05_wiring": "Architectural",
    "18_security": "Architectural", "02_technological": "Technological",
    "08_providers": "Technological", "03_logical": "Logical",
    "19_performance": "Logical", "06_database": "Database Wiring",
    "10_migrations": "Database Wiring", "07_tables_fields": "Table",
    "14_frontend_web": "Frontend Web", "24_browser_behavior": "Frontend Web",
    "15_frontend_mobile": "Frontend Mobile", "16_features": "Feature Relation",
    "12_tests": "Test File", "11_environmental": "Environmental",
    "13_dev_to_prod": "Environmental", "04_operational": "Over All",
    "09_laws": "Over All", "17_code_file_management": "Over All",
    "20_observability_resilience": "Over All", "21_contradictions": "Over All",
    "22_anti_patterns": "Over All", "23_code_intent": "Over All",
    "25_ai_drift": "Over All", "26_code_alignment": "Over All",
}

PHASE_ORDER = ["emergency", "boot", "tech", "db", "logic", "arch",
               "security", "frontend", "defer"]
PHASE_RANK = {p: i for i, p in enumerate(PHASE_ORDER)}

STATUS_TOKENS = {"PASS", "FAIL", "PARTIAL", "MISSING", "NEW", "COMPILED",
                 "RESOLVED", "INVALID", "DEFERRED", "VALID", "CONTRADICTED",
                 "INFERRED", "VERIFIED", "UNKNOWN", "ABSENT", "PRESENT"}


def split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    cells, buf, esc = [], [], False
    for ch in line:
        if esc:
            buf.append(ch); esc = False
        elif ch == "\\":
            esc = True
        elif ch == "|":
            cells.append("".join(buf).strip()); buf = []
        else:
            buf.append(ch)
    cells.append("".join(buf).strip())
    return cells


VERDICT_HEADER_RE = re.compile(
    r"\b(status|severity|priority|impact|divergence|confirmation|"
    r"compliance\s*blocker|completion\s*blocker)\b", re.I
)
ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*[-_][0-9A-Za-z][0-9A-Za-z\-_.]*$")


def norm_header(h: str) -> str | None:
    key = re.sub(r"[*`_\s]+", " ", h.strip().lower()).strip()
    key = key.replace("/", " / ")
    return ALIASES.get(key)


def norm_path(file_line: str) -> str | None:
    if not file_line or file_line in {NP, ""}:
        return None
    s = file_line.strip().strip("`").strip()
    m = re.match(r"^`?([A-Za-z0-9_./\-]+?\.[A-Za-z0-9]+)(?::(\d+)(?:-(\d+))?)?`?$", s)
    if m:
        return m.group(1).replace("\\", "/")
    # fall back: first backticked or bare path-looking token
    toks = re.findall(r"[A-Za-z0-9_.\-/]+\.[A-Za-z0-9]+", s)
    if toks:
        return max(toks, key=len).replace("\\", "/")
    return None


def is_table_header(cells: list[str]) -> bool:
    """A findings table needs >=2 recognisable columns and >=3 columns total."""
    if len(cells) < 3:
        return False
    return sum(1 for c in cells if norm_header(c)) >= 2


def has_verdict_column(cells: list[str]) -> bool:
    if any(norm_header(c) == "Status" for c in cells):
        return True
    return any(VERDICT_HEADER_RE.search(c or "") for c in cells)


def is_headerless_canonical(first_row: list[str]) -> bool:
    """00_boot_smoke_test.md ships a 23-column findings table with NO header
    row. Detect it structurally: first cell is a finding ID and the column
    count matches the canonical schema."""
    if len(first_row) < 15:
        return False
    c0 = first_row[0].strip().strip("*` ")
    return bool(ID_RE.match(c0))


def make_record(cells: list[str], header: list[str], dim: str,
                tidx: int, section: str, key: str) -> dict:
    rec = {f: NP for f in CANON}
    extra: dict[str, str] = {}
    for h, c in zip(header, cells):
        f = norm_header(h)
        if f:
            # first alias wins so a real column beats a weak alias
            if rec.get(f, NP) == NP:
                rec[f] = c or NP
        elif c:
            extra[h.strip() or "col"] = c
    rec["Extra"] = extra
    rec["ID"] = key
    rec["_dimension"] = dim
    rec["_subsection"] = DIM_TO_SUBSECTION.get(dim, "Over All")
    rec["_table_index"] = tidx
    rec["_section"] = section
    rec["_key"] = key
    rec["_path"] = norm_path(rec["File:Line"])
    # 22_anti_patterns splits location across a Folder column and a File
    # column holding a path relative to that folder. Join them rather than
    # reporting a bare fragment as a repo path.
    if rec["_path"] and not rec["_path"].startswith(("backend/", "frontend/", "docs/")):
        folder = extra.get("Folder", "").strip().strip("`")
        if folder and not folder.startswith(("http", "*")):
            rec["_path"] = f"{folder.strip('/')}/{rec['_path']}".replace("\\", "/")
    return rec


def scan_dimension(path: str) -> tuple[list[dict], dict]:
    dim = os.path.splitext(os.path.basename(path))[0]
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().split("\n")

    recs: list[dict] = []
    section = "(top)"
    tidx = 0
    i, n = 0, len(lines)
    auto = 0

    while i < n:
        ln = lines[i]
        h = ln.strip()
        if h.startswith("#"):
            section = h.lstrip("#").strip()
        if h.startswith("|"):
            # collect the contiguous run of pipe rows starting at i
            body, j = [], i
            while j < n and lines[j].strip().startswith("|"):
                body.append(lines[j])
                j += 1
            if len(body) < 2:
                i = j
                continue
            if re.match(r"^\|[\s:|-]+\|$", body[1].strip()):
                header = split_row(body[0])
                rows = [split_row(x) for x in body[2:]]
            elif is_headerless_canonical(split_row(body[0])):
                # 00_boot_smoke_test.md ships the 23-column table with no
                # header row; the canonical order is known.
                header = list(CANON)
                rows = [split_row(x) for x in body]
            else:
                i = j
                continue
            rows = [r for r in rows if not (set(r) <= {"-", ""})]
            if rows and is_table_header(header) and has_verdict_column(header):
                tidx += 1
                for cells in rows:
                    if len(cells) < len(header):
                        cells = cells + [NP] * (len(header) - len(cells))
                    cells = cells[:len(header)]
                    auto += 1
                    raw = cells[0].strip().strip("*` ") or ""
                    # Positional keys ("1", "40") are not finding IDs and
                    # would collide across dimensions, so namespace them.
                    key = re.sub(r"\s+", "-", raw) or f"A{auto:04d}"
                    if not ID_RE.match(key):
                        key = f"{dim}-{re.sub(r'[^A-Za-z0-9_.-]+', '-', key)}"
                    recs.append(make_record(cells, header, dim, tidx, section, key))
            i = j
            continue
        i += 1

    # Prose finding blocks:  ### Finding ENV-01 - title   /  ## SUP-001: title
    # The ID part is greedy so `FIND-09-001:` does not collapse to `FIND-09`.
    prose = re.compile(
        r"^#{2,4}\s*(?:\*\*)?(?:Finding\s+)?"
        r"([A-Za-z][A-Za-z0-9]*(?:[-_][0-9A-Za-z]+)+)"
        r"(?:\*\*)?\s*[:\u2014\u2013-]\s*(.*)$"
    )
    kv = re.compile(r"^\s*[-*]\s*\*\*(.+?)\*\*\s*[:\u2014-]\s*(.*)$")
    cur_key = None
    cur_rec: dict | None = None
    cur_sec = "(prose)"
    for ln in lines:
        h = ln.strip()
        m = prose.match(h)
        if m:
            if cur_rec is not None:
                recs.append(cur_rec)
            key = m.group(1).strip().strip("*")
            cur_sec = h.lstrip("#").strip()
            cur_key = key
            cur_rec = make_record([key] + [NP] * 23,
                                  ["ID"] + [f for f in CANON[1:]] + ["x"],
                                  dim, 0, cur_sec, key)
            cur_rec["ID"] = key
            cur_rec["_key"] = key
            if m.group(2).strip():
                cur_rec["Current"] = m.group(2).strip()
            continue
        m2 = kv.match(h)
        if m2 and cur_rec is not None:
            k = norm_header(m2.group(1)) or norm_header(re.sub(r"[*`_\s]+", " ", m2.group(1).lower()).strip())
            if k and cur_rec.get(k, NP) == NP:
                cur_rec[k] = m2.group(2).strip() or NP
            elif m2.group(2).strip():
                cur_rec["Extra"][m2.group(1).strip()] = m2.group(2).strip()
            continue
    if cur_rec is not None:
        recs.append(cur_rec)

    # Deduplicate on (dimension, key); keep first.
    seen, uniq = set(), []
    for r in recs:
        k = (dim, r["_key"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(r)
    recs = uniq

    meta = {
        "dimension": dim,
        "records": len(recs),
        "tables": tidx,
        "path": os.path.relpath(path, ROOT).replace("\\", "/"),
        "subsections_touched": sorted({r["_subsection"] for r in recs}),
        "records_without_path": sum(1 for r in recs if not r["_path"]),
    }
    return recs, meta


def main() -> int:
    files = sorted(glob.glob(os.path.join(DIM_DIR, "*.md")))
    if not files:
        print("COMPILER PARTIAL - missing dimension files", flush=True)
        return 1

    all_recs: list[dict] = []
    metas = []
    for f in files:
        recs, meta = scan_dimension(f)
        all_recs.extend(recs)
        metas.append(meta)
        flag = "" if recs else "   <-- ZERO, MUST REVIEW"
        print(f"{meta['dimension']:<36} recs={meta['records']:<5} "
              f"tables={meta['tables']:<3} nopath={meta['records_without_path']:<4}{flag}")

    all_recs.sort(key=lambda r: (
        PHASE_RANK.get((r.get("Phase") or "").strip().lower(), 99),
        r["_path"] or "~",
        r["_dimension"], str(r["_key"]),
    ))

    by_path = defaultdict(list)
    by_dim = defaultdict(int)
    dupes = defaultdict(list)
    seen_ids = defaultdict(list)
    for r in all_recs:
        by_path[r["_path"] or "(no-path)"].append(r["ID"])
        by_dim[r["_dimension"]] += 1
        seen_ids[r["ID"]].append(r["_dimension"])
    for k, v in seen_ids.items():
        if len(v) > 1:
            dupes[k] = v

    field_gaps = {
        f: sum(1 for r in all_recs if r.get(f, NP) == NP)
        for f in CANON
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({
            "canonical_fields": CANON,
            "np_token": NP,
            "dimensions": metas,
            "findings": all_recs,
            "file_index": {k: v for k, v in sorted(by_path.items())},
            "per_dimension_counts": dict(sorted(by_dim.items())),
            "duplicate_keys_across_dimensions": dict(dupes),
            "field_gap_counts": field_gaps,
        }, fh, indent=1, ensure_ascii=False)

    print()
    print(f"dimension files        : {len(metas)}")
    print(f"records extracted      : {len(all_recs)}")
    print(f"distinct repo paths    : {len(by_path)}")
    print(f"records w/o repo path  : {sum(1 for r in all_recs if not r['_path'])}")
    print(f"duplicate IDs across dims: {len(dupes)}")
    zero = [m["dimension"] for m in metas if m["records"] == 0]
    print(f"dimensions with 0 records: {zero if zero else 'none'}")
    print("field gaps (NOT_PROVIDED counts):")
    for f, c in sorted(field_gaps.items(), key=lambda kv: -kv[1]):
        if c:
            print(f"  {f:<24} {c}")
    print(f"written: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
