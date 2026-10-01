# ZOZI Platform — Technology Stack (Canonical)

> **Purpose.** The single canonical reference for every technology used in the ZOZI
> platform. Read alongside `ARCHITECTURE_STACK.md` (structure, modules, domains, laws).
>
> **Columns**
> - **Scope** — where the technology runs (`All`, `Prod`, `Dev`, `CI`, `Docker`).
> - **Use it for** — the concrete job it does in the platform.
> - **Reason for selection** — why this tech was chosen over alternatives.
> - **Use recommendation** — when a feature should reach for this technology.
>
> **Rule of use.** Pick the technology that matches your feature's demand. If a
> technology is not listed here, it is not approved. New entries require an
> ARCHITECTURE_STACK.md law update in the same PR.

---

## 1 · Backend — Runtime & Framework

| Technology | Version | Scope | Use it for | Reason for selection | Use recommendation |
|---|---|---|---|---|---|
| Python | 3.13.x | All | Backend runtime for all domain services, jobs, and Celery workers. | Mature async ecosystem; best-supported combination with Celery, asyncpg, and the FastAPI toolchain. | Always. Pin to the 3.13 line; do not drift without re-auditing Celery, asyncpg, and FastAPI. |
| FastAPI | 0.141.x | All | Web framework for all HTTP endpoints; automatic OpenAPI; Pydantic request validation. | Async-first, type-safe, dependency injection, auto-generated docs. | Always — every HTTP endpoint lives here. |
| Starlette | >=1.6.0,<1.7.0 | All | ASGI framework; routing, middleware, WebSocket protocol (FastAPI is built on it). | Required by FastAPI; provides routing, middleware, and WebSocket primitives. | Always — installed with FastAPI. Pin the range to avoid the build-from-source bug in Debian #1132860. |
| Uvicorn | 0.35.0+ | All | ASGI server handling HTTP/1.1 and WebSocket upgrades. | Production-grade; uses uvloop; streaming and long-lived connections. | Always — the sole ASGI server. HTTP/2 terminates at Cloudflare. |
| uvloop | 0.21.0 | All | High-performance asyncio event loop used by Uvicorn. | 2–4× throughput vs stdlib asyncio for network I/O. | Always when running Uvicorn — automatic via Uvicorn's default. |
| httptools | 0.7.0 | All | C-based HTTP parser used by Uvicorn. | Faster than pure-Python parser; lower latency under load. | Always — pulled in by Uvicorn production extra. |
| Gunicorn | 26.0.0 | Prod | Production process manager spawning Uvicorn workers. | Graceful restarts, pre-fork model, signal handling. | Use in production with `--worker-class uvicorn_worker.UvicornWorker`. Never the default sync worker class. |
| anyio | 4.15.1 | All | Async compatibility layer (asyncio/trio abstraction). | Required by FastAPI/Starlette; explicit for visibility. | Always — transitive dependency made explicit. |
| Pydantic | 2.13.4 | All | Runtime validation for request/response models and domain schemas. | Type-hint-driven validation; JSON Schema for OpenAPI. | Always — every request body and response model. |
| pydantic-settings | 2.9.1+ | All | Typed environment variable loading (`.env`, system env). | Avoids the `os.getenv("false")` truthiness bug; validation at startup. | Always for `config.py`. Never use raw `os.getenv()` in production code. |
| python-multipart | 0.0.32 | All | Multipart form parsing for file uploads and form submissions. | Required by FastAPI's `Form` and `File` parameters. | Use when a route accepts `multipart/form-data` (file upload, form submission). |
| email-validator | 2.3.0 | All | RFC 5322 email format validation. | Deliverability checking; used before any send. | Use in schemas and providers/comms before email dispatch. |

---

## 2 · Backend — Database & Migrations

| Technology | Version | Scope | Use it for | Reason for selection | Use recommendation |
|---|---|---|---|---|---|
| Neon PostgreSQL | 18 | Staging/Prod | Primary OLTP database; 15 domain schemas; RLS for multi-tenant isolation. | Serverless, branch-per-PR, PostgreSQL 18 features, no self-hosted DB ops. | Always in staging/production — the only primary database there. Connect via connection string. |
| PostgreSQL (local) | 16 | Dev | Primary OLTP database for local development; 15 domain schemas; RLS for multi-tenant isolation. | Faster inner loop than cloud DB; offline-capable; no egress/cost; disposable `dropdb/createdb` cycle. | Always in local development. Run via Docker Compose (`postgres:16-alpine`). Never point dev at Neon. |
| asyncpg | 0.31.0 | All | Native async PostgreSQL driver. | Lowest latency vs threaded drivers; direct asyncio integration. | Always. `psycopg`/`psycopg2` are forbidden in production code. |
| SQLAlchemy | 2.0.52 | All | Async ORM; single source of truth for data access. | Async session, declarative mapping, `async with session.begin()`. | Always — all domain models and queries. Never use SQLAlchemy's sync engine in application code. |
| Alembic | 1.19.1+ | All | Schema migrations (linear history) across 15 domain schemas. | Works with SQLAlchemy MetaData; autogenerate; single migration source. | Always. Must use a direct (non-pooled) connection string. In dev, use the local Postgres DSN. Never auto-migrate on web replica boot. |
| PostgreSQL full-text + pg_trgm | PG 18 built-in | Prod | Full-text (`tsvector`) + fuzzy (`pg_trgm`) catalog search. | Keeps search inside Neon; no extra cluster. | Use for catalog search, autocomplete, and fuzzy product matching. |
| pgvector | PG 18 extension | Prod | Vector similarity on embeddings for semantic search. | Optional; enable only when vector search is needed. | Use only when the feature requires semantic similarity (embedding-based search). |
| OpenSearch | 3.0.0 | Prod | External search cluster (catalog size > PostgreSQL capability). | Only when Postgres full-text cannot handle scale or complexity. | Do NOT deploy unless scale demands it. Not part of baseline. |
| providers/async_workers | — | All | Process-pool executors for CPU-bound work (image processing, AI inference). | Keeps the event loop responsive. | Use inside a domain service whenever the work is CPU-bound. Never call blocking CPU work directly in async code. |

---

## 3 · Backend — Cache, Sessions, Jobs & Scheduling

| Technology | Version | Scope | Use it for | Reason for selection | Use recommendation |
|---|---|---|---|---|---|
| Valkey | 9.0.6+ | All | Sessions, catalog cache, rate-limit counters, WebSocket fan-out (Pub/Sub), event bus (Streams), Celery broker. | Ephemeral store; single service for all real-time needs; no Redis license concerns. | Always for sessions, cache, rate limiting, Celery broker, and cross-domain event bus (Streams). Never store permanent data. |
| valkey (Python client) | 6.1.1 | All | Async Python client for Valkey. | Coroutine-based; seamless with asyncio; supports Streams/Pub/Sub/Lua. | Always — the only Valkey client. |
| Celery | 5.5+ | All | Distributed task queue for background processing. | Retries, routing, result backends; consumes from Valkey. | Use for CPU-bound, long-running, or async work that must not block request handlers. |
| Celery Beat | 5.5+ | All | Periodic (cron-like) task scheduling. | Runs finance, logistics, promotions, governance, analytics jobs. | Use for scheduled jobs. Backed by Valkey — NEVER SQLite. |

---

## 4 · Backend — Storage & Media

| Technology | Version | Scope | Use it for | Reason for selection | Use recommendation |
|---|---|---|---|---|---|
| Cloudflare R2 | — | Prod | Object storage for media blobs, audit archives, AI models. | Zero egress fees; S3-compatible; Standard + Infrequent Access. | Always for production media. Use presigned URLs so files never pass through the app. Alternative providers are forbidden. |
| providers/storage/r2.py | — | All | Provider wrapper for R2 operations (presigned PUT/GET, lifecycle). | Isolates S3 SDK from domain logic. | Use inside any service that reads/writes media or archives. |
| aiofiles | 25.1.0 | All | Async file I/O for non-blocking reads/writes. | Required for async context; used by storage and image providers. | Use when a feature performs file I/O inside async code. |
| Pillow | 12.2.0 | All | Image resize, crop, format conversion (JPEG→WebP), EXIF strip. | Standard Python imaging; reliable, well-known. | Use for any product/user image processing. Heavy processing goes through providers/async_workers. |
| puremagic | 2.2.0 | All | MIME type detection from magic bytes. | Pure Python, no libmagic CVE surface; replacement for python-magic. | Use to validate uploaded files before processing. `python-magic` is forbidden. |
| python-slugify | 8.0.4 | All | URL-friendly slugs for products and content. | Unicode-aware; predictable. | Use when generating a slug for a public URL. |
| rembg | 2.0.69 | All | AI background removal for product photography (transparent PNG). | ONNX-based; CPU-friendly. | Use when a feature requires product image background removal. Always via async_workers. |
| opencv-python | 5.0.0 | All | Computer vision: barcode detection, OCR preprocessing, image similarity, parcel verification. | CPU-optimized, mature ecosystem. | Use when a feature does image analysis beyond basic Pillow operations. |
| onnxruntime | 1.23.2 | All | Runtime for ONNX ML models (chatbot, search, image similarity, sentiment). | CPU-first; optional GPU; standard inference engine. | Use inside providers/ai for any model inference. Never block the event loop — run via async_workers. |
| fastembed | 0.4.0+ | All | Lightweight CPU-first embedding generation for search and semantic features. | ONNX models; no HuggingFace runtime dependency. | Use when a feature needs text embeddings. Model is served from R2, not from HuggingFace. |

---

## 5 · Backend — Authentication, Crypto & Rate Limiting

| Technology | Version | Scope | Use it for | Reason for selection | Use recommendation |
|---|---|---|---|---|---|
| PyJWT | 2.13.0+ | All | JWT sign/verify (HS256); jti blacklist cached in Valkey. | OWASP-recommended; maintained; replaces unmaintained python-jose. | Always. Verify the `type` claim on every decode. `python-jose` is forbidden. |
| bcrypt | 5.0.0 | All | Password hashing with 72-byte limit enforcement. | Adaptive cost; widely audited. | Always for passwords. Reject passwords > 72 bytes; never truncate. |
| pyotp | 2.10.0 | All | TOTP generation for 2FA on admin and employee accounts. | Compatible with Google Authenticator and Authy. | Use for admin/employee MFA. Store the TOTP secret encrypted (AES-256-GCM), never bcrypt-hashed. |
| cryptography | 50.0.1 | All | AES-256-GCM envelope encryption for sensitive DB fields (PII, financial, TOTP secrets). | Industry-standard; no external KMS required. | Use via `infrastructure/security/field_encryption.py` with `FIELD_ENCRYPTION_KEY` from Coolify env vars. Vault Transit and AWS KMS are not used. |
| fastapi-limiter-valkey | latest stable | All | Valkey-native rate limiting via FastAPI dependency injection for supplemental per-route limits. | No in-memory fallback; consistent across workers. | Use for route-specific decorators only. Global enforcement is handled by the canonical custom `RateLimitMiddleware` in `backend/middleware/rate_limit_middleware.py`. Fails closed if Valkey is down. |
| pybreaker | 1.4.1 | All | Circuit breaker for external service calls. | Prevents cascade failures when a provider is down. | Wrap every external provider call (payments, SMS, geocoding) in a circuit breaker. |

---

## 6 · Backend — HTTP Clients & External APIs

| Technology | Version | Scope | Use it for | Reason for selection | Use recommendation |
|---|---|---|---|---|---|
| httpx | 0.28.1 | All | Async HTTP client for provider calls (Stripe, PayPal, SMS, geocoding) and FastAPI tests. | Both sync and async; connection pooling; retries; `TestClient` compatible. | Always. Single canonical HTTP client. `requests` is forbidden. |
| stripe (SDK) | 15.5.1 | All | Stripe Python SDK for payment processing. | Official SDK; matches Stripe API. | Use inside `providers/payments/stripe_adapter.py` only. Routing logic stays in `domains/finance`. |
| PayPal | direct REST via httpx | All | PayPal payments via direct REST. | No official maintained Python SDK; REST is stable and auditable. | Use inside `providers/payments/paypal_adapter.py`. `paypal-payments-sdk` is forbidden. |
| Tap / PayTabs / Thawani | direct REST via httpx | All | Regional GCC/MENA payment gateways (config-driven additions). | Config-driven design; no dependency on community SDKs. | Add via `providers/payments/` when a country actually requires the gateway. Do not pre-install SDKs. |
| ollama | 0.6.2+ | All | Local AI runtime (chatbot, search, finance_ai) — free, self-hosted. | No cloud API fees; local inference. | Use when a feature requires AI inference and local hosting is acceptable. |
| feedparser | 6.0.12 | All | RSS/Atom feed parsing for regulatory monitoring and news. | Handles encodings; robust. | Use for governance/audit regulatory monitoring features. |
| phonenumbers | 9.0.35 | All | Phone parsing, validation, E.164 formatting. | Accurate carrier/location data; standard for SMS delivery. | Use for user phone verification and any SMS-related feature. |

---

## 7 · Backend — Communication Providers

| Technology | Version | Scope | Use it for | Reason for selection | Use recommendation |
|---|---|---|---|---|---|
| providers/comms/email.py | — | All | Async SMTP email sending (transactional). | Async, provider-agnostic; never blocks the request. | Always send email via Celery task, never in a request handler. |
| providers/comms/sms.py | — | All | Self-hosted SMS sending. | Removes external dependency; cost control. | Use for OTP delivery and transactional SMS. Async only. |
| providers/comms/whatsapp_selfhosted.py | — | All | Self-hosted WhatsApp sending. | Cost-effective; no Twilio dependency. | Use for order updates and notifications where WhatsApp is the preferred channel. |

---

## 8 · Backend — Internationalization, Money & Documents

| Technology | Version | Scope | Use it for | Reason for selection | Use recommendation |
|---|---|---|---|---|---|
| py-moneyed | 3.0+ | All | Money/Currency value objects and locale-aware currency formatting. | Lightweight; BSD; avoids babel's CLDR payload. | Use in every domain service that handles monetary values. Never use `float` for money. |
| zoneinfo + tzdata | 2025b | All | Timezone handling per PEP 615. | Stdlib; no `pytz`; `tzlocal` redundant on 3.9+. | Use `zoneinfo.ZoneInfo` everywhere. `pytz`/`tzlocal` are forbidden. |
| python-docx | 1.2.0 | All | Word document generation (reports, invoices). | Standard `.docx` writer. | Use when a feature generates downloadable Word documents. |
| openpyxl | 3.1.5 | All | Excel `.xlsx` read/write for exports and reports. | Standard Excel library. | Use when a feature generates or consumes spreadsheets. |

---

## 9 · Backend — Observability & Logging

| Technology | Version | Scope | Use it for | Reason for selection | Use recommendation |
|---|---|---|---|---|---|
| structlog | 26.1.0 | All | Structured JSON logging with context (`user_id`, `request_id`, `domain`, `action`). | Contextual logging; JSON-friendly; easy to filter. | Always. Never use `print()`. |
| sentry-sdk[fastapi] | 2.68.1 | Prod | Exception reporting wire format; sends to self-hosted GlitchTip. | Sentry-API-compatible; no SaaS cost. | Always in production. DSN points to GlitchTip. Fallback to structlog if GlitchTip is unreachable. |
| GlitchTip | latest stable | Prod | Self-hosted error tracker (Sentry-API compatible). | Zero SaaS cost; owns the error data. | Use as the destination for backend and frontend error reports. |
| prometheus-fastapi-instrumentator | 8.1.0+ | All | Automatic Prometheus instrumentation; exposes `/metrics`. | One-line integration with FastAPI. | Always mount in production. Do NOT install `prometheus-client` standalone. |
| Prometheus Server | 3.0.0+ | Prod | Metrics scraping from `/metrics` endpoints. | SLO monitoring; alerting rules. | Optional in v1; enable when SLO dashboards are needed. |
| Grafana | 13.x+ | Prod | Dashboards for latency, error rate, throughput (p50/p95/p99). | Standard visualization for Prometheus. | Optional in v1; enable when dashboards are required. |
| Loki | 3.7.x+ | Prod | Log aggregation (30-day hot storage; queryable via Grafana). | Lightweight vs ELK; fits the VPS budget. | Optional in v1. Prefer Coolify container logs first; add Loki when log volume requires it. |
| OpenTelemetry | 1.44.0 | All | Distributed tracing for cross-service requests. | Industry standard; selective instrumentation possible. | Optional. Enable only when cross-service tracing is required. Adds 8–12% CPU overhead. |

---

## 10 · Backend — Testing

| Technology | Version | Scope | Use it for | Reason for selection | Use recommendation |
|---|---|---|---|---|---|
| pytest | 9.1.1 | All | Python test framework (unit, integration, architecture). | Standard; rich plugin ecosystem. | Always — all backend tests. |
| pytest-asyncio | 1.4.0 | All | Async test support for FastAPI endpoints and SQLAlchemy. | Enables `async def test_` functions. | Always for any async code under test. |
| pytest-xdist | 3.6.1+ | All | Parallel test execution across CPUs. | Reduces CI time. | Use in CI with `-n auto`. Not needed for local runs. |
| pytest-cov | 6.0.0+ | All | Coverage reporting for pytest. | Required for CI coverage gates. | Use in CI. |
| respx | 0.23.1+ | All | HTTP mocking for async tests (httpx). | Mock provider calls without real network access. | Use in any test that mocks an external provider. |
| factory-boy | 3.3.3 | All | Test fixture factories. | Repeatable test data; less boilerplate. | Use for any non-trivial test fixture setup. |
| websockets | 16.1.1+ | All | WebSocket client for integration tests. | Test real-time endpoints. | Use only in tests. Not a production dependency. |
| testcontainers | 4.15.0+ | All | Docker-based test containers (Postgres, Valkey). | Real services for integration tests. | Use when a test needs a real Postgres or Valkey. Requires Docker-in-Docker on CI. |

---

## 11 · Backend — Code Quality & Security Scanning

| Technology | Version | Scope | Use it for | Reason for selection | Use recommendation |
|---|---|---|---|---|---|
| ruff | 0.16.6+ | All | Fast Python linter (replaces flake8). | Rust-based; blocks CI on violations. | Always in pre-commit and CI. |
| mypy | 1.14.1+ | All | Static type checking. | Catches type errors before runtime. | Always in CI. IDE integration recommended. |
| import-linter | 2.14+ | All | Enforces architectural import rules (Law 1, cross-domain bans). | Blocks CI on layer violations. | Always in CI. Contracts live in `tests/architecture/`. |
| pre-commit | 4.2.0+ | All | Git hook framework (ruff, mypy, import-linter, architecture tests). | Fast local gate before CI. | Always — install locally, run on every commit. |
| gitleaks | 8.21.2+ | CI | Secret scanning (API keys, tokens, passwords). | Prevents committing secrets. | Always in CI. Blocks on any finding. |
| pip-audit | 2.10.1+ | CI | Python dependency CVE scanner against `uv.lock`. | Complements Dependabot with CI enforcement. | Always in CI. Blocks on high/critical CVEs. |
| Dependabot | — | CI | Automated dependency vulnerability alerts + PRs (GitHub). | Integrated with GitHub Advisory Database. | Always enabled on GitHub. High/critical CVEs block deployment. |
| Trivy | 0.74.0+ | CI | Container, filesystem, IaC, git vulnerability scan. | Comprehensive; single tool for multiple surfaces. | Always in CI. Blocks on critical findings. |
| cosign | 2.6.3+ | CI | Container image signing (Sigstore). | Image integrity and provenance. | Use when external image consumers or compliance requires it. |
| Syft / CycloneDX | 1.17.0+ | CI | Software Bill of Materials generation. | License and supply chain auditing. | Use for every release when external consumers exist. |

---

## 12 · Frontend — Framework, Build & Language

| Technology | Version | Scope | Use it for | Reason for selection | Use recommendation |
|---|---|---|---|---|---|
| Next.js | 16.3.5 | All | React framework with App Router, RSC, and API proxy. | File-based routing; SSR/ISR; Next API routes as backend proxy. | Always. All web traffic flows through Next.js API routes to the backend. |
| React | 19.2.8 | All | UI library with React Server Components. | RSC stabilized in React 19; server-side data fetching. | Always. Data-fetching = Server Components; interactivity = Client Components. |
| TypeScript | 5.9.3 | All | Type-safe JavaScript; strict mode. | Catches null/undefined at compile time; required for `@zozi/shared`. | Always. Pin to 5.9.3 — TS 7.0 native is not toolchain-compatible yet. |
| pnpm | 10.x+ | All | Workspace-aware package manager for the monorepo. | Fast, disk-efficient, strict dependency isolation. | Always. Do NOT use npm or yarn — they break workspace resolution. |
| Node.js | 22.12.0 | Docker | Runtime for Next.js SSR and API routes (Alpine image). | LTS; Alpine base is small (~50MB). | Always in the frontend Docker image. |
| Multi-stage Docker | — | Docker | Frontend production image build (builder + runner). | Smaller final image; no devDependencies in prod. | Always for production builds. |
| sharp | 0.35.4 | Prod | Image optimization engine for `next/image` in production. | WebP/AVIF conversion; resize; metadata strip. | Always in production — without it, `next/image` optimization is disabled. Note: 0.35.5+ does not exist in npm registry as of 2026-09-15; 0.35.4 has 0 known CVEs per npm audit. |

---

## 13 · Frontend — UI, Styling & Components

| Technology | Version | Scope | Use it for | Reason for selection | Use recommendation |
|---|---|---|---|---|---|
| Tailwind CSS | 4.3.3 | All | Utility-first CSS; design tokens. | CSS-based config (no `tailwind.config.js` in v4); applied via theme. | Always for styling. |
| cva (class-variance-authority) | 0.7.1 | All | Type-safe component variants. | Compile-time validation of variant combinations. | Use when a component exposes multiple visual variants. |
| clsx | 2.1.1 | All | Conditional className utility. | Simple, tiny; handles undefined/null. | Use for conditional class assignment. |
| tailwind-merge | 3.5.0 | All | Smart Tailwind class merging. | Resolves conflicting utilities when classes are composed. | Use when component props merge Tailwind classes. |
| lucide-react | 0.563.0 | All | Icon library (web). | Tree-shakeable; consistent with mobile. | Use for all web icons. |
| motion (framer-motion) | 13.2.0+ | All | Gesture-driven animation library. | Spring/tween presets; layout transitions. | Use for interactive animations. Import from `motion/react`. |
| @zxing/library | 0.21.3 | All | Barcode / QR scanning via device camera. | Mature scanning algorithms. | Use for parcel verification and product lookup screens. |
| qrcode | 1.5.4 | All | Client-side QR generation. | Offloads QR generation from the server. | Use for checkout, parcel, and tracking QRs. |
| dompurify | 3.4.0 | All | DOM sanitization (XSS prevention). | Essential for user-generated content. | Use whenever rendering user HTML (reviews, comments). |
| chart.js + react-chartjs-2 | 4.5.1 / 5.3.1 | All | Data visualization for admin dashboards. | Responsive charts; line/bar/pie/radar. | Use for admin analytics dashboards. |
| leaflet + react-leaflet | 1.9.4 / 5.0.0 | All | Interactive maps (product location, tracking, delivery). | CDN tiles; no bundled map data. | Use for tracking and delivery maps. |
| jspdf | 4.2.1 | All | Client-side PDF generation (invoices, receipts, reports). | Saves server bandwidth. | Use for downloadable documents generated on the client. |
| jose | 6.2.10 | All | JWT parsing in the browser. | Decodes token payload for permissions; never signs. | Use only to read token payload. Signing always happens server-side. |

---

## 14 · Frontend — State, Forms & Data

| Technology | Version | Scope | Use it for | Reason for selection | Use recommendation |
|---|---|---|---|---|---|
| Zustand | 5.0.14 | All | Global and client-cache state. | Tiny; hooks-based; middleware for persistence. | Use for client state (cart, UI, cache). Shared with mobile via `@zozi/shared`. |
| React Server Components | React 19 | All | Server-side data fetching. | Native to React 19; reduces JS bundle. | Use Server Components for data fetching. Use Zustand for client cache. |
| React Hook Form | 7.84.0 | All | Performant form state management. | Minimal re-renders; integrates with Zod. | Use for every form. |
| Zod | 4.3.6 | All | Schema validation (forms, API payloads). | Runtime type safety; shared with backend schemas conceptually. | Use for all form and API validation. |
| @hookform/resolvers | 5.2.2 | All | Zod ↔ React Hook Form integration. | Required for Zod 4 support. | Use `zodResolver(schema)` directly in `useForm` — avoid the `<Form>` wrapper for type safety. |
| next-intl | 4.14.2 | All | i18n (translations, locale routing, formatting). | App Router native; integrates with `@zozi/shared`. | Use for all locale routing and translations. Configure locale fallback (`en`) before multi-country launch. |

---

## 15 · Frontend — Payments, Errors & Testing

| Technology | Version | Scope | Use it for | Reason for selection | Use recommendation |
|---|---|---|---|---|---|
| @stripe/react-stripe-js | 6.9.0 | All | Stripe Elements for card form; PCI-compliant. | Card data never touches your server. | Use for all Stripe card forms. |
| @stripe/stripe-js | 5.5.0+ | All | Core Stripe.js loader (peer dependency). | Required by `@stripe/react-stripe-js`. | Always install with the React package. |
| @sentry/nextjs | 9.x+ | Prod | Frontend error tracking (GlitchTip destination via DSN). | Source maps; browser-side exceptions. | Always in production. DSN points to self-hosted GlitchTip. |
| Jest | 29.7.0 | All | Frontend unit test runner. | Standard React stack. | Always. |
| ts-jest | 29.2.5 | All | TypeScript transform for Jest (majors must match Jest). | Type-aware tests. | Always install with matching Jest major. |
| React Testing Library | 16.3.0 | All | Component testing focused on user behavior. | Tests components like users interact. | Always for component tests. |
| jest-axe | 10.0.0 | All | Accessibility testing in unit tests. | Catches WCAG violations early. | Include in component test suites. |
| Playwright | 1.62.1+ | All | Cross-browser E2E testing. | Real user flows across browsers. | Use for every critical path. |
| Detox | 20.0.0+ | All | Mobile E2E testing. | Real native device flows. | Use for all mobile critical paths. |
| ESLint 10 + typescript-eslint | 10 / 8.62.0 | All | Linting (import order, unused vars, type issues). | Blocks CI on errors. | Always. Node.js ≥ 20.19.0 required. |
| Prettier | 3.3.3 | All | Code formatting. | Consistent style across the monorepo. | Always. Run on save + pre-commit. |

---

## 16 · Mobile

| Technology | Version | Scope | Use it for | Reason for selection | Use recommendation |
|---|---|---|---|---|---|
| Expo SDK | 57.0.20+ | Mobile | Managed React Native workflow. | OTA updates, EAS build, mature ecosystem. | Use when a native mobile app is required. Shares types and API client with web via `@zozi/shared`. |
| React Native | 0.86.3 | Mobile | Native app runtime. | Same JS runtime as web; native modules for camera/storage/notifications. | Always with Expo. |
| Expo Router | 57.0.19 | Mobile | File-based routing with deep linking. | Mirrors Next.js routing; native stack/tab navigators. | Always. Pinned to the Expo SDK version. |
| expo-updates | — | Mobile | OTA JS bundle updates. | Hotfixes without app store review. | Always. |
| expo-secure-storage | 14.2.3 | Mobile | Encrypted key-value storage (Keychain/Keystore). | Store tokens and secrets safely. | Always for tokens. Never store secrets in AsyncStorage. |
| AsyncStorage | 2.x | Mobile | Non-sensitive key-value storage. | Preferences, theme, cached responses. | Use only for non-sensitive data. |
| lucide-react-native | 0.563.0 | Mobile | Native icon library (parity with web). | Consistent icon set. | Always. |
| react-native-maps | 1.29.0 | Mobile | Native maps (iOS MapKit / Google Maps). | Native performance; web counterpart is Leaflet. | Use for tracking and delivery screens. |
| EAS CLI | 22.x | Mobile | Build/submit/update from CI. | Expo-managed pipeline. | Install globally, never as project dep. |

---

## 17 · Shared (Cross-Platform TypeScript)

| Technology | Version | Scope | Use it for | Reason for selection | Use recommendation |
|---|---|---|---|---|---|
| @zozi/shared | — | All | Cross-platform types, API client, money/i18n helpers, permissions. | Single source of truth for both web and mobile. | Always — imported by both apps. Never imports from `web_app` or `mobile_app`. |
| api-core.ts | — | All | Base HTTP fetch wrapper (auth, errors, retry, cache). | Same client on web and mobile. | Use for all API calls from both platforms. |
| money.ts | — | All | Currency formatting via `Intl.NumberFormat`. | Consistent monetary display across platforms. | Use everywhere money is displayed. |
| permissions.ts | — | All | Generated from backend `/rbac/catalog`. | UI gating and backend gating share one source. | Regenerate on every RBAC change. Never edit manually. |

---

## 18 · Infrastructure — Hosting & Deployment

| Technology | Version | Scope | Use it for | Reason for selection | Use recommendation |
|---|---|---|---|---|---|
| Hostinger VPS | KVM 8 (primary), KVM 4 (fallback) | Prod | Compute for FastAPI, Celery, Beat, Valkey, GlitchTip. | Flat VPS cost; no per-service SaaS pricing. | Start on KVM 4 when AI and full observability are deferred; move to KVM 8 for growth headroom. |
| Coolify | latest stable | Prod | Self-hosted PaaS: deploys containers, manages env vars, TLS, rolling restarts. | Zero-cost; auto-deploy from GitHub; Traefik reverse proxy. | Always — the deployment layer on the VPS. |
| Cloudflare Pages | — | Prod | Frontend hosting (Next.js SSR/ISR, global CDN, unlimited bandwidth). | Free-tier; consolidates vendors (R2/CDN/WAF already Cloudflare). | Always for the web app. |
| Cloudflare Tunnel | — | Prod | Ingress from Cloudflare edge → Traefik on the VPS. | No open 443 on origin. | Always. |
| Cloudflare DNS | — | Prod | DNS resolution (proxied). | Integrated with Cloudflare WAF and Tunnel. | Always. |
| Cloudflare CDN | — | Prod | Static asset and image caching. | 40–60% bandwidth reduction; DDoS protection. | Always. |
| Cloudflare WAF | — | Prod | WAF + DDoS protection. | Blocks SQLi, XSS, and volumetric attacks. | Always. |
| Docker Compose | 2.40.0+ | Dev | Local service orchestration (PostgreSQL 16, Valkey, backend, frontend, Celery, Beat). | Mirrors production with local Postgres instead of Neon. | Use for local dev. Includes a local Postgres 16 container. |
| Multi-stage Dockerfiles | — | Docker | Backend and frontend production images. | Smaller images; better security posture. | Always for production builds. |

---

## 19 · Infrastructure — CI, IaC & Tooling

| Technology | Version | Scope | Use it for | Reason for selection | Use recommendation |
|---|---|---|---|---|---|
| GitHub Actions | Node.js 24 runtime | CI | CI, schema drift, docs drift, e2e, import lint. | Native to the repo; runs on Ubuntu 24.04. | Always. Workflows: `ci.yml`, `schema-drift.yml`, `docs-drift.yml`, `e2e.yml`, `import-lint.yml`. |
| Terraform CLI | 1.15.x+ | Prod | Multi-environment IaC (VPS, Coolify services, Neon, R2, DNS). | Free, open-source; remote state on R2. | Optional — use when multi-environment IaC is required. Manual + `SETUP.md` is sufficient for a solo VPS. |
| uv | 0.12.12 | All | Python dependency management with lockfile. | Fast; canonical; replaces pip-tools. | Always. Commit `uv.lock`. |
| Neon CLI | 4.14.3+ | Dev/CI | Neon branch management (create/delete, connection strings). | Branch-per-dev and branch-per-PR workflow. | Use in dev and CI. Renamed from `neonctl` — the `neon` binary is canonical. |
| MailHog | 0.2.1+ | Dev | Local SMTP capture for development. | Inspect email content without sending. | Use in dev only. |

---

## 20 · Infrastructure — Secrets & Configuration

| Variable | Secret | Required | Description | Scope | Use it for | Reason for selection | Use recommendation |
|---|---|---|---|---|---|---|---|
| **App / Runtime** |
| `APP_ENV` | No | Dev | Environment profile: `development`, `staging`, `production`. | All | Selects config profile and feature gates. | Required for environment-specific behavior (debug, CORS, DB). | Always set. Never default to production in dev. |
| `RUNTIME_PROFILE` | No | No | Runtime mode: `standard` or `loadtest`. | All | Switches between normal and load-test profiles. | Allows load-test mode without code changes. | Set to `loadtest` only during intentional load tests. |
| `SECRET_KEY` | **YES** | Prod | JWT signing key (HS256). Generate with `secrets.token_hex(32)`. | All | Signs and verifies JWT access/refresh tokens. | OWASP-recommended HS256; replaces unmaintained python-jose. | Generate fresh per environment; rotate on 90-day schedule. Never commit. |
| **Database** |
| `DATABASE_URL` | No | Prod | Neon PostgreSQL connection string (direct, non-pooled for Alembic). | All | Primary DB connection for all domain services. | Neon branch-per-env; non-pooled for migrations. | Always. Use direct DSN for Alembic; pooled for app runtime. |
| `DATABASE_REPLICA_URL` | No | No | Optional read-replica connection string. | Prod | Read-heavy queries via `get_read_db()`. | Separates read load from primary; required by Law 48. | Set when read replicas are provisioned; otherwise leave empty. |
| `DB_POOL_SIZE` | No | No | SQLAlchemy pool size (default 50). | All | Controls per-worker DB connection pool. | Must be ≥ 10 per Law 47; total capacity = workers × (pool_size + max_overflow). | Tune to match Neon Pooler limits and worker count. |
| `DB_MAX_OVERFLOW` | No | No | SQLAlchemy pool overflow (default 100). | All | Excess connections beyond pool_size. | Allows burst capacity without permanent connections. | Keep ≥ 2× pool_size for burst tolerance. |
| `DB_POOL_RECYCLE` | No | No | Connection recycle seconds (default 1800). | All | Max age of a pooled connection. | Prevents stale connections on Neon serverless. | Do not exceed Neon's 30-min idle timeout. |
| `DB_CONNECT_TIMEOUT` | No | No | Connect timeout seconds (default 30). | All | TCP connection timeout to Neon. | Prevents hung workers on network issues. | 30s is safe; reduce only if cold-start is a problem. |
| `DB_STATEMENT_TIMEOUT` | No | No | Statement timeout ms (default 60000). | All | Per-query timeout enforced at DB level. | Prevents runaway queries from blocking the pool. | Tune per domain; finance queries may need higher limits. |
| **CORS / URLs** |
| `CORS_ORIGINS` | No | Prod | Comma-separated allowed origins (no localhost in production). | All | CORS allowlist for browser requests. | Backend CORS disabled for browsers; Next.js proxy handles CORS in production (Law 40). | Only used in dev; must be empty or correct production origins in prod. |
| `FRONTEND_URL` | No | No | Frontend base URL (Next.js). | All | Generates absolute links, webhook callbacks, email templates. | Next.js runs on Cloudflare Pages; backend must know its public URL. | Set to Cloudflare Pages URL in production. |
| `BACKEND_URL` | No | No | Backend base URL. | All | Generates absolute API links in emails, webhooks. | Required for external callers (payment webhooks, email links). | Set to public API URL (e.g., `https://api.zozi.com`). |
| **Payments** |
| `STRIPE_SECRET_KEY` | **YES** | Prod | Stripe secret API key. | Prod | Passed to Stripe SDK for server-side charges. | Only stored server-side; never exposed to browser. | Store in Coolify; use Stripe Elements for card input. |
| `STRIPE_PUBLISHABLE_KEY` | No | Prod | Stripe publishable key. | Prod | Passed to Stripe.js in browser. | Required for Stripe Elements in checkout. | Exposed to browser by design; safe to be public. |
| `STRIPE_WEBHOOK_SECRET` | **YES** | Prod | Stripe webhook signing secret. | Prod | Verifies webhook authenticity from Stripe. | Prevents webhook spoofing. | Rotate if leaked; stored in Coolify. |
| `STRIPE_API_VERSION` | No | No | Stripe API version override. | All | Pins Stripe API version for compatibility. | Prevents breaking changes from Stripe API upgrades. | Set to tested version; update with migration plan. |
| `STRIPE_CONNECT_AUTO_CREATE_ACCOUNTS` | No | No | Auto-create Stripe Connect accounts (default false). | All | Supplier onboarding automation. | Reduces manual account creation step. | Enable when supplier self-service onboarding is live. |
| `TAP_SECRET_KEY` | **YES** | Prod | Tap (PayTabs) secret API key. | Prod | Authenticates Tap API requests. | Regional GCC/MENA gateway; direct REST via httpx. | Store in Coolify; rotate on compromise. |
| `TAP_WEBHOOK_SECRET` | **YES** | No | Tap webhook signing secret. | All | Verifies Tap webhook authenticity. | Prevents webhook spoofing for Tap gateway. | Set when Tap webhooks are configured. |
| `TAP_WEBHOOK_URL` | No | No | Tap webhook callback URL. | All | Public URL Tap calls for payment events. | Must be reachable from Tap servers. | Use `/api/v1/webhooks/payments/tap`. |
| **SMS / WhatsApp** |
| `TWILIO_ACCOUNT_SID` | No | No | Twilio account SID (self-hosted SMS/WhatsApp). | All | Identifies Twilio account for SMS/WhatsApp sends. | Self-hosted SMS/WhatsApp via Twilio; no Twilio dependency if not configured. | Set when Twilio is the active SMS/WhatsApp provider. |
| `TWILIO_AUTH_TOKEN` | **YES** | No | Twilio auth token. | All | Authenticates Twilio API calls. | Required for any Twilio send. | Store in Coolify; rotate if leaked. |
| **Email** |
| `SMTP_HOST` | No | No | SMTP server hostname. | All | Connects to SMTP relay for transactional email. | Required for email sending; MailHog in dev. | Set to production SMTP host in Coolify. |
| `SMTP_PORT` | No | No | SMTP port (default 587). | All | TLS port for SMTP connection. | Standard submission port; 465 for SSL. | 587 with STARTTLS is the default recommendation. |
| `SMTP_USER` | No | No | SMTP auth username. | All | SMTP authentication identity. | Required for authenticated SMTP relay. | Set in Coolify alongside SMTP_PASSWORD. |
| `SMTP_PASSWORD` | **YES** | No | SMTP auth password. | All | SMTP authentication credential. | Required for authenticated SMTP relay. | Store in Coolify; never commit. |
| `EMAIL_FROM` | No | No | Sender address (default `noreply@zozi.com`). | All | From address for all transactional emails. | Must match authenticated SMTP identity. | Use a verified domain in production. |
| `RESEND_API_KEY` | **YES** | No | Resend API key (alternative SMTP provider). | All | Authenticates Resend HTTP API. | Alternative to SMTP; simpler for transactional email. | Set when Resend is the active email provider. |
| `RESEND_WEBHOOK_SECRET` | **YES** | No | Resend webhook signing secret. | All | Verifies Resend webhook authenticity. | Tracks delivery, bounces, complaints. | Set when Resend webhooks are configured. |
| **OAuth Social** |
| `GOOGLE_CLIENT_ID` | No | No | Google OAuth client ID. | All | Identifies app in Google OAuth flow. | Social login via Google. | Register in Google Cloud Console; set in Coolify. |
| `GOOGLE_CLIENT_SECRET` | **YES** | No | Google OAuth client secret. | All | Authenticates app in Google OAuth token exchange. | Required for OAuth token exchange. | Store in Coolify; rotate if leaked. |
| `FACEBOOK_CLIENT_ID` | No | No | Facebook OAuth client ID. | All | Identifies app in Facebook OAuth flow. | Social login via Facebook. | Register in Meta Developer Console. |
| `FACEBOOK_CLIENT_SECRET` | **YES** | No | Facebook OAuth client secret. | All | Authenticates app in Facebook OAuth token exchange. | Required for OAuth token exchange. | Store in Coolify; rotate if leaked. |
| **Celery / Valkey** |
| `CELERY_BROKER_URL` | No | Prod | Valkey broker URL (default `valkey://localhost:6379/1`). | All | Message broker for Celery task queue. | Valkey replaces Redis as the canonical broker (Law 102a). | Must be a Valkey URL; SQLite is forbidden for Celery Beat. |
| `CELERY_RESULT_BACKEND` | No | No | Valkey result backend URL. | All | Stores Celery task results and state. | Required for task status tracking and result retrieval. | Use Valkey; separate DB index from broker for isolation. |
| `CELERY_TASK_ALWAYS_EAGER` | No | No | Run tasks synchronously (default false). | Dev | Runs Celery tasks in-process for testing. | Eliminates broker dependency in unit tests. | Set `true` only in test environments; never in production. |
| `ML_WORKERS` | No | No | ML worker process count (default 2). | All | Number of subprocess workers for CPU-bound ML inference. | Isolates ONNX/ollama CPU work from event loop. | Match to available CPU cores; monitor memory. |
| **Storage / R2** |
| `STORAGE_BACKEND` | No | No | Storage backend: `local` or `r2` (production must be `r2`). | All | Selects object storage implementation. | R2 is mandatory for production (Law 120a); local for dev. | Always `r2` in production. Local is dev-only. |
| `S3_BUCKET` | No | Prod | R2 bucket name. | Prod | Cloudflare R2 bucket for media blobs and audit archives. | Canonical R2 bucket identifier; S3_ prefix is a deprecated alias. | Use R2_BUCKET in new code; S3_BUCKET is backward-compat alias. |
| `S3_REGION` | No | No | R2 region (default `auto`). | All | R2 bucket region for S3-compatible API calls. | R2 uses `auto`; S3_ prefix is deprecated alias. | Use R2_REGION in new code. |
| `S3_ENDPOINT_URL` | No | No | R2-compatible S3 endpoint URL. | All | S3-compatible endpoint for boto3/r2_client. | Required for R2 S3-compatible API; S3_ prefix is deprecated alias. | Use R2_ENDPOINT_URL in new code. |
| `S3_CDN_BASE` | No | No | CDN base URL for presigned download links. | All | Base URL prepended to presigned download paths. | Cloudflare CDN front for R2; S3_ prefix is deprecated alias. | Use R2_CDN_BASE in new code. |
| `S3_ACCESS_KEY_ID` | **YES** | Prod | R2 access key ID. | Prod | Authenticates S3-compatible API requests to R2. | S3_ prefix is deprecated alias for R2_ACCESS_KEY_ID. | Use R2_ACCESS_KEY_ID in new code. |
| `S3_SECRET_ACCESS_KEY` | **YES** | Prod | R2 secret access key. | Prod | Signs S3-compatible API requests to R2. | S3_ prefix is deprecated alias for R2_SECRET_ACCESS_KEY. | Use R2_SECRET_ACCESS_KEY in new code. |
| `S3_PRESIGN_TTL_SECONDS` | No | No | Presigned URL TTL seconds (default 900). | All | How long a presigned upload/download URL is valid. | Balances security (short TTL) against UX (long enough for large uploads). | 900s (15 min) is the default; increase only for large media uploads. |
| `PRESIGNED_UPLOADS_ENABLED` | No | No | Enable presigned upload URLs (default false). | All | Activates presigned PUT URL flow for uploads. | Files never pass through app server; direct client→R2. | Enable in production; disable only for local dev with local storage. |
| **AI / ML Providers** |
| `OPENAI_API_KEY` | **YES** | No | OpenAI API key (if used as provider). | All | Authenticates OpenAI API calls. | OpenAI discontinued as primary provider; kept as optional fallback. | Set only if OpenAI models are actively used as a provider. |
| `HF_API_TOKEN` | **YES** | No | HuggingFace API token (if used). | All | Authenticates HuggingFace Inference API. | HuggingFace discontinued as primary provider; kept as optional fallback. | Set only if HuggingFace models are actively used. |
| `OLLAMA_BASE_URL` | No | No | Ollama server URL (default `http://localhost:11434`). | All | Endpoint for local ONNX/ollama inference. | Self-hosted AI runtime; zero cloud API fees. | Point to production Ollama instance in Coolify; localhost in dev. |
| `OLLAMA_MODEL` | No | No | Default Ollama vision model (default `moondream:latest`). | All | Model tag for vision-capable Ollama inference. | CPU-first vision model for product analysis. | Pull model to production Ollama instance before deploy. |
| `OLLAMA_TEXT_MODEL` | No | No | Default Ollama text model (default `phi3:mini`). | All | Model tag for text-only Ollama inference. | Lightweight text model for chatbot, search, finance AI. | Pull model to production Ollama instance before deploy. |
| `COUNTRY_AI_OLLAMA_MODEL` | No | No | Ollama model for country AI assistant (default `llama3.1`). | All | Model used by the country-specific AI assistant. | Larger, more capable model for country-context AI; separate from generic text model. | Pull llama3.1 to production Ollama instance; tune per country if needed. |
| **Background Removal** |
| `BG_MAX_CONCURRENT` | No | No | Max concurrent background removal jobs (default 2). | All | Semaphore limit for CPU-bound rembg processes. | Prevents OOM when multiple images are processed simultaneously. | Tune to available CPU cores and memory. |
| `BG_MAX_SESSION_CACHE` | No | No | Max cached rembg sessions (default 2). | All | Limits ONNX session reuse pool for background removal. | Sessions are memory-heavy; bounded cache prevents OOM. | Keep at 2 unless memory allows more concurrent sessions. |
| `BG_MAX_IMAGE_DIM` | No | No | Max image dimension px (default 1024). | All | Caps input image size before background removal. | Prevents OOM on very large product photos. | 1024 is a safe default; increase only with more memory. |
| `BG_LITE_MAX_DIM` | No | No | Max dimension for lite model (default 1024). | All | Size cap when using the lightweight rembg model variant. | Lite model trades accuracy for speed; smaller input = faster. | Use 512 for fast previews; 1024 for production quality. |
| `BG_MEMORY_WARN_MB` | No | No | Memory warning threshold MB (default 256). | All | Triggers a warning when rembg session exceeds this RSS. | Alerts ops before OOM kills the worker. | Set below actual container memory limit with headroom. |
| `BG_SKIP_HEAVY_MODELS` | No | No | Skip heavy rembg models by default (default true). | All | Prefers the lite rembg model unless explicitly overridden. | Reduces startup time and memory in dev and low-resource environments. | Keep `true` in dev; set `false` in production for best quality. |
| **Field Encryption** |
| `FIELD_ENCRYPTION_KEY` | **YES** | Prod | AES-256-GCM master key (Coolify env var; never commit). | Prod | Master key for field-level encryption of PII, financial, and TOTP secrets. | AES-256-GCM via `infrastructure/security/field_encryption.py`; no external KMS required. | Generate with `secrets.token_hex(32)`; store only in Coolify; rotate with data migration. |
| **Audit / Security** |
| `AUDIT_CHAIN_KEY` | **YES** | Prod | Audit chain HMAC key (WORM log integrity). | Prod | Signs each audit log entry to detect post-hoc tampering. | WORM audit trail for compliance investigations (Law 96). | Generate fresh per environment; rotation requires re-signing audit history. |
| `TRUSTED_PROXY_IPS` | No | No | Comma-separated trusted proxy IPs for `X-Forwarded-For`. | Prod | Extracts real client IP behind Cloudflare Tunnel and reverse proxy. | Cloudflare Tunnel is the sole ingress; real client IP comes from CF headers. | Set to Cloudflare egress IPs; leave empty in dev. |
| `FRAUD_PROXY_SEED_IPS` | No | No | Seed IPs for fraud proxy-detection heuristics. | All | Baseline IPs for impossible-travel and proxy fraud scoring. | Feeds `FraudDetectionMiddleware` IP-reputation heuristics (Law 6). | Populate with known proxy/VPN datacenter IP ranges. |
| **Country AI** |
| `COUNTRY_AI_ENABLED` | No | No | Enable country AI assistant (default true). | All | Feature gate for the country-specific AI chatbot. | Allows country AI to be toggled per environment without code change. | Set `false` in environments without an Ollama instance. |
| `COUNTRY_AI_OLLAMA_MODEL` | No | No | Ollama model for country AI assistant (default `llama3.1`). | All | Model tag used by the country-context AI assistant. | Larger, more capable model for country-context AI; separate from generic text model. | Pull `llama3.1` to the production Ollama instance before enabling. |
| `COUNTRY_AI_CACHE_TTL_SECONDS` | No | No | Country AI response cache TTL (default 86400). | All | Valkey TTL for cached country AI responses. | Reduces repeated Ollama inference cost for common country queries. | 86400 (24h) default; reduce for more dynamic country data. |
| `COUNTRY_AI_WEB_SEARCH_ENABLED` | No | No | Enable web search in country AI (default true). | All | Allows country AI to augment answers with live web search. | Requires `feedparser` + outbound HTTP; disable in air-gapped environments. | Disable in environments with restricted egress. |
| `COUNTRY_AI_MAX_CONCURRENT_JOBS` | No | No | Max concurrent country AI jobs (default 5). | All | Semaphore limit for concurrent country AI inference jobs. | Prevents Ollama overload during peak multi-country usage. | Tune to Ollama instance CPU/memory capacity. |
| **Observability** |
| `SENTRY_DSN` | No | Prod | GlitchTip DSN for exception tracking. | Prod | Exception reporting wire format; sends to self-hosted GlitchTip. | Sentry-API-compatible; zero SaaS cost. | Always in production; fallback to structlog if GlitchTip is unreachable. |
| **Bank API** |
| `BANK_API_ENABLED` | No | No | Enable bank API integration (default false). | All | Feature gate for bank verification and payout APIs. | Allows bank API to be toggled without code change. | Set `true` only when bank integration is live for the country. |
| `BANK_API_BASE_URL` | No | No | Bank API base URL. | All | Root URL for bank API calls. | Required when BANK_API_ENABLED is true. | Set to bank's production API endpoint in Coolify. |
| `BANK_API_BATCH_PATH` | No | No | Bank API batch endpoint path. | All | Relative path for batch bank operations. | Appended to BANK_API_BASE_URL for batch requests. | Keep in sync with bank's API spec. |
| `BANK_API_AUTH_TOKEN` | **YES** | No | Bank API bearer token. | All | Authenticates requests to the bank API. | Required for all bank API calls when enabled. | Store in Coolify; rotate on bank notification. |
| `BANK_API_SOURCE_ACCOUNT_ID` | No | No | Bank source account identifier. | All | Identifies the platform's primary bank account. | Required for payout initiation and balance queries. | Set to the platform's primary operating account ID. |
| `BANK_API_TIMEOUT_SECONDS` | No | No | Bank API call timeout (default 30). | All | HTTP timeout for bank API requests. | Prevents worker hangs on slow bank responses. | 30s default; reduce if bank SLA is faster. |
| **Geo** |
| `DEFAULT_COUNTRY` | No | No | Default country code (ISO 3166-1 alpha-2; default `US`). | All | Fallback country when detection fails or no session context. | Required for RLS context and localization before user country is known. | Set to primary market country in production. |
| **Seed Data** |
| `SEED_ADMIN_PASSWORD` | **YES** | Dev | Admin seed user password (dev only). | Dev | Seeds initial admin user in development. | Used by seed scripts; must be strong in shared dev environments. | Dev only; never set in production. |
| `SEED_CUSTOMER_PASSWORD` | **YES** | Dev | Customer seed user password (dev only). | Dev | Seeds initial customer user in development. | Used by seed scripts; must be strong in shared dev environments. | Dev only; never set in production. |
| **Frontend (reference — Next.js build-time)** |
| `NEXT_PUBLIC_API_URL` | No | Dev | Backend API URL for Next.js API proxy (default `http://127.0.0.1:8000`). | Dev/Staging | Next.js API proxy target; also used in mobile app config. | Next.js proxies `/api/v1/*` to this URL in dev; mobile uses it directly. | Set to public API URL in production via Coolify; localhost in dev. |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | No | Prod | Stripe publishable key exposed to browser for Elements. | Prod | Client-side Stripe.js key for Elements checkout. | Required for card payment UI in the browser. | Exposed to browser by design; safe to be public. |
| `AUTH_SECRET` | **YES** | All | Next.js server JWT verification secret (must match backend SECRET_KEY in dev). See Security Note. | All | Verifies JWT in Next.js server components and middleware. | Separate from SECRET_KEY to allow independent rotation; duplication risk documented below. | Treat as independent from SECRET_KEY; rotate simultaneously on 90-day schedule. |
| `NEXT_PUBLIC_APP_NAME` | No | Dev | Application name for meta tags and titles (default `ZOZI Marketplace`). | All | Browser tab title, meta tags, and share cards. | Used in Next.js metadata API. | Set per environment if branding differs. |
| `NEXT_PUBLIC_APP_URL` | No | Dev | Public frontend URL for absolute links (default `http://localhost:3000`). | All | Generates absolute frontend URLs in meta tags and redirects. | Required for SEO meta tags and OAuth redirects. | Set to Cloudflare Pages URL in production. |
| `NEXT_PUBLIC_ENABLE_ANALYTICS` | No | No | Enable analytics tracking (default false). | All | Feature gate for frontend analytics instrumentation. | Allows analytics to be toggled without code change. | Enable only when analytics provider is configured. |
| `NEXT_PUBLIC_ENABLE_PWA` | No | No | Enable PWA service worker (default false). | All | Activates PWA service worker for offline support. | Allows PWA installability and offline caching. | Enable after service worker and manifest are tested. |
| **Valkey / Cache** |
| `VALKEY_URL` | No | Prod | Canonical Valkey connection string. | All | Sessions, cache, rate-limit counters, Celery broker, event bus. | Valkey replaces Redis; single service for all real-time needs; no license concerns. | Always. Never use Redis. |
| `REDIS_URL` | No | All | Backward-compat alias for VALKEY_URL. **Deprecated.** | All | Maps to VALKEY_URL via shim in `infrastructure/valkey/client.py`. | Backward compat during Valkey migration. | Migrate all references to VALKEY_URL; REDIS_URL will be removed. |
| **Payments (additional gateways)** |
| `TAP_API_BASE_URL` | No | No | Tap API base URL (default `https://api.tap.company`). | All | Root URL for Tap (PayTabs) direct REST calls. | Config-driven; no SDK dependency; direct REST via httpx. | Set to the correct regional Tap endpoint per country. |
| `PAYPAL_CLIENT_ID` | No | No | PayPal OAuth client ID. | All | Identifies app in PayPal OAuth2 flow. | PayPal uses direct REST (no SDK); client ID for OAuth token. | Set from PayPal Developer Dashboard. |
| `PAYPAL_SECRET` | **YES** | No | PayPal OAuth client secret. | All | Authenticates PayPal OAuth2 token request. | Required for all PayPal API calls. | Store in Coolify; rotate on compromise. |
| `PAYPAL_MODE` | No | No | PayPal environment mode: `sandbox` or `live` (default `sandbox`). | All | Selects PayPal API environment. | Prevents accidental live charges in dev/staging. | Set `live` only in production Coolify environment. |
| `PAYTABS_SERVER_KEY` | **YES** | No | PayTabs server API key. | All | Authenticates PayTabs API requests. | Direct REST via httpx; no SDK dependency. | Store in Coolify; rotate on compromise. |
| `PAYTABS_WEBHOOK_SECRET` | **YES** | No | PayTabs webhook signing secret. | All | Verifies PayTabs webhook authenticity. | Prevents webhook spoofing for PayTabs gateway. | Set when PayTabs webhooks are configured. |
| `PAYTABS_PROFILE_ID` | No | No | PayTabs merchant profile ID. | All | Identifies merchant profile in PayTabs. | Required for PayTabs payment page creation. | Set from PayTabs merchant dashboard. |
| `PAYTABS_API_BASE_URL` | No | No | PayTabs API base URL (default `https://secure.paytabs.com`). | All | Root URL for PayTabs REST API. | Direct REST endpoint; configurable per region. | Override only for regional PayTabs endpoints. |
| `PAYTABS_CALLBACK_URL` | No | No | PayTabs redirect callback URL. | All | URL PayTabs redirects to after payment. | Must be publicly reachable from PayTabs servers. | Use `/api/v1/webhooks/payments/paytabs` or checkout callback route. |
| `THAWANI_SECRET_KEY` | **YES** | No | Thawani secret API key. | All | Authenticates Thawani API requests. | Direct REST via httpx; no SDK dependency. | Store in Coolify; rotate on compromise. |
| `THAWANI_PUBLISHABLE_KEY` | No | No | Thawani publishable key. | All | Public key for Thawani checkout sessions. | Required for Thawani payment page initialization. | Set from Thawani merchant dashboard. |
| `THAWANI_API_BASE_URL` | No | No | Thawani API base URL (default `https://uatcheckout.thawani.om/api/v1`). | All | Root URL for Thawani REST API. | UAT default; production URL is `https://checkout.thawani.om/api/v1`. | Override to production URL when going live. |
| `THAWANI_WEBHOOK_SECRET` | **YES** | No | Thawani webhook signing secret. | All | Verifies Thawani webhook authenticity. | Prevents webhook spoofing for Thawani gateway. | Set when Thawani webhooks are configured. |
| **Object Storage (R2 canonical)** |
| `R2_BUCKET` | No | Prod | Cloudflare R2 bucket name. | Prod | Primary object storage bucket for media blobs and audit archives. | R2 is the only allowed production object storage (Law 120a); zero egress fees. | Always. Create bucket in Cloudflare R2 dashboard. |
| `R2_REGION` | No | No | R2 bucket region (default `auto`). | All | R2 bucket region for S3-compatible API calls. | Cloudflare manages region; `auto` is correct for R2. | Leave as `auto`; R2 does not use explicit region like AWS S3. |
| `R2_ENDPOINT_URL` | No | No | Custom R2/S3-compatible endpoint URL. | All | S3-compatible API endpoint for boto3/r2_client. | Required for programmatic R2 access via S3 protocol. | Use the account-specific endpoint from Cloudflare R2 dashboard. |
| `R2_CDN_BASE` | No | No | CDN base URL for R2 presigned download links. | All | Cloudflare CDN domain prepended to R2 object paths. | Serves media via CDN; reduces R2 egress and latency. | Set to the Cloudflare R2 public domain (e.g., `pub-xxx.r2.dev`). |
| `R2_ACCESS_KEY_ID` | **YES** | Prod | R2 access key ID. | Prod | Authenticates S3-compatible API requests to R2. | Required for presigned URL generation and admin uploads. | Store in Coolify; rotate if leaked. |
| `R2_SECRET_ACCESS_KEY` | **YES** | Prod | R2 secret access key. | Prod | Signs S3-compatible API requests to R2. | Required alongside access key ID for all R2 operations. | Store in Coolify; never commit. |
| `R2_PRESIGN_TTL_SECONDS` | No | No | Presigned URL TTL seconds (default 900). | All | How long a presigned upload/download URL remains valid. | Balances upload UX (time for large files) against security (short exposure). | 900s (15 min) is the default; increase only for large media uploads. |
| `S3_BUCKET` | No | Prod | **Deprecated alias** for `R2_BUCKET`. | Prod | Backward-compat mapping to R2_BUCKET. | Migration from legacy S3 naming; R2 is canonical. | Migrate to R2_BUCKET; S3_BUCKET will be removed in next sprint. |
| `S3_REGION` | No | No | **Deprecated alias** for `R2_REGION`. | All | Backward-compat mapping to R2_REGION. | Legacy naming preserved during R2 migration. | Migrate to R2_REGION. |
| `S3_ENDPOINT_URL` | No | No | **Deprecated alias** for `R2_ENDPOINT_URL`. | All | Backward-compat mapping to R2_ENDPOINT_URL. | Legacy naming preserved during R2 migration. | Migrate to R2_ENDPOINT_URL. |
| `S3_CDN_BASE` | No | No | **Deprecated alias** for `R2_CDN_BASE`. | All | Backward-compat mapping to R2_CDN_BASE. | Legacy naming preserved during R2 migration. | Migrate to R2_CDN_BASE. |
| `S3_ACCESS_KEY_ID` | **YES** | Prod | **Deprecated alias** for `R2_ACCESS_KEY_ID`. | Prod | Backward-compat mapping to R2_ACCESS_KEY_ID. | Legacy naming preserved during R2 migration. | Migrate to R2_ACCESS_KEY_ID. |
| `S3_SECRET_ACCESS_KEY` | **YES** | Prod | **Deprecated alias** for `R2_SECRET_ACCESS_KEY`. | Prod | Backward-compat mapping to R2_SECRET_ACCESS_KEY. | Legacy naming preserved during R2 migration. | Migrate to R2_SECRET_ACCESS_KEY. |
| `S3_PRESIGN_TTL_SECONDS` | No | No | **Deprecated alias** for `R2_PRESIGN_TTL_SECONDS`. | All | Backward-compat mapping to R2_PRESIGN_TTL_SECONDS. | Legacy naming preserved during R2 migration. | Migrate to R2_PRESIGN_TTL_SECONDS. |
| `ENCRYPTION_KEY` | **YES** | Prod | **Deprecated alias** for `FIELD_ENCRYPTION_KEY`. | Prod | Backward-compat mapping resolved in `backend/config.py`. | Legacy naming from before field-encryption refactor. | Migrate to FIELD_ENCRYPTION_KEY; ENCRYPTION_KEY will be removed. |
| **Finance & Scheduling** |
| `VAT_RATE` | No | No | VAT/tax rate (default 0.0). | All | Applied to taxable transactions at checkout. | Country-specific VAT is configured per domain; global default here. | Set per-country in admin; global default is no VAT. |
| `ZOZI_COMMISSION_RATE` | No | No | Platform commission rate (default 0.1). | All | Platform cut taken from each supplier sale. | Waterfall commission matrix; this is the global fallback (Law 110). | Configure per supplier/product type in admin; global is 10%. |
| `PAYOUT_HOLDING_DAYS` | No | No | Days to hold payouts before release (default 7). | All | Holding period before supplier payout is released. | Protects against returns and chargebacks post-delivery. | 7 days is standard; adjust per country regulation. |
| `FINANCE_SCHEDULER_ENABLED` | No | No | Enable finance scheduler jobs (default false). | All | Master switch for all scheduled finance jobs. | Celery Beat tasks for payouts, reconciliation, accruals. | Enable only when finance scheduler is deployed and tested. |
| `FINANCE_SCHEDULER_PROCESS_PAYOUTS` | No | No | Enable automatic payout processing (default false). | All | Enables the payout processing Celery task. | Automates payout sweeps on schedule. | Enable after payout provider is configured and tested. |
| `FINANCE_SCHEDULER_DISPATCH_PROVIDER` | No | No | Payout provider selector. | All | Selects which payment gateway to use for payouts. | Allows per-country or per-supplier payout routing. | Set to the active payout provider slug (e.g., `stripe`, `tap`). |
| `FINANCE_SCHEDULER_DISPATCH_PAYOUTS` | No | No | Enable payout dispatch jobs (default false). | All | Enables the payout dispatch Celery task. | Automates payout dispatch to selected provider. | Enable after payout processing is verified. |
| `FINANCE_SCHEDULER_DISPATCH_DRY_RUN` | No | No | Run payout dispatch in dry-run mode (default true). | All | Simulates payout dispatch without executing real transfers. | Prevents accidental live payouts during initial configuration. | Set `false` only when payout dispatch is verified in staging. |
| `FINANCE_AUTO_RECONCILE_BATCH_LIMIT` | No | No | Max batch size for auto-reconciliation (default 100). | All | Limits rows per reconciliation batch job. | Prevents long-running transactions; keeps batches manageable. | Tune based on DB capacity and reconciliation SLA. |
| **Observability & Flags** |
| `LOG_LEVEL` | No | No | Logging verbosity level. | All | Controls structlog log level (DEBUG, INFO, WARNING, ERROR). | Structured logging per Law 92; level set at startup. | `INFO` in production; `DEBUG` for local debugging only. |
| `LOADTEST_PROFILE_ENABLED` | No | No | Enable load-test profile (default false). | All | Activates RUNTIME_PROFILE=loadtest behavior. | Allows load testing without changing RUNTIME_PROFILE directly. | Enable only during planned load tests. |
| `COOKIE_SECURE` | No | Prod | Set `Secure` flag on cookies (default true). | Prod | Forces cookies to be sent over HTTPS only. | Required for SameSite=None cookies in production. | Keep `true` in production; `false` only in local dev over HTTP. |
| `HSTS_ENABLED` | No | Prod | Enable HSTS header (default true). | Prod | Instructs browsers to enforce HTTPS for the domain. | Prevents SSL-stripping attacks (Law 36). | Enable in production after verifying HTTPS is stable. |
| `SECURITY_HEADERS_ENABLED` | No | All | Enable security response headers (default true). | All | Emits CSP, X-Frame-Options, Referrer-Policy headers. | Defense-in-depth against XSS and clickjacking (Law 36). | Always enable; tune CSP to match actual asset origins. |
| `RATE_LIMIT_ENABLED` | No | All | Enable rate limiting globally (default true). | All | Activates FastAPI rate-limit dependency on public endpoints. | Prevents brute-force and DoS (Law 37). | Keep `true`; disable only for specific load-test scenarios. |
| `CUSTOMER_EMAIL_VERIFICATION_MODE` | No | No | Email verification mode for customers (default `auto`). | All | Controls whether customers must verify email before accessing the platform. | Balances onboarding friction against account abuse. | `auto` (verify when suspicious); `strict` for high-risk markets. |
| `READINESS_REQUIRE_REDIS` | No | No | Require Valkey for readiness probe (default false). | All | Makes `/health/ready` fail if Valkey is unreachable. | Useful for staging/prod where Valkey is required. | Set `true` in production; `false` in dev where Valkey may be absent. |
| `READINESS_REQUIRE_EMAIL` | No | No | Require email provider for readiness probe (default false). | All | Makes `/health/ready` fail if email provider is unreachable. | Prevents false healthy status when email is broken. | Set `true` if email delivery is crit