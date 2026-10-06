"""Dimension 01 (architectural) + Dimension 17 (code & file management)."""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from zz_core.constants import (
    CANONICAL_DOMAINS, CANONICAL_MODULES, FORBIDDEN_ROOT_DIRS,
    CANONICAL_BACKEND_ROOT_ENTRIES, ROUTER_OK_INFRA,
)
from zz_core.model import CheckResult, Finding, Observation, ScanContext
from zz_core.registry import check
from zz_core.util import (
    ast_imports, iter_functions, normalized_hash, parse_python, read_text,
    sha1_file, walk_files,
)

CORE_DIRS = ("domains", "modules", "rbac", "kernel", "infrastructure",
             "providers", "jobs", "middleware")


def _f(dimension: str, phase: str, file: str, line: int, current: str,
       target: str, fix: str, *, priority: str = "P2", effort: str = "M",
       laws: tuple = (), blocker: str = "no", confidence: int = 4,
       evidence_strength: str = "multiple", claim: str = "VERIFIED",
       verify: str = "", test: str = "", sibling: str = "", cluster: str = "",
       truth: str = "L0", snippet: str = "", blast: str = "") -> Finding:
    return Finding(
        id="", dimension=dimension, phase=phase, cluster=cluster, file=file,
        line=line, current=current, target=target, delta=current[:180], fix=fix,
        effort=effort, priority=priority, confidence=confidence,
        evidence_strength=evidence_strength, truth_level=truth, claim_state=claim,
        sibling=sibling, verify=verify, test=test, completion_blocker=blocker,
        laws=laws, snippet=snippet, blast_radius=blast,
    )


def _backend_core_files(ctx: ScanContext) -> list[Path]:
    out = []
    for p in ctx.py_files:
        try:
            rel = p.relative_to(ctx.backend).parts
        except ValueError:
            continue
        if rel and rel[0] in CORE_DIRS:
            out.append(p)
    return out


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #

@check("arch_extra_units", "01_architectural", "arch",
       "Flag any module outside the fixed 5 and any domain outside the fixed 15; "
       "flag approved-extra vs forbidden schemas dirs.")
def arch_extra_units(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="arch_extra_units", dimension="01_architectural")
    mod_root = ctx.backend / "modules"
    if mod_root.exists():
        for d in sorted(mod_root.iterdir()):
            if d.is_dir() and d.name not in CANONICAL_MODULES and d.name != "__pycache__":
                res.findings.append(_f(
                    "01_architectural", "arch", ctx.rel(d),
                    1, f"top-level module `{d.name}` exists", 
                    "fixed 5 modules: admin, customer, employee, logistics, supplier (Law 13)",
                    f"Move {d.name} routers under a canonical module or delete the package",
                    priority="P1", blocker="yes", laws=(13,),
                    verify=f"ls backend/modules",
                    cluster="CLUSTER-extra-module",
                ))
    dom_root = ctx.backend / "domains"
    if dom_root.exists():
        for d in sorted(dom_root.iterdir()):
            if d.is_dir() and d.name not in CANONICAL_DOMAINS and d.name != "__pycache__":
                res.findings.append(_f(
                    "01_architectural", "arch", ctx.rel(d),
                    1, f"domain package `{d.name}` exists",
                    "fixed 15 domains (Law 12); media/treasury/ai/configuration are schemas only",
                    f"Demote {d.name} to canonical domain or document an ARCH change",
                    priority="P1", blocker="partial", laws=(12,),
                    verify="ls backend/domains",
                    cluster="CLUSTER-extra-domain",
                ))
    return res


@check("arch_root_discipline", "17_code_file_management", "arch",
       "Audit backend/ root for forbidden folders, temp/debug scripts, duplicate "
       "test runners and non-canonical entries (Laws 18, 27).")
def arch_root_discipline(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="arch_root_discipline", dimension="17_code_file_management")
    root = ctx.backend
    temp_patterns = (
        r"^_tmp_.*\.py$", r"^health_test_.*\.py$", r"^fix_.*\.py$",
        r"^debug_.*\.py$", r"^_audit_boot_check\.py$", r"^test_output\d*\.txt$",
        r"^alembic_chain\.(py|txt)$",
    )
    hits: list[str] = []
    for p in sorted(root.glob("*")):
        if p.is_dir():
            if p.name in FORBIDDEN_ROOT_DIRS:
                res.findings.append(_f(
                    "17_code_file_management", "arch", ctx.rel(p), 1,
                    f"forbidden root-level directory `{p.name}/`",
                    "root-level utils/routers/controllers/services/models/db are FORBIDDEN (Law 18)",
                    f"Relocate {p.name}/ into the layer that owns it",
                    priority="P1", laws=(18,), cluster="CLUSTER-root-discipline",
                ))
            continue
        name = p.name
        if name in CANONICAL_BACKEND_ROOT_ENTRIES:
            continue
        if any(re.match(pat, name) for pat in temp_patterns):
            hits.append(name)
        elif not name.endswith((".md", ".txt", ".ini", ".cfg", ".toml", ".lock", ".yaml", ".yml", ".json", ".env")) \
                and name not in (".env.example", ".gitignore"):
            res.observations.append(Observation(
                "file", name, ctx.rel(p), 0, "17_code_file_management",
                evidence="non-canonical backend root entry", note="inspect manually"))
    if hits:
        sample = ", ".join(sorted(hits)[:12])
        res.findings.append(_f(
            "17_code_file_management", "arch", "backend/", 0,
            f"{len(hits)} temp/debug/health-test file(s) at backend root: {sample}"
            + (" ..." if len(hits) > 12 else ""),
            "Root contains only canonical entries; temp scripts deleted after use (Law 27)",
            "Delete the temp/debug scripts (they also embed secrets), keep one test runner",
            priority="P1", effort="S", laws=(27,), blocker="partial",
            cluster="CLUSTER-root-discipline",
            verify="ls backend/_tmp_*.py backend/health_test_*.py",
        ))
    for runner in ("run_tests.ps1", "run_tests.sh"):
        if (root / runner).exists():
            res.findings.append(_f(
                "17_code_file_management", "arch", f"backend/{runner}", 1,
                f"competing test runner `{runner}` present",
                "single canonical test entry point",
                f"Delete {runner}; use the canonical runner",
                priority="P2", effort="S", laws=(27,),
            ))
    return res


def _build_import_graph(ctx: ScanContext):
    def build():
        graph: dict[str, list[tuple[str, int, list[str]]]] = {}
        for p in _backend_core_files(ctx):
            parsed = parse_python(p)
            if parsed.error:
                graph[ctx.rel(p)] = []
                continue
            imports = []
            for module, names, lineno, kind in ast_imports(parsed.tree):
                imports.append((module, lineno, names))
            graph[ctx.rel(p)] = imports
        return graph
    return ctx.memo("import_graph", build)


#: Symbols that are framework plumbing rather than business logic. A module
#: router receiving a session or the current user is not a reverse-arrow
#: violation of Law 1; a module importing a service, repository, ORM model or
#: business schema is.
FRAMEWORK_SYMBOLS: frozenset[str] = frozenset({
    "get_db", "get_session", "get_async_db", "async_get_db", "Depends",
    "Session", "AsyncSession", "sessionmaker", "Base", "DeclarativeBase",
    "get_current_user", "get_current_admin", "get_current_employee",
    "require_admin", "require_role", "require_feature", "require_permission",
    "require_employee", "require_auth", "oauth2_scheme", "HTTPBearer",
    "HTTPAuthorizationCredentials", "OAuth2PasswordBearer", "HTTPException",
    "status", "Header", "Cookie", "Query", "Path", "Body", "Form", "File",
    "UploadFile", "APIRouter", "Request", "Response", "BackgroundTasks",
    "WebSocket", "DependsException", "BaseSchema", "CamelCaseModel",
    "PaginationMeta", "PaginatedResponse", "ORMSchema", "ConfigDict",
    "datetime", "uuid4", "utcnow", "timezone", "Enum", "field_validator",
    "model_validator", "computed_field", "SecretStr",
})


def _all_framework(names) -> bool:
    """True only when EVERY imported symbol is framework plumbing.

    If even one symbol is a service, repository, ORM model or business schema,
    the import is a real reverse-arrow violation and must be reported. An empty
    name list is never treated as framework wiring.
    """
    real = [n for n in (names or ()) if n and n != "*"]
    if not real:
        return False
    return all(n in FRAMEWORK_SYMBOLS for n in real)


#: A Pydantic DTO is transport, not business logic. Law 1's reverse-arrow rule
#: is about *business* dependencies (services, repositories, ORM models).
DTO_SUFFIXES = (
    "Request", "Response", "Body", "Schema", "Create", "Update", "Patch",
    "Payload", "Filters", "Filter", "Query", "Meta", "Params", "Payload",
    "In", "Out", "DTO", "Item", "Page", "PageParams", "ListResponse",
)
RATE_LIMIT_SYMBOLS = {"limiter", "RL_SENSITIVE", "RL_STANDARD", "rate_limiter",
                      "rate_limit", "slowapi_limiter", "get_limiter"}

#: Infrastructure subpackages a `modules/**/routers/` file may import. Law 1 bans
#: skipping the domain layer; it does not ban the framework wiring a router needs
#: in order to do its job. Matched as a prefix against `infrastructure.<...>`.
#:
#:   security.*              RBAC gates — Laws 87/88 require a router to inject one
#:   utils.country_rls       country scoping guard used at the request boundary
#:   utils.auth              token decode
#:   utils.config            settings
#:   utils.currency_service  per-request currency context
#:   utils.pagination        response shaping, i.e. transport
#:   utils.invoice_html      document rendering
#:   utils.background_jobs   job status lookup
#:   database.rls_interceptor  SET LOCAL RLS context (Law 227)
#:   database.schemas        Pydantic DTOs
#:
#: Anything else from `infrastructure` in a router -- `messaging.ws_manager`,
#: `storage.*`, `database.session`, `providers.*` -- is a genuine bypass and is
#: still reported.
#:
#: The list itself now lives in `zz_core.constants.ROUTER_OK_INFRA` so the probe
#: adjudicates these findings with the same allowlist the detector used.


def _is_framework_symbol(symbol: str) -> bool:
    """True when an imported symbol is transport or framework plumbing."""
    if not symbol or symbol == "*":
        return True
    if symbol in FRAMEWORK_SYMBOLS or symbol in RATE_LIMIT_SYMBOLS:
        return True
    return symbol.endswith(DTO_SUFFIXES)


#: A session call is DB access. A `db: Session = Depends(get_db)` declaration is
#: the CORRECT FastAPI pattern, not a Law 2 violation — Law 2 forbids *querying*
#: in the router, not receiving a session. Counting the declaration made every
#: well-formed router a finding (6/6 adjudicated samples were false positives).
DB_CALL_RE = re.compile(
    r"\b(?:db|session|self\.db)\s*\.\s*"
    r"(?:query|execute|commit|rollback|flush|add|delete|refresh|merge)\s*\(")


def _layer_of(rel: str) -> str:
    parts = rel.split("/")
    if len(parts) >= 2 and parts[0] == "backend":
        p = parts[1]
        if p in ("domains", "modules") and len(parts) >= 3:
            return f"{p}.{parts[2]}"
        return p
    return rel


@check("arch_import_direction", "01_architectural", "arch",
       "Build the AST import graph and flag every reverse-layer import and "
       "cross-domain direct import (Laws 1, 3, 97-106). Also detect cycles.")
def arch_import_direction(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="arch_import_direction", dimension="01_architectural")
    graph = _build_import_graph(ctx)
    violations: dict[str, list[tuple[str, int, str]]] = {}
    cross_domain: list[tuple[str, int, str]] = []

    def flag(kind: str, rel: str, line: int, target: str):
        violations.setdefault(kind, []).append((rel, line, target))

    allowed_cross = ("ports", "events", "subscribers", "schemas", "read_models")
    for rel, imports in graph.items():
        layer = _layer_of(rel)
        for module, line, names in imports:
            top = module.split(".")[0] if module else ""
            if not module or top in ("__future__",):
                continue
            if layer.startswith("domains."):
                src_domain = layer.split(".", 1)[1]
                if top == "modules":
                    flag("domain-imports-module", rel, line, module)
                elif top == "domains" and len(module.split(".")) >= 2:
                    dst_domain = module.split(".")[1]
                    if dst_domain != src_domain:
                        sub = module.split(".")[2] if len(module.split(".")) > 2 else ""
                        if sub not in allowed_cross:
                            cross_domain.append((rel, line, module))
            elif layer == "infrastructure":
                if top in ("domains", "modules", "rbac", "providers", "jobs", "middleware"):
                    flag("infra-imports-above", rel, line, module)
            elif layer == "kernel":
                if top in ("domains", "modules", "rbac", "providers", "jobs", "middleware"):
                    flag("kernel-imports-above", rel, line, module)
            elif layer == "providers":
                if top in ("domains", "modules", "rbac", "jobs", "middleware"):
                    flag("provider-imports-above", rel, line, module)
            elif layer == "middleware":
                if top in ("domains", "modules", "providers", "jobs"):
                    flag("middleware-imports-above", rel, line, module)
            elif layer == "jobs":
                if top in ("modules", "middleware"):
                    flag("job-imports-forbidden", rel, line, module)
            elif layer == "rbac":
                if top in ("modules", "providers", "jobs", "middleware"):
                    flag("rbac-imports-forbidden", rel, line, module)
            elif layer.startswith("modules."):
                if top == "domains" or top == "rbac":
                    continue  # allowed
                if top == "infrastructure":
                    # Law 1 separates *business* layers. A router may import
                    # framework plumbing from infrastructure; what it must not do
                    # is reach past its domain service into infrastructure
                    # internals.
                    #
                    # This used to filter on the imported SYMBOL name, which is the
                    # wrong axis, and produced 69 findings of which 67 were false:
                    #   27  security.dependencies   require_supplier/require_logistics/
                    #                              require_super_admin/verify_captcha
                    #                              -- the RBAC gates Laws 87/88 REQUIRE
                    #                              a router to use
                    #   15  utils.country_rls       get_country_or_404/enforce_country_access
                    #   12  database.rls_interceptor set_/clear_rls_context -- the SET LOCAL
                    #                              pattern Law 227 mandates
                    #    4  database.schemas       CreateStaffAccount/UpdateStaffAccount
                    #                              -- Pydantic DTOs, i.e. transport
                    #    2  utils.config           settings
                    #    2  utils.invoice_html     document rendering
                    #    4  utils.{auth,currency_service,pagination,background_jobs}
                    # The class of import is a property of the SUBPACKAGE, not of
                    # the symbol, so the test belongs here.
                    subpkg = ".".join(module.split(".")[1:3])
                    if subpkg.startswith(ROUTER_OK_INFRA) or module.startswith(
                            ROUTER_OK_INFRA):
                        continue
                    symbol = names if isinstance(names, str) else str(names or "")
                    if _is_framework_symbol(symbol):
                        continue
                    flag("module-imports-infrastructure", rel, line,
                         f"{module}.{symbol}")

    for kind, items in violations.items():
        for rel, line, module in items[:200]:
            res.findings.append(_f(
                "01_architectural", "arch", rel, line,
                f"`{kind.replace('-', ' ')}`: imports `{module}`",
                "Arrows point down only (Law 1/97-106)",
                "Route through the sanctioned layer (events/ports/service call)",
                priority="P1", laws=(1, 97, 98, 99, 100, 101, 102, 103, 104),
                cluster=f"CLUSTER-{kind}",
                verify=f"grep -n '{module}' {rel}",
            ))
    if cross_domain:
        by_pair: dict[tuple[str, str], list[tuple[str, int, str]]] = {}
        for rel, line, module in cross_domain:
            src = _layer_of(rel)
            dst = ".".join(module.split(".")[:2])
            by_pair.setdefault((src, dst), []).append((rel, line, module))
        for (src, dst), items in sorted(by_pair.items())[:200]:
            rel, line, module = items[0]
            res.findings.append(_f(
                "01_architectural", "arch", rel, line,
                f"cross-domain import `{module}` ({src} -> {dst}); "
                f"{len(items)} occurrence(s) in this file",
                "cross-domain reads via ports.py, writes via events.py (Law 3)",
                "Move the call behind the owning domain's ports/ or emit an event",
                priority="P1", laws=(3, 17), cluster="CLUSTER-cross-domain-direct",
                verify=f"grep -rn 'from {dst}' {ctx.rel(ctx.backend)}/domains/{src.split('.')[1] if '.' in src else src}",
            ))
        res.facts["cross_domain_imports"] = sum(len(v) for v in by_pair.values())

    # cycles at package granularity
    #
    # The reported chain must be the traversal PATH, not the alphabetically
    # sorted member set. `tuple(sorted(set(...)))` produced
    #   domains.accounts -> domains.audit -> domains.catalog -> domains.comms
    # for a cycle whose actual edges were something else entirely, so 15 of 16
    # reported chains named imports that do not exist. The chain is the claim, so
    # it has to be the thing that was observed.
    edges: dict[str, set[str]] = {}
    edge_site: dict[tuple[str, str], str] = {}
    for rel, imports in graph.items():
        src = _layer_of(rel)
        for module, line, names in imports:
            top = module.split(".")[0]
            if top in CORE_DIRS:
                dst = _layer_of(f"backend/{module.replace('.', '/')}")
                if dst != src:
                    edges.setdefault(src, set()).add(dst)
                    edge_site.setdefault((src, dst), f"{rel}:{line}")

    def _canonical(path: list[str]) -> tuple[str, ...]:
        """Rotation-independent identity, so A->B->A and B->A->B are one cycle."""
        ring = path[:-1]
        if not ring:
            return ()
        k = min(range(len(ring)), key=lambda i: ring[i:])
        return tuple(ring[k:] + ring[:k]) + (ring[k],)

    seen_cycles: dict[tuple[str, ...], list[str]] = {}
    path: list[str] = []
    on_path: set[str] = set()
    done: set[str] = set()

    def dfs(node: str) -> None:
        path.append(node)
        on_path.add(node)
        for nxt in sorted(edges.get(node, ())):
            if nxt in on_path:
                cyc = path[path.index(nxt):] + [nxt]
                key = _canonical(cyc)
                # keep the first (shortest, lexicographically stable) rotation
                if key and len(key) > 2 and key not in seen_cycles:
                    seen_cycles[key] = cyc
            elif nxt not in done:
                dfs(nxt)
        path.pop()
        on_path.discard(node)
        done.add(node)

    for n in sorted(edges):
        if n not in done:
            dfs(n)

    for cyc in list(seen_cycles.values())[:20]:
        chain = " -> ".join(cyc)
        evidence = "; ".join(
            f"{a} -> {b} via {edge_site.get((a, b), '?')}"
            for a, b in zip(cyc, cyc[1:]))
        res.findings.append(_f(
            "01_architectural", "arch", cyc[0], 0,
            f"circular package dependency: {chain}",
            "no circular imports between packages (Law 98)",
            "Break the cycle with a port/event boundary",
            priority="P1", laws=(98,), cluster="CLUSTER-circular-import",
            truth="L1", evidence_strength="multiple",
            snippet=evidence,
            verify=f"grep -rn 'from {cyc[1]}' backend/{cyc[0].split('.', 1)[-1]}",
        ))
    res.facts["package_cycles"] = len(seen_cycles)
    return res


@check("arch_router_thinness", "01_architectural", "arch",
       "Read every module router: DB access, business branches, service-call "
       "count; routers not registered in routers/__init__.py (Laws 2, 8, 134-136).")
def arch_router_thinness(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="arch_router_thinness", dimension="01_architectural")
    router_files = [p for p in ctx.py_files
                    if "/modules/" in ctx.rel(p) and "/routers/" in ctx.rel(p)]
    registered: dict[str, set[str]] = {}
    for init in ctx.backend.glob("modules/*/routers/__init__.py"):
        text, _ = read_text(init)
        names = set(re.findall(r"from\s+\.(\w+)\s+import", text))
        registered[ctx.rel(init).split("/")[-2]] = names
    for p in router_files:
        rel = ctx.rel(p)
        if p.name == "__init__.py":
            continue
        parsed = parse_python(p)
        if parsed.error:
            continue
        text = parsed.text
        # A router declaring `db: Session = Depends(get_db)` is the CORRECT
        # FastAPI pattern, not a Law 2 violation — Law 2 forbids *querying* in
        # the router, not receiving a session. Counting the declaration made
        # every well-formed router a finding (6/6 adjudicated samples were
        # false positives on this basis). Only a real session call counts.
        db_access = len(DB_CALL_RE.findall(text))
        endpoints = len(re.findall(r"@router\.(get|post|put|patch|delete)", text))
        service_calls = len(re.findall(r"services[\.\w]*\(", text))
        branches = len(re.findall(r"^\s+(if|for|while|try)\b", text, re.MULTILINE))
        mod = rel.split("/")[1]
        stem = p.stem
        reg = registered.get(mod, set())
        if reg and stem not in reg and endpoints:
            res.findings.append(_f(
                "01_architectural", "arch", rel, 1,
                f"router file with {endpoints} endpoint(s) not listed in routers/__init__.py",
                "every router listed in the module's routers/__init__.py (Law 135)",
                "Register the router or delete the dead file",
                priority="P1", laws=(135,), cluster="CLUSTER-unregistered-router",
                verify=f"grep -rn '{stem}' {ctx.rel(p.parent)}/__init__.py",
            ))
        if endpoints == 0 and len(text.splitlines()) > 30:
            res.findings.append(_f(
                "01_architectural", "arch", rel, 1,
                "file lives in routers/ but declares zero endpoint decorators",
                "routers declare HTTP endpoints (anti-inference: verify content)",
                "Delete or convert to a service module",
                priority="P2", laws=(8, 134), claim="VERIFIED",
                cluster="CLUSTER-router-empty",
            ))
        if db_access:
            res.findings.append(_f(
                "01_architectural", "arch", rel, 1,
                f"router touches DB/ORM directly ({db_access} hit(s))",
                "router = auth + require_feature + ONE service call (Law 2)",
                "Move DB access into the domain service",
                priority="P1", laws=(2, 90), cluster="CLUSTER-router-db-access",
                verify=f"grep -nE 'get_db|Session|session\\.' {rel}",
            ))
        if branches > 6 and endpoints:
            res.findings.append(_f(
                "01_architectural", "arch", rel, 1,
                f"router contains {branches} branch statements (business logic signal)",
                "routers contain only auth/gate/parse/one service call (Law 90)",
                "Extract branching logic into the domain service",
                priority="P2", laws=(90,), cluster="CLUSTER-router-business-logic",
            ))
        res.observations.append(Observation(
            "file", stem, rel, 1, "01_architectural",
            evidence=f"endpoints={endpoints} db={db_access} branches={branches} "
                     f"service_calls={service_calls}",
        ))
    return res


@check("arch_domain_structure", "01_architectural", "arch",
       "Verify each domain has services/models/schemas/policies/events.py/"
       "subscribers.py/ports.py/features.py; each module has auth/routers/serializers.")
def arch_domain_structure(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="arch_domain_structure", dimension="01_architectural")
    required = ["services", "models", "schemas", "policies", "events.py",
                "subscribers.py", "ports.py", "features.py"]
    for name in CANONICAL_DOMAINS:
        dom = ctx.backend / "domains" / name
        if not dom.exists():
            res.findings.append(_f(
                "01_architectural", "arch", f"backend/domains/{name}", 0,
                f"canonical domain `{name}` is missing entirely",
                "all 15 canonical domains exist (Law 12/160)",
                f"Restore or document the removal of domains/{name}",
                priority="P1", laws=(12, 160), blocker="partial",
            ))
            continue
        missing = [r for r in required if not (dom / r).exists()]
        if missing:
            res.findings.append(_f(
                "01_architectural", "arch", f"backend/domains/{name}", 0,
                f"missing domain artefacts: {', '.join(missing)}",
                "standard domain structure (Law 150)",
                f"Create {', '.join(missing)} or document the intentional deviation",
                priority="P2", laws=(150,), truth="L1",
            ))
    for name in CANONICAL_MODULES:
        mod = ctx.backend / "modules" / name
        if not mod.exists():
            res.findings.append(_f(
                "01_architectural", "arch", f"backend/modules/{name}", 0,
                f"canonical module `{name}` is missing",
                "all 5 canonical modules exist (Law 13)",
                f"Restore modules/{name}",
                priority="P1", laws=(13,), blocker="partial",
            ))
            continue
        for sub in ("auth", "routers", "serializers"):
            if not (mod / sub).exists():
                res.findings.append(_f(
                    "01_architectural", "arch", f"backend/modules/{name}/{sub}", 0,
                    f"module `{name}` lacks `{sub}/`",
                    "module layout: auth/, routers/, serializers/ (Law 132)",
                    f"Create modules/{name}/{sub}/",
                    priority="P2", laws=(132,), truth="L1",
                ))
    return res


@check("arch_dead_code", "17_code_file_management", "arch",
       "Detect duplicate files, duplicate function bodies, oversized files "
       "(split candidates) and clearly unreferenced modules.")
def arch_dead_code(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="arch_dead_code", dimension="17_code_file_management")
    files = _backend_core_files(ctx)
    # duplicate whole files
    hashes: dict[str, list[str]] = {}
    for p in files:
        if p.stat().st_size < 400:
            continue
        h = sha1_file(p)
        if h:
            hashes.setdefault(h, []).append(ctx.rel(p))
    for h, group in hashes.items():
        if len(group) > 1:
            res.findings.append(_f(
                "17_code_file_management", "arch", group[0], 0,
                f"byte-identical duplicate file(s): {', '.join(group[:4])}",
                "single source per implementation (Law 67 DRY)",
                "Delete the duplicates and keep one owner",
                priority="P2", laws=(67,), cluster="CLUSTER-duplicate-file",
            ))
    # duplicate function bodies
    body_hashes: dict[str, tuple[str, str, int]] = {}
    dups: list[tuple[str, str, int, str]] = []
    for p in files:
        parsed = parse_python(p)
        if parsed.error:
            continue
        for qualname, node, start, end, depth in iter_functions(parsed.tree):
            if end - start < 12:
                continue
            h = normalized_hash(node)
            if not h:
                continue
            key = h
            if key in body_hashes:
                dups.append((ctx.rel(p), qualname, start, body_hashes[key][0]))
            else:
                body_hashes[key] = (ctx.rel(p), qualname, start)
    # One finding per duplication PAIR, not per function.
    #
    # 120 of the 142 cluster-less findings came from here: `dups` holds one entry
    # per duplicated function, so a pair of files sharing six helpers produced six
    # findings that could not be worked as a unit -- and none of them carried a
    # cluster, so no cluster-level triage could see them at all. The actionable
    # unit is the pair: "these two files share N functions" is one edit.
    by_pair: dict[tuple[str, str], list[tuple[str, int]]] = defaultdict(list)
    for rel, qualname, start, other in dups:
        by_pair[(rel, other)].append((qualname, start))
    for (rel, other), items in sorted(by_pair.items(), key=lambda kv: -len(kv[1]))[:120]:
        names = ", ".join(f"`{q}`" for q, _s in items[:5])
        more = f" (+{len(items) - 5} more)" if len(items) > 5 else ""
        res.findings.append(_f(
            "17_code_file_management", "arch", rel, items[0][1],
            f"{len(items)} function(s) in this file duplicate `{other}` "
            f"(normalized AST): {names}{more}",
            "duplicate logic >5 lines must be extracted (Law 67)",
            f"Extract the shared implementation(s) into one module and import them "
            f"from both `{rel}` and `{other}`",
            priority="P3", laws=(67,), truth="L2", evidence_strength="single",
            claim="INFERRED", cluster="CLUSTER-duplicate-symbol",
        ))
    # oversized files
    for p in files:
        try:
            n = sum(1 for _ in p.open("r", encoding="utf-8-sig", errors="replace"))
        except Exception:
            continue
        if n > 1500:
            res.findings.append(_f(
                "17_code_file_management", "arch", ctx.rel(p), 1,
                f"file has {n} lines (split candidate)",
                "files remain reviewable; large services split by capability (Law 64/65 spirit)",
                "Split into capability-scoped modules",
                priority="P3", effort="L", claim="VERIFIED", laws=(64, 65),
                truth="L1", cluster="CLUSTER-file-too-long",
            ))
    return res


@check("arch_allowlist", "01_architectural", "arch",
       "Audit DOMAIN_ALLOWLIST.yaml: entries, dated removal plans, shrink-only rule (Law 7).")
def arch_allowlist(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="arch_allowlist", dimension="01_architectural")
    path = ctx.backend / "DOMAIN_ALLOWLIST.yaml"
    if not path.exists():
        return res
    text, _ = read_text(path)
    entries = re.findall(r"^\s*-\s*(.+)$", text or "", re.MULTILINE)
    res.observations.append(Observation(
        "file", "DOMAIN_ALLOWLIST.yaml", ctx.rel(path), 1, "01_architectural",
        evidence=f"{len(entries)} entries",
    ))
    from datetime import date
    today = date.today()
    for entry in entries[:200]:
        m = re.search(r"(\d{4}-\d{2}-\d{2})", entry)
        if not m:
            res.findings.append(_f(
                "01_architectural", "arch", ctx.rel(path), 1,
                f"allowlist entry without dated removal plan: `{entry.strip()[:120]}`",
                "every allowlist entry carries a dated removal plan <=30 days (Law 7)",
                "Add the removal date or remove the entry",
                priority="P2", laws=(7,), cluster="CLUSTER-allowlist",
            ))
        else:
            try:
                due = date.fromisoformat(m.group(1))
                if due < today:
                    res.findings.append(_f(
                        "01_architectural", "arch", ctx.rel(path), 1,
                        f"allowlist entry expired on {m.group(1)}: `{entry.strip()[:120]}`",
                        "allowlist may only shrink; expired entries must be removed (Law 7)",
                        "Remove the import and the entry",
                        priority="P1", laws=(7,), cluster="CLUSTER-allowlist",
                    ))
            except ValueError:
                pass
    return res
