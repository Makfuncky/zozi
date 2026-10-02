"""Check registry + bounded parallel executor.

Each registered check is a self-contained "sub-agent": it receives the shared
``ScanContext``, performs one well-scoped investigation and returns findings /
observations / facts. The executor never runs more than 10 checks at once.
"""
from __future__ import annotations

import re
import sys
import time
import traceback
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import dataclass, field
from typing import Callable, Iterable

from .model import CheckResult, Finding, Observation, ScanContext


@dataclass
class Check:
    name: str
    dimension: str
    phase: str
    instructions: str
    fn: Callable[[ScanContext], CheckResult | None] | None = None
    quick: bool = False
    order: int = 0


_CHECKS: dict[str, Check] = {}
_ORDER = 0


def check(name: str, dimension: str, phase: str, instructions: str,
          quick: bool = False):
    """Register a check function. ``instructions`` is the sub-agent brief."""
    def deco(fn):
        global _ORDER
        _ORDER += 1
        _CHECKS[name] = Check(
            name=name, dimension=dimension, phase=phase,
            instructions=instructions, fn=fn, quick=quick, order=_ORDER,
        )
        return fn
    return deco


def all_checks() -> list[Check]:
    return sorted(_CHECKS.values(), key=lambda c: c.order)


def cap_workers(n: int) -> int:
    return max(1, min(10, int(n or 10)))


def _defect_result(chk: Check, msg: str, notes: str = "") -> CheckResult:
    """A check that crashed/timed out becomes an auditor-defect finding."""
    res = CheckResult(check=chk.name, dimension=chk.dimension, error=msg)
    res.findings.append(Finding(
        id="", dimension=chk.dimension, phase="defer",
        file="_zozi_audit", line=0,
        current=f"check `{chk.name}` failed: {msg}",
        target="every check must run to completion",
        delta="audit check failure (auditor defect, not necessarily a codebase defect)",
        fix="Fix the check implementation, then re-run the audit",
        effort="S", priority="P3", confidence=5, evidence_strength="triangulated",
        truth_level="L0", claim_state="VERIFIED",
        completion_blocker="no", notes=notes[:1000], origin="static",
    ))
    return res


def _run_one(ctx: ScanContext, chk: Check) -> CheckResult:
    started = time.time()
    try:
        res = chk.fn(ctx) if chk.fn else None
        if res is None:
            res = CheckResult(check=chk.name, dimension=chk.dimension)
        res.check = chk.name
        if not res.dimension:
            res.dimension = chk.dimension
        res.facts.setdefault("_duration_s", round(time.time() - started, 2))
        return res
    except Exception as exc:  # a broken check must never kill the audit
        err = f"{type(exc).__name__}: {exc}"
        tb = traceback.format_exc(limit=6)
        ctx.errors.append(f"check {chk.name}: {err}\n{tb}")
        return _defect_result(chk, f"crashed: {err}", tb)


def run_checks(ctx: ScanContext, only: Iterable[str] | None = None,
               workers: int = 10, quick_only: bool = False,
               on_progress: bool = True,
               sweep_timeout: float | None = None) -> list[CheckResult]:
    """Run every selected check in a bounded pool (never more than 10 at once).

    ``sweep_timeout`` caps the wall-clock time spent waiting for the pool; a
    check that overruns is reported as an auditor defect instead of hanging the
    whole audit forever.
    """
    checks = all_checks()
    if only:
        wanted = {c.strip() for c in only}
        checks = [c for c in checks if c.name in wanted or c.dimension in wanted]
    if quick_only:
        checks = [c for c in checks if c.quick]
    results: list[CheckResult] = []
    workers = cap_workers(workers)
    total = len(checks)
    started = time.time()
    if on_progress:
        print(f"[audit] running {total} checks with {workers} workers", file=sys.stderr)
    if sweep_timeout is None:
        sweep_timeout = float(ctx.options.get("sweep_timeout", 0) or 0) or None
    pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="zozi-audit")
    futures = {pool.submit(_run_one, ctx, c): c for c in checks}
    done = 0
    pending = set(futures)
    deadline = (started + sweep_timeout) if sweep_timeout else None
    try:
        while pending:
            remaining = None
            if deadline is not None:
                remaining = max(0.0, deadline - time.time())
            finished, pending = wait(pending, timeout=remaining,
                                     return_when=FIRST_COMPLETED)
            for fut in finished:
                chk = futures[fut]
                try:
                    res = fut.result()
                except Exception as exc:  # pragma: no cover
                    res = _defect_result(chk, f"executor error: {type(exc).__name__}: {exc}")
                results.append(res)
                done += 1
                if on_progress:
                    print(f"[audit] {done}/{total} {chk.name} "
                          f"({len(res.findings)} findings, "
                          f"{round(time.time() - started, 1)}s)", file=sys.stderr)
            if deadline is not None and time.time() >= deadline and pending:
                break
    finally:
        if pending:
            for fut in pending:
                chk = futures[fut]
                fut.cancel()
                msg = f"timeout after {sweep_timeout:.0f}s (check still running)"
                ctx.errors.append(f"check {chk.name}: {msg}")
                results.append(_defect_result(chk, msg))
                if on_progress:
                    print(f"[audit] TIMEOUT {chk.name}", file=sys.stderr)
        pool.shutdown(wait=False, cancel_futures=True)
    return results


def dedupe_findings(findings: list[Finding]) -> list[Finding]:
    """Stable dedupe on (file, line, current, target); keep the strongest."""
    best: dict[tuple, Finding] = {}
    rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    for f in findings:
        key = (f.file, f.line, (f.current or "")[:180], (f.target or "")[:120])
        prev = best.get(key)
        if prev is None:
            best[key] = f
            continue
        if (rank.get(f.priority, 9), -f.confidence) < (rank.get(prev.priority, 9), -prev.confidence):
            best[key] = f
    return list(best.values())


def assign_ids(findings: list[Finding]) -> list[Finding]:
    """Assign stable IDs per dimension prefix when a check did not set one."""
    from .constants import ID_PREFIX_BY_DIMENSION

    counters: dict[str, int] = {}
    for f in findings:
        if f.id:
            prefix = f.id.split("-")[0]
            try:
                counters[prefix] = max(counters.get(prefix, 0), int(f.id.split("-")[-1]))
            except ValueError:
                counters[prefix] = counters.get(prefix, 0) + 1
    for f in findings:
        if f.id:
            continue
        prefix = ID_PREFIX_BY_DIMENSION.get(f.dimension, "FIND")
        counters[prefix] = counters.get(prefix, 0) + 1
        f.id = f"{prefix}-{counters[prefix]:03d}"
    return findings


def group(results: list[CheckResult]) -> dict:
    """Merge all check results into a report-ready structure."""
    findings: list[Finding] = []
    observations: list[Observation] = []
    recommendations: list = []
    facts: dict = {}
    warnings: list[str] = []
    by_dimension: dict[str, dict] = {}
    for res in results:
        for item in res.findings:
            if isinstance(item, Finding):
                findings.append(item)
            else:
                warnings.append(f"check {res.check}: dropped non-Finding item "
                                f"({type(item).__name__})")
        for item in res.observations:
            if isinstance(item, Observation):
                observations.append(item)
            else:
                warnings.append(f"check {res.check}: dropped non-Observation item "
                                f"({type(item).__name__})")
        for item in res.recommendations:
            title = getattr(item, "title", "")
            if not title:
                warnings.append(f"check {res.check}: dropped recommendation "
                                f"without a title")
                continue
            recommendations.append(item)
        for key, value in res.facts.items():
            if key in facts and isinstance(facts[key], list) and isinstance(value, list):
                facts[key].extend(value)
            elif key in facts and isinstance(facts[key], dict) and isinstance(value, dict):
                facts[key].update(value)
            else:
                facts.setdefault(key, value)
    findings = assign_ids(dedupe_findings(findings))
    for f in findings:
        slot = by_dimension.setdefault(f.dimension, {"findings": [], "observations": []})
        slot["findings"].append(f)
    for o in observations:
        slot = by_dimension.setdefault(o.dimension, {"findings": [], "observations": []})
        slot["observations"].append(o)
    recs = assign_recommendation_ids(dedupe_recommendations(recommendations))
    return {"findings": findings, "observations": observations,
            "recommendations": recs, "facts": facts,
            "by_dimension": by_dimension, "warnings": warnings}


def dedupe_recommendations(recs: list) -> list:
    """Stable dedupe on (area, title); keep the highest-confidence instance."""
    best: dict[tuple, object] = {}
    for r in recs:
        key = (r.area, (r.title or "")[:120])
        prev = best.get(key)
        if prev is None or r.confidence > prev.confidence:
            best[key] = r
    return list(best.values())


def assign_recommendation_ids(recs: list) -> list:
    """Number recommendations REC-<area>-NNN so the compiler can reference them."""
    counters: dict[str, int] = {}
    for r in recs:
        area = re.sub(r"[^a-z0-9]+", "", (r.area or "gen").lower()) or "gen"
        counters[area] = counters.get(area, 0) + 1
        r.id = f"REC-{area.upper()}-{counters[area]:03d}"
    return recs
