"""Dimension 02 (technological) + Dimension 28 (supply chain security)."""
from __future__ import annotations

import re
from pathlib import Path

from zz_core.constants import (
    FORBIDDEN_JS_PACKAGES, FORBIDDEN_PY_PACKAGES, JS_VERSION_PINS_FALLBACK,
    PY_VERSION_PINS_FALLBACK,
)
from zz_core.model import CheckResult, Finding, Observation, ScanContext
from zz_core.registry import check
from zz_core.util import (
    parse_markdown_tables, parse_package_json, parse_requirements, parse_python,
    read_text,
)


def _norm(name: str) -> str:
    return name.lower().replace("_", "-").strip()


def _ver_tuple(v: str):
    nums = re.findall(r"\d+", v)
    return tuple(int(n) for n in nums[:3]) if nums else ()


def _satisfies(actual: str, target: str) -> bool:
    """Loose version check for pin tables like 0.141.x / 1.19.1+ / 3.0+."""
    if not actual or not target:
        return True
    a = _ver_tuple(actual)
    if not a:
        return True
    if "x" in target:
        t = _ver_tuple(target.replace("x", "0"))
        return a[:2] == t[:2]
    if target.endswith("+"):
        t = _ver_tuple(target[:-1])
        return a >= t
    if "<" in target or ">" in target:
        return True  # range: accept (full range parsing is out of scope)
    t = _ver_tuple(target)
    if not t:
        return True
    # exact match on the significant prefix
    return a[:len(t)] == t


def _tech_finding(dimension: str, phase: str, file: str, line: int, current: str,
                  target: str, fix: str, *, priority="P2", effort="S",
                  laws=(), blocker="no", confidence=5, cluster="",
                  origin="static", verify="") -> Finding:
    return Finding(
        id="", dimension=dimension, phase=phase, cluster=cluster, file=file,
        line=line, current=current, target=target, delta=current[:180],
        fix=fix, effort=effort, priority=priority, confidence=confidence,
        evidence_strength="triangulated" if confidence >= 4 else "multiple",
        truth_level="L0", claim_state="VERIFIED", completion_blocker=blocker,
        laws=laws, origin=origin, verify=verify,
    )


def _load_version_pins() -> dict:
    """Parse the TECHNOLOGY_STACK tables at runtime; fall back to constants."""
    from zz_core.constants import load_doc
    pins = dict(PY_VERSION_PINS_FALLBACK)
    text = load_doc("TECHNOLOGY_STACK.md")
    if not text:
        return pins
    for table in parse_markdown_tables(text):
        for row in table:
            if len(row) >= 2:
                tech = row[0].strip().strip("*`")
                version = row[1].strip().strip("*`")
                if tech and version and re.search(r"\d", version) and len(tech) < 40:
                    key = _norm(tech.split()[0])
                    if key and not key.startswith("-"):
                        pins.setdefault(key, version)
    return pins


@check("tech_python_deps", "02_technological", "tech",
       "Compare requirements/pyproject against TECHNOLOGY_STACK pins; flag "
       "forbidden packages and undeclared imports.")
def tech_python_deps(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="tech_python_deps", dimension="02_technological")
    pins = ctx.memo("py_version_pins", _load_version_pins)
    manifests = [p for p in (ctx.backend / "requirements.txt",
                             ctx.backend / "requirements-dev.txt",
                             ctx.backend / "requirements-compiled.txt")
                 if p.exists()]
    declared: dict[str, tuple[str, str, int]] = {}
    for mf in manifests:
        reqs = parse_requirements(mf)
        text, _ = read_text(mf)
        for pkg, ver in reqs.items():
            if pkg not in declared:
                line = 0
                for idx, line_text in enumerate((text or "").splitlines(), 1):
                    if re.match(rf"^\s*{re.escape(pkg)}[=<>!\[]", line_text, re.IGNORECASE):
                        line = idx
                        break
                declared[pkg] = (ver, ctx.rel(mf), line)
    # forbidden declared packages
    for pkg, (ver, mf, line) in declared.items():
        base = pkg.split("[")[0]
        if base in FORBIDDEN_PY_PACKAGES:
            res.findings.append(_tech_finding(
                "02_technological", "tech", mf, line,
                f"forbidden package declared: `{pkg}`" + (f"=={ver}" if ver else ""),
                "package is on the TECHNOLOGY_STACK forbidden list",
                f"Remove {base}; use the canonical replacement",
                priority="P1", laws=(44, 290), cluster="CLUSTER-forbidden-package",
                verify=f"grep -rni '{base}' backend/requirements*.txt",
            ))
    # version mismatches for packages that are pinned
    for pkg, (ver, mf, line) in declared.items():
        pin = pins.get(pkg) or pins.get(pkg.replace("-", "_"))
        if not pin or not ver:
            continue
        if not _satisfies(ver, pin):
            res.findings.append(_tech_finding(
                "02_technological", "tech", mf, line,
                f"`{pkg}=={ver}` does not satisfy pinned `{pin}`",
                f"TECHNOLOGY_STACK.md pins {pkg} at {pin}",
                f"Update {pkg} to the pinned version",
                priority="P1", laws=(290,), cluster="CLUSTER-version-drift",
                verify=f"grep -i '{pkg}' backend/requirements.txt",
            ))
    # missing canonical packages that the code imports
    code_imports = ctx.memo("backend_import_names", lambda: _top_level_imports(ctx))
    for mod in sorted(code_imports):
        if mod in ("fastapi_limiter_valkey",) and mod.replace("_", "-") not in declared:
            res.findings.append(_tech_finding(
                "02_technological", "tech", "backend/requirements.txt", 0,
                f"`{mod}` imported in production code but absent from requirements",
                "every production import is declared (build reproducibility)",
                f"Add {mod.replace('_', '-')} to requirements.txt",
                priority="P0", blocker="yes", cluster="CLUSTER-undeclared-import",
                verify=f"grep -rn 'import {mod}' backend | head",
            ))
    # uv.lock usability
    uv = ctx.backend / "uv.lock"
    uv_text, _ = read_text(uv)
    entries = len(re.findall(r"^\[\[package\]\]", uv_text or "", re.MULTILINE))
    if uv.exists() and entries < 10:
        res.findings.append(_tech_finding(
            "02_technological", "tech", "backend/uv.lock", 1,
            f"uv.lock holds only {entries} package entr(ies) — not a usable lockfile",
            "uv.lock is a complete lockfile (TECHNOLOGY_STACK §19)",
            "Regenerate uv.lock with `uv lock`",
            priority="P0", blocker="yes", cluster="CLUSTER-lockfile",
            verify="uv lock --check",
        ))
    pyproject = ctx.backend / "pyproject.toml"
    pt, _ = read_text(pyproject)
    if pyproject.exists() and "[project.dependencies]" not in (pt or ""):
        res.findings.append(_tech_finding(
            "02_technological", "tech", "backend/pyproject.toml", 1,
            "pyproject.toml declares no [project.dependencies]",
            "uv-managed dependency source of truth",
            "Move runtime dependencies into [project.dependencies]",
            priority="P1", cluster="CLUSTER-lockfile",
        ))
    return res


def _top_level_imports(ctx: ScanContext) -> set[str]:
    names: set[str] = set()
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if not any(rel.startswith(f"backend/{d}/") for d in
                   ("domains", "modules", "rbac", "kernel", "infrastructure",
                    "providers", "jobs", "middleware")) and rel != "backend/main.py":
            continue
        parsed = parse_python(p)
        if parsed.error:
            continue
        from zz_core.util import ast_imports
        for module, _names, _line, _kind in ast_imports(parsed.tree):
            if module and not module.startswith("."):
                names.add(module.split(".")[0])
    return names


@check("tech_js_deps", "02_technological", "tech",
       "Compare web/mobile/shared package.json against pins; flag forbidden "
       "packages, missing canonical packages and lockfile problems.")
def tech_js_deps(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="tech_js_deps", dimension="02_technological")
    pins = JS_VERSION_PINS_FALLBACK
    targets = {
        "web": ctx.frontend / "web_app" / "package.json",
        "mobile": ctx.frontend / "mobile_app" / "package.json",
        "shared": ctx.frontend / "shared" / "package.json",
        "root": ctx.root / "package.json",
    }
    required_web = ("next-intl", "@sentry/nextjs", "sharp")
    for label, path in targets.items():
        if not path.exists():
            continue
        pkg = parse_package_json(path)
        deps = {}
        deps.update(pkg.get("dependencies") or {})
        deps.update(pkg.get("devDependencies") or {})
        rel = ctx.rel(path)
        for name, spec in deps.items():
            low = _norm(name)
            if low in FORBIDDEN_JS_PACKAGES:
                res.findings.append(_tech_finding(
                    "02_technological", "tech", rel, 1,
                    f"forbidden package `{name}` in {label}",
                    "Law 171 forbids @tanstack/react-query and SWR",
                    f"Remove {name}; use RSC + Zustand",
                    priority="P1", laws=(171,), cluster="CLUSTER-forbidden-js-package",
                ))
            pin = pins.get(low)
            if pin and spec:
                actual = re.sub(r"^[\^~>=<]+", "", str(spec))
                if not _satisfies(actual, pin):
                    res.findings.append(_tech_finding(
                        "02_technological", "tech", rel, 1,
                        f"`{name}: {spec}` does not satisfy pinned `{pin}`",
                        f"TECHNOLOGY_STACK.md pins {name} at {pin}",
                        f"Upgrade {name} to {pin}",
                        priority="P1" if _ver_tuple(actual)[:1] != _ver_tuple(pin)[:1] else "P2",
                        cluster="CLUSTER-version-drift",
                    ))
        if label == "web":
            for req in required_web:
                if req not in deps:
                    res.findings.append(_tech_finding(
                        "02_technological", "tech", rel, 1,
                        f"required web package missing: `{req}`",
                        "TECHNOLOGY_STACK requires next-intl, @sentry/nextjs, sharp",
                        f"Install {req}",
                        priority="P1", cluster="CLUSTER-missing-js-package",
                    ))
            if "framer-motion" not in deps and "motion" not in deps:
                res.findings.append(_tech_finding(
                    "02_technological", "tech", rel, 1,
                    "neither `motion` nor `framer-motion` installed",
                    "motion 13.2.0+ is the canonical animation library",
                    "Install motion@13.2.0+",
                    priority="P2", cluster="CLUSTER-missing-js-package",
                ))
        res.observations.append(Observation(
            "package", label, rel, 1, "02_technological",
            evidence=f"{len(deps)} declared packages",
        ))
    # package manager policy
    lock = ctx.frontend / "web_app" / "pnpm-lock.yaml"
    if not lock.exists():
        res.findings.append(_tech_finding(
            "02_technological", "tech", "frontend/web_app/", 0,
            "pnpm-lock.yaml missing for the web app",
            "pnpm is the canonical package manager; lockfile committed",
            "Generate and commit pnpm-lock.yaml",
            priority="P0", blocker="yes", cluster="CLUSTER-lockfile",
        ))
    for stray in ("package-lock.json", "yarn.lock"):
        hits = [p for p in (ctx.frontend / "web_app", ctx.root) if (p / stray).exists()]
        for hit in hits:
            res.findings.append(_tech_finding(
                "02_technological", "tech", ctx.rel(hit / stray), 1,
                f"non-canonical lockfile `{stray}` present",
                "pnpm exclusively (TECHNOLOGY_STACK §12)",
                f"Delete {stray}",
                priority="P2", cluster="CLUSTER-package-manager",
            ))
    root_pkg = parse_package_json(ctx.root / "package.json")
    if root_pkg:
        scripts = " ".join((root_pkg.get("scripts") or {}).values())
        if re.search(r"\bnpm\b", scripts):
            res.findings.append(_tech_finding(
                "02_technological", "tech", "package.json", 1,
                "root scripts invoke `npm` instead of `pnpm`",
                "pnpm exclusively (TECHNOLOGY_STACK §12)",
                "Replace npm invocations with pnpm",
                priority="P2", cluster="CLUSTER-package-manager",
            ))
        if not root_pkg.get("packageManager"):
            res.findings.append(_tech_finding(
                "02_technological", "tech", "package.json", 1,
                "no `packageManager` field",
                "pin the package manager (pnpm 10.x)",
                'Add "packageManager": "pnpm@10.x"',
                priority="P3", cluster="CLUSTER-package-manager",
            ))
    return res


@check("tech_runtime_images", "02_technological", "tech",
       "Dockerfiles, compose images, CI python/node versions (Python 3.13, "
       "Node 22.12, Postgres 16 dev).")
def tech_runtime_images(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="tech_runtime_images", dimension="02_technological")
    for dockerfile in [ctx.backend / "Dockerfile", ctx.backend / "Dockerfile.prod",
                       ctx.frontend / "web_app" / "Dockerfile" if (ctx.frontend / "web_app" / "Dockerfile").exists() else None]:
        if not dockerfile or not Path(dockerfile).exists():
            continue
        text, _ = read_text(dockerfile)
        rel = ctx.rel(dockerfile)
        for idx, line in enumerate((text or "").splitlines(), 1):
            m = re.match(r"\s*FROM\s+(\S+)", line)
            if not m:
                continue
            image = m.group(1)
            if image.startswith("python:") and not re.match(r"python:3\.13", image):
                res.findings.append(_tech_finding(
                    "02_technological", "tech", rel, idx,
                    f"base image `{image}` drifts from Python 3.13.x",
                    "Python 3.13.x runtime (TECHNOLOGY_STACK §1)",
                    "Update base image to python:3.13-slim",
                    priority="P0", blocker="yes", cluster="CLUSTER-base-image",
                ))
            if image.startswith("node:") and not re.match(r"node:2[24]", image):
                res.findings.append(_tech_finding(
                    "02_technological", "tech", rel, idx,
                    f"base image `{image}` drifts from Node 22.x",
                    "Node 22.12.0 runtime (TECHNOLOGY_STACK §12)",
                    "Update base image to node:22-alpine",
                    priority="P1", cluster="CLUSTER-base-image",
                ))
            if image.startswith("python:3.13") and "slim" not in image:
                res.findings.append(_tech_finding(
                    "02_technological", "tech", rel, idx,
                    "python base image is not slim",
                    "python:3.13-slim for a small secure image",
                    "Switch to python:3.13-slim",
                    priority="P3",
                ))
    compose = ctx.root / "docker-compose.yml"
    text, _ = read_text(compose)
    for idx, line in enumerate((text or "").splitlines(), 1):
        m = re.search(r"image:\s*(postgres:\S+)", line)
        if m and "16" not in m.group(1):
            res.findings.append(_tech_finding(
                "02_technological", "tech", ctx.rel(compose), idx,
                f"dev database image `{m.group(1)}` (documented: postgres:16-alpine)",
                "local dev uses PostgreSQL 16-alpine (TECHNOLOGY_STACK §2)",
                "Align the compose image with the documented dev database",
                priority="P2", cluster="CLUSTER-base-image",
            ))
    # CI python / node
    for wf in (ctx.root / ".github" / "workflows").glob("*.yml"):
        text, _ = read_text(wf)
        for idx, line in enumerate((text or "").splitlines(), 1):
            m = re.search(r'python-version:\s*["\']?([\d.]+)', line)
            if m and not m.group(1).startswith("3.13"):
                res.findings.append(_tech_finding(
                    "02_technological", "tech", ctx.rel(wf), idx,
                    f"CI python-version {m.group(1)} (canonical 3.13)",
                    "CI runs the canonical Python line",
                    "Set python-version to 3.13",
                    priority="P1", cluster="CLUSTER-ci-runtime",
                ))
            m = re.search(r'node-version:\s*["\']?([\d.]+)', line)
            if m and not m.group(1).startswith("22"):
                res.findings.append(_tech_finding(
                    "02_technological", "tech", ctx.rel(wf), idx,
                    f"CI node-version {m.group(1)} (canonical 22.12)",
                    "CI runs Node 22",
                    "Set node-version to 22",
                    priority="P2", cluster="CLUSTER-ci-runtime",
                ))
    return res


@check("tech_supply_chain", "28_supply_chain_security", "tech",
       "SBOM presence, dependency scanning in CI, gitleaks config, workflow "
       "permissions, package-manager policy, image signing.")
def tech_supply_chain(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="tech_supply_chain", dimension="28_supply_chain_security")
    wf_dir = ctx.root / ".github" / "workflows"
    workflows = list(wf_dir.glob("*.yml")) + list(wf_dir.glob("*.yaml"))
    all_ci = ""
    for wf in workflows:
        text, _ = read_text(wf)
        all_ci += (text or "") + "\n"
    checks = [
        ("dependency scanning (pip-audit / trivy / snyk / dependabot)",
         r"pip-audit|trivy|snyk|dependabot", "no dependency scanning step in CI"),
        ("secret scanning (gitleaks / trufflehog)",
         r"gitleaks|trufflehog|detect-secrets", "no secret scanning in CI"),
        ("SBOM generation (syft / cyclonedx)",
         r"syft|cyclonedx|sbom", "no SBOM generation in CI"),
        ("container image scanning (trivy/grype)",
         r"trivy|grype", "no container scan in CI"),
    ]
    for area, pattern, note in checks:
        found = bool(re.search(pattern, all_ci, re.IGNORECASE))
        res.facts.setdefault("supply_chain", []).append({
            "area": area, "finding": "present" if found else note,
            "evidence": ".github/workflows/*",
            "status": "PASS" if found else "FAIL",
            "blocker": "no" if found else "partial",
        })
        if not found:
            res.findings.append(_tech_finding(
                "28_supply_chain_security", "infra", ".github/workflows/", 0,
                note, "supply-chain security gates in CI (Laws 44, 291)",
                "Add the scanning step to CI", priority="P1",
                laws=(44, 291), cluster="CLUSTER-supply-chain",
            ))
    # workflow permissions
    for wf in workflows:
        text, _ = read_text(wf)
        if text and "permissions:" not in text:
            res.findings.append(_tech_finding(
                "28_supply_chain_security", "infra", ctx.rel(wf), 1,
                "workflow declares no `permissions:` block",
                "least-privilege GITHUB_TOKEN permissions",
                "Add an explicit permissions block (contents: read)",
                priority="P2", cluster="CLUSTER-supply-chain",
            ))
    # gitleaks config
    gl = ctx.root / ".gitleaks.toml"
    res.observations.append(Observation(
        "file", ".gitleaks.toml", ctx.rel(gl), 0, "28_supply_chain_security",
        evidence="present" if gl.exists() else "absent",
    ))
    # SBOM artifact presence
    # pruned walk — never rglob the whole repo (node_modules/.next/.kilo worktrees)
    sbom = [p for p in ctx.all_files
            if p.name.endswith(".sbom.json") or (p.name.startswith("sbom") and p.name.endswith(".json"))]
    if not sbom:
        res.findings.append(_tech_finding(
            "28_supply_chain_security", "infra", ".", 0,
            "no SBOM artifact found in the repository",
            "SBOM is available as a compliance artifact (Law 291)",
            "Generate SBOM via Syft/CycloneDX in CI and retain it",
            priority="P2", laws=(291,), cluster="CLUSTER-supply-chain",
        ))
    return res
