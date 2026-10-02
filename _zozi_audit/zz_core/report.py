"""Markdown renderer — produces the single consolidated audit report.

``zozi_forensic_audit.md`` contains every dimension, cross-cutting pass,
completion-blocker rollup and the 18-condition production-readiness gate.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

from .constants import DIMENSIONS, DIMENSION_LABELS, ID_PREFIX_BY_DIMENSION
from .model import Finding, Observation, ScanContext
from .util import fmt_seconds, md_escape

PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
FINDING_COLUMNS = (
    "ID", "Phase", "Status", "Cluster", "File:Line", "Current", "Target",
    "Delta", "Fix", "Effort", "Priority", "Conf", "Evidence", "Truth",
    "Claim", "Sibling", "Verify", "Test", "Rollback", "Blast radius",
    "Depends on", "Blocks", "Completion blocker", "Laws",
)


def _cell(v) -> str:
    s = "" if v is None else str(v)
    s = s.replace("\r", " ").replace("\n", " ").replace("|", "\\|")
    if len(s) > 300:
        s = s[:297] + "..."
    return s.strip() or "—"


def _clip(v, n: int) -> str:
    s = "" if v is None else str(v).replace("\r", " ").replace("\n", " ").strip()
    return s[: n - 3] + "..." if len(s) > n else s


def _table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "_None._\n"
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        out.append("| " + " | ".join(_cell(c) for c in row) + " |")
    return "\n".join(out) + "\n"


def _finding_row(f: Finding) -> list[str]:
    return [
        f.id, f.phase, f.status, f.cluster or "—", f.location or "—",
        f.current, f.target, f.delta, f.fix, f.effort, f.priority,
        str(f.confidence), f.evidence_strength, f.truth_level, f.claim_state,
        f.sibling or "—", f.verify or "—", f.test or "—", f.rollback,
        f.blast_radius or "—", f.depends_on or "—", f.blocks or "—",
        f.completion_blocker, ",".join(f"L-{n}" for n in f.laws) or "—",
    ]


def _findings_table(findings: list[Finding]) -> str:
    findings = sorted(findings, key=lambda f: (
        PRIORITY_ORDER.get(f.priority, 9), f.dimension, f.file, f.line, f.id))
    return _table(list(FINDING_COLUMNS), [_finding_row(f) for f in findings])


# --------------------------------------------------------------------------- #
# Header / summary
# --------------------------------------------------------------------------- #

def render_header(ctx: ScanContext, meta: dict, preflight: list[dict]) -> str:
    counts = meta.get("file_counts", {})
    lines = [
        "# ZOZI FORENSIC AUDIT",
        "",
        f"> **Generated:** {meta.get('started_at', '')}  ",
        f"> **Run ID:** `{meta.get('run_id', '')}`  ",
        f"> **Commit:** `{meta.get('commit', 'unknown')}`  ",
        f"> **Mode:** {'fast (static only)' if ctx.fast else 'full'} · "
        f"**Workers:** {ctx.workers} · **Repo root:** `{ctx.root}`  ",
        "> **Benchmarks:** `_most_imp_docx/ARCHITECTURE_STACK.md`, "
        "`_most_imp_docx/TECHNOLOGY_STACK.md`, `_most_imp_docx/PROMPT_FORENSIC_AUDIT.md`, "
        "`_most_imp_docx/FEATURE_STACK.md`  ",
        f"> **Surface:** {counts.get('python', 0)} Python · "
        f"{counts.get('typescript', 0)} TS/TSX · {counts.get('all', 0)} total files walked "
        "(excludes `.git`, `.kilo`, `node_modules`, caches, build output).",
        "",
        "## 0 · Pre-conditions (Phase 0 / 0.5)",
        "",
    ]
    lines.append(_table(
        ["#", "Check", "Status", "Evidence"],
        [[str(i + 1), c.get("check", ""), c.get("status", ""),
          c.get("evidence", "")] for i, c in enumerate(preflight)],
    ))
    return "\n".join(lines)


def render_headline(findings: list[Finding], facts: dict,
                    recommendations: list | None = None) -> str:
    priorities = {p: sum(1 for f in findings if f.priority == p)
                  for p in ("P0", "P1", "P2", "P3")}
    blockers = {
        "yes": sum(1 for f in findings if f.completion_blocker == "yes"),
        "partial": sum(1 for f in findings if f.completion_blocker == "partial"),
        "no": sum(1 for f in findings if f.completion_blocker == "no"),
    }
    clusters = {f.cluster for f in findings if f.cluster}
    files_with_findings = {f.file for f in findings if f.file}
    effort_hours = {"S": 1.0, "M": 2.5, "L": 6.0}
    total_hours = sum(effort_hours.get(f.effort, 1.0) for f in findings
                      if f.priority in ("P0", "P1"))
    rows = [
        ["Findings total", str(len(findings))],
        ["P0 / P1 / P2 / P3", f"{priorities['P0']} / {priorities['P1']} / "
                              f"{priorities['P2']} / {priorities['P3']}"],
        ["Older-status (COMPILED/RESOLVED/etc.)", "0 — this run emits NEW only"],
        ["Completion blockers (yes / partial / no)",
         f"{blockers['yes']} / {blockers['partial']} / {blockers['no']}"],
        ["Clusters", str(len(clusters))],
        ["Files with findings", str(len(files_with_findings))],
        ["Contradictions", str(len(facts.get("contradictions", [])))],
        ["Anti-pattern categories",
         str(len(merge_anti_patterns(facts.get("anti_patterns", []))))],
        ["Chains audited", str(len(facts.get("chains", [])))],
        ["Browser steps recorded", str(len(facts.get("browser_steps", [])))],
        ["LLM-reviewed hotspots", str(len(facts.get("llm_reviews", [])))],
        ["HTTP responses probed", str(len(facts.get("http_checks", [])))],
        ["Recommendations (not blockers)", str(len(recommendations or []))],
        ["Estimated P0+P1 effort", f"~{total_hours:.0f}h (S=1h, M=2.5h, L=6h)"],
        ["Coverage (dimensions with findings)",
         f"{len({f.dimension for f in findings})}/28"],
    ]
    out = ["## 1 · Headline numbers", "", _table(["Metric", "Value"], rows)]
    verdict = "NOT PRODUCTION READY" if blockers["yes"] else (
        "CONDITIONALLY READY" if blockers["partial"] else "NO BLOCKERS DETECTED")
    out.insert(0, f"**VERDICT: {verdict}** — "
                  f"{blockers['yes']} hard completion blocker(s).\n")
    return "\n".join(out)


def render_recommendations(recs: list, facts: dict) -> str:
    """Improvement opportunities — deliberately separate from findings.

    A missing ``create_refund_ledger_entry`` is a defect and appears as a
    finding. "Batch payout reconciliation" is an opportunity: it does not block
    anything, it reduces workload. Mixing the two would inflate the blocker
    count and make the remediation plan unfalsifiable.
    """
    out = ["## 7 · Recommendations & automation opportunities", ""]
    if not recs:
        out += ["_No recommendations were produced in this run._", ""]
        return "\n".join(out)
    by_area: dict[str, list] = {}
    for r in recs:
        by_area.setdefault(r.area, []).append(r)
    impact_rank = {"high": 0, "medium": 1, "low": 2}
    out += [
        f"{len(recs)} recommendation(s) across {len(by_area)} area(s). "
        f"These are **not** completion blockers — they are the backlog that takes "
        f"the project from *correct* to *good*.",
        "",
        _table(["Area", "Count", "High impact", "XL effort"],
               [[area, str(len(items)),
                 str(sum(1 for i in items if i.impact == "high")),
                 str(sum(1 for i in items if i.effort == "XL"))]
                for area, items in sorted(by_area.items(),
                                          key=lambda t: -len(t[1]))]),
        "---",
    ]
    for area, items in sorted(by_area.items(), key=lambda t: -len(t[1])):
        out += [f"### {area}", ""]
        for r in sorted(items, key=lambda x: (impact_rank.get(x.impact, 9),
                                              {"XL": 0, "L": 1, "M": 2, "S": 3}.get(x.effort, 9))):
            out += [
                f"#### {r.id} · {r.title}",
                "",
                f"- **Why now:** {r.rationale}",
                f"- **Current state:** {r.current}",
                f"- **Proposal:** {r.proposal}",
                f"- **Benefit:** {r.benefit}",
                f"- **Effort / impact:** {r.effort} / {r.impact}"
                + (f" · **Human effort saved:** {r.human_effort_saved}"
                   if r.human_effort_saved else "")
                + (f" · **Prerequisites:** {', '.join(r.prerequisites)}"
                   if r.prerequisites else ""),
                f"- **Evidence:** {r.evidence or '—'}",
                "",
            ]
    return "\n".join(out)


def render_design_and_coverage(facts: dict) -> str:
    """The design / interaction / taxonomy / coverage measurements, as measured."""
    blocks = [
        ("Design system", "color_drift", "design_tokens", "ui_primitives"),
        ("Interaction robustness", "interaction_buttons", "interaction_modals",
         "interaction_forms", "interaction_toasts", "page_states"),
        ("Feature & taxonomy", "feature_catalog", "route_test_matrix",
         "category_taxonomy"),
        ("HTTP layer (live responses)", "http_probe", "security_header_policy"),
        ("Settings contract", "settings_contract"),
        ("Workflow & automation", "workflow_runtime", "workflow_event_spine",
         "workflow_status_integrity", "handover_assurance", "quality_assurance",
         "automation_candidates", "finance_automation"),
        ("Database management", "table_management", "schema_drift"),
    ]
    out = ["## 8 · Design, interaction, taxonomy, workflow & data measurements", "",
           "Every number below is measured from source during this run.", ""]
    any_row = False
    for title, *keys in blocks:
        rows = []
        for k in keys:
            v = facts.get(k)
            if isinstance(v, dict):
                rows.append([k, _render_measurements(v)])
            elif v is not None:
                rows.append([k, str(v)])
        if not rows:
            continue
        any_row = True
        out += [f"### {title}", "", _table(["Measurement", "Value"], rows), ""]
    if not any_row:
        out += ["_No extension measurements were produced in this run._", ""]
    return "\n".join(out)


def _render_measurements(v: dict, limit: int = 14) -> str:
    scalars = []
    lists = []
    for k, val in v.items():
        if isinstance(val, bool):
            scalars.append(f"{k}={'yes' if val else 'no'}")
        elif isinstance(val, (int, float, str)):
            scalars.append(f"{k}={val}")
        elif isinstance(val, list):
            lists.append(f"{k}[{len(val)}]")
        elif isinstance(val, dict):
            scalars.append(f"{k}={{{len(val)}}}")
    text = "; ".join(scalars[:limit])
    if lists:
        text += ("; " if text else "") + " " + " ".join(lists[:6])
    return md_escape(text)


def render_completion_blockers(findings: list[Finding]) -> str:
    yes = [f for f in findings if f.completion_blocker == "yes"]
    partial = [f for f in findings if f.completion_blocker == "partial"]
    cols = ["ID", "Phase", "Dimension", "File:Line", "Fix", "Effort",
            "Priority", "Conf", "Verify", "Depends on"]
    rows = [[f.id, f.phase, DIMENSION_LABELS.get(f.dimension, f.dimension),
             f.location, f.fix, f.effort, f.priority, str(f.confidence),
             f.verify or "—", f.depends_on or "—"]
            for f in sorted(yes, key=lambda x: (PRIORITY_ORDER.get(x.priority, 9), x.id))]
    out = ["## 2 · Completion blockers (fix before anything else)", "",
           f"**{len(yes)}** yes-blocker(s) · **{len(partial)}** partial-blocker(s) "
           "blocking some journeys/environments.", "",
           _table(cols, rows)]
    if partial:
        out += ["### Partial blockers", "",
                _table(cols, [[f.id, f.phase, DIMENSION_LABELS.get(f.dimension, f.dimension),
                               f.location, f.fix, f.effort, f.priority,
                               str(f.confidence), f.verify or "—", f.depends_on or "—"]
                              for f in partial])]
    return "\n".join(out)


def render_top_findings(findings: list[Finding], n: int = 20) -> str:
    ranked = sorted(findings, key=lambda f: (
        PRIORITY_ORDER.get(f.priority, 9), -f.confidence,
        f.completion_blocker != "yes", f.id))
    rows = [[f.id, f.priority, DIMENSION_LABELS.get(f.dimension, f.dimension),
             f.location, f.fix, f.effort, str(f.confidence), f.completion_blocker]
            for f in ranked[:n]]
    return ("## 3 · Top findings (priority ranked)\n\n"
            + _table(["ID", "Priority", "Dimension", "File:Line", "Fix",
                      "Effort", "Conf", "Blocker"], rows))


def render_clusters(findings: list[Finding]) -> str:
    clusters: dict[str, list[Finding]] = {}
    for f in findings:
        if f.cluster:
            clusters.setdefault(f.cluster, []).append(f)
    if not clusters:
        return "## 4 · Clusters\n\n_No clusters (no root cause shared by 3+ findings)._\n"
    ranked = sorted(clusters.items(), key=lambda kv: -len(kv[1]))
    rows = []
    for cid, members in ranked[:20]:
        rows.append([
            cid, str(len(members)),
            ", ".join(sorted({m.id for m in members})[:12]) + ("..." if len(members) > 12 else ""),
            members[0].fix,
            sum(1 for m in members if m.completion_blocker == "yes"),
        ])
    return ("## 4 · Clusters (shared root causes)\n\n"
            + _table(["Cluster", "Size", "Members", "Recommended single fix",
                      "Yes-blockers"], rows))


# --------------------------------------------------------------------------- #
# Dimension sections
# --------------------------------------------------------------------------- #

def render_dimension(dimension: str, findings: list[Finding],
                     observations: list[Observation], ctx: ScanContext) -> str:
    label = DIMENSION_LABELS.get(dimension, dimension)
    files = {f.file for f in findings if f.file}
    laws = sorted({n for f in findings for n in f.laws})
    priorities = {p: sum(1 for f in findings if f.priority == p)
                  for p in ("P0", "P1", "P2", "P3")}
    slow = [t for t in observations if t.truth_level == "L0"]
    blockers = sum(1 for f in findings if f.completion_blocker == "yes")
    if findings:
        confirmation = "❌ FAIL"
    elif observations:
        # A dimension that only recorded observations asserted nothing. Calling
        # that a PASS would claim a verification the check never performed.
        confirmation = (f"⚠️  NOT VERIFIED (0 findings, {len(observations)} "
                        f"observation(s) recorded — no violation asserted, but "
                        f"this dimension was not proven clean)")
    else:
        confirmation = ("⚠️  NO EVIDENCE (check produced neither findings nor "
                        "observations — treat as unverified)")
    out = [
        f"## Dimension {label}",
        "",
        "### Summary",
        f"- Confirmation: {confirmation}",
        f"- Files with findings: {len(files)}",
        f"- Findings: {len(findings)}",
        f"- P0: {priorities['P0']}  P1: {priorities['P1']}  "
        f"P2: {priorities['P2']}  P3: {priorities['P3']}",
        f"- Clusters: {len({f.cluster for f in findings if f.cluster})}",
        f"- Laws implicated: {', '.join(f'L-{n}' for n in laws) if laws else '—'}",
        f"- Completion blockers: {blockers} yes · "
        f"{sum(1 for f in findings if f.completion_blocker == 'partial')} partial · "
        f"{sum(1 for f in findings if f.completion_blocker == 'no')} no",
        f"- Observations: {len(observations)} (L0: {len(slow)})",
        "- Status: NEW: " + str(len(findings)) + " · COMPILED: 0 · RESOLVED: 0 · "
        "DEFERRED: 0 · INVALID: 0",
        "",
        "### Findings",
        "",
        _findings_table(findings),
        "",
        "### Over all",
        "",
        "**Problem(s)**",
    ]
    problems = sorted({f.delta for f in findings if f.delta})
    out += [f"{i+1}. {p}" for i, p in enumerate(problems[:30])] or ["1. None identified."]
    out += ["", "**Solution(s)**"]
    solutions = sorted({f.fix for f in findings if f.fix})
    out += [f"{i+1}. {s}" for i, s in enumerate(solutions[:30])] or ["1. None required."]
    out += ["", "**Corrections required (prioritized)**", "",
            _table(["Priority", "Correction", "Target", "Blocking", "Effort"],
                   [[f.priority, f.fix, f.location, f.completion_blocker, f.effort]
                    for f in sorted(findings, key=lambda x: (
                        PRIORITY_ORDER.get(x.priority, 9), x.id))][:60])]
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# Cross-cutting sections
# --------------------------------------------------------------------------- #

def render_chains(facts: dict) -> str:
    chains = facts.get("chains", [])
    out = ["## 6.1 · Chains (critical business journeys)", ""]
    if not chains:
        out.append("_No chain data produced (scanner failure or --fast mode)._")
        return "\n".join(out)
    rows = []
    for c in chains:
        rows.append([
            c.get("id", ""), c.get("name", ""),
            ", ".join(c.get("actors", [])), ", ".join(c.get("domains", [])),
            c.get("entry", ""), c.get("happy", "?"), c.get("failure", "?"),
            c.get("rollback", "?"), c.get("verdict", "?"),
            c.get("critical", "?"),
        ])
    out.append(_table(["ID", "Name", "Actors", "Domains", "Entry", "Happy",
                       "Failure paths", "Rollback", "Verdict", "Launch-critical"],
                      rows))
    for c in chains:
        steps = c.get("steps", [])
        if not steps:
            continue
        out.append(f"\n### {c.get('id', '')}: {c.get('name', '')}\n")
        out.append(_table(["Step", "Actor", "Expected outcome", "Evidence", "Status"],
                          [[str(i + 1), s.get("actor", ""), s.get("expected", ""),
                            s.get("evidence", ""), s.get("status", "")]
                           for i, s in enumerate(steps)]))
        if c.get("findings"):
            out.append("\n**Chain findings:** " + "; ".join(c["findings"]) + "\n")
    return "\n".join(out)


def render_contradictions(facts: dict) -> str:
    items = facts.get("contradictions", [])
    out = ["## 6.2 · Contradictions (never silently resolved)", ""]
    if not items:
        out.append("_None detected by the checks that ran._")
        return "\n".join(out)
    sections = []
    for c in items:
        sections.append(
            f"### {c.get('id', 'CONTRAD')}\n\n"
            f"- **Category:** {c.get('category', '')}\n"
            f"- **Source A:** `{c.get('source_a', '')}` — {c.get('a_says', '')}\n"
            f"- **Source B:** `{c.get('source_b', '')}` — {c.get('b_says', '')}\n"
            f"- **Conflict:** {c.get('conflict', '')}\n"
            f"- **Impact:** {c.get('impact', '')}\n"
            f"- **Project completion blocker:** {c.get('blocker', 'no')}\n"
            f"- **User decision required:** {c.get('user_decision', 'no')}\n"
        )
    out += sections
    return "\n".join(out)


_BLOCKER_RANK = {"yes": 0, "partial": 1, "no": 2}


def merge_anti_patterns(items: list[dict]) -> list[dict]:
    """Several checks can report the same anti-pattern id; merge them so the
    report never lists one category twice with different counts."""
    merged: dict[str, dict] = {}
    for a in items:
        key = str(a.get("id") or a.get("category") or "AP-unknown")
        m = merged.get(key)
        if m is None:
            merged[key] = dict(a)
            continue
        try:
            m["occurrences"] = int(m.get("occurrences") or 0) + int(a.get("occurrences") or 0)
        except (TypeError, ValueError):
            pass
        if _BLOCKER_RANK.get(str(a.get("blocker", "no")), 9) < \
                _BLOCKER_RANK.get(str(m.get("blocker", "no")), 9):
            m["blocker"] = a.get("blocker")
        if not m.get("sample") and a.get("sample"):
            m["sample"] = a.get("sample")
        if not m.get("remediation") and a.get("remediation"):
            m["remediation"] = a.get("remediation")
    return sorted(merged.values(), key=lambda x: -int(x.get("occurrences") or 0))


def render_anti_patterns(facts: dict) -> str:
    items = merge_anti_patterns(facts.get("anti_patterns", []))
    out = ["## 6.3 · Anti-patterns", ""]
    if not items:
        out.append("_None detected._")
        return "\n".join(out)
    rows = [[a.get("id", ""), a.get("category", ""),
             str(a.get("occurrences", "")), a.get("sample", ""),
             a.get("blocker", "no"), a.get("remediation", "")]
            for a in items]
    out.append(_table(["ID", "Category", "Occurrences", "Sample location",
                       "Blocker", "Remediation"], rows))
    return "\n".join(out)


def render_feature_health(facts: dict) -> str:
    feats = facts.get("feature_health", [])
    out = ["## 6.4 · Feature health", ""]
    if not feats:
        out.append("_No feature catalog data._")
        return "\n".join(out)
    rows = [[f.get("feature", ""), f.get("domain", ""),
             str(f.get("score", "")), f.get("launch_critical", ""),
             f.get("status", ""), f.get("notes", "")]
            for f in sorted(feats, key=lambda x: str(x.get("feature", "")))[:250]]
    out.append(_table(["Feature", "Domain", "Score /100", "Launch-critical",
                       "Status", "Notes"], rows))
    return "\n".join(out)


def render_generic_facts(title: str, key: str, facts: dict,
                         headers: list[str], mapper) -> str:
    items = facts.get(key, [])
    out = [f"## {title}", ""]
    if not items:
        out.append("_None recorded._")
        return "\n".join(out)
    out.append(_table(headers, [mapper(i) for i in items]))
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# Readiness / remediation
# --------------------------------------------------------------------------- #

def default_readiness(findings: list[Finding], facts: dict) -> list[dict]:
    """Fallback 18-condition gate when the blockers scanner did not supply one."""
    yes = [f for f in findings if f.completion_blocker == "yes"]
    p1 = [f for f in findings if f.priority == "P1"]
    tools = facts.get("readiness_tools", {})
    conditions = [
        ("All yes completion-blocker findings RESOLVED or waived",
         "fail" if yes else "pass",
         f"{len(yes)} open yes-blocker(s)"),
        ("All P1 findings RESOLVED or scheduled with a date",
         "fail" if p1 else "pass", f"{len(p1)} open P1"),
        ("pytest tests/architecture green", tools.get("arch_tests", "unverifiable"),
         tools.get("arch_tests_evidence", "run `pytest tests/architecture/`")),
        ("pytest commerce-domain suite green", tools.get("commerce", "unverifiable"),
         "collection status from pre-flight"),
        ("pytest security suite green", tools.get("security", "unverifiable"),
         "collection status from pre-flight"),
        ("App boots with zero skipped routers/stubs",
         tools.get("boot", "unverifiable"), "boot smoke output"),
        ("Frontend build passes with zero errors", tools.get("tsc", "unverifiable"),
         "tsc --noEmit / next build"),
        ("Mobile build succeeds or explicitly deferred",
         tools.get("mobile", "unverifiable"), "eas build / deferral"),
        ("Browser: money-path features pass", tools.get("browser", "unverifiable"),
         "browser probe results"),
        ("Browser: security-path features pass", tools.get("browser", "unverifiable"),
         "browser probe results"),
        ("Load test p95 < 500 ms at 2x peak", tools.get("load", "unverifiable"),
         "load probe results"),
        ("Zero KEEP/HARDEN violations", "pass", "no KEEP/HARDEN constraints defined"),
        ("Zero open contradictions blocking P0/P1",
         "fail" if facts.get("contradictions") else "pass",
         f"{len(facts.get('contradictions', []))} contradiction(s)"),
        ("Verifier: 3 consecutive GREEN cycles",
         tools.get("ci", "unverifiable"), "CI history"),
        ("All required env vars set in production config", tools.get("env", "unverifiable"),
         "env inventory"),
        ("Database migrations linear and tested", tools.get("migrations", "unverifiable"),
         "alembic heads"),
        ("Payment credentials stored encrypted", tools.get("payment_creds", "unverifiable"),
         "field-encryption check"),
        ("PCI-DSS compliance verified (if card payments active)",
         "unverifiable", "not automatically verifiable"),
    ]
    return [{"n": i + 1, "condition": c, "status": s, "evidence": e}
            for i, (c, s, e) in enumerate(conditions)]


def render_readiness(facts: dict, findings: list[Finding]) -> str:
    conditions = facts.get("readiness") or default_readiness(findings, facts)
    rows = [[str(c["n"]), c["condition"], c["status"], c.get("evidence", "")]
            for c in conditions]
    counts = {"pass": 0, "fail": 0, "unverifiable": 0, "deferred": 0}
    for c in conditions:
        counts[c["status"]] = counts.get(c["status"], 0) + 1
    out = ["## 7 · Production readiness — 18-condition gate", "",
           f"**{counts['pass']} pass · {counts['fail']} fail · "
           f"{counts.get('partial', 0)} partial · "
           f"{counts['unverifiable']} unverifiable · {counts.get('deferred', 0)} deferred**",
           "", _table(["#", "Condition", "Status", "Evidence"], rows), "",
           "### Unverifiable conditions", "",
           _table(["#", "Condition", "Reason", "What would verify it"],
                  [[str(c["n"]), c["condition"], c.get("evidence", ""),
                    c.get("verify_with", "live environment / CI") ]
                   for c in conditions if c["status"] == "unverifiable"]),
           "", "### Waivers", "", "_None on record._"]
    return "\n".join(out)


def render_remediation(findings: list[Finding], facts: dict) -> str:
    out = ["## 8 · Remediation plan", ""]
    yes = [f for f in findings if f.completion_blocker == "yes"]
    out += ["### Completion blockers first", "",
            _table(["ID", "Phase", "File:Line", "Fix", "Effort", "Verify"],
                   [[f.id, f.phase, f.location, f.fix, f.effort, f.verify or "—"]
                    for f in yes])]
    phase_order = ["emergency", "boot", "tech", "db", "logic", "arch",
                   "security", "payment", "compliance", "frontend", "mobile",
                   "testing", "infra", "docs", "defer"]
    out += ["", "### Phase execution order", "",
            _table(["Phase", "Findings", "Blockers (yes)", "Example work"],
                   [[p, str(sum(1 for f in findings if f.phase == p)),
                     str(sum(1 for f in findings if f.phase == p and f.completion_blocker == "yes")),
                     next((f.fix for f in findings if f.phase == p), "—")]
                    for p in phase_order
                    if any(f.phase == p for f in findings)])]
    for p in ("P0", "P1", "P2", "P3"):
        subset = [f for f in findings if f.priority == p]
        out += ["", f"### {p} — {len(subset)} finding(s)", "",
                _table(["ID", "Phase", "Dimension", "File:Line", "Fix", "Effort",
                        "Conf", "Blocker"],
                       [[f.id, f.phase, DIMENSION_LABELS.get(f.dimension, f.dimension),
                         f.location, f.fix, f.effort, str(f.confidence),
                         f.completion_blocker] for f in subset][:400])]
    keep = facts.get("keep_harden", [])
    out += ["", "### KEEP / HARDEN (all six criteria required)", "",
            _table(["ID", "Component", "Deviation", "Why not to change",
                    "Suggested hardening"],
                   [[k.get("id", ""), k.get("component", ""), k.get("deviation", ""),
                     k.get("why_not", ""), k.get("hardening", "")] for k in keep])
            if keep else "### KEEP / HARDEN\n\n_None qualified._"]
    return "\n".join(out)


def render_appendix_tools(ctx: ScanContext) -> str:
    rows = []
    for name, res in sorted(ctx.tools.items()):
        rows.append([name, getattr(res, "cmd", ""), getattr(res, "status", "?"),
                     str(getattr(res, "exit_code", "")),
                     f"{getattr(res, 'duration_s', 0)}s",
                     getattr(res, "skipped_reason", "") or "—"])
    return ("## Appendix A · Tool-run ledger\n\n"
            + _table(["Tool", "Command", "Status", "Exit", "Duration", "Notes"],
                     rows))


def render_appendix_coverage(ctx: ScanContext, findings: list[Finding],
                             results, observations) -> str:
    by_dim_files: dict[str, set] = {}
    for f in findings:
        if f.file:
            by_dim_files.setdefault(f.dimension, set()).add(f.file)
    dim_rows = []
    for i, (num, name) in enumerate(DIMENSIONS):
        key = f"{num}_{name}"
        found = [f for f in findings if f.dimension == key]
        dim_rows.append([key, str(len(found)), str(len(by_dim_files.get(key, set()))),
                         str(sum(1 for f in found if f.completion_blocker == "yes"))])
    errors = [r for r in results if getattr(r, "error", "")]
    out = [
        "## Appendix B · Coverage & method",
        "",
        "**Method.** The audit walks the repository (excluding `.git`, `.kilo`, "
        "`node_modules`, caches and build output), parses Python with `ast` and "
        "TypeScript/JSON/YAML/SQL/TOML with textual analysers, parses the benchmark "
        "documents at runtime, and runs each finding-producing check as an "
        "independent task in a bounded pool (max 10 concurrent).",
        "",
        "**Static-only findings** are marked `truth_level=L0` (source) or `L1` "
        "(evidence). Runtime claims are only made when a tool run succeeded; "
        "otherwise the item is `unverifiable` with the command that would verify it.",
        "",
        _table(["Dimension", "Findings", "Files cited", "Yes-blockers"], dim_rows),
        "",
        f"Observations recorded: **{len(observations)}** "
        "(full stream: `logs/observations.jsonl`).",
        "",
    ]
    if errors:
        out += ["**Checks that crashed (auditor defects):**", ""]
        out += [f"- `{e}`" for e in errors[:40]]
    else:
        out += ["All registered checks completed without crashing."]
    out += ["", "**Explicit exclusions:** `.git/`, `.kilo/` (nested worktrees), "
            "`node_modules/`, `__pycache__/`, `.next/`, `dist/`, `build/`, "
            "`_extra_files/`, `_legacy.bak/`, binary/media/sqlite artifacts.",
            "",
            "**What this audit does NOT do:** it does not compile findings, does not "
            "resolve them, does not modify source files, and does not treat the prior "
            "`_audit/**` corpus as ground truth — prior findings are re-verified or "
            "reported as not-found."]
    return "\n".join(out)


def render_laws(facts: dict) -> str:
    rows = facts.get("laws", [])
    if not rows:
        return "_Law matrix not produced._\n"
    table = _table(["Law", "Category", "Rule", "Status", "Evidence"],
                   [[str(r.get("law")), r.get("category", ""), r.get("rule", ""),
                     r.get("status", ""), r.get("evidence", "")] for r in rows])
    return ("### Law matrix (1-325)\n\n"
            f"PASS: {facts.get('laws_pass', '?')} · FAIL: {facts.get('laws_fail', '?')} · "
            f"UNVERIFIABLE: {facts.get('laws_unverifiable', '?')} · "
            f"Total parsed: {facts.get('laws_total', '?')}\n\n" + table)


def render_self_check(results) -> str:
    rows = []
    for r in sorted(results, key=lambda x: x.check):
        duration = r.facts.get("_duration_s", "")
        rows.append([r.check, r.dimension, str(len(r.findings)),
                     str(len(r.observations)), str(duration) + "s",
                     "ERROR" if r.error else "ok"])
    return ("## Appendix C · Auditor self-check\n\n"
            + _table(["Check", "Dimension", "Findings", "Observations",
                      "Duration", "Status"], rows))


# --------------------------------------------------------------------------- #
# Main render
# --------------------------------------------------------------------------- #

def render_llm_section(facts: dict) -> str:
    pre = facts.get("llm_precondition")
    reviews = facts.get("llm_reviews", [])
    out = ["## 6.10 · LLM semantic review (Ollama, L2 only)", ""]
    if pre and not reviews:
        out.append(f"_Skipped: {pre}._")
        return "\n".join(out)
    if not reviews:
        out.append("_None recorded (run with --llm)._")
        return "\n".join(out)
    summary = facts.get("llm_summary", {})
    out.append(f"Model `{summary.get('model', '?')}` · {summary.get('reviewed', len(reviews))} "
               "hotspot(s) reviewed. LLM verdicts are advisory (L2/INFERRED); they never "
               "count as verified findings.")
    out.append("")
    out.append(_table(
        ["File", "Verdict", "Intent", "Actual / drift", "Blocker", "Conf."],
        [[r.get("path", ""), r.get("verdict", ""), _clip(r.get("intent", ""), 90),
          _clip(r.get("drift") or r.get("actual", ""), 90),
          r.get("completion_impact", "no"), str(r.get("confidence", 1))]
         for r in reviews]))
    return "\n".join(out)


def render_load_section(facts: dict) -> str:
    out = ["## 6.12 · Load / latency probe", ""]
    pre = facts.get("load_precondition")
    load = facts.get("load")
    if pre and not load:
        out.append(f"_Skipped: {pre}._")
        return "\n".join(out)
    if not load:
        out.append("_None recorded (run with --load against a live API)._")
        return "\n".join(out)
    out.append(_table(
        ["Target", "Requests", "Errors", "p50 ms", "p95 ms", "p99 ms", "Error rate"],
        [[load.get("url", ""), str(load.get("requests", 0)), str(load.get("errors", 0)),
          str(load.get("p50_ms", "")), str(load.get("p95_ms", "")),
          str(load.get("p99_ms", "")), str(load.get("error_rate", ""))]]))
    out.append("")
    out.append("_Probe measures latency/error behaviour only; it does not by itself prove "
               "capacity — pair it with the documented 2× peak assumption._")
    return "\n".join(out)


def build_report(ctx: ScanContext, meta: dict, grouped: dict,
                 results, browser=None, llm=None, db=None, extra: dict | None = None) -> str:
    findings: list[Finding] = grouped["findings"]
    observations = grouped["observations"]
    recommendations = grouped.get("recommendations", [])
    facts = grouped["facts"]
    if browser:
        facts.update(browser)
    if llm:
        facts.update(llm)
    if db:
        facts.update(db)
    if extra:
        facts.update(extra)

    parts = [
        render_header(ctx, meta, facts.get("preflight", [])),
        "---",
        render_headline(findings, facts, recommendations),
        "---",
        render_completion_blockers(findings),
        "---",
        render_top_findings(findings),
        "---",
        render_clusters(findings),
        "---",
        "## 5 · Dimensions",
        "",
    ]
    by_dim = grouped["by_dimension"]
    for num, name in DIMENSIONS:
        key = f"{num}_{name}"
        slot = by_dim.get(key, {"findings": [], "observations": []})
        parts.append(render_dimension(key, slot["findings"], slot["observations"], ctx))
        if key == "09_laws":
            parts.append(render_laws(facts))
        parts.append("---")
    parts += [
        "## 6 · Cross-cutting passes",
        "",
        render_chains(facts),
        "---",
        render_contradictions(facts),
        "---",
        render_anti_patterns(facts),
        "---",
        render_feature_health(facts),
        "---",
        render_generic_facts("6.5 · Code intent", "intents", facts,
                             ["ID", "Location", "Apparent intent (L2)",
                              "Actual behavior (L0)", "Blocker", "Evidence"],
                             lambda i: [i.get("id", ""), i.get("location", ""),
                                        i.get("intent", ""), i.get("actual", ""),
                                        i.get("blocker", "no"), i.get("evidence", "")]),
        "---",
        render_generic_facts("6.6 · AI drift", "drift", facts,
                             ["ID", "Type", "Location", "Divergence", "Blocker",
                              "Evidence"],
                             lambda i: [i.get("id", ""), i.get("type", ""),
                                        i.get("location", ""), i.get("divergence", ""),
                                        i.get("blocker", "no"), i.get("evidence", "")]),
        "---",
        render_generic_facts("6.7 · Code alignment (frontend ↔ backend ↔ mobile)",
                             "alignment", facts,
                             ["ID", "Area", "Frontend", "Backend", "Verdict",
                              "Blocker"],
                             lambda i: [i.get("id", ""), i.get("area", ""),
                                        i.get("frontend", ""), i.get("backend", ""),
                                        i.get("verdict", ""), i.get("blocker", "no")]),
        "---",
        render_generic_facts("6.8 · Browser behavior", "browser_steps", facts,
                             ["ID", "Step", "Expected", "Observed", "Status",
                              "Evidence"],
                             lambda i: [i.get("id", ""), i.get("step", ""),
                                        i.get("expected", ""), i.get("observed", ""),
                                        i.get("status", ""), i.get("evidence", "")]),
        "---",
        render_generic_facts("6.9 · Supply chain security", "supply_chain", facts,
                             ["Area", "Finding", "Evidence", "Status", "Blocker"],
                             lambda i: [i.get("area", ""), i.get("finding", ""),
                                        i.get("evidence", ""), i.get("status", ""),
                                        i.get("blocker", "no")]),
        "---",
        render_llm_section(facts),
        "---",
        render_generic_facts("6.11 · Live database drift", "db_drift", facts,
                             ["Area", "Finding", "Evidence", "Status", "Blocker"],
                             lambda i: [i.get("area", ""), i.get("finding", ""),
                                        i.get("evidence", ""), i.get("status", ""),
                                        i.get("blocker", "no")]),
        "---",
        render_load_section(facts),
        "---",
        render_readiness(facts, findings),
        "---",
        render_design_and_coverage(facts),
        "---",
        render_recommendations(recommendations, facts),
        "---",
        render_remediation(findings, facts),
        "---",
        render_appendix_tools(ctx),
        "---",
        render_appendix_coverage(ctx, findings, results, observations),
        "---",
        render_self_check(results),
        "",
        "---",
        "",
        f"_Report generated by `_zozi_audit/zozi_audit.py` — run `{meta.get('run_id', '')}` — "
        f"{datetime.now(timezone.utc).isoformat()}._",
        "",
        "_For the ordered, executable remediation plan derived from this report, "
        "run `python _zozi_audit/zozi_compile.py` → `_zozi_audit/zozi_remediation_plan.md`._",
        "",
    ]
    return "\n".join(parts)


def write_report(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
