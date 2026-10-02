"""Dimension 04 (operational) + Dimension 13 (dev to production)."""
from __future__ import annotations

import re

from zz_core.model import CheckResult, Finding, Observation, ScanContext
from zz_core.registry import check
from zz_core.util import read_text, SimpleYaml


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


@check("ops_jobs", "04_operational", "infra",
       "Enumerate backend/jobs/*: celery registration, beat schedule, retry, "
       "DLQ, timeout, rate/concurrency limits, orphan jobs (Laws 115, 297-299).")
def ops_jobs(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="ops_jobs", dimension="04_operational")
    jobs_dir = ctx.backend / "jobs"
    if not jobs_dir.exists():
        return res
    celery_text, _ = read_text(jobs_dir / "celery_app.py")
    beat_text, _ = read_text(jobs_dir / "periodic_tasks.py")
    celery_all = (celery_text or "") + "\n" + (beat_text or "")
    job_files = [p for p in jobs_dir.glob("*.py") if p.name not in ("__init__.py",)]
    unregistered = []
    for p in sorted(job_files):
        stem = p.stem
        text, _ = read_text(p)
        has_tasks = "@shared_task" in (text or "") or "@app.task" in (text or "") or "task(" in (text or "")
        registered = stem in celery_all or f"jobs.{stem}" in celery_all
        res.observations.append(Observation(
            "job", stem, ctx.rel(p), 1, "04_operational",
            evidence=f"tasks={has_tasks} registered={registered}",
        ))
        if has_tasks and not registered:
            unregistered.append(stem)
        if has_tasks:
            if "retry" not in (text or "").lower():
                res.findings.append(_f(
                    "04_operational", "infra", ctx.rel(p), 1,
                    "celery task module without retry policy",
                    "retry with backoff + jitter, max 5 (Law 297)",
                    "Add autoretry_for/retry_backoff_max and a DLQ path",
                    priority="P2", laws=(297,), cluster="CLUSTER-job-resilience",
                ))
            if "dlq" not in (text or "").lower() and "dead_letter" not in (text or "").lower():
                res.findings.append(_f(
                    "04_operational", "infra", ctx.rel(p), 1,
                    "celery task module with no DLQ reference",
                    "failed events go to a replayable DLQ (Law 298)",
                    "Route terminal failures to the DLQ",
                    priority="P3", laws=(298,), cluster="CLUSTER-job-resilience",
                    truth="L1", claim="INFERRED",
                ))
    if unregistered:
        res.findings.append(_f(
            "04_operational", "infra", "backend/jobs/", 0,
            f"{len(unregistered)} task module(s) never referenced by celery_app/periodic_tasks: "
            f"{', '.join(sorted(unregistered)[:10])}",
            "every scheduled job is registered (Law 115)",
            "Register the tasks or delete the dead modules",
            priority="P2", laws=(115,), cluster="CLUSTER-orphan-job",
            truth="L1", claim="INFERRED",
        ))
    # beat schedule presence
    if jobs_dir.exists() and "beat_schedule" not in celery_all:
        res.findings.append(_f(
            "04_operational", "infra", "backend/jobs/celery_app.py", 0,
            "no beat_schedule found in celery configuration",
            "Celery Beat runs scheduled finance/logistics jobs (Law 115)",
            "Define beat_schedule entries or document the external scheduler",
            priority="P2", laws=(115,), cluster="CLUSTER-job-scheduling",
            truth="L1", claim="INFERRED",
        ))
    return res


@check("ops_health_checks", "04_operational", "infra",
       "Verify /health, /health/deps, /health/ready existence and fail-closed "
       "behaviour (Law 81, OPS-001).")
def ops_health_checks(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="ops_health_checks", dimension="04_operational")
    main_text, _ = read_text(ctx.backend / "main.py")
    text = main_text or ""
    for route in ("/health", "/health/deps", "/health/ready"):
        present = route in text
        res.observations.append(Observation(
            "route", route, "backend/main.py", 0, "04_operational",
            evidence="declared" if present else "MISSING",
        ))
        if not present:
            res.findings.append(_f(
                "04_operational", "infra", "backend/main.py", 0,
                f"health endpoint `{route}` not found",
                "liveness/dependency/readiness endpoints exist (Law 81)",
                f"Implement {route}",
                priority="P1", laws=(81,), cluster="CLUSTER-health",
                blocker="partial",
            ))
    # /health/deps fail-closed analysis: does it ever return non-200?
    deps_block = ""
    m = re.search(r"async def health_deps\(.*?(?=\n@app\.|\ndef |\Z)", text, re.DOTALL)
    if m:
        deps_block = m.group(0)
        if "status_code" not in deps_block and "503" not in deps_block:
            res.findings.append(_f(
                "04_operational", "infra", "backend/main.py",
                ctx.line_of("backend/main.py", "async def health_deps"),
                "/health/deps always returns HTTP 200 regardless of dependency state",
                "health endpoints fail closed so orchestrators stop routing (Law 81)",
                "Return 503 when DB/Valkey/payments/email are unhealthy",
                priority="P0", blocker="yes", laws=(81,),
                cluster="CLUSTER-health", verify="grep -n 'health_deps' -A25 backend/main.py",
            ))
    return res


@check("ops_ci_cd", "13_dev_to_prod", "infra",
       "Audit .github/workflows: test/deploy/rollback jobs, pre-deploy migrations, "
       "health gates, promotion, secret/dependency scanning (Laws 217-219, 243).")
def ops_ci_cd(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="ops_ci_cd", dimension="13_dev_to_prod")
    wf_dir = ctx.root / ".github" / "workflows"
    workflows = sorted(list(wf_dir.glob("*.yml")) + list(wf_dir.glob("*.yaml"))) if wf_dir.exists() else []
    if not workflows:
        res.findings.append(_f(
            "13_dev_to_prod", "infra", ".github/workflows/", 0,
            "no GitHub Actions workflows present",
            "CI pipeline runs lint/type/tests/build (Laws 217-219)",
            "Create ci.yml + deploy.yml with pre-deploy migrations and a health gate",
            priority="P0", blocker="yes", laws=(217, 218, 219),
            cluster="CLUSTER-ci-cd",
        ))
        return res
    names = []
    combined = ""
    for wf in workflows:
        text, _ = read_text(wf)
        combined += (text or "") + "\n"
        names.append(wf.name)
        res.observations.append(Observation(
            "build_step", wf.name, ctx.rel(wf), 1, "13_dev_to_prod",
            evidence=f"{len((text or '').splitlines())} lines",
        ))
    checks = [
        ("CI workflow", r"pytest|test", "ci.yml"),
        ("deploy workflow", r"deploy", "deploy.yml"),
        ("rollback workflow", r"rollback", "rollback.yml"),
        ("pre-deploy migration step", r"alembic\s+upgrade\s+head", None),
        ("post-deploy health gate", r"health/ready|health/deps|/health", None),
        ("secret scanning", r"gitleaks|trufflehog", None),
        ("dependency scanning", r"pip-audit|trivy|safety|dependabot", None),
    ]
    for label, pattern, _hint in checks:
        if not re.search(pattern, combined, re.IGNORECASE):
            priority = "P0" if label in ("deploy workflow", "pre-deploy migration step") else "P1"
            blocker = "yes" if priority == "P0" else "partial"
            res.findings.append(_f(
                "13_dev_to_prod", "infra", ".github/workflows/", 0,
                f"pipeline lacks: {label}",
                "CI/CD covers lint, tests, migrations, health gate, rollback (Laws 217-219)",
                f"Add a {label} step",
                priority=priority, blocker=blocker, laws=(217, 218, 219),
                cluster="CLUSTER-ci-cd",
            ))
    res.facts["workflows"] = names
    return res


@check("ops_deployment_assets", "13_dev_to_prod", "infra",
       "Dockerfiles (multi-stage, non-root), compose limits, runbooks, "
       "rollback docs, Makefile targets (Laws 215-220, 248).")
def ops_deployment_assets(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="ops_deployment_assets", dimension="13_dev_to_prod")
    for df in [ctx.backend / "Dockerfile", ctx.backend / "Dockerfile.prod"]:
        if not df.exists():
            continue
        text, _ = read_text(df)
        rel = ctx.rel(df)
        if "USER " not in (text or ""):
            res.findings.append(_f(
                "13_dev_to_prod", "infra", rel, 0,
                "container runs without a non-root USER",
                "least-privilege container user",
                "Create an app user and switch to it",
                priority="P2", cluster="CLUSTER-deploy",
            ))
        if "HEALTHCHECK" not in (text or ""):
            res.findings.append(_f(
                "13_dev_to_prod", "infra", rel, 0,
                "container has no HEALTHCHECK",
                "container health is checkable",
                "Add HEALTHCHECK against /health",
                priority="P2", cluster="CLUSTER-deploy",
            ))
    compose = ctx.root / "docker-compose.yml"
    text, _ = read_text(compose)
    if compose.exists() and "deploy:" not in (text or "") and "mem_limit" not in (text or ""):
        res.findings.append(_f(
            "13_dev_to_prod", "infra", ctx.rel(compose), 0,
            "no resource limits declared in compose",
            "resource limits guard the single VPS (Law 267)",
            "Add mem/cpu limits to long-running services",
            priority="P3", cluster="CLUSTER-deploy",
        ))
    runbooks = list((ctx.root / "docs").rglob("*.md")) if (ctx.root / "docs").exists() else []
    rb_names = " ".join(p.name.lower() for p in runbooks)
    for needed in ("deploy", "rollback", "migration"):
        if needed not in rb_names:
            res.findings.append(_f(
                "13_dev_to_prod", "docs", f"docs/runbooks/{needed}.md", 0,
                f"no {needed} runbook found",
                "runbook exists per operational procedure (Law 248)",
                f"Write docs/runbooks/{needed}.md",
                priority="P2", laws=(248,), cluster="CLUSTER-runbooks",
            ))
    setup = ctx.root / "SETUP.md"
    if not setup.exists():
        res.findings.append(_f(
            "13_dev_to_prod", "docs", "SETUP.md", 0,
            "SETUP.md missing",
            "infrastructure setup documented (Law 314)",
            "Document provisioning in SETUP.md",
            priority="P3", cluster="CLUSTER-docs",
        ))
    return res


@check("ops_feature_flags", "04_operational", "infra",
       "Typed feature flags via pydantic-settings; raw os.getenv in production "
       "paths; security-relevant defaults (Law 84, OPS-004).")
def ops_feature_flags(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="ops_feature_flags", dimension="04_operational")
    raw_hits: list[tuple[str, int, str]] = []
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if not any(rel.startswith(f"backend/{d}/") for d in
                   ("providers", "domains", "jobs", "middleware", "infrastructure")):
            continue
        text, _ = read_text(p)
        if not text:
            continue
        for idx, line in enumerate(text.splitlines(), 1):
            if re.search(r"os\.(getenv|environ\.get)\(", line) and "settings." not in line:
                raw_hits.append((rel, idx, line.strip()[:160]))
    if raw_hits:
        by_dir: dict[str, int] = {}
        for rel, _l, _s in raw_hits:
            by_dir[rel.split("/")[1] if "/" in rel else rel] = by_dir.get(rel.split("/")[1] if "/" in rel else rel, 0) + 1
        res.findings.append(_f(
            "04_operational", "infra", raw_hits[0][0], raw_hits[0][1],
            f"{len(raw_hits)} raw os.getenv/os.environ read(s) in production paths "
            f"(top: {', '.join(f'{k}={v}' for k, v in sorted(by_dir.items(), key=lambda kv: -kv[1])[:6])})",
            "typed pydantic-settings only; raw os.getenv FORBIDDEN (Law 84)",
            "Move each variable into typed settings",
            priority="P1", laws=(84,), blocker="partial",
            cluster="CLUSTER-raw-getenv", evidence="multiple",
        ))
    # security-disabling defaults
    cfg, _ = read_text(ctx.backend / "config.py")
    for var, pattern, target in (
        ("RATE_LIMIT_ENABLED", r"rate_limit_enabled[^=]*=\s*Field\([^)]*default\s*=\s*False", "true (fail closed)"),
        ("CSRF", r"csrf_enabled[^=]*=\s*Field\([^)]*default\s*=\s*False", "enabled in all environments"),
    ):
        if re.search(pattern, cfg or "", re.IGNORECASE | re.DOTALL):
            res.findings.append(_f(
                "04_operational", "security", "backend/config.py",
                ctx.line_of("backend/config.py", var.lower()),
                f"`{var}` defaults to disabled",
                f"{var} must default to {target} (Laws 35, 37)",
                f"Flip the default to {target}",
                priority="P1", blocker="partial", laws=(35, 37),
                cluster="CLUSTER-insecure-default",
            ))
    return res
