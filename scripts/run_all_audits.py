#!/usr/bin/env python3
"""
run_all_audits.py — ZOZI Unified Governance Orchestrator v2.0

Runs all 4 audit scripts, collects their JSON output,
and merges everything into one combined platform governance report.

Fixes in v2.0:
  - Windows console encoding fix (UnicodeEncodeError on cp1252)
  - PYTHONIOENCODING=utf-8 passed to all subprocesses
  - Graceful handling of subprocess crashes
  - Combined report generation

Usage:
  python scripts/run_all_audits.py --no-fail
  python scripts/run_all_audits.py --ci
  python scripts/run_all_audits.py --root /path/to/repo --no-fail

Output:
  GOVERNANCE_REPORT.md          — combined human-readable report
  out/governance/combined.json  — combined machine-readable JSON
  + all 4 individual reports still generated as before
"""

from __future__ import annotations

import argparse
import datetime
import io
import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

# ============================================================================
# Windows console encoding fix — MUST be before any print() calls
# ============================================================================
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        try:
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, encoding="utf-8", errors="replace"
            )
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer, encoding="utf-8", errors="replace"
            )
        except Exception:
            pass


# ============================================================================
# 1. CONFIGURATION
# ============================================================================

AUDIT_SCRIPTS = [
    {
        "name": "Architecture",
        "script": "system_architecture_audit.py",
        "report": "ARCHITECTURE_AUDIT_REPORT.md",
        "json": "out/governance/architecture_audit.json",
        "icon": "[ARCH]",
    },
    {
        "name": "Database",
        "script": "database_audit.py",
        "report": "DATABASE_AUDIT_REPORT.md",
        "json": "out/governance/database_audit.json",
        "icon": "[DB]",
    },
    {
        "name": "Design",
        "script": "design_audit.py",
        "report": "DESIGN_AUDIT_REPORT.md",
        "json": "out/governance/design_audit.json",
        "icon": "[UI]",
    },
    {
        "name": "Health",
        "script": "health_audit.py",
        "report": "HEALTH_AUDIT_REPORT.md",
        "json": "out/governance/health_audit.json",
        "icon": "[HP]",
    },
]

SEV_ICON = {"VIOLATION": "[RED]", "ADVISORY": "[YEL]", "INFO": "[GRN]"}
PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


# ============================================================================
# 2. HELPERS
# ============================================================================


def find_repo(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()

    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir,
        script_dir.parent,
        script_dir.parent.parent,
        Path.cwd().resolve(),
    ]

    for cand in candidates:
        cand = cand.resolve()
        if (cand / "backend").is_dir():
            return cand

    return Path.cwd().resolve()


def safe_print(text: str) -> None:
    """Print that never crashes on Windows encoding."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"))


# ============================================================================
# 3. RUN AUDITS
# ============================================================================


def run_audit(
    repo: Path,
    audit: dict,
    no_fail: bool,
    ci: bool,
) -> dict | None:
    """Run one audit script and return its JSON output."""
    script_path = repo / "scripts" / audit["script"]

    if not script_path.exists():
        safe_print(f"  WARNING  {audit['name']}: script not found at {script_path}")
        return None

    json_path = repo / audit["json"]
    json_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(script_path),
        "--json", str(json_path),
        "--no-write",
    ]

    if no_fail:
        cmd.append("--no-fail")

    if ci:
        cmd.append("--ci")

    safe_print(f"\n{'=' * 60}")
    safe_print(f"  {audit['icon']}  Running {audit['name']} Audit...")
    safe_print(f"{'=' * 60}")

    # Fix Windows encoding: tell subprocess to use UTF-8
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    try:
        result = subprocess.run(
            cmd,
            cwd=str(repo),
            capture_output=True,
            timeout=600,
            env=env,
            encoding="utf-8",
            errors="replace",
        )

        # Print stdout
        if result.stdout:
            safe_print(result.stdout)

        if result.stderr:
            safe_print(result.stderr)

        exit_code = result.returncode
        status = "PASS" if exit_code == 0 else "FAIL"
        safe_print(f"\n  {audit['icon']}  {audit['name']}: {status} (exit={exit_code})")

    except subprocess.TimeoutExpired:
        safe_print(f"\n  WARNING  {audit['name']}: TIMEOUT (600s)")
        return None
    except Exception as exc:
        safe_print(f"\n  WARNING  {audit['name']}: ERROR - {exc}")
        return None

    # Read JSON output
    if json_path.exists():
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else None
        except Exception:
            return None

    return None


# ============================================================================
# 4. MERGE RESULTS
# ============================================================================


def merge_results(
    results: dict[str, dict | None],
    repo: Path,
) -> dict:
    """Merge all 4 audit results into one combined summary."""

    all_findings = []
    auditor_scores = {}
    total_red = 0
    total_yel = 0
    total_grn = 0
    priority_counts = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    domain_counts: dict[str, int] = defaultdict(int)
    file_scores: dict[str, dict] = defaultdict(lambda: {"weight": 0, "codes": set()})

    for audit in AUDIT_SCRIPTS:
        name = audit["name"]
        data = results.get(name)

        if data is None:
            auditor_scores[name] = {
                "score": None, "grade": "N/A",
                "red": 0, "yellow": 0, "green": 0,
            }
            continue

        summary = data.get("summary", {})
        findings = data.get("findings", [])

        score = summary.get("health_score", summary.get("debt_score", 0))
        grade = summary.get("grade", "?")
        red = summary.get("red", 0)
        yel = summary.get("yellow", 0)
        grn = summary.get("green", 0)

        auditor_scores[name] = {
            "score": score, "grade": grade,
            "red": red, "yellow": yel, "green": grn,
        }

        total_red += red
        total_yel += yel
        total_grn += grn

        for f in findings:
            f["auditor"] = name
            f["icon"] = audit["icon"]
            all_findings.append(f)

            sev = f.get("sev", "")
            priority = f.get("priority", "P3")
            domain = f.get("domain", "other")
            path = f.get("path", "")
            code = f.get("code", "")

            if priority in priority_counts:
                priority_counts[priority] += f.get("count", 1)

            domain_counts[domain] += f.get("count", 1)

            if path and path not in {"repo", "frontend/", "backend/", "CI/CD"}:
                weight = {"VIOLATION": 10, "ADVISORY": 2, "INFO": 0}.get(sev, 1)
                file_scores[path]["weight"] += weight * f.get("count", 1)
                file_scores[path]["codes"].add(code)

    # Calculate combined platform score
    valid_scores = [
        s["score"] for s in auditor_scores.values() if s["score"] is not None
    ]
    if valid_scores:
        platform_score = int(sum(valid_scores) / len(valid_scores))
    else:
        platform_score = 0

    if platform_score >= 90:
        platform_grade = "A"
    elif platform_score >= 75:
        platform_grade = "B"
    elif platform_score >= 60:
        platform_grade = "C"
    elif platform_score >= 40:
        platform_grade = "D"
    else:
        platform_grade = "F"

    # Top unhealthiest files
    ranked_files = sorted(
        file_scores.items(),
        key=lambda x: -x[1]["weight"],
    )[:30]

    return {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "repo": str(repo),
        "platform_score": platform_score,
        "platform_grade": platform_grade,
        "total_red": total_red,
        "total_yellow": total_yel,
        "total_green": total_grn,
        "total_findings": len(all_findings),
        "auditor_scores": auditor_scores,
        "priority_counts": priority_counts,
        "domain_counts": dict(domain_counts),
        "top_files": [
            {
                "file": path,
                "weight": data["weight"],
                "codes": sorted(data["codes"]),
            }
            for path, data in ranked_files
        ],
        "findings": all_findings,
    }


# ============================================================================
# 5. GENERATE COMBINED REPORT
# ============================================================================


def generate_combined_report(merged: dict, repo: Path) -> str:
    """Generate the combined markdown report."""

    score = merged["platform_score"]
    grade = merged["platform_grade"]
    red = merged["total_red"]
    yel = merged["total_yellow"]
    grn = merged["total_green"]
    total = merged["total_findings"]
    pri = merged["priority_counts"]
    auditors = merged["auditor_scores"]

    L = [
        "# ZOZI Platform Governance Report",
        "",
        f"**Generated:** {merged['timestamp']}  ",
        f"**Repo:** `{merged['repo']}`  ",
        "",
        "---",
        "",
        "## Platform Health Score",
        "",
        f"# {score}/100 ({grade})",
        "",
        "| Metric | Count |",
        "|---|---:|",
        f"| RED Violations | {red} |",
        f"| YELLOW Advisories | {yel} |",
        f"| GREEN Info | {grn} |",
        f"| **Total findings** | **{total}** |",
        "",
        "---",
        "",
        "## Per-Auditor Scores",
        "",
        "| Auditor | Score | Grade | RED | YEL | GRN |",
        "|---|---:|---|---:|---:|---:|",
    ]

    for audit in AUDIT_SCRIPTS:
        name = audit["name"]
        s = auditors.get(name, {})
        sc = s.get("score")
        gr = s.get("grade", "N/A")
        r = s.get("red", 0)
        y = s.get("yellow", 0)
        g = s.get("green", 0)

        if sc is not None:
            L.append(
                f"| {audit['icon']} {name} | {sc}/100 | {gr} | {r} | {y} | {g} |"
            )
        else:
            L.append(f"| {audit['icon']} {name} | N/A | N/A | - | - | - |")

    L.extend([
        "",
        "---",
        "",
        "## Priority Matrix",
        "",
        "| Priority | Count | Action |",
        "|---|---:|---|",
        f"| P0 - Fix Today | {pri.get('P0', 0)} | Production / security risk |",
        f"| P1 - Fix This Sprint | {pri.get('P1', 0)} | Scaling / performance risk |",
        f"| P2 - Fix This Month | {pri.get('P2', 0)} | Maintainability / structure |",
        f"| P3 - Fix When Convenient | {pri.get('P3', 0)} | Hygiene / style |",
    ])

    # Top unhealthiest files
    top_files = merged.get("top_files", [])
    if top_files:
        L.extend([
            "",
            "---",
            "",
            "## Top 30 Unhealthiest Files (All Auditors Combined)",
            "",
            "| # | File | Weight | Issues |",
            "|---|---|---:|---|",
        ])
        for i, f in enumerate(top_files, 1):
            codes = ", ".join(f["codes"][:8])
            if len(f["codes"]) > 8:
                codes += f" +{len(f['codes']) - 8} more"
            L.append(f"| {i} | `{f['file']}` | {f['weight']} | {codes} |")

    # RED findings hotlist
    red_findings = [
        f for f in merged["findings"] if f.get("sev") == "VIOLATION"
    ]
    if red_findings:
        L.extend([
            "",
            "---",
            "",
            f"## RED Violations ({len(red_findings)} findings)",
            "",
            "| Auditor | Rule | Domain | Location | Problem | Fix |",
            "|---|---|---|---|---|---|",
        ])
        for f in red_findings[:50]:
            icon = f.get("icon", "")
            auditor = f.get("auditor", "")
            code = f.get("code", "")
            domain = f.get("domain", "")
            path = f.get("path", "")
            line = f.get("line")
            loc = f"{path}:{line}" if line else path
            msg = f.get("message", "")
            intended = f.get("intended", "-")
            L.append(
                f"| {icon} {auditor} | {code} | {domain} "
                f"| `{loc}` | {msg} | {intended} |"
            )

    # P1 findings
    p1_findings = [
        f for f in merged["findings"]
        if f.get("priority") == "P1" and f.get("sev") != "VIOLATION"
    ]
    if p1_findings:
        L.extend([
            "",
            "---",
            "",
            f"## P1 - Fix This Sprint ({len(p1_findings)} findings)",
            "",
            "| Auditor | Rule | Domain | Location | Problem | Fix |",
            "|---|---|---|---|---|---|",
        ])
        for f in p1_findings[:40]:
            icon = f.get("icon", "")
            auditor = f.get("auditor", "")
            code = f.get("code", "")
            domain = f.get("domain", "")
            path = f.get("path", "")
            line = f.get("line")
            loc = f"{path}:{line}" if line else path
            msg = f.get("message", "")
            intended = f.get("intended", "-")
            L.append(
                f"| {icon} {auditor} | {code} | {domain} "
                f"| `{loc}` | {msg} | {intended} |"
            )

    # Domain breakdown
    domain_counts = merged.get("domain_counts", {})
    if domain_counts:
        L.extend([
            "",
            "---",
            "",
            "## Findings by Domain",
            "",
            "| Domain | Findings |",
            "|---|---:|",
        ])
        for domain, count in sorted(
            domain_counts.items(), key=lambda x: -x[1]
        ):
            L.append(f"| {domain} | {count} |")

    # Fix priority roadmap
    L.extend([
        "",
        "---",
        "",
        "## Fix Priority Roadmap",
        "",
        "### Week 1 - P0 (Production Blockers)",
        "",
    ])

    p0_findings = [
        f for f in merged["findings"] if f.get("priority") == "P0"
    ]
    if p0_findings:
        for f in p0_findings[:20]:
            icon = f.get("icon", "")
            code = f.get("code", "")
            msg = f.get("message", "")
            intended = f.get("intended", "")
            L.append(f"- {icon} **{code}**: {msg}")
            if intended:
                L.append(f"  - Fix: {intended}")
    else:
        L.append("- No P0 findings - production blockers clear")

    L.extend([
        "",
        "### Week 2-3 - P1 (Scaling / Performance)",
        "",
    ])

    if p1_findings:
        p1_by_code: dict[str, list] = defaultdict(list)
        for f in p1_findings:
            p1_by_code[f.get("code", "")].append(f)

        for code, findings in sorted(p1_by_code.items()):
            count = sum(f.get("count", 1) for f in findings)
            msg = findings[0].get("message", "")
            intended = findings[0].get("intended", "")
            L.append(f"- **{code}** ({count} findings): {msg}")
            if intended:
                L.append(f"  - Fix: {intended}")
    else:
        L.append("- No P1 findings")

    L.extend([
        "",
        "### Month 2 - P2 (Maintainability)",
        "",
        "Address P2 findings during regular development sprints.",
        "Focus on the Top 30 Unhealthiest Files first.",
        "",
        "### Ongoing - P3 (Hygiene)",
        "",
        "Fix P3 findings opportunistically during related work.",
        "",
    ])

    # AI Governance Contract
    L.extend([
        "---",
        "",
        "## AI Governance Contract",
        "",
        "**Before making ANY code change, the AI must:**",
        "",
        "1. Read this report and understand current violations",
        "2. Not introduce new P0/P1 violations",
        "3. Follow the Python + JS polyglot strategy:",
        "",
        "| Workload | Best Tool | Why |",
        "|---|---|---|",
        "| Business logic / orchestration | **Python** (FastAPI) | Readability, DB, ecosystem |",
        "| Database operations | **Python** (SQLAlchemy) | ORM, migrations, RLS |",
        "| ML / AI inference | **Python** (PyTorch) | Model ecosystem |",
        "| File / media processing | **Python worker** (Celery/arq) | Background, not request path |",
        "| High-throughput JSON | **Python + orjson** or **Node.js sidecar** | 3-10x faster |",
        "| Real-time WebSocket | **Node.js** gateway + Python backend | 100k+ connections |",
        "| Edge / CDN functions | **Node.js** (Cloudflare/Vercel) | Cold start < 5ms |",
        "| Frontend rendering | **React / Next.js** | Component model, SSR/SSG |",
        "| Client-side CPU work | **Web Worker** or **WASM** | Keep main thread free |",
        "",
        "4. Place files in correct domain folders",
        "5. Use structured logging (no print, no console.log)",
        "6. Add response_model to all new endpoints",
        "7. Use cursor pagination (never OFFSET)",
        "8. Add timeout to all external calls",
        "9. Use bulk operations (never N+1 loops)",
        "10. Run this audit before submitting: `python scripts/run_all_audits.py --no-fail`",
        "",
    ])

    # Individual report references
    L.extend([
        "---",
        "",
        "## Individual Audit Reports",
        "",
        "| Auditor | Report | JSON |",
        "|---|---|---|",
    ])

    for audit in AUDIT_SCRIPTS:
        L.append(
            f"| {audit['icon']} {audit['name']} "
            f"| `{audit['report']}` | `{audit['json']}` |"
        )

    L.extend([
        "",
        "---",
        "",
        f"*Generated by run_all_audits.py v2.0 at {merged['timestamp']}*",
        "",
    ])

    return "\n".join(L)


# ============================================================================
# 6. MAIN
# ============================================================================


def main() -> int:
    ap = argparse.ArgumentParser(
        description="ZOZI Unified Governance Orchestrator - "
                    "runs all 4 audits and merges reports."
    )
    ap.add_argument("--root", default=None, help="repo root")
    ap.add_argument("--no-fail", action="store_true", help="always exit 0")
    ap.add_argument("--ci", action="store_true", help="CI mode")
    ap.add_argument(
        "--out",
        default=None,
        help="combined report path (default: GOVERNANCE_REPORT.md)",
    )

    args = ap.parse_args()
    repo = find_repo(args.root)

    safe_print("=" * 60)
    safe_print("  ZOZI UNIFIED GOVERNANCE ORCHESTRATOR v2.0")
    safe_print("  Running all 4 audits...")
    safe_print("=" * 60)
    safe_print(f"  Repo: {repo}")

    # Run all 4 audits
    results: dict[str, dict | None] = {}

    for audit in AUDIT_SCRIPTS:
        data = run_audit(repo, audit, args.no_fail, args.ci)
        results[audit["name"]] = data

    # Merge results
    safe_print(f"\n{'=' * 60}")
    safe_print("  Merging results...")
    safe_print(f"{'=' * 60}")

    merged = merge_results(results, repo)

    # Generate combined report
    report_md = generate_combined_report(merged, repo)

    out_path = Path(args.out) if args.out else repo / "GOVERNANCE_REPORT.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report_md, encoding="utf-8")

    # Write combined JSON
    json_out = repo / "out" / "governance" / "combined.json"
    json_out.parent.mkdir(parents=True, exist_ok=True)

    # Make findings serializable
    serializable_findings = []
    for f in merged["findings"]:
        sf = dict(f)
        for k, v in sf.items():
            if isinstance(v, set):
                sf[k] = sorted(v)
        serializable_findings.append(sf)

    merged_serializable = dict(merged)
    merged_serializable["findings"] = serializable_findings

    json_out.write_text(
        json.dumps(merged_serializable, indent=2, default=str),
        encoding="utf-8",
    )

    # Print summary
    score = merged["platform_score"]
    grade = merged["platform_grade"]
    red = merged["total_red"]
    yel = merged["total_yellow"]
    grn = merged["total_green"]
    pri = merged["priority_counts"]

    safe_print(f"\n{'=' * 60}")
    safe_print(f"  PLATFORM HEALTH: {score}/100 ({grade})")
    safe_print(f"{'=' * 60}")
    safe_print(f"  RED:  {red}")
    safe_print(f"  YEL:  {yel}")
    safe_print(f"  GRN:  {grn}")
    safe_print(
        f"  P0={pri.get('P0', 0)}  P1={pri.get('P1', 0)}  "
        f"P2={pri.get('P2', 0)}  P3={pri.get('P3', 0)}"
    )
    safe_print("")

    for audit in AUDIT_SCRIPTS:
        name = audit["name"]
        s = merged["auditor_scores"].get(name, {})
        sc = s.get("score")
        gr = s.get("grade", "N/A")
        if sc is not None:
            bar_len = int(sc / 5)
            bar = "#" * bar_len + "-" * (20 - bar_len)
            safe_print(
                f"  {audit['icon']} {name:<15} [{bar}] {sc}/100 ({gr})"
            )
        else:
            safe_print(f"  {audit['icon']} {name:<15} [N/A]")

    safe_print(f"\n  Combined report: {out_path}")
    safe_print(f"  Combined JSON:   {json_out}")
    safe_print(f"{'=' * 60}")

    # Exit code
    if args.no_fail:
        return 0

    if red > 0:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())