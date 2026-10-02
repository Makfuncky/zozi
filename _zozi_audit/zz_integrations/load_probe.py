#!/usr/bin/env python3
"""Load probe — latency sampling against a live API (optional).

Standalone:
    python _zozi_audit/zz_integrations/load_probe.py \
        --url http://127.0.0.1:8000 --paths /health,/rbac/catalog --rps 5 --seconds 20
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from zz_core.util import percentile  # noqa: E402


def _one(url: str, timeout: float) -> tuple[float, int]:
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            resp.read(1000)
            code = resp.status
    except Exception:
        code = 0
    return (time.perf_counter() - started) * 1000.0, code


def run_probe(ctx) -> dict:
    base = ctx.options.get("load_url", "http://127.0.0.1:8000")
    paths = ["/health"]
    rps = 5
    seconds = 20
    facts: dict = {"load": {}}
    latencies: list[float] = []
    errors = 0
    lock = threading.Lock()
    stop_at = time.time() + seconds
    interval = 1.0 / max(1, rps)

    def worker():
        nonlocal errors
        while time.time() < stop_at:
            for path in paths:
                ms, code = _one(base.rstrip("/") + path, timeout=10)
                with lock:
                    latencies.append(ms)
                    if code == 0 or code >= 500:
                        errors += 1
            time.sleep(interval)

    threads = [threading.Thread(target=worker, daemon=True) for _ in range(min(4, rps))]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=seconds + 30)
    if not latencies:
        facts["load_precondition"] = f"no responses from {base}"
        return facts
    facts["load"] = {
        "url": base, "paths": paths, "requests": len(latencies),
        "errors": errors,
        "p50_ms": round(percentile(latencies, 50), 1),
        "p95_ms": round(percentile(latencies, 95), 1),
        "p99_ms": round(percentile(latencies, 99), 1),
        "error_rate": round(errors / max(1, len(latencies)), 4),
    }
    out = Path(ctx.out_dir) / "logs" / "load_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(facts, indent=2), encoding="utf-8")
    return facts


def main(argv=None) -> int:
    from zz_core.model import ScanContext

    p = argparse.ArgumentParser(description="ZOZI load probe")
    p.add_argument("--root", default="")
    p.add_argument("--url", default="http://127.0.0.1:8000")
    p.add_argument("--paths", default="/health")
    args = p.parse_args(argv)
    root = Path(args.root).resolve() if args.root else HERE.parent
    ctx = ScanContext(root, root / "_zozi_audit", options={"load_url": args.url})
    facts = run_probe(ctx)
    print(json.dumps(facts.get("load", facts.get("load_precondition")), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
