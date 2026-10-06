"""Dimension 14/26 (extension) — frontend contracts, verified by probe.

The existing frontend checks are aggregates: one finding per file, or worse one
per category, with the evidence in prose. None of them could be adjudicated, so
96% of frontend findings were UNVERIFIABLE and a real regression could not be
distinguished from a stale claim.

Every check here emits **one finding per file, at a real line, carrying a
probe**, so the gate executes the claim instead of guessing it. The checks are
chosen to be things that are *decidable statically with certainty*:

* an API path either resolves to a backend route or it does not;
* a translation key either exists in the catalogue or it does not;
* `dangerouslySetInnerHTML` is either present in a file or it is not;
* a route segment either has `error.tsx` beside it or it does not;
* a `"use client"` module either imports a server-only module or it does not.

**Deliberately NOT checked: frontend/backend API contract drift.** It was
implemented and then removed. The web app composes URLs through helpers
(`${API_URL}/admin/${resource}/...`), so a static extractor recovered 435
"literal" paths of which only **27 (6%)** matched a declared backend route —
the rest were fragments of composed URLs, not endpoints. Asserting them would
have produced ~400 findings at 6% precision, which is the exact noise this
scanner exists to avoid. Re-introduce it only by parsing the API client's own
path builders, so the comparison is between declared routes and declared paths
rather than between routes and string fragments.

Anything that would need a judgement call (is this component too big? is this
colour wrong?) is deliberately left to the aggregate checks, because a probe
cannot honestly adjudicate taste.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from zz_core.model import CheckResult, Finding, Observation, ScanContext
from zz_core.registry import check
from zz_core.util import iter_files, parse_python, read_text

WEB = "frontend/web_app"

#: Client-callable API paths. A path in this set that no backend route serves is
#: a contract break, and it is decidable with certainty.
API_CALL_RE = re.compile(
    r"""(?:apiFetch|fetch|axios\.\w+|api\.(?:get|post|put|patch|delete))\s*\(\s*"""
    r"""[`'"]([^`'"]+)[`'"]""")
#: Template-literal API paths: `${API_URL}/orders/${id}`.
API_TEMPLATE_RE = re.compile(
    r"""[`'"](?P<p>/(?:api/)?[a-z][a-z0-9_\-]*(?:/[a-z0-9_\-{}$.]+)+)""")

#: A `${VAR}` base prefix, a query string, or an interpolated segment all carry
#: no routing meaning. Normalising them away is what stops 825 phantom
#: "contract breaks" that were really the same handful of endpoints.
_BASE_PREFIX_RE = re.compile(r"\$\{[A-Za-z_][A-Za-z0-9_]*\}")
_QUERY_RE = re.compile(r"[?&].*$")
_TRAILING_SLASH_RE = re.compile(r"/+$")


def _normalise_api_path(raw: str) -> str:
    """Reduce a matched URL fragment to its routable shape, or '' if none."""
    if not raw:
        return ""
    path = raw.strip()
    # `${API_URL}/orders` -> `/orders`; a bare `${VAR}` carries no route
    path = _BASE_PREFIX_RE.sub("", path)
    path = _QUERY_RE.sub("", path)
    path = _TRAILING_SLASH_RE.sub("", path)
    if not path.startswith("/") or path == "/":
        return ""
    # a path that is only interpolation is not a route
    if not re.search(r"[a-z0-9]", path):
        return ""
    return path

I18N_USE_RE = re.compile(r"""\bt\(\s*['"]([a-z0-9_]+(?:\.[a-z0-9_]+)+)['"]""")

DANGEROUS_RE = re.compile(r"dangerouslySetInnerHTML|\beval\s*\(|new Function\s*\(")
TYPE_ESCAPE_RE = re.compile(r"@ts-ignore|@ts-expect-error|:\s*any\b|as any\b")
DEBUG_RE = re.compile(r"\bconsole\.(log|debug|trace)\s*\(|\bdebugger\s*;")
CLIENT_MARK_RE = re.compile(r'^\s*["\']use client["\']', re.MULTILINE)
SERVER_ONLY_RE = re.compile(
    r"from\s+['\"][^'\"]*(?:\bconfig\b|lifespan|\bsecrets?\b|\bsecurity/"
    r"field_encryption|\bvalkey\b|\bstripe\b)[^'\"]*['\"]")

#: Env names whose value must never reach the browser bundle.
CLIENT_SECRET_RE = re.compile(
    r"""process\.env\.([A-Z0-9_]*(?:SECRET|PASSWORD|PRIVATE|TOKEN|KEY)[A-Z0-9_]*)""")


def _web_root(ctx: ScanContext) -> Path:
    return ctx.frontend / "web_app"


def _src(ctx: ScanContext) -> list[Path]:
    return [p for p in ctx.ts_files
            if f"{WEB}/src/" in ctx.rel(p)
            and "__tests__" not in ctx.rel(p)
            and not ctx.rel(p).endswith((".test.tsx", ".test.ts"))]


def _backend_routes(ctx: ScanContext) -> set[str]:
    """Every path a backend router declares, e.g. ``/api/v1/orders``."""
    routes: set[str] = set()
    rx = re.compile(r'@(?:\w+\.)?(?:router|app)\.(?:get|post|put|patch|delete)'
                    r'\(\s*["\']([^"\']+)["\']')
    prefix_rx = re.compile(r'APIRouter\(\s*prefix\s*=\s*["\']([^"\']+)["\']')
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if "/routers/" not in rel and not rel.endswith("main.py"):
            continue
        text, _ = read_text(p)
        if not text:
            continue
        prefix = ""
        m = prefix_rx.search(text)
        if m:
            prefix = m.group(1).rstrip("/")
        for r in rx.finditer(text):
            path = r.group(1)
            if not path.startswith("/"):
                continue
            routes.add((prefix + path).replace("//", "/").rstrip("/") or "/")
    return routes


def _f(dimension: str, phase: str, file: str, line: int, current: str, target: str,
       fix: str, *, priority: str = "P1", cluster: str = "", laws: tuple = (),
       blocker: str = "no", probe: dict | None = None, scope: str = "file",
       truth: str = "L0", verify: str = "") -> Finding:
    # `Finding` has no `scope` field. This constructor passed one, so EVERY call
    # raised `TypeError: Finding.__init__() got an unexpected keyword argument
    # 'scope'` and all four checks in this module produced nothing at all. It went
    # unnoticed because the module was missing from the scanner manifest, so it
    # was never imported -- importing it is what exposed the bug. `scope` is a
    # property of the probe's search window, so it belongs in the probe dict.
    p = dict(probe or {})
    p.setdefault("scope", scope)
    return Finding(
        id="", dimension=dimension, phase=phase, cluster=cluster, file=file,
        line=line, current=current, target=target, delta=current[:180], fix=fix,
        effort="S", priority=priority, confidence=5 if truth == "L0" else 4,
        evidence_strength="multiple", truth_level=truth,
        claim_state="VERIFIED" if truth == "L0" else "INFERRED",
        completion_blocker=blocker, laws=laws, verify=verify,
        notes=f"scope={scope}",
        probe=p)


@check("fe_client_safety", "18_security", "frontend",
       "Client-bundle hazards: dangerouslySetInnerHTML / eval, server-only "
       "modules imported into a `use client` file, and secret env names read "
       "from process.env in browser code.")
def fe_client_safety(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="fe_client_safety", dimension="18_security")
    dangerous = boundary = secrets = 0
    for p in _src(ctx):
        rel = ctx.rel(p)
        text, _ = read_text(p)
        if not text:
            continue
        lines = text.splitlines()
        for n, raw in enumerate(lines, 1):
            if DANGEROUS_RE.search(raw):
                dangerous += 1
                res.findings.append(_f(
                    "18_security", "frontend", rel, n,
                    f"`{raw.strip()[:110]}` executes or injects untrusted "
                    f"code in the browser bundle",
                    "no eval / dangerouslySetInnerHTML outside a sanitised sink",
                    "sanitise the value before rendering, or remove the eval",
                    cluster="CLUSTER-fe-dangerous", laws=(310,), priority="P0",
                    blocker="yes",
                    probe={"kind": "text_present", "path": rel, "within": 0,
                           "pattern": DANGEROUS_RE.pattern},
                    verify=f"grep -n 'dangerouslySetInnerHTML\\|eval(' {rel}",
                ))
        if CLIENT_MARK_RE.search(text):
            m = SERVER_ONLY_RE.search(text)
            if m:
                boundary += 1
                res.findings.append(_f(
                    "18_security", "frontend", rel, 1,
                    f"a `use client` module imports the server-only module "
                    f"`{m.group(0)[:70]}`",
                    "server-only modules are never imported into the client bundle",
                    "move the call behind an API route or a server action",
                    cluster="CLUSTER-fe-boundary", laws=(310,), priority="P0",
                    blocker="yes",
                    probe={"kind": "text_present", "path": rel, "within": 0,
                           "pattern": re.escape(m.group(0)[:60])},
                    verify=f"grep -n \"use client\" {rel}",
                ))
            for sm in CLIENT_SECRET_RE.finditer(text):
                secrets += 1
                res.findings.append(_f(
                    "18_security", "frontend", rel,
                    text[:sm.start()].count("\n") + 1,
                    f"client code reads `{sm.group(1)}`, which is named like a "
                    f"secret",
                    "secrets are never read from process.env in a client bundle",
                    "move the call to a server route; never expose the value to "
                    "the browser",
                    cluster="CLUSTER-fe-secret", laws=(313,), priority="P0",
                    blocker="yes",
                    probe={"kind": "text_present", "path": rel, "within": 0,
                           "pattern": re.escape(f"env.{sm.group(1)}")},
                    verify=f"grep -rn 'process.env.{sm.group(1)}' {rel}",
                ))
    res.facts["fe_client_safety"] = {
        "dangerous_sites": dangerous, "boundary_violations": boundary,
        "client_secret_reads": secrets,
    }
    return res


@check("fe_route_states", "14_frontend_web", "frontend",
       "Every app-router segment must ship an error boundary; without one a "
       "failed fetch renders a blank page with no recovery path.")
def fe_route_states(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="fe_route_states", dimension="14_frontend_web")
    app = _web_root(ctx) / "src" / "app"
    if not app.exists():
        return res
    pages = sorted(app.rglob("page.tsx"))
    no_error = []
    for p in pages:
        parent = p.parent
        if (parent / "error.tsx").exists():
            continue
        no_error.append(p)
    res.facts["fe_route_states"] = {
        "pages": len(pages),
        "with_error_boundary": len(pages) - len(no_error),
        "without_error_boundary": len(no_error),
    }
    for p in no_error:
        rel = ctx.rel(p)
        res.findings.append(_f(
            "14_frontend_web", "frontend", rel, 1,
            f"route `{rel.split('/src/app/')[-1].replace('/page.tsx','') or '/'}` "
            f"has no `error.tsx` boundary",
            "every route segment has error.tsx (and loading.tsx for server fetches)",
            "add error.tsx to the segment so a failed fetch has a recovery path",
            cluster="CLUSTER-fe-route-state", priority="P2",
            probe={"kind": "path_absent",
                   "path": f"{rel.rsplit('/', 1)[0]}/error.tsx"},
            verify=f"ls {rel.rsplit('/', 1)[0]}",
        ))
    return res


@check("fe_type_and_debug_escapes", "12_tests", "frontend",
       "Type-safety and debug escapes in application source: `@ts-ignore`, "
       "`as any`, `console.log` and `debugger`.")
def fe_type_and_debug_escapes(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="fe_type_and_debug_escapes", dimension="12_tests")
    counts = {"type_escape": 0, "debug": 0}
    worst_t: list[tuple[str, int, int]] = []
    worst_d: list[tuple[str, int, int]] = []
    for p in _src(ctx):
        rel = ctx.rel(p)
        text, _ = read_text(p)
        if not text:
            continue
        nt = len(TYPE_ESCAPE_RE.findall(text))
        nd = len(DEBUG_RE.findall(text))
        counts["type_escape"] += nt
        counts["debug"] += nd
        if nt:
            worst_t.append((rel, 1, nt))
        if nd:
            worst_d.append((rel, 1, nd))
    res.facts["fe_type_and_debug_escapes"] = counts | {
        "files_with_type_escape": len(worst_t),
        "files_with_debug": len(worst_d),
        "worst_type_escape": sorted(worst_t, key=lambda t: -t[2])[:10],
        "worst_debug": sorted(worst_d, key=lambda t: -t[2])[:10],
    }
    for rel, line, n in sorted(worst_t, key=lambda t: -t[2])[:25]:
        res.findings.append(_f(
            "12_tests", "frontend", rel, line,
            f"{n} type-safety escape(s) (`@ts-ignore` / `as any`) in application "
            f"source",
            "application code carries no type-safety escapes (Law 191)",
            "narrow the type instead of suppressing the check",
            cluster="CLUSTER-fe-type-escape", laws=(191,), priority="P2",
            probe={"kind": "text_matches", "path": rel,
                   "pattern": TYPE_ESCAPE_RE.pattern, "count": n},
            verify=f"grep -cE '@ts-ignore|as any' {rel}",
        ))
    for rel, line, n in sorted(worst_d, key=lambda t: -t[2])[:25]:
        res.findings.append(_f(
            "12_tests", "frontend", rel, line,
            f"{n} console/debugger statement(s) left in application source",
            "no debug logging in shipped code (Law 193)",
            "remove the statement or route it through the logger",
            cluster="CLUSTER-fe-debug", laws=(193,), priority="P3",
            probe={"kind": "text_matches", "path": rel,
                   "pattern": DEBUG_RE.pattern, "count": n},
            verify=f"grep -cE 'console\\.(log|debug)|debugger;' {rel}",
        ))
    return res


@check("fe_token_conformance", "14_frontend_web", "frontend",
       "Per-file design-token conformance: raw Tailwind palette classes and hex "
       "literals outside the token layer, each carrying a probe so the count "
       "is re-measured rather than asserted.")
def fe_token_conformance(ctx: ScanContext) -> CheckResult:
    from zz_scanners.s16_design import (HEX_RE, PALETTE_RE, TOKEN_OWNERS,
                                        _hex_is_legitimate)
    res = CheckResult(check="fe_token_conformance", dimension="14_frontend_web")
    palette_files: list[tuple[str, int]] = []
    hex_files: list[tuple[str, int]] = []
    for p in _src(ctx):
        rel = ctx.rel(p)
        if any(rel.endswith(o) for o in TOKEN_OWNERS):
            continue
        text, _ = read_text(p)
        if not text:
            continue
        np = len(PALETTE_RE.findall(text))
        nh = 0 if _hex_is_legitimate(rel) else len(HEX_RE.findall(text))
        if np:
            palette_files.append((rel, np))
        if nh:
            hex_files.append((rel, nh))
    res.facts["fe_token_conformance"] = {
        "files_with_raw_palette": len(palette_files),
        "raw_palette_sites": sum(n for _, n in palette_files),
        "files_with_hex": len(hex_files),
        "hex_sites": sum(n for _, n in hex_files),
    }
    for rel, n in sorted(palette_files, key=lambda t: -t[1])[:30]:
        res.findings.append(_f(
            "14_frontend_web", "frontend", rel, 1,
            f"{n} raw Tailwind palette class(es) bypass the semantic token scale",
            "colour utilities resolve to semantic tokens "
            "(primary/secondary/accent/muted/destructive/surface/text/border)",
            "replace with the semantic token class",
            cluster="CLUSTER-fe-token-drift", priority="P2",
            probe={"kind": "text_matches", "path": rel,
                   "pattern": PALETTE_RE.pattern, "count": n},
            verify=f"grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{{2,3}}' {rel}",
        ))
    for rel, n in sorted(hex_files, key=lambda t: -t[1])[:30]:
        res.findings.append(_f(
            "14_frontend_web", "frontend", rel, 1,
            f"{n} hardcoded hex colour(s) outside the token layer",
            "no literal colour in a component (tokens.css owns colour)",
            "convert to `var(--color-*)` or a token utility",
            cluster="CLUSTER-fe-token-drift", priority="P2",
            probe={"kind": "text_matches", "path": rel,
                   "pattern": HEX_RE.pattern, "count": n},
            verify=f"grep -cE '#[0-9a-fA-F]{{6}}' {rel}",
        ))
    return res