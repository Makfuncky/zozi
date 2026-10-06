#!/usr/bin/env python3
"""ZOZI Forensic Audit — main entry point.

Usage (from the repository root):

    python _zozi_audit/zozi_audit.py                 # full audit, all tools
    python _zozi_audit/zozi_audit.py --fast          # static checks only
    python _zozi_audit/zozi_audit.py --browser --llm # + browser + Ollama
    python _zozi_audit/zozi_audit.py --dimensions 01,18

Produces ONE consolidated file:

    _zozi_audit/zozi_forensic_audit.md

Supporting machine-readable logs land in `_zozi_audit/logs/`.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from zz_core import report as report_mod  # noqa: E402
from zz_core import registry, tools  # noqa: E402
from zz_core.logs import RunLog  # noqa: E402
from zz_core.model import ScanContext, ToolResult  # noqa: E402
from zz_core.util import walk_all  # noqa: E402


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="ZOZI forensic audit (single-report mode)")
    p.add_argument("--root", default="", help="repository root (default: auto)")
    p.add_argument("--out", default="", help="report path (default: _zozi_audit/zozi_forensic_audit.md)")
    p.add_argument("--workers", type=int, default=10, help="concurrent checks (max 10)")
    p.add_argument("--fast", action="store_true", help="static checks only")
    p.add_argument("--full", action="store_true", help="run every available tool (default)")
    p.add_argument("--no-tools", action="store_true", help="never spawn subprocesses")
    p.add_argument("--dimensions", default="", help="comma list e.g. 01,06,18")
    p.add_argument("--browser", action="store_true", help="run browser probe")
    p.add_argument("--browser-base", default="http://127.0.0.1:3100")
    p.add_argument("--llm", action="store_true", help="run Ollama semantic review")
    p.add_argument("--ollama-url", default="http://localhost:11434")
    p.add_argument("--ollama-model", default="phi3:mini")
    p.add_argument("--ollama-limit", type=int, default=25)
    p.add_argument("--db", action="store_true", help="run database introspection probe")
    p.add_argument("--dsn", default="", help="database DSN for the DB probe")
    p.add_argument("--load", action="store_true", help="run load probe")
    p.add_argument("--load-url", default="http://127.0.0.1:8000")
    p.add_argument("--quiet", action="store_true")
    p.add_argument("--check-timeout", type=float, default=900.0,
                   help="max wall-clock seconds for the check sweep (default 900)")
    p.add_argument("--self-test", action="store_true",
                   help="run the detector/probe regression suite and exit "
                        "(delegates to tests/run_tests.py)")
    return p.parse_args(argv)


def run_self_test() -> int:
    """Entry point for `--self-test`.

    `AUDIT_SUITE_PLAN.md` documents `zozi_audit.py --self-test` as the
    regression gate, but the flag was never implemented, so the documented
    command failed with "unrecognized arguments". It delegates to the suite
    that already exists rather than reimplementing it.
    """
    runner = HERE / "tests" / "run_tests.py"
    if not runner.exists():
        print(f"self-test runner missing: {runner}", file=sys.stderr)
        return 2
    print(f"[audit] self-test -> {runner}")
    import runpy
    try:
        runpy.run_path(str(runner), run_name="__main__")
    except SystemExit as exc:
        return int(exc.code or 0)
    return 0


def resolve_root(arg_root: str) -> Path:
    if arg_root:
        return Path(arg_root).resolve()
    # _zozi_audit/zozi_audit.py -> repo root is the parent
    return HERE.parent.resolve()


def build_context(args, root: Path, out_dir: Path) -> ScanContext:
    ctx = ScanContext(root, out_dir, options={
        "fast": bool(args.fast and not args.full),
        "workers": min(10, max(1, args.workers)),
        "no_tools": bool(args.no_tools),
        "browser": bool(args.browser),
        "browser_base": args.browser_base,
        "llm": bool(args.llm),
        "ollama_url": args.ollama_url,
        "ollama_model": args.ollama_model,
        "ollama_limit": args.ollama_limit,
        "db": bool(args.db),
        "dsn": args.dsn,
        "load": bool(args.load),
        "load_url": args.load_url,
        "quiet": bool(args.quiet),
        "dimensions": args.dimensions,
        "sweep_timeout": float(args.check_timeout or 0.0),
    })
    ctx.run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
    ctx.started_at = datetime.now(timezone.utc).isoformat()
    print(f"[audit] root={ctx.root}")
    ctx.all_files = walk_all(ctx.root)
    ctx.py_files = [p for p in ctx.all_files if p.suffix == ".py"]
    ctx.ts_files = [p for p in ctx.all_files if p.suffix in (".ts", ".tsx")]
    ctx.js_files = [p for p in ctx.all_files if p.suffix in (".js", ".jsx", ".mjs", ".cjs")]
    ctx.docs = [p for p in ctx.all_files if p.suffix in (".md", ".txt")]
    print(f"[audit] files: {len(ctx.py_files)} py · {len(ctx.ts_files)} ts/tsx · "
          f"{len(ctx.all_files)} total")
    return ctx


def merge_extra_results(base: list, extra: list) -> list:
    if not extra:
        return base
    seen = {id(r) for r in base}
    for r in extra:
        if id(r) not in seen:
            base.append(r)
    return base


def reset_generated_logs(out_dir: Path) -> list[str]:
    """Delete the previous run's per-dimension and recommendation dumps.

    `save_logs()` only writes dimensions that produced a finding, so a dimension
    that goes quiet silently keeps the file from an EARLIER run: `25_ai_drift.jsonl`
    was still dated Oct 4 beside Oct 5 findings, and `23_law_coverage.jsonl`
    survived the renumber to 29 while `29_law_coverage.jsonl` was written next to
    it. Nothing reported this, because the stale files look exactly like current
    output. `findings.jsonl` had a guard for the same class of bug; the dimension
    dumps did not.

    Returns the names removed, for the console line and the run metadata.
    """
    logs = out_dir / "logs"
    if not logs.is_dir():
        return []
    removed: list[str] = []
    for path in sorted(logs.iterdir()):
        if not path.is_file():
            continue
        name = path.name
        if (name[:2].isdigit() and name.endswith(".jsonl")) or \
                (name.startswith("rec_") and name.endswith(".jsonl")):
            try:
                path.unlink()
                removed.append(name)
            except OSError as exc:
                print(f"[audit] could not clear stale {name}: {exc}", file=sys.stderr)
    return removed


def save_logs(run_log: RunLog, ctx: ScanContext, grouped: dict, results) -> None:
    run_log.write_jsonl("findings.jsonl", [f.to_row() for f in grouped["findings"]])
    run_log.write_jsonl("observations.jsonl", [o.to_row() for o in grouped["observations"]])
    run_log.write_jsonl("recommendations.jsonl",
                        [r.to_row() for r in grouped.get("recommendations", [])])
    # Every dimension gets a file, including the ones with no findings. An
    # empty file and a missing file must not be able to mean the same thing: the
    # first says "this dimension ran and found nothing", the second used to say
    # "this dimension ran and found nothing" OR "this dimension was never run
    # this time" -- with last run's file still on disk underneath.
    by_dim: dict[str, list] = {}
    for f in grouped["findings"]:
        by_dim.setdefault(f.dimension, []).append(f.to_row())
    from zz_core.constants import DIMENSIONS
    known = [f"{num}_{name}" for num, name in DIMENSIONS]
    for dim in known:
        run_log.write_jsonl(f"{dim}.jsonl", by_dim.get(dim, []))
    for dim, rows in by_dim.items():
        if dim not in known:
            run_log.write_jsonl(f"{dim}.jsonl", rows)
    rec_by_area: dict[str, list] = {}
    for r in grouped.get("recommendations", []):
        rec_by_area.setdefault(r.area, []).append(r.to_row())
    for area, rows in rec_by_area.items():
        run_log.write_jsonl(f"rec_{area}.jsonl", rows)
    run_log.write_tool_ledger(ctx.tools)
    run_log.write("facts.json", {k: v for k, v in grouped["facts"].items()
                                 if isinstance(v, (list, dict, str, int, float, bool))})
    if ctx.errors:
        run_log.write("check_errors.json", ctx.errors)


def main(argv=None) -> int:
    args = parse_args(argv)
    started = time.time()
    if args.self_test:
        return run_self_test()
    root = resolve_root(args.root)
    if not (root / "_most_imp_docx").exists():
        print("FATAL: `_most_imp_docx/` not found — run from the repository root or pass --root.",
              file=sys.stderr)
        return 2
    out_dir = root / "_zozi_audit"
    out_dir.mkdir(parents=True, exist_ok=True)
    # A previous run's error file must never be mistaken for this run's: every
    # log that is only written conditionally is cleared before the sweep.
    stale = out_dir / "logs" / "check_errors.json"
    if stale.exists():
        stale.unlink()
    removed_stale = reset_generated_logs(out_dir)
    if removed_stale:
        print(f"[audit] cleared {len(removed_stale)} log file(s) from the previous run")
    report_path = Path(args.out) if args.out else out_dir / "zozi_forensic_audit.md"
    run_log = RunLog(out_dir, run_id="pending")
    ctx = build_context(args, root, out_dir)
    run_log = RunLog(out_dir, run_id=ctx.run_id)
    meta_extra = {}
    # The commit SHA must always be captured: without it the report cannot be
    # re-verified against a revision. Fast mode only skips the *heavy* tools.
    git = tools.run(["git", "rev-parse", "HEAD"], cwd=ctx.root, timeout=30, name="git:rev")
    ctx.tools["git:rev"] = git
    meta_extra["commit"] = ((git.stdout_tail or "").strip().splitlines() or ["unknown"])[0] \
        if git.exit_code == 0 else "unknown"
    dirty = tools.run(["git", "status", "--porcelain"], cwd=ctx.root, timeout=30, name="git:status")
    ctx.tools["git:status"] = dirty
    meta_extra["dirty_files"] = len([l for l in (dirty.stdout_tail or "").splitlines() if l.strip()])
    meta_extra["stale_logs_cleared"] = len(removed_stale)
    if not (ctx.fast or args.no_tools):
        tools.probe_all(ctx)

    # ---- Phase 0 / 0.5 preflight (must run before checks that consume tools) --
    preflight_rows: list[dict] = []
    preflight_results: list = []
    try:
        from zz_scanners import preflight
        preflight_rows, preflight_results = preflight.run_preflight(ctx)
    except Exception as exc:  # pragma: no cover
        print(f"[audit] preflight unavailable: {exc}", file=sys.stderr)

    # ---- parallel checks ------------------------------------------------------
    only = None
    if args.dimensions:
        wanted = {d.strip() for d in args.dimensions.split(",") if d.strip()}
        only = [f"{d}_{name}" for d, name in _dimension_keys() if d in wanted]
        only += [d for d in wanted]  # also match raw dimension numbers via check filter
    results = registry.run_checks(ctx, only=only, workers=ctx.workers,
                                  quick_only=False, on_progress=not args.quiet,
                                  sweep_timeout=ctx.options.get("sweep_timeout"))
    results = merge_extra_results(preflight_results, results)
    grouped = registry.group(results)
    grouped["facts"]["preflight"] = preflight_rows

    # ---- attach machine-checkable probes ------------------------------------
    # Without this, 0 findings carry a probe: `probes.attach()` had no caller in
    # the entry point, so every "probe coverage" number the suite published was
    # describing code that never ran.
    probe_report = None
    try:
        from zz_core.probes import attach as attach_probes
        probe_report = attach_probes(grouped["findings"], ctx.root)
        grouped["facts"]["probe_coverage"] = probe_report.to_dict()
        attached = probe_report.already + probe_report.attached
        print(f"[audit] probes attached {attached}/{probe_report.total} findings "
              f"({probe_report.no_rule} clusters have no rule, "
              f"{probe_report.unreadable} files unreadable, "
              f"{probe_report.zero_match} patterns matched nowhere)")
        if probe_report.builder_errors:
            # Loud on purpose. A builder exception used to abort the whole pass
            # silently: the run printed a success line while hundreds of findings
            # had no probe, and the only trace was a field nothing read.
            print(f"[audit] PROBE BUILDER ERRORS: {len(probe_report.builder_errors)} "
                  f"(probe attachment is incomplete)", file=sys.stderr)
            for msg in probe_report.builder_errors[:5]:
                print(f"[audit]   {msg}", file=sys.stderr)
    except Exception as exc:
        print(f"[audit] probe attach unavailable: {exc}", file=sys.stderr)
        grouped["facts"]["probe_coverage"] = {"error": str(exc)}

    # ---- optional integrations -------------------------------------------------
    browser_facts = llm_facts = db_facts = load_facts = None
    if args.browser and not ctx.fast:
        try:
            from zz_integrations import browser_probe
            browser_facts = browser_probe.run_probe(ctx)
        except Exception as exc:
            print(f"[audit] browser probe failed: {exc}", file=sys.stderr)
    if args.llm and not ctx.fast:
        try:
            from zz_integrations import ollama_probe
            llm_facts = ollama_probe.run_probe(ctx)
            llm_findings = ollama_probe.findings_from(llm_facts)
            if llm_findings:
                results.append(ToolResult(
                    name="llm:ollama_intent", ok=True, findings=llm_findings,
                    duration_ms=0, notes="L2 advisory findings from LLM review"))
        except Exception as exc:
            print(f"[audit] llm probe failed: {exc}", file=sys.stderr)
    if args.db and not ctx.fast:
        try:
            from zz_integrations import db_probe
            db_facts = db_probe.run_probe(ctx)
        except Exception as exc:
            print(f"[audit] db probe failed: {exc}", file=sys.stderr)
    if args.load and not ctx.fast:
        try:
            from zz_integrations import load_probe
            load_facts = load_probe.run_probe(ctx)
        except Exception as exc:
            print(f"[audit] load probe failed: {exc}", file=sys.stderr)

    # ---- report -----------------------------------------------------------------
    meta = run_log.run_metadata(ctx, extra=meta_extra)
    meta["generated_at"] = datetime.now(timezone.utc).isoformat()
    text = report_mod.build_report(ctx, meta, grouped, results,
                                   browser=browser_facts, llm=llm_facts,
                                   db=db_facts, extra=load_facts)
    report_mod.write_report(report_path, text)
    save_logs(run_log, ctx, grouped, results)
    run_log.checkpoint("final", 38, len(ctx.all_files),
                       len(grouped["findings"]))
    elapsed = time.time() - started
    blockers = sum(1 for f in grouped["findings"] if f.completion_blocker == "yes")
    print(f"[audit] DONE in {elapsed:.0f}s — {len(grouped['findings'])} findings "
          f"({blockers} yes-blockers) — report: {report_path}")
    print("[audit] authoritative outputs: zozi_forensic_audit.md (findings) · "
          "logs/findings.jsonl (machine-readable) · logs/facts.json (probe coverage)")
    print("[audit] then: zozi_verify.py  ->  zozi_compile.py")
    sys.stdout.flush()
    sys.stderr.flush()
    # A timed-out check may leave a worker thread running; exit hard so the CLI
    # never hangs after the report and logs are safely on disk.
    os._exit(3 if blockers else 0)


def _dimension_keys():
    from zz_core.constants import DIMENSIONS
    return DIMENSIONS


if __name__ == "__main__":
    sys.exit(main())
