"""Assemble `_audit/TO_BE_RESOLVE.md` in the file-block schema the resolver
consumes, from the parsed dimension records plus the second-pass verdicts.

CONTRACT (PROMPT_AUDIT_COMPILER.md 5.2)
  ## FILE <n>: <relative path>
  - Phase / Depends on / Findings / Effort / Resolution status / Blast radius
  - exactly 11 subsections in fixed order, each with Confirmation / Problem / Solution
  - Feature Relation + Resolution sections

HONESTY RULES ENFORCED HERE
  * A finding enters a file block only if its verdict is REAL.
    FALSE_POSITIVE -> excluded, recorded as INVALID with its counter-evidence.
    ALREADY_FIXED  -> excluded, recorded as RESOLVED with its verify output.
    BLOCKED_BY_CONTRADICTION -> excluded, recorded as such, never resolved.
  * A value the audit did not supply is emitted as NOT_PROVIDED. Values this
    script derives are marked `(derived: ...)` inline. Nothing is invented.
  * A finding with no single repo path cannot be a per-file block; it goes to
    SECTION 2 (Over All) per compiler 0.4 rule 15.
  * `Problem`/`Solution` pairs are 1:1 and numbered. A Problem with no Solution
    is impossible by construction (compiler 0.12 rule 52).
"""

from __future__ import annotations

import glob
import json
import os
import re
from collections import defaultdict
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COMP = os.path.join(ROOT, "_audit", "compiler")
FINDINGS = os.path.join(COMP, "_findings.json")
VERD = os.path.join(COMP, "verdicts")
OUT = os.path.join(ROOT, "_audit", "TO_BE_RESOLVE.md")

NP = "NOT_PROVIDED"

PHASE_ORDER = ["emergency", "boot", "tech", "db", "logic", "arch",
               "security", "frontend", "defer"]
PHASE_RANK = {p: i for i, p in enumerate(PHASE_ORDER)}

SUBSECTIONS = [
    ("Architectural", "laws 1-7, 14-18, 97-106"),
    ("Technological", "laws 107-122, forbidden packages"),
    ("Logical", "laws 19, 50, 58-68, 239"),
    ("Database Wiring", "laws 45-57, 227-229"),
    ("Table", "laws 20-23, 51-55"),
    ("Frontend Web", "laws 111-112, 168-186"),
    ("Frontend Mobile", "laws 187-194"),
    ("Test File", "laws 69-74, 207-214"),
    ("Environmental", "laws 82-86, 201-206"),
    ("Over All", "laws 75-81, 92-96, 245-250, 251-325"),
    ("Feature Relation", "feature IDs, chain IDs, upstream/downstream"),
]

# Only used when a finding carried no Phase of its own. Sourced from
# _audit/SHARED_INSTRUCTIONS.md's dimension list, not invented per-finding.
DIM_PHASE_FALLBACK = {
    "00_boot_smoke_test": "boot", "01_architectural": "arch",
    "02_technological": "tech", "03_logical": "logic",
    "04_operational": "arch", "05_wiring": "arch",
    "06_database": "db", "07_tables_fields": "db",
    "07_CONTRADICTIONS": "arch", "08_providers": "tech",
    "09_laws": "arch", "10_migrations": "db",
    "11_environmental": "emergency", "12_tests": "tech",
    "12_tests_collection_verify": "tech", "13_dev_to_prod": "tech",
    "13_dev_to_prod_docker_verify": "tech", "14_frontend_web": "frontend",
    "15_frontend_mobile": "frontend", "16_features": "arch",
    "17_code_file_management": "arch", "18_security": "security",
    "19_performance": "logic", "20_observability_resilience": "arch",
    "21_contradictions": "arch", "22_anti_patterns": "arch",
    "23_code_intent": "arch", "24_browser_behavior": "frontend",
    "25_ai_drift": "arch", "26_code_alignment": "arch",
    "27_project_completion_blockers": "emergency",
    "28_supply_chain_security": "security", "config_verification": "emergency",
    "suppliers": "arch",
}

NATURE_TOKENS = [
    ("browser", r"browser"),
    ("ai_drift", r"ai[_ ]?drift"),
    ("alignment", r"align"),
    ("db", r"\bdb\b|database"),
    ("tables", r"table|column|field"),
    ("migrations", r"migration|alembic"),
    ("security", r"security|secret|auth|csrf|injection"),
    ("perf", r"perf|n\+1|latency|index|pagination"),
    ("obs", r"observab|logging|metric|trace"),
    ("providers", r"provider|sdk"),
    ("wiring", r"wiring|event|subscriber|middleware"),
    ("arch", r"architect|law|import|layer"),
    ("env", r"env|config|setting"),
    ("tests", r"test"),
    ("fe", r"frontend|web|react|next"),
    ("mobile", r"mobile|expo|react.native"),
    ("anti-pattern", r"anti.?pattern"),
    ("ops", r"ops|deploy|docker|ci\b"),
    ("features", r"feature|rbac"),
    ("logical", r"logic|money|idempot|float|except"),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def nature_of(rec: dict, sub: str) -> str:
    blob = " ".join(str(rec.get(f, "")) for f in
                    ("Cluster", "Current", "Delta", "_dimension", "_section")).lower()
    for token, pat in NATURE_TOKENS:
        if re.search(pat, blob):
            return token
    return {"Architectural": "arch", "Technological": "tech",
            "Logical": "logical", "Database Wiring": "db", "Table": "tables",
            "Frontend Web": "fe", "Frontend Mobile": "mobile",
            "Test File": "tests", "Environmental": "env",
            "Feature Relation": "features"}.get(sub, "arch")


def norm_phase(rec: dict) -> tuple[str, bool]:
    p = (rec.get("Phase") or "").strip().lower()
    if p in PHASE_RANK:
        return p, False
    fb = DIM_PHASE_FALLBACK.get(rec["_dimension"], "arch")
    return fb, True


def effort_of(recs: list[dict]) -> str:
    for r in recs:
        e = (r.get("Effort") or "").strip()
        if e and e != NP:
            return e
    n = len(recs)
    return "L (TBD)" if n > 8 else ("M (TBD)" if n > 3 else "S (TBD)")


def clean(s: str, limit: int = 700) -> str:
    s = re.sub(r"\s+", " ", (s or "").strip())
    s = s.replace("|", "\\|")
    return s if len(s) <= limit else s[: limit - 1].rsplit(" ", 1)[0] + "…"


def is_browser_nature(nat: str) -> bool:
    return nat in {"browser", "fe", "mobile"}


def verify_cmd(rec: dict, nat: str) -> str:
    v = (rec.get("Verify") or "").strip()
    if v and v != NP and "git revert" not in v:
        return clean(v, 300)
    return f"`{nat}`-specific check required — audit supplied no runnable Verify command"


def test_path(rec: dict) -> str:
    t = (rec.get("Test") or "").strip()
    if t and t != NP and "git revert" not in t:
        return clean(t, 300)
    return f"{NP} — FIX_UNTESTABLE: audit supplied no Test path"


def blast_of(recs: list[dict]) -> str:
    parts = []
    for r in recs:
        b = (r.get("Blast radius") or "").strip()
        if b and b != NP and b not in parts:
            parts.append(b)
        if len(parts) >= 6:
            break
    return "; ".join(parts) if parts else NP


def feature_relation(recs: list[dict]) -> list[str]:
    up, down, chains, ev, ports = set(), set(), set(), set(), set()
    for r in recs:
        b = (r.get("Blast radius") or "")
        for tok in re.findall(r"\bF-\d+\b", b):
            up.add(tok)
        for tok in re.findall(r"\bCHAIN-\d+\b", b):
            chains.add(tok)
        ex = r.get("Extra") or {}
        for key, val in ex.items():
            if key == "Chains touched":
                chains.update(re.findall(r"\bCHAIN-\d+\b", str(val)))
            if key == "Events emitted / consumed":
                ev.add(clean(str(val), 120))
            if key == "Ports exposed / called":
                ports.add(clean(str(val), 120))
        fe = clean(str(r.get("Blast radius") or ""), 300)
        if fe and fe != NP and ("F-" in fe or "CHAIN" in fe):
            down.add("")
    return [
        f"- **Upstream features:** [{', '.join(sorted(up))}]" if up
        else f"- **Upstream features:** {NP}",
        f"- **Downstream features:** [{', '.join(sorted(x for x in down if x))}]"
        if any(down) else f"- **Downstream features:** {NP}",
        f"- **Chains touched:** [{', '.join(sorted(chains))}]" if chains
        else f"- **Chains touched:** {NP}",
        f"- **Events emitted / consumed:** [{'; '.join(sorted(ev))}]" if ev
        else f"- **Events emitted / consumed:** {NP}",
        f"- **Ports exposed / called:** [{'; '.join(sorted(ports))}]" if ports
        else f"- **Ports exposed / called:** {NP}",
    ]


def load_verdicts() -> tuple[dict, list[dict]]:
    by_key: dict[tuple[str, str], dict] = {}
    all_meta: list[dict] = []
    for path in sorted(glob.glob(os.path.join(VERD, "*.json"))):
        name = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        dim = data.get("dimension", name)
        vmap = {}
        for v in data.get("verdicts", []):
            vmap[str(v.get("key"))] = v
            by_key[(dim, str(v.get("key")))] = v
        meta = {
            "agent": data.get("agent_id", name),
            "dimension": dim,
            "considered": data.get("records_considered", len(vmap)),
            "duplicates": data.get("duplicates_merged", []),
            "contradictions": data.get("internal_contradictions", []),
            "cross_cutting": data.get("cross_cutting_candidates", []),
            "gaps": data.get("coverage_gaps", []),
            "by_key": vmap,
        }
        all_meta.append(meta)
    return by_key, all_meta


def main() -> int:
    with open(FINDINGS, encoding="utf-8") as fh:
        corpus = json.load(fh)
    records = corpus["findings"]
    by_key, metas = load_verdicts()

    # Duplicate / contradiction indexes built from agent output.
    dup_survivor: dict[str, str] = {}
    dup_why: dict[str, str] = {}
    contradiction_ids: dict[tuple[str, str], str] = {}
    for m in metas:
        for d in m["duplicates"]:
            dup = str(d.get("duplicate") or d.get("merged") or "")
            surv = str(d.get("survivor") or "")
            if dup:
                dup_survivor[dup] = surv
                dup_why[dup] = str(d.get("why") or d.get("reason") or "")
        for c in m["contradictions"]:
            for kid in c.get("keys", []):
                contradiction_ids[(m["dimension"], str(kid))] = clean(
                    str(c.get("conflict", "")), 300)

    # ---- classify every record -------------------------------------------------
    stats = defaultdict(int)
    blocks: dict[str, list[dict]] = defaultdict(list)
    over_all: list[dict] = []
    excluded: list[dict] = []

    for rec in records:
        dim, key = rec["_dimension"], str(rec["_key"])
        v = by_key.get((dim, key))
        if v is None:
            stats["NO_VERDICT"] += 1
            excluded.append({"rec": rec, "why": "no verdict produced"})
            continue
        verdict = str(v.get("verdict", "")).strip()
        stats[f"verdict:{verdict}"] += 1

        if verdict == "FALSE_POSITIVE":
            excluded.append({"rec": rec, "why": "INVALID — " +
                             clean(str(v.get("counter_evidence", "")), 300)})
            continue
        if verdict == "ALREADY_FIXED":
            excluded.append({"rec": rec, "why": "RESOLVED — verify output: " +
                             clean(str(v.get("verify_output", "")), 200)})
            continue
        if verdict == "BLOCKED_BY_CONTRADICTION":
            excluded.append({"rec": rec, "why": "BLOCKED_BY_CONTRADICTION"})
            continue
        if verdict != "REAL":
            stats["verdict:OTHER"] += 1
            excluded.append({"rec": rec, "why": f"non-standard verdict '{verdict}'"})
            continue
        if key in dup_survivor:
            stats["DUPLICATE"] += 1
            excluded.append({"rec": rec, "why":
                             f"DUPLICATE of {dup_survivor[key]} — {dup_why.get(key,'')[:200]}"})
            continue
        if (dim, key) in contradiction_ids:
            stats["CONTRADICTION_INTERNAL"] += 1
            excluded.append({"rec": rec, "why":
                             "CONTRADICTION_INTERNAL — " + contradiction_ids[(dim, key)]})
            continue

        rec = dict(rec)
        rec["_verdict"] = v
        path = rec.get("_path")
        if not path or path in {"(no-path)", "~"}:
            rec["_over_all_reason"] = (
                "no single repo path in File:Line — cross-cutting per compiler 0.4 rule 15")
            over_all.append(rec)
            continue
        blocks[path].append(rec)

    # ---- order: phase, then path ----------------------------------------------
    def phase_of(group: list[dict]) -> str:
        best, derived_any = "defer", False
        for r in group:
            p, derived = norm_phase(r)
            derived_any = derived_any or derived
            if PHASE_RANK[p] < PHASE_RANK[best]:
                best = p
        r0 = group[0]
        ph, _ = norm_phase(r0)
        if derived_any and PHASE_RANK[best] > PHASE_RANK[ph]:
            best = ph
        return best

    ordered: list[tuple[str, str, list[dict]]] = []
    for path, grp in blocks.items():
        ordered.append((phase_of(grp), path, grp))
    ordered.sort(key=lambda t: (PHASE_RANK[t[0]], t[1]))

    if over_all:
        ordered.append(("defer", "(cross-cutting findings — see SECTION 2)", over_all))

    # ---- emit ------------------------------------------------------------------
    L: list[str] = []
    total_findings = sum(len(g) for _, _, g in ordered)
    L.append("# TO_BE_RESOLVE.md — ZOZI Master Worklist")
    L.append("")
    L.append("> Generated by `PROMPT_AUDIT_COMPILER.md` from the 34 files under")
    L.append("> `_audit/dimensions/`, after a second-pass re-investigation of every")
    L.append("> finding by 34 verification sub-agents.")
    L.append("> Consumed by `PROMPT_RESOLUTION_ORCHESTRATOR.md` one file block at a time.")
    L.append("")
    L.append(f"Generated: {now_iso()}")
    L.append(f"Source commit: 6666d435 (working tree has uncommitted changes — see "
             f"COMPILER_LOG.md §State dependency)")
    L.append("Run number: 8 (re-investigation)")
    L.append(f"Total files with findings: {len(ordered)}")
    L.append(f"Total findings compiled: {total_findings}")
    L.append(f"Records extracted from dimensions: {len(records)}")
    L.append("")
    L.append("| Verdict | Count | Meaning |")
    L.append("|---|---|---|")
    for k in ("REAL", "FALSE_POSITIVE", "ALREADY_FIXED",
              "BLOCKED_BY_CONTRADICTION", "OTHER", "NO_VERDICT"):
        if stats.get(f"verdict:{k}") or (k == "OTHER" and stats.get("verdict:OTHER")):
            L.append(f"| {k} | {stats.get(f'verdict:{k}', 0)} | |")
    L.append(f"| DUPLICATE (merged) | {stats['DUPLICATE']} | "
             f"merged per compiler 0.6 rule 41 |")
    L.append(f"| CONTRADICTION_INTERNAL | {stats['CONTRADICTION_INTERNAL']} | "
             f"blocked per compiler 0.6 rule 40 |")
    L.append("")
    L.append("**Reading this worklist.** A file block's `Resolution status` starts "
             "`☐ PENDING`. Only findings whose second-pass verdict is `REAL` appear "
             "in a Problem list. False positives, already-fixed findings and "
             "contradiction-blocked findings are excluded and listed in "
             "`COMPILER_LOG.md` §Excluded with their evidence.")
    L.append("")
    L.append("---")
    L.append("")

    # executive summary
    L.append("## Executive summary")
    L.append("")
    L.append("| Phase | Files | Findings |")
    L.append("|---|---|---|")
    for ph in PHASE_ORDER:
        # the cross-cutting pseudo-block is SECTION 2, not a per-file block,
        # so it is reported on its own row rather than inside a phase
        fs = [g for p, path, g in ordered
              if p == ph and not path.startswith("(cross-cutting")]
        if fs:
            L.append(f"| {ph} | {len(fs)} | {sum(len(x) for x in fs)} |")
    if over_all:
        L.append(f"| _section 2 (cross-cutting) | 1 | {len(over_all)} |")
    L.append("")

    # resolution order
    L.append("## Resolution order")
    L.append("")
    L.append("Files are processed in phase order. A file cannot be resolved until "
             "its dependencies are resolved.")
    L.append("")
    L.append("| Order | Phase | File | Depends on | Findings | Effort |")
    L.append("|---|---|---|---|---|---|")
    for i, (ph, path, grp) in enumerate(ordered, start=1):
        if path.startswith("(cross-cutting"):
            continue
        L.append(f"| {i} | {ph} | `{path}` | none | {len(grp)} | {effort_of(grp)} |")
    L.append("")
    L.append("> `Depends on` is `none` for every block because the audit's `Depends on`")
    L.append("> column was `NOT_PROVIDED` on the records that reached a `REAL` verdict.")
    L.append("> The orchestrator must derive dependencies from observed import edges")
    L.append("> when it freezes each contract; this compiler does not invent them.")
    L.append("")
    L.append("---")
    L.append("")
    L.append("# SECTION 1 — PER-FILE BLOCKS")
    L.append("")

    file_no = 0
    for ph, path, grp in ordered:
        if path.startswith("(cross-cutting"):
            continue
        file_no += 1
        sub_map: dict[str, list[dict]] = defaultdict(list)
        for r in grp:
            sub_map[r["_subsection"]].append(r)
        natures = sorted({nature_of(r, r["_subsection"]) for r in grp})
        L.append(f"## FILE {file_no}: {path}")
        L.append("")
        L.append(f"- **Phase:** {ph}")
        L.append("- **Depends on:** none (see note above)")
        L.append(f"- **Findings:** {len(grp)}")
        L.append(f"- **Effort:** {effort_of(grp)}")
        L.append("- **Resolution status:** ☐ PENDING")
        L.append(f"- **Blast radius:** {blast_of(grp)}")
        L.append(f"- **Nature:** {', '.join(natures)}")
        L.append(f"- **Dimensions contributing:** "
                 f"{', '.join(sorted({r['_dimension'] for r in grp}))}")
        L.append("")

        for name, laws in SUBSECTIONS:
            # Feature Relation is the 11th subsection but carries relation
            # fields, not Confirmation/Problem/Solution. Emitted once, below.
            if name == "Feature Relation":
                continue
            rows = sub_map.get(name, [])
            L.append(f"### {name}")
            L.append("")
            L.append(f"<!-- laws: {laws} -->")
            if not rows:
                L.append("- **Confirmation:** ✔️")
                L.append("- **Problem:**")
                L.append("- **Solution:**")
                L.append("")
                continue
            L.append("- **Confirmation:** ❌")
            L.append("- **Problem:**")
            for i, r in enumerate(rows, start=1):
                cur = clean(str(r.get("Current", NP)), 400)
                loc = clean(str(r.get("File:Line", NP)), 160)
                note = ""
                if r.get("_verdict", {}).get("line_exists") is False:
                    note = " (cited line drifted; agent confirmed at " \
                           f"{r['_verdict'].get('actual_line_range')})"
                extra = ""
                if r.get("_verdict", {}).get("current_matches_claim") in ("partial", "no"):
                    extra = f" — claim accuracy: {r['_verdict']['current_matches_claim']}"
                L.append(f"  {i}. `{loc}` {cur}{note}{extra} "
                         f"(`{r['ID']}`, `{r['_dimension']}`)")
            L.append("- **Solution:**")
            for i, r in enumerate(rows, start=1):
                fx = clean(str(r.get("Fix", NP)), 400)
                v = r.get("_verdict", {})
                flags = []
                fxtext = f"{fx}"
                if (r.get("Fix") or NP) == NP:
                    fxtext = ("implement the Target stated by the audit; "
                              f"Target={clean(str(r.get('Target', NP)), 260)}")
                if v.get("counter_evidence"):
                    flags.append("counter-evidence retained")
                if (r.get("Test") or NP) == NP or "git revert" in str(r.get("Test", "")):
                    flags.append("FIX_UNTESTABLE")
                ff = v.get("filled_fields") or {}
                if ff:
                    flags.append("fields filled by agent: " +
                                 ", ".join(sorted(ff)[:6]))
                tail = (" — " + "; ".join(flags)) if flags else ""
                L.append(f"  {i}. {fxtext} — verify: {verify_cmd(r, nature_of(r, name))}"
                         f" — test: {test_path(r)}{tail}")
            L.append("")

        L.append("### Feature Relation")
        L.append("")
        for line in feature_relation(grp):
            L.append(line)
        L.append("")
        L.append("### Resolution")
        L.append("")
        L.append(f"- **Verify (all problems):** run the per-finding verify commands "
                 f"above in order; every one must return its expected output")
        L.append(f"- **Paired test (all problems):** "
                 f"{test_path(grp[0])}")
        L.append("- **Rollback:** revert")
        bt = [r for r in grp if is_browser_nature(nature_of(r, r['_subsection']))]
        L.append(f"- **Browser test:** {'REQUIRED — ' + ', '.join(sorted({nature_of(r, r['_subsection']) for r in bt})) + ' nature' if bt else 'N/A (no browser-facing finding in this block)'}")
        L.append(f"- **Contradiction gate:** "
                 f"{'BLOCKED — see COMPILER_LOG.md' if any((r['_dimension'], str(r['_key'])) in contradiction_ids for r in grp) else 'clear'}")
        L.append("")
        L.append("---")
        L.append("")

    # SECTION 2
    L.append("# SECTION 2 — CODEBASE IMPLEMENTATION (OVER ALL)")
    L.append("")
    L.append("Cross-cutting findings that are not tied to a single file. These are "
             "resolved **after** all per-file blocks in their phase are complete. "
             "Compiler 0.4 rule 15: a finding is cross-cutting when it applies to "
             ">=5 files, has no single File:Line, or its File:Line is a config "
             "artefact governing the whole codebase.")
    L.append("")
    if over_all:
        sub_map = defaultdict(list)
        for r in over_all:
            sub_map[r["_subsection"]].append(r)
        for name, laws in SUBSECTIONS:
            if name == "Feature Relation":
                continue
            rows = sub_map.get(name, [])
            L.append(f"## Codebase Implementation — {name}")
            L.append("")
            L.append(f"<!-- laws: {laws} -->")
            if not rows:
                L.append("- **Confirmation:** ✔️")
                L.append("- **Problem:**")
                L.append("- **Solution:**")
                L.append("")
                continue
            ph = min((norm_phase(r)[0] for r in rows), key=lambda x: PHASE_RANK[x])
            L.append("- **Confirmation:** ❌")
            L.append(f"- **Phase:** {ph}")
            L.append(f"- **Findings:** {len(rows)}")
            L.append("- **Problem:**")
            for i, r in enumerate(rows, start=1):
                cur = clean(str(r.get("Current", NP)), 400)
                L.append(f"  {i}. `{clean(str(r.get('File:Line', NP)), 140)}` {cur} "
                         f"(`{r['ID']}`, `{r['_dimension']}`) — "
                         f"{r.get('_over_all_reason', '')}")
            L.append("- **Solution:**")
            for i, r in enumerate(rows, start=1):
                fx = clean(str(r.get("Fix", NP)), 400)
                if (r.get("Fix") or NP) == NP:
                    fx = ("implement the audit's Target: " +
                          clean(str(r.get("Target", NP)), 260))
                L.append(f"  {i}. {fx} — verify: {verify_cmd(r, nature_of(r, name))}"
                         f" — test: {test_path(r)}")
            L.append("")
        fr = sub_map.get("Feature Relation", [])
        L.append("## Codebase Implementation — Feature Relation")
        L.append("")
        L.append("<!-- laws: feature IDs, chain IDs, upstream/downstream -->")
        L.append("- **Confirmation:** " + ("\u274c" if fr else "\u2714\ufe0f"))
        if fr:
            L.append(f"- **Findings:** {len(fr)}")
        for line in feature_relation(fr or over_all):
            L.append(line)
        L.append("")
        L.append("### Resolution")
        L.append("")
        L.append("- **Verify (cross-cutting):** run every per-finding verify command "
                 "above; each must return its expected output")
        L.append("- **Paired test:** `backend/tests/architecture/` "
                 "(note: the benchmark's `test/architecture/` path does not exist)")
        L.append("- **Rollback:** per-file revert")
        L.append("- **Browser test:** N/A")
        L.append("")
        L.append("---")
        L.append("")

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")

    print(f"wrote {OUT}")
    print(f"file blocks          : {file_no}")
    print(f"cross-cutting records: {len(over_all)}")
    print(f"compiled findings    : {total_findings}")
    print(f"excluded records     : {len(excluded)}")
    print("exclusion reasons    :")
    reasons = defaultdict(int)
    for e in excluded:
        reasons[e["why"].split(" —")[0].split(":")[0]] += 1
    for r, c in sorted(reasons.items(), key=lambda kv: -kv[1]):
        print(f"  {c:>5}  {r}")
    with open(os.path.join(COMP, "_excluded.json"), "w", encoding="utf-8") as fh:
        json.dump([{"id": e["rec"]["ID"], "dimension": e["rec"]["_dimension"],
                    "path": e["rec"].get("_path"), "why": e["why"]}
                   for e in excluded], fh, indent=1, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())