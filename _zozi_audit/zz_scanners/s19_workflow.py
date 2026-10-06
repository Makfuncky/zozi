"""Dimension 04/27 (extension) — workflow integrity, handover assurance, QA
mechanisms, and automation opportunities.

The prompt audits *code shape*. This module audits *work*: whether a business
workflow can actually run to completion, whether custody can transfer safely,
whether a quality gate exists, and which repetitive manual steps are
candidates for automation. Two streams are produced:

* findings      — a named artefact or symbol is missing/incorrect (defect)
* recommendations — the business capability is absent and here is its design
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

from zz_core.model import CheckResult, Finding, Observation, Recommendation, ScanContext
from zz_core.registry import check
from zz_core.util import parse_python, read_text

# A Celery worker cannot run a beat schedule without the app object.
CELERY_APP_CANDIDATES = ("celery_app.py", "celery.py", "worker.py")

HANDOVER_TOKENS = ("handover", "hand_over", "takeover", "take_over", "custody",
                   "reassign", "transfer_ownership", "assign_review")
HANDOVER_GUARANTEES = (
    ("permission_both_sides", re.compile(r"require_feature|require_permission|"
                                        r"Depends\(require_|has_permission", re.I)),
    ("audit_trail", re.compile(r"audit|AuditMixin|create_audit|record_audit|"
                               r"log_transition|write_audit", re.I)),
    ("notifies_previous", re.compile(r"notif|notify|email|websocket|event|publish|emit", re.I)),
    ("both_parties_recorded", re.compile(r"(from_|to_|previous_|new_)(user|agent|staff|"
                                         r"employee|owner|assignee|reviewer)", re.I)),
    ("idempotent", re.compile(r"idempot|already_|duplicate|exists\(|ON CONFLICT|"
                              r"unique", re.I)),
)

# A status machine that is not centralised cannot be reasoned about or enforced.
STATUS_ASSIGN_RE = re.compile(r"\.status\s*=\s*[\"'][a-z_]+[\"']|status\s*=\s*Status\.")

# Statuses that mean "a human must act".
HUMAN_IN_LOOP = (
    "pending_review", "pending_verification", "pending_approval", "needs_approval",
    "manual_review", "on_hold", "hold", "quarantine", "awaiting_review",
    "pending_signature", "disputed", "escalated",
)


def _py(ctx: ScanContext, *substrings: str) -> list[Path]:
    out = []
    for p in ctx.py_files:
        rel = ctx.rel(p).replace("\\", "/")
        if any(s in rel for s in substrings):
            out.append(p)
    return out


def module_level_bindings(tree: ast.AST) -> set[str]:
    """Every name a module makes available at import time.

    Functions, classes, module-level constants (plain and annotated), and
    imported/re-exported names all count. Only then can "is `mod.SYMBOL`
    defined?" be answered without lying about constants.
    """
    names: set[str] = set()
    for node in getattr(tree, "body", []):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    names.add(tgt.id)
                elif isinstance(tgt, (ast.Tuple, ast.List)):
                    names.update(e.id for e in tgt.elts if isinstance(e, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, ast.ImportFrom):
            names.update(a.asname or a.name for a in node.names)
        elif isinstance(node, ast.Import):
            names.update((a.asname or a.name.split(".")[0]) for a in node.names)
        elif isinstance(node, ast.If):
            # Conditional re-exports (`if TYPE_CHECKING:`, platform switches).
            for st in ast.walk(node):
                if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    names.add(st.name)
                elif isinstance(st, ast.Assign):
                    names.update(t.id for t in st.targets if isinstance(t, ast.Name))
                elif isinstance(st, ast.ImportFrom):
                    names.update(a.asname or a.name for a in st.names)
    return names


def _strip_py_noise(text: str) -> str:
    """Blank out comments and docstrings, keeping line numbers intact.

    A regex that matches ``require_feature("x")`` inside a comment produces a
    phantom "undefined gate" that no reviewer can reproduce.
    """
    import io
    import tokenize
    out = list(text)
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type == tokenize.COMMENT:
                for i in range(tok.start[0], tok.end[0] + 1):
                    if 0 <= i - 1 < len(out):
                        out[i - 1] = re.sub(r"[^\n]", " ", out[i - 1])
            elif tok.type == tokenize.STRING and tok.line.strip().startswith(
                    ('"""', "'''")):
                for i in range(tok.start[0], tok.end[0] + 1):
                    if 0 <= i - 1 < len(out):
                        out[i - 1] = re.sub(r"[^\n]", " ", out[i - 1])
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return text
    return "".join(out)


def _celery_app(ctx: ScanContext) -> Path | None:
    """Locate the Celery application object anywhere under backend/.

    A fixed candidate list at backend/ root misses ``backend/jobs/celery_app.py``,
    which is where this codebase keeps it.
    """
    best: tuple[int, Path] | None = None
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if not rel.startswith("backend/"):
            continue
        text, _ = read_text(p)
        if not text or "Celery(" not in text:
            continue
        depth = rel.count("/")
        if best is None or depth < best[0]:
            best = (depth, p)
    return best[1] if best else None


@check("workflow_runtime_bootstrap", "04_operational", "infra",
       "Background work must actually be schedulable: the Celery app object, the "
       "beat schedule, and every symbol a scheduled task imports.")
def workflow_runtime_bootstrap(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="workflow_runtime_bootstrap", dimension="04_operational")
    backend = ctx.backend
    celery_app = _celery_app(ctx)
    schedule_hits: list[tuple[str, int]] = []
    for p in _py(ctx, "celery", "jobs/", "beat"):
        text, _ = read_text(p)
        if not text:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if re.search(r"beat_schedule|add_periodic_task|crontab\(|schedule\s*=", line):
                schedule_hits.append((ctx.rel(p), n))
    # Every symbol a scheduled task imports must exist somewhere.
    # A task is "scheduled" when its NAME is referenced by the Celery app, which
    # is where `beat_schedule` lives. The previous test asked whether the 900
    # characters following the decorator mentioned "schedule" anywhere, so a task
    # that merely sat near an unrelated comment counted as scheduled and a task
    # registered in `beat_schedule` from another file did not. The probe judges
    # this claim against `celery_app.py`, so the detector has to as well.
    celery_src = ""
    if celery_app is not None:
        celery_src, _ = read_text(celery_app)
    task_files = sorted((backend / "jobs").glob("*.py")) if (backend / "jobs").exists() else []
    tasks: list[dict] = []
    for p in task_files:
        text, _ = read_text(p)
        if not text:
            continue
        for m in re.finditer(r"@(?:shared_task|app\.task|celery_app\.task)\b", text):
            block = text[m.start():m.start() + 900]
            # Resolve the task's real name, in precedence order:
            #   1. an explicit `name=` kwarg
            #   2. the decorated `def`
            # The previous regex grabbed the FIRST parenthesised token after the
            # decorator, which for `@shared_task(bind=True, ...)` is the kwarg
            # `bind` -- so 38 tasks collapsed to two names, `bind` and `name`,
            # and "is `bind` in the beat schedule?" decided a real finding.
            name_m = re.search(r"""\bname\s*=\s*["']([\w.]+)["']""", block)
            if not name_m:
                name_m = re.search(r"^\s*(?:async\s+)?def\s+(\w+)", block,
                                   re.MULTILINE)
            name = name_m.group(1) if name_m else "?"
            scheduled = bool(
                name != "?"
                and celery_src
                and re.search(rf"\b{re.escape(name.split('.')[-1])}\b", celery_src)
            )
            tasks.append({
                "file": ctx.rel(p), "line": text[:m.start()].count("\n") + 1,
                "name": name,
                "scheduled": scheduled,
            })

    res.facts["workflow_runtime"] = {
        "celery_app_file": ctx.rel(celery_app) if celery_app else "",
        "beat_schedule_definitions": len(schedule_hits),
        "scheduled_tasks": len(tasks),
        "tasks": tasks[:40],
    }
    for t in tasks[:30]:
        res.observations.append(Observation(
            "celery_task", t["file"], t["file"], t["line"], "04_operational",
            evidence=f"task {t['name']} scheduled_in_source={t['scheduled']}",
        ))
    if celery_app is None:
        res.findings.append(Finding(
            id="WF-celery-app-missing", dimension="04_operational", phase="infra",
            cluster="CLUSTER-workflow-runtime", file="backend/jobs/celery_app.py",
            current="no Celery application object exists anywhere under backend/",
            target="a Celery app with a beat schedule, so periodic tasks are "
                   "actually dispatched",
            delta="every scheduled job is dead code: nothing triggers it",
            fix="create the Celery app, register the periodic tasks in "
                "beat_schedule, and reference it from the worker and compose files",
            effort="M", priority="P0", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="yes",
            verify="cd backend && celery -A celery_app inspect ping",
            snippet=f"{len(tasks)} task(s) found in backend/jobs/ with no app to run them",
        ))
    elif not schedule_hits:
        res.findings.append(Finding(
            id="WF-no-beat-schedule", dimension="04_operational", phase="infra",
            cluster="CLUSTER-workflow-runtime", file=ctx.rel(celery_app),
            current="a Celery app exists but no beat schedule is declared",
            target="every periodic job has an explicit schedule entry",
            delta=f"{len(tasks)} task(s) can only run if triggered manually",
            fix="declare beat_schedule (or add_periodic_task) for each periodic job",
            effort="S", priority="P0", confidence=4, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="yes",
            verify="cd backend && celery -A celery_app inspect conf",
        ))
    else:
        # The app exists: report what is scheduled vs merely defined, which is
        # the actionable question, rather than claiming there is no app.
        res.facts["workflow_runtime"]["scheduled_task_names"] = sorted(
            {t["name"] for t in tasks if t["scheduled"]})
        res.findings.append(Finding(
            id="WF-unscheduled-tasks", dimension="04_operational", phase="infra",
            cluster="CLUSTER-workflow-runtime", file=ctx.rel(celery_app),
            current=f"{len(tasks) - sum(1 for t in tasks if t['scheduled'])} of "
                    f"{len(tasks)} Celery task(s) are defined but never registered "
                    f"in a beat schedule",
            target="every recurring job appears in beat_schedule; the rest are "
                   "explicitly event-driven",
            delta=f"{len(schedule_hits)} schedule declaration(s) cover fewer tasks "
                  f"than are defined, so some background work never runs",
            fix="add a beat_schedule entry per recurring task, or document the task "
                "as event-triggered and delete the unused decoration",
            effort="S", priority="P1", confidence=4, evidence_strength="multiple",
            truth_level="L1", claim_state="INFERRED", completion_blocker="no",
            verify="cd backend && celery -A celery_app inspect conf | grep -A40 beat",
        ))

    # Dangling imports: a task imports a symbol that does not exist anywhere.
    symbols: dict[str, str] = {}
    for p in ctx.py_files:
        text, _ = read_text(p)
        if not text:
            continue
        for m in re.finditer(r"from\s+([\w.]+)\s+import\s+(\w+)", text):
            if m.group(1).startswith(("infrastructure", "domains", "modules", "kernel",
                                     "jobs", "providers", "rbac")):
                symbols.setdefault(m.group(2), ctx.rel(p))
    # Every module-level BINDING counts as defined, not just def/class.
    #
    # The old scan collected only functions and classes, so a module-level
    # constant -- the normal way this codebase exports an event name
    # (`EVENT_SHIPMENT_CREATED = "logistics.shipment.created"`) -- was invisible.
    # It reported 10 exports as "not defined anywhere in the codebase" and marked
    # every one of them P0 / completion_blocker=yes, while all 10 resolve:
    # `backend/domains/logistics/events.py:20` defines the symbol the detector
    # called missing, and `backend/jobs/event_workers.py:17` imports it. A false
    # hard blocker is the most expensive defect this suite can produce, because
    # it is the first thing a reader is told to fix.
    defined: set[str] = set()
    for p in ctx.py_files:
        text, _ = read_text(p)
        if not text:
            continue
        tree = parse_python(p).tree
        if tree is None:
            # Unparsable file: fall back to the line scan so a syntax error in an
            # unrelated file cannot manufacture a dangling import.
            defined.update(re.findall(r"^\s*(?:async\s+)?def\s+(\w+)", text, re.M))
            defined.update(re.findall(r"^\s*class\s+(\w+)", text, re.M))
            defined.update(re.findall(r"^\s*(\w+)\s*(?::[^=]+)?=", text, re.M))
            continue
        defined |= module_level_bindings(tree)
    dangling: list[tuple[str, str, str]] = []
    for p in task_files:
        text, _ = read_text(p)
        if not text:
            continue
        for m in re.finditer(r"from\s+([\w.]+)\s+import\s+\(?\s*([\w,\s]+)\)", text):
            mod, names = m.group(1), m.group(2)
            if not mod.startswith(("domains", "infrastructure", "modules", "kernel")):
                continue
            for nm in re.split(r"[,\s]+", names):
                nm = nm.strip()
                if nm and nm.isidentifier() and nm not in defined and \
                        not nm.startswith("_") and nm != "annotations":
                    dangling.append((ctx.rel(p), f"{mod}.{nm}", mod))
    seen: set[tuple[str, str]] = set()
    for rel, sym, mod in dangling:
        if (rel, sym) in seen:
            continue
        seen.add((rel, sym))
        # A task importing a missing symbol only breaks at call time: the
        # scheduler keeps firing and the job raises every run.
        res.findings.append(Finding(
            id="WF-dangling-import", dimension="04_operational", phase="infra",
            cluster="CLUSTER-workflow-runtime", file=rel,
            current=f"`{rel}` imports `{sym}`, which is not defined anywhere in the "
                    f"codebase",
            target="every import resolves; a scheduled task never raises on dispatch",
            delta="the periodic job fails on every run with ImportError and the "
                  "work is silently never done",
            fix=f"implement `{sym.split('.')[-1]}` in {mod}, or remove the import and "
                f"the task",
            effort="M", priority="P0", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="yes",
            # The old verify command imported `domains.jobs`, which is not a
            # module -- a verification step that cannot pass proves nothing.
            verify="cd backend && python -c 'import " + mod + "; print(" + nm + ")'"
        ))
    if dangling:
        res.recommendations.append(Recommendation(
            area="ops", dimension="04_operational",
            title="Add a dispatch smoke test for every scheduled task",
            rationale=f"{len(dangling)} scheduled task(s) import symbols that do not "
                      f"exist, so they fail on every dispatch. Nothing detects this "
                      f"because the app is not running.",
            current="scheduled jobs are only exercised in production.",
            proposal="add a test that imports every task module and asserts each "
                     "task's callable resolves, plus a startup self-check in the "
                     "worker entrypoint that exits non-zero on an unresolvable task.",
            benefit="a dead scheduled job fails CI in seconds instead of silently "
                    "every night",
            effort="S", impact="high", category="quality",
            evidence="backend/jobs/*.py",
        ))
    return res


@check("workflow_event_spine", "04_operational", "arch",
       "Are domain events actually driving side effects, or are subscribers "
       "log-only stubs? A stub subscriber is a promise the code does not keep.")
def workflow_event_spine(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="workflow_event_spine", dimension="04_operational")
    files = _py(ctx, "/subscribers.py")
    per_domain: dict[str, dict] = {}
    stub_sites: list[tuple[str, int]] = []
    total = stubs = 0
    for p in files:
        rel = ctx.rel(p)
        text, _ = read_text(p)
        if not text:
            continue
        domain = rel.split("/domains/")[1].split("/")[0] if "/domains/" in rel else "?"
        code = _strip_py_noise(text)
        for m in re.finditer(r"(?:async\s+)?def\s+(?:_?on_|handle_)(\w+)\s*\(", code):
            start = m.end()
            nxt = code.find("\n    def ", start)
            nxt2 = code.find("\n    async def ", start)
            end = min([e for e in (nxt, nxt2, len(code)) if e != -1])
            body = code[start:end]
            # A handler that delegates to a service helper is not a stub: the
            # write happens one frame down.
            writes = re.findall(r"\.status\s*=|\.save\(|\.add\(|create_\w+|post_\w+|"
                                r"update_\w+|\.delete\(|setattr\(|await\s+self\._\w+|"
                                r"await\s+\w+\.\w+\(|await\s+self\.[a-z]\w+\(", body)
            total += 1
            line = code[:m.start()].count("\n") + 1
            if not writes:
                stubs += 1
                stub_sites.append((rel, line))
        per_domain[domain] = {
            "handlers": len(re.findall(r"(?:async\s+)?def\s+(?:_?on_|handle_)\w+", text)),
            "future_markers": len(re.findall(r"#\s*(?:TODO|Future)", text)),
        }
    res.facts["workflow_event_spine"] = {
        "subscriber_files": len(files),
        "handlers": total,
        "log_only_stubs": stubs,
        "stub_ratio": (round(stubs / total, 3) if total else None),
        "per_domain": per_domain,
    }
    for rel, line in stub_sites[:40]:
        res.observations.append(Observation(
            "event_handler", rel, rel, line, "04_operational",
            evidence="handler logs and returns without a write (stub)",
        ))
    if total and stubs / total > 0.4:
        res.findings.append(Finding(
            id="WF-stub-subscribers", dimension="04_operational", phase="arch",
            cluster="CLUSTER-event-spine", file="backend/domains",
            current=f"{stubs} of {total} event handlers ({stubs}/{total}) log and "
                    f"return without performing the write they imply",
            target="a published domain event produces its side effect, or is not "
                   "published",
            delta="cross-domain business logic (ledger posting, commission accrual, "
                  "inventory reservation, notification) never runs",
            fix="either implement each handler or stop publishing the event; a "
                "handler marked `# Future:` should raise in non-dev so it cannot be "
                "mistaken for working code",
            effort="XL", priority="P0", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="yes",
            verify="grep -rn '# Future:' backend/domains | wc -l",
            snippet=", ".join(f"{p}:{l}" for p, l in stub_sites[:8]),
        ))
        res.recommendations.append(Recommendation(
            area="workflow", dimension="04_operational",
            title="Turn the event spine into real work, or delete it",
            rationale=f"{stubs} stub handlers mean the architecture claims "
                      f"event-driven domains while the side effects are unimplemented. "
                      f"Every one is a manual process hidden behind a log line.",
            current=f"{stubs} log-only handlers.",
            proposal="triage each handler into (a) implement now, (b) schedule as a "
                     "remediation item with an owner, (c) delete the publication. "
                     "Add a test that asserts a published event reaches a handler that "
                     "performs a write.",
            benefit="converts hidden manual work into either automation or an "
                    "explicitly accepted risk",
            effort="XL", impact="high", category="automation",
            evidence="backend/domains/*/subscribers.py",
            human_effort_saved="removes an estimated recurring manual reconciliation "
                               "load across finance/logistics/orders",
        ))
    return res


@check("workflow_status_integrity", "04_operational", "arch",
       "Order/payout/ticket state machines must be centralised; scattered status "
       "assignments cannot be validated or audited.")
def workflow_status_integrity(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="workflow_status_integrity", dimension="04_operational")
    sites: dict[str, list[int]] = {}
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if "/tests/" in rel:
            continue
        text, _ = read_text(p)
        if not text:
            continue
        hits = [n for n, line in enumerate(text.splitlines(), 1)
                if STATUS_ASSIGN_RE.search(line)]
        if hits:
            sites[rel] = hits
    total = sum(len(v) for v in sites.values())
    # A transition guard must be a real map or a real assertion helper. An enum
    # of status *values* is not a state machine: it describes the states, not
    # the moves between them.
    has_machine = False
    machine_sites: list[str] = []
    for p in _py(ctx, "rbac", "kernel", "infrastructure", "domains"):
        text, _ = read_text(p)
        if not text:
            continue
        if re.search(r"ALLOWED_TRANSITIONS|TRANSITIONS\s*[:=]\s*[\[{]|"
                     r"VALID_TRANSITIONS|def\s+(?:can_transition|assert_transition|"
                     r"validate_transition|ensure_transition|transition_to)\b", text):
            has_machine = True
            machine_sites.append(ctx.rel(p))
    res.facts["workflow_status_integrity"] = {
        "status_assignment_sites": total,
        "files": len(sites),
        "central_state_machine": has_machine,
        "state_machine_sites": machine_sites[:5],
        "top_files": sorted(((p, len(v)) for p, v in sites.items()),
                            key=lambda t: -t[1])[:15],
    }
    for rel, lines in sorted(sites.items(), key=lambda t: -len(t[1]))[:30]:
        res.observations.append(Observation(
            "status_transition", rel, rel, lines[0], "04_operational",
            evidence=f"{len(lines)} direct status assignment(s)",
        ))
    if total > 40 and not has_machine:
        res.findings.append(Finding(
            id="WF-no-state-machine", dimension="04_operational", phase="arch",
            cluster="CLUSTER-state-machine", file="backend/domains",
            current=f"{total} scattered status assignments across {len(sites)} files "
                    f"with no centralised transition table",
            target="one transition table per aggregate, enforced by a single helper "
                   "that also writes the audit record",
            delta="an illegal transition (e.g. paid -> cancelled) cannot be "
                  "prevented or reported",
            fix="introduce `assert_transition(obj, new_status)` per domain, backed by "
                "an allowed-transition map, and route every assignment through it",
            effort="L", priority="P1", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="no",
            verify="grep -rEc '\\.status\\s*=' backend/domains | awk -F: '$2>0' | wc -l",
            snippet=", ".join(f"{p} ({n})" for p, n in
                              sorted(((p, len(v)) for p, v in sites.items()),
                                     key=lambda t: -t[1])[:5]),
        ))
    return res


@check("handover_assurance", "04_operational", "arch",
       "Handover and takeover: does custody transfer enforce permission, audit, "
       "notification, dual-party record and idempotency?")
def handover_assurance(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="handover_assurance", dimension="04_operational")
    flows: list[dict] = []
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if "/tests/" in rel:
            continue
        text, _ = read_text(p)
        if not text:
            continue
        low = text.lower()
        if not any(tok in low for tok in HANDOVER_TOKENS):
            continue
        for m in re.finditer(r"(?:async\s+)?def\s+(\w*(?:handover|hand_over|takeover|"
                             r"take_over|reassign|transfer_\w+)\w*)\s*\(", text, re.I):
            start = m.end()
            nxt = re.search(r"\n(?:    |)(?:async\s+)?def\s+\w+", text[start:])
            end = start + (nxt.start() if nxt else 2000)
            body = text[start:end][:3000]
            guarantees = {name: bool(rx.search(body))
                          for name, rx in HANDOVER_GUARANTEES}
            flows.append({
                "file": rel,
                "line": text[:m.start()].count("\n") + 1,
                "name": m.group(1),
                "guarantees": guarantees,
                "has_audit_write": bool(re.search(r"\.save\(|AuditMixin|audit", body)),
            })
    complete = [f for f in flows if all(f["guarantees"].values())]
    res.facts["handover_assurance"] = {
        "handover_functions": len(flows),
        "fully_guarded": len(complete),
        "flows": flows[:40],
    }
    for f in flows[:40]:
        missing = [k for k, v in f["guarantees"].items() if not v]
        res.observations.append(Observation(
            "handover", f["file"], f["file"], f["line"], "04_operational",
            evidence=f"{f['name']}() guarantees: "
                     f"{'all' if not missing else 'missing ' + ','.join(missing)}",
        ))
    if flows and len(complete) < len(flows):
        weak = [(f["file"], f["line"], [k for k, v in f["guarantees"].items() if not v])
                for f in flows if not all(f["guarantees"].values())]
        worst = {}
        for rel, line, missing in weak:
            for mname in missing:
                worst[mname] = worst.get(mname, 0) + 1
        res.findings.append(Finding(
            id="WF-handover-unguarded", dimension="04_operational", phase="arch",
            cluster="CLUSTER-handover", file="backend/domains",
            current=f"{len(flows) - len(complete)} of {len(flows)} handover/takeover "
                    f"function(s) are missing at least one safety guarantee",
            target="every custody transfer enforces permission, writes an audit "
                   "record, notifies the previous owner, records both parties, and "
                   "is idempotent",
            delta="most-missing guarantees: " + ", ".join(
                f"{k}={v}" for k, v in sorted(worst.items(), key=lambda t: -t[1])),
            fix="route every transfer through a single HandoverService that asserts "
                "permission, writes the audit record, emits a notification, and is "
                "idempotent on (object, from, to)",
            effort="L", priority="P1", confidence=4, evidence_strength="multiple",
            truth_level="L1", claim_state="INFERRED", completion_blocker="no",
            verify="grep -rn 'handover\\|takeover' backend/domains | wc -l",
            snippet=", ".join(f"{p}:{l}" for p, l, _ in weak[:6]),
        ))
        res.recommendations.append(Recommendation(
            area="workflow", dimension="04_operational",
            title="Guarantee custody transfer with a single HandoverService",
            rationale="Handover and takeover are the highest-risk manual operations "
                      "(shift handover, courier reassignment, review ownership, order "
                      "reassignment). Today each is implemented ad hoc, so a missed "
                      "step loses accountability.",
            current=f"{len(flows)} ad-hoc transfer implementations with differing "
                    f"safety guarantees.",
            proposal="one HandoverService.transfer(obj, from_party, to_party, reason) "
                     "that (1) checks permission on both sides, (2) writes an "
                     "immutable audit record with before/after, (3) notifies both "
                     "parties, (4) records both ids, (5) is idempotent; then add a "
                     "test matrix over the five guarantees.",
            benefit="no silent loss of custody; every transfer is provable in an audit",
            effort="L", impact="high", category="quality",
            evidence="backend/domains/*/**handover*, *_handover*",
            human_effort_saved="removes manual reconciliation after every shift change",
        ))
    return res


@check("quality_assurance_gaps", "04_operational", "arch",
       "Product QA, dispatch readiness, proof of delivery, returns and supplier "
       "scorecards: which quality mechanisms exist and which are absent.")
def quality_assurance_gaps(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="quality_assurance_gaps", dimension="04_operational")
    probes = {
        # Each mechanism must be a real definition — a model class, a service
        # function, or a table — not a column name or a comment that happens to
        # contain the words.
        "product_inspection": r"class\s+\w*(?:Inspection|QualityCheck|QualityControl|"
                              r"Defect|NonConform)\w*\b"
                              r"|def\s+\w*(?:inspect|quality_check|record_defect)\w*\s*\(",
        "dispatch_readiness": r"def\s+\w*(?:dispatch_ready|ready_to_dispatch|"
                              r"packing_check|pack_ready)\w*\s*\("
                              r"|dispatch_ready\s*[:=]",
        "proof_of_delivery": r"class\s+\w*(?:ProofOfDelivery|DeliveryProof|Pod\w*)\b"
                             r"|def\s+\w*(?:attach_pod|record_proof_of_delivery|"
                             r"capture_delivery_proof)\w*\s*\(",
        "return_rejection": r"class\s+\w*Return\w*\b|def\s+\w*(?:create_return|"
                            r"process_return|reject_delivery)\w*\s*\(",
        "supplier_scorecard": r"class\s+\w*(?:SupplierScore|SupplierRating|"
                              r"SupplierSuspension|SupplierBlacklist)\b"
                              r"|def\s+\w*(?:recompute_supplier_score|"
                              r"update_supplier_rating)\w*\s*\(",
        "sla_breach": r"def\s+\w*(?:sla_breach|breach_sla|check_sla|evaluate_sla)\w*\s*\("
                      r"|sla_breach\s*[:=]",
    }
    present: dict[str, list[str]] = {}
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if "/tests/" in rel:
            continue
        text, _ = read_text(p)
        if not text:
            continue
        code = _strip_py_noise(text)
        for name, rx in probes.items():
            if re.search(rx, code, re.I):
                present.setdefault(name, []).append(rel)
    absent = [n for n in probes if n not in present]
    res.facts["quality_assurance"] = {
        "mechanisms_present": {k: len(v) for k, v in present.items()},
        "mechanisms_absent": absent,
    }
    for name in probes:
        sites = present.get(name, [])
        res.observations.append(Observation(
            "qa_mechanism", name, sites[0] if sites else "backend/domains", 0,
            "04_operational",
            evidence=f"{len(sites)} implementation site(s)",
        ))
    if absent:
        res.findings.append(Finding(
            id="QA-mechanisms-absent", dimension="04_operational", phase="arch",
            cluster="CLUSTER-quality-assurance", file="backend/domains",
            current=f"no implementation found for: {', '.join(absent)}",
            target="a quality mechanism exists for each of: product inspection, "
                   "dispatch readiness, proof of delivery, returns, supplier "
                   "scorecard, SLA breach",
            delta="these steps are performed manually or not at all, and nothing in "
                  "the system can prove a handover passed QA",
            fix="model each missing mechanism (table + service + event) and gate the "
                "downstream transition on it",
            effort="XL", priority="P1", confidence=4, evidence_strength="multiple",
            truth_level="L1", claim_state="INFERRED", completion_blocker="no",
            verify="grep -rn 'class .*Inspection\\|proof_of_delivery\\|supplier_score' "
                   "backend/domains",
        ))
        res.recommendations.append(Recommendation(
            area="qa", dimension="04_operational",
            title="Introduce a quality-gate chain across fulfilment",
            rationale="Product quality assurance and handover/takeover assurance are "
                      "the two places where human judgement is most expensive and most "
                      "often skipped under load. Encoding them as gates converts an "
                      "audit finding into a system guarantee.",
            current=f"absent: {', '.join(absent)}",
            proposal="implement a QualityGate chain: (1) inbound inspection record, "
                     "(2) dispatch-readiness checklist blocking pick when unmet, "
                     "(3) proof-of-delivery capture (photo/signature/OTP) required "
                     "before `delivered`, (4) return reason codes feeding the supplier "
                     "scorecard, (5) scorecard-driven auto-suspension thresholds, "
                     "(6) SLA breach alerting with escalation.",
            benefit="reduces avoidable returns and disputes; makes supplier quality "
                    "a measurable, enforceable input rather than an opinion",
            effort="XL", impact="high", category="quality",
            evidence=f"backend/domains (absent: {', '.join(absent)})",
            human_effort_saved="~1 FTE-equivalent in manual dispute handling",
            prerequisites=("WF-no-state-machine",),
        ))
    return res


@check("automation_candidates", "04_operational", "ops",
       "Where does the system currently stop and wait for a human? Each such stop "
       "is an automation opportunity with a measurable workload.")
def automation_candidates(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="automation_candidates", dimension="04_operational")
    human_status: dict[str, list[str]] = {}
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if "/tests/" in rel:
            continue
        text, _ = read_text(p)
        if not text:
            continue
        for m in re.finditer(r"[\"'](" + "|".join(HUMAN_IN_LOOP) + r")[\"']", text):
            human_status.setdefault(m.group(1), []).append(
                f"{rel}:{text[:m.start()].count(chr(10)) + 1}")
    jobs: list[dict] = []
    for p in _py(ctx, "jobs/"):
        text, _ = read_text(p)
        if not text:
            continue
        # Only decorated Celery tasks count; a helper function in a job module
        # is not a scheduled unit of work.
        for m in re.finditer(r"@(?:shared_task|app\.task|celery_app\.task)\b",
                             text):
            fn = re.search(r"def\s+(\w+)\s*\(", text[m.end():m.end() + 200])
            # `@shared_task` above `def bind(...)` is a Task subclass instance, so
            # the callable name is not the job name; the class name is.
            name = fn.group(1) if fn else "?"
            if name in ("bind", "__call__", "run"):
                cls = re.search(r"class\s+(\w+)", text[max(0, m.start() - 400):m.start()])
                name = cls.group(1) if cls else name
            body_start = m.end() + (fn.end() if fn else 0)
            body = text[body_start:body_start + 1200]
            jobs.append({
                "file": ctx.rel(p),
                "name": name,
                "line": text[:m.start()].count("\n") + 1,
                "scheduled": bool(re.search(r"beat_schedule|add_periodic_task|crontab",
                                            text[:m.start()] + body)),
                "loops": len(re.findall(r"for\s+\w+\s+in|\.all\(\)|\.limit\(", body)),
            })
    # Repetitive synchronous work: a per-item loop that performs a network/db write.
    loops: list[tuple[str, int]] = []
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if "/tests/" in rel or "/alembic/" in rel:
            continue
        text, _ = read_text(p)
        if not text:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if re.search(r"for\s+\w+\s+in\s+.*:\s*$", line) and \
                    re.search(r"httpx\.|requests\.|await\s+session\.|create_task|"
                              r"send\(|publish\(", "\n".join(
                                  (text.splitlines() + [""] * 40)[n:n + 25])):
                loops.append((rel, n))
    res.facts["automation_candidates"] = {
        "human_in_the_loop_statuses": {k: len(v) for k, v in sorted(human_status.items())},
        "jobs": len(jobs),
        "scheduled_jobs": sum(1 for j in jobs if j["scheduled"]),
        "serial_network_loops": len(loops),
        "job_sample": jobs[:25],
    }
    for status, sites in sorted(human_status.items(), key=lambda t: -len(t[1]))[:15]:
        res.observations.append(Observation(
            "human_in_the_loop", sites[0].split(":")[0], sites[0].split(":")[0],
            int(sites[0].split(":")[-1] or 0), "04_operational",
            evidence=f"status `{status}` used in {len(sites)} place(s)",
        ))
    if human_status or loops:
        res.recommendations.append(Recommendation(
            area="automation", dimension="04_operational",
            title="Automate the human-in-the-loop queue and the serial write loops",
            rationale="The system already records which states wait for a person. "
                      "Those states are the workload; each one is a candidate for an "
                      "auto-resolution rule with a human fallback.",
            current=f"{len(human_status)} human-waiting status(es) in use; "
                    f"{len(loops)} per-item serial network/db loop(s).",
            proposal="for each human-waiting status define an auto-rule with a "
                     "confidence threshold and an escalation path: e.g. auto-resolve "
                     "payout holds when the bank line matches the expected amount; "
                     "auto-assign unreviewed fraud flags round-robin with a "
                     "first-responder SLA; batch the per-item loops into a single "
                     "bulk endpoint. Keep a human override on every rule.",
            benefit="moves repetitive reconciliation to machines and leaves "
                    "exception handling to people",
            effort="L", impact="high", category="automation",
            evidence="; ".join(f"{k}={len(v)}" for k, v in
                               sorted(human_status.items(), key=lambda t: -len(t[1]))[:6]),
            human_effort_saved="est. several hours/week of reconciliation and triage",
        ))
    for status, sites in sorted(human_status.items(), key=lambda t: -len(t[1]))[:8]:
        res.recommendations.append(Recommendation(
            area="automation", dimension="04_operational",
            title=f"Auto-route `{status}` work",
            rationale=f"`{status}` appears in {len(sites)} place(s); every one is a "
                      f"point where work waits for a person with no queue discipline.",
            current="manual review, unmeasured queue.",
            proposal="add a queue table with assignee, SLA and a rule-based "
                     "auto-assign; surface queue age on the admin dashboard.",
            benefit="bounded wait time instead of an unbounded queue",
            effort="S", impact="medium", category="automation",
            evidence=", ".join(sites[:4]),
        ))
    return res


@check("finance_automation_surface", "04_operational", "ops",
       "Which finance processes are automated today, and which are manual? This "
       "is the workload-reduction surface the business asked for.")
def finance_automation_surface(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="finance_automation_surface", dimension="04_operational")
    capabilities = {
        # a capability is *automated* only when a function/table with that job
        # is actually defined — a name appearing in an import or a comment is
        # not automation.
        "vat_remittance": (r"def\s+compute_vat_remittance|def\s+post_vat_remittance|"
                           r"class\s+VATRemittance\b"),
        "commission_accrual": (r"def\s+compute_commission|def\s+accrue_commission|"
                               r"class\s+CommissionLedger"),
        "payout_batching": (r"def\s+(?:run|dispatch|process)_payout|class\s+PayoutBatch\b"),
        "cod_remittance": (r"def\s+\w*cod_remittance|def\s+reconcile_cod"),
        "fx_revaluation": (r"def\s+\w*fx_revaluat|def\s+revalue_\w*"),
        "bank_reconciliation": (r"def\s+\w*reconcil\w*"),
        "bad_debt_provision": (r"def\s+\w*bad_debt|class\s+BadDebt\b|"
                               r"def\s+provision_\w*receiv"),
        "refund_ledger": (r"def\s+(?:create_refund_ledger|post_refund)"),
        "gateway_fee": (r"def\s+\w*gateway_fee|def\s+reconcile_\w*settlement"),
        "supplier_settlement": (r"def\s+\w*supplier_settlement|def\s+post_supplier_settlement"),
    }
    present: dict[str, list[str]] = {}
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if "/tests/" in rel:
            continue
        text, _ = read_text(p)
        if not text:
            continue
        code = _strip_py_noise(text)
        for name, rx in capabilities.items():
            if re.search(rx, code, re.I):
                present.setdefault(name, []).append(rel)
    manual = [c for c in capabilities if c not in present]
    res.facts["finance_automation"] = {
        "automated": sorted(present),
        "not_automated": manual,
        "sites": {k: len(v) for k, v in present.items()},
    }
    for name in capabilities:
        sites = present.get(name, [])
        res.observations.append(Observation(
            "finance_capability", name, sites[0] if sites else "backend/domains/finance",
            0, "04_operational",
            evidence=f"automated={bool(sites)} sites={len(sites)}",
        ))
    if manual:
        res.findings.append(Finding(
            id="FIN-manual-processes", dimension="04_operational", phase="ops",
            cluster="CLUSTER-finance-automation", file="backend/domains/finance",
            current=f"no implementation found for: {', '.join(manual)}",
            target="each finance process is a scheduled, auditable job with an "
                   "exception report",
            delta=f"{len(manual)} finance process(es) remain manual, which is where "
                  f"the reported workload lives",
            fix="implement each as a Celery task with an idempotent posting path and "
                "a daily exception report, and register it in the beat schedule",
            effort="XL", priority="P1", confidence=4, evidence_strength="multiple",
            truth_level="L1", claim_state="INFERRED", completion_blocker="no",
            verify="grep -rn 'bad_debt\\|gateway_fee' backend/domains/finance",
        ))
        res.recommendations.append(Recommendation(
            area="finance", dimension="04_operational",
            title="Automate the manual finance processes end to end",
            rationale="Finance is the largest recurring manual workload. Each missing "
                      "capability is a spreadsheet step that scales linearly with order "
                      "volume.",
            current=f"not automated: {', '.join(manual)}",
            proposal="sequence: (1) gateway-fee reconciliation from settlement "
                     "files, (2) automated COD remittance on bank credit match, "
                     "(3) daily bank reconciliation with an unmatched-items report, "
                     "(4) commission accrual at order capture instead of at payout, "
                     "(5) bad-debt provisioning by ageing bucket, (6) FX revaluation "
                     "on a nightly rate. Each writes a journal entry through the "
                     "existing `create_journal_entry` and is idempotent per period.",
            benefit="removes the recurring manual finance effort; makes the ledger "
                    "self-reconciling",
            effort="XL", impact="high", category="automation",
            evidence=f"backend/domains/finance (missing: {', '.join(manual)})",
            human_effort_saved="multi-day per month of finance reconciliation",
            prerequisites=("WF-celery-app-missing", "WF-dangling-import"),
        ))
    return res
