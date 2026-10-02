"""Dimension 18 (security) — OWASP A01-A10 + platform security laws."""
from __future__ import annotations

import re

from zz_core.model import CheckResult, Finding, Observation, ScanContext
from zz_core.registry import check
from zz_core.util import read_text

CORE_DIRS = ("domains", "modules", "rbac", "kernel", "infrastructure",
             "providers", "jobs", "middleware")


def _f(phase, file, line, current, target, fix, *, priority="P1",
       effort="M", laws=(), blocker="partial", cluster="", truth="L0",
       claim="VERIFIED", evidence="multiple") -> Finding:
    return Finding(
        id="", dimension="18_security", phase=phase, cluster=cluster, file=file,
        line=line, current=current, target=target, delta=current[:180], fix=fix,
        effort=effort, priority=priority, confidence=4, evidence_strength=evidence,
        truth_level=truth, claim_state=claim, completion_blocker=blocker,
        laws=laws, origin="static",
    )


@check("sec_secrets_and_encryption", "18_security", "security",
       "Hardcoded secrets, field-encryption coverage, PCI scope, .env tracked, "
       "webhook secrets (Laws 32, 275, 313).")
def sec_secrets_and_encryption(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="sec_secrets_and_encryption", dimension="18_security")
    secret_rx = re.compile(
        r"(?i)\b(password|passwd|secret|api_key|apikey|access_key|auth_token|client_secret)\b"
        r"\s*[:=]\s*[\"'][^\"'\s]{10,}[\"']")
    placeholder = re.compile(r"(?i)change.?me|placeholder|example|dummy|xxx|<.*>|your[-_ ]")
    hits: list[tuple[str, int, str]] = []
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if not any(rel.startswith(f"backend/{d}/") for d in CORE_DIRS):
            continue
        if "/tests/" in rel:
            continue
        text, _ = read_text(p)
        if not text:
            continue
        for idx, line in enumerate(text.splitlines(), 1):
            if secret_rx.search(line) and not placeholder.search(line):
                hits.append((rel, idx, line.strip()[:160]))
    if hits:
        res.findings.append(_f(
            "security", hits[0][0], hits[0][1],
            f"{len(hits)} hardcoded secret-like literal(s); first: `{hits[0][2]}`",
            "secrets come from env/secrets manager only (Law 32)",
            "Move the literal into Coolify env vars and rotate it",
            priority="P0", blocker="yes", laws=(32,),
            cluster="CLUSTER-hardcoded-secret",
            verify=f"grep -nE '(password|secret|api_key)=' {hits[0][0]}",
        ))
    # .env tracked by git?
    import subprocess, sys
    try:
        out = subprocess.run(["git", "ls-files", ".env", "backend/.env",
                              "frontend/web_app/.env.local"],
                             cwd=str(ctx.root), capture_output=True, text=True, timeout=30)
        tracked = [l for l in (out.stdout or "").splitlines() if l.strip()]
        if tracked:
            res.findings.append(_f(
                "security", tracked[0], 0,
                f"secret-bearing file(s) tracked in git: {', '.join(tracked)}",
                "env files are dev-only and never committed (Law 204)",
                "git rm --cached the file, rotate its secrets, add to .gitignore",
                priority="P0", blocker="yes", laws=(32, 204),
                cluster="CLUSTER-env-committed", origin="tool",
            ))
    except Exception:
        pass
    # field encryption coverage for payment secrets
    pay_models = [p for p in (ctx.backend / "domains").rglob("*.py")
                  if "payment" in p.name and "model" in ctx.rel(p)]
    for p in pay_models:
        text, _ = read_text(p)
        if text and re.search(r"(secret_key|webhook_secret|credentials)\s*[:=]", text) \
                and "EncryptedString" not in text and "encrypt" not in text.lower():
            res.findings.append(_f(
                "payment", ctx.rel(p), 1,
                "payment gateway secret field(s) stored without field encryption",
                "AES-256-GCM encryption for gateway credentials (Laws 275/313)",
                "Use infrastructure/security/field_encryption.py EncryptedString",
                priority="P0", blocker="yes", laws=(275, 313),
                cluster="CLUSTER-payment-credentials",
            ))
    # WORM mutation
    for p in (ctx.backend / "domains" / "audit").rglob("*.py"):
        text, _ = read_text(p)
        if text and re.search(r"UPDATE\s+audit|\.update\(\s*\{[^}]*worm", text, re.IGNORECASE):
            res.findings.append(_f(
                "logic", ctx.rel(p), 1,
                "audit trail mutates rows after INSERT (UPDATE on audit table)",
                "WORM: write-once, never UPDATE (Laws 278)",
                "Compute the chain hash before INSERT; drop the post-insert UPDATE",
                priority="P1", blocker="partial", laws=(278,),
                cluster="CLUSTER-worm", truth="L1", claim="INFERRED",
            ))
    return res


@check("sec_injection_and_ssrf", "18_security", "security",
       "SQL injection (f-string SQL), SSRF (outbound URL validation), command "
       "injection, unsafe deserialization (OWASP A03/A10).")
def sec_injection_and_ssrf(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="sec_injection_and_ssrf", dimension="18_security")
    fstring_sql: list[tuple[str, int, str]] = []
    ssrf: list[tuple[str, int, str]] = []
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if not any(rel.startswith(f"backend/{d}/") for d in CORE_DIRS):
            continue
        text, _ = read_text(p)
        if not text:
            continue
        for idx, line in enumerate(text.splitlines(), 1):
            if re.search(r"(text|execute|executemany)\(\s*f[\"']", line) or \
               re.search(r"(SELECT|INSERT|UPDATE|DELETE).*\{.*\}.*[\"']\s*\)", line):
                fstring_sql.append((rel, idx, line.strip()[:160]))
            if re.search(r"(urlopen|httpx\.(get|post|stream)|requests\.(get|post))\(\s*[a-z_]", line):
                ctx_window = "\n".join(text.splitlines()[max(0, idx - 6):idx + 3])
                if not re.search(r"require_safe_url|is_safe_url|validate_url|allowlist|allow_list", ctx_window):
                    ssrf.append((rel, idx, line.strip()[:160]))
    if fstring_sql:
        res.findings.append(_f(
            "security", fstring_sql[0][0], fstring_sql[0][1],
            f"{len(fstring_sql)} f-string SQL site(s); first: `{fstring_sql[0][2]}`",
            "parameterized SQL only (Law 34)",
            "Replace with text() + bound parameters",
            priority="P0", blocker="yes", laws=(34,),
            cluster="CLUSTER-sql-injection",
        ))
    if ssrf:
        res.findings.append(_f(
            "security", ssrf[0][0], ssrf[0][1],
            f"{len(ssrf)} caller-influenced outbound URL call(s) without safe-URL guard; "
            f"first: `{ssrf[0][2]}`",
            "outbound URLs validated against private ranges (SSRF defense)",
            "Wrap calls in require_safe_url()/allowlist validation",
            priority="P0", blocker="yes", cluster="CLUSTER-ssrf",
            truth="L1", claim="INFERRED",
        ))
    return res


@check("sec_auth_hardening", "18_security", "security",
       "JWT type checks, CSRF, security headers, password length, rate-limit "
       "fail-closed, MFA enforcement, CAPTCHA fail-open, cookie/debug posture.")
def sec_auth_hardening(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="sec_auth_hardening", dimension="18_security")
    auth_text, _ = read_text(ctx.backend / "infrastructure" / "security" / "auth.py")
    decode_calls = re.findall(r"decode_token\([^)]*\)", auth_text or "")
    no_type = [c for c in decode_calls if "expected_type" not in c and "verify" not in c]
    if no_type:
        res.findings.append(_f(
            "security", "backend/infrastructure/security/auth.py", 1,
            f"{len(no_type)} decode_token call(s) without explicit type verification",
            "all JWT decoders verify the type claim (Law 33)",
            "Pass expected_type on every decode",
            priority="P1", laws=(33,), cluster="CLUSTER-jwt",
        ))
    turnstile, _ = read_text(ctx.backend / "infrastructure" / "security" / "dependencies.py")
    if turnstile and re.search(r"TURNSTILE_SECRET_KEY", turnstile) and re.search(r"if not .*TURNSTILE|return True|skip", turnstile):
        res.findings.append(_f(
            "security", "backend/infrastructure/security/dependencies.py", 1,
            "CAPTCHA verification short-circuits when TURNSTILE_SECRET_KEY is unset",
            "bot protection fails closed (Law 281)",
            "Fail closed or require the key in production",
            priority="P1", blocker="partial", laws=(281,),
            cluster="CLUSTER-captcha", truth="L1", claim="INFERRED",
        ))
    # MFA enforcement for admin login
    mfa = False
    for p in (ctx.backend / "domains" / "accounts").rglob("*.py"):
        text, _ = read_text(p)
        if text and re.search(r"(admin|employee).*(totp|mfa)|(totp|mfa).*(admin|employee)", text, re.IGNORECASE | re.DOTALL):
            mfa = True
            break
    if not mfa:
        res.findings.append(_f(
            "security", "backend/domains/accounts/", 0,
            "no code path enforces MFA for admin/employee roles",
            "TOTP MFA enforced for admin/employee (Law 283)",
            "Require TOTP at login for privileged roles",
            priority="P1", blocker="partial", laws=(283,),
            cluster="CLUSTER-mfa", truth="L1", claim="INFERRED",
        ))
    # debug/cookie posture
    cfg, _ = read_text(ctx.backend / "config.py")
    if re.search(r"debug[^=]*=\s*Field\([^)]*default\s*=\s*True", cfg or ""):
        res.findings.append(_f(
            "security", "backend/config.py", 0,
            "DEBUG defaults to True",
            "debug=False in production (Law 205)",
            "Default debug to False",
            priority="P1", laws=(205,), cluster="CLUSTER-debug",
        ))
    res.facts["jwt_decode_calls"] = len(decode_calls)
    return res


@check("sec_access_control", "18_security", "security",
       "Broad RBAC grants (wildcards), admin surfaces, unauthorized ws, PII in "
       "non-admin responses (OWASP A01).")
def sec_access_control(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="sec_access_control", dimension="18_security")
    dep, _ = read_text(ctx.backend / "rbac" / "dependencies.py")
    wildcards = re.findall(r"[\"']([\w]+)[\"']\s*:\s*\[\s*[\"']\*[\"']", dep or "")
    if wildcards:
        res.observations.append(Observation(
            "file", "rbac-wildcards", "backend/rbac/dependencies.py", 0,
            "18_security",
            evidence=f"roles with full wildcard: {', '.join(wildcards)}",
        ))
    # unauthenticated websocket (delegated to wiring check but repeat cheaply)
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if "/routers/" not in rel:
            continue
        text, _ = read_text(p)
        if not text:
            continue
        for m in re.finditer(r"async def (\w*websocket\w*)\(([^)]*)\):", text):
            name = m.group(1)
            line = text[:m.start()].count("\n") + 1
            window = text[m.start():m.start() + 1500]
            if "accept()" in window and "decode_token" not in window and "get_current_user" not in window:
                res.findings.append(_f(
                    "security", rel, line,
                    f"websocket `{name}` accepts without token verification",
                    "WebSocket auth verifies access token (Law 41)",
                    "Verify JWT before accept()",
                    priority="P0", blocker="yes", laws=(41,),
                    cluster="CLUSTER-ws-auth",
                ))
    return res
