#!/usr/bin/env python3
"""Browser probe — runs the Playwright suite against a live stack.

Standalone:
    python _zozi_audit/zz_integrations/browser_probe.py \
        --base-url http://127.0.0.1:3100 --api-url http://127.0.0.1:8000

Consumes `_browser_test/` when present; writes
`_zozi_audit/logs/browser_results.json` and returns facts for dimension 24.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from zz_core import tools  # noqa: E402
from zz_core.util import read_text  # noqa: E402


def _stack_alive(url: str, timeout: float = 4.0) -> bool:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status < 500
    except Exception:
        return False


def run_probe(ctx, specs: str = "all") -> dict:
    """Run Playwright and return facts for dimension 24."""
    facts: dict = {"browser_steps": []}
    browser_root = ctx.root / "_browser_test"
    config = browser_root / "playwright.config.ts"
    if not config.exists():
        facts["browser_precondition"] = (
            "phase_precondition_unmet — `_browser_test/playwright.config.ts` absent")
        return facts
    base = ctx.options.get("browser_base", "http://127.0.0.1:3100")
    if not _stack_alive(base):
        facts["browser_precondition"] = (
            f"phase_precondition_unmet — web stack not reachable at {base} "
            "(start the stack, then re-run with --browser)")
        return facts
    if not tools.which("npx"):
        facts["browser_precondition"] = "precondition_unmet — npx not installed"
        return facts
    spec_arg = {
        "all": "tests",
        "preflight": "tests/preflight.spec.ts",
        "auth": "tests/auth",
        "database": "tests/database.spec.ts",
    }.get(specs, specs)
    res = tools.run(
        f"npx playwright test {spec_arg} --reporter=json",
        cwd=browser_root, timeout=1200, name="playwright",
        env={"WEB_BASE_URL": base, "API_BASE_URL": ctx.options.get("browser_api", "http://127.0.0.1:8000")},
    )
    ctx.tools["browser:playwright"] = res
    report = browser_root / "reports" / "run" / "results.json"
    data = None
    if report.exists():
        try:
            data = json.loads(report.read_text(encoding="utf-8"))
        except Exception:
            data = None
    steps = []
    if data:
        for suite in data.get("suites", []):
            for spec in suite.get("specs", []):
                for test in spec.get("tests", []):
                    results = test.get("results") or [{}]
                    status = results[-1].get("status", "unknown")
                    steps.append({
                        "id": f"BROWSER-{len(steps)+1:03d}",
                        "step": spec.get("title", ""),
                        "expected": "pass",
                        "observed": status,
                        "status": "PASS" if status == "passed" else "FAILED",
                        "evidence": ctx.rel(report),
                    })
    elif res.exit_code != 0:
        facts["browser_precondition"] = (
            f"playwright exit={res.exit_code}; no JSON report found "
            f"(stderr: {(res.stderr_tail or '')[-200:]})")
    failures = sum(1 for s in steps if s["status"] != "PASS")
    facts["browser_steps"] = steps
    facts["browser_summary"] = {
        "source": ctx.rel(report) if report.exists() else "playwright",
        "steps": len(steps), "failures": failures,
        "exit_code": res.exit_code,
    }
    out = Path(ctx.out_dir) / "logs" / "browser_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(facts, indent=2), encoding="utf-8")
    return facts


def main(argv=None) -> int:
    from zz_core.model import ScanContext

    p = argparse.ArgumentParser(description="ZOZI browser probe")
    p.add_argument("--root", default="")
    p.add_argument("--base-url", default="http://127.0.0.1:3100")
    p.add_argument("--api-url", default="http://127.0.0.1:8000")
    p.add_argument("--specs", default="all")
    args = p.parse_args(argv)
    root = Path(args.root).resolve() if args.root else HERE.parent
    ctx = ScanContext(root, root / "_zozi_audit",
                      options={"browser_base": args.base_url, "browser_api": args.api_url})
    facts = run_probe(ctx, args.specs)
    print(json.dumps(facts.get("browser_summary", facts.get("browser_precondition")),
                     indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
