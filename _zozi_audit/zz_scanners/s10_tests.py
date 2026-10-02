"""Dimension 12 (tests)."""
from __future__ import annotations

import re
from pathlib import Path

from zz_core.constants import CANONICAL_DOMAINS
from zz_core.model import CheckResult, Finding, Observation, ScanContext
from zz_core.registry import check
from zz_core.util import iter_files, parse_python, read_text


def _f(dimension, phase, file, line, current, target, fix, *, priority="P2",
       effort="M", laws=(), blocker="no", cluster="", truth="L0",
       claim="VERIFIED", evidence="multiple", origin="static") -> Finding:
    return Finding(
        id="", dimension=dimension, phase=phase, cluster=cluster, file=file,
        line=line, current=current, target=target, delta=current[:180], fix=fix,
        effort=effort, priority=priority, confidence=4, evidence_strength=evidence,
        truth_level=truth, claim_state=claim, completion_blocker=blocker,
        laws=laws, origin=origin,
    )


@check("tests_inventory", "12_tests", "testing",
       "Inventory every test file: type, assertions, skips, collection errors, "
       "domain coverage, money/security path coverage, e2e presence (Laws 69-74).")
def tests_inventory(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="tests_inventory", dimension="12_tests")
    test_dirs = [ctx.backend / "tests", ctx.root / "tests"]
    files: list[Path] = []
    for d in test_dirs:
        if d.exists():
            files += [p for p in iter_files(d, (".py",))
                      if p.name.startswith("test_") or p.name.endswith("_test.py")]
    files = sorted(set(files))
    asserts = skips = xfails = parse_errors = 0
    domain_hits: dict[str, int] = {d: 0 for d in CANONICAL_DOMAINS}
    money_tests = security_tests = 0
    for p in files:
        rel = ctx.rel(p)
        parsed = parse_python(p)
        if parsed.error:
            parse_errors += 1
            res.findings.append(_f(
                "12_tests", "testing", rel, 1,
                f"test file cannot be parsed: {parsed.error[:120]}",
                "test files are syntactically valid (Law 71)",
                "Fix the syntax/import error",
                priority="P1", blocker="partial", laws=(71,),
                cluster="CLUSTER-test-broken",
            ))
            continue
        text = parsed.text
        asserts += len(re.findall(r"\bassert\b|self\.assert", text))
        skips += len(re.findall(r"pytest\.skip|@unittest\.skip|@pytest\.mark\.skip", text))
        xfails += len(re.findall(r"xfail", text))
        low = rel.lower()
        for d in CANONICAL_DOMAINS:
            if f"/{d}/" in low or f"test_{d}" in low or f"{d}_" in low:
                domain_hits[d] += 1
        if any(k in low for k in ("payment", "payout", "order", "checkout", "ledger", "finance")):
            money_tests += 1
        if any(k in low for k in ("security", "auth", "rbac", "permission", "csrf", "jwt")):
            security_tests += 1
        if not re.search(r"assert", text):
            res.findings.append(_f(
                "12_tests", "testing", rel, 1,
                "test file contains no assertions",
                "tests assert outcomes/invariants (Law 73)",
                "Add outcome assertions",
                priority="P2", cluster="CLUSTER-test-no-assert",
            ))
    uncovered = [d for d, n in domain_hits.items() if n == 0]
    if uncovered:
        res.findings.append(_f(
            "12_tests", "testing", "backend/tests/", 0,
            f"no dedicated test file found for domain(s): {', '.join(sorted(uncovered))}",
            "every domain has at least one smoke test (Law 69)",
            "Add domain smoke tests",
            priority="P1", blocker="partial", laws=(69,),
            cluster="CLUSTER-test-coverage",
        ))
    arch = ctx.backend / "tests" / "architecture"
    arch_files = list(arch.glob("test_*.py")) if arch.exists() else []
    for required in ("test_import_laws.py", "test_feature_catalog.py",
                     "test_schema_discipline.py", "test_model_relocation.py"):
        if not (arch / required).exists():
            res.findings.append(_f(
                "12_tests", "testing", f"backend/tests/architecture/{required}", 0,
                f"architecture law test `{required}` missing",
                "every statically checkable law has a test (Law 70/212)",
                f"Add {required}",
                priority="P0", blocker="yes", laws=(70, 212),
                cluster="CLUSTER-arch-tests",
            ))
    # e2e presence
    web = ctx.frontend / "web_app"
    pw_specs = [p for p in iter_files(web, (".ts",)) if p.name.endswith(".spec.ts")] \
        if web.exists() else []
    browser_specs = list((ctx.root / "_browser_test" / "tests").rglob("*.spec.ts")) \
        if (ctx.root / "_browser_test").exists() else []
    mobile = ctx.frontend / "mobile_app"
    detox = [p for p in iter_files(mobile, (".js", ".ts")) if ".e2e." in p.name] \
        if mobile.exists() else []
    res.observations.append(Observation(
        "test", "playwright", "frontend/web_app", 0, "12_tests",
        evidence=f"{len(pw_specs)} web spec(s) + {len(browser_specs)} _browser_test spec(s)",
    ))
    if not detox and mobile.exists():
        res.findings.append(_f(
            "12_tests", "mobile", "frontend/mobile_app", 0,
            "no Detox/mobile e2e specs found",
            "critical mobile paths covered by Detox (TECHNOLOGY_STACK §15)",
            "Add Detox specs for login/browse/checkout",
            priority="P2", cluster="CLUSTER-mobile-e2e",
        ))
    # collection errors from tool run
    collect = ctx.tools.get("pytest:collect")
    if collect is not None and getattr(collect, "exit_code", 0) not in (0, None):
        errors = re.findall(r"ERROR\s+(\S+)", (collect.stdout_tail or "") + (collect.stderr_tail or ""))
        if errors:
            res.findings.append(_f(
                "12_tests", "testing", errors[0], 0,
                f"{len(set(errors))} test collection error(s): {', '.join(sorted(set(errors))[:6])}",
                "full suite collects (Law 71)",
                "Fix the broken imports",
                priority="P0", blocker="yes", laws=(71,),
                cluster="CLUSTER-test-broken", origin="tool",
            ))
    res.facts["tests"] = {
        "files": len(files), "asserts": asserts, "skips": skips,
        "xfails": xfails, "parse_errors": parse_errors,
        "money_tests": money_tests, "security_tests": security_tests,
        "architecture_tests": len(arch_files),
        "playwright_specs": len(pw_specs) + len(browser_specs),
        "detox_specs": len(detox),
        "uncovered_domains": uncovered,
    }
    if money_tests == 0:
        res.findings.append(_f(
            "12_tests", "testing", "backend/tests/", 0,
            "no money-path test files detected",
            "money paths have unit + integration tests (Laws 73, 213)",
            "Add payment/order/payout tests",
            priority="P0", blocker="yes", laws=(73, 213),
            cluster="CLUSTER-test-coverage", truth="L1", claim="INFERRED",
        ))
    if security_tests == 0:
        res.findings.append(_f(
            "12_tests", "testing", "backend/tests/", 0,
            "no security-path test files detected",
            "security paths have tests (Laws 44, 213)",
            "Add auth/RBAC/CSRF tests",
            priority="P0", blocker="yes", laws=(213,),
            cluster="CLUSTER-test-coverage", truth="L1", claim="INFERRED",
        ))
    return res
