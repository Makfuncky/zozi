# ZOZI Provider Tools — Complete Reference Guide

> **Version:** 2.0
> **Last Updated:** 2026-08-26
> **Scope:** All 30+ external provider tools, their APIs, domain connections, wiring patterns, and best practices.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Provider Categories](#2-provider-categories)
3. [Complete Provider Reference](#3-complete-provider-reference)
4. [Provider-to-Domain Mapping](#4-provider-to-domain-mapping)
5. [Wiring Guide](#5-wiring-guide)
6. [Error Handling Patterns](#6-error-handling-patterns)
7. [Testing Providers](#7-testing-providers)
8. [Best Practices](#8-best-practices)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Architecture Overview

### What Are Providers?

Providers are **pure external SDK wrappers**. They encapsulate third-party APIs (Stripe, Twilio, OpenAI, Ollama, etc.) so that domain services never import external libraries directly.

```
Domain Service → Provider → External SDK → External API
```

### Core Rules

| Rule | Description |
|------|-------------|
| **No domain imports** | Providers must NEVER import from `domains/`, `modules/`, `infrastructure/` |
| **Primitive I/O** | Accept primitives (str, bytes, dict, int) → return primitives (dict, list, bytes) |
| **Graceful degradation** | Use `HAS_<SDK>` flags to detect missing SDKs and fall back |
| **No business logic** | Providers wrap SDKs only — decisions belong in domain services |
| **No DB access** | Providers never touch the database |

### Provider Availability Flags

Every provider exposes a boolean flag indicating whether its SDK is installed:

```python
# Check before using
from providers.image.free_image_tools import HAS_CV2, HAS_REMBG

if HAS_CV2:
    result = cv2_something()
else:
    result = fallback()  # graceful degradation
```

### Folder Structure

```
providers/
├── ai/                      # AI/ML: chatbot, search, vision, text, sentiment, recommendation
├── analytics/               # Admin analytics dashboards
├── auth/                    # JWT, OAuth, TOTP, Apple Auth
├── automation/              # Job scheduler (APScheduler)
├── barcode/                 # EAN/UPC/Code128 generation
├── bg_removal/              # AI background removal (rembg + OpenCV)
├── comms/                   # Email, Twilio, WhatsApp
├── finance/                 # Bank API integration
├── geo/                     # Geo utilities
├── geography/               # IP geolocation, country, maps, currency rates
├── image/                   # Pillow processing, OCR, bg_remover, parcel verification
├── media/                   # Media AI services
├── news/                    # RSS feed parsing
├── ocr/                     # Document OCR parsing
├── payments/                # Stripe, PayPal, Tap, PayTabs, Thawani, webhooks, registry
├── qr/                      # QR generation, parcel verification
├── scanner/                 # QR/barcode scanning from images
├── security/                # Encryption, threat intel, watchlist
├── shipping/                # Rate calculator, carrier comparison
├── storage/                 # S3/local storage backends
├── voice/                   # Speech-to-text, voice commands
├── async_workers/           # Thread/process pool executors
├── observability/           # Provider health monitoring
└── _base.py                 # BaseProvider / BaseAIProvider
```

---

## 2. Provider Categories

### Category 1: AI / ML Providers

| Provider | Module | SDK | Purpose |
|----------|--------|-----|---------|
| Chatbot | `ai/chatbot.py` | — | Intent classification, session management |
| Search | `ai/search.py` | — | Semantic product search, autocomplete |
| Vision | `ai/vision.py` | Ollama | Image classification, object detection |
| Text | `ai/text.py` | Ollama | Embeddings, translation, JSON extraction |
| Sentiment | `ai/sentiment.py` | VADER (optional) | Review/message sentiment analysis |
| Recommendation | `ai/recommendation.py` | — | Collaborative filtering, "bought together" |
| Price Intelligence | `ai/price_intelligence.py` | — | Competitor tracking, dynamic pricing |
| Image Similarity | `ai/image_similarity.py` | PIL+numpy | Visual similarity for duplicate detection |
| Finance AI | `ai/finance_ai.py` | — | Bank transaction categorization |
| HuggingFace | `ai/huggingface.py` | HF Inference API | BLIP captions, BART zero-shot classification |
| AI Variant Config | `ai/ai_variant_config.py` | Ollama | Product variant analysis |
| AI Research Jobs | `ai/ai_research_jobs.py` | — | In-memory job tracking |
| Visual Voice Search | `ai/visual_voice_search.py` | — | Voice-activated visual search |

### Category 2: Communication Providers

| Provider | Module | SDK | Purpose |
|----------|--------|-----|---------|
| Email | `comms/email.py` | SMTP | Transactional email delivery |
| Twilio | `comms/twilio.py` | Twilio | SMS, voice calls, proxy numbers |
| WhatsApp | `comms/whatsapp.py` | WhatsApp Business API | WhatsApp messaging |

### Category 3: Payment Providers

| Provider | Module | SDK | Purpose |
|----------|--------|-----|---------|
| Stripe | `payments/stripe_sdk.py` | Stripe | Card payments, refunds, PaymentIntents |
| PayPal | `payments/paypal.py` | PayPal | PayPal checkout |
| Tap | `payments/tap.py` | Tap Payments | MENA region payments |
| PayTabs | `payments/paytabs.py` | PayTabs | MENA region payments |
| Thawani | `payments/thawani.py` | Thawani | Saudi/Qatar payments |
| Registry | `payments/registry.py` | — | Runtime provider resolution |
| Webhooks | `payments/webhooks.py` | — | PSP webhook verification |
| Connect | `payments/connect.py` | Stripe Connect | Marketplace split payments |

### Category 4: Geography Providers

| Provider | Module | SDK | Purpose |
|----------|--------|-----|---------|
| Country | `geography/country.py` | — | Country search, currency mapping |
| IP Geolocation | `geography/ip.py` | — | IP-based location detection |
| GeoIP | `geography/geoip.py` | MaxMind | Database lookups |
| Geo | `geography/geo.py` | — | Geocoding, reverse geocoding |
| Rates | `geography/rates.py` | — | Currency exchange rates |
| Map | `geography/map.py` | — | Map rendering, routes |
| Country HTTP | `geography/country_http.py` | — | External country data APIs |
| External Data | `geography/external_data.py` | — | Supplementary geo metadata |

### Category 5: Image Processing Providers

| Provider | Module | SDK | Purpose |
|----------|--------|-----|---------|
| Free Image Tools | `image/free_image_tools.py` | PIL, rembg, OpenCV | 12 image tools (crop, sharpen, upscale, etc.) |
| BG Remover | `image/bg_remover.py` | rembg, OpenCV | AI background removal |
| OCR | `image/ocr.py` | Tesseract | Optical character recognition |
| Parcel Verification | `image/parcel_verification.py` | scikit-image, OpenCV | Multi-engine parcel photo comparison |
| Core Image | `image/image.py` | PIL | Basic image operations |

### Category 6: Security Providers

| Provider | Module | SDK | Purpose |
|----------|--------|-----|---------|
| JWT | `auth/jwt.py` | python-jose | Token issue/validation |
| OAuth | `auth/oauth.py` | — | Social login, OAuth2 flow |
| TOTP | `auth/totp.py` | pyotp | Time-based 2FA |
| Apple Auth | `auth/apple.py` | — | Sign in with Apple |
| Encryption | `security/encryption.py` | cryptography | AES/bcrypt, key management |
| Threat Intel | `security/threat_intel.py` | — | Tor exit list, threat feeds |
| Watchlist | `security/watchlist.py` | — | Sanctions/PEP/AML screening |

### Category 7: Shipping & Logistics Providers

| Provider | Module | SDK | Purpose |
|----------|--------|-----|---------|
| Shipping Calculator | `shipping/shipping_calculator.py` | — | Rate calculation, carrier comparison |
| QR Generator | `qr/qr_generator.py` | qrcode | QR code generation |
| Barcode Generator | `barcode/barcode_generator.py` | python-barcode | EAN/UPC/Code128 generation |
| Scanner | `scanner/scanner.py` | pyzbar | QR/barcode decoding from images |
| Parcel Verification | `qr/parcel_verification_service.py` | — | QR-based parcel verification |

### Category 8: Utility Providers

| Provider | Module | SDK | Purpose |
|----------|--------|-----|---------|
| Storage | `storage/storage_backend.py` | boto3 | S3/local storage abstraction |
| S3 Client | `storage/s3_client.py` | boto3 | Direct S3 operations |
| Voice-to-Text | `voice/voice_to_text.py` | Ollama/SpeechRecognition | Transcription, voice commands |
| Analytics | `analytics/analytics.py` | — | Dashboard metrics |
| News | `news/rss_provider.py` | feedparser | RSS feed parsing |
| OCR Parser | `ocr/ocr_parser.py` | — | Regex-based bill/statement parsing |
| AI Media | `media/services/ai.py` | Ollama | Product name/category inference |
| BG Removal | `bg_removal/bg_removal_service.py` | rembg | AI background removal |
| Automation | `automation/scheduler.py` | APScheduler | Cron job scheduling |
| Async Workers | `async_workers.py` | — | Thread/process pool executors |

---

## 3. Complete Provider Reference

### 3.1 AI Search (`providers/ai/search.py`)

```python
from providers.ai.search import AdvancedSearchEngine

engine = AdvancedSearchEngine()

# Load products once
engine.load_product_catalog([
    {"id": 1, "name": "Cotton Shirt", "description": "...", "tags": ["cotton"]},
])

# Search
result = engine.search(
    query="red shoes under $50",
    filters={"brand": "Nike"},
    limit=20,
    sort_by="relevance",  # or "price_asc", "price_desc", "newest"
)
# Returns: {"products": [...], "total": N, "parsed_query": {...}, "all_filters": {...}}

# Autocomplete
suggestions = engine.get_autocomplete_suggestions("shi", limit=10)
```

### 3.2 Sentiment Analysis (`providers/ai/sentiment.py`)

```python
from providers.ai.sentiment import analyze_sentiment, analyze_review, extract_review_insights

# Single text
result = analyze_sentiment("This product is amazing!")
# Returns: {"score": 0.85, "label": "positive", "confidence": 0.92}

# Review with rating
result = analyze_review("Great quality!", rating=5)
# Returns: {"combined_score": 0.9, "rating_sentiment": "positive", "agreement": True}

# Batch insights
insights = extract_review_insights(["Great!", "Terrible!", "Okay"])
# Returns: {"sentiment_distribution": {"positive": 2, "negative": 1}, "total_reviews": 3}
```

### 3.3 Text Embedding (`providers/ai/text.py`)

```python
from providers.ai.text import embed_text, cosine_similarity, translate_en_to_ar

# Generate embedding
vector = embed_text("cotton shirt")  # Returns: [0.1, 0.2, ...] or [] on failure

# Similarity
sim = cosine_similarity(vec1, vec2)  # Returns: 0.0 to 1.0

# Translation
arabic = await translate_en_to_ar("product sale")  # Returns: "منتج تخفيض"
```

### 3.4 Image Processing (`providers/image/free_image_tools.py`)

```python
from providers.image.free_image_tools import (
    magic_erase, smart_crop, auto_rotate, auto_lighting,
    auto_process_image, HAS_CV2, HAS_REMBG,
)

# Background removal
result_bytes = magic_erase(image_bytes, max_dim=1024)

# Smart crop to product
cropped = smart_crop(image_bytes, target_ratio=1.0)

# Auto-fix orientation from EXIF
rotated = auto_rotate(image_bytes)

# Auto-fix lighting
lit = auto_lighting(image_bytes)

# Full pipeline
processed = auto_process_image(
    image_bytes,
    tools=["auto_rotate", "auto_lighting", "smart_crop", "compress"],
)
```

### 3.5 Shipping Calculator (`providers/shipping/shipping_calculator.py`)

```python
from providers.shipping.shipping_calculator import (
    calculate_shipping_rate, compare_shipping_options,
    estimate_delivery_days, get_available_carriers,
)

# Single rate
rate = calculate_shipping_rate(
    origin={"country": "US", "city": "NYC", "postal": "10001"},
    destination={"country": "AE", "city": "Dubai", "postal": "00000"},
    package={"weight_kg": 1.5, "length_cm": 30, "width_cm": 20, "height_cm": 10},
    carrier="fedex",
)
# Returns: {"total": 25.50, "carrier": "fedex", "currency": "USD"}

# Compare all carriers
options = compare_shipping_options(origin, destination, package)
# Returns: [{"carrier": "fedex", "total": 25.50}, {"carrier": "dhl", "total": 30.00}]

# Delivery estimate
days = estimate_delivery_days(origin, destination, "fedex")
# Returns: {"min_days": 3, "max_days": 7}
```

### 3.6 QR/Barcode (`providers/qr/`, `providers/barcode/`, `providers/scanner/`)

```python
from providers.qr.qr_generator import generate_qr, generate_tracking_qr
from providers.barcode.barcode_generator import generate_ean13, generate_code128, validate_ean13
from providers.scanner.scanner import scan_qr, scan_barcode

# QR generation
qr_png = generate_qr("https://zozi.com/product/123")
tracking_png = generate_tracking_qr("TRACK123456")

# Barcode generation
ean13_png = generate_ean13("1234567890128")
code128_png = generate_code128("ZOZI-PROD-001")

# Validation
is_valid = validate_ean13("1234567890128")  # Returns: True/False

# Scanning
qr_results = scan_qr(image_bytes)  # Returns: ["decoded_text"]
barcode_results = scan_barcode(image_bytes)  # Returns: [{"type": "EAN13", "data": "..."}]
```

### 3.7 Payments (`providers/payments/`)

```python
from providers.payments.stripe_sdk import refund_payment_intent, HAS_STRIPE
from providers.payments.registry import PaymentGatewayRegistry, resolve_gateway
from providers.payments.webhooks import verify_stripe_webhook

# Refund
result = refund_payment_intent(payment_intent_id="pi_123", amount=5000)  # cents

# Gateway resolution
gateway = resolve_gateway("AE")  # Returns: "tap" for GCC
gateway = resolve_gateway("US")  # Returns: "stripe"

# Webhook verification
payload = verify_stripe_webhook(payload_body, signature_header, webhook_secret)
```

### 3.8 Geography (`providers/geography/`)

```python
from providers.geography.country import search_countries, get_currency
from providers.geography.ip import geolocate_ip
from providers.geography.rates import fetch_rates
from providers.geography.map import geocode_address, reverse_geocode

# Country
countries = search_countries("United")  # Returns: [{"name": "United States", "code": "US"}]
currency = get_currency("US")  # Returns: "USD"

# IP
location = geolocate_ip("8.8.8.8")  # Returns: {"country": "US", "city": "Mountain View"}

# Rates
rates = fetch_rates(base="USD")  # Returns: {"EUR": 0.85, "AED": 3.67}

# Maps
coords = geocode_address("1600 Amphitheatre Parkway")  # Returns: {"lat": 37.42, "lng": -122.08}
```

### 3.9 Auth (`providers/auth/`)

```python
from providers.auth.jwt import create_token, decode_token
from providers.auth.oauth import verify_oauth_token
from providers.auth.totp import generate_secret, verify as verify_totp, provisioning_uri
from providers.auth.apple import build_apple_auth_url

# JWT
token = create_token({"user_id": 1}, secret_key="secret")
payload = decode_token(token, secret="secret")

# TOTP
secret = generate_secret()  # Returns: "JBSWY3DPEHPK3PXP"
uri = provisioning_uri(secret, account_name="user@example.com", issuer="ZOZI")
is_valid = verify_totp(secret, "123456")

# Apple
auth_url = build_apple_auth_url(client_id="com.zozi.app", redirect_uri="https://zozi.com/callback")
```

### 3.10 Communication (`providers/comms/`)

```python
from providers.comms.email import deliver_email
from providers.comms.twilio import create_twilio_client, send_sms
from providers.comms.whatsapp import send_whatsapp_message

# Email
result = deliver_email(
    to_email="user@example.com",
    subject="Order Confirmed",
    body="Your order #123 has been confirmed.",
    html=False,
)

# SMS
client = create_twilio_client(account_sid="ACxxx", auth_token="xxx")
result = send_sms(client, to_number="+1234567890", message="Your code is 1234")

# WhatsApp
result = send_whatsapp_message(to_number="+1234567890", message="Order shipped!")
```

### 3.11 Security (`providers/security/`)

```python
from providers.security.encryption import encrypt_message, decrypt_message, hash_password
from providers.security.threat_intel import is_tor_exit_node
from providers.security.watchlist import screen_watchlist

# Encryption
encrypted = encrypt_message("sensitive data", key="encryption_key")
decrypted = decrypt_message(encrypted, key="encryption_key")

# Threat intel
is_tor = is_tor_exit_node("1.2.3.4")  # Returns: True/False

# Watchlist
result = screen_watchlist(employee_code="EMP001", full_name="John Doe", country_code="US")
# Returns: {"cleared": True, "matches": []}
```

### 3.12 Storage (`providers/storage/`)

```python
from providers.storage.storage_backend import get_storage, LocalStorage, S3Storage

# Get active backend (local or s3 based on STORAGE_BACKEND env)
storage = get_storage()

# Save
url = storage.save("products/123.jpg", image_bytes, content_type="image/jpeg")

# Read
data = storage.read("products/123.jpg")

# Delete
storage.delete("products/123.jpg")

# URL
public_url = storage.url("products/123.jpg")
```

---

## 4. Provider-to-Domain Mapping

### 4.1 Catalog Domain

| Service | Provider | Use Case | Priority |
|---------|----------|----------|----------|
| `ai_upload_service.py` | `media.services.ai` | Infer product names, categories, tags from images | CRITICAL |
| `ai_upload_service.py` | `storage` | Persist uploaded images | CRITICAL |
| `ai_upload_service.py` | `image.free_image_tools` | Preprocess images (rotate, light, crop, BG removal) | HIGH |
| `ai_upload_service.py` | `ai.image_similarity` | Detect duplicate product images | MEDIUM |
| `ai_upload_service.py` | `ai.huggingface` | Fallback ML inference | HIGH |
| `search_service.py` | `ai.search` | Semantic product search | HIGH |
| `search_service.py` | `ai.text` | Query/product embeddings | HIGH |

### 4.2 Customers Domain

| Service | Provider | Use Case | Priority |
|---------|----------|----------|----------|
| `cart_service.py` | `shipping` | Calculate cart shipping rates | HIGH |
| `search_service.py` | `ai.search` | Natural language product search | HIGH |
| `reviews_service.py` | `ai.sentiment` | Review moderation, quality scoring | MEDIUM |
| `reviews_service.py` | `image.free_image_tools` | Compress reviewer photos | LOW |
| `customer_health_engine.py` | `ai.recommendation` | Personalized recommendations | HIGH |

### 4.3 Orders Domain

| Service | Provider | Use Case | Priority |
|---------|----------|----------|----------|
| `orders_service.py` | `payments.stripe_sdk` | Process refunds | CRITICAL |
| `orders_service.py` | `payments.registry` | Resolve payment provider per country | CRITICAL |
| `orders_service.py` | `payments.webhooks` | Handle async payment confirmations | CRITICAL |
| `orders_service.py` | `shipping` | Calculate order shipping | HIGH |
| `orders_service.py` | `comms.email` | Order status emails | HIGH |
| `orders_service.py` | `geography.rates` | Multi-currency checkout | MEDIUM |
| `geography.ip` | `geography.ip` | Detect country for tax/shipping | MEDIUM |

### 4.4 Finance Domain

| Service | Provider | Use Case | Priority |
|---------|----------|----------|----------|
| `finance_service.py` | `finance.bank_api` | Bank connection, transfers | CRITICAL |
| `finance_service.py` | `payments.connect` | Marketplace split payments | CRITICAL |
| `finance_service.py` | `payments.registry` | Payment provider dispatch | HIGH |
| `finance_service.py` | `geography.rates` | Multi-currency reconciliation | HIGH |
| `finance_service.py` | `ai.finance_ai` | Transaction categorization | MEDIUM |
| `finance_service.py` | `image.ocr` | Invoice/receipt OCR | MEDIUM |
| `finance_service.py` | `automation.scheduler` | Scheduled payouts | HIGH |

### 4.5 Communications Domain

| Service | Provider | Use Case | Priority |
|---------|----------|----------|----------|
| `proxy_communication.py` | `comms.twilio` | SMS, voice calls, proxy numbers | CRITICAL |
| `proxy_communication.py` | `comms.whatsapp` | WhatsApp messaging | HIGH |
| `proxy_communication.py` | `comms.email` | Transactional emails | CRITICAL |
| `proxy_communication.py` | `security.encryption` | Encrypt message content | HIGH |

### 4.6 Logistics Domain

| Service | Provider | Use Case | Priority |
|---------|----------|----------|----------|
| `features.py` | `shipping` | Rate calculation, carrier comparison | CRITICAL |
| `features.py` | `qr.qr_generator` | Shipment label QR codes | HIGH |
| `features.py` | `barcode.barcode_generator` | Tracking barcodes | HIGH |
| `features.py` | `qr.parcel_verification` | Parcel checkpoint verification | HIGH |
| `features.py` | `geography.map` | Route visualization | MEDIUM |
| `features.py` | `comms.twilio` | Delivery SMS updates | HIGH |
| `features.py` | `automation.scheduler` | Shipment status sync | MEDIUM |

### 4.7 Country Domain

| Service | Provider | Use Case | Priority |
|---------|----------|----------|----------|
| `events.py` | `geography.country` | Country search, currency mapping | HIGH |
| `events.py` | `geography.ip` | IP-based localization | HIGH |
| `events.py` | `geography.rates` | Exchange rates for pricing | HIGH |
| `events.py` | `geography.country_http` | Live country data | MEDIUM |
| `events.py` | `geography.external_data` | Supplementary geo metadata | MEDIUM |

### 4.8 Promotions Domain

| Service | Provider | Use Case | Priority |
|---------|----------|----------|----------|
| `flash_sale_service.py` | `comms.email` | Campaign blasts | HIGH |
| `flash_sale_service.py` | `comms.whatsapp` | Promotional broadcasts | MEDIUM |
| `promotions_write_service.py` | `automation.scheduler` | Flash sale timing | HIGH |
| `promotions_write_service.py` | `ai.recommendation` | Targeted promotions | MEDIUM |
| `promotions_write_service.py` | `ai.price_intelligence` | Dynamic discount pricing | MEDIUM |
| `promotions_write_service.py` | `image.free_image_tools` | Banner image processing | MEDIUM |

### 4.9 Security Domain

| Service | Provider | Use Case | Priority |
|---------|----------|----------|----------|
| `features.py` | `auth.jwt` | Session token issue/validate | CRITICAL |
| `features.py` | `auth.oauth` | Social login | CRITICAL |
| `features.py` | `auth.totp` | 2FA/MFA | HIGH |
| `features.py` | `auth.apple` | Apple ID sign-in | HIGH |
| `features.py` | `security.encryption` | PII encryption | CRITICAL |
| `features.py` | `security.threat_intel` | Tor/malicious IP blocking | HIGH |
| `features.py` | `security.watchlist` | AML/KYC screening | HIGH |

### 4.10 Accounts Domain

| Service | Provider | Use Case | Priority |
|---------|----------|----------|----------|
| *(auth flows)* | `auth.jwt` | Session management | CRITICAL |
| *(auth flows)* | `auth.oauth` | Social login | HIGH |
| *(auth flows)* | `auth.totp` | Two-factor auth | HIGH |
| *(auth flows)* | `comms.email` | Welcome/verification emails | CRITICAL |
| *(auth flows)* | `comms.twilio` | Phone verification SMS | HIGH |
| *(auth flows)* | `image.free_image_tools` | Profile photo processing | MEDIUM |
| *(auth flows)* | `image.ocr` | ID document OCR | MEDIUM |

### 4.11 HR Domain

| Service | Provider | Use Case | Priority |
|---------|----------|----------|----------|
| *(employee mgmt)* | `security.watchlist` | Employee screening | HIGH |
| *(employee mgmt)* | `comms.email` | Onboarding emails | HIGH |
| *(employee mgmt)* | `security.encryption` | Employee PII protection | CRITICAL |

### 4.12 Governance Domain

| Service | Provider | Use Case | Priority |
|---------|----------|----------|----------|
| *(compliance)* | `security.threat_intel` | Fraud detection feeds | HIGH |
| *(compliance)* | `security.watchlist` | AML/KYC compliance | CRITICAL |
| *(compliance)* | `security.encryption` | Data residency compliance | CRITICAL |
| *(compliance)* | `automation.scheduler` | Audit scheduling | HIGH |
| *(compliance)* | `news.rss_provider` | Regulatory news monitoring | LOW |

### 4.13 Audit Domain

| Service | Provider | Use Case | Priority |
|---------|----------|----------|----------|
| `audit_service.py` | `security.encryption` | Encrypt audit logs | CRITICAL |
| `audit_service.py` | `storage` | Archive logs to S3 | HIGH |
| `audit_service.py` | `geography.country` | Data residency enforcement | CRITICAL |
| `audit_service.py` | `automation.scheduler` | Log rotation/archival | HIGH |

### 4.14 Analytics Domain

| Service | Provider | Use Case | Priority |
|---------|----------|----------|----------|
| `flat_analytics_service.py` | `analytics.analytics` | Dashboard metrics | HIGH |
| `flat_analytics_service.py` | `ai.chatbot` | Chatbot query tracking | HIGH |
| `flat_analytics_service.py` | `ai.recommendation` | Personalized feeds | HIGH |
| `flat_analytics_service.py` | `geography.rates` | Multi-currency normalization | MEDIUM |
| `flat_analytics_service.py` | `automation.scheduler` | Snapshot refresh | HIGH |

### 4.15 Suppliers Domain

| Service | Provider | Use Case | Priority |
|---------|----------|----------|----------|
| `supplier_service.py` | `comms.email` | Onboarding emails | HIGH |
| `supplier_service.py` | `comms.twilio` | Order alerts | HIGH |
| `supplier_service.py` | `image.free_image_tools` | Product image enhancement | HIGH |
| `supplier_service.py` | `security.watchlist` | Sanctions screening | CRITICAL |
| `supplier_service.py` | `finance.bank_api` | Bank account verification | HIGH |
| `supplier_service.py` | `storage` | Document storage | HIGH |

---

## 5. Wiring Guide

### 5.1 Basic Wiring Pattern

```python
# ── Step 1: Import at top of domain service file ────────────────────────
from providers.<category>.<module> import <function_or_class>

# ── Step 2: Call provider with primitive parameters ─────────────────────
def my_service_function(param1: str, param2: bytes):
    result = provider_function(param1, param2)

    # ── Step 3: Handle result ─────────────────────────────────────────
    if isinstance(result, dict) and result.get("error"):
        # Fallback logic
        return default_value
    return result

# ── Step 4: Handle exceptions ───────────────────────────────────────────
    try:
        result = provider_function(param1)
    except NotImplementedError:
        # SDK not installed — use fallback
        return fallback_value
    except (ConnectionError, TimeoutError):
        # Network failure — retry or degrade
        return {"queued": True}
```

### 5.2 Image Processing Wiring

```python
from providers.image.free_image_tools import (
    auto_rotate, auto_lighting, smart_crop, magic_erase,
    HAS_CV2, HAS_REMBG,
)

def preprocess_supplier_image(img_bytes: bytes) -> bytes:
    """Preprocess supplier-uploaded product image before AI inference."""
    if not HAS_CV2:
        return img_bytes  # graceful degradation

    # Chain: rotate → light → crop → BG removal
    img_bytes = auto_rotate(img_bytes)
    img_bytes = auto_lighting(img_bytes)
    img_bytes = smart_crop(img_bytes, target_ratio=1.0)

    if HAS_REMBG:
        img_bytes = magic_erase(img_bytes, max_dim=1024)

    return img_bytes
```

### 5.3 AI Provider Wiring

```python
from providers.ai.sentiment import analyze_review
from providers.ai.recommendation import get_product_recommendations

def moderate_review(review_text: str, rating: int = 0):
    """Moderate a product review using sentiment analysis."""
    try:
        result = analyze_review(review_text, rating=rating)
        return {
            "is_positive": result["combined_score"] > 0,
            "needs_review": result["combined_score"] < -0.3,
            "label": result["combined_label"],
        }
    except NotImplementedError:
        # Sentiment SDK not installed
        return {"is_positive": True, "needs_review": False, "label": "neutral"}
    except (ConnectionError, TimeoutError):
        # Ollama unavailable
        return {"is_positive": rating >= 3, "needs_review": rating < 3, "label": "neutral"}
```

### 5.4 Payment Provider Wiring

```python
from providers.payments.stripe_sdk import refund_payment_intent, HAS_STRIPE
from providers.payments.registry import resolve_gateway

def refund_order(order, amount: float, currency: str = "usd"):
    """Refund an order through the appropriate payment gateway."""
    gateway = resolve_gateway(order.country_code)

    if gateway == "stripe" and HAS_STRIPE:
        return refund_payment_intent(
            payment_intent_id=order.payment_intent_id,
            amount=int(amount * 100),  # cents
        )
    elif gateway == "tap":
        provider = PaymentGatewayRegistry.get("tap")
        return provider.refund(order.payment_intent_id, amount, currency)
    else:
        raise NotImplementedError(f"Refund not supported for gateway: {gateway}")
```

### 5.5 Shipping Provider Wiring

```python
from providers.shipping.shipping_calculator import (
    calculate_shipping_rate, compare_shipping_options,
)

def get_order_shipping_options(order, destination: dict):
    """Get shipping options for an order."""
    origin = {
        "country": order.warehouse_country,
        "city": order.warehouse_city,
    }
    package = {
        "weight_kg": float(order.total_weight_kg or 0),
        "length_cm": 30, "width_cm": 20, "height_cm": 10,
    }

    try:
        return compare_shipping_options(origin, destination, package)
    except (ConnectionError, TimeoutError):
        # Return flat rate fallback
        return [{"carrier": "flat_rate", "total": 10.0, "currency": "USD"}]
```

### 5.6 Async Provider Wiring

```python
from providers.async_workers import remove_background_async, embed_text_async

async def process_image_pipeline(img_bytes: bytes) -> bytes:
    """Process image using async workers (CPU-bound)."""
    img_bytes = await remove_background_async(img_bytes, strategy="auto")
    return img_bytes

async def generate_catalog_embeddings(products: list[dict]):
    """Generate embeddings for all products asynchronously."""
    texts = [f"{p['name']} {p['description']}" for p in products]
    embeddings = await embed_text_async(texts)
    return embeddings
```

---

## 6. Error Handling Patterns

### Pattern 1: SDK Not Installed

```python
from providers.image.free_image_tools import HAS_REMBG, magic_erase

def remove_bg(img_bytes: bytes) -> bytes:
    if not HAS_REMBG:
        logger.warning("rembg not installed, skipping BG removal")
        return img_bytes  # graceful degradation
    return magic_erase(img_bytes)
```

### Pattern 2: Network Failure

```python
from providers.comms.email import deliver_email
from requests.exceptions import ConnectionError, Timeout

def send_notification_email(to: str, subject: str, body: str):
    try:
        return deliver_email(to, subject, body)
    except (ConnectionError, Timeout):
        logger.error("Email delivery failed, queuing for retry")
        queue_for_retry(to, subject, body)
        return {"queued": True}
```

### Pattern 3: Provider Not Configured

```python
from providers.analytics.analytics import AnalyticsProvider, HAS_ANALYTICS

def get_analytics():
    if not HAS_ANALYTICS:
        return {"status": "not_configured", "message": "Set ANALYTICS_API_KEY"}
    return AnalyticsProvider().get_dashboard_summary()
```

### Pattern 4: Gateway Resolution

```python
from providers.payments.registry import resolve_gateway

def process_payment(order, amount: float):
    gateway = resolve_gateway(order.country_code)

    if gateway == "stripe":
        return process_stripe_payment(order, amount)
    elif gateway == "tap":
        return process_tap_payment(order, amount)
    elif gateway == "paytabs":
        return process_paytabs_payment(order, amount)
    else:
        raise NotImplementedError(f"Unsupported gateway: {gateway}")
```

---

## 7. Testing Providers

### 7.1 Testing Pattern: Mock External SDKs

```python
from unittest.mock import patch, MagicMock

def test_process_image_with_mock():
    with patch("providers.image.free_image_tools.auto_rotate") as mock_rotate:
        mock_rotate.return_value = b"rotated"
        result = auto_rotate(b"input")
        mock_rotate.assert_called_once_with(b"input")
        assert result == b"rotated"
```

### 7.2 Testing Pattern: Mock Ollama API

```python
def test_embed_text_with_mock_ollama():
    from providers.ai.text import embed_text
    mock_embedding = [0.1, 0.2, 0.3]
    mock_response = json.dumps({"embedding": mock_embedding}).encode()

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=MagicMock(read=MagicMock(return_value=mock_response)))
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_ctx

        result = embed_text("test")
        assert result == mock_embedding
```

### 7.3 Testing Pattern: Test Graceful Degradation

```python
def test_preprocess_skips_when_no_cv2():
    from providers.image.free_image_tools import auto_rotate

    with patch("providers.image.free_image_tools.HAS_CV2", False):
        # When CV2 not installed, function should handle gracefully
        pass
```

---

## 8. Best Practices

### DO

1. **Import providers at module level** — not inside functions (unless avoiding circular imports)
2. **Use `HAS_<SDK>` flags** to check availability before calling
3. **Catch specific exceptions** — `ConnectionError`, `TimeoutError`, `NotImplementedError`
4. **Return meaningful fallbacks** — never crash because a provider is unavailable
5. **Use async workers** for CPU-bound provider work (image processing, embeddings)
6. **Mock external APIs in tests** — never hit real APIs during testing

### DON'T

1. **Don't import domains in providers** — this violates the architecture laws
2. **Don't catch bare `Exception`** — always catch specific exception types
3. **Don't put business logic in providers** — decisions belong in domain services
4. **Don't access the database from providers** — providers are stateless
5. **Don't hardcode API keys** — use `os.environ.get()` or `settings`
6. **Don't make synchronous network calls in async contexts** — use `async_workers`

---

## 9. Troubleshooting

### Issue: `ImportError: No module named 'stripe'`

**Cause:** The `stripe` SDK is not installed.
**Fix:** The provider handles this gracefully with `HAS_STRIPE = False`. Domain services should check the flag:
```python
from providers.payments.stripe_sdk import HAS_STRIPE

if not HAS_STRIPE:
    # Use fallback payment method
    pass
```

### Issue: `ConnectionError` when calling Ollama

**Cause:** Ollama is not running or unreachable.
**Fix:** Providers catch this and return empty results. Domain services should handle:
```python
embedding = embed_text("product")
if not embedding:  # Empty list on failure
    # Use fallback (e.g., keyword matching)
    pass
```

### Issue: Provider returns empty results

**Cause:** Usually a network timeout or API rate limit.
**Fix:** Check provider logs, implement retry logic in domain service:
```python
for attempt in range(3):
    result = provider_call()
    if result:
        break
    time.sleep(1 * (attempt + 1))
```

### Issue: Circular import when wiring provider

**Cause:** Domain service imports provider, provider accidentally imports domain.
**Fix:** Run the architecture audit:
```bash
python -m pytest tests/architecture/ -v
```

---

## Appendix A: Provider Availability Flags

| Flag | Provider | SDK Checked |
|------|----------|-------------|
| `HAS_STRIPE` | payments | `stripe` |
| `HAS_PAYPAL` | payments | `paypalrestsdk` |
| `HAS_TAP` | payments | `tap` |
| `HAS_PAYTABS` | payments | `paytabs` |
| `HAS_THAWANI` | payments | `thawani` |
| `HAS_TWILIO` | comms | `twilio` |
| `HAS_WHATSAPP` | comms | `whatsapp-business` |
| `HAS_CV2` | image | `opencv-python` |
| `HAS_REMBG` | image | `rembg` |
| `HAS_PIL` | image | `Pillow` |
| `HAS_SCIPY` | image | `scipy` |
| `HAS_SKIMAGE` | image | `scikit-image` |
| `HAS_TESSERACT` | ocr | `pytesseract` |
| `HAS_QRCODE` | qr | `qrcode` |
| `HAS_BARCODE` | barcode | `python-barcode` |
| `HAS_PYZBAR` | scanner | `pyzbar` |
| `HAS_VADER` | sentiment | `vaderSentiment` |
| `HAS_HF` | huggingface | `requests` |
| `HAS_BOTO3` | storage | `boto3` |
| `HAS_REDIS` | cache | `redis` |

## Appendix B: Environment Variables

| Variable | Provider | Purpose |
|----------|----------|---------|
| `STRIPE_SECRET_KEY` | Stripe | API authentication |
| `STRIPE_WEBHOOK_SECRET` | Stripe | Webhook verification |
| `TWILIO_ACCOUNT_SID` | Twilio | Account identifier |
| `TWILIO_AUTH_TOKEN` | Twilio | API authentication |
| `SMTP_HOST` | Email | Mail server |
| `SMTP_USER` | Email | Mail username |
| `SMTP_PASSWORD` | Email | Mail password |
| `OLLAMA_BASE_URL` | AI/Ollama | Ollama server URL |
| `HF_API_TOKEN` | HuggingFace | Inference API token |
| `ANALYTICS_API_KEY` | Analytics | Analytics service key |
| `S3_BUCKET` | Storage | S3 bucket name |
| `S3_REGION` | Storage | AWS region |
| `S3_ACCESS_KEY_ID` | Storage | AWS credentials |
| `S3_SECRET_ACCESS_KEY` | Storage | AWS credentials |
| `STORAGE_BACKEND` | Storage | `local` or `s3` |
| `JWT_SECRET` | Auth | Token signing secret |
| `ENCRYPTION_KEY` | Security | Field encryption key |
| `FIELD_ENCRYPTION_KEY` | Security | Database field encryption |

---

*End of Provider Reference Guide*
