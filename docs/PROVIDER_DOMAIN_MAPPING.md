# Provider — Domain Mapping

> **Generated:** 2026-08-26
> **Purpose:** Maps every external provider tool to the domain(s) that consume it, with specific use cases and priority.
> **Scope:** All 15 domains × all provider categories (AI/ML, Communication, Payments, Geography, Security, Image, Shipping, etc.)

---

## Priority Legend

| Priority | Meaning |
|----------|---------|
| **CRITICAL** | Required for core business operations; domain is non-functional without it |
| **HIGH** | Required for primary user-facing features; workarounds are limited |
| **MEDIUM** | Enhances functionality; domain operates but with reduced capability |

---

## 1. Catalog Domain (Products, Variants, Search, Uploads)

### Service: `ai_upload_service.py`
| Provider Tool | Use Case | Priority |
|--------------|----------|----------|
| **AI Image Service** (`providers.media.services.ai`) | Infer product names, suggest categories/tags, generate descriptions, detect colors, suggest variant templates — all from uploaded images | CRITICAL |
| **Storage Backend** (`providers.storage.storage_backend`) | Persist uploaded product images to S3/local storage during AI upload pipeline | CRITICAL |
| **AI HuggingFace** (`providers.ai.huggingface`) | Fallback ML model for image classification and product name inference when rule-based system is insufficient | HIGH |
| **BG Removal** (`providers.image.free_image_tools.magic_erase`) | Remove backgrounds from supplier-uploaded product images using rembg/OpenCV | MEDIUM |
| **Image Processing Pipeline** (`providers.image.free_image_tools`) | Smart crop, auto-rotate, auto-lighting, upscale, denoise, white balance, compress, WebP convert — full preprocessing pipeline for catalog images | HIGH |
| **OCR** (`providers.image.ocr`) | Extract text from supplier-uploaded images (e.g., labels, packaging text) | MEDIUM |
| **Barcode/QR Scanner** (`providers.scanner.scanner`) | Scan barcodes/QR codes from product images for SKU/UPC lookup | MEDIUM |

### Service: `search_service.py`
| Provider Tool | Use Case | Priority |
|--------------|----------|----------|
| **Vector Search** (`providers.ai.search.AdvancedSearchEngine`) | Semantic product search using embeddings (nomic-embed-text/Ollama), fuzzy matching, autocomplete suggestions | HIGH |
| **Text Embedding** (`providers.ai.text.embed_text`) | Generate vector embeddings for product catalog to enable semantic search ranking | HIGH |

---

## 2. Customers Domain (Cart, Wishlist, Reviews, Coupons)

### Service: `cart_service.py`
| Provider Tool | Use Case | Priority |
|--------------|----------|----------|
| **Shipping Calculator** (`providers.shipping.shipping_calculator`) | Re-exported via `cart_service` — calculate shipping rates for cart items across carriers (FedEx/UPS/DHL/Aramex/local post) | HIGH |

### Service: `search_service.py`
| Provider Tool | Use Case | Priority |
|--------------|----------|----------|
| **Vector Search** (`providers.ai.search.AdvancedSearchEngine`) | Natural language product search with NLP query parsing, category synonym expansion, fuzzy matching | HIGH |
| **Text Embedding** (`providers.ai.text`) | Embed user queries and product data for semantic similarity ranking | HIGH |

### Service: `reviews_service.py`
| Provider Tool | Use Case | Priority |
|--------------|----------|----------|
| **Sentiment Analysis** (`providers.ai.sentiment`) | Analyze review text sentiment for automated moderation and quality scoring | MEDIUM |
| **Image Processing** (`providers.image.free_image_tools`) | Compress/resize reviewer-uploaded photos before storage | LOW |

### Service: `coupons_service.py`
| Provider Tool | Use Case | Priority |
|--------------|----------|----------|
| *(No external providers)* | Pure DB logic — coupon validation, discount calculation, usage tracking | — |

### Service: `wishlist_service.py`
| Provider Tool | Use Case | Priority |
|--------------|----------|----------|
| *(No external providers)* | Pure DB logic — wishlist CRUD operations | — |

### Service: `customer_health_engine.py`
| Provider Tool | Use Case | Priority |
|--------------|----------|----------|
| **Recommendation Engine** (`providers.ai.recommendation`) | Power customer health scoring via purchase patterns, wishlist signals, and collaborative filtering | HIGH |

---

## 3. Orders Domain (Checkout, Payment, Shipping)

### Service: `orders_service.py`
| Provider Tool | Use Case | Priority |
|--------------|----------|----------|
| **Stripe** (`providers.payments.stripe`) | Process refunds via `refund_payment_intent`; Stripe secret key resolution for payment operations | CRITICAL |
| **Payment Registry** (`providers.payments.registry`) | Resolve active payment provider at runtime (Stripe/PayPal/Tap/PayTabs/Thawani) | CRITICAL |
| **Payment Webhooks** (`providers.payments.webhooks`) | Handle async payment confirmation events from PSPs | CRITICAL |
| **Shipping Calculator** (`providers.shipping.shipping_calculator`) | Calculate shipping rates for orders; carrier comparison and delivery estimates | HIGH |
| **Email Service** (`domains.comms.services.transactional_email_service`) | Send order status change emails, refund confirmation emails | HIGH |
| **Notification Service** (`domains.comms`) | Create in-app notifications for order updates, shipping alerts | HIGH |
| **Currency Rates** (`providers.geography.rates`) | Convert order totals to local currency for multi-country checkout | MEDIUM |
| **IP Geolocation** (`providers.geolocation`) | Detect customer country for tax/shipping calculation at checkout | MEDIUM |

### Service: `admin_orders_service.py`
| Provider Tool | Use Case | Priority |
|--------------|----------|----------|
| **Stripe** (`providers.payments.stripe`) | Admin-initiated refunds via Stripe API | CRITICAL |
| **Bank API** (`providers.finance.bank_api`) | Verify bank transactions during reconciliation, process supplier/logistics payouts | HIGH |

---

## 4. Finance Domain (Invoices, Expenses, Reconciliation)

### Service: `finance_service.py`
| Provider Tool | Use Case | Priority |
|--------------|----------|----------|
| **Bank API** (`providers.finance.bank_api`) | Bank connection testing, transaction fetching, fund transfers for supplier/logistics payouts | CRITICAL |
| **Stripe Connect** (`providers.payments.connect`) | Marketplace split payments — route funds between platform, suppliers, logistics partners | CRITICAL |
| **Payment Registry** (`providers.payments.registry`) | Determine active payment provider for dispatch (Stripe/PayPal/Tap/PayTabs/Thawani) | HIGH |
| **Currency Rates** (`providers.geography.rates`) | Multi-currency reconciliation, VAT remittance calculations across countries | HIGH |
| **AI Finance** (`providers.ai.finance_ai`) | Automated bank transaction categorization, anomaly detection in financial flows | MEDIUM |
| **OCR** (`providers.image.ocr`) | Extract text from uploaded invoice/receipt images for data entry | MEDIUM |
| **Automation Scheduler** (`providers.automation.scheduler`) | Schedule recurring payouts, batch settlement processing | HIGH |

### Service: `commission_engine.py`
| Provider Tool | Use Case | Priority |
|--------------|----------|----------|
| *(No external providers)* | Pure calculation logic — commission rate resolution by badge/category/product | — |

---

## 5. Communications Domain (Email, SMS, Notifications)

### Service: `proxy_communication.py`
| Provider Tool | Use Case | Priority |
|--------------|----------|----------|
| **Twilio** (`providers.comms.twilio`) | Proxy phone number allocation, SMS sending, voice calls, call recording for B2B masked communications | CRITICAL |
| **WhatsApp** (`providers.comms.whatsapp`) | Send WhatsApp messages to customers/suppliers for order updates, delivery coordination | HIGH |
| **Email** (`providers.comms.email`) | Send transactional emails (order confirmations, shipping notices, refund alerts) | CRITICAL |
| **Encryption** (`providers.security.encryption`) | Encrypt proxy message content for B2B communication channels | HIGH |

### Service: `events.py`
| Provider Tool | Use Case | Priority |
|--------------|----------|----------|
| **Event Bus** (`infrastructure.messaging.events.event_bus`) | Publish/receive cross-domain events (message sent, notification sent, ticket created) | HIGH |

---

## 6. Logistics Domain (Shipping, Tracking)

### Service: `features.py` / `events.py`
| Provider Tool | Use Case | Priority |
|--------------|----------|----------|
| **Shipping Calculator** (`providers.shipping.shipping_calculator`) | Core logistics: rate calculation, carrier comparison, delivery day estimation across FedEx/UPS/DHL/Aramex/local post | CRITICAL |
| **QR/Barcode** (`providers.qr.qr_generator`, `providers.barcode.barcode_generator`) | Generate QR codes for shipment labels, tracking numbers, parcel verification | HIGH |
| **QR Parcel Verification** (`providers.qr.parcel_verification_service`) | Scan/verify parcels at pickup, transit, and delivery checkpoints | HIGH |
| **Maps** (`providers.geography.map`) | Display shipment routes, warehouse locations, delivery zones | MEDIUM |
| **IP Geolocation** (`providers.geography.ip`) | Auto-detect origin country for shipment routing | MEDIUM |
| **Twilio** (`providers.comms.twilio`) | SMS notifications for delivery updates, pickup coordination | HIGH |
| **WhatsApp** (`providers.comms.whatsapp`) | WhatsApp delivery notifications and driver-customer communication | MEDIUM |
| **Automation Scheduler** (`providers.automation.scheduler`) | Schedule recurring shipment status sync, delivery estimate updates | MEDIUM |

---

## 7. Country Domain (Geo, Currency)

### Service: `events.py`
| Provider Tool | Use Case | Priority |
|--------------|----------|----------|
| **Country Provider** (`providers.geography.country`) | Country search, currency mapping, region detection, phone code lookup | HIGH |
| **IP Geolocation** (`providers.geography.ip`, `providers.geography.geoip`) | Detect user country from IP for auto-localization, tax rules, shipping eligibility | HIGH |
| **Currency Rates** (`providers.geography.rates`) | Real-time exchange rates for multi-currency pricing display | HIGH |
| **Country HTTP** (`providers.geography.country_http`) | Fetch live country data from external APIs (restcountries.com etc.) | MEDIUM |
| **External Data** (`providers.geography.external_data`) | Fetch supplementary geo data (languages, timezones, VAT rates) | MEDIUM |

---

## 8. Promotions Domain (Discounts, Flash Sales)

### Service: `promotions_write_service.py` / `flash_sale_service.py`
| Provider Tool | Use Case | Priority |
|--------------|----------|----------|
| **Email Service** (`providers.comms.email`) | Send flash sale announcement emails, promotional campaign blasts | HIGH |
| **WhatsApp** (`providers.comms.whatsapp`) | Broadcast promotional messages to opted-in customers | MEDIUM |
| **Twilio** (`providers.comms.twilio`) | SMS flash sale alerts for high-priority promotions | MEDIUM |
| **Recommendation Engine** (`providers.ai.recommendation`) | Target personalized promotions based on user purchase history | MEDIUM |
| **Automation Scheduler** (`providers.automation.scheduler`) | Schedule flash sale start/end, time-limited coupon activation | HIGH |
| **Image Processing** (`providers.image.free_image_tools`) | Process promotional banner images, optimize hero images for campaigns | MEDIUM |
| **Price Intelligence** (`providers.ai.price_intelligence`) | Dynamic discount pricing based on competitor analysis and demand signals | MEDIUM |

---

## 9. Security Domain (Authentication, Authorization)

### Service: `features.py` / `events.py`
| Provider Tool | Use Case | Priority |
|--------------|----------|----------|
| **JWT** (`providers.auth.jwt`) | Issue/validate JSON Web Tokens for user sessions, API authentication | CRITICAL |
| **OAuth** (`providers.auth.oauth`) | Third-party login (Google, Facebook, Apple), OAuth2 flow for API access | CRITICAL |
| **TOTP** (`providers.auth.totp`) | Time-based one-time passwords for 2FA/MFA | HIGH |
| **Apple Auth** (`providers.auth.apple`) | Sign in with Apple for iOS users | HIGH |
| **Encryption** (`providers.security.encryption`) | Encrypt PII at rest, secure communications, hash sensitive data | CRITICAL |
| **Threat Intel** (`providers.security.threat_intel`) | Fetch Tor exit-node IP list for blocking anonymized malicious traffic | HIGH |
| **Watchlist** (`providers.security.watchlist`) | Sanctions/PEP screening via external vendors (LexisNexis, World-Check) during supplier onboarding | HIGH |
| **IP Geolocation** (`providers.geolocation`) | Geo-blocking, impossible travel detection, IP reputation scoring | MEDIUM |
| **Sentiment Analysis** (`providers.ai.sentiment`) | Detect abusive/harassing messages in proxy communications | LOW |

---

## 10. Accounts Domain (Users, Profiles)

### Service: *(auth flows, profile management)*
| Provider Tool | Use Case | Priority |
|--------------|----------|----------|
| **JWT** (`providers.auth.jwt`) | Session token generation/validation for user authentication | CRITICAL |
| **OAuth** (`providers.auth.oauth`) | Social login integration (Google, Facebook) | HIGH |
| **TOTP** (`providers.auth.totp`) | Two-factor authentication for account security | HIGH |
| **Apple Auth** (`providers.auth.apple`) | Apple ID sign-in for mobile users | MEDIUM |
| **Email** (`providers.comms.email`) | Welcome emails, password reset, account verification | CRITICAL |
| **Twilio** (`providers.comms.twilio`) | SMS-based OTP for phone verification | HIGH |
| **IP Geolocation** (`providers.geolocation`) | Detect signup country, flag suspicious login locations | MEDIUM |
| **Image Processing** (`providers.image.free_image_tools`) | Process/verify profile photos and ID document uploads | MEDIUM |
| **OCR** (`providers.image.ocr`) | Extract text from uploaded ID documents for KYC verification | MEDIUM |

---

## 11. HR Domain (Employees, Hierarchy)

### Service: *(employee management, access control)*
| Provider Tool | Use Case | Priority |
|--------------|----------|----------|
| **Watchlist** (`providers.security.watchlist`) | Screen new hires against sanctions/PEP lists during employee onboarding | HIGH |
| **Email** (`providers.comms.email`) | Send onboarding emails, policy notifications, internal announcements | HIGH |
| **Twilio** (`providers.comms.twilio`) | SMS notifications for shift schedules, urgent alerts | MEDIUM |
| **Encryption** (`providers.security.encryption`) | Encrypt employee PII, salary data, and personal documents | CRITICAL |
| **Image Processing** (`providers.image.free_image_tools`) | Process employee profile photos, ID document images | LOW |

---

## 12. Governance Domain (Compliance, Fraud)

### Service: *(compliance, audit policies, RBAC)*
| Provider Tool | Use Case | Priority |
|--------------|----------|----------|
| **Threat Intel** (`providers.security.threat_intel`) | Feed Tor exit-nodes and known-malicious IPs into fraud detection engine | HIGH |
| **Watchlist** (`providers.security.watchlist`) | AML/KYC compliance screening for suppliers and partners | CRITICAL |
| **Encryption** (`providers.security.encryption`) | Data encryption for compliance with data residency laws (GDPR, etc.) | CRITICAL |
| **Automation Scheduler** (`providers.automation.scheduler`) | Schedule compliance audits, data retention policy enforcement | HIGH |
| **News/RSS** (`providers.news.rss_provider`) | Monitor regulatory news feeds for compliance updates | LOW |
| **AI/ML Sentiment** (`providers.ai.sentiment`) | Detect fraudulent review patterns, fake supplier profiles | MEDIUM |

---

## 13. Audit Domain (Logging, Data Residency)

### Service: `audit_service.py` / `data_residency_service.py`
| Provider Tool | Use Case | Priority |
|--------------|----------|----------|
| **Encryption** (`providers.security.encryption`) | Encrypt audit logs at rest; ensure tamper-evident log storage | CRITICAL |
| **Storage Backend** (`providers.storage.storage_backend`) | Archive audit logs to S3/long-term storage | HIGH |
| **Data Residency** (`providers.geography.country`) | Enforce data residency rules — ensure audit logs for each country's users stay within jurisdictional boundaries | CRITICAL |
| **Automation Scheduler** (`providers.automation.scheduler`) | Schedule log rotation, archival, and purging per retention policies | HIGH |
| **OCR** (`providers.image.ocr`) | Extract text from uploaded compliance documents for e-discovery | MEDIUM |
| **News/RSS** (`providers.news.rss_provider`) | Monitor security advisory feeds for compliance relevance | LOW |

---

## 14. Analytics Domain (Reports, Dashboards)

### Service: `flat_analytics_service.py` / `analytics_controller.py`
| Provider Tool | Use Case | Priority |
|--------------|----------|----------|
| **Analytics Provider** (`providers.analytics.analytics`) | Dashboard summaries, sales trends, product performance metrics, AI-generated insights | HIGH |
| **Chatbot Analytics** (`providers.ai.chatbot`) | Track chatbot query volumes, click-through rates, intent classification, product search analytics | HIGH |
| **Recommendation Engine** (`providers.ai.recommendation`) | Power "you may also like" sections, personalized homepage product feeds | HIGH |
| **Price Intelligence** (`providers.ai.price_intelligence`) | Competitor price tracking, dynamic pricing recommendations | MEDIUM |
| **Sentiment Analysis** (`providers.ai.sentiment`) | Aggregate review sentiment trends for product quality dashboards | MEDIUM |
| **Currency Rates** (`providers.geography.rates`) | Normalize revenue metrics across currencies for multi-country dashboards | MEDIUM |
| **Automation Scheduler** (`providers.automation.scheduler`) | Schedule analytics snapshot refresh (hourly/daily aggregation jobs) | HIGH |
| **Storage Backend** (`providers.storage.storage_backend`) | Persist analytics snapshots and cached report data | MEDIUM |

---

## 15. Suppliers Domain (Onboarding, Catalog)

### Service: `supplier_service.py` (and sub-services)
| Provider Tool | Use Case | Priority |
|--------------|----------|----------|
| **Email** (`providers.comms.email`) | Supplier onboarding emails, verification notices, settlement notifications | HIGH |
| **Twilio** (`providers.comms.twilio`) | SMS order alerts to suppliers, delivery coordination messages | HIGH |
| **WhatsApp** (`providers.comms.whatsapp`) | WhatsApp order notifications for suppliers without email access | MEDIUM |
| **Image Processing** (`providers.image.free_image_tools`) | Process supplier-uploaded product images — auto-enhancement, background removal, compression | HIGH |
| **OCR** (`providers.image.ocr`) | Extract data from supplier-uploaded certificates, licenses, product spec sheets | MEDIUM |
| **Barcode/QR** (`providers.barcode.barcode_generator`) | Generate barcodes for supplier product SKUs | MEDIUM |
| **Watchlist** (`providers.security.watchlist`) | Sanctions screening during supplier onboarding (KYC/AML) | CRITICAL |
| **Bank API** (`providers.finance.bank_api`) | Validate supplier bank account details, process settlements | HIGH |
| **Storage Backend** (`providers.storage.storage_backend`) | Store supplier-uploaded documents (certificates, catalogs, media) | HIGH |
| **Country Provider** (`providers.geography.country`) | Validate supplier operating regions, supported currencies | MEDIUM |

---

## Cross-Provider Dependency Matrix

> Shows which providers serve the most domains — these are the highest-value integration points.

| Provider Tool | Domains Served | Count |
|--------------|----------------|-------|
| **Encryption** (`providers.security.encryption`) | Security, Accounts, HR, Governance, Audit, Comms | 6 |
| **Email** (`providers.comms.email`) | Orders, Comms, Promotions, Accounts, HR, Suppliers | 6 |
| **Twilio** (`providers.comms.twilio`) | Comms, Logistics, Promotions, Accounts, HR, Suppliers | 6 |
| **Image Processing** (`providers.image.free_image_tools`) | Catalog, Reviews, Promotions, Accounts, HR, Suppliers | 6 |
| **Storage Backend** (`providers.storage.storage_backend`) | Catalog, Audit, Analytics, Suppliers | 4 |
| **JWT** (`providers.auth.jwt`) | Security, Accounts | 2 |
| **OAuth** (`providers.auth.oauth`) | Security, Accounts | 2 |
| **TOTP** (`providers.auth.totp`) | Security, Accounts | 2 |
| **IP Geolocation** (`providers.geolocation`) | Orders, Logistics, Country, Security, Accounts | 5 |
| **Currency Rates** (`providers.geography.rates`) | Orders, Finance, Country, Analytics | 4 |
| **Shipping Calculator** (`providers.shipping.shipping_calculator`) | Orders, Customers (cart), Logistics | 3 |
| **Stripe** (`providers.payments.stripe`) | Orders, Finance | 2 |
| **Bank API** (`providers.finance.bank_api`) | Finance, Orders, Suppliers | 3 |
| **Watchlist** (`providers.security.watchlist`) | Security, Governance, HR, Suppliers | 4 |
| **Threat Intel** (`providers.security.threat_intel`) | Security, Governance | 2 |
| **OCR** (`providers.image.ocr`) | Catalog, Finance, Accounts, Audit, Suppliers | 5 |
| **WhatsApp** (`providers.comms.whatsapp`) | Comms, Logistics, Promotions, Suppliers | 4 |
| **Recommendation Engine** (`providers.ai.recommendation`) | Customers, Promotions, Analytics | 3 |
| **Automation Scheduler** (`providers.automation.scheduler`) | Finance, Logistics, Promotions, Governance, Audit, Analytics | 6 |
| **Country Provider** (`providers.geography.country`) | Country, Analytics, Audit, Suppliers | 4 |
| **QR/Barcode** (`providers.qr`, `providers.barcode`) | Logistics, Catalog, Suppliers | 3 |
| **AI Search** (`providers.ai.search`) | Catalog, Customers | 2 |
| **Text Embedding** (`providers.ai.text`) | Catalog, Customers | 2 |
| **AI Image Service** (`providers.media.services.ai`) | Catalog | 1 |
| **HuggingFace** (`providers.ai.huggingface`) | Catalog | 1 |
| **Sentiment Analysis** (`providers.ai.sentiment`) | Reviews, Security, Analytics | 3 |
| **Price Intelligence** (`providers.ai.price_intelligence`) | Promotions, Analytics | 2 |
| **Chatbot** (`providers.ai.chatbot`) | Analytics | 1 |
| **News/RSS** (`providers.news.rss_provider`) | Governance, Audit | 2 |
| **Apple Auth** (`providers.auth.apple`) | Security, Accounts | 2 |
| **Stripe Connect** (`providers.payments.connect`) | Finance | 1 |
| **PayPal** (`providers.payments.paypal`) | Orders (via registry) | 1 |
| **Tap** (`providers.payments.tap`) | Orders (via registry) | 1 |
| **PayTabs** (`providers.payments.paytabs`) | Orders (via registry) | 1 |
| **Thawani** (`providers.payments.thawani`) | Orders (via registry) | 1 |
| **AI Finance** (`providers.ai.finance_ai`) | Finance | 1 |
| **Voice-to-Text** (`providers.voice.voice_to_text`) | *(available, future use)* | 0 |
| **Visual Voice Search** (`providers.ai.visual_voice_search_service`) | *(available, future use)* | 0 |
| **Translation** (`providers.ai.text`) | *(available, future EN→AR use)* | 0 |
| **Web Search** (`providers.ai.web_search`) | *(available, future use)* | 0 |

---

## Provider Categories Summary

### Image Processing
| Tool | Capability | Domains |
|------|-----------|---------|
| `providers.image.free_image_tools` | Magic erase (BG removal), smart crop, auto-rotate, auto-lighting, upscale, denoise, white balance, compress, WebP convert, color enhance, auto levels | Catalog, Reviews, Promotions, Accounts, HR, Suppliers |
| `providers.image.bg_remover` | AI background removal via rembg | Catalog |
| `providers.image.ocr` | Optical character recognition for documents/labels | Catalog, Finance, Accounts, Audit, Suppliers |
| `providers.image.image` | Core Pillow image operations | Catalog |
| `providers.image.parcel_verification` | Parcel image verification | Logistics |

### AI / ML
| Tool | Capability | Domains |
|------|-----------|---------|
| `providers.ai.chatbot` | Intent classification, session management, product search assistant | Analytics |
| `providers.ai.search` | NLP query parsing, vector embedding search, fuzzy matching, autocomplete | Catalog, Customers |
| `providers.ai.text` | Text embedding (nomic-embed-text), cosine similarity, translation | Catalog, Customers |
| `providers.ai.sentiment` | Sentiment analysis for reviews, messages, fraud signals | Reviews, Security, Analytics |
| `providers.ai.recommendation` | Collaborative filtering, purchase-pattern recommendations | Customers, Promotions, Analytics |
| `providers.ai.price_intelligence` | Competitor price tracking, dynamic pricing | Promotions, Analytics |
| `providers.ai.vision` | Image classification, object detection | Catalog |
| `providers.ai.image_similarity` | Visual similarity matching for duplicate detection | Catalog |
| `providers.ai.huggingface` | HuggingFace Inference API fallback for ML tasks | Catalog |
| `providers.ai.finance_ai` | Bank transaction categorization, financial anomaly detection | Finance |
| `providers.media.services.ai` | Product name inference, category suggestion, description generation, color detection | Catalog |
| `providers.ai.visual_voice_search_service` | Voice-activated visual product search | *(future)* |

### Communication
| Tool | Capability | Domains |
|------|-----------|---------|
| `providers.comms.email` | SMTP/transactional email delivery | Orders, Comms, Promotions, Accounts, HR, Suppliers |
| `providers.comms.twilio` | SMS, voice calls, proxy phone numbers, call recording | Comms, Logistics, Promotions, Accounts, HR, Suppliers |
| `providers.comms.whatsapp` | WhatsApp Business API messaging | Comms, Logistics, Promotions, Suppliers |

### Payments
| Tool | Capability | Domains |
|------|-----------|---------|
| `providers.payments.stripe` | Card payments, refunds, PaymentIntents | Orders, Finance |
| `providers.payments.paypal` | PayPal checkout | Orders (via registry) |
| `providers.payments.tap` | Tap Payments (MENA region) | Orders (via registry) |
| `providers.payments.paytabs` | PayTabs (MENA region) | Orders (via registry) |
| `providers.payments.thawani` | Thawani (Saudi/Qatar) | Orders (via registry) |
| `providers.payments.connect` | Stripe Connect marketplace splits | Finance |
| `providers.payments.registry` | Runtime provider resolution | Orders, Finance |
| `providers.payments.webhooks` | PSP webhook handling | Orders |
| `providers.finance.bank_api` | Bank account verification, transfers | Finance, Orders, Suppliers |

### Geography
| Tool | Capability | Domains |
|------|-----------|---------|
| `providers.geography.country` | Country search, currency mapping, region data | Country, Analytics, Audit, Suppliers |
| `providers.geography.ip` | IP-based geolocation | Orders, Logistics, Country, Security, Accounts |
| `providers.geography.geoip` | MaxMind GeoIP database lookups | Country, Security |
| `providers.geography.rates` | Real-time currency exchange rates | Orders, Finance, Country, Analytics |
| `providers.geography.map` | Map rendering, route visualization | Logistics |
| `providers.geography.country_http` | External country data API | Country |
| `providers.geography.external_data` | Supplementary geo metadata | Country |

### Security
| Tool | Capability | Domains |
|------|-----------|---------|
| `providers.auth.jwt` | JSON Web Token issue/validate | Security, Accounts |
| `providers.auth.oauth` | OAuth2 flow, social login | Security, Accounts |
| `providers.auth.totp` | TOTP/HOTP for 2FA | Security, Accounts |
| `providers.auth.apple` | Sign in with Apple | Security, Accounts |
| `providers.security.encryption` | AES/bcrypt encryption, key management | Security, Accounts, HR, Governance, Audit, Comms |
| `providers.security.threat_intel` | Tor exit list, threat feeds | Security, Governance |
| `providers.security.watchlist` | Sanctions/PEP/AML screening | Security, Governance, HR, Suppliers |

### Shipping
| Tool | Capability | Domains |
|------|-----------|---------|
| `providers.shipping.shipping_calculator` | Rate calculation, carrier comparison, delivery estimation (FedEx/UPS/DHL/Aramex/local post) | Orders, Customers (cart), Logistics |

### QR / Barcode
| Tool | Capability | Domains |
|------|-----------|---------|
| `providers.qr.qr_generator` | QR code generation for tracking/labels | Logistics, Catalog |
| `providers.qr.parcel_verification_service` | QR-based parcel verification | Logistics |
| `providers.barcode.barcode_generator` | Barcode generation (Code128/EAN/UPC) | Logistics, Catalog, Suppliers |
| `providers.scanner.scanner` | QR/barcode scanning from images | Catalog |

### Storage
| Tool | Capability | Domains |
|------|-----------|---------|
| `providers.storage.storage_backend` | S3/local storage abstraction | Catalog, Audit, Analytics, Suppliers |
| `providers.storage.s3_client` | AWS S3 direct operations | Catalog, Suppliers |

### Automation
| Tool | Capability | Domains |
|------|-----------|---------|
| `providers.automation.scheduler` | Cron job scheduling, recurring tasks | Finance, Logistics, Promotions, Governance, Audit, Analytics |

### News / Research
| Tool | Capability | Domains |
|------|-----------|---------|
| `providers.news.rss_provider` | RSS feed parsing for regulatory/news monitoring | Governance, Audit |
| `providers.ai.web_search` | External web search for product enrichment | *(future)* |

---

## Implementation Notes

### Provider Availability Flags
All providers use `HAS_<SDK>` boolean flags (e.g., `HAS_STRIPE`, `HAS_TWILIO`, `HAS_OPENCV`) imported from `providers.config`. Domains must gracefully degrade when a provider SDK is not installed.

### Domain Isolation Rule
Providers must **never** import from `domains/`. All data flows through:
- Domain → Provider: via function parameters (DTOs/primitives)
- Provider → Domain: via return values (dataclasses/pydantic models)

### Async Workers
`providers.async_workers` provides thread-pool and process-pool executors for background tasks (AI upload jobs, email dispatch, analytics snapshots). All CPU-bound provider work (image processing, embedding generation) should run through this layer.

### Multi-Country Payment Routing
The `providers.payments.registry` resolves the active payment provider per country:
- **GCC countries** → Tap / PayTabs
- **Saudi/Qatar** → Thawani
- **Global** → Stripe / PayPal

### Data Residency
The Audit domain enforces that provider calls for a given country's users stay within jurisdictional boundaries. Storage and encryption providers must respect `country_code` parameters to route data to the correct regional backend.
