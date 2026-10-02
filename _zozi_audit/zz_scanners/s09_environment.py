"""Dimension 11 (environmental)."""
from __future__ import annotations

import re

from zz_core.constants import DEPRECATED_ENV_ALIASES, load_doc, REQUIRED_PROD_ENV
from zz_core.model import CheckResult, Finding, Observation, ScanContext
from zz_core.registry import check
from zz_core.util import parse_markdown_tables, parse_python, read_text


def _f(dimension, phase, file, line, current, target, fix, *, priority="P2",
       effort="S", laws=(), blocker="no", cluster="", truth="L0",
       claim="VERIFIED", evidence="multiple", verify="", snippet="") -> Finding:
    return Finding(
        id="", dimension=dimension, phase=phase, cluster=cluster, file=file,
        line=line, current=current, target=target, delta=current[:180], fix=fix,
        effort=effort, priority=priority, confidence=4, evidence_strength=evidence,
        truth_level=truth, claim_state=claim, completion_blocker=blocker,
        laws=laws, origin="static", verify=verify, snippet=snippet,
    )


def _env_doc_names() -> set[str]:
    text = load_doc("TECHNOLOGY_STACK.md")
    names: set[str] = set()
    for table in parse_markdown_tables(text):
        for row in table:
            for cell in row:
                for m in re.findall(r"\b([A-Z][A-Z0-9_]{3,})\b", cell):
                    names.add(m)
    return names


@check("env_inventory", "11_environmental", "infra",
       "Every env read: path:line, typed?, documented, in .env.example, "
       "deprecated aliases, required-in-prod presence.")
def env_inventory(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="env_inventory", dimension="11_environmental")
    reads: dict[str, list[str]] = {}
    raw_reads: list[tuple[str, int, str]] = []
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if not any(rel.startswith(f"backend/{d}/") for d in
                   ("domains", "modules", "rbac", "kernel", "infrastructure",
                    "providers", "jobs", "middleware")) and rel not in (
                "backend/main.py", "backend/config.py", "backend/lifespan.py"):
            continue
        text, _ = read_text(p)
        if not text:
            continue
        for idx, line in enumerate(text.splitlines(), 1):
            for m in re.finditer(r"os\.(?:getenv|environ\.get)\(\s*[\"']([A-Z][A-Z0-9_]+)[\"']", line):
                reads.setdefault(m.group(1), []).append(f"{rel}:{idx}")
                raw_reads.append((rel, idx, m.group(1)))
    doc_names = _env_doc_names()
    env_example, _ = read_text(ctx.root / ".env.example")
    declared = set(re.findall(r"^([A-Z][A-Z0-9_]+)=", env_example or "", re.MULTILINE))
    cfg, _ = read_text(ctx.backend / "config.py")
    typed_fields = set(re.findall(r"^\s*([a-z_][a-z0-9_]*)\s*:\s*[A-Za-z]", cfg or "", re.MULTILINE))
    typed_upper = {f.upper() for f in typed_fields}
    for name, sites in sorted(reads.items()):
        res.observations.append(Observation(
            "env_var", name, sites[0].split(":")[0], int(sites[0].split(":")[1]),
            "11_environmental",
            evidence=f"{len(sites)} raw read(s)",
        ))
        if name in DEPRECATED_ENV_ALIASES:
            res.findings.append(_f(
                "11_environmental", "tech", sites[0].split(":")[0],
                int(sites[0].split(":")[1]),
                f"deprecated env alias `{name}` read at {sites[0]}",
                f"use canonical `{DEPRECATED_ENV_ALIASES[name]}`",
                f"Migrate {name} → {DEPRECATED_ENV_ALIASES[name]}",
                priority="P2", cluster="CLUSTER-env-alias",
            ))
        if name not in declared and name not in doc_names and name not in typed_upper:
            res.findings.append(_f(
                "11_environmental", "infra", sites[0].split(":")[0],
                int(sites[0].split(":")[1]),
                f"env var `{name}` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK",
                "every env var is declared + documented (Law 202)",
                f"Add {name} to typed settings and .env.example",
                priority="P2", cluster="CLUSTER-env-undeclared",
                truth="L1", claim="INFERRED",
            ))
    if raw_reads:
        res.findings.append(_f(
            "11_environmental", "infra", raw_reads[0][0], raw_reads[0][1],
            f"{len(raw_reads)} raw os.getenv/environ read(s) bypass typed settings",
            "pydantic-settings typed loading only (Laws 84, 203)",
            "Move reads into config.py settings",
            priority="P1", blocker="partial", laws=(84, 203),
            cluster="CLUSTER-env-raw",
        ))
    missing_req = [r for r in REQUIRED_PROD_ENV if r not in declared]
    if missing_req:
        res.findings.append(_f(
            "11_environmental", "infra", ".env.example", 0,
            f"required-in-production vars absent from .env.example: {', '.join(missing_req)}",
            "required vars declared and validated (Law 202)",
            "Add the vars with empty defaults",
            priority="P1", blocker="partial", laws=(202,),
            cluster="CLUSTER-env-required",
        ))
    res.facts["env_vars_raw"] = len(reads)
    res.facts["env_vars_declared"] = len(declared)
    res.facts["env_vars_documented"] = len(doc_names)
    return res


@check("env_country_config", "11_environmental", "infra",
       "Country-specific configuration: DEFAULT_COUNTRY drift, per-country tax/"
       "commission/gateway/logistics config surfaces.")
def env_country_config(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="env_country_config", dimension="11_environmental")
    cfg, _ = read_text(ctx.backend / "config.py")
    m = re.search(r"default_country[^=]*=\s*(?:Field\()?[^\"']*[\"']([A-Z]{2})[\"']", cfg or "")
    default_country = m.group(1) if m else ""
    doc = load_doc("TECHNOLOGY_STACK.md")
    doc_country = ""
    if "DEFAULT_COUNTRY" in doc:
        dm = re.search(r"DEFAULT_COUNTRY.*?default `([A-Z]{2})`", doc)
        doc_country = dm.group(1) if dm else ""
    if default_country and doc_country and default_country != doc_country:
        res.findings.append(_f(
            "11_environmental", "infra", "backend/config.py", 0,
            f"DEFAULT_COUNTRY default `{default_country}` vs documented `{doc_country}`",
            "config matches canonical documentation",
            "Align the default or update the canonical doc",
            priority="P2", cluster="CLUSTER-env-country",
            truth="L1", claim="CONTRADICTED" if doc_country else "INFERRED",
            evidence="triangulated",
        ))
        res.facts.setdefault("contradictions", []).append({
            "id": "CONTRAD-CONFIG-DEFAULT-COUNTRY", "category": "code_vs_config",
            "source_a": "_most_imp_docx/TECHNOLOGY_STACK.md",
            "a_says": f"DEFAULT_COUNTRY default {doc_country}",
            "source_b": "backend/config.py",
            "b_says": f"default_country default {default_country}",
            "conflict": "default country differs between documentation and code",
            "impact": "RLS fallback and localization bind to the wrong country",
            "blocker": "partial", "user_decision": "yes",
        })
    country_modules = list((ctx.backend / "domains" / "country").rglob("*.py")) \
        if (ctx.backend / "domains" / "country").exists() else []
    res.observations.append(Observation(
        "file", "country-domain", "backend/domains/country", 0, "11_environmental",
        evidence=f"{len(country_modules)} module(s)",
    ))
    for surface, pattern in (
        ("tax rates", r"tax_rate|vat_rate"),
        ("commission rates", r"commission_rate"),
        ("payment gateways", r"payment_gateway"),
        ("logistics settings", r"logistics.*config|shipping.*config"),
        ("legal templates", r"terms_of_service|privacy_policy|legal_document"),
    ):
        found = False
        for p in country_modules:
            text, _ = read_text(p)
            if re.search(pattern, text or "", re.IGNORECASE):
                found = True
                break
        res.facts.setdefault("country_config", []).append({
            "area": surface, "present": found,
        })
        if not found:
            res.findings.append(_f(
                "11_environmental", "infra", "backend/domains/country/", 0,
                f"no country-config surface found for {surface}",
                "country-specific config exists per capability",
                f"Model {surface} under the country domain",
                priority="P2", cluster="CLUSTER-country-config",
                truth="L1", claim="INFERRED",
            ))
    return res


@check("settings_contract", "11_environmental", "infra",
       "Every settings.<attr> read and every os.getenv() key resolved against the "
       "fields Settings actually declares. A read of an undeclared attribute only "
       "fails when that code path executes, which is why it survives every other "
       "check in this suite.")
def settings_contract(ctx: ScanContext) -> CheckResult:
    import ast

    res = CheckResult(check="settings_contract", dimension="11_environmental")
    config = ctx.backend / "config.py"
    if not config.exists():
        return res
    parsed = parse_python(config)
    if not parsed.tree:
        res.findings.append(_f(
            "11_environmental", "infra", "backend/config.py", 0,
            "backend/config.py could not be parsed, so the settings contract "
            "cannot be established",
            "config.py parses", "fix the syntax error", priority="P0",
            cluster="CLUSTER-settings-contract"))
        return res

    declared: set[str] = set()
    for node in ast.walk(parsed.tree):
        if isinstance(node, ast.ClassDef):
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    declared.add(stmt.target.id)
                elif isinstance(stmt, ast.Assign):
                    for t in stmt.targets:
                        if isinstance(t, ast.Name):
                            declared.add(t.id)
                # A @property or a helper method is also a valid attribute of
                # the instance. Excluding them reports `settings.has_smtp_config`
                # as undefined when it is a property — the same false-positive
                # class this suite keeps having to correct.
                elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    declared.add(stmt.name)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            declared.add(node.target.id)
    # Settings may also inherit fields or methods from a base class.
    for node in ast.walk(parsed.tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id != "Settings":
                    declared.add(base.id)
                    bp = node
                    _ = bp

    reads: dict[str, list[str]] = {}
    env_reads: dict[str, list[str]] = {}
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if rel in ("backend/config.py",) or "/tests/" in rel:
            continue
        p_parsed = parse_python(p)
        if not p_parsed.tree:
            continue
        for node in ast.walk(p_parsed.tree):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) \
                    and node.value.id == "settings":
                reads.setdefault(node.attr, []).append(
                    f"{rel}:{node.lineno}")
            if isinstance(node, ast.Call):
                fn = getattr(node.func, "attr", getattr(node.func, "id", ""))
                if fn in ("getenv", "get"):
                    for arg in node.args[:1]:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            env_reads.setdefault(arg.value.upper(), []).append(
                                f"{rel}:{node.lineno}")

    undefined = {k: v for k, v in reads.items() if k not in declared}
    res.facts["settings_contract"] = {
        "declared_fields": len(declared),
        "settings_attribute_reads": len(reads),
        "undefined_attributes": len(undefined),
        "undefined_names": sorted(undefined),
        "env_keys_read": len(env_reads),
        "env_keys_not_declared_as_field": sorted(
            k for k in env_reads
            if k.lower() not in {d.lower() for d in declared})[:40],
    }
    for attr, sites in sorted(undefined.items(), key=lambda kv: -len(kv[1]))[:40]:
        rel, _, line = sites[0].partition(":")
        res.observations.append(Observation(
            "settings_read", f"{rel}:{line}", rel, int(line or 0),
            "11_environmental",
            evidence=f"settings.{attr} read but not declared on Settings "
                     f"({len(sites)} site(s))"))
    for attr, sites in sorted(undefined.items(), key=lambda kv: -len(kv[1]))[:12]:
        rel, _, line = sites[0].partition(":")
        res.findings.append(_f(
            "11_environmental", "infra", rel, int(line or 0),
            f"settings.{attr} is read but Settings declares no such field",
            f"Settings declares every attribute the code reads "
            f"({len(declared)} fields declared, {len(undefined)} read but missing)",
            f"add `{attr}` to the Settings class in backend/config.py, or correct "
            f"the read site",
            priority="P0", cluster="CLUSTER-settings-contract",
            verify=f"grep -n '{attr}' backend/config.py",
            snippet="; ".join(sites[:5]),
        ))
    return res
