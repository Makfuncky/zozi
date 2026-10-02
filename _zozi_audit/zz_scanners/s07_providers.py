"""Dimension 08 (providers)."""
from __future__ import annotations

import re
from pathlib import Path

from zz_core.constants import CANONICAL_PROVIDER_DIRS, load_doc
from zz_core.model import CheckResult, Finding, Observation, ScanContext
from zz_core.registry import check
from zz_core.util import read_text, parse_markdown_tables


def _f(dimension, phase, file, line, current, target, fix, *, priority="P2",
       effort="S", laws=(), blocker="no", cluster="", truth="L0",
       claim="VERIFIED", evidence="multiple", verify="") -> Finding:
    return Finding(
        id="", dimension=dimension, phase=phase, cluster=cluster, file=file,
        line=line, current=current, target=target, delta=current[:180], fix=fix,
        effort=effort, priority=priority, confidence=4, evidence_strength=evidence,
        truth_level=truth, claim_state=claim, completion_blocker=blocker,
        laws=laws, origin="static", verify=verify,
    )


@check("prov_inventory", "08_providers", "arch",
       "Inventory every provider module: category, HAS_ flags, health_check(), "
       "async usage, timeouts, secrets source, tests, callers, extras.")
def prov_inventory(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="prov_inventory", dimension="08_providers")
    root = ctx.backend / "providers"
    if not root.exists():
        return res
    provider_files = [p for p in root.rglob("*.py")
                      if p.name != "__init__.py" and p.name != "_base.py"]
    no_health: list[str] = []
    no_has: list[str] = []
    no_async: list[str] = []
    no_timeout: list[str] = []
    raw_env: list[str] = []
    test_root = ctx.backend / "tests" / "providers"
    tested = 0
    callers: dict[str, int] = {}
    domain_imports = ctx.memo("domain_provider_refs", lambda: _domain_provider_refs(ctx))
    for p in provider_files:
        rel = ctx.rel(p)
        text, _ = read_text(p)
        if not text:
            continue
        has_health = "def health_check" in text
        has_flag = bool(re.search(r"HAS_[A-Z_]+", text))
        is_async = "async def" in text
        has_timeout = bool(re.search(r"timeout", text, re.IGNORECASE))
        uses_env = bool(re.search(r"os\.getenv|os\.environ", text))
        if not has_health:
            no_health.append(rel)
        if not has_flag:
            no_has.append(rel)
        if not is_async:
            no_async.append(rel)
        if not has_timeout:
            no_timeout.append(rel)
        if uses_env:
            raw_env.append(rel)
        stem = p.stem
        if test_root.exists() and any(stem in t.name for t in test_root.rglob("*.py")):
            tested += 1
        callers[stem] = domain_imports.get(stem, 0)
        res.observations.append(Observation(
            "provider", stem, rel, 1, "08_providers",
            evidence=f"health={has_health} HAS_flag={has_flag} async={is_async} "
                     f"timeout={has_timeout} env={uses_env} domain_refs={callers[stem]}",
        ))
    # undocumented provider directories
    observed_dirs = {p.relative_to(root).parts[0] for p in provider_files}
    extras = sorted(d for d in observed_dirs if d not in CANONICAL_PROVIDER_DIRS and d not in (".",))
    if extras:
        res.findings.append(_f(
            "08_providers", "arch", "backend/providers/", 0,
            f"provider package(s) outside the canonical tree: {', '.join(extras)}",
            "provider tree fixed by ARCHITECTURE_STACK §3 (Law 9/16)",
            "Promote into a canonical provider category or document the addition",
            priority="P2", laws=(9, 16), cluster="CLUSTER-provider-extra",
        ))
    n = max(1, len(provider_files))
    if len(no_health) > n * 0.5:
        res.findings.append(_f(
            "08_providers", "arch", "backend/providers/", 0,
            f"{len(no_health)}/{n} provider modules lack health_check()",
            "every provider exposes health_check() (Law 129)",
            "Add BaseProvider.health_check() implementations",
            priority="P1", blocker="partial", laws=(129,),
            cluster="CLUSTER-provider-health",
        ))
    if len(no_has) > n * 0.5:
        res.findings.append(_f(
            "08_providers", "arch", "backend/providers/", 0,
            f"{len(no_has)}/{n} provider modules expose no HAS_<SDK> flag",
            "HAS_<SDK> flags enable graceful degradation (Laws 30/124)",
            "Add HAS_ flags for every optional SDK",
            priority="P1", blocker="partial", laws=(30, 124),
            cluster="CLUSTER-provider-degradation",
        ))
    if raw_env:
        res.findings.append(_f(
            "08_providers", "arch", "backend/providers/", 0,
            f"{len(raw_env)} provider module(s) read secrets via raw os.getenv",
            "provider config lives in providers/config.py typed settings (Law 127)",
            "Move the reads into typed config",
            priority="P1", blocker="partial", laws=(127,),
            cluster="CLUSTER-provider-config",
        ))
    if no_timeout:
        res.findings.append(_f(
            "08_providers", "arch", "backend/providers/", 0,
            f"{len(no_timeout)}/{n} provider modules declare no timeout",
            "every outbound call has an explicit timeout",
            "Add explicit timeouts to HTTP/SDK calls",
            priority="P1", blocker="partial", laws=(75,),
            cluster="CLUSTER-provider-timeout",
        ))
    res.facts["providers"] = {
        "count": len(provider_files), "tested": tested,
        "no_health": len(no_health), "no_has_flag": len(no_has),
        "no_timeout": len(no_timeout), "raw_env": len(raw_env),
        "extras": extras,
    }
    # provider unnamed/unused
    orphan = [k for k, v in callers.items() if v == 0 and k not in ("async_workers",)]
    if orphan:
        res.findings.append(_f(
            "08_providers", "arch", "backend/providers/", 0,
            f"{len(orphan)} provider module(s) never referenced by any domain file: "
            f"{', '.join(sorted(orphan)[:12])}",
            "every provider has a caller or is documented as deferred",
            "Delete or wire the orphan providers",
            priority="P2", cluster="CLUSTER-orphan-provider",
            truth="L1", claim="INFERRED",
        ))
    return res


def _domain_provider_refs(ctx: ScanContext) -> dict[str, int]:
    refs: dict[str, int] = {}
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if not rel.startswith("backend/domains/"):
            continue
        text, _ = read_text(p)
        if not text:
            continue
        for m in re.finditer(r"from\s+providers(?:\.([\w.]+))?\s+import|import\s+providers(?:\.([\w.]+))?", text):
            mod = (m.group(1) or m.group(2) or "").split(".")[0]
            if mod:
                refs[mod] = refs.get(mod, 0) + 1
    return refs


@check("prov_payment_security", "08_providers", "payment",
       "Payment adapters + gateway storage: encrypted credentials, webhook "
       "signature verification, idempotency, fallback routing (Laws 118/123/313).")
def prov_payment_security(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="prov_payment_security", dimension="08_providers")
    pay_dir = ctx.backend / "providers" / "payments"
    if pay_dir.exists():
        files = [p for p in pay_dir.rglob("*.py") if p.name != "__init__.py"]
        for p in files:
            rel = ctx.rel(p)
            text, _ = read_text(p)
            if not text:
                continue
            if "verify" not in text.lower() and "webhook" in text.lower():
                res.findings.append(_f(
                    "08_providers", "payment", rel, 1,
                    "payment adapter references webhooks but shows no signature verification",
                    "webhook signatures verified before trusting payloads (Law 313)",
                    "Verify the gateway signature with the stored secret",
                    priority="P0", blocker="yes", laws=(313,),
                    cluster="CLUSTER-payment-webhook", truth="L1", claim="INFERRED",
                ))
        res.facts["payment_adapters"] = len(files)
    # encrypted credential storage
    models_text = ""
    for p in (ctx.backend / "domains" / "finance").rglob("*.py"):
        if "payment" in p.name and "model" in ctx.rel(p):
            t, _ = read_text(p)
            models_text += t or ""
    if models_text and re.search(r"secret_key\s*[:=]", models_text) and not re.search(r"EncryptedString|encrypted", models_text):
        res.findings.append(_f(
            "08_providers", "payment", "backend/domains/finance/", 0,
            "payment gateway secret columns appear to be plain String (no encryption marker)",
            "AES-256-GCM field encryption for gateway credentials (Laws 275/313)",
            "Use infrastructure/security/field_encryption.py for secret columns",
            priority="P0", blocker="yes", laws=(275, 313),
            cluster="CLUSTER-payment-credentials", truth="L1", claim="INFERRED",
        ))
    return res
