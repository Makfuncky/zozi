"""Dimension 16 (features) + Dimension 23 (code intent & feature health)."""
from __future__ import annotations

import re
from pathlib import Path

from zz_core.model import CheckResult, Finding, Observation, ScanContext
from zz_core.registry import check
from zz_core.util import feature_gate_literals, parse_python, read_text


def _f(dimension, phase, file, line, current, target, fix, *, priority="P2",
       effort="S", laws=(), blocker="no", cluster="", truth="L0",
       claim="VERIFIED", evidence="single") -> Finding:
    return Finding(
        id="", dimension=dimension, phase=phase, cluster=cluster, file=file,
        line=line, current=current, target=target, delta=current[:160], fix=fix,
        effort=effort, priority=priority, confidence=4, evidence_strength=evidence,
        truth_level=truth, claim_state=claim, completion_blocker=blocker,
        laws=laws, origin="static",
    )


@check("feat_catalog", "16_features", "arch",
       "Feature atoms from domains/*/features.py: orphans (defined, never "
       "gated), ghosts (gated, undefined), per-domain counts, feature tests, "
       "feature health score.")
def feat_catalog(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="feat_catalog", dimension="16_features")
    features: dict[str, str] = {}
    feature_line: dict[str, tuple[str, int]] = {}
    described: set[str] = set()
    for fp in ctx.backend.glob("domains/*/features.py"):
        text, _ = read_text(fp)
        if not text:
            continue
        rel = ctx.rel(fp)
        described.update(re.findall(
            r"[\"']([a-z][a-z0-9_.]*\.[a-z0-9_.]+)[\"']\s*:\s*[\"'][^\"']{8,}", text))
        for idx, line in enumerate(text.splitlines(), 1):
            m = re.match(r"\s*[\"']([a-z][a-z0-9_.]*\.[a-z0-9_.]+)[\"']\s*:", line)
            if m:
                features[m.group(1)] = rel
                feature_line[m.group(1)] = (rel, idx)
    # AST extraction, not a regex. The old pattern `[^"']+` spans newlines, so
    # an assertion or docstring that merely names `require_feature()` captured a
    # "literal" made of the following lines (FEAT-004 reported `)` + `assert
    # require_feature_count >= len(endpoints)` as an undefined atom). The same
    # helper now feeds `measurements.m_dead_feature_gate`, so detector and
    # measurement cannot disagree about what a gate literal is.
    gated: dict[str, int] = dict(feature_gate_literals(
        [p for p in ctx.py_files if "/modules/" in ctx.rel(p)]))
    orphans = sorted(set(features) - set(gated))
    ghosts = sorted(set(gated) - set(features))
    tests_text = ""
    tests_root = ctx.backend / "tests"
    if tests_root.exists():
        for p in tests_root.rglob("*.py"):
            t, _ = read_text(p)
            tests_text += (t or "")[:20000]
    health_rows = []
    for feat, rel in sorted(features.items()):
        domain = feat.split(".")[0]
        components = {
            "defined": 25,
            "gated": 25 if feat in gated else 0,
            "test_referenced": 20 if feat in tests_text else 0,
            "domain_tests": 15 if re.search(rf"test_{domain}|/{domain}/", tests_text) else 0,
            "description": 15 if feat in described else 0,
        }
        unmeasured = []
        score = sum(components.values())
        if feat not in tests_text:
            unmeasured.append("outcome assertion not located")
        health_rows.append({
            "feature": feat, "domain": domain, "score": score,
            "launch_critical": "yes" if domain in ("orders", "finance") else "no",
            "status": "LIVE" if feat in gated else "ORPHAN",
            "notes": "; ".join(unmeasured) or "all measured components present",
        })
    res.facts["feature_health"] = health_rows
    res.facts["feature_counts"] = {
        "defined": len(features), "gated": len(gated),
        "orphans": len(orphans), "ghosts": len(ghosts),
    }
    if orphans:
        sample = ", ".join(orphans[:15])
        res.findings.append(_f(
            "16_features", "arch", "backend/domains/", 0,
            f"{len(orphans)} orphan feature atom(s) defined but never gated "
            f"(e.g. {sample})",
            "every catalog atom is enforced on a route or removed (Law 4/161)",
            "Gate the atoms or delete them from the catalog",
            priority="P1", blocker="partial", laws=(4, 161),
            cluster="CLUSTER-orphan-feature",
        ))
    if ghosts:
        res.findings.append(_f(
            "16_features", "arch", "backend/modules/", 0,
            f"{len(ghosts)} gate literal(s) referenced but not defined in any "
            f"features.py: {', '.join(ghosts[:10])}",
            "require_feature literals exist in the catalog (Law 4)",
            "Add the atoms to features.py",
            priority="P1", blocker="partial", laws=(4,),
            cluster="CLUSTER-ghost-feature",
        ))
    # feature tests per domain
    missing_tests = []
    for fp in sorted(ctx.backend.glob("domains/*/features.py")):
        dom = fp.parent.name
        found = False
        if tests_root.exists():
            for t in tests_root.rglob("*.py"):
                if dom in t.name.lower():
                    found = True
                    break
        if not found:
            missing_tests.append(dom)
    if missing_tests:
        res.findings.append(_f(
            "16_features", "testing", "backend/tests/", 0,
            f"domain(s) without a dedicated feature test file: {', '.join(missing_tests)}",
            "each domain has feature tests (Law 69/213)",
            "Add feature tests per domain",
            priority="P1", blocker="partial", laws=(69, 213),
            cluster="CLUSTER-feature-tests",
        ))
    return res


@check("intent_drift", "23_code_intent", "logic",
       "Intent-vs-behaviour: live routes serving stubs, log-only handlers, "
       "'not yet wired' responses, TODO-heavy services.")
def intent_drift(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="intent_drift", dimension="23_code_intent")
    intents = []
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if not (rel.startswith("backend/modules/") or rel.startswith("backend/domains/")):
            continue
        text, _ = read_text(p)
        if not text:
            continue
        todos = len(re.findall(r"#\s*(TODO|Future:)", text))
        not_wired = len(re.findall(r"not yet wired|not yet implemented|coming soon", text, re.IGNORECASE))
        log_only = len(re.findall(r"def \w+\([^)]*\):\s*\n(?:\s*\"\"\".*?\"\"\"\s*\n)?\s*logger\.(info|warning|debug)\([^\n]*\)\s*\n\s*(?:return|$)", text))
        if todos >= 5 or not_wired or log_only >= 2:
            intents.append({
                "id": f"INTENT-{len(intents)+1:03d}",
                "location": f"{rel}:1",
                "intent": "module advertises live capability (routes/handlers)",
                "actual": (f"{todos} TODO/Future marker(s)" if todos >= 5 else "")
                          + (f"; {not_wired} not-wired placeholder(s)" if not_wired else "")
                          + (f"; {log_only} log-only handler(s)" if log_only else ""),
                "blocker": "yes" if not_wired else "partial",
                "evidence": f"{rel}:1",
            })
            if not_wired:
                res.findings.append(_f(
                    "23_code_intent", "logic", rel, 1,
                    f"{not_wired} placeholder response(s) ('not yet wired') in live module",
                    "live handlers implement the promised behaviour",
                    "Implement or remove the placeholder",
                    priority="P1", blocker="partial", cluster="CLUSTER-intent-stub",
                ))
    res.facts["intents"] = intents[:200]
    return res
