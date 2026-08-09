#!/usr/bin/env python
"""
CI Gate — Schema Audit Deployment Check
========================================

Runs ``python -m utils.schema_audit --json`` and exits with a non-zero
code when ORM/database drift or Alembic migration-tree issues are found.

Use as a **deployment gate** — if this script fails, the release pipeline
should halt until the schema is reconciled.

Usage
-----
    python scripts/schema_audit_ci.py
        Runs the full audit.  Exits 0 if healthy, 1 if issues found.

    python scripts/schema_audit_ci.py --fail-on priority:2
        Exits non-zero only for priority 1 (table) and 2 (column) issues.
        Priority levels: 1=tables/migrations, 2=columns, 3=types/indexes/FKs, 4=defaults

    python scripts/schema_audit_ci.py --fail-on alembic
        Only fails on Alembic migration-tree issues (stamp, head, linearity).

    python scripts/schema_audit_ci.py --json
        Outputs the full JSON audit report to stdout.

    python scripts/schema_audit_ci.py --github-annotation
        Emits GitHub Workflow Command annotations for each issue.

    python scripts/schema_audit_ci.py --webhook-url https://hooks.slack.com/...
        Sends a Slack notification when the audit fails.

Exit Codes
----------
0 — Schema is healthy (no issues, or only issues below the ``--fail-on`` threshold)
1 — Schema drift or migration-tree issues detected (deployment gate BLOCKED)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any

# ── Ensure the backend root PYTHONPATH works ──────────────────────────────
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("PYTHONPATH", str(_BACKEND_ROOT))
sys.path.insert(0, str(_BACKEND_ROOT))


def _run_audit() -> dict[str, Any]:
    """Run ``python -m utils.schema_audit --json`` and return the parsed dict."""
    result = subprocess.run(
        [sys.executable, "-m", "utils.schema_audit", "--json"],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(_BACKEND_ROOT),
        env={**os.environ, "PYTHONPATH": str(_BACKEND_ROOT)},
    )

    if result.returncode == 0:
        stderr = result.stderr.strip()
        # Filter out non-JSON lines (e.g. "FIELD_ENCRYPTION_KEY not set")
        json_lines = []
        for line in result.stdout.splitlines():
            stripped = line.strip()
            if stripped.startswith("{"):
                json_lines.append(stripped)
        if json_lines:
            return json.loads("".join(json_lines))
        return {"error": f"No JSON output from audit subprocess (exit {result.returncode})"}

    # Non-zero exit code means issues were found — JSON is on stdout
    json_str = result.stdout.strip()
    if json_str:
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Fall through — try stderr
            pass
    for line in result.stderr.splitlines():
        stripped = line.strip()
        if stripped.startswith("{"):
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                continue

    stderr_msg = result.stderr.strip() or "(no output)"
    return {
        "error": f"Audit subprocess failed (exit {result.returncode}): {stderr_msg}",
        "healthy": False,
        "issue_count": -1,
    }


def _should_fail(report: dict[str, Any], fail_on: str) -> bool:
    """Determine whether the issues in *report* exceed the *fail_on* threshold.

    *fail_on* can be:
    - ``"any"`` — fail on any issue
    - ``"alembic"`` — fail only on Alembic migration-tree issues
    - ``"priority:N"`` — fail on issues with priority <= N (1=highest, 4=lowest)
    """
    issues: list[dict[str, Any]] = report.get("issues", [])

    if not issues:
        return False

    if fail_on == "any":
        return True

    if fail_on == "alembic":
        alembic_kinds = {
            "alembic_stamp_missing",
            "alembic_head_mismatch",
            "alembic_tree_not_linear",
            "alembic_multiple_roots",
            "alembic_multiple_heads",
        }
        return any(i.get("kind") in alembic_kinds for i in issues)

    if fail_on.startswith("priority:"):
        try:
            max_priority = int(fail_on.split(":", 1)[1])
        except (ValueError, IndexError):
            max_priority = 4  # default: all priorities
        # Priority mapping (same as schema_audit.py)
        priority_map: dict[str, int] = {
            "table_missing_in_db": 1,
            "table_extra_in_db": 1,
            "alembic_stamp_missing": 1,
            "alembic_head_mismatch": 1,
            "alembic_tree_not_linear": 1,
            "alembic_multiple_roots": 1,
            "alembic_multiple_heads": 1,
            "column_missing_in_db": 2,
            "column_extra_in_db": 2,
            "column_type_mismatch": 3,
            "column_nullable_mismatch": 3,
            "index_missing_in_db": 3,
            "index_extra_in_db": 3,
            "fk_missing_in_db": 3,
            "fk_extra_in_db": 3,
            "column_default_mismatch": 4,
            "index_columns_mismatch": 4,
            "index_unique_mismatch": 4,
            "fk_columns_mismatch": 4,
            "db_connection_error": 0,
        }
        for issue in issues:
            kind = issue.get("kind", "")
            pri = priority_map.get(kind, 99)
            if pri <= max_priority:
                return True
        return False

    return True  # unknown fail_on value — fail safe


def _emit_github_annotations(report: dict[str, Any]) -> None:
    """Print GitHub Workflow Command annotations for each issue.

    See: https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions
    """
    issues: list[dict[str, Any]] = report.get("issues", [])
    for issue in issues:
        kind = issue.get("kind", "unknown")
        table = issue.get("table", "")
        column = issue.get("column", "")
        detail = issue.get("detail", "")
        msg = f"[{kind}] {table}"
        if column:
            msg += f".{column}"
        if detail:
            msg += f" — {detail}"
        # Limit message length for GitHub annotations
        msg = msg[:200]
        print(f"::warning title=Schema Audit::{msg}")


def _notify_slack(report: dict[str, Any], webhook_url: str) -> None:
    """Send a Slack notification when the audit fails."""
    issue_count = report.get("issue_count", 0)
    healthy = report.get("healthy", True)
    alembic = report.get("alembic", {})

    if healthy:
        return

    lines = [f"❌ *Schema Audit Failed* — {issue_count} issue(s) found"]
    if alembic:
        stamp = alembic.get("stamped_version", "N/A")
        head = alembic.get("head_version", "N/A")
        lines.append(f"• Alembic: stamp=`{stamp}` head=`{head}`")

    # Group issues by kind
    issues: list[dict[str, Any]] = report.get("issues", [])
    kind_counts: dict[str, int] = {}
    for issue in issues:
        k = issue.get("kind", "unknown")
        kind_counts[k] = kind_counts.get(k, 0) + 1

    if kind_counts:
        lines.append("• Issues:")
        for kind, count in sorted(kind_counts.items(), key=lambda x: -x[1]):
            lines.append(f"  · `{kind}`: {count}")

    payload = json.dumps({"text": "\n".join(lines), "mrkdwn": True}).encode("utf-8")
    try:
        req = urllib.request.Request(
            webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as exc:
        print(f"[ci_schema_audit] Slack notification failed: {exc}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="CI Gate — Schema Audit Deployment Check",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--fail-on",
        default="any",
        help=(
            "When to fail the CI check.  Options: "
            "'any' (default, fail on any issue), "
            "'alembic' (fail only on migration-tree issues), "
            "'priority:N' (fail on issues with priority <= N)"
        ),
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Print the full JSON audit report to stdout",
    )
    p.add_argument(
        "--github-annotation",
        action="store_true",
        help="Emit GitHub Workflow Command annotations for each issue",
    )
    p.add_argument(
        "--webhook-url",
        type=str,
        default=None,
        help="Slack webhook URL for failure notifications",
    )
    args = p.parse_args(argv)

    # Support reading piped JSON (from stdin) for --github-annotation
    if args.github_annotation and not sys.stdin.isatty():
        try:
            report = json.load(sys.stdin)
        except json.JSONDecodeError as exc:
            print(f"[ci_schema_audit] Failed to parse stdin JSON: {exc}", file=sys.stderr)
            return 2
    else:
        report = _run_audit()

    if args.json:
        print(json.dumps(report, indent=2))

    # Error running the audit itself
    if "error" in report:
        print(f"[ci_schema_audit] {report['error']}", file=sys.stderr)
        return 2

    # Emit GitHub annotations
    if args.github_annotation:
        _emit_github_annotations(report)

    # Send Slack notification
    if args.webhook_url and not report.get("healthy", True):
        _notify_slack(report, args.webhook_url)

    # Determine exit code
    if _should_fail(report, args.fail_on):
        print(
            f"[ci_schema_audit] BLOCKED — {report.get('issue_count', 0)} issue(s) found "
            f"(fail_on={args.fail_on})",
            file=sys.stderr,
        )
        return 1

    print("[ci_schema_audit] PASSED — schema is healthy")
    return 0


if __name__ == "__main__":
    sys.exit(main())
