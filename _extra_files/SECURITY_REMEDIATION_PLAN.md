# ZOZI Security Remediation Plan

**Scope:** Genuine security defects in `backend/` (auth, RLS, secrets/encryption, CORS, middleware), derived from `SYSTEM_AUDIT_REPORT.md` + direct source review.
**Status:** This session implements Tier-1 (CRITICAL/HIGH) fixes and adds regression tests. Architecture-debt findings (W1/CG1/DG layering) are documented as out-of-scope for security-only remediation.

---

## A. Problems with `SYSTEM_AUDIT_REPORT.md` itself

1. **SQL-injection rules are syntactically naive → massive false positives.**
   `SEC101` (8) and `SEC5` (33) flag *any* f-string/`text()` SQL that interpolates a variable, regardless of whether the value is user-controlled. Verified: **0 genuine SQL-injection sites** exist. Every interpolated value is a constant table name, a hardcoded column literal, a validated identifier (`_assert_safe_identifier`, `_validate_table_name`), or a bound `:param`. The audit cannot distinguish trusted from untrusted data flow.
2. **Architecture debt mislabeled as "violation".** `W1` (745 controller/router DB writes), `CG1` (109), `DG` (190) are layer-contract advisories for a large legacy recovery-era codebase — not security vulnerabilities. They should not be in the same severity bucket as RLS bypass or CORS `*`.
3. **No taint/trace analysis.** Findings never establish that external request input reaches a dangerous sink, so counts are inflated and untrustworthy for prioritisation.
4. **Missing genuine-security context.** The report under-weights the *real* issues that a taint analysis would surface: RLS fail-open, JWT revocation not enforced on one auth path, vault key reuse, KMS silent plaintext, CORS `*`+credentials.

**Conclusion:** Trust the report's *architecture* signal; do NOT trust its raw security counts. Genuine security work must be driven by data-flow review (done below), not by the violation tally.

---

## B. Current vs Required Security Structure (audit §2.4)

| Concern | Required (§2.4) | Current state | Gap |
|---|---|---|---|
| Auth deps | single `get_current_user`, jti revocation always enforced | `auth_controller.get_current_user` (verify_token ✓) **and** `utils/dependencies.get_current_user` (uses `decode_token` ✗ no blacklist) | revocation bypass on 2nd path |
| RLS | **one canonical enforcer**, fail-closed | `rls_interceptor.py` is the real enforcer, but `country_context.py` lets a staff user disable scoping via `X-Country-Code`/path | fail-open escalation |
| Secrets | dedicated keys, never reuse JWT `SECRET_KEY` | `vault.py` falls back to `secret_key` | key reuse |
| Encryption at rest | fail closed when key missing | `kms_encryption.py` returns **plaintext** when `KMS_MASTER_KEY` unset | silent data exposure |
| CORS | explicit origin allowlist, never `*`+credentials | `location_service/main.py` defaults `allow_origins="*"` + `allow_credentials=True` | CRITICAL misconfig |
| SECRET_KEY | required, refuses to start if empty | `config.py` already enforces at `Settings()` construction (✓ already fixed) | none — verified |

---

## C. Tier-1 Fixes implemented this session

| # | Severity | File | Fix |
|---|---|---|---|
| 1 | HIGH | `utils/auth.py` | Enforce `is_token_blacklisted` inside `decode_token` (closes revocation bypass in `utils/dependencies.get_current_user` and registration routers). |
| 2 | HIGH | `utils/vault.py` | Remove JWT `secret_key` fallback; vault key derives only from `ZOZI_VAULT_MASTER_KEY`/`field_encryption_key`. |
| 3 | HIGH | `utils/kms_encryption.py` | Raise `KMSEncryptionError` when `KMS_MASTER_KEY` unset instead of silently storing plaintext. |
| 4 | CRITICAL | `location_service/main.py` | Replace `*` default with explicit origins; disable credentials when wildcard is explicitly set. |
| 5 | CRITICAL | `middleware/country_context.py` | Harden non-admin RLS scope resolution: staff are **always** restricted to assigned countries; `X-Country-Code`/path country may only *narrow* to an assigned country, never disable scoping. Validate country codes via `normalize_country_code`. |
| 6 | MEDIUM | `utils/rls_interceptor.py` | Document it as THE canonical RLS enforcer; keep fail-closed `SecurityContextMissingError` when restricted-without-scope. |

## D. Tier-2 (documented, follow-up)

- Consolidate the two `get_current_user` implementations into one (dependencies reuse `verify_token`).
- Add HSTS preload + CSP `frame-ancestors` hardening (HSTS already wired via `settings.hsts_enabled`).
- Dedupe CSRF token generators (`utils/csrf.py` vs `utils/csrf_utils.py`).
- Unify the two rate-limit systems (middleware vs SlowAPI `utils/rate_limiter.py`).
- SSRF: require scheme allowlist + block metadata IPs for operator-supplied webhook `verify_url` (low risk — server-controlled today).
- Architecture debt (W1/CG1/DG): separate migration/refactor program; not a security fix.

## E. Testing

New regression suite `tests/test_security_hardening.py`:
- blacklist enforced via `decode_token` (revoked token rejected; valid token accepted).
- vault refuses to derive from JWT `secret_key`.
- KMS raises when key missing; encrypt/decrypt round-trips when key present.
- location_service CORS: no `*`+credentials; explicit origins honoured.
- RLS scope logic (`_compute_rls_scope`): staff restricted to assigned, header spoof ignored, customer unrestricted-by-country.
- RLS interceptor fail-closed raises `SecurityContextMissingError`.
- Re-run existing `tests/test_security.py` to confirm no regression.
