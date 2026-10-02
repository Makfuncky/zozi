"""Dimension 14/18 (extension) — HTTP layer.

The audit previously had no HTTP dimension at all. Everything else is static,
CLI-based, or in-process ASGI; none of it inspects a real response. That is why
a CORS preflight returning 405 — which breaks every cross-origin write in a
browser while looking perfectly healthy to curl and TestClient — went
unreported.

Two checks, deliberately:

* `http_response_contract` needs a live server (the integration probe). It is
  the only check in the suite that observes real bytes.
* `security_header_policy` is static, so header-policy defects are still
  reported when the stack is down or the probe is disabled.
"""
from __future__ import annotations

import re
from pathlib import Path

from zz_core.model import CheckResult, Finding, Observation, Recommendation, ScanContext
from zz_core.registry import check
from zz_core.util import read_text

# Directives a policy needs to be meaningful. `object-src 'none'` and
# `base-uri 'self'` are the two most commonly omitted.
REQUIRED_CSP_DIRECTIVES = ("default-src", "object-src", "base-uri")
DEPRECATED_CSP_DIRECTIVES = {
    "report-uri": "superseded by report-to / Reporting-Endpoints; ignored by "
                  "current Chrome and Firefox",
    "frame-ancestors": "still valid; use clickjacking via CSP where possible",
    "sandbox": "still valid",
}
HEADER_SOURCE_HINTS = ("middleware", "main.py")


def _header_sources(ctx: ScanContext) -> list[Path]:
    out: list[Path] = []
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if rel.startswith("backend/middleware/") or rel == "backend/main.py":
            out.append(p)
        elif "security_header" in rel or "cors" in rel.lower():
            out.append(p)
    return out


@check("http_response_contract", "14_frontend_web", "infra",
       "Boot the app under a real server and assert on the bytes that come back: "
       "CORS preflight status, security-header presence and consistency, cookie "
       "flags, CSP shape, and startup errors the app logged as non-critical.")
def http_response_contract(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="http_response_contract", dimension="14_frontend_web")
    if ctx.fast or ctx.options.get("no_tools"):
        res.facts["http_probe_skipped"] = "fast mode or --no-tools"
        return res
    try:
        from zz_integrations import http_probe
        # The probe boots a second uvicorn while the 10-worker sweep is running.
        # 300 s was not enough under that load and produced a false
        # "unavailable" verdict, so the default is generous; the readiness
        # signal is a real HTTP exchange, not a log line.
        facts = http_probe.run_probe(
            ctx, timeout=int(ctx.options.get("http_timeout", 900)))
    except Exception as exc:  # pragma: no cover
        res.facts["http_probe_error"] = f"{type(exc).__name__}: {exc}"
        return res

    res.facts["http_probe"] = {
        k: v for k, v in facts.items()
        if k not in ("checks", "startup_errors")}
    checks = facts.get("checks", [])
    res.facts["http_checks"] = checks
    if not facts.get("probed"):
        res.findings.append(Finding(
            id="HTTP-probe-unavailable", dimension="14_frontend_web", phase="infra",
            cluster="CLUSTER-http-layer", file="backend/main.py",
            current=f"the live HTTP probe could not run: "
                    f"{facts.get('error') or facts.get('boot', {}).get('exited_early')}",
            target="the app boots and serves at least one HTTP response",
            delta="no runtime HTTP evidence exists; header and CORS defects are "
                  "unobservable",
            fix="start the stack (valkey + database reachable) and re-run with --http",
            effort="S", priority="P1", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="partial",
            verify="python _zozi_audit/zozi_audit.py --full --http",
        ))
        return res

    for chk in checks:
        res.observations.append(Observation(
            "http_check", chk.get("id", "?"), chk.get("path", "/"), 0,
            "14_frontend_web",
            evidence=("ok" if chk.get("ok") else "PROBLEM") + " · " +
                      ", ".join(f"{k}={v}" for k, v in chk.items()
                                if k not in ("id", "ok", "csp", "traceback_tail")
                                and not isinstance(v, (dict,)))[:220],
        ))

    # CORS preflight — the defect class this dimension exists for.
    for chk in checks:
        if chk.get("id") != "HTTP-CORS-PREFLIGHT":
            continue
        if chk.get("ok"):
            continue
        res.findings.append(Finding(
            id="HTTP-cors-preflight", dimension="14_frontend_web", phase="infra",
            cluster="CLUSTER-http-cors",
            file=f"backend::GET {chk.get('path')}",
            current=f"CORS preflight for `{chk.get('method')} {chk.get('path')}` "
                    f"answered **{chk.get('status')} {chk.get('reason', '')}** instead "
                    f"of 2xx with Access-Control-Allow-Methods",
            target="a preflight answers 2xx with Access-Control-Allow-Origin, "
                   "-Methods and -Headers",
            delta="a browser refuses to send the real request, so every "
                  "cross-origin write from the web app fails; curl and the "
                  "in-process ASGI test client both pass, which is why this was "
                  "never caught",
            fix="intercept OPTIONS before routing — use Starlette's "
                "CORSMiddleware at app level instead of adding the headers in a "
                "BaseHTTPMiddleware, which runs after routing has already 405'd",
            effort="S", priority="P0", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="yes",
            verify=f"curl -i -X OPTIONS http://127.0.0.1:8000{chk.get('path')} "
                   f"-H 'Origin: http://localhost:3000' "
                   f"-H 'Access-Control-Request-Method: {chk.get('method')}'",
            snippet=f"allow_origin={chk.get('allow_origin')} "
                    f"allow_methods={chk.get('allow_methods')}",
        ))
        res.recommendations.append(Recommendation(
            area="ops", dimension="14_frontend_web",
            title="Replace hand-rolled CORS headers with Starlette CORSMiddleware",
            rationale="Setting Access-Control-* inside a BaseHTTPMiddleware happens "
                      "after the router has already rejected the OPTIONS verb, so "
                      "preflight fails while the headers look present in the response.",
            current="manual ACAO/ACAM/ACAH assignment in a response middleware.",
            proposal="mount `CORSMiddleware` once at app level with allow_origins, "
                     "allow_methods, allow_headers and allow_credentials; delete the "
                     "manual header writes; add a preflight test that asserts the "
                     "status code, not just the headers.",
            benefit="cross-origin writes work in a browser, and one preflight test "
                    "locks it in",
            effort="S", impact="high", category="quality",
            evidence="backend/middleware/security_headers.py",
        ))

    for chk in checks:
        if chk.get("id") != "HTTP-HEADERS" or chk.get("ok"):
            continue
        missing = ", ".join(chk.get("missing_required") or []) or "none"
        deprecated = ", ".join(chk.get("deprecated_present") or []) or "none"
        res.findings.append(Finding(
            id="HTTP-header-policy", dimension="18_security", phase="infra",
            cluster="CLUSTER-http-headers", file="backend/middleware/security_headers.py",
            current=f"`{chk.get('path')}` is missing {missing}; deprecated headers "
                    f"present: {deprecated}",
            target="every response carries the modern security header set and no "
                   "removed header",
            delta="the browser has no defence-in-depth for this route",
            fix="add the missing headers to the security-headers middleware and "
                "remove X-XSS-Protection (removed from all current browsers)",
            effort="S", priority="P1", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="partial",
            verify="curl -sS -D - -o /dev/null http://127.0.0.1:8000/health",
            snippet=deprecated,
        ))

    for chk in checks:
        if chk.get("id") != "HTTP-CSP-SHAPE" or chk.get("ok"):
            continue
        loc = ", ".join(chk.get("localhost_in_csp") or [])[:200]
        res.findings.append(Finding(
            id="HTTP-csp-localhost", dimension="18_security", phase="infra",
            cluster="CLUSTER-http-csp", file="backend/middleware/security_headers.py",
            current=f"the CSP served on `{chk.get('path')}` names localhost origins: "
                    f"{loc}",
            target="a shipped CSP references only real origins; development origins "
                   "are injected only when APP_ENV is not production",
            delta="a localhost origin in a production CSP is both dead weight and a "
                  "hint of the dev default leaking into a deployed policy",
            fix="build connect-src from the configured frontend_url/backend_url only, "
                "and omit localhost entirely when app_env == 'production'",
            effort="S", priority="P1", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="partial",
            verify="APP_ENV=production curl -sS -D - -o /dev/null "
                   "http://127.0.0.1:8000/health | grep -i content-security-policy",
            snippet=loc,
        ))

    for chk in checks:
        if chk.get("id") != "HTTP-CSP-SHAPE":
            continue
        issues = []
        if chk.get("uses_deprecated_report_uri"):
            issues.append("uses report-uri, superseded by report-to")
        if chk.get("missing_object_src"):
            issues.append("no object-src directive")
        if chk.get("missing_base_uri"):
            issues.append("no base-uri directive")
        if chk.get("wildcard_in_script_src"):
            issues.append("script-src is wildcard or allows unsafe-inline")
        if not issues:
            continue
        res.findings.append(Finding(
            id="HTTP-csp-directives", dimension="18_security", phase="infra",
            cluster="CLUSTER-http-csp", file="backend/middleware/security_headers.py",
            current=f"CSP on `{chk.get('path')}`: {'; '.join(issues)}",
            target="object-src 'none' and base-uri 'self' are present, and reporting "
                   "uses report-to",
            delta="a policy without object-src/base-uri leaves base-tag and plugin "
                  "injection paths open",
            fix="add the missing directives to CSP_POLICY and CSP_POLICY_DEV, and "
                "move to report-to/Reporting-Endpoints",
            effort="S", priority="P1", confidence=4, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="partial",
            verify="curl -sS -D - -o /dev/null http://127.0.0.1:8000/health | "
                   "grep -i content-security-policy",
            snippet="; ".join(issues),
        ))

    for chk in checks:
        if chk.get("id") != "HTTP-CORS-ORIGIN" or chk.get("ok"):
            continue
        res.findings.append(Finding(
            id="HTTP-cors-wildcard", dimension="18_security", phase="infra",
            cluster="CLUSTER-http-cors", file="backend/middleware/security_headers.py",
            current="Access-Control-Allow-Origin is `*` while credentials are allowed",
            target="an explicit origin list, never `*` together with credentials",
            delta="any site can make credentialed cross-origin reads",
            fix="resolve the Origin against the configured allowlist instead of `*`",
            effort="S", priority="P0", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="yes",
            verify="curl -sS -D - -o /dev/null -H 'Origin: https://evil.example' "
                   "http://127.0.0.1:8000/health | grep -i access-control-allow-origin",
        ))

    for chk in checks:
        if chk.get("id") != "HTTP-COOKIE-FLAGS" or chk.get("ok"):
            continue
        res.findings.append(Finding(
            id="HTTP-cookie-flags", dimension="18_security", phase="infra",
            cluster="CLUSTER-http-cookies", file="backend/middleware/security_headers.py",
            current=f"{len(chk.get('missing_secure_or_httponly') or [])} cookie(s) set "
                    f"without Secure or HttpOnly: "
                    f"{'; '.join(chk.get('missing_secure_or_httponly') or [])[:160]}",
            target="every session/CSRF cookie is HttpOnly and Secure outside local dev",
            delta="the CSRF token is readable by injected script",
            fix="set httponly=True and secure=True on the CSRF/session cookies, "
                "gated on app_env == 'production'",
            effort="S", priority="P1", confidence=4, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="partial",
            verify="curl -sS -D - -o /dev/null http://127.0.0.1:8000/health | "
                   "grep -i set-cookie",
        ))

    # Startup errors the app itself downgraded to "non-critical".
    for err in facts.get("startup_errors", [])[:10]:
        loc = err.get("location") or "backend/lifespan.py"
        res.findings.append(Finding(
            id="HTTP-startup-error", dimension="04_operational", phase="infra",
            cluster="CLUSTER-startup", file=loc,
            current=(f"startup logged an error from {err.get('logger', 'lifespan')}"
                     f"{'/' + err['event'] if err.get('event') else ''}: "
                     f"{err.get('message') or err.get('attribute') or 'see http_probe.log'}"),
            target="the lifespan starts every background subsystem without error",
            delta="a subsystem that fails here is absent in production and nothing "
                  "in the health endpoint reports it",
            fix=f"resolve the failing attribute ({err.get('attribute')}) in Settings, "
                f"or make the subsystem degrade explicitly rather than log-and-continue",
            effort="S", priority="P0", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="yes",
            verify="python -m uvicorn main:app --port 8000 2>&1 | grep -i error",
            snippet=err.get("traceback_tail", "")[-300:],
        ))
    return res


@check("security_header_policy", "18_security", "infra",
       "Static header-policy audit: what security headers and CSP directives the "
       "middleware can emit, including headers that are deprecated or removed. "
       "Runs with no server so header defects are never hidden behind a down stack.")
def security_header_policy(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="security_header_policy", dimension="18_security")
    emitted: dict[str, str] = {}
    localhost_defaults: list[tuple[str, int]] = []
    deprecated_csp: list[tuple[str, int]] = []
    directive_gaps: list[str] = []
    x_xss: list[tuple[str, int]] = []
    hardcoded_cors: list[tuple[str, int]] = []
    preflight_hits: list[tuple[str, int, str]] = []
    for p in _header_sources(ctx):
        rel = ctx.rel(p)
        text, _ = read_text(p)
        if not text:
            continue
        code = re.sub(r'"""[\s\S]*?"""', lambda m: " " * len(m.group(0)), text)
        # A preflight handler that calls call_next() and then decorates the
        # result has already let the router reject OPTIONS with 405. This is the
        # exact shape of the defect the live probe found, and it is detectable
        # without a server, so it stays reported when the stack is down.
        for m in re.finditer(
                r'(?:method|request\.method)\s*==\s*["\']OPTIONS["\'][\s\S]{0,600}?'
                r'(call_next\s*\(\s*request\s*\))', code):
            segment = code[m.start():m.start() + 700]
            after = segment[m.end(1) - m.start():]
            if re.search(r"^\s*return\b", after):
                continue
            ln = code[:m.start()].count("\n") + 1
            preflight_hits.append((
                rel, ln,
                "the OPTIONS branch decorates the routed response instead of "
                "answering the preflight itself"))
    # Several middleware files special-case OPTIONS; the finding is only
    # actionable if it names the one that owns the CORS headers.
    preflight_short_circuit = next(
        (h for h in preflight_hits if "security_header" in h[0]), None) or \
        (preflight_hits[0] if preflight_hits else None)

    for p in _header_sources(ctx):
        rel = ctx.rel(p)
        text, _ = read_text(p)
        if not text:
            continue
        code = re.sub(r'"""[\s\S]*?"""', lambda m: " " * len(m.group(0)), text)
        for m in re.finditer(r'(?:response\.headers|headers)\[\s*["\']([a-z0-9-]+)["\']'
                             r'\s*\]\s*=\s*([^;\n]{0,200})', code, re.I):
            emitted.setdefault(m.group(1).lower(), rel)
        for m in re.finditer(r'(?:response\.headers|headers)\.append\(\s*'
                             r'["\']([a-z0-9-]+)["\']', code, re.I):
            emitted.setdefault(m.group(1).lower(), rel)
        # Headers are commonly applied from a module-level dict in a loop:
        # `for header_name, header_value in ZOZI_SECURITY_HEADERS.items():`.
        # Matching only literal `headers["x"] = ...` reports those as missing,
        # which is exactly wrong — the live probe proves they are sent.
        for m in re.finditer(r'for\s+\w+\s*,\s*\w+\s+in\s+(\w+)\.items\(\)'
                             r'[\s\S]{0,400}?headers\[\w+\]\s*=\s*\w+', code, re.I):
            table = m.group(1)
            tm = re.search(rf"{table}\s*=\s*\{{([\s\S]*?)\n\}}", text or "")
            if not tm:
                continue
            for km in re.finditer(r'["\']([A-Za-z0-9-]+)["\']\s*:', tm.group(1)):
                emitted.setdefault(km.group(1).lower(), f"{rel}#{table}")
        lines = code.splitlines()
        for n, raw in enumerate(lines, 1):
            low = raw.lower()
            # A localhost/127.0.0.1 origin anywhere in a header or middleware
            # file is a default that can reach a deployed policy. Requiring the
            # line to also mention "csp" missed the real case, which is an
            # os.getenv default feeding the policy builder.
            if re.search(r"localhost:\d+|127\.0\.0\.1", low) and \
                    not re.search(r"docstring|example", low):
                localhost_defaults.append((f"{rel}:{n}", n))
            if "report-uri" in low:
                deprecated_csp.append((f"{rel}:{n}", n))
            if "x-xss-protection" in low:
                x_xss.append((f"{rel}:{n}", n))
            if re.search(r"allow_origins?\s*=\s*\[?\s*[\"']\*[\"']", low) or \
                    re.search(r"allow_origin[\"']?\s*\]?\s*=\s*[\"']\*[\"']", low):
                hardcoded_cors.append((f"{rel}:{n}", n))

    csp_src = next((p for p in _header_sources(ctx)
                    if "security_header" in ctx.rel(p)), None)
    directive_gaps: list[str] = []
    if csp_src is not None:
        text, _ = read_text(csp_src)
        for block_name in ("CSP_POLICY", "CSP_POLICY_DEV"):
            m = re.search(rf"{block_name}\s*=\s*\(([\s\S]*?)\n\)", text or "")
            if not m:
                continue
            body = m.group(1)
            present = set(re.findall(r"\b([a-z][a-z-]*)", body))
            gap = [d for d in REQUIRED_CSP_DIRECTIVES if d not in present]
            if gap:
                directive_gaps.extend(f"{block_name}: {', '.join(gap)}")

    res.facts["security_header_policy"] = {
        "header_sources": sorted({ctx.rel(p) for p in _header_sources(ctx)}),
        "headers_emitted": sorted(emitted),
        "missing_from_middleware": sorted(
            n for n in REQUIRED_HEADERS_LOCAL if n not in emitted),
        "localhost_defaults": len(localhost_defaults),
        "deprecated_csp_directives": len(deprecated_csp),
        "x_xss_protection_emitted": len(x_xss),
        "hardcoded_wildcard_cors": len(hardcoded_cors),
        "csp_directive_gaps": directive_gaps,
    }
    for path, line in localhost_defaults[:10]:
        res.observations.append(Observation(
            "header_source", path, path.split(":")[0], line, "18_security",
            evidence="localhost origin used as a CORS/CSP default"))
    for path, line in x_xss[:5]:
        res.observations.append(Observation(
            "header_source", path, path.split(":")[0], line, "18_security",
            evidence="X-XSS-Protection emitted — removed from all current browsers"))

    if x_xss:
        res.findings.append(Finding(
            id="SEC-xss-header-removed", dimension="18_security", phase="infra",
            cluster="CLUSTER-http-headers",
            file=x_xss[0][0].split(":")[0], line=x_xss[0][1],
            current=f"the security middleware emits X-XSS-Protection ({len(x_xss)} "
                    f"site(s))",
            target="no X-XSS-Protection: it was removed from Chrome, Firefox and "
                   "Edge and is ignored everywhere",
            delta="a dead header that reads as protection and can re-enable legacy "
                  "XSS filters on old user agents",
            fix="delete the X-XSS-Protection header and rely on the CSP",
            effort="S", priority="P2", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="no",
            verify="grep -rn 'x-xss-protection' backend/middleware",
            snippet="; ".join(p for p, _ in x_xss[:4]),
        ))
    if deprecated_csp:
        res.findings.append(Finding(
            id="SEC-csp-report-uri", dimension="18_security", phase="infra",
            cluster="CLUSTER-http-csp",
            file=deprecated_csp[0][0].split(":")[0], line=deprecated_csp[0][1],
            current="the CSP uses the deprecated `report-uri` directive",
            target="`report-to` with a Reporting-Endpoints header, or none",
            delta="violation reports are silently dropped by current Chrome and "
                  "Firefox, so CSP incidents are never seen",
            fix="add a Reporting-Endpoints header and switch to report-to",
            effort="S", priority="P2", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="no",
            verify="grep -rn 'report-uri' backend/middleware",
        ))
    if directive_gaps:
        res.findings.append(Finding(
            id="SEC-csp-missing-directive", dimension="18_security", phase="infra",
            cluster="CLUSTER-http-csp", file=ctx.rel(csp_src) if csp_src else "",
            current="the CSP is missing directives that close real injection paths: "
                    + "; ".join(directive_gaps),
            target="object-src 'none' and base-uri 'self' are always present",
            delta="without object-src and base-uri, <object>, <embed> and <base> "
                  "remain injectable",
            fix="add `object-src 'none';` and `base-uri 'self';` to both "
                "CSP_POLICY and CSP_POLICY_DEV",
            effort="S", priority="P1", confidence=4, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="partial",
            verify="grep -n \"object-src\\|base-uri\" backend/middleware/security_headers.py",
            snippet="; ".join(directive_gaps),
        ))
    if hardcoded_cors:
        res.findings.append(Finding(
            id="SEC-cors-wildcard-static", dimension="18_security", phase="infra",
            cluster="CLUSTER-http-cors",
            file=hardcoded_cors[0][0].split(":")[0], line=hardcoded_cors[0][1],
            current="CORS is configured with a wildcard origin",
            target="an explicit origin allowlist resolved per request",
            delta="with allow_credentials=True a wildcard is rejected by browsers; "
                  "without it, any site can read responses",
            fix="list the configured frontend origins explicitly",
            effort="S", priority="P1", confidence=4, evidence_strength="single",
            truth_level="L1", claim_state="INFERRED", completion_blocker="no",
            verify="grep -rn 'allow_origins' backend | head",
        ))
    if preflight_short_circuit:
        path, line, why = preflight_short_circuit
        res.findings.append(Finding(
            id="SEC-cors-preflight-static", dimension="18_security", phase="infra",
            cluster="CLUSTER-http-cors", file=path, line=line,
            current="the security middleware handles OPTIONS by calling call_next() "
                    "and then decorating the result, so the router has already "
                    "answered the preflight",
            target="a preflight is answered with its own 2xx response, before routing",
            delta=f"{why}; a browser therefore never sends the real cross-origin "
                  f"request, so every preflighted write fails in the browser while "
                  f"curl and the in-process test client pass",
            fix="return a Response(status_code=204, headers=...) for OPTIONS without "
                "calling call_next, or delete the hand-rolled headers and mount "
                "Starlette's CORSMiddleware at app level",
            effort="S", priority="P0", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="yes",
            verify="curl -i -X OPTIONS http://127.0.0.1:8000/api/v1/auth/login "
                   "-H 'Origin: http://localhost:3000' "
                   "-H 'Access-Control-Request-Method: POST'",
        ))
    if localhost_defaults:
        res.findings.append(Finding(
            id="SEC-localhost-origin-default", dimension="18_security", phase="infra",
            cluster="CLUSTER-http-csp", file=localhost_defaults[0][0].split(":")[0],
            line=localhost_defaults[0][1],
            current=f"{len(localhost_defaults)} place(s) default a CORS/CSP origin to "
                    f"localhost",
            target="localhost only when app_env is not production",
            delta="a deployed policy silently trusts localhost origins and hides the "
                  "fact that the real origin was never configured",
            fix="require the origin in production; fail closed when frontend_url is unset",
            effort="S", priority="P1", confidence=4, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="partial",
            verify="grep -rn 'localhost:3000\\|localhost:8000' backend/middleware",
            snippet="; ".join(p for p, _ in localhost_defaults[:4]),
        ))
    return res


REQUIRED_HEADERS_LOCAL = {
    "content-security-policy",
    "strict-transport-security",
    "x-content-type-options",
    "x-frame-options",
    "referrer-policy",
    "permissions-policy",
}
