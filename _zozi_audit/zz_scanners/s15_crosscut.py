"""Cross-cutting: chains (dim 10-style), contradictions (21), anti-patterns (22),
browser bridge (24), completion-blocker readiness signals (27)."""
from __future__ import annotations

import json
import re
from pathlib import Path

from zz_core.model import CheckResult, Finding, Observation, ScanContext
from zz_core.registry import check
from zz_core.util import read_text


def _f(dimension, phase, file, current, target, fix, *, priority="P1",
       blocker="partial", cluster="", truth="L1", claim="INFERRED",
       notes="") -> Finding:
    return Finding(
        id="", dimension=dimension, phase=phase, cluster=cluster, file=file,
        line=0, current=current, target=target, delta=current[:180], fix=fix,
        effort="L", priority=priority, confidence=3, evidence_strength="multiple",
        truth_level=truth, claim_state=claim, completion_blocker=blocker,
        origin="static", notes=notes,
    )


CHAINS = [
    ("CHAIN-001", "Customer order placement (multi-supplier)", ["customer"],
     ["orders", "catalog", "promotions", "finance", "comms", "audit"],
     "POST /api/v1/customer/orders/orders",
     ["create_order", "_rollback_order_creation", "confirm_cash_on_delivery_order"],
     ["orders.order.created"]),
    ("CHAIN-002", "Supplier payout", ["supplier", "admin"],
     ["finance", "suppliers", "bank"], "admin payout routes",
     ["generate_supplier_payout_batches", "payout", "reconciliation"],
     ["finance.payout.created"]),
    ("CHAIN-003", "Return and refund", ["customer", "admin"],
     ["orders", "finance", "logistics"], "return request routes",
     ["update_return_request", "refund_order", "refund"], ["orders.refund.posted"]),
    ("CHAIN-004", "Logistics pickup and delivery", ["logistics"],
     ["logistics", "orders"], "logistics shipment routes",
     ["create_shipment", "pickup", "deliver"], ["logistics.shipment.created"]),
    ("CHAIN-005", "Admin ledger posting and reconciliation", ["admin"],
     ["finance", "audit"], "admin ledger routes",
     ["create_journal_entry", "reconcile"], ["finance.journal.posted"]),
    ("CHAIN-006", "Customer registration and KYC", ["customer"],
     ["accounts", "customers", "security"], "register route",
     ["register_user", "otp", "kyc"], ["accounts.customer.registered"]),
    ("CHAIN-007", "Supplier onboarding and first product listing", ["supplier"],
     ["suppliers", "catalog"], "supplier onboarding routes",
     ["register_supplier", "supplier_documents", "create_product"],
     ["suppliers.supplier.registered", "catalog.product.created"]),
]


@check("cross_chains", "27_project_completion_blockers", "arch",
       "Trace the 7 critical chains: entry, steps, events, tests, rollback; "
       "verdict COMPLETE/PARTIAL/BROKEN/MISSING with evidence.")
def cross_chains(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="cross_chains", dimension="27_project_completion_blockers")
    all_text_cache: dict[str, str] = {}
    tests_text = ""
    tests_root = ctx.backend / "tests"
    if tests_root.exists():
        for p in tests_root.rglob("*.py"):
            t, _ = read_text(p)
            if t and len(tests_text) < 3_000_000:
                tests_text += t
    chain_rows = []
    for cid, name, actors, domains, entry, step_names, event_names in CHAINS:
        found_steps = []
        for step in step_names:
            hit = None
            for d in domains:
                for p in (ctx.backend / "domains" / d).rglob("*.py"):
                    rel = ctx.rel(p)
                    if rel not in all_text_cache:
                        t, _ = read_text(p)
                        all_text_cache[rel] = t or ""
                    if step in all_text_cache[rel]:
                        hit = f"{rel}"
                        break
                if hit:
                    break
            found_steps.append({"actor": actors[0], "expected": step,
                                "evidence": hit or "not located",
                                "status": "found" if hit else "missing"})
        events_found = []
        for ev in event_names:
            for p in (ctx.backend / "domains").glob("*/events.py"):
                t, _ = read_text(p)
                if ev in (t or ""):
                    events_found.append(f"{ctx.rel(p)}")
                    break
        steps_found = sum(1 for s in found_steps if s["status"] == "found")
        happy = "verified" if steps_found == len(step_names) else (
            "partial" if steps_found else "broken")
        rollback = "verified" if any("rollback" in s["expected"] for s in found_steps if s["status"] == "found") else "partial"
        failure = "partial"
        tests_found = any(step in tests_text for step in step_names[:2])
        verdict = "PARTIAL" if steps_found else "MISSING"
        if steps_found == len(step_names) and events_found and tests_found:
            verdict = "COMPLETE"
        chain_rows.append({
            "id": cid, "name": name, "actors": actors, "domains": domains,
            "entry": entry, "happy": happy, "failure": failure,
            "rollback": rollback, "verdict": verdict, "critical": "yes",
            "steps": found_steps,
            "findings": [
                (f"event {'present' if events_found else 'NOT published'}: "
                 f"{', '.join(event_names)}"),
                (f"integration test {'located' if tests_found else 'not located'}"),
            ],
        })
        if verdict != "COMPLETE":
            res.findings.append(_f(
                "27_project_completion_blockers", "logic",
                f"backend/domains/{domains[0]}/",
                f"{cid} ({name}) is {verdict}: {steps_found}/{len(step_names)} steps located; "
                f"events {len(events_found)}/{len(event_names)}; tests={'yes' if tests_found else 'no'}",
                "chain has happy path + failure path + rollback + tests",
                "Implement the missing steps/events and add a chain integration test",
                priority="P0" if cid in ("CHAIN-001", "CHAIN-005") else "P1",
                blocker="yes" if cid in ("CHAIN-001", "CHAIN-005") else "partial",
                cluster="CLUSTER-chain-" + cid.lower(),
                # The probe needs the event name to re-derive independently;
                # without it the finding is an unadjudicable "events 0/1".
                notes=f"chain={cid}; events={','.join(event_names)}; "
                      f"actors={','.join(actors)}",
            ))
    res.facts["chains"] = chain_rows
    return res


@check("cross_contradictions", "21_contradictions", "arch",
       "Harvest target-vs-code contradictions with Source A / Source B; never "
       "silently resolve.")
def cross_contradictions(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="cross_contradictions", dimension="21_contradictions")
    items = list(res.facts.get("contradictions", []))

    def add(cid, category, a, a_says, b, b_says, conflict, impact, blocker,
            decision="no"):
        items.append({
            "id": cid, "category": category, "source_a": a, "a_says": a_says,
            "source_b": b, "b_says": b_says, "conflict": conflict,
            "impact": impact, "blocker": blocker, "user_decision": decision,
        })

    # extra module
    if (ctx.backend / "modules" / "finance").exists():
        add("CONTRAD-001", "target_vs_code",
            "_most_imp_docx/ARCHITECTURE_STACK.md (Law 13)",
            "fixed 5 modules", "backend/modules/finance/",
            "a 6th module directory exists",
            "canonical module set violated",
            "extra actor surface outside the documented boundaries", "yes", "yes")
    # extra domain
    for extra in ("payments", "media"):
        if (ctx.backend / "domains" / extra).exists():
            add(f"CONTRAD-00{2 if extra == 'payments' else 3}", "target_vs_code",
                "_most_imp_docx/ARCHITECTURE_STACK.md (Law 12)",
                "fixed 15 domains", f"backend/domains/{extra}/",
                f"domain package `{extra}` exists",
                f"`{extra}` has no canonical domain slot",
                "domain count and ownership boundaries drift", "yes" if extra == "payments" else "partial",
                "yes")
    # float money config
    cfg, _ = read_text(ctx.backend / "config.py")
    if cfg and re.search(r"(vat_rate|commission_rate)\s*:\s*float", cfg):
        add("CONTRAD-020", "target_vs_code", "Law 19", "no float for money",
            "backend/config.py", "vat_rate/commission_rate typed float",
            "money config uses float", "rounding drift in tax/commission", "yes", "no")
    # frontend zod major
    from zz_core.util import parse_package_json
    pkg = parse_package_json(ctx.frontend / "web_app" / "package.json")
    zod = (pkg.get("dependencies") or {}).get("zod", "")
    if zod and str(zod).lstrip("^~")[:1] == "3":
        add("CONTRAD-024", "tech_target_vs_lockfile", "TECHNOLOGY_STACK.md",
            "zod 4.3.6", "frontend/web_app/package.json", f"zod {zod}",
            "major-version drift", "different validation semantics", "yes", "no")
    # /hr rewrite without hr module
    nxt, _ = read_text(ctx.frontend / "web_app" / "next.config.ts")
    if nxt and re.search(r"source:\s*['\"]/hr", nxt) and not (ctx.backend / "modules" / "hr").exists():
        add("CONTRAD-029", "frontend_vs_backend", "Law 13 (5 modules)",
            "no standalone hr module", "frontend/web_app/next.config.ts",
            "/hr/* rewrite exists",
            "frontend routes to a non-canonical backend surface",
            "404s or unauthorized surface", "yes", "yes")
    # hr.py shadowed by package
    emp = ctx.backend / "modules" / "employee" / "routers"
    if (emp / "hr.py").exists() and (emp / "hr").is_dir():
        add("CONTRAD-034", "doc_vs_code", "one router per module",
            "every router file registered", ctx.rel(emp),
            "hr.py file and hr/ package coexist",
            "shadowed router file is unreachable", "guaranteed dead route", "yes",
            "no")
    # lockfile vs manifest
    uv = ctx.backend / "uv.lock"
    uv_text, _ = read_text(uv)
    if uv.exists() and len(re.findall(r"^\[\[package\]\]", uv_text or "", re.MULTILINE)) < 10:
        add("CONTRAD-lockfile", "package_vs_import", "TECHNOLOGY_STACK.md §19",
            "uv.lock is the dependency lockfile", "backend/uv.lock",
            "uv.lock has <10 package entries (pip is the real manager)",
            "declared dependency management differs from practice",
            "reproducibility/supply chain", "yes", "no")
    res.facts["contradictions"] = items
    # Every contradiction must also be a first-class finding in dimension 21,
    # otherwise the dimension renders "PASS (no findings)" while the report
    # body lists contradictions. One finding per contradiction, ID preserved.
    for item in items:
        res.findings.append(Finding(
            id=str(item["id"]),
            dimension="21_contradictions",
            phase="arch",
            cluster=f"CLUSTER-contradiction-{item['category']}",
            file=str(item["source_b"]),
            line=0,
            current=f"{item['source_a']}: {item['a_says']} | "
                    f"{item['source_b']}: {item['b_says']}",
            target=f"{item['source_a']} is authoritative",
            delta=str(item["conflict"]),
            fix=("Decide which source is authoritative and align the other; "
                 "user decision required" if item.get("user_decision") == "yes"
                 else f"Align {item['source_b']} with {item['source_a']}"),
            effort="M",
            priority="P0" if item.get("blocker") == "yes" else "P1",
            confidence=4,
            evidence_strength="multiple",
            truth_level="L0",
            claim_state="VERIFIED",
            completion_blocker="yes" if item.get("blocker") == "yes" else "partial",
            snippet=str(item["impact"]),
            notes=f"category={item['category']}; user_decision={item.get('user_decision', 'no')}",
            origin="static",
        ))
    return res


@check("cross_anti_patterns", "22_anti_patterns", "logic",
       "Roll up anti-pattern categories with occurrence counts and samples.")
def cross_anti_patterns(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="cross_anti_patterns", dimension="22_anti_patterns")
    counts: dict[str, dict] = {}
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if not rel.startswith("backend/"):
            continue
        text, _ = read_text(p)
        if not text:
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            if re.search(r"^\s*#\s*(TODO|Future:)", line):
                c = counts.setdefault("TODO-only implementation", {"count": 0, "sample": f"{rel}:{line_no}"})
                c["count"] += 1
            if re.search(r"NotImplementedError", line):
                c = counts.setdefault("Stub function (NotImplementedError)", {"count": 0, "sample": f"{rel}:{line_no}"})
                c["count"] += 1
            if re.search(r"^\s*#\s*(import |from |def |class )", line):
                c = counts.setdefault("Commented code", {"count": 0, "sample": f"{rel}:{line_no}"})
                c["count"] += 1
            if re.search(r"[\"'][a-z][a-z0-9_.]*\.[a-z0-9_.]+[\"']", line) and "feature" in text[max(0, text.find(line) - 200):text.find(line)].lower():
                pass
    blockers = {
        "TODO-only implementation": "yes",
        "Stub function (NotImplementedError)": "partial",
        "Commented code": "no",
    }
    for cat, data in sorted(counts.items(), key=lambda kv: -kv[1]["count"]):
        res.facts.setdefault("anti_patterns", []).append({
            "id": f"AP-{re.sub(r'[^a-z]+', '-', cat.lower()).strip('-')}",
            "category": cat, "occurrences": data["count"],
            "sample": data["sample"], "blocker": blockers.get(cat, "no"),
            "remediation": {
                "TODO-only implementation": "Implement or delete the marked code paths",
                "Stub function (NotImplementedError)": "Implement or remove the stub",
                "Commented code": "Delete commented-out code; git history is the archive",
            }.get(cat, "Review"),
        })
        if data["count"] >= 25 and blockers.get(cat) == "yes":
            res.findings.append(_f(
                "22_anti_patterns", "logic", data["sample"].split(":")[0],
                f"{cat}: {data['count']} occurrence(s); sample {data['sample']}",
                "no live stubs/TODO-only paths (AP catalog)",
                "Implement or remove the marked paths",
                priority="P1", blocker="partial", cluster="CLUSTER-ap-" + cat.split()[0].lower(),
            ))
    return res


@check("cross_browser_bridge", "24_browser_behavior", "frontend",
       "Consume the recorded Playwright run when present; report runner/collection "
       "failures and historical failures; never invent findings and never render "
       "a clean PASS when no browser evidence exists.")
def cross_browser_bridge(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="cross_browser_bridge", dimension="24_browser_behavior")
    browser_root = ctx.root / "_browser_test"

    # -- 1. spec inventory (always available when the suite exists) ---------- #
    specs = sorted((browser_root / "tests").rglob("*.spec.ts")) \
        if (browser_root / "tests").exists() else []
    for spec in specs:
        text, _ = read_text(spec)
        res.observations.append(Observation(
            "browser_spec", ctx.rel(spec), ctx.rel(spec), 0,
            "24_browser_behavior",
            evidence=f"{(text or '').count('test(')} test() call(s)",
        ))

    # -- 2. the recorded Playwright JSON run --------------------------------- #
    candidates = [
        browser_root / "reports" / "run" / "results.json",
        browser_root / "browser_results.json",
        ctx.out_dir / "logs" / "browser_results.json",
    ]
    data = None
    source = ""
    for c in candidates:
        if c.exists():
            try:
                data = json.loads(c.read_text(encoding="utf-8-sig"))
                source = ctx.rel(c)
                break
            except Exception:
                continue

    steps: list[dict] = []
    failures = 0
    if data is not None:
        for err in (data.get("errors") or []):
            msg = str(err.get("message", "")).strip().splitlines()[0] if err else ""
            if not msg:
                continue
            res.findings.append(_f(
                "24_browser_behavior", "testing", source,
                f"Playwright run produced no executable tests: {msg}",
                "the recorded browser run executes its specs and reports per-test status",
                "Fix the Playwright collection error, then re-run "
                "`npx playwright test` inside `_browser_test/`",
                priority="P0", blocker="yes",
                cluster="CLUSTER-browser-runner-broken",
            ))
        suites = data.get("suites") or []
        for suite in suites:
            for spec in suite.get("specs", []) or []:
                for test in spec.get("tests", []) or []:
                    last = (test.get("results") or [{}])[-1]
                    status = last.get("status", "unknown")
                    steps.append({
                        "id": f"BROWSER-{len(steps)+1:03d}",
                        "step": spec.get("title", ""),
                        "expected": "pass",
                        "observed": status,
                        "status": "PASS" if status == "passed" else "FAILED",
                        "evidence": source,
                    })
                    if status != "passed":
                        failures += 1
        stats = data.get("stats") or {}
        res.facts["browser_summary"] = {
            "source": source,
            "steps": len(steps),
            "failures": failures,
            "expected": stats.get("expected"),
            "unexpected": stats.get("unexpected"),
            "flaky": stats.get("flaky"),
            "skipped": stats.get("skipped"),
            "start_time": stats.get("startTime"),
            "duration_s": round(float(stats.get("duration") or 0) / 1000.0, 1),
            "run_errors": [str(e.get("message", "")).strip().splitlines()[0]
                           for e in (data.get("errors") or []) if e.get("message")],
        }
    if steps:
        res.facts["browser_steps"] = steps

    # -- 3. the last run that actually produced per-test artifacts ----------- #
    historical = browser_root / "test-results" / ".last-run.json"
    if historical.exists():
        try:
            hist = json.loads(historical.read_text(encoding="utf-8-sig"))
        except Exception:
            hist = {}
        failed_ids = hist.get("failedTests") or []
        res.facts["browser_historical"] = {
            "source": ctx.rel(historical),
            "status": hist.get("status", "unknown"),
            "failed_tests": len(failed_ids),
        }
        res.observations.append(Observation(
            "browser_run", ctx.rel(historical), ctx.rel(historical), 0,
            "24_browser_behavior",
            evidence=(f"last run status={hist.get('status', 'unknown')}, "
                      f"{len(failed_ids)} failed test id(s); "
                      f"{len(list((browser_root / 'test-results').glob('*.md')))} "
                      "error-context file(s)"),
        ))
        if failed_ids:
            res.findings.append(_f(
                "24_browser_behavior", "testing", ctx.rel(historical),
                f"{len(failed_ids)} browser test(s) failed in the last recorded run "
                f"(status={hist.get('status', 'unknown')})",
                "every critical browser journey passes before release",
                "Open `_browser_test/reports/html/index.html` and fix each failing spec",
                priority="P1", blocker="yes",
                cluster="CLUSTER-browser-failure",
            ))

    # -- 4. per-step failures ------------------------------------------------ #
    #
    # These come from a results.json on disk, which is evidence about whatever
    # code was running WHEN IT WAS WRITTEN -- not necessarily the current tree.
    # The run that produced this output may have executed zero browser steps
    # (`--no-tools`, no Playwright, or a preflight failure), and then one P1 per
    # recorded step is 71 findings asserting product failures on the strength of
    # a stale file. That is the same class of defect as a probe that could not
    # run being reported as a clean pass: an absent measurement must never be
    # laundered into a measurement.
    probe_ran = False
    probe_note = ""
    probe_tool = ctx.tools.get("browser:playwright")
    if probe_tool is not None:
        probe_ran = bool(getattr(probe_tool, "ok", False)) and \
            int(getattr(probe_tool, "exit_code", 1) or 1) == 0
        probe_note = (f"exit={getattr(probe_tool, 'exit_code', '?')} "
                      f"reason={getattr(probe_tool, 'skipped_reason', '') or '-'}")
    else:
        probe_note = "no browser probe was executed in this run"

    stale = bool(steps) and not probe_ran

    if stale:
        res.facts["browser_evidence_stale"] = True
        res.findings.append(_f(
            "24_browser_behavior", "frontend", source,
            f"browser evidence is STALE: {len(steps)} recorded step(s) in {source} are "
            f"from an earlier run, and this run executed none ({probe_note}); "
            f"{failures} of them recorded non-PASS",
            "browser evidence must describe the code under audit",
            "Run the browser probe (`zozi_audit.py --full --browser`) so the steps "
            "reflect the current tree, then re-run the audit; do NOT fix the "
            "reported steps on the strength of this file",
            priority="P2", blocker="no",
            cluster="CLUSTER-browser-evidence-stale",
        ))
    else:
        for s in steps:
            if s["status"] != "PASS":
                res.findings.append(_f(
                    "24_browser_behavior", "frontend", source,
                    f"browser step failed: {s['step']} ({s['observed']})",
                    "every critical browser journey passes",
                    "Fix the failing step or update the spec",
                    priority="P1", blocker="partial",
                    cluster="CLUSTER-browser-failure",
                ))

    # -- 5. no evidence at all -> explicit precondition, never a clean PASS --- #
    if data is None and not failed_ids:
        res.facts["browser_precondition"] = (
            "phase_precondition_unmet — browser_audit_absent "
            "(no Playwright JSON run found; run `npx playwright test` inside "
            "`_browser_test/`, or `zozi_audit.py --browser` against a live stack)")
        res.findings.append(_f(
            "24_browser_behavior", "testing",
            ctx.rel(browser_root) if browser_root.exists() else "_browser_test",
            "no consumable browser-audit result: no Playwright JSON report and no "
            "recorded last-run",
            "browser behaviour is verified by a recorded Playwright run",
            "Run `npx playwright test` in `_browser_test/` and keep "
            "`reports/run/results.json` as evidence",
            priority="P1", blocker="partial",
            cluster="CLUSTER-browser-precondition-unmet",
        ))
    return res


@check("cross_readiness_signals", "27_project_completion_blockers", "infra",
       "Collect tool-derived readiness signals (boot, tests, tsc, migrations, "
       "env) for the 18-condition gate.")
def cross_readiness_signals(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="cross_readiness_signals",
                      dimension="27_project_completion_blockers")
    def status_of(name, ok_codes=(0,)):
        tool = ctx.tools.get(name)
        if tool is None:
            return "unverifiable", "not run"
        if getattr(tool, "skipped_reason", ""):
            return "unverifiable", tool.skipped_reason
        return ("pass" if tool.exit_code in ok_codes else "fail",
                f"exit={tool.exit_code}")
    boot_status, boot_ev = status_of("boot:root")
    if boot_status == "fail":
        adapted = ctx.tools.get("boot:backend-cwd")
        if adapted is not None and adapted.exit_code == 0:
            # The app does boot via the documented backend-cwd command; the
            # root-import failure is reported separately as BLOCK-boot-import.
            boot_status = "pass"
            boot_ev = f"boots from backend/ (adapted command); root import fails ({boot_ev})"
    arch = ctx.tools.get("pytest:architecture")
    arch_status, arch_ev = ("unverifiable", "not run") if arch is None else (
        ("pass", "green") if arch.exit_code == 0 else ("fail", f"exit={arch.exit_code}"))
    tsc_status, tsc_ev = status_of("tsc")
    mig = ctx.tools.get("alembic:heads")
    mig_status = "unverifiable"
    mig_ev = "not run"
    if mig is not None:
        tail = (mig.stdout_tail or "") + "\n" + (mig.stderr_tail or "")
        heads = len(re.findall(r"\(head\)", tail))
        if getattr(mig, "skipped_reason", ""):
            mig_status, mig_ev = "unverifiable", mig.skipped_reason
        elif mig.exit_code == 0:
            mig_status = "pass" if heads == 1 else "fail"
            mig_ev = f"{heads} head(s)"
        else:
            # The CLI ran and failed: that is a fail, not "not run".
            mig_status = "fail"
            mig_ev = (f"alembic heads exit={mig.exit_code}: "
                      f"{tail.strip().splitlines()[-1] if tail.strip() else 'no output'}")
    res.facts["readiness_tools"] = {
        "boot": boot_status, "boot_evidence": boot_ev,
        "arch_tests": arch_status, "arch_tests_evidence": arch_ev,
        "tsc": tsc_status, "tsc_evidence": tsc_ev,
        "migrations": mig_status, "migrations_evidence": mig_ev,
        "ci": "fail" if not list((ctx.root / ".github" / "workflows").glob("deploy*.yml")) else "partial",
        "ci_evidence": "deploy workflow presence",
        "browser": "unverifiable", "load": "unverifiable",
        "env": "unverifiable", "payment_creds": "unverifiable",
        "mobile": "unverifiable", "commerce": "unverifiable",
        "security": "unverifiable",
    }
    return res
