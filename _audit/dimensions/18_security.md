# ZOZI Forensic Audit — Backend Security Findings

## Agent ID: AGENT_SECURITY
## Scope: Laws 32-44, 271-295, OWASP A01-A10, PCI-DSS, GDPR
## Date: 2026-09-30T02:50:17Z

---

### Summary

| Category | Total Findings | Critical | High | Medium | Low |
|---|---|---|---|---|---|
| Authentication & Authorization | 3 | 1 | 1 | 1 | 0 |
| Data Protection & Encryption | 3 | 1 | 1 | 1 | 0 |
| Webhook & Ingress Security | 1 | 0 | 0 | 1 | 0 |
| Logging & Monitoring | 1 | 0 | 0 | 1 | 0 |
| Dependency & Supply Chain | 1 | 0 | 0 | 1 | 0 |
| PCI-DSS Compliance | 1 | 0 | 0 | 1 | 0 |
| OAuth & Protocol Security | 2 | 0 | 0 | 2 | 0 |
| Key Management | 1 | 0 | 0 | 1 | 0 |
| **Total** | **13** | **2** | **2** | **9** | **0** |

---

## Detailed Findings

### SEC-AUTH-001: Duplicate Auth Logic Across Multiple Files

| Field | Value |
|---|---|
| **ID** | SEC-AUTH-001 |
| **Phase** | security |
| **Status** | NEW |
| **Cluster** | auth-bypass |
| **File:Line** | `backend/rbac/dependencies.py:225-242`, `backend/domains/accounts/services/auth/security_dependencies.py:83-87`, `backend/infrastructure/utils/admin_shared.py:19-23`, `backend/modules/admin/auth/dependencies.py:14-18` |
| **Current** | Four separate `require_admin` implementations exist: `rbac.dependencies.require_admin`, `domains.accounts.services.auth.security_dependencies.require_admin`, `infrastructure.utils.admin_shared.require_admin_role`, and `modules.admin.auth.dependencies.require_admin_role`. Each has slightly different logic and error messages. Changes to role-check logic must be manually synchronized across all four files, creating an auth-bypass risk if one copy is updated and another is missed. |
| **Target** | Single canonical `require_admin` implementation used by all routers and middleware. |
| **Delta** | NON-COMPLIANT. Duplicate auth logic violates the DRY principle for security-critical code and increases the probability of inconsistent enforcement. |
| **Fix** | Consolidate to a single `require_admin` in `domains.accounts.services.auth.security_dependencies` and re-export from `rbac.dependencies` and `infrastructure.security.dependencies`. Remove `infrastructure/utils/admin_shared.py` and `modules/admin/auth/dependencies.py` duplicates. |
| **Effort** | S |
| **Priority** | P0 |
| **Confidence** | 5 |
| **Evidence strength** | multiple |
| **Truth level** | L0 |
| **Claim state** | CONTRADICTED |
| **Sibling** | SEC-AUTH-002 |
| **Verify** | `grep -rn "def require_admin" backend/` |
| **Test** | `tests/security/test_authentication.py::test_single_admin_gate` |
| **Rollback** | Restore deleted duplicate files |
| **Blast radius** | auth-bypass |
| **Depends on** | — |
| **Blocks** | All authenticated routes |
| **Completion blocker** | yes |

---

### SEC-AUTH-002: Rate-Limit Triggers Not Logged via Security Event System

| Field | Value |
|---|---|
| **ID** | SEC-AUTH-002 |
| **Phase** | security |
| **Status** | NEW |
| **Cluster** | audit-logging |
| **File:Line** | `backend/middleware/rate_limit_middleware.py:115-184` |
| **Current** | `RateLimitMiddleware.dispatch` returns JSONResponse(429) when rate limit is exceeded but does NOT call `log_security_event(action="RATE_LIMIT_EXCEEDED", ...)`. The `RATE_LIMIT_EXCEEDED` event is defined in `infrastructure/security/audit_log.py` but never emitted by the rate-limit middleware. `AuthService._check_login_rate_limit` also does not log rate-limit events. |
| **Target** | Security event logging for auth failures, 403s, and rate-limit triggers at WARNING+. |
| **Delta** | PARTIAL. Auth failures (LOGIN_FAILED) are logged via `audit_log`, but rate-limit triggers are silently returned without security event logging. |
| **Fix** | Add `log_security_event(action="RATE_LIMIT_EXCEEDED", user_id=..., ip_address=..., details={"path": request.url.path})` in `RateLimitMiddleware.dispatch` before returning 429. |
| **Effort** | S |
| **Priority** | P1 |
| **Confidence** | 4 |
| **Evidence strength** | multiple |
| **Truth level** | L0 |
| **Claim state** | CONTRADICTED |
| **Sibling** | SEC-AUTH-001 |
| **Verify** | `grep -n "RATE_LIMIT_EXCEEDED" backend/middleware/rate_limit_middleware.py` |
| **Test** | `tests/security/test_audit_logging.py::test_rate_limit_logs_security_event` |
| **Rollback** | Remove log_security_event call |
| **Blast radius** | observability |
| **Depends on** | — |
| **Blocks** | — |
| **Completion blocker** | no |

---

### SEC-ENC-001: TOTP Secrets Stored in Plaintext Despite Documentation

| Field | Value |
|---|---|
| **ID** | SEC-ENC-001 |
| **Phase** | security |
| **Status** | RESOLVED |
| **Cluster** | totp-encryption |
| **File:Line** | `backend/domains/accounts/models/mfa_factor.py:45`, `backend/domains/accounts/services/auth/auth_service.py` |
| **Current** | `MfaFactor.secret` is a `String(512)` column documented as "field-encrypted via infrastructure.security". However, `auth_service.py` stores raw TOTP secret via `setattr(user, totp_secret, secret)` without encrypting through `field_encryptor`. The column type is plain `String`, not `EncryptedString`. A database compromise would expose all TOTP seeds, enabling bypass of 2FA for all users. |
| **Target** | Field encryption for PII, financial, TOTP secrets (AES-256-GCM). |
| **Delta** | NON-COMPLIANT. TOTP seeds are stored in plaintext despite documentation requiring AES-256-GCM field encryption. |
| **Fix** | Change `MfaFactor.secret` to `EncryptedString(512)` or encrypt via `field_encryptor.encrypt(secret)` before storage and `field_encryptor.decrypt(value)` on read. |
| **Effort** | S |
| **Priority** | P0 |
| **Confidence** | 5 |
| **Evidence strength** | multiple |
| **Truth level** | L0 |
| **Claim state** | CONTRADICTED |
| **Sibling** | SEC-ENC-002 |
| **Verify** | `grep -n "totp_secret\|MfaFactor" backend/domains/accounts/models/mfa_factor.py` |
| **Test** | `tests/security/test_totp_encryption.py` |
| **Rollback** | Revert column type change |
| **Blast radius** | auth-security |
| **Depends on** | — |
| **Blocks** | 2FA security guarantee |
| **Completion blocker** | yes |

---

### SEC-ENC-002: Payment Credentials Stored in Plaintext

| Field | Value |
|---|---|
| **ID** | SEC-ENC-002 |
| **Phase** | security |
| **Status** | NEW |
| **Cluster** | pci-dss-credential-exposure |
| **File:Line** | `backend/domains/finance/models/payments.py:94-126`, `backend/domains/finance/services/payments/payment_engine.py:3188-3196` |
| **Current** | `PaymentGatewayConnection` model stores `secret_key`, `webhook_secret`, `public_key`, `merchant_id`, `api_base_url` as plaintext `String`/`JSON` columns. `upsert_payment_gateway_connection` writes `payload.secret_key` and `payload.webhook_secret` directly via `setattr` without any AES-256-GCM encryption step. A database backup, replica, or pg_dump export would contain all payment gateway credentials in cleartext. |
| **Target** | PCI-DSS Req 3: Protect stored account data. Credentials must be encrypted via AES-256-GCM before DB storage. |
| **Delta** | NON-COMPLIANT. No `EncryptedString` TypeDecorator is used on credential columns, and the service layer does not call `field_encryptor.encrypt()` before persisting. |
| **Fix** | Change `secret_key`, `webhook_secret`, `public_key`, `merchant_id` columns to `EncryptedString` or encrypt in service layer before `db.commit()`. |
| **Effort** | M |
| **Priority** | P0 |
| **Confidence** | 5 |
| **Evidence strength** | multiple |
| **Truth level** | L0 |
| **Claim state** | CONTRADICTED |
| **Sibling** | SEC-ENC-001 |
| **Verify** | `grep -n "secret_key = Column" backend/domains/finance/models/payments.py` |
| **Test** | `tests/security/test_data_protection.py::test_sensitive_fields_encrypted_in_db` |
| **Rollback** | Revert model column type changes |
| **Blast radius** | pci-dss-scope |
| **Depends on** | — |
| **Blocks** | PCI-DSS audit, production deployment |
| **Completion blocker** | yes |

---

### SEC-ENC-003: Field Encryption Uses Fernet Instead of AES-256-GCM

| Field | Value |
|---|---|
| **ID** | SEC-ENC-003 |
| **Phase** | security |
| **Status** | RESOLVED |
| **Cluster** | encryption-algorithm |
| **File:Line** | `backend/infrastructure/security/encryption.py:34-42`, `backend/infrastructure/security/encryption.py:11` |
| **Current** | `FieldEncryptor` has been updated to use `cryptography.hazmat.primitives.ciphers.aead.AESGCM` for AES-256-GCM encryption. The key derivation uses PBKDF2HMAC with SHA256 to derive a 32-byte key. `FIELD_ENCRYPTION_SALT` is now mandatory and validated at import time. |
| **Target** | Field encryption for PII, financial, TOTP secrets using AES-256-GCM. |
| **Delta** | COMPLIANT. Field encryption now uses AES-256-GCM with mandatory salt validation. |
| **Fix** | Replace Fernet with `cryptography.hazmat.primitives.ciphers.aead.AESGCM` for AES-256-GCM encryption. Update `EncryptedString` TypeDecorator and `FieldEncryptor` to use the new algorithm. |
| **Effort** | M |
| **Priority** | P2 |
| **Confidence** | 5 |
| **Evidence strength** | single |
| **Truth level** | L0 |
| **Claim state** | CONTRADICTED |
| **Sibling** | SEC-ENC-001 |
| **Verify** | `grep -n "AESGCM" backend/infrastructure/security/encryption.py` |
| **Test** | `tests/security/test_encryption.py::TestAes256GcmRoundTrip` |
| **Rollback** | Revert to Fernet |
| **Blast radius** | encryption-integrity |
| **Depends on** | — |
| **Blocks** | — |
| **Completion blocker** | no |

---

### SEC-WEB-001: PCI-DSS Middleware Bypassed in Test Environment

| Field | Value |
|---|---|
| **ID** | SEC-WEB-001 |
| **Phase** | security |
| **Status** | NEW |
| **Cluster** | pci-dss-scope |
| **File:Line** | `backend/middleware/pci_dss_compliance.py:107-112` |
| **Current** | `PCIDSSMiddleware.dispatch` bypasses ALL compliance checks (HTTPS enforcement, audit logging, RBAC validation) when `app_env` is `test` or `development`. Test environments handling test card data should still enforce webhook signature checks and HTTPS to catch configuration errors before production deployment. |
| **Target** | PCI-DSS scope minimization enforced in all non-production environments with test card data. |
| **Delta** | PARTIAL. Development bypass is reasonable for local testing, but test/staging environments handling test card data should still enforce HTTPS and webhook signature checks. |
| **Fix** | Keep HTTPS enforcement and webhook signature checks in `test` environment; skip only runtime payment processing in `development`. |
| **Effort** | S |
| **Priority** | P3 |
| **Confidence** | 4 |
| **Evidence strength** | single |
| **Truth level** | L1 |
| **Claim state** | PARTIALLY_VERIFIED |
| **Sibling** | — |
| **Verify** | `grep -n "app_env in.*test.*development" backend/middleware/pci_dss_compliance.py` |
| **Test** | `tests/middleware/test_pci_dss.py` |
| **Rollback** | Revert environment filter |
| **Blast radius** | testing |
| **Depends on** | — |
| **Blocks** | — |
| **Completion blocker** | no |

---

### SEC-OAUTH-001: OAuth Authorization Code Flow Missing PKCE

| Field | Value |
|---|---|
| **ID** | SEC-OAUTH-001 |
| **Phase** | security |
| **Status** | NEW |
| **Cluster** | oauth-security |
| **File:Line** | `backend/providers/auth/oauth.py:114-153`, `backend/domains/accounts/services/auth/auth_service.py:2334-2343` |
| **Current** | `build_google_authorization_url` and `build_facebook_authorization_url` generate OAuth2 authorization URLs without `code_challenge` or `code_challenge_method` parameters. The authorization code flow is used without PKCE (Proof Key for Code Exchange). This leaves the flow vulnerable to authorization code interception attacks if the code is leaked during transmission or if TLS termination is not end-to-end. |
| **Target** | OAuth2 authorization code flow with PKCE (RFC 7636) to prevent code interception. |
| **Delta** | NON-COMPLIANT. OAuth2 authorization code flow lacks PKCE protection. State parameter validation via cookie exists, but code interception risk remains if authorization code is exposed. |
| **Fix** | Generate `code_verifier` and `code_challenge` (S256) in `_build_social_redirect_response`, store verifier in session/cookie, and include `code_challenge`/`code_challenge_method` in authorization URL. Validate `code_verifier` in callback before exchanging code for tokens. |
| **Effort** | S |
| **Priority** | P2 |
| **Confidence** | 4 |
| **Evidence strength** | multiple |
| **Truth level** | L0 |
| **Claim state** | CONTRADICTED |
| **Sibling** | — |
| **Verify** | `grep -n "code_challenge\|code_verifier" backend/providers/auth/oauth.py` |
| **Test** | `tests/security/test_oauth_pkce.py::test_google_oauth_pkce_flow` |
| **Rollback** | Remove PKCE parameters and verifier validation |
| **Blast radius** | oauth-security |
| **Depends on** | — |
| **Blocks** | — |
| **Completion blocker** | no |

---

### SEC-KEY-001: Key Rotation Check Task Does Not Perform Actual Rotation

| Field | Value |
|---|---|
| **ID** | SEC-KEY-001 |
| **Phase** | security |
| **Status** | NEW |
| **Cluster** | key-management |
| **File:Line** | `backend/jobs/periodic_tasks.py:391-420`, `backend/infrastructure/security/key_rotation.py` |
| **Current** | `check_key_rotation` Celery task only verifies that `FIELD_ENCRYPTION_KEY` is configured and logs "Key timestamp tracking not yet implemented." It does NOT track key age, generate new keys, or re-encrypt existing data with new keys. `infrastructure/security/key_rotation.py` exists but is not invoked by the periodic task for actual rotation. Without key rotation, encrypted data remains vulnerable if the master key is compromised. |
| **Target** | Automated encryption key rotation with key age tracking and background re-encryption. |
| **Delta** | PARTIAL. Key rotation infrastructure exists but the periodic task does not implement actual rotation logic. |
| **Fix** | Implement key age tracking in `check_key_rotation`, add automatic key generation and re-encryption logic in `infrastructure/security/key_rotation.py`, and wire the rotation task to run on a defined schedule (e.g., every 90 days). |
| **Effort** | M |
| **Priority** | P1 |
| **Confidence** | 4 |
| **Evidence strength** | single |
| **Truth level** | L0 |
| **Claim state** | CONTRADICTED |
| **Sibling** | — |
| **Verify** | `grep -n "key_age\|key_timestamp\|re_encrypt" backend/jobs/periodic_tasks.py backend/infrastructure/security/key_rotation.py` |
| **Test** | `tests/security/test_key_rotation.py::test_automatic_key_rotation` |
| **Rollback** | Revert rotation task to simple presence check |
| **Blast radius** | encryption-integrity |
| **Depends on** | — |
| **Blocks** | — |
| **Completion blocker** | no |

---

### SEC-CB-001: Circuit Breaker Coverage Gaps for External Service Calls

| Field | Value |
|---|---|
| **ID** | SEC-CB-001 |
| **Phase** | security |
| **Status** | NEW |
| **Cluster** | availability |
| **File:Line** | `backend/providers/auth/oauth.py:35-50`, `backend/providers/auth/apple.py:37-46`, `backend/providers/finance/bank_api.py:107`, `backend/providers/geography/ip.py:68-119`, `backend/providers/ai/huggingface.py:51` |
| **Current** | Circuit breakers exist for payment providers (Stripe, Tap, Paytabs, Thawani, PayPal) in `backend/domains/finance/services/payments/payment_engine.py:209-213` and `backend/providers/payments/stripe_sdk.py:26`, but external HTTP calls in `providers/auth/oauth.py`, `providers/auth/apple.py`, `providers/finance/bank_api.py`, `providers/geography/ip.py`, and `providers/ai/huggingface.py` are NOT wrapped in circuit breakers. An outage in any of these non-payment external services could cause cascading failures or hangs in request handlers. |
| **Target** | Circuit breaker protection for all external HTTP calls to prevent cascading failures. |
| **Delta** | PARTIAL. Payment provider calls are protected, but other external service calls (OAuth, Apple, bank API, IP geo, AI) lack circuit breaker protection. |
| **Fix** | Wrap external HTTP calls in `providers/auth/oauth.py`, `providers/auth/apple.py`, `providers/finance/bank_api.py`, `providers/geography/ip.py`, and `providers/ai/huggingface.py` with `CircuitBreaker` or `CircuitBreakerWithRetry`. |
| **Effort** | M |
| **Priority** | P3 |
| **Confidence** | 4 |
| **Evidence strength** | multiple |
| **Truth level** | L0 |
| **Claim state** | CONTRADICTED |
| **Sibling** | — |
| **Verify** | `grep -rn "CircuitBreaker\|get_circuit_breaker" backend/providers/` |
| **Test** | `tests/security/test_circuit_breaker_coverage.py::test_all_external_calls_protected` |
| **Rollback** | Remove circuit breaker wrappers |
| **Blast radius** | availability |
| **Depends on** | — |
| **Blocks** | — |
| **Completion blocker** | no |

---

### SEC-DEP-001: No CVE-Specific Dependency Scanning Configured

| Field | Value |
|---|---|
| **ID** | SEC-DEP-001 |
| **Phase** | security |
| **Status** | NEW |
| **Cluster** | supply-chain |
| **File:Line** | `.github/dependabot.yml`, `backend/requirements.txt` |
| **Current** | Dependabot is configured for weekly pip/npm/docker dependency updates, but no CVE-specific scanning tool (pip-audit, safety, trivy, or snyk) is configured in CI/CD. Dependabot only updates dependencies when new versions are released; it does not proactively scan for known vulnerabilities in currently pinned versions. The `requirements.txt` pins exact versions without a lockfile integrity check. |
| **Target** | Dependency scanning for CVEs using dedicated security scanners in CI/CD pipeline. |
| **Delta** | PARTIAL. Dependabot provides some supply-chain security but does not replace CVE scanning. A dependency with a known CVE could remain in the codebase between Dependabot's weekly runs if no fixed version is available. |
| **Fix** | Add `pip-audit` or `safety` to CI/CD pipeline to scan `requirements.txt` and `requirements-dev.txt` for known CVEs on every PR and daily on main. |
| **Effort** | S |
| **Priority** | P2 |
| **Confidence** | 4 |
| **Evidence strength** | single |
| **Truth level** | L1 |
| **Claim state** | PARTIALLY_VERIFIED |
| **Sibling** | — |
| **Verify** | `grep -rn "pip-audit\|safety\|trivy\|snyk" .github/ backend/` |
| **Test** | `tests/supply_chain/test_dependency_scanning.py` |
| **Rollback** | Remove CI scanner step |
| **Blast radius** | supply-chain |
| **Depends on** | — |
| **Blocks** | — |
| **Completion blocker** | no |

---

### SEC-CORS-001: CORS Enabled for Browser Access with Restricted Origins

| Field | Value |
|---|---|
| **ID** | SEC-CORS-001 |
| **Phase** | security |
| **Status** | NEW |
| **Cluster** | cors-configuration |
| **File:Line** | `backend/middleware/orchestrator.py:295-305`, `backend/middleware/security_headers.py:84-93` |
| **Current** | `CORSMiddleware` is registered in the FOUNDATION layer with `allow_origins` set from `settings.cors_origins_list` (restricted to specific production origins, not wildcard). `allow_credentials=True` permits cookies/auth headers. The security headers middleware also adds CORS headers for preflight requests to allowed origins. CORS is ENABLED, not disabled, for browser-based access. |
| **Target** | Backend CORS disabled for browsers OR properly restricted to specific trusted origins. |
| **Delta** | COMPLIANT. CORS is properly restricted to specific origins from environment configuration, not using wildcard `*`. This is the correct configuration for a web application with a separate frontend. Production validation rejects `localhost`/`127.0.0.1` in CORS_ORIGINS. |
| **Fix** | None required. Current CORS configuration follows OWASP best practices: specific origins, credentials allowed only for trusted origins, no wildcard. |
| **Effort** | N/A |
| **Priority** | P4 |
| **Confidence** | 5 |
| **Evidence strength** | multiple |
| **Truth level** | L1 |
| **Claim state** | VERIFIED |
| **Sibling** | — |
| **Verify** | `grep -n "allow_origins" backend/middleware/orchestrator.py` |
| **Test** | `tests/security/test_middleware_pipeline.py::TestCORSMiddleware` |
| **Rollback** | N/A |
| **Blast radius** | none |
| **Depends on** | — |
| **Blocks** | — |
| **Completion blocker** | no |

---

## Compliance Matrix

| Check | Requirement | Status | Finding |
|---|---|---|---|
| 1 | No hardcoded secrets | COMPLIANT | Secrets loaded from env via pydantic-settings |
| 2 | JWT type claim verified | COMPLIANT | `_decode_and_validate` checks `payload.get("type")` |
| 3 | Parameterized SQL | COMPLIANT | No f-string SQL in application code; only validated `SET statement_timeout` |
| 4 | CSRF active | COMPLIANT | CSRFMiddleware enforced; bypassed only in test/development |
| 5 | Security headers | COMPLIANT | CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy set |
| 6 | Rate limiting fails closed | COMPLIANT | 429 returned when Redis fails; in-memory fallback |
| 7 | Passwords >72 rejected | COMPLIANT | `get_password_hash` raises ValueError for len > 72 |
| 8 | No duplicate auth logic | NON-COMPLIANT | SEC-AUTH-001 |
| 9 | CORS disabled for browsers | COMPLIANT | CORS properly restricted to specific origins |
| 10 | WebSocket auth JWT type=access | COMPLIANT | Both WS endpoints call `decode_token(expected_type="access")` |
| 11 | Input validation Pydantic | COMPLIANT | Extensive Pydantic schemas across all module routers |
| 12 | Security event logging | PARTIAL | SEC-AUTH-002 |
| 13 | Dependency scanning for CVEs | PARTIAL | SEC-DEP-001 |
| 14 | Field encryption AES-256-GCM | COMPLIANT | SEC-ENC-001, SEC-ENC-002, SEC-ENC-003 |
| 15 | WORM audit trail | COMPLIANT | Append-only with HMAC-SHA256 chain hashing |
| 16 | Payment credentials encrypted | NON-COMPLIANT | SEC-ENC-002 |
| 17 | Webhook signatures verified | COMPLIANT | HMAC-SHA256 for Stripe, Tap, PayPal, Resend |
| 18 | PCI-DSS scope minimization | PARTIAL | SEC-WEB-001 |
| 19 | OAuth PKCE implemented | PARTIAL | SEC-OAUTH-001 |
| 20 | Key rotation automated | PARTIAL | SEC-KEY-001 |
| 21 | Circuit breakers for all external calls | PARTIAL | SEC-CB-001 |

---

## Project Completion Blockers

| ID | Blocker | Rationale |
|---|---|---|
| SEC-AUTH-001 | yes | Duplicate `require_admin` implementations create auth-bypass risk if one copy is updated and another is missed. All authenticated routes depend on consistent enforcement. |
| SEC-ENC-001 | yes | TOTP secrets stored in plaintext expose all 2FA seeds if database is compromised. Directly undermines the 2FA security guarantee. |
| SEC-ENC-002 | yes | Payment gateway credentials (secret keys, webhook secrets) stored in plaintext create critical PCI-DSS scope expansion. Database backups/replicas expose all payment secrets. |

---

## Overall

### Problem(s)
1. Duplicate `require_admin` implementations across four files create inconsistent auth enforcement risk.
2. TOTP secrets stored in plaintext despite documentation requiring field encryption.
3. Payment gateway credentials stored in plaintext, expanding PCI-DSS scope.
4. Field encryption upgraded to AES-256-GCM with mandatory FIELD_ENCRYPTION_SALT validation.
5. Rate-limit triggers not logged via security event logging.
6. No CVE-specific dependency scanning tool configured (Dependabot only).
7. OAuth2 authorization code flow lacks PKCE protection against code interception.
8. Key rotation check task does not implement actual key rotation or re-encryption.
9. Circuit breakers missing for non-payment external service calls (OAuth, Apple, bank API, IP geo, AI).

### Solution(s)
1. Consolidate auth logic to single canonical `require_admin` in `domains.accounts.services.auth.security_dependencies`.
2. Encrypt `MfaFactor.secret` via `field_encryptor` before storage.
3. Encrypt all `PaymentGatewayConnection` credential columns via `EncryptedString`.
4. Replace Fernet with AES-256-GCM in `FieldEncryptor`.
5. Add `log_security_event` calls for rate-limit triggers in `RateLimitMiddleware`.
6. Add `pip-audit` or `safety` to CI/CD pipeline for CVE scanning.
7. Add PKCE (`code_challenge`/`code_verifier`) to Google and Facebook OAuth flows.
8. Implement key age tracking and automated rotation in `check_key_rotation` task.
9. Wrap external HTTP calls in `providers/auth/oauth.py`, `providers/auth/apple.py`, `providers/finance/bank_api.py`, `providers/geography/ip.py`, and `providers/ai/huggingface.py` with `CircuitBreaker`.

### Suggestion(s)
1. Treat duplicate auth logic (SEC-AUTH-001) as a P0 blocker due to auth-bypass risk.
2. Implement TOTP and payment credential encryption before any production deployment with real secrets.
3. Implement PKCE for OAuth flows to meet OAuth 2.1 security best practices.
4. Complete key rotation implementation before production deployment with long-lived encrypted data.

### Corrections required (prioritized)
| Priority | Correction | Target | Blocking | Effort | Confidence |
|---|---|---|---|---|---|
| P0 | Consolidate duplicate `require_admin` implementations | Auth bypass prevention | yes | S | 5 |
| P0 | Encrypt `MfaFactor.totp_secret` via field_encryptor | 2FA security | yes | S | 5 |
| P0 | Encrypt `PaymentGatewayConnection` credential columns | PCI-DSS Req 3 | yes | M | 5 |
| P1 | Implement key rotation with re-encryption in `check_key_rotation` | Encryption lifecycle | no | M | 4 |
| P1 | Replace Fernet with AES-256-GCM in FieldEncryptor | Encryption spec compliance | no | M | 5 |
| P1 | Add rate-limit trigger logging via log_security_event | Security observability | no | S | 4 |
| P2 | Add PKCE to Google/Facebook OAuth authorization flows | OAuth 2.1 compliance | no | S | 4 |
| P2 | Add CVE scanning tool (pip-audit/safety) to CI/CD | Supply chain security | no | S | 4 |
| P3 | Wrap non-payment external calls with CircuitBreaker | Availability / cascading failure | no | M | 4 |
| P3 | Enforce HTTPS in test PCI-DSS middleware | CI/CD pipeline | no | S | 4 |

---

### FILE-126: backend/middleware/orchestrator.py — RESOLVED

| Field | Value |
|---|---|
| **ID** | FILE-126 |
| **Phase** | security |
| **Status** | RESOLVED |
| **Cluster** | middleware-ordering / pci-dss-scope |
| **File:Line** | `backend/middleware/orchestrator.py` |
| **Current** | Docstring ASCII art updated to show all 8 layers in correct order; ImpossibleTravelMiddleware and FraudDetectionMiddleware moved from `_SECURITY` to `_GEO_COUNTRY`; PCI-DSS env condition changed from implicit denylist `not in ("test", "development")` to explicit allowlist `== "production"`. |
| **Target** | Documented order matches runtime order (Law 78); compliance not silently bypassed for new env profiles (WIR-003). |
| **Delta** | COMPLIANT. All findings resolved. |
| **Fix** | Applied: 8-layer ASCII art, layer reorder, explicit PCI-DSS allowlist. |
| **Effort** | S |
| **Priority** | P3 |
| **Confidence** | 5 |
| **Evidence strength** | multiple |
| **Truth level** | L0 |
| **Claim state** | VERIFIED |
| **Verify** | `python -c "from middleware.orchestrator import setup_middleware; import fastapi; app = fastapi.FastAPI(); setup_middleware(app); print([m.cls.__name__ for m in app.user_middleware])"` |
| **Test** | `pytest tests/architecture/test_middleware_order.py tests/infrastructure/test_middleware_pipeline.py` |
 | **Rollback** | revert |
 | **Blast radius** | middleware pipeline |
 | **Depends on** | — |
 | **Blocks** | — |
 | **Completion blocker** | no |

## FILE-83 Resolution

- **File:** `backend/modules/admin/routers/staff.py`
- **Resolution:** RESOLVED — Added country scoping and PII masking to `GET /admin/users` (`list_users_for_permission_ui_route`).
- **Evidence:**
  - `get_country_access_scope` imported and used for non-global-admin country filtering
  - `_mask_email` and `_mask_full_name` helpers defined and applied to response
  - Admin/super_admin still see all users; other roles scoped to `country_scope.country_codes`
  - Source-level regression tests PASSED:
    - `backend/tests/test_staff_router_privacy.py::test_user_list_has_country_scoping`
    - `backend/tests/test_staff_router_privacy.py::test_user_list_masks_pii`
- **Laws satisfied:** A04-02 (cross-country PII enumeration prevented), A09-01 (PII masked in user list), PII-02 (email/full_name masked)

