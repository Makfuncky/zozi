# Provider Tools Refactoring Plan

## Core Principle
**Providers must ONLY wrap external SDKs/APIs. No business logic. No domain imports.**

A provider tool is a pure function or class that:
1. Takes primitive inputs (str, int, float, dict, list)
2. Calls an external API/SDK
3. Returns the result (dict, bytes, or simple dataclass)
4. Does NOT access database, domain models, or domain services

## Provider Categories

### 1. `providers/auth/` — Authentication providers
- JWT decode/encode, TOTP, OAuth (Google, Apple, Facebook)
- **Should**: Decode tokens, verify signatures, generate TOTP secrets
- **Should NOT**: Query user database, check permissions

### 2. `providers/payments/` — Payment gateway SDKs
- Stripe, PayPal, PayTabs, Tap, Thawani
- **Should**: Create charges, refunds, verify webhooks
- **Should NOT**: Update order status, calculate taxes, send notifications

### 3. `providers/image/` — Image processing
- Background removal, OCR, image search, resizing
- **Should**: Process images, remove backgrounds, run OCR
- **Should NOT**: Update product catalogs, store images

### 4. `providers/geography/` — Geo/IP services
- IP geolocation, reverse geocode, currency rates
- **Should**: Resolve IP to country, geocode addresses
- **Should NOT**: Apply country rules, validate addresses

### 5. `providers/ai/` — AI/ML model inference
- Text generation, embeddings, translation, MCP tools
- **Should**: Call model APIs, tokenize, embed
- **Should NOT**: Store chat history, manage conversations

### 6. `providers/comms/` — Communication SDKs
- Twilio, WhatsApp, SendGrid
- **Should**: Send SMS, WhatsApp messages, emails
- **Should NOT**: Manage notification preferences, queue messages

### 7. `providers/media/` — Media management
- **Should**: Handle file uploads to S3/CDN, generate URLs
- **Should NOT**: Track asset ownership, manage permissions

### 8. `providers/analytics/` — Analytics SDKs
- **Should**: Track events to external analytics platforms
- **Should NOT**: Read/write internal analytics data

### 9. `providers/security/` — Security tools
- Encryption, fraud detection, watchlists
- **Should**: Encrypt/decrypt, check fraud blacklists
- **Should NOT**: Manage security policies

## Migration Strategy

### Phase 1: Remove Junk
- Delete `_unstage_files/` directory
- Remove duplicate files (keep canonical versions)
- Remove stub implementations (or mark clearly)

### Phase 2: Extract Business Logic
For each file with domain imports:
1. Identify the external SDK wrapper code → KEEP
2. Identify business logic using domain models → MOVE to `domains/{domain}/services/`
3. Replace domain imports with primitive parameters

### Phase 3: Consolidation
- Merge duplicate implementations
- Standardize naming conventions
- Fix import ordering

### Phase 4: Testing
- Create test stubs for each provider
- Verify imports work
- Test with mock credentials

### Phase 5: Documentation
- Create PROVIDER_TOOLS_GUIDE.md
- Document each tool's purpose, inputs, outputs
