"""Dimension 19 (performance) — static analysis unless tool output is available."""
from __future__ import annotations

import re

from zz_core.model import CheckResult, Finding, Observation, ScanContext
from zz_core.registry import check
from zz_core.util import read_text


def _f(file, line, current, target, fix, *, priority="P2", effort="M",
       laws=(), blocker="no", cluster="", truth="L0", claim="VERIFIED") -> Finding:
    return Finding(
        id="", dimension="19_performance", phase="deploy" if False else "infra",
        cluster=cluster, file=file, line=line, current=current, target=target,
        delta=current[:180], fix=fix, effort=effort, priority=priority,
        confidence=4, evidence_strength="multiple", truth_level=truth,
        claim_state=claim, completion_blocker=blocker, laws=laws, origin="static",
    )


@check("perf_bundle_and_assets", "19_performance", "frontend",
       "Bundle analysis from next build output when available; image/CDN config.")
def perf_bundle_and_assets(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="perf_bundle_and_assets", dimension="19_performance")
    build = ctx.tools.get("next:build")
    big = []
    if build is not None and getattr(build, "stdout_tail", ""):
        for line in build.stdout_tail.splitlines():
            m = re.search(r"([\d.]+)\s*kB", line)
            if m and float(m.group(1)) > 200:
                big.append(line.strip()[:160])
    if big:
        res.findings.append(_f(
            "frontend/web_app", 0,
            f"{len(big)} bundle chunk(s) exceed 200 kB (from next build output)",
            "code-split so no chunk exceeds 200 kB",
            "Dynamic-import heavy components; analyze with @next/bundle-analyzer",
            priority="P2", cluster="CLUSTER-bundle", origin="tool",
        ))
    elif build is None:
        res.observations.append(Observation(
            "build_step", "next-build", "frontend/web_app", 0, "19_performance",
            evidence="next build output not available",
        ))
        res.facts.setdefault("unverifiable", []).append(
            "bundle size: next build not run (--full + installed deps required)")
    nxt, _ = read_text(ctx.frontend / "web_app" / "next.config.ts")
    if nxt:
        if "bundle-analyzer" not in nxt and "@next/bundle-analyzer" not in nxt:
            res.findings.append(_f(
                "frontend/web_app/next.config.ts", 0,
                "no bundle analyzer configured",
                "bundle analysis available (Law 264)",
                "Add @next/bundle-analyzer for CI measurement",
                priority="P3", cluster="CLUSTER-bundle",
            ))
    # CDN config
    env, _ = read_text(ctx.root / ".env.example")
    if env and "R2_CDN_BASE" not in env and "S3_CDN_BASE" not in env:
        res.findings.append(_f(
            ".env.example", 0,
            "no CDN base URL variable documented",
            "media served via CDN (Laws 225/264)",
            "Document R2_CDN_BASE",
            priority="P3", cluster="CLUSTER-cdn",
        ))
    return res


@check("perf_cache_and_pagination", "19_performance", "infra",
       "Cache usage/TTL, pagination format on list endpoints, async processing "
       "offload (Laws 221, 237, 255).")
def perf_cache_and_pagination(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="perf_cache_and_pagination", dimension="19_performance")
    cache_hits = cursor_hits = offset_hits = count_hits = 0
    list_endpoints = 0
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if not rel.startswith("backend/"):
            continue
        text, _ = read_text(p)
        if not text:
            continue
        cache_hits += len(re.findall(r"cache\.(get|set)|valkey.*(get|set)|\.expire\(", text))
        cursor_hits += len(re.findall(r"next_cursor|cursor_paginate", text))
        offset_hits += len(re.findall(r"\.offset\(", text))
        count_hits += len(re.findall(r"\.count\(\)", text))
        if "/routers/" in rel:
            list_endpoints += len(re.findall(r"@router\.get\(", text))
    if list_endpoints and cache_hits < list_endpoints:
        res.findings.append(_f(
            "backend/", 0,
            f"cache references ({cache_hits}) below list-endpoint count ({list_endpoints})",
            "hot read paths cached with TTL + event invalidation (Law 221)",
            "Add cache-aside reads with TTL for catalog/list endpoints",
            priority="P2", cluster="CLUSTER-cache-coverage",
        ))
    if offset_hits and cursor_hits == 0:
        res.findings.append(_f(
            "backend/", 0,
            "OFFSET pagination present with no cursor pagination helper usage",
            "keyset pagination is the default (Law 222)",
            "Adopt cursor_paginate_asc for hot lists",
            priority="P1", blocker="partial", laws=(222,),
            cluster="CLUSTER-offset-pagination",
        ))
    if count_hits > 20:
        res.findings.append(_f(
            "backend/", 0,
            f"{count_hits} `.count()` calls (expensive on large tables)",
            "items + next_cursor + has_more; no count on hot lists (Law 237)",
            "Remove counts from hot list responses",
            priority="P2", laws=(237,), cluster="CLUSTER-count-queries",
        ))
    res.facts["perf"] = {
        "cache_refs": cache_hits, "cursor_refs": cursor_hits,
        "offset_refs": offset_hits, "count_refs": count_hits,
        "list_endpoints": list_endpoints,
    }
    return res


@check("perf_load_probe", "19_performance", "infra",
       "Consume the load-probe results when available; otherwise record the "
       "condition as unverifiable with the exact command.")
def perf_load_probe(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="perf_load_probe", dimension="19_performance")
    load = ctx.tools.get("load:probe")
    facts = ctx.memo("load_facts", lambda: {})
    if not facts:
        res.facts.setdefault("unverifiable", []).append(
            "p95 latency: run `python -m zz_integrations.load_probe --url <api>` "
            "against a live stack")
        return res
    p95 = facts.get("p95_ms")
    if p95 is not None and p95 > 500:
        res.findings.append(_f(
            str(facts.get("url", "")), 0,
            f"p95 latency {p95:.0f} ms exceeds 500 ms budget",
            "p95 < 500 ms at 2x expected peak (Law 73 / readiness condition 11)",
            "Profile hot endpoints; fix N+1/OFFSET; cache reads",
            priority="P1", blocker="partial", laws=(73,),
            cluster="CLUSTER-latency",
        ))
    res.facts["load"] = facts
    return res
