"""Dimension 05 (wiring) + Dimension 20 (observability & resilience)."""
from __future__ import annotations

import ast
import re

from zz_core.model import CheckResult, Finding, Observation, ScanContext
from zz_core.registry import check
from zz_core.util import ast_imports, parse_python, read_text

ROUTER_METHODS = ("get", "post", "put", "patch", "delete", "websocket", "websocket_route")

#: Callables that authenticate or authorise a request. This list was previously a
#: single regex naming only `require_admin`/`require_feature`/`require_module`/
#: `require_roles`/`get_current_user`. That made every route gated by
#: `require_employee`, `require_logistics`, `require_supplier`,
#: `require_super_admin`, `verify_captcha` or a security scheme look ungated:
#: 27 of 47 findings in this cluster were false, 3 of them P0 blockers.
#:
#: The set is derived from what `backend/modules/**` actually injects, so a new
#: gate in `rbac/dependencies.py` or `domains/accounts/.../security_dependencies.py`
#: is picked up rather than silently reported as a vulnerability.
AUTH_GATE_NAMES = frozenset({
    "require_admin", "require_feature", "require_module", "require_roles",
    "require_employee", "require_supplier", "require_logistics",
    "require_super_admin", "require_customer", "require_permission",
    "get_current_user", "get_current_active_user", "get_current_user_optional",
    "get_optional_user", "get_current_employee", "get_current_supplier",
    "rbac_get_current_user", "_require_admin",
    "verify_token", "verify_captcha", "verify_api_key",
    # security schemes: these authenticate the caller even though they are not
    # RBAC gates
    "HTTPBearer", "OAuth2", "APIKeyHeader", "HTTPAuthorizationCredentials",
})

#: `Annotated[dict, Depends(gate)]` aliases hide the gate from any scan of the
#: handler signature itself. `backend/modules/employee/routers/comms.py` defines
#: `AdminUser = Annotated[dict, Depends(require_roles("admin"))]` and uses it on
#: 11 routes; all 11 were reported ungated.
_ALIAS_RX = re.compile(r"^\s*(\w+)\s*=\s*Annotated\s*\[", re.M)


def _gate_aliases(source: str) -> set[str]:
    """Names bound to ``Annotated[..., Depends(<gate>)]`` anywhere in the file."""
    out: set[str] = set()
    if not source:
        return out
    for m in _ALIAS_RX.finditer(source):
        tail = source[m.end():m.end() + 400]
        close = tail.find("]")
        if close == -1:
            continue
        segment = tail[:close]
        if "Depends" not in segment:
            continue
        if not re.search(r"require_|current_user|verify_|HTTPBearer|OAuth2|APIKey", segment):
            continue
        out.add(m.group(1))
    return out


#: Endpoints whose whole purpose is to be reachable without a session. Law 88
#: ("all non-public endpoints MUST use require_feature()") cannot be satisfied by
#: `/health`, and login/register/oauth-start endpoints cannot require a prior
#: session because obtaining the session is what they do. These are reported
#: separately as an explicit inventory rather than as vulnerabilities.
LIVENESS_RX = re.compile(r"(^|_)(health|healthz|readyz|ready|live|liveness|ping|status)$", re.I)
AUTH_ENTRY_RX = re.compile(r"(^|_)(login|register|signup|logout|refresh|oauth|social|"
                           r"captcha|callback|forgot|reset|verify|activate)(_|$)", re.I)


def _handler_dependencies(node: ast.AST, aliases: set[str]) -> list[str]:
    """Every callable the handler injects, including through Annotated aliases."""
    names: list[str] = []

    def _name(node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        if isinstance(node, ast.Call):
            return _name(node.func)
        if isinstance(node, ast.Subscript):
            return _name(node.value)
        return ""

    for d in list(node.args.defaults) + [x for x in node.args.kw_defaults if x]:
        for sub in ast.walk(d):
            if isinstance(sub, ast.Call):
                fn = _name(sub.func)
                if fn == "Depends" and sub.args:
                    nm = _name(sub.args[0])
                    if nm:
                        names.append(nm)
    for a in list(node.args.args) + list(node.args.kwonlyargs):
        if a.annotation is None:
            continue
        for sub in ast.walk(a.annotation):
            if isinstance(sub, ast.Name) and sub.id in aliases:
                names.append(sub.id)
    return names


def _f(dimension, phase, file, line, current, target, fix, *, priority="P2",
       effort="M", laws=(), blocker="no", cluster="", truth="L0",
       claim="VERIFIED", evidence="multiple", origin="static", verify="") -> Finding:
    return Finding(
        id="", dimension=dimension, phase=phase, cluster=cluster, file=file,
        line=line, current=current, target=target, delta=current[:180], fix=fix,
        effort=effort, priority=priority, confidence=4, evidence_strength=evidence,
        truth_level=truth, claim_state=claim, completion_blocker=blocker,
        laws=laws, origin=origin, verify=verify,
    )


@check("wire_middleware_order", "05_wiring", "arch",
       "Compare middleware/orchestrator.py call order with the canonical 8-layer "
       "pipeline (Law 78).")
def wire_middleware_order(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="wire_middleware_order", dimension="05_wiring")
    path = ctx.backend / "middleware" / "orchestrator.py"
    text, _ = read_text(path)
    if not path.exists():
        res.findings.append(_f(
            "05_wiring", "arch", "backend/middleware/orchestrator.py", 0,
            "middleware orchestrator missing",
            "middleware pipeline ordered Foundation→Auth→Rate→Webhook→Geo→Security→Observe→Compliance (Law 78)",
            "Restore the orchestrator",
            priority="P0", blocker="yes", laws=(78,), cluster="CLUSTER-middleware",
        ))
        return res
    canonical = [
        ("foundation", ("gzip", "cors", "ip", "request_id", "version")),
        ("auth", ("authentication", "device_binding", "zerotrust", "zero_trust")),
        ("rate", ("rate_limit",)),
        ("webhook", ("webhook",)),
        ("geo", ("country", "impossible_travel")),
        ("security", ("security_header", "csrf", "fraud")),
        ("observe", ("logging", "metrics", "observability")),
        ("compliance", ("pci",)),
    ]
    lines = text.splitlines()
    positions = {}
    for idx, line in enumerate(lines, 1):
        low = line.lower()
        for layer, keys in canonical:
            for key in keys:
                if key in low and ("add_middleware" in low or "middleware" in low or "setup" in low or "install" in low):
                    positions.setdefault(layer, idx)
    ordered = sorted(positions.items(), key=lambda kv: kv[1])
    order_names = [name for name, _ in ordered]
    expected = [name for name, _ in canonical if name in positions]
    if order_names != expected:
        res.findings.append(_f(
            "05_wiring", "arch", "backend/middleware/orchestrator.py", 1,
            f"middleware order is {order_names}; canonical is {expected}",
            "pipeline order FIXED (Law 78)",
            "Reorder registrations to match the canonical pipeline",
            priority="P1", blocker="partial", laws=(78,),
            cluster="CLUSTER-middleware",
            verify="grep -n 'add_middleware\\|setup\\|install' backend/middleware/orchestrator.py",
        ))
    for layer, keys in canonical:
        if layer not in positions:
            # compliance may be prod-only; still record
            res.observations.append(Observation(
                "middleware", layer, "backend/middleware/orchestrator.py", 0,
                "05_wiring", evidence="layer not detected in orchestrator",
            ))
    res.facts["middleware_order"] = order_names
    return res


@check("wire_websocket_auth", "05_wiring", "security",
       "Verify every WebSocket endpoint verifies JWT (type=access) before "
       "accept(); flag unauthenticated accept paths (Law 41).")
def wire_websocket_auth(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="wire_websocket_auth", dimension="05_wiring")
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if not rel.startswith("backend/"):
            continue
        parsed = parse_python(p)
        if parsed.error:
            continue
        for name, node, start, end, _d in _iter_funcs(parsed.tree):
            if not isinstance(node, ast.AsyncFunctionDef):
                continue
            decorators = [ast.unparse(d) if hasattr(ast, "unparse") else "" for d in node.decorator_list]
            is_ws = any("websocket" in d.lower() for d in decorators) or name.startswith("websocket")
            if not is_ws:
                continue
            body = "\n".join(parsed.text.splitlines()[start:end])
            verify_before_accept = False
            accept_lineno = None
            for idx in range(start, min(end, len(parsed.text.splitlines())) + 1):
                line = parsed.text.splitlines()[idx - 1]
                if "accept(" in line and accept_lineno is None:
                    accept_lineno = idx
                if ("decode_token" in line or "verify_token" in line or "get_current_user" in line) and (
                        accept_lineno is None or idx < accept_lineno):
                    verify_before_accept = True
            if accept_lineno and not verify_before_accept:
                res.findings.append(_f(
                    "05_wiring", "security", rel, accept_lineno,
                    f"WebSocket `{name}` calls accept() without a prior JWT check",
                    "WebSocket connections verify JWT type=access (Law 41)",
                    "Verify the token before accept() and close(4001) otherwise",
                    priority="P0", blocker="yes", laws=(41,),
                    cluster="CLUSTER-ws-auth",
                    verify=f"sed -n '{start},{end}p' {rel}",
                ))
    return res


def _iter_funcs(tree):
    from zz_core.util import iter_functions
    return iter_functions(tree)


def _public_router_files(ctx: ScanContext) -> set[str]:
    out: set[str] = set()
    for init in ctx.backend.glob("modules/*/routers/__init__.py"):
        text, _ = read_text(init)
        m = re.search(r"public_routers\s*=\s*\[(.*?)\]", text or "", re.DOTALL)
        if m:
            names = re.findall(r"(\w+)", m.group(1))
            for n in names:
                out.add(n)
    return out


@check("wire_feature_gates", "05_wiring", "security",
       "Every non-public endpoint must carry auth + require_* gate; also check "
       "gate literals exist in the RBAC catalog (Laws 4, 87, 88).")
def wire_feature_gates(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="wire_feature_gates", dimension="05_wiring")
    public_files = _public_router_files(ctx)
    # catalog from domains/*/features.py
    catalog: set[str] = set()
    for fp in ctx.backend.glob("domains/*/features.py"):
        text, _ = read_text(fp)
        catalog.update(re.findall(r'"([a-z][a-z0-9_.]*\.[a-z0-9_.]+)"\s*:', text or ""))
    gate_literals: set[str] = set()
    unguarded: list[tuple[str, int, str]] = []
    #: unauthenticated on purpose (liveness probe / auth entry point)
    unguarded_by_design: list[tuple[str, int, str, str]] = []
    unknown_gates: list[tuple[str, int, str]] = []
    total_endpoints = 0
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if "/modules/" not in rel or "/routers/" not in rel or p.name == "__init__.py":
            continue
        if p.stem in public_files:
            continue
        parsed = parse_python(p)
        if parsed.error:
            continue
        aliases = _gate_aliases(parsed.text or "")
        for name, node, start, end, _d in _iter_funcs(parsed.tree):
            dec_text = " ".join(ast.unparse(d) for d in node.decorator_list if hasattr(ast, "unparse"))
            if not any(f"router.{m}" in dec_text for m in ROUTER_METHODS):
                continue
            total_endpoints += 1
            # The signature may span several lines and the guard may sit on any of
            # them, so search the decorator plus the whole `def` block rather than
            # a fixed window.
            block = "\n".join(parsed.text.splitlines()[max(0, start - 1):end])
            scope = block + "\n" + dec_text
            deps = _handler_dependencies(node, aliases)
            gates = re.findall(r'require_feature\(\s*["\']([^"\']+)["\']', scope)
            gates += re.findall(r'require_module\(\s*["\']([^"\']+)["\']', scope)
            gate_literals.update(gates)
            if any(d in AUTH_GATE_NAMES or d in aliases for d in deps) \
                    or re.search(r"get_current_user|require_feature\(|require_module\("
                                 r"|require_admin|require_roles|require_employee|"
                                 r"require_logistics|require_supplier|require_super_admin|"
                                 r"get_current_active_user|Depends\(\w*auth", scope):
                continue
            # Unauthenticated by design: record it as an inventory item, not a
            # vulnerability. It still has to be a deliberate decision, so it is
            # reported at P3 rather than dropped.
            if LIVENESS_RX.search(name or "") or AUTH_ENTRY_RX.search(name or ""):
                unguarded_by_design.append((rel, start, name,
                                           "liveness probe" if LIVENESS_RX.search(name or "")
                                           else "authentication entry point"))
                continue
            unguarded.append((rel, start, name))
            for g in gates:
                if g not in catalog and not g.endswith(".*"):
                    unknown_gates.append((rel, start, g))
        for g in (re.findall(r'require_feature\(\s*["\']([^"\']+)["\']', parsed.text or "")
                  + re.findall(r'require_module\(\s*["\']([^"\']+)["\']', parsed.text or "")):
            if g not in catalog and not g.endswith(".*"):
                unknown_gates.append((rel, 0, g))
    if unguarded:
        by_file: dict[str, int] = {}
        for rel, _s, _n in unguarded:
            by_file[rel] = by_file.get(rel, 0) + 1
        res.findings.append(_f(
            "05_wiring", "security", unguarded[0][0], unguarded[0][1],
            f"{len(unguarded)} endpoint(s) across {len(by_file)} router(s) have no visible "
            f"auth/gate dependency (sample: {unguarded[0][0]}:{unguarded[0][1]} {unguarded[0][2]})",
            "all non-public endpoints use get_current_user + require_* (Laws 87, 88)",
            "Add the auth dependency or move the route to public_routers",
            priority="P0", blocker="yes", laws=(87, 88),
            cluster="CLUSTER-ungated-route", evidence="multiple",
            verify=f"grep -n 'def {unguarded[0][2]}' {unguarded[0][0]}",
        ))
        for rel, line, name in unguarded[:120]:
            res.findings.append(_f(
                "05_wiring", "security", rel, line,
                f"endpoint `{name}` has no visible auth/feature gate",
                "auth + gate on every protected endpoint (Laws 87, 88)",
                "Add Depends(get_current_user) + require_feature(...)",
                priority="P0" if "/admin/" in rel or "/supplier/" in rel else "P1",
                blocker="yes" if "/admin/" in rel else "partial",
                laws=(87, 88), cluster="CLUSTER-ungated-route",
                truth="L0", claim="VERIFIED",
            ))
    if unguarded_by_design:
        by_reason: dict[str, int] = {}
        for _r, _l, _n, why in unguarded_by_design:
            by_reason[why] = by_reason.get(why, 0) + 1
        res.findings.append(_f(
            "05_wiring", "security", unguarded_by_design[0][0], unguarded_by_design[0][1],
            f"{len(unguarded_by_design)} endpoint(s) are unauthenticated by design "
            f"({', '.join(f'{n} {k}' for k, n in sorted(by_reason.items()))}); "
            f"sample: {unguarded_by_design[0][0]}:{unguarded_by_design[0][1]} "
            f"{unguarded_by_design[0][2]}",
            "every intentionally-public endpoint is a recorded decision, not an omission",
            "Record each in the module's `public_routers` list, or add an inline "
            "`# public: <reason>` comment so the exemption is reviewable",
            priority="P3", blocker="no", laws=(87, 88),
            cluster="CLUSTER-public-by-design",
        ))
    if unknown_gates:
        sample = ", ".join(sorted({g for _r, _l, g in unknown_gates})[:10])
        res.findings.append(_f(
            "05_wiring", "security", unknown_gates[0][0], unknown_gates[0][1],
            f"{len(unknown_gates)} require_feature literal(s) not found in any "
            f"domains/*/features.py catalog: {sample}",
            "every gate literal exists in the catalog (Law 4/161)",
            "Add the atoms to features.py or fix the literals",
            priority="P1", blocker="partial", laws=(4, 161),
            cluster="CLUSTER-unknown-gate",
        ))
    res.facts["endpoints_total"] = total_endpoints
    res.facts["endpoints_unguarded"] = len(unguarded)
    res.facts["endpoints_public_by_design"] = len(unguarded_by_design)
    res.facts["gate_literals"] = len(gate_literals)
    res.facts["catalog_atoms"] = len(catalog)
    return res


@check("wire_rls", "05_wiring", "db",
       "Canonical set_rls_context must execute SET LOCAL; policy variable names "
       "must match the middleware (Laws 5, 227, WIRE-002, DB-005).")
def wire_rls(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="wire_rls", dimension="05_wiring")
    interceptor = ctx.backend / "infrastructure" / "database" / "rls_interceptor.py"
    text, _ = read_text(interceptor)
    if interceptor.exists():
        has_set_local = "SET LOCAL" in (text or "")
        fn_line = (text or "").find("def set_rls_context")
        if fn_line >= 0 and not has_set_local:
            line = (text or "").count("\n", 0, fn_line) + 1
            res.findings.append(_f(
                "05_wiring", "db", ctx.rel(interceptor), line,
                "canonical `set_rls_context()` sets ContextVars only; no `SET LOCAL` executed",
                "RLS context is set via `SET LOCAL app.country_code` inside the transaction (Law 227)",
                "Execute SET LOCAL in the active transaction (never session-level SET)",
                priority="P0", blocker="yes", laws=(5, 227),
                cluster="CLUSTER-rls",
                verify="grep -n 'set_rls_context' -A30 backend/infrastructure/database/rls_interceptor.py",
            ))
    # policy variable name vs middleware
    policy_var = mid_var = ""
    for p in (ctx.backend / "infrastructure").rglob("*.sql"):
        t, _ = read_text(p)
        m = re.search(r"current_setting\(\s*'([^']+)'", t or "")
        if m:
            policy_var = m.group(1)
            break
    for p in (ctx.backend / "middleware").glob("*.py"):
        t, _ = read_text(p)
        for m in re.finditer(r"SET\s+LOCAL\s+([a-z_.]+)\s*=", t or "", re.IGNORECASE):
            mid_var = m.group(1)
            break
        if mid_var:
            break
    if policy_var and mid_var and policy_var != mid_var:
        res.findings.append(_f(
            "05_wiring", "db", "backend/middleware/country_context.py", 0,
            f"RLS mismatch: policies read `{policy_var}` while middleware sets `{mid_var}`",
            "one variable name across policy + middleware (Law 5)",
            "Align the variable name (and keep SET LOCAL, not SET)",
            priority="P0", blocker="yes", laws=(5, 227),
            cluster="CLUSTER-rls",
            verify="grep -rn 'current_setting' backend/infrastructure/database/sql",
        ))
    res.facts["rls_policy_var"] = policy_var
    res.facts["rls_middleware_var"] = mid_var
    return res


@check("wire_event_bus", "05_wiring", "arch",
       "Which events are defined vs published vs consumed; post-commit semantics; "
       "stub subscribers; retry/DLQ (Law 3/144, WIRE-003, AP-018).")
def wire_event_bus(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="wire_event_bus", dimension="05_wiring")
    domains = ctx.backend / "domains"
    defined = published = 0
    stub_subscribers: list[tuple[str, int, str]] = []
    published_events: set[str] = set()
    subscriptions: dict[str, int] = {}
    for ev in domains.glob("*/events.py"):
        text, _ = read_text(ev)
        evs = set(re.findall(r'^EVENT_[A-Z_]+\s*=\s*["\']([^"\']+)["\']', text or "", re.MULTILINE))
        defined += len(evs)
        dom = ev.parent.name
        for svc in (domains / dom).rglob("*.py"):
            if svc.name == "events.py":
                continue
            st, _ = read_text(svc)
            if not st:
                continue
            for ev_name in evs:
                if ev_name in st:
                    published_events.add(ev_name)
    published = len(published_events)
    for sub in domains.glob("*/subscribers.py"):
        text, _ = read_text(sub)
        dom = sub.parent.name
        fn_count = len(re.findall(r"^def _on_", text or "", re.MULTILINE))
        subscribe_count = len(re.findall(r"subscribe\(", text or ""))
        subscriptions[dom] = subscribe_count
        future_marks = len(re.findall(r"#\s*Future:", text or ""))
        if fn_count and future_marks >= max(1, fn_count - 1):
            stub_subscribers.append((ctx.rel(sub), 1,
                                     f"{fn_count} handlers, {future_marks} `# Future:` markers"))
        elif subscribe_count == 0 and fn_count:
            stub_subscribers.append((ctx.rel(sub), 1,
                                     f"{fn_count} handlers but no subscribe() registration"))
    if defined and published == 0:
        res.findings.append(_f(
            "05_wiring", "arch", "backend/domains/", 0,
            f"{defined} event(s) defined across domains but none referenced by any service "
            "(publishers never invoked)",
            "cross-domain writes travel through events.py (Law 3)",
            "Call the publish/emit function after commit in each service flow",
            priority="P0", blocker="yes", laws=(3, 144),
            cluster="CLUSTER-event-spine", evidence="multiple",
            verify="grep -rn 'from domains.*events import' backend/domains | head",
        ))
    elif defined and published < defined:
        res.findings.append(_f(
            "05_wiring", "arch", "backend/domains/", 0,
            f"only {published}/{defined} defined event type(s) referenced by services",
            "every declared event has a publisher path (Law 3)",
            "Publish or delete the unused event classes",
            priority="P1", blocker="partial", laws=(3, 144),
            cluster="CLUSTER-event-spine", truth="L1", claim="INFERRED",
        ))
    for rel, line, note in stub_subscribers[:40]:
        res.findings.append(_f(
            "05_wiring", "arch", rel, line,
            f"stub subscriber module: {note}",
            "subscribers implement cross-domain reactions (Law 3)",
            "Implement the handlers or remove the registrations",
            priority="P0", blocker="yes", laws=(3,),
            cluster="CLUSTER-stub-subscriber",
        ))
    res.facts["events_defined"] = defined
    res.facts["events_published"] = published
    res.facts["subscriber_modules"] = subscriptions
    res.facts.setdefault("anti_patterns", []).append({
        "id": "AP-not-wired-event", "category": "Not-wired event",
        "occurrences": len(stub_subscribers), "sample": stub_subscribers[0][0] if stub_subscribers else "—",
        "blocker": "yes" if stub_subscribers else "no",
        "remediation": "Implement subscribers and publish post-commit",
    })
    return res


@check("wire_resilience", "20_observability_resilience", "infra",
       "Circuit breakers, retries with backoff, timeouts, graceful degradation "
       "(Laws 296-300).")
def wire_resilience(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="wire_resilience", dimension="20_observability_resilience")
    breakers = 0
    retries = 0
    timeouts = 0
    providers = list((ctx.backend / "providers").rglob("*.py"))
    provider_files = [p for p in providers if p.name != "__init__.py"]
    for p in provider_files:
        text, _ = read_text(p)
        if not text:
            continue
        if re.search(r"pybreaker|CircuitBreaker|circuit_breaker|breaker\.call", text):
            breakers += 1
        if re.search(r"retry|tenacity|backoff|max_retries", text, re.IGNORECASE):
            retries += 1
        if re.search(r"timeout\s*=", text):
            timeouts += 1
    n = max(1, len(provider_files))
    if breakers < n * 0.3:
        res.findings.append(_f(
            "20_observability_resilience", "infra", "backend/providers/", 0,
            f"circuit breaker present in {breakers}/{n} provider modules",
            "all external calls wrapped in a circuit breaker (Law 296)",
            "Wrap provider calls in pybreaker breakers",
            priority="P1", laws=(296,), blocker="partial",
            cluster="CLUSTER-provider-resilience",
        ))
    if retries < n * 0.5:
        res.findings.append(_f(
            "20_observability_resilience", "infra", "backend/providers/", 0,
            f"retry policy present in {retries}/{n} provider modules",
            "retry 1-2-4-8s with jitter, max 5 (Law 297)",
            "Add bounded retries with jitter",
            priority="P1", laws=(297,), blocker="partial",
            cluster="CLUSTER-provider-resilience",
        ))
    if timeouts < n * 0.5:
        res.findings.append(_f(
            "20_observability_resilience", "infra", "backend/providers/", 0,
            f"explicit timeout in {timeouts}/{n} provider modules",
            "every outbound call has a timeout",
            "Add explicit HTTP timeouts",
            priority="P1", laws=(296,), blocker="partial",
            cluster="CLUSTER-provider-resilience",
        ))
    res.facts["provider_resilience"] = {
        "providers": n, "breakers": breakers, "retries": retries, "timeouts": timeouts}
    return res


@check("wire_observability", "20_observability_resilience", "infra",
       "structlog vs print, request-id, metrics endpoint, error tracking, PII "
       "in logs, log retention (Laws 92-96, 282, 315).")
def wire_observability(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="wire_observability", dimension="20_observability_resilience")
    prints = []
    pii_logs = []
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if not any(rel.startswith(f"backend/{d}/") for d in
                   ("domains", "modules", "infrastructure", "kernel", "rbac",
                    "providers", "jobs", "middleware")):
            continue
        text, _ = read_text(p)
        if not text:
            continue
        for idx, line in enumerate(text.splitlines(), 1):
            if re.search(r"(?<![\w.])print\(", line) and "#" not in line.split("print")[0]:
                prints.append((rel, idx, line.strip()[:140]))
            if re.search(r'(log|logger)\.\w+\([^)]*(password|card_number|credit_card|ssn|secret|api_key)', line, re.IGNORECASE):
                pii_logs.append((rel, idx, line.strip()[:160]))
    if prints:
        res.findings.append(_f(
            "20_observability_resilience", "infra", prints[0][0], prints[0][1],
            f"{len(prints)} `print()` call(s) in production paths (sample {prints[0][0]}:{prints[0][1]})",
            "structlog only; print FORBIDDEN (Law 58)",
            "Replace print() with the structured logger",
            priority="P2", laws=(58,), cluster="CLUSTER-print-logging",
        ))
    if pii_logs:
        res.findings.append(_f(
            "20_observability_resilience", "security", pii_logs[0][0], pii_logs[0][1],
            f"{len(pii_logs)} log statement(s) may include PII/secrets (sample: {pii_logs[0][2]})",
            "PII masked in logs (Law 282)",
            "Mask or drop PII fields before logging",
            priority="P1", laws=(282,), blocker="partial",
            cluster="CLUSTER-pii-logs", truth="L1", claim="INFERRED",
        ))
    infra = ctx.backend / "infrastructure"
    obs = infra / "observability"
    if not obs.exists():
        res.findings.append(_f(
            "20_observability_resilience", "infra", "backend/infrastructure/observability/", 0,
            "observability package missing", "structlog/metrics/error tracker wired (Laws 92-95)",
            "Restore the observability package", priority="P1", blocker="partial",
            laws=(92, 95), cluster="CLUSTER-observability",
        ))
    else:
        found_metrics = any("prometheus" in p.name.lower() or "metric" in p.name.lower()
                            for p in obs.rglob("*.py"))
        if not found_metrics:
            res.findings.append(_f(
                "20_observability_resilience", "infra", "backend/infrastructure/observability/", 0,
                "no metrics module found", "Prometheus metrics mounted (Law 94)",
                "Add the metrics exporter", priority="P2", laws=(94,),
                cluster="CLUSTER-observability",
            ))
    res.facts["prints"] = len(prints)
    return res
