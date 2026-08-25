# Provider Tools Guide

## 1. Overview

The `providers/` layer contains **external SDK wrappers only**. Each module wraps a third-party service (Stripe, Twilio, Ollama, rembg, etc.) so that domain services never import vendor SDKs directly.

**Core principle:** Providers accept primitives (strings, bytes, dicts) and return primitives. They contain zero business logic.

```
providers/
├── ai/            # Ollama LLM, vision, embeddings, search, MCP server
├── analytics/     # Admin dashboard analytics
├── auth/          # JWT, TOTP, OAuth (Google/Facebook), Apple Sign-In
├── automation/    # APScheduler background jobs
├── br_remover/    # Legacy background removal model variants
├── comms/         # Twilio SMS, WhatsApp, email (SMTP/Resend)
├── finance/       # Bank API dispatch
├── geo/           # FastAPI location service (IP geocode, reverse geocode)
├── geography/     # IP geolocation, currency rates, country data
├── image/         # Background removal, OCR, parcel verification
├── media/         # OpenCV (cv2) access point
├── news/          # RSS/Atom feed aggregation
├── payments/      # Stripe, PayPal, PayTabs, Tap, Thawani, Connect
├── security/      # Encryption (Fernet), threat intel, watchlist
├── voice/         # Voice-to-text transcription, command parsing
├── _base.py       # BaseProvider / BaseAIProvider ABCs
├── config.py      # ProviderConfig settings dataclass
├── http.py        # HTTP client utilities
├── storage.py     # S3 / boto3 client factory
└── parcel_verification.py  # Top-level parcel verification entry
```

## 2. Architecture Rule

> **Providers must NOT import from `domains/`.**

| Layer | Imports From | Exports |
|-------|-------------|---------|
| `providers/` | `infrastructure.utils.*`, external SDKs only | Pure functions, primitives |
| `domains/*/services/` | `providers/`, `infrastructure/` | Business logic |
| `modules/*/routers/` | `domains/*/services/` | HTTP endpoints |

If a provider file imports from `domains/`, it violates the layer boundary. Business logic belongs in `domains/*/services/`, not in providers.

## 3. How to Use

Domain services import provider functions directly:

```python
# In domains/finance/services/payment_service.py
from providers.payments.stripe import create_payment_intent
from providers.payments.base import BasePaymentGateway, register_provider
from providers.ai.text import embed_text, cosine_similarity
from providers.image.bg_remover import remove_background
from providers.comms.email import deliver_email
```

For class-based providers, subclass the ABC and register:

```python
from providers.payments.base import BasePaymentGateway, GatewayDefinition, register_provider

class MyGateway(BasePaymentGateway):
    display_name = "My Gateway"
    def process_payment(self, amount, currency, credentials, **kwargs):
        # Call vendor SDK here
        return PaymentResult(success=True, transaction_id="...")

register_provider(GatewayDefinition(
    code="mygateway",
    kind="custom",
    label="My Gateway",
    module=__name__,
    settings_resolver=lambda db: {},
    is_configured=lambda db: True,
    operations={"create": lambda *a, **k: None},
))
```

## 4. Provider Reference

---

### 4.1 `auth/` — Authentication Providers

Wraps JWT, TOTP, and social OAuth SDKs.

#### `jwt.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `decode_unverified_claims` | `(token: str) -> dict` | Read JWT claims without verifying signature (e.g. to read `jti`) |
| `decode_token` | `(token: str, secret: str, algorithms) -> dict` | Verify and decode a signed JWT |

```python
from providers.auth.jwt import decode_token, decode_unverified_claims

claims = decode_unverified_claims(token)  # Read jti without verifying
payload = decode_token(token, secret="my-secret", algorithms=["HS256"])
```

#### `totp.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `generate_secret` | `() -> str` | Generate a new base32 TOTP secret |
| `provisioning_uri` | `(secret: str, name: str, issuer_name: str) -> str` | Build `otpauth://` URI for QR enrollment |
| `verify` | `(secret: str, code: str, valid_window: int = 0) -> bool` | Verify a TOTP code against secret |

```python
from providers.auth.totp import generate_secret, provisioning_uri, verify

secret = generate_secret()
uri = provisioning_uri(secret, name="user@example.com", issuer_name="ZOZI")
is_valid = verify(secret, "123456")
```

#### `oauth.py` (Google + Facebook)
| Function | Signature | Description |
|----------|-----------|-------------|
| `verify_google_id_token` | `(id_token: str) -> dict` | Validate a Google identity token |
| `exchange_google_code` | `(code, redirect_uri, client_id, client_secret) -> dict` | Exchange OAuth code for Google tokens |
| `get_google_userinfo` | `(access_token: str) -> dict` | Fetch Google user profile |
| `exchange_facebook_code` | `(code, redirect_uri, client_id, client_secret) -> dict` | Exchange OAuth code for Facebook tokens |
| `get_facebook_profile` | `(access_token: str) -> dict` | Fetch Facebook user profile |
| `build_google_authorization_url` | `(*, client_id, redirect_uri, state, scope, prompt) -> str` | Build Google OAuth redirect URL |
| `build_facebook_authorization_url` | `(*, client_id, redirect_uri, state, scope) -> str` | Build Facebook OAuth dialog URL |

```python
from providers.auth.oauth import exchange_google_code, get_google_userinfo

tokens = exchange_google_code(code="...", redirect_uri="...", client_id="...", client_secret="...")
profile = get_google_userinfo(tokens["access_token"])
```

#### `apple.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `build_apple_auth_url` | `(client_id, redirect_uri, state, scope, response_mode) -> str` | Build Apple authorization URL |
| `create_apple_client_secret` | `(team_id, client_id, key_id, private_key_pem, max_age) -> str` | Create ES256-signed JWT client secret |
| `exchange_apple_code` | `(code, redirect_uri, client_id, client_secret) -> dict` | Exchange Apple auth code for tokens |
| `verify_apple_identity` | `(id_token: str, client_id: Optional[str]) -> dict` | Validate Apple id_token against JWKS |
| `get_apple_userinfo` | `(id_token: str, client_id: Optional[str]) -> dict` | Extract user identity from id_token |

---

### 4.2 `payments/` — Payment Gateway Providers

Wraps Stripe, PayPal, PayTabs, Tap, Thawani, and generic gateway adapters.

#### `base.py`
| Class/Function | Description |
|----------------|-------------|
| `BasePaymentGateway` | ABC all gateways implement. Methods: `process_payment()`, `process_refund()`, `test_connection()`, `verify_webhook_signature()`, `normalize_webhook_payload()` |
| `GatewaySettings` | Resolved runtime config for a gateway (provider_code, secret_key, mode, etc.) |
| `GatewayDefinition` | Registration record (code, kind, label, settings_resolver, operations) |
| `register_provider(definition)` | Register a gateway adapter |
| `get_provider(code)` | Look up a registered gateway |
| `dispatch_provider_operation(code, operation, *args, **kwargs)` | Dispatch create/confirm/webhook to a gateway |

#### `stripe.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `create_payment_intent` | `(body, current_user, db) -> dict` | Create a Stripe PaymentIntent, returns `client_secret` |
| `create_stripe_checkout_session` | `(body, current_user, db) -> dict` | Create a Stripe Checkout Session |
| `confirm_card_payment` | `(body, current_user, db) -> dict` | Synchronously confirm a card payment |
| `handle_stripe_webhook` | `(request, db) -> dict` | Verify + process Stripe webhook event |
| `refund_payment_intent` | `(payment_intent: str, api_key: str \| None) -> dict` | Issue a Stripe refund |

#### `paypal.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `create_paypal_order` | `(body, current_user, db) -> dict` | Create PayPal order, returns `approve_url` |
| `capture_paypal_order` | `(body, current_user, db) -> dict` | Capture an approved PayPal order |
| `handle_paypal_webhook` | `(request, db) -> dict` | Verify + process PayPal webhook |

#### `paytabs.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `create_paytabs_charge` | `(body, current_user, db) -> dict` | Create a PayTabs charge page |
| `confirm_paytabs_payment` | `(body, current_user, db) -> dict` | Verify and finalize a PayTabs payment |
| `handle_paytabs_callback` | `(request, db) -> dict` | Process PayTabs server callback |

#### `tap.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `create_tap_charge` | `(body, current_user, db) -> dict` | Create a Tap charge, returns `redirect_url` |
| `confirm_tap_payment` | `(body, current_user, db) -> dict` | Verify and finalize a Tap payment |
| `handle_tap_webhook` | `(request, db) -> dict` | Process Tap webhook |
| `refund_tap_charge` | `(charge_id, amount, api_key, reason, api_base_url) -> dict` | Issue a Tap refund |

#### `thawani.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `create_thawani_session` | `(body, current_user, db) -> dict` | Create a Thawani hosted checkout (OMR) |
| `handle_thawani_webhook` | `(request, db) -> dict` | Process Thawani webhook |
| `confirm_thawani_payment` | `(body, current_user, db) -> dict` | Poll Thawani session status |

#### `generic.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `create_generic_gateway_payment` | `(body, current_user, db) -> dict` | Initiate payment for any custom gateway |
| `handle_generic_gateway_callback` | `(request, provider_code, db) -> dict` | Process callback from custom gateway |
| `confirm_generic_gateway_payment` | `(body, current_user, db) -> dict` | Confirm a custom gateway payment |

#### `connect.py` (Stripe Connect)
| Function | Signature | Description |
|----------|-----------|-------------|
| `configure_stripe_connect` | `(api_key, api_version) -> None` | Set Stripe API key/version |
| `create_connect_account` | `(**kwargs) -> Any` | Create a Stripe Connect account |
| `modify_connect_account` | `(account_id, **kwargs) -> Any` | Modify a Connect account |
| `create_connect_transfer` | `(**kwargs) -> Any` | Create a Connect transfer (payout) |

---

### 4.3 `ai/` — AI & ML Providers

Wraps Ollama LLM, HuggingFace, OpenAI, and MCP server.

#### `text.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `_ollama_chat` | `(prompt: str, model: str \| None) -> str` | Send a chat prompt to Ollama |
| `_ollama_vision_chat` | `(prompt: str, image_bytes: bytes, model: str \| None) -> str` | Send vision + prompt to Ollama |
| `transcribe_audio` | `(audio_bytes: bytes, model: str \| None) -> str` | Transcribe audio via Ollama whisper |
| `embed_text` | `(text: str, model: str \| None) -> List[float]` | Generate embedding vector |
| `cosine_similarity` | `(a: List[float], b: List[float]) -> float` | Cosine similarity between two vectors |
| `_extract_json` | `(text: str) -> Optional[dict]` | Extract JSON from text with phi3:mini fallback fixes |
| `translate_en_to_ar` | `(text: str) -> str` | English to Arabic translation (Ollama + glossary fallback) |
| `_ollama_chat_completion` | `(base_url, model, content, images, ...) -> Optional[str]` | Low-level Ollama chat completion |
| `ollama_chat_json` | `(prompt, model, base_url, timeout, temperature, num_ctx) -> dict` | Generate structured JSON from Ollama |

#### `vision.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `analyze_product_image` | `(image_bytes, filename, generate_copy, use_vision, subcategory) -> dict` | Analyze product image: extract name, category, color, tags, variants |
| `classify_product_type` | `(product_name, category, subcategory) -> str` | Classify product type (clothing/electronic/etc.) |
| `suggest_price` | `(image_bytes, product_name, category) -> dict` | AI price suggestion with fallback |
| `normalize_category` | `(product_name, description) -> str` | Normalize category from name/description |

#### `chatbot.py`
| Class | Description |
|-------|-------------|
| `ChatbotProvider` | AI chatbot with session history. Methods: `process_query(query, session_id, user_id)`, `get_session_history(session_id)`, `clear_session(session_id)` |

#### `search.py`
| Class | Description |
|-------|-------------|
| `AdvancedSearchEngine` | AI-powered search with NLP parsing, vector embeddings, autocomplete, fuzzy matching. Methods: `parse_query(query)`, `search(query, filters, limit, offset, sort_by)`, `load_product_catalog(products)`, `fuzzy_search(query, limit, cutoff)` |

#### `finance_ai.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `parse_email_to_ledger` | `(email_text: str) -> FinanceAIResult` | Parse email body into ledger entries |
| `extract_bill_fields` | `(image_bytes: bytes) -> FinanceAIResult` | OCR a bill image and extract fields |
| `suggest_reconciliation_match` | `(transaction: dict, candidates: list) -> FinanceAIResult` | Suggest best match for a transaction |

#### `huggingface.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `call_hf_image_api` | `(model: str, image_bytes: bytes, timeout) -> Optional[bytes]` | POST image to HF Inference API, return image bytes |

#### `openai_client.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `transcribe_audio` | `(audio_bytes, api_key, source_language) -> str` | Transcribe via OpenAI Whisper |
| `translate_text` | `(text, api_key, target_language) -> str` | Translate via OpenAI GPT |

#### `web_search.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `duckduckgo_search` | `(query, user_agent, timeout, snippet_limit) -> List[dict]` | DuckDuckGo HTML search |

#### `zozi_mcp.py`
Exposes the ZOZI backend as Model Context Protocol tools. Run with `python -m services.mcp.zozi_mcp`.

---

### 4.4 `geography/` — Geographic Data Providers

#### `geo.py`
| Class/Function | Signature | Description |
|----------------|-----------|-------------|
| `CountryDetectionProvider` | Class | Detect country from IP. Methods: `detect_country_from_ip(headers, client_host)`, `get_country_by_coordinates(lat, lon)` |
| `resolve_ip_location` | `(ip, client_host, forwarded_for, real_ip) -> IpLocation` | Resolve IP to coordinates via ipwho.is / ip-api.com |
| `reverse_geocode` | `(latitude, longitude) -> ReverseLocation` | Reverse geocode via OpenStreetMap Nominatim |

#### `geoip.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `lookup_coordinates` | `(ip: str) -> Optional[Tuple[float, float]]` | GeoIP city lookup (lat/lon) |
| `lookup_country_code` | `(ip: str) -> Optional[str]` | GeoIP country code lookup |

#### `ip.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `detect_country_from_ip` | `(ip_address: str) -> Optional[str]` | IP -> country code via IP-API with ipapi.co fallback |
| `geocode_location` | `(name, count, language, timeout) -> Optional[list]` | Geocode place name via Open-Meteo |

#### `rates.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `fetch_rates` | `() -> (dict[str, Decimal], str)` | Fetch FX rates (TTL cached), source='live' or 'fallback' |
| `lookup_currency_from_wikidata` | `(country: str) -> str \| None` | Look up currency code from Wikidata |
| `normalize_currency_code` | `(code: str \| None, default: str) -> str` | Normalize to 3-letter uppercase currency code |
| `reset_rate_cache` | `() -> None` | Force next fetch_rates to hit upstream |

#### `country.py`
| Class | Description |
|-------|-------------|
| `CountrySearchProvider` | Country search with built-in data. Methods: `search_country(query)`, `get_country_details(code)`, `get_country_by_name(name)`, `get_countries_by_region(region)`, `get_currencies()` |

#### `map.py`
| Class | Description |
|-------|-------------|
| `LocationProvider` | Map/location provider. Methods: `resolve_ip(ip)`, `reverse_geocode(lat, lon)`, `calculate_distance(lat1, lon1, lat2, lon2)` |

#### `external_data.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `fetch_restcountries` | `(session, country_code) -> dict` | Country identity from RestCountries |
| `fetch_worldbank` | `(session, country_code) -> Any` | Economic data from World Bank |
| `fetch_geodb_cities` | `(session, country_code) -> list` | Cities from GeoDB |
| `fetch_nager_holidays` | `(session, country_code, year) -> list` | Public holidays from Nager.Date |

#### `country_http.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `get_json` | `(url, params, timeout) -> Optional[Any]` | GET JSON or None on failure |
| `fetch_restcountries_raw` | `(term) -> Optional[Any]` | Fetch country by code or name |
| `fetch_worldbank_indicator_raw` | `(code, indicator, per_page) -> Optional[Any]` | World Bank indicator data |
| `fetch_nager_holidays_raw` | `(code, year) -> Optional[Any]` | Public holidays |
| `fetch_vat_rate_raw` | `(country_code) -> Optional[Any]` | VAT rates |

---

### 4.5 `image/` — Image Processing Providers

#### `bg_remover.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `remove_background` | `(image_bytes: bytes, model: str \| None, strategy: str \| None) -> bytes` | Core background removal entry point |
| `remove_background_preset` | `(image_bytes: bytes, preset_name: str) -> bytes` | Remove bg using a named preset |
| `remove_background_model` | `(image_bytes: bytes, model_name: str) -> bytes` | Remove bg using specific model |
| `remove_background_strategy` | `(image_bytes: bytes, strategy: str) -> bytes` | Remove bg using a processing strategy |
| `magic_erase` | `(image_bytes: bytes, mask: np.ndarray) -> bytes` | Erase regions from image using mask |
| `rembg_remove_bytes` | `(data: bytes, session, alpha_matting, post_process_mask) -> bytes` | Run rembg on raw bytes |
| `create_rembg_session` | `(model_name: str) -> Any` | Create a rembg session |
| `process_folder` | `(input_folder, output_folder, strategy, model, background) -> List[dict]` | Batch process images |
| `process_product_image` | `(image_bytes, background, output_format) -> dict` | Process product image (returns base64) |

**Strategies:** `clean_commercial`, `precision_geometry`, `production_birefnet`, `ultimate_v11`, `ultimate_v12`, `variant_testing`, `general`

**Available models:** `birefnet-general`, `isnet-general-use`, `u2net`, `u2netp`, `silueta`, `sam2`, `vitmatte`, etc.

#### `ocr.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `parse_bill_text` | `(image_bytes: bytes) -> dict` | OCR a bill/receipt, extract vendor/date/total/items |
| `parse_statement_csv` | `(csv_bytes: bytes) -> dict` | Parse financial CSV statement |
| `ocr_image_array` | `(image_array: np.ndarray) -> Optional[Tuple[str, str]]` | Run pytesseract on preprocessed array |

#### `parcel_verification.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `verify_parcel_photo` | `(image_bytes, item_descriptions, reference_image_bytes, run_ssim, run_feature_match, run_homography, run_vision_ai, fast_mode) -> dict` | Multi-engine parcel verification (SSIM + ORB + homography + vision AI) |
| `verify_parcel_fast` | `(image_bytes, item_descriptions, reference_image_bytes) -> dict` | Fast verification (no vision AI) |

---

### 4.6 `comms/` — Communication Providers

#### `email.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `deliver_email` | `(to, subject, html, *, from_address, provider, config) -> None` | Send email via `resend`, `smtp`, or `console` preview |

```python
from providers.comms.email import deliver_email

deliver_email(
    to="user@example.com",
    subject="Order Confirmed",
    html="<h1>Your order is confirmed</h1>",
    from_address="noreply@zozi.com",
    provider="resend",
    config={"resend_api_key": "re_..."},
)
```

#### `twilio.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `create_twilio_client` | `(account_sid: str, auth_token: str) -> Client \| None` | Build a Twilio REST client |

#### `whatsapp.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `send_whatsapp_message` | `(to, body, *, from_number, account_sid, auth_token, preview) -> dict` | Send WhatsApp message via Twilio |

---

### 4.7 `security/` — Security Providers

#### `encryption.py`
Re-exports from the `cryptography` SDK:
- `Fernet` — Symmetric encryption
- `hashes` — Hash algorithms
- `PBKDF2HMAC` — Password-based key derivation

```python
from providers.security.encryption import Fernet

key = Fernet.generate_key()
cipher = Fernet(key)
encrypted = cipher.encrypt(b"secret data")
```

#### `threat_intel.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `fetch_tor_exit_list` | `() -> List[str]` | Fetch Tor exit-node IP list |

#### `watchlist.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `screen_watchlist` | `(employee_code, full_name, country_code, api_url) -> dict` | Query watchlist/sanctions screening API |

---

### 4.8 `finance/` — Finance Providers

#### `bank_api.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `test_connection` | `(base_url, batch_path, auth_token, timeout) -> dict` | Probe bank API reachability |
| `dispatch_batch` | `(base_url, batch_path, auth_token, idempotency_key, payload, timeout) -> dict` | Dispatch transfer batch to bank API |

---

### 4.9 `voice/` — Voice Providers

#### `voice_to_text.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `transcribe_audio` | `(audio_bytes: bytes, model: str \| None) -> str` | Transcribe audio via Ollama whisper |
| `process_product_voice_command` | `(transcript: str) -> dict` | Extract product variants/quantity from voice transcript |
| `process_finance_voice_command` | `(transcript: str) -> dict` | Extract finance task info from voice transcript |

---

### 4.10 `news/` — News Aggregation

#### `rss_provider.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `fetch_rss_entries` | `(url: str, timeout: float) -> List[Any]` | Fetch and parse RSS/Atom feed |
| `fetch_api_payload` | `(url, headers, timeout) -> dict` | Fetch JSON news API payload |

---

### 4.11 `storage/` — Storage Providers

#### `storage.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `create_s3_client` | `(bucket, region, endpoint_url, access_key, secret_key) -> Any` | Create boto3 S3 client |
| `create_ssm_client` | `(region: str) -> Any` | Create boto3 SSM client for secrets |

---

### 4.12 `analytics/` — Analytics Provider

#### `analytics.py`
| Class | Description |
|-------|-------------|
| `AnalyticsProvider` | Admin analytics. Methods: `get_dashboard_summary(country_code, period)`, `get_chatbot_analytics(country_code, period)`, `get_product_performance(country_code, limit)`, `get_sales_trends(country_code, period)`, `get_ai_insights(country_code)` |

---

### 4.13 `automation/` — Automation Provider

#### `scheduler.py`
| Function | Signature | Description |
|----------|-----------|-------------|
| `create_scheduler` | `(timezone: str = "UTC") -> AsyncIOScheduler` | Create APScheduler background scheduler |
| `add_interval_job` | `(scheduler, func, seconds, args, id, **kwargs) -> None` | Register an interval job |

---

### 4.14 `geo/` — Location Service (FastAPI App)

A standalone FastAPI application for IP geolocation and reverse geocode.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/geo/from-ip` | GET | Geolocate an IP (query: `ip`, headers: `X-Forwarded-For`, `X-Real-IP`) |
| `/api/geo/locate` | GET | Auto-detect client IP and geolocate |
| `/api/geo/reverse` | POST | Reverse geocode (body: `{lat, lon}`) |
| `/api/geo/resolve` | POST | Resolve IP (body: `{ip}`) |

---

### 4.15 `media/` — OpenCV Access Point

Re-exports `cv2` and `ximgproc` so services never import OpenCV directly.

```python
from providers.media import cv2, HAS_CV2

if HAS_CV2:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
```

---

### 4.16 Root-Level Providers

#### `_base.py`
| Class | Description |
|-------|-------------|
| `BaseProvider` | ABC for all providers. Methods: `initialize()`, `is_available()`, `health_check()` |
| `BaseAIProvider` | ABC for AI providers. Methods: `load_model()`, `predict()`, `preprocess()`, `postprocess()` |

#### `config.py`
| Symbol | Description |
|--------|-------------|
| `ProviderConfig` | Dataclass with all provider settings (HF token, OpenAI key, Ollama URL, rembg models, search/geo/analytics defaults) |
| `settings` | Singleton instance of `ProviderConfig` |

---

## 5. Adding New Providers

### Guidelines

1. **Create a new subdirectory** under `providers/` (e.g. `providers/sms/`).
2. **Wrap only vendor SDK calls** — no business logic, no domain model imports.
3. **Accept and return primitives** — strings, bytes, dicts, lists.
4. **Create an `__init__.py`** that re-exports the public API.
5. **Document the vendor SDK** in the module docstring.

### Template

```python
"""New provider — wraps the `vendor_sdk` package.

External vendor HTTP/SDK calls are encapsulated here so services
orchestrate through these helpers instead of importing vendor_sdk directly.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

def do_something(input_data: str, api_key: str) -> Dict[str, Any]:
    """One-line description of what this does."""
    try:
        import vendor_sdk
        result = vendor_sdk.call(input_data, key=api_key)
        return {"success": True, "data": result}
    except Exception as exc:
        logger.error("vendor_sdk call failed: %s", exc)
        return {"success": False, "error": str(exc)}

__all__ = ["do_something"]
```

### Registration Pattern (for gateway-style providers)

```python
from providers.payments.base import BasePaymentGateway, GatewayDefinition, register_provider

class NewGateway(BasePaymentGateway):
    display_name = "New Gateway"
    def process_payment(self, amount, currency, credentials, **kwargs):
        # Vendor SDK call here
        pass

register_provider(GatewayDefinition(
    code="newgateway",
    kind="custom",
    label="New Gateway",
    module=__name__,
    settings_resolver=lambda db: {},
    is_configured=lambda db: True,
    operations={},
))
```

### Key Dependencies by Provider

| Provider | External SDK |
|----------|-------------|
| `auth/jwt.py` | `python-jose` |
| `auth/totp.py` | `pyotp` |
| `auth/apple.py` | `PyJWT`, `requests` |
| `payments/*` | `stripe`, `httpx` |
| `ai/text.py`, `ai/vision.py` | `urllib` (Ollama HTTP) |
| `ai/huggingface.py` | `requests` |
| `ai/openai_client.py` | `httpx` |
| `image/bg_remover.py` | `rembg`, `opencv-python`, `numpy` |
| `image/ocr.py` | `pytesseract`, `opencv-python` |
| `image/parcel_verification.py` | `scikit-image`, `opencv-python`, `scipy` |
| `comms/twilio.py` | `twilio` |
| `comms/email.py` | `smtplib`, `urllib` (Resend) |
| `security/encryption.py` | `cryptography` |
| `automation/scheduler.py` | `apscheduler` |
| `storage.py` | `boto3` |
| `news/rss_provider.py` | `feedparser`, `httpx` |
| `geography/*` | `httpx`, `requests`, `geoip2` (optional) |
| `geo/main.py` | `fastapi`, `requests` |
