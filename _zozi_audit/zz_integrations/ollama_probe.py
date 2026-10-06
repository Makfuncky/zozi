#!/usr/bin/env python3
"""Ollama probe — local-LLM semantic review of audit hotspots.

Standalone:
    python _zozi_audit/zz_integrations/ollama_probe.py \
        --url http://localhost:11434 --model phi3:mini --limit 25

Selects deterministic hotspots (large/stub-heavy/money/security files), asks
strict-JSON questions, caches results, and writes `logs/llm_results.json`.
LLM findings are L2/INFERRED and can never be promoted to L0.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from zz_core import tools  # noqa: E402
from zz_core.util import read_text  # noqa: E402

PROMPT = """You are a forensic code auditor. Analyse the file excerpt and answer ONLY with JSON:
{{"verdict":"ok|suspicious|broken","intent":"what the code tries to do","actual":"what it actually does",
"drift":"any comment/docstring vs behaviour divergence or empty",
"completion_impact":"yes|no|partial","evidence_lines":"line hints","confidence":1}}
Rules: do not invent behaviour you cannot see; if the excerpt is insufficient answer "suspicious" with confidence 1.

FILE: {path}
EXCERPT:
{excerpt}
"""


def _hotspots(ctx, limit: int) -> list[Path]:
    scored: list[tuple[float, Path]] = []
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if not any(rel.startswith(f"backend/{d}/") for d in
                   ("domains", "modules", "infrastructure", "providers", "jobs", "middleware")):
            continue
        text, _ = read_text(p)
        if not text or len(text) < 800:
            continue
        score = 0.0
        score += min(60, len(text) / 2000)
        score += 10 * len(re.findall(r"#\s*(TODO|Future:)", text))
        score += 15 * len(re.findall(r"NotImplementedError", text))
        score += 8 * len(re.findall(r"not yet wired|not yet implemented", text, re.IGNORECASE))
        low = rel.lower()
        if any(k in low for k in ("payment", "payout", "ledger", "refund", "tax")):
            score += 40
        if any(k in low for k in ("auth", "security", "rls")):
            score += 25
        scored.append((score, p))
    scored.sort(key=lambda kv: -kv[0])
    return [p for _s, p in scored[:limit]]


def run_probe(ctx, limit: int | None = None) -> dict:
    limit = limit or int(ctx.options.get("ollama_limit", 25))
    facts: dict = {"llm_reviews": []}
    hotspots = _hotspots(ctx, limit)
    if not hotspots:
        facts["llm_precondition"] = "no hotspots selected"
        return facts
    cache_path = Path(ctx.out_dir) / "logs" / "llm_cache.json"
    cache = {}
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8-sig"))
        except Exception:
            cache = {}
    reviewed = 0
    for p in hotspots:
        rel = ctx.rel(p)
        text, _ = read_text(p, max_bytes=12000)
        key = f"{rel}:{len(text)}"
        if key in cache:
            answer = cache[key]
        else:
            ok, raw = tools.ollama_chat(
                ctx, PROMPT.format(path=rel, excerpt=(text or "")[:6000]),
                timeout=180)
            if not ok:
                facts["llm_precondition"] = raw
                break
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            answer = {}
            if match:
                try:
                    answer = json.loads(match.group(0))
                except Exception:
                    answer = {"verdict": "unparsable", "raw": raw[:300]}
            else:
                answer = {"verdict": "unparsable", "raw": raw[:300]}
            cache[key] = answer
        reviewed += 1
        facts["llm_reviews"].append({
            "path": rel, "verdict": answer.get("verdict", "unknown"),
            "intent": answer.get("intent", ""),
            "actual": answer.get("actual", ""),
            "drift": answer.get("drift", ""),
            "completion_impact": answer.get("completion_impact", "no"),
            "confidence": answer.get("confidence", 1),
            "evidence_lines": answer.get("evidence_lines", ""),
        })
    cache_path.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    facts["llm_summary"] = {"reviewed": reviewed, "model": ctx.options.get("ollama_model", "")}
    out = Path(ctx.out_dir) / "logs" / "llm_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(facts, indent=2, default=str), encoding="utf-8")
    return facts


def findings_from(facts: dict, dimension: str = "23_code_intent") -> list:
    from zz_core.model import Finding
    out = []
    for i, r in enumerate(facts.get("llm_reviews", []), 1):
        if r.get("verdict") not in ("suspicious", "broken"):
            continue
        out.append(Finding(
            id=f"INTENT-LLM-{i:03d}", dimension=dimension, phase="logic",
            cluster="CLUSTER-llm-review", file=r["path"], line=0,
            current=f"LLM verdict={r['verdict']}: {r.get('drift') or r.get('actual','')[:150]}",
            target="code behaviour matches its stated intent",
            delta="LLM-flagged intent/behaviour divergence (L2 only)",
            fix="Manually verify the flagged file and fix or dismiss",
            effort="S", priority="P2", confidence=2, evidence_strength="single",
            truth_level="L2", claim_state="INFERRED", completion_blocker="partial",
            origin="llm", notes=str(r.get("evidence_lines", "")),
        ))
    return out


def main(argv=None) -> int:
    from zz_core.model import ScanContext

    p = argparse.ArgumentParser(description="ZOZI Ollama probe")
    p.add_argument("--root", default="")
    p.add_argument("--url", default="http://localhost:11434")
    p.add_argument("--model", default="phi3:mini")
    p.add_argument("--limit", type=int, default=25)
    args = p.parse_args(argv)
    root = Path(args.root).resolve() if args.root else HERE.parent
    ctx = ScanContext(root, root / "_zozi_audit",
                      options={"ollama_url": args.url, "ollama_model": args.model,
                               "ollama_limit": args.limit})
    facts = run_probe(ctx)
    print(json.dumps(facts.get("llm_summary", facts.get("llm_precondition")),
                     indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
