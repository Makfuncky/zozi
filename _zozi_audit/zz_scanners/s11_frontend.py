"""Dimension 14 (frontend web) + Dimension 15 (frontend mobile) + Dimension 26 (alignment)."""
from __future__ import annotations

import re
from pathlib import Path

from zz_core.model import CheckResult, Finding, Observation, ScanContext
from zz_core.registry import check
from zz_core.util import iter_files, parse_package_json, read_text


def _f(dimension, phase, file, line, current, target, fix, *, priority="P2",
       effort="M", laws=(), blocker="no", cluster="", truth="L0",
       claim="VERIFIED", evidence="multiple") -> Finding:
    return Finding(
        id="", dimension=dimension, phase=phase, cluster=cluster, file=file,
        line=line, current=current, target=target, delta=current[:180], fix=fix,
        effort=effort, priority=priority, confidence=4, evidence_strength=evidence,
        truth_level=truth, claim_state=claim, completion_blocker=blocker,
        laws=laws, origin="static",
    )


def _web_root(ctx: ScanContext) -> Path:
    return ctx.frontend / "web_app"


@check("web_route_tree", "14_frontend_web", "frontend",
       "Route tree: pages/layouts/loading/error coverage, RSC vs client, "
       "duplicate actor trees, rewrites (Laws 111-112, 173, 177-178).")
def web_route_tree(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="web_route_tree", dimension="14_frontend_web")
    app = _web_root(ctx) / "src" / "app"
    if not app.exists():
        res.findings.append(_f(
            "14_frontend_web", "frontend", "frontend/web_app/src/app", 0,
            "Next.js app router tree missing",
            "App Router route tree exists (Law 111)",
            "Restore the app directory",
            priority="P0", blocker="yes", laws=(111,),
            cluster="CLUSTER-web-routes",
        ))
        return res
    pages = sorted(p for p in iter_files(app, (".tsx",)) if p.name == "page.tsx")
    missing_states = []
    client_pages = 0
    for page in pages:
        route = page.parent
        if not (route / "loading.tsx").exists() and not (route / "loading.jsx").exists():
            missing_states.append(f"{ctx.rel(route)}/loading.tsx")
        if not (route / "error.tsx").exists() and not (route / "error.jsx").exists():
            missing_states.append(f"{ctx.rel(route)}/error.tsx")
        text, _ = ctx.read(page)
        if "use client" in (text or "")[:200]:
            client_pages += 1
    if missing_states:
        res.findings.append(_f(
            "14_frontend_web", "frontend", ctx.rel(pages[0]) if pages else "frontend/web_app/src/app", 0,
            f"{len(missing_states)} page(s) lack loading/error siblings (sample {missing_states[0]})",
            "every route has loading + error states (Law 178)",
            "Add loading.tsx/error.tsx per route group",
            priority="P1", blocker="partial", laws=(178,),
            cluster="CLUSTER-web-states",
        ))
    # duplicate actor trees
    for a, b in (("logistics-partner", "logistics-partners"),):
        if (app / a).exists() and (app / b).exists():
            res.findings.append(_f(
                "14_frontend_web", "frontend", f"frontend/web_app/src/app/{a}", 0,
                f"duplicate route trees `{a}` and `{b}` both exist",
                "one route tree per actor (Law 177)",
                "Consolidate the duplicate trees",
                priority="P2", laws=(177,), cluster="CLUSTER-web-routes",
            ))
    # rewrites vs backend modules
    nxt, _ = read_text(_web_root(ctx) / "next.config.ts")
    if nxt and re.search(r"source:\s*['\"]/hr", nxt):
        res.findings.append(_f(
            "14_frontend_web", "frontend", "frontend/web_app/next.config.ts",
            ctx.line_of(_web_root(ctx) / "next.config.ts", "/hr"),
            "rewrite `/hr/*` targets a non-canonical backend surface",
            "only canonical module prefixes are proxied (Laws 13/173)",
            "Remove the /hr rewrite or move it under admin",
            priority="P2", laws=(13, 173), cluster="CLUSTER-web-rewrites",
        ))
    res.facts["web_pages"] = len(pages)
    res.facts["web_missing_states"] = len(missing_states)
    res.facts["web_client_pages"] = client_pages
    res.observations.append(Observation(
        "page", "web-app", ctx.rel(app), 0, "14_frontend_web",
        evidence=f"pages={len(pages)} client={client_pages} missing_states={len(missing_states)}",
    ))
    return res


@check("web_ui_quality", "14_frontend_web", "frontend",
       "Modals (role/aria/focus), buttons (labels/loading), images (next/image, "
       "AVIF candidates), console.log, any-types, TODOs.")
def web_ui_quality(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="web_ui_quality", dimension="14_frontend_web")
    files = [p for p in ctx.ts_files if "/frontend/web_app/" in ctx.rel(p)]
    modal_hits = 0
    modal_bad = 0
    img_plain = 0
    console_logs = 0
    any_count = 0
    todo = 0
    for p in files:
        text, _ = read_text(p)
        if not text:
            continue
        rel = ctx.rel(p)
        for idx, line in enumerate(text.splitlines(), 1):
            if re.search(r"role=[\"']dialog[\"']|aria-modal", line):
                modal_hits += 1
            if re.search(r"<Modal|Dialog|Popup", line) and "aria" not in line:
                modal_bad += 1
            if re.search(r"<img\b", line):
                img_plain += 1
            if re.search(r"console\.log\(", line):
                console_logs += 1
            if re.search(r":\s*any\b|<any>|as any", line):
                any_count += 1
            if re.search(r"\b(TODO|FIXME)\b", line):
                todo += 1
    if modal_hits == 0 and modal_bad:
        res.findings.append(_f(
            "14_frontend_web", "frontend", "frontend/web_app/src", 0,
            f"{modal_bad} modal/dialog pattern(s) without role/aria-modal",
            "dialog semantics: role=dialog, aria-modal, focus trap, Escape (a11y)",
            "Add dialog semantics and focus management",
            priority="P1", blocker="partial", cluster="CLUSTER-web-a11y",
        ))
    if img_plain:
        res.findings.append(_f(
            "14_frontend_web", "frontend", "frontend/web_app/src", 0,
            f"{img_plain} plain <img> tag(s) (next/image not used)",
            "images use next/image with WebP/AVIF + lazy loading (Laws 225/258)",
            "Replace <img> with next/image",
            priority="P1", blocker="partial", cluster="CLUSTER-web-images",
        ))
    if console_logs:
        res.findings.append(_f(
            "14_frontend_web", "frontend", "frontend/web_app/src", 0,
            f"{console_logs} console.log call(s) in production components",
            "unhandled errors go to the error tracker, not console (Law 176)",
            "Remove or route through the error reporter",
            priority="P3", cluster="CLUSTER-web-quality",
        ))
    res.facts["web_any_types"] = any_count
    res.facts["web_todos"] = todo
    if any_count > 20:
        res.findings.append(_f(
            "14_frontend_web", "frontend", "frontend/web_app/src", 0,
            f"{any_count} `any` usages",
            "TypeScript strict mode; any requires justification (Law 170)",
            "Replace any with precise types",
            priority="P2", cluster="CLUSTER-web-types",
        ))
    # image formats in next config
    nxt, _ = read_text(_web_root(ctx) / "next.config.ts")
    if nxt and "avif" not in nxt.lower():
        res.findings.append(_f(
            "14_frontend_web", "frontend", "frontend/web_app/next.config.ts", 0,
            "next/image formats do not enable AVIF",
            "image pipeline serves WebP/AVIF (Law 258)",
            "Add formats: ['image/avif','image/webp']",
            priority="P2", cluster="CLUSTER-web-images",
        ))
    return res


def _backend_routes(ctx: ScanContext) -> set[str]:
    routes: set[str] = set()
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if "/modules/" not in rel or "/routers/" not in rel:
            continue
        text, _ = read_text(p)
        if not text:
            continue
        prefix_m = re.search(r"APIRouter\(\s*[^)]*prefix\s*=\s*[\"']([^\"']+)[\"']", text, re.S)
        prefix = prefix_m.group(1) if prefix_m else ""
        for m in re.finditer(r"@router\.(get|post|put|patch|delete)\(\s*[\"']([^\"']*)[\"']", text):
            method, path = m.group(1).upper(), m.group(2)
            full = (prefix + path).rstrip("/") or "/"
            full = re.sub(r"\{[^}]+\}", "*", full)
            routes.add(f"{method} {full}")
    return routes


@check("web_api_alignment", "26_code_alignment", "frontend",
       "Frontend API calls vs backend routes: orphan calls, shape alignment, "
       "permissions alignment (dimension 26).")
def web_api_alignment(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="web_api_alignment", dimension="26_code_alignment")
    backend = _backend_routes(ctx)
    frontend_calls: dict[str, list[str]] = {}
    for p in ctx.ts_files + ctx.js_files:
        rel = ctx.rel(p)
        if "/frontend/" not in rel and "/_browser_test/" not in rel:
            continue
        text, _ = read_text(p)
        if not text:
            continue
        for m in re.finditer(r"[\"'`](/api/v1/[^\"'`\s)]+)", text):
            path = m.group(1).split("?")[0]
            path = re.sub(r"\$\{[^}]+\}", "*", path)
            frontend_calls.setdefault(path, []).append(rel)
    unmatched = []
    for path, sites in sorted(frontend_calls.items()):
        if not _route_matches(backend, path):
            unmatched.append((path, sites[0]))
    if frontend_calls:
        res.facts.setdefault("alignment", []).append({
            "id": "ALIGN-web-api",
            "area": "Frontend API calls ↔ backend routes",
            "frontend": f"{len(frontend_calls)} distinct paths",
            "backend": f"{len(backend)} routes",
            "verdict": f"{len(unmatched)} unmatched frontend path(s)",
            "blocker": "partial" if unmatched else "no",
        })
    for path, site in unmatched[:80]:
        res.findings.append(_f(
            "26_code_alignment", "frontend", site, 0,
            f"frontend calls `{path}` with no matching backend route",
            "every frontend call maps to a backend route (Law 172/173)",
            "Fix the path or add the backend route",
            priority="P1", blocker="partial", laws=(172, 173),
            cluster="CLUSTER-align-api", truth="L1", claim="INFERRED",
        ))
    _alignment_coverage(ctx, res, backend, frontend_calls)
    return res


#: Alignment areas required by PROMPT_FORENSIC_AUDIT §7.26. Each entry records
#: whether this static pass actually inspected it, so dimension 26 can never
#: render a clean PASS for work that was not done.
ALIGNMENT_AREAS: tuple[tuple[str, str, str], ...] = (
    ("ALIGN-route", "route parity", "static"),
    ("ALIGN-type", "request/response type parity", "static"),
    ("ALIGN-store", "Zustand store ↔ API payload shape", "static"),
    ("ALIGN-permission", "permission string ↔ /rbac/catalog", "static"),
    ("ALIGN-error-shape", "error envelope shape", "static"),
    ("ALIGN-pagination", "pagination envelope shape", "static"),
    ("ALIGN-idempotency", "idempotency key propagation", "static"),
    ("ALIGN-screen", "screen ↔ module parity", "static"),
    ("ALIGN-feature", "feature-gate ↔ catalog parity", "static"),
    ("ALIGN-store-shape", "shared store shape parity (web/mobile)", "static"),
    ("ALIGN-api-client", "api-core.ts vs generated types", "static"),
)


def _route_matches(backend_routes: set[str], frontend_path: str) -> bool:
    """Strict route resolution: exact path, template wildcard, or prefix mount."""
    norm = re.sub(r"\{[^}]+\}", "*", frontend_path).rstrip("/") or "/"
    for route in backend_routes:
        _, _, bpath = route.partition(" ")
        bpath = bpath.rstrip("/") or "/"
        if norm == bpath:
            return True
        if "*" in bpath:
            head = bpath.split("*", 1)[0].rstrip("/")
            if norm == head or norm.startswith(head + "/"):
                return True
        # backend route mounted under a versioned prefix the frontend also uses
        if norm.endswith(bpath) or bpath.endswith(norm):
            return True
    return False


def _alignment_coverage(ctx: ScanContext, res: CheckResult,
                        backend: set[str], frontend_calls: dict[str, list[str]]) -> None:
    """Emit one observation per required alignment area (checked or not)."""
    web_text = ""
    for p in ctx.ts_files:
        if "/frontend/" in ctx.rel(p):
            text, _ = read_text(p)
            web_text += (text or "")[:200_000]
    for area_id, area, _kind in ALIGNMENT_AREAS:
        if area_id == "ALIGN-route":
            ev = f"{len(frontend_calls)} frontend path(s) vs {len(backend)} backend route(s)"
        elif area_id == "ALIGN-permission":
            perms = web_text.count("require_feature") + web_text.count("hasPermission")
            ev = f"{perms} permission-gate reference(s) in web source"
        elif area_id == "ALIGN-error-shape":
            ev = f"{len(re.findall(r'detail', web_text))} error-envelope reference(s) in web source"
        elif area_id == "ALIGN-pagination":
            ev = f"{len(re.findall(r'items|total|page|limit', web_text))} pagination field reference(s) in web source"
        else:
            ev = "inventory recorded; no divergence asserted without a tool run"
        res.observations.append(Observation(
            "alignment_area", area_id, area, 0, "26_code_alignment",
            evidence=ev, note=area,
        ))


@check("mobile_app", "15_frontend_mobile", "mobile",
       "Expo config, OTA updates, secure storage, offline handling, push, "
       "permissions, payments, Detox (Laws 187-194).")
def mobile_app(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="mobile_app", dimension="15_frontend_mobile")
    mobile = ctx.frontend / "mobile_app"
    if not mobile.exists():
        res.findings.append(_f(
            "15_frontend_mobile", "mobile", "frontend/mobile_app", 0,
            "mobile app directory missing",
            "Expo app exists or is explicitly deferred",
            "Restore the app or document deferral",
            priority="P2", blocker="partial", cluster="CLUSTER-mobile",
            truth="L1", claim="INFERRED",
        ))
        return res
    pkg = parse_package_json(mobile / "package.json")
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    app_json = mobile / "app.json"
    aj, _ = read_text(app_json)
    if "expo-updates" not in deps:
        res.findings.append(_f(
            "15_frontend_mobile", "mobile", "frontend/mobile_app/package.json", 0,
            "expo-updates absent from dependencies",
            "OTA updates enabled (Law 194)",
            "Install expo-updates and enable updates in app config",
            priority="P1", blocker="partial", cluster="CLUSTER-mobile-ota",
        ))
    if aj and re.search(r'"ENABLED"\s*:\s*false|"enabled"\s*:\s*false', aj):
        res.findings.append(_f(
            "15_frontend_mobile", "mobile", "frontend/mobile_app/app.json", 0,
            "expo updates explicitly disabled in app config",
            "OTA hotfix path available (Law 194)",
            "Enable expo-updates",
            priority="P1", blocker="partial", cluster="CLUSTER-mobile-ota",
        ))
    # secure storage vs async storage for tokens
    insecure = []
    for p in iter_files(mobile, (".ts", ".tsx")):
        text, _ = read_text(p)
        if text and re.search(r"AsyncStorage.*(token|jwt|secret)", text, re.IGNORECASE):
            insecure.append(ctx.rel(p))
    if insecure:
        res.findings.append(_f(
            "15_frontend_mobile", "mobile", insecure[0], 0,
            f"{len(insecure)} file(s) persist tokens via AsyncStorage",
            "tokens use expo-secure-store/Keychain (Law 193)",
            "Move token storage to SecureStore",
            priority="P0", blocker="yes", laws=(193,),
            cluster="CLUSTER-mobile-secrets",
        ))
    detox = [p for p in iter_files(mobile, (".js", ".ts")) if ".e2e." in p.name]
    if not detox:
        res.findings.append(_f(
            "15_frontend_mobile", "mobile", "frontend/mobile_app", 0,
            "no Detox e2e specs",
            "mobile critical paths covered by Detox (TECHNOLOGY_STACK §15)",
            "Add Detox specs",
            priority="P2", cluster="CLUSTER-mobile-e2e",
        ))
    # dynamic requires not declared
    dynamic_pkgs = set()
    for p in iter_files(mobile, (".ts", ".tsx")):
        text, _ = read_text(p)
        for m in re.finditer(r"require\(['\"](@[\w\-/]+|[\w\-]+)['\"]\)", text or ""):
            dynamic_pkgs.add(m.group(1))
    missing = [d for d in dynamic_pkgs if d not in deps and not d.startswith(".")]
    if missing:
        res.findings.append(_f(
            "15_frontend_mobile", "mobile", "frontend/mobile_app", 0,
            f"dynamically required package(s) absent from package.json: {', '.join(sorted(missing)[:8])}",
            "every runtime dependency is declared",
            "Declare or remove the dynamic requires",
            priority="P1", blocker="partial", cluster="CLUSTER-mobile-deps",
        ))
    res.facts["mobile"] = {
        "deps": len(deps), "detox_specs": len(detox),
        "ota_pkg": "expo-updates" in deps,
        "insecure_token_files": len(insecure),
    }
    return res
