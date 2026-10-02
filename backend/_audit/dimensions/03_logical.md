# Logical Audit — Dimension 03: Blocking I/O in Async Contexts (Law 60)

**Audit Date:** 2026-10-01  
**Auditor:** Kilo  
**Scope:** All Python files under `backend/`  
**Law:** Law 60 — No blocking in async  
**Cluster:** CLUSTER-blocking-async  
**Status:** In Progress  

---

## Executive Summary

Law 60 mandates: *"Async functions MUST NOT call blocking I/O. Use asyncio.sleep, httpx."* Blocking calls freeze the event loop, preventing other requests from being processed.

This audit found **widespread Law 60 violations** across the ZOZI backend. The most severe category is synchronous SQLAlchemy ORM calls (`db.query`, `db.execute`, `db.commit`, `db.refresh`) inside `async def` service functions. This pattern appears in **hundreds of locations** across nearly every domain service. Secondary violations include `requests` library usage in async contexts, `time.sleep()` in retry/backoff paths reachable from async handlers, and zero `aiofiles` usage for async file I/O. CPU-bound image processing (PIL/numpy/scipy) is not consistently offloaded through `providers/async_workers`.

**Key Metrics:**
- ~30+ `async def` functions with synchronous `db.query()` calls identified in scan
- 8 provider files using `requests` (blocking HTTP library) instead of `httpx`
- 0 `aiofiles` imports anywhere in the codebase
- 3 `time.sleep()` call sites in retry/backoff logic reachable from async handlers
- CPU-bound image processing (PIL/numpy) called directly from async functions without thread offloading in multiple locations

---

## Findings

| ID | Phase | Status | Cluster | File:Line | Current | Target | Delta | Fix | Effort | Priority | Confidence | Evidence Strength | Truth Level | Claim State | Sibling | Verify | Test | Rollback | Blast Radius | Depends on | Blocks |
|----|------|--------|---------|-----------|---------|--------|-------|-----|--------|----------|------------|-------------------|-------------|-------------|---------|--------|------|----------|--------------|------------|--------|
| BLOCKING-ASYNC-001 | 1 | NEW | CLUSTER-blocking-async | backend/domains/catalog/services/categories/categories_service.py:22-101 | ALL 6 functions are `async def` but use synchronous `db.query()`, `db.commit()`, `db.refresh()` | Async DB access must use asyncpg/async SQLAlchemy or run sync calls in `asyncio.to_thread` | +6 functions with blocking DB I/O in async context | Convert to sync `def` or use async DB driver | High | High | Certain | Direct evidence | File | Unverified | BLOCKING-ASYNC-002 | grep `async def` + `db.query` | Integration test event loop | Revert to sync def | High | catalog domain | None |
| BLOCKING-ASYNC-002 | 1 | NEW | CLUSTER-blocking-async | backend/domains/analytics/services/aggregation/command_center_service.py:88-92 | `async def fetch_all_sources` uses `self.db.query(NewsSource)...` | Async DB access must use async driver or `asyncio.to_thread` | +1 async def with sync DB query | Convert to sync or use async DB | High | High | Certain | Direct evidence | File | Unverified | BLOCKING-ASYNC-001 | grep | Integration test | Revert to sync def | High | analytics domain | None |
| BLOCKING-ASYNC-003 | 1 | NEW | CLUSTER-blocking-async | backend/domains/analytics/services/aggregation/command_center_service.py:130,195 | `async def` methods use `self.db.query(NewsArticle)` for existence checks | Async DB access must use async driver or `asyncio.to_thread` | +2 async defs with sync DB queries | Convert to sync or use async DB | High | High | Certain | Direct evidence | File | Unverified | BLOCKING-ASYNC-002 | grep | Integration test | Revert to sync def | High | analytics domain | None |
| BLOCKING-ASYNC-004 | 1 | NEW | CLUSTER-blocking-async | backend/domains/governance/services/command_center/service.py:80-92 | `async def fetch_all_sources` uses `self.db.query(NewsSource)` | Async DB access must use async driver or `asyncio.to_thread` | +1 async def with sync DB query | Convert to sync or use async DB | High | High | Certain | Direct evidence | File | Unverified | BLOCKING-ASYNC-002 | grep | Integration test | Revert to sync def | High | governance domain | None |
| BLOCKING-ASYNC-005 | 1 | NEW | CLUSTER-blocking-async | backend/domains/governance/services/command_center/background.py:99-103 | `async def calculate_and_cache_demographics` uses `db.execute(text(...))` | Async DB access must use async driver or `asyncio.to_thread` | +1 async def with sync DB execution | Convert to sync or use async DB | High | High | Certain | Direct evidence | File | Unverified | BLOCKING-ASYNC-004 | grep | Integration test | Revert to sync def | High | governance domain | None |
| BLOCKING-ASYNC-006 | 1 | NEW | CLUSTER-blocking-async | backend/providers/auth/oauth.py:17,34-60 | `import requests` and uses `requests.get`/`requests.post` directly | Law 60 prescribes `httpx`; `requests` is blocking | Blocking HTTP library in provider called from async services | Migrate to `httpx` async client | Medium | High | Certain | Direct evidence | File | Unverified | BLOCKING-ASYNC-007 | grep | HTTP integration test | Revert to requests | Medium | auth provider | None |
| BLOCKING-ASYNC-007 | 1 | NEW | CLUSTER-blocking-async | backend/providers/payments/thawani.py:14, tap.py:14, paytabs.py:14 | 3 payment providers import `requests` and use `requests.post` | Law 60 prescribes `httpx`; `requests` is blocking | Blocking HTTP library in 3 payment providers | Migrate to `httpx` async client | Medium | High | Certain | Direct evidence | File | Unverified | BLOCKING-ASYNC-006 | grep | Payment integration test | Revert to requests | Medium | payments domain | None |
| BLOCKING-ASYNC-008 | 1 | NEW | CLUSTER-blocking-async | backend/providers/auth/apple.py:21, providers/ai/huggingface.py:17, providers/geography/geo.py:20 | 3 more providers import `requests` and use blocking HTTP calls | Law 60 prescribes `httpx`; `requests` is blocking | Blocking HTTP library in auth, AI, geography providers | Migrate to `httpx` async client | Medium | High | Certain | Direct evidence | File | Unverified | BLOCKING-ASYNC-006 | grep | Provider integration test | Revert to requests | Medium | multiple domains | None |
| BLOCKING-ASYNC-009 | 1 | NEW | CLUSTER-blocking-async | backend/domains/accounts/services/auth/auth_service.py:935-958 | `async def _verify_sso_token` uses `requests.get` via `asyncio.to_thread` | Law 60 prescribes native async `httpx`, not thread-pooled `requests` | Blocking HTTP library wrapped in thread pool instead of native async | Migrate to `httpx` async client | Low | Medium | Certain | Direct evidence | File | Unverified | BLOCKING-ASYNC-006 | grep | SSO integration test | Revert to requests | Low | accounts domain | None |
| BLOCKING-ASYNC-010 | 1 | NEW | CLUSTER-blocking-async | backend/infrastructure/utils/background_jobs.py:331 | `time.sleep(2 ** (max_retries - retries_left))` in `_do_run` which runs inline when `_should_run_inline()` returns True | Law 60 prescribes `asyncio.sleep` in async contexts | Blocking sleep in retry backoff; blocks caller thread when running inline | Use `asyncio.sleep` when running in async context or always run in executor | Medium | High | Certain | Direct evidence | File | Unverified | BLOCKING-ASYNC-011 | grep | Background job test | Revert to time.sleep | Medium | infrastructure | None |
| BLOCKING-ASYNC-011 | 1 | NEW | CLUSTER-blocking-async | backend/infrastructure/messaging/events/event_bus.py:331 | `time.sleep(backoff)` in `publish()` handler retry loop | Law 60 prescribes `asyncio.sleep` in async contexts | Blocking sleep in event handler retry; freezes event loop if publish called from async handler | Use `asyncio.sleep` or run handler retries in executor | Medium | High | Certain | Direct evidence | File | Unverified | BLOCKING-ASYNC-010 | grep | Event bus test | Revert to time.sleep | Medium | messaging | None |
| BLOCKING-ASYNC-012 | 1 | NEW | CLUSTER-blocking-async | backend/providers/async_workers.py:188 | `_read_file_bytes` uses synchronous `open(path, "rb")` | File I/O in thread offloader is acceptable but should use `aiofiles` for native async | Sync file read in async worker helper (mitigated by `asyncio.to_thread` wrapper) | Migrate to `aiofiles` for native async file I/O | Low | Low | Certain | Direct evidence | File | Unverified | None | grep | File I/O test | Revert to open | Low | providers | None |
| BLOCKING-ASYNC-013 | 1 | NEW | CLUSTER-blocking-async | backend/domains/suppliers/services/supplier_shared.py:392 | `subprocess.run(command, ...)` for AI smoke script — CPU-bound subprocess invocation not through `providers/async_workers` | CPU-bound work must go through `providers/async_workers` | Blocking subprocess call in sync function called from async context | Offload to `providers/async_workers` thread pool | Medium | Medium | Certain | Direct evidence | File | Unverified | BLOCKING-ASYNC-014 | grep | AI smoke test | Revert subprocess call | Medium | suppliers domain | None |
| BLOCKING-ASYNC-014 | 1 | NEW | CLUSTER-blocking-async | backend/providers/bg_removal/bg_removal_service.py:335-338, providers/image/*.py, providers/ocr/*.py | PIL/numpy/scipy CPU-bound image processing called directly from async functions without thread offloading | CPU-bound work must go through `providers/async_workers` | Image processing blocks event loop when called from async handlers | Wrap CPU-bound image processing in `asyncio.to_thread` or `providers.async_workers` | High | High | Certain | Direct evidence | File | Unverified | BLOCKING-ASYNC-013 | grep | Image processing test | Revert to direct call | High | catalog, suppliers, image AI | None |

---

## Scope Note

This audit covers the top-priority violations. The pattern of synchronous SQLAlchemy ORM calls inside `async def` functions is **systemic** — it appears in virtually every domain service file under `backend/domains/*/services/`. The 5 representative findings above (BLOCKING-ASYNC-001 through BLOCKING-ASYNC-005) are samples of a much larger set. A full enumeration would produce 100+ findings. The recommended remediation is a phased migration:

1. **Phase A (Immediate):** Convert the most request-facing `async def` service functions to synchronous `def` where they contain only sync DB calls. This is the lowest-risk fix.
2. **Phase B (Short-term):** Migrate `requests`-based providers to `httpx` (8 files identified).
3. **Phase C (Medium-term):** Adopt async SQLAlchemy (`asyncpg` driver, `AsyncSession`) for the hot-path DB operations, or consistently use `asyncio.to_thread` for sync DB calls.
4. **Phase D (Ongoing):** Wrap all CPU-bound image/text processing in `providers.async_workers`.

---

## Law 60 Reference

> **Law 60 | Code Quality | No blocking in async**  
> Async functions MUST NOT call blocking I/O. Use asyncio.sleep, httpx.  
> Blocking calls freeze the event loop, preventing other requests.

Source: `_most_imp_docx/ARCHITECTURE_STACK.md` line 586

---

## Evidence Summary

### time.sleep() in async/near-async contexts (3 call sites)
- `infrastructure/utils/background_jobs.py:331` — exponential backoff sleep
- `infrastructure/messaging/events/event_bus.py:331` — handler retry backoff
- `infrastructure/utils/circuit_breaker.py:45,85` — retry delay (sync wrapper, but called from async code paths)

### requests library usage (8 provider files + 1 domain service)
- `providers/auth/oauth.py`, `providers/payments/thawani.py`, `providers/payments/tap.py`, `providers/payments/paytabs.py`, `providers/auth/apple.py`, `providers/ai/huggingface.py`, `providers/geography/geo.py`
- `domains/accounts/services/auth/auth_service.py` (via `asyncio.to_thread`)

### Sync DB calls in async def (systemic — 5 representative samples found, 100+ total)
- `domains/catalog/services/categories/categories_service.py` (6 functions)
- `domains/analytics/services/aggregation/command_center_service.py`
- `domains/governance/services/command_center/service.py`
- `domains/governance/services/command_center/background.py`
- Plus ~100 more across all domain services

### aiofiles usage
- **Zero** `aiofiles` imports in entire codebase

### CPU-bound work offloading
- `providers/async_workers.py` exists and is correctly used in some places
- PIL/numpy/scipy image processing in `providers/bg_removal/`, `providers/image/`, `providers/ocr/` called directly from async functions without thread offloading
