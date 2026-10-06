"""Dimension 03 (logical) + Dimension 22 (anti-patterns) + Dimension 25 (AI drift, static)."""
from __future__ import annotations

import ast
import re
from pathlib import Path

from zz_core.constants import MONEY_FILE_HINTS, MONEY_FIELD_HINTS
from zz_core.model import CheckResult, Finding, Observation, ScanContext
from zz_core.registry import check
from zz_core.util import (
    ast_calls, iter_functions, max_nesting, parse_python,
)

CODE_DIRS = ("domains", "modules", "rbac", "kernel", "infrastructure",
             "providers", "jobs", "middleware")

MONEY_RX = re.compile("|".join(MONEY_FIELD_HINTS), re.IGNORECASE)


def _core_files(ctx: ScanContext) -> list[Path]:
    out = []
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if rel.startswith("backend/tests/") or "/alembic/" in rel or rel.startswith("backend/scripts/"):
            continue
        if any(rel.startswith(f"backend/{d}/") for d in CODE_DIRS) or rel in (
                "backend/main.py", "backend/config.py", "backend/lifespan.py"):
            out.append(p)
    return out


def _f(dimension, phase, file, line, current, target, fix, *, priority="P2",
       effort="M", laws=(), blocker="no", confidence=4, cluster="",
       truth="L0", claim="VERIFIED", evidence="multiple", origin="static",
       snippet="", verify="", blast="", depends="", blocks="") -> Finding:
    return Finding(
        id="", dimension=dimension, phase=phase, cluster=cluster, file=file,
        line=line, current=current, target=target, delta=current[:180], fix=fix,
        effort=effort, priority=priority, confidence=confidence,
        evidence_strength=evidence, truth_level=truth, claim_state=claim,
        completion_blocker=blocker, laws=laws, origin=origin, snippet=snippet,
        verify=verify, blast_radius=blast, depends_on=depends, blocks=blocks,
    )


# --------------------------------------------------------------------------- #
# Money / float (Law 19)
# --------------------------------------------------------------------------- #

@check("logic_money_type", "03_logical", "logic",
       "AST scan for float-for-money: Float columns, float() casts near money "
       "terms, float annotations on money fields, float money config (Law 19).")
def logic_money_type(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="logic_money_type", dimension="03_logical")
    hits: list[tuple[str, int, str, str]] = []  # file, line, kind, snippet
    for p in _core_files(ctx):
        rel = ctx.rel(p)
        parsed = parse_python(p)
        if parsed.error:
            continue
        money_file = any(h in rel.lower() for h in MONEY_FILE_HINTS)
        text = parsed.text
        lines = text.splitlines()

        def is_rate(name: str) -> bool:
            """Law 19 forbids float for MONEY. A rate/percentage/ratio/score is
            not money: 4 of 14 adjudicated samples were exactly that.

            This is called both with an IDENTIFIER (`amount`, `open_rate`) and
            with a whole SOURCE LINE (`    open_rate = round(...)`). It used to
            anchor the token with `^`/`$`, which an identifier satisfies but a
            line never does, so every `round()`-on-a-rate line was reported as
            float-for-money. Seven findings were exactly that:
            `open_rate`, `click_through_rate`, `return_rate` and `percent`.

            The anchor is therefore a *word* boundary, not the ends of the string:
            `(?<![a-z])` still blocks `credit` matching `rate`, and `_` counts as
            a boundary so `open_rate` matches while `revenue` does not.
            """
            return bool(re.search(
                r"(?<![a-z])(?:rate|percent|pct|ratio|score|weight|multiplier|"
                r"factor|coefficient|marquee)(?:s|es)?(?![a-z])",
                name, re.I))

        def converted_to_decimal(ln: int) -> bool:
            """A transport float that becomes a Decimal before it is stored is
            not a Law 19 violation; it is the correct boundary."""
            window = "\n".join(lines[max(0, ln - 6):ln + 12])
            return bool(re.search(r"Decimal\s*\(|ctrl_validate|to_decimal|"
                                  r"quantize\s*\(\s*Decimal|str\([^)]*\)\s*\)", window))

        for node in ast.walk(parsed.tree):
            # Float column in a money-named field
            if isinstance(node, ast.Call):
                name = getattr(node.func, "id", "") or getattr(node.func, "attr", "")
                line_text = lines[node.lineno - 1] if node.lineno - 1 < len(lines) else ""
                if name == "Float" and MONEY_RX.search(line_text) \
                        and not is_rate(line_text):
                    hits.append((rel, node.lineno, "Float-column-money", line_text.strip()[:200]))
                if name == "float":
                    ctx_text = line_text
                    if MONEY_RX.search(ctx_text) and not is_rate(ctx_text) \
                            and not converted_to_decimal(node.lineno):
                        hits.append((rel, node.lineno, "float-cast-money", ctx_text.strip()[:200]))
            # float annotation on a money field
            if isinstance(node, ast.AnnAssign):
                ann = ast.unparse(node.annotation) if hasattr(ast, "unparse") else ""
                target = ast.unparse(node.target) if hasattr(ast, "unparse") else ""
                if "float" in ann.lower() and MONEY_RX.search(target) \
                        and not is_rate(target) \
                        and not converted_to_decimal(node.lineno):
                    hits.append((rel, node.lineno, "float-annotation-money",
                                 f"{target}: {ann}"))
            if isinstance(node, ast.arg) and node.annotation is not None:
                ann = ast.unparse(node.annotation) if hasattr(ast, "unparse") else ""
                if "float" in ann.lower() and MONEY_RX.search(node.arg) \
                        and not is_rate(node.arg) \
                        and not converted_to_decimal(node.lineno):
                    hits.append((rel, node.lineno, "float-param-money",
                                 f"{node.arg}: {ann}"))
        # round() on money lines
        for idx, line in enumerate(lines, 1):
            if re.search(r"\bround\(", line) and MONEY_RX.search(line) \
                    and not is_rate(line):
                if "$" not in line and "Decimal" not in line:
                    hits.append((rel, idx, "round-on-money", line.strip()[:200]))
    # group by file (cap 6 per file)
    by_file: dict[str, list] = {}
    for rel, line, kind, snip in hits:
        by_file.setdefault(rel, []).append((line, kind, snip))
    for rel, items in sorted(by_file.items()):
        top = items[0]
        finance_path = any(h in rel.lower() for h in ("finance", "payment", "payout", "ledger", "tax", "order"))
        res.findings.append(_f(
            "03_logical", "logic", rel, top[0],
            f"{len(items)} float-for-money signal(s); first: `{top[2]}`",
            "monetary values use Decimal/Numeric only (Law 19)",
            "Convert to Decimal and use kernel.money rounding helpers",
            priority="P0" if finance_path else "P1",
            blocker="yes" if finance_path else "partial",
            laws=(19,), cluster="CLUSTER-float-money", truth="L0",
            verify=f"grep -nE 'float\\(|Float|: float' {rel} | head -20",
            snippet=top[2], blast="money calculations, payouts, tax, commissions",
        ))
    res.facts["float_money_files"] = len(by_file)
    return res


# --------------------------------------------------------------------------- #
# Silent excepts (Law 59)
# --------------------------------------------------------------------------- #

def _effective_length(text: str, start: int, end: int) -> int:
    """Lines a human would count, per Law 64: docstrings and blanks excluded.

    Law 64 reads "Functions SHOULD NOT exceed 50 lines (excl. docstrings/blanks)".
    Counting the raw span instead inflated every function containing a SQL
    literal, a big dict, or a module docstring into a false positive.
    """
    lines = text.splitlines()[start - 1:end]
    count = 0
    in_doc = False
    delim = ""
    for raw in lines:
        s = raw.strip()
        if not s:
            continue
        if not in_doc:
            for q in ('"""', "'''"):
                if s.startswith(q) or (q in s and len(s.split(q)[0]) == 0):
                    delim = q
                    if s.count(q) < 2 or s.endswith(q):
                        in_doc = False
                    else:
                        in_doc = True
                    break
            if delim and in_doc:
                continue
            count += 1
        else:
            if delim in s:
                in_doc = False
    return count


@check("logic_silent_excepts", "03_logical", "logic",
       "Find except blocks that neither log, re-raise, return a fallback, nor "
       "perform a domain action (Law 59, AP-004). A handler that deliberately "
       "returns a default or collects the error is handling the exception and "
       "is NOT silent.")
def logic_silent_excepts(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="logic_silent_excepts", dimension="03_logical")
    # Every stdlib/application logging verb. `debug` was missing and alone
    # accounted for a large share of false positives: `logger.debug(...)` reads
    # as silent to a naive matcher but is a deliberate, documented choice.
    LOG_NAMES = ("log", "warning", "warn", "error", "exception", "critical",
                 "fatal", "print", "debug", "info", "notice", "trace",
                 "event", "record_event", "audit", "track")
    by_file: dict[str, list[tuple[int, str]]] = {}
    for p in _core_files(ctx):
        parsed = parse_python(p)
        if parsed.error:
            continue
        lines = parsed.text.splitlines()
        for node in ast.walk(parsed.tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            # `except NotImplementedError: raise` in an ABC is a contract, not a
            # swallowed error.
            exc_names = []
            if node.type is not None:
                exc_names = [n for n in (ast.unparse(node.type),)]
            is_contract = any(
                n in ("NotImplementedError", "SystemExit", "KeyboardInterrupt",
                      "GeneratorExit", "asyncio.CancelledError", "CancelledError",
                      "ImportError", "ModuleNotFoundError", "OptionalDependencyError")
                for n in exc_names)
            # An optional-import guard (`except ImportError: HAS_X = False`) is
            # the documented graceful-degradation pattern required by Law 30.
            # A `# pragma: no cover - defensive` marker or an explanatory comment
            # records a deliberate decision, which Law 59 does not forbid.
            node_src = ast.get_source_segment(parsed.text, node) or ""
            documented = bool(re.search(r"#\s*pragma:?\s*no cover|"
                                        r"#\s*(?:intentional|deliberate|best[- ]effort|"
                                        r"defensive|graceful|optional|suppress)", node_src, re.I))
            body = node.body
            has_log = False
            has_raise = False
            has_action = False
            has_return = False
            for stmt in body:
                if isinstance(stmt, ast.Return):
                    # Returning a default, an error envelope, or a collected
                    # error IS the handling. Adjudication showed most "silent"
                    # handlers in this repo are exactly this shape.
                    has_return = True
                for sub in ast.walk(stmt):
                    if isinstance(sub, ast.Call):
                        name = (getattr(sub.func, "attr", "")
                                or getattr(sub.func, "id", "") or "")
                        low = name.lower()
                        if any(k in low for k in LOG_NAMES):
                            has_log = True
                        if name in ("emit", "publish", "rollback", "add", "delete",
                                    "handle", "raise_", "set_", "update",
                                    "append", "extend", "notify", "capture"):
                            has_action = True
                    if isinstance(sub, ast.Raise):
                        has_raise = True
                if isinstance(stmt, ast.Raise):
                    has_raise = True
            if has_log or has_raise or has_action or has_return or is_contract or documented:
                continue
            line = (lines[node.lineno - 1].strip()
                    if node.lineno - 1 < len(lines) else "except")
            if len(body) == 1 and isinstance(body[0], ast.Pass):
                kind = "pass-only"
            else:
                kind = "truly-silent"
            by_file.setdefault(ctx.rel(p), []).append((node.lineno, f"{kind}: {line[:160]}"))
    total = 0
    for rel, items in sorted(by_file.items(), key=lambda kv: -len(kv[1])):
        total += len(items)
        finance_path = any(h in rel.lower() for h in ("finance", "payment", "payout", "ledger", "tax", "security", "supplier"))
        line, snip = items[0]
        res.findings.append(_f(
            "03_logical", "logic", rel, line,
            f"{len(items)} silent except block(s); first at line {line}: {snip}",
            "all except blocks log at minimum DEBUG (Law 59)",
            "Add logger.warning(..., exc_info=True) or re-raise",
            priority="P1" if finance_path else "P2",
            blocker="partial" if finance_path else "no",
            laws=(59,), cluster="CLUSTER-silent-except",
            verify=f"grep -n 'except' {rel}",
        ))
    res.facts["silent_except_count"] = total
    res.facts.setdefault("anti_patterns", []).append({
        "id": "AP-silent-except", "category": "Silent except",
        "occurrences": total, "sample": next(iter(by_file), "—"),
        "blocker": "partial" if total else "no",
        "remediation": "Log or re-raise in every handler",
    })
    return res


# --------------------------------------------------------------------------- #
# Blocking I/O in async (Law 60)
# --------------------------------------------------------------------------- #

BLOCKING_RX = [
    (re.compile(r"\btime\.sleep\("), "time.sleep in async"),
    (re.compile(r"(?<!await )\brequests\.(get|post|put|delete|request)\("), "sync requests.* call"),
    (re.compile(r"\bloop\.run_until_complete\("), "loop.run_until_complete in async"),
    (re.compile(r"\burllib\.request\.urlopen\("), "urlopen in async"),
    (re.compile(r"\bsubprocess\.run\("), "subprocess.run without to_thread"),
    (re.compile(r"\bopen\([^)]*\)(?!\s*[,)]?.*as)"), "sync open() in async"),
]


@check("logic_blocking_io", "03_logical", "logic",
       "Find blocking calls inside async functions (Law 60).")
def logic_blocking_io(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="logic_blocking_io", dimension="03_logical")
    hits: list[tuple[str, int, str]] = []
    for p in _core_files(ctx):
        parsed = parse_python(p)
        if parsed.error:
            continue
        lines = parsed.text.splitlines()
        for name, node, start, end, _depth in iter_functions(parsed.tree):
            if not isinstance(node, ast.AsyncFunctionDef):
                continue
            for idx in range(start, min(end, len(lines)) + 1):
                line = lines[idx - 1]
                if "await" in line and "subprocess" not in line:
                    continue
                for rx, label in BLOCKING_RX:
                    if rx.search(line) and "to_thread" not in line and "asyncio" not in line:
                        hits.append((ctx.rel(p), idx, f"{label}: {line.strip()[:180]}"))
                        break
    seen = set()
    for rel, line, snip in hits:
        if (rel, line) in seen:
            continue
        seen.add((rel, line))
        res.findings.append(_f(
            "03_logical", "logic", rel, line, snip,
            "async handlers must not block the event loop (Law 60)",
            "Use asyncio.sleep / httpx / run_in_executor",
            priority="P1", laws=(60,), cluster="CLUSTER-blocking-async",
            verify=f"sed -n '{line}p' {rel}",
        ))
    res.facts["blocking_async_count"] = len(seen)
    return res


# --------------------------------------------------------------------------- #
# Idempotency (Law 239)
# --------------------------------------------------------------------------- #

@check("logic_idempotency", "03_logical", "logic",
       "Check payment/order/refund/webhook handlers for Idempotency-Key "
       "enforcement; find optional idempotency_key fields (Law 239).")
def logic_idempotency(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="logic_idempotency", dimension="03_logical")
    core = _core_files(ctx)
    idem_hits = 0
    for p in core:
        rel = ctx.rel(p)
        if not any(h in rel.lower() for h in ("payment", "webhook", "payout", "refund")):
            continue
        parsed = parse_python(p)
        if parsed.error:
            continue
        text = parsed.text
        if re.search(r"idempotency", text, re.IGNORECASE):
            idem_hits += 1
    # optional idempotency fields
    for p in core:
        rel = ctx.rel(p)
        parsed = parse_python(p)
        if parsed.error:
            continue
        text = parsed.text
        for idx, line in enumerate(text.splitlines(), 1):
            if re.search(r"idempotency_key\s*:\s*Optional", line):
                res.findings.append(_f(
                    "03_logical", "logic", rel, idx, line.strip()[:200],
                    "idempotency keys are REQUIRED on payment/order/refund/webhook paths (Law 239)",
                    "Make the idempotency key required and enforce uniqueness",
                    priority="P0", blocker="yes", laws=(239,),
                    cluster="CLUSTER-idempotency",
                    verify=f"sed -n '{idx}p' {rel}",
                ))
    # payment routers without any idempotency reference
    for p in core:
        rel = ctx.rel(p)
        if "/routers/" not in rel:
            continue
        if not any(h in rel.lower() for h in ("payment", "webhook")):
            continue
        text, _ = ctx.read(p)
        if "idempotency" not in (text or "").lower():
            res.findings.append(_f(
                "03_logical", "logic", rel, 1,
                "payment/webhook router has no idempotency handling",
                "Idempotency-Key required on payment, order, refund, webhook endpoints (Law 239)",
                "Enforce the Idempotency-Key header via cache-backed dedupe",
                priority="P0", blocker="yes", laws=(239,),
                cluster="CLUSTER-idempotency",
                truth="L1", claim="INFERRED", evidence="multiple",
            ))
    res.facts["idempotency_files"] = idem_hits
    return res


# --------------------------------------------------------------------------- #
# Quality: length, nesting, TODO hygiene, magic numbers, unbounded caches
# --------------------------------------------------------------------------- #

@check("logic_quality", "03_logical", "logic",
       "Function length/nesting, TODO/FIXME hygiene, unbounded module caches, "
       "magic numbers in money paths (Laws 61, 62, 64, 65, 66).")
def logic_quality(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="logic_quality", dimension="03_logical")
    long_funcs: list[tuple[str, str, int, int]] = []
    deep_funcs: list[tuple[str, int, int]] = []
    todos: list[tuple[str, int, str]] = []
    caches: list[tuple[str, int, str]] = []
    for p in _core_files(ctx):
        rel = ctx.rel(p)
        parsed = parse_python(p)
        if parsed.error:
            continue
        for name, node, start, end, _depth in iter_functions(parsed.tree):
            # Law 64 excludes docstrings and blank lines from the count.
            # Counting raw span made every function carrying a long SQL
            # literal or a big dict look like a Law 64 violation, and 6/6
            # adjudicated samples were false positives on that basis.
            length = _effective_length(parsed.text, start, end)
            if length > 50:
                long_funcs.append((rel, name, start, length))
            depth = max_nesting(node)
            if depth > 4:
                deep_funcs.append((rel, start, depth))
        for idx, line in enumerate(parsed.text.splitlines(), 1):
            if re.search(r"\b(TODO|FIXME|HACK|XXX)\b", line):
                if not re.search(r"(#\d+|[A-Z]+-\d+|\d{4}-\d{2}-\d{2})", line):
                    todos.append((rel, idx, line.strip()[:180]))
            if re.search(r"^\s*[A-Z_]+\s*[:=]\s*\{", line) and "_CACHE" in line:
                caches.append((rel, idx, line.strip()[:180]))
    res.facts["long_functions"] = len(long_funcs)
    res.facts["deep_functions"] = len(deep_funcs)
    res.facts["untracked_todos"] = len(todos)
    if long_funcs:
        by_file: dict[str, list] = {}
        for rel, name, line, length in long_funcs:
            by_file.setdefault(rel, []).append((name, line, length))
        for rel, items in sorted(by_file.items(), key=lambda kv: -len(kv[1]))[:60]:
            name, line, length = items[0]
            res.findings.append(_f(
                "03_logical", "logic", rel, line,
                f"{len(items)} function(s) >50 lines; longest sample `{name}` = {length} lines",
                "functions SHOULD stay <=50 lines (Law 64)",
                "Split the longest functions by responsibility",
                priority="P3", laws=(64,), cluster="CLUSTER-long-function",
            ))
    if deep_funcs:
        res.findings.append(_f(
            "03_logical", "logic", deep_funcs[0][0], deep_funcs[0][1],
            f"{len(deep_funcs)} function(s) exceed 4 nesting levels (max seen {max(d[2] for d in deep_funcs)})",
            "maximum 4 indentation levels per function (Law 65)",
            "Refactor with guard clauses / extracted helpers",
            priority="P3", laws=(65,), cluster="CLUSTER-deep-nesting",
        ))
    if todos:
        sample = "; ".join(f"{rel}:{line}" for rel, line, _ in todos[:5])
        res.findings.append(_f(
            "03_logical", "logic", todos[0][0], todos[0][1],
            f"{len(todos)} TODO/FIXME without ticket reference or expiration date "
            f"(e.g. {sample})",
            "TODO/FIXME carry a ticket reference and expiration date (Law 62)",
            "Link each TODO to a ticket or delete it",
            priority="P2", laws=(62,), cluster="CLUSTER-todo-hygiene",
            evidence="multiple",
        ))
    if caches:
        res.findings.append(_f(
            "03_logical", "logic", caches[0][0], caches[0][1],
            f"{len(caches)} module-level cache candidate(s) (no TTL/size visible)",
            "in-memory caches are bounded with max size/TTL (Law 61)",
            "Replace with bounded/TTL caches or Valkey",
            priority="P2", laws=(61,), cluster="CLUSTER-unbounded-cache",
            truth="L1", claim="INFERRED",
        ))
    return res


# --------------------------------------------------------------------------- #
# Stubs / defaults masking failure / placeholders (AP categories)
# --------------------------------------------------------------------------- #

@check("logic_stubs_and_placeholders", "22_anti_patterns", "logic",
       "TODO-only bodies, NotImplementedError stubs, pass-only handlers, "
       "'not yet wired' placeholders, truthy-string defaults (AP-001..AP-020).")
def logic_stubs_and_placeholders(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="logic_stubs_and_placeholders", dimension="22_anti_patterns")
    categories: dict[str, dict] = {}
    for p in _core_files(ctx):
        rel = ctx.rel(p)
        parsed = parse_python(p)
        if parsed.error:
            continue
        text = parsed.text
        # NotImplementedError
        for idx, line in enumerate(text.splitlines(), 1):
            if "NotImplementedError" in line:
                categories.setdefault("Stub function (NotImplementedError)", {
                    "count": 0, "sample": f"{rel}:{idx}", "blocker": "partial",
                    "remediation": "Implement or remove the stub",
                })["count"] += 1
            if re.search(r"(?i)not yet wired|not yet implemented|coming soon|module not yet created", line):
                categories.setdefault("Unimplemented placeholder", {
                    "count": 0, "sample": f"{rel}:{idx}", "blocker": "yes",
                    "remediation": "Implement or remove the placeholder endpoint",
                })["count"] += 1
        # pass-only function bodies
        for name, node, start, end, _d in iter_functions(parsed.tree):
            body = [s for s in node.body if not isinstance(s, ast.Expr) or not isinstance(getattr(s, "value", None), ast.Constant) or not isinstance(s.value.value, str)]
            if len(body) == 1 and isinstance(body[0], ast.Pass):
                categories.setdefault("Empty handler (pass)", {
                    "count": 0, "sample": f"{rel}:{start}", "blocker": "partial",
                    "remediation": "Implement or delete the handler",
                })["count"] += 1
        # TODO-only implementation heuristic: file body mostly comments/TODO
        todo_lines = len(re.findall(r"#.*TODO|#\s*Future:", text))
        code_lines = len([l for l in text.splitlines() if l.strip() and not l.strip().startswith("#")])
        if todo_lines >= 5 and code_lines < todo_lines:
            categories.setdefault("TODO-only implementation", {
                "count": 0, "sample": f"{rel}:1", "blocker": "yes",
                "remediation": "Replace TODO scaffolding with real implementations",
            })["count"] += todo_lines
        # truthy-string defaults
        for idx, line in enumerate(text.splitlines(), 1):
            if re.search(r"getenv\([^)]*\)\s*==\s*[\"']false[\"']", line, re.IGNORECASE):
                categories.setdefault("Default masks failure (truthy string)", {
                    "count": 0, "sample": f"{rel}:{idx}", "blocker": "partial",
                    "remediation": "Use typed pydantic-settings booleans (Law 84)",
                })["count"] += 1
    for cat, data in categories.items():
        res.facts.setdefault("anti_patterns", []).append({
            "id": f"AP-{re.sub(r'[^a-z]+', '-', cat.lower()).strip('-')}",
            "category": cat, "occurrences": data["count"],
            "sample": data["sample"], "blocker": data["blocker"],
            "remediation": data["remediation"],
        })
        res.findings.append(_f(
            "22_anti_patterns", "logic", data["sample"].split(":")[0],
            int(data["sample"].split(":")[1]) if data["sample"].count(":") == 1 else 0,
            f"{cat}: {data['count']} occurrence(s); sample `{data['sample']}`",
            "no stubs/placeholders on live paths (AP catalog)",
            data["remediation"], priority="P1" if data["blocker"] == "yes" else "P2",
            blocker=data["blocker"], cluster=f"CLUSTER-ap-{re.sub(r'[^a-z]+', '-', cat.lower()).strip('-')}",
            effort="M" if data["blocker"] == "yes" else "S",
        ))
    return res


# --------------------------------------------------------------------------- #
# AI drift (static detectors)
# --------------------------------------------------------------------------- #

@check("drift_static", "25_ai_drift", "logic",
       "Comment/code divergence, phantom imports, unused parameters, docstring "
       "drift, naming drift (dimension 25 static detectors).")
def drift_static(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="drift_static", dimension="25_ai_drift")
    core = _core_files(ctx)
    # phantom imports: module names that look like project modules but don't exist
    known = {p.stem for p in ctx.py_files}
    pkg_names = set()
    for p in ctx.py_files:
        try:
            rel = p.relative_to(ctx.backend)
        except ValueError:
            continue  # repo-root scripts are not importable project modules
        if rel.suffix == ".py":
            pkg_names.add(str(rel).replace("\\", "/").replace("/", ".")[:-3])
    for p in core:
        parsed = parse_python(p)
        if parsed.error:
            continue
        from zz_core.util import ast_imports
        for module, names, line, kind in ast_imports(parsed.tree):
            if not module or module.startswith("."):
                continue
            top = module.split(".")[0]
            if top not in ("domains", "modules", "infrastructure", "kernel", "rbac",
                           "providers", "jobs", "middleware"):
                continue
            resolved = module in pkg_names or any(n.startswith(module + ".") for n in pkg_names)
            if not resolved and module != top:
                res.facts.setdefault("drift", []).append({
                    "id": f"DRIFT-phantom-import-{len(res.facts.get('drift', []))+1}",
                    "type": "Phantom import", "location": f"{ctx.rel(p)}:{line}",
                    "divergence": f"imports `{module}` which does not resolve in-tree",
                    "blocker": "partial", "evidence": f"{ctx.rel(p)}:{line}",
                })
        # unused function parameters (name never referenced in body)
        for name, node, start, end, _d in iter_functions(parsed.tree):
            args = [a.arg for a in getattr(node.args, "args", []) if a.arg not in ("self", "cls")]
            body_src = "\n".join((parsed.text.splitlines())[start:end])
            body_only = "\n".join((parsed.text.splitlines())[start + 1:end])
            unused = [a for a in args if not re.search(rf"\b{re.escape(a)}\b", body_only)]
            if unused and len(unused) < len(args):
                res.facts.setdefault("drift", []).append({
                    "id": f"DRIFT-unused-param-{len(res.facts.get('drift', []))+1}",
                    "type": "Unused parameter drift",
                    "location": f"{ctx.rel(p)}:{start} ({name})",
                    "divergence": f"parameter(s) never used: {', '.join(unused[:4])}",
                    "blocker": "no", "evidence": f"{ctx.rel(p)}:{start}",
                })
    # comment says TODO/Future while body is live? (comment/code divergence heuristic)
    for p in core[:1500]:
        rel = ctx.rel(p)
        text, _ = ctx.read(p)
        if not text:
            continue
        for idx, line in enumerate(text.splitlines(), 1):
            if "# Future:" in line and idx > 0:
                res.facts.setdefault("drift", []).append({
                    "id": f"DRIFT-comment-divergence-{len(res.facts.get('drift', []))+1}",
                    "type": "Comment/code divergence",
                    "location": f"{rel}:{idx}",
                    "divergence": "`# Future:` marker in live code — unfinished behaviour documented as future work",
                    "blocker": "partial", "evidence": f"{rel}:{idx}",
                })
    return res
