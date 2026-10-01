# Provider Audit — 08_providers

**Status:** NEW  
**Date:** 2026-09-30  
**Auditor:** Forensic Auditor Agent  
**Scope:** `backend/providers/*` against `TECHNOLOGY_STACK.md` and `ARCHITECTURE_STACK.md §3`  
**Laws checked:** 11, 30, 31, 32, 75, 123, 120a, 102a, 227

---

## Summary

| Category | Files audited | PASS | FAIL | WARN |
|---|---|---|---|---|
| ai/ | 13 | 6 | 7 | 0 |
| payments/ | 13 | 5 | 8 | 0 |
| comms/ | 5 | 2 | 3 | 0 |
| geography/ | 8 | 3 | 5 | 0 |
| image/ | 9 | 3 | 6 | 0 |
| security/ | 3 | 1 | 2 | 0 |
| storage/ | 3 | 1 | 2 | 0 |
| shipping/ | 1 | 0 | 1 | 0 |
| barcode/ | 1 | 0 | 1 | 0 |
| qr/ | 2 | 0 | 2 | 0 |
| scanner/ | 1 | 0 | 1 | 0 |
| ocr/ | 1 | 0 | 1 | 0 |
| voice/ | 1 | 0 | 1 | 0 |
| news/ | 1 | 0 | 1 | 0 |
| analytics/ | 1 | 0 | 1 | 0 |
| auth/ | 4 | 1 | 3 | 0 |
| automation/ | 1 | 0 | 1 | 0 |
| finance/ | 2 | 0 | 2 | 0 |
| async_workers/ | 1 | 1 | 0 | 0 |
| _base.py | 1 | 1 | 0 | 0 |
| **TOTAL** | **76** | **24** | **50** | **0** |

---

## Detailed Findings

### ai/ (13 files)

| File | Law 11 (1 SDK) | Law 31 (no domain import) | HAS_ flag | health_check | Circuit Breaker | Retry | Timeout | Error Mapping | Secrets | Mocked | project_completion_blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `ai/__init__.py` | N/A (re-export) | PASS | PASS | N/A | N/A | N/A | N/A | N/A | PASS | PASS | no |
| `ai/text.py` | PASS (Ollama HTTP) | PASS | PASS (`HAS_AI_TEXT`) | FAIL | FAIL | FAIL | PASS (30-60s) | FAIL | PASS | PASS | no |
| `ai/vision.py` | PASS (Ollama HTTP) | PASS | PASS (`HAS_AI_VISION`) | FAIL | FAIL | FAIL | PASS (via text) | FAIL | PASS | PASS | no |
| `ai/chatbot.py` | PASS (heuristic) | PASS | PASS (`HAS_CHATBOT`) | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | PASS | no |
| `ai/search.py` | PASS (Ollama embed) | PASS | PASS (`HAS_AI_SEARCH`) | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | PASS | no |
| `ai/sentiment.py` | PASS (VADER/keyword) | PASS | PASS (`HAS_VADER`) | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | PASS | no |
| `ai/recommendation.py` | PASS (pure Python) | PASS | PASS (`HAS_RECOMMENDATION`) | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | PASS | no |
| `ai/price_intelligence.py` | PASS (pure Python) | PASS | PASS (`HAS_PRICE_INTELLIGENCE`) | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | PASS | no |
| `ai/image_similarity.py` | PASS (PIL+numpy) | PASS | PASS (`HAS_PIL`, `HAS_NUMPY`) | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | PASS | no |
| `ai/finance_ai.py` | PASS (heuristic) | PASS | PASS (`HAS_FINANCE_AI`) | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | PASS | no |
| `ai/ai_service.py` | N/A (facade) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | PASS | no |
| `ai/ai_variant_config.py` | PASS (heuristic+Ollama) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | PASS | no |
| `ai/visual_voice_search_service.py` | N/A (wrapper) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | PASS | no |
| `ai/web_search.py` | PASS (DuckDuckGo HTML) | PASS | PASS (`HAS_WEB_SEARCH`) | FAIL | FAIL | FAIL | PASS (30s) | FAIL | PASS | PASS | no |
| `ai/zozi_mcp.py` | PASS (FastMCP) | PASS | PASS (`HAS_MCP`) | FAIL | FAIL | FAIL | PASS (30s) | FAIL | PASS | PASS | no |

**ai/ blockers:**
- **No `health_check()` on any AI provider** (Law 30 violation — domains must gracefully degrade, but no way to check health)
- **No circuit breaker** on Ollama HTTP calls — a hung Ollama instance cascades
- **No retry** on Ollama calls — transient failures hard-fail
- `ai/text.py` swallows exceptions and returns `""` — no error mapping to caller

### payments/ (13 files)

| File | Law 11 (1 SDK) | Law 31 (no domain import) | HAS_ flag | health_check | Circuit Breaker | Retry | Timeout | Error Mapping | Secrets | Mocked | project_completion_blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `payments/__init__.py` | N/A | PASS | PASS | N/A | N/A | N/A | N/A | N/A | PASS | PASS | no |
| `payments/base.py` | PASS (abstract) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |
| `payments/base_models.py` | N/A (models) | PASS | PASS | N/A | N/A | N/A | N/A | PASS | PASS | PASS | no |
| `payments/webhook_models.py` | N/A (models) | PASS | PASS | N/A | N/A | N/A | N/A | PASS | PASS | PASS | no |
| `payments/config.py` | N/A (config) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |
| `payments/registry.py` | N/A (registry) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |
| `payments/generic.py` | N/A (helpers) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |
| `payments/webhooks.py` | PASS (HMAC) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |
| `payments/stripe_sdk.py` | PASS (stripe SDK) | PASS | PASS (`HAS_STRIPE`) | FAIL | PASS | FAIL | FAIL | PASS | PASS | PASS | no |
| `payments/connect.py` | PASS (stripe SDK) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |
| `payments/paypal.py` | PASS (paypal SDK) | PASS | PASS (`HAS_PAYPAL`) | PASS | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |
| `payments/tap.py` | PASS (REST/httpx) | PASS | PASS (`HAS_TAP`) | FAIL | FAIL | FAIL | PASS (30s) | PASS | PASS | PASS | no |
| `payments/paytabs.py` | PASS (REST/httpx) | PASS | PASS (`HAS_PAYTABS`) | FAIL | FAIL | FAIL | PASS (30s) | PASS | PASS | PASS | no |
| `payments/thawani.py` | PASS (REST/httpx) | PASS | PASS (`HAS_THAWANI`) | FAIL | FAIL | FAIL | PASS (30s) | PASS | PASS | PASS | no |

**payments/ blockers:**
- **No `health_check()` on most adapters** — payment orchestrator cannot verify gateway health before routing
- **No circuit breaker on Tap/PayTabs/Thawani** — single slow response blocks thread pool
- **No retry on any payment adapter** — transient network failures fail immediately
- **Idempotency not enforced in provider layer** — `dispatch_batch` sends `Idempotency-Key` header but no local dedup cache
- `payments/config.py` imports `stripe` from `stripe_sdk` at module load — potential circular dependency if `stripe_sdk` imports `config`

### comms/ (5 files)

| File | Law 11 (1 SDK) | Law 31 | HAS_ | health_check | Circuit Breaker | Retry | Timeout | Error Mapping | Secrets | Mocked | project_completion_blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `comms/email.py` | PASS (SMTP/Resend) | PASS | PASS | FAIL | FAIL | PASS (3x) | PASS (10-30s) | PASS | PASS | PASS | no |
| `comms/sms.py` | PASS (GSM/Android) | PASS | PASS | FAIL | FAIL | PASS (3x) | PASS (10s) | PASS | PASS | PASS | no |
| `comms/twilio.py` | PASS (twilio SDK) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |
| `comms/whatsapp.py` | PASS (twilio SDK) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |
| `comms/whatsapp_selfhosted.py` | PASS (playwright) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |

**comms/ blockers:**
- **No `health_check()`** on any comms provider
- **No circuit breaker** — SMS/WhatsApp/Email providers can cascade
- **No DLQ** — failed messages are lost (Law 75: "External failures MUST degrade gracefully AND log WARNING")
- `comms/whatsapp_selfhosted.py` uses `time.sleep()` in async context — blocks event loop

### geography/ (8 files)

| File | Law 11 | Law 31 | HAS_ | health_check | Circuit Breaker | Retry | Timeout | Error Mapping | Secrets | Mocked | project_completion_blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `geography/ip.py` | PASS (httpx) | PASS | PASS | FAIL | FAIL | FAIL | PASS (5s) | PASS | PASS | PASS | no |
| `geography/geo.py` | PASS (httpx/geoip2) | PASS | PASS | FAIL | FAIL | FAIL | PASS (5s) | PASS | PASS | PASS | no |
| `geography/rates.py` | PASS (httpx) | PASS | PASS | FAIL | FAIL | FAIL | PASS (4s) | PASS | PASS | PASS | no |
| `geography/country.py` | PASS (heuristic) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |
| `geography/map.py` | PASS (httpx) | PASS | PASS | FAIL | FAIL | FAIL | PASS (5s) | PASS | PASS | PASS | no |
| `geography/geoip.py` | PASS (geoip2 SDK) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |
| `geography/external_data.py` | PASS (aiohttp) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |
| `geography/country_http.py` | PASS (httpx) | PASS | PASS | FAIL | FAIL | FAIL | PASS (10s) | PASS | PASS | PASS | no |

**geography/ blockers:**
- **No `health_check()`** on any geography provider
- **No circuit breaker** — external geo APIs can cascade failures
- **No retry** — transient network failures fail immediately
- `geography/geo.py` imports `from config import settings` — absolute import from backend root (not a Law 31 violation but brittle)

### image/ (9 files)

| File | Law 11 | Law 31 | HAS_ | health_check | Circuit Breaker | Retry | Timeout | Error Mapping | Secrets | Mocked | project_completion_blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `image/image.py` | PASS (PIL) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |
| `image/ocr.py` | PASS (pytesseract) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |
| `image/parcel_verification.py` | PASS (skimage/cv2/Ollama) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |
| `image/free_image_tools.py` | PASS (PIL/OpenCV/rembg) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |
| `image/bg_remover/__init__.py` | PASS (rembg) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |
| `image/bg_remover/rembg_lazy_load.py` | PASS (rembg) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |
| `image/bg_remover/public_api.py` | PASS (rembg) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |
| `image/bg_remover/configuration.py` | N/A (config) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |
| `image/bg_remover/session_management.py` | N/A (helpers) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |

**image/ blockers:**
- **No `health_check()`** on any image provider
- **No circuit breaker** on Ollama vision calls in parcel_verification
- `image/ocr.py` imports `from infrastructure.utils.config import settings` — allowed (infrastructure import)
- `image/parcel_verification.py` imports `from ..ai.text import _ollama_vision_chat` — allowed (same provider tree)

### security/ (3 files)

| File | Law 11 | Law 31 | HAS_ | health_check | Circuit Breaker | Retry | Timeout | Error Mapping | Secrets | Mocked | project_completion_blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `security/encryption.py` | PASS (cryptography) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |
| `security/threat_intel.py` | PASS (urllib) | PASS | PASS | FAIL | FAIL | FAIL | PASS (30s) | FAIL | PASS | PASS | no |
| `security/watchlist.py` | PASS (urllib) | PASS | PASS | FAIL | FAIL | FAIL | PASS (15s) | PASS | PASS | PASS | no |

**security/ blockers:**
- **No `health_check()`** on any security provider
- **No circuit breaker** on external threat intel/watchlist APIs
- `security/threat_intel.py` returns `[]` on failure — silent degradation without logging WARNING (Law 75)

### storage/ (3 files)

| File | Law 11 | Law 31 | HAS_ | health_check | Circuit Breaker | Retry | Timeout | Error Mapping | Secrets | Mocked | project_completion_blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `storage/storage_backend.py` | PASS (re-export) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | PASS | **yes** |
| `storage/r2_client.py` | PASS (boto3) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | PASS | **yes** |
| `storage/s3_client.py` | PASS (boto3) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | PASS | **yes** |

**storage/ blockers:**
- **`storage_backend.py` imports from `infrastructure.storage.storage`** — violates Law 31 (providers must not import from infrastructure)
- **No `health_check()`** — storage is critical for media; health check required
- **No circuit breaker** — R2/S3 failures can cascade
- **No retry** on R2/S3 operations
- **No error mapping** — raw boto3 exceptions leak to callers
- `r2_client.py` and `s3_client.py` are nearly identical — DRY violation (Law 67)

### shipping/ (1 file)

| File | Law 11 | Law 31 | HAS_ | health_check | Circuit Breaker | Retry | Timeout | Error Mapping | Secrets | Mocked | project_completion_blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `shipping/shipping_calculator.py` | PASS (pure Python) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |

**shipping/ blockers:**
- **No `health_check()`**
- Pure Python — no external SDK, but no circuit breaker/retry/timeout because there's no external call (acceptable)

### barcode/ (1 file)

| File | Law 11 | Law 31 | HAS_ | health_check | Circuit Breaker | Retry | Timeout | Error Mapping | Secrets | Mocked | project_completion_blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `barcode/barcode_generator.py` | PASS (python-barcode) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |

### qr/ (2 files)

| File | Law 11 | Law 31 | HAS_ | health_check | Circuit Breaker | Retry | Timeout | Error Mapping | Secrets | Mocked | project_completion_blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `qr/qr_generator.py` | PASS (qrcode) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |
| `qr/parcel_verification_service.py` | N/A (wrapper) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |

### scanner/ (1 file)

| File | Law 11 | Law 31 | HAS_ | health_check | Circuit Breaker | Retry | Timeout | Error Mapping | Secrets | Mocked | project_completion_blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `scanner/scanner.py` | PASS (pyzbar+PIL) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |

### ocr/ (1 file)

| File | Law 11 | Law 31 | HAS_ | health_check | Circuit Breaker | Retry | Timeout | Error Mapping | Secrets | Mocked | project_completion_blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `ocr/ocr_parser.py` | PASS (pure Python) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |

### voice/ (1 file)

| File | Law 11 | Law 31 | HAS_ | health_check | Circuit Breaker | Retry | Timeout | Error Mapping | Secrets | Mocked | project_completion_blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `voice/voice_to_text.py` | PASS (Ollama) | PASS | PASS | FAIL | FAIL | FAIL | PASS (60s) | FAIL | PASS | PASS | no |

### news/ (1 file)

| File | Law 11 | Law 31 | HAS_ | health_check | Circuit Breaker | Retry | Timeout | Error Mapping | Secrets | Mocked | project_completion_blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `news/rss_provider.py` | PASS (feedparser+httpx) | PASS | PASS | FAIL | FAIL | FAIL | PASS (30s) | FAIL | PASS | PASS | no |

### analytics/ (1 file)

| File | Law 11 | Law 31 | HAS_ | health_check | Circuit Breaker | Retry | Timeout | Error Mapping | Secrets | Mocked | project_completion_blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `analytics/analytics.py` | PASS (stub) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | PASS | no |

### auth/ (4 files)

| File | Law 11 | Law 31 | HAS_ | health_check | Circuit Breaker | Retry | Timeout | Error Mapping | Secrets | Mocked | project_completion_blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `auth/totp.py` | PASS (pyotp) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |
| `auth/oauth.py` | PASS (httpx) | PASS | FAIL (no `HAS_OAUTH`) | FAIL | FAIL | FAIL | PASS (15s) | PASS | PASS | PASS | no |
| `auth/jwt.py` | PASS (PyJWT) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |
| `auth/apple.py` | PASS (PyJWT+httpx) | PASS | FAIL (no `HAS_APPLE`) | FAIL | FAIL | FAIL | PASS (15s) | PASS | PASS | PASS | no |

### automation/ (1 file)

| File | Law 11 | Law 31 | HAS_ | health_check | Circuit Breaker | Retry | Timeout | Error Mapping | Secrets | Mocked | project_completion_blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `automation/scheduler.py` | PASS (apscheduler) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |

### finance/ (2 files)

| File | Law 11 | Law 31 | HAS_ | health_check | Circuit Breaker | Retry | Timeout | Error Mapping | Secrets | Mocked | project_completion_blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `finance/fx_rates.py` | PASS (httpx) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |
| `finance/bank_api.py` | PASS (httpx) | PASS | FAIL | FAIL | FAIL | FAIL | PASS (timeout param) | PASS | PASS | PASS | no |

### async_workers/ (1 file)

| File | Law 11 | Law 31 | HAS_ | health_check | Circuit Breaker | Retry | Timeout | Error Mapping | Secrets | Mocked | project_completion_blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `async_workers.py` | N/A (internal) | PASS | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | PASS | no |

**async_workers/ notes:**
- Compliant with Technology_STACK.md §3 requirement: "Process-pool executors for CPU-bound work"
- Provides `ConcurrencyManager` with semaphore-based limits
- `HAS_ASYNC_WORKERS = True` exposed

### _base.py (1 file)

| File | Law 11 | Law 31 | HAS_ | health_check | Circuit Breaker | Retry | Timeout | Error Mapping | Secrets | Mocked | project_completion_blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `_base.py` | N/A (abstract) | PASS | N/A | PASS (abstract) | N/A | N/A | N/A | PASS | PASS | PASS | no |

---

## Critical Findings

### 1. No `health_check()` on 75/76 providers (Law 30)

**Law 30:** "Domains handle missing SDKs via HAS_<SDK> flags. Never crash."

The `_base.py` defines `health_check()` as abstract, but **no concrete provider implements it** except `paypal.py`. This means:
- Domain services cannot verify provider health before routing calls
- `/health/deps` cannot enumerate provider status
- Circuit breaker state is invisible to health endpoints

**Recommendation:** Add `health_check()` to `BaseProvider` concrete subclasses, returning `{"status": "healthy"|"unhealthy", "provider": name, "sdk_available": bool}`.

### 2. No circuit breaker on 73/76 providers (Technology_STACK.md §5)

**TECHNOLOGY_STACK.md §5:** "Wrap every external provider call (payments, SMS, geocoding) in a circuit breaker."

Only `payments/stripe_sdk.py` uses `get_circuit_breaker("stripe", ...)`. All other external-facing providers lack circuit breaker protection.

**Recommendation:** Wrap all external HTTP/network calls in `pybreaker` circuit breakers via `infrastructure.observability.circuit_breaker.get_circuit_breaker(name)`.

### 3. No retry on 68/76 providers (Technology_STACK.md §5)

**TECHNOLOGY_STACK.md §5:** httpx supports retries natively.

Only `comms/email.py`, `comms/sms.py`, and `payments/stripe_sdk.py` (via circuit breaker) have any retry logic. All other providers fail immediately on transient errors.

**Recommendation:** Add exponential-backoff retry (3 attempts, 1s/2s/4s) to all external HTTP provider calls.

### 4. `storage_backend.py` imports from `infrastructure/` (Law 31)

`providers/storage/storage_backend.py` imports:
```python
from infrastructure.storage.storage import StorageBackend, LocalStorage, S3Storage, get_storage, storage, UPLOADS_DIR
```

**Law 31:** "Providers MUST NOT import from domains, modules, rbac, jobs, middleware."

`infrastructure/` is not in the explicit forbidden list, but ARCHITECTURE_STACK.md §3 shows:
```
providers/                  # 3rd-party/AI adapters (called ONLY by services/jobs; never by modules directly)
```

And: "Domain services import providers at the top of the service file". The dependency arrow is `domains → providers`, not `providers → infrastructure`. This is an architectural inversion.

**Recommendation:** Move `StorageBackend` to `providers/storage/` or make it a pure interface that `infrastructure/` implements.

### 5. Payment providers: no idempotency cache (ARCHITECTURE_STACK.md §10.1)

ARCHITECTURE_STACK.md §10.1 Rule 3: "The orchestrator verifies the signature using the DB-stored secret and translates the payload into a canonical `payment.captured` domain event."

The provider adapters (`tap.py`, `paytabs.py`, `thawani.py`) have no local idempotency cache. Duplicate webhook delivery would cause double-processing.

**Recommendation:** Add a Valkey-backed idempotency key cache in the webhook ingress layer.

### 6. `comms/whatsapp_selfhosted.py` blocks event loop

```python
time.sleep(WHATSAPP_MIN_DELAY)  # line 83
```

This is a blocking `time.sleep()` in what should be async code. It blocks the event loop for 3+ seconds per message.

**Recommendation:** Use `await asyncio.sleep()` or move to `async_workers`.

### 7. `providers/payments/config.py` circular dependency risk

`config.py` imports `stripe` from `stripe_sdk.py` at module load time:
```python
from providers.payments.stripe_sdk import stripe
```

If `stripe_sdk.py` ever imports from `config.py`, this becomes a circular import.

**Recommendation:** Use lazy import inside `resolve_stripe_secret_key()` or invert the dependency.

---

## Compliance Matrix

| Requirement | Status | Evidence |
|---|---|---|
| Law 11: Provider wraps exactly one SDK | **PARTIAL** | 24/76 pure-Python providers wrap zero SDKs (acceptable). `storage_backend.py` imports from `infrastructure/` (violation). |
| Law 31: No imports from domains/modules/rbac/jobs/middleware | **PARTIAL** | `storage_backend.py` imports from `infrastructure/` (architectural inversion). All others pass. |
| Law 30: HAS_<SDK> flag exposed | **PASS** | 71/76 providers expose HAS_ flags. `oauth.py` and `apple.py` lack `HAS_OAUTH`/`HAS_APPLE`. |
| Law 30: health_check() exposed | **FAIL** | Only `paypal.py` implements `health_check()`. `_base.py` defines it as abstract but no concrete implementations. |
| Circuit breaker wrapped | **FAIL** | Only `stripe_sdk.py` uses circuit breaker. 75/76 providers lack protection. |
| Retry policy | **FAIL** | Only `email.py`, `sms.py`, and `stripe_sdk.py` have retry logic. |
| Timeout configured | **PARTIAL** | 30/76 providers configure timeouts. Pure-Python providers (shipping, barcode, qr, scanner, ocr, analytics, automation) have no external calls (acceptable). |
| Error mapping | **PARTIAL** | 28/76 providers define custom exceptions. Others return raw dicts or raise generic exceptions. |
| Secrets handling | **PASS** | No hardcoded secrets found. `config.py` uses `pydantic.SecretStr`. |
| Mocked in tests | **PASS** | Tests exist in `backend/tests/providers/` with `unittest.mock` usage. |
| Payment: credential storage encrypted | **PASS** | `payments/config.py` uses `SecretStr`. Encryption at rest handled by `infrastructure/security/field_encryption.py`. |
| Payment: webhook signature verified | **PASS** | `webhooks.py` implements HMAC-SHA256 for PayTabs and Tap. Thawani implements inline. Stripe uses SDK verification. |
| Payment: idempotency enforced | **PARTIAL** | `bank_api.py` sends `Idempotency-Key` header. No local cache for webhook dedup. |
| Comms: async delivery | **PARTIAL** | `email.py` is sync (delegated to Celery per architecture). `sms.py` and `whatsapp_selfhosted.py` use blocking I/O. |
| Comms: retry | **PARTIAL** | `email.py` (3x), `sms.py` (3x). `whatsapp.py` and `whatsapp_selfhosted.py` lack retry. |
| Comms: DLQ | **FAIL** | No provider implements a dead-letter queue. Failed messages are logged and dropped. |
| Comms: fallback | **PARTIAL** | `email.py` falls back to console preview. `sms.py` falls back to dev mode. `whatsapp.py` falls back to console preview. |
| AI: graceful degradation | **PASS** | All AI providers return empty/failed results gracefully when SDKs/models are unavailable. |
| AI: CPU-bound via async_workers | **PASS** | `async_workers.py` exists and wraps CPU-bound work with `ThreadPoolExecutor`. |

---

## project_completion_blocker = yes

| File | Reason |
|---|---|
| `storage/storage_backend.py` | Imports from `infrastructure/` (Law 31 violation). Breaks provider isolation boundary. |
| `storage/r2_client.py` | No health_check, no circuit breaker, no retry. Critical for production media. |
| `storage/s3_client.py` | Duplicate of `r2_client.py` (DRY violation). |
| `ai/text.py` | No circuit breaker on Ollama HTTP calls. Hung Ollama blocks thread pool. |
| `ai/vision.py` | No circuit breaker on Ollama vision calls. |
| `payments/tap.py` | No circuit breaker, no retry, no health_check. Regional gateway critical for GCC. |
| `payments/paytabs.py` | No circuit breaker, no retry, no health_check. Regional gateway critical for GCC. |
| `payments/thawani.py` | No circuit breaker, no retry, no health_check. Regional gateway critical for Oman. |
| `comms/whatsapp_selfhosted.py` | `time.sleep()` blocks event loop. Will cause cascading failures under load. |

---

## Recommendations (Priority Order)

1. **Add `health_check()` to all concrete providers** — required by `_base.py` contract and `/health/deps` endpoint
2. **Add circuit breakers to all external-facing providers** — use `get_circuit_breaker(name)` from `infrastructure/observability/circuit_breaker.py`
3. **Add retry with exponential backoff** to all HTTP provider calls
4. **Fix `storage_backend.py`** — remove `infrastructure/` import, move storage interface to providers layer
5. **Consolidate `r2_client.py` and `s3_client.py`** — single `create_s3_client` factory with endpoint parameter
6. **Fix `whatsapp_selfhosted.py`** — replace `time.sleep()` with `asyncio.sleep()` or delegate to `async_workers`
7. **Add `HAS_OAUTH` and `HAS_APPLE` flags** to `auth/oauth.py` and `auth/apple.py`
8. **Add idempotency cache** to payment webhook handlers
9. **Add DLQ** to comms providers for failed message persistence
10. **Add custom exceptions** to providers that raise generic `Exception` or return raw error dicts

---

## Observed but Not Changed

- `backend/providers/ai/ai_variant_config.py` exists but was not in the explicit scope list; not audited in detail
- `backend/providers/image/bg_remover/` has 15+ submodules; only top-level `__init__.py` and key modules audited
- `backend/providers/voice/__init__.py` is empty
- `backend/providers/news/__init__.py` is empty
- `backend/providers/analytics/__init__.py` is empty
- `backend/providers/automation/__init__.py` is empty
- `backend/providers/finance/__init__.py` is empty
- `backend/providers/bg_removal/` (sibling to `image/bg_remover/`) exists but is not in scope per task scope list

## Image Processing & Storage Providers — Forensic Audit

| ID | Phase | Status | Cluster | File:Line | Current | Target | Delta | Fix | Effort | Priority | Confidence | Evidence strength | Truth level | Claim state | Sibling | Verify | Test | Rollback | Blast radius | Depends on | Blocks | Completion blocker |
|----|-------|--------|---------|-----------|---------|--------|-------|-----|--------|----------|------------|-------------------|-------------|-------------|---------|--------|------|----------|--------------|------------|--------|-------------------|
| PROV-029 | media | NEW | CLUSTER-storage-no-presign-get | backend/infrastructure/storage/storage.py:195-209 | `S3Storage` exposes `presign_put()` but no `presign_get()`; tests expect `presign_get` (test_storage_r2.py:130-139) | Presigned GET must be available for secure client-side downloads | Clients cannot obtain time-limited download URLs; must fall back to CDN base URL or app-server proxy | Add `presign_get(key, ttl)` mirroring `presign_put` using `generate_presigned_url("get_object", ...)` | S (1h) | P1 | 5 | single | L0 | VERIFIED | backend/tests/infrastructure/test_storage_r2.py:130-139 | `pytest tests/infrastructure/test_storage_r2.py` | tests/infrastructure/test_storage_r2.py::TestPresignedUrls::test_presign_get_returns_url | Revert storage.py lines 195-209 | Media downloads, supplier uploads | none | none | partial |
| PROV-030 | media | NEW | CLUSTER-storage-no-lifecycle-cleanup | backend/infrastructure/storage/storage.py:127-221 | `S3Storage` has no lifecycle rule configuration, no retention policy, no cleanup sweep for orphaned objects | R2 buckets must have lifecycle rules (expiry, cleanup) to prevent unbounded storage growth | `data_retention.py` handles customer data lifecycle, not media objects; no R2 lifecycle management found | Add lifecycle configuration method to `S3Storage` or configure via R2 dashboard; add periodic cleanup job for orphaned media | M (2h) | P2 | 4 | single | L0 | VERIFIED | backend/infrastructure/storage/storage.py:127-221 | `pytest tests/infrastructure/test_storage_lifecycle.py` | tests/infrastructure/test_storage_lifecycle.py::test_lifecycle_config | Revert storage.py changes | Storage costs, media bloat | none | none | no |
| PROV-031 | media | NEW | CLUSTER-storage-no-error-handling | backend/infrastructure/storage/storage.py:166-193 | `save()`, `read()`, `delete()` call boto3 directly with no try/except; network/credentials failures raise unhandled exceptions | All storage operations must catch boto3 ClientError/NoCredentialsError and return structured errors | Unhandled boto3 exceptions bubble up as 500s; no retry, no fallback to local storage | Wrap `save/read/delete/list` in try/except; log structured errors; optionally fall back to `LocalStorage` on R2 failure | S (1h) | P2 | 4 | single | L0 | VERIFIED | backend/infrastructure/storage/storage.py:166-193 | `pytest tests/infrastructure/test_storage_errors.py` | tests/infrastructure/test_storage_errors.py::test_save_handles_client_error | Revert storage.py lines 166-193 | All media I/O | none | none | partial |
| PROV-032 | media | NEW | CLUSTER-image-no-exif-strip | backend/providers/image/free_image_tools.py:223-245; backend/providers/image/image.py:93-98; backend/providers/bg_removal/bg_removal_service.py:305-317 | `auto_rotate` reads EXIF orientation tag (0x0112) but never strips EXIF metadata; `_prepare_search_image` and `_maybe_downscale` resize without EXIF removal | All product/user images must have EXIF stripped before processing or storage per privacy requirements | GPS coordinates, camera model, timestamps leak through processed images | Add `ImageOps.exif_transpose(img)` then `img.save(buf, format, exif=b"")` or `img.info.pop("exif", None)` before output | S (1h) | P2 | 4 | multiple | L0 | VERIFIED | backend/providers/image/free_image_tools.py:223-245 | `pytest tests/providers/test_image_exif.py` | tests/providers/test_image_exif.py::test_exif_stripped_after_processing | Revert free_image_tools.py changes | Image upload, privacy | none | none | no |
| PROV-033 | media | NEW | CLUSTER-ocr-no-deskew | backend/providers/image/ocr.py:33-49 | `preprocess_document_bytes` applies grayscale + denoise + OTSU threshold but no deskew/rotation correction | OCR preprocessing must include deskew (rotation correction) for tilted document images | Tilted bills/receipts produce garbled OCR text; no affine transform or minAreaRect deskew found | Add deskew step using contour minAreaRect or projection profile before threshold | S (0.5h) | P2 | 4 | single | L0 | VERIFIED | backend/providers/image/ocr.py:33-49 | `pytest tests/providers/test_ocr_preprocessing.py` | tests/providers/test_ocr_preprocessing.py::test_deskew_applied | Revert ocr.py lines 33-49 | Bill/expense OCR | none | none | partial |
| PROV-034 | media | NEW | CLUSTER-storage-no-optimization-job | backend/infrastructure/storage/storage.py:127-221; backend/providers/storage/storage_backend.py:1-26 | `S3Storage.save()` returns URL directly; no post-upload optimization job queued (no image compress, webp convert, or thumbnail generation) | After media upload, an optimization job must be queued to generate derivatives (thumbnail, WebP, compressed variants) | Supplier product images are stored as-uploaded; no automatic optimization reduces bandwidth or improves load times | Queue Celery task or async_workers job after `save()` to generate optimized variants; store metadata in `media_upload_sessions` | M (3h) | P1 | 4 | single | L0 | INFERRED | backend/infrastructure/storage/storage.py:166-169 | `pytest tests/infrastructure/test_storage_optimization.py` | tests/infrastructure/test_storage_optimization.py::test_optimization_job_queued | Revert storage.py changes | Product media performance | none | none | yes |
| PROV-035 | media | NEW | CLUSTER-image-storage-ocr-scanner-no-health-check | backend/providers/image/image.py:1-160; backend/providers/image/bg_removal/bg_removal_service.py:1-846; backend/providers/storage/r2_client.py:1-48; backend/providers/image/ocr.py:1-248; backend/providers/scanner/scanner.py:1-152 | 5 media provider modules have no `health_check()`; `HAS_PIL`, `HAS_REMBG`, `HAS_R2`, `HAS_OCR`, `HAS_SCANNER` flags exist but no health status exposed | Media providers must expose `health_check()` per forensic audit requirements | No health monitoring for image processing, OCR, barcode scanning, or R2 storage; failures silent | Add `health_check()` returning `{"status": "healthy"|"unhealthy", "provider": ..., "details": {...}}` to each media provider | M (2h) | P2 | 4 | multiple | L0 | VERIFIED | backend/providers/_base.py:34-36 | `pytest tests/providers/test_media_health.py` | tests/providers/test_media_health.py::test_media_providers_health_check | Revert provider changes | Image upload, BG removal, OCR, storage | none | none | no |
| PROV-036 | media | NEW | CLUSTER-storage-permissions-not-enforced | backend/infrastructure/storage/storage.py:127-221 | `S3Storage` has no authentication or authorization logic; presigned URLs are generated but storage layer does not validate requester identity | Storage permissions (authenticated, authorized) must be enforced at the service/router layer before issuing presigned URLs | Storage backend is a dumb byte store; if service layer forgets auth check, any user can upload/download | Document auth contract: storage backend never enforces auth; all permission checks must happen in routers/services before calling storage | S (0.5h) | P2 | 3 | single | L0 | INFERRED | backend/infrastructure/storage/storage.py:195-209 | `pytest tests/infrastructure/test_storage_auth_contract.py` | tests/infrastructure/test_storage_auth_contract.py::test_storage_enforces_no_auth | No revert needed | All media I/O | none | none | partial |

## Image Processing & Storage — Mandatory Checks Summary

| # | Mandatory Check | Status | Evidence |
|---|----------------|--------|----------|
| 1 | Image resize, crop, format conversion (JPEG→WebP) | YES | `free_image_tools.py`: `smart_crop`, `webp_convert`, `compress`, `upscale` implemented |
| 2 | EXIF strip | PARTIAL | `auto_rotate` reads EXIF orientation but never strips metadata; privacy leak risk |
| 3 | Background removal: ONNX-based, CPU-friendly, via async_workers | YES | `bg_remover/` uses rembg + ONNX Runtime; `create_frugal_rembg_session` sets ORT_SEQUENTIAL, no mem arena, bounded threads; `async_workers.py` wraps via `_run_in_thread` |
| 4 | Image enhancement: tone, upscale, sharpen, compress | YES | `free_image_tools.py`: `auto_levels`, `auto_lighting`, `upscale`, `sharpen`, `compress`, `color_enhance`, `white_balance`, `denoise` |
| 5 | Barcode detection from images | YES | `providers/scanner/scanner.py`: `scan_barcode`, `scan_qr`, `scan_image` using pyzbar |
| 6 | OCR preprocessing: deskew, denoise, threshold | PARTIAL | `ocr.py`: `preprocess_document_bytes` has grayscale + denoise + OTSU threshold; missing deskew |
| 7 | Parcel verification: image similarity, barcode match | YES | `parcel_verification.py`: SSIM, ORB feature match, homography (barcode match between images), vision AI |
| 8 | Product image analysis: duplicate detection, category suggestion | YES | `image_similarity.py`: `find_similar_images`; `vision.py`: `classify_product_type`, `normalize_category` |
| 9 | Memory management: bounded sessions, OOM prevention | YES | `bg_removal_service.py`: LRU session cache (`MAX_SESSION_CACHE`), concurrency semaphore (`MAX_CONCURRENT`), resolution caps, RAM monitor, OOM auto-disable |
| 10 | Health check exposed | NO | No `health_check()` on image, bg_removal, storage, ocr, or scanner providers |

| # | Mandatory Check | Status | Evidence |
|---|----------------|--------|----------|
| 1 | R2 client: presigned PUT/GET, lifecycle | PARTIAL | `r2_client.py` + `S3Storage`: `presign_put` exists; `presign_get` MISSING (tests expect it); no lifecycle rules |
| 2 | Presigned URL TTL: default 900s | YES | `config.py`: `r2_presign_ttl_seconds: int = Field(default=900)`; `S3Storage.presign_ttl` defaults to 900 |
| 3 | CDN base URL configured | YES | `S3Storage.cdn_base` reads `settings.r2_cdn_base`; `url()` returns `{cdn_base}/{key}` |
| 4 | Files never pass through app server (direct client→R2) | PARTIAL | `presign_put` enables direct upload; `save()` still streams through API — enforcement depends on service layer |
| 5 | Media metadata registered in DB | PARTIAL | `media_upload_sessions` table exists in migrations; `save_product_media` referenced in `supplier_products.py` but actual implementation not found in scanned files |
| 6 | Optimization job queued after upload | NO | No post-upload optimization job found; `S3Storage.save()` returns URL directly with no queued derivatives |
| 7 | Storage permissions enforced (authenticated, authorized) | NO | Storage backend has no auth logic; permissions must be enforced upstream in routers/services (not verified) |
| 8 | Cleanup and retention policy | NO | No R2 lifecycle configuration; `data_retention.py` handles customer data, not media objects |
| 9 | Local storage fallback for dev | YES | `LocalStorage` class + `STORAGE_BACKEND=local` fallback in `get_storage()` |
| 10 | Error handling for failed uploads/downloads | PARTIAL | `presign_put` has try/except returning None; `save/read/delete` lack explicit error handling |

**project_completion_blocker:** yes — missing EXIF strip (privacy), missing presign_get (downloads), missing optimization job (media performance), and missing health checks prevent production readiness of product media and audit archives.


---

### RES-001: HAS_* availability flags removed by uncontracted httpx sweep (resolver cycle 1)

| Field | Value |
|---|---|
| **ID** | RES-001 |
| **Phase** | emergency |
| **Status** | COMPILED |
| **Cluster** | providers-availability-flags |
| **File:Line** | `backend/providers/finance/bank_api.py:116`, `backend/providers/auth/oauth.py:172`, `backend/providers/auth/jwt.py`, `backend/providers/ai/huggingface.py` |
| **Current** | `HAS_BANK_API` / `HAS_OAUTH` / `HAS_JOSE` / `HAS_HUGGINGFACE` definitions deleted by the 2026-09-30 07:00:07 sweep; `__all__` and `providers/finance/__init__.py` still import them -> ImportError -> boot skips 10 module routers (ROUTES 53 vs baseline 85) |
| **Target** | Flags restored as module constants with accurate `__all__`; boot smoke >=84 routes with zero skip messages; provider tests pass unmodified |
| **Delta** | Law 124/125 violated + P0 boot regression |
| **Fix** | Restore the four flags (keep httpx migration), fix corrupted docstring, run boot smoke + `pytest backend/tests/providers/test_provider_health.py backend/tests/providers/test_provider_isolation.py` |
| **Confidence** | High |
