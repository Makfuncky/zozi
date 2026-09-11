# PHASE 09 — AUTHENTICATION / AUTHORIZATION SECURITY AUDIT
**Project:** ZOZI Marketplace  
**Auditor:** Kilo  
**Date:** 2026-09-11  
**Scope:** Identity and access control — registration, login, logout, sessions, cookies, JWT, refresh tokens, password hashing, password reset, email verification, MFA, OAuth, roles, permissions, seller/admin/employee accounts, privileged operations  
**Files inspected:** `backend/providers/auth/`, `backend/domains/security/`, `backend/rbac/`, `backend/modules/admin/`, `backend/modules/customer/`, `backend/modules/employee/`, `backend/middleware/`, `backend/config.py`, `backend/domains/accounts/`, `backend/infrastructure/security/`, `backend/infrastructure/utils/auth.py`

---

## EXECUTIVE SUMMARY

The ZOZI Marketplace backend implements a multi-layered authentication and authorization architecture with JWT access/refresh tokens, bcrypt password hashing, TOTP MFA, refresh-token rotation with reuse detection, account lockout, rate limiting, CSRF double-submit cookie protection, an admin-guard middleware, and a feature-catalog-driven RBAC system. However, **two critical privilege-escalation vulnerabilities** allow an unauthenticated attacker to obtain elevated roles during registration and to bypass OIDC verification on a social-login endpoint. Additional high- and medium-severity issues include plaintext storage of password-reset and email-verification tokens, a logout path that can silently fail to blacklist tokens, and an inconsistent middleware ordering that may allow the CSRF exemption on auth endpoints to be exploited.

---

## FINDINGS

### FINDING 1 — CRITICAL: Unauthenticated Privilege Escalation via Registration
**Status:** CONFIRMED  
**Severity:** Critical  
**Affected endpoint/function:** `POST /api/v1/auth/register` ? `json_register_user()` ? `register_user()`  
**Files:**  
- `backend/modules/customer/routers/accounts.py:317-329`  
- `backend/domains/accounts/services/auth/auth_service.py:2353-2511`  
- `backend/infrastructure/database/schemas.py:87-99`  
**Symbols:** `RegisterRequest.role`, `register_user`, `json_register_user`, `auth_register`

**Evidence:**
- `RegisterRequest` defaults `role` to `"customer"` but allows any string (`role: str = "customer"`).
- `register_user()` accepts `user.role` from the request and writes it directly to the `User.role` column after only checking it against an allow-list:
  ```python
  valid_roles = {'customer', 'supplier', 'admin', 'employee', 'logistics_partner'}
  if payload.role not in valid_roles:
      raise HTTPException(...)
  ```
- The endpoint is **public** (no authentication required).
- The `User` model stores `role` with no further server-side constraint.

**Attack scenario:**
1. Attacker sends `POST /api/v1/auth/register` with JSON body:
   ```json
   {"email":"attacker@evil.com","password":"Str0ng!Pass","role":"admin"}
   ```
2. The server creates a `users` row with `role='admin'`.
3. The same call issues a valid JWT access token and refresh token in the response.
4. Attacker now has a fully privileged admin account.

**Impact:** Complete administrative takeover of the marketplace. The attacker can access all admin endpoints, modify users, alter financial records, and exfiltrate PII.

**Recommended remediation:**
- Remove `role` from client-supplied registration payload entirely.
- Hard-code `role = "customer"` for all public self-registration.
- If other roles must be creatable via API, gate those endpoints behind `require_admin` and use an internal admin registration flow.

---

### FINDING 2 — CRITICAL: Social-Login Dev Stub Accepts Caller-Supplied Claims Without OIDC Verification
**Status:** CONFIRMED (code path exists; endpoint currently broken due to mismatched Pydantic model, but the underlying vulnerability is present)  
**Severity:** Critical  
**Affected endpoint/function:** `POST /api/v1/admin/accounts/social/login` ? `social_login()` ? `verify_social_identity()`  
**Files:**  
- `backend/modules/admin/routers/accounts.py:469-509`  
- `backend/domains/accounts/services/auth/auth_service.py:3537-3574`  
- `backend/domains/accounts/services/auth/auth_service.py:3624-3633`  
**Symbols:** `verify_social_identity`, `sign_in_social`, `SocialLoginRequest`

**Evidence:**
- `verify_social_identity()` contains a dev-only shortcut:
  ```python
  if provider_user_id:
      logging.getLogger(__name__).warning(
          "verify_social_identity accepting caller-supplied claims "
          "(provider=%s) — OIDC verification NOT performed", provider,
      )
      return {"provider_user_id": provider_user_id, "email": email, "full_name": full_name}
  ```
- The `social_login` endpoint calls `verify_social_identity()` with `provider_user_id`, `email`, and `full_name` taken directly from the request body.
- No JWKS fetch, no signature check, no `iss`/`aud`/`exp` validation occurs in this path.

**Attack scenario:**
1. Attacker sends `POST /api/v1/admin/accounts/social/login` with body:
   ```json
   {"provider":"google","provider_user_id":"fake_id","email":"victim@example.com","full_name":"Victim"}
   ```
2. `verify_social_identity()` returns the caller-supplied claims without verification.
3. `sign_in_social()` calls `find_or_create_user()`, which either finds an existing user by `provider_user_id` or creates a new `User` + `SocialIdentity` record.
4. `issue_auth_response()` returns a valid auth payload.

**Impact:** Account takeover via social-identity spoofing. An attacker can impersonate any user (including admins) on the platform.

**Recommended remediation:**
- Remove the dev-only shortcut from `verify_social_identity()`.
- Enforce OIDC/JWKS verification for all providers in all environments.
- If a dev/test shortcut is required, gate it behind an explicit `APP_ENV=development` check and never expose it in production builds.

---

### FINDING 3 — HIGH: Password Reset Tokens Stored in Plaintext
**Status:** CONFIRMED  
**Severity:** High  
**Affected endpoint/function:** `POST /api/v1/auth/forgot-password` ? `forgot_password()`  
**Files:**  
- `backend/domains/accounts/services/auth/auth_service.py:3118-3143`  
- `backend/domains/accounts/models/user.py:185-211`  
**Symbols:** `PasswordResetToken.token`, `forgot_password`, `reset_password`

**Evidence:**
- `forgot_password()` stores the raw token:
  ```python
  raw_token = secrets.token_urlsafe(32)
  db_token = PasswordResetToken(
      user_id=user.id,
      token=raw_token,   # <-- plaintext
      expires_at=...,
  )
  ```
- `reset_password()` queries by exact match:
  ```python
  db_token = db.query(PasswordResetToken).filter(
      PasswordResetToken.token == body.token,  # <-- plaintext comparison
  ).first()
  ```
- The `token` column is `String(255)` with no hashing.

**Attack scenario:**
1. Attacker gains read access to the database (e.g., via SQL injection, backup leak, or compromised DB credential).
2. Attacker extracts all plaintext password-reset tokens.
3. Attacker uses a still-valid token to reset any user's password without needing access to the user's email.

**Impact:** Mass account compromise if the database is breached. Password-reset tokens become long-lived credentials equivalent to the user's password.

**Recommended remediation:**
- Hash the token before storage using the same bcrypt mechanism used for passwords (`get_password_hash`).
- Store only the hash in the database; transmit the raw token only via the out-of-band email channel.
- On reset, hash the submitted token and compare against the stored hash.

---

### FINDING 4 — HIGH: Email Verification Tokens Stored in Plaintext
**Status:** CONFIRMED  
**Severity:** High  
**Affected endpoint/function:** `POST /api/v1/auth/verify-email/{token}` ? `verify_email_token()`  
**Files:**  
- `backend/domains/accounts/services/auth/auth_service.py:2516-2539`  
- `backend/domains/accounts/models/user.py:214-240`  
**Symbols:** `EmailVerificationToken.token`, `verify_email_token`, `resend_verification`

**Evidence:**
- `register_user()` stores the raw token:
  ```python
  raw_token = secrets.token_urlsafe(32)
  db.add(EmailVerificationToken(
      user_id=created_user_id,
      token=raw_token,   # <-- plaintext
      expires_at=...,
  ))
  ```
- `verify_email_token()` queries by exact match:
  ```python
  ev = db.query(EmailVerificationToken).filter(
      EmailVerificationToken.token == token,  # <-- plaintext comparison
  ).first()
  ```

**Attack scenario:**
1. Attacker with database read access extracts plaintext email-verification tokens.
2. Attacker verifies email addresses for arbitrary accounts, bypassing the verification gate.
3. For accounts where email verification is required for login, this enables unauthorized login.

**Impact:** Email-verification bypass; account enumeration; potential login bypass for verification-gated accounts.

**Recommended remediation:**
- Hash verification tokens before storage (same approach as password-reset tokens).
- Compare hashed tokens on verification.

---

### FINDING 5 — MEDIUM: `/auth/me` Bypasses Token Blacklist Check
**Status:** CONFIRMED  
**Severity:** Medium  
**Affected endpoint/function:** `GET /api/v1/auth/me`  
**Files:**  
- `backend/modules/customer/routers/accounts.py:237-251`  
- `backend/infrastructure/utils/auth.py:344-356`  
**Symbols:** `decode_token(check_blacklist=False)`, `me`

**Evidence:**
```python
@router.get("/api/v1/auth/me", tags=["auth"])
def me(credentials: ...):
    payload = decode_token(credentials.credentials, expected_type="access", check_blacklist=False)
    return {"id": payload.get("sub"), "role": payload.get("role"), "email": payload.get("email")}
```

**Attack scenario:**
1. User logs out. The access-token JTI is blacklisted.
2. Attacker (or the user themselves) replays the same access token to `/auth/me`.
3. The endpoint returns the user's identity because `check_blacklist=False`.

**Impact:** Information disclosure after logout. An attacker with a captured access token can continue to probe the user's identity even after the user has logged out.

**Recommended remediation:**
- Remove `check_blacklist=False` from the `me` endpoint.
- If performance is a concern, cache the blacklist check result for the duration of the request.

---

### FINDING 6 — MEDIUM: Logout Silently Fails to Invalidate Tokens When Redis Is Unavailable
**Status:** CONFIRMED  
**Severity:** Medium  
**Affected endpoint/function:** `POST /api/v1/auth/logout` ? `logout_user()`  
**Files:**  
- `backend/domains/accounts/services/auth/auth_service.py:2985-3022`  
- `backend/infrastructure/utils/auth.py:79-96`  
**Symbols:** `logout_user`, `blacklist_token`, `revoke_refresh_family`

**Evidence:**
- `blacklist_token()` raises `RuntimeError` in production when Redis is down:
  ```python
  if app_env == "production":
      logger.error("Redis unavailable for token blacklist in production ...")
      raise RuntimeError("Redis unavailable - cannot blacklist token")
  ```
- `logout_user()` catches all exceptions with bare `except Exception: pass`:
  ```python
  try:
      ...
      blacklist_token(jti, ttl)
  except Exception:
      pass  # best-effort blacklist
  ```
- The access-token cookie is never cleared on logout (only the refresh-token cookie is deleted).

**Attack scenario:**
1. Redis becomes temporarily unavailable in production.
2. User logs out. The blacklist calls raise `RuntimeError`, which is silently swallowed.
3. The access token and refresh token remain valid.
4. Attacker who intercepted the tokens can continue to use them.

**Impact:** Session persistence after logout under Redis outage. Tokens remain valid and usable.

**Recommended remediation:**
- Do not swallow `RuntimeError` from `blacklist_token` in production; return an error response so the client knows the logout was incomplete.
- Alternatively, implement a secondary blacklist store (e.g., database table) as a fallback when Redis is unavailable.
- Clear the access-token cookie in the logout response.

---

### FINDING 7 — MEDIUM: Default Development SECRET_KEY in Config
**Status:** CONFIRMED (code-level); mitigated by runtime validation  
**Severity:** Medium  
**Affected file:** `backend/config.py:31`  
**Symbols:** `Settings._DEFAULTS["secret_key"]`

**Evidence:**
```python
"secret_key": os.getenv("SECRET_KEY", "zozi-dev-secret-key-change-in-production-2026"),
```
- The default value is a well-known string embedded in source control.
- Production validation rejects placeholder values:
  ```python
  if secret_key.lower() in {"change-me-in-production", "change-me", "changeme", "secret", "secret-key", "default"}:
      raise ValueError("SECRET_KEY must not be a placeholder value in production.")
  ```
- However, the default value `"zozi-dev-secret-key-change-in-production-2026"` is NOT in the rejection list.

**Attack scenario:**
1. Production is deployed without `SECRET_KEY` set.
2. The application starts with the embedded default secret.
3. Attacker, knowing the default, can forge valid JWTs or compute the HMAC for existing tokens.

**Impact:** Complete authentication bypass in misconfigured production deployments.

**Recommended remediation:**
- Add `"zozi-dev-secret-key-change-in-production-2026"` to the placeholder rejection set.
- Consider failing closed: require `SECRET_KEY` to be set explicitly in all non-test environments, not just production.

---

### FINDING 8 — MEDIUM: CSRF Exemption on Auth Endpoints Combined with Cookie-Based Auth
**Status:** CONFIRMED  
**Severity:** Medium  
**Affected file:** `backend/middleware/csrf_middleware.py:27-37`  
**Symbols:** `CSRF_EXEMPT_PATHS`

**Evidence:**
- Auth endpoints are CSRF-exempt:
  ```python
  CSRF_EXEMPT_PATHS = {
      "/api/v1/auth/login",
      "/api/v1/auth/register",
      "/api/v1/auth/refresh",
      "/api/v1/auth/logout",
      "/api/v1/auth/forgot-password",
      "/api/v1/auth/reset-password",
      "/api/v1/auth/verify-email",
      "/api/v1/auth/me",
  }
  ```
- Access tokens are set as cookies (`httponly=True`, `samesite='lax'` or `'none'` in production).
- Refresh tokens are set as HttpOnly cookies.

**Attack scenario:**
1. User is authenticated and has a valid access-token cookie.
2. Attacker hosts a malicious page that submits a form to `/api/v1/auth/register` or `/api/v1/auth/forgot-password`.
3. Because these endpoints are CSRF-exempt, the browser sends the user's cookies.
4. For `/auth/forgot-password`, the server sends a password-reset email to the victim's address (no state change on the server, but information leakage via timing/response differences).
5. For `/auth/register`, the server creates a new account (no direct harm to the victim, but could be used for spam).

**Impact:** Limited direct impact due to SameSite cookie behavior, but CSRF exemption on state-changing auth endpoints weakens the overall CSRF defense posture.

**Recommended remediation:**
- Consider whether CSRF protection should apply to auth endpoints that change state (register, forgot-password, reset-password).
- For `/auth/register` and `/auth/forgot-password`, add explicit CSRF token validation or require a custom header (`X-Requested-With: XMLHttpRequest`) in addition to the cookie.
- Ensure `samesite='strict'` is used where cross-site cookie sending is not required.

---

### FINDING 9 — MEDIUM: Inconsistent Role Definitions Across Codebase
**Status:** CONFIRMED  
**Severity:** Medium  
**Files:**  
- `backend/rbac/catalog.py:14`  
- `backend/rbac/dependencies.py:60-90`  
- `backend/rbac/roles.py:33-41`  
- `backend/middleware/admin_guard_middleware.py:45`  
**Symbols:** `VALID_USER_ROLES`, `_ROLE_FEATURES`, `_ROLE_MODULES`, `is_admin_role`

**Evidence:**
- `VALID_USER_ROLES = {"customer", "supplier", "admin", "sub_admin", "moderator", "support"}` (catalog.py:14)
- `_ROLE_FEATURES` keys: `super_admin`, `admin`, `employee`, `staff`, `supplier`, `logistics_partner`, `customer` (dependencies.py:60)
- `_ROLE_MODULES` keys: same as above (dependencies.py:93)
- `is_admin_role` in `roles.py`: `{"admin", "sub_admin"}`
- `is_admin_role` in `admin_guard_middleware.py`: `{"admin", "super_admin", "superadmin"}`
- `require_admin` in `security_dependencies.py`: `("admin", "super_admin")`

**Discrepancies:**
1. `VALID_USER_ROLES` includes `sub_admin`, `moderator`, `support` but these roles have no entries in `_ROLE_FEATURES` or `_ROLE_MODULES`.
2. `superadmin` (lowercase) is accepted by `AdminGuardMiddleware` but not by `require_admin` in `security_dependencies.py`.
3. `sub_admin` is considered admin by `roles.py:is_admin_role` but is not in the admin guard's allow-list.

**Impact:** Role confusion. A user with `role="superadmin"` (lowercase) would pass the admin guard middleware but fail `require_admin` dependency, leading to unpredictable access control behavior.

**Recommended remediation:**
- Unify role definitions into a single source of truth (e.g., an enum or constants module).
- Ensure all role-checking functions reference the same canonical set.
- Remove or document legacy aliases (`superadmin` vs `super_admin`).

---

### FINDING 10 — LOW: Missing Explicit Concurrent Session Limit Enforcement
**Status:** INFERRED (no evidence of enforcement in reviewed code)  
**Severity:** Low  
**Affected area:** Session issuance across all login doors  
**Files:**  
- `backend/domains/accounts/services/auth/auth_service.py:1121-1238`  
- `backend/domains/accounts/models/user.py:90-121`  
**Symbols:** `_issue_session`, `UserSession`

**Evidence:**
- The `UserSession` model exists and is created on login, but `_issue_session()` does not check the number of existing active sessions before issuing a new one.
- There is no configuration for maximum concurrent sessions.
- The `session_service.py` module exists (`domains/accounts/services/sessions/session_service.py`) but was not reviewed in detail; no call to a session-limit check was found in `_issue_session`.

**Attack scenario:**
1. Attacker obtains a user's credentials.
2. Attacker logs in from multiple devices simultaneously, creating many active sessions.
3. No alert is raised and no limit is enforced.

**Impact:** Increased exposure window if credentials are compromised. No anomaly detection for concurrent session spikes.

**Recommended remediation:**
- Add a `MAX_CONCURRENT_SESSIONS` configuration and enforce it in `_issue_session()`.
- Invalidate oldest sessions when the limit is exceeded.
- Alert on concurrent session count exceeding a threshold.

---

### FINDING 11 — LOW: Device Fingerprint Is Client-Influenced in Some Paths
**Status:** CONFIRMED  
**Severity:** Low  
**Affected file:** `backend/middleware/device_binding_middleware.py`  
**Symbols:** `DeviceBindingMiddleware`, `request.state.device_binding`

**Evidence:**
```python
fingerprint = request.headers.get("X-Device-Fingerprint") or request.headers.get("X-Device-ID")
request.state.device_binding = fingerprint
```
- The device fingerprint is taken directly from client-supplied headers (`X-Device-Fingerprint` or `X-Device-ID`).
- In `auth_service.py`, `_compute_device_fingerprint()` computes a server-side fingerprint from IP + User-Agent, which is more reliable.
- However, `DeviceBindingMiddleware` (registered in the middleware pipeline) stores the client-provided value on `request.state.device_binding`, which could be used by downstream code.

**Impact:** An attacker can spoof the device fingerprint by setting arbitrary `X-Device-Fingerprint` headers, potentially bypassing device-trust checks if downstream code relies on `request.state.device_binding` instead of the server-computed fingerprint.

**Recommended remediation:**
- Prefer the server-computed fingerprint (`_compute_device_fingerprint`) over client headers.
- If client-provided device IDs are needed for business logic, treat them as opaque identifiers and validate them separately from the security fingerprint.

---

## POSITIVE FINDINGS (CONTROLS THAT ARE IMPLEMENTED CORRECTLY)

| Control | Status | Evidence |
|---|---|---|
| **Password hashing** | VERIFIED | `bcrypt.hashpw` with `rounds=13` (`infrastructure/utils/auth.py:189`) |
| **Password complexity** | VERIFIED | Regex enforcing 8+ chars, upper, lower, digit, special char (`schemas.py:63-80`) |
| **Access token TTL** | VERIFIED | 15 minutes default (`config.py:34`) |
| **Refresh token TTL** | VERIFIED | 7 days default (`config.py:35`) |
| **Refresh token rotation** | VERIFIED | `rotate_refresh_token()` with family_id + jti reuse detection (`auth.py:359-399`) |
| **Refresh token family revocation** | VERIFIED | `revoke_refresh_family()` on reuse (`auth.py:246-256`) |
| **Account lockout** | VERIFIED | 5 failed attempts ? 15-minute lockout (`auth.py:25-26`, `120-176`) |
| **Login rate limiting** | VERIFIED | Sliding-window per-IP limiter on `/auth/login` (`rate_limit_middleware.py:26-39`) |
| **Brute-force protection** | VERIFIED | `record_failed_login` + `is_account_locked` in login flow |
| **TOTP MFA** | VERIFIED | `pyotp`-based TOTP with provisioning URI, recovery codes, temp-token challenge flow (`providers/auth/totp.py`, `auth_service.py:3226-3363`) |
| **Admin guard middleware** | VERIFIED | Blocks non-admin roles from `/admin/*` paths (`middleware/admin_guard_middleware.py`) |
| **RBAC feature catalog** | VERIFIED | `FEATURE_CATALOG` + `require_feature()` + `require_module()` gating (`rbac/`) |
| **CSRF double-submit cookie** | VERIFIED | `X-CSRF-Token` header + `csrf_token` cookie with constant-time comparison (`middleware/csrf_middleware.py`) |
| **Security headers** | VERIFIED | CSP, HSTS, X-Frame-Options, X-XSS-Protection (`middleware/security_headers.py`) |
| **JWT type discrimination** | VERIFIED | `type: "access"` / `type: "refresh"` / `type: "temp"` enforced (`auth.py:312-356`) |
| **JTI blacklist** | VERIFIED | `blacklist_token` / `is_token_blacklisted` with Redis + memory fallback (`auth.py:79-117`) |
| **RLS country isolation** | VERIFIED | `SET app.current_country_code` on login; admin/global roles bypass (`auth_service.py:233-259`) |
| **Email verification** | VERIFIED | Token-based with 24h TTL; gated login for customers (`auth_service.py:2516-2577`) |
| **Audit logging** | VERIFIED | `audit_log` for login success/failure, logout, profile updates (`domains/audit/`) |
| **SSO verification** | VERIFIED | Google/Apple/Microsoft ID tokens verified via JWKS with audience/issuer validation (`auth_service.py:935-1023`) |
| **OAuth state parameter** | VERIFIED | `state` cookie validated on callback (`auth_service.py:2176-2192`) |
| **Password reset TTL** | VERIFIED | 1-hour token expiry (`auth_service.py:1575`) |

---

## ARCHITECTURE NOTES

1. **Auth provider layer** (`backend/providers/auth/`) correctly wraps third-party SDKs (`python-jose`, `pyotp`, `requests`, `PyJWT`) so that domain services never import SDKs directly.
2. **Middleware ordering** is well-documented in `middleware/orchestrator.py` and follows the intended sequence: Foundation ? Authentication ? Rate Limiting ? Webhooks ? Geo/Country ? Security ? Observability.
3. **Dual login paths** exist: the legacy `public_security_registration_service.py` and the canonical `domains/accounts/services/auth/auth_service.py`. Both have similar security properties, but the legacy path uses `check_blacklist=False` in the `me` endpoint and sets cookies with slightly different parameters.
4. **Biometric auth** (`BiometricAuthService`) is currently a stub that only validates token format. Real biometric verification (FaceID, fingerprint, WebAuthn) must be implemented before production use.

---

## REMEDIATION PRIORITY

| Priority | Finding | Action |
|---|---|---|
| P0 | #1 — Unauthenticated role escalation via registration | Remove `role` from public registration; hard-code `"customer"` |
| P0 | #2 — Social-login OIDC bypass | Remove dev stub; enforce JWKS verification in all environments |
| P1 | #3 — Plaintext password-reset tokens | Hash tokens before DB storage |
| P1 | #4 — Plaintext email-verification tokens | Hash tokens before DB storage |
| P1 | #6 — Logout fails silently when Redis is down | Do not swallow `RuntimeError`; add DB fallback or return error |
| P2 | #5 — `/auth/me` bypasses blacklist | Pass `check_blacklist=True` |
| P2 | #7 — Default SECRET_KEY not in rejection list | Add default string to placeholder rejection set |
| P2 | #8 — CSRF exemption on state-changing auth endpoints | Validate CSRF on register/forgot-password/reset-password |
| P2 | #9 — Inconsistent role definitions | Unify role constants in a single module |
| P3 | #10 — No concurrent session limit | Enforce max sessions per user |
| P3 | #11 — Client-influenced device fingerprint | Prefer server-computed fingerprint |

---

*End of Phase 09 Auth Security Audit. No files were modified during this analysis.*
