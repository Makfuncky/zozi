"""Law-coverage accounting: the audit states what it does not check.

Motivation
----------
Measured on this repository: the benchmark defines 325 laws and the scanners
declare 114 of them. A further 127 have subject matter that a check's own brief
mentions, but nothing ties them to a law, and 84 have no check at all.

That 84 was invisible. Nothing in the output said "these rules were not
examined", so a clean-looking report could be read as "all 325 rules pass". This
module makes the gap a first-class output:

  * laws with no check        -> findings, one per area, so they enter the plan
  * laws enforced but untraced -> findings, because a finding that cannot be
                                  attributed to a law cannot be defended
  * the coverage ratio        -> facts, so a regression is measurable

The distinction that matters: `candidate_unattributed` is NOT treated as
coverage. Matching a law's wording against a check's brief is inference, and
inferring coverage would repeat the defect this suite has been removing --
reporting a claim nothing verified.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from zz_core.constants import DIMENSIONS
from zz_core.model import CheckResult, Finding, ScanContext
from zz_core.registry import check

HERE = Path(__file__).resolve().parents[1]
LAWMAP = HERE / "zz_core" / "lawmap.json"

#: Laws whose subject cannot be settled by reading source. Each needs a running
#: system, a human decision, or a tool outside this suite. Declaring them is the
#: point: an unmeasurable law must be visible, not quietly counted as passing.
NOT_STATICALLY_VERIFIABLE = {
    # needs a live system to observe
    "horizontal scaling": "requires load testing across instances",
    "capacity planning": "requires production traffic history",
    "synthetic monitoring": "requires probes running against a live deployment",
    "chaos engineering": "requires fault injection against a live system",
    "db monitoring": "requires a monitoring backend to be scraped",
    "dependency monitoring": "requires an external dependency scanner",
    "data exfiltration": "requires egress inspection, not source review",
    "adversarial detection": "requires adversarial input, not source review",
    "pen testing": "requires a human or contracted tester",
    "training": "organisational, not observable from source",
    "sustainability": "organisational, not observable from source",
    "change mgmt": "process, not observable from source",
    "release mgmt": "requires the release system, not the source tree",
    "cost allocation": "requires billing data, not source",
    "cost optimization": "requires billing data, not source",
    "disaster recovery": "requires a failover drill",
    "db failover": "requires a failover drill",
    "error budget": "requires incident history",
    "a/b testing": "requires experimentation data",
    "log aggregation": "requires a running log pipeline",
    "dashboards": "requires the observability stack to be deployed",
    "alerting tiers": "requires the paging system to be configured",
    "on-call": "organisational",
    "key rotation": "requires the secret store's audit log",
    "zero-trust": "architectural intent, not mechanically decidable",
    "session binding": "requires observing a live session",
    "tenant quotas": "requires observing enforcement under load",
    "api caching": "requires observing response headers under load",
    "partitioning": "requires observing table growth",
    "cqrs": "architectural intent; absence of markers is not proof",
    "archiving": "requires observing retention over time",
    "feature health": "requires the health dashboard",
    "per-feature fallback": "requires fault injection",
    "multi-region": "requires a second region",
    "on call": "organisational",
}


def _f(**kw):
    # The subject of these findings is the benchmark's law table, not a code
    # file. Citing a path that does not exist produced 46 spurious
    # WRONG_LOCATION verdicts, and `_zozi_audit` is excluded from the walk so
    # the verifier can never resolve it.
    base = dict(dimension="29_law_coverage", phase="defer",
                file="_most_imp_docx/ARCHITECTURE_STACK.md",
                line=0, target="every benchmark law is enforced or declared unmeasurable",
                delta="audit cannot currently enforce this law", effort="M",
                priority="P2", completion_blocker="no", truth_level="L0",
                claim_state="VERIFIED", evidence_strength="triangulated",
                origin="static")
    base.update(kw)
    return Finding(id="", **base)


@check("law_coverage_accounting", "29_law_coverage", "defer",
       "State which benchmark laws this suite enforces, which it enforces without "
       "attributing them, and which it does not check at all. A law nobody "
       "examines must appear in the output, not be counted as passing.")
def law_coverage(ctx: ScanContext) -> CheckResult:
    res = CheckResult()
    if not LAWMAP.exists():
        res.findings.append(_f(
            current="law coverage registry missing, so benchmark coverage is unknown",
            fix="regenerate zz_core/lawmap.json",
            cluster="CLUSTER-law-coverage-unknown"))
        return res
    try:
        reg = json.loads(LAWMAP.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        res.findings.append(_f(
            current=f"law coverage registry unreadable: {exc}",
            fix="regenerate zz_core/lawmap.json",
            cluster="CLUSTER-law-coverage-unknown"))
        return res

    total = int(reg.get("benchmark_laws_total") or 0)
    enforced = reg.get("enforced_by_check") or {}
    candidate = reg.get("candidate_unattributed") or {}
    gaps = [n for n in (reg.get("no_check") or [])]

    bench_text = ""
    for cand in ("_most_imp_docx/ARCHITECTURE_STACK.md",):
        p = ctx.root / cand
        if p.exists():
            bench_text = p.read_text(encoding="utf-8-sig", errors="replace")
    laws: dict[str, tuple[str, str]] = {}
    for ln in bench_text.splitlines():
        m = re.match(r"^\s*\|\s*(\d{1,3})\s*\|\s*([^|]*)\|\s*([^|]*)\|", ln)
        if m:
            laws[m.group(1)] = (m.group(2).strip(), m.group(3).strip())

    pct_enforced = round(100.0 * len(enforced) / total, 1) if total else 0.0
    pct_with_cand = (round(100.0 * (len(enforced) + len(candidate)) / total, 1)
                     if total else 0.0)
    res.facts["laws_total"] = total
    res.facts["laws_enforced"] = len(enforced)
    res.facts["laws_enforced_pct"] = pct_enforced
    res.facts["laws_candidate_unattributed"] = len(candidate)
    res.facts["laws_enforced_with_candidates_pct"] = pct_with_cand
    res.facts["laws_no_check"] = len(gaps)

    # ---- tier 1: a law nothing checks, split by whether source can decide it -
    by_area: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for n in gaps:
        area, rule = laws.get(n, ("?", "?"))
        by_area[area].append((n, rule))
    checkable, needs_runtime = [], []
    for area, items in sorted(by_area.items(), key=lambda kv: -len(kv[1])):
        for n, rule in items:
            key = re.sub(r"[^a-z ]", " ", rule.lower()).strip()
            reason = next((v for k, v in NOT_STATICALLY_VERIFIABLE.items() if k in key), None)
            (needs_runtime if reason else checkable).append((n, area, rule, reason))

    for n, area, rule, reason in needs_runtime:
        res.findings.append(_f(
            current=f"Law {n} ({area}) is not verifiable from source: {rule}",
            fix=f"verify by other means -- {reason}",
            cluster="CLUSTER-law-not-statically-verifiable",
            priority="P3", notes=f"reason={reason}"))

    if checkable:
        by_area2: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for n, area, rule, _r in checkable:
            by_area2[area].append((n, rule))
        for area, items in sorted(by_area2.items(), key=lambda kv: -len(kv[1])):
            names = ", ".join(f"{n}: {r[:44]}" for n, r in items[:6])
            more = f" (+{len(items) - 6} more)" if len(items) > 6 else ""
            res.findings.append(_f(
                current=f"{len(items)} law(s) in '{area}' have no check but ARE "
                        f"decidable from source: {names}{more}",
                fix="add a check, or declare the law non-enforceable with a reason",
                cluster="CLUSTER-law-gap-checkable",
                priority="P2", effort="L"))

    # ---- tier 2: enforced, but no finding can be attributed to the law ------
    if candidate:
        items = sorted(candidate.items(), key=lambda kv: int(kv[0]))[:12]
        sample = "; ".join(f"Law {n}: {laws.get(n, ('?', '?'))[1][:34]}" for n, _c in items)
        res.findings.append(_f(
            current=f"{len(candidate)} law(s) are enforced by a check but no finding "
                    f"cites them, so no result is attributable to them "
                    f"({100.0 * len(candidate) / max(1, total):.0f}% of the benchmark). "
                    f"Sample: {sample}",
            fix="extend `laws=(...)` on the check that actually enforces each one, so "
                "the report can attribute findings to laws",
            cluster="CLUSTER-law-unattributed",
            priority="P2", effort="M"))

    # ---- tier 3: citation drift -- a check cites a law the benchmark lacks ----
    known = set(laws)
    drift = sorted({int(n) for n in enforced} - {int(k) for k in known}) if known else []
    if drift:
        res.findings.append(_f(
            current=f"{len(drift)} law number(s) cited by a check do not exist in the "
                    f"benchmark: {drift[:12]}",
            fix="correct the `laws=(...)` tuples, or the benchmark table",
            cluster="CLUSTER-law-citation-drift", priority="P2"))
        res.facts["law_citation_drift"] = len(drift)

    return res