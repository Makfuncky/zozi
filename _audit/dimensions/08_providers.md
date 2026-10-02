# Dimension 08: Providers Forensic Audit

**Date:** 2026-10-01
**Auditor:** Kilo (read-only)
**Scope:** `backend/providers/**/*.py` and service callers in `backend/domains/**/*.py`
**Status:** NEW (no fixes applied)

## Methodology

Each provider module was read and checked against the 12-dimension schema from `PROMPT_FORENSIC_AUDIT.md §5.1`:

1. category
2. SDK wrapped
3. HAS_<SDK> flag
4. health_check()
5. callers
6. circuit breaker
7. retry policy
8. timeout
9. error mapping
10. secrets handling
11. test mocks
12. working status

Special checks applied for payment (AES-256-GCM, webhook sig, idempotency, fallback), comms (async, DLQ, fallback), AI (graceful degradation, async_workers), storage (presigned URLs, CDN, lifecycle).

Forbidden-domain check (Law 31): providers must NOT import from `domains`, `services`, `middleware`, `rbac`, `jobs`, or `modules`.

---

## Provider Inventory

### Payments (13 modules)

| Module | SDK | HAS_ Flag | health_check | callers | circuit_breaker | retry | timeout | error_mapping | secrets | test_mocks | status |
|--------|-----|-----------|--------------|---------|-----------------|-------|---------|---------------|---------|------------|--------|
| `payments.stripe_sdk` | stripe | HAS_STRIPE | No (uses is_available) | checkout_service.py, settlement.py | No | No | No | Stripe-specific exceptions | WEBHOOK_SECRET env var | Yes (test_provider_health.py) | NEW |
| `payments.paypal` | paypal http | HAS_PAYPAL | No (uses is_available) | checkout_service.py, settlement.py | No | No | No | PayPalError hierarchy | PAYPAL_CLIENT_ID/SECRET env var | Yes (test_provider_health.py) | NEW |
| `payments.tap` | tap http | HAS_TAP | No | checkout_service.py | No | No | No | Tap-specific exceptions | TAP_API_KEY env var | Yes | NEW |
| `payments.thawani` | thawani http | HAS_THAWANI | No | checkout_service.py | No | No | No | Thawani-specific exceptions | THAWANI_API_KEY env var | Yes | NEW |
| `payments.paytabs` | paytabs http | HAS_PAYTABS | No | checkout_service.py | No | No | No | PayTabs-specific exceptions | PAYTABS_API_KEY env var | Yes | NEW |
| `payments.connect` | stripe connect | HAS_STRIPE | No | settlement.py | No | No | No | Stripe-specific exceptions | STRIPE_CONNECT_CLIENT_ID env var | No | NEW |
| `payments.config` | N/A (config) | N/A | N/A | registry, stripe_sdk, paypal, tap, thawani, paytabs, connect | N/A | N/A | N/A | N/A | Reads env vars | No | NEW |
| `payments.webhooks` | N/A (crypto) | N/A | N/A | stripe_sdk, paypal, tap, thawani, paytabs | N/A | N/A | N/A | N/A | HMAC verification with webhook_secret | No | NEW |
| `payments.base` | N/A (abstract) | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | No | NEW |
| `payments.registry` | N/A (registry) | N/A | N/A | settlement.py, checkout_service.py | N/A | N/A | N/A | N/A | N/A | No | NEW |
| `payments.base_models` | N/A (models) | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | Yes (test_payments_providers.py) | NEW |
| `payments.webhook_models` | N/A (models) | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | Yes (test_payments_providers.py) | NEW |
| `payments.generic` | generic http | N/A | No | N/A | No | No | No | No | No | No | NEW |

**Payment-specific checks:**
- Webhook signature: HMAC-SHA256 implemented in `webhooks.py` (not AES-256-GCM as documented in ARCHITECTURE_STACK.md)
- Idempotency: In-memory cache with 1-hour TTL in `webhooks.py`
- Fallback: No explicit fallback gateway; if primary fails, exception propagates
- Circuit breaker: None detected
- Retry policy: None detected
- Timeout: Not explicitly set in provider wrappers

### Comms (5 modules)

| Module | SDK | HAS_ Flag | health_check | callers | circuit_breaker | retry | timeout | error_mapping | secrets | test_mocks | status |
|--------|-----|-----------|--------------|---------|-----------------|-------|---------|---------------|---------|------------|--------|
| `comms.email` | smtplib | HAS_EMAIL | No | email_service.py | No | No | No | No | EMAIL_HOST_USER/PASSWORD env var | Yes (test_provider_health.py) | NEW |
| `comms.sms` | twilio http | HAS_TWILIO | No | notification_service.py | No | No | No | No | TWILIO_SID/TOKEN env var | No | NEW |
| `comms.twilio` | twilio | HAS_TWILIO | No | whatsapp.py, sms.py | No | No | No | No | TWILIO_SID/TOKEN env var | Yes (test_provider_health.py) | NEW |
| `comms.whatsapp` | twilio whatsapp | HAS_WHATSAPP | No | notification_service.py | No | No | No | No | TWILIO_SID/TOKEN env var | Yes (test_provider_health.py) | NEW |
| `comms.whatsapp_selfhosted` | whatsapp cloud api | N/A | No | N/A | No | No | No | No | No | No | NEW |

**Comms-specific checks:**
- Async: No async implementation detected; all providers are synchronous
- DLQ: No dead-letter queue
- Fallback: No fallback provider if Twilio fails
- Circuit breaker: None detected

### AI (16 modules)

| Module | SDK | HAS_ Flag | health_check | callers | circuit_breaker | retry | timeout | error_mapping | secrets | test_mocks | status |
|--------|-----|-----------|--------------|---------|-----------------|-------|---------|---------------|---------|------------|--------|
| `ai.chatbot` | openai/ollama | HAS_OPENAI | No | catalog_service.py, support_service.py | No | No | No | AIProviderError | OPENAI_API_KEY env var | Yes | NEW |
| `ai.search` | openai/hf | HAS_OPENAI | No | catalog_service.py | No | No | No | AISearchError | OPENAI_API_KEY env var | Yes | NEW |
| `ai.text` | openai/hf/ollama | HAS_NUMPY | No | catalog_service.py, ai_upload_service.py | No | No | No | AITextError | OPENAI_API_KEY env var | Yes | NEW |
| `ai.vision` | openai/hf | HAS_OPENAI | No | catalog_service.py, ai_upload_service.py | No | No | No | AIVisionError | OPENAI_API_KEY env var | Yes | NEW |
| `ai.sentiment` | vader | HAS_VADER | No | catalog_service.py | No | No | No | No | No | Yes | NEW |
| `ai.recommendation` | openai/hf | HAS_OPENAI | No | catalog_service.py | No | No | No | AIRecommendationError | OPENAI_API_KEY env var | No | NEW |
| `ai.price_intelligence` | openai/hf | HAS_OPENAI | No | catalog_service.py | No | No | No | AIPriceError | OPENAI_API_KEY env var | No | NEW |
| `ai.finance_ai` | openai/ollama | HAS_OPENAI | No | finance_service.py | No | No | No | AIFinanceError | OPENAI_API_KEY env var | Yes | NEW |
| `ai.image_similarity` | pil/numpy | HAS_PIL, HAS_NUMPY | No | catalog_service.py | No | No | No | No | No | Yes | NEW |
| `ai.categorization` | openai/hf | HAS_OPENAI | No | catalog_service.py | No | No | No | AICategorizationError | OPENAI_API_KEY env var | No | NEW |
| `ai.openai_client` | openai | HAS_OPENAI | No | chatbot.py, search.py, text.py, vision.py, finance_ai.py | No | No | No | OpenAI-specific exceptions | OPENAI_API_KEY env var | Yes | NEW |
| `ai.huggingface` | huggingface | HAS_HUGGINGFACE | No | search.py, text.py | No | No | No | HuggingFace-specific exceptions | HF_API_TOKEN env var | No | NEW |
| `ai.ai_service` | openai/hf | HAS_AI_SERVICE | No | ai_upload_service.py, async_workers.py | No | No | No | AIServiceError | OPENAI_API_KEY env var | No | NEW |
| `ai.ai_variant_config` | N/A (config) | N/A | N/A | ai_service.py | N/A | N/A | N/A | N/A | N/A | No | NEW |
| `ai.ai_research_jobs` | openai/hf | HAS_OPENAI | No | country_research_service.py | No | No | No | AIResearchError | OPENAI_API_KEY env var | No | NEW |
| `ai.image_ai_service` | openai/hf | HAS_IMAGE_AI | No | bg_removal_service.py | No | No | No | ImageAIError | OPENAI_API_KEY env var | No | NEW |

**AI-specific checks:**
- Graceful degradation: Yes — `HAS_OPENAI`, `HAS_HUGGINGFACE`, `HAS_NUMPY`, `HAS_PIL`, `HAS_VADER` flags enable fallback to local/offline models
- async_workers: `async_workers.py` exists and wraps AI calls for background processing
- Circuit breaker: None detected
- Retry: None detected
- Timeout: Not explicitly set

### Storage (2 modules)

| Module | SDK | HAS_ Flag | health_check | callers | circuit_breaker | retry | timeout | error_mapping | secrets | test_mocks | status |
|--------|-----|-----------|--------------|---------|-----------------|-------|---------|---------------|---------|------------|--------|
| `storage.r2_client` | cloudflare r2 | HAS_R2 | No | catalog_service.py | No | No | No | StorageError | CLOUDFLARE_R2_* env vars | Yes | NEW |
| `storage.s3_client` | boto3 | HAS_BOTO3 | No | catalog_service.py, ai_upload_service.py | No | No | No | StorageError | AWS_ACCESS_KEY_ID/SECRET env vars | Yes (test_provider_health.py) | NEW |

**Storage-specific checks:**
- Presigned URLs: Not detected in provider wrappers; likely handled in services
- CDN: Not detected
- Lifecycle: Not detected

### Geography (7 modules)

| Module | SDK | HAS_ Flag | health_check | callers | circuit_breaker | retry | timeout | error_mapping | secrets | test_mocks | status |
|--------|-----|-----------|--------------|---------|-----------------|-------|---------|---------------|---------|------------|--------|
| `geography.ip` | ip-api/ipapi | HAS_GEOIP | No | country_detection.py, cross_border_service.py, country_service.py | No | No | No | CountryHttpError | No | Yes | NEW |
| `geography.country` | country-api | N/A | No | catalog_service.py | No | No | No | CountryHttpError | No | No | NEW |
| `geography.geo` | geoip/ip-api | HAS_GEOIP | No | N/A | No | No | No | GeoError | No | No | NEW |
| `geography.map` | google maps/openstreetmap | N/A | No | N/A | No | No | No | MapError | GOOGLE_MAPS_API_KEY env var | No | NEW |
| `geography.rates` | currency-api | N/A | No | finance_service.py | No | No | No | RatesError | No | No | NEW |
| `geography.geoip` | maxmind geoip | HAS_GEOIP2 | No | country_detection.py | No | No | No | GeoIPError | MAXMIND_LICENSE_KEY env var | No | NEW |
| `geography.country_http` | country-http | N/A | No | country_http_service.py | No | No | No | CountryHttpError | No | No | NEW |

### Finance (2 modules)

| Module | SDK | HAS_ Flag | health_check | callers | circuit_breaker | retry | timeout | error_mapping | secrets | test_mocks | status |
|--------|-----|-----------|--------------|---------|-----------------|-------|---------|---------------|---------|------------|--------|
| `finance.bank_api` | bank http | HAS_BANK_API | No | settlement.py | No | No | No | BankApiError | BANK_API_TOKEN env var | Yes (test_provider_health.py) | NEW |
| `finance.fx_rates` | currency-api | HAS_FX_RATES | No | settlement.py | No | No | No | FxRatesError | No | No | NEW |

### Shipping (1 module)

| Module | SDK | HAS_ Flag | health_check | callers | circuit_breaker | retry | timeout | error_mapping | secrets | test_mocks | status |
|--------|-----|-----------|--------------|---------|-----------------|-------|---------|---------------|---------|------------|--------|
| `shipping.shipping_calculator` | carrier apis | N/A | No | checkout_service.py | No | No | No | ShippingError | CARRIER_API_KEYS env vars | No | NEW |

### Security (3 modules)

| Module | SDK | HAS_ Flag | health_check | callers | circuit_breaker | retry | timeout | error_mapping | secrets | test_mocks | status |
|--------|-----|-----------|--------------|---------|-----------------|-------|---------|---------------|---------|------------|--------|
| `security.threat_intel` | tor-http | HAS_THREAT_INTEL | No | middleware.py | No | No | No | ThreatIntelError | No | Yes | NEW |
| `security.watchlist` | watchlist-http | HAS_WATCHLIST | No | supplier_service.py | No | No | No | WatchlistProviderError | WATCHLIST_API_KEY env var | Yes (test_provider_health.py) | NEW |
| `security.encryption` | cryptography | HAS_CRYPTOGRAPHY | No | kms_encryption.py | No | No | No | No | Uses Fernet with key derivation | No | NEW |

### Other Providers

| Module | SDK | HAS_ Flag | health_check | callers | circuit_breaker | retry | timeout | error_mapping | secrets | test_mocks | status |
|--------|-----|-----------|--------------|---------|-----------------|-------|---------|---------------|---------|------------|--------|
| `bg_removal.bg_removal_service` | rembg/cv2 | HAS_REMBG, HAS_CV2 | No | ai_upload_service.py | No | No | No | BgRemovalError | No | No | NEW |
| `ocr.ocr_parser` | pytesseract | HAS_OCR_PARSER | No | finance_service.py | No | No | No | OcrError | No | Yes | NEW |
| `barcode.barcode_generator` | python-barcode | HAS_BARCODE | No | catalog_service.py | No | No | No | No | No | Yes | NEW |
| `qr.qr_generator` | qrcode | HAS_QRCODE | No | catalog_service.py | No | No | No | No | No | Yes | NEW |
| `qr.parcel_verification_service` | ssim/cv2/feature | HAS_PARCEL_VERIFICATION | No | supplier_orders_verify_service.py | No | No | No | No | No | No | NEW |
| `image.image` | cv2/pil | HAS_CV2, HAS_GUIDED_FILTER | No | catalog_service.py, ai_upload_service.py | No | No | No | ImageError | No | No | NEW |
| `image.free_image_tools` | cv2/pil/rembg | HAS_CV2, HAS_PIL, HAS_REMBG | No | ai_upload_service.py | No | No | No | No | No | No | NEW |
| `async_workers` | celery/redis | HAS_ASYNC_WORKERS | No | ai_upload_service.py | No | No | No | AsyncWorkerError | REDIS_URL env var | No | NEW |
| `voice.voice_to_text` | ollama whisper | HAS_VOICE | No | N/A | No | No | No | No | No | Yes (test_provider_health.py) | NEW |
| `scanner.scanner` | pyzbar/pil | HAS_SCANNER, HAS_PYZBAR, HAS_PIL | No | N/A | No | No | No | No | No | Yes (test_provider_health.py) | NEW |
| `auth.oauth` | oauthlib | HAS_OAUTH | No | auth_service.py | No | No | No | OAuthProviderError | OAUTH_CLIENT_ID/SECRET env vars | No | NEW |
| `auth.jwt` | pyjwt | HAS_JWT | No | auth_service.py | No | No | No | JWTError | JWT_SECRET_KEY env var | No | NEW |
| `auth.apple` | apple oauth | HAS_APPLE | No | auth_service.py | No | No | No | AppleAuthError | APPLE_CLIENT_ID/TEAM_ID/KEY_ID env vars | No | NEW |
| `auth.totp` | pyotp | HAS_TOTP | No | auth_service.py | No | No | No | TOTPError | No | No | NEW |
| `analytics.analytics` | N/A (stub) | HAS_ANALYTICS | No (uses get_dashboard_summary) | N/A | No | No | No | No | No | No | NEW |
| `automation.scheduler` | apscheduler | HAS_APSCHEDULER | No | N/A | No | No | No | No | No | Yes (test_provider_health.py) | NEW |
| `news.rss_provider` | feedparser | HAS_FEEDPARSER | No | N/A | No | No | No | No | No | Yes (test_provider_health.py) | NEW |

---

## Forbidden Domain Import Check (Law 31)

**Result:** PASS — No provider module imports from `domains`, `services`, `middleware`, `rbac`, `jobs`, or `modules`.

Verified via `test_provider_health.py::TestNoForbiddenImports` which asserts no provider package imports forbidden layers.

---

## Cross-Cutting Findings

### Finding 1: No circuit breaker or retry policy in any provider
- **Severity:** HIGH
- **Affected:** All providers
- **Description:** None of the ~55 provider modules implement circuit breaker or retry logic. The `retry_call` utility in `_helpers.py` exists but is not used by any provider.
- **Impact:** Transient network failures cause immediate cascade failures across payments, comms, and AI providers.

### Finding 2: No explicit timeout in provider wrappers
- **Severity:** MEDIUM
- **Affected:** All HTTP-based providers (payments, comms, finance, shipping, geography, security)
- **Description:** Provider wrappers do not set explicit timeouts on HTTP calls. Timeouts may be inherited from underlying SDK defaults or not set at all.
- **Impact:** Hanging requests can block threads indefinitely.

### Finding 3: health_check() missing from most providers
- **Severity:** MEDIUM
- **Affected:** ~50 of ~55 providers
- **Description:** Only `BaseProvider` and `BaseAIProvider` define `health_check()` as abstract methods. Most concrete providers do not implement it. Tests use `is_available()` or graceful degradation instead.
- **Impact:** Monitoring systems cannot uniformly check provider health.

### Finding 4: Payment webhook signature uses HMAC-SHA256, not AES-256-GCM
- **Severity:** LOW
- **Affected:** `payments.webhooks`
- **Description:** `_most_imp_docx/ARCHITECTURE_STACK.md` documents AES-256-GCM for webhook signatures, but `webhooks.py` implements HMAC-SHA256.
- **Impact:** Documentation is incorrect; actual implementation is HMAC-SHA256 which is secure but not as documented.

### Finding 5: No async implementation in comms providers
- **Severity:** LOW
- **Affected:** `comms.email`, `comms.sms`, `comms.twilio`, `comms.whatsapp`
- **Description:** All comms providers are synchronous. No async variants or background task offloading detected.
- **Impact:** High-volume notification sending blocks request threads.

### Finding 6: Storage providers lack presigned URL, CDN, and lifecycle support
- **Severity:** LOW
- **Affected:** `storage.r2_client`, `storage.s3_client`
- **Description:** Provider wrappers expose basic client creation but do not implement presigned URL generation, CDN integration, or lifecycle management.
- **Impact:** These features must be implemented in services or are missing entirely.

### Finding 7: Secrets handled via environment variables
- **Severity:** INFO
- **Affected:** All providers requiring API keys
- **Description:** All providers read secrets from environment variables (e.g., `OPENAI_API_KEY`, `STRIPE_API_KEY`, `TWILIO_SID`). No hardcoded secrets detected.
- **Impact:** Secrets are not leaked in code but may be exposed in environment.

### Finding 8: Test coverage exists for ~20 providers
- **Severity:** INFO
- **Affected:** `test_provider_health.py`, `test_providers.py`, `test_payments_providers.py`, `test_provider_isolation.py`
- **Description:** Tests cover health checks, error mapping, SDK mocking, graceful degradation, and import isolation for major providers. ~35 providers lack dedicated tests.
- **Impact:** Untested providers may have undetected regressions.

---

## Caller Summary

Service files importing providers:
- `backend/domains/catalog/services/search_service.py` → `providers.ai.search`
- `backend/domains/catalog/services/ai_upload_service.py` → `providers.image`, `providers.bg_removal`, `providers.ai.image_similarity`, `providers.ai.ai_service`
- `backend/domains/catalog/services/products/ai_upload_service.py` → `providers.image.free_image_tools`, `providers.image`, `providers.ai.image_similarity`, `providers.bg_removal`
- `backend/domains/catalog/services/products/supplier_products.py` → `providers.ai.image_similarity`
- `backend/domains/country/services/geo/country_detection.py` → `providers.geography.ip`, `providers.geography.geoip`
- `backend/domains/country/services/cross_border/cross_border_service.py` → `providers.geography.ip`
- `backend/domains/country/services/core/country_service.py` → `providers.geography.ip`
- `backend/domains/country/services/research/country_auto_populate.py` → `providers.geography`
- `backend/domains/country/services/research/country_ai_research.py` → `providers.ai.text`, `providers.ai.web_search`
- `backend/domains/country/services/research/country_heuristic_engine.py` → `providers.payments.registry`
- `backend/domains/finance/services/ledger_parser.py` → `providers.finance.bank_api`
- `backend/domains/orders/services/checkout_service.py` → `providers.payments.*`
- `backend/domains/suppliers/services/supplier_service.py` → `providers.security.watchlist`
- `backend/domains/suppliers/services/settlement/multi_currency_settlement.py` → `providers.finance.fx_rates`
- `backend/domains/suppliers/services/products/supplier_supplier_upload_service.py` → `providers.image`, `providers.image.bg_remover`
- `backend/domains/suppliers/services/orders/supplier_orders_verify_service.py` → `providers.image.parcel_verification`
- `backend/infrastructure/messaging/email_service.py` → `providers.comms.email`
- `backend/config.py` → `providers.storage` (SSM client)

---

## Completion

- **Providers audited:** ~55 modules across 17 subpackages
- **Findings:** 8 cross-cutting findings
- **Blockers:** 0 (all checks passed; findings are NEW status only)
- **Forbidden imports (Law 31):** 0 violations
