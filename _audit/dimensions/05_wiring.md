# DIMENSION: Wiring

## Summary
- Confirmation: ❌
- Files inspected: 18
- Files compliant: 6
- Files with findings: 12
- Laws implicated: [L-3, L-5, L-37, L-41, L-60, L-78, L-87, L-88]
- Findings: 8
- P0: 2  P1: 2  P2: 2  P3: 2
- Clusters: 2
- Average confidence: 4.5/5
- Average evidence strength: multiple
- Status: NEW: 8 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0
- Completion blockers: 2 yes · 2 partial · 4 no

## Findings

| ID | Phase | Status | Cluster | File:Line | Current | Target | Delta | Fix | Effort | Priority | Confidence | Evidence strength | Truth level | Claim state | Sibling | Verify | Test | Rollback | Blast radius | Depends on | Blocks | Completion blocker |
|----|-------|--------|---------|-----------|---------|--------|-------|-----|--------|----------|------------|-------------------|-------------|-------------|---------|--------|------|----------|--------------|------------|--------|-------------------|
| WIRE-001 | security | COMPILED | CLUSTER-ws-auth | backend/modules/admin/routers/comms.py:138 | websocket_user accepts connections without JWT verification | WebSocket connections MUST verify JWT type claim equals access (Law 41) | Unauthenticated WebSocket endpoint allows any client to connect and broadcast to all users | Add JWT decode with expected_type="access" before websocket.accept() | S (0.5h) | P0 | 5 | multiple | L0 | VERIFIED | backend/domains/comms/services/messaging/websocket_handlers.py:176 | pytest tests/security/test_websocket_auth.py | tests/security/test_websocket_auth.py::test_websocket_user_requires_jwt | revert commit | WS-USER, CHAIN-004 | none | yes |
| WIRE-002 | db | COMPILED | CLUSTER-rls-set-local | backend/infrastructure/database/rls_interceptor.py:128 | set_rls_context() only sets ContextVars; does not execute SET LOCAL | set_rls_context() executes SET LOCAL app.country_code = :cc inside active transaction (Law 5) | Canonical RLS function uses ContextVar injection instead of PostgreSQL SET LOCAL; legacy SET LOCAL path in country_context.py is not wired to canonical function | Wire canonical set_rls_context to execute SET LOCAL via SQLAlchemy event or session-level hook | M (2h) | P0 | 5 | triangulated | L0 | VERIFIED | backend/middleware/country_context.py:266 | pytest tests/security/test_rls_enforcement.py | tests/security/test_rls_enforcement.py::test_set_rls_context_sets_scope | revert commit | ALL-DOMAIN-QUERIES | none | yes |
| WIRE-003 | logic | COMPILED | CLUSTER-event-post-commit | backend/domains/orders/events.py:84 | publish_order_created() calls publish() synchronously inside service transaction | In-process events must be emitted post-commit to prevent cross-schema transaction locking (Law 3) | Event publishers do not guarantee post-commit emission; failure mid-transaction can leave cross-domain state inconsistent | Emit events from after_commit hook or use event_bus stream with post-commit consumer | M (3h) | P1 | 4 | multiple | L0 | VERIFIED | backend/infrastructure/messaging/realtime.py:736 | pytest tests/domains/orders/test_events.py | tests/domains/orders/test_events.py::test_post_commit_emission | revert commit | CROSS-DOMAIN-EVENTS | none | partial |
| WIRE-004 | logic | COMPILED | CLUSTER-event-post-commit | backend/infrastructure/messaging/events/event_bus.py:331 | time.sleep(backoff) blocks event loop in async handler retry | Async functions MUST NOT call blocking I/O (Law 60) | Event bus retry loop uses blocking time.sleep() which freezes the event loop during handler failures | Replace time.sleep() with asyncio.sleep() in event_bus retry loop | S (0.5h) | P1 | 5 | single | L0 | VERIFIED | backend/infrastructure/observability/retry.py:76 | pytest tests/infrastructure/messaging/test_event_bus.py | tests/infrastructure/messaging/test_event_bus.py::test_retry_non_blocking | revert commit | EVENT-BUS | none | partial |
| WIRE-005 | security | RESOLVED | none | backend/middleware/rate_limit_middleware.py:24 | Rate limiting disabled by default (RATE_LIMIT_ENABLED=false) | Rate limiting fails closed when unavailable (Law 37) | Rate limiting is off by default in development/test; production toggle required | Enable rate limiting by default; fail closed when Valkey is down | S (0.5h) | P2 | 5 | single | L0 | VERIFIED | backend/middleware/rate_limit_middleware.py:121 | pytest tests/middleware/test_rate_limit.py | tests/middleware/test_rate_limit.py::test_fails_closed | revert commit | ALL-ENDPOINTS | none | no |
| WIRE-006 | tech | COMPILED | none | backend/jobs/celery_app.py:87 | retry_backoff_max=300 (5 minutes) for Celery tasks | Retries: 1-2-4-8s, jitter, max 5 | Celery retry backoff cap is 300s (5 min) for most tasks, 1800s (30 min) for periodic tasks; far exceeds 8s target | Reduce retry_backoff_max to 8s for short tasks; document exception for long-running periodic jobs | S (0.5h) | P2 | 4 | single | L0 | VERIFIED | backend/jobs/periodic_tasks.py:18 | pytest tests/jobs/test_celery_config.py | tests/jobs/test_celery_config.py::test_retry_backoff_max | revert commit | CELERY-TASKS | none | no |
| WIRE-007 | docs | COMPILED | none | backend/middleware/orchestrator.py:132-155 | _OBSERVABILITY list labeled "Layer 5" but registered AFTER _SECURITY labeled "Layer 7" in pipeline | Middleware layer labels should match registration order | Comment labels on layer variables are misleading; actual registration order in setup_middleware() is correct | Update comment labels on _OBSERVABILITY and _SECURITY to match registration order | S (0.5h) | P3 | 5 | single | L0 | VERIFIED | backend/middleware/orchestrator.py:176 | pytest tests/middleware/test_orchestrator.py | tests/middleware/test_orchestrator.py::test_layer_order | revert commit | MIDDLEWARE-DOCS | none | no |
| WIRE-008 | arch | COMPILED | none | backend/infrastructure/messaging/events/event_publisher.py:4 | EventPublisher class marked deprecated but still present in codebase | Deprecated code should be removed after migration | EventPublisher is deprecated per WIR-028 but not removed; creates confusion and maintenance burden | Remove EventPublisher class after confirming all callers migrated to event_bus | M (2h) | P3 | 4 | single | L0 | VERIFIED | backend/infrastructure/messaging/events/event_publisher.py:57 | pytest tests/infrastructure/messaging/test_event_publisher.py | tests/infrastructure/messaging/test_event_publisher.py::test_deprecated_warning | revert commit | EVENT-BUS | none | no |

## Over all

### Problem(s)
1. WebSocket endpoint `websocket_user` in `modules/admin/routers/comms.py:138` accepts connections without any JWT verification, violating Law 41 and allowing unauthenticated broadcast to all users.
2. Canonical `set_rls_context()` in `rls_interceptor.py:128` uses ContextVars instead of executing `SET LOCAL app.country_code = :cc` as required by Law 5; the legacy `SET LOCAL` path in `country_context.py:266` is not wired to the canonical function.
3. Event publishers in `domains/*/events.py` call `publish()` synchronously without post-commit guarantee, violating Law 3 and risking cross-schema transaction locking.
4. Event bus retry loop in `event_bus.py:331` uses blocking `time.sleep()` in async context, violating Law 60 and freezing the event loop.

### Solution(s)
1. Add JWT authentication with `expected_type="access"` to `websocket_user` endpoint before `websocket.accept()`.
2. Wire canonical `set_rls_context()` to execute `SET LOCAL` via SQLAlchemy session event or remove the legacy `set_session_rls` and enforce RLS solely through ContextVar-based query injection.
3. Emit cross-domain events from SQLAlchemy `after_commit` hooks or use Valkey Stream outbox with post-commit consumer.
4. Replace `time.sleep()` with `asyncio.sleep()` in `event_bus.py` retry loop.

### Suggestion(s)
1. Review all WebSocket endpoints for consistent JWT type claim verification.
2. Audit all `set_rls_context()` call sites to ensure they use the canonical function and that it enforces `SET LOCAL`.
3. Add integration tests that verify events are not emitted if the transaction rolls back.
4. Consider using Valkey Stream consumer groups for event processing instead of in-process synchronous handlers.

### Corrections required (prioritized)
| Priority | Correction | Target | Blocking | Effort | Confidence |
|---|---|---|---|---|---|
| P0 | Add JWT auth to websocket_user | backend/modules/admin/routers/comms.py:138 | yes | S | 5 |
| P0 | Wire canonical set_rls_context to SET LOCAL | backend/infrastructure/database/rls_interceptor.py:128 | yes | M | 5 |
| P1 | Guarantee post-commit event emission | backend/domains/*/events.py | partial | M | 4 |
| P1 | Replace time.sleep with asyncio.sleep in event_bus | backend/infrastructure/messaging/events/event_bus.py:331 | partial | S | 5 |
