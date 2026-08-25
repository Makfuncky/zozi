# Provider Tools Guide

## Overview

The `backend/providers/` package contains all third-party SDK/API adapters for the ZOZI platform. Providers encapsulate external service integrations — they wrap vendor SDKs, handle HTTP calls, and expose clean primitive interfaces that domain services consume.

**Key principle**: Providers are called ONLY by services/jobs. Modules and domain layers must never import providers directly.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Modules (routers/controllers)                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Domain Services (business logic)                      │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  Providers (3rd-party SDK wrappers)             │  │  │
│  │  │  - Stripe, Twilio, OpenAI, Ollama, etc.         │  │  │
│  │  │  - Take primitive inputs (str, bytes, dict)     │  │  │
│  │  │  - Return primitive outputs (dict, str, bool)   │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Rules

1. **Providers must NOT import from `domains/`** — business logic stays in services
2. **Providers take primitive inputs** — strings, bytes, dicts, not ORM models
3. **Providers return primitive outputs** — dicts, strings, bools, not domain entities
4. **Services orchestrate** — they call providers, then apply business rules
5. **Optional SDKs degrade gracefully** — missing dependencies return None/empty, never crash

---

## Base Classes

### `BaseProvider` (`providers/_base.py`)

Abstract base for all providers. Requires `is_available()` and `health_check()` implementations.

```python
from providers._base import BaseProvider

class MyProvider(BaseProvider):
    def is_available(self) -> bool:
        return self._initialized

    def health_check(self) -> dict[str, Any]:
        return {"status": "healthy", "provider": self.name}
```

### `BaseAIProvider` (`providers/_base.py`)

Extends `BaseProvider` for AI/model inference providers. Adds `load_model()`, `predict()`, `preprocess()`, `postprocess()`.

```python
from providers._base import BaseAIProvider

class MyAIProvider(BaseAIProvider):
    def load_model(self) -> None:
        self._model_loaded = True

    def predict(self, input_data):
        return self.postprocess(self._model(input_data))

    def preprocess(self, input_data):
        return input_data

    def postprocess(self, output):
        return output
```

---

## Provider: `ai` — Artificial Intelligence

**External services**: Ollama (LLM inference), OpenAI (Whisper/translation), HuggingFace (BLIP/BART), DuckDuckGo (web search)

### Exports

| Symbol | Purpose |
|--------|---------|
| `suggest_price` | AI price suggestion from product image |
| `normalize_category` | Keyword-based category normalization |
| `VariantConfig` | Dataclass for product variant detection config |
| `analyze_product_image` | Vision AI product analysis |
| `classify_product_type` | Product type detection |
| `_ollama_chat` | Send chat prompt to Ollama |
| `_ollama_vision_chat` | Send vision prompt to Ollama |
| `_OLLAMA_TEXT_MODEL` | Default text model name |
| `_extract_json` | Extract JSON from LLM response |
| `embed_text` | Generate text embedding via Ollama |
| `cosine_similarity` | Compute cosine similarity between vectors |
| `transcribe_audio` | Speech-to-text via Ollama Whisper |
| `translate_en_to_ar` | English to Arabic translation |
| `ChatbotProvider` | AI chatbot with session history |
| `AdvancedSearchEngine` | AI-powered product search with vectorization |
| `FinanceAIResult` | Dataclass for finance AI results |
| `parse_email_to_ledger` | Parse email body into ledger entries |
| `extract_bill_fields` | Extract structured fields from bill text |
| `suggest_reconciliation_match` | Suggest reconciliation matches |

### Usage Examples

```python
# Vision analysis
from providers.ai.vision import analyze_product_image, suggest_price

result = await analyze_product_image(image_bytes, product_name="")
price = await suggest_price(image_bytes, category="electronics")

# Text/embedding
from providers.ai.text import _ollama_chat, embed_text, cosine_similarity

response = _ollama_chat("Summarize this product description")
embedding = await embed_text("blue cotton t-shirt")
similarity = cosine_similarity(vec1, vec2)

# Chatbot
from providers.ai.chatbot import ChatbotProvider

chatbot = ChatbotProvider()
result = chatbot.process_query("Find me running shoes", session_id="sess_123")
# Returns: {"session_id": ..., "intent": "product_search", "response": ...}

# Search
from providers.ai.search import AdvancedSearchEngine

engine = AdvancedSearchEngine(db=db_session)
results = engine.search("red shoes under $50", category="fashion")

# Finance AI
from providers.ai.finance_ai import parse_email_to_ledger, extract_bill_fields

ledger = parse_email_to_ledger(email_body_text)
fields = extract_bill_fields(receipt_text)
```

---

## Provider: `analytics` — Admin Analytics

**External services**: Analytics API (configurable via `ANALYTICS_API_KEY`)

### Exports

| Symbol | Purpose |
|--------|---------|
| `AnalyticsProvider` | Dashboard and chatbot analytics |

### Usage Example

```python
from providers.analytics.analytics import AnalyticsProvider

analytics = AnalyticsProvider()
summary = analytics.get_dashboard_summary(country_code="US", period="30d")
chatbot_stats = analytics.get_chatbot_analytics(period="7d")
```

---

## Provider: `auth` — Authentication

**External services**: Google OAuth, Apple Sign-In, Facebook OAuth, pyotp (TOTP/2FA), python-jose (JWT)

### Exports

| Symbol | Purpose |
|--------|---------|
| `OAuthProviderError` | Exception for OAuth failures |
| `verify_google_id_token` | Validate Google identity token |
| `exchange_google_code` | Exchange Google auth code for tokens |
| `get_google_userinfo` | Fetch Google user profile |
| `exchange_facebook_code` | Exchange Facebook auth code |
| `get_facebook_profile` | Fetch Facebook user profile |
| `build_apple_auth_url` | Build Apple OAuth authorization URL |
| `create_apple_client_secret` | Create Apple client secret JWT |
| `exchange_apple_code` | Exchange Apple auth code |
| `get_apple_userinfo` | Decode Apple id_token claims |
| `verify_apple_identity` | Verify Apple identity token |
| `generate_secret` | Generate TOTP secret |
| `provisioning_uri` | Build otpauth:// URI for QR enrollment |
| `verify_totp` | Verify TOTP code against secret |
| `JWTError` | JWT decode error |
| `decode_token` | Verify and decode signed JWT |
| `decode_unverified_claims` | Read JWT claims without verification |

### Usage Examples

```python
# Google OAuth
from providers.auth.oauth import exchange_google_code, get_google_userinfo

tokens = exchange_google_code(code="...", redirect_uri="...")
user_info = get_google_userinfo(access_token=tokens["access_token"])

# Apple Sign-In
from providers.auth.apple import build_apple_auth_url, exchange_apple_code

auth_url = build_apple_auth_url(client_id="...", redirect_uri="...", state="...")
result = exchange_apple_code(code="...", client_id="...", redirect_uri="...")

# TOTP/2FA
from providers.auth.totp import generate_secret, provisioning_uri, verify

secret = generate_secret()
uri = provisioning_uri(secret, name="user@example.com", issuer_name="ZOZI")
is_valid = verify(secret, code="123456")

# JWT
from providers.auth.jwt import decode_token, decode_unverified_claims

claims = decode_token(token, secret="my-secret", algorithms=["HS256"])
unverified = decode_unverified_claims(token)  # Read jti without verifying
```

---

## Provider: `automation` — Background Jobs

**External services**: APScheduler (async scheduler)

### Exports

| Symbol | Purpose |
|--------|---------|
| `AsyncIOScheduler` | Re-exported APScheduler class |
| `IntervalTrigger` | Re-exported interval trigger |
| `create_scheduler` | Factory for background scheduler |
| `add_interval_job` | Register a recurring interval job |

### Usage Example

```python
from providers.automation.scheduler import create_scheduler, add_interval_job

scheduler = create_scheduler(timezone="UTC")

add_interval_job(
    scheduler,
    func=my_cleanup_task,
    seconds=3600,  # Run every hour
    id="cleanup_job",
)

scheduler.start()
```

---

## Provider: `comms` — Communications

**External services**: Twilio (SMS/voice), Twilio WhatsApp Cloud API, Resend (email), SMTP

### Exports

| Symbol | Purpose |
|--------|---------|
| `HAS_TWILIO` | Whether twilio SDK is available |
| `TwilioRestException` | Twilio error type |
| `create_twilio_client` | Build Twilio REST client |
| `HAS_WHATSAPP` | Whether WhatsApp delivery is available |
| `send_whatsapp_message` | Send WhatsApp text message |

### Usage Examples

```python
# Twilio
from providers.comms.twilio import create_twilio_client, HAS_TWILIO

if HAS_TWILIO:
    client = create_twilio_client(account_sid="...", auth_token="...")
    client.messages.create(to="+1234567890", from_="+0987654321", body="Hello")

# WhatsApp
from providers.comms.whatsapp import send_whatsapp_message

result = send_whatsapp_message(
    to="+1234567890",
    body="Your order has shipped!",
    from_number="+0987654321",
    account_sid="...",
    auth_token="...",
)
# Returns: {"delivered": True, "message_sid": "..."}

# Email
from providers.comms.email import deliver_email

await deliver_email(
    to="user@example.com",
    subject="Order Confirmation",
    html="<h1>Thank you for your order!</h1>",
    from_address="noreply@zozi.com",
    api_key="re_...",  # Resend API key
)
```

---

## Provider: `finance` — Banking/Treasury

**External services**: Configurable bank/treasury API

### Exports

| Symbol | Purpose |
|--------|---------|
| `BankApiError` | Exception for bank API failures |
| `test_connection` | Probe bank API with OPTIONS request |
| `dispatch_batch` | Dispatch a batch of transfers |

### Usage Example

```python
from providers.finance.bank_api import test_connection, dispatch_batch, BankApiError

# Test connectivity
result = test_connection(
    base_url="https://api.bank.com",
    batch_path="/v1/batches",
    auth_token="...",
    timeout=10.0,
)
# Returns: {"reachable": True, "ok": True, "status_code": 200}

# Dispatch transfers
try:
    response = dispatch_batch(
        base_url="https://api.bank.com",
        batch_path="/v1/batches",
        auth_token="...",
        transfers=[{"amount": 100.0, "recipient": "..."}],
    )
except BankApiError as exc:
    logger.error("Bank API failed: %s (status=%s)", exc, exc.status_code)
```

---

## Provider: `geography` — Location & Currency

**External services**: IP geolocation APIs, open.er-api.com (FX rates), Wikidata (currency lookup)

### Exports

| Symbol | Purpose |
|--------|---------|
| `CountryDetectionProvider` | Detect country from IP/headers |
| `LocationProvider` | Resolve IP to location data |
| `CountrySearchProvider` | Search country details |
| `RATE_CACHE_TTL_SECONDS` | FX rate cache TTL |
| `normalize_currency_code` | Normalize currency code to ISO 4217 |
| `fetch_rates` | Fetch live FX rates with caching |
| `lookup_currency_from_wikidata` | Resolve currency from country via Wikidata |
| `reset_rate_cache` | Clear FX rate cache |
| `rate_cache_expiry` | Get current cache expiry timestamp |

### Usage Examples

```python
# Country detection from request
from providers.geography.geo import CountryDetectionProvider

detector = CountryDetectionProvider()
country_code, country_name = detector.detect_country_from_ip(
    request_headers={"X-Forwarded-For": "1.2.3.4"},
)

# IP geolocation
from providers.geography.map import LocationProvider

locator = LocationProvider()
location = locator.resolve_ip("1.2.3.4")
# Returns: {"ip": ..., "country": "United States", "city": "New York", ...}

# Country search
from providers.geography.country import CountrySearchProvider

search = CountrySearchProvider()
results = search.search_country("united")
details = search.get_country_details("US")

# FX rates
from providers.geography.rates import fetch_rates, normalize_currency_code

rates, source = fetch_rates()
# rates = {"USD": Decimal("1.0"), "EUR": Decimal("0.85"), ...}
# source = "live" or "fallback"

code = normalize_currency_code("usd")  # Returns "USD"
```

---

## Provider: `image` — Image Processing

**External services**: rembg (background removal), pytesseract (OCR), Pillow/PIL, OpenCV, scikit-image

### Exports

| Symbol | Purpose |
|--------|---------|
| `remove_background` | Remove image background (unified API) |
| `remove_background_preset` | Remove bg using named preset |
| `remove_background_model` | Remove bg using specific model |
| `remove_background_strategy` | Remove bg using strategy |
| `magic_erase` | AI-powered magic erase |
| `AVAILABLE_MODELS` | List of available bg removal models |
| `VALID_STRATEGIES` | List of valid removal strategies |
| `CleanEdgeRefiner` | Edge refinement class |
| `EdgeRefiner` | Advanced edge refinement |
| `SceneAnalyzer` | Scene analysis for bg removal |
| `HandRemover` | Hand detection and removal |
| `HoleFiller` | Fill holes in masks |
| `ThinPartHandler` | Handle thin product parts |
| `HumanPreserver` | Preserve human subjects |
| `EdgeShaver` | Shave rough edges |
| `GlobalBackgroundBleeder` | Remove global background color |
| `ArtifactIsolator` | Isolate image artifacts |
| `FloatingArtifactRemover` | Remove floating artifacts |
| `BottomTextEraser` | Erase bottom text from images |
| `WoodBackgroundRemover` | Remove wood backgrounds |
| `image_remove_background` | Alternative bg removal API |
| `generate_angles` | Generate product angle views |
| `process_image_search` | Process image for visual search |
| `parse_bill_text` | OCR text from bill/receipt image |
| `parse_statement_csv` | Parse CSV from bank statement |
| `verify_parcel_photo` | Multi-engine parcel verification |
| `verify_parcel_fast` | Fast parcel verification |
| `Image`, `ImageOps`, `ImageFilter`, `ImageEnhance` | Re-exported Pillow classes |

### Usage Examples

```python
# Background removal
from providers.image.bg_remover import remove_background, remove_background_preset

result_bytes = remove_background(image_bytes, model="isnet-general-use")
result_bytes = remove_background_preset(image_bytes, preset="marketing")

# OCR
from providers.image.ocr import parse_bill_text, parse_statement_csv

text = parse_bill_text(receipt_image_bytes)
csv_data = parse_statement_csv(statement_image_bytes)

# Parcel verification
from providers.image.parcel_verification import verify_parcel_photo, verify_parcel_fast

report = verify_parcel_photo(
    image_bytes=parcel_photo,
    item_descriptions=["iPhone 15", "AirPods Pro"],
    reference_image_bytes=catalog_photo,
    run_ssim=True,
    run_feature_match=True,
    run_homography=True,
    run_vision_ai=True,
)
# Returns: {"combined_score": 0.85, "engines": {...}, "recommendation": "pass"}

fast_report = verify_parcel_fast(
    image_bytes=parcel_photo,
    item_descriptions=["iPhone 15"],
)

# Pillow (use via provider, not direct import)
from providers.image import Image, ImageFilter

img = Image.open("product.jpg")
img = img.resize((800, 800))
img = img.filter(ImageFilter.SHARPEN)
```

---

## Provider: `media` — Media Storage & Processing

**External services**: OpenCV (cv2), S3-compatible object storage

### Exports

| Symbol | Purpose |
|--------|---------|
| `cv2` | Re-exported OpenCV module (None if unavailable) |
| `ximgproc` | OpenCV extended image processing |
| `HAS_CV2` | Whether OpenCV is available |
| `HAS_GUIDED_FILTER` | Whether guided filter is available |
| `StorageBackend` | Abstract storage interface |
| `MediaStorageService` | Media storage with 3-tier path structure |
| `MediaAssetResponse` | Pydantic schema for media asset |
| `MediaUploadRequest` | Pydantic schema for upload request |
| `AIUploadJobResponse` | Pydantic schema for AI upload job |
| `MediaUsageSummary` | Aggregated media usage projection |
| `AIUploadJobSummary` | AI upload job status projection |
| `verify_parcel_photo` | Service-layer wrapper for parcel verification |
| `verify_parcel_fast` | Service-layer wrapper for fast verification |

### Usage Examples

```python
# OpenCV (via provider only)
from providers.media import cv2, HAS_CV2

if HAS_CV2:
    img = cv2.imread("product.jpg")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Storage backend
from providers.media.storage.storage import StorageBackend

# Use via dependency injection — backend selected by STORAGE_BACKEND env var
# "local" -> LocalStorage, "s3" -> S3Storage

# Media storage service
from providers.media.storage.media_storage import MediaStorageService

service = MediaStorageService(db=db_session)
path = service._generate_storage_path(
    country_code="US",
    supplier_id=42,
    product_id=101,
    variant="original",
    filename="photo.jpg",
)
```

---

## Provider: `news` — News Aggregation

**External services**: feedparser (RSS/Atom), httpx (HTTP fetch)

### Exports

| Symbol | Purpose |
|--------|---------|
| `fetch_rss_entries` | Fetch and parse RSS/Atom feed |
| `fetch_api_payload` | Fetch JSON news API payload |

### Usage Example

```python
from providers.news.rss_provider import fetch_rss_entries, fetch_api_payload

# RSS feed
entries = await fetch_rss_entries("https://news.ycombinator.com/rss")
for entry in entries:
    print(entry.title, entry.link)

# JSON API
data = await fetch_api_payload(
    "https://newsapi.org/v2/top-headlines?country=us",
    headers={"Authorization": "Bearer ..."},
)
```

---

## Provider: `payments` — Payment Gateways

**External services**: Stripe, Tap, PayTabs, PayPal, Thawani

### Exports

| Symbol | Purpose |
|--------|---------|
| `stripe` | Re-exported Stripe SDK (None if unavailable) |
| `HAS_STRIPE` | Whether Stripe SDK is available |
| `BasePaymentGateway` | Abstract base for gateway adapters |
| `GatewaySettings` | Runtime config for a gateway |
| `GatewayDefinition` | Registration record for adapter |
| `PaymentGatewayRegistry` | Registry mapping provider_code -> adapter |
| `ConnectionTestResult` | Gateway connectivity test result |
| `PaymentResult` | Payment operation result |
| `RefundResult` | Refund operation result |
| `WebhookEventType` | Enum: payment/refund/chargeback/unknown |
| `WebhookStatus` | Enum: succeeded/failed/pending/disputed |
| `ZoziPaymentEvent` | Normalized payment webhook event |
| `ZoziRefundEvent` | Normalized refund webhook event |
| `ZoziChargebackEvent` | Normalized chargeback webhook event |
| `configure_stripe_connect` | Set Stripe API key/version |
| `create_connect_account` | Create Stripe Connect account |
| `modify_connect_account` | Modify Stripe Connect account |
| `create_connect_transfer` | Create Stripe Connect transfer |
| `resolve_stripe_secret_key` | Get Stripe secret key from env |
| `resolve_tap_secret_key` | Get Tap secret key from env |
| `resolve_paytabs_server_key` | Get PayTabs server key from env |
| `resolve_thawani_secret_key` | Get Thawani secret key from env |
| `resolve_paypal_credentials` | Get PayPal credentials from env |
| `parse_generic_payload` | Parse generic webhook payload |
| `fill_gateway_template` | Fill template string with context |
| `normalize_generic_status` | Normalize payment status string |

### Usage Examples

```python
# Stripe SDK (via provider only)
from providers.payments.stripe_sdk import stripe, HAS_STRIPE

if HAS_STRIPE:
    stripe.api_key = "sk_..."
    charge = stripe.Charge.create(amount=2000, currency="usd", source="tok_...")

# Stripe Connect
from providers.payments.connect import create_connect_account, create_connect_transfer

account = create_connect_account(type="express", country="US")
transfer = create_connect_transfer(amount=1000, currency="usd", destination="acct_...")

# Gateway registry
from providers.payments.registry import PaymentGatewayRegistry
from providers.payments.base import BasePaymentGateway

@PaymentGatewayRegistry.register_adapter("stripe")
class StripeAdapter(BasePaymentGateway):
    def process_payment(self, amount, currency, **kwargs):
        ...

# Resolve gateway
adapter_cls = PaymentGatewayRegistry.get("stripe")
adapter = adapter_cls(settings=GatewaySettings(provider_code="stripe", ...))

# Config resolution
from providers.payments.config import resolve_stripe_secret_key, is_stripe_configured

if is_stripe_configured():
    key = resolve_stripe_secret_key()

# Webhook verification
from providers.payments.webhooks import _verify_tap_signature, _verify_paytabs_signature

is_valid = _verify_tap_signature(raw_body, sig_header, webhook_secret)
is_valid = _verify_paytabs_signature(payload_bytes, signature, webhook_secret)
```

---

## Provider: `security` — Security Vendors

**External services**: cryptography (Fernet/KDF), Tor Project (exit nodes), Watchlist/sanctions API

### Exports

| Symbol | Purpose |
|--------|---------|
| `Fernet` | Symmetric encryption (from cryptography) |
| `hashes` | Hash functions (from cryptography) |
| `PBKDF2HMAC` | Key derivation (from cryptography) |
| `fetch_tor_exit_list` | Fetch Tor exit-node IP list |
| `WatchlistProviderError` | Watchlist API error |
| `screen_watchlist` | Query sanctions/watchlist screening API |

### Usage Examples

```python
# Encryption
from providers.security.encryption import Fernet

fernet = Fernet(key)
encrypted = fernet.encrypt(b"sensitive data")
decrypted = fernet.decrypt(encrypted)

# Tor exit nodes
from providers.security.threat_intel import fetch_tor_exit_list

exit_nodes = fetch_tor_exit_list()
if client_ip in exit_nodes:
    # Flag as potential anonymizer
    ...

# Watchlist screening
from providers.security.watchlist import screen_watchlist, WatchlistProviderError

try:
    result = screen_watchlist(
        employee_code="EMP001",
        full_name="John Doe",
        country_code="US",
    )
    # Returns: {"status": "clear", "score": 0.1, "flagged_categories": []}
except WatchlistProviderError as exc:
    logger.error("Watchlist check failed: %s", exc)
```

---

## Provider: `voice` — Voice Processing

**External services**: Ollama (Whisper model for transcription)

### Exports

| Symbol | Purpose |
|--------|---------|
| `transcribe_audio` | Transcribe audio bytes to text |
| `process_product_voice_command` | Parse voice command for product operations |
| `process_finance_voice_command` | Parse voice command for finance operations |

### Usage Examples

```python
from providers.voice.voice_to_text import transcribe_audio, process_product_voice_command

# Transcription
text = transcribe_audio(audio_bytes, model="whisper:small")

# Voice commands
result = process_product_voice_command("add blue shirt to inventory")
# Returns: {"action": "add", "product": "blue shirt", "confidence": 0.85}

result = process_finance_voice_command("record expense for office supplies")
# Returns: {"action": "expense", "category": "office supplies", ...}
```

---

## Provider: Top-Level Modules

### `providers/storage.py` — Cloud Storage

| Symbol | Purpose |
|--------|---------|
| `create_s3_client` | Create boto3 S3 client |
| `create_ssm_client` | Create boto3 SSM client for secrets |

```python
from providers.storage import create_s3_client

s3 = create_s3_client(
    bucket="zozi-media",
    region="us-east-1",
    endpoint_url="https://s3.amazonaws.com",
    access_key="...",
    secret_key="...",
)
s3.put_object(Bucket="zozi-media", Key="photo.jpg", Body=image_bytes)
```

### `providers/observability.py` — Error Tracking

| Symbol | Purpose |
|--------|---------|
| `capture_exception` | Capture exception to Sentry (no-op if unavailable) |
| `capture_message` | Capture message to Sentry (no-op if unavailable) |

```python
from providers.observability import capture_exception, capture_message

try:
    ...
except Exception as exc:
    capture_exception(exc)

capture_message("Deployment completed", level="info")
```

### `providers/async_workers.py` — Async/Parallel Processing

| Symbol | Purpose |
|--------|---------|
| `remove_background_async` | Async background removal |
| `analyze_product_image_async` | Async vision analysis |
| `embed_text_async` | Async text embedding |
| `parse_bill_async` | Async bill OCR |
| `search_products_async` | Async product search |
| `batch_analyze_images_async` | Batch async image analysis |
| `parallel_process_product_async` | Parallel bg+vision processing |

```python
from providers.async_workers import parallel_process_product_async

result = await parallel_process_product_async(image_bytes)
# Returns {"bg_result": ..., "ai_result": ...} processed in parallel
```

### `providers/config.py` — Provider Configuration

```python
from providers.config import ProviderConfig

config = ProviderConfig()
print(config.ollama_base_url)  # From OLLAMA_BASE_URL env var
print(config.ollama_model)     # From OLLAMA_MODEL env var
```

---

## Anti-Patterns to Avoid

### DO NOT import providers from modules/routers

```python
# WRONG — router importing provider directly
# modules/orders/router.py
from providers.payments.stripe_sdk import stripe  # NEVER

# CORRECT — router calls service, service calls provider
# modules/orders/router.py
from domains.orders.services.payment_service import process_payment

# domains/orders/services/payment_service.py
from providers.payments.connect import create_connect_transfer
```

### DO NOT import from domains/ inside providers

```python
# WRONG — provider importing domain model
# providers/payments/stripe.py
from domains.orders.models import Order  # NEVER

# CORRECT — provider takes primitive inputs
def create_charge(amount: int, currency: str, customer_id: str) -> dict:
    ...
```

### DO NOT let SDK import errors crash the app

```python
# WRONG — hard dependency on optional SDK
import stripe  # Crashes if not installed

# CORRECT — graceful degradation
try:
    import stripe as _stripe
    HAS_STRIPE = True
except ImportError:
    _stripe = None
    HAS_STRIPE = False
```

### DO NOT put business logic in providers

```python
# WRONG — provider deciding business rules
def process_payment(amount, currency):
    if amount > 1000:  # Business rule!
        require_approval()
    ...

# CORRECT — provider only wraps SDK call
def create_charge(amount: int, currency: str) -> dict:
    return stripe.Charge.create(amount=amount, currency=currency)

# Business rule lives in service:
def process_payment(amount, currency):
    if amount > 1000:
        require_approval()
    provider.create_charge(amount, currency)
```

### DO NOT return ORM models from providers

```python
# WRONG — provider returns ORM model
def get_payment(payment_id: int) -> Payment:
    return db.query(Payment).get(payment_id)

# CORRECT — provider returns primitive dict
def fetch_charge(charge_id: str) -> dict:
    return stripe.Charge.retrieve(charge_id)
```

---

## Quick Reference Table

| Provider | External Services | Primary Exports |
|----------|-------------------|-----------------|
| `ai` | Ollama, OpenAI, HuggingFace, DuckDuckGo | `analyze_product_image`, `_ollama_chat`, `ChatbotProvider`, `AdvancedSearchEngine`, `FinanceAIResult` |
| `analytics` | Analytics API | `AnalyticsProvider` |
| `auth` | Google, Apple, Facebook, pyotp, python-jose | `exchange_google_code`, `verify_totp`, `decode_token`, `build_apple_auth_url` |
| `automation` | APScheduler | `create_scheduler`, `add_interval_job` |
| `comms` | Twilio, Resend, SMTP | `create_twilio_client`, `send_whatsapp_message`, `deliver_email` |
| `finance` | Bank/treasury API | `test_connection`, `dispatch_batch` |
| `geography` | IP APIs, open.er-api.com, Wikidata | `CountryDetectionProvider`, `fetch_rates`, `LocationProvider` |
| `image` | rembg, pytesseract, Pillow, OpenCV | `remove_background`, `parse_bill_text`, `verify_parcel_photo` |
| `media` | OpenCV, S3 | `cv2`, `StorageBackend`, `MediaStorageService` |
| `news` | feedparser, httpx | `fetch_rss_entries`, `fetch_api_payload` |
| `payments` | Stripe, Tap, PayTabs, PayPal, Thawani | `BasePaymentGateway`, `PaymentGatewayRegistry`, `stripe`, `connect` |
| `security` | cryptography, Tor Project, Watchlist API | `Fernet`, `fetch_tor_exit_list`, `screen_watchlist` |
| `voice` | Ollama (Whisper) | `transcribe_audio`, `process_product_voice_command` |
| `storage.py` | boto3 (S3/SSM) | `create_s3_client`, `create_ssm_client` |
| `observability.py` | Sentry | `capture_exception`, `capture_message` |
| `async_workers.py` | asyncio, ThreadPoolExecutor | `parallel_process_product_async`, `remove_background_async` |
| `config.py` | Environment variables | `ProviderConfig` |

---

## File Structure

```
providers/
├── __init__.py              # Re-exports all public symbols
├── _base.py                 # BaseProvider, BaseAIProvider ABCs
├── config.py                # ProviderConfig dataclass
├── storage.py               # S3/SSM client factories
├── observability.py         # Sentry capture helpers
├── async_workers.py         # Async/parallel provider wrappers
├── parcel_verification.py   # Top-level parcel verification
├── ai/
│   ├── vision.py            # Product image analysis, price suggestion
│   ├── text.py              # Ollama chat, embeddings, transcription
│   ├── chatbot.py           # ChatbotProvider with session history
│   ├── search.py            # AdvancedSearchEngine with vectorization
│   ├── finance_ai.py        # Email parsing, bill extraction
│   ├── openai_client.py     # OpenAI Whisper/translation
│   ├── huggingface.py       # BLIP captioning, BART classification
│   ├── web_search.py        # DuckDuckGo search
│   └── zozi_mcp.py          # MCP server for ZOZI API
├── analytics/
│   └── analytics.py         # Admin analytics provider
├── auth/
│   ├── oauth.py             # Google + Facebook OAuth
│   ├── apple.py             # Apple Sign-In
│   ├── totp.py              # TOTP/2FA (pyotp wrapper)
│   └── jwt.py               # JWT handling (python-jose wrapper)
├── automation/
│   └── scheduler.py         # APScheduler wrapper
├── comms/
│   ├── twilio.py            # Twilio SDK wrapper
│   ├── whatsapp.py          # WhatsApp via Twilio
│   └── email.py             # Resend/SMTP email delivery
├── finance/
│   └── bank_api.py          # Bank/treasury API
├── geography/
│   ├── geo.py               # Country detection from IP
│   ├── map.py               # IP geolocation
│   ├── country.py           # Country search/details
│   └── rates.py             # FX rates + currency lookup
├── image/
│   ├── bg_remover.py        # Background removal (6 models)
│   ├── image.py             # Image processing utilities
│   ├── ocr.py               # OCR (pytesseract wrapper)
│   └── parcel_verification.py  # Multi-engine parcel verification
├── media/
│   ├── __init__.py          # cv2 re-export
│   ├── subscribers.py       # (empty)
│   ├── upload/
│   │   ├── ai_upload_service.py      # AI upload business logic
│   │   └── ai_upload_write_service.py # AI upload DB mutations
│   ├── storage/
│   │   ├── storage.py       # StorageBackend ABC + Local/S3
│   │   └── media_storage.py # MediaStorageService
│   ├── schemas/
│   │   └── media_schemas.py # Pydantic response schemas
│   ├── read_models/
│   │   └── media_read_models.py  # CQRS read projections
│   └── qr/
│       └── parcel_verification_service.py  # Service-layer wrapper
├── news/
│   └── rss_provider.py      # RSS/Atom + JSON news fetch
├── payments/
│   ├── stripe_sdk.py        # Stripe SDK re-export
│   ├── base.py              # BasePaymentGateway ABC
│   ├── base_models.py       # PaymentResult, RefundResult, etc.
│   ├── webhook_models.py    # Normalized webhook events
│   ├── webhooks.py          # Signature verification
│   ├── config.py            # Gateway config resolution
│   ├── registry.py          # PaymentGatewayRegistry
│   ├── generic.py           # Generic payload parsing
│   ├── connect.py           # Stripe Connect operations
│   ├── stripe.py            # Stripe adapter
│   ├── tap.py               # Tap adapter
│   ├── paytabs.py           # PayTabs adapter
│   ├── thawani.py           # Thawani adapter
│   ├── paypal.py            # PayPal adapter
│   └── payment_persistence.py  # Payment record persistence
├── security/
│   ├── encryption.py        # cryptography SDK re-export
│   ├── threat_intel.py      # Tor exit-node list
│   └── watchlist.py         # Sanctions screening
└── voice/
    └── voice_to_text.py     # Audio transcription + voice commands
```
