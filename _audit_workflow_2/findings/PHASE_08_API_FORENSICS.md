# TASK 08 — API FORENSIC AUDIT

## Executive Summary

The ZOZI Marketplace backend is a FastAPI-based REST API with supplemental WebSocket, Webhook, and an internal standalone FastAPI microservice. No GraphQL or gRPC/RPC layers were found.

Critical Findings:
- `/ws/user` WebSocket endpoint has NO authentication — any client can connect and broadcast to the user:realtime room
- Standalone FastAPI microservice (Zozi Location Service) in `domains/logistics/services/core/service.py` with `/api/geo/*` routes — NOT mounted into main app; appears to be orphaned code with no entry point
- Frontend `openapi.json` is empty — no API contract available for frontend developers
- Admin routers use dual authorization (`require_admin` + `require_feature`) — potential for misconfiguration
- Webhook verification middleware implements HMAC with replay protection for Stripe, Tap, PayPal

## 1. API Architecture Overview

| Layer | Technology | Status |
|-------|-----------|--------|
| Primary API | FastAPI (Python) | VERIFIED |
| GraphQL | None found | VERIFIED |
| gRPC / RPC | None found | VERIFIED |
| WebSockets | FastAPI WebSocket + custom in-memory managers | VERIFIED |
| Webhooks | HMAC-verified inbound (Stripe, Tap, PayPal) | VERIFIED |
| Internal APIs | Separate FastAPI microservice (location) — NOT mounted | VERIFIED |
| External APIs | Stripe, Tap, PayPal, Thawani, PayTabs, Resend, geography provider | VERIFIED |

Evidence:
- `backend/main.py:72` — `app = FastAPI(...)`
- `backend/domains/logistics/services/core/service.py:2967` — standalone `app = FastAPI(title="Zozi Location Service")`
- No GraphQL schema files, no `.proto` files found.

## 2. REST Endpoint Inventory

Routers are discovered dynamically from 5 module packages:
- `modules/customer/routers/`
- `modules/supplier/routers/`
- `modules/logistics/routers/`
- `modules/admin/routers/`
- `modules/employee/routers/`

Each package exposes `routers` and `public_routers` lists built from domain router modules via `importlib.import_module`.

### 2.1 Admin Module (18 routers)

| Router | Prefix | Auth Pattern |
|--------|--------|--------------|
| accounts | `/api/v1/admin/accounts` | require_admin + require_feature |
| analytics | `/api/v1/admin/analytics` | require_admin + require_feature |
| audit | `/api/v1/admin/audit` | require_admin + require_feature |
| catalog | `/api/v1/admin/catalog` | require_admin + require_feature |
| comms | `/api/v1/admin/comms` | require_admin + require_feature |
| config_versions | `/api/v1/admin/config-versions` | require_admin + require_feature |
| country | `/api/v1/admin/country` | require_admin + require_feature |
| customers | `/api/v1/admin/customers` | require_admin + require_feature |
| disputes | `/api/v1/admin/disputes` | require_admin + require_feature |
| finance | `/api/v1/admin/finance` | require_admin + require_feature |
| governance | `/api/v1/admin/governance` | require_admin + require_feature |
| hr | `/api/v1/admin/hr` | require_admin + require_feature |
| logistics | `/api/v1/admin/logistics` | require_admin + require_feature |
| orders | `/api/v1/admin/orders` | require_admin + require_feature |
| permissions | `/api/v1/admin/permissions` | require_admin + require_feature |
| promotions | `/api/v1/admin/promotions` | require_admin + require_feature |
| security | `/api/v1/admin/security` | require_admin + require_feature |
| staff | `/api/v1/admin/staff` | require_admin + require_feature |
| suppliers | `/api/v1/admin/suppliers` | require_admin + require_feature |
| tickets | `/api/v1/admin/tickets` | require_admin + require_feature |

Note: `modules/admin/routers/orders.py` contains campaign-related routes (imported from `domains.comms.ports`) — potential copy-paste error; the router prefix is `/api/v1/admin/orders` but routes reference campaigns.

### 2.2 Customer Module (15 routers)

| Router | Prefix |
|--------|--------|
| accounts | (domain router) |
| analytics | (domain router) |
| audit | (domain router) |
| catalog | (domain router) |
| comms | (domain router) |
| country | (domain router) |
| customers | (domain router) |
| finance | (domain router) |
| governance | (domain router) |
| hr | (domain router) |
| logistics | (domain router) |
| orders | (domain router) |
| promotions | (domain router) |
| security | (domain router) |
| suppliers | (domain router) |

### 2.3 Supplier Module (15 routers)

Same domain router set as customer, mounted under supplier namespace.

### 2.4 Logistics Module (15 routers)

Same domain router set, mounted under logistics namespace.

### 2.5 Employee Module (15 routers + HR sub-routers)

Employee has the same 15 domain routers plus an additional `hr` sub-package with 10 sub-routers:
- `modules/employee/routers/hr/approval.py`
- `modules/employee/routers/hr/attendance.py`
- `modules/employee/routers/hr/employees.py`
- `modules/employee/routers/hr/ess.py`
- `modules/employee/routers/hr/health.py`
- `modules/employee/routers/hr/hierarchy.py`
- `modules/employee/routers/hr/leaves.py`
- `modules/employee/routers/hr/lms.py`
- `modules/employee/routers/hr/matrix.py`
- `modules/employee/routers/hr/offices.py`
- `modules/employee/routers/hr/payroll.py`
- `modules/employee/routers/hr/performance.py`
- `modules/employee/routers/hr/schedule.py`
- `modules/employee/routers/hr/schemas.py`
- `modules/employee/routers/hr/schemas_admin.py`
- `modules/employee/routers/hr/succession.py`

## 3. WebSocket Endpoints

| Endpoint | Auth | Evidence |
|----------|------|----------|
| `/ws/user` | **NONE** | `backend/main.py:194-196` imports `websocket_user` from `modules.admin.routers.comms` (line 138-156) which has NO authentication |
| `/ws/admin/background-jobs` | JWT + admin role | `backend/main.py:204-240` — validates JWT token, checks role in `("admin", "super_admin")` |
| `/ws-chat/ws/user` | JWT token query param | `backend/domains/comms/services/messaging/websocket_handlers.py:218-288` — `_decode_ws_token` validates JWT |

### 3.1 `/ws/user` — CRITICAL: Unauthenticated

The `websocket_user` function in `modules/admin/routers/comms.py:138-156`:
```python
async def websocket_user(websocket: WebSocket):
    """Handle a user realtime WebSocket connection."""
    await websocket.accept()
    manager.active_connections[USER_ROOM].append(websocket)
    ...
```

This function is imported in `main.py:194` and registered at `/ws/user` at line 196. A local `websocket_user` with JWT auth is defined later in `main.py:289-325`, but the route was already registered with the unauthenticated version.

Impact: Any unauthenticated client can connect to `/ws/user`, join the `user:realtime` room, and broadcast arbitrary messages to all connected clients.

## 4. Standalone Location Service (Orphaned)

`backend/domains/logistics/services/core/service.py:2967` defines a complete standalone FastAPI app:

```python
app = FastAPI(title="Zozi Location Service", version="1.0.0")
```

Routes:
- `GET /api/health` — health check
- `GET /api/geo/from-ip` — resolve location from IP (auth required)
- `GET /api/geo/locate` — locate from request IP (auth required)
- `POST /api/geo/reverse` — reverse geocode (auth required)
- `POST /api/geo/resolve` — resolve location from IP payload (auth required)

All geo routes require JWT via `_get_current_user_geo` dependency.

**Status: NOT mounted into main app.** No entry point (no `if __name__ == "__main__"` block, no separate run script found). This appears to be orphaned code that is not deployed or runnable.

Evidence: No references found in docker-compose, Procfile, systemd units, or deployment configs.

## 5. Webhook Verification

`backend/middleware/webhook_verification.py` implements HMAC signature verification:

| Provider | Secret Config | Signature Header | Tolerance |
|----------|--------------|------------------|-----------|
| Stripe | `settings.stripe_webhook_secret` | `Stripe-Signature` | 300s |
| Tap | `settings.tap_webhook_secret` | `Tap-Signature` | 300s |
| PayPal | `settings.paypal_webhook_secret` | `PayPal-Transmission-Sig` | 300s |

Additional `WebhookIPWhitelistMiddleware` (`backend/middleware/webhook_ip_whitelist.py`) provides IP-based allowlisting.

Replay attack protection: timestamp tolerance of 300 seconds (5 minutes).

## 6. Middleware Pipeline

8-layer pipeline registered in `backend/middleware/orchestrator.py`:

| Layer | Middleware | Purpose |
|-------|-----------|---------|
| 1. Foundation | GZip, IPExtraction, RequestID, ApiVersion | Request plumbing |
| 2. Authentication | AuthenticationMiddleware, DeviceBindingMiddleware | JWT resolution |
| 3. Rate Limiting | RateLimitMiddleware | Sliding-window DoS protection |
| 3.5 Webhooks | WebhookIPWhitelist, WebhookVerification | IP + HMAC verification |
| 4. Geo & Country | CountryContextMiddleware | RLS scope setup |
| 5. Observability | RequestLoggingMiddleware | Request logging |
| 6. PCI Compliance | PCIDSSMiddleware | HTTPS enforcement (prod only) |
| 7. Security | EnhancedSecurityHeaders, ImpossibleTravel, FraudDetection, FraudScoring, CSRF | Security enforcement |

Registration order is reversed due to Starlette prepend behavior.

## 7. OpenAPI Specification

`backend/main.py:77-78` enables docs:
```python
docs_url="/docs",
redoc_url="/redoc",
```

However, `frontend/web_app/openapi.json` is empty:
```json
{
  "openapi": "3.0.0",
  "info": { "title": "ZOZI", "version": "0.1.0" },
  "paths": {}
}
```

This means the TypeScript frontend has no generated API client contract. The backend does generate an OpenAPI spec at runtime (`/openapi.json`), but it has not been exported to the frontend.

## 8. API Versioning

Versioning is header-based via `ApiVersionMiddleware`:
- `backend/infrastructure/utils/versioning.py` — `VERSION_PREFIX`, `get_version_path`, `versioned_prefix`, `get_active_versions`
- Active versions tracked in settings
- `/health` returns `active_versions` list

## 9. Authentication Patterns

| Pattern | Implementation | Evidence |
|---------|---------------|----------|
| HTTP Bearer JWT | `AuthenticationMiddleware` + `require_admin` dependency | `backend/middleware/authentication_middleware.py:33-67` |
| WebSocket JWT (query param) | `token: str = Query(...)` + `_decode_ws_token` | `backend/domains/comms/services/messaging/websocket_handlers.py:218-288` |
| WebSocket JWT (admin) | Same pattern + role check | `backend/main.py:204-240` |
| Dual auth (admin) | `require_admin` + `require_feature("...")` | All admin routers |

## 10. Rate Limiting

`RateLimitMiddleware` (`backend/middleware/rate_limit_middleware.py`) implements sliding-window per-path rate limiting. Runs after authentication but before expensive DB operations.

## 11. CORS Configuration

`CORSMiddleware` configured in `backend/middleware/orchestrator.py:217-227`:
- `allow_origins`: `settings.cors_origins_list`
- `allow_credentials`: True
- `allow_methods`: GET, POST, PUT, PATCH, DELETE, OPTIONS
- `allow_headers`: Authorization, Content-Type, X-CSRF-Token, X-Country-Code, X-Requested-With

## 12. Health Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Liveness — returns status, version, API version, active versions |
| `GET /health/deps` | Dependency status — redis, email, payments, error_tracking |
| `GET /health/ready` | Readiness — database, blocking dependencies, returns 503 if blocked |

## 13. Security Findings Summary

| # | Issue | Severity | Evidence |
|---|-------|----------|----------|
| 1 | `/ws/user` WebSocket endpoint has no authentication — any client can connect and broadcast to user:realtime room | HIGH | `modules/admin/routers/comms.py:138-156` |
| 2 | Standalone FastAPI microservice (location service) is NOT mounted in main app — orphaned code | MEDIUM | `domains/logistics/services/core/service.py:2967` |
| 3 | Frontend openapi.json is empty — no API contract available for frontend developers | MEDIUM | `frontend/web_app/openapi.json` |
| 4 | Admin routers use dual authorization (require_admin + require_feature) — potential for misconfiguration | LOW | `modules/admin/routers/*` |
| 5 | WebSocket `/ws/user` broadcasts raw text without sanitization | MEDIUM | `modules/admin/routers/comms.py:143-149` |
