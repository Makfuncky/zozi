# Providers Layer — Architectural Violation & Code Quality Report

**Scope:** `backend/providers/` — 22 provider packages + shared modules
**Date:** 2026-08-26
**Reference:** ARCHITECTURE_DIAGRAM.md, DOMAIN_WORK.md, AGENTS.md

---

## Executive Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 5 |
| HIGH | 8 |
| MEDIUM | 10 |
| LOW | 6 |

The providers layer has **systemic architectural violations**. The core design rule — "providers wrap external SDKs only, no business logic" — is violated across the `ai/`, `shipping/`, `voice/`, and `media/` subpackages. Additionally, `providers/media/` exists in the wrong layer entirely.

---

## CRITICAL Violations

### C1. `providers/media/` — Wrong layer entirely

**File:** `providers/media/services/ai_service.py` (1114 lines)
**File:** `providers/media/services/ai.py` (36 lines — stub)
**File:** `providers/media/services/ai_copy_jobs.py` (100 lines)

Per `DOMAIN_WORK.md` and `project.md`: "all code from domains/media must be shifted to providers/media" — but the **opposite** is true. The `media/` directory contains **business logic** (product description generation, category suggestion, tag suggestion, variant template suggestion, material candidates, visual product matching with hardcoded product fingerprints). This is domain logic, not SDK wrapping.

The `ai_service.py` file alone is 1,114 lines of pure business logic:
- Hardcoded product categories (`PRODUCT_CATEGORIES`, lines 44-48)
- Hardcoded tag mappings (`COMMON_TAGS`, lines 50-65)
- Hardcoded variant templates (`VARIANT_TEMPLATE_OPTIONS`, lines 67-76)
- Hardcoded material suggestions (`MATERIAL_SUGGESTIONS_BY_TEMPLATE`, lines 78-87)
- Hardcoded visual reference hints with **WhatsApp image filenames** (`_VISUAL_HINT_SPECS`, lines 116-224)
- Product description templates (`_build_description`, lines 938-1041)
- Category keyword mapping (`_keyword_category`, lines 856-884)

**Fix:** Move `providers/media/` → `domains/media/services/`. The `ai.py` stub file should be deleted.

---

### C2. `providers/ai/recommendation.py` — Pure business logic, no SDK

**File:** `providers/ai/recommendation.py` (273 lines)

This module implements a full recommendation engine (TF-IDF, cosine similarity, collaborative filtering, market basket analysis) with **zero external SDK usage**. It is pure Python business logic.

```python
# Line 93-177: Full recommendation engine with TF-IDF + collaborative filtering
def get_product_recommendations(product_id, user_history, all_products, limit=10): ...

# Line 180-225: Similar products via TF-IDF
def get_similar_products(product_id, products, limit=10): ...

# Line 228-273: Market basket analysis
def get_frequently_bought_together(product_id, orders, limit=5): ...
```

**Fix:** Move to `domains/catalog/services/recommendation_service.py` or a new `domains/analytics/services/`.

---

### C3. `providers/ai/price_intelligence.py` — Pure business logic with hardcoded data

**File:** `providers/ai/price_intelligence.py` (235 lines)

Contains hardcoded price benchmarks (`_CATEGORY_BENCHMARKS`, lines 24-40) and implements price analysis, positioning, and suggestion logic. No external SDK.

```python
# Line 24-40: Hardcoded business data
_CATEGORY_BENCHMARKS: Dict[str, Dict[str, float]] = {
    "electronics": {"min": 5.0, "max": 3000.0, "avg": 350.0, "std": 400.0},
    "fashion": {"min": 3.0, "max": 500.0, "avg": 60.0, "std": 70.0},
    ...
}
```

**Fix:** Move to `domains/catalog/services/price_intelligence_service.py`. Benchmarks should come from the database, not hardcoded constants.

---

### C4. `providers/ai/search.py` — Full search engine, not an SDK wrapper

**File:** `providers/ai/search.py` (352 lines)

Implements `AdvancedSearchEngine` class with natural language query parsing, category synonym expansion, vector embedding search, fuzzy matching, and autocomplete. Only uses `embed_text` from `providers.ai.text` — the rest is business logic.

```python
# Line 36-352: Full search engine class
class AdvancedSearchEngine:
    def parse_query(self, query): ...  # NL query parsing
    def search(self, query, filters, limit, offset, sort_by): ...
    def load_product_catalog(self, products): ...
    def get_autocomplete_suggestions(self, query, limit): ...
    def fuzzy_search(self, query, limit, cutoff): ...
```

**Fix:** Move to `domains/catalog/services/search_service.py`. The embedding call can stay as a provider call.

---

### C5. `providers/ai/chatbot.py` — Business logic, not SDK wrapper

**File:** `providers/ai/chatbot.py` (109 lines)

Implements intent classification and response generation with hardcoded patterns and responses. No external SDK.

```python
# Line 57-80: Hardcoded intent classification
def _classify_intent(self, query):
    intent_patterns = [
        ("product_search", ["find", "show", "search", ...]),
        ("order_status", ["my order", "order status", "track"]),
        ...
    ]

# Line 82-94: Hardcoded response templates
def _generate_response(self, intent, query):
    responses = {
        "product_search": "I can help you find products...",
        ...
    }
```

**Fix:** Move to `domains/comms/services/chatbot_service.py`.

---

## HIGH Violations

### H1. `providers/shipping/shipping_calculator.py` — Business logic with hardcoded carrier data

**File:** `providers/shipping/shipping_calculator.py` (407 lines)

Contains hardcoded carrier definitions, zone mappings, and pricing models. This is business logic, not an SDK wrapper.

```python
# Line 29-115: Hardcoded carrier business data
_CARRIERS: Dict[str, Dict[str, Any]] = {
    "fedex": {"base_rate": 8.50, "per_kg": 2.80, "per_cbm": 180.0, ...},
    "ups": {"base_rate": 7.95, "per_kg": 2.65, ...},
    ...
}

# Line 118-125: Hardcoded zone mappings
_ZONE_MAP: Dict[str, int] = {"US": 1, "CA": 2, ...}
```

**Fix:** Move to `domains/logistics/services/shipping_calculator.py`. Carrier data should be in the database.

---

### H2. `providers/voice/voice_to_text.py` — Domain-specific command processing

**File:** `providers/voice/voice_to_text.py` (198 lines)

While `transcribe_audio()` is a valid SDK wrapper (Ollama), the file also contains:
- `process_product_voice_command()` (lines 69-133) — extracts product variants, quantity, action
- `process_finance_voice_command()` (lines 136-198) — extracts finance task types, amounts, categories

These are domain-specific business logic functions with hardcoded keyword lists.

```python
# Line 22-32: Hardcoded domain keyword lists
_VariantKeywords = {"color": [...], "size": [...], "material": [...]}
_FinanceKeywords = {"expense": [...], "asset": [...], "task": [...]}
```

**Fix:** Keep `transcribe_audio()` in providers. Move `process_product_voice_command()` → `domains/catalog/services/`. Move `process_finance_voice_command()` → `domains/finance/services/`.

---

### H3. `providers/ai/vision.py` — Business logic mixed with SDK calls

**File:** `providers/ai/vision.py` (309 lines)

Contains `analyze_product_image()` which calls Ollama (valid), but also:
- `classify_product_type()` — keyword-based product classification (line 70)
- `normalize_category()` — keyword-based category normalization (line 172)
- `suggest_price()` — AI price suggestion with business logic (line 120)
- `VariantConfig` dataclass — business config (line 47)

**Fix:** Keep Ollama vision calls. Move classification/normalization to `domains/catalog/services/`.

---

### H4. `providers/ai/finance_ai.py` — Business logic, no SDK

**File:** `providers/ai/finance_ai.py` (204 lines)

Implements email-to-ledger parsing, bill field extraction, and reconciliation matching. Pure regex-based business logic, no external SDK.

```python
# Line 37-100: Email parsing business logic
def parse_email_to_ledger(email_text): ...

# Line 112-146: Bill field extraction
def extract_bill_fields(image_bytes): ...

# Line 148-204: Reconciliation matching
def suggest_reconciliation_match(...): ...
```

**Fix:** Move to `domains/finance/services/`.

---

### H5. `providers/ai/sentiment.py` — Business logic with optional SDK

**File:** `providers/ai/sentiment.py` (378 lines)

Has `HAS_VADER` flag (good), but the keyword-based sentiment analysis, review analysis, and insight extraction are pure business logic.

**Fix:** This could stay as a provider IF it only wrapped VADER. The keyword fallback and review insight extraction should move to `domains/catalog/services/` or `domains/analytics/services/`.

---

### H6. `providers/ai/text.py` — Mixed: SDK wrapper + business logic

**File:** `providers/ai/text.py` (552 lines)

Contains valid Ollama SDK wrapping (`_ollama_chat`, `embed_text`, `transcribe_audio`), but also:
- `_extract_variant_from_text()` — product variant extraction
- `_extract_product_name()` — product name extraction
- `_extract_tags()` — tag extraction
- `translate_en_to_ar()` — translation (valid if wrapping a translation API)

**Fix:** Keep Ollama/embedding functions. Move extraction functions to `domains/catalog/services/`.

---

### H7. Cross-provider imports — `bg_removal` imports from `image`

**File:** `providers/bg_removal/bg_removal_service.py` (line 43-53)

```python
from providers.image import Image
from providers.image.bg_remover import create_frugal_rembg_session, rembg_remove_bytes
from providers.image import HAS_CV2 as _HAS_CV2, HAS_GUIDED_FILTER as _HAS_GUIDED_FILTER, cv2, ximgproc
```

Providers should be independent. `bg_removal` should either be merged into `image/` or the shared code should be in a shared utilities module.

---

### H8. Cross-provider imports — `ai_variant_config` imports from `ai/text`

**File:** `providers/ai/ai_variant_config.py` (line 29)

```python
from providers.ai.text import _ollama_chat_completion, _extract_json
```

Cross-provider imports create coupling. This should be refactored to accept dependencies via injection.

---

## MEDIUM Violations

### M1. Missing `HAS_` flags for several providers

The following providers wrap external SDKs but **lack** `HAS_<SDK>` boolean flags:

| Provider | File | SDK Used | Has Flag? |
|----------|------|----------|-----------|
| ai/text.py | Ollama via urllib | No |
| ai/vision.py | Ollama via urllib | No |
| ai/finance_ai.py | None (pure Python) | N/A |
| ai/chatbot.py | None (pure Python) | N/A |
| ai/search.py | None (pure Python) | N/A |
| ai/recommendation.py | None (pure Python) | N/A |
| ai/price_intelligence.py | None (pure Python) | N/A |
| geography/geo.py | None (pure Python) | No |
| geography/country.py | None (pure Python) | No |
| geography/map.py | None (pure Python) | No |
| storage/s3_client.py | boto3 | No |
| storage/storage_backend.py | boto3 | No |
| image/image.py | PIL | No |
| image/parcel_verification.py | PIL | No |
| ocr/ocr_parser.py | None (pure Python) | No |
| payments/base.py | None (abstract) | No |
| payments/generic.py | None (pure Python) | No |
| payments/registry.py | None (pure Python) | No |
| payments/webhooks.py | None (pure Python) | No |
| security/encryption.py | None (pure Python) | No |
| security/threat_intel.py | None (pure Python) | No |
| security/watchlist.py | None (pure Python) | No |
| news/rss_provider.py | None (pure Python) | No |
| qr/parcel_verification_service.py | None (pure Python) | No |

**Fix:** Add `HAS_<SDK>` flags for all providers that wrap external SDKs. For pure-Python providers, add a comment explaining why no flag is needed.

---

### M2. `providers/ai/image_ai_service.py` — Cross-provider imports

**File:** `providers/ai/image_ai_service.py` (lines 30-33)

```python
from providers.image import Image, ImageOps, ImageFilter
from providers.image.bg_remover import create_rembg_session, rembg_remove_bytes
from providers.ai.huggingface import call_hf_image_api
```

Cross-provider coupling between `ai/` and `image/`.

---

### M3. `providers/ai/visual_voice_search_service.py` — Cross-provider imports

**File:** `providers/ai/visual_voice_search_service.py` (lines 10-11)

```python
from providers.image import process_image_search
from providers.voice import transcribe_audio
```

---

### M4. `providers/qr/parcel_verification_service.py` — Cross-provider import

**File:** `providers/qr/parcel_verification_service.py` (line 12)

```python
from providers.image.parcel_verification import (...)
```

---

### M5. `providers/async_workers.py` — Orchestrator, not a provider

**File:** `providers/async_workers.py` (466 lines)

This module is an **orchestrator** that coordinates across multiple providers (bg_removal, vision, text, OCR, search). It also contains a `ConcurrencyManager` and `process_large_batch_async` — infrastructure concerns.

While it's acceptable to have async wrappers, the orchestration logic (pipeline coordination) belongs in the domain layer.

**Fix:** Keep simple async wrappers in providers. Move pipeline orchestration (`full_supplier_pipeline_async`, `parallel_process_product_async`) to `domains/catalog/services/` or a new `domains/ai_orchestration/`.

---

### M6. `providers/ai/ai_variant_config.py` — Business logic + cross-provider import

**File:** `providers/ai/ai_variant_config.py` (442 lines)

Contains `AIVariantConfig` class with product type classification, variant extraction, and AI rules. Pure business logic with a cross-provider import.

---

### M7. `providers/ai/image_similarity.py` — Business logic

**File:** `providers/ai/image_similarity.py`

Implements image embedding computation and similarity matching. While it has `HAS_PIL` and `HAS_NUMPY` flags (good), the similarity algorithms are business logic.

---

### M8. `providers/ai/web_search.py` — Likely business logic

Not read but by name suggests search orchestration rather than SDK wrapping.

---

### M9. `providers/ai/zozi_mcp.py` — Likely business logic

Not read but MCP server implementation is typically business logic.

---

### M10. `providers/media/services/ai.py` — Dead stub code

**File:** `providers/media/services/ai.py` (36 lines)

Contains only stub implementations returning `{"status": "not_implemented"}`. Dead code.

```python
class AIService:
    def process(self, *args, **kwargs) -> dict:
        return {"status": "not_implemented"}
```

**Fix:** Delete this file.

---

## LOW Violations

### L1. `providers/config.py` — Shared config used by multiple providers

**File:** `providers/config.py` (69 lines)

This is a shared configuration dataclass used by 10+ providers. While not ideal (each provider could have its own config), this is acceptable for environment-variable-based configuration. However, it mixes AI config, BG removal config, search config, geo config, etc.

**Fix:** Consider splitting into per-provider config files or moving to `infrastructure/config/`.

---

### L2. `providers/http.py` — Trivial re-export

**File:** `providers/http.py` (9 lines)

Simply re-exports `aiohttp` symbols. This is fine as an SDK isolation layer but could be more explicit about its purpose.

---

### L3. `providers/observability.py` — No HAS flag

**File:** `providers/observability.py` (31 lines)

Wraps `sentry_sdk` but doesn't expose a `HAS_SENTRY` flag. Uses `importlib.import_module` instead of the standard try/except pattern.

```python
# Current (non-standard pattern):
def capture_exception(exc):
    try:
        sentry_sdk = importlib.import_module("sentry_sdk")
        sentry_sdk.capture_exception(exc)
    except Exception:
        pass

# Should be:
try:
    import sentry_sdk
    HAS_SENTRY = True
except ImportError:
    HAS_SENTRY = False
```

---

### L4. `providers/ai/huggingface.py` — Not read but likely needs review

Not investigated in detail. Should be checked for business logic vs SDK wrapping.

---

### L5. `providers/geo/__init__.py` — Empty directory

**File:** `providers/geo/__init__.py` (empty)

The `geo/` directory has only an empty `__init__.py`. Dead code or incomplete migration.

**Fix:** Delete the empty directory.

---

### L6. `providers/payments/paytabs.py` and `payments/thawani.py` — Hardcoded `HAS_=True`

**File:** `providers/payments/paytabs.py` (line 27)
**File:** `providers/payments/thawani.py` (line 26)

```python
HAS_PAYTABS = True  # No try/except — assumes SDK is installed
HAS_THAWANI = True  # No try/except — assumes SDK is installed
```

These don't follow the graceful degradation pattern. If the SDK is missing, imports will fail.

---

## Summary of Files Needing Migration

| Current Path | Target Path | Lines | Priority |
|-------------|-------------|-------|----------|
| `providers/media/` | `domains/media/services/` | 1150 | CRITICAL |
| `providers/ai/recommendation.py` | `domains/catalog/services/` | 273 | CRITICAL |
| `providers/ai/price_intelligence.py` | `domains/catalog/services/` | 235 | CRITICAL |
| `providers/ai/search.py` | `domains/catalog/services/` | 352 | CRITICAL |
| `providers/ai/chatbot.py` | `domains/comms/services/` | 109 | CRITICAL |
| `providers/shipping/shipping_calculator.py` | `domains/logistics/services/` | 407 | HIGH |
| `providers/voice/voice_to_text.py` (partial) | `domains/catalog/services/` + `domains/finance/services/` | 130 | HIGH |
| `providers/ai/vision.py` (partial) | `domains/catalog/services/` | 200 | HIGH |
| `providers/ai/finance_ai.py` | `domains/finance/services/` | 204 | HIGH |
| `providers/ai/sentiment.py` (partial) | `domains/catalog/services/` | 250 | HIGH |
| `providers/ai/text.py` (partial) | `domains/catalog/services/` | 300 | HIGH |
| `providers/ai/ai_variant_config.py` | `domains/catalog/services/` | 442 | MEDIUM |
| `providers/ai/image_similarity.py` | `domains/catalog/services/` | ~250 | MEDIUM |
| `providers/async_workers.py` (partial) | `domains/catalog/services/` | 200 | MEDIUM |

---

## Positive Findings

1. **No domain imports** — No provider imports from `domains/`. This law is respected.
2. **No infrastructure.messaging imports** — This law is respected.
3. **HAS_ flags present in many providers** — `analytics`, `auth/jwt`, `auth/oauth`, `auth/totp`, `automation`, `barcode`, `bg_removal`, `comms/twilio`, `comms/whatsapp`, `finance`, `geography/rates`, `image/ocr`, `image/bg_remover`, `payments/stripe_sdk`, `payments/paypal`, `qr`, `scanner`, `sentiment` all have proper flags.
4. **Graceful degradation** — Most providers with HAS_ flags properly degrade when SDK is missing.
5. **Proper async patterns** — `async_workers.py` correctly uses `asyncio.to_thread` and `ThreadPoolExecutor` for CPU-bound work.
6. **No hardcoded secrets** — All API keys/tokens come from environment variables via `config.py`.
7. **Logging** — All providers use `logging.getLogger(__name__)` appropriately.
8. **Self-contained providers** — Most providers (auth, payments, storage, geography) are properly self-contained.

---

## Recommended Action Plan

1. **Phase 1 (CRITICAL):** Move `providers/media/` → `domains/media/services/`
2. **Phase 2 (CRITICAL):** Move `ai/recommendation.py`, `ai/price_intelligence.py`, `ai/search.py`, `ai/chatbot.py` to appropriate domains
3. **Phase 3 (HIGH):** Move `shipping/shipping_calculator.py`, `ai/finance_ai.py`, and partial extractions from `vision.py`, `voice_to_text.py`, `text.py`
4. **Phase 4 (MEDIUM):** Add missing `HAS_` flags, resolve cross-provider imports, clean up dead code
5. **Phase 5 (LOW):** Split `config.py`, standardize `observability.py` pattern, delete empty `geo/` directory
