ZOZI Platform Features (Investor Version)	

# _____________________________________________________________________________________________ Database Work.

## ZOZI ENTERPRISE DATABASE CONSTITUTION & BUILD MASTER PLAN

This document is the **Single Source of Truth** and **Binding Contract** for the ZOZI Platform Data Layer. Any AI agent or engineer MUST read this in full before generating, altering, or querying any database artifact.

---

## 1. ARCHITECTURE & FLOW DIAGRAMS

### A. Layered System & Data Flow Architecture
```mermaid
graph TD
    Client[Web / Mobile / API] -->|HTTPS/WSS| WAF[WAF / Nginx / CDN]
    WAF --> API[FastAPI Routers]
    API --> Ctrl[Controllers]
    Ctrl --> Svc[Services - ONLY WRITERS]
    
    Svc -->|Sync/ACID| DB[(PostgreSQL 15)]
    Svc -->|Async/Events| Outbox[Transactional Outbox]
    Svc -->|Cache/Queue| Redis[(Redis Cluster)]
    Svc -->|Bytes/Media| S3[Cloudflare R2 / S3]
    
    Outbox -->|Relay| Broker[Message Broker]
    Broker --> Workers[Task Workers: AI, Email, Analytics]
    
    DB -->|Read Replicas| Analytics[Analytics & Snapshots]
    DB -->|RLS / Partitions| Tenants[Country / Tenant Isolation]
```

### B. Media, Storage & AI Lifecycle
```text
[Upload] -> API Validation -> S3/R2 (Original Bytes) -> DB (`media_assets` Metadata)
                 |
                 v
         [Async Workers] -> Optimize/Thumbnail/WebP -> CDN Edge
                 |
                 v
         [AI Pipeline] -> CLIP/Whisper/OCR -> `ai_embeddings` (pgvector) -> `ai_staging`
                 |
                 v
         [Explicit Commit] -> Business Tables (e.g., `products`) -> Audit Log
```

---

## 2. MASTER BULLET POINTS (The "What" & "Rules")

### 🏛️ Golden Rules & Governance
*   **Single Source of Truth:** Never duplicate transactional data; reference it. No cross-ecosystem Foreign Keys (use Events/Services).
*   **No Silent Fallbacks:** If a pipeline fails, report it explicitly. Never mask errors.
*   **Schema Changes:** **Alembic ONLY**. `Base.metadata.create_all()` is strictly forbidden in Production. Every migration requires a downgrade and contract test.
*   **Country Isolation:** 100% of country-scoped tables MUST have `country_code` and PostgreSQL Row-Level Security (RLS).
*   **Immutability:** Financial ledgers and audit logs are append-only/WORM. Never `UPDATE` posted journal entries.
*   **Config as Data:** No hardcoded business constants (commissions, fees). Use config tables.

### 🗄️ Bounded Contexts (PostgreSQL Schemas)
*   `core`: Users, roles, sessions, devices, auth.
*   `commerce`: Products, variants, categories, carts, orders.
*   `supplier`: Profiles, KYC, documents, wallets.
*   `customer`: Profiles, addresses, wishlists, points.
*   `logistics`: Partners, fleet, shipments, routes, POD.
*   `finance`: Chart of Accounts, double-entry journal, AR/AP, invoices.
*   `treasury`: Cash positions, bank reconciliation, payouts.
*   `hr`: Employees, attendance, shifts, payroll.
*   `country`: Configs, cities, tax rules, legal rules.
*   `media`: `media_assets` metadata (bytes in object storage).
*   `ai`: Embeddings, requests, results, staging tables, jobs.
*   `communication`: Chat, email, SMS, push, tickets, video rooms.
*   `audit`: WORM logs, permission audits, security logs.
*   `security`: API keys, fraud, risk, MFA, OTP.
*   `analytics`: Daily/monthly snapshots, KPIs, materialized views.
*   `configuration`: System toggles, business rules.

### 🔍 Domain-Specific "Small Details" & Data Patterns

#### 🛒 Commerce & Catalog
*   **Categories:** Materialized path (`/1/15/42/`) + `lft/rgt` for instant subtree queries.
*   **Variants:** JSONB `attributes` + GIN index + `variant_key` hash. No flat columns for color/size.
*   **Limits:** Max 20 images per product. Max 50 variants per product.

#### 💰 Finance & Treasury
*   **Ledger Chain:** CoA → Journal → Ledger → Balance → Trial Balance → P&L.
*   **Rules:** Strict double-entry. `Σdebit == Σcredit`. Period-close locking.
*   **Payouts:** Batches → Treasury Payout → Journal → Bank.

#### 💬 Communication (Chat, Email, Video Calls)
*   **Chat Tables:** `chat_threads`, `chat_messages` (Partitioned monthly by `created_at`).
*   **Chat Features:** Read receipts, typing indicators (Redis), last seen, voice notes (Max 5MB, S3 stored).
*   **Video Calls:** `video_rooms` table tracks `session_id`, `participants`, `started_at`, `ended_at`. WebRTC signaling via WebSockets; DB only stores metadata/billing.
*   **Email/SMS:** `notification_queue`, `email_messages`. Provider-agnostic. Track opens/clicks via webhooks → `email_events`. Retry logic + Dead Letter Queue (DLQ).

#### 🖼️ Media & Storage (Images, Videos, Voice, Docs)
*   **Rule:** **Metadata in DB, Bytes in Object Storage (Cloudflare R2/S3).**
*   **Images:** Original → Optimized → Thumbnail → WebP → CDN. DB stores `url`, `mime`, `hash`, `w/h`, `ai_status`.
*   **Videos:** Max 200MB. Streamed via CDN.
*   **Documents:** Supplier KYC, PDFs. Encrypted at rest in S3.
*   **Lifecycle:** Hot (CDN) → Warm (S3 Standard) → Cold (S3 Glacier/Archive) → Destroyed (after legal retention).

#### 🤖 AI, Search & Vectorization
*   **Vectorization:** `pgvector` extension. `embedding vector(1536)` on products/AI assets. HNSW indexing.
*   **Search Strategy:** Hybrid Search = Full-Text Search (`tsvector` + GIN) + Semantic (`pgvector`) + CLIP (Vision).
*   **AI Staging:** AI NEVER writes directly to business tables. Flow: `ai_upload_jobs` → `ai_staging_*` → Explicit Human/Auto Commit → `products`.
*   **Models:** Local Ollama (`phi3:mini`, `qwen2.5`, `moondream`). Vision OFF by default on VPS to save costs.

#### 📊 Analytics, Events & Audit
*   **Events (Transactional Outbox):** `outbox_events` (written in same TX as business data) → Relay → Broker → `inbox_events` (idempotency dedupe) → `event_dead_letter`.
*   **Analytics:** NEVER run live aggregates on transactional tables. Use Materialized Views (`mv_daily_sales`, `kpi_revenue`) refreshed by cron.
*   **Audit:** ONE append-only `audit_logs` table, range-partitioned monthly. `log_type` enum (activity, security, finance, api).

### ⚙️ Infrastructure, Scaling & Security
*   **Performance Targets:** Search <300ms, Product Page <200ms, Checkout <500ms, Hot-list p95 <300ms.
*   **Pooling:** PgBouncer (Transaction mode) in Prod. App pool `size=5`, `max_overflow=10`.
*   **Pagination:** Cursor-based EVERYWHERE. No `OFFSET` on large tables.
*   **Security:** TLS in transit, Encryption at rest. PII masking at app layer. WORM for financial/legal.
*   **Growth Planning:** MVP (10K products) → Scale (1M products, JSONB GIN, pgvector) → Massive (100M products, shard by country).

---

## 3. STEP-BY-STEP CONSTRUCTION GUIDE (For AI & Engineers)

*Execute these steps sequentially. Do not skip phases. Validate against the "AI Binding Contract" at every step.*

### Step 1: Foundation & Governance Setup
1.  **Initialize Alembic:** Set up `alembic/` directory. Configure `env.py` to read from `APP_ENV`.
2.  **Enforce Env Gate:** Write a startup guard in `db/database.py` that raises a fatal error if `Base.metadata.create_all()` is called when `APP_ENV != development`.
3.  **Create Schemas:** Execute `CREATE SCHEMA` for all 16 bounded contexts (`core`, `commerce`, `finance`, etc.).
4.  **Implement Mixins:** Create `db/mixins.py` with `AuditMixin` (created_at, updated_at, created_by, version), `SoftDeleteMixin` (is_deleted, deleted_at, delete_reason), and `TenantMixin` (country_code).

### Step 2: Core, Identity & Country Isolation
1.  **Build Core Tables:** `users`, `roles`, `sessions`, `devices` in the `core` schema.
2.  **Implement RLS:** Write `data/pg_rls_policies.sql`. Create the `rls_interceptor.py` middleware to `SET app.current_country_code` on every request.
3.  **Apply RLS:** Apply policies to all `TenantMixin` inherited tables. Ensure cross-country reads return 0 rows (fail-closed).
4.  **Security Tables:** Build `security` schema (api_keys, mfa, otp, blacklist).

### Step 3: Catalog, Media & Object Storage
1.  **Object Storage Setup:** Configure `boto3` with Cloudflare R2 endpoint.
2.  **Build Media Tables:** Create `media.media_assets` (metadata only: url, mime, hash, w/h, ai_status).
3.  **Build Catalog:** Create `commerce.categories` (materialized path), `commerce.products`, `commerce.product_variants` (JSONB attributes + GIN).
4.  **Implement Upload Flow:** API receives file -> uploads bytes to R2 -> saves metadata to `media_assets` -> links to product.

### Step 4: Commerce, Logistics & Event Outbox
1.  **Build Order Flow:** `commerce.orders`, `order_items`, `carts`.
2.  **Implement Transactional Outbox:** Create `outbox_events`, `inbox_events`, `event_retry_queue`, `event_dead_letter`.
3.  **Wire Services:** Ensure `OrderService` writes to `orders` AND `outbox_events` in the **exact same database transaction**.
4.  **Logistics:** Build `logistics.shipments`, `routes`, `pod` (Proof of Delivery). Link via events, not FKs.

### Step 5: Strict Finance & Ledger Implementation
1.  **Build Ledger:** Create `finance.accounts` (CoA), `finance.journal_entries`, `finance.journal_entry_lines`.
2.  **Enforce Immutability:** Write a PostgreSQL Trigger that raises an exception on `UPDATE` or `DELETE` to `journal_entry_lines`.
3.  **Build Ledger Service:** Create `finance_ledger_service.py`. This is the **ONLY** service allowed to insert into journal tables. Ensure `Σdebit == Σcredit` before commit.
4.  **Treasury:** Build `treasury.payout_batches`, `cash_positions`.

### Step 6: Communication (Chat, Video, Notifications)
1.  **Build Chat:** Create `communication.chat_threads`, `chat_messages`. Apply **Monthly Range Partitioning** on `chat_messages.created_at`.
2.  **Video Calls:** Create `communication.video_rooms` for session metadata. Integrate WebSocket router for WebRTC signaling.
3.  **Notifications:** Build `communication.notification_queue`, `email_messages`, `push_logs`. Implement retry logic and DLQ routing.
4.  **Presence:** Configure Redis to handle ephemeral "typing" and "online" states (do not store in Postgres).

### Step 7: AI, Vectorization & Search
1.  **Enable Extensions:** Run `CREATE EXTENSION vector; CREATE EXTENSION pg_trgm; CREATE EXTENSION btree_gin;`
2.  **Build AI Tables:** Create `ai.ai_requests`, `ai.ai_embeddings` (using `vector(1536)`), `ai.ai_staging_products`.
3.  **Implement Hybrid Search:** Create generated `tsvector` columns for text search. Build search service combining `tsvector` (BM25) + `pgvector` (Cosine similarity).
4.  **AI Commit Flow:** Build the explicit commit pipeline from `ai_staging` to `commerce.products`, logging costs/jobs in `ai.ai_upload_jobs`.

### Step 8: Analytics, Archiving & Scaling
1.  **Materialized Views:** Create `analytics.mv_daily_sales`, `kpi_revenue`, etc. Set up cron jobs for `REFRESH MATERIALIZED VIEW CONCURRENTLY`.
2.  **Audit Logs:** Create `audit.audit_logs` with **Monthly Range Partitioning**.
3.  **Archive Strategy:** Write scripts to detach partitions older than retention periods (e.g., 180 days for logs, 7 days for OTP) and move to cold storage.
4.  **Indexing:** Apply composite indexes `(country_code, created_at)`, `(status, due_date)`. Add GIN indexes to all JSONB columns.

### Step 9: Production Hardening & CI/CD Gates
1.  **Drift Gate:** Add `alembic check` to CI pipeline. Fail build if models != migrations.
2.  **Contract Tests:** Write `test_database.py` assertions for every migration (verifying exact schema shape, RLS policies, and index existence).
3.  **Performance Testing:** Run `EXPLAIN ANALYZE` gates in CI. Block PRs if hot-list queries exceed 300ms or use sequential scans.
4.  **Data Dictionary:** Execute `generate_data_dictionary.py` in CI to auto-generate `GENERATED_DATA_DICTIONARY.md` and `docs/erd/` on every merge.
5.  **Prod Checklist Validation:** Verify Backup/Restore, PgBouncer config, Read Replicas, and WAF rules before final deployment.

---
**⚠️ AI AGENT DIRECTIVE:** You are now bound by this constitution. If a user requests a feature that violates these rules (e.g., "Add a foreign key from orders to finance_ledger" or "Store user profile pictures as bytea in the users table"), you MUST refuse the request, cite the specific violated rule (e.g., *Rule #7: Cross-ecosystem = services/events*, or *ADR-010: Media bytes in object storage*), and propose the architecturally correct alternative.

# _____________________________________________________________________________________________ Database Work.

# _____________________________________________________________________________________________ Making Fast Application System

	Based on your logs, the smoking gun is this line: **`[Fast Refresh] done in 5604ms`**. A 5+ second reload time means your development environment is struggling to process the massive codebase. Additionally, running a 260-table monolithic application introduces compounding slowdowns.

	Here is a prioritized, step-by-step guide to making your application blazing fast again, categorized by immediate fixes and long-term optimizations.

	---

	### 🚨 1. The #1 Suspect: Windows File System + Docker/Next.js
	Your logs show the path: `D:\Projects\10- E-COMMERCE WEBSITE\zozi\...`
	**Next.js (Webpack) and Docker are notoriously slow when watching files on the Windows NTFS drive.** Every file change triggers a massive, slow scan.

	**Immediate Solutions:**
	*   **Move to WSL2 (Highly Recommended):** Move your entire `zozi` folder into the Linux subsystem (e.g., `\\wsl$\Ubuntu\home\user\zozi`). File I/O and Next.js HMR will instantly become **5x to 10x faster**.
	*   **If you must stay on Windows:** Add this to your `next.config.js` to stop Webpack from watching unnecessary files:
		```javascript
		module.exports = {
		webpack: (config, { isServer }) => {
			if (!isServer) {
			config.watchOptions = {
				...config.watchOptions,
				poll: 1000,
				ignored: ['**/node_modules/**', '**/.git/**', '**/dist/**', '**/coverage/**'],
			};
			}
			return config;
		},
		}
		```

	---

	### ⚡ 2. Frontend (Next.js) Speedups
	Your frontend is bundling too much code on every change.

	*   **Enable Turbopack (Next.js 14+):** Turbopack is written in Rust and is exponentially faster than Webpack for development.
		*   Change your `package.json` script: `"dev": "next dev --turbo"`
	*   **Dynamic Imports (Code Splitting):** Don't load heavy components (like Maps, large Charts, or the AI Image Editor) on initial page load. Load them only when needed.
		```tsx
		import dynamic from 'next/dynamic';
		const HeavyMapComponent = dynamic(() => import('@/components/HeavyMap'), { ssr: false, loading: () => <p>Loading...</p> });
		```
	*   **Disable ESLint during Dev:** ESLint runs on every save and can add seconds to HMR. Disable it in dev mode:
		```javascript
		// next.config.js
		module.exports = {
		eslint: { ignoreDuringBuilds: process.env.NODE_ENV === 'development' },
		}
		```

	---

	### 🚀 3. Backend (FastAPI) Speedups
	With 260 tables, FastAPI can take seconds just to start up and validate Pydantic models.

	*   **Upgrade to Pydantic V2:** If you are still on Pydantic V1, upgrade immediately (`pip install "pydantic>=2.0"`). Pydantic V2 (powered by Rust) is **5x to 50x faster** at data validation.
	*   **Lazy-Load Routers:** Do not import all 20+ routers at the top of `main.py`. Import them inside the `lifespan` context or use a dynamic registration loop to reduce initial memory load and startup time.
	*   **Disable Docs in Production:** Ensure `docs_url=None` and `redoc_url=None` in your `FastAPI()` initialization for production, as generating the OpenAPI schema for 260 tables is expensive.

	---

	### 🗄️ 4. Database (PostgreSQL) Optimizations
	A massive schema leads to slow queries, which makes the whole app feel sluggish.

	*   **Fix N+1 Queries:** With 260 tables, it's easy to accidentally trigger dozens of queries per request. Use SQLAlchemy's `selectinload` or `joinedload` to fetch relationships in a single query.
		*   *Bad:* `order.customer.address` (triggers 3 queries)
		*   *Good:* `db.query(Order).options(selectinload(Order.customer).selectinload(Customer.address)).first()`
	*   **Ensure Critical Indexes Exist:** Verify that every foreign key, `country_code`, `status`, and `created_at` column has an index. Your logs show you are adding GIN indexes for JSONB, which is excellent—keep doing that.
	*   **Use Materialized Views for Dashboards:** The Command Center and Analytics pages are likely running complex `JOIN`s across 10+ tables. Create a `materialized view` that aggregates this data and refresh it every 5 minutes via a background cron job, rather than calculating it on every page load.

	---

	### 🐳 5. Docker Compose Optimizations
	If you are running this via `docker-compose up`, file syncing is a major bottleneck.

	*   **Use `cached` or `delegated` volume mounts:** Tell Docker that the container's view of the files is authoritative for reading, which speeds up I/O.
		```yaml
		volumes:
		- ./frontend/web_app:/app:cached  # Add :cached for Mac/Windows
		- ./backend:/app:cached
		```
	*   **Increase Docker Resources:** Ensure Docker Desktop is allocated at least **4 CPUs** and **8GB of RAM**.

	---

	### 🛠️ Action Plan: Do This Right Now
	1. **Move the project to WSL2** (if on Windows) or ensure you are not running it from a synced network drive.
	2. Update `package.json` to use `"dev": "next dev --turbo"`.
	3. Run `npm run dev` and watch the `[Fast Refresh]` time drop from ~5000ms to **< 500ms**.
	4. Check your FastAPI logs: if startup takes > 3 seconds, review your Pydantic models and router imports.

	If you implement just the **WSL2 move** and **Turbopack**, you will see an immediate, dramatic improvement in your development speed.

# _____________________________________________________________________________________________ Making Fast Application System

# _____________________________________________________________________________________________ Frontend/web_app UIUX AUDIT

## UI and UX of the web_app:

1. Read the codebase in detail and list down all the file and Function for UI and UX of the web_app.
2. UI and UX of the web_app is mis-match accross all the pages, button, widgets, font, theme, color, panel, glossy look accross all the pages. 
3. Panel Pages, Login/Signup Page of `Admin`, `Supplier` and `Logistic Partner` needs to be attention to be similar.
4. Light theme need attention to be look glossy and attractive and better look.
5. Dark theme as well for similar accross to all the pages and panels.
6. Need complete audit and review of the UI and UX of all the pages and panels and make it more attractive, user friendly and glossy look and similar accross to all the pages and panels and also make sure all the functions are working properly.
7. All three panels `Admin`, `Supplier` and `Logistic Partner` will be handle 1000s of queries and request at a time so according to that you can use below intelligently: 
    -  alert and notification system.
    -  tabs and filters system, search and sorting system. 
    -  color coding system for the status and priority and etc but under the theme, not extra colors.
    -  complete integrated dashborad system for the panels to manage and track all the queries and request efficiently and effectively.
    - and make changes of improvement what you feel better to have in the Ui and UX to manage and track 1000s of queries and request at a time. 
8. You don't need to make big changes.
9. Make a complete plan, checkpoint, test before implementation and after implementation and start to work on it.
10. You have to be careful while working on the UI and UX our website is already 80% complete already.


## Audit of UI and UX of the web_app:

### Phase 1: Analysis
1. Audit all pages in `frontend/web_app` and document current UI/UX inconsistencies
2. Identify mismatches across: buttons, widgets, fonts, themes, colors, spacing, and visual effects
3. Compare Login/Signup and Panel designs for `Admin`, `Supplier`, and `Logistic Partner` - highlight alignment gaps

### Phase 2: Design System Definition
4. Create a unified design system with consistent theme variables (light and dark modes)
5. Define standardized components: buttons, cards, inputs, modals, notifications, and panels
6. Establish typography, spacing, color palette, and glossy visual effects guidelines

### Phase 3: Implementation Strategy
7. For high-volume query/request management across all panels, implement:
    - Smart alert and notification system with priority levels
    - Advanced filters, search, and sorting functionality
    - Color-coded status indicators (using theme-aware palette, no extra colors)
    - Integrated dashboard with real-time analytics and query tracking
    - Responsive layout optimizations for handling concurrent operations
8. Minimize disruption: target incremental refinements, not full redesigns
9. Create migration checkpoints to prevent breaking existing functionality

### Phase 4: Execution & Validation
10. Establish QA checkpoints (pre-implementation, mid-sprint, post-implementation)
11. Test all functionality across light/dark themes on each updated page
12. Verify performance under load and ensure consistency across all three panels
13. Proceed carefully—preserve the 80% completion; focus on polish and consistency


Frontend/web_app

make a plan. there is a range of inconsistancy in all over the system of styling, color, component, and layout.
1. check all the panels, supplier, logistic, admin for buttons color, design, layout and etc to make it consistant. specially lime green color buttons, it must be follow same color of system color.
2. Slider of the Panel is not working properly of all panels, need to fix it and inconsistant the buttons and is not responsive
3. all the popup and dropdown are not consistant.
4. Product card are not responsive buttons, text, font, currency and everything is not responsive.
5. make everything faster and responsive
6. read more in detail all the frontend/web_app and find more problem of the frontend.
7. The system is loading very slow and not responsive. optimize the frontend/web_app performance.
8. there are a range of problems of frontend in the panels, pages, tab, widget consistancy which are still not solved.
9. remove the hardcode and do not write new hardcode
10. improve all the st

do the complete audit and investigation and resolve all problem correctly.

# _____________________________________________________________________________________________ Frontend/web_app UIUX AUDIT

# _____________________________________________________________________________________________ Frontend/mobile_app UIUX AUDIT

## Mobile App Audit, Alignment & Enhancement

### Phase 1: Codebase Analysis
1. List all files, folder structure, pages, components, and functions in `frontend/mobile_app` and `frontend/shared`
2. Document UI/UX framework, state management, authentication, API integration, and navigation
3. Audit all existing functionality: features, bugs, performance issues, and incomplete implementations
4. Update `CODEBASE_STATUS_MATRIX_DETAILED.md` with mobile app current status

### Phase 2: Web-to-Mobile Feature Mapping
5. Create comprehensive inventory of all `frontend/web_app` pages, components, functions, and features
6. Map each web_app feature to corresponding mobile_app implementation status (Complete/Partial/Missing/Broken)
7. Identify gaps: missing pages, missing functions, incomplete features, and non-working functions
8. Document UI/UX differences and usability issues specific to mobile

### Phase 3: Bug Fixing & Core Stabilization
9. Reproduce, document, and fix all identified bugs and issues in mobile_app
10. Test core functionality: authentication, API calls, state persistence, offline handling, navigation flow
11. Verify error handling, validation, and user feedback across all screens
12. Test on multiple device sizes (phone, tablet), orientations, and OS versions

### Phase 4: Feature Implementation & Alignment
13. Implement all missing pages and features from web_app (prioritize by business criticality)
14. Ensure functional parity: test each implemented feature against web_app equivalent
15. Implement missing API integrations and backend connections
16. Verify all components integrate properly with `frontend/shared` components

### Phase 5: UI/UX Enhancement & Consistency
17. Audit UI consistency: typography, spacing, colors, button styles, icons, and theme application
18. Redesign basic/outdated UI elements to match modern mobile standards
19. Implement responsive design patterns for varied screen sizes
20. Apply unified design system across light/dark themes for mobile platform
21. Enhance navigation patterns, gestures, loading states, and error screens

### Phase 6: Performance & Reliability Testing
22. Profile app performance: startup time, memory usage, navigation speed, API response time
23. Optimize: lazy loading, image optimization, state management, network requests
24. Test offline functionality, network reconnection handling, and data sync
25. Conduct load testing and stress testing on critical features

### Phase 7: End-to-End Testing
26. Create comprehensive test matrix covering all pages, functions, and user flows
27. Test on real devices (not just emulators): iOS and Android, various OS versions
28. Perform UAT (User Acceptance Testing) across all three user types: Customer, Supplier, Logistic Partner
29. Test payment flows, order management, notifications, and authentication workflows
30. Verify all backend API calls work correctly and handle errors gracefully

### Phase 8: Security & Data Validation
31. Audit security: credentials storage, API authentication, data encryption, sensitive data handling
32. Validate input handling on all forms and user inputs
33. Test permission requests (camera, location, notifications, storage)
34. Verify secure session management and logout functionality

### Phase 9: Documentation & Readiness
35. Document all implemented features, known limitations, and known issues
36. Create user guides for mobile app functionality
37. Update developer documentation with mobile-specific implementation details
38. Prepare release notes and deployment checklist

### Testing Checkpoints:
- **Pre-Implementation**: Document current issues, create test cases database
- **Mid-Implementation**: Test features as implemented, verify API integration
- **Post-Implementation**: Full regression testing, device compatibility testing, performance validation
- **Final Release**: UAT sign-off, production readiness check, backup and rollback plan

### Success Criteria:
- All web_app features functional in mobile_app (or documented as intentional omissions)
- No critical bugs; all P0 and P1 issues resolved
- Performance metrics met (startup < 3s, navigation < 500ms, API calls < 2s)
- UI/UX consistent across all screens and themes
- All three user roles (Customer, Supplier, Logistic Partner) fully functional with complete workflows
- Test coverage > 80% on critical user flows



	## Mobile Screen:

	`http://localhost:19006/home` and `http://localhost:19006/products` both have same objective.
		keep the `http://localhost:19006/products` and remove complete `http://localhost:19006/home` 
		but `http://localhost:19006/products` needs some changes
		Header: 
			1. Make a complete Header with the theme lime color with same shades, both side slider button is fine and place of button and in middle ZOZI logo.
			2. Search+Filter bar needs to be complete copy from the web_app because I love that style of Search + Filter bar and also keep at top at middle. 
			3. banner will component will come.
		Footer:
			1. Color will be the theme lime color with same shades, 
			2. Buttons will be looks glossy according to the theme Dark & Light.
			3. remove the search button, home button because Home Screen no longer needed, Search Bar is at upside in header.

	Read the code of the header, banner, and footer and make the changes according below. and read the html code for your reference. 

	1. the header top needs to cover too come at down the  search+filter bar and half banner.
	2. the footer needs to be color lime green
	3. remove extra search bar you just added and we need original search bar which we have same as in web_app



	- banner data is comming too much, and mobile banner will be allowed to design from the Admin seperately becasue of it has low space and customer will not like crowed banner. so make the arragement accordingly. 
	- Footer needs to be lime green as same as it header and also footer needs to folllow the system styling.
	- complete mobile application is not following the theme color, theme setting. it is not consistent with the website theme. so check and fix.
	- Product card size is inconsistent and also not responsive.
	- Take exact color scheme of the web_app into the mobile_app of lime and yellow gradient, I need same.
	- http://localhost:8081/products | shift the `search+filter` bar to upward more to be fit into/inside of the header section and also align into one line and also do the the copy of style of web_app.
	- Search+Filter bar needs size adjustment properly to fit into one row. and according to the web_app search bar we have some thin border which is not coming into mobile_app search bar. if you need you can remove the text from it.
	- http://localhost:8081/products/** is not following the style of the application.
	- Login Screen | have 2 ZOZI logos. 
	- Footer | is also must be lime green color as same as system theme color.
	- Font | use better font.
	- http://localhost:8081/edit-profile | have error check and resolve it and test also.
	- Range of things are coming double which have to resolve, so do the audit of doubling and resolve the doubling issue
	- application is running very slow, make it faster properly. 

shift up the search+filter bar, remove search text from search button.

1. `http://localhost:8081/addresses` is the part of profile so remove that.
2. `My Order` and `Notification` is the Family Feature of My Account. right ? so shift that into right side.
3. copy the color of Sign-In button and use that in all button everywhere becasue that is the theme color button.
4. fix the icons in all over the application
5. Search+Filter is not working and remove the text. add the animation when anyone press it will show the text, according to that we will get space. and reduce the size of icon in search bar.
6. Coupon is comming in 2 place.
7. Flash Sale scren has error, so fix that.
8. Notification Screen have some animation proper. fix that.
9. there a range of animation problem which you have to understand and enhance
10. banner size need to be reduce. 	- banner data is comming too much, and mobile banner will be allowed to design from the Admin seperately becasue of it has low space and customer will not like crowed banner. so make the arragement accordingly. banner is not sliding up while scrolling.
11. Footer needs to be lime green as same as it header and also footer needs to folllow the system styling.
12. Languague should open one more slider for list of selection
13. Seeting UIUX is not cool, make it better.
14. Profile have again notification, my order, offers & Coupons, setting, AI chatbot and etc which is repeating. 





---

	### 📱 Mobile App Frontend Fixes (Zozi)
		- **Banner Management**
		- Mobile banners must be designed separately in Admin (smaller space, avoid crowding).
		- Reduce banner data load; optimize for mobile UX.

		- **Theme & Styling**
		- Footer must be lime green (same as header) and follow system styling.
		- Entire mobile app must consistently follow website theme colors (lime + yellow gradient).
		- Product card sizes must be consistent and responsive.
		- Fonts should be improved for readability and modern look.

		- **Search & Filter**
		- On `/products`, shift search+filter bar upward into header section.
		- Align search+filter bar into one row; copy exact style from web_app.
		- Add thin border styling (same as web_app); remove extra text if needed.
		- Ensure `/products/**` pages follow application style.

		- **Screens Consistency**
		- Login screen currently shows **two Zozi logos** → keep only one.
		- Header must be copied and consistent across all screens.
		- Footer must be lime green everywhere (system theme color).

		- **Profile & Error Handling**
		- `/edit-profile` has errors → fix and test thoroughly.
		- Audit and resolve **duplicate/double rendering issues** across app.

		- **Performance**
		- App is running slow → optimize performance (lazy loading, caching, API response times).
		- Ensure smooth navigation and responsiveness across devices.

---
	do the audit and investiagation of all screens of the mobile_app and backend and start connect and make better UIUX of th mobile_app.
	there is a range of screen are not live





# _____________________________________________________________________________________________ Frontend/mobile_app UIUX AUDIT

# _____________________________________________________________________________________________ Order System

## ZOZI ORDER TRACKER & ORDER MANAGEMENT — BINDING BUILD SPEC

> Scope: Customer → Supplier → Logistic Partner → Customer delivery loop, with Admin oversight. This spec is **constitution-compliant** (`01_DATABASE.md`): events over cross-FKs, media bytes in R2, config-as-data, RLS `country_code`, audit-everything, **no silent/hardcoded fallbacks**.

---

## 1. DETAILED BULLET POINTS

### 1.1 Non-negotiables
- **One order, one identity:** every order gets a unique Order ID + signed QR token at placement; the QR is the physical "passport" of the parcel across all hands.
- **Single source of truth for status:** status lives only in DB; every change is a server-side validated transition (config-driven state machine, **not** UI logic) written to `shipment_events` + published as an outbox event.
- **No hardcoded fallbacks:** if QR service / location service / signature capture is unavailable, the system reports an explicit error mode and offers the *audited alternate path* (request→confirm). Never auto-succeed, never fake a scan.
- **Universal visibility:** the same order + same timeline is visible to **Customer, Supplier, Logistic Partner, Admin** — each with role-scoped actions.
- **Proof at every handover:** pickup = QR scan *or* supplier-confirmed request; delivery = e-signature *or* customer-confirmed request; packaging = packed-parcel photo. All proofs are media files (bytes in R2, metadata in DB).
- **Admin is the referee:** Admin can correct any wrongly-set status and cancel any wrong order — always with mandatory reason + audit log + notification to all parties.

### 1.2 Canonical lifecycle — EXACTLY as defined (order → delivery)
1. **`PENDING`** — Customer places order (payment/COD). Location captured (GPS + IP-geo service). Order appears on Supplier page (new-order alert), Customer "My Orders", Admin. Not shown to logistics yet.
2. **`PROCESSING`** — Supplier sees and accepts the order; starts processing. Visible on Supplier / Customer / Admin pages.
3. **`PREPARED`** — Supplier finishes packing: prints the parcel sheet, applies tamper seal + QR label, logs weight/dimensions, **uploads photo of the packed parcel**. Status flips to `PREPARED` and the order **flashes on ALL logistic partner pages** as available for pick-up.
4. **`PICKING UP`** — One logistic partner confirms pick-up. From this moment the order is **removed from every other logistic partner's page** and visible only to the claiming partner (plus Supplier/Customer/Admin).
   - Logistic partner **may cancel the pick-up** at this stage (any reason, **before** picked/shipped) → order returns to `PREPARED` and re-flashes to all partners.
5. **`PICKED FROM SUPPLIER`** — physical handover, verified by **either** path:
   - **Path A:** logistic partner **scans the parcel QR** in-app at handover; **or**
   - **Path B:** logistic sends a pick-up request → supplier gets notified → supplier confirms the handover.
6. **Transit (logistic-only sub-statuses, allowed only between `PICKED` and `DELIVERED`):**
   - `LOGISTIC RECEIVED` (hub receives from rider) → `DISTRIBUTION CHECKPOINT` (reaches distribution center) → `OUT FOR DELIVERY` / *In Transit / Delivering to Customer* (rider out, live GPS on).
   - Exceptions: `SHIPMENT DELAYED` (problem, resumes later), `SHIPMENT RESCHEDULED` (new slot), `SHIPMENT FAILED` (unresolvable → must **return parcel to supplier** → `SHIPMENT CANCELLED`), `SHIPMENT RETURNED` (customer rejects at door → return to supplier → cancel/refund).
7. **`DELIVERED`** — final handover, verified by **either** path:
   - **Path A:** logistic takes the customer's **e-signature** on the app; **or**
   - **Path B:** logistic sends a delivery request → customer gets notified → customer confirms receipt.
8. **`CANCELLED`** — customer cancels mid-process (before pick-up completes), or Admin cancels a wrong order. Visible everywhere.
9. **Post-delivery:** Returns / Replacement window opens (see §1.5).

### 1.3 Status & transition rules (who may do what)
- **Supplier:** `PENDING→PROCESSING→PREPARED`; confirm pick-up request (Path B); confirm return receipt.
- **Logistic partner:** claim `PREPARED→PICKING UP`; cancel own claim; scan QR / request pick-up; all transit sub-statuses; request delivery confirmation.
- **Customer:** cancel (early stages); confirm delivery (Path B); reject at door (`SHIPMENT RETURNED`); request return/replacement.
- **Admin:** **override/correct any status** (mandatory reason), **cancel any order**, resolve disputes, view everything.
- Transition matrix stored in **`configuration.order_status_rules`** (config-as-data) — server enforces it; illegal transitions rejected with explicit error.

### 1.4 Packaging & printing material
- **Supplier packages by default** (fastest); standardized: tamper-proof seal + QR label + optional weight/dimensions. Optional future **Packaging Manager** role (central hub) — reserved, config-switchable, no schema redesign later.
- **"Print Parcel Sheet" button on the Supplier order page** generates a one-page sheet containing:
  - Customer Name · Contact Number · Full Location **+ Latitude/Longitude** · Landmark
  - Order Items List (qty, variant attributes) · Invoice · Order Number · **QR code**
  - Payment method + **COD amount to collect** (if COD) · Supplier return address · Tamper-seal ID · Print timestamp
- Label payload served by a **first-class endpoint** (`/orders/{id}/label`) returning structured JSON + printable PDF/HTML; QR encodes a signed token URL resolved server-side (role + status checked on every scan).

### 1.5 Returns & replacements (part of tracking, not an afterthought)
- Customer requests **Return** or **Replacement** from My Orders within a configurable window (`order_status_rules`/config), with reason + optional photos.
- Admin (or auto-policy) approves → **reverse shipment** created and tracked with the same engine: `RETURN_REQUESTED → RETURN_APPROVED → RETURN_IN_TRANSIT (reverse pick-up) → RETURNED_TO_SUPPLIER (inspection)`.
- Outcome: **Refund** posted only through the finance **ledger service** (never ad-hoc), or **Replacement** = new order linked via `original_order_uuid`, dispatched through the identical tracking flow.

### 1.6 Panel visibility matrix
| Status | Customer | Supplier | Claiming Logistic | Other Logistics | Admin |
|---|---|---|---|---|---|
| PENDING / PROCESSING | ✅ timeline | ✅ queue | — | — | ✅ |
| PREPARED | ✅ | ✅ | ✅ **flashing pick-up board** | ✅ flashing | ✅ |
| PICKING UP → OUT FOR DELIVERY | ✅ live + GPS | ✅ | ✅ own order only | ❌ **hidden** | ✅ |
| DELIVERED / CANCELLED / SHIPMENT CANCELLED / RETURNED | ✅ | ✅ | ✅ history | ❌ | ✅ |

### 1.7 Database additions (constitution-compliant)
- `commerce.packages`: 1:1 to order · `qr_token_hash` · weight/dimensions · `tamper_seal_id` · `packed_photo_media_id` · `packaged_by/at`.
- `logistics.shipments`: claiming partner, claim/cancel timestamps, current sub-status.
- `logistics.shipment_events`: **monthly range-partitioned** · `order_uuid`, `actor_role`, `status`, lat/lng, notes, `media_ref` (photo/signature), idempotency key.
- `logistics.proof_of_delivery`: method (`qr_scan | supplier_confirm | e_signature | customer_confirm`), `signature_media_id`, confirmer.
- `commerce.return_requests` (+ replacement link) · `configuration.order_status_rules`.
- All tables: `country_code` + RLS, audit mixins, soft-delete; **media bytes in R2**, metadata in `media_assets`.

### 1.8 Events, notifications & reconciliation
- Every status change → same-transaction `outbox_events` write → WS push + push notification + email (key transitions) to the 4 panels; UI shows explicit error state if feed unavailable (no silent zeros).
- **Reconciliation engine (restored, country-aware):**
  - `COD:` Delivered → rider collects cash → **Logistic remits → ZOZI Treasury → Supplier payout (− commission)**
  - `Card:` Gateway → **Treasury → Supplier payout (− commission)** and **Treasury → Logistic delivery fee**
  - Nightly reconciliation cron with variance alerting; order referenced by `order_uuid` data column + events (no cross-ecosystem FK).
- **Location service:** small Python sidecar resolving IP→geo (GeoIP DB) merged with device GPS; stored on order with accuracy; failure → explicit "pin manually" mode, never silent.
- **Admin ecosystem wiring:** staff/employees+permissions merged hierarchy; unified Communication tab (video/chat/email); unified Moderator/Tickets/Disputes; Command Center + Analytics merged; Payments/Payouts, Finance CoA + Treasury wired; commission engine restored; full Admin CRUD.

### 1.9 Surfaces & sign-off
- Implement identically in **web_app** (Customer/Admin/Supplier/Logistic panels) and **mobile_app** (scan, signature, GPS, claim board).
- **E2E test matrix:** golden path (place→process→pack+photo+print→claim→QR scan→transit sub-statuses→e-sign→delivered); pick-up cancel; delayed/rescheduled; failed→return→cancelled; door-reject→returned; customer cancel; admin override/cancel; return & replacement; visibility assertions (flash at PREPARED, hide at PICKING UP); no-fallback assertions; COD reconciliation run.
- After all green → update `documents/CODEBASE_STATUS_MATRIX_DETAILED.md` section-by-section.

---

## 2. DIAGRAMS

### 2.1 End-to-end flow (swim-lane, handovers & proofs)
```mermaid
flowchart TB
subgraph CUST["👤 CUSTOMER"]
  C1["Places order (COD/Card)<br/>GPS + IP-geo captured"]
  C2["My Orders: live timeline"]
  C3["e-Signature on app (A)<br/>OR confirms delivery request (B)"]
  C4["Rejects at door / requests return"]
end
subgraph SUP["🏪 SUPPLIER"]
  S1["New order → PROCESSING"]
  S2["Packs · PRINTS PARCEL SHEET<br/>tamper seal + QR + weight/dims"]
  S3["Uploads packed-parcel PHOTO → PREPARED"]
  S4["Confirms pick-up request (B)"]
end
subgraph LOG["🚚 LOGISTIC PARTNER"]
  L1["Pick-up board: PREPARED orders FLASH<br/>(all partners)"]
  L2["Claims pick-up → PICKING UP<br/>hidden from other partners"]
  L3["Scans parcel QR (A)"]
  L4["LOGISTIC RECEIVED → DISTRIBUTION CHECKPOINT<br/>→ OUT FOR DELIVERY (+live GPS)"]
  L5["Exceptions: DELAYED · RESCHEDULED ·<br/>FAILED→return to supplier→CANCELLED"]
end
subgraph SYS["🧠 SYSTEM / ️ ADMIN"]
  Q["Order ID + signed QR generated<br/>label payload endpoint"]
  E["Each change → shipment_events + outbox event<br/>→ WS/push to all 4 panels"]
  AD["ADMIN: full visibility · correct wrong status ·<br/>cancel wrong order · disputes · reconciliation"]
end

C1 --> Q --> S1 --> S2 --> S3 --> L1 --> L2
L2 --> L3 --> L4
L2 --> S4 --> L4
S4 -.notify.-> SUP
L4 --> L5
L4 --> C3 -->|DELIVERED| C2
L4 --> C4 -->|SHIPMENT RETURNED → supplier| C2
C1 -.customer/admin cancel.-> CX["CANCELLED"]
E -.fan-out.-> CUST & SUP & LOG & AD
```

### 2.2 Status state-machine (guards = roles; proofs required)
```mermaid
stateDiagram-v2
    [*] --> PENDING : Customer places order
    PENDING --> PROCESSING : Supplier accepts
    PROCESSING --> PREPARED : Supplier packs + photo + printed QR label
    PREPARED --> PICKING_UP : ONE logistic claims (others hidden)
    PICKING_UP --> PREPARED : Logistic cancels claim (before picked)
    PREPARED --> PICKED_FROM_SUPPLIER : QR scan (A) / supplier confirms (B)
    PICKING_UP --> PICKED_FROM_SUPPLIER : QR scan (A) / supplier confirms (B)
    PICKED_FROM_SUPPLIER --> LOGISTIC_RECEIVED : hub intake
    LOGISTIC_RECEIVED --> DISTRIBUTION_CHECKPOINT : dist. center
    DISTRIBUTION_CHECKPOINT --> OUT_FOR_DELIVERY : rider dispatched
    PICKED_FROM_SUPPLIER --> SHIPMENT_DELAYED : issue → resume
    SHIPMENT_DELAYED --> OUT_FOR_DELIVERY
    PICKED_FROM_SUPPLIER --> SHIPMENT_RESCHEDULED : new slot
    SHIPMENT_RESCHEDULED --> OUT_FOR_DELIVERY
    PICKED_FROM_SUPPLIER --> SHIPMENT_FAILED : unresolvable
    SHIPMENT_FAILED --> SHIPMENT_CANCELLED : return to supplier, then cancel
    OUT_FOR_DELIVERY --> DELIVERED : e-signature (A) / customer confirms (B)
    OUT_FOR_DELIVERY --> SHIPMENT_RETURNED : reject at door → return to supplier
    PENDING --> CANCELLED : customer / admin
    PROCESSING --> CANCELLED : customer / admin
    PREPARED --> CANCELLED : customer / admin
    DELIVERED --> RETURN_REQUESTED : return/replacement window
    RETURN_REQUESTED --> RETURN_APPROVED : admin/policy
    RETURN_APPROVED --> RETURN_IN_TRANSIT : reverse pick-up
    RETURN_IN_TRANSIT --> RETURNED_TO_SUPPLIER : inspection
    RETURNED_TO_SUPPLIER --> REFUNDED : ledger refund
    RETURNED_TO_SUPPLIER --> REPLACEMENT_DISPATCHED : linked new order
    DELIVERED --> [*]
    CANCELLED --> [*]
    SHIPMENT_CANCELLED --> [*]
    SHIPMENT_RETURNED --> [*]
```

### 2.3 Money flow (reconciliation)
```
COD :  DELIVERED → rider collects cash → LOGISTIC remits → ZOZI TREASURY → SUPPLIER payout (− commission)
CARD:  Gateway → ZOZI TREASURY → ├─ SUPPLIER payout (− commission)   └─ LOGISTIC delivery fee
```

---

## 3. STEP-BY-STEP CONSTRUCTION POINTS

**Step 1 — Schema & state machine.** Alembic migration (with downgrade + contract test) creating `packages`, `shipments`, `shipment_events` (monthly-partitioned), `proof_of_delivery`, `return_requests`, `order_status_rules`; add `country_code`+RLS + audit mixins; seed the transition matrix as config data. *Done when:* illegal transition rejected in test; drift gate green.

**Step 2 — Placement, location & QR.** Order creation writes `delivery_lat/lng` (GPS + IP-geo sidecar; explicit manual-pin mode on failure); generate signed QR token + `/orders/{id}/label` payload endpoint (all print fields). *Done when:* label renders with QR + COD amount; scan token resolves server-side with role/status checks.

**Step 3 — Supplier workflow.** Order queue → accept (`PROCESSING`) → pack → **Print Parcel Sheet** button → upload packed photo (bytes→R2) → `PREPARED` + outbox event. *Done when:* photo missing blocks `PREPARED` with explicit error.

**Step 4 — Logistic claim & handover.** Flashing pick-up board for all partners at `PREPARED`; claim → `PICKING UP` (row-level visibility filter hides from others); claim-cancel returns to `PREPARED`; Path A QR scan + Path B request/confirm → `PICKED FROM SUPPLIER` (idempotent, double-scan rejected). *Done when:* visibility assertions pass.

**Step 5 — Transit & exceptions.** Transit sub-statuses with GPS trail; DELAYED/RESCHEDULED/FAILED; FAILED enforces return-to-supplier before `SHIPMENT CANCELLED`; door-reject → `SHIPMENT RETURNED`. *Done when:* each exception path leaves a full audited trail.

**Step 6 — Delivery proof.** In-app e-signature capture (PNG→R2) or customer confirm request → `DELIVERED` + `proof_of_delivery` row + COD flag for reconciliation. *Done when:* both paths produce POD record.

**Step 7 — Returns/replacements & money.** RMA flow → reverse shipment → inspection → ledger-only refund or linked replacement order; wire reconciliation entries (COD & Card paths) + nightly variance cron. *Done when:* COD run reconciles Order→Logistic→Treasury→Supplier with zero variance.

**Step 8 — Admin controls & panels.** Status-override + cancel-with-reason (audit + notify); disputes/communication/command-center merges; finance/treasury/commission wiring; build timeline/boards/scan/signature/print UIs in **web_app and mobile_app** with loading + empty + explicit-error states. *Done when:* parity check web vs mobile passes.

**Step 9 — E2E test & close-out.** Run the full §1.9 matrix (golden + all exception paths + no-fallback checks) on clean Postgres via Alembic; load-test hot lists (p95 < 300ms); then update `CODEBASE_STATUS_MATRIX_DETAILED.md` section-by-section. *Done when:* every row green and matrix committed.

> **AI Directive:** build strictly in this order; any request that bypasses the state machine, skips proof artifacts, stores media bytes in the DB, or adds a silent fallback MUST be refused and corrected per this spec and Appendix A of `01_DATABASE.md`.

# _____________________________________________________________________________________________ Order System

# _____________________________________________________________________________________________ products/xxxx : product page layout of web_app
### products/xxxx : product page layout of web_app:
		• **Top navigation bar** - Zozi logo, search, and user account icons
		• **Left sidebar** - "All photos" thumbnail gallery for product images
		• **Main product image** - Large centered photo display area with zoom capability
		• **Product details section** (top right) - Title "Designer Watch", star rating (4.8), price (Rs 37,844.83 with 29% discount), supplier description, quantity selector, and green "Add to Cart" button
		• **Supplier Details** (middle right) - Information about the seller with member since date and approval status
		• **Review section** (bottom left) - "Type your review" input area for customers
		• **Public reviews** (bottom right) - Shows "(0)" indicating no reviews yet
		• **Right sidebar** - "You may also like" product recommendations
		• **Bottom chat button** - Yellow floating chat support button

# _____________________________________________________________________________________________ products/xxxx : product page layout of web_app

# _____________________________________________________________________________________________ Admin Finance ERP System
### Admin Panel -> Finance Page:
	Read in detail backend and frontend in detail for the improvement and enhancement of http://localhost:3000/admin/finance.
	1. The Feature and tab needs to be modify and extent to actual and complete EPR level of Chart of Account, Payments, Other Sales, expenses, receivable, payeble, and etc. we have very basic system right now which needs more enhanced system.
	2. Put more automations to handle the large oraganization, like scanning the bills and record into expense,auto  bank reconciliation, Mapping System, and etc
	3. Make a dynamic Frontend System of Finance according to complete Accounts and Finance Management.
	4. Keep in mind System is running very slow, so write & modify the code to make it faster to handle 1000s of users at a time.
	5. Do the sample transaction.
	6. for admin keep the CRUD operations and admin can allow the access to any employee or sub-admin
	7. DO the complete audit of the system and according to you add more feature and finance related fucntions and tab and functionality.
	8. test each and everything in detail.

	---


For **ZoZI**, I would avoid building a full ERP like SAP or Oracle at the beginning. Build a **marketplace finance engine** that can later expand into a complete accounting system.

---

	# Accounts & Finance Roadmap

	## Phase 1 – Core Accounting

	* [ ] Chart of Accounts (COA)
	* [ ] Account Groups
	* [ ] Fiscal Year
	* [ ] Accounting Periods
	* [ ] Journal Entries
	* [ ] General Ledger (GL)
	* [ ] Trial Balance
	* [ ] Balance Sheet
	* [ ] Income Statement
	* [ ] Cash Flow Statement

	---

	## Phase 2 – Treasury & Banking

	* [ ] Bank Accounts
	* [ ] Cash Accounts
	* [ ] Bank Transactions
	* [ ] Bank Reconciliation
	* [ ] Payment Methods
	* [ ] Payment Gateway Transactions
	* [ ] Payment Gateway Reconciliation

	---

	## Phase 3 – Marketplace Finance

	* [ ] Commission Engine
	* [ ] Commission Rules
	* [ ] Supplier Settlement
	* [ ] Supplier Payout
	* [ ] Customer Refund
	* [ ] Refund Reconciliation
	* [ ] COD Reconciliation
	* [ ] Logistics Settlement
	* [ ] Platform Revenue Ledger

	---

	## Phase 4 – Receivables & Payables

	* [ ] Accounts Receivable (AR)
	* [ ] Customer Receipts
	* [ ] Accounts Payable (AP)
	* [ ] Supplier Payments
	* [ ] Outstanding Balance
	* [ ] Aging Reports

	---

	## Phase 5 – Expense Management

	* [ ] Expense Categories
	* [ ] Expense Entry
	* [ ] Expense Approval
	* [ ] Recurring Expenses
	* [ ] Employee Reimbursement

	---

	## Phase 6 – Tax

	* [ ] Tax Configuration
	* [ ] Tax Rates
	* [ ] Tax Calculation
	* [ ] Tax Ledger
	* [ ] Tax Reports

	---

	## Phase 7 – Budgeting

	* [ ] Annual Budget
	* [ ] Department Budget
	* [ ] Budget vs Actual
	* [ ] Forecast

	---

	## Phase 8 – Fixed Assets

	* [ ] Asset Register
	* [ ] Asset Categories
	* [ ] Asset Depreciation
	* [ ] Asset Disposal

	---

	## Phase 9 – Financial Reports

	* [ ] Profit & Loss
	* [ ] Balance Sheet
	* [ ] Cash Flow
	* [ ] Trial Balance
	* [ ] General Ledger
	* [ ] Journal Report
	* [ ] Supplier Statement
	* [ ] Customer Statement
	* [ ] Bank Statement
	* [ ] Commission Report

	---

	## Phase 10 – Audit & Compliance

	* [ ] Audit Log
	* [ ] Approval Workflow
	* [ ] Document Attachment
	* [ ] Financial Notes
	* [ ] Year-End Closing
	* [ ] Period Lock

	---

	# Marketplace-Specific Modules (Highest Priority)

	* [ ] Commission Engine
	* [ ] Settlement Engine
	* [ ] Payout Engine
	* [ ] Refund Engine
	* [ ] COD Engine
	* [ ] Wallet/Ledger Engine (if introduced)
	* [ ] Revenue Recognition
	* [ ] Chargeback Management
	* [ ] Payment Failure Handling

	---

	# Automation

	* [ ] Auto Journal Posting
	* [ ] Auto Commission Calculation
	* [ ] Auto Supplier Settlement
	* [ ] Auto Payout Generation
	* [ ] Auto Refund Posting
	* [ ] Auto Tax Calculation
	* [ ] Auto Bank Reconciliation
	* [ ] Auto Financial Reports
	* [ ] Scheduled Month-End Closing

	---

	# Nice-to-Have (Future)

	* [ ] Multi-Currency Accounting
	* [ ] Inter-Country Consolidation
	* [ ] Cost Centers
	* [ ] Profit Centers
	* [ ] Project Accounting
	* [ ] Loan Management
	* [ ] Investor Capital Ledger
	* [ ] Financial KPI Dashboard
	* [ ] AI Financial Insights
	* [ ] AI Anomaly Detection

	## My Recommendation

	Before adding more finance features, ensure these **10 core engines** are complete and robust:

	1. ✅ Chart of Accounts (COA)
	2. ✅ General Ledger (GL)
	3. ✅ Journal Engine
	4. ✅ Commission Engine
	5. ✅ Settlement Engine
	6. ✅ Payout Engine
	7. ✅ Bank Reconciliation Engine
	8. ✅ Tax Engine
	9. ✅ Financial Reporting Engine
	10. ✅ Audit & Period Closing Engine

	These provide a solid accounting foundation for ZoZI while remaining scalable as the platform grows into a multi-country marketplace.




# _____________________________________________________________________________________________ Admin Finance ERP System

# _____________________________________________________________________________________________ [ADMIN FINANCE & TEASURY SYSTEM ERP]

## ZOZI FINANCE · TREASURY · AUTOMATION — MASTER BUILD SPEC

> Binding addendum to `01_DATABASE.md` (finance domain → future `03_FINANCE.md`). All rules below inherit the constitution: **Alembic-only schema changes, event-driven writes, AI outputs staged → explicit commit (ADR-007), config-as-data, RLS `country_code`, media bytes in R2, immutable ledger, no silent fallbacks.**

---

## 1. BULLET POINTS — EXTRACTED + ENHANCED

### 1.1 Non-negotiable mandates
- **Event-based double-entry truth:** never `UPDATE` a balance column; balances = sums of immutable `journal_entry_lines`; `SUM(Dr) == SUM(Cr)` enforced at DB level (trigger + service check); posted entries immutable; reversals only via counter-entries.
- **Money math:** Python `Decimal` + Postgres `NUMERIC(16,4)` everywhere; **no floats** (Penny-Rounding law).
- **Event-driven ledger:** Orders/Logistics/Payments publish outbox events (`OrderDelivered`, `RefundApproved`…); only `TreasuryService`/`GeneralLedgerService` write to the GL (ADR-006/014).
- **75% zero-touch automation:** routines auto-run; humans work only the **Exception Queue**.
- **Triple-Verification for every auto-post:** ① rule/logic match ② AI confidence ≥ 95% (threshold config-driven) ③ GL/sub-ledger cross-reference; any fail → Exception Queue, never a guess.
- **Maker-Checker:** manual journals & payout batches live in `pending_journal_entries`/`payout_batches(draft)` until a *second, distinct* user with approve rights posts; checker ≠ maker enforced.
- **Period-close locking:** `fiscal_periods.is_closed` rejects back-dated postings at DB level.
- **Shadow-mode cutover:** new ledger runs parallel to legacy `wallet_balance`; nightly drift cron; cutover only at 0 variance; legacy killed after.
- **Orphan Detector cron (03:00):** any `delivered/paid` order or payout without a journal entry → Critical alert to Finance Command Center.
- **(ADDED) Automation staging law:** every AI/OCR/parsed result lands in a staging table first and is committed explicitly — auto-post *is* the commit step, logged as `actor=system:<automation>` in `finance_audit_logs`.
- **(ADDED) Idempotency law:** every automation run/line carries an idempotency key (`inbox_events`), e.g. `bankrec:{import_id}:{line_id}` — retries can never double-post.
- **(ADDED) Kill-switch law:** each automation has an independent pause toggle; paused/failed states show explicit badges — never silent stoppage (Rule #16).

### 1.2 Four-tier data architecture (schema)
- **Tier 1 CoA:** `account_groups` (1000–6000 hierarchy) · `accounts` (code, `normal_side`, currency) · `account_balances` (locked materialized cache).
- **Tier 2 Immutable Ledger:** `journal_entries` (header: date, `reference_type/id`, currency, fx_rate, status draft/posted/reversed) · `journal_entry_lines` (account, side, amount>0, cost-center, entity) · `pending_journal_entries` · `fiscal_periods`.
- **Tier 3 Treasury:** `treasury_accounts` (buckets: `cash_operating`, `cash_gateway_settlement`, `reserve_supplier_payable`, `reserve_logistics_payable`, `reserve_refund`, `reserve_vat`, `reserve_commission`, `receivable_customer`) · `treasury_transactions` · `cash_position_snapshots` · `gateway_settlement_schedules` (T+2/T+7) · `cash_flow_forecasts` · `exchange_rates`.
- **Tier 4 Sub-ledgers & Automation:** `ar_invoices`/`ar_ledger_entries` · `ap_bills`/`ap_ledger_entries` · `commission_ledger_entries` · `payout_rules/batches/batch_items/payouts` · `bank_statement_imports/lines` · `bank_mapping_rules` · `scanned_expenses` · `accruals` · `vat_remittances` · `fixed_assets` · `finance_audit_logs` · **(ADDED)** `automation_runs`, `exception_queue`, `report_definitions`, `purchase_orders/grn/landed_costs`, `loans/investments/schedules`.
- GCC CoA seeded idempotently (1010 Cash Op · 1020 Gateway Clearing · 1030 COD Receivable · 2010 Supplier Payables · 2020 Logistics Payables · 2040 VAT Payable · 2060 Deferred Revenue · 4010 Commission Revenue · 6010 Gateway Fees …); **GMV ≠ revenue** — only commission/markups/SaaS are revenue.

### 1.3 Double-entry matrix (auto-posted per event)
| Event | Debit | Credit |
|---|---|---|
| Card payment | 1020 Gateway Clearing | 2060 Deferred Revenue |
| Gateway settles | 1010 Cash Op + 6010 Gateway Fee | 1020 Clearing |
| Delivered (card) | 2060 Deferred Rev | 2010 Supplier Pay + 2020 Logistics Pay + 4010 Commission Rev + 2040 VAT |
| Delivered (COD) | 1030 COD Receivable | same 4-way split |
| Logistics remits COD | 1010 Cash Op | 1030 COD Receivable |
| Supplier payout | 2010 Supplier Pay | 1010 Cash Op |
| Refund | Rev/Deferred + payables reversed | 1010/1020 cash out |
| Month-end FX reval | 6060 FX Loss (or reverse) | FX asset/AR/AP accounts |

### 1.4 Treasury engine
- Real-time cash position (event-refreshed `account_balances` + snapshots EOD/hourly); **Free Cash = cash − reserves** (VAT/supplier/refund reserves can never be spent accidentally).
- Gateway settlement tracking (webhook + CSV auto-match vs `1020`), COD remittance engine vs `1030`, reserve transfers (Maker-Checker), 30/60/90 cash-flow forecast (ML over open AR/AP + payout schedules + historical refund rate), month-end FX revaluation auto-posts.

### 1.5 🤖 THE AUTOMATION SYSTEM (detail — the core ask)
| # | Automation | Trigger | Staging target | Auto-post condition | Exception path |
|---|---|---|---|---|---|
| 1 | **OCR expense & asset capture** (auto-expense) | camera/upload/`finance@` email; bytes→R2 | `scanned_expenses` (vendor, date, amount, VAT, per-field confidence) + pgvector embed | conf ≥95% **+ duplicate check (hash+vendor+amount+date)** + ≤ auto-limit → drafts AP bill *or* `fixed_assets` card | split-screen review (original vs fields) |
| 2 | **Email-to-Ledger inbox** | IMAP watcher on `finance@zozi.com` | `scanned_expenses` / `gateway_settlement_schedules` | template/vendor match ≥95% | queue; original email kept as immutable artifact |
| 3 | **Auto bank reconciliation** | statement CSV/API upload (daily) | `bank_statement_lines` | amount exact + ref match + date ±3d (configurable) + conf ≥95% → `is_reconciled` | split-screen match UI, bulk resolve |
| 4 | **Auto supplier payouts (scheduler)** | nightly cron 02:00 | `payout_batches(draft)` from `commission_ledger_entries` + `payout_rules` | generation is auto; **dispatch always Maker-Checker**; supplier gets secure SMS/email pre-review link | payout exception list (mismatched balances, KYC holds) |
| 5 | **Auto-accrual & reversal** | month-end 23:59 / day-1 cron | `accruals` | rule-based (no AI gate) | review list |
| 6 | **Depreciation run** | monthly cron | draft JEs from `fixed_assets` (straight-line/declining; disposal gain/loss) | schedule config valid | asset exception list |
| 7 | **FX revaluation** | month-end cron | draft JEs | rate source present (timestamped `exchange_rates`) | manual rate entry screen |
| 8 | **VAT remittance** | continuous aggregation + month-end | `vat_remittances` (output−input) | arithmetic exact | ZATCA/FTA CSV export wizard + review |
| 9 | **Orphan detector** | daily 03:00 | alerts only | n/a | Critical alert, Command Center |
| 10 | **Voice-to-text finance ops** | mic (admin web/mobile) → Whisper STT (EN `phi3`/AR `qwen2.5`) | intent draft card | **never auto-posts** — confirm card → maker-checker if posting | explicit "STT unavailable" mode, manual entry |
| 11 | **Finance chatbot (vectorized)** | NL query; RAG over CoA+ledger+docs via `ai_embeddings` (pgvector) | `ai_staging_journals` | user taps **Confirm** (+checker above threshold) | explicit "cannot verify" answer, cites sources |
| 12 | **Import & Purchase automation** | PO/GRN/vendor-invoice events | `ap_bills(draft)` | **3-way match** PO↔GRN↔Invoice within tolerance + **landed-cost auto-allocation** (customs/freight/insurance → asset/COGS value) | match-exception queue |
| 13 | **Loans & Investments** | wizard field-selection (principal, rate, term, method) | `schedules` (effective-interest amortization / valuation) | schedule cron posts interest/valuation JEs | manual review list |
| 14 | **Wholesale / B2B revenue** | bulk-order dispatch on terms | `ar_invoices` + `ar_ledger_entries` (net-30, credit limits, IFRS-15 deferred amortization) | credit check passes | credit-hold queue + **auto dunning cadence** (emails day 3/7/14, late-fee per config) |

**Automation governance (ADDED hardening):** `configuration.automation_rules` holds every threshold (confidence %, auto-post caps, date variance, 3-way-match tolerance, dunning cadence) — editable in UI, versioned, audited; `automation_runs` logs each run (job, started, status, posted/exception counts, error) powering the Control Tower; DLQ via `event_dead_letter`; local Ollama `moondream` for vision when available, explicit degraded-queue mode when not (ADR-015, Rule #16).

### 1.6 Security · RBAC · Performance · Testing
- Granular perms (`finance.ap.post`, `finance.ledger.approve`, `finance.reconciliation`…) via `require_finance_permission`; delegated roles (AP Clerk / Treasury Analyst); append-only `finance_audit_logs` (actor incl. `system:*`, old/new JSON, IP).
- N+1 eradication (`selectinload/joinedload`); composite indexes `(country_code, created_at)`, `(status, due_date)`, `(entity_type, entity_id)`; dashboards/reports served from **materialized views + read replicas**; cursor pagination; Decimal-only.
- Tests: **Chaos Monkey** (1000 checkouts + 500 payouts, zero deadlocks, Dr==Cr), **Penny Rounding**, **Time-Travel Audit** (replay journals to reconstruct any past date), **malformed-automation tests** (bad CSV/OCR → Exception Queue, never crash), E2E Playwright (CSV→AI map→draft→approve→trial balance), k6 load.

---

## 2. DIAGRAMS

### 2.1 Master automation & ledger pipeline
```mermaid
flowchart TB
subgraph SRC["📥 SOURCES"]
  O["Order/Logistics/Refund<br/>outbox events"]
  BK["Bank statements CSV/API"]
  EM["finance@ inbox PDFs/CSVs"]
  OC["OCR scans: receipts·bills·asset invoices"]
  VC["Voice commands"]
  CH["Chatbot NL requests"]
  PU["Purchase/Import: PO·GRN·customs"]
end
subgraph AI["🤖 INGEST + AI STAGING (ADR-007)"]
  P["Parsers: OCR·Whisper·NLP·fuzzy·pgvector embed"]
  S["Staging: scanned_expenses·bank_statement_lines·<br/>ai_staging_journals·ap drafts·schedules"]
  TV["TRIPLE-VERIFY: ① rules ② conf≥95% ③ GL cross-ref<br/>+ duplicate & idempotency checks"]
end
SRC --> P --> S --> TV
TV -->|PASS| POST["TreasuryService AUTO-POST<br/>(immutable, Dr==Cr, NUMERIC)"]
TV -->|FAIL/LOW-CONF| EQ["EXCEPTION QUEUE<br/>split-screen human review"]
EQ -->|approve/edit| POST
POST --> GL[("journal_entries/lines<br/>+ account_balances(locked)")]
GL --> TR["Treasury buckets·snapshots·forecasts"]
GL --> SUB["AR·AP·Commission·VAT sub-ledgers"]
TR --> SCH["SCHEDULERS: payouts·accruals·depreciation·<br/>FX·VAT·dunning·orphan-detector"]
SCH --> PAY["Maker-Checker → Supplier/Logistics payouts"]
GL --> REP["Report builder·mat-views·dashboards"]
SCH & EQ --> TWR["AUTOMATION CONTROL TOWER<br/>toggles·thresholds·runs·DLQ"]
```

### 2.2 Money circuit (order → treasury → payout; same circuit as Order Tracker)
```mermaid
flowchart LR
  ORD["Order placed"] -->|Card| GW["Dr 1020 / Cr 2060"]
  GW -->|T+2/T+7 auto-match| CASH["Dr 1010 + 6010 fee / Cr 1020"]
  ORD -->|COD| DEL
  GW --> DEL
  DEL["DELIVERED (QR/e-sig proof)"] --> SPLIT["Dr 2060 → Cr 2010 Supplier<br/>Cr 2020 Logistics · Cr 4010 Commission · Cr 2040 VAT"]
  ORD2["Rider collects COD → Dr 1030"] -->|reittance auto-rec| CASH
  SPLIT --> BAT["Nightly auto payout_batches"]
  BAT --> MC["Maker-Checker + supplier pre-review"]
  MC --> OUT["Dr 2010 / Cr 1010 → Supplier paid"]
  SPLIT --> VATR["VAT reserve → monthly ZATCA/FTA export"]
```

### 2.3 Automation item lifecycle
```mermaid
stateDiagram-v2
    [*] --> INGESTED : doc/statement/voice/email/PO received (bytes→R2)
    INGESTED --> PARSED : OCR/NLP/fuzzy + pgvector embed
    PARSED --> VERIFIED : triple-verification + dup/idempotency
    VERIFIED --> AUTO_POSTED : conf≥95% & within config limits
    VERIFIED --> EXCEPTION : low conf / dup / mismatch
    EXCEPTION --> POSTED : human approve/edit (audited)
    EXCEPTION --> REJECTED : human reject (reason logged)
    AUTO_POSTED --> [*]
    POSTED --> [*]
    REJECTED --> [*]
```

---

## 3. STEP-BY-STEP CONSTRUCTION

**Phase 0 — Governance.** Freeze mandates §1.1; define RBAC matrix; create `configuration.automation_rules` + `automation_runs` + `exception_queue` designs. *Done when:* thresholds & roles signed off (ADR log updated).

**Phase 1 — Schema & seeds.** One Alembic migration set (downgrade + contract tests) for the 4 tiers + automation tables; immutable-ledger DB trigger; seed GCC CoA, treasury buckets, fiscal periods. *Done when:* drift gate green; trial-balance endpoint returns seeded zeros balanced.

**Phase 2 — Core engines.** `GeneralLedgerService.post_journal_entry()` (Dr==Cr abort, `SELECT … FOR UPDATE` on `account_balances`) + `TreasuryService` (position, snapshots, forecasts, settlements). *Done when:* Penny-Rounding + Time-Travel unit tests pass.

**Phase 3 — Shadow mode & cutover.** Inject GL into payments/orders/payouts controllers in shadow; nightly drift cron legacy-vs-ledger; at 0 variance kill legacy wallet writes; wire gateway webhook auto-match + COD remittance engine. *Done when:* 7 clean drift-free nights.

**Phase 4 — Automation Wave 1 (documents & money-in).** OCR auto-expense/asset pipeline; Email-to-Ledger; auto bank rec; orphan detector. *Done when:* malformed-file tests land 100% in Exception Queue; ≥95%-conf fixtures auto-post.

**Phase 5 — Automation Wave 2 (schedulers).** Nightly payout batch generator + supplier pre-review links + Maker-Checker dispatch; accrual/reversal; depreciation; FX reval; VAT aggregation/export; dunning cadence. *Done when:* one full simulated month closes with zero manual routine posts.

**Phase 6 — Voice & chatbot.** Whisper STT service + intent parser (confirm-gated); RAG chatbot over CoA/ledger/docs with draft-journal cards. *Done when:* voice→draft→approve E2E passes; degraded-mode test shows explicit errors only.

**Phase 7 — Advanced ERP modules.** AR/AP aging + approvals; Import & Purchase 3-way match + landed cost; Loans & Investments wizards + schedule crons; Wholesale/B2B credit, AR invoicing, IFRS-15 recognition. *Done when:* 3-way-match tolerance tests + amortization math tests pass.

**Phase 8 — Report builder & analytics.** `report_definitions` (JSONB fields/filters/group-by) + preview + save + scheduled email/CSV/PDF; heavy reports on materialized views/read replicas. *Done when:* admin builds, saves, schedules a custom P&L-by-cost-center with no code.

**Phase 9 — Command Center UI (web + mobile parity).** Build per §4; lazy-loaded routes; skeletons; WS live ticks. *Done when:* Playwright E2E full lifecycle green on both apps.

**Phase 10 — Hardening & close-out.** Chaos Monkey, load (k6), security (RLS fail-closed per country), restore drills; update `CODEBASE_STATUS_MATRIX_DETAILED.md` section-by-section. *Done when:* all gates green + sign-off.

---

## 4. UI/UX LAYOUT — FINANCE COMMAND CENTER

### 4.1 Route-driven sidebar (`/admin/finance?section=…`, lazy-loaded)
```
📊 Command Center (dashboard+analytics merged)   🏦 Treasury (cash·banks·reconciliation·gateway)
📒 Ledger (CoA tree·journals·trial balance·pending)  🤝 Settlements (commissions·payouts·COD·refunds)
💰 Receivables (invoices·receipts·aging·dunning)     🏗 Purchasing (PO·GRN·imports·landed cost)
🏢 Payables (bills·payments·aging·OCR dropzone)      🏛 Assets & Capital (fixed assets·loans·investments)
🧾 Tax & Compliance (VAT·WHT·period close)           📑 Reports (builder·saved·scheduled)
🤖 Automation Tower (controls·exception queue·audit)
```
**Topbar:** global hybrid search (FTS+vector) · 🎙 voice · 🤖 chatbot drawer · country switcher (RLS) · 🔔 exception-count bell.

### 4.2 Key screens
- **Dashboard:** KPI card row (Free Cash, Locked Reserves, MTD Net Revenue, Pending Payouts, VAT Due, Exceptions) with skeleton loaders + sparklines; 30/60/90 cash-flow chart; AP/AR aging bars; live GMV tick (WS).
- **Exception Queue (the human inbox):** left = prioritized list (source icon, confidence chip, amount); right = **split-screen**: original PDF/image (R2 viewer) | extracted fields (per-field confidence) | suggested GL lines; actions Approve / Edit / Reject (reason) with keyboard shortcuts; bulk-resolve.
- **OCR Dropzone (Payables + mobile camera):** drag-drop → side-by-side original vs extracted → "Post to AP" / "Register Asset"; duplicate-invoice warning banner.
- **Reconciliation (Treasury):** bank line left ↔ suggested GL matches right with confidence chips; auto-match toggle + threshold slider; one-click & bulk reconcile; exception filter.
- **Payout Control Room (Settlements):** batch pipeline chips `draft→pending→approved→dispatched→settled`; maker notes; **Approve disabled for the maker**; dispatch → bank API/CSV; supplier pre-review status column.
- **Report Builder:** drag fields (CoA ranges, dimensions: country/supplier/cost-center/period) + filter builder + group-by → live preview grid → Save / Schedule (daily/weekly/monthly email) / Export CSV·PDF.
- **Automation Control Tower:** card per automation (OCR, bank-rec, payouts, accruals, depreciation, FX, VAT, dunning, orphan, voice, chatbot) with ON/OFF toggle, cron, last-run, posted/exception counters, threshold sliders, "View DLQ"; paused = explicit badge.
- **Chatbot drawer & Voice chip:** suggested prompts ("Why did VAT jump?", "Draft rent accrual"); every actionable answer is a **confirm card** (→ maker-checker above limits); transcript chip editable before intent parse.
- **UX principles:** sub-200ms first paint via materialized views + server components; tabular numerals; sticky headers; ARIA + keyboard nav; empty/loading/error states never silent zeros; mobile app = supplier invoice submit, logistics remittance upload, approver push-approvals, camera OCR.

> **AI Directive:** implement in Phase order; any automation that posts without staging+triple-verify, any balance `UPDATE`, any float math, or any silent fallback violates this spec and Appendix A — STOP and ask.

# _____________________________________________________________________________________________ [ADMIN FINANCE & TEASURY SYSTEM ERP]

# _____________________________________________________________________________________________ [EMPLOYEES & Hr SYSTEM]

## ZOZI EMPLOYEE MANAGEMENT SYSTEM (EMS) + COMMUNICATION SUITE — MASTER BUILD SPEC

> Binding addendum to `01_DATABASE.md` (hr + comms schemas → future `05_HR.md` / `06_COMMUNICATION.md`). Inherits the constitution: **RLS `country_code` on every hr/comms row, Alembic-only migrations, event-driven cross-domain writes (outbox), media bytes in R2, append-only audit, Maker-Checker on money & permissions, config-as-data, AI staged→committed, no silent fallbacks.** Strategy: **complete + wire + govern the ~70% existing skeleton; do not rebuild.**

---

## 1. BULLET POINTS — EXTRACTED + ENHANCED

### 1.1 Core mandates
- **One Identity, Many Doors:** single `users`+`employees` identity across password/TOTP, phone-OTP, biometric, QR-kiosk, SSO — same permissions everywhere.
- **Hierarchy = Authority = Permission:** org chart *drives* approvals (leave, expense, payroll, handover) via `reporting_manager_id` + `authority_level`; not cosmetic.
- **Country isolation by default:** RLS context set at login; Oman manager never sees KSA staff; only `global/admin` see consolidated.
- **Internal-first communication:** resolve recipients in-org first (in-DB delivery); only explicit external addresses hit SMTP.
- **Performance feeds payroll:** KPI/OKR → bonus multiplier in auto-disbursement; zero spreadsheet math.
- **(ADDED) Escalation SLA law:** any approval (leave/expense/access/payroll) unactioned > config hours auto-escalates to next `authority_level` — no silent stalls.
- **(ADDED) Automation governance:** every auto-action logged as `actor=system:<job>` in `employee_activity_logs`/audit; thresholds in `configuration` tables; runs in `automation_runs`; failures → explicit Exception Queue (Rule #16).

### 1.2 Unified login & session security (5 doors)
- **D1** Email/password + TOTP (`users.totp_secret`); **D2** SMS/WhatsApp OTP short-lived token; **D3** biometric (`employee_biometrics.fingerprint_hash/face_encoding`) only on `user_devices.is_trusted=True`, enrollment bootstrapped by password+OTP; **D4** QR kiosk: `dynamic_qr_sessions.qr_token` + expiry + `geo_fence_logs.is_within_fence` + optional liveness biometric vs buddy-punching → writes attendance *and* kiosk-scoped session (8h); **D5** SSO (Google/Apple/MS) mapping `sub`→email, auto-provision pre-registered employees.
- Every login writes `user_devices` (fingerprint, IP, OS); unknown device → force MFA/block; concurrent-session policy per role; refresh-token rotation (mobile 30d).
- On login: `SET app.current_country_code`; **risk score** (geo anomaly + new device + odd hour) > threshold → step-up MFA or lock + manager notify.
- **(ADDED)** device-fingerprint + face-liveness combo for buddy-punch detection; **(ADDED)** quarterly access-recertification campaign auto-revokes unconfirmed grants.

### 1.3 Hierarchy & RBAC
- `org_units` **materialized path** `/1/12/45/` + `parent_id`; solid line = `reporting_manager_id`; dotted line = `employee_relations(relation_type='matrix_manager')`; DB triggers block circular reporting & reporting to lower authority (unless matrix-flagged).
- Authority thresholds config-driven (e.g., expense > 500 OMR needs `authority_level ≥ 3`); services `get_org_chart / get_user_chain / get_all_subordinates / can_manage / reassign_manager / backfill_authority_levels` recomputed in one transaction on drag-reassign.
- **3-layer RBAC:** Global role JSON → Country role (`country_staff_assignments.role_in_country`) → Hierarchy-derived; resolver precedence **Country > Hierarchy > Global**, Redis-cached, invalidated on change; `require_permission("hr.payroll.release")` on every protected endpoint; Permission-Matrix UI with Maker-Checker for sensitive grants (`finance.*`, `users.delete`); sub-admins **cannot grant what they don't hold**; self-service access requests route up `can_manage()` chain.

### 1.4 Country-wise management & localization
- Country Staff Assignment console (multi-country regional roles + country switcher re-sets RLS); per-country: salary currency, leave allocations (`employee_leave_ledgers`), `country_holiday_calendars`, labor-law rules (notice, EOSB) from `country_configs`.

### 1.5 Lifecycle (onboarding ↔ offboarding)
- Onboarding pipeline with SLA per step: create user+employee → org/manager/role/country → documents → biometric enrollment → `employee_assets` → `physical_id_cards` → welcome email; probation auto-alerts 30/60/90; conversion requires check-in.
- Offboarding auto-run: revoke sessions + disable devices + reclaim assets + exit survey + transfer `shift_handover_tasks` + archive chat/email per retention (legal-hold override) + `employment_status='terminated'`; **(ADDED)** final EOSB settlement published as event → Treasury posts journal (no manual hand-off).

### 1.6 Time, attendance, leave, shifts
- Attendance via QR-kiosk/biometric/geo-fence; `is_anomaly` when Haversine > 50m or untrusted device → manager anomaly dashboard; shifts auto-rostered by rules; **handover gate:** outgoing staff must acknowledge `shift_handover_tasks` before clock-out; leave routed to manager, balances enforced vs ledger, country-specific types; `employee_work_logs` (hours+geo+approval) → utilization analytics.

### 1.7 Communication suite (chat · video · email) — complete the gaps
- **Chat:** 1:1 `direct_chat_rooms`, groups (roles, @mentions), Slack-style `internal_channels` (dept/country/project, public/private, pinned); **gap-fill:** `chat_attachments`→`media_assets` for image/video/document + **voice notes** (compressed .ogg/.m4a + duration + waveform JSON); realtime via `WebSocketManager` (typing, `chat_read_receipts`, presence); threading, edit/delete (audited), reactions, FTS search, forward, per-channel retention + legal-hold; every write → `communication_audit_trails`.
- **Video:** rooms + participants + recordings + watermark + boardroom mode + tokens; **gap-fill:** real-time Whisper transcription + AR/EN translation + `extract_action_items()` → **auto-create assigned tasks** (staged→confirm); recordings to **WORM/retention-locked object storage**.
- **Email:** `internal_emails` + `email_folders`; **smart router** (directory-first, in-DB instant delivery; external only via relay); threading, labels/rules, FTS; attachments with size limits + virus-scan hook; external controls: domain allow-lists, **DLP PII scan**, mandatory compliance BCC per role; **gap-fill missing endpoints** `POST /email/bulk`, `POST /email/from-alias`.
- **(ADDED)** auto-translate chat/channel messages AR↔EN; **(ADDED)** announcements with mandatory read-confirmation tracking; **(ADDED)** meeting-cost indicator (participants × duration × rate) to curb meeting bloat.

### 1.8 Activity ledger, compliance, analytics
- Append-only `employee_activity_logs` (actor, target, action, entity, country, metadata, ip, device) — logins, scans, handovers, mentions, shares, approvals, hierarchy moves, reviews; visibility: self / manager-subtree / HR-legal (gated + access-logged); eDiscovery export.
- COI engine auto-detects relative reporting lines / shared interests → review flags; document/certification expiry alerts + action blocks; disciplinary workflow with evidence; PDPL/GDPR: PII encrypted at rest, right-to-access/export packages, retention purge jobs with hold override.
- HR dashboards from **materialized views**: headcount by country/dept, attrition-risk model, DEI pay-equity, hiring velocity, leave burn rate, overtime cost; composite indexes `(country_code, employment_status)`, `(reporting_manager_id)`, `(org_unit_id)`.

### 1.9 Payroll & auto-disbursement (wired to Treasury)
- Auto-aggregate: base + attendance deductions + OT (work_logs) + approved expenses + per-diem + leave encashment + **KPI bonus multiplier** + statutory (tax/social/EOSB) with country rules from `country_configs`.
- Pipeline: draft `payout_batch` (line per employee → `employee_bank_accounts` IBAN/SWIFT) → **Maker (payroll mgr) ≠ Checker (finance controller)** → Treasury posts journal (Dr Salary Expense / Cr Bank + Payables + Tax Payable) → bank API/file → auto bank-recon + retry failed → payslip PDF → `employee_documents(type=payslip)` (owner + payroll admin only) → notify in-app/email/SMS; post-close immutability; corrections via next-period adjustments.

### 1.10 🤖 THE AUTOMATION SYSTEM (detail — the core ask)
| # | Automation | Trigger | Staging/Inputs | Auto action | Exception path |
|---|---|---|---|---|---|
| 1 | **Auto-onboarding** | offer accepted | pipeline steps w/ SLA | user+employee, org, role, country, docs request, biometric invite, assets, ID card, welcome mail, default channels | SLA breach → escalate to HR head |
| 2 | **Auto-attendance & anomaly** | kiosk/biometric/geo scan | haversine, device trust, scan pattern | check-in/out, late/OT compute | anomaly queue (buddy-punch, >50m, untrusted) → manager |
| 3 | **Auto-rostering & handover** | weekly cron + leave/skills | shift rules, certifications | publish rosters; block clock-out till handover acknowledged | coverage conflicts → scheduler UI |
| 4 | **Auto-leave processing** | request | ledger balance + country calendar + conflicts | auto-approve if ≤ threshold & no conflict; else route up; year-end carry-forward | abuse-pattern alerts → manager |
| 5 | **Auto-payroll & disbursement** | monthly cron | attendance/OT/expenses/KPI/deductions | draft batch → Maker-Checker → journal → bank → recon → payslips | salary-Δ > threshold / missing IBAN → hold queue |
| 6 | **Auto-performance signals** | nightly + cycle crons | operational KPIs (sales, tickets, on-time) via read-only | health score R/A/G; open 360 cycles; PIP trigger; bonus multiplier → payroll | calibration session UI |
| 7 | **Auto document/cert expiry** | daily scan | expiry_date | notify 30/14/7d; block dependent actions (e.g., shift w/o cert) | renewal escalation |
| 8 | **Auto-COI detection** | hierarchy/relations change | dependents + relations + interests graph | flag conflicting lines for review | compliance case |
| 9 | **Auto comms compliance** | message/email write | DLP rules, allow-lists, virus-scan | internal-first routing; block/quarantine external violations; auto legal-hold on case open; retention purge | DLP quarantine review |
| 10 | **Auto meeting intelligence** | recording end | Whisper transcript + translation | action items → staged tasks → confirm → assigned with due dates; RAG-index transcript | low-confidence items → review list |
| 11 | **HR chatbot + voice assistant** | NL/voice (Whisper) | handbook/policy RAG (pgvector) | answers + draft requests (leave, expense, 1:1) via confirm cards | explicit "cannot verify" mode |
| 12 | **Auto-offboarding & settlement** | termination event | asset/task/comms inventories | revoke all, transfer tasks, archive per policy, EOSB event → Treasury | unrecovered assets → case |
| 13 | **Auto access governance** | request + quarterly cron | permission catalog | route requests up chain; recertification campaign auto-revokes | manager review queue |
| 14 | **Auto HR analytics & attrition risk** | nightly | mat-views | R/A/G dashboards; attrition-risk alerts to managers | — |

### 1.15 Security · Performance · Testing
- MFA for privileged roles; device binding; immutable audit; PII encryption; WORM recordings; **(ADDED)** bank-detail change = verification freeze + penny-test before next payroll.
- `selectinload/joinedload`; mat-views for dashboards; heavy work (payslip PDF, bank files, transcoding, analytics) on Celery/Redis — never in request path.
- Acceptance = source "Definition of Done": biometric + kiosk login same identity/country scope; manager subtree approvals + health board; 1:1 chat with voice note + image realtime + channel broadcast; internal email never touches SMTP, external passes DLP; month-end payroll auto-aggregate → Maker-Checker → balanced journal → disbursed + reconciled; everything in activity ledger, RLS-isolated.

---

## 2. DIAGRAMS

### 2.1 Master EMS architecture
```mermaid
flowchart TB
subgraph ID["🔐 UNIFIED IDENTITY — 5 DOORS"]
  D1["Password+TOTP"] & D2["Phone OTP"] & D3["Biometric<br/>(trusted device)"] & D4["QR Kiosk<br/>+geo-fence"] & D5["SSO"]
end
ID --> SES["Session Engine: user_devices · risk-score → step-up MFA<br/>SET app.current_country_code (RLS)"]
SES --> RBAC["Permission Resolver: Country > Hierarchy > Global<br/>(Redis-cached · require_permission guards)"]
RBAC --> ORG
subgraph HR["🧩 HR MODULES (hr schema)"]
  ORG["Org Chart: path · solid/dotted · authority_level"]
  ATT["Attendance · Shifts · Handover · Leave"]
  LIFE["Onboarding ↔ Offboarding (SLA)"]
  PERF["OKR/KPI · 360° · Health Score · PIP"]
  PAY["Payroll auto-aggregate"]
end
ORG --> ATT
ORG --> PERF
PERF -->|bonus multiplier| PAY
subgraph COM["💬 COMMUNICATION SUITE (comms schema)"]
  CH["1:1·Groups·Channels + attachments/voice (R2)<br/>WS realtime · receipts · presence"]
  EM["Internal Email: internal-first router · DLP · allow-list"]
  VD["Video: tokens · watermark · WORM recording ·<br/>Whisper transcript → action-item tasks"]
end
HR --> EV[("outbox_events")]
COM --> EV
EV --> FIN["finance/treasury: payout_batch →<br/>double-entry journal → bank → auto-recon"]
EV --> AN["analytics mat-views: headcount · attrition ·<br/>OT cost · DEI · leave burn"]
HR & COM --> AL[("employee_activity_logs · append-only")]
```

### 2.2 Payroll auto-disbursement circuit
```mermaid
flowchart LR
  A["Nightly inputs: attendance · OT · expenses ·<br/>per-diem · KPI multiplier · statutory"] --> B["Draft payroll batch"]
  B --> C{"Anomaly gate:<br/>salary Δ > thr? IBAN missing?<br/>cert expired?"}
  C -->|clean| D["MAKER generates"]
  C -->|flag| E["Exception queue"] --> D
  D --> F["CHECKER approves (≠maker)"]
  F --> G["Treasury journal:<br/>Dr Salary Exp · Cr Bank/Payables/Tax"]
  G --> H["Bank dispatch · retry failed"]
  H --> I["Auto bank-recon"]
  G --> J["Payslip PDF → docs + notify"]
  I --> K["Period close → immutable"]
```

### 2.3 Employee lifecycle
```mermaid
stateDiagram-v2
    [*] --> ONBOARDING : offer accepted (auto pipeline)
    ONBOARDING --> PROBATION : steps complete, SLA met
    PROBATION --> ACTIVE : 90-day conversion + check-in
    PROBATION --> OFFBOARDING : failed conversion
    ACTIVE --> PIP : health score red (auto)
    PIP --> ACTIVE : improvement confirmed
    PIP --> OFFBOARDING : unresolved → disciplinary tie-in
    ACTIVE --> OFFBOARDING : resignation/termination
    OFFBOARDING --> ALUMNI : auto revoke + EOSB event → Treasury
    ALUMNI --> ACTIVE : boomerang re-hire (ADDED)
```

---

## 3. STEP-BY-STEP CONSTRUCTION

**Phase 0 — Schema alignment & gaps.** Alembic migration (downgrade + contract tests) for gap tables: `employee_bank_accounts`, `okr_objectives`, `kpi_metrics`, `performance_reviews`, `internal_emails`, `email_folders`, `chat_attachments`, `chat_read_receipts`, `employee_activity_logs`; move `employee_*`/`org_units`/`offices`→`hr`, channels/chats→`comms`; freeze `HR_PERMISSION_MAP`; verify RLS registry. *Done when:* drift gate green + orphan-table warning zero.

**Phase 1 — Identity.** `auth_service.py` 5 doors + device trust + risk scoring + RLS-on-login + kiosk attendance session. *Done when:* same person logs in via biometric (mobile) and QR-kiosk with correct country scope; unknown-device MFA test passes.

**Phase 2 — Org engine.** Materialized path + matrix relations + anti-cycle triggers + authority backfill; draggable Org Chart UI (single-transaction reassign). *Done when:* drag-reassign recomputes path/authority and approvals follow new chain.

**Phase 3 — RBAC.** Resolver + Redis cache + `require_permission` everywhere + Matrix UI + Maker-Checker sensitive grants + self-service requests + **(ADDED)** recertification campaign. *Done when:* sub-admin cannot grant beyond own set (test).

**Phase 4 — Country console.** Assignments, multi-country switcher, localization (currency/leave/holidays/EOSB from `country_configs`). *Done when:* cross-country read returns nothing without global role.

**Phase 5 — Lifecycle.** Onboarding SLA pipeline, probation alerts, offboarding auto-revoke + task transfer + EOSB event. *Done when:* offboarding completes with zero live sessions/devices.

**Phase 6 — Time & shifts.** Anomaly detection, auto-rostering, handover gate, leave auto-approve/route + escalation SLA. *Done when:* unactioned leave auto-escalates per config.

**Phase 7 — Communication completion.** Attachments + voice waveform, receipts/presence/typing WS, threading/reactions/FTS, retention + legal-hold; WORM recordings + realtime transcript + action-item tasks; internal email client + smart router + DLP + allow-list + BCC; add `POST /email/bulk`, `/email/from-alias`. *Done when:* 1:1 voice-note + image chat realtime E2E passes; external DLP block test passes.

**Phase 8 — Activity ledger & eDiscovery.** Append-only writer hooks across all modules; privacy-gated viewers; export. *Done when:* every Phase-1..7 action appears in ledger.

**Phase 9 — Performance.** OKR cascade, auto KPI pulls (read-only from commerce/logistics/support), 360 cycles, health score, calibration, PIP, bonus multiplier feed. *Done when:* health board matches computed signals in test fixtures.

**Phase 10 — Payroll.** Auto-aggregate → Maker-Checker → Treasury journal → bank → recon → payslips → notify; penny-test bank-change freeze. *Done when:* simulated month disburses with balanced journal + 0 recon variance.

**Phase 11 — ESS portal + mobile parity.** Self-service profile/docs/leave/expense/payslip/shift-swap/goals/LMS; kiosk mode; biometric login. *Done when:* web/mobile feature parity checklist green.

**Phase 12 — Automation Tower + assistants.** `automation_runs` + toggles + thresholds UI; HR chatbot + voice (confirm-gated); analytics mat-views + attrition alerts. *Done when:* each automation shows run health; paused = explicit badge.

**Phase 13 — Compliance & close-out.** COI flags, expiry blocks, GDPR/PDPL export, retention purges with holds; E2E Playwright full acceptance; k6 load; update `CODEBASE_STATUS_MATRIX_DETAILED.md`. *Done when:* all acceptance criteria (§1.15) green.

---

## 4. UI/UX LAYOUT

### 4.1 Employee Workspace (default landing)
```
┌─────────────────────────────────────────────────────────────────────────┐
│ TOPBAR: [🔍 people/search] [🎙 voice] [🤖 HR bot] [country: OM ▼] [🔔2] │
├──────────────┬──────────────────────────────────────────────────────────┤
│ SIDEBAR      │ MY DAY: shift card · handover tasks (ack gate) ·         │
│ My Workspace │ approvals due · announcements (read-confirm)             │
│ Org Chart    │ KPI STRIP: attendance · health R/A/G · leave balance ·   │
│ Directory    │ pending expenses                                         │
│ Attendance   │ ──────────────────────────────────────────────────────── │
│ Shifts/Leave │ QUICK ACTIONS: leave · expense · book room · start 1:1 · │
│ Payroll      │ payslip · shift-swap                                     │
│ Performance  │ ──────────────────────────────────────────────────────── │
│ Comms Hub    │ TEAM PULSE: calendar · birthdays · recognition badges    │
│ Compliance   │ CHAT DRAWER (right): DMs · channels · voice waveforms ·  │
│ Analytics    │ presence dots                                            │
│ Automation   │                                                          │
└──────────────┴──────────────────────────────────────────────────────────┘
```

### 4.2 Admin HR Command Center (route-driven tabs, lazy-loaded)
`directory · org-chart (draggable canvas, solid/dotted lines, authority badges) · attendance (anomaly queue split-screen: scan map+device vs policy) · shifts-handover · leave (auto-approve log + escalations) · payroll control room (batch pipeline chips, maker≠checker locks, exception holds) · performance (health board, calibration, PIP) · onboarding/offboarding pipelines (SLA timers) · documents-compliance (expiry radar 30/14/7) · coi-disciplinary · comms-hub (channels admin, eDiscovery portal, audit viewer, legal-hold controls) · analytics-DEI · permission-matrix (role×group grid, sensitive = Maker-Checker draft) · country-assignments · automation-tower (per-job toggle/cron/last-run/exception counters/DLQ)`.

### 4.3 Key screens
- **Chat:** 3-pane (rooms/channels | thread | details/members); voice-note inline waveform player; attachment lightbox; pinned + search; retention badge per channel.
- **Email client:** folders left, list, reading pane; compose with **directory-first autocomplete** + internal/external chip; DLP warning banner before external send; labels/rules builder.
- **Video:** calendar scheduler; join via token; live transcript panel (AR/EN toggle); action-items side panel with "assign" confirm; watermark/boardroom toggles; recording → WORM badge.
- **Org Chart:** drag-to-reassign with impact preview (subtree count, authority recompute) + single-transaction commit; matrix lines dashed.
- **Payroll Control Room:** batch list `draft→approved→dispatched→settled`; per-employee drilldown (inputs provenance: attendance/OT/KPI); approve disabled for maker.
- **UX principles:** skeleton loaders; explicit empty/error states; tabular numerals; ARIA + keyboard; density toggle; country switcher re-sets RLS; mobile = biometric login, kiosk, scan payslip, approvals push, camera expense/voice notes.

> **AI Directive:** build in Phase order on the existing skeleton; any cross-domain write bypassing outbox, any balance-style mutable HR money field, any attachment byte in DB, or any silent fallback violates this spec and Appendix A — STOP and ask.


# _____________________________________________________________________________________________ [EMPLOYEES & Hr SYSTEM]

# _____________________________________________________________________________________________ [ADVANCED FILTERS · AI SEARCH · VIDEO COMMERCE — MASTER BUILD SPEC]

## ZOZI DISCOVERY LAYER — ADVANCED FILTERS · AI SEARCH · VIDEO COMMERCE — MASTER BUILD SPEC

> Binding addendum to `01_DATABASE.md` (commerce/media/ai/analytics schemas → future `02_SEARCH.md`). Inherits the constitution: **hybrid search = FTS + pgvector + CLIP (ADR-013), JSONB variants + GIN (ADR-004), materialized-path categories (ADR-005), media bytes in R2 + CDN (ADR-010), snapshots/mat-views never live aggregates (ADR-008), AI staged→commit (ADR-007), RLS `country_code`, config-as-data, cursor pagination, p95 < 300ms, no silent fallbacks (`mode:"lexical"`).**

### 0. Corrections to the supplied draft (constitution alignment)
- **Elasticsearch ≠ source of truth:** Postgres-native hybrid (tsvector+GIN / pgvector HNSW / CLIP) is the engine; a dedicated OpenSearch cluster appears **only at the Massive scale stage** as an event-synced read-model (never a second truth).
- `OFFSET` pagination → **cursor pagination**; `float` prices → **NUMERIC/Decimal**; sync `views_count` UPDATE → **async batched counters** (Redis INCR → flush); live facet aggregates → **`mv_facet_counts` + Redis**; add `country_code`+RLS to every new table; processing on **Celery/ARQ**, never in request path.

---

## 1. BULLET POINTS — EXTRACTED + ENHANCED

### 1.1 Feature 1 — Advanced Faceted Filters (Amazon-style)
- **Config-driven facets:** `product_filter_metadata` (category_id, filter_name, type `range|multi_select|single_select|boolean`, display_order, is_active) + `product_filter_options` (value, display, count, sort) — per-category dynamic rails; editable in admin, versioned, audited.
- **Data columns:** `products.filter_attributes` **JSONB + GIN**; variant attrs JSONB + `variant_key`; generated `search_vector tsvector` + GIN; partial index `WHERE is_deleted=false AND is_active=true`; composite `(country_code, created_at)`, `(supplier_id, is_active)`.
- **Facet set:** price (min/max/avg + **histogram buckets (ADDED)**), brands w/ counts, rating distribution, dynamic attributes, availability, shipping options, country-aware promotions.
- **Disjunctive faceting (ADDED):** each facet's counts ignore its own selection so options never self-hide; zero-count options auto-hidden, trending options auto-promoted.
- **API:** `GET /search/filters?category_id&search_query` (counts respect active query) · `POST /search/advanced` (sorts: relevance/price↑↓/rating/newest) · **filter state URL-synced** for shareability + SEO (ADDED).
- **Frontend:** desktop left rail / mobile bottom-sheet; active-filter **chips + clear-all**; dual price slider over histogram; star "≥N & up"; skeleton loaders; result-count tick per toggle.

### 1.2 Feature 2 — Google-style AI Search
- **Query parser:** intent classification (`product | compare | recommendation | reviews`) + entity extraction ("under 100 OMR" → max_price, "4+ stars" → min_rating, brand dictionary, attribute:value pairs); parsed filters surface as **removable understanding chips** (ADDED).
- **Retrieval:** hybrid RRF fusion — lexical `tsvector` (boosts `name^3 brand^2 description^2 tags`, fuzziness AUTO) + semantic `pgvector` HNSW + CLIP image match; synonym expansion with decaying boost; **did-you-mean via `pg_trgm` (AR+EN) (ADDED)**.
- **Autocomplete & trending:** completion suggest + Redis sorted-set of popular queries + trigram fallback; trending from `search_events` with recency decay, **per country (RLS)**; voice input (Whisper) (ADDED).
- **AI NER:** local models (`qwen2.5` AR/EN, `phi3`) for brand/category/attribute; spaCy-style rules as fast path; **(ADDED) LLM fallback only with explicit confidence, else `mode:"lexical"` — never silent.**
- **Analytics loop:** every query/click/zero-result/abandon → outbox events → `search_analytics` snapshots; powers auto-tuning (§1.5).

### 1.3 Feature 3 — Video Commerce (row-first, hybrid desktop)
- **Schema:** `product_videos` (product_id, urls, thumbnail, duration, type `demo|unboxing|review|lifestyle`, title, views, is_featured, `upload_status pending|processing|ready|failed`) + batched `video_events` (view/complete/pause/skip, watch_duration, device) — **monthly partitioned (ADDED)**; `products.video_count`.
- **Processing (queue, never request path):** validate ≤100MB + mime; transcode H.264/AAC ≤720p crf23 faststart, trim ≤30s; **(ADDED) HLS adaptive renditions**; thumbs @10/50/90% + WebP poster; **Whisper captions AR/EN (accessibility condition)**; watermark; CDN publish; explicit `failed` + reason + retry/DLQ.
- **Placement verdict (adopted):** **mobile-first horizontal snap-row** after banner/search (GCC 85%+ mobile; native scroll; above fold; lazy-independent) + **desktop hybrid**: optional right rail (related videos · recently viewed · cross-sell) ≥1024px only.
- **Playback rules:** lazy via IntersectionObserver (`preload=none` + poster); auto-play **muted**, one-at-a-time; show 1.5 cards (scroll affordance); snap points; duration badge; tap→sound; **user disable toggle persisted**; **Save-Data/slow-conn → poster image fallback**; captions toggle; RTL-safe.
- **Recommendation strategy:** same product → same category/brand/tag-overlap → **(ADDED) pgvector video-embedding similarity + co-view graph + trending decay**, country-scoped; featured flag curated by merchandising automation.
- **Pros honored / cons mitigated:** engagement & conversion ↑ vs bandwidth/storage/load → CDN + lazy + short clips + HLS + disable + fallback (all conditions from analysis enforced as code rules).

### 1.4 🤖 AUTOMATION SYSTEM (detail — the core ask)
| # | Automation | Trigger | Staging/Inputs | Auto action | Exception path |
|---|---|---|---|---|---|
| 1 | **Auto catalog enrichment** | supplier upload | CLIP/moondream tags, alt-text, category suggest, attribute extraction, text+image embeddings | `ai_staging_products` → commit to `products/filter_attributes/embedding` | low-conf → merchandiser queue |
| 2 | **Auto facet/count refresh** | write events + cron 15min | product/stock/price events | invalidate Redis + refresh `mv_facet_counts`; hide zeros; promote trending options | variance alert |
| 3 | **Auto synonym & redirect mining** | nightly | zero-result + reformulated queries + search_events | draft synonyms/redirects; auto-apply ≥ conf threshold | review list |
| 4 | **Auto search-rank tuning** | nightly + A/B harness | CTR/abandon/conversion per query class | adjust boost weights **inside guarded bands**; flag regressions | rollback + alert |
| 5 | **Auto video pipeline** | upload | R2 original | transcode/thumbs/captions/watermark/CDN; status transitions; retry+DLQ | explicit `failed` + reason UI |
| 6 | **Auto video recs & trending** | events + cron | embeddings + co-view + watch-time | recency-decayed trending per country; personalized rail | cold-start → curated featured |
| 7 | **Auto merchandising** | schedules + CTR | banner calendar, row CTR | banner on/off; row re-rank; recently-viewed; cross-sell/upsell slots | manual override pin |
| 8 | **Auto accessibility & localization** | media commit | Whisper/CLIP outputs | captions, alt-text, AR translation (qwen2.5), RTL checks, did-you-mean AR | editor queue |
| 9 | **Auto integrity/spam guard** | event stream | view/review patterns | bot-view filtering, review spam, fake-engagement scrub, price/stock anomaly | exception queue |
| 10 | **Auto SEO** | product change | metadata | meta titles/descriptions, JSON-LD, sitemap + canonical filtered URLs | — |
| 11 | **Auto cache invalidation** | price/stock writes | events | Redis purge + stampede guards; warm top-N facet pages | explicit stale-badge if lag |
| 12 | **Auto KPI watchdog** | hourly | metrics snapshots | compare vs targets (filter use >40%, search success >85%, video engage >60%, load <3s, 3G <5s) → report/alert | regression ticket auto-created |

### 1.5 Scale ladder & testing
- MVP: FTS + GIN + Redis → Growth: mat-views + replica + PgBouncer → Scale: JSONB GIN + pgvector + partition `video_events` → Massive: country shard + dedicated search read-model.
- Tests: contract per migration; `EXPLAIN ANALYZE` CI gate on products/search queries; k6 hot-list p95 <300ms; A/B filter & video placements; Lighthouse + 3G throttle; accessibility audit (captions/ARIA/RTL); spam-fixture tests; update `CODEBASE_STATUS_MATRIX_DETAILED.md`.

---

## 2. DIAGRAMS

### 2.1 Discovery architecture (search + filters + learning loop)
```mermaid
flowchart TB
subgraph FE["🛍️ STOREFRONT web+mobile"]
  SB["Search bar: autocomplete · voice · trending"]
  FR["Filter rail/bottom-sheet · chips · URL-sync"]
  VR["Video snap-row · PDP rail"]
end
SB --> QP["Query Parser: intent · price/rating/brand ·<br/>synonyms · did-you-mean · understanding chips"]
QP --> HYB["HYBRID RETRIEVAL + RRF (boosts=config)"]
subgraph PG["PostgreSQL = SOURCE OF TRUTH (RLS per country)"]
  FTS["tsvector + GIN"]
  VEC["pgvector HNSW"]
  CLP["CLIP image embed"]
  JB["filter_attributes JSONB + GIN"]
  MV["mv_facet_counts · snapshots"]
end
HYB --> FTS
HYB --> VEC
HYB --> CLP
FR --> JB
FTS & VEC & CLP --> RRF["Fusion + intent-aware re-rank"]
RRF --> RES["Results + disjunctive facets (MV+Redis)"]
JB --> RES
MV --> RES
RES --> FE
FE --> EV[("search/video events → outbox (async)")]
EV --> AN["analytics: CTR · zero-results · watch-time"]
AN --> TUNE["AUTO-LOOP: synonyms · boosts ·<br/>trending · recs · merchandising"]
TUNE --> HYB
TUNE --> VR
```

### 2.2 Video pipeline & recommendation circuit
```mermaid
flowchart LR
  UP["Supplier upload ≤100MB"] --> VAL["Validate · status=processing"]
  VAL --> R2[("R2 original (bytes)")]
  R2 --> WK["Celery workers"]
  WK --> TR["Transcode H.264 ≤720p ≤30s + HLS"]
  WK --> TH["Thumbs 10/50/90% + WebP poster"]
  WK --> CP["Whisper captions AR/EN"]
  WK --> WM["Watermark"]
  TR & TH & CP & WM --> RDY["CDN publish · status=ready<br/>metadata → product_videos (DB)"]
  RDY --> REC["Recs: cat/brand/tags · pgvector sim ·<br/>co-view · trending decay (per country)"]
  REC --> ROW["Mobile snap-row · desktop rail"]
  ROW --> EVT["video_events batched<br/>(Redis → flush → partitioned table)"]
  EVT --> REC
  VAL -->|failure| DLQ["Explicit failed + reason · retry/DLQ"]
```

### 2.3 Video status lifecycle
```mermaid
stateDiagram-v2
    [*] --> PENDING : upload accepted (metadata row)
    PENDING --> PROCESSING : worker claimed
    PROCESSING --> READY : transcode+thumbs+captions+CDN ok
    PROCESSING --> FAILED : explicit reason (retry/DLQ)
    FAILED --> PROCESSING : retry
    READY --> FEATURED : merchandising auto/curated
    READY --> ARCHIVED : retention/product inactive
```

---

## 3. STEP-BY-STEP CONSTRUCTION

**Phase 0 — Schema & config.** Alembic (downgrade + contract tests): `product_filter_metadata/options`, `products.filter_attributes`+GIN, generated `search_vector`, `products.embedding vector`, `product_videos`, `video_events`+`search_events` (monthly partitions), config tables (synonyms, boosts, thresholds, facet defs); RLS on all; Redis keyspace plan. *Done when:* drift gate green; EXPLAIN shows index-only scans on hot facets.

**Phase 1 — Facet foundation.** Backfill `filter_attributes` from variants; build `mv_facet_counts` + cron + event invalidation; stampede-guarded cache. *Done when:* facet API < 50ms warm on 1M-product fixture.

**Phase 2 — Filter engine.** Service (disjunctive counts, JSONB apply, sorts) + endpoints + cursor pagination; URL-state sync. *Done when:* p95 < 300ms; multi-facet combo test green.

**Phase 3 — Hybrid search.** RRF fusion + parser + autocomplete + trending + did-you-mean + voice; explicit `mode:"lexical"` degradation; search events → outbox. *Done when:* zero-result rate baseline captured; fallback test shows explicit mode only.

**Phase 4 — AI enrichment & tuning loop.** Staging→commit enrichment; synonym mining; guarded boost tuner + A/B harness; audit every auto-change. *Done when:* nightly loop runs 7 clean nights with audit trail.

**Phase 5 — Video pipeline.** Upload validation → R2 → workers (transcode/HLS/thumbs/captions/watermark) → CDN → status; batched analytics; recommendation engine. *Done when:* upload→READY < 5 min; captions present on 100% of ready videos.

**Phase 6 — Storefront UI.** Filter rail/bottom-sheet + chips; search dropdown w/ understanding chips; video snap-row (mobile) + desktop rail; lazy-load, disable toggle, save-data fallback; RTL/AR; skeletons. *Done when:* Lighthouse ≥ target + 3G < 5s test passes on web + mobile apps.

**Phase 7 — Merchandising & SEO automation.** Banner scheduler, row re-rank, recently-viewed, cross-sell, JSON-LD/sitemaps. *Done when:* KPI watchdog dashboard live with all 12 automations reporting health.

**Phase 8 — Validate & close-out.** A/B (row vs sidebar vs hybrid), k6 load, accessibility + spam fixtures, E2E Playwright (search→filter→video→PDP→cart); update `CODEBASE_STATUS_MATRIX_DETAILED.md`. *Done when:* all success metrics (§1.5) instrumented and green.

---

## 4. UI/UX LAYOUT

### 4.1 PLP / Home (mobile-first hybrid)
```
MOBILE (<768px)                          DESKTOP (>1024px)
┌──────────────────────────┐   ┌───────────────┬──────────────────────────┬──────────────┐
│ Banner (auto-scheduled)  │   │ FILTER RAIL   │ Banner + Search + voice  │ RIGHT RAIL   │
│ Search + voice + chips   │   │ price hist    ├──────────────────────────┤ related vids │
│ [▶▶ VIDEO SNAP-ROW 1.5]  │   │ brands(counts)│ [▶▶ HORIZONTAL VIDEO ROW]│ recently seen│
│ Chips: under-100 × 4★ ×  │   │ attrs groups  ├──────────────────────────┤ cross-sell   │
│ 2-col grid · infinite    │   │ ≥4★ · in-stock│ PRODUCT GRID (cursor)    │              │
│ [Filters] bottom-sheet   │   │ clear-all     │                          │              │
└──────────────────────────┘   └───────────────┴──────────────────────────┴──────────────┘
```

### 4.2 Key screens
- **Search dropdown:** suggestions w/ thumbnails + trending tag; understanding chips ("under 100 OMR ×", "brand: Samsung ×"); did-you-mean banner; empty state = remove-filter suggestions + synonyms (never silent zero).
- **PDP:** gallery with video tab + captions; desktop right rail "You may also like (video)"; mobile row below fold; add-to-cart sticky; save-data → posters.
- **Supplier Video Studio:** upload w/ live validation; processing timeline (transcode→thumbs→captions→CDN); caption editor; thumbnail picker; analytics (views, watch-time, completion, attributed conversions); explicit failure cards w/ retry.
- **Admin Merchandising Console:** facet metadata manager (per-category rails, order, types); synonym/redirect manager w/ confidence slider; boost tuner + A/B dashboard; featured-video approval queue; trending controls; **KPI watchdog** vs targets (filter use >40% · search success >85% · video engage >60% · load <3s · 3G <5s) with auto-tickets on regression.
- **UX principles:** one muted autoplay; disable toggle persisted per user; captions default-on when sound off; skeletons + explicit stale badges; ARIA/keyboard; RTL-first Arabic; tabular price numerals; density toggle.

> **AI Directive:** build in Phase order; any live aggregate in a request path, any media byte in DB, any OFFSET on large tables, any sync counter UPDATE, or any silent search fallback violates this spec and Appendix A — STOP and ask.

# _____________________________________________________________________________________________ [ADVANCED FILTERS · AI SEARCH · VIDEO COMMERCE — MASTER BUILD SPEC]

# _____________________________________________________________________________________________ [ADMIN COMMAND CENTER]

## ZOZI UNIFIED OPERATIONS COMMAND CENTER — MASTER BUILD SPEC

> Binding addendum to `01_DATABASE.md` (analytics/audit/comms/country schemas → future `10_ANALYTICS.md` + `08_COUNTRY.md`). Inherits the constitution: **analytics never live-aggregate on request path (ADR-008 → 4-tier strategy), financial truth only from the double-entry ledger (ADR-006), RLS `country_code` everywhere, events via outbox (ADR-014), config-as-data, AI staged→commit, append-only audit, no silent fallbacks (explicit `degraded` flags), p95 < 300ms, cursor pagination, Alembic-only.**

### 0. Prime directives (from founder notes)
- **Merge Command Center + Analytics into ONE "Single Window"** — they currently replicate/complement each other; **read all existing dashboard/analytics code in detail before merging**; delete the duplicate page after cutover.
- **Dashboard ≠ Command Center:** *every employee* gets a **limited personal dashboard**; *Admin* gets the **full Command Center**; Admin may **grant Command Center access to others with limited, zone-scoped, country-scoped rights** (Maker-Checker for sensitive zones like Treasury/Fraud).
- Dynamic, modern, glanceable UI: one-glance organizational health; widgets over tables; traffic-light semantics; deep-link every number to its filtered workspace.

---

## 1. BULLET POINTS — EXTRACTED + ENHANCED

### 1.1 Access & visibility model
- Same URL for all; UI + data auto-shaped by **role layer (Global > Country > Hierarchy)** + RLS: CEO/Global Admin = aggregated global; Country Head = identical UI filtered to assigned countries (metrics, chats, escalations, roster); Employee = personal KPIs only.
- **Zone-level permission strings** (`cc.treasury.view`, `cc.fraud.view`, `cc.workforce.view`…) in the frozen permission catalog; assignment audited in `admin_change_audit_logs`; sensitive grants = Maker-Checker.
- **(ADDED) Data-freshness badge per widget** (tier + last-updated + `degraded` flag) — transparency, never fake-live.
- **(ADDED) Alert-fatigue control:** dedupe/aggregate repeats; quiet-hours per tier (Tier-3 always breaks through).

### 1.2 Metric inventory → 4-Tier data strategy
| Zone / Metrics | Tier |
|---|---|
| **Z1 Heartbeat:** today's orders/GMV/revenue, active users (buying vs window-shopping: session + >3 views + no cart 10min), live fleet (companies vs individuals, active shipments, delayed, failed), employees working, system issues | **T1** WS/Redis PubSub 2–5s (`/ws/admin/telemetry`) |
| **Z2 Treasury:** available/locked/operating cash, supplier & logistics payables, refund reserve, VAT liability (+remittance countdown), commission reserve, pending payouts, refunds, disputes | **T3** instant SQL on `account_balances` (1010/2010/2020/2040…) — *never order sums* |
| **Z3 Growth:** revenue trend 30d, country-wise sales map, category/product trends, top searches + zero-results, gender split, signups, CLV **(ADDED)**, cash-runway forecast **(ADDED)** | **T2** Redis 5-min cron + **T4** nightly MVs (`daily_trend_aggregates`) |
| **Z4 Workforce/Ops:** on-duty roster (QR/geo), performance tickers (tickets/hr, moderation approve-rate, payouts processed), bottlenecks (KYC pending, moderation queue, stuck orders, returns), shift handovers, grievances | **T1+T2** |
| **Z5 External Intel:** Market Radar news ticker, regulatory shield (ZATCA/PDPL/VAT countdowns), FX ticker + margin alerts, supply-chain alerts, competitor price index, sentiment/NPS pulse, PR crisis radar | **T2** + news pipeline |
| **Z6 Engine Room & Fraud:** API p95/p99, error rate, CPU/mem, DB conns/replication lag/disk, Redis hit/eviction, gateway success heatmap (auto-reroute <85%), CDN health by region, live attack map, chargeback velocity (>1% critical), ATO radar (reset spikes, supplier bank-change) | **T1** Prometheus/Grafana/Loki embed + fraud engine |
- Partner health MVs: `supplier_health_scores` (cancellation/return/KYC-expiry), `logistics_sla_alerts`. New tracking tables: `search_logs`, `user_sessions`, `system_health_events`.

### 1.3 Human Operations layer (the "active cockpit")
- **Broadcasts:** Global (Admin) vs Local (Country Head) color-coded dismissible banners; read-confirmation tracking **(ADDED)**.
- **Shift handover logs:** mandatory end-of-shift digital sign-off (unresolved criticals, pending approvals, glitches); incoming shift must acknowledge; **(ADDED) block clock-out until filed** (ties to EMS handover gate).
- **Escalation Siren:** Tier-1 Country Manager (2h ack timer) → Tier-2 Country Head/Finance (in-alert Approve/Block) → Tier-3 Admin/CTO (SMS/email fallback + red flash); every ack/action → append-only audit ("alert 14:00, acked 14:05, no action").
- **War-Room chat:** entity-attached threads (click "Failed Deliveries" → the exact chat about that batch); @mentions deep-link to the exact screen with action button ready; auto-translate AR↔EN.
- **Safe Box:** supplier grievances vs staff + anonymous whistleblower channel → visible **only** Global Admin/Compliance (bypasses local heads); SLA-penalty tracker requiring Admin sign-off.
- **(ADDED) Follow-the-sun handoff view:** auto-highlights which country shift is handing over now.

### 1.4 News & Market Intelligence pipeline
- `news_sources` (name, url, type `rss|api|scrape`, category `market|logistics|regulatory|ecommerce|internal`, `target_audience admin_only|supplier|public`, fetch_interval, is_active, api_key_required) + `news_articles` (external_id, **SHA256 content_hash dedupe**, title/summary/content, url, image_url, published/fetched_at, country_code nullable, `ai_sentiment`, `ai_tags` JSONB, `is_published`).
- Async fetchers (feedparser/httpx/newspaper3k) on 15-min cron with per-source `last_fetched` in Redis; sanitize (strip HTML/trackers, UTC normalize); **AI enrichment staged**: entity→country/module map, sentiment, relevance score **<40 discarded**; PubSub → WS ticker; audience routing: Admin Market Radar / Supplier Insights / Public SEO blog; moderation queue + `flush-now` + publish toggle; auto-publish only ≥ confidence threshold **(ADDED, ADR-007)**.
- **Regulatory Shield:** ZATCA Phase-2 e-invoicing success ticker, PDPL/GDPR audit countdown + encryption %, VAT filing countdowns **linked to ledger `2040`**; T-7/T-3/T-1 alerts **(ADDED)**.
- **What-If Simulation Engine:** commission/SLA/promo-ROI simulators read **snapshots only**, outputs labeled "projection — not truth", never write to ledger **(ADDED guardrail)**; launched via Ctrl+K.

### 1.5 Decision Engine & monitoring
- Anomaly rules (config-driven): delayed >5% active → red; zero-search spike → "Alert Procurement" + stock check; VAT > threshold + due ≤4d → "Generate Tax Report"; gateway <85% → auto-reroute + badge; every alert carries a **deep-link action button** into the pre-filtered workspace.
- Monitoring embed (Zone 6): app p95/p99, error rate, CPU/mem; DB conns/slow-query/replication-lag/disk; Redis mem/hit/eviction; business (orders/hr, conversion, signups); alerts: error >1%, resp >3s, CPU >80%, disk >85%, gateway fail >5%.

### 1.6 Country Control Plane (integrated, not siloed)
- Normalized schema: split `country_configs` → basics/economics/tax/legal + `country_cities`, `country_category_tax_rates`, `country_config_versions` (draft→approve→publish→rollback), `country_feature_flags`, `country_staff_assignments`.
- **Heuristic Orchestrator:** RestCountries/WorldBank/GeoDB/Nager.Date fetchers, 48h Redis cache, **explicit `degraded` flags** (Rule #16); gateway ranking 0–100; commission-tier generator; KYC-tier auto-assign; logistics model recommender; restricted-category auto-tag; **source-transparency badges** in UI.
- **Ghost-Row Ledger UI** (no modals): inline expandable create row, 600ms debounced auto-map search, 17-tab workspace, inline editors within algorithmic bounds, masked keys + "Test Connection".
- **Downstream auto-wiring:** checkout gateways, supplier KYC fields, moderation blocks, payout holds/minimums, ETA holiday-skip — all read country config live (no deploys).
- Cross-border detection (`cross_country_customer_records`), dynamic currency/tax swap, deep localization (Eastern Arabic numerals, Hijri, RTL logical CSS, dynamic address builder); draft-to-publish safety net; localized legal PDF generation; immutable financial edit audit with mandatory reason; data-residency KMS + export redaction; geospatial maps (cities, shops/warehouses, partner GPS, parcel tracking).

### 1.7 🤖 AUTOMATION SYSTEM (detail — the core ask)
| # | Automation | Trigger | Auto action | Exception path |
|---|---|---|---|---|
| 1 | **Metric aggregation** | crons 5min + nightly | T2 Redis JSON + T4 MV refresh; drift vs T3 ledger checked | variance alert |
| 2 | **Live telemetry push** | outbox events | PubSub → WS heartbeat increments | explicit stale badge on lag |
| 3 | **Escalation engine** | alert raise | tier timers → auto-escalate → SMS/email T3; ack audit | missed-SLA → performance flag |
| 4 | **News flush & enrich** | 15-min cron | fetch→dedupe→sanitize→AI tag/sentiment→route by audience | moderation queue; `degraded` source badge |
| 5 | **Gateway health & reroute** | webhook stream | per-country success heatmap; <85% auto-reroute + banner | manual freeze button |
| 6 | **Fraud watch** | event stream | attack map, chargeback >1% critical, ATO radar (bank-change) | Tier-2/3 queue |
| 7 | **Decision-engine anomalies** | rules cron | deep-link action cards (procurement, tax report, SLA breach) | dismiss-with-reason logged |
| 8 | **Handover enforcement** | shift end | block clock-out till log filed; incoming ack required | manager override logged |
| 9 | **Broadcast targeting** | publish | global/local routing + read-confirm tracking | non-readers → reminder ping |
| 10 | **Regulatory countdowns** | daily | VAT from ledger; ZATCA/PDPL timers T-7/3/1 | compliance queue |
| 11 | **Sentiment & PR radar** | scrape cron | sentiment score, NPS pulse, viral-traction alert | PR queue |
| 12 | **What-If sims** | Ctrl+K request | snapshot-only projection models | labeled "not truth" |
| 13 | **Auto digests** | daily 07:00 **(ADDED)** | CEO briefing assembled from zones → email/chat; country digests | — |
| 14 | **Dashboard personalization** | role login **(ADDED)** | zone/widget layout per role; saved layouts; compare-mode (today vs yesterday) | admin-published defaults |
| 15 | **Country orchestrator** | new-country search | auto-map heuristics → **draft** → publish approval | degraded flags per source |
| 16 | **KPI watchdog** | hourly | targets vs actuals (load <500ms, alert MTTA, ack SLA) → auto-tickets | regression alerts |

---

## 2. DIAGRAMS

### 2.1 Single-Window data architecture (4 tiers → zones → actions)
```mermaid
flowchart TB
subgraph SRC["EVENT SOURCES (outbox · webhooks · scrapers)"]
  O["orders/shipments/payments"] & A["auth/sessions/attendance"] & S["search/video events"] & H["prometheus · gateways · system_health"] & N["RSS/API news"]
end
O --> T1 & T2 & T4
A --> T1 & T2
S --> T2
H --> T1
N --> NP["NEWS PIPELINE: dedupe SHA256 → sanitize →<br/>AI enrich (sentiment/tags/relevance≥40) → audience route"]
NP --> T2
subgraph TIERS["4-TIER STRATEGY"]
  T1["T1 REAL-TIME 2-5s<br/>Redis PubSub → /ws/admin/telemetry"]
  T2["T2 CACHE 5-min TTL<br/>cron → Redis JSON"]
  T3["T3 LEDGER instant SQL<br/>account_balances (cash/VAT/payables)"]
  T4["T4 NIGHTLY MV/OLAP<br/>trends · health scores · CLV"]
end
T1 & T2 & T3 & T4 --> CC["COMMAND CENTER — SINGLE WINDOW (6 Zones)<br/>RLS + role-shaped · freshness badges"]
CC --> DR["ACTION DRAWER: Alerts · Comms · Roster"]
CC --> CP["Ctrl+K PALETTE: jump · broadcast · simulate"]
CC --> DE["DECISION ENGINE cards w/ deep-link buttons"]
DE --> ESC["ESCALATION TIERS 1→2→3 (timers · SMS/email)"]
ESC --> AUD[("admin_change_audit_logs · append-only")]
DE --> OPS["pre-filtered workspaces: refund approve ·<br/>gateway reroute · tax report · fraud queue"]
```

### 2.2 Escalation lifecycle
```mermaid
stateDiagram-v2
    [*] --> RAISED : anomaly/monitor/fraud/ledger-imbalance
    RAISED --> TIER1 : Country Manager (2h timer)
    TIER1 --> ACKED : ack + action (deep-link)
    TIER1 --> TIER2 : timer expiry
    TIER2 --> ACKED : in-alert Approve/Block
    TIER2 --> TIER3 : expiry / financial risk
    TIER3 --> ACKED : SMS+email fallback + red flash
    ACKED --> AUDITED : who/when/action logged
    AUDITED --> [*]
```

### 2.3 News → surfaces routing
```mermaid
flowchart LR
  F["Fetchers (rss/api/scrape)"] --> D["Dedupe + Sanitize"]
  D --> E["AI: entities→country/module · sentiment · relevance"]
  E -->|<40| X["Discard (logged)"]
  E -->|≥40| R["Route by audience"]
  R -->|admin_only| MR["Market Radar ticker + Regulatory Shield"]
  R -->|supplier| SI["Supplier Industry Insights"]
  R -->|public| BL["Storefront Blog (SEO)"]
  MR --> B["1-click: Draft Internal Broadcast"]
```

---

## 3. STEP-BY-STEP CONSTRUCTION

**Phase 0 — Audit & freeze.** Read *all* existing Command Center/Dashboard/Analytics code; map duplicates; define unified zone taxonomy + widget catalog; freeze permission strings (`cc.*`) + alert thresholds in config tables. *Done when:* duplicate-feature map signed off; old routes listed for deletion.

**Phase 1 — Schema & MVs.** Alembic (downgrade + contract tests): `search_logs`, `user_sessions`, `system_health_events`, `news_sources/articles`, `escalations`, `broadcasts(+read_confirms)`, `shift_handover_logs`, `grievances`; MVs `supplier_health_scores`, `logistics_sla_alerts`, `daily_trend_aggregates`; RLS + indexes on all. *Done when:* drift gate green.

**Phase 2 — Tier services.** Cron cache jobs (T2) + WS telemetry channel (T1) hooked to order/shipment/auth events; T3 ledger reader; gateway-health monitor + reroute hook; freshness/degraded metadata on every payload. *Done when:* dashboard API < 500ms with 50+ metrics; zero raw-table aggregates in request path.

**Phase 3 — Unified frontend.** Build 6-zone Single Window + Action Drawer + Ctrl+K; role variants (employee-limited / country-filtered / global); **delete old Analytics page**; skeletons, traffic-lights, sparklines, compare-mode, annotations **(ADDED)**, RTL/AR. *Done when:* Playwright E2E on all three role views; Lighthouse green.

**Phase 4 — Human Ops.** Broadcasts + read-confirm; handover enforcement; escalation matrix with timers + audit; entity-attached war-room chat + translate; Safe Box; penalty tracker. *Done when:* unacked Tier-1 auto-escalates in test; every ack audited.

**Phase 5 — News & Shield.** Ingestion workers + dedupe + AI enrichment + routing; Market Radar ticker; Regulatory countdowns wired to ledger VAT; moderation queue + flush-now. *Done when:* 7 clean cron nights; duplicate wire stories deduped 100%.

**Phase 6 — Engine Room & Fraud.** Prometheus/Grafana/Loki embeds; attack map; chargeback/ATO alerts; CDN-by-region health. *Done when:* all 5 infra alert rules fire correctly in chaos test.

**Phase 7 — Decision & Simulation.** Anomaly rule engine + deep-link action cards; What-If simulators (snapshot-only, labeled projections). *Done when:* each card lands on the pre-filtered workspace with action ready.

**Phase 8 — Country Plane wiring.** Ghost-row + 17-tab workspace; orchestrator with degraded flags; downstream syncs (checkout/KYC/moderation/payouts/ETA); localization + residency + legal PDFs; geospatial maps. *Done when:* adding a country changes checkout/KYC/payout behavior with zero deploys.

**Phase 9 — Watchdog, digests & hardening.** KPI watchdog + auto-tickets; daily auto-digests; alert-fatigue controls; load test (k6) on dashboard; security (RLS fail-closed per zone). *Done when:* MTTA/ack-SLA baselines met.

**Phase 10 — Close-out.** Full E2E (CEO/CountryHead/Employee views), heuristics Pytest, schema-drift gate, update `CODEBASE_STATUS_MATRIX_DETAILED.md`. *Done when:* old duplicate pages removed and matrix green.

---

## 4. UI/UX LAYOUT — THE SINGLE WINDOW

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ TOPBAR: [Ctrl+K palette] [country ctx ▼] [ tier-badged] [broadcast ▾]      │
│ [BANNER: global/local notices — color-coded, dismissible, read-tracked]      │
├───────────────────────────────────────────────────────────────┬──────────────┤
│ Z1 HEARTBEAT (live): Orders·GMV·Rev·Buying-vs-Window·Fleet map │ ACTION       │
│ Z2 TREASURY: cash waterfall·liability dials·VAT countdown·     │ DRAWER       │
│    gateway heatmap            │ Z3 GROWTH: country map·trends· │ [Alerts▸timers]│
│                                │  intent radar·gender·CLV       │ [Comms▸war-room]│
│ Z4 WORKFORCE: roster·tickers·bottlenecks·handover·safe-box     │ [Roster▸perf]│
│ Z5 INTEL: Market Radar ticker·Regulatory Shield·FX·sentiment   │              │
│ Z6 ENGINE ROOM: traffic-lights·infra·attack map·chargeback     │              │
└───────────────────────────────────────────────────────────────┴──────────────┘
```
- **Role variants:** Employee = personal KPIs + team roster + announcements only; Country Head = full zones, country-filtered, no global Treasury/Fraud unless granted; Admin/CEO = global + grant management.
- **Widget grammar:** every card = value + spark/dial + traffic-light + freshness badge + click→filtered workspace; skeletons on load; explicit stale/degraded badges; compare toggle; admin-pinnable annotations ("Ramadan sale start").
- **Palette examples:** "Show Gateway Health KSA", "Simulate 2% commission drop", "Broadcast maintenance OM", "Pending KYC Saudi".
- **Mobile:** condensed heartbeat + tier-3 alerts + drawer; push digests; tap→deep-link.
- **Principles:** glance-first (no 30-query page loads), action-over-observation (every alert has a button), audit-everything, RTL-first Arabic, ARIA/keyboard, density toggle.

> **AI Directive:** implement in Phase order; any dashboard query that live-aggregates transactional tables, any financial widget not sourced from the ledger, any cross-country leak, any un-audited alert/ack, or any silent degraded path violates this spec and Appendix A — STOP and ask.

# _____________________________________________________________________________________________ [ADMIN COMMAND CENTER]

# _____________________________________________________________________________________________ [COUNTRY PAGE SYSTEM & COUNTRY ADDING SYSTEM]



# _____________________________________________________________________________________________ [COUNTRY PAGE SYSTEM & COUNTRY ADDING SYSTEM]




# _____________________________________________________________________________________________ AI Provider System

`D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\providers\**` we need all the AI provider into this folder 
- image bg removal, 
- image to text ( for product image reading and description, tag, product name identify, finding variant for particular product ), 
- voice to text ( For Product adding variant, quantity and etc )
- ocr system ( for scan the bills and recipt for expenses and assets )
- voice to text ( For finance for doing task )
- chatbot ( for chatbot for vactorization of product and chating with the customer )
- advance search engine + filtering using AI and vectorization.
- IP address detection system for customer location and country  detection and also 
- Map and location provider system.
- country details search AI work and system.
- AI analysis for Admin analytics

---

Read complete system, find the files in the complete `backend` folder shift all relevant files and if you didn't get any file you can create files. for image bg removal, i need all the model below 
	"D:\Projects\10- E-COMMERCE WEBSITE\zozi\Working_API\zozi_ai_image_service\br_13.py"
	"D:\Projects\10- E-COMMERCE WEBSITE\zozi\Working_API\zozi_ai_image_service\br_05.py"
	"D:\Projects\10- E-COMMERCE WEBSITE\zozi\Working_API\zozi_ai_image_service\br_06.py"
	"D:\Projects\10- E-COMMERCE WEBSITE\zozi\Working_API\zozi_ai_image_service\br_08.py"
	"D:\Projects\10- E-COMMERCE WEBSITE\zozi\Working_API\zozi_ai_image_service\br_11.py"
	"D:\Projects\10- E-COMMERCE WEBSITE\zozi\Working_API\zozi_ai_image_service\br_12.py"

and for image to text detection, you can take reference from below
	"D:\Projects\10- E-COMMERCE WEBSITE\zozi\Working_API\zozi_ai_upload_session\zozi_variant_config.json"
	"D:\Projects\10- E-COMMERCE WEBSITE\zozi\Working_API\zozi_ai_upload_session\upload_auto_05.py"

---

- `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\providers\**` read all the models and test them properly,
- keep the test files into the `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\tests\_test_provider\**`, 
- keep the reference of the test into the files for future reference `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\providers\**`
- ensure all the `providers/**` AI models are working 100% coreectly.
- update 2 times each test file for ensuring all the `providers` are working and providing correct information and result.

---

- all the models must be `light-weight` with better result because we are integrate into website where 1000s of user will use at a time & VPS can't handle heavy models. 
- use the concurrent and mult-threads system where you feel it will help to manage 1000s of users.
- Use the images of products from `D:\Projects\10- E-COMMERCE WEBSITE\zozi\image` for test and perform test in detail.
- Keep all the result of test into `D:\Projects\10- E-COMMERCE WEBSITE\zozi\provider_test`

---


# _____________________________________________________________________________________________ AI Provider System

# _____________________________________________________________________________________________ Details of COUNTRY NEEDED

## 📋 Complete Country Research Data Framework for E-Commerce

Below is the **exhaustive master list** of every data point you need, organized by module, with the recommended **presentation format** for each.

---

## 🗂️ MODULE 1: COUNTRY IDENTITY & BASICS

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 1.1 | Official Country Name | Republic of India | Header / Title |
| 1.2 | Common/Short Name | India | Searchable tag |
| 1.3 | Country Code (ISO Alpha-2) | IN | Badge/Chip |
| 1.4 | Country Code (ISO Alpha-3) | IND | Badge/Chip |
| 1.5 | Numeric Code | 356 | Hidden field |
| 1.6 | Capital City | New Delhi | Info card |
| 1.7 | Flag (Emoji + Image URL) | 🇮🇳 | Icon |
| 1.8 | Region / Continent | Asia > Southern Asia | Breadcrumb |
| 1.9 | Total Area (km²) | 3,287,263 | Stat card |
| 1.10 | Time Zones | UTC+5:30 | Dropdown selector |
| 1.11 | Calling Code | +91 | Input prefix |
| 1.12 | Google Maps Link | URL | Button |
| 1.13 | Government Type | Federal Parliamentary Republic | Tag |
| 1.14 | Independence / Founding Year | 1947 | Timeline |

---

## 🗂️ MODULE 2: DEMOGRAPHICS & POPULATION

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 2.1 | Total Population | 1.44 Billion | Big stat card |
| 2.2 | Population Growth Rate | 0.8% / year | Trend arrow ↑↓ |
| 2.3 | Median Age | 28.7 years | Gauge chart |
| 2.4 | Age Distribution (0-14, 15-64, 65+) | 25%, 68%, 7% | Pie chart |
| 2.5 | Urban vs Rural Split | 35% Urban / 65% Rural | Donut chart |
| 2.6 | Gender Ratio | 1.08 M : 1 F | Bar chart |
| 2.7 | Literacy Rate | 77.7% | Progress bar |
| 2.8 | Top 10 Cities (by population) | Mumbai, Delhi, Bangalore... | Ranked table |
| 2.9 | Top 5 E-commerce Ready Cities | Bangalore, Mumbai, Delhi, Hyderabad, Pune | Highlighted cards with reasoning |
| 2.10 | Ethnic / Racial Composition | Diverse, 2000+ ethnic groups | Tag cloud |
| 2.11 | Religious Composition | Hindu 79%, Muslim 14%, etc. | Pie chart |
| 2.12 | Expatriate / Foreign Worker % | 0.5% | Stat card |

---

## 🗂️ MODULE 3: ECONOMY & WEALTH

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 3.1 | GDP (Nominal) | $3.94 Trillion | Stat card |
| 3.2 | GDP Per Capita (PPP) | $9,183 | Stat card |
| 3.3 | GDP Growth Rate | 6.5% | Trend line |
| 3.4 | Inflation Rate | 5.1% | Warning indicator |
| 3.5 | Unemployment Rate | 7.2% | Gauge |
| 3.6 | Income Distribution (Gini Coefficient) | 35.7 | Scale bar |
| 3.7 | Middle Class Size (% of pop) | ~30% (400M people) | Highlighted stat |
| 3.8 | Average Monthly Salary | $600 USD | Stat card |
| 3.9 | Average Disposable Income | $250-$400/month | Range slider visual |
| 3.10 | Poverty Rate | 10.5% | Alert badge |
| 3.11 | Wealth Tiers Breakdown | Ultra-rich 1%, Upper-middle 10%, Middle 30%, Lower 59% | Stacked bar |
| 3.12 | Currency Name | Indian Rupee | Text |
| 3.13 | Currency Code (ISO) | INR | Badge |
| 3.14 | Currency Symbol | ₹ | Icon |
| 3.15 | Exchange Rate (vs USD) | 1 USD = 83.2 INR | Live ticker |
| 3.16 | Currency Stability (1yr trend) | Depreciating ~3%/yr | Sparkline |
| 3.17 | Foreign Exchange Controls | Partial restrictions | Alert tag |

---

## 🗂️ MODULE 4: TAX SYSTEM & DUTIES

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 4.1 | Tax System Type | GST (Goods & Services Tax) | Tag |
| 4.2 | Standard Tax Rate | 18% | Big stat |
| 4.3 | Tax Slabs / Tiers | 0%, 5%, 12%, 18%, 28% | Tiered table |
| 4.4 | Tax on Digital Goods | 18% | Info card |
| 4.5 | Tax on Physical Goods | 5%-28% (category-based) | Category table |
| 4.6 | Import / Customs Duty | 10%-30% (varies by HS code) | Range table |
| 4.7 | Customs Threshold (De Minimis) | ₹50,000 (~$600) | Alert box |
| 4.8 | Who Pays Duty? (DDP vs DDU) | Customer pays at door (DDU common) | Flow diagram |
| 4.9 | Tax Registration Requirement | GSTIN needed for >₹40L turnover | Checklist |
| 4.10 | Foreign Company Tax Obligation | Need local entity or agent | Alert box |
| 4.11 | Withholding Tax on Cross-border | 10%-20% | Info card |
| 4.12 | Tax Filing Frequency | Monthly / Quarterly | Calendar icon |
| 4.13 | Tax Authority Name | Central Board of Direct Taxes (CBDT) | Link |
| 4.14 | Free Trade Agreements | ASEAN, SAFTA, bilateral deals | Tag list |

---

## 🗂️ MODULE 5: CONSUMER PSYCHOLOGY & MINDSET

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 5.1 | General Mindset Toward Online Shopping | "Trust but verify" – growing but cautious | Narrative card |
| 5.2 | Price Sensitivity Level | HIGH (8/10) | Rating scale |
| 5.3 | Brand Loyalty Level | MEDIUM – switch for discounts | Rating scale |
| 5.4 | Status / Prestige Buying | YES – luxury brands signal success | Tag |
| 5.5 | Family Influence on Purchases | VERY HIGH – joint family decisions | Rating scale |
| 5.6 | Peer / Social Proof Influence | HIGH – reviews & word-of-mouth critical | Rating scale |
| 5.7 | FOMO (Fear of Missing Out) Factor | HIGH during sales events | Rating scale |
| 5.8 | Trust in Foreign Brands | MEDIUM – prefer known global names | Gauge |
| 5.9 | Trust in New/Unknown Brands | LOW – need heavy social proof | Gauge |
| 5.10 | Bargaining / Negotiation Culture | YES – expect discounts, coupons | Tag |
| 5.11 | Impulse vs Planned Buying Ratio | 40% impulse / 60% planned | Pie chart |
| 5.12 | Research Before Purchase | HIGH – compare 3-5 sites before buying | Info card |
| 5.13 | Emotional vs Rational Buying | 60% emotional / 40% rational | Split bar |
| 5.14 | Attitude Toward "Made in [Country]" | Patriotic buying trend (e.g., "Make in India") | Tag |
| 5.15 | Generational Differences | Gen-Z: digital-first; 40+: prefer COD | Comparison table |

---

## 🗂️ MODULE 6: CONSUMPTION PREFERENCES

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 6.1 | Top 10 Product Categories (by demand) | Electronics, Fashion, Grocery, Beauty... | Ranked list |
| 6.2 | Average Order Value (AOV) | $25-$45 | Stat card |
| 6.3 | Quality vs Price Priority | Price-first for mass; Quality for premium | Split view |
| 6.4 | Sustainability / Eco-consciousness | LOW-MEDIUM (growing in metros) | Gauge |
| 6.5 | Preference for Local vs International | Mixed – local for food, intl for tech | Comparison |
| 6.6 | Size / Fit Preferences | Specific to body types, modest wear in some regions | Info card |
| 6.7 | Color / Design Preferences | Bright colors, gold accents, cultural motifs | Visual palette |
| 6.8 | Packaging Expectations | Gift wrapping important during festivals | Tag |
| 6.9 | Subscription / Repeat Purchase Rate | LOW – prefer one-time buys | Stat |
| 6.10 | Bulk / Wholesale Buying Culture | HIGH – family-size packs preferred | Tag |
| 6.11 | Seasonal Product Demand | Winter wear (North), AC/fans (South), etc. | Calendar heatmap |
| 6.12 | Halal / Kosher / Vegetarian Requirements | 30%+ vegetarian; Halal important for Muslim segment | Alert tags |
| 6.13 | Prohibited / Restricted Products | Alcohol banned in some states; beef restrictions | Red alert box |

---

## 🗂️ MODULE 7: SHOPPING SEASONALITY & EVENTS

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 7.1 | Major Shopping Festivals | Diwali, Holi, Eid, Christmas | Calendar timeline |
| 7.2 | E-commerce Specific Sales Events | Big Billion Days (Flipkart), Great Indian Festival (Amazon) | Highlighted cards |
| 7.3 | Global Sales Events Participation | Black Friday, Cyber Monday, 11.11 | Tags |
| 7.4 | Payday Shopping Cycles | 1st-5th of month (salary week) | Recurring highlight |
| 7.5 | Wedding Season Impact | Oct-Feb: massive gold, clothing, gift demand | Seasonal banner |
| 7.6 | Back-to-School Season | April-June (varies by state) | Calendar tag |
| 7.7 | Religious Fasting Periods | Ramadan, Navratri – altered buying patterns | Alert |
| 7.8 | Monsoon / Weather Impact | Jun-Sep: indoor shopping spikes, logistics delays | Weather icon |
| 7.9 | Peak Shopping Hours | 8 PM - 12 AM (post-work browsing) | Clock visual |
| 7.10 | Peak Shopping Days | Weekends, Sunday highest | Bar chart |

---

## 🗂️ MODULE 8: DIGITAL LANDSCAPE & INTERNET

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 8.1 | Internet Penetration Rate | 52% (750M+ users) | Progress bar |
| 8.2 | Mobile vs Desktop Split | 85% Mobile / 15% Desktop | Donut chart |
| 8.3 | Average Internet Speed | 60 Mbps (mobile) | Gauge |
| 8.4 | Smartphone Penetration | 45%+ and growing | Stat card |
| 8.5 | Dominant OS (Android vs iOS) | Android 95% / iOS 5% | Pie chart |
| 8.6 | Top Social Media Platforms | YouTube, WhatsApp, Instagram, Facebook | Ranked icons |
| 8.7 | Social Media Usage (hrs/day) | 2.5 hours average | Stat card |
| 8.8 | E-commerce App Preferences | Flipkart, Amazon, Meesho, Myntra | Ranked list |
| 8.9 | Search Engine Preference | Google 98% | Stat |
| 8.10 | Email Open / Engagement Rate | LOW – WhatsApp preferred for communication | Alert |
| 8.11 | Video Commerce / Live Shopping | Growing – YouTube, Instagram Live | Trend tag |
| 8.12 | AI / Chatbot Acceptance | MEDIUM – prefer human support | Gauge |

---

## 🗂️ MODULE 9: PAYMENT INFRASTRUCTURE

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 9.1 | Most Popular Payment Method | UPI (Unified Payments Interface) | #1 Highlighted card |
| 9.2 | Top 5 Payment Gateways | Razorpay, PayU, CCAvenue, PhonePe, Paytm | Ranked list |
| 9.3 | Credit/Debit Card Penetration | 35% of adults | Stat card |
| 9.4 | Digital Wallet Usage | PhonePe, Google Pay, Paytm – VERY HIGH | Tag cloud |
| 9.5 | Cash on Delivery (COD) % | 40-50% of e-commerce orders | Big alert stat |
| 9.6 | Bank Transfer / Net Banking | 15% of transactions | Stat |
| 9.7 | Buy Now Pay Later (BNPL) | Growing – Simpl, LazyPay, Amazon Pay Later | Trend tag |
| 9.8 | EMI / Installment Culture | VERY HIGH – "No Cost EMI" expected | Highlighted |
| 9.9 | International Card Acceptance | Visa, Mastercard accepted; Amex limited | Tag list |
| 9.10 | Cryptocurrency Status | Banned / Restricted / Taxed | Alert badge |
| 9.11 | Average Transaction Value | $15-$30 online | Stat card |
| 9.12 | Payment Failure Rate | 5-8% (UPI much lower) | Warning indicator |
| 9.13 | Refund Processing Time | 5-7 business days expected | Info card |
| 9.14 | Currency Conversion Fees | 2-3.5% on international cards | Info card |

---

## 🗂️ MODULE 10: LOGISTICS & SHIPPING

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 10.1 | Top Courier / Logistics Companies | Delhivery, BlueDart, DTDC, India Post | Ranked list |
| 10.2 | Average Delivery Time (Metro) | 1-3 days | Stat card |
| 10.3 | Average Delivery Time (Rural) | 5-10 days | Stat card |
| 10.4 | Shipping Cost Expectation | FREE shipping expected (subsidized) | Alert |
| 10.5 | Free Shipping Threshold | Orders above ₹499-₹999 | Info card |
| 10.6 | Same-Day / Next-Day Availability | Metro cities only | Tag |
| 10.7 | Last-Mile Delivery Quality | MEDIUM – address issues in rural areas | Gauge |
| 10.8 | Package Tracking Expectation | MANDATORY – real-time tracking expected | Alert |
| 10.9 | COD Availability by Region | Urban: Yes; Remote: Limited | Map overlay |
| 10.10 | Return Pickup Service | Expected – doorstep pickup for returns | Info card |
| 10.11 | Customs Clearance Time (Imports) | 3-7 days | Stat card |
| 10.12 | Warehousing Hubs | Mumbai, Delhi NCR, Bangalore, Hyderabad | Map pins |
| 10.13 | Packaging Regulations | Plastic ban in some states; eco-packaging push | Alert |

---

## 🗂️ MODULE 11: LEGAL, RULES & REGULATIONS

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 11.1 | E-commerce Registration Requirement | FDI rules, local entity needed for marketplace | Checklist |
| 11.2 | Consumer Protection Law | Consumer Protection Act 2019 | Info card |
| 11.3 | Mandatory Return/Refund Window | 7-10 days (platform dependent) | Stat card |
| 11.4 | Data Privacy Law | Digital Personal Data Protection Act (DPDP) 2023 | Alert card |
| 11.5 | Data Localization Requirement | Critical data must stay in-country | Red alert |
| 11.6 | Cookie / Tracking Consent Rules | Consent-based (similar to GDPR) | Info card |
| 11.7 | Advertising Standards / Restrictions | No misleading claims; ASCI guidelines | Checklist |
| 11.8 | Product Labeling Requirements | MRP, manufacturing date, FSSAI (food), BIS (electronics) | Checklist |
| 11.9 | Prohibited / Restricted Items for Sale | Alcohol, tobacco, weapons, certain drugs | Red alert box |
| 11.10 | Intellectual Property / Trademark Laws | Trademark Act 1999; strict on counterfeits | Info card |
| 11.11 | Anti-Trust / Competition Law | Competition Act 2002 – no predatory pricing | Alert |
| 11.12 | GST Invoice Requirements | Mandatory GSTIN on all invoices | Checklist |
| 11.13 | Foreign Exchange Regulations (FEMA) | RBI guidelines on cross-border payments | Alert |
| 11.14 | Age Verification Requirements | 18+ for certain products (alcohol, tobacco) | Tag |
| 11.15 | Environmental / E-Waste Regulations | E-waste management rules apply to electronics | Info card |

---

## 🗂️ MODULE 12: LANGUAGE & COMMUNICATION

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 12.1 | Official Language(s) | Hindi, English | Tag badges |
| 12.2 | Regional / State Languages | Tamil, Telugu, Bengali, Marathi, etc. (22 scheduled) | Expandable list |
| 12.3 | Primary E-commerce Language | English + Hindi (Hinglish) | Highlighted |
| 12.4 | Localization Requirement | Product descriptions in 5+ languages for reach | Checklist |
| 12.5 | Script / Writing System | Devanagari, Tamil, Bengali scripts | Visual samples |
| 12.6 | Number / Date Format | DD/MM/YYYY; Indian numbering (Lakh, Crore) | Info card |
| 12.7 | Measurement System | Metric (kg, cm, liters) | Tag |
| 12.8 | Customer Support Language Expectation | Hindi + English minimum; regional preferred | Alert |
| 12.9 | RTL (Right-to-Left) Requirement | No (but YES for Arabic/Urdu markets) | Boolean flag |
| 12.10 | Tone / Formality in Communication | Formal with elders; casual with Gen-Z | Info card |

---

## 🗂️ MODULE 13: COMMUNITY & SOCIAL STRUCTURE

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 13.1 | Family Structure | Joint family common; nuclear growing in cities | Info card |
| 13.2 | Decision-Making Unit | Family / household (not individual) | Tag |
| 13.3 | Caste / Class Sensitivity | Sensitive topic – avoid in marketing | Red alert |
| 13.4 | Gender Roles in Purchasing | Women: household, fashion; Men: electronics, auto | Info card |
| 13.5 | Community / Group Buying Culture | WhatsApp groups for deals; community buying | Tag |
| 13.6 | Influencer / Celebrity Impact | VERY HIGH – Bollywood, cricket stars, YouTubers | Rating |
| 13.7 | Religious / Cultural Sensitivities | Avoid beef imagery, respect festivals, modesty norms | Red alert box |
| 13.8 | Festival Gifting Culture | Diwali, Raksha Bandhan – massive gifting demand | Highlighted |
| 13.9 | Trust in Word-of-Mouth | EXTREMELY HIGH – personal recommendations > ads | Rating |
| 13.10 | Review / Rating Culture | Growing – read reviews but write fewer | Gauge |

---

## 🗂️ MODULE 14: MARKETING & ADVERTISING LANDSCAPE

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 14.1 | Most Effective Ad Channel | YouTube video ads, Instagram Reels | Ranked list |
| 14.2 | Influencer Marketing Effectiveness | HIGH – micro-influencers (10K-100K) best ROI | Rating |
| 14.3 | Email Marketing Effectiveness | LOW – 2-5% open rate | Warning |
| 14.4 | WhatsApp Marketing | VERY HIGH – primary communication channel | Highlighted |
| 14.5 | SMS Marketing | MEDIUM – OTP + offers still work | Tag |
| 14.6 | TV / Traditional Media Impact | Still HIGH in Tier 2/3 cities | Info card |
| 14.7 | Affiliate Marketing Maturity | Growing – CouponDunia, GoPaisa | Tag |
| 14.8 | SEO / Organic Search Behavior | Google search in English + Hindi | Info card |
| 14.9 | Ad Spend Per Capita | $3-$5 annually | Stat card |
| 14.10 | Best Time to Run Ads | 7 PM - 11 PM; Weekends | Clock visual |
| 14.11 | Content Format Preference | Short video (Reels/Shorts) > Images > Text | Ranked |
| 14.12 | Loyalty / Rewards Program Response | HIGH – cashback, points, coupons loved | Tag |

---

## 🗂️ MODULE 15: COMPETITION & MARKET LANDSCAPE

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 15.1 | Top 5 E-commerce Platforms | Amazon, Flipkart, Meesho, Myntra, Nykaa | Ranked cards |
| 15.2 | Market Share Breakdown | Amazon 30%, Flipkart 28%, Others 42% | Pie chart |
| 15.3 | Niche / Vertical Players | Nykaa (beauty), PharmEasy (health), BigBasket (grocery) | Tag list |
| 15.4 | Social Commerce Platforms | Meesho, Instagram Shopping, WhatsApp Business | Tags |
| 15.5 | D2C Brand Ecosystem | Growing – Mamaearth, boAt, Sugar | Info card |
| 15.6 | Price Comparison Behavior | HIGH – use PriceDekho, MySmartPrice | Alert |
| 15.7 | Market Entry Barriers | FDI restrictions, local competition, logistics | Checklist |
| 15.8 | White Space / Untapped Niches | Tier 3 cities, vernacular commerce, B2B | Opportunity cards |

---

## 🗂️ MODULE 16: CUSTOMER SERVICE EXPECTATIONS

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 16.1 | Preferred Support Channel | WhatsApp > Phone > Email > Chat | Ranked list |
| 16.2 | Expected Response Time | < 2 hours (WhatsApp); < 24 hrs (email) | SLA card |
| 16.3 | Language for Support | Hindi + English minimum | Tag |
| 16.4 | Return / Refund Expectation | 7-10 day no-questions return | Info card |
| 16.5 | Compensation Culture | Expect discount/coupon for inconvenience | Tag |
| 16.6 | Social Media Complaint Behavior | HIGH – public shaming on Twitter/X common | Alert |
| 16.7 | Warranty / Guarantee Expectation | 1-year standard for electronics | Info card |
| 16.8 | After-Sales Service Importance | VERY HIGH – installation, setup support | Rating |

---

## 🗂️ MODULE 17: TECHNOLOGY & INFRASTRUCTURE

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 17.1 | Cloud / Hosting Regulations | Data must be stored in-country (for some sectors) | Alert |
| 17.2 | CDN / Server Location Recommendation | Mumbai, Delhi, Bangalore data centers | Map pins |
| 17.3 | App Store Preferences | Google Play dominant (95%+) | Stat |
| 17.4 | PWA vs Native App Preference | App preferred; PWA for low-storage users | Info card |
| 17.5 | Browser Usage | Chrome 90%+, Safari 5% | Pie chart |
| 17.6 | Screen Size / Resolution Common | 6.1"-6.7" smartphones dominant | Info card |
| 17.7 | Low-Bandwidth Optimization Need | YES – 40%+ on 3G/4G in rural | Alert |
| 17.8 | UPI / API Integration Standards | NPCI guidelines for UPI | Technical doc link |

---

## 🗂️ MODULE 18: NEWS & CURRENT CONTEXT

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 18.1 | Current Economic News | Inflation trends, RBI rate decisions | News feed card |
| 18.2 | Political Stability | Stable / Election year / Unrest | Status badge (🟢🟡🔴) |
| 18.3 | Recent Regulatory Changes | New e-commerce rules, tax amendments | Alert feed |
| 18.4 | Natural Disasters / Disruptions | Monsoon floods, pandemic impact | Warning banner |
| 18.5 | Consumer Sentiment Index | Optimistic / Cautious / Pessimistic | Gauge |
| 18.6 | Trending Products / Viral Items | Current viral product categories | Trending tags |
| 18.7 | Exchange Rate Volatility (Current) | Stable / Volatile | Sparkline |

---

## 🗂️ MODULE 19: RISK & COMPLIANCE MATRIX

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 19.1 | Fraud / Chargeback Rate | MEDIUM-HIGH (COD rejections 15-20%) | Risk meter |
| 19.2 | Counterfeit Product Prevalence | HIGH in fashion, electronics | Alert |
| 19.3 | Cybersecurity Threat Level | MEDIUM | Risk badge |
| 19.4 | Sanctions / Trade Restrictions | None / Partial / Full | Status badge |
| 19.5 | Political Risk to Business | LOW / MEDIUM / HIGH | Traffic light |
| 19.6 | Currency Risk (Repatriation) | LOW – freely convertible | Tag |
| 19.7 | Legal Dispute Resolution | Arbitration preferred; slow courts | Info card |

---

## 🗂️ MODULE 20: STRATEGIC RECOMMENDATIONS (AI-Generated)

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 20.1 | Market Entry Strategy | Start with Metro cities → expand Tier 2 | Roadmap |
| 20.2 | Pricing Strategy | Competitive + heavy discounting initially | Info card |
| 20.3 | Recommended Product Mix | Fashion + Electronics + Beauty first | Priority list |
| 20.4 | Recommended Payment Stack | UPI + COD + Cards + BNPL | Checklist |
| 20.5 | Recommended Marketing Mix | 60% Social, 20% Influencer, 10% SEO, 10% Email | Pie chart |
| 20.6 | Localization Priority | Hindi → Tamil → Telugu → Bengali | Ordered list |
| 20.7 | Key Success Factors | Free shipping, COD, fast delivery, WhatsApp support | Checklist |
| 20.8 | Key Risks to Mitigate | COD rejection, returns, regulatory changes | Alert list |
| 20.9 | Estimated Time to Profitability | 18-24 months | Timeline |
| 20.10 | Recommended Budget Allocation | Marketing 40%, Logistics 25%, Tech 20%, Ops 15% | Pie chart |

---

## 🎨 PRESENTATION FORMAT GUIDE

### For Backend / Database (JSON Structure)
```
{
  "country_code": "IN",
  "modules": {
    "identity": { ... },
    "demographics": { ... },
    "economy": { ... },
    "tax": { ... },
    "psychology": { ... },
    "consumption": { ... },
    "seasonality": { ... },
    "digital": { ... },
    "payments": { ... },
    "logistics": { ... },
    "legal": { ... },
    "language": { ... },
    "community": { ... },
    "marketing": { ... },
    "competition": { ... },
    "customer_service": { ... },
    "technology": { ... },
    "news": { ... },
    "risk": { ... },
    "strategy": { ... }
  },
  "last_updated": "2026-07-25",
  "data_sources": ["REST Countries API", "World Bank", "OpenAI Research"]
}
```

### For Admin Dashboard (UI Presentation)

| Element | Use For |
|---------|---------|
| **Stat Cards** (big number + label) | Population, GDP, Tax Rate, AOV |
| **Gauge / Progress Bars** | Internet penetration, Price sensitivity, Trust levels |
| **Pie / Donut Charts** | Age distribution, Payment split, Market share |
| **Ranked Lists** | Top cities, Top payment methods, Top categories |
| **Traffic Light Badges** (🟢🟡🔴) | Risk levels, Political stability, Compliance status |
| **Alert Boxes** (Red/Yellow) | Legal restrictions, COD %, Data localization |
| **Calendar / Timeline** | Shopping festivals, Seasons, Peak hours |
| **Comparison Tables** | Urban vs Rural, Gen-Z vs 40+, Local vs Foreign |
| **Checklists** | Compliance requirements, Registration steps |
| **Map Overlays** | Warehouse hubs, Delivery zones, City targeting |
| **Trend Sparklines** | Currency, GDP growth, Inflation |
| **Tag Clouds / Chips** | Languages, Platforms, Product categories |
| **Narrative Cards** | Psychology, Mindset, Cultural notes |

### For E-commerce System Integration

| Data Point | System Use |
|-----------|------------|
| Currency + Exchange Rate | Dynamic pricing, checkout display |
| Tax Slabs | Cart tax calculation |
| Payment Methods | Checkout gateway selection |
| COD % | Enable/disable COD option |
| Language | UI localization, product descriptions |
| Cities | Shipping zone configuration |
| Return Window | Return policy display |
| Prohibited Items | Product listing filters |
| Peak Hours | Ad scheduling, server scaling |
| Size Preferences | Size chart localization |
| Festival Calendar | Automated sale campaigns |

---

## 📊 SUMMARY: 20 MODULES × ~200+ DATA POINTS

| Module | Data Points | Priority |
|--------|------------|----------|
| 1. Country Identity | 14 | 🔴 Critical |
| 2. Demographics | 12 | 🔴 Critical |
| 3. Economy & Wealth | 17 | 🔴 Critical |
| 4. Tax & Duties | 14 | 🔴 Critical |
| 5. Consumer Psychology | 15 | 🔴 Critical |
| 6. Consumption Preferences | 13 | 🔴 Critical |
| 7. Shopping Seasonality | 10 | 🟡 High |
| 8. Digital Landscape | 12 | 🔴 Critical |
| 9. Payment Infrastructure | 14 | 🔴 Critical |
| 10. Logistics & Shipping | 13 | 🔴 Critical |
| 11. Legal & Regulations | 15 | 🔴 Critical |
| 12. Language & Communication | 10 | 🟡 High |
| 13. Community & Social | 10 | 🟡 High |
| 14. Marketing Landscape | 12 | 🟡 High |
| 15. Competition | 8 | 🟡 High |
| 16. Customer Service | 8 | 🟡 High |
| 17. Technology | 8 | 🟢 Medium |
| 18. News & Context | 7 | 🟢 Medium |
| 19. Risk & Compliance | 7 | 🟡 High |
| 20. Strategic Recommendations | 10 | 🟢 Medium |

---

This is your **complete master blueprint**. You can now feed this exact structure into the Python script's AI prompt to generate a fully populated JSON report for any country, and build your e-commerce admin dashboard around these 20 modules. Want me to update the Python script to cover **all 20 modules** in the API prompt?



# _____________________________________________________________________________________________ Details of COUNTRY NEEDED

# _____________________________________________________________________________________________ Cash Management & Payment Management Cycle
## Audit Cash Management and Payment Management Cycle

- List down all the File and Function of `frontend/web_app`, `frontend/mobile_app`, `backend`, `backend API`, `Database setup` for `Cash and Payment Management Cycle` in detail and test all the files and update the `CODEBASE_STATUS_MATRIX_DETAILED.md` because this the document from which we are following for completing the project.

- Investigate and Audit in detial and Review each and every element of the `Cash and Payment Management Cycle` and findout what are actually the problems and issues in the `Cash and Payment Management Cycle` and list down all the problems and issues in detail and start to work on it one by one and make sure all the functions are working properly in the `Cash and Payment Management Cycle` and also make sure it is efficient, secure, scalable, reliable, maintainable and well documented as well.

- The Target ressult `Cash and Payment Management Cycle` should be:
    - Admin Panel : Admin will put the Bank Account details and updated Bank Statement. 
        - it will automatically start the `payout system` and also for the `reconciliation process` and also for the refund process and etc.
        - Logistic Partner will receive the cash on delivery from the customer and then it will automatically start the `reconciliation process` for the cash on delivery and also for the payout system for the logistic partner and also for the refund process and etc.
        - Supplier will receive the payment from the Zozi Management for the order completion and delivery and then it will automatically start the `reconciliation process` for the payment and also for the payout system for the supplier and also for the refund process and etc.
    - Customer Panel : Customer will make the payment by card and then it will automatically start the `reconciliation process` for the pay by card and also for the refund process and etc.
    - Reconciliation Process : it will automatically reconcile with the Bank System -> Supplier Payout -> Logistic Partner Payout -> Cash on Delivery Reconciliation -> Pay by Card Reconciliation -> Refund Reconciliation -> Payout Reconciliation -> etc.
    - Payout System : it will automatically payout to the Supplier and Logistic Partner based on the order completion and delivery and also based on the cash on delivery and pay by card and also based on the refund process and etc.
    - Refund Process : it will automatically manage the refund process for the customer and also for the Supplier and Logistic Partner based on the order cancellation and refund process and also based on the cash on delivery and pay by card and also based on the reconciliation process and etc.

- Test everything for the `Cash and Payment Management Cycle` and make sure all the functions are working properly in the `Cash and Payment Management Cycle` and also make sure it is efficient, secure, scalable, reliable, maintainable and well documented as well.

- Potential Problem: 
    - How it will connect with real bank account even if I give you real bank account details ?

# _____________________________________________________________________________________________ Cash Management & Payment Management Cycle


# _____________________________________________________________________________________________ Automation List

---

	# 1. Workflow Automation Engine (Highest Priority)

	* [ ] Visual workflow builder
	* [ ] Trigger → Condition → Action
	* [ ] Manual approval step
	* [ ] Parallel workflow support
	* [ ] Scheduled workflow support
	* [ ] Workflow versioning

	---

	# 2. Event Engine

	* [ ] Event publisher
	* [ ] Event subscriber
	* [ ] Event queue
	* [ ] Retry mechanism
	* [ ] Dead-letter queue
	* [ ] Event monitoring

	---

	# 3. Notification Engine

	* [ ] Email
	* [ ] SMS
	* [ ] WhatsApp
	* [ ] Push notification
	* [ ] In-app notification
	* [ ] Notification templates
	* [ ] Retry failed notifications

	---

	# 4. Scheduled Jobs Engine

	* [ ] Cron jobs
	* [ ] Recurring jobs
	* [ ] Delayed jobs
	* [ ] One-time jobs
	* [ ] Job history
	* [ ] Job monitoring

	---

	# 5. Approval Engine

	* [ ] Single approval
	* [ ] Multi-level approval
	* [ ] Auto approval rules
	* [ ] Escalation
	* [ ] Approval history

	---

	# 6. Rule Engine

	* [ ] Business rules
	* [ ] Country rules
	* [ ] Supplier rules
	* [ ] Customer rules
	* [ ] Promotion rules
	* [ ] Logistics rules

	---

	# 7. Assignment Engine

	* [ ] Delivery assignment
	* [ ] Support ticket assignment
	* [ ] Complaint assignment
	* [ ] Task assignment
	* [ ] Load balancing

	---

	# 8. Reminder Engine

	* [ ] Payment reminders
	* [ ] KYC reminders
	* [ ] Expiry reminders
	* [ ] Follow-up reminders
	* [ ] Renewal reminders

	---

	# 9. Escalation Engine

	* [ ] SLA monitoring
	* [ ] Auto escalation
	* [ ] Escalation levels
	* [ ] Manager notification

	---

	# 10. Finance Automation

	* [ ] Auto journal posting
	* [ ] Auto commission calculation
	* [ ] Auto settlement
	* [ ] Auto payout
	* [ ] Auto reconciliation
	* [ ] Auto refund posting

	---

	# 11. Inventory Automation

	* [ ] Stock updates
	* [ ] Low stock alerts
	* [ ] Out-of-stock handling
	* [ ] Auto stock reservation
	* [ ] Inventory synchronization

	---

	# 12. Order Automation

	* [ ] Order validation
	* [ ] Supplier routing
	* [ ] Split order handling
	* [ ] Order status updates
	* [ ] Return workflow

	---

	# 13. Logistics Automation

	* [ ] Delivery assignment
	* [ ] Route optimization
	* [ ] Pickup scheduling
	* [ ] Delivery tracking
	* [ ] POD verification
	* [ ] COD reconciliation

	---

	# 14. AI Automation

	* [ ] Product description generation
	* [ ] Product categorization
	* [ ] Image optimization
	* [ ] Duplicate detection
	* [ ] Content moderation

	---

	# 15. Data Automation

	* [ ] Import jobs
	* [ ] Export jobs
	* [ ] Data cleanup
	* [ ] Archive old records
	* [ ] Backup verification

	---

	# 16. Security Automation

	* [ ] Login monitoring
	* [ ] Suspicious activity detection
	* [ ] Account lock
	* [ ] Session cleanup
	* [ ] API monitoring

	---

	# 17. Customer Automation

	* [ ] Welcome journey
	* [ ] Cart abandonment
	* [ ] Review requests
	* [ ] Loyalty rewards
	* [ ] Re-engagement campaigns

	---

	# 18. Supplier Automation

	* [ ] KYC workflow
	* [ ] Store approval
	* [ ] Product approval
	* [ ] Performance alerts
	* [ ] Payout notifications

	---

	# 19. Admin Automation

	* [ ] Dashboard alerts
	* [ ] Health monitoring
	* [ ] Error reporting
	* [ ] Daily summary
	* [ ] Weekly summary

	---

	# 20. Monitoring & Recovery

	* [ ] Automation logs
	* [ ] Failure alerts
	* [ ] Retry queue
	* [ ] Execution history
	* [ ] Performance metrics

	---

	## Platform-Level Suggestions (High Value)

	* [ ] Central Automation Dashboard
	* [ ] Global Automation Settings
	* [ ] Enable/Disable per automation
	* [ ] Execution priority
	* [ ] Dependency management
	* [ ] Dry-run/Test mode
	* [ ] Audit trail
	* [ ] Version control
	* [ ] Role-based permissions
	* [ ] API-triggered automations

	---

	## Priority Order

	1. Workflow Engine
	2. Event Engine
	3. Rule Engine
	4. Notification Engine
	5. Scheduled Jobs Engine
		6. Finance Automation
	7. Order Automation
	8. Logistics Automation
	9. Inventory Automation
	10. Approval Engine
	11. Assignment Engine
	12. Monitoring & Recovery
	13. AI Automation
	14. Security Automation
	15. Customer & Supplier Automation

	This order gives you a reusable automation foundation before implementing feature-specific workflows, reducing duplicated logic across the platform.

# _____________________________________________________________________________________________ Automation List

# _____________________________________________________________________________________________ Supplier Product Upload

### Supplier/ upload product 
	http://localhost:3000/supplier/products/add
	Supplier-Panel/ Upload Product Page:

	Automation should take place more rather then typing.

	Supplier/ upload product 
		1. Popup of image file upload or capture, [ Once Supplier will upload the image one by one and video or capture ] then
		2. Popup will have icon of [ Mic ~ for voice Detail, 
								Magic Photo Editing Icon ~ for Photo Editing ]
			2a. if Supplier will press on `Mic` then 
				Voice recognition and distribution of data according to the voice note will be handle. 
				Suppose, Supplier said : "A T-shirt - 4 color = blue, yellow, black, white, having print [I love Oman] "
					Then system will handle everything from here by automation 
						Description: automatic detected
						Tag: automatic detected
						Name of product: automatic
						Cloth Fabric : ask by supplier by popup - [giving all kind of cloths which can be able for ticking anyone]
						Quantity: ask by supplier by popup 
							1st popup : 
											Blue S = [ ? ], 
											Blue M = [ ? ],
											Blue L = [ ? ],
											Blue XL = [ ? ],
							2nd popup : 
											Yellow S = [ ? ], 
												Yellow M = [ ? ],
											Yellow L = [ ? ],
											Yellow XL = [ ? ],
							
						Total Quantity: System will detect by itself
						Price: Popup will come and Supplier will enter.	
			
					Popup: for verification of all details then at bottom there is 3 button [ Edit Details, Upload, Edit Images]
						if Supplier selects `Edit Detail` 
							then he can edit by himself
						if Supplier selects `Upload` 
							then upload product and give finish message `Thank You to using ZOZI`
						if Supplier selects `Edit Images` then Popup appear of canvas of Image Editing.
							all the option will be appear on it of the Canvas 
								When the supplier will satisfy then he will press 'Done' button
									Popup: for verification of all details then at bottom there is 3 button [ Edit Details, Upload, Edit Images]
										Supplier will press `Upload` and Finish everything and upload will process.

			2b. if Supplier will press on `Magic Photo Editing` then 
				all the option will be appear on it of the Canvas 
					when supplier will done `Edit Photo` then 
						automatically detected and there is also option of voice details.
							Description: 	automatic detected
							Tag: 		automatic detected
							Name of product: automatic detected
							Color: 		automatic-detected 
								Popup appeared for more color to select, and type also

							Cloth Fabric : ask by supplier by popup - [giving all kind of cloths which can be able for ticking anyone]
							Quantity: ask by supplier by popup 
							1st popup : 
											Blue S = [ ? ], 
											Blue M = [ ? ],
											Blue L = [ ? ],
											Blue XL = [ ? ],
							2nd popup : 
											Yellow S = [ ? ], 
												Yellow M = [ ? ],
											Yellow L = [ ? ],
											Yellow XL = [ ? ],
							
						Total Quantity: System will detect by itself
						Price: Popup will come and Supplier will enter.	
			
					Popup: for verification of all details then at bottom there is 3 button [ Edit Details, Upload, Edit Images]
						if Supplier selects `Edit Detail` 
							then he can edit by himself
						if Supplier selects `Upload` 
							then upload product and give finish message `Thank You to using ZOZI`
						if Supplier selects `Edit Images` then Popup appear of canvas of Image Editing.
							all the option will be appear on it of the Canvas 
								When the supplier will satisfy then he will press 'Done' button
									Popup: for verification of all details then at bottom there is 3 button [ Edit Details, Upload, Edit Images]
										Supplier will press `Upload` and Finish everything and upload will process.
				



## Implementation Plan: ZOZI Supplier Product Upload — Speed-First Redesign

## Goal
Re-engineer the supplier product-upload flow into a modal-popup-driven, automation-first 5-step system
that completes a full product upload (including BG removal, AI analysis, all variant quantity fills,
and publish) **in under 30 seconds** for an experienced supplier.

---

## Overview of the Two Processes

| | Process A — Photo-First | Process B — Voice-First |
|---|---|---|
| Step 1 | Upload / Capture image | Upload / Capture image |
| Step 2 | BG Removal (auto-select best model) | BG Removal (auto-select best model) |
| Step 3 | AI detect → auto-fill all fields | 🎤 Voice note → NLP parse → auto-fill |
| Step 4 | Variant-per-color quantity popups | Variant-per-color quantity popups |
| Step 5 | Verify popup → Publish | Verify popup → Publish |

---

## Design Principles
- **Zero typing** wherever automation can fill it (name, description, tags, category, color).
- **Modal-popup-driven** — every step is a focused bottom-sheet / center modal, not a multi-page wizard.
- **Parallel processing** — BG removal fires simultaneously with AI analysis; both finish before Step 3.
- **Quantity popups per color** — one popup per color, looping through colors, each showing all sizes.
- **Universal variant support** — driven by `zozi_variant_config.json`: apparel (color/size), electronics
  (storage/RAM), beauty (volume/scent), jewelry (karat/plating), etc.

---

## Step-by-Step UI Flow

```
[ADD PRODUCT button]
        ↓
┌─────────────────────────────────────────────────────────────────┐
│  MODAL 1 — MEDIA UPLOAD                                         │
│  [ 📷 Take Photo ]  [ 🗂️ Upload File ]                          │
│  ┌────────────────┐                                             │
│  │  image preview │  (thumbnail once selected)                  │
│  └────────────────┘                                             │
│  [ 🎤 Voice Note ]  [ ✨ Magic Editing ]                         │
│                             [Next →]                            │
└─────────────────────────────────────────────────────────────────┘
        ↓ (Next fires PARALLEL: bg-removal + AI-analyze)
┌─────────────────────────────────────────────────────────────────┐
│  MODAL 2A — PROCESSING (spinner)                                │
│  "Removing background…  ████████░░  80%"                        │
│  "Analyzing product…    ████░░░░░░  40%"                        │
│  (both run in parallel — typical total: 5-8 s)                 │
└─────────────────────────────────────────────────────────────────┘
        ↓ AI fills everything automatically
┌─────────────────────────────────────────────────────────────────┐
│  MODAL 2B — PHOTO EDITING CANVAS (optional, tap ✨)             │
│  [ br05 Clean ][ br06 Geo ][ br08 Prod ][ br11 Gap ]           │
│  [ Sharpen ][ Denoise ][ White Balance ][ Auto Light ]          │
│  [ Done ✓ ]                                                     │
└─────────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────────┐
│  MODAL 3 — AI RESULTS + FIELD REVIEW                            │
│  Name:        [Auto-filled ✓]  [edit]                           │
│  Description: [Auto-filled ✓]  [edit]                           │
│  Category:    [Auto-filled ✓]  [change ▾]                       │
│  Tags:        [chip][chip][chip]  [+ add]                       │
│  Color(s):    [🔵 Blue][🟡 Yellow][➕ Add color]               │
│  Fabric/Type: [tap chips: Cotton / Polyester / Leather…]        │
│  Price:       [ OMR _____ ]  (AI suggests 5.000)               │
│                         [Next: Set Quantities →]                │
└─────────────────────────────────────────────────────────────────┘
        ↓ (one popup per color, cycling)
┌─────────────────────────────────────────────────────────────────┐
│  MODAL 4A — QUANTITY: 🔵 BLUE                (1 of 4)           │
│  S  [____]   M  [____]   L  [____]   XL [____]                 │
│  XXL [____]  (only sizes relevant to category shown)            │
│  [ Fill All = 50 ]              [Next Color →]                  │
└─────────────────────────────────────────────────────────────────┘
│  MODAL 4B — QUANTITY: 🟡 YELLOW              (2 of 4)           │
│  …same layout…                  [Next Color →]                  │
└─────────────────────────────────────────────────────────────────┘
        ↓ (electronics: storage×RAM instead; beauty: volume/scent, etc.)
┌─────────────────────────────────────────────────────────────────┐
│  MODAL 5 — FINAL REVIEW & PUBLISH                               │
│  ┌──────────┐   Product: "Blue T-Shirt I Love Oman"             │
│  │ image ✓  │   Category: Clothing → T-Shirts                   │
│  └──────────┘   Colors: Blue, Yellow, Black, White              │
│                 Sizes: S, M, L, XL   Total Stock: 320           │
│                 Price: 5.000 OMR                                 │
│  [ ✏️ Edit Details ] [ 🖼️ Edit Images ] [ ✅ Publish ]          │
│        ↓ on Publish                                             │
│  "✅ Published! Thank you for using ZOZI"                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Files to Create / Modify

### Frontend — New Components

---

#### [NEW] `src/components/supplier/upload/UploadModal.tsx`
Single-entry modal covering Step 1 (file/camera input + Voice/Edit buttons).
- Accepts `onImage(file)`, `onVoice()`, `onEdit()` callbacks.
- Native `capture="environment"` for mobile camera.
- Drag-and-drop zone for desktop.

#### [NEW] `src/components/supplier/upload/ProcessingModal.tsx`
Dual progress-bar overlay shown during parallel BG removal + AI analysis.
- Two `<progress>` bars driven by SSE or polling.
- Auto-closes when both complete; passes results up.

#### [NEW] `src/components/supplier/upload/PhotoEditModal.tsx`
Full-screen canvas panel (already partially exists as `PhotoEditorModal.tsx` — refactor/extend).
- Integrates all 6 BG models (br05–br13) as one-tap buttons.
- Image tool strip (sharpen, denoise, white balance, etc.).
- "Done ✓" closes and returns processed blob.

#### [NEW] `src/components/supplier/upload/AIResultsModal.tsx`
Step 3 field-review modal.
- Shows all AI-filled fields as editable inline items.
- Color chip selector (auto-detected + add more).
- Fabric/material chip grid (from `zozi_variant_config.json` categories).
- Price input with AI-suggested value pre-filled.
- "Next: Set Quantities →" button.

#### [NEW] `src/components/supplier/upload/QuantityModal.tsx`
Step 4 cycling quantity popup.
- Props: `colorName`, `colorIndex`, `totalColors`, `sizes[]`, `onComplete(qty: Record<size, number>)`.
- "Fill All = 50" shortcut button.
- Keyboard-friendly: Tab moves between size inputs, Enter advances to next color.
- For non-apparel: renders relevant variant axes (storage×RAM, volume, etc.).

#### [NEW] `src/components/supplier/upload/VerifyPublishModal.tsx`
Step 5 final review.
- Product image thumbnail + all details.
- Total stock auto-calculated.
- Three buttons: Edit Details → re-opens AIResultsModal; Edit Images → re-opens PhotoEditModal; Publish → POST + success screen.

#### [NEW] `src/components/supplier/upload/VoiceModal.tsx`
Dedicated voice-recording bottom sheet (Step 3 voice path).
- Waveform animation while recording.
- NLP parse result displayed as editable chips before confirming.

---

### Frontend — Core Logic

#### [NEW] `src/lib/uploadOrchestrator.ts`
Central state machine managing the entire 5-step flow.
```typescript
type UploadPhase =
  | 'idle' | 'media' | 'processing' | 'photo_edit'
  | 'ai_results' | 'quantity' | 'verify' | 'done';
```
- Fires parallel `Promise.all([removeBg(), analyzeImage()])` at end of Step 1.
- Caches results so re-opening any modal is instant.
- Tracks current color index for quantity loop.
- Computes `totalStock` reactively.

#### [MODIFY] `src/lib/variantEngine.ts`
Add `getVariantAxesForCategory(category, subcategory)` that reads the embedded
`zozi_variant_config.json` to return the correct variant axes and their default options
for every supported product type. This replaces the current hardcoded arrays.

#### [NEW] `src/lib/variantConfig.ts`
Typed wrapper around `zozi_variant_config.json` — exposes:
- `getAxesForCategory(cat, subcat)` → `VariantAxis[]`
- `getDefaultOptions(axisKey)` → `string[]`
- `detectAxesFromVoice(voiceResult)` → `VariantAxis[]`
- `getMaterialOptions(productType)` → `string[]`

#### [MODIFY] `src/lib/wizardStore.ts`
Add upload orchestrator state:
- `uploadPhase: UploadPhase`
- `currentColorIndex: number`
- `quantityMap: Record<color, Record<size, number>>`
- `detectedAxes: VariantAxis[]`

---

### Frontend — Page Update

#### [MODIFY] `src/app/supplier/products/add/page.tsx`
Replace the current inline two-column layout with a single **"Add Product" button**
that opens `UploadModal`. All subsequent steps are driven by the orchestrator modals,
not the scrollable page layout.

---

### Backend — AI & BG Removal

#### [MODIFY] `backend/routers/suppliers/supplier.py`
- `/supplier/upload/remove-background` — already exists ✓ (no change needed)
- `/supplier/upload/ai-analyze` — already exists ✓ (no change needed)
- `/supplier/upload/voice-transcribe` — already exists ✓

New endpoint needed:
#### `POST /supplier/upload/analyze-parallel`
Accepts multipart with `image` field. Runs BG removal **and** AI analysis in parallel
(using `asyncio.gather`) and returns combined JSON:
```json
{
  "bg_removed_url": "...",
  "name": "...", "category": "...", "tags": [...],
  "colors": [...], "variants": {...}, "price_suggestion": 5.0
}
```
This single call replaces two sequential round-trips, cutting Step 2 time by ~40%.

---

### Backend — Variant Config Integration

#### [NEW] `backend/services/suppliers/variant_config_service.py`
Loads `zozi_variant_config.json` at startup and exposes:
- `get_axes_for_category(category, subcategory)` — returns applicable axes
- `get_material_options(product_type)` — chips for the fabric/material picker

#### [NEW] `GET /supplier/upload/variant-axes?category=clothing&subcategory=t-shirts`
Returns the correct axes + default options for the frontend to render quantity modals
correctly for any product type (apparel, electronics, beauty, jewelry, etc.).

---

### Playwright Test Suite

#### [NEW] `backend/tests/playwright/conftest.py`
- `login_as_supplier` fixture (re-uses token for session).
- `backend_url` fixture reading from env.
- `cleanup_product(id)` fixture calling `DELETE /supplier/products/{id}`.

#### [NEW] `backend/tests/playwright/test_upload_flow.py`
Tests **both** Process A (photo) and Process B (voice):
```
test_photo_upload_flow   — uploads image_04.jpg, bg removal, AI fill, qty, publish
test_voice_upload_flow   — uploads image_05.jpg, voice transcribe, field fill, publish
test_all_category_axes   — verifies correct axes rendered for clothing/electronics/beauty/jewelry
```

#### [MODIFY] `backend/requirements.txt`
Add `playwright>=1.40.0` and `pytest-playwright>=0.4.0`.

#### [NEW] `backend/scripts/run_playwright_tests.py`
```python
subprocess.run(["playwright", "install", "chromium"])
subprocess.run(["pytest", "tests/playwright/", "-v", "--headed=false"])
```

---

## Speed Budget (target ≤ 30 s total)

| Step | Action | Time |
|---|---|---|
| 1 | Image selected | < 1 s |
| 2 | Parallel BG removal + AI analysis | 5–8 s |
| 3 | Review AI fields (pre-filled, just glance) | 3–5 s |
| 4 | Quantity popups × N colors (Fill All = 50) | 2 s × N colors |
| 5 | Verify + Publish click + server response | 2–3 s |
| **Total (2 colors)** | | **~18 s** |
| **Total (4 colors)** | | **~26 s** |

> [!IMPORTANT]
> The "Fill All = 50" button on each quantity popup fills all size inputs at once — a supplier
> with 4 colors can complete Step 4 in 4 × 1 tap = 4 seconds total.

---

## Verification Plan

### Automated Tests
```bash
cd backend
python scripts/run_playwright_tests.py
```
- All 3 test cases pass (exit 0).
- Product appears in `GET /supplier/products` after publish.
- Product is deleted by cleanup fixture.

### Manual Verification
- Open `http://localhost:3000/supplier/products/add`.
- Click "Add Product" → modal appears (Step 1).
- Upload `D:\Projects\10- E-COMMERCE WEBSITE\zozi\image\image_04.jpg`.
- Confirm processing modal shows dual progress bars.
- Confirm AI fills name, category, tags, colors automatically.
- Fill quantities via color popups using "Fill All = 50".
- Publish → "Thank you for using ZOZI" screen appears.
- Navigate to `/supplier/products` → product visible in list.



┌─ Upload ──────────────────────────────────────────┐
│  Drag-and-drop or file picker (JPG/PNG/WebP)      │
│  Validates type + size (10 MB max)                 │
└────────────────────────┬──────────────────────────┘
                         │
┌─ Category Selector ───────────────────────────────┐
│  Clothing │ Electronics │ Beauty │ Not specified   │
│  └── Drives "Best" badge per strategy             │
└────────────────────────┬──────────────────────────┘
                         │
┌─ "Run All 6" ─────────────────────────────────────┐
│  Parallel Promise.all → 6× POST /remove-background │
│  Each: 120s timeout, timing tracked per strategy   │
│  Results: { blob, url, timing, error? }            │
└────────────────────────┬──────────────────────────┘
                         │
┌─ View Modes ──────────────────────────────────────┐
│  [Grid] [Side-by-side] [Diff]                     │
│                                                    │
│  ┌─ Grid (default) ────── 3 cols ──────────────┐ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐      │ │
│  │  │ Clean·05 │ │ Geom·06  │ │ Prod·08  │      │ │
│  │  │  Ⓡ Best  │ │ 2,341ms  │ │  ERROR   │      │ │
│  │  │ Δ 12.3%  │ │ Δ 8.1%   │ │  ...     │      │ │
│  │  └──────────┘ └──────────┘ └──────────┘      │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐      │ │
│  │  │ Gaps·11  │ │ Mkt·12   │ │ Lite·13  │      │ │
│  │  │ ...      │ │ ...      │ │ ...      │      │ │
│  │  └──────────┘ └──────────┘ └──────────┘      │ │
│  └──────────────────────────────────────────────┘ │
└────────────────────────┬──────────────────────────┘
                         │
┌─ RGBA Diff Engine ─────────────────────────────────┐
│  Canvas-based pixel comparison:                    │
│  🟢 Green  = identical pixels                     │
│  🔴 Red    = RGB differs                          │
│  🔵 Blue   = alpha differs                        │
│  🟡 Yellow = both differ                          │
│                                                    │
│  Threshold: >8 intensity steps = "differs"        │
│  Metrics: Δ total %, RGB %, alpha %               │
└────────────────────────┬──────────────────────────┘
                         │
┌─ Expandable Cards ────────────────────────────────┐
│  Click ▶ on any strategy to reveal:               │
│  ┌─ Original │ Result │ Diff ──── 3-up view ──┐  │
│  │   [img]   │ [img]  │ [canvas diff overlay] │  │
│  └─────────────────────────────────────────────┘  │
│  Plus: Legend popup explaining color coding       │
└───────────────────────────────────────────────────┘

# _____________________________________________________________________________________________ Supplier Product Upload

# _____________________________________________________________________________________________ Logistic Panel

## Logistic Panel | Profile Page | Cities - Countries and Charges Management which will be reflect to customer order and cart system:

- Read the codebase in detail and list down all the file and Function for Logistic Panel.

- Read the Supplier Panel Profile Page code for your reference and make the Logistic Panel Profile Page in detail with all the necessary functions and UI/UX and test it properly backend and frontend both.

- Logistic Panel should have the option to manage cities, countries and charges which will be reflect to customer order and cart system and that will be reflect into all the order management system. implement it and test it properly backend and frontend both.

- Admin Panel will have for approval to accept the Logistic Partner Charges and Cities and Countries management and also for the approval of Logistic Partner Profile. 

- http://localhost:3000/logistics-partner/ 

- this is very tricky and important part of the system so please make sure to implement it properly and test it properly backend and frontend both and verifiy Order and Cart System reflection becasue it is linked with the `location` and `GPS system` becasue it is wokring cities and countries. Admin must to accept the charges which is giving by the logistic partner then it should be complete the process and reflect to the order and cart system. if admin reject the charges then it should not be reflect to the order and cart system. and also logistic partner profile must be approved by admin then only it should be visible to the customers and also in the search result when customer search for logistic partner.

- according to `ORDER_MANAGEMENT.md` system when the Supplier will complete preperation of the order means point number 3 and 4. if the Admin reject the logistic partner changes then it should not be flash the order in the partner shipment page `http://localhost:3000/logistics-partner/shipments`.

- make a complete plan, checkpoint, test before implementation and after implementation and start to work on it.


# _____________________________________________________________________________________________ Logistic Panel

# _____________________________________________________________________________________________ Payment Engine

## Payment Management System | Cash on Delivery | Pay by Card | Payout System of Supplier and Logistic Partner:

let's get back to cash management system of the ZOZI website.
There is 2 ways to payment "Cash on Delivery" and "Pay by Card"

- "Cash On Delivery" will receive by the Logistic Partner which is last end.
- "Pay by Card" will receive by the Zozi Management.

Now the point is how we will manage efficiently and track cash appropriately ?

Every Order have 4 components:
    1. Product Price.
    2. Delivery Charges. - which have 2 changes Pick-Up Charges and Drop-Off Charges. 
    3. VAT - 5% of the Product Price and Delivery Charges.
    4. ZOZI Service Charges - 10% to 20% of the Product Price.


## Problem 1: 
    When Logistic Partner receive cash on delivery from the customer then how Zozi Management will ask the Delivery Charges from the Logistic Partner and Logistic Partner never pay it back to the Zozi Management becasue it is their charges to keep with them.

## Problem 2: 
    How can we reconcile Management automatically and Payout System will work automatically for the Supplier and Logistic Partner based on the order completion and delivery.

## Problem 3:
    If the customer will order for Product A, B and C from Supplier A, B, and C.
    - `Supplier A` is located `City 1` and `Logistic Partner 1` will pick up the order from `City 1`.
    - `Supplier B` is located `City 2` and `Logistic Partner 2` will pick up the order from `City 2`.
    - `Supplier C` is located `City 3` and `Logistic Partner 3` will pick up the order from `City 3`.
    - Pick-up Charges of `City 1`, `City 2` and `City 3` 
    - Drop-off Charges of `City 4` which is customer location.
    - How it will be manage full process and how we will manage the reconciliation and payout system for the Supplier and Logistic Partner based on the order completion and delivery ?

## Problem 4:
    How we will manage the refund process for the customer and how it will be reflect to the Supplier and Logistic Partner based on the order cancellation and refund process ?

## Problem 5:
    How to reconcile with Bank System -> Supplier Payout -> Logistic Partner Payout -> Cash on Delivery Reconciliation -> Pay by Card Reconciliation -> Refund Reconciliation -> Payout Reconciliation -> etc.

## Problem 6:
    Product Wise, Category Wise, Weight Wise, Distance Wise.
    How we will manage the charges and payment management system for the different product, category, weight and distance ?

What will be complete ecosystem of the payment management system for the ZOZI website and how it will be manage and track efficiently and automatically with the help of technology and how we will manage the reconciliation process for the Zozi Management, Supplier and Logistic Partner.

## Some suggestions for the payment management system:
    1. Suggestion of Hybrid Model: `flat fees for in‑city, distance + weight for inter‑city.` is nice
    2. `Allow product/category overrides for bulky or fragile items` this suggestion also nice.
    3. Ensure logistics partner revenue is tied to actual effort (weight + distance), making it profitable and sustainable.



# _____________________________________________________________________________________________ Payment Engine

# _____________________________________________________________________________________________ Employee's Communication

I rendered a visual reference first so the layout reads as a real, working surface — then below it the precise spec (the prompt) and the engineering diagrams.


## Confluence — One Surface for Every Conversation

The reference render above is the north star: a single dark canvas, lime as the only loud color, five zones working as one instrument. Read it left‑to‑right as **navigate → choose → converse → understand**. Nothing about it is a marketing hero; it opens *mid‑work*, exactly where your users actually live.

The reason most "unified comms" pages fail is that they stack email, chat, and video as **tabs** — which is just three apps wearing a trench coat (and it's literally how `AdminCommunicationPage` ships today: `email | chat | video` silos). Confluence inverts that. There is **one inbox and one composer**; *modality is a filter, not a room*. A direct message, a group thread, an internal channel, an entity‑linked B2B chat, a country memo, an email, and a missed video call are all the same object rendered differently — which maps cleanly onto the schema you already planned: `conversations` + `conversation_messages` + `conversation_participants` with a `channel_type` enum, plus the `proxy_*` masked layer sitting on top. The design below is the visual contract for that model.

Three principles govern every pixel:

- **Unified signal.** One chronological triage stream across all channels, ranked by urgency (you → mentions → DMs → groups → email → channels), so "inbox zero" means *zero*, not "zero in this one tab."
- **Modality as a filter.** The left rail switches *what kind* of thing you see; it never hides the others from search or from a contact's timeline.
- **Context travels.** The right inspector carries participants, every file ever shared in that thread, the email chain, and one‑click actions — so you never leave the conversation to go hunt for "that invoice."

---

## Diagram 1 — Spatial Layout (the five zones + overlay layers)

```
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│  ZONE A · COMMAND BAR  [ ⌕  Search people · messages · files · rooms · emails      ⌘K ]      │
│  ◐ brand        [＋ New ▾]              ● ● ● presence stack        ◑ theme   ⤢ fullscreen   │
├────┬──────────────────────────────┬───────────────────────────────────────────┬───────────────┤
│    │  ZONE C · LIST (contextual)  │  ZONE D · CONVERSATION + COMPOSER         │ ZONE E ·      │
│ Z  │  [All][Unread][@Me][★]  🔍  │  ┌─ header: title · presence · ⋯ ─────┐   │ INSPECTOR     │
│ O  │  ┌──────────────────────┐    │  │  ▸ participants · 📹 call · 👤 info │  │ (collapsible) │
│ N  │  │ 🟢 Avatar  Name      │    │  ├────────────────────────────────────┤  │ ───────────┐ │
│ E  │  │    last message…  2m │    │  │                                    │  │ │ Details   │ │
│    │  │ 💬 glyph   ● unread  │    │  │   ◌  incoming bubble + image att.  │  │ │ Shared  ◀─┼─┐
│ B  │  └──────────────────────┘    │  │                                    │  │ │ Members   │ │ │
│    │  ┌──────────────────────┐    │  │              outgoing bubble  ◌    │  │ │ Pinned    │ │ │
│ R  │  │ Avatar  Name         │    │  │              🎙 voice‑note wave ◌  │  │ │ Chain/    │ │ │
│ A  │  │    preview…      11m │    │  │         ── video call started ──     │  │ │  Labels   │ │ │
│ I  │  └──────────────────────┘    │  │                                    │  │ │ Actions   │ │ │
│ L  │  ┌──────────────────────┐    │  │   scroll‑reveal message stream     │  │ └───────────┘ │ │
│    │  │ 🟢 Avatar  #channel  │    │  │                                    │  │  Shared files │ │
│    │  │    3 new · pinned 📌 │    │  │                                    │  │  ▢ invoice.pdf│ │
│ 64 │  └──────────────────────┘    │  │                                    │  │  ▢ spec.fig │ │ │
│ px │            ⋮                 │  │                                    │  │  ▢ clip.mp4 │ │ │
│    │                              │  ├────────────────────────────────────┤  │  ───────────  │ │
│ ⬡  │                              │  │ [📎][][☺][@]  type a message…    │  │  live tiles   │ │
│ ✎  │                              │  │  chips: 📎file  🖼img   [send ➤]   │  │  [👤][👤][👤]│ │
│ ✉  │                              │  └────────────────────────────────────┘  │  ▁▃▅ now spk  │ │
│ 📹 │                              │                                         │               │ │
│ 👥 │                              │                                         │               │ │
│ 📁 │                              │                                         │               │ │
│ @  │                              │                                         │               │ │
│ 🛡  │                              │                                         │               │ │
├────┴──────────────────────────────┴───────────────────────────────────────────┴───────────────┤
│  OVERLAYS (float above all):  ⌘K palette · 📞 incoming‑call ring · 🖼 lightbox · 🎙 recorder  │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
   Zone B = modality rail      Zone C = conversation list      Zone D = active thread
   Zone E = context inspector  Zone A = global command + identity
```

**Zone legend (what each region owns):**

- **A — Command bar.** Universal search across people, messages, files, rooms, emails (the ⌘K palette). Holds brand mark, the polymorphic **New** button (its menu adapts: new chat / new group / new channel / new email / new meeting), the live presence stack of online teammates, theme toggle, density toggle.
- **B — Modality rail (icon‑only, 64px).** The *kind* selector: Unified Inbox, Direct, Groups, Channels, Email, Meet, Contacts, Files, @Mentions, Security/DLP, eDiscovery. Each carries an unread badge; the active item gets the lime pill + left accent bar.
- **C — Conversation list.** Context‑sensitive to B. Segmented filter (All / Unread / @Me / Starred) + local search. Rows show avatar, name, last line, relative time, a tiny `channel_type` glyph, presence dot, and state chips (pinned / muted / snoozed / draft / unread count).
- **D — Conversation + composer.** Header (title, participant avatars, one‑click 📹 call, 👤 info,  menu), the unified message stream, and the morphing composer. This is where email and chat *look like siblings*, not strangers.
- **E — Inspector.** Tabs: Details, **Shared** (every attachment/link/media in this thread — the file‑hunting killer), Members, Pinned, Chain/Labels (email thread + tags), Actions (schedule meeting with these people, create task, escalate, flag DLP). Below: a live participant strip when a call is active.
- **Overlays.** Command palette, incoming‑call ring sheet, attachment lightbox, hold‑to‑record voice popover, new‑conversation bottom sheet.

---

## Diagram 2 — Cross‑channel workflow (the "it all connects" flow)

```
                       ┌─────────────────────────────────────────────┐
   start anywhere ───▶ │  UNIFIED INBOX  (one triage queue, ranked)  │
                       └───────────────┬─────────────────────────────┘
                                       │ open
              ┌────────────────────────┼────────────────────────┐
              ▼                        ▼                        ▼
        [ DM / Group ]           [ Email thread ]         [ Entity / B2B ]
        channel_type=            channel_type=            channel_type=
        direct|group|internal    email                    entity  (proxy_*)
              │                        │                        │
              │   one composer, modality inferred / toggled     │
              └────────────┬───────────┴────────────┬───────────┘
                           ▼                        ▼
                  escalate to 📹 VIDEO       every file → FILES hub
                  (same participants          every person → CONTACT
                   auto‑join, lobby,           timeline (all your
                   record, captions)           history with them)
                           │                        │
                           ▼                        ▼
                  recap + transcript +       relationship view feeds
                  shared files land back     supplier / B2B trust
                  in the SAME thread         (masked contacts intact)
                           │
                           ▼
              all events → communication_audit_trail  (+ DLP / legal‑hold)
```

The point of this flow: **nothing is an island.** A chat escalates to a call with one click; the call's recording, transcript, and shared files fall back into the originating thread; an email to a contact auto‑links (or creates) a contact card; a customer/supplier email sent from an entity context keeps the masked B2B proxy; and every single event is auditable. That continuity *is* the efficiency.

---

## THE HANDOFF PROMPT

> Hand this block to a designer or a UI‑building model verbatim. It is the complete spec.

**Product intent.** Build *Confluence*, the unified communication workspace for the Zozi admin/employee panel. One screen absorbs direct chat, group chat, internal channels, entity‑linked (order/supplier) threads, country memos, full email, and video meetings — plus a first‑class Contacts directory and a global Attachments hub. Success metric: a user resolves a mixed email‑and‑chat thread, finds a previously shared file, and jumps on a call with the same people **without ever switching top‑level tabs**.

**Visual reference.** Match the five‑zone dark render provided: charcoal surfaces over a faint topographic‑mesh background (not gradient blobs), lime `#6AE022` as the sole accent, strong weight contrast between bold titles and whisper‑quiet metadata, soft layered shadows, hairline borders. Provide a full light theme via tokens (see Design Tokens).

**Information architecture — Zone B rail items & their list contents (Zone C):**
- *Unified Inbox* → every unread across channels, ranked: direct mentions → DMs → groups → email → channels.
- *Direct* → 1:1 threads (`channel_type=direct`).
- *Groups* → private multi‑person rooms (`group`).
- *Channels* → topic rooms, public/private (`internal`), with member counts.
- *Email* → mailbox folders (Inbox/Sent/Drafts/Labels) **and** the same mails surfaced in the unified stream.
- *Meet* → scheduled + recent rooms, "join active" pinned to top.
- *Contacts* → directory + recent + favorites; each contact opens a **relationship timeline** aggregating every chat/email/call with them.
- *Files* → every attachment ever shared, filterable by person / type / thread / date.
- *@Mentions* → a personal signal feed of every time you were tagged.
- *Security/DLP* → policy hits, masked‑channel audit, leak alerts (compliance roles only).
- *eDiscovery* → cross‑channel content search + legal hold + export (legal roles only).

**Zone A — Command bar.** Full‑width rounded search field with magnifier + a `⌘K` hint chip; opens a command palette that searches people, messages, files, rooms, emails and runs actions ("New group with…", "Schedule call with…", "Jump to #finance‑oman"). Right cluster: polymorphic **New** button, presence avatar stack (online now), theme toggle, density toggle, fullscreen.

**Zone C — Conversation list.** Sticky segmented filter `All · Unread · @Me · ★` + a local filter input. Each row: 40px avatar (or channel hash tile), bold name, one‑line muted preview (strip markup), trailing relative time, a 14px `channel_type` glyph, a presence dot for people, and state chips (📌 pinned, 🔕 muted, 💤 snoozed, ✎ draft, lime unread pill). Active row: lime left‑bar + tinted surface. Hover: 2px lift + surface‑2. Keyboard: `j/k` move, `Enter` open, `e` archive, `m` mute, `u` mark unread, `s` star.

**Zone D — Conversation + composer.**
- *Header*: title + participant avatar cluster (overflow `+N`), presence, a 📹 **Call** button (instant meeting with exactly these participants), 👤 info (toggles Zone E), ⋯ menu (mute, leave, retention, link to entity, copy link).
- *Stream*: a single **Message Block** component renders every channel type. Left = others, right = you. A block carries: sender chip (in groups), body (text/markdown/links), optional inline media (image thumb / video poster / **voice‑note waveform chip** with duration), attachment card(s), emoji reactions, reply‑thread affordance, read ticks (`✓ sent → ✓✓ read`), and an edited flag. System events (call started/ended, member joined, file shared) render as centered pills, not bubbles. Email renders through the *same* block but with a quoted‑chain collapse and label chips. New messages **scroll‑reveal** (120ms fade+rise); respect reduced‑motion.
- *Composer*: a morphing bar (matrix below). Left tools: 📎 attach (image/video/voice/file/doc), 🎙 hold‑to‑record voice note, ☺ emoji, `@` mention, formatting toggle. Inline **attachment chips** appear above the input as you add them (removable). Right: lime **Send** (chat) which becomes **Send / Schedule ▾** (email). Typing indicator (three pulsing dots) shows in the stream footer. Optimistic send: message appears instantly with a clock, flips to `✓` then `✓✓`.

**Composer behavior matrix (one composer, modality‑aware):**

| Modality | Shows To/Cc/Subject? | Send semantics | Attachments | Masking / routing |
|---|---|---|---|---|
| Direct / Group / Channel | No | instant WebSocket | all types, voice notes | internal, in‑DB |
| Email (internal addr) | Yes (collapsible) | instant, in‑DB (no SMTP) | all types + signature | internal resolver |
| Email (external addr) | Yes | queued via relay | + DLP scan before send | SMTP relay + allow‑list |
| Entity / B2B | No (context‑bound) | instant | all types | `proxy_*` masked gateway |
| Meet invite | Yes (auto‑fill attendees) | schedules room + posts link | calendar .ics | internal/external aware |

**Zone E — Inspector (collapsible, 320px).** Tab strip: *Details* (topic, created, retention, notification level, link to entity/order), ***Shared*** (chronological grid of every file/link/media in this thread with type icon, sender, date, one‑click preview/download — this is the feature that pays for the whole page), *Members* (roster, roles, add/remove, mute‑all), *Pinned*, *Chain/Labels* (full email thread + label toggles when the conversation is an email), *Actions* (schedule meeting with these people, create task from selection, escalate, flag for DLP, legal‑hold). When a call is live, the inspector footer shows the participant tile strip with a green live dot and a thin "now speaking" waveform on the active speaker.

**The Unified Message Model (design ↔ schema).** Treat an email and a chat bubble as one component fed by one record shape: `{ id, conversation_id, channel_type, sender_id, body, attachments[], reply_to_id, reactions[], read_by[], created_at, meta }`. `channel_type ∈ { direct, group, internal, entity, country, email, video_event }`. Masked/B2B conversations carry `is_masked=true` and route through the `proxy_*` layer; the UI shows a small shield glyph and never reveals the true contact to the external party. This is exactly the `conversations / conversation_messages / conversation_participants` merge you specified — the UI is its visual proof.

**Micro‑interactions & the "living" layer (this is what makes it feel alive, not static):**
- Ambient topographic‑mesh / faint grid background behind the rails (subtle parallax on scroll), explicitly *not* aurora blobs.
- Presence dots **pulse** softly when someone comes online; avatar stack reflows with a spring.
- Unread badges **pop** in (scale 0.8→1 with a 180ms spring) and the rail item flashes a 1px lime edge once.
- Typing indicator: three dots staggered at 120ms.
- Send lifecycle: clock → `✓` → `✓✓` with cross‑fade; failure shows a red retry dot inline.
- Conversation rows: 2px hover lift + surface shift; active row slides the lime bar in (150ms).
- Message stream: scroll‑reveal fade+rise; "new messages ↓" pill when scrolled up.
- Voice note: animated waveform while recording; playback scrubber with a moving lime head.
- Live call: active‑speaker tile gets a lime ring + a 3‑bar equalizer.
- Skeleton shimmer on every list/stream while loading (shape‑matched, never a spinner wall).
- Inspector tabs underline‑slide; file cards tilt 1° on hover.
- All transitions 120–250ms `cubic-bezier(.2,.7,.2,1)`; honor `prefers-reduced-motion`.


## ___________________________________________________________ 2nd Prompt

## 0 — The opening move

Stop thinking of this page as *three tabs wearing a trench coat*. Email, chat, and video are not products — they are **transports**. The thing a person actually works in is the *conversation*, and the conversation doesn't care whether it arrived by socket, SMTP, or a WebRTC room. So the page below is not a tab strip. It is a **single conversation deck**: one inbox that swallows every signal, one stage that *morphs* its renderer to match whatever you opened, and one context rail that turns the person or room on the other side into a 360° object. Tabs become *filters*. Pages become *panes*. That inversion is the whole design.

What follows is the layout, the motion language, the workflow, the Tailwind composition in your own tokens, and — at the end — one **self‑contained implementation prompt** you can hand to any builder verbatim.

---

## 1 — Design doctrine (read this before the pixels)

- **Conversation is the atom.** A DM, a group channel post, an email thread, a missed video, a support ticket — all are *threads* with a `transport` badge. The rail lists threads; the stage renders them.
- **One inbox, many lenses.** The default view is a *Unified Inbox* (everything, chronological). Lenses (`All · Unread · Mentions · Email · Channels · DMs · Video · Flagged`) are chips, not pages.
- **The stage morphs, it doesn't navigate.** Opening a thread swaps the *renderer* inside the same stage shell — chat stream, email thread, video grid, or contact card — with a cross‑fade, never a route change. Muscle memory survives.
- **The right rail is contextual, not decorative.** In chat it shows members + shared files + AI summary; in email it shows the contact 360 + related orders/tickets + templates; in video it shows tiles + agenda + notes + recording; on a contact it shows *every* interaction across *every* transport.
- **The composer is universal.** One dock, one draft. A `send‑as` toggle decides whether it leaves as 💬 chat,  email, or 📱 SMS‑bridge. Same keystrokes, different pipe.
- **Keyboard‑first, density‑aware.** It plugs into your existing `useDensity` and `KeyboardShortcutsHelp`. Compact = Slack‑tight rows; expanded = airy email rows.
- **Theme‑agnostic by construction.** Colors come *only* from your tokens via classes; the structural CSS never hardcodes a hex, so light/dark “just work”.

---

## 2 — The layout (diagrams)

### Master deck — desktop, *balanced* density

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ COMMAND BAR   [⌘K  search people, threads, messages, files…        ]  ◑ live  + │
│               lenses: (All) Unread @Mentions ✉Email #Channels ●DMs 📹Video ⚑    │
├──────────────┬──────────────────────────────────────────────┬───────────────────┤
│ RAIL  264px  │  STAGE   flex · min 460px                    │ CONTEXT  336px    │
│ ───────────  │  ┌─ thread head ──────────────────────── ⋯ ┐ │ ───────────────   │
│ ▸ INBOX  12  │  │ #oman‑sales        ● 4 online    📹  📞 │ │ ▸ PEOPLE / 360    │
│              │  └─────────────────────────────────────────┘ │   Aisha · Sales   │
│ CHANNELS     │                                              │   last seen 2m    │
│  # general   │   ┌ msg ──────────────────────── 10:24 ✓✓ ┐ │   ─ history ──   │
│  # finance   │   │ ◉  body / card / inline attachment     │ │   ✉ 3  💬 12  📹1 │
│  # oman‑ops  │   └────────────────────────────────────────┘ │                   │
│              │   ┌ msg ──────────────────────── 10:26 ✓  ┐ │ ▸ SHARED FILES    │
│ DIRECT       │   │ ◉  …                                   │ │   🖼 4  📄 2  🎙 1 │
│  ● Aisha     │   └────────────────────────────────────────┘ │                   │
│  ◐ Karim     │   ┌ typing… ──────────────────────────────┐ │ ▸ PINNED / TASKS  │
│  ○ Layla     │   └────────────────────────────────────────┘ │   ☐ send invoice  │
│              │                                              │                   │
│ MAILBOX      │   ╔═ COMPOSER DOCK (universal) ═══════════╗ │ ▸ AI · DLP · AUDIT│
│  ✉ Inbox 3   │   ║ [📎][🖼][🎙][@][#][☺]  write message… ║ │   summarize       │
│  ↗ Sent      │   ║ send‑as:  💬 chat │ ✉ email │ 📱 sms   ║ │   draft reply     │
│  ✎ Drafts    │   ╚══════════════════════════ [ ⌘↵ send ▾]╝ │   🛡 DLP: clear    │
├──────────────┴──────────────────────────────────────────────┴───────────────────┤
│ STATUS DOCK   ● socket connected · Aisha is typing… · DLP ok · press ⌘/ for keys │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### The morph — same shell, four renderers in the STAGE

```
   STAGE when transport = chat            STAGE when transport = email
   ┌──────────────────────────┐          ┌──────────────────────────┐
   │ live message stream      │          │ subject + from/to chips  │
   │ (virtualized, bubbles)   │          │ threaded replies (indent)│
   │ + inline reactions       │          │ + template / forward bar │
   └──────────────────────────┘          └──────────────────────────┘
   STAGE when transport = video           STAGE when transport = contact
   ┌──────────────────────────┐          ┌──────────────────────────┐
   │ 2×2 → 3×3 tile grid that │          │ profile hero + stats     │
   │ reflows on join/leave    │          │ timeline across ALL      │
   │ + side chat + controls   │          │ transports (the 360)     │
   └──────────────────────────┘          └──────────────────────────┘
```

### Responsive collapse

```
 TABLET (≤1024)                 MOBILE (≤640)
 ┌──────┬───────────┬──┐        ┌──────────────┐
 │ RAIL │  STAGE    │▤ │ ctx    │  STAGE       │
 │ 64px │           │ =drawer  │  (full)      │
 │icons │           │          │              │
 └─────────────────┴──┘        ├──────────────┤
  rail→icon strip,               rail→bottom sheet
  context→slide drawer           context→"info" sheet
                                 composer→sticky dock
```

---

## 3 — Anatomy of each zone

- **Command bar** — global ⌘K search across people + threads + message text + files (wires to your `search_communications` eDiscovery). Lens chips filter the rail. Right cluster: live‑connection pill, presence avatar stack, `+ new` (thread / channel / room / email / contact).
- **Rail** — three stacked groups (Inbox lenses · Channels · Direct · Mailbox). Each row: avatar/`#`, title, last‑line preview, time, unread chip, transport glyph. Hover reveals `mute · pin · 📹 · ⋯`. Active row gets an animated left brand bar.
- **Stage** — header (title, presence, transport switch, `📹 call` / `📞 audio`), the renderer (see morph), and the **universal composer dock** pinned to the stage bottom.
- **Context rail** — five collapsible cards that re‑key per transport: *People/360*, *Shared files*, *Pinned & tasks*, *AI · DLP*, *Audit / eDiscovery*.
- **Status dock** — socket state, remote typing, DLP verdict, shortcut hint. Thin, always present, the heartbeat of the page.

---

## 4 — Motion & micro‑interaction language

> Concrete, not vague. All respect `prefers-reduced-motion`.

- **Thread enter** — stage renderer cross‑fades (`opacity` + 6px rise, 180ms ease‑out); rail selection bar *springs* to the new row.
- **New message** — slides up with a 220ms spring; if the thread is *not* focused, its rail row flashes a 1.2s brand tint and the unread chip increments with a pop.
- **Presence** — online dot uses a 2s `pulse` ring; “typing…” renders an animated 3‑dot ellipsis in both the stream and the status dock.
- **Composer** — grows height on focus (120→ up to 40vh) with a layout transition; attach buttons stagger‑fade in.
- **Attachments** — drag‑over turns the composer into a dashed brand drop‑zone; each upload shows a radial progress ring that *ticks* into a thumbnail on completion.
- **Video grid** — tiles animate position/size with a shared‑layout morph when participants join/leave/pin (no jarring reflow).
- **Rail collapse** — width tweens 264→64px while labels fade; content never reflows horizontally (icon column is fixed‑width).
- **Ambient layer** — a *whisper*, not a blob: a 2px dot‑grid at ~4% plus a single brand radial at ~5% that drifts 40px over 24s. Disabled under reduced‑motion and on mobile. Built from `currentColor` so it inherits your theme accent.
- **Hover affordances** — row quick‑actions reveal with a 90ms stagger; buttons lift 1px with a soft token‑colored shadow.

Performance guardrails: virtualize the message stream and the rail (thousands of rows); lazy‑mount the video SDK and the context rail *per transport*; memoize thread rows; route the unified inbox through a server‑side cursor, never client‑side filter of everything.

Accessibility: `role="log"` + `aria-live="polite"` on the stream, `role="listbox/option"` on the rail, focus‑trapped modals, visible focus rings in `text-primary`, full keyboard nav (see §5).

---

## 5 — The efficient workflow

1. Land on **Unified Inbox** — the day’s signal, one scroll.
2. `⌘K` to jump anywhere; `j`/`k` to move the rail selection; `Enter` opens in the stage; `o` marks read.
3. Reply in the **composer**; flip `send‑as` to email when the thread needs a paper trail — *same draft, no copy‑paste*.
4. **Drag an email → right rail** to spawn a task; **drag a contact → stage** to start a thread; **drag a file → composer** to attach.
5. `v` opens a video room *from the current thread* (participants pre‑seeded); its chat and recording land back in the same thread.
6. AI card: *summarize thread*, *draft reply*, *extract action items* — each writes a pinned task. DLP verdict shows inline; a flagged send is held, not silently dropped.
7. `⌘/` opens your existing shortcuts sheet, scoped to `comms`.

### Mode matrix — what each transport shows where

| Transport | Rail glyph | Stage renderer | Context rail emphasis |
|---|---|---|---|
| Direct chat | ● avatar | live bubble stream | People · shared files · AI |
| Group / channel | `#` | stream + reactions | Members · pinned · tasks |
| Email | ✉ | threaded mail + templates | Contact 360 · related order/ticket |
| Video room | 📹 | tile grid + side chat | Agenda · notes · recording |
| Contact | 👤 | 360 timeline | full cross‑transport history |
| B2B masked |  | masked thread | true‑contact reveal (gated) |
| Incident / war room | 🚨 | room + action items | SLA · audit · eDiscovery |

---

## 6 — Tailwind composition (your tokens, at a glance)

This is the *markup skeleton* so you can see how the deck is built from your existing classes. The structural/motion CSS lives in §7.

```tsx
<div className="comm-shell theme-card" data-rail="open" data-ctx="open">
  {/* ambient — inherits accent via text-primary, never a hardcoded color */}
  <div aria-hidden className="comm-ambient text-primary" />

  {/* COMMAND BAR */}
  <header className="comm-bar theme-elevated border-b border-border">
    <CommandPalette />                       {/* ⌘K */}
    <LensChips />                            {/* All · Unread · @ · ✉ · # · ● · 📹 */}
    <div className="ml-auto flex items-center gap-2">
      <LivePill /> <PresenceStack /> <NewMenu />
    </div>
  </header>

  {/* RAIL */}
  <aside className="comm-rail border-r border-border">
    <RailGroup title="Inbox"  items={lenses} />
    <RailGroup title="Channels" items={channels} />
    <RailGroup title="Direct" items={dms} />
    <RailGroup title="Mailbox" items={mail} />
  </aside>

  {/* STAGE */}
  <main className="comm-stage">
    <ThreadHeader thread={active} />
    <div className="comm-stream">{renderTransport(active.transport)}</div>
    <ComposerDock sendAs={sendAs} setSendAs={setSendAs} />
  </main>

  {/* CONTEXT */}
  <aside className="comm-context border-l border-border">
    <ContextCard title="People / 360" />
    <ContextCard title="Shared files" />
    <ContextCard title="Pinned & tasks" />
    <ContextCard title="AI · DLP" />
    <ContextCard title="Audit / eDiscovery" />
  </aside>

  <footer className="comm-dock theme-elevated border-t border-border"><StatusDock /></footer>
</div>
```

Every color/typography decision above is a token class (`theme-card`, `theme-elevated`, `border-border`, `text-text`, `text-text-muted`, `text-primary`, `bg-primary/10`). The new `comm-*` classes add *only* structure + motion.

---

## 7 — IMPLEMENTATION PROMPT  *(copy everything in this block verbatim)*

> Hand this entire block to your builder. It is self‑contained: stack, tokens, layout diagram, the structural CSS, the JSX skeleton, behaviors, data models, endpoints, file tree, and acceptance criteria. The surrounding document (§0–§6) is the rationale — attach it optionally.

````
You are building the unified Communication workspace for the Zozi admin/staff web app
(Next.js 15 App Router, React 19, TypeScript, Tailwind, framer-motion). Replace the
current flat 3-tab page at `frontend/web_app/src/app/admin/communication/page.tsx`
(which just swaps AdminEmailPanel / AdminChatPanel / AdminVideoPanel) with a single
"conversation deck": one rail, one morphing stage, one contextual rail, one universal
composer. Do NOT use page navigation between chat/email/video — swap the renderer
inside the same stage shell with a cross-fade.

=== EXISTING TOKENS / CLASSES TO REUSE (do not invent new colors) ===
Surfaces & cards: `theme-card`, `theme-elevated`, `theme-input`, `theme-overlay`
Borders: `border-border`
Text: `text-text`, `text-text-muted`, `text-text-faint`
Accent: `text-primary`, `bg-primary`, `bg-primary/10`, `border-primary/40`, `bg-brand`
Danger/ok: `text-error`, `bg-error`, plus emerald-500 ONLY for tiny presence dots.
Layout helpers already present: `PanelContent`, `PanelTabs`, `EnterpriseDataTable`.
Hooks/util present: `useAuth`, `useAdminCountry`, `useDensity` (compact|balanced|expanded),
`useChatWebSocket`, `WebSocketManager`, `apiFetch`, `parseJsonResponse`, `KeyboardShortcutsHelp`.
Icons present (lucide): MessageCircle, Mail, Video, Phone, Users, Send, Paperclip,
Image as ImageIcon, Mic, Hash, AtSign, Smile, CheckCheck, Pin, BellOff, Search, Plus,
Shield, FileSearch, Copy, X, ChevronDown, PhoneOff, ScreenShare.

=== OPTIONAL TYPE UPGRADE ===
Add one CSS var `--font-display` (e.g. "Space Grotesk", fallback ui-sans-serif) and a
utility `.font-display { font-family: var(--font-display); letter-spacing: -0.01em; }`.
Use it ONLY for module titles, lens chips, numerals, and section eyebrows. Body text
stays on the app's existing body font. If you cannot add a font, skip it — never fall
back to a generic indigo/gradient "hero" look.

=== LAYOUT DIAGRAM (implement this grid) ===
Desktop grid (3 columns + top bar + bottom dock):
┌──────────────────────────────────────────────────────────────────────┐
│ COMMAND BAR  [⌘K search]  lenses chips            ●live  presence + │
├────────────┬───────────────────────────────────────┬─────────────────┤
│ RAIL 264px │ STAGE flex min 460px                  │ CONTEXT 336px   │
│  Inbox     │  thread header                        │  People/360     │
│  Channels  │  message/mail/video/contact renderer  │  Shared files   │
│  Direct    │  (virtualized stream)                 │  Pinned/tasks   │
│  Mailbox   │  ── universal composer dock ──        │  AI·DLP·Audit   │
├───────────────────────────────────────────────────┴─────────────────┤
│ STATUS DOCK  ● connected · typing… · DLP ok · ⌘/                     │
└──────────────────────────────────────────────────────────────────────┘
Stage renderer morphs by `thread.transport` ∈ {chat, group, email, video, contact,
b2b_masked, incident} with a cross-fade; no route change.
Tablet (≤1024): rail collapses to a 64px icon strip; context becomes a slide-in drawer.
Mobile (≤640): rail = bottom sheet, context = "info" sheet, composer = sticky dock.

=== STRUCTURAL + MOTION CSS  (create `frontend/web_app/src/styles/comm.css`) ===
This CSS adds ONLY structure & motion. It hardcodes NO color — theming comes from the
token classes on the elements. Ambient layer uses currentColor so it inherits the accent.

:root{
  --rail-w: 264px; --rail-w-collapsed: 64px;
  --ctx-w: 336px;  --bar-h: 56px;  --dock-h: 36px;
}
.comm-shell{
  position: relative; display: grid; overflow: hidden;
  grid-template-columns: var(--rail-w) minmax(0,1fr) var(--ctx-w);
  grid-template-rows: var(--bar-h) 1fr var(--dock-h);
  grid-template-areas: "bar bar bar" "rail stage ctx" "dock dock dock";
  height: calc(100dvh - var(--app-chrome, 0px));
  transition: grid-template-columns .28s cubic-bezier(.22,1,.36,1);
}
.comm-shell[data-rail="collapsed"]{ grid-template-columns: var(--rail-w-collapsed) minmax(0,1fr) var(--ctx-w); }
.comm-shell[data-ctx="closed"]{ grid-template-columns: var(--rail-w) minmax(0,1fr) 0px; }
.comm-shell[data-rail="collapsed"][data-ctx="closed"]{ grid-template-columns: var(--rail-w-collapsed) minmax(0,1fr) 0px; }
.comm-bar{ grid-area: bar; } .comm-rail{ grid-area: rail; overflow-y:auto; }
.comm-stage{ grid-area: stage; display:flex; flex-direction:column; min-width:0; }
.comm-context{ grid-area: ctx; overflow-y:auto; } .comm-dock{ grid-area: dock; }

/* ambient whisper — inherits accent from a parent text-primary; no hardcoded hex */
.comm-ambient{ position:absolute; inset:0; pointer-events:none; z-index:0; opacity:.5;
  background:
    radial-gradient(40% 50% at 80% -10%, color-mix(in srgb, currentColor 6%, transparent), transparent 70%),
    radial-gradient(currentColor .6px, transparent .6px) 0 0 / 22px 22px;
  -webkit-mask-image: linear-gradient(180deg, #000, transparent 60%);
          mask-image: linear-gradient(180deg, #000, transparent 60%);
  animation: comm-drift 24s ease-in-out infinite alternate;
}
@keyframes comm-drift{ from{ background-position: 0 0, 0 0; } to{ background-position: 0 0, 40px 30px; } }

/* rail rows */
.comm-row{ position:relative; display:flex; gap:10px; align-items:center;
  padding:8px 12px; border-radius:10px; cursor:pointer; }
.comm-row::before{ content:""; position:absolute; left:0; top:8px; bottom:8px; width:3px;
  border-radius:3px; background: currentColor; transform: scaleY(0); transform-origin:center;
  transition: transform .2s cubic-bezier(.22,1,.36,1); }
.comm-row[data-active="true"]::before{ transform: scaleY(1); }
.comm-row .quick{ opacity:0; transition: opacity .12s ease; }
.comm-row:hover .quick, .comm-row:focus-within .quick{ opacity:1; }

/* composer dock */
.composer-dock{ position: sticky; bottom:0; }
.composer-box{ transition: min-height .2s ease, box-shadow .2s ease; min-height:48px; }
.composer-box:focus-within{ min-height:96px; }
.composer-box[data-dragover="true"]{ outline:2px dashed currentColor; outline-offset:-6px; }

/* presence + reveals */
.dot-online{ position:relative; }
.dot-online::after{ content:""; position:absolute; inset:-3px; border-radius:999px;
  border:2px solid currentColor; opacity:.6; animation: comm-pulse 2s ease-out infinite; }
@keyframes comm-pulse{ 0%{ transform:scale(.6); opacity:.6 } 100%{ transform:scale(1.8); opacity:0 } }
.msg-enter{ animation: comm-rise .22s cubic-bezier(.22,1,.36,1) both; }
@keyframes comm-rise{ from{ opacity:0; transform: translateY(6px) } to{ opacity:1; transform:none } }

/* stage morph */
.stage-fade{ animation: comm-fade .18s ease-out both; }
@keyframes comm-fade{ from{ opacity:0; transform: translateY(4px) } to{ opacity:1; transform:none } }

/* responsive */
@media (max-width:1024px){
  .comm-shell{ grid-template-columns: var(--rail-w-collapsed) minmax(0,1fr) 0px; }
  .comm-context{ position:fixed; right:0; top:var(--bar-h); bottom:var(--dock-h);
    width:min(360px,86vw); transform: translateX(100%); transition: transform .28s ease; z-index:40; }
  .comm-shell[data-ctx="open"] .comm-context{ transform:none; }
}
@media (max-width:640px){
  .comm-shell{ grid-template-columns: 1fr; grid-template-areas:"bar" "stage" "dock"; }
  .comm-rail{ position:fixed; inset:auto 0 0 0; max-height:70vh; transform: translateY(100%);
    transition: transform .3s ease; z-index:45; border-top-left-radius:18px; border-top-right-radius:18px; }
  .comm-shell[data-rail="sheet"] .comm-rail{ transform:none; }
}
@media (prefers-reduced-motion: reduce){
  .comm-ambient,.dot-online::after,.msg-enter,.stage-fade{ animation:none !important; }
  .comm-shell,.comm-context,.comm-rail,.composer-box{ transition:none !important; }
}

=== JSX SKELETON (compose with token classes; structure from CSS above) ===
<div className="comm-shell theme-card" data-rail={rail} data-ctx={ctx}>
  <div aria-hidden className="comm-ambient text-primary" />
  <header className="comm-bar theme-elevated border-b border-border flex items-center gap-3 px-3">
     <CommandPalette/> <LensChips/>
     <div className="ml-auto flex items-center gap-2"><LivePill/><PresenceStack/><NewMenu/></div>
  </header>
  <aside className="comm-rail border-r border-border p-2 space-y-3">
     <RailGroup title="Inbox" items={lenses}/>
     <RailGroup title="Channels" items={channels}/>
     <RailGroup title="Direct" items={dms}/>
     <RailGroup title="Mailbox" items={mail}/>
  </aside>
  <main className="comm-stage">
     <ThreadHeader thread={active}/>
     <div className="comm-stream flex-1 overflow-y-auto p-3">
        <AnimatePresence mode="wait">
          <motion.div key={active.transport} className="stage-fade">
            {renderTransport(active)}   {/* chat|group|email|video|contact|b2b|incident */}
          </motion.div>
        </AnimatePresence>
     </div>
     <ComposerDock sendAs={sendAs} setSendAs={setSendAs}/>
  </main>
  <aside className="comm-context border-l border-border p-3 space-y-3 theme-elevated">
     <ContextCard title="People / 360"/>
     <ContextCard title="Shared files"/>
     <ContextCard title="Pinned & tasks"/>
     <ContextCard title="AI · DLP"/>
     <ContextCard title="Audit / eDiscovery"/>
  </aside>
  <footer className="comm-dock theme-elevated border-t border-border"><StatusDock/></footer>
</div>

`renderTransport` returns: chat/group → virtualized bubble stream with reactions;
email → subject + from/to chips + indented threaded replies + template/forward bar;
video → reflowing tile grid (animate layout on join/leave) + side chat + controls
(wire to existing create_video_room + /meet/[room]); contact → 360 timeline across
all transports; b2b_masked → masked thread with gated true-contact reveal;
incident → room + action items + SLA.

`ComposerDock` = one textarea + attach row [📎 🖼  @ # ☺] + a `send-as` segmented
toggle (chat | email | sms) + send (⌘↵). Drag files onto it (data-dragover). Voice
note records to a compressed blob with a waveform preview. The same draft posts to
whichever pipe `send-as` selects.

=== DATA MODELS TO WIRE (already exist) ===
DirectChatRoom/Message, GroupChatMember/Message, InternalChannel/Member/Message,
EntityChatMessage, CommunicationAuditTrail. Video via comm_controller.create_video_room
and the /meet/[room] page. eDiscovery via search_communications(...).

=== ENDPOINTS ===
Reuse existing chat/email/video/country-communication routers. ADD one aggregator:
GET /comms/unified-inbox?lens=&cursor=&limit=  → returns a cursor-paginated, server-sorted
merge of DMs, group mentions, channel posts, emails, missed videos, tickets, each as a
normalized {thread_id, transport, peer, preview, unread, updated_at}. The rail renders
THIS, not four separate lists. Real-time deltas arrive over the existing WebSocket
(manager.broadcast_to_room / send_employee_update) and patch the inbox.

=== BEHAVIORS / INTERACTIONS ===
- ⌘K global search; j/k move rail selection; Enter open; o mark read; c compose;
  v start video from active thread; ⌘/ opens KeyboardShortcutsHelp scoped to "comms".
- Drag email→context rail = create task; drag contact→stage = new thread; drag file→composer.
- Hover rail row reveals quick actions with 90ms stagger; active row animates left brand bar.
- New message: spring rise in stream; if unfocused, rail row flashes + unread chip pops.
- Presence dot pulse; remote typing shown in stream AND status dock.
- AI card: summarize / draft reply / extract tasks (tasks pin to context rail).
- DLP: inline verdict; flagged sends are HELD with a reason, never silently dropped.
- Density: compact = 36px rows, balanced = 48px, expanded = 64px (read useDensity).

=== PERFORMANCE / A11Y ===
Virtualize stream + rail. Lazy-mount video SDK and the context rail per transport.
Server-cursor the inbox (never client-filter everything). role="log"+aria-live on stream,
role="listbox/option" on rail, focus-trapped modals, visible focus rings, full keyboard nav,
reduced-motion honored (CSS already does).

=== FILE TREE TO CREATE/EDIT ===
- src/app/admin/communication/page.tsx            (rewrite → the deck)
- src/components/comms/CommShell.tsx
- src/components/comms/Rail/{RailGroup,RailRow,LensChips}.tsx
- src/components/comms/Stage/{ThreadHeader,ComposerDock,renderTransport.tsx}
- src/components/comms/Stage/renderers/{Chat,Email,Video,Contact,B2B,Incident}.tsx
- src/components/comms/Context/{ContextCard,People360,SharedFiles,Tasks,AiDlp,Audit}.tsx
- src/components/comms/CommandPalette.tsx  (⌘K over unified inbox + eDiscovery)
- src/components/comms/StatusDock.tsx
- src/hooks/useUnifiedInbox.ts  (cursor + WS patch)
- src/styles/comm.css  (the CSS block above; import in layout)
- backend: routers/comms_unified.py + controller method for /comms/unified-inbox

=== ACCEPTANCE CRITERIA ===
1. One page, zero route changes between chat/email/video — only the stage renderer swaps.
2. Unified inbox shows DMs+channels+email+video+tickets merged, server-paginated, WS-live.
3. Composer `send-as` delivers the same draft as chat OR email OR sms-bridge.
4. Context rail re-keys per transport; contact view shows cross-transport 360 history.
5. Light AND dark themes correct with no hardcoded colors in comm.css.
6. Tablet/mobile collapses per the diagram; keyboard + reduced-motion + screen-reader pass.
7. Lighthouse/interaction: rail & stream virtualized; opening a 10k-message thread stays smooth.
8. E2E (extend existing command-center/communication specs): open inbox → open thread →
   reply via chat → flip send-as to email → start video from thread → verify audit log entry.
Build it as a portfolio-grade, alive workspace: layered surfaces, the ambient whisper,
spring reveals, presence pulses, and strong type contrast (display face on titles/numerals,
body face elsewhere). No centered hero, no equal-card grid, no indigo/aurora clichés.
````

---

## 8 — Build order (so you ship in slices, not one cliff)

1. **Shell + grid + ambient** — get the three panes resizing and collapsing right.
2. **Rail + Unified Inbox endpoint** — the merged, cursor‑paginated, WS‑patched list.
3. **Stage: chat + group renderers + composer** (send‑as = chat only at first).
4. **Email renderer + send‑as = email** — the morph becomes real.
5. **Context rail** (People/360 → files → tasks → AI/DLP → audit), re‑keyed per transport.
6. **Video renderer** wired to your existing rooms; **contact 360**.
7. **Drag‑and‑drop + ⌘K + keyboard map**; density wiring.
8. **E2E + a11y + Lighthouse** pass; reduced‑motion audit.

---

The page you end up with won't feel like “email and chat glued together.” It will feel like a **signal deck** — one place where every conversation in the company lives, breathes, and turns into action without ever making the user think about which pipe it arrived through. That is the efficiency win, and it is the whole point.



# _____________________________________________________________________________________________ Employee's Communication

# _____________________________________________________________________________________________ [ADVANCED SMART SEARCH · FILTER · SORT BAR — IMPLEMENTATION]

## 0. Objective - ADVANCED SMART SEARCH · FILTER · SORT BAR — IMPLEMENTATION
Build the **Advanced Smart Filtering · Sorting · Searching Bar** for the ZOZI customer storefront by **reusing and extending** what already exists — **not** by creating a new component or a new look. The bar must support **text (AI-parsed) + image + voice** search, **combined faceted filtering** (Category + Price + Rating + Supplier together), be **fully wired to the database**, and meet a **<300ms p95** latency budget.

## 1. Ground rules (non-negotiable)
- **Reuse, do not redesign.** Use the existing `FilterSearchBar` (web) and `ProductSearchFilterBar` (mobile) and the system theme: `glass-search`, `glass-dropdown`, theme tokens (`surface0/1/2`, `text/textMuted`, `glass.border`), the density system, and **RTL/i18n** (Arabic strings already exist — preserve them).
- **Keep the exact bar look** below. Only its *placement* changes (centered in the header after the ZOZI logo). Do **not** restyle the component itself.
- **Hybrid search, not vector-only.** Keep PostgreSQL FTS/ILIKE for lexical; **add** pgvector for semantic; **add** CLIP for visual. Fuse with Reciprocal Rank Fusion (RRF).
- **One search brain.** Voice and image must funnel into the **existing** NLP query parser (`parsed`: brand/color/size/price/min_rating/quality/sort/has_video) — do **not** build a second parser.
- **Read before you change.** Read every file listed in Step 1 in full before editing anything.
- **No hardcoded fallbacks** that silently mask a broken pipeline.

### Bar layout (preserve exactly)
```
┌────────────┬───────┬────────┬──────────┬───────────────────────────┬────────┬────────┐   ┌─────────────┐
│     🛍️     │  🏷️  │   ⭐   │    🏪   │                           │   📷  │   🎙️   │   │     🔍      │
│ Categories │ Price │ Rating │ Supplier │   AI search input space   │ image  │ voice  │   │   Search    │
└────────────┴───────┴────────┴──────────┴───────────────────────────┴────────┴────────┘   └─────────────┘
        └──────────── combined facets (apply together) ────────────┘   └─ new builds ─┘
```

---

## 2. Architecture (corrected request flow)
```
┌─ Frontend (reuse FilterSearchBar / ProductSearchFilterBar) ─────────────┐
│  Category·Price·Rating·Supplier·[AI text]·📷 image·🎙 voice·🔍         │
│  debounced input · cursor pagination · RTL · renders grid + facet counts│
└───────────────┬─────────────────────────────────────────────────────────┘
                │ GET /search/filtered   POST /search/by-image   POST /search/voice
                ▼
┌─ routers/search.py  (entry · validation · rate-limit) ───────────────────┐
└───────────────┬──────────────────────────────────────────────────────────┘
                ▼
┌─ controllers / AdvancedFilterService + AdvancedSearchEngine ────────────────┐
│   voice → Whisper/Web-Speech → text ─┐                                      │
│   image → CLIP embedding ────────────┼─► HYBRID RETRIEVAL ─► RRF merge      │
│   text  → existing NLP parser ───────┘     ├─ lexical: PostgreSQL FTS/ILIKE │
│                                            └─ semantic: pgvector (text+CLIP)│
│   then: SQL WHERE (category·price·rating·supplier·stock) → sort → cursor    │
│   providers/ = embeddings + CLIP + Whisper (+ optional LLM re-rank)         │
└───────────────┬─────────────────────────────────────────────────────────────┘
                ▼
   database (products + pgvector index + facet-count materialized views)
                ▲
   Redis cache (popular queries + warm facets) sits in front of the service
```
> Note the direction: **frontend → router → service → (providers + database) → JSON → frontend**. Routers are the entry point, not a step after the database.

---

## 3. Step-by-step implementation

### `# ____ STEP 1 — RECON (read in full before any edit) ____`
- Frontend: `FilterSearchBar.tsx`, `ProductSearchFilterBar.tsx`, the products page (`searchProducts` client + URL-param state: `search, category, sort, minPrice, maxPrice, brand, color, supplier, minRating, trending, newArrivals`), the web `Header`, the mobile `HeaderBar`, `themeStore`, translations (EN/AR search keys).
- Backend: `routers/search.py` (`/search/advanced`, `/search/filtered`, `/search/fuzzy`, `/search/predict`, `/search/trending`), `services/advanced_filter_service.py`, `AdvancedSearchEngine`, `AISearchService` (NLP `parsed` dict, `expand_query` synonyms, `_build_postgres_tsquery`, `_build_postgres_search_document`, `_database_supports_postgres_fts`, `get_autocomplete_suggestions`, fuzzy `get_close_matches`), the chatbot NL search (`_extract_search_keywords`) as the reference parser, and `providers/`.
- **Output:** a short note confirming current behavior + the exact response shape of `/search/filtered` today. **Do not change code yet.**

### `# ____ STEP 2 — RELOCATE BAR TO HEADER (no restyle) ____`
- Move the existing bar into the global header, centered **after the ZOZI logo**, on web.
- **Reconcile mobile:** the mobile `HeaderBar` is intentionally tall and currently states *"the search lives in ProductSearchFilterBar, not here."* Decide one source of truth (recommended: keep `ProductSearchFilterBar` as the bar, mount it inside/under the header region) so you do **not** render two search bars or break the lime header layout.
- **Done when:** one bar, correct position, identical styling, LTR + RTL, all three densities.

### `# ____ STEP 3 — HYBRID SEARCH CORE (backend) ____`
- Keep the lexical path (PostgreSQL FTS + ILIKE) as-is.
- Add a semantic path: embed the parsed query → nearest-neighbor over `products.embedding` (pgvector).
- Fuse lexical + semantic with **Reciprocal Rank Fusion**; then apply hard filters as SQL `WHERE` (category, min/max price, min rating, supplier, in_stock, brand, color, size, has_video); then `sort` (`relevance|price_asc|price_desc|rating|newest`); then **cursor pagination**.
- Extend the **existing** parser (do not replace): add multi-item parsing so *"black blouse with black pant"* yields two product intents.
- **Done when:** exact brand/price queries still resolve lexically; fuzzy/typo queries improve via semantic; combined filters apply simultaneously.
```
lexical hits  ─┐
               ├─► RRF score = Σ 1/(k + rank_i)  ─► filter WHERE ─► sort ─► cursor page
semantic hits ─┘
```

### `# ____ STEP 4 — AI PROVIDERS (`backend/providers`) ____`
- Add an **embedding provider** (text → vector) and a **CLIP provider** (image+text → shared vector space) and a **Whisper provider** (audio → text). CPU-friendly, quantized models; lazy-load; cache the model in memory.
- All providers behind a single interface with graceful degradation: if semantic/visual is unavailable, fall back to lexical **and report `mode: "lexical"`** (never silent zeros).
- **Done when:** providers return vectors/transcripts and are unit-tested with a tiny fixture.

### `# ____ STEP 5 — IMAGE SEARCH (new build) ____`
- `POST /search/by-image` (multipart `file`): validate type/size → CLIP-embed → nearest-neighbor in pgvector → same response shape as `/search/filtered`.
- Wire the existing 📷 `onImageSearch` handler (currently a stub: `searchImageSoon: "AI image search coming soon!"`) to this endpoint with an upload progress + preview state.
- Add **rate limiting + abuse guards** (this is a cost surface).
- **Done when:** uploading a product photo returns visually similar products.

### `# ____ STEP 6 — VOICE SEARCH (new build, reuses parser) ____`
- 🎙 → browser **Web Speech API** (fallback: `POST /search/voice` → Whisper) → **text** → feed the **existing** NLP parser → call `/search/filtered`.
- Show listening state + interim transcript; respect RTL/Arabic locale.
- **Done when:** *"Do you have black blouse with black pant"* → transcript → lists black blouses **and** black pants.

### `# ____ STEP 7 — FACETED COUNTS + CACHE + INDEXES ____`
- Return **facet counts** that reflect the *current* filter state (count per category/brand/price-range/supplier given the other active filters).
- Back hot facets with **materialized views** refreshed on a cron (≈15 min) + a **Redis** cache for popular query+filter combos (invalidate on product write).
- DB: enable `pgvector`; add `products.embedding vector(N)`; create an **HNSW/IVFFlat** index; add composite indexes `(category, is_active, is_deleted)`, `(price)`, `(supplier_id)`, and a GIN index on `attributes_json`.
- **Done when:** facet chips show live counts; repeated popular queries served from cache < 300ms.

### `# ____ STEP 8 — FRONTEND WIRING ____`
- Debounce the input; drive results via cursor pagination ("Load More"); render the grid + facet chips; keep `glass-dropdown` panels floating (existing `z-[999]` fix); preserve URL-param sync and supplier-storefront redirect on exact supplier match.
- Show `mode` (lexical/semantic/visual/hybrid) subtly for debugging; show `corrected_query`/`suggestions`.
- **Done when:** Category + Price + Rating + Supplier apply **together** and update counts without a full reload; works LTR/RTL, light/dark, all densities.

### `# ____ STEP 9 — PERFORMANCE GUARDRAILS ____`
- Enforce **<300ms p95** with Redis warm; cap candidate set before RRF; paginate; lazy-load providers; rate-limit image/voice.
- **Done when:** a load test (k6/Locust) holds p95 < 300ms at target concurrency.

---

## 4. Endpoint contract (agree first, build to it)
```
GET  /search/filtered
     ?q=&category=&brand=&color=&size=&min_price=&max_price=&min_rating=
     &supplier=&sort=&has_video=&in_stock=&cursor=&limit=
POST /search/by-image      (multipart: file)        → same response shape
POST /search/voice         (audio | {text})         → { transcript } then client calls /search/filtered

Response:
{
  "products": [ ... ],
  "total": 1234,
  "next_cursor": "...",
  "facets": { "categories":[{"label":"T-Shirts","count":123}], "brands":[...], "price_ranges":[...], "suppliers":[...] },
  "suggestions": ["t-shirt", "t-shirts men"],
  "corrected_query": "t-shirt",
  "mode": "hybrid"          // lexical | semantic | visual | hybrid
}
```

---

## 5. Testing
- **Backend** → `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\tests`
  - lexical exact (brand/price), semantic fuzzy/typo, image (CLIP), voice→parser, **combined filters**, multi-item voice query, empty/no-results, facet-count correctness, rate-limit, provider-fallback (`mode:"lexical"`).
- **Frontend Playwright e2e** → place specs where your `playwright.config.ts` `testDir` points (existing specs live in `frontend/web_app/e2e/`, e.g. `command-center.spec.ts`); **Jest/component tests** → `D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\__tests__`.
  - bar renders in header after logo; combined filter updates grid + counts; image upload returns similar products; voice query returns results; **RTL** render; light/dark; densities; debounce + load-more.
- Run both suites to green before proceeding.

## 6. Acceptance criteria
- "Do you have T-shirt" returns T-shirts via the **existing** parser (no rebuild).
- Voice "black blouse with black pant" → returns black blouses **and** black pants.
- Uploaded photo → visually similar products (CLIP + pgvector).
- Category + Price + Rating + Supplier apply **simultaneously** and update **facet counts**.
- Exact brand/price queries still resolve via lexical FTS (precision not degraded by vectors).
- Bar correct in **LTR & RTL**, light & dark, all three densities; one bar only (no duplicate on mobile).
- p95 < 300ms with Redis warm; backend + Playwright suites green.

## 7. Definition of done
- All steps green; no silent fallbacks; providers degrade gracefully with `mode` reported.
- Update `documents/CODEBASE_STATUS_MATRIX.md` (search/filter/sort rows → Implemented + verified, with the new endpoints, providers, pgvector migration, and test evidence) **only after** suites pass.

# _____________________________________________________________________________________________[ADVANCED SMART SEARCH · FILTER · SORT BAR — IMPLEMENTATION]

# _____________________________________________________________________________________________ Inbox 
┌─────────────────────────────────────────────────────────────┐
│  UnifiedInboxBridge (new)                                   │
│  ┌─────────────────────┐    ┌──────────────────────────┐    │
│  │ useUnifiedInbox()   │    │ useThreadMessages()      │    │
│  │ → /comms/unified-   │    │ → /chat/threads/{id}/    │    │
│  │   inbox?lens=...    │    │   messages               │    │
│  └────────┬────────────┘    └────────┬─────────────────┘    │
│           │                          │                      │
│     setThreads(items)          setMessages(items)           │
│           │                          │                      │
│     ┌─────▼──────────────────────────▼──────┐               │
│     │         CommShell Context             │               │
│     │  (threads, messages, activeThread)    │               │
│     └─────┬─────────────────────┬───────────┘               │
│           │                     │                           │
│     ┌─────▼──────┐        ┌─────▼──────┐                    │
│     │  Rail      │        │  Stage     │                    │
│     │  (threads) │        │  (messages)│                    │
│     └────────────┘        └────────────┘                    │
│                                                             │
│  Loading/error via CSS classes + MutationObserver           │
│  → .comm-threads-loading, .comm-threads-error               │
│  → .comm-messages-loading, .comm-messages-error             │
│                                                             │
│  Retry via: window.dispatchEvent(new CustomEvent(           │
│               'comm-refetch'))                              │
└─────────────────────────────────────────────────────────────┘

# _____________________________________________________________________________________________ Inbox 


# _____________________________________________________________________________________________ List of Problem to be fix.

# _________________________________________________ 






# _____________________________________________________________________________________________ List of Problem to be fix.





# Web_app -> Pages: 

## Customer
		
	✅ Customer Registration & Login	
	✅ OTP / Authentication	
	✅ Customer Profile	
	✅ Address Book	
	✅ Wishlist	
	✅ Shopping Cart	
	✅ Smart Checkout	
	✅ Multiple Payment Methods	
	✅ Cash on Delivery (COD)	
	✅ Real-Time Order Tracking	
	✅ Order History	
	✅ Invoice Download	
	✅ Returns & Refund Requests	
	✅ Ratings & Reviews	
	✅ Notifications	
	✅ Search & Advanced Filtering	
	✅ Product Recommendations (Foundation)	
	✅ Discount & Coupon Support	
	
	
2. Supplier Platform (92%)	
	
Complete Digital Storefront	
	
✅ Supplier Registration	
✅ KYC Verification Workflow	
✅ Digital Store Creation	
✅ Product Management	
✅ Bulk Product Upload	
✅ AI Product Description Assistance	
✅ AI Category Suggestions	
🚀 AI Picture Background Removal	
🚀 Automation and AI use for product upload
✅ Inventory Management	
✅ Pricing Management	
✅ Discount Management	
✅ Order Processing	
✅ Shipment Preparation	
✅ QR Order Handover	
✅ Sales Dashboard	
✅ Revenue Dashboard	
✅ Commission Dashboard	
✅ Payout Tracking	
✅ Store Performance Analytics	
	
	
3. Marketplace Engine (90%)	
	
This is ZoZI's core.	
	
✅ Multi-Supplier Marketplace	
✅ Single Customer Checkout	
✅ Multi-Vendor Order Splitting	
✅ Supplier-wise Commission Calculation	
✅ Order Routing	
✅ Stock Validation	
✅ Product Approval Workflow	
✅ Category Management	
✅ Brand Management	
✅ SKU Management	
✅ Product Status Workflow	
	
	
4. Logistics Engine (88%)	
	
One of ZoZI's strongest differentiators.	
	
✅ Multiple Logistics Partners	
✅ Smart Delivery Assignment	
✅ Pick-up Management	
✅ Delivery Management	
✅ QR-Based Handover	
✅ Proof of Delivery	
✅ Delivery Tracking	
✅ COD Management	
✅ Logistics Settlement	
✅ Delivery Charges Engine	
✅ Distance-Based Charges	
✅ Weight-Based Charges	
✅ Category-Based Charges	
✅ Hybrid Pricing Engine	
✅ Multi-City Logistics	
	
	
5. Finance & Treasury Platform (80%)	
	
A capability that many early marketplaces lack.	
	
✅ Commission Engine	
✅ Automated Commission Calculation	
✅ Supplier Payout Calculation	
✅ COD Reconciliation	
✅ Payment Reconciliation	
✅ Logistics Settlement	
✅ Revenue Reporting	
✅ Expense Tracking	
✅ Financial Dashboard	
🚧 Unified Ledger (Planned)	
🚧 Treasury Engine (Planned)	
🚧 Automated Accounting Journal (Planned)	
	
	
6. Admin Platform (90%)	
	
Complete operational control.	
	
✅ Dashboard	
✅ User Management	
✅ Customer Management	
✅ Supplier Management	
✅ Logistics Management	
✅ Product Approval	
✅ Category Management	
✅ Banner Management
		Read the banner
- Banner: 
	- manageable by the admin team/employees 
	- countries wise can be change and different. 
	- it must be complete canvas system where admin/employee can manage new banner, colors shapes, images, video, buttons, design and etc. everything can be changeable. can make any shape & and shape inside and outside complete changeable everything.
	- Banner will come at product page means main page after the header and before search-engine bar.

- Background Effects animation effects.
	- Background effect animation effects is related to the banner and celebration, season, occasion. so add into the banner-canvas to add.	
✅ Coupon Management	
✅ Order Management	
✅ Refund Management	
✅ Complaint Management	
✅ Commission Management	
✅ Reports	
✅ Settings	

	

	
7. AI Automation (80%)	
	
One of the future competitive advantages.	
	
✅ AI Product Description	
✅ AI Product Content Assistance	
✅ AI Category Assistance	
🚧 Duplicate Product Detection	
🚧 Smart Pricing Suggestions	
🚧 Fraud Detection	
🚧 Demand Forecasting	
🚧 AI Customer Support	
🚧 AI Supplier Assistant	
	
	
	
8. Automation Engine (90%)	
	
This is what makes ZoZI scalable.	
	
✅ Automated Order Workflow	
✅ Automated Supplier Payout Calculation	
✅ Automated Commission Calculation	
✅ Automated Logistics Assignment	
✅ Automated Inventory Updates	
✅ Automated Notifications	
✅ Automated COD Reconciliation	
✅ Automated Refund Workflow	
✅ Automated QR Workflow	
✅ Automated Approval Workflow	
	
	
9. Security Platform (75%)	
	
✅ JWT Authentication	
✅ Role-Based Access Control	
✅ Audit Logs	
✅ Permission Management	
🚧 Multi-Factor Authentication	
🚧 Device Trust	
🚧 Fraud Engine	
🚧 Risk Scoring	
	
	
10. Business Intelligence (85%)	
	
✅ Revenue Dashboard	
✅ Sales Dashboard	
✅ Supplier Dashboard	
✅ Customer Dashboard	
✅ Order Reports	
✅ Logistics Reports	
🚧 Executive KPI Dashboard	
🚧 Predictive Analytics	
	
	
11. Multi-Country Architecture (75%)	
	
Designed from the beginning for GCC expansion.	
	
✅ Country Segregation	
✅ Multi-Currency Foundation	
✅ Country-wise Suppliers	
✅ Country-wise Customers	
✅ Country-wise Logistics	
🚧 Dynamic Country Configuration	
🚧 Country Tax Engine	
🚧 Country Payment Gateway Mapping	
	
	
12. Operations Platform (90%)	
	
This is often overlooked but very valuable.	
	
✅ Complaint Management	
✅ Refund Routing	
✅ Return Management	
✅ QR Chain of Custody	
✅ Supplier Verification	
✅ Delivery Verification	
✅ COD Verification	
✅ Operational Alerts	
	
	
Technology & Platform	
	
From an investor perspective, these aren't "features," but they reduce execution risk.	
	
Modern Web Application	
Mobile Application	
Modular Backend	
REST APIs	
Scalable Database Design	
AI Integration Foundation	
Role-Based Access Control	
Cloud-Ready Architecture	
Automation-First Design	
	
	
What Makes ZoZI Different?	
	
This is the section I would highlight in an investor deck because it's about defensibility, not just functionality.	
	
Competitive Capability	Status
Multi-vendor marketplace	✅
AI-assisted product onboarding	✅
Bulk product upload	✅
Automated supplier payouts	✅
Automated payment reconciliation	✅
QR-based logistics chain of custody	✅
Configurable logistics pricing engine	✅
Third-party logistics integration model	✅
Finance automation	✅
Treasury architecture designed	🚧
Multi-country (GCC) foundation	✅
Automation-first operations	✅
	
	
Platform Maturity Summary	
	
	Module	Completion
Customer Platform	90%
Supplier Platform	92%
Marketplace Engine	90%
Logistics Platform	88%
Finance Platform	80%
Admin Platform	90%
AI Automation	80%
Operations Automation	90%
Security	75%
Multi-Country Foundation	75%



_________________________________________________________________________________________________________________________
_________________________________________________________________________________________________________________________





# ________________________________________________________________________________________________________________________

# Current Working
1. Payment Gateway
2. Frontend UI UX fixing 					| 🚀 3
3. Mobile UI UX enhancement and fixing		| 🚀 4
4. Data base audit and fixing.				| 🚀 1
5. Finance ERP - Automation.				| 🚀 2
	Treasury architecture designed	🚧
6. Supplier Product Upload.					| 🚀 5
		🚧 Duplicate Product Detection	
		🚧 Smart Pricing Suggestions	
		🚧 Fraud Detection	
		🚧 Demand Forecasting	
		🚧 AI Customer Support	
		🚧 AI Supplier Assistant	

7. Order Flow Fixing.
8. Employees Segment.
9. Audit of Country Setup and Automation	| 🎯 6
	🚧 Dynamic Country Configuration	
	🚧 Country Tax Engine	
	🚧 Country Payment Gateway Mapping	
10. Security
	🚧 Multi-Factor Authentication	
	🚧 Device Trust	
	🚧 Fraud Engine	
	🚧 Risk Scoring	
11. Email System + Video + Chat system of the Admin.




# _____________________________________________________________________________________________ Comman Prompt
- Proceed for next step
- after implementation do the complete detailed browser test with playwright to ensure everything is running soomthly
- the test folder for backend is `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\tests`, you can keep all the test file in it.
- the test folder for frontend is `D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\__tests__`, you can keep all the test file in it.
- update also documents\CODEBASE_STATUS_MATRIX.md after ensuring.
# _____________________________________________________________________________________________ Comman Prompt

---

# _____________________________________________________________________________________________ Comman Prompt 2
- Read in detail `backend`, `frontend` carefully.
- Find the relevant files and list down of below problem. 

```


```

- Find the problem and resolve it
- after implementation do the complete detailed browser test with playwright to ensure everything is running soomthly
- the test folder for backend is `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\tests`, you can keep all the test file in it.
- the test folder for frontend is `D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\__tests__`, you can keep all the test file in it.

# _____________________________________________________________________________________________ Comman Prompt 2





- Have to align properly, `backend/controllers/**`, `backend/routers/**`, `backend/services/**` folders and files according to the moduler. 
- Do investigation in more detail for all files of `backend/controllers/**`, `backend/routers/**`, `backend/services/**` folders and files according to the moduler for shifting efficiently because we completed 75% of project we can't take risk of loss the project and make better plan for shifing and arrangement of the files.
- Read all the folders and files in detail, make plan in detail for alignment and shifting exactly into the proper folder or create folder also.
- Investigate what changes are needed also and list down.
- the test folder is `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\tests`, you can keep all the test file in it.

---

Have to align properly, `backend/controllers/**`, `backend/routers/**`, `backend/services/**` folders and files according to the moduler. 
read all the folders and files in detail, make plan in detail for alignment and shifting exactly into the proper folder or create folder also.

---


delete router stubs - They are required for dynamic import mechanism and do complete proper wiring. a
delete dependencies/db.py or dependencies/auth.py - Used by 71+ files; would require widespread changes	

`db → models → services → controllers → routers → frontend`

"""
	Database
		↓ (db.database, db.base, db.schemas)
	Models
		↓
	Services  (business logic, database access)
		↘
	Controllers  (business logic orchestration, uses Services + Models directly)
		↓
	Routers  (HTTP endpoints, use Controllers)
		↓
	Frontend
"""

"""
	Database
		↓ (db.database, db.base, db.schemas)
	Models
		↓
	Providers (ai, automation process, bg removal, serach engine, vectorization, )
		↓
	Services  (business logic, database access)
		↘
	Controllers  (business logic orchestration, uses Services + Models directly)
		↓
	Routers  (HTTP endpoints, use Controllers)
		↓
	Frontend
"""


Read all the files of services and controllers and make a proper domain wise plan.

1:
`Domin list` | `Sub-Domain list` | `Sub-Sub-Domain list`.

2: 
`services` available and make changes of domain wise.
`services` not available and create services.

3: 
`controllers` available and make changes of domain wise.
`controllers` not available and create services.



							HTTP/WebSocket Request
										│
										▼
					┌──────────────────────────────────┐
					│    FastAPI/ASGI Server (uvicorn) │
					└──────────────────────────────────┘
										│
										▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ MIDDLEWARE LAYER  ←  `backend/middleware/`                					  │
│                                                           				  	  │
│  Layer 1  FOUNDATION:  GZip → CORS → IP Extraction →RequestID → ApiVersion      │
│  Layer 2  SECURITY:    SecurityHeaders → ImpossibleTravel → CSRF   			  │
│  Layer 3  RATE LIMIT:  RateLimit                          					  │
│  Layer 4  GEO/CCOUNTRY: CountryContext                    					  │
│  Layer 5  OBSERVABILITY: RequestLogging                   					  │
│  Layer 6  COMPLIANCE:  PCI-DSS (prod only)                					  │
└─────────────────────────────────────────────────────────────────────────────────┘
										│
										▼
			┌────────────────────────────────────────────────────────┐
			│ ROUTERS (by surface: admin/supplier/customer/internal) │
			│  `backend/routers/{surface}/{feature}.py`              │
			│  → Validates request                                   │
			│  → Calls controller                                    │
			└────────────────────────────────────────────────────────┘
										│
										▼
			┌────────────────────────────────────────────────────────┐
			│ CONTROLLERS (by domain)  ← `backend/controllers/`      │
			│  `backend/controllers/{domain}/{name}_controller.py`   │
			│  → Orchestrates business logic                         │
			│  → Calls services                                      │
			│  → Uses models directly                                │
			└────────────────────────────────────────────────────────┘
										│
										▼
			┌────────────────────────────────────────────────────────┐
			│ SERVICES (by domain)  ← `backend/services/`            │
			│  `backend/services/{domain}/{name}_service.py`         │
			│  → Executes database operations                        │
			│  → Contains business rules                             │
			│  → Returns model objects                               │
			└────────────────────────────────────────────────────────┘
										│
										▼
					DB MODELS + SQLAlchemy   ←  `backend/models/`
										│
										▼
						DATABASE (PostgreSQL/SQLite)

"""

## ====================================================================================================

Let's refine the plan first in detail. 
---

Right now, I don't know what is the architecture audit is doing or is that working correctly or not, creating file, distributing functions and etc. should be completely into the organize way.
---

First of all, we must to draw a `grid line` what `aligned structure/circuit` we need.
Secondly, which files are crossing our architecture structured line and why and how to make changes to put into our `aligned structure`
Third, Recommendation for changes.
---

Am I correct or not ?
---

Right Now, our project backend architecture is not properly defined, all files are created by AI randomly, running all the functions of the website but what is working at where we don't know.

---

First of all, we must to draw a `grid line` what `aligned structure/circuit` we need.

---

I asked to AI what is our Architecture it said first below:

```
`db → models → services → controllers → routers → frontend`

"""
	Database
		↓ (db.database, db.base, db.schemas)
	Models
		↓
	Services  (business logic, database access)
		↘
	Controllers  (business logic orchestration, uses Services + Models directly)
		↓
	Routers  (HTTP endpoints, use Controllers)
		↓
	Frontend
"""

"""
	Database
		↓ (db.database, db.base, db.schemas)
	Models
		↓
	Providers (ai, automation process, bg removal, serach engine, vectorization, )
		↓
	Services  (business logic, database access)
		↘
	Controllers  (business logic orchestration, uses Services + Models directly)
		↓
	Routers  (HTTP endpoints, use Controllers)
		↓
	Frontend
"""
```

then I asked (Where `middleware` is fitting into the circuit of flow of backend ?)
then I got reply below:

```
## Middleware Position in the Backend Circuit

Based on the codebase analysis, here is exactly where middleware fits:

### The Complete Backend Circuit Flow

```
HTTP/WebSocket Request
        │
        ▼
  ┌──────────────────────────────────┐
  │    FastAPI/ASGI Server (uvicorn) │
  └──────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────┐
│ MIDDLEWARE LAYER  ←  `backend/middleware/`              │
│                                                          │
│  Layer 1  FOUNDATION:  GZip → CORS → IP Extraction →     │
│                         RequestID → ApiVersion           │
│  Layer 2  SECURITY:    SecurityHeaders → ImpossibleTravel │
│                         → CSRF                           │
│  Layer 3  RATE LIMIT:  RateLimit                         │
│  Layer 4  GEO/CCOUNTRY: CountryContext                  │
│  Layer 5  OBSERVABILITY: RequestLogging                │
│  Layer 6  COMPLIANCE:  PCI-DSS (prod only)             │
└────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────┐
│ ROUTERS (by surface: admin/supplier/customer/internal)│
│  `backend/routers/{surface}/{feature}.py`             │
│  → Validates request                                   │
│  → Calls controller                                    │
└────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────┐
│ CONTROLLERS (by domain)  ← `backend/controllers/`     │
│  `backend/controllers/{domain}/{name}_controller.py`  │
│  → Orchestrates business logic                         │
│  → Calls services                                      │
│  → Uses models directly                                │
└────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────┐
│ SERVICES (by domain)  ← `backend/services/`             │
│  `backend/services/{domain}/{name}_service.py`         │
│  → Executes database operations                         │
│  → Contains business rules                            │
│  → Returns model objects                              │
└────────────────────────────────────────────────────────┘
        │
        ▼
DB MODELS + SQLAlchemy   ←  `backend/models/`
        │
        ▼
   DATABASE (PostgreSQL/SQLite)
```

### Middleware's Role in the Circuit

Middleware operates as the **request preprocessing pipeline** that runs *before* any router, controller, or service code. It is the **outermost layer** of the backend logic (after the ASGI server's network handling).

### Key Integration Points

1. **Entry Point**: `main.py:65` → `setup_middleware(app)` registers all middleware on the FastAPI app
2. **Request Context**: Middleware populates `request.state` with:
   - `client_ip` (from `IPExtractionMiddleware`)
   - `country_code` / `country_scope` (from `CountryContextMiddleware`)
   - `request_id` (from `RequestIDMiddleware`)
3. **Downstream Consumption**: Routers read country context via `from middleware.rls_dependency import get_country_scope` (used in `routers/supplier/countries.py:15`)
4. **Service Integration**: `CountryContextMiddleware` calls `from services.hr.coi_service import check_approval_blocked` (line 38 of `country_context.py`) — **this is a cross-layer violation** where middleware reaches into HR service domain directly

### Architectural Problem

The circuit as documented has **no middleware layer**, but the actual code has a critical middleware layer that:
- Sets up RLS country scoping before any router runs
- Handles security headers, CSRF, rate limiting, PCI compliance
- Extracts and forwards context (IP, country, request ID) to downstream layers
- **Directly imports from `services.hr.coi_service`** and `utils.rls_interceptor` — coupling security middleware to HR domain logic and utility-level RLS interceptors

This means the **documented circuit is incomplete**. The real backend circuit includes middleware as the **first processing layer** before routers.

```
---

It is not clearly defined what is the architecture we have and what AI have to do?

---

The Audit Purpose is to Grid everything line and all code properly.
List down, First what will be the backend circuit for large project workable and be specific and according to the destroyed structure.

Secondly, we must to draw a `grid line` what `aligned structure/circuit` we need.
Third, which files are crossing our architecture structured line and why and how to make changes to put into our `aligned structure`
Forth, Recommendation for changes.

---

Am I correct ?



## ====================================================================================================

Middleware
    ↓
Routers
    ↓
Controllers
    ↓
Services
    ↓
Providers
    ↓
Models
    ↓
Database



**Goal** 
- Align all the folder, Sub-folder, files, file name, code quality, code distribution, code & file wiring, and etc. properly for scaling, handling, and need complete accuracy of code because it is big project and it is not easy task to make it porduction ready.

**Procee**
- Read complete backend and frontend.
- Read all reports in details `.\ARCHITECTURE_AUDIT_REPORT.md`, `.\DESIGN_AUDIT_REPORT.md`, `.\DATABASE_AUDIT_REPORT.md`, `.\HEALTH_AUDIT_REPORT.md`,
- evaluate all the aligation are correct or not of the reports.
- evaluate everything in detail make a pipeline properly module to module to resolve the correct problem.
- take one module and start working to resolve all the problem of 
	alignment, file name, shifting the file, folder creation, code betterment, proper router, proper controllers, 
	proper services code, proper database, if any provider using then keep in to providers folder and calling, 
	keep the test files into test folder and check everything with into the test, keep playwright file also and keep into test folder, 
	follow all the protocol properly, 
- implement to resolve everything in detail & do the test.
- regenerate the reports by running the 
	`scripts\system_architecture_audit.py`,
	`scripts\design_audit.py`,
	`scripts\health_audit.py`,
	`scripts\database_audit.py`.
- Do not use the hardcode and do the complete wiring and connections.
- Do not damage the to run the application, right now already is not running properly.

**Note**
- Do not make changes in scripts, you are not allowed.
