```
=== AGENT LOG ===
PHASE: 09 — Authentication / Authorization Security Audit
STATUS: COMPLETED
REPORT_FILE: _audit/findings/PHASE_09_AUTH_SECURITY.md
SCOPE_COVERED: Registration, login (5 staff "doors" + customer), logout, sessions,
  refresh-token rotation, JWT signing/verification, password hashing, password
  reset/change, email verification gate, TOTP MFA, OAuth/social login, RBAC
  roles/permissions, admin guard, CSRF, cookie flags, brute-force lockout.
FILES_EXAMINED: ~18
EVIDENCE_ITEMS: 55+
FINDINGS_TOTAL: 14  (VERIFIED: 12 / INFERRED: 1 / UNKNOWN: 1)
SEVERITY_BREAKDOWN: BLOCKER: 1 / HIGH: 1 / MEDIUM: 5 / LOW: 4 / INFO: 3
TOP_FINDINGS:
  1. Unauthenticated privilege escalation via `role` mass-assignment on POST /api/v1/auth/register — backend/modules/customer/routers/accounts.py:317 + backend/infrastructure/database/schemas.py:1657 + backend/domains/accounts/services/auth/auth_service.py:2404
  2. Known/committed default SECRET_KEY not rejected by production guard (HS256 forge) — backend/config.py:31 + backend/config.py:214 + backend/infrastructure/security/auth.py:192
  3. Password reset/change do not invalidate existing JWTs/refresh families — backend/domains/accounts/services/auth/auth_service.py:3146,3101
  4. Password-reset tokens stored in plaintext (OTP is hashed; reset is not) — backend/domains/accounts/services/auth/auth_service.py:3126
  5. TOTP secrets stored in plaintext (no field encryption) — backend/domains/accounts/services/auth/auth_service.py:3260
GAPS / NOT DETERMINABLE:
  - Actual production deployment env values for SECRET_KEY / APP_ENV (repo-only view).
  - Reachability/mounting of staff SSO door (`authenticate_sso`) to an HTTP route.
  - Runtime Redis availability (affects brute-force + blacklist fail-open/closed).
SELF_SKEPTICISM_RATING: 5
=== END AGENT LOG ===
```

# PHASE 09 — Authentication / Authorization Security Audit

> Forensic, evidence-based. Every claim cites `file:line`. Labels:
> **VERIFIED** (confirmed from source), **INFERRED** (strongly suggested),
> **UNKNOWN** (insufficient evidence). Severity per MASTER_RULES §16.
> Classification per §15: *confirmed vulnerability* / *security weakness* /
> *potential risk requiring verification*. No secret values are reproduced.

## Scope & method

Identity/access-control only. Traced actual call paths:
- Customer auth routes: [backend/modules/customer/routers/accounts.py](../../backend/modules/customer/routers/accounts.py)
- Admin auth routes: [backend/modules/admin/routers/accounts.py](../../backend/modules/admin/routers/accounts.py)
- Auth service (customer + 5 staff "doors"): [backend/domains/accounts/services/auth/auth_service.py](../../backend/domains/accounts/services/auth/auth_service.py)
- Core JWT/password/blacklist primitives: [backend/infrastructure/security/auth.py](../../backend/infrastructure/security/auth.py)
- Dependencies/RBAC: [backend/domains/accounts/services/auth/security_dependencies.py](../../backend/domains/accounts/services/auth/security_dependencies.py), [backend/rbac/dependencies.py](../../backend/rbac/dependencies.py), [backend/infrastructure/security/dependencies.py](../../backend/infrastructure/security/dependencies.py)
- Middleware: [backend/middleware/authentication_middleware.py](../../backend/middleware/authentication_middleware.py), [backend/middleware/admin_guard_middleware.py](../../backend/middleware/admin_guard_middleware.py), [backend/middleware/csrf_middleware.py](../../backend/middleware/csrf_middleware.py)
- Config/schemas: [backend/config.py](../../backend/config.py), [backend/infrastructure/database/schemas.py](../../backend/infrastructure/database/schemas.py)

---

## FINDING 01 — Unauthenticated vertical privilege escalation via `role` mass-assignment on registration
- **Severity:** BLOCKER
- **Classification:** Confirmed vulnerability
- **Status:** VERIFIED
- **Confidence:** High
- **Affected endpoint:** `POST /api/v1/auth/register` (also `POST /api/v1/auth/register-form`)
- **Affected functions:** `auth_register` → `json_register_user` → `register_user`

### Evidence
- Route is public (no auth dependency), explicitly documented as such:
  [backend/modules/customer/routers/accounts.py:317](../../backend/modules/customer/routers/accounts.py#L317) — `@router.post("/api/v1/auth/register", ...)`; docstring "Public endpoint — no authentication required" ([:326](../../backend/modules/customer/routers/accounts.py#L326)); body typed `user_data: UserCreate` ([:321](../../backend/modules/customer/routers/accounts.py#L321)).
- `UserCreate.role` is an unconstrained free string (no `Enum`, no validator):
  [backend/infrastructure/database/schemas.py:1657](../../backend/infrastructure/database/schemas.py#L1657) — `role: Optional[str] = "customer"`.
  Same for `RegisterRequest.role` ([backend/infrastructure/database/schemas.py:92](../../backend/infrastructure/database/schemas.py#L92)) and [backend/domains/accounts/schemas/user_schemas.py:46](../../backend/domains/accounts/schemas/user_schemas.py#L46).
- `register_user` persists the client-supplied role verbatim with no allow-list:
  [backend/domains/accounts/services/auth/auth_service.py:2404](../../backend/domains/accounts/services/auth/auth_service.py#L2404) — `role=user.role`. Only `supplier` gets extra validation ([:2361](../../backend/domains/accounts/services/auth/auth_service.py#L2361)); `admin`/`super_admin`/`employee`/`staff` pass through with only email-uniqueness + password-complexity checks.
- `json_register_user` immediately issues a working access token for the new account:
  [backend/domains/accounts/services/auth/auth_service.py:2843](../../backend/domains/accounts/services/auth/auth_service.py#L2843).
- Downstream authorization then honors the DB role: `require_admin` checks `user.role in ("admin","super_admin")` from the ORM object ([backend/domains/accounts/services/auth/security_dependencies.py:85](../../backend/domains/accounts/services/auth/security_dependencies.py#L85)); admin routes use it ([backend/modules/admin/routers/accounts.py:313](../../backend/modules/admin/routers/accounts.py#L313)). On login, the JWT `role` claim is minted from the DB role ([auth_service.py:2062](../../backend/domains/accounts/services/auth/auth_service.py#L2062)), so `AdminGuardMiddleware` ([admin_guard_middleware.py:96](../../backend/middleware/admin_guard_middleware.py#L96)) also passes.

### Attack scenario (defensive description)
An unauthenticated attacker sends a normal registration request to `POST /api/v1/auth/register` with the JSON `role` field set to `admin` (or `super_admin`). The account is created with that role and a valid access token is returned. On the next login the JWT carries `role=admin`; both the per-route `require_admin` (DB role) and the server-side admin guard (JWT role) accept the account, granting full admin-console access (user management, role assignment, force password reset, hard delete, finance operations).

### Impact
Full, unauthenticated vertical privilege escalation to the highest role. Complete compromise of the administrative surface.

### Remediation
- Never accept `role` from a public request. Force `role="customer"` (or an explicit self-service allow-list `{customer, supplier}`) inside `register_user`; ignore/reject any other client value.
- Constrain `role` in the schema to an `Enum`/`Literal` and reject privileged values for public endpoints.
- Assign privileged roles only through an authenticated admin path (which already exists: `update_user_role` behind `require_admin`, [backend/modules/admin/routers/accounts.py:352](../../backend/modules/admin/routers/accounts.py#L352)).

---

## FINDING 02 — Known/committed default `SECRET_KEY` accepted by production guard (JWT forgery)
- **Severity:** HIGH
- **Classification:** Security weakness (confirmed gap in the guard); exploitability depends on deployment env
- **Status:** VERIFIED (code) / INFERRED (real deployments)
- **Confidence:** High (code), Medium (exploitability)
- **Affected functions:** `Settings.__init__` validation; `create_access_token` / `_decode_and_validate`

### Evidence
- Hardcoded fallback secret committed to the repo:
  [backend/config.py:31](../../backend/config.py#L31) — `"secret_key": os.getenv("SECRET_KEY", "zozi-dev-secret-key-change-in-production-2026")`.
- Production validation rejects only *empty* and a small placeholder set that does **not** include the default above:
  [backend/config.py:214-224](../../backend/config.py#L214) — blocklist is `{"change-me-in-production","change-me","changeme","secret","secret-key","default"}`. The committed default `zozi-dev-secret-key-...` is non-empty and not in the set, so it **passes** the production guard.
- JWTs are HS256 (symmetric — the signing secret is also the verification secret):
  [backend/config.py:32](../../backend/config.py#L32) `"algorithm": "HS256"`; sign at [backend/infrastructure/security/auth.py:199](../../backend/infrastructure/security/auth.py#L199); verify at [:289](../../backend/infrastructure/security/auth.py#L289), [:314](../../backend/infrastructure/security/auth.py#L314), [:346](../../backend/infrastructure/security/auth.py#L346).

### Attack scenario
If a production deployment does not set the `SECRET_KEY` env var, the app boots with the repository-known secret (validation does not stop it). Because HS256 is symmetric, anyone possessing that secret can forge a valid access token, e.g. `{"sub":"1","type":"access","role":"admin","jti":...,"exp":...}`. `get_current_user` loads user id 1 (a guessable admin id) and `require_admin` passes on the real DB role — yielding admin access without credentials. Even absent a real admin at that id, forged tokens satisfy any bearer-authenticated endpoint.

### Impact
Complete authentication bypass / privilege escalation if the default secret is ever in effect in a non-dev environment.

### Remediation
- Add the committed default (and any `*dev*`, `*change*`, `*example*` patterns / low-entropy values) to the production rejection list, or require a minimum entropy/length. Fail hard when `secret_key == _DEFAULTS["secret_key"]` in production.
- Do not ship a usable default secret in source; require the env var unconditionally in production.

---

## FINDING 03 — Password reset / change do not invalidate existing sessions or tokens
- **Severity:** MEDIUM
- **Classification:** Security weakness
- **Status:** VERIFIED
- **Confidence:** High
- **Affected functions:** `reset_password`, `change_password`, admin `force_reset_password`

### Evidence
- `reset_password` sets a new hash and marks the token used, but never blacklists access tokens or revokes the refresh family:
  [backend/domains/accounts/services/auth/auth_service.py:3146-3175](../../backend/domains/accounts/services/auth/auth_service.py#L3146).
- `change_password` likewise re-hashes and commits with no token revocation:
  [backend/domains/accounts/services/auth/auth_service.py:3101-3115](../../backend/domains/accounts/services/auth/auth_service.py#L3101).
- Revocation primitives exist but are not called here: `blacklist_token` / `revoke_refresh_family` ([backend/infrastructure/security/auth.py:79](../../backend/infrastructure/security/auth.py#L79), [:239](../../backend/infrastructure/security/auth.py#L239)).

### Attack scenario
A victim resets their password after suspecting compromise (or an attacker resets it). Tokens issued before the change remain valid — access tokens up to `access_token_expire_minutes` (15) and refresh tokens up to `refresh_token_expire_days` (7) ([backend/config.py:34-35](../../backend/config.py#L34)). An attacker holding a pre-reset refresh token can continue to mint access tokens for up to 7 days.

### Impact
Credential change does not evict active sessions — undermines the primary account-recovery control.

### Remediation
On password reset/change (and admin force-reset), revoke the user's refresh families and/or bump a per-user token epoch/`token_version` claim checked at decode time; blacklist outstanding access JTIs where tracked.

---

## FINDING 04 — Password-reset tokens stored in plaintext (inconsistent with OTP hashing)
- **Severity:** MEDIUM
- **Classification:** Security weakness + contradiction
- **Status:** VERIFIED
- **Confidence:** High
- **Affected functions:** `forgot_password`, `reset_password`, `create_password_reset_token`

### Evidence
- Reset token generated with a strong RNG but persisted **as-is**:
  [backend/domains/accounts/services/auth/auth_service.py:3126-3135](../../backend/domains/accounts/services/auth/auth_service.py#L3126) — `raw_token = secrets.token_urlsafe(32)` then `PasswordResetToken(token=raw_token, ...)`.
- Lookup compares the raw token directly: [auth_service.py:3151-3157](../../backend/domains/accounts/services/auth/auth_service.py#L3151).
- **Contradiction:** OTP codes in the same domain are bcrypt-hashed at rest (`code_hash=get_password_hash(code)`, [auth_service.py](../../backend/domains/accounts/services/auth/auth_service.py) OTP section) — reset tokens are not.

### Attack scenario
Read access to the `password_reset_tokens` table (SQLi, backup leak, insider) yields directly usable reset tokens for any user with an outstanding request (TTL 1h, [backend/infrastructure/utils/constants.py:78](../../backend/infrastructure/utils/constants.py#L78)), enabling account takeover without email access.

### Impact
DB compromise escalates to account takeover for accounts with live reset tokens.

### Remediation
Store only a hash (e.g. SHA-256) of the reset token; look up by hash. Keep the short TTL and single-use marking already present (good).

---

## FINDING 05 — TOTP (MFA) secrets stored in plaintext
- **Severity:** MEDIUM
- **Classification:** Security weakness
- **Status:** VERIFIED
- **Confidence:** High
- **Affected functions:** `setup_totp`, `enable_totp`, staff MFA enroll

### Evidence
- Column is plain `String`: [backend/alembic/versions/2026_08_06_0003-...baseline_sync_orm_tables.py:6199](../../backend/alembic/versions/2026_08_06_0003-20260806_0003_baseline_sync_orm_tables.py#L6199) — `sa.Column('totp_secret', sa.String(), nullable=True)`.
- Secret assigned directly (no encryption): [backend/domains/accounts/services/auth/auth_service.py:3260](../../backend/domains/accounts/services/auth/auth_service.py#L3260) and [:4373](../../backend/domains/accounts/services/auth/auth_service.py#L4373).
- A field-encryption facility exists in config but is not applied to `totp_secret` ([backend/config.py](../../backend/config.py) `field_encryption_key*`).

### Attack scenario
DB read access exposes TOTP shared secrets; an attacker can compute valid TOTP codes for any MFA-enabled account, neutralizing the second factor (and the admin step-up 2FA at [auth_service.py:3367](../../backend/domains/accounts/services/auth/auth_service.py#L3367)).

### Impact
MFA provides no protection against a database compromise.

### Remediation
Encrypt `totp_secret` at rest using the existing field-encryption key (envelope/KMS), or store it in a secrets manager. Encrypt/HMAC recovery codes similarly.

---

## FINDING 06 — Registration issues a usable access token before email verification
- **Severity:** MEDIUM
- **Classification:** Security weakness / contradiction (config-dependent)
- **Status:** VERIFIED
- **Confidence:** Medium (depends on `customer_email_verification_mode`)
- **Affected functions:** `json_register_user` vs `json_login_user`/`login_user`

### Evidence
- Registration mints tokens immediately, with no verification check:
  [backend/domains/accounts/services/auth/auth_service.py:2837-2861](../../backend/domains/accounts/services/auth/auth_service.py#L2837).
- Login enforces an email-verification gate for customers:
  [auth_service.py:2673-2678](../../backend/domains/accounts/services/auth/auth_service.py#L2673) and [:2749-2754](../../backend/domains/accounts/services/auth/auth_service.py#L2749).
- Mode is config-driven, default `auto` (gate off): [backend/config.py:80](../../backend/config.py#L80) `"customer_email_verification_mode": "auto"`.

### Attack scenario
When the platform is set to `required` verification, the login path blocks unverified customers — but the register path already returned a valid token, so the attacker/user simply uses that token and never logs in, bypassing the verification gate for the token's lifetime (and refreshing it).

### Impact
The email-verification control is inconsistently enforced; unverified accounts can access authenticated endpoints when verification is supposed to be mandatory.

### Remediation
Do not issue session tokens from registration when verification is required; return a "verify your email" response instead. Or enforce `email_verified` inside `get_current_user`/a dependency (single choke point) rather than only at login.

---

## FINDING 07 — `/api/v1/auth/me` unconditionally skips the token blacklist
- **Severity:** MEDIUM (leaning LOW — read-only)
- **Classification:** Security weakness
- **Status:** VERIFIED
- **Confidence:** High
- **Affected endpoint:** `GET /api/v1/auth/me`

### Evidence
- [backend/modules/customer/routers/accounts.py:246](../../backend/modules/customer/routers/accounts.py#L246) — `decode_token(credentials.credentials, expected_type="access", check_blacklist=False)`. The inline comment says "Skip blacklist check in development", but the flag is hardcoded `False` for all environments.
- `decode_token` honors the flag: [backend/infrastructure/security/auth.py:344-357](../../backend/infrastructure/security/auth.py#L344).
- The endpoint returns identity fields (`id`, `role`, `email`) straight from the JWT claims ([customer/routers/accounts.py:248-252](../../backend/modules/customer/routers/accounts.py#L248)).

### Attack scenario
After logout (which blacklists the access JTI, [auth_service.py:2985](../../backend/domains/accounts/services/auth/auth_service.py#L2985)) or admin token revocation, the still-unexpired access token is rejected everywhere except `/auth/me`, which continues to confirm the session and echo identity.

### Impact
Revocation bypass for a read-only identity endpoint; weakens "log out everywhere" guarantees. Low direct damage (no state change) but a correctness/logout-integrity gap.

### Remediation
Remove `check_blacklist=False` (or gate it strictly on `app_env in {development,test}`). Prefer resolving `/me` through the shared `get_current_user` dependency so all checks apply uniformly.

---

## FINDING 08 — CSRF-exempt, cookie-reading endpoints (`/auth/refresh`, `/auth/logout`)
- **Severity:** LOW
- **Classification:** Potential risk
- **Status:** VERIFIED
- **Confidence:** Medium
- **Affected endpoints:** `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout`

### Evidence
- Both are in the CSRF exemption list: [backend/middleware/csrf_middleware.py:28-32](../../backend/middleware/csrf_middleware.py#L28).
- Both read the refresh token from the cookie: `request.cookies.get(settings.refresh_token_cookie_name)` — refresh at [auth_service.py:2771](../../backend/domains/accounts/services/auth/auth_service.py#L2771), logout at [auth_service.py:3007](../../backend/domains/accounts/services/auth/auth_service.py#L3007).
- In production the refresh cookie is forced to `SameSite=None` (so it is sent cross-site): [backend/config.py:228-231](../../backend/config.py#L228). Cookie is `HttpOnly`+`Secure(prod)` ([auth_service.py:2815-2820](../../backend/domains/accounts/services/auth/auth_service.py#L2815)).

### Attack scenario
A malicious site auto-submits `POST /auth/logout` (CSRF-forced logout) or `POST /auth/refresh` (forced token rotation) using the victim's ambient refresh cookie. The rotated access token in the response body cannot be read cross-origin (Same-Origin Policy / CORS), so token theft is not achieved; impact is limited to nuisance logout and refresh churn.

### Impact
Cross-site forced logout and refresh-token rotation. No token exfiltration. Note: primary authorization uses the `Authorization: Bearer` header ([security_dependencies.py:41](../../backend/domains/accounts/services/auth/security_dependencies.py#L41)), which is not attachable cross-site, so state-changing APIs remain CSRF-resistant.

### Remediation
Require a CSRF token (or an `Origin`/`Sec-Fetch-Site` check) on the cookie-reading `refresh`/`logout` endpoints, or bind refresh to a header/body value in addition to the cookie.

---

## FINDING 09 — Inconsistent JWT `role` claim across issuance paths undermines the admin-guard's defense-in-depth
- **Severity:** LOW
- **Classification:** Security weakness / contradiction
- **Status:** VERIFIED
- **Confidence:** High

### Evidence
- Login **includes** the role claim: [auth_service.py:2062](../../backend/domains/accounts/services/auth/auth_service.py#L2062) — `create_access_token(data={"sub": ..., "role": _user_role(user)}, ...)`.
- Refresh **omits** it: [auth_service.py:2802-2804](../../backend/domains/accounts/services/auth/auth_service.py#L2802) — `create_access_token(data={"sub": ...})`. Same for `json_register_user` ([:2843](../../backend/domains/accounts/services/auth/auth_service.py#L2843)) and OAuth callbacks ([:2282](../../backend/domains/accounts/services/auth/auth_service.py#L2282)).
- `AuthenticationMiddleware` sets `request.state.user_role = payload.get("role")` ([backend/middleware/authentication_middleware.py:48](../../backend/middleware/authentication_middleware.py#L48)); `AdminGuardMiddleware` gates `/admin*` purely on that JWT-claim role ([backend/middleware/admin_guard_middleware.py:96-101](../../backend/middleware/admin_guard_middleware.py#L96)).

### Impact
After a refresh (or register/OAuth), the access token has no `role` claim → `request.state.user_role` is `None` → the outer admin guard returns 403 even for legitimate admins (fail-closed, so no bypass), meaning the "defense-in-depth" middleware provides no real second layer for refreshed sessions; enforcement relies solely on the per-route DB-role `require_admin`. It is a robustness/consistency defect and a functional bug (admins blocked post-refresh).

### Remediation
Include the same identity claims (`role`, and `email` if used) on every issuance path, or make the admin guard resolve role from the DB rather than the JWT claim.

---

## FINDING 10 — Login issues tokens for inactive/disabled accounts
- **Severity:** LOW
- **Classification:** Security weakness
- **Status:** VERIFIED
- **Confidence:** High

### Evidence
- `login_user` / `json_login_user` verify password and email-verification but never check `is_active`:
  [auth_service.py:2653-2681](../../backend/domains/accounts/services/auth/auth_service.py#L2653), [:2732-2757](../../backend/domains/accounts/services/auth/auth_service.py#L2732).
- The active check exists only later, in the dependency: [security_dependencies.py:36-38](../../backend/domains/accounts/services/auth/security_dependencies.py#L36) (`get_current_user` raises 403 for inactive).

### Impact
A disabled account receives HTTP 200 with a valid token pair on login, though it cannot use bearer-protected routes (dependency blocks it). Inconsistent signaling; a disabled user can still hold a refresh token. Low risk.

### Remediation
Check `is_active` in the login flow before issuing tokens (fail with 403), matching the dependency.

---

## FINDING 11 — Fragmented, partially JWT-trusting authorization primitives
- **Severity:** LOW / INFO
- **Classification:** Security weakness (systemic)
- **Status:** VERIFIED
- **Confidence:** Medium

### Evidence — multiple `require_admin`/role checkers with different trust sources:
- DB-role (ORM) based (strong): [backend/domains/accounts/services/auth/security_dependencies.py:82-90](../../backend/domains/accounts/services/auth/security_dependencies.py#L82).
- Dict-or-ORM, ContextVar based: [backend/rbac/dependencies.py:193-212](../../backend/rbac/dependencies.py#L193) — reads `user.get("role")` when a dict is supplied.
- JWT-dict role for step-up 2FA: [auth_service.py:3374](../../backend/domains/accounts/services/auth/auth_service.py#L3374) — `current_user.get("role") != "admin"`.
- Permission helper with admin bypass: [backend/infrastructure/security/auth.py:389-405](../../backend/infrastructure/security/auth.py#L389) (`require_permission`).
- Additional `require_admin_role` copies: [backend/infrastructure/utils/admin_shared.py:19](../../backend/infrastructure/utils/admin_shared.py#L19), [backend/modules/admin/auth/dependencies.py:14](../../backend/modules/admin/auth/dependencies.py#L14).
- Middleware trusts JWT role: [backend/middleware/authentication_middleware.py:48](../../backend/middleware/authentication_middleware.py#L48).

### Impact
Divergent enforcement increases the chance of a route trusting a JWT-claim role (tamperable only if Finding 02 is realized) instead of the DB role. Today the primary route guards read DB role (good), but the surface is inconsistent and fragile.

### Remediation
Consolidate to a single dependency that derives role/permissions from the DB (or a signed, server-controlled claim protected by a strong secret). Deprecate the duplicate checkers.

---

## FINDING 12 — Latent dev bypass in `verify_social_identity` (no environment guard)
- **Severity:** INFO (not currently reachable with a working session)
- **Classification:** Potential risk (latent)
- **Status:** VERIFIED (code) / not exploitable via wired routes
- **Confidence:** Medium

### Evidence
- `verify_social_identity` returns caller-supplied claims **without** OIDC verification whenever `provider_user_id` is passed, with only a warning and **no** `app_env` guard:
  [backend/domains/accounts/services/auth/auth_service.py:3537-3575](../../backend/domains/accounts/services/auth/auth_service.py#L3537).
- Its only caller `sign_in_social` returns a stub response with `access_token: None`:
  [auth_service.py:3624-3632](../../backend/domains/accounts/services/auth/auth_service.py#L3624) → `issue_auth_response` stub [:3520-3535](../../backend/domains/accounts/services/auth/auth_service.py#L3520) — so no usable session is produced today.
- The wired Google One-Tap route uses proper verification instead: `handle_google_id_token_login` → `_resolve_google_identity_token` (raises on failure) [auth_service.py:2235-2258](../../backend/domains/accounts/services/auth/auth_service.py#L2235); requires `google_client_id` configured.

### Impact
Not currently exploitable (dead/stub path), but if `verify_social_identity`/`sign_in_social` are ever wired to a real token issuer, an unauthenticated attacker could assert any `email`/`provider_user_id` and, via `find_or_create_user`'s email linking ([auth_service.py:3579-3607](../../backend/domains/accounts/services/auth/auth_service.py#L3579)), take over existing accounts.

### Remediation
Delete the caller-supplied-claims branch, or hard-gate it on `app_env in {development,test}` and never link to a pre-existing account without a provider-verified, `email_verified` assertion.

---

## FINDING 13 — Staff SSO door skips audience validation when `SSO_CLIENT_ID` unset
- **Severity:** INFO / potential
- **Classification:** Potential risk (route reachability UNKNOWN)
- **Status:** VERIFIED (code) / UNKNOWN (mounting)
- **Confidence:** Medium

### Evidence
- `_verify_sso_token` disables audience checking when no client id is configured:
  [backend/domains/accounts/services/auth/auth_service.py:990-997](../../backend/domains/accounts/services/auth/auth_service.py#L990) — `audience = client_id if client_id else None; options={"verify_aud": audience is not None}`.
- Signature/issuer via provider JWKS is validated ([:983-996](../../backend/domains/accounts/services/auth/auth_service.py#L983)); auto-provisioning further requires a pre-registered employee ([:1073-1090](../../backend/domains/accounts/services/auth/auth_service.py#L1073)).
- I did **not** find an HTTP route mounting `authenticate_sso` — reachability UNKNOWN.

### Impact
If exposed without a configured client id, a provider-signed ID token minted for a *different* relying party could be replayed (audience confusion), constrained by the pre-registration requirement.

### Remediation
Require `sso_client_id` and enforce `verify_aud=True` before enabling the staff SSO door in any non-dev environment.

---

## FINDING 14 — "Public endpoint" docstrings contradict `require_feature` gates
- **Severity:** INFO
- **Classification:** Contradiction (§10/§11)
- **Status:** VERIFIED
- **Confidence:** High

### Evidence
- `POST /api/v1/auth/register-form` is documented "Public endpoint — no authentication required" but is gated by `require_feature("accounts.user.create")` ([backend/modules/customer/routers/accounts.py:332-343](../../backend/modules/customer/routers/accounts.py#L332)). For anonymous users, `require_feature` resolves only `_PUBLIC_FEATURES = {"catalog.list","catalog.read"}` ([backend/rbac/dependencies.py:53-56](../../backend/rbac/dependencies.py#L53), [:118-146](../../backend/rbac/dependencies.py#L118)) → the route actually **403s** anonymously.
- `POST /api/v1/auth/social/google/id-token` similarly documented public but gated by `require_feature("accounts.social.link")` ([customer/routers/accounts.py:583-596](../../backend/modules/customer/routers/accounts.py#L583)).

### Impact
Documentation/behavior mismatch; the gating happens to *reduce* the register-form escalation surface (Finding 01 remains via the ungated `/auth/register`). Noted per the "report contradictions" rule.

### Remediation
Align docstrings with actual gating; confirm intended access for each auth endpoint.

---

## Positive controls observed (for balance / skepticism)
- **Password hashing:** bcrypt with `rounds=13` and a 72-byte cap — [backend/infrastructure/security/auth.py:186-190](../../backend/infrastructure/security/auth.py#L186), verify at [:178](../../backend/infrastructure/security/auth.py#L178). VERIFIED.
- **JWT algorithm pinned** to a single value list `[HS256]` on every decode — no `alg=none`/algorithm-confusion — [auth.py:289,314,346](../../backend/infrastructure/security/auth.py#L289). VERIFIED.
- **Refresh-token rotation with reuse detection + family revocation** — [auth_service.py:2770-2825](../../backend/domains/accounts/services/auth/auth_service.py#L2770); primitives [auth.py:220-262](../../backend/infrastructure/security/auth.py#L220). VERIFIED.
- **Brute-force lockout** (5 fails / 15 min) on customer login — [auth_service.py:2638,2716](../../backend/domains/accounts/services/auth/auth_service.py#L2638); staff login rate-limit fails **closed** when Redis is down — [auth_service.py:108-146](../../backend/domains/accounts/services/auth/auth_service.py#L108). VERIFIED.
- **Anti-enumeration:** generic responses on forgot-password ([auth_service.py:3118-3144](../../backend/domains/accounts/services/auth/auth_service.py#L3118)) and identical login error/status for unknown user vs bad password ([:2655-2669](../../backend/domains/accounts/services/auth/auth_service.py#L2655)). VERIFIED.
- **Cookies:** refresh cookie `HttpOnly`, `Secure` in production, `SameSite` configured; access token not exposed to JS on the primary flows — [auth_service.py:2815-2820](../../backend/domains/accounts/services/auth/auth_service.py#L2815); `should_secure_cookies == (app_env=="production")` [config.py:473](../../backend/config.py#L473). VERIFIED.
- **CSRF double-submit** with constant-time compare and no production disable — [csrf_middleware.py:90-96,55-60](../../backend/middleware/csrf_middleware.py#L90). VERIFIED.
- **OAuth CSRF state** validated on Google/Facebook callbacks — [auth_service.py:2189-2192](../../backend/domains/accounts/services/auth/auth_service.py#L2189). VERIFIED.
- **Token blacklist fails closed in production** for `is_token_blacklisted` — [auth.py:99-118](../../backend/infrastructure/security/auth.py#L99). VERIFIED.
- **Password complexity** enforced (≥8, upper/lower/digit/special) on register/reset/change — [auth.py:263-278](../../backend/infrastructure/security/auth.py#L263). VERIFIED.

## Contradictions catalogued (MASTER_RULES §10–§11)
1. OTP codes are hashed at rest, but password-reset tokens are stored plaintext (Findings 04/05 context).
2. JWT `role` claim present on login, absent on refresh/register/OAuth (Finding 09).
3. "Public endpoint" docstrings vs `require_feature` gates (Finding 14).
4. `/auth/me` comment says "skip blacklist in development" but the code skips it always (Finding 07).
5. Refresh-cookie `path` differs across issuers — `"/"` in the primary flow ([auth_service.py:2820](../../backend/domains/accounts/services/auth/auth_service.py#L2820)) vs `"/auth/refresh"` in [backend/domains/accounts/services/auth/public_security_registration_service.py:116](../../backend/domains/accounts/services/auth/public_security_registration_service.py#L116).

## Notes / limitations
- Findings are from static reading of the repository (READ-ONLY; no code executed, no exploit written).
- Runtime-dependent behaviors (Redis availability → brute-force/blacklist fail-open vs fail-closed) and deployment env values (`SECRET_KEY`, `APP_ENV`) cannot be confirmed from source alone.
- Staff SSO door mounting (Finding 13) is `NOT DETERMINABLE FROM AVAILABLE CODE`.
```
=== AGENT LOG ===
PHASE: 09 — Authentication / Authorization Security Audit
STATUS: COMPLETED
REPORT_FILE: _audit/findings/PHASE_09_AUTH_SECURITY.md
SCOPE_COVERED: registration, login (customer + 5 staff doors), logout, sessions, refresh rotation, JWT sign/verify, password hashing, reset/change, email verification, TOTP MFA, OAuth/social, RBAC, admin guard, CSRF, cookies, brute-force.
FILES_EXAMINED: ~18
EVIDENCE_ITEMS: 55+
FINDINGS_TOTAL: 14  (VERIFIED: 12 / INFERRED: 1 / UNKNOWN: 1)
SEVERITY_BREAKDOWN: BLOCKER: 1 / HIGH: 1 / MEDIUM: 5 / LOW: 4 / INFO: 3
TOP_FINDINGS:
  1. Unauth privilege escalation via role mass-assignment on POST /api/v1/auth/register — modules/customer/routers/accounts.py:317 + infrastructure/database/schemas.py:1657 + domains/accounts/services/auth/auth_service.py:2404
  2. Committed default SECRET_KEY passes production guard (HS256 forge) — config.py:31 + config.py:214 + infrastructure/security/auth.py:192
  3. Password reset/change do not revoke tokens/refresh families — auth_service.py:3146,3101
  4. Reset tokens stored plaintext — auth_service.py:3126
  5. TOTP secrets stored plaintext — auth_service.py:3260
GAPS / NOT DETERMINABLE: production SECRET_KEY/APP_ENV values; staff SSO route mounting; runtime Redis availability.
SELF_SKEPTICISM_RATING: 5
=== END AGENT LOG ===
```
