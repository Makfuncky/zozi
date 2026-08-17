# =============================================================================
# ZOZI FEATURE DEFINITIONS — SPEC-DRIVEN (v2 schema)
# =============================================================================
#
# feature_tracker.py does everything else: finds files, tables, routes, tests,
# and computes the completion percentage.
#
# Write WHAT a feature must do. NEVER write file names/paths in `description` —
# the tracker finds the evidence in the codebase. Only the optional `expected:`
# block may list target paths (use the P1 naming) so the tracker can verify them.
#
# The tracker auto-extracts checkpoints from `description`:
#   * `schema.table`         -> DB-table checkpoint
#   * `/route/{param}/...`   -> API-route checkpoint
#   * UPPER_CASE statuses    -> state-machine checkpoint
#   * `snake_case` backticks -> field/identifier checkpoint
#   * **bold phrases**       -> capability checkpoint
#   * **Step N — ...**       -> milestone checkpoint
# Best worked example: feature SYS_007 (Order Tracker).
# =============================================================================
#
# =============================================================================
# P1 - ARCHITECTURE PRINCIPLES & RULES:
# =============================================================================
# ^## BACKEND "circuit":  Client → Middleware → Routers (thin) → Controllers (orchestrate/auth) → Services (business logic + DB) → Models/Providers/Redis → PostgreSQL (PgBouncer) + External APIs.
#    *- backend/routers/      → Keeping files [ backend/routers/{surface}_{domain}_{feature}_router.py (flat) ] - thin: accept request, call a service, return response_model. New controllers auto-emit thin routers into routers/ TOP-LEVEL carrying the AUTO-GENERATED marker; routers/generated/ holds only the auto_router.py generator + AUTO_ROUTER.md + generated health endpoints. Legacy fat routers stay hand-written and still contain logic + db writes — these will be removed once all controllers are confirmed 100% accurately ready for auto-generation.
#    *- backend/controllers/  → Keeping files [ backend/controllers/{domain}/{surface}_{feature}_controller.py ] - NEW controllers declare routes with @get/@post/... from routers.generated.auto_router (which auto-emits the thin routers). CURRENT STATE IS HYBRID: many controllers still import FastAPI (APIRouter/Depends/HTTPException) and a few perform db writes (core/ai_controller.py, treasury/cash_management_write_controller.py) — these violate the target. TARGET: controllers orchestrate only, delegate all DB to services, never import FastAPI. Domains: admin, ai, catalog, commerce, comms, core, customer, delegators, documents, finance, gateway, geography, governance, hr, identity.
#    *- backend/services/     → Keeping files [ backend/services/{domain}/{surface}_{feature}_service.py ] - own DB access + transactions (services/<domain>/*.py already exists & is full: admin/, security/, and per-domain service modules). Single source of business logic + get_db() sessions.
#    *- backend/providers/    → 3rd-party/AI adapters; subclass providers/_base BaseProvider/BaseAIProvider, implement health_check(). Called ONLY by services/ and jobs/. Never by routers. Subpackages: ai, analytics, auth, automation, comms, finance, geography, image, legacy, media, news, payments, provider_test, security, voice.
#    *- backend/models/       → Keeping files [ backend/models/{domain}/{surface}_{feature}_model.py (subfolders by domain) ] - SQLAlchemy ORM, all inherit db/base.Base; live in domain schemas (customer/supplier/logistics/admin/employee), NO core/platform/identity schemas.
#    *- backend/db/           → base.py (Base + metadata), database.py (engine + get_db() session factory), session.py, transaction.py, schemas.py (schema registry), models.py, create_tables.py / init_db.py (dev-only create_all, refuses prod), seeds/ (idempotent seed data: seed.py, treasury_seeder.py, demo.py), database_logging.py. get_db() is the ONLY session source; PgBouncer in front; keyset cursor helper for hot lists.
#    *- backend/jobs/         → background workers / consumers: background_tasks.py, fraud_monitoring.py, ghost_order_detector.py, mcp_server.py, seed_all.py, threat_feed_updater.py. Heavy/AI/off-request work only (never routers).
#    *- backend/events/       → event_publisher.py (Redis pub/sub), payment_events.py (domain event schemas). Services publish commands/events; jobs/ consumers subscribe.
#    *- backend/middleware/   → Keeping files [ backend/middleware/{function}_middleware.py - flat ] orchestrator.py (ordered pipeline) + modules: api_version, country_context, csrf, database_security, device_binding, impossible_travel, ip_extraction, logging, pci_dss_compliance, rate_limit, request_id, rls_dependency, security_headers, webhook_ip_whitelist, webhook_verification, zero_trust_auth. Enforces security/RLS/geo before routers; imports only utils/settings/db(read-only).
#    *- utils/, middleware/   → cross-cutting only.
#
# ^## DATABASE "circuit": 
#    *- Engine (QueuePool sync today / AsyncPG at scale) sits behind PgBouncer (transaction mode) → get_db() yields one session → ORM models across domain schemas; Alembic is the single schema source of truth (create_all dev-only); RLS enforced on every session via ONE canonical enforcer (target: db/security.py — currently scattered across rls_dependency, rls_middleware, rls_interceptor, rls_context, country_context and MUST be consolidated); Redis fronts catalog/session/cache reads.
#    *- Hot lists use keyset cursors (NEVER OFFSET); cross-domain FKs allowed and resolved from ORM metadata; check_connection_health() → SELECT 1 backs /health/ready.
#    *- Schema policy: each domain owns its own actor tables (domain-actor isolation). NO central "core" or "platform" user table. Each surface authenticates against its own domain schema:
#       TARGET: customer login  → customer.profiles / customer.accounts, supplier login  → supplier.supplier_accounts, admin login     → admin.admin_accounts, employee login  → employee.employees, logistics login → logistics.logistics_partners
#       Shared reference data (countries, currencies, roles catalog) lives in country / configuration schemas.
#       JWT sessions + token blacklist live in Redis, NOT in a DB schema.
#
#   ~### 100K capacity requirements (what MUST be in place)
#     *1. Partitioning (MANDATORY for tables > 10M rows):
#         audit.audit_logs        → monthly partition (created_at)
#         analytics.snapshots     → monthly partition
#         communication.messages  → monthly partition
#         orders.orders           → quarterly partition
#         events.outbox_events    → weekly partition (processed → delete)
#         media.assets            → yearly partition
#       Cold partitions archived to object storage after retention period.
#     *2. Read/write split:
#         get_db()     → primary (writes only)
#         get_read_db()→ replica (catalog, search, analytics reads)
#       Replica lag SLO: < 1s. Monitored via pg_stat_replication.
#     *3. Connection budget:
#         App: pool_size=5 per process (NEVER more)
#         PgBouncer: max_client_conn=1000, default_pool_size=50
#         PostgreSQL: max_connections=100 (behind PgBouncer)
#         Read replicas: same budget, 95% reads routed there
#       Long transactions (>500ms) moved to jobs/ background workers.
#     *4. Redis topology:
#         Phase A: single Redis + RDB persistence
#         Phase B: Redis Sentinel (failover) + pub/sub for WS
#         Phase C: Redis Cluster (sharded) for 100K+ ops/sec
#     *5. Retention & archive:
#         sessions/carts/notifications → hard delete 30/90 days
#         audit_logs/analytics         → archive to S3 after 2yr
#         events.outbox                → hard delete 7d after processed
#         media metadata               → keep forever (blobs in S3/R2)
#       Implemented via pg_cron or jobs/data_retention.py nightly.
#     *6. Read model (Phase C only — when throughput justifies):
#         CDC (Debezium) → Kafka → OpenSearch for catalog/search reads
#         Redis hydrates price/stock after OpenSearch returns IDs
#         Removes ~80% read load from PostgreSQL at scale
#     *7. Observability (required before claiming any phase):
#         pg_stat_activity → connection saturation (< 80% SLO)
#         pg_stat_replication → replica lag (< 1s SLO)
#         pg_stat_statements → top slow queries (weekly review)
#         Prometheus + Grafana dashboards + alerts
#
#   ~### Design how database management must change to support:
#       videos, images, chats, and "a range of things" (e.g., attachments, thumbnails, transcripts, reactions, moderation flags).
#
# ^## FRONTEND "circuit":  Web (Next.js 15) + Mobile (Expo RN) + shared (TS) → both call one FastAPI backend via apiFetch; web via next.config rewrites/middleware, RN via lib/ api client.
# 	~### web_app (frontend/web_app, Next.js 15) "circuit":
# 		*- frontend/web_app/src/app:        → route tree (layout/loading/error/page per folder); groups: customer, auth, admin/*, supplier/*, logistics-partner/*, wishlist, profile, chatbot, tracking; app/api/ = Next server routes (auth proxy, currency, geo, errors).
# 		*- frontend/web_app/src/components: → reusable UI: ui/ (design-system), admin/, auth/, chat/, comms/, country/, ems/, map/, supplier/.
# 		*- frontend/web_app/src/styles:     → Tailwind globals + CSS variables / base styles.
# 		*- frontend/web_app/src/lib:        → api/ (client.ts typed fetch wrapper, auth.ts, country.ts, errors.ts, index.ts); Zustand stores + useAuth/useApi via sibling hooks/.
# 		*- frontend/web_app/src/hooks:      → data-fetching + WebSocket hooks (useApi, useAuth).
# 		*- frontend/web_app/src/services:   → localizationService.ts, crossBorderService.ts, addressFormatService.ts.
# 		*- frontend/web_app/src/theme:      → design tokens (colors/spacing/typography) consumed by Tailwind + components (NO inline <style>).
# 		*- frontend/web_app/src/styles:     → global stylesheet + token mapping (Tailwind config references theme/).
# 		*- frontend/web_app/src/types:      → TS ambient/domain type decls (framer-motion.d.ts); shared types live in shared/src/types.ts.
# 		*- frontend/web_app/src/utils:      → small helpers (test.ts); prefer shared/src/utils.
# 		*- frontend/web_app/src/logo:       → brand logo assets.
# 		*- frontend/web_app/tests/mocks:    → __mocks__ / test doubles for components & api.
# 		*- frontend/web_app/root:           → next.config.ts (rewrites), middleware.ts, tailwind.config, playwright.config, e2e/.
#
# 	~### mobile_app (frontend/mobile_app, Expo RN) "circuit":
# 		*- frontend/mobile_app/app/:         → Expo Router .tsx screens + (auth)/(tabs) groups + admin/products/orders/supplier/tracking/returns folders.
# 		*- frontend/mobile_app/components/:  → ui/ (design-system components).
# 		*- frontend/mobile_app/lib/:         → api.ts (client), authStore/cartStore/currencyStore/localeStore/notificationStore (Zustand), authPrompt, countryContext, geo, paymentService, socialAuth, expoSecureStorage, errorReporter (api + stores + auth + platform helpers).
# 		*- frontend/mobile_app/theme/:       → mobile design tokens (mirrors web theme).
# 		*- frontend/mobile_app/assets/:      → images / fonts / icons bundles.
# 		*- frontend/mobile_app/android/:     → Expo-managed native Android project.
# 		*- frontend/mobile_app/mocks/:       → test mocks.
# 		*- frontend/mobile_app/e2e/:         → Playwright/Detox e2e tests.
# 		*- frontend/mobile_app/scripts/:     → build / codegen scripts.
# 		*- frontend/mobile_app/web-dist/:    → Expo web build output.
# 		*- frontend/mobile_app/root:         → app.config.js, metro.config, babel.config, expo-env.d.ts, sentry, pnpm-workspace.
#
# 	~### shared (frontend/shared) "circuit":
# 		*- src: cross-platform TS — api-core.ts (apiFetch), money.ts, i18n.ts, localization.ts, cartHelpers/checkoutHelpers/orderHelpers/productHelpers/ticketHelpers/returnsApi/wishlistHelpers/notificationHelpers, adminPermissions.ts, statusColors.ts, requestCache.ts, realtime.ts, chatbot.ts, types.ts, theme.ts + theme.native.ts, components/, logo/, __tests__.
#
# ^## Combine "circuit":
# 	*- shared/src imported by web_app (@shared alias) and mobile_app (workspace pkg); keeps api-core, money/i18n, cart/checkout/order, permissions, types identical.
# 	*- Transport: both call backend via apiFetch; web via next.config rewrites + middleware.ts → FastAPI; RN via lib/api.ts → same backend.
# 	*- Backend: single FastAPI serves both; middleware/orchestrator applies security; dependencies/ injects country/RLS/COI; routers thin → controllers orchestrate → services own DB.
# 	*- Monorepo: web_app (Next) + mobile_app (Expo) + shared (TS) + root docker-compose / Makefile / pnpm-workspace.
#
# ^## Extra Files:
# 	*- use the `_extra_files/**` for keeping temporary files for making changes, audit, testing of architecture & etc.
#
# =============================================================================
#
# =============================================================================
# P2 - FEATURE INSTRUCTION TEMPLATE (PURE INSTRUCTION for the AI / writer):
# =============================================================================
# TODO - id: SYS_XXX
# TODO     name: <Feature Title>
# TODO     update_version: "xxx_<DD-MM-YYYY>"
# TODO     description: | the FULL binding build spec (paste your complete prompt).
# TODO       ## Capabilities:
# TODO       - bullet list of WHAT the feature does
# TODO       - reference `media_assets` for videos/images (storage-ref, not blobs)
# TODO       ## Non-negotiables:
# TODO       - **bold phrases** become capability checkpoints
# TODO       ## Step-by-step:
# TODO       - **Step 1 — ...**       -> milestone checkpoint
# TODO       ## Discussion notes:
# TODO       - **Point 1 — ...**       -> awareness point for problem and their solution.
# TODO     state_checkpoint: `PENDING`, `AI-DONE`, `TESTED`, `HUMAN-APPROVED`
# TODO     scope: roles (Customer · Supplier · Logistics · Admin · Employee · Internal)
# TODO     sections: section-wise job per panel (§I Infra, §II Customer, §III Supplier, §IV Logistics, §V Admin). One sentence each.
# TODO     file_reference: | any document and file references (e.g., `FEATURES.md`) that describe the feature in detail. Use storage-ref for media assets (not blobs).
# TODO     workflow (compulsory): define properly the workflow of the feature of `backend` and `frontend` (e.g., `backend/middleware` → `backend/routers` and etc.) and the flow of data between them.
# TODO     diagram: | mermaid diagram of the feature (if applicable)
# TODO     expected:
# TODO       backend_files:      # List of backend file paths
# TODO         - backend/routers/{surface}_{domain}_{feature}_router.py                           → auto-generated thin router                                    | (feature description is needed for particular router file)
# TODO         - backend/controllers/{domain}/{surface}_{feature}_controller.py                   → orchestrates routes, delegates services                       | (feature description is needed for particular controller file)  
# TODO         - backend/services/{domain}/{surface}_{feature}_service.py                         → owns DB writes, business logic                                | (feature description is needed for particular service file)
# TODO         - backend/middleware/{function}_middleware.py                                      → cross-cutting middleware (security, RLS, geo, logging, etc.)  | (feature description is needed for particular middleware file)
# TODO         - backend/jobs/{function}.py                                                       → background worker / consumer                                  | (feature description is needed for particular jobs file)
# TODO         - backend/events/{name}.py                                                         → event publisher / subscriber                                  | (feature description is needed for particular event file)   
# TODO         - backend/providers/{domain}/{name}_provider.py                                    → 3rd-party/AI adapter (subclass BaseProvider/BaseAIProvider)   | (feature description is needed for particular provider file)
# TODO       database files:    # List of setup of the database
# TODO         - backend/db/base.py                    # Single declarative Base (re-exported from models)
# TODO         - backend/db/database.py                # Engine, pool, SSL, schema_translate_map, instrumentation
# TODO         - backend/db/session.py                 # get_db, get_read_db, get_service_session, context managers
# TODO         - backend/db/transaction.py             # Transaction helpers/context managers
# TODO         - backend/db/schemas.py                 # Schema registry
# TODO         - backend/db/models.py                  # Model registry / re-exports
# TODO         - backend/db/create_tables.py           # Dev-only create_all
# TODO         - backend/db/init_db.py                 # Dev-only DB init (refuses prod)
# TODO         - backend/db/security/                  # rls.py (Canonical RLS enforcer (replaces scattered middleware)), policies.py (Per-schema RLS policy SQL strings)
# TODO       - backend/db/setup/                     # check.py (Pre-flight DB checks), health.py (/health/ready and /health/db helpers), reset.py (Dev-only create_all/drop_all (guarded)) etc.
# TODO         - backend/db/seeds/                     # demo.py (seed_data, _ensure_demo_user), seed.py (Idempotent seed data), treasury_seeder.py (Treasury seed data) & etc.
# TODO         - backend/db/database_logging.py        # Query instrumentation, pool metrics
# TODO         - backend/alembic/                      # Alembic migrations (single source of truth for schema)
# TODO       model files:      # List of DB model files
# TODO         - backend/models/{domain}/{surface}_{feature}_model.py → SQLAlchemy ORM model | (feature description is needed for particular model file)
# TODO           - mixins.py           # AuditMixin, SoftDeleteMixin, VersionMixin
# TODO           - ai/                 # ai models, training jobs, inference schemas
# TODO           - catalog/            # catalog.products, catalog.search_vectors
# TODO           - media/              # media.assets, media.variants, media.reactions, media.moderation_flags
# TODO           - orders/             # orders, carts, fulfillment
# TODO           - permissions/        # RBAC, roles, scopes
# TODO       frontend_web:       # List of web app file paths
# TODO         - "frontend/web_app/src/app/{surface}/{domain}_{feature}/page.tsx"
# TODO       frontend_mobile:    # List of mobile app file paths
# TODO         - "frontend/mobile_app/app/{surface}/{domain}_{feature}.tsx"
# TODO       tests:              # List of test file paths (all accumulated under tests/)
# TODO         - "tests/backend/_test_{surface}_{domain}_{feature}.py"
# TODO         - "tests/frontend/web_app/_test_{surface}_{domain}_{feature}.test.tsx"
# TODO         - "tests/frontend/mobile_app/_test_{surface}_{domain}_{feature}.test.tsx"
# TODO         - "tests/playwright/**"
# TODO       api_routes:         # List of API routes (METHOD /path)
# TODO         - "GET /channels"
# TODO         - "POST /channels/{channel_id}/messages"
# TODO       models:             # List of DB model class names
# TODO         - "DirectChatRoom"
# TODO         - "EntityChatThread"
# TODO   extra_files (optional): list any files under `_extra_files/` used for temporary changes, audits, or architecture testing (not tracked in completion %).
# =============================================================================
#
# =============================================================================
# P3 - documents/CODEBASE_STATUS_MATRIX_AUTO.md structure:
# =============================================================================
# *- | Sno | Surface | Domain | Feature | Description/Operation of Feature | Visibility Functions & Details | backend:utils | backend:jobs | backend:events | backend:dependencies | backend:models | backend:db | backend:providers | backend:services | backend:controllers |  backend:routers | backend:middlewares | backend:tests | backend:connection report | frontend:web_app | frontend:mobile_app | frontend:Shared / Utils | frontend: Web Tests | frontend: Mobile Tests |Completion Status % | Remaining todo | Comments for reference |
# =============================================================================
# 
# =============================================================================
version: 1
schema: spec-driven
features:
  # ===========================================================================
  - id: SYS_001   # Communication Workspace (Chat · Email · Video · Contacts · Files)
    name: Communication Workspace (Chat · Email · Video · Contacts · Files)
    weight: 8
    update_version: "v1_14-08-2026"
    scope: Admin · Employee · Supplier - Customer - 
    details: | 
      - **For more details read the file `FEATURES.md` [Communication Workspace (Chat · Email · Video · Contacts · Files)]
    description: |
      ## Capabilities
      - **Unified Communication Workspace** — the `communication` bounded context that combines **Chat · Email · Video · Contacts · Files** for internal staff, customers and supplier/entity communication. Inherits the constitution: **RLS `country_code` on every comms row, Alembic-only migrations, event-driven cross-domain writes (outbox_events), media bytes in Cloudflare R2/S3, append-only audit, no silent fallbacks.** Strategy: **complete + wire + govern the existing ~70% skeleton; do not rebuild.**
      - **Chat (1:1 · groups · channels):** `communication.direct_chat_rooms` for 1:1, groups (roles + `@mentions`), and Slack-style `communication.internal_channels` (dept/country/project scoped, public/private, pinned, `@mention` routing). `communication.chat_attachments` → `media.media_assets` for image/video/document + **voice notes** (compressed `.ogg`/`.m4a` + `duration` + `waveform` JSON, max 5MB, S3/R2 stored). Realtime over `WebSocketManager` (`backend/events/websocket_manager.py`): typing indicators, `communication.chat_read_receipts`, presence/last-seen via Redis. **Threading** (parent `chat_messages.message_id`), edit/delete (audited to `communication_audit_trails`), **reactions** (`chat_reactions`), **FTS** (`tsvector` + GIN on `chat_messages.body`), forward, per-channel retention + legal-hold. **Every write → `communication.communication_audit_trails`.**
      - **Video rooms:** `communication.video_rooms` (`session_id`, `participants`, `started_at`/`ended_at`, `boardroom_mode`, `watermark_enabled`) with WebRTC signaling over WebSockets (`backend/events/video_signaling.py`); Postgres stores metadata/billing only. `communication.video_recordings` → **WORM/retention-locked object storage**. **Gap-fill:** real-time Whisper transcription (`communication.video_transcripts`) + AR/EN translation + `extract_action_items()` → **auto-create assigned tasks** via `communication.video_action_items` (state `STAGED` → confirm → `ASSIGNED`).
      - **Email:** `communication.internal_emails` + `communication.email_folders`; **smart router** (`email_smart_router_service.py`) resolves directory-first (in-DB instant delivery for in-org recipients) and only routes explicit external addresses to SMTP/relay — *internal mail never touches SMTP*. Threading, labels/rules, FTS, attachments with size limits + virus-scan hook. External controls: **domain allow-lists, DLP PII scan (`dlp_service.py`), mandatory compliance BCC per role**. **Gap-fill endpoints** `POST /email/bulk`, `POST /email/from-alias`. `communication.notification_queue` / `email_messages` / `push_logs` are provider-agnostic with webhook open/click tracking → `communication.email_events` + retry + **DLQ** (`event_dead_letter`).
      - **Contacts & internal-first routing:** directory resolution (`contacts_service.py`) drives internal-first delivery — resolve recipients in-org first (in-DB), only explicit external addresses hit SMTP. Customer/supplier support inboxes surface as `communication.conversations` with `channel_type` (`DM`/`group`/`email`/`channel`). Employee directory viewer respects RLS `country_code` (Oman manager never sees KSA staff).
      - **Files & media:** metadata in `media.media_assets` (`url`, `mime`, `hash`, `w/h`, `ai_status`) with bytes in Cloudflare R2; pipeline Original → Optimized → Thumbnail → WebP → CDN; lifecycle Hot → Warm → Cold → Destroyed after legal retention. **Never store attachment bytes in DB.** Voice notes ≤5MB `.ogg`/`.m4a`.
      - **Realtime chat** — 1:1, groups, channels with typing indicators, read-receipts, presence/last-seen (Redis), threading, edit/delete (audited), reactions, forward, FTS search, per-channel retention + legal-hold. **Voice notes** inline in chat (≤5MB `.ogg`/`.m4a` + waveform JSON). **Every write → `communication.communication_audit_trails`.**
      - **Confluence — single employee surface (merged from SYS_012):** one surface for every employee conversation — `communication.conversations` + `communication.conversation_messages` + `communication.conversation_participants` keyed by `channel_type` (`DM`/`group`/`email`/`channel`) so chat, email, video and tickets unify into one timeline. **Ranked unified-inbox triage** `you → mentions → DMs → groups → email → channels` via `UnifiedInboxBridge` + `useUnifiedInbox()` + `useThreadMessages()` + `CommShell` React context; each thread deep-links to its entity/workspace. **Modality (chat / email / video) as a filter**; **proxy-masking layer** `communication.proxy_messages` / `proxy_channels` / `proxy_sessions` protects external contacts' real numbers (audited, reuses masking contract); **war-room / entity-attached threads** (shared with SYS_007): click a batch/order → the exact chat about it, `@mentions` deep-link to the screen with an action button, auto-translate AR↔EN; **explicit loading/error states** via `.comm-threads-loading` / `.comm-messages-loading` classes with realtime-feed errors surfaced (no silent zeros).
      - **Cross-cutting comms:** **(ADDED)** auto-translate AR↔EN for chat/channel messages (`translation_service.py`); **(ADDED)** announcements with mandatory read-confirmation tracking (`announcement_service.py`, escalates unread to manager after SLA); **(ADDED)** meeting-cost indicator (participants × duration × rate) on video rooms to curb meeting bloat; every comms action logged to `hr.employee_activity_logs` / `communication.communication_audit_trails` for **eDiscovery export**. Tightly wired to **SYS_005** (EMS identity/sessions, `user_devices`, risk-score, RLS-on-login), **SYS_009** (AI transcription/translation), **SYS_003** (Treasury payslip delivery via notify).

      ## Non-negotiables
      - **Realtime presence** on every chat and video session (typing + online via Redis; never store ephemeral presence in Postgres).
      - **Internal-first routing** — in-DB delivery for org recipients, SMTP/relay only for explicit external addresses.
      - **DLP + allow-list + compliance BCC** on every external email; quarantine/block on violation (never silent).
      - **WORM/retention-locked** video recordings + append-only `communication.communication_audit_trails` (eDiscovery-ready).
      - **Media attachments** delivered through object storage with metadata only in `media.media_assets` (no DB blobs).
      - **Voice notes + waveform** supported inline in chat (max 5MB, `.ogg`/`.m4a`).
      - **Auto action-items from video** staged for human confirm before task assignment.
      - **Explicit error states** when realtime feed is unavailable (no silent zeros; DLQ surfaced).
      - **RLS `country_code`** on every comms row; cross-country reads return 0 rows (fail-closed).

      ## Data model (`communication` schema unless noted)
      - `communication.direct_chat_rooms`
      - `communication.internal_channels`
      - `communication.channel_members`
      - `communication.channel_pins`
      - `communication.chat_messages` (monthly range partition on `created_at`)
      - `communication.chat_attachments`
      - `communication.chat_read_receipts`
      - `communication.chat_reactions`
      - `communication.chat_threads`
      - `communication.video_rooms`
      - `communication.video_participants`
      - `communication.video_recordings`
      - `communication.video_transcripts`
      - `communication.video_action_items`
      - `communication.internal_emails`
      - `communication.email_threads`
      - `communication.email_folders`
      - `communication.email_labels`
      - `communication.email_rules`
      - `communication.email_events`
      - `communication.notification_queue`
      - `communication.email_messages`
      - `communication.push_logs`
      - `communication.announcements`
      - `communication.announcement_read_receipts`
      - `communication.conversations`
      - `communication.conversation_messages`
      - `communication.conversation_participants`
      - `communication.proxy_messages`
      - `communication.proxy_channels`
      - `communication.proxy_sessions`
      - `communication.communication_audit_trails`
      - `communication.legal_holds`
      - `communication.dlp_quarantine`
      - `media.media_assets`
      - `hr.employee_activity_logs`

      ## API (comms-scoped)
      - `GET /channels` · `POST /channels` · `GET /channels/{channel_id}` · `PATCH /channels/{channel_id}` · `DELETE /channels/{channel_id}`
      - `GET /channels/{channel_id}/messages` · `POST /channels/{channel_id}/messages`
      - `PATCH /messages/{message_id}` (edit, audited) · `DELETE /messages/{message_id}`
      - `POST /messages/{message_id}/react` · `POST /messages/{message_id}/forward`
      - `GET /direct-chats` · `POST /direct-chats`
      - `POST /chat/voice-note` · `GET /chat/{room_id}/read-receipts` · `POST /chat/typing` · `GET /chat/search`
      - `GET /video-rooms` · `POST /video-rooms` · `GET /video-rooms/{room_id}` · `PATCH /video-rooms/{room_id}`
      - `POST /video-rooms/{room_id}/signal` (WebRTC) · `POST /video-rooms/{room_id}/join`
      - `GET /video-rooms/{room_id}/transcript` · `POST /video-rooms/{room_id}/action-items` · `POST /video-rooms/{room_id}/recording/lock` (WORM)
      - `GET /email` · `GET /email/folders` · `POST /email/folders` · `GET /email/{id}` · `POST /email` (compose, internal-first) · `POST /email/bulk` · `POST /email/from-alias`
      - `GET /email/{id}/read` · `POST /email/{id}/labels` · `GET /email/search` · `POST /email/rules` · `GET /email/threads/{thread_id}`
      - `GET /announcements` · `POST /announcements` · `POST /announcements/{id}/ack` · `GET /announcements/{id}/read-status`
      - `GET /contacts` · `GET /contacts/{id}` · `GET /directory/search`
      - `GET /files` · `POST /files` (upload → R2) · `GET /files/{id}`
      - `POST /comms/translate` · `POST /comms/translate/message/{message_id}`
      - `GET /conversations/inbox` (ranked triage) · `GET /conversations` · `GET /conversations/{conversation_id}` · `GET /conversations/{conversation_id}/messages` · `POST /conversations/{conversation_id}/messages` · `PATCH /conversations/{conversation_id}/read`
      - `GET /confluence/channels` · `POST /confluence/channels` · `POST /confluence/channels/{channel_id}/archive` · `GET /confluence/war-room/{entity_type}/{entity_id}` · `POST /confluence/threads`
      - `GET /comms/audit-trail` · `GET /comms/eDiscovery/export` · `POST /comms/legal-hold` · `GET /comms/legal-hold` · `POST /comms/dlp/quarantine/{id}/review`
      - `GET /comms/proxy/contacts` (masked) · `POST /comms/proxy/unmask/{session_id}`

      ## State machine
      - `ACTIVE` → `ARCHIVED` (channel/conversation)
      - `ONLINE` → `OFFLINE` (presence)
      - `MASKED` → `UNMASKED` (proxy contact)
      - `UNREAD` → `READ` (message/conversation)
      - `OPEN` → `ARCHIVED` (announcement/ticket)
      - `DRAFT` → `SENT` (internal email in-DB) / `RELAYED` (external via SMTP)
      - `RELAYED` → `DELIVERED` / `BOUNCED` → `QUARANTINED` (DLP hit)
      - `RECORDING` → `WORM_LOCKED` (video room)
      - `STAGED` → `ASSIGNED` (video action-item tasks, after human confirm)
      - `LIVE` → `ENDED` → `TRANSCRIBED` (video session)

      ## Automations (comms-scoped)
      - **Auto comms compliance (#9):** on every message/email write, evaluate DLP rules + allow-lists + virus-scan → internal-first routing; block/quarantine external violations; auto legal-hold on case open; retention purge with hold override. Exception: DLP quarantine review queue.
      - **Auto meeting intelligence (#10):** on recording end, Whisper transcript + translation → action items staged → confirm → assigned with due dates; RAG-index transcript. Exception: low-confidence items → review list.
      - **HR chatbot + voice assistant (#11):** NL/voice (Whisper) over handbook/policy RAG (pgvector) → answers + draft requests (leave, expense, 1:1) via confirm cards. Exception: explicit "cannot verify" mode.
      - **Announcement read-confirm tracking:** mandatory read-confirm; escalates unread to manager after SLA.

      ## UI/UX layout
      - **Chat:** 3-pane (rooms/channels | thread | details/members); `VoiceNotePlayer` inline waveform; `AttachmentLightbox`; pinned + search; per-channel retention badge; `ReactionBar`; `TypingIndicator`; `ReadReceipts`.
      - **Email client:** folders left, list, reading pane; compose with **directory-first autocomplete** + internal/external chip; `DlpWarningBanner` before external send; labels/rules builder; thread view.
      - **Video:** `VideoScheduler` calendar; join via token; live `VideoTranscriptPanel` (AR/EN toggle); `ActionItemsPanel` with assign-confirm; watermark/boardroom toggles; recording → WORM badge; `MeetingCostIndicator`.
      - **Contacts:** directory with org-chart resolver; internal-first chips; external masked via proxy (`ProxyMaskBadge`).
      - **Confluence single surface:** `UnifiedInboxBridge` + `CommShell` shell with ranked triage pane (you → mentions → DMs → groups → email → channels); `ModalityFilter` (chat/email/video); `useUnifiedInbox()` + `useThreadMessages()` hooks; `.comm-threads-loading` / `.comm-messages-loading` states; war-room/entity-attached thread deep-links (`WarRoomThread`).
      - **Comms Hub (admin):** channels admin, eDiscovery portal (`EDIscoveryExport`), audit viewer, legal-hold controls (`LegalHoldPanel`), `AnnouncementBanner` read-confirm, moderation.
      - **UX principles:** skeleton loaders, explicit empty/error states, tabular numerals, ARIA + keyboard, density toggle, country switcher re-sets RLS; mobile = biometric login, camera voice notes, push approvals.

      ## Step-by-step
      - **Step 1 — Realtime chat core.** `WebSocketManager` delivery for `direct_chat_rooms` / `internal_channels` with `chat_read_receipts`, typing + presence (Redis), threading, reactions, edit/delete (audited). *Done when:* message delivered to all participants within SLA and receipt + audit persisted.
      - **Step 2 — Attachments, voice & media.** `chat_attachments` → `media_assets`; inline voice notes (`.ogg`/`.m4a` + waveform) ≤5MB; forward + FTS search. *Done when:* media renders from R2 via CDN; voice-note waveform plays inline.
      - **Step 3 — Channels, grouping & legal-hold.** `internal_channels` (public/private, pinned, role + `@mentions`) with per-channel retention + legal-hold; Contacts/directory-first resolution. *Done when:* external channel members cannot see real personal contacts; retention badge shown.
      - **Step 4 — Email smart router + DLP.** `internal_emails`/`email_folders` with directory-first in-DB routing, threading, labels/rules, FTS, virus-scan; external path enforces allow-list + DLP PII + compliance BCC; add `POST /email/bulk`, `POST /email/from-alias`. *Done when:* internal email never touches SMTP, external DLP block/quarantine test passes.
      - **Step 5 — Video rooms & intelligence.** `video_rooms` (WebRTC signaling, tokens, watermark, boardroom mode) with realtime Whisper transcription + AR/EN translation; `extract_action_items()` → staged tasks → confirm → assigned; recordings to WORM. *Done when:* admin console shows live room health + transcript; action items appear as confirm cards.
      - **Step 6 — Unified inbox (Confluence), announcements & eDiscovery.** `conversations` + `conversation_messages` + `conversation_participants` with `channel_type` (`DM`/`group`/`email`/`channel`); `UnifiedInboxBridge` + `useUnifiedInbox()` ranked triage `you → mentions → DMs → groups → email → channels` with `CommShell` + `useThreadMessages()`; modality filter (chat/email/video); `.comm-threads-loading` / `.comm-messages-loading` explicit states + realtime-error surfaced; `proxy_*` masking for external contacts (audited); war-room/entity-attached threads with `@mention` deep-links + AR↔EN; announcements with read-confirm; full `communication_audit_trails` + `employee_activity_logs` export (eDiscovery). *Done when:* a single inbox renders all sources in ranked order, threads deep-link to entities, proxy masks external parties, and compliance export/eDiscovery passes.

    sections:
      §I: "Realtime infrastructure: WebSocketManager chat delivery, typing/read-receipts/presence (Redis), voice notes, channel masking, unified inbox aggregation, seed data."
      §II: "Customer: read-only visibility of support conversations where applicable; supplier support inbox handling customer conversations."
      §III: "Supplier: support inbox page handling customer conversations; masked proxy external contacts."
      §IV: "Logistics: no logistics-specific comms surface; shared notification/real-time infra only."
      §V: "Admin + Employee: Confluence unified single surface, ranked inbox triage, channels admin, eDiscovery portal, audit viewer, legal-hold controls, moderation, announcements read-confirm."
    expected:
      backend_files:
        - backend/routers/comms_chat_router.py
        - backend/routers/comms_channel_router.py
        - backend/routers/comms_email_router.py
        - backend/routers/comms_video_router.py
        - backend/routers/comms_contacts_router.py
        - backend/routers/comms_announcement_router.py
        - backend/routers/comms_notification_router.py
        - backend/routers/comms_files_router.py
        - backend/routers/comms_translate_router.py
        - backend/routers/comms_unified_inbox_router.py
        - backend/routers/comms_conversation_router.py
        - backend/routers/comms_compliance_router.py
        - backend/routers/comms_proxy_router.py
        - backend/controllers/comms/chat_controller.py
        - backend/controllers/comms/email_controller.py
        - backend/controllers/comms/video_controller.py
        - backend/controllers/comms/contacts_controller.py
        - backend/controllers/comms/announcement_controller.py
        - backend/controllers/comms/unified_inbox_controller.py
        - backend/controllers/comms/confluence_controller.py
        - backend/controllers/comms/compliance_controller.py
        - backend/services/comms/chat_service.py
        - backend/services/comms/email_router_service.py
        - backend/services/comms/email_smart_router_service.py
        - backend/services/comms/video_service.py
        - backend/services/comms/video_intelligence_service.py
        - backend/services/comms/presence_service.py
        - backend/services/comms/notification_service.py
        - backend/services/comms/translation_service.py
        - backend/services/comms/contacts_service.py
        - backend/services/comms/dlp_service.py
        - backend/services/comms/announcement_service.py
        - backend/services/comms/confluence_service.py
        - backend/services/comms/conversation_service.py
        - backend/services/comms/proxy_masking_service.py
        - backend/services/comms/legal_hold_service.py
        - backend/services/comms/eDiscovery_export_service.py
        - backend/services/comms/meeting_cost_service.py
        - backend/services/comms/files_service.py
        - backend/services/comms/war_room_service.py
        - backend/models/comms/chat_model.py
        - backend/models/comms/channel_model.py
        - backend/models/comms/email_model.py
        - backend/models/comms/video_model.py
        - backend/models/comms/notification_model.py
        - backend/models/comms/announcement_model.py
        - backend/models/comms/conversation_model.py
        - backend/models/comms/confluence_model.py
        - backend/models/comms/proxy_model.py
        - backend/models/comms/communication_audit_model.py
        - backend/models/comms/compliance_model.py
        - backend/models/comms/contact_model.py
        - backend/events/websocket_manager.py
        - backend/events/video_signaling.py
        - backend/events/presence_redis.py
        - backend/events/websocket_manager.py
        - backend/jobs/comms_realtime_consumer.py
        - backend/jobs/comms_email_worker.py
        - backend/jobs/comms_email_dlq_worker.py
        - backend/jobs/comms_transcription_task.py
        - backend/events/communication_events.py
        - backend/providers/comms/email_provider.py
        - backend/providers/comms/sms_provider.py
        - backend/providers/comms/push_provider.py
        - backend/providers/comms/storage_provider.py
        - backend/jobs/comms_automation.py
        - backend/jobs/comms_transcription_task.py
        - backend/db/schemas.py
        - backend/alembic/versions/comms_initial.py
      frontend_web:
        - "frontend/web_app/src/app/comms/layout.tsx"
        - "frontend/web_app/src/app/comms/chat/page.tsx"
        - "frontend/web_app/src/app/comms/channels/page.tsx"
        - "frontend/web_app/src/app/comms/email/page.tsx"
        - "frontend/web_app/src/app/comms/video/page.tsx"
        - "frontend/web_app/src/app/comms/contacts/page.tsx"
        - "frontend/web_app/src/app/comms/files/page.tsx"
        - "frontend/web_app/src/app/comms/announcements/page.tsx"
        - "frontend/web_app/src/app/comms/confluence/page.tsx"
        - "frontend/web_app/src/app/comms/eDiscovery/page.tsx"
        - "frontend/web_app/src/app/comms/settings/page.tsx"
        - "frontend/web_app/src/components/comms/ChatRoom.tsx"
        - "frontend/web_app/src/components/comms/ChannelList.tsx"
        - "frontend/web_app/src/components/comms/MessageThread.tsx"
        - "frontend/web_app/src/components/comms/VoiceNotePlayer.tsx"
        - "frontend/web_app/src/components/comms/AttachmentLightbox.tsx"
        - "frontend/web_app/src/components/comms/ReactionBar.tsx"
        - "frontend/web_app/src/components/comms/TypingIndicator.tsx"
        - "frontend/web_app/src/components/comms/ReadReceipts.tsx"
        - "frontend/web_app/src/components/comms/EmailClient.tsx"
        - "frontend/web_app/src/components/comms/EmailCompose.tsx"
        - "frontend/web_app/src/components/comms/EmailFolders.tsx"
        - "frontend/web_app/src/components/comms/DlpWarningBanner.tsx"
        - "frontend/web_app/src/components/comms/VideoRoom.tsx"
        - "frontend/web_app/src/components/comms/VideoScheduler.tsx"
        - "frontend/web_app/src/components/comms/VideoTranscriptPanel.tsx"
        - "frontend/web_app/src/components/comms/ActionItemsPanel.tsx"
        - "frontend/web_app/src/components/comms/MeetingCostIndicator.tsx"
        - "frontend/web_app/src/components/comms/UnifiedInbox.tsx"
        - "frontend/web_app/src/components/comms/ConversationView.tsx"
        - "frontend/web_app/src/components/comms/ModalityFilter.tsx"
        - "frontend/web_app/src/components/comms/WarRoomThread.tsx"
        - "frontend/web_app/src/components/comms/ContactsDirectory.tsx"
        - "frontend/web_app/src/components/comms/AnnouncementBanner.tsx"
        - "frontend/web_app/src/components/comms/AnnouncementReadConfirm.tsx"
        - "frontend/web_app/src/components/comms/PresenceDots.tsx"
        - "frontend/web_app/src/components/comms/ProxyMaskBadge.tsx"
        - "frontend/web_app/src/components/comms/LegalHoldPanel.tsx"
        - "frontend/web_app/src/components/comms/EDIscoveryExport.tsx"
        - "frontend/web_app/src/components/comms/CommsHub.tsx"
        - "frontend/web_app/src/components/comms/TranslationToggle.tsx"
        - "frontend/web_app/src/lib/comms/websocket.ts"
        - "frontend/web_app/src/lib/comms/translation.ts"
        - "frontend/web_app/src/lib/comms/upload.ts"
        - "frontend/web_app/src/lib/comms/voiceRecorder.ts"
        - "frontend/web_app/src/lib/comms/dlpBanner.ts"
        - "frontend/web_app/src/lib/comms/UnifiedInboxBridge.tsx"
        - "frontend/web_app/src/lib/comms/CommShell.tsx"
        - "frontend/web_app/src/hooks/useUnifiedInbox.ts"
        - "frontend/web_app/src/hooks/useThreadMessages.ts"
        - "frontend/web_app/src/hooks/usePresence.ts"
        - "frontend/web_app/src/hooks/useTypingIndicator.ts"
        - "frontend/web_app/src/hooks/useChatSocket.ts"
        - "frontend/web_app/src/hooks/useVideoRooms.ts"
        - "frontend/web_app/src/hooks/useEmailFolders.ts"
        - "frontend/web_app/src/hooks/useAnnouncements.ts"
        - "frontend/web_app/src/hooks/useContacts.ts"
        - "frontend/web_app/src/hooks/useConversations.ts"
        - "frontend/web_app/src/hooks/useProxyMask.ts"
        - "frontend/web_app/src/hooks/useWarRoom.ts"
      frontend_mobile:
        - "frontend/mobile_app/app/comms/index.tsx"
        - "frontend/mobile_app/app/comms/chat.tsx"
        - "frontend/mobile_app/app/comms/channels.tsx"
        - "frontend/mobile_app/app/comms/email.tsx"
        - "frontend/mobile_app/app/comms/video.tsx"
        - "frontend/mobile_app/app/comms/contacts.tsx"
        - "frontend/mobile_app/app/comms/files.tsx"
        - "frontend/mobile_app/app/comms/announcements.tsx"
        - "frontend/mobile_app/app/comms/confluence.tsx"
        - "frontend/mobile_app/app/comms/war-room.tsx"
      tests:
        - "backend/tests/comms/_test_chat.py"
        - "backend/tests/comms/_test_channels.py"
        - "backend/tests/comms/_test_email_router_dlp.py"
        - "backend/tests/comms/_test_email_smart_router.py"
        - "backend/tests/comms/_test_video_transcription.py"
        - "backend/tests/comms/_test_video_action_items.py"
        - "backend/tests/comms/_test_notifications.py"
        - "backend/tests/comms/_test_voice_note.py"
        - "backend/tests/comms/_test_unified_inbox.py"
        - "backend/tests/comms/_test_announcements.py"
        - "backend/tests/comms/_test_contacts.py"
        - "backend/tests/comms/_test_confluence.py"
        - "backend/tests/comms/_test_proxy_masking.py"
        - "backend/tests/comms/_test_legal_hold.py"
        - "backend/tests/comms/_test_eDiscovery.py"
        - "backend/tests/comms/_test_files_media.py"
        - "backend/tests/comms/_test_websocket_presence.py"
        - "backend/tests/comms/_test_meeting_cost.py"
        - "backend/tests/comms/_test_translation.py"
        - "backend/tests/comms/_test_war_room.py"
        - "frontend/web_app/src/__tests__/components/comms/_test_chat.test.tsx"
        - "frontend/web_app/src/__tests__/components/comms/_test_email.test.tsx"
        - "frontend/web_app/src/__tests__/components/comms/_test_video.test.tsx"
        - "frontend/web_app/src/__tests__/components/comms/_test_announcements.test.tsx"
        - "frontend/web_app/src/__tests__/components/comms/_test_contacts.test.tsx"
        - "frontend/web_app/src/__tests__/components/comms/_test_files.test.tsx"
        - "frontend/web_app/src/__tests__/pages/comms/_test_communication_workspace.test.tsx"
        - "frontend/web_app/src/__tests__/pages/comms/_test_confluence.test.tsx"
        - "frontend/web_app/src/__tests__/components/comms/_test_unified_inbox.test.tsx"
      api_routes:
        - "GET /channels"
        - "POST /channels"
        - "GET /channels/{channel_id}"
        - "PATCH /channels/{channel_id}"
        - "DELETE /channels/{channel_id}"
        - "GET /channels/{channel_id}/messages"
        - "POST /channels/{channel_id}/messages"
        - "PATCH /messages/{message_id}"
        - "DELETE /messages/{message_id}"
        - "POST /messages/{message_id}/react"
        - "POST /messages/{message_id}/forward"
        - "GET /direct-chats"
        - "POST /direct-chats"
        - "POST /chat/voice-note"
        - "GET /chat/{room_id}/read-receipts"
        - "POST /chat/typing"
        - "GET /chat/search"
        - "GET /video-rooms"
        - "POST /video-rooms"
        - "GET /video-rooms/{room_id}"
        - "PATCH /video-rooms/{room_id}"
        - "POST /video-rooms/{room_id}/signal"
        - "POST /video-rooms/{room_id}/join"
        - "GET /video-rooms/{room_id}/transcript"
        - "POST /video-rooms/{room_id}/action-items"
        - "POST /video-rooms/{room_id}/recording/lock"
        - "GET /email"
        - "GET /email/folders"
        - "POST /email/folders"
        - "GET /email/{id}"
        - "POST /email"
        - "POST /email/bulk"
        - "POST /email/from-alias"
        - "GET /email/{id}/read"
        - "POST /email/{id}/labels"
        - "GET /email/search"
        - "POST /email/rules"
        - "GET /email/threads/{thread_id}"
        - "GET /announcements"
        - "POST /announcements"
        - "POST /announcements/{id}/ack"
        - "GET /announcements/{id}/read-status"
        - "GET /contacts"
        - "GET /contacts/{id}"
        - "GET /directory/search"
        - "GET /files"
        - "POST /files"
        - "GET /files/{id}"
        - "POST /comms/translate"
        - "POST /comms/translate/message/{message_id}"
        - "GET /conversations/inbox"
        - "GET /conversations"
        - "GET /conversations/{conversation_id}"
        - "GET /conversations/{conversation_id}/messages"
        - "POST /conversations/{conversation_id}/messages"
        - "PATCH /conversations/{conversation_id}/read"
        - "GET /confluence/channels"
        - "POST /confluence/channels"
        - "POST /confluence/channels/{channel_id}/archive"
        - "GET /confluence/war-room/{entity_type}/{entity_id}"
        - "POST /confluence/threads"
        - "GET /comms/audit-trail"
        - "GET /comms/eDiscovery/export"
        - "POST /comms/legal-hold"
        - "GET /comms/legal-hold"
        - "POST /comms/dlp/quarantine/{id}/review"
        - "GET /comms/proxy/contacts"
        - "POST /comms/proxy/unmask/{session_id}"
      models:
        - "DirectChatRoom"
        - "InternalChannel"
        - "ChannelMember"
        - "ChannelPin"
        - "ChatMessage"
        - "ChatAttachment"
        - "ChatReadReceipt"
        - "ChatReaction"
        - "ChatThread"
        - "VideoRoom"
        - "VideoParticipant"
        - "VideoRecording"
        - "VideoTranscript"
        - "VideoActionItem"
        - "InternalEmail"
        - "EmailThread"
        - "EmailFolder"
        - "EmailLabel"
        - "EmailRule"
        - "EmailEvent"
        - "NotificationQueue"
        - "EmailMessage"
        - "PushLog"
        - "Announcement"
        - "AnnouncementReadReceipt"
        - "Conversation"
        - "ConversationMessage"
        - "ConversationParticipant"
        - "ProxyMessage"
        - "ProxyChannel"
        - "ProxySession"
        - "CommunicationAuditTrail"
        - "LegalHold"
        - "DlpQuarantine"
        - "MediaAsset"
        - "EmployeeActivityLog"
    diagram: |
      flowchart TB
        subgraph CH["CHAT · 1:1 / groups / channels"]
          D[direct_chat_rooms] --> WS["WebSocketManager: typing / read-receipts / presence (Redis)"]
          IC[internal_channels] --> WS
          MSG[chat_messages] --> ATT[chat_attachments -> media_assets]
          MSG --> RX[chat_reactions]
          MSG --> TH[chat_threads]
        end
        subgraph EM["EMAIL · smart router"]
          IE[internal_emails] --> RT["email_smart_router: directory-first in-DB"]
          RT -->|internal| DB[(comms schema)]
          RT -->|external| SMTP["SMTP + DLP + allow-list + BCC"]
          SMTP --> Q[dlp_quarantine / event_dead_letter]
        end
        subgraph VD["VIDEO"]
          VR[video_rooms] --> SIG[WebRTC signaling]
          VR --> WT["Whisper transcript + AR/EN"]
          WT --> AIX["extract_action_items -> STAGED -> ASSIGNED"]
          VR --> WORM["WORM recordings (retention-locked)"]
        end
        subgraph CON["CONTACTS · FILES"]
          CT[contacts / directory] --> INT[internal-first resolution]
          FL[files] --> MA[media_assets + R2/CDN]
        end
        CH --> CONV[("conversations / unified inbox")]
        EM --> CONV
        VD --> CONV
        INT --> CONV
        CONV --> TRIAGE["ranked triage: you > mentions > DM > group > email > channel"]
        TRIAGE --> PROXY["proxy_* masking external contacts"]
        TRIAGE --> WAR["war-room / entity-attached threads"]
        TRIAGE --> MOD["modality filter chat / email / video"]
        TRIAGE --> ACK["announcements read-confirm"]
        CONV --> AUD["communication_audit_trails + employee_activity_logs (eDiscovery)"]
        CH --> EV[("outbox_events")]
        EM --> EV
        VD --> EV
        EV --> TR["treasury / analytics"]

    ui_diagram: |
      flowchart TB
        subgraph WIN["WINDOW - Communication Workspace"]
          HD["Top bar: country switcher - presence dots - search - new message"]
          NV["Left rail: Chat - Channels - Email - Video - Contacts - Files"]
          IN["Inbox: ranked triage you>mentions>DM>group>email>channel (UnifiedInbox)"]
          MA["Center: ConversationView - MessageThread - EmailClient - VideoRoom"]
          SB["Right: details - members - ModalityFilter - ReactionBar"]
          MD["Modals: VideoScheduler - ActionItemsPanel - LegalHoldPanel - ProxyMaskBadge"]
        end
        WIN --> RT["Realtime: WebSocketManager typing/presence (Redis)"]
  # ===========================================================================
  - id: SYS_002   # Product & Catalog System
    name: Product & Catalog System
    weight: 9
    update_version: "v1_14-08-2026"
    scope: Admin · Employee - Customer - Supplier
    description: |
      ## Capabilities
      - **Product & Catalog System** — the `commerce` bounded context (products, `product_variants`, `categories`, brands, attributes/facets, pricing, inventory flags, media, tags, taxonomy) plus the storefront surfaces (PLP, PDP, catalog admin, variant editor, media manager). Inherits constitutional rules: **RLS `country_code` on every catalog row, Alembic-only migrations, event-driven writes (outbox), media bytes in R2, append-only audit, config-as-data, no silent fallbacks.** Strategy: **complete + wire the existing skeleton; do not rebuild.**
      - **Categories & taxonomy:** `commerce.categories` use **materialized path** (`/1/15/42/`) + `lft`/`rgt` (nested-set) for instant subtree queries; `commerce.brands`, `commerce.tags`, `commerce.product_attributes` (facet definitions). Tree admin with drag-reorder; moving a node recomputes `lft/rgt` in one transaction.
      - **Products & variants:** `commerce.products` (base price, `compare_at_price`, sale price, `currency_code` per country, `is_active`, `country_code`, `stock_status` on/off, `is_featured`, SEO slug). `commerce.product_variants` use **JSONB `attributes` + GIN index + `variant_key` hash** — no flat color/size columns. Limits enforced: **max 20 images per product, max 50 variants per product**. SKU/GTIN fields; variant-level price/stock.
      - **Media & assets:** `media.media_assets` metadata only (`url`, `mime`, `hash`, `w/h`, `ai_status`); bytes in Cloudflare R2; pipeline Original → Optimized → Thumbnail → WebP → CDN; lifecycle Hot → Warm → Cold → Destroyed after legal retention. Product gallery links to `media_assets`.
      - **Attributes / facets / search indexing:** `commerce.product_attributes` + `commerce.product_attribute_values` drive faceted filters; every product write emits an outbox event to refresh FTS (`tsvector`) + `pgvector` embedding for hybrid search (handled by SYS_006). AI staging flow: `ai.ai_staging_products` → explicit human/auto commit → `commerce.products` (AI NEVER writes business tables directly).
      - **Pricing & inventory:** country-scoped price + compare-at; stock `on_hand`/`reserved`/`available`; low-stock flag; backorder toggle; multi-currency from `country_configs`. Price/inventory changes emit events to finance/order domains.
      - **Storefront surfaces:** PLP (filter/sort/search bar = SYS_006), PDP (gallery, variant selector, price, add-to-cart, reviews hook), catalog admin (CRUD + bulk import/export), variant editor (matrix builder), media manager (upload/optimize/reorder). Customer sees only `country_code`-matched, `is_active` products.

      ## Non-negotiables
      - **Materialized path + nested-set** on categories; subtree queries must be O(1)-ish via `lft/rgt`.
      - **Variants = JSONB attributes + GIN**, never flat columns; `variant_key` is a deterministic hash.
      - **Media bytes in R2**, metadata only in `media_assets`; max 20 images / 50 variants per product.
      - **RLS `country_code`** on products/categories; cross-country reads return 0 rows (fail-closed).
      - **AI staged→committed**: no direct AI writes to `commerce.products`.
      - **Config-as-data** for commissions/fees/category rules.
      - **Outbox events** on every product/price/inventory change (never silent).

      ## Data model (`commerce` schema unless noted)
      - `commerce.categories` (materialized path + lft/rgt)
      - `commerce.brands`
      - `commerce.tags`
      - `commerce.products`
      - `commerce.product_variants` (JSONB attributes + GIN + variant_key)
      - `commerce.product_images`
      - `commerce.product_attributes`
      - `commerce.product_attribute_values`
      - `commerce.product_tags`
      - `commerce.product_pricing` (country-scoped)
      - `commerce.inventory` (on_hand/reserved/available)
      - `commerce.product_reviews` (stub/hook)
      - `media.media_assets`
      - `ai.ai_staging_products`
      - `analytics.mv_category_tree`

      ## API
      - `GET /products` · `POST /products` · `GET /products/{id}` · `PATCH /products/{id}` · `DELETE /products/{id}`
      - `GET /products/{id}/variants` · `POST /products/{id}/variants` · `PATCH /products/{id}/variants/{variant_id}` · `DELETE /products/{id}/variants/{variant_id}`
      - `POST /products/bulk-import` · `GET /products/bulk-export`
      - `GET /categories` · `POST /categories` · `GET /categories/{id}` · `PATCH /categories/{id}` · `DELETE /categories/{id}` · `POST /categories/{id}/reorder`
      - `GET /brands` · `POST /brands`
      - `GET /tags` · `POST /tags`
      - `GET /products/{id}/images` · `POST /products/{id}/images` · `DELETE /products/{id}/images/{image_id}`
      - `GET /attributes` · `POST /attributes` · `GET /attributes/{id}/values`
      - `PATCH /products/{id}/pricing` · `GET /products/{id}/inventory` · `PATCH /products/{id}/inventory`
      - `GET /products/search` (delegates to SYS_006)

      ## State machine
      - `DRAFT` → `ACTIVE` / `INACTIVE` (product)
      - `IN_STOCK` → `LOW_STOCK` → `OUT_OF_STOCK` → `BACKORDER` (inventory)
      - `STAGED` → `COMMITTED` / `REJECTED` (AI staging)
      - `UPLOADED` → `OPTIMIZED` → `CDN_READY` (media)

      ## Automations
      - **Auto-categorization:** on product create, suggest category/attributes from description via AI; human confirm.
      - **Price-change event:** on price update, emit event → order/finance repricing + analytics.
      - **Low-stock alert:** inventory threshold → notify supplier/admin + restock suggestion.
      - **Media optimization pipeline:** on upload → auto Optimized/Thumbnail/WebP → CDN.

      ## UI/UX layout
      - **PLP:** faceted filter sidebar (Category/Price/Rating/Supplier/Brand/Attributes), sort bar, grid, lazy-load, RTL/i18n.
      - **PDP:** gallery lightbox, variant matrix selector, price + compare-at, stock badge, add-to-cart, sticky buy box, related products.
      - **Catalog admin:** table with bulk actions, inline edit, drawer for full edit, import/export.
      - **Variant editor:** attribute matrix builder (color×size), per-variant price/stock/SKU.
      - **Media manager:** upload → progress → reorder → set hero; shows R2/CDN URLs.
      - **UX principles:** skeleton loaders, explicit empty/error, ARIA + keyboard, density toggle, country switcher re-sets RLS.

      ## Step-by-step
      - **Step 1 — Categories & taxonomy.** `commerce.categories` materialized path + nested-set; brands/tags; tree admin reorder. *Done when:* subtree query returns correct node set; move recomputes lft/rgt atomically.
      - **Step 2 — Products & variants.** `commerce.products` + `product_variants` (JSONB + GIN + variant_key); enforce 20-image/50-variant limits. *Done when:* variant matrix builds; filter by attribute works.
      - **Step 3 — Media pipeline.** `media.media_assets` + R2 upload → Optimized/Thumbnail/WebP/CDN; gallery link. *Done when:* image renders from CDN; reorder persists.
      - **Step 4 — Pricing & inventory.** Country-scoped pricing, stock on_hand/reserved/available, low-stock flag, outbox events. *Done when:* price change emits event; stock badge correct.
      - **Step 5 — Attributes & search indexing.** `product_attributes`/`values` facets; outbox → FTS + pgvector refresh. *Done when:* faceted filter + hybrid search return correct results.
      - **Step 6 — Storefront & admin surfaces.** PLP/PDP/catalog admin/variant editor/media manager; RLS country scoping. *Done when:* customer sees only country-matched active products; admin CRUD + bulk import/export pass.
    sections:
      §I: "Admin: full CRUD on products/categories/variants, media manager, bulk import/export, AI staging review."
      §II: "Customer: read-only PLP/PDP scoped to country + active; add-to-cart; reviews hook."
      §III: "Supplier: can manage own products (scoped) via SYS_010 upload flow."
      §IV: "Logistics: reads product weight/dimensions for shipping calc."
      §V: "Search/Discovery: emits index events consumed by SYS_006 (hybrid search)."
    expected:
      backend_files:
        - backend/routers/commerce_product_router.py
        - backend/routers/commerce_category_router.py
        - backend/routers/commerce_brand_router.py
        - backend/routers/commerce_tag_router.py
        - backend/routers/commerce_variant_router.py
        - backend/routers/commerce_attribute_router.py
        - backend/routers/commerce_inventory_router.py
        - backend/routers/commerce_media_router.py
        - backend/controllers/commerce/product_controller.py
        - backend/controllers/commerce/category_controller.py
        - backend/controllers/commerce/variant_controller.py
        - backend/controllers/commerce/inventory_controller.py
        - backend/controllers/commerce/media_controller.py
        - backend/services/commerce/product_service.py
        - backend/services/commerce/category_service.py
        - backend/services/commerce/variant_service.py
        - backend/services/commerce/pricing_service.py
        - backend/services/commerce/inventory_service.py
        - backend/services/commerce/attribute_service.py
        - backend/services/commerce/media_service.py
        - backend/services/commerce/catalog_search_index_service.py
        - backend/services/commerce/bulk_import_service.py
        - backend/models/catalog/product_model.py
        - backend/models/catalog/category_model.py
        - backend/models/catalog/brand_model.py
        - backend/models/catalog/tag_model.py
        - backend/models/catalog/variant_model.py
        - backend/models/catalog/attribute_model.py
        - backend/models/catalog/inventory_model.py
        - backend/models/catalog/product_review_model.py
        - backend/models/media/media_asset_model.py
        - backend/events/catalog_cache_invalidator.py
        - backend/events/catalog_events.py
        - backend/providers/media/r2_storage_provider.py
        - backend/jobs/media_optimization_task.py
        - backend/jobs/catalog_index_task.py
        - backend/db/schemas.py
        - backend/db/schemas.py
        - backend/db/schemas.py
        - backend/db/schemas.py
        - backend/alembic/versions/commerce_catalog_initial.py
      frontend_web:
        - "frontend/web_app/src/app/products/page.tsx"
        - "frontend/web_app/src/app/products/[id]/page.tsx"
        - "frontend/web_app/src/app/admin/catalog/products/page.tsx"
        - "frontend/web_app/src/app/admin/catalog/categories/page.tsx"
        - "frontend/web_app/src/app/admin/catalog/variants/page.tsx"
        - "frontend/web_app/src/app/admin/catalog/media/page.tsx"
        - "frontend/web_app/src/app/admin/catalog/attributes/page.tsx"
        - "frontend/web_app/src/components/ui/ProductCard.tsx"
        - "frontend/web_app/src/components/ui/ProductGrid.tsx"
        - "frontend/web_app/src/components/ui/ProductGallery.tsx"
        - "frontend/web_app/src/components/ui/VariantMatrix.tsx"
        - "frontend/web_app/src/components/ui/PriceBlock.tsx"
        - "frontend/web_app/src/components/ui/AddToCart.tsx"
        - "frontend/web_app/src/components/ui/CategoryTree.tsx"
        - "frontend/web_app/src/components/ui/ProductTable.tsx"
        - "frontend/web_app/src/components/ui/VariantEditor.tsx"
        - "frontend/web_app/src/components/ui/MediaManager.tsx"
        - "frontend/web_app/src/components/ui/BulkImportExport.tsx"
        - "frontend/web_app/src/lib/commerce/products.ts"
        - "frontend/web_app/src/lib/commerce/variants.ts"
        - "frontend/web_app/src/lib/commerce/media.ts"
        - "frontend/web_app/src/hooks/useProducts.ts"
        - "frontend/web_app/src/hooks/useCategories.ts"
        - "frontend/web_app/src/hooks/useVariants.ts"
        - "frontend/web_app/src/hooks/useInventory.ts"
      frontend_mobile:
        - "frontend/mobile_app/app/products/index.tsx"
        - "frontend/mobile_app/app/products/[id].tsx"
        - "frontend/mobile_app/app/products/products.tsx"
        - "frontend/mobile_app/app/products/categories.tsx"
        - "frontend/mobile_app/app/products/media.tsx"
      tests:
        - "backend/tests/commerce/_test_products.py"
        - "backend/tests/commerce/_test_categories.py"
        - "backend/tests/commerce/_test_variants.py"
        - "backend/tests/commerce/_test_inventory.py"
        - "backend/tests/commerce/_test_media_pipeline.py"
        - "backend/tests/commerce/_test_bulk_import.py"
        - "backend/tests/commerce/_test_rls_country.py"
        - "frontend/web_app/src/__tests__/components/product/_test_product_card.test.tsx"
        - "frontend/web_app/src/__tests__/components/catalog/_test_category_tree.test.tsx"
        - "frontend/web_app/src/__tests__/pages/products/_test_product_detail.test.tsx"
        - "frontend/web_app/src/__tests__/pages/admin/catalog/_test_catalog_admin.test.tsx"
      api_routes:
        - "GET /products"
        - "POST /products"
        - "GET /products/{id}"
        - "PATCH /products/{id}"
        - "DELETE /products/{id}"
        - "GET /products/{id}/variants"
        - "POST /products/{id}/variants"
        - "PATCH /products/{id}/variants/{variant_id}"
        - "DELETE /products/{id}/variants/{variant_id}"
        - "POST /products/bulk-import"
        - "GET /products/bulk-export"
        - "GET /categories"
        - "POST /categories"
        - "GET /categories/{id}"
        - "PATCH /categories/{id}"
        - "DELETE /categories/{id}"
        - "POST /categories/{id}/reorder"
        - "GET /brands"
        - "POST /brands"
        - "GET /tags"
        - "POST /tags"
        - "GET /products/{id}/images"
        - "POST /products/{id}/images"
        - "DELETE /products/{id}/images/{image_id}"
        - "GET /attributes"
        - "POST /attributes"
        - "GET /attributes/{id}/values"
        - "PATCH /products/{id}/pricing"
        - "GET /products/{id}/inventory"
        - "PATCH /products/{id}/inventory"
        - "GET /products/search"
      models:
        - "Category"
        - "Brand"
        - "Tag"
        - "Product"
        - "ProductVariant"
        - "ProductImage"
        - "ProductAttribute"
        - "ProductAttributeValue"
        - "ProductTag"
        - "ProductPricing"
        - "Inventory"
        - "ProductReview"
        - "MediaAsset"
        - "AiStagingProduct"
    diagram: |
      flowchart TB
        P[commerce.products] --> V["product_variants (JSONB attributes + GIN)"]
        P --> CAT[commerce.categories: path + lft/rgt]
        P --> BR[commerce.brands]
        P --> TAG[commerce.tags]
        P --> IMG[product_images -> media_assets + R2/CDN]
        P --> PR[product_pricing: country-scoped]
        P --> INV[inventory: on_hand/reserved/available]
        P --> ATTR[product_attributes -> facets]
        P --> OUT[("outbox_events")]
        OUT --> SRCH["SYS_006: FTS + pgvector hybrid"]
        OUT --> FIN[finance / order repricing]
        OUT --> AN[analytics materialized views]

    ui_diagram: |
      flowchart TB
        subgraph WIN["WINDOW - Product & Catalog"]
          HD["Top bar: catalog admin nav - country - bulk import/export"]
          NV["Left: CategoryTree (nested-set) - Brands - Tags - Attributes"]
          MA["Center: PLP grid (ProductGrid/Card) - PDP gallery+variant - VariantEditor matrix"]
          SB["Right: MediaManager (upload/optimize) - FacetPanel"]
          TB["Toolbar: FilterSearchBar - SortBar - ImageSearchButton - VoiceSearchButton"]
        end
        WIN --> SR["Search SYS_006: Autocomplete - FacetPanel - results"]
  # ===========================================================================
  - id: SYS_003   # Cash Management / Finance / Treasury System
    name: Cash Management / Finance / Treasury System
    weight: 10
    update_version: "v1_14-08-2026"
    scope: Admin · Employee - Supplier - Logistic Partner
    description: |
      ## Capabilities
      - **Finance · Treasury · Automation** — the `finance` + `treasury` + `audit` bounded contexts implementing strict double-entry accounting, cash/treasury management, payouts (to suppliers & logistics partners), COD / pay-by-card, bank reconciliation, and the automation tower. Inherits constitutional rules: **RLS `country_code`, Alembic-only migrations, event-driven writes (outbox), append-only/WORM financial ledgers, Maker-Checker on money & permissions, config-as-data, no silent fallbacks.** Strategy: **complete + wire the existing skeleton; do not rebuild.**

      - **Chart of Accounts & double-entry:** `finance.accounts` (CoA, hierarchical). `finance.journal_entries` + `finance.journal_entry_lines` enforce **strict double-entry** (`Σdebit == Σcredit`); immutability via PostgreSQL trigger raising on `UPDATE`/`DELETE` of posted lines (WORM). Period-close locking prevents edits after close.

      - **Ledger chain:** CoA → Journal → Ledger → Balance → Trial Balance → P&L. `finance.ledger`, `finance.trial_balance`, `finance.profit_loss` derived/materialized.

      - **Treasury engine:** `treasury.cash_positions` (per currency/country), `treasury.payout_batches`, `treasury.bank_reconciliations`, `treasury.payout_runs`. Payouts cascade: batch → Treasury payout → journal → bank. Supports supplier payouts and logistics-partner payouts.

      - **Payment engine:** `payment_transactions` (Cash on Delivery, Pay by Card, wallet), `payment_methods`, reconciliation with provider webhooks; COD collected → banked; card captured → settled. Refunds/reversals post reversing journal entries.

      - **4-tier data architecture:** (1) operational ledgers → (2) country marts (`country_code`) → (3) consolidated → (4) analytics materialized views (`analytics.mv_*`). Reconciliation between tiers mandatory.

      - **Automation tower:** reconciliation jobs, fraud/risk scoring, bank-recon retry with DLQ, anomaly gates (salary Δ > threshold, missing IBAN, cert expired), payout batch auto-draft → Maker-Checker → dispatch → recon → payslips (payroll belongs to SYS_005 but journals here). Every auto-action logged `actor=system:<job>`.

      - **RBAC / compliance:** `require_permission` on every money endpoint; Maker ≠ Checker enforced; sensitive grants (finance.*) via Maker-Checker; audit via `audit.audit_logs` (WORM); tax/VAT/EOSB/statutory rules from `country_configs`.

      ## Non-negotiables
      - **Strict double-entry**: `Σdebit == Σcredit` before commit; immutability trigger on journal lines.
      - **WORM financial ledgers / audit logs**; never UPDATE/DELETE posted entries.
      - **Maker ≠ Checker** on every payout/journal approval.
      - **RLS `country_code`** on all finance rows; cross-country reads return 0 rows.
      - **Bank reconciliation** must balance to 0 variance or route to exception.
      - **Config-as-data** for fees/commissions/tax; **no silent fallbacks** (fail loud + DLQ).

      ## Data model (`finance`/`treasury`/`audit` unless noted)
      - `finance.accounts` (CoA)
      - `finance.journal_entries`
      - `finance.journal_entry_lines`
      - `finance.ledger`
      - `finance.trial_balance`
      - `finance.profit_loss`
      - `finance.period_closes`
      - `treasury.cash_positions`
      - `treasury.payout_batches`
      - `treasury.payout_runs`
      - `treasury.bank_reconciliations`
      - `treasury.bank_accounts`
      - `payment_transactions`
      - `payment_methods`
      - `finance.refunds`
      - `finance.fx_rates`
      - `security.fraud_scores`
      - `audit.audit_logs`

      ## API
      - `GET /finance/accounts` · `POST /finance/accounts` · `GET /finance/accounts/{id}`
      - `POST /finance/journal` (double-entry post) · `GET /finance/journal` · `GET /finance/journal/{id}`
      - `POST /finance/ledger/recompute` · `GET /finance/trial-balance` · `GET /finance/profit-loss`
      - `POST /finance/period-close` · `GET /finance/periods`
      - `GET /treasury/cash-positions` · `POST /treasury/payout-batches` · `GET /treasury/payout-batches/{id}` · `POST /treasury/payout-batches/{id}/approve` (Checker) · `POST /treasury/payout-batches/{id}/dispatch`
      - `POST /treasury/bank-reconciliations` · `GET /treasury/bank-reconciliations/{id}` · `POST /treasury/bank-reconciliations/{id}/match`
      - `POST /payments/charge` · `POST /payments/refund` · `GET /payments/{id}` · `POST /payments/webhook`
      - `GET /finance/reports/balance-sheet` · `GET /finance/reports/cash-flow`
      - `GET /finance/automations` · `POST /finance/automations/{id}/run`

      ## State machine
      - `DRAFT` → `POSTED` → `SETTLED` (journal)
      - `OPEN` → `CLOSED` (period)
      - `DRAFT` → `APPROVED` (Maker) → `DISPATCHED` → `RECONCILED` → `SETTLED` (payout batch)
      - `PENDING` → `CAPTURED` → `SETTLED` / `REFUNDED` / `FAILED` (payment)
      - `UNRECONCILED` → `RECONCILED` / `EXCEPTION` (bank recon)

      ## Automations
      - **Auto-reconciliation:** nightly match bank statements → ledger; variance → exception queue.
      - **Anomaly gate:** salary Δ > threshold / missing IBAN / expired cert → hold queue.
      - **Fraud/risk scoring:** on payment, score via `security.fraud_scores`; high → step-up/block.
      - **Bank-recon retry + DLQ:** failed recon retries with dead-letter.
      - **Payout batch auto-draft → Maker-Checker → dispatch → recon** (wired to SYS_005 payroll).

      ## UI/UX layout
      - **Finance Command Center** sidebar (`/admin/finance?section=…`, lazy): Chart of Accounts, Journal, Ledger, Trial Balance, P&L, Period Close, Cash Positions, Payout Batches (pipeline chips: draft→approved→dispatched→settled, maker≠checker locks, exception holds), Bank Reconciliation (match grid), Payments, Reports, Automation Tower (per-job toggle/cron/last-run/exception counters/DLQ), Audit Viewer (WORM).
      - **Key screens:** Journal entry form (debit/credit balanced, immutable after post); Payout Control Room (batch list + per-employee drilldown provenance); Reconciliation match grid; Reports (balance sheet, cash flow); RBAC permission-matrix for `finance.*`.
      - **UX principles:** skeleton loaders, explicit empty/error, tabular numerals, ARIA + keyboard, density toggle, country switcher re-sets RLS, immutable audit viewer.

      ## Step-by-step
      - **Step 1 — Chart of Accounts & journal.** `finance.accounts` + `journal_entries`/`journal_entry_lines` with strict double-entry + immutability trigger + period-close lock. *Done when:* unbalanced post rejected; posted line UPDATE/DELETE raises.
      - **Step 2 — Ledger & reporting.** Ledger chain → trial balance → P&L; recompute job. *Done when:* trial balance balances; P&L matches.
      - **Step 3 — Treasury & payouts.** `cash_positions`, `payout_batches`/`runs`; supplier + logistics payouts cascade to journal→bank. *Done when:* payout posts balanced journal + dispatches.
      - **Step 4 — Payment engine.** COD/card/wallet `payment_transactions` + webhooks + refunds. *Done when:* charge settles; refund reverses via journal.
      - **Step 5 — Bank reconciliation.** Statement import → match grid → variance exception. *Done when:* recon balances to 0 or routes exceptions; DLQ surfaced.
      - **Step 6 — Automation & compliance.** Recon/risk/retry automations + Maker-Checker + WORM audit + RBAC `finance.*`. *Done when:* each automation shows run health; paused = explicit badge; audit export passes.
    sections:
      §I: "Admin/Finance: full ledger, payouts, reconciliation, reports, automation tower, audit viewer."
      §II: "Customer: payment methods, COD/card checkout, refunds (read own)."
      §III: "Supplier: payout status, bank details, statements."
      §IV: "Logistics: partner payout status, statements."
      §V: "Cross-domain: journals posted from order/payroll events via outbox; analytics marts."
    expected:
      backend_files:
        - backend/routers/finance_account_router.py
        - backend/routers/finance_journal_router.py
        - backend/routers/finance_ledger_router.py
        - backend/routers/finance_period_router.py
        - backend/routers/treasury_cash_position_router.py
        - backend/routers/treasury_payout_router.py
        - backend/routers/treasury_reconciliation_router.py
        - backend/routers/finance_payment_router.py
        - backend/routers/finance_report_router.py
        - backend/routers/finance_automation_router.py
        - backend/controllers/finance/journal_controller.py
        - backend/controllers/finance/ledger_controller.py
        - backend/controllers/treasury/payout_controller.py
        - backend/controllers/treasury/reconciliation_controller.py
        - backend/controllers/finance/payment_controller.py
        - backend/services/finance/ledger_service.py
        - backend/services/finance/journal_service.py
        - backend/services/finance/account_service.py
        - backend/services/finance/report_service.py
        - backend/services/finance/period_close_service.py
        - backend/services/treasury/cash_position_service.py
        - backend/services/treasury/payout_service.py
        - backend/services/treasury/reconciliation_service.py
        - backend/services/finance/payment_service.py
        - backend/services/finance/refund_service.py
        - backend/services/finance/fraud_service.py
        - backend/services/finance/automation_service.py
        - backend/models/finance/account_model.py
        - backend/models/finance/journal_model.py
        - backend/models/finance/ledger_model.py
        - backend/models/finance/report_model.py
        - backend/models/finance/payment_model.py
        - backend/models/finance/cash_position_model.py
        - backend/models/finance/payout_model.py
        - backend/models/finance/reconciliation_model.py
        - backend/models/core/audit_log_model.py
        - backend/events/finance_cache_invalidator.py
        - backend/events/finance_events.py
        - backend/jobs/finance_reconciliation_worker.py
        - backend/jobs/finance_payout_worker.py
        - backend/jobs/finance_automation_worker.py
        - backend/providers/finance/bank_provider.py
        - backend/providers/finance/payment_gateway_provider.py
        - backend/jobs/finance_ledger_task.py
        - backend/db/schemas.py
        - backend/db/schemas.py
        - backend/db/schemas.py
        - backend/alembic/versions/finance_treasury_initial.py
      frontend_web:
        - "frontend/web_app/src/app/admin/finance/layout.tsx"
        - "frontend/web_app/src/app/admin/finance/accounts/page.tsx"
        - "frontend/web_app/src/app/admin/finance/journal/page.tsx"
        - "frontend/web_app/src/app/admin/finance/ledger/page.tsx"
        - "frontend/web_app/src/app/admin/finance/trial-balance/page.tsx"
        - "frontend/web_app/src/app/admin/finance/profit-loss/page.tsx"
        - "frontend/web_app/src/app/admin/finance/period-close/page.tsx"
        - "frontend/web_app/src/app/admin/finance/cash-positions/page.tsx"
        - "frontend/web_app/src/app/admin/finance/payouts/page.tsx"
        - "frontend/web_app/src/app/admin/finance/reconciliation/page.tsx"
        - "frontend/web_app/src/app/admin/finance/payments/page.tsx"
        - "frontend/web_app/src/app/admin/finance/reports/page.tsx"
        - "frontend/web_app/src/app/admin/finance/automation/page.tsx"
        - "frontend/web_app/src/app/admin/finance/audit/page.tsx"
        - "frontend/web_app/src/components/admin/JournalEntryForm.tsx"
        - "frontend/web_app/src/components/admin/PayoutControlRoom.tsx"
        - "frontend/web_app/src/components/admin/ReconciliationGrid.tsx"
        - "frontend/web_app/src/components/admin/BalanceSheet.tsx"
        - "frontend/web_app/src/components/admin/CashFlowReport.tsx"
        - "frontend/web_app/src/components/admin/AutomationTower.tsx"
        - "frontend/web_app/src/components/admin/AuditViewer.tsx"
        - "frontend/web_app/src/components/admin/PermissionMatrix.tsx"
        - "frontend/web_app/src/lib/finance/ledger.ts"
        - "frontend/web_app/src/lib/finance/payouts.ts"
        - "frontend/web_app/src/hooks/useJournal.ts"
        - "frontend/web_app/src/hooks/usePayouts.ts"
        - "frontend/web_app/src/hooks/useReconciliation.ts"
      frontend_mobile:
        - "frontend/mobile_app/app/finance/index.tsx"
        - "frontend/mobile_app/app/finance/payouts.tsx"
        - "frontend/mobile_app/app/finance/reconciliation.tsx"
        - "frontend/mobile_app/app/finance/reports.tsx"
      tests:
        - "backend/tests/finance/_test_double_entry.py"
        - "backend/tests/finance/_test_immutability_trigger.py"
        - "backend/tests/finance/_test_ledger_chain.py"
        - "backend/tests/finance/_test_payout_maker_checker.py"
        - "backend/tests/finance/_test_reconciliation.py"
        - "backend/tests/finance/_test_payments_refunds.py"
        - "backend/tests/finance/_test_period_close.py"
        - "backend/tests/finance/_test_rls_country.py"
        - "backend/tests/finance/_test_automation.py"
        - "frontend/web_app/src/__tests__/components/finance/_test_journal_form.test.tsx"
        - "frontend/web_app/src/__tests__/components/finance/_test_payout_control_room.test.tsx"
        - "frontend/web_app/src/__tests__/pages/admin/finance/_test_finance_command_center.test.tsx"
      api_routes:
        - "GET /finance/accounts"
        - "POST /finance/accounts"
        - "GET /finance/accounts/{id}"
        - "POST /finance/journal"
        - "GET /finance/journal"
        - "GET /finance/journal/{id}"
        - "POST /finance/ledger/recompute"
        - "GET /finance/trial-balance"
        - "GET /finance/profit-loss"
        - "POST /finance/period-close"
        - "GET /finance/periods"
        - "GET /treasury/cash-positions"
        - "POST /treasury/payout-batches"
        - "GET /treasury/payout-batches/{id}"
        - "POST /treasury/payout-batches/{id}/approve"
        - "POST /treasury/payout-batches/{id}/dispatch"
        - "POST /treasury/bank-reconciliations"
        - "GET /treasury/bank-reconciliations/{id}"
        - "POST /treasury/bank-reconciliations/{id}/match"
        - "POST /payments/charge"
        - "POST /payments/refund"
        - "GET /payments/{id}"
        - "POST /payments/webhook"
        - "GET /finance/reports/balance-sheet"
        - "GET /finance/reports/cash-flow"
        - "GET /finance/automations"
        - "POST /finance/automations/{id}/run"
      models:
        - "Account"
        - "JournalEntry"
        - "JournalEntryLine"
        - "Ledger"
        - "TrialBalance"
        - "ProfitLoss"
        - "PeriodClose"
        - "CashPosition"
        - "PayoutBatch"
        - "PayoutRun"
        - "BankReconciliation"
        - "BankAccount"
        - "PaymentTransaction"
        - "PaymentMethod"
        - "Refund"
        - "FxRate"
        - "FraudScore"
        - "AuditLog"
    diagram: |
      flowchart TB
        OE[("outbox_events: order/payroll")]
        OE --> JE[finance.journal_entries + journal_entry_lines]
        JE -->|strict double-entry| LG[finance.ledger]
        LG --> TB[finance.trial_balance] --> PL[finance.profit_loss]
        JE --> CASH[treasury.cash_positions]
        JE --> PB[treasury.payout_batches] -->|Maker != Checker| DISP[dispatch -> bank]
        DISP --> REC[treasury.bank_reconciliations]
        REC -->|variance| EX[exception queue / DLQ]
        PAY[payment_transactions] --> JE
        JE --> AUD[audit.audit_logs WORM]
        REC --> AN[analytics marts]

    ui_diagram: |
      flowchart TB
        subgraph WIN["WINDOW - Finance / Treasury Command Room"]
          HD["Top bar: period - cash-positions - trial-balance - reports"]
          NV["Left: Journal - Ledger - Payments - Payouts - Reconciliation - Audit"]
          MA["Center: JournalEntryForm - LedgerChain - PayoutControlRoom - ReconciliationGrid"]
          SB["Right: BalanceSheet - CashFlowReport - ProfitLoss - KpiStrip"]
          MK["Maker-Checker: confirm/approve money & permission actions"]
        end
        WIN --> EV["Outbox events -> treasury/analytics"]
  # ===========================================================================
  - id: SYS_004   # Order Tracker & Order Management
    name: Order Tracker & Order Management
    weight: 9
    update_version: "v1_14-08-2026"
    scope: Admin · Customer · Supplier - Logistic Partner - Employee
    description: |
      ## Capabilities
      - **Order Tracker & Order Management** — the `commerce.orders` / `order_items` / `carts` lifecycle plus `logistics.shipments` / `pod` (proof of delivery) and returns/refunds, spanning customer, supplier, admin and logistics views. Inherits constitutional rules: **RLS `country_code`, Alembic-only migrations, event-driven writes (outbox), append-only audit, no silent fallbacks.** Strategy: **complete + wire the existing skeleton; do not rebuild.**

      - **Canonical lifecycle (order → delivery):** `PENDING_PAYMENT` → `CONFIRMED` → `PROCESSING` → `PACKED` → `SHIPPED` → `IN_TRANSIT` → `OUT_FOR_DELIVERY` → `DELIVERED`, with `CANCELLED` / `RETURNED` / `REFUNDED` branches. Each transition is role-guarded and (where required) proof-gated.

      - **Status & transition rules:** who-may-do-what enforced server-side (customer cancels only pre-`CONFIRMED`; supplier marks `PACKED`; logistics `SHIPPED`/`IN_TRANSIT`/`OUT_FOR_DELIVERY`; `DELIVERED` requires POD/signature proof). Invalid transitions rejected.

      - **Packaging & printing material:** on `PACKED`, generate shipping label + packing slip (PDF) via `backend/providers/media/shipping_label_provider.py`; `communication`/print queue.

      - **Returns & replacements:** `returns` / `refunds` tracked as first-class (not an afterthought); return request → approve → pickup/refund; replacement re-creates order line.

      - **Panel visibility matrix:** customer sees own orders + tracking; supplier sees fulfillment for assigned products; admin sees all + ops; logistics sees shipments + POD capture.

      - **Events, notifications & reconciliation:** every transition emits `outbox_events` → notifications (in-app/email/SMS/push), customer tracking updates, and finance/treasury money-flow reconciliation (payment ↔ order ↔ payout).

      - **Surfaces & sign-off:** customer tracking page, supplier fulfillment dashboard, admin order panel (ops cockpit), logistics handoff + POD capture (mobile).

      ## Non-negotiables
      - **Strict lifecycle + role guards**; invalid transitions rejected server-side.
      - **Proof-gated `DELIVERED`** (POD/signature); no silent delivery.
      - **Returns/refunds first-class** with audit trail.
      - **Outbox events** on every transition → notifications + finance recon.
      - **RLS `country_code`**; cross-country order reads return 0 rows.
      - **No silent fallbacks** (fail loud + DLQ for notify/recon).

      ## Data model (`commerce`/`logistics` unless noted)
      - `commerce.carts`
      - `commerce.orders`
      - `commerce.order_items`
      - `commerce.order_status_history`
      - `logistics.shipments`
      - `logistics.shipment_items`
      - `logistics.pod` (proof of delivery)
      - `logistics.return_requests`
      - `commerce.refunds`
      - `commerce.shipping_labels`
      - `commerce.order_events` (notification log)
      - `audit.audit_logs`

      ## API
      - `POST /carts` · `GET /carts/{id}` · `PATCH /carts/{id}`
      - `POST /orders` (checkout) · `GET /orders` · ` · `GET /orders/{id}` · `PATCH /orders/{id}` · `POST /orders/{id}/cancel`
      - `POST /orders/{id}/confirm` · `POST /orders/{id}/pack` · `POST /orders/{id}/ship` · `POST /orders/{id}/in-transit` · `POST /orders/{id}/out-for-delivery` · `POST /orders/{id}/deliver` (POD)
      - `GET /orders/{id}/tracking` · `GET /orders/{id}/history`
      - `POST /orders/{id}/labels` (print) · `GET /orders/{id}/labels`
      - `POST /returns` · `GET /returns` · `PATCH /returns/{id}` (approve/reject) · `POST /returns/{id}/pickup`
      - `POST /refunds` · `GET /refunds/{id}`
      - `GET /shipments` · `GET /shipments/{id}` · `POST /shipments/{id}/pod`
      - `GET /admin/orders` (ops cockpit)

      ## State machine
      - `PENDING_PAYMENT` → `CONFIRMED` → `PROCESSING` → `PACKED` → `SHIPPED` → `IN_TRANSIT` → `OUT_FOR_DELIVERY` → `DELIVERED`
      - `CONFIRMED`/`PROCESSING` → `CANCELLED` (pre-delivery, role-guarded)
      - `DELIVERED` → `RETURNED` → `REFUNDED`
      - `PACKED` → `SHIPPED` requires label; `DELIVERED` requires POD proof.

      ## Automations
      - **Auto-cancel:** unpaid `PENDING_PAYMENT` after SLA → cancel + release stock.
      - **Auto-transition on POD:** `OUT_FOR_DELIVERY` → `DELIVERED` on proof capture; notify customer + recon.
      - **Refund workflow:** approved return → refund → reversing journal (SYS_003) + restock.
      - **Notify on every transition** via outbox → in-app/email/SMS/push.

      ## UI/UX layout
      - **Customer tracking page:** timeline of statuses with proofs (label, POD), ETA, return/refund actions, support link.
      - **Supplier fulfillment dashboard:** queue of `PACKED`-pending orders for assigned products; pack + label print.
      - **Admin order panel (ops cockpit):** filterable table, bulk actions, status override (role-guarded), returns/refunds queue, exception watch.
      - **Logistics handoff (mobile):** scan → `SHIPPED`/`IN_TRANSIT`/`OUT_FOR_DELIVERY` → POD capture (photo/signature).
      - **UX principles:** timeline component, skeleton loaders, explicit empty/error, ARIA + keyboard, country switcher re-sets RLS.

      ## Step-by-step
      - **Step 1 — Orders & cart.** `commerce.orders`/`order_items`/`carts` with country scoping + status history. *Done when:* checkout creates order; history records transitions.
      - **Step 2 — Lifecycle & guards.** All status transitions role-guarded + invalid rejected. *Done when:* only authorized roles can advance; POD required for `DELIVERED`.
      - **Step 3 — Packaging & labels.** `PACKED` generates label + packing slip PDF. *Done when:* label prints; shipment created.
      - **Step 4 — Shipments & POD.** `logistics.shipments`/`pod`; mobile capture. *Done when:* POD capture flips to `DELIVERED`; proof stored.
      - **Step 5 — Returns & refunds.** `return_requests`/`refunds` first-class + audit + restock + reversing journal. *Done when:* return approves; refund posts; stock restored.
      - **Step 6 — Events, notifications & recon.** Outbox on every transition → notify + finance reconciliation. *Done when:* customer tracking live; recon balances; DLQ surfaced.
    sections:
      §I: "Admin: ops cockpit, all orders, overrides (role-guarded), returns/refunds queue."
      §II: "Customer: own orders, tracking, returns/refunds, notifications."
      §III: "Supplier: fulfillment queue for assigned products, pack + label."
      §IV: "Logistics: shipments, status advance, POD capture (mobile)."
      §V: "Cross-domain: outbox → notifications + SYS_003 reconciliation + SYS_001 comms."
    expected:
      backend_files:
        - backend/routers/commerce_order_router.py
        - backend/routers/commerce_cart_router.py
        - backend/routers/logistics_shipment_router.py
        - backend/routers/commerce_return_router.py
        - backend/routers/commerce_refund_router.py
        - backend/controllers/commerce/order_controller.py
        - backend/controllers/commerce/cart_controller.py
        - backend/controllers/logistics/shipment_controller.py
        - backend/controllers/commerce/return_controller.py
        - backend/services/commerce/order_service.py
        - backend/services/commerce/cart_service.py
        - backend/services/commerce/order_lifecycle_service.py
        - backend/services/logistics/shipment_service.py
        - backend/services/commerce/return_service.py
        - backend/services/commerce/refund_service.py
        - backend/services/commerce/order_notification_service.py
        - backend/models/orders/order_model.py
        - backend/models/orders/cart_model.py
        - backend/models/orders/order_item_model.py
        - backend/models/orders/order_status_history_model.py
        - backend/models/logistics/shipment_model.py
        - backend/models/logistics/pod_model.py
        - backend/models/orders/return_model.py
        - backend/models/orders/refund_model.py
        - backend/models/orders/shipping_label_model.py
        - backend/events/order_status_pusher.py
        - backend/events/order_events.py
        - backend/jobs/order_autocancel_worker.py
        - backend/providers/media/shipping_label_provider.py
        - backend/jobs/order_notification_task.py
        - backend/db/schemas.py
        - backend/db/schemas.py
        - backend/db/schemas.py
        - backend/alembic/versions/commerce_orders_initial.py
      frontend_web:
        - "frontend/web_app/src/app/orders/page.tsx"
        - "frontend/web_app/src/app/orders/[id]/page.tsx"
        - "frontend/web_app/src/app/orders/[id]/tracking/page.tsx"
        - "frontend/web_app/src/app/profile/orders/page.tsx"
        - "frontend/web_app/src/app/admin/orders/page.tsx"
        - "frontend/web_app/src/app/admin/orders/returns/page.tsx"
        - "frontend/web_app/src/app/supplier/fulfillment/page.tsx"
        - "frontend/web_app/src/components/admin/OrderTimeline.tsx"
        - "frontend/web_app/src/components/admin/OrderCard.tsx"
        - "frontend/web_app/src/components/admin/OrderTable.tsx"
        - "frontend/web_app/src/components/admin/TrackingView.tsx"
        - "frontend/web_app/src/components/admin/ReturnRequestForm.tsx"
        - "frontend/web_app/src/components/admin/RefundStatus.tsx"
        - "frontend/web_app/src/components/admin/ShippingLabelPrint.tsx"
        - "frontend/web_app/src/components/admin/OrderOpsCockpit.tsx"
        - "frontend/web_app/src/lib/order/orders.ts"
        - "frontend/web_app/src/lib/order/tracking.ts"
        - "frontend/web_app/src/hooks/useOrders.ts"
        - "frontend/web_app/src/hooks/useOrderTracking.ts"
        - "frontend/web_app/src/hooks/useReturns.ts"
      frontend_mobile:
        - "frontend/mobile_app/app/orders/index.tsx"
        - "frontend/mobile_app/app/orders/[id].tsx"
        - "frontend/mobile_app/app/logistics-partner/shipments.tsx"
        - "frontend/mobile_app/app/logistics-partner/pod.tsx"
      tests:
        - "backend/tests/commerce/_test_orders.py"
        - "backend/tests/commerce/_test_order_lifecycle_guards.py"
        - "backend/tests/commerce/_test_pod_delivery.py"
        - "backend/tests/commerce/_test_returns_refunds.py"
        - "backend/tests/commerce/_test_autocancel.py"
        - "backend/tests/commerce/_test_rls_country.py"
        - "frontend/web_app/src/__tests__/components/order/_test_order_timeline.test.tsx"
        - "frontend/web_app/src/__tests__/pages/orders/_test_tracking.test.tsx"
        - "frontend/web_app/src/__tests__/pages/admin/orders/_test_ops_cockpit.test.tsx"
      api_routes:
        - "POST /carts"
        - "GET /carts/{id}"
        - "PATCH /carts/{id}"
        - "POST /orders"
        - "GET /orders"
        - "GET /orders/{id}"
        - "PATCH /orders/{id}"
        - "POST /orders/{id}/cancel"
        - "POST /orders/{id}/confirm"
        - "POST /orders/{id}/pack"
        - "POST /orders/{id}/ship"
        - "POST /orders/{id}/in-transit"
        - "POST /orders/{id}/out-for-delivery"
        - "POST /orders/{id}/deliver"
        - "GET /orders/{id}/tracking"
        - "GET /orders/{id}/history"
        - "POST /orders/{id}/labels"
        - "GET /orders/{id}/labels"
        - "POST /returns"
        - "GET /returns"
        - "PATCH /returns/{id}"
        - "POST /returns/{id}/pickup"
        - "POST /refunds"
        - "GET /refunds/{id}"
        - "GET /shipments"
        - "GET /shipments/{id}"
        - "POST /shipments/{id}/pod"
        - "GET /admin/orders"
      models:
        - "Cart"
        - "Order"
        - "OrderItem"
        - "OrderStatusHistory"
        - "Shipment"
        - "ShipmentItem"
        - "Pod"
        - "ReturnRequest"
        - "Refund"
        - "ShippingLabel"
        - "OrderEvent"
        - "AuditLog"
    diagram: |
      flowchart LR
        C[carts] --> O[orders]
        O --> H[order_status_history]
        O -->|CONFIRMED| PACK[PACKED -> shipping_labels]
        PACK --> SH[shipments] --> POD[pod -> DELIVERED]
        O --> RET[return_requests] --> REF[refunds]
        O --> OUT[("outbox_events")]
        OUT --> NOT[notifications]
        OUT --> FIN[SYS_003 reconciliation]
        OUT --> COMM[SYS_001 comms]

    ui_diagram: |
      flowchart TB
        subgraph WIN["WINDOW - Order Tracker & OMS"]
          HD["Top bar: orders nav - tracking - returns - refunds"]
          NV["Left: order list (status filter) - exceptions"]
          MA["Center: OrderTimeline - OrderTable - TrackingView - ReturnRequestForm"]
          SB["Right: RefundStatus - ShippingLabelPrint - Customer/Support thread"]
        end
        WIN --> RE["Real-time: order_status_pusher - tracking updates"]
  # ===========================================================================
  - id: SYS_005   # Employees & HR System
    name: Employees & HR System
    weight: 9
    update_version: "v1_14-08-2026"
    scope: Admin · Employee - Country Admin - Manager
    description: |
      ## Capabilities
      - **Employees & HR System (EMS core)** — the `hr` bounded context implementing unified identity (5 doors), org chart & hierarchy/RBAC, country-wise management, lifecycle (onboarding↔offboarding), time/attendance/leave/shifts, activity ledger, payroll auto-disbursement, and the automation tower. (Communication suite = SYS_001; payroll journals post into SYS_003.) Inherits constitutional rules: **RLS `country_code`, Alembic-only migrations, event-driven writes (outbox), append-only audit, Maker-Checker on money & permissions, config-as-data, no silent fallbacks.** Strategy: **complete + wire the existing ~70% skeleton; do not rebuild.**

      - **Unified identity & 5 doors:** single `users`+`employees` across password/TOTP, phone-OTP, biometric (trusted device), QR-kiosk+geo-fence, SSO. `user_devices` fingerprint/IP/OS; unknown device → force MFA. Login sets `SET app.current_country_code` (RLS); risk score → step-up MFA/lock + manager notify. Quarterly access-recertification.

      - **Org chart & hierarchy:** `org_units` materialized path + `parent_id` + `reporting_manager_id` + `authority_level`; matrix relations (`employee_relations`); triggers block circular/lower-authority reporting. Services: `get_org_chart / get_user_chain / get_all_subordinates / can_manage / reassign_manager / backfill_authority_levels` (single-transaction drag-reassign).

      - **3-layer RBAC:** Global role JSON → Country role (`country_staff_assignments.role_in_country`) → Hierarchy-derived; resolver precedence **Country > Hierarchy > Global**, Redis-cached, invalidated on change; `require_permission(...)` everywhere; Permission-Matrix UI with Maker-Checker for `finance.*`/`users.delete`; sub-admins cannot grant what they don't hold; self-service requests route up `can_manage()`.

      - **Country-wise management:** Country Staff Assignment console (multi-country roles + country switcher re-sets RLS); per-country salary currency, leave allocations (`employee_leave_ledgers`), `country_holiday_calendars`, labor-law rules (notice/EOSB) from `country_configs`.

      - **Lifecycle:** Onboarding pipeline with SLA per step (user+employee → org/manager/role/country → documents → biometric → assets → ID card → welcome); probation 30/60/90 alerts; Offboarding auto-run revokes sessions + disables devices + reclaims assets + exit survey + transfers `shift_handover_tasks` + archives per retention (legal-hold override) + `employment_status='terminated'`; final EOSB event → Treasury (SYS_003).

      - **Time, attendance, leave, shifts:** QR-kiosk/biometric/geo-fence attendance; `is_anomaly` (Haversine >50m or untrusted) → manager anomaly dashboard; auto-rostering by rules; handover gate (ack `shift_handover_tasks` before clock-out); leave routed to manager with balance enforcement + country types; `employee_work_logs` → utilization analytics.

      - **Activity ledger & compliance:** append-only `employee_activity_logs` (actor/target/action/entity/country/metadata/ip/device); visibility self / manager-subtree / HR-legal (gated + access-logged); eDiscovery export; COI detection; document/cert expiry alerts + blocks; PDPL/GDPR export packages.

      - **Payroll & auto-disbursement:** auto-aggregate base + attendance + OT + expenses + per-diem + leave encashment + KPI multiplier + statutory; draft `payout_batch` per employee → **Maker (payroll mgr) ≠ Checker (finance controller)** → Treasury journal (SYS_003) → bank → recon → payslip PDF → notify; post-close immutable.

      - **Automation tower:** onboarding, attendance/anomaly, rostering/handover, leave, payroll, doc-expiry, COI, offboarding, access-governance, analytics/attrition — each run logged `actor=system:<job>`, thresholds in `configuration`, DLQ on failure.

      ## Non-negotiables
      - **One identity, many doors**; RLS `country_code` set at login; cross-country reads return 0 rows.
      - **Hierarchy = authority = permission**; anti-cycle + authority triggers.
      - **3-layer RBAC** with `require_permission`; Maker ≠ Checker on money/permissions.
      - **Activity ledger append-only**; eDiscovery-ready; PII encrypted at rest.
      - **Payroll immutable post-close**; corrections via next-period adjustments.
      - **No silent fallbacks**; automation failures → explicit exception/DLQ.

      ## Data model (`hr` schema unless noted)
      - `hr.employees`
      - `hr.org_units` (materialized path)
      - `hr.employee_relations` (matrix)
      - `hr.roles`
      - `hr.country_staff_assignments`
      - `hr.employee_permissions`
      - `hr.user_devices`
      - `hr.employee_biometrics`
      - `hr.dynamic_qr_sessions`
      - `hr.geo_fence_logs`
      - `hr.employee_documents`
      - `hr.employee_assets`
      - `hr.physical_id_cards`
      - `hr.employee_leave_ledgers`
      - `hr.employee_work_logs`
      - `hr.shift_handover_tasks`
      - `hr.employee_bank_accounts`
      - `hr.okr_objectives`
      - `hr.kpi_metrics`
      - `hr.performance_reviews`
      - `hr.employee_activity_logs`
      - `hr.automation_runs`
      - `hr.country_holiday_calendars`
      - `configuration.*` (thresholds/rules)
      - `media.media_assets`

      ## API
      - `POST /auth/login` (5 doors) · `POST /auth/logout` · `POST /auth/mfa/verify` · `POST /auth/refresh`
      - `GET /employees` · `POST /employees` · `GET /employees/{id}` · `PATCH /employees/{id}` · `DELETE /employees/{id}`
      - `GET /org-chart` · `POST /org-chart/reassign` · `GET /org-chart/chain/{id}` · `GET /subordinates/{id}`
      - `GET /roles` · `POST /roles` · `GET /permissions/matrix` · `POST /permissions/grant` (Maker-Checker)
      - `GET /country-assignments` · `POST /country-assignments` · `POST /country/switch`
      - `POST /onboarding/start` · `GET /onboarding/status/{id}`
      - `POST /attendance/check-in` · `POST /attendance/check-out` · `GET /attendance/anomalies`
      - `POST /leave/request` · `GET /leave` · `PATCH /leave/{id}` · `POST /leave/{id}/escalate`
      - `GET /shifts/roster` · `POST /shifts/roster` · `GET /handover/tasks`
      - `GET /activity-log` · `GET /activity-log/eDiscovery/export`
      - `POST /payroll/run` · `GET /payroll/batches` · `POST /payroll/batches/{id}/approve` (Checker) · `POST /payroll/batches/{id}/dispatch`
      - `GET /automations` · `POST /automations/{id}/run` · `GET /automations/{id}/runs`
      - `GET /performance/reviews` · `POST /performance/reviews`

      ## State machine
      - `ONBOARDING` → `PROBATION` → `ACTIVE` → `PIP` → `OFFBOARDING` → `ALUMNI` (employee lifecycle)
      - `DRAFT` → `APPROVED` → `DISPATCHED` → `SETTLED` (payroll batch; Maker≠Checker)
      - `PENDING` → `APPROVED`/`REJECTED`/`ESCALATED` (leave)
      - `UNCONFIRMED` → `CONFIRMED` (device/biometric)
      - `OPEN` → `ACKNOWLEDGED` (handover)

      ## Automations
      - **Auto-onboarding:** offer accepted → pipeline steps w/ SLA; SLA breach → escalate HR head.
      - **Auto-attendance/anomaly:** scan → check-in/out + late/OT; anomaly (buddy-punch/>50m/untrusted) → manager.
      - **Auto-rostering/handover:** publish rosters; block clock-out till handover ack.
      - **Auto-leave:** ≤threshold & no conflict → auto-approve else route up; year-end carry-forward; abuse alerts.
      - **Auto-payroll:** monthly → draft → Maker-Checker → journal (SYS_003) → bank → recon → payslips; hold on salary Δ/IBAN/cert.
      - **Auto doc/cert expiry, COI, offboarding, access-governance, analytics** per EMS spec.

      ## UI/UX layout
      - **Employee Workspace (landing):** My Day (shift/handover/approvals/announcements), KPI strip, quick actions, team pulse, chat drawer.
      - **Admin HR Command Center (lazy tabs):** directory · org-chart (draggable, solid/dotted, authority badges) · attendance (anomaly split-screen) · shifts-handover · leave (auto-approve log + escalations) · payroll control room (maker≠checker locks, exception holds) · performance (health board, calibration, PIP) · onboarding/offboarding (SLA timers) · documents-compliance (expiry radar 30/14/7) · coi-disciplinary · permission-matrix (Maker-Checker) · country-assignments · automation-tower (toggle/cron/last-run/DLQ).
      - **Key screens:** Org Chart drag-reassign with impact preview; Payroll Control Room pipeline chips; biometric/kiosk login; anomaly dashboard.
      - **UX principles:** skeleton loaders, explicit empty/error, ARIA + keyboard, density toggle, country switcher re-sets RLS; mobile = biometric login, kiosk, scan payslip, approvals push.

      ## Step-by-step
      - **Step 1 — Identity (5 doors).** auth + device trust + risk + RLS-on-login + kiosk session. *Done when:* same person logs in via biometric + QR-kiosk with correct country scope; unknown-device MFA passes.
      - **Step 2 — Org engine.** Materialized path + matrix + anti-cycle + authority backfill; draggable reassign. *Done when:* drag recomputes path/authority; approvals follow chain.
      - **Step 3 — RBAC.** Resolver + Redis cache + `require_permission` + Matrix UI + Maker-Checker + recertification. *Done when:* sub-admin cannot over-grant.
      - **Step 4 — Country console.** Assignments + switcher + localization. *Done when:* cross-country read empty without global role.
      - **Step 5 — Lifecycle.** Onboarding SLA + probation + offboarding auto-revoke + EOSB event. *Done when:* offboarding leaves 0 live sessions/devices.
      - **Step 6 — Time & shifts.** Anomaly + auto-rostering + handover gate + leave auto-approve/escalate. *Done when:* unactioned leave auto-escalates.
      - **Step 7 — Activity ledger & eDiscovery.** Append-only hooks across modules + export. *Done when:* every action appears in ledger.
      - **Step 8 — Performance.** OKR cascade + KPI pulls + 360 + health/PIP + bonus feed. *Done when:* health board matches fixtures.
      - **Step 9 — Payroll.** Aggregate → Maker-Checker → Treasury journal → bank → recon → payslips. *Done when:* simulated month disburses balanced + 0 recon variance.
      - **Step 10 — Automation tower.** `automation_runs` + toggles + assistants + analytics. *Done when:* each automation shows run health; paused = badge.
    sections:
      §I: "Admin/HR: employees, org chart, RBAC, country console, lifecycle, time, payroll, performance, automation."
      §II: "Employee (self): ESS portal, profile/docs/leave/expense/payslip/shift-swap/goals, kiosk."
      §III: "Supplier: n/a (HR internal)."
      §IV: "Logistics: n/a (HR internal)."
      §V: "Cross-domain: EOSB/offboarding events → SYS_003 Treasury; activity ledger → SYS_001 comms; RLS shared."
    expected:
      backend_files:
        - backend/routers/hr_employee_router.py
        - backend/routers/hr_org_chart_router.py
        - backend/routers/hr_role_router.py
        - backend/routers/hr_permission_router.py
        - backend/routers/hr_country_assignment_router.py
        - backend/routers/hr_lifecycle_router.py
        - backend/routers/hr_attendance_router.py
        - backend/routers/hr_leave_router.py
        - backend/routers/hr_shift_router.py
        - backend/routers/hr_performance_router.py
        - backend/routers/hr_payroll_router.py
        - backend/routers/hr_activity_log_router.py
        - backend/routers/hr_automation_router.py
        - backend/controllers/hr/employee_controller.py
        - backend/controllers/hr/org_chart_controller.py
        - backend/controllers/hr/rbac_controller.py
        - backend/controllers/hr/attendance_controller.py
        - backend/controllers/hr/payroll_controller.py
        - backend/controllers/hr/automation_controller.py
        - backend/services/security/auth_service.py
        - backend/services/security/device_trust_service.py
        - backend/services/security/risk_scoring_service.py
        - backend/services/hr/org_chart_service.py
        - backend/services/hr/rbac_resolver_service.py
        - backend/services/hr/country_assignment_service.py
        - backend/services/hr/lifecycle_service.py
        - backend/services/hr/attendance_service.py
        - backend/services/hr/leave_service.py
        - backend/services/hr/shift_service.py
        - backend/services/hr/performance_service.py
        - backend/services/hr/payroll_service.py
        - backend/services/hr/activity_log_service.py
        - backend/services/hr/automation_service.py
        - backend/services/hr/compliance_service.py
        - backend/models/hr/employee_model.py
        - backend/models/hr/org_unit_model.py
        - backend/models/hr/role_model.py
        - backend/models/hr/permission_model.py
        - backend/models/hr/device_model.py
        - backend/models/hr/biometric_model.py
        - backend/models/hr/document_model.py
        - backend/models/hr/asset_model.py
        - backend/models/hr/leave_model.py
        - backend/models/hr/attendance_model.py
        - backend/models/hr/payroll_model.py
        - backend/models/hr/performance_model.py
        - backend/models/hr/activity_log_model.py
        - backend/models/hr/automation_run_model.py
        - backend/events/attendance_presence.py
        - backend/events/hr_events.py
        - backend/jobs/hr_automation_worker.py
        - backend/jobs/hr_payroll_worker.py
        - backend/providers/auth/sso_provider.py
        - backend/jobs/hr_onboarding_task.py
        - backend/db/schemas.py
        - backend/db/schemas.py
        - backend/db/schemas.py
        - backend/db/schemas.py
        - backend/alembic/versions/hr_initial.py
      frontend_web:
        - "frontend/web_app/src/app/employee/workspace/page.tsx"
        - "frontend/web_app/src/app/admin/hr/employees/page.tsx"
        - "frontend/web_app/src/app/admin/hr/org-chart/page.tsx"
        - "frontend/web_app/src/app/admin/hr/roles/page.tsx"
        - "frontend/web_app/src/app/admin/hr/permissions/page.tsx"
        - "frontend/web_app/src/app/admin/hr/country-assignments/page.tsx"
        - "frontend/web_app/src/app/admin/hr/onboarding/page.tsx"
        - "frontend/web_app/src/app/admin/hr/offboarding/page.tsx"
        - "frontend/web_app/src/app/admin/hr/attendance/page.tsx"
        - "frontend/web_app/src/app/admin/hr/leave/page.tsx"
        - "frontend/web_app/src/app/admin/hr/shifts/page.tsx"
        - "frontend/web_app/src/app/admin/hr/payroll/page.tsx"
        - "frontend/web_app/src/app/admin/hr/performance/page.tsx"
        - "frontend/web_app/src/app/admin/hr/automation/page.tsx"
        - "frontend/web_app/src/app/admin/hr/activity-log/page.tsx"
        - "frontend/web_app/src/components/ems/EmployeeWorkspace.tsx"
        - "frontend/web_app/src/components/ems/OrgChartCanvas.tsx"
        - "frontend/web_app/src/components/ems/PermissionMatrix.tsx"
        - "frontend/web_app/src/components/ems/AttendanceAnomalyBoard.tsx"
        - "frontend/web_app/src/components/ems/LeaveApprovalBoard.tsx"
        - "frontend/web_app/src/components/ems/PayrollControlRoom.tsx"
        - "frontend/web_app/src/components/ems/PerformanceHealthBoard.tsx"
        - "frontend/web_app/src/components/ems/AutomationTower.tsx"
        - "frontend/web_app/src/components/ems/OnboardingPipeline.tsx"
        - "frontend/web_app/src/lib/hr/auth.ts"
        - "frontend/web_app/src/lib/hr/orgChart.ts"
        - "frontend/web_app/src/hooks/useEmployees.ts"
        - "frontend/web_app/src/hooks/useOrgChart.ts"
        - "frontend/web_app/src/hooks/usePermissions.ts"
        - "frontend/web_app/src/hooks/usePayroll.ts"
        - "frontend/web_app/src/hooks/useAttendance.ts"
      frontend_mobile:
        - "frontend/mobile_app/app/employee/index.tsx"
        - "frontend/mobile_app/app/employee/kiosk.tsx"
        - "frontend/mobile_app/app/employee/attendance.tsx"
        - "frontend/mobile_app/app/employee/leave.tsx"
        - "frontend/mobile_app/app/employee/payslip.tsx"
        - "frontend/mobile_app/app/employee/approvals.tsx"
        - "frontend/mobile_app/app/employee/goals.tsx"
      tests:
        - "backend/tests/hr/_test_auth_five_doors.py"
        - "backend/tests/hr/_test_org_chart.py"
        - "backend/tests/hr/_test_rbac_resolver.py"
        - "backend/tests/hr/_test_lifecycle.py"
        - "backend/tests/hr/_test_attendance_anomaly.py"
        - "backend/tests/hr/_test_leave_automation.py"
        - "backend/tests/hr/_test_payroll_maker_checker.py"
        - "backend/tests/hr/_test_activity_ledger.py"
        - "backend/tests/hr/_test_rls_country.py"
        - "backend/tests/hr/_test_automation.py"
        - "frontend/web_app/src/__tests__/components/hr/_test_org_chart.test.tsx"
        - "frontend/web_app/src/__tests__/components/hr/_test_payroll_control_room.test.tsx"
        - "frontend/web_app/src/__tests__/pages/admin/hr/_test_hr_command_center.test.tsx"
      api_routes:
        - "POST /auth/login"
        - "POST /auth/logout"
        - "POST /auth/mfa/verify"
        - "POST /auth/refresh"
        - "GET /employees"
        - "POST /employees"
        - "GET /employees/{id}"
        - "PATCH /employees/{id}"
        - "DELETE /employees/{id}"
        - "GET /org-chart"
        - "POST /org-chart/reassign"
        - "GET /org-chart/chain/{id}"
        - "GET /subordinates/{id}"
        - "GET /roles"
        - "POST /roles"
        - "GET /permissions/matrix"
        - "POST /permissions/grant"
        - "GET /country-assignments"
        - "POST /country-assignments"
        - "POST /country/switch"
        - "POST /onboarding/start"
        - "GET /onboarding/status/{id}"
        - "POST /attendance/check-in"
        - "POST /attendance/check-out"
        - "GET /attendance/anomalies"
        - "POST /leave/request"
        - "GET /leave"
        - "PATCH /leave/{id}"
        - "POST /leave/{id}/escalate"
        - "GET /shifts/roster"
        - "POST /shifts/roster"
        - "GET /handover/tasks"
        - "GET /activity-log"
        - "GET /activity-log/eDiscovery/export"
        - "POST /payroll/run"
        - "GET /payroll/batches"
        - "POST /payroll/batches/{id}/approve"
        - "POST /payroll/batches/{id}/dispatch"
        - "GET /automations"
        - "POST /automations/{id}/run"
        - "GET /automations/{id}/runs"
        - "GET /performance/reviews"
        - "POST /performance/reviews"
      models:
        - "Employee"
        - "OrgUnit"
        - "EmployeeRelation"
        - "Role"
        - "CountryStaffAssignment"
        - "EmployeePermission"
        - "UserDevice"
        - "EmployeeBiometric"
        - "DynamicQrSession"
        - "GeoFenceLog"
        - "EmployeeDocument"
        - "EmployeeAsset"
        - "PhysicalIdCard"
        - "EmployeeLeaveLedger"
        - "EmployeeWorkLog"
        - "ShiftHandoverTask"
        - "EmployeeBankAccount"
        - "OkrObjective"
        - "KpiMetric"
        - "PerformanceReview"
        - "EmployeeActivityLog"
        - "AutomationRun"
        - "CountryHolidayCalendar"
    diagram: |
      flowchart TB
        ID["5 doors: pwd/TOTP, OTP, biometric, QR-kiosk, SSO"] --> SES["Session: user_devices + risk -> step-up MFA + RLS"]
        SES --> RBAC["RBAC resolver: Country > Hierarchy > Global (Redis)"]
        RBAC --> ORG[hr.org_units: path + authority_level]
        ORG --> ATT[attendance / shifts / handover / leave]
        ORG --> LIFE[onboarding <-> offboarding]
        ORG --> PERF[OKR/KPI/360/PIP]
        PERF -->|bonus| PAY[payroll aggregate]
        PAY -->|Maker != Checker| FIN[(SYS_003 treasury journal)]
        ORG & ATT & LIFE --> AL[("employee_activity_logs WORM")]
        LIFE -->|EOSB event| FIN

    ui_diagram: |
      flowchart TB
        subgraph WIN["WINDOW - Employees & HR (EMS)"]
          HD["Top bar: employee workspace - country - kiosk"]
          NV["Left: OrgChart - Attendance - Leave - Payroll - Performance - Permissions"]
          MA["Center: OrgChartCanvas - AttendanceAnomalyBoard - LeaveApprovalBoard - PayrollControlRoom"]
          SB["Right: PerformanceHealthBoard - PermissionMatrix - ActivityLedger"]
          AU["5-doors auth - device trust - risk score on login"]
        end
        WIN --> EV["Lifecycle events -> Treasury / Comms"]
  # ===========================================================================
  - id: SYS_006   # Advanced Smart Search · Filter · Sort Bar
    name: Advanced Smart Search · Filter · Sort Bar
    weight: 8
    update_version: "v1_14-08-2026"
    scope: Customer - Employee - Supplier
    description: |
      ## Capabilities
      - **Advanced Smart Search · Filter · Sort Bar (Discovery Layer)** — the customer storefront discovery surface reusing & extending `FilterSearchBar` (web) / `ProductSearchFilterBar` (mobile): **text (AI-parsed) + image + voice** search, **combined faceted filtering** (Category + Price + Rating + Supplier + Brand + Attributes together) with faceted counts, hybrid ranking, cursor pagination, all wired to PostgreSQL. Inherits constitutional rules: **RLS `country_code`, Alembic-only migrations, media bytes in R2, no silent fallbacks, reuse don't redesign.** Strategy: **extend the existing bar + index layer; do not rebuild the component look.**

      - **Reuse, don't redesign:** keep `FilterSearchBar`/`ProductSearchFilterBar` and the theme tokens (`glass-search`, `glass-dropdown`, `surface0/1/2`, `text/textMuted`, `glass.border`), density system, RTL/i18n (Arabic preserved). Bar placement centered in header after logo; exact bar look preserved.

      - **Hybrid search (not vector-only):** PostgreSQL FTS/ILIKE (lexical) + `pgvector` (semantic, `embedding vector(1536)`) + CLIP (visual) fused with **Reciprocal Rank Fusion (RRF)**. Extensions: `vector`, `pg_trgm`, `btree_gin`.

      - **One search brain:** voice + image funnel into the existing NLP parser `parsed` (brand/color/size/price/min_rating/quality/sort/has_video) — no second parser. Image → CLIP embedding → vector search; voice → Whisper → text → parser.

      - **Combined faceted filtering:** Category tree + Price range + Rating + Supplier + Brand + Attributes multi-select; **faceted counts** recomputed per filter set; applied as SQL WHERE (`country_code` + FTS + vector + facet predicates). Sort options: relevance, price asc/desc, rating, newest, popularity.

      - **Performance:** cursor-based pagination (no OFFSET on large tables); composite indexes `(country_code, created_at)`, `(status, due_date)`; GIN on JSONB/tsvector; materialized views for popular facets; **<300ms p95** budget; EXPLAIN ANALYZE gates in CI (block sequential scans / >300ms).

      - **Video commerce:** row-first hybrid desktop video grid; video → recommendation circuit (watch→embed→recommend); video status lifecycle (UPLOADED→TRANSCODING→READY→FAILED).

      - **Scale ladder:** MVP (10K products) → Scale (1M, JSONB GIN, pgvector) → Massive (100M, shard by country).

      ## Non-negotiables
      - **Reuse existing components**; preserve exact bar look + RTL/i18n.
      - **Hybrid only** (FTS + pgvector + CLIP + RRF); single NLP parser.
      - **Combined facets with counts**; cursor pagination; **<300ms p95**.
      - **RLS `country_code`** on every query; cross-country results excluded.
      - **No silent fallbacks**; failed pipeline → explicit error state, never masked zeros.

      ## Data model
      - `commerce.products` (+ `tsvector` generated column, GIN)
      - `commerce.product_variants` (JSONB attributes + GIN)
      - `commerce.categories` (materialized path)
      - `commerce.product_attributes` / `product_attribute_values`
      - `ai.ai_embeddings` (`vector(1536)`)
      - `media.media_assets` (CLIP embeddings for image search)
      - `search.search_queries` (logs/learning)
      - `search.facets_cache` (materialized counts)
      - `analytics.mv_popular_facets`
      - `video.videos` (video commerce)

      ## API
      - `GET /search?q=&category=&min_price=&max_price=&min_rating=&supplier=&brand=&attrs=&sort=&cursor=` (hybrid + facets)
      - `GET /search/facets` (faceted counts for current filter set)
      - `POST /search/image` (CLIP image search)
      - `POST /search/voice` (Whisper → parser)
      - `GET /search/autocomplete?q=`
      - `GET /search/suggestions` (personalized)
      - `POST /search/track` (learning loop)
      - `GET /products` (filtered PLP, delegates here)

      ## State machine
      - `IDLE` → `PARSING` → `QUERYING` → `RANKING` (RRF) → `RESULT` (search request)
      - `UPLOADED` → `TRANSCODING` → `READY` / `FAILED` (video)
      - `CACHED` → `INVALIDATED` (facet counts)

      ## Automations
      - **Learning loop:** search queries → embeddings → personalization/suggestions.
      - **Facet cache refresh:** on catalog change (outbox) → recompute `facets_cache` + mviews.
      - **Video recommendation:** watch events → embed → recommend.

      ## UI/UX layout
      - **Bar (preserved look):** centered in header; text input + image/voice buttons + filter & sort chips; dropdown panels (glass-dropdown) for facets; RTL aware.
      - **PLP / Home (mobile-first hybrid):** filter sidebar (desktop) / bottom-sheet (mobile), result grid, sort bar, lazy-load, skeleton loaders, explicit empty/error (no silent zero).
      - **Video commerce:** row-first hybrid grid; video cards play inline; recommendations rail.
      - **UX principles:** density toggle, tabular numerals, ARIA + keyboard, country switcher re-sets RLS, <300ms perceived.

      ## Step-by-step
      - **Step 1 — RECON.** Read every file in Step 1 list (bar components, search service, schema, indexes) before editing. *Done when:* no unknown dependency.
      - **Step 2 — Relocate bar to header** (centered, no restyle). *Done when:* bar renders in header, look identical.
      - **Step 3 — Hybrid search core (backend).** FTS/ILIKE + pgvector + CLIP + RRF; single parser `parsed`. *Done when:* text/image/voice all return ranked results <300ms p95.
      - **Step 4 — AI providers** (`backend/providers`): Whisper (voice), CLIP (image), embedding model. *Done when:* voice→text→parser; image→embedding→vector search.
      - **Step 5 — Image search** (new build). *Done when:* upload image → similar products.
      - **Step 6 — Voice search** (reuses parser). *Done when:* speak query → results.
      - **Step 7 — Faceted counts + cache + indexes.** Combined facets with counts; materialized views; GIN/btree_gin. *Done when:* filter set + counts correct; indexes used (EXPLAIN).
      - **Step 8 — Frontend wiring.** Bar → API; PLP renders; sort/filter sync to URL. *Done when:* UI reflects filters; <300ms.
      - **Step 9 — Performance guardrails.** Cursor pagination, composite indexes, EXPLAIN ANALYZE CI gate. *Done when:* hot queries <300ms, no seq scan.
    sections:
      §I: "Admin: index tuning, facet cache jobs, search analytics, video moderation."
      §II: "Customer: full discovery (text/image/voice + facets + sort), video commerce."
      §III: "Supplier: see own products in results; attribute-driven facets."
      §IV: "Logistics: n/a (discovery internal)."
      §V: "Cross-domain: consumes catalog index events (SYS_002); vectors in ai/commerce; RLS shared."
    expected:
      backend_files:
        - backend/routers/search_search_router.py
        - backend/routers/search_facet_router.py
        - backend/routers/search_autocomplete_router.py
        - backend/routers/search_image_search_router.py
        - backend/routers/search_voice_search_router.py
        - backend/controllers/search/search_controller.py
        - backend/controllers/search/facet_controller.py
        - backend/services/search/search_service.py
        - backend/services/search/hybrid_rank_service.py
        - backend/services/search/fts_service.py
        - backend/services/search/vector_search_service.py
        - backend/services/search/clip_service.py
        - backend/services/search/nlp_parser_service.py
        - backend/services/search/facet_service.py
        - backend/services/search/autocomplete_service.py
        - backend/services/search/personalization_service.py
        - backend/services/media/video_commerce_service.py
        - backend/services/search/facet_cache_service.py
        - backend/models/catalog/search_query_model.py
        - backend/models/catalog/facet_cache_model.py
        - backend/models/media/video_model.py
        - backend/models/ai/embedding_model.py
        - backend/events/search_suggest_pusher.py
        - backend/events/search_index_events.py
        - backend/jobs/search_facet_cache_worker.py
        - backend/providers/ai/whisper_provider.py
        - backend/providers/ai/clip_provider.py
        - backend/providers/ai/embedding_provider.py
        - backend/jobs/search_index_task.py
        - backend/db/schemas.py
        - backend/db/schemas.py
        - backend/alembic/versions/search_vector_initial.py
      frontend_web:
        - "frontend/web_app/src/app/search/page.tsx"
        - "frontend/web_app/src/app/(store)/layout.tsx"
        - "frontend/web_app/src/components/ui/FilterSearchBar.tsx"
        - "frontend/web_app/src/components/ui/SearchDropdown.tsx"
        - "frontend/web_app/src/components/ui/FacetPanel.tsx"
        - "frontend/web_app/src/components/ui/SortBar.tsx"
        - "frontend/web_app/src/components/ui/ImageSearchButton.tsx"
        - "frontend/web_app/src/components/ui/VoiceSearchButton.tsx"
        - "frontend/web_app/src/components/ui/Autocomplete.tsx"
        - "frontend/web_app/src/components/ui/ProductGrid.tsx"
        - "frontend/web_app/src/components/ui/VideoCommerceGrid.tsx"
        - "frontend/web_app/src/components/ui/SearchEmptyError.tsx"
        - "frontend/web_app/src/lib/search/api.ts"
        - "frontend/web_app/src/lib/search/parser.ts"
        - "frontend/web_app/src/lib/search/rrf.ts"
        - "frontend/web_app/src/hooks/useSearch.ts"
        - "frontend/web_app/src/hooks/useFacets.ts"
        - "frontend/web_app/src/hooks/useImageSearch.ts"
        - "frontend/web_app/src/hooks/useVoiceSearch.ts"
      frontend_mobile:
        - "frontend/mobile_app/app/search/index.tsx"
        - "frontend/mobile_app/app/(store)/layout.tsx"
        - "frontend/mobile_app/components/ui/ProductSearchFilterBar.tsx"
        - "frontend/mobile_app/app/search/facets.tsx"
        - "frontend/mobile_app/app/search/voice.tsx"
        - "frontend/mobile_app/app/search/image.tsx"
      tests:
        - "backend/tests/search/_test_hybrid_rank.py"
        - "backend/tests/search/_test_facets_counts.py"
        - "backend/tests/search/_test_image_search.py"
        - "backend/tests/search/_test_voice_search.py"
        - "backend/tests/search/_test_parser.py"
        - "backend/tests/search/_test_cursor_pagination.py"
        - "backend/tests/search/_test_rls_country.py"
        - "backend/tests/search/_test_perf_300ms.py"
        - "frontend/web_app/src/__tests__/components/search/_test_filter_bar.test.tsx"
        - "frontend/web_app/src/__tests__/components/search/_test_facets.test.tsx"
        - "frontend/web_app/src/__tests__/pages/search/_test_search.test.tsx"
      api_routes:
        - "GET /search"
        - "GET /search/facets"
        - "POST /search/image"
        - "POST /search/voice"
        - "GET /search/autocomplete"
        - "GET /search/suggestions"
        - "POST /search/track"
        - "GET /products"
      models:
        - "SearchQuery"
        - "FacetCache"
        - "Video"
        - "AiEmbedding"
        - "Product"
        - "ProductVariant"
        - "Category"
        - "ProductAttribute"
    diagram: |
      flowchart TB
        BAR[FilterSearchBar: text + image + voice] --> PARSE[nlp_parser: parsed brand/color/size/price/rating/sort]
        IMG[image -> CLIP] --> VEC[pgvector semantic]
        VOICE[voice -> Whisper] --> PARSE
        TXT[text -> FTS/ILIKE] --> HYB["hybrid rank (RRF)"]
        VEC --> HYB
        PARSE --> FACET[faceted filter + counts]
        FACET --> Q[(SQL: country_code + predicates)]
        Q --> RES[results <300ms p95]
        Q --> FC[facets_cache / mviews]
        RES --> VID[video commerce recommendations]

    ui_diagram: |
      flowchart TB
        subgraph WIN["WINDOW - Advanced Smart Search"]
          HD["Top bar: global search input (voice/image buttons)"]
          SB["Left: FacetPanel (categories/brands/price/attributes) - SortBar"]
          MA["Center: ProductGrid results - Autocomplete dropdown - SearchEmptyError"]
          TB["Toolbar: FilterSearchBar - ImageSearchButton - VoiceSearchButton"]
          MOD["Modality: text - image - voice - hybrid rank"]
        end
        WIN --> AI["AI: CLIP/image - Whisper/voice - vector+FTS hybrid"]
  # ===========================================================================
  - id: SYS_007   # Admin Command Center / Unified Operations Single Window
    name: Admin Command Center / Unified Operations Single Window
    weight: 8
    update_version: "v1_14-08-2026"
    scope: Admin · Country Admin - Employee
    description: |
      ## Capabilities
      - **Unified Operations Command Center (Single Window)** — the admin aggregation surface that unifies metrics, human operations, news & market intelligence, decision engine, and the Country Control Plane into one window, pulling from every domain via the **4-tier data strategy** (operational → country mart → consolidated → analytics mviews). Inherits constitutional rules: **RLS `country_code`, Alembic-only migrations, event-driven reads, RBAC on every surface, no silent fallbacks.** Strategy: **build the single-window shell + aggregation services on existing data; do not duplicate domain logic.**

      - **Access & visibility model:** role + country-scoped; global admin sees consolidated, country admin sees own country; surfaces gated by `require_permission`. Live data via WebSocket push; never stale silent zeros.

      - **Metric inventory → 4-tier data strategy:** every KPI sourced from the correct tier (real-time operational for live ops, mviews for analytics); `analytics.mv_*` materialized views refreshed by cron; composite indexes support fast rollups.

      - **Human Operations layer (active cockpit):** actionable queues (fulfillment, exceptions, approvals, anomalies, recon holds) with one-click actions that call the owning domain's API (order SYS_004, finance SYS_003, HR SYS_005, comms SYS_001). The window orchestrates, domains execute.

      - **News & Market Intelligence pipeline:** ingest news/market feeds → classify → route to relevant surfaces (country, category, supplier) with sentiment; `news_items` + `market_intelligence`.

      - **Decision Engine & monitoring:** rules + thresholds (from `configuration`) trigger alerts/escalations; anomaly detection on KPIs; escalation lifecycle (NEW→ACK→IN_PROGRESS→RESOLVED).

      - **Country Control Plane (integrated):** switch country context, view country-scoped KPIs, push country config changes (`country_configs`), manage country admins — not siloed.

      - **Automation oversight:** view/run/pause automations across domains (finance/hr/comms) with health, last-run, exception counters, DLQ.

      ## Non-negotiables
      - **Single window = orchestration**, not duplication; actions delegate to owning domain APIs.
      - **4-tier sourcing**: real-time vs mviews correctly chosen; mviews refreshed by cron.
      - **RLS `country_code`**; global vs country admin scopes enforced.
      - **Live push (WebSocket)**; explicit loading/error; no silent stale zeros.
      - **RBAC** on every surface/action.

      ## Data model
      - `analytics.mv_kpi_revenue`
      - `analytics.mv_daily_sales`
      - `analytics.mv_ops_health`
      - `admin.news_items`
      - `admin.market_intelligence`
      - `admin.decision_rules`
      - `admin.escalations`
      - `admin.control_plane_config`
      - `admin.automation_health`
      - `configuration.*` (thresholds/rules)
      - `audit.audit_logs`

      ## API
      - `GET /admin/command-center/overview` · `GET /admin/metrics` · `GET /admin/metrics/{kpi}`
      - `GET /admin/ops-queue` (fulfillment/exceptions/approvals/anomalies) · `POST /admin/ops-queue/{id}/action`
      - `GET /admin/news` · `POST /admin/news/ingest` · `GET /admin/market-intelligence`
      - `GET /admin/decision-rules` · `POST /admin/decision-rules` · `POST /admin/escalations/{id}/ack`
      - `GET /admin/country-control-plane` · `POST /admin/country-control-plane/config`
      - `GET /admin/automations/health` · `POST /admin/automations/{id}/run` · `POST /admin/automations/{id}/pause`
      - `WS /admin/command-center/stream` (live metrics/queues)

      ## State machine
      - `NEW` → `ACK` → `IN_PROGRESS` → `RESOLVED` (escalation)
      - `RAW` → `CLASSIFIED` → `ROUTED` (news/intelligence)
      - `ACTIVE` → `PAUSED` (automation)
      - `STALE` → `REFRESHED` (mview)

      ## Automations
      - **News ingest + classify:** schedule fetch → sentiment/classify → route to surfaces.
      - **KPI anomaly detection:** nightly/streaming → threshold breach → escalation.
      - **Automation health sweep:** aggregate run health across domains → alert on DLQ spike.
      - **Control-plane config push:** country config change → propagate → verify.

      ## UI/UX layout
      - **THE SINGLE WINDOW:** zone-based dashboard — top KPI strip (revenue/orders/ops health), left nav (Overview, Ops Queues, News/Intel, Decisions, Country Plane, Automations, Audit), center stage per zone, right contextual panel (live feed/escalations).
      - **Ops Queues:** split lists with one-click actions; clicking opens the owning domain screen in a drawer.
      - **News/Intel:** feed cards with sentiment + routing chips.
      - **Country Control Plane:** country switcher + scoped KPIs + config editor.
      - **Automation Tower:** per-job toggle/cron/last-run/exception counters/DLQ.
      - **UX principles:** WebSocket live updates, skeleton loaders, explicit empty/error, ARIA + keyboard, density toggle, country switcher re-sets RLS.

      ## Step-by-step
      - **Step 1 — Access & shell.** Role/country gating + single-window shell + WebSocket stream. *Done when:* admin sees only scoped data; live updates flow.
      - **Step 2 — 4-tier metrics.** KPI sources mapped to tiers; mviews + refresh cron. *Done when:* overview renders from correct tiers <300ms.
      - **Step 3 — Ops cockpit.** Queues pulling from domains + one-click delegate actions. *Done when:* action on queue calls correct domain API and reflects back.
      - **Step 4 — News/Intel.** Ingest + classify + route. *Done when:* feed shows sentiment + routing.
      - **Step 5 — Decision engine.** Rules + thresholds + escalation lifecycle. *Done when:* breach → escalation appears.
      - **Step 6 — Country Control Plane.** Switch + scoped KPIs + config push. *Done when:* country admin sees own only.
      - **Step 7 — Automation oversight.** Health/run/pause across domains. *Done when:* automation tower shows run health + DLQ.
    sections:
      §I: "Admin/Global: full single window, all countries, all queues, config, audit."
      §II: "Customer: n/a (internal admin)."
      §III: "Supplier: visible via ops queues when action needed (fulfillment)."
      §IV: "Logistics: visible via ops queues (shipments/exceptions)."
      §V: "Cross-domain: orchestrates SYS_001/003/004/005/006; reads analytics mviews; RLS shared."
    expected:
      backend_files:
        - backend/routers/admin_command_center_router.py
        - backend/routers/admin_metrics_router.py
        - backend/routers/admin_ops_queue_router.py
        - backend/routers/admin_news_router.py
        - backend/routers/admin_decision_router.py
        - backend/routers/admin_country_control_router.py
        - backend/routers/admin_automation_health_router.py
        - backend/controllers/admin/command_center_controller.py
        - backend/controllers/admin/ops_queue_controller.py
        - backend/controllers/admin/news_controller.py
        - backend/controllers/admin/decision_controller.py
        - backend/services/admin/metrics_aggregation_service.py
        - backend/services/admin/ops_queue_service.py
        - backend/services/admin/news_intelligence_service.py
        - backend/services/admin/decision_engine_service.py
        - backend/services/admin/country_control_service.py
        - backend/services/admin/automation_health_service.py
        - backend/services/admin/mview_refresh_service.py
        - backend/models/core/news_model.py
        - backend/models/core/market_intel_model.py
        - backend/models/core/decision_rule_model.py
        - backend/models/core/escalation_model.py
        - backend/models/core/control_plane_model.py
        - backend/models/core/automation_health_model.py
        - backend/events/admin_command_center_stream.py
        - backend/events/admin_events.py
        - backend/jobs/admin_mview_refresh_worker.py
        - backend/jobs/admin_news_ingest_worker.py
        - backend/providers/news/news_provider.py
        - backend/jobs/admin_decision_task.py
        - backend/db/schemas.py
        - backend/db/schemas.py
        - backend/alembic/versions/admin_command_center_initial.py
      frontend_web:
        - "frontend/web_app/src/app/admin/command-center/layout.tsx"
        - "frontend/web_app/src/app/admin/command-center/overview/page.tsx"
        - "frontend/web_app/src/app/admin/command-center/ops-queues/page.tsx"
        - "frontend/web_app/src/app/admin/command-center/news-intel/page.tsx"
        - "frontend/web_app/src/app/admin/command-center/decisions/page.tsx"
        - "frontend/web_app/src/app/admin/command-center/country-plane/page.tsx"
        - "frontend/web_app/src/app/admin/command-center/automations/page.tsx"
        - "frontend/web_app/src/components/admin/SingleWindow.tsx"
        - "frontend/web_app/src/components/admin/KpiStrip.tsx"
        - "frontend/web_app/src/components/admin/OpsQueueList.tsx"
        - "frontend/web_app/src/components/admin/NewsIntelFeed.tsx"
        - "frontend/web_app/src/components/admin/EscalationBoard.tsx"
        - "frontend/web_app/src/components/admin/CountryControlPlane.tsx"
        - "frontend/web_app/src/components/admin/AutomationHealthTower.tsx"
        - "frontend/web_app/src/lib/admin/metrics.ts"
        - "frontend/web_app/src/lib/admin/stream.ts"
        - "frontend/web_app/src/hooks/useCommandCenter.ts"
        - "frontend/web_app/src/hooks/useOpsQueues.ts"
        - "frontend/web_app/src/hooks/useNewsIntel.ts"
      frontend_mobile:
        - "frontend/mobile_app/app/admin/command-center.tsx"
        - "frontend/mobile_app/app/admin/ops-queues.tsx"
        - "frontend/mobile_app/app/admin/news-intel.tsx"
      tests:
        - "backend/tests/admin/_test_metrics_aggregation.py"
        - "backend/tests/admin/_test_ops_queue.py"
        - "backend/tests/admin/_test_news_intel.py"
        - "backend/tests/admin/_test_decision_engine.py"
        - "backend/tests/admin/_test_country_control.py"
        - "backend/tests/admin/_test_rls_country.py"
        - "frontend/web_app/src/__tests__/components/admin/_test_single_window.test.tsx"
        - "frontend/web_app/src/__tests__/components/admin/_test_ops_queue.test.tsx"
        - "frontend/web_app/src/__tests__/pages/admin/command-center/_test_overview.test.tsx"
      api_routes:
        - "GET /admin/command-center/overview"
        - "GET /admin/metrics"
        - "GET /admin/metrics/{kpi}"
        - "GET /admin/ops-queue"
        - "POST /admin/ops-queue/{id}/action"
        - "GET /admin/news"
        - "POST /admin/news/ingest"
        - "GET /admin/market-intelligence"
        - "GET /admin/decision-rules"
        - "POST /admin/decision-rules"
        - "POST /admin/escalations/{id}/ack"
        - "GET /admin/country-control-plane"
        - "POST /admin/country-control-plane/config"
        - "GET /admin/automations/health"
        - "POST /admin/automations/{id}/run"
        - "POST /admin/automations/{id}/pause"
      models:
        - "NewsItem"
        - "MarketIntelligence"
        - "DecisionRule"
        - "Escalation"
        - "ControlPlaneConfig"
        - "AutomationHealth"
        - "MvKpiRevenue"
        - "MvDailySales"
        - "MvOpsHealth"
    diagram: |
      flowchart TB
        WIN["Single Window shell + WebSocket stream"]
        WIN --> METRICS["metrics aggregation (4-tier: operational + mv_*)"]
        WIN --> Q[ops queues -> delegate to domains]
        Q --> D1[(SYS_004 orders)] & D2[(SYS_003 finance)] & D3[(SYS_005 hr)] & D4[(SYS_001 comms)]
        WIN --> NEWS["news/intel ingest + classify + route"]
        WIN --> DEC[decision engine -> escalations]
        WIN --> CCP[country control plane]
        WIN --> AH[automation health across domains]
        METRICS --> MV[("analytics mviews (cron refresh)")]

    ui_diagram: |
      flowchart TB
        subgraph WIN["WINDOW - Admin Command Center (Single Window)"]
          HD["Top bar: SingleWindow - country control plane - notifications"]
          KS["KPI strip: per-domain health (catalog/finance/hr/comms/search)"]
          Q["Queues: OpsQueueList - EscalationBoard - decision board"]
          MA["Center: OrderOpsCockpit - AutomationTower - CountryControlPlane - NewsIntelFeed"]
          AC["Actionable: one-click approve/resolve -> owning domain API"]
        end
        WIN --> ETL["Reads analytics mviews - orchestrates SYS_001/004/005/006"]
  # ===========================================================================
  - id: SYS_008   # Country Page & Country Adding System
    name: Country Page & Country Adding System
    weight: 7
    update_version: "v1_14-08-2026"
    scope: Admin · Country Admin - Customer
    description: |
      ## Capabilities
      - **Country Page & Country Adding System** — the `country` bounded context for onboarding new countries with a complete research data framework (20 modules × 200+ data points) and reflecting that data into the operational system via `country_configs`, plus a public Country Page. Inherits constitutional rules: **100% of country-scoped tables MUST have `country_code` + RLS, Alembic-only migrations, event-driven propagation, config-as-data, no silent fallbacks.** Strategy: **build the country research framework + config propagation + country page; do not rebuild domain logic.**

      - **Country research data framework (20 modules):** Identity & basics, Demographics, Economy & wealth, Tax system & duties, Consumer psychology, Consumption preferences, Shopping seasonality, Digital landscape & internet, Payment infrastructure, Logistics & shipping, Legal/rules/regulations, Language & communication, Community & social, Marketing & advertising, Competition & market, Customer service expectations, Technology & infrastructure, News & current context, Risk & compliance matrix, Strategic recommendations. Stored as structured JSON in `country.country_profiles` + normalized tables (`country.tax_rules`, `country_holiday_calendars`, `country_currencies`, `country_logistics_zones`, `country_legal_rules`).

      - **Country adding workflow:** Admin triggers "Add Country" → research intake (manual + AI-assisted) → validation against framework → create `country.countries` + seed `country_configs` (currency, tax, holidays, labor law, logistics zones, payment methods, language, legal) → propagate to `core`/`commerce`/`hr`/`logistics`/`finance` config → RLS registry entry. Each step has SLA + approval.

      - **Config propagation:** `country_configs` is the single source for country-scoped business rules consumed by finance (tax/VAT/EOSB), HR (leave/holidays/labor), logistics (zones/charges), catalog (currency/availability). Changes emit events; dependent domains re-read on access (RLS `app.current_country_code`).

      - **Public Country Page:** SEO-friendly page per country showing available categories, currency, shipping, payment methods, holidays, localized content (RTL/i18n). Customer switches country → RLS re-set → catalog/pricing/logistics scoped.

      - **Country isolation by default:** login sets `SET app.current_country_code`; RLS policies return 0 rows cross-country (fail-closed); only `global/admin` see consolidated.

      ## Non-negotiables
      - **Every country-scoped table has `country_code` + RLS**; cross-country reads return 0 rows.
      - **Full 20-module research framework** captured before a country goes live.
      - **`country_configs` = single source** for country rules; propagated, not hardcoded.
      - **Add-country is a guarded, approved workflow**; partial config blocks go-live.
      - **No silent fallbacks** (fail loud if config missing).

      ## Data model (`country` schema)
      - `country.countries`
      - `country.country_profiles` (JSON framework)
      - `country.country_configs` (operational rules)
      - `country.country_currencies`
      - `country.tax_rules`
      - `country.country_holiday_calendars`
      - `country.country_logistics_zones`
      - `country.country_legal_rules`
      - `country.country_payment_methods`
      - `country.country_languages`
      - `country.country_risk_matrix`
      - `country.country_onboarding_tasks`
      - `audit.audit_logs`

      ## API
      - `GET /countries` · `POST /countries` (add) · `GET /countries/{code}` · `PATCH /countries/{code}` · `DELETE /countries/{code}`
      - `GET /countries/{code}/profile` · `POST /countries/{code}/profile` (research intake) · `POST /countries/{code}/profile/validate`
      - `GET /countries/{code}/config` · `PATCH /countries/{code}/config`
      - `POST /countries/{code}/onboard` (run workflow) · `GET /countries/{code}/onboarding-status`
      - `GET /country-page/{code}` (public SEO page)
      - `POST /country/switch` (sets RLS context)
      - `GET /countries/{code}/holidays` · `GET /countries/{code}/tax` · `GET /countries/{code}/logistics-zones` · `GET /countries/{code}/payments`

      ## State machine
      - `DRAFT` → `RESEARCHING` → `VALIDATED` → `CONFIGURED` → `PROPAGATED` → `LIVE` (country onboarding)
      - `ACTIVE` → `SUSPENDED` → `ARCHIVED` (country lifecycle)
      - `PENDING` → `APPROVED` → `PROPAGATED` (config change)

      ## Automations
      - **Research intake assist:** AI drafts 20-module profile from web + prior data; human verifies.
      - **Config propagation:** on `country_configs` change → emit events → dependent domains re-cache.
      - **Onboarding SLA monitor:** stalled step → escalate to country admin.
      - **Risk/compliance sync:** `country_risk_matrix` updates → flag high-risk before go-live.

      ## UI/UX layout
      - **Country Admin console:** list + Add Country wizard (stepped: research → validate → configure → propagate → go-live), profile editor (20 modules), config editor, onboarding-status tracker, public page preview.
      - **Public Country Page:** hero + localized categories + currency/shipping/payment/holidays + RTL/i18n + SEO.
      - **Country switcher (global):** re-sets RLS everywhere.
      - **UX principles:** skeleton loaders, explicit validation errors, ARIA + keyboard, density toggle, RTL support.

      ## Step-by-step
      - **Step 1 — Research framework.** `country_profiles` JSON + normalized tables for 20 modules. *Done when:* all modules captured per country.
      - **Step 2 — Add Country wizard.** Draft → research → validate → configure. *Done when:* validation passes; config seeded.
      - **Step 3 — Config propagation.** Seed `country_configs` → propagate to domains → RLS registry. *Done when:* finance/HR/logistics read correct country rules.
      - **Step 4 — Country Page.** Public SEO page + switcher. *Done when:* page renders localized; switch re-sets RLS.
      - **Step 5 — Go-live gating.** Partial config blocks LIVE. *Done when:* only fully-configured countries go LIVE.
    sections:
      §I: "Admin/Country Admin: add/config countries, research, propagation, page mgmt."
      §II: "Customer: country switcher, localized Country Page, scoped catalog."
      §III: "Supplier: sees country-scoped selling config."
      §IV: "Logistics: country logistics zones/charges reflected."
      §V: "Cross-domain: country_configs feed finance/HR/logistics/catalog; RLS shared everywhere."
    expected:
      backend_files:
        - backend/routers/country_country_router.py
        - backend/routers/country_profile_router.py
        - backend/routers/country_config_router.py
        - backend/routers/country_onboarding_router.py
        - backend/routers/country_country_page_router.py
        - backend/controllers/geography/country_controller.py
        - backend/controllers/geography/profile_controller.py
        - backend/controllers/geography/onboarding_controller.py
        - backend/services/country/country_service.py
        - backend/services/country/profile_service.py
        - backend/services/country/config_propagation_service.py
        - backend/services/country/onboarding_service.py
        - backend/services/country/country_page_service.py
        - backend/services/country/research_assist_service.py
        - backend/models/geography/country_model.py
        - backend/models/geography/profile_model.py
        - backend/models/geography/config_model.py
        - backend/models/geography/tax_rule_model.py
        - backend/models/geography/holiday_calendar_model.py
        - backend/models/geography/logistics_zone_model.py
        - backend/models/geography/legal_rule_model.py
        - backend/models/geography/payment_method_model.py
        - backend/models/geography/language_model.py
        - backend/models/geography/risk_matrix_model.py
        - backend/models/geography/onboarding_task_model.py
        - backend/db/migrations/pg_rls_policies.sql
        - backend/events/country_events.py
        - backend/jobs/country_onboarding_worker.py
        - backend/providers/analytics/country_research_provider.py
        - backend/jobs/country_config_propagation_task.py
        - backend/db/schemas.py
        - backend/db/schemas.py
        - backend/db/schemas.py
        - backend/alembic/versions/country_initial.py
      frontend_web:
        - "frontend/web_app/src/app/admin/countries/page.tsx"
        - "frontend/web_app/src/app/admin/countries/add/page.tsx"
        - "frontend/web_app/src/app/admin/countries/[code]/profile/page.tsx"
        - "frontend/web_app/src/app/admin/countries/[code]/config/page.tsx"
        - "frontend/web_app/src/app/admin/countries/[code]/onboarding/page.tsx"
        - "frontend/web_app/src/app/country/[code]/page.tsx"
        - "frontend/web_app/src/components/country/AddCountryWizard.tsx"
        - "frontend/web_app/src/components/country/CountryProfileEditor.tsx"
        - "frontend/web_app/src/components/country/CountryConfigEditor.tsx"
        - "frontend/web_app/src/components/country/OnboardingStatusTracker.tsx"
        - "frontend/web_app/src/components/country/CountryPageView.tsx"
        - "frontend/web_app/src/components/country/CountrySwitcher.tsx"
        - "frontend/web_app/src/lib/country/countries.ts"
        - "frontend/web_app/src/lib/country/config.ts"
        - "frontend/web_app/src/hooks/useCountries.ts"
        - "frontend/web_app/src/hooks/useCountryConfig.ts"
        - "frontend/web_app/src/hooks/useCountrySwitch.ts"
      frontend_mobile:
        - "frontend/mobile_app/app/country/[code].tsx"
        - "frontend/mobile_app/app/country/switch.tsx"
        - "frontend/mobile_app/app/admin/countries.tsx"
      tests:
        - "backend/tests/country/_test_country_crud.py"
        - "backend/tests/country/_test_profile_framework.py"
        - "backend/tests/country/_test_config_propagation.py"
        - "backend/tests/country/_test_onboarding_workflow.py"
        - "backend/tests/country/_test_rls_country.py"
        - "frontend/web_app/src/__tests__/components/country/_test_add_wizard.test.tsx"
        - "frontend/web_app/src/__tests__/components/country/_test_country_page.test.tsx"
        - "frontend/web_app/src/__tests__/pages/admin/countries/_test_country_admin.test.tsx"
      api_routes:
        - "GET /countries"
        - "POST /countries"
        - "GET /countries/{code}"
        - "PATCH /countries/{code}"
        - "DELETE /countries/{code}"
        - "GET /countries/{code}/profile"
        - "POST /countries/{code}/profile"
        - "POST /countries/{code}/profile/validate"
        - "GET /countries/{code}/config"
        - "PATCH /countries/{code}/config"
        - "POST /countries/{code}/onboard"
        - "GET /countries/{code}/onboarding-status"
        - "GET /country-page/{code}"
        - "POST /country/switch"
        - "GET /countries/{code}/holidays"
        - "GET /countries/{code}/tax"
        - "GET /countries/{code}/logistics-zones"
        - "GET /countries/{code}/payments"
      models:
        - "Country"
        - "CountryProfile"
        - "CountryConfig"
        - "TaxRule"
        - "CountryHolidayCalendar"
        - "CountryLogisticsZone"
        - "CountryLegalRule"
        - "CountryPaymentMethod"
        - "CountryLanguage"
        - "CountryRiskMatrix"
        - "CountryOnboardingTask"
    diagram: |
      flowchart TB
        ADD["Add Country wizard"] --> RESEARCH["research intake (20 modules)"]
        RESEARCH --> VAL[validate] --> CFG[seed country_configs]
        CFG --> PROP["config propagation -> finance/HR/logistics/catalog"]
        PROP --> RLS[(RLS registry: app.current_country_code)]
        RLS --> PAGE[public Country Page + switcher]
        CFG --> LIVE[country LIVE]
        PAGE --> CUST[customer scoped catalog/pricing]

    ui_diagram: |
      flowchart TB
        subgraph WIN["WINDOW - Country Page & Adding"]
          HD["Public: CountryPageView (storefront localized)"]
          WZ["AddCountryWizard: step form (profile - config - legal - tax - payment)"]
          ED["Editors: CountryProfileEditor - CountryConfigEditor - OnboardingStatusTracker"]
          SB["Right: CountrySwitcher - RLS country_code scope indicator"]
        end
        WIN --> PROP["Config propagation -> all domains (RLS)"]
  # ===========================================================================
  - id: SYS_009   # AI Provider System
    name: AI Provider System
    weight: 8
    update_version: "v1_14-08-2026"
    scope: Admin · System - Employee - Customer
    description: |
      ## Capabilities
      - **AI Provider System** — the provider-abstraction + model-registry layer that every AI feature consumes (chat/email transcription & translation in SYS_001, hybrid search/image/voice in SYS_006, catalog embedding in SYS_002, HR chatbot). Inherits constitutional rules: **AI NEVER writes directly to business tables (staging→commit only), config-as-data for model selection, Alembic-only, no silent fallbacks.** Strategy: **build the provider gateway + registry + routing; wire existing callers through it.**

      - **Provider abstraction:** uniform interface over LLM (local Ollama `phi3:mini`/`qwen2.5`/`moondream`, plus optional cloud), embedding models (`vector(1536)`), speech (Whisper), vision (CLIP). `backend/providers/ai/` pluggable; switch provider without touching callers.

      - **Local-first, cost-aware:** default to local Ollama to save VPS cost; **vision OFF by default** (toggle in `configuration`); cloud fallback only when configured. Model registry in `ai.model_registry` with capability tags (chat/embed/transcribe/vision) + cost per 1K tokens.

      - **Routing & fallback:** request → capability match → primary provider → on failure fallback chain; explicit error (no silent degrade). `ai.provider_routes` + health checks.

      - **Vectorization service:** `ai.ai_embeddings` (`embedding vector(1536)`, HNSW index) for products/AI assets; hybrid search = FTS + pgvector + CLIP (used by SYS_006). `ai.ai_upload_jobs` → `ai.ai_staging_*` → explicit commit → business tables (never direct).

      - **Cost & usage tracking:** every AI call logged to `ai.ai_requests` / `ai.ai_usage_logs` with tokens + cost; budgets/alerts in `configuration`; dashboards from `analytics.mv_*`.

      - **Safety & governance:** PII masking before send, output redaction, rate limits, content policy; "cannot verify" mode for low-confidence (HR chatbot SYS_005/SYS_001).

      ## Non-negotiables
      - **Provider abstraction**: callers depend on the gateway, not a specific provider.
      - **Local-first, vision off by default**; cloud fallback only when configured.
      - **AI staged→committed**: no direct AI writes to business tables.
      - **Cost + usage tracked** per request; budgets enforce.
      - **No silent fallback**: failure → explicit error + DLQ.
      - **PII masking** before any external provider call.

      ## Data model (`ai` schema)
      - `ai.model_registry`
      - `ai.provider_routes`
      - `ai.provider_health`
      - `ai.ai_requests`
      - `ai.ai_usage_logs`
      - `ai.ai_embeddings` (`vector(1536)`, HNSW)
      - `ai.ai_upload_jobs`
      - `ai.ai_staging_products`
      - `ai.ai_staging_assets`
      - `configuration.ai_settings`
      - `audit.audit_logs`

      ## API
      - `GET /ai/models` · `POST /ai/models` · `PATCH /ai/models/{id}` (toggle vision/cost)
      - `POST /ai/complete` (chat/completion) · `POST /ai/embed` · `POST /ai/transcribe` (Whisper) · `POST /ai/vision` (CLIP)
      - `GET /ai/routes` · `POST /ai/routes` · `POST /ai/routes/{id}/health`
      - `GET /ai/usage` · `GET /ai/usage/cost-report`
      - `GET /ai/staging/{job_id}` · `POST /ai/staging/{job_id}/commit` · `POST /ai/staging/{job_id}/reject`
      - `POST /ai/settings` (vision toggle, budgets)

      ## State machine
      - `IDLE` → `RUNNING` → `SUCCESS` / `FAILED` (AI request)
      - `PENDING` → `COMMITTED` / `REJECTED` (staging)
      - `HEALTHY` → `DEGRADED` → `DOWN` (provider)
      - `ENABLED` → `DISABLED` (model/vision)

      ## Automations
      - **Provider health sweep:** ping providers → update `provider_health` → reroute on DOWN.
      - **Cost budget alert:** usage vs budget → notify admin; throttle on breach.
      - **Staging→commit pipeline:** upload job → stage → human/auto commit → business table.
      - **Vision auto-toggle:** load-based enable/disable per config.

      ## UI/UX layout
      - **AI Admin console:** model registry (capability/cost/vision toggle), provider routes + health, usage/cost dashboard, staging review queue (commit/reject), settings (budgets, vision default-off).
      - **UX principles:** explicit provider status, cost visibility, skeleton loaders, ARIA + keyboard.

      ## Step-by-step
      - **Step 1 — Provider gateway.** `backend/providers/ai/` abstraction + registry. *Done when:* swap provider without caller change.
      - **Step 2 — Local-first + vision off.** Ollama default; vision toggle in config. *Done when:* local runs; vision off until enabled.
      - **Step 3 — Routing & fallback.** Capability match + fallback chain + health. *Done when:* primary down → fallback; failure explicit.
      - **Step 4 — Vectorization.** `ai_embeddings` (1536) + HNSW; staging→commit. *Done when:* product embed + hybrid search works; no direct writes.
      - **Step 5 — Cost & usage.** Log tokens/cost; budgets/alerts. *Done when:* cost report accurate; throttle on breach.
      - **Step 6 — Governance.** PII mask + rate limit + "cannot verify". *Done when:* PII never leaks to external provider.
    sections:
      §I: "Admin/System: model registry, routes, health, cost, staging review, settings."
      §II: "Customer: consumes AI via search/voice/image (SYS_006) transparently."
      §III: "Supplier: catalog embedding via staging (SYS_002)."
      §IV: "Logistics: n/a (AI infra)."
      §V: "Cross-domain: powers SYS_001 (transcription/translation), SYS_006 (search/image/voice), SYS_002 (catalog embed), SYS_005 (chatbot)."
    expected:
      backend_files:
        - backend/routers/ai_model_router.py
        - backend/routers/ai_provider_router.py
        - backend/routers/ai_usage_router.py
        - backend/routers/ai_staging_router.py
        - backend/routers/ai_settings_router.py
        - backend/controllers/ai/ai_controller.py
        - backend/controllers/ai/staging_controller.py
        - backend/services/ai/provider_gateway_service.py
        - backend/services/ai/routing_service.py
        - backend/services/ai/embedding_service.py
        - backend/services/ai/transcription_service.py
        - backend/services/ai/vision_service.py
        - backend/services/ai/usage_tracking_service.py
        - backend/services/ai/staging_commit_service.py
        - backend/services/ai/safety_service.py
        - backend/models/ai/model_registry_model.py
        - backend/models/ai/provider_route_model.py
        - backend/models/ai/provider_health_model.py
        - backend/models/ai/usage_log_model.py
        - backend/models/ai/embedding_model.py
        - backend/models/ai/upload_job_model.py
        - backend/models/ai/staging_model.py
        - backend/providers/ai/base_provider.py
        - backend/providers/ai/ollama_provider.py
        - backend/providers/ai/cloud_llm_provider.py
        - backend/providers/ai/whisper_provider.py
        - backend/providers/ai/clip_provider.py
        - backend/providers/ai/embedding_provider.py
        - backend/events/ai_events.py
        - backend/jobs/ai_provider_health_worker.py
        - backend/jobs/ai_staging_commit_worker.py
        - backend/jobs/ai_embedding_task.py
        - backend/db/schemas.py
        - backend/db/schemas.py
        - backend/alembic/versions/ai_initial.py
      frontend_web:
        - "frontend/web_app/src/app/admin/ai/models/page.tsx"
        - "frontend/web_app/src/app/admin/ai/routes/page.tsx"
        - "frontend/web_app/src/app/admin/ai/usage/page.tsx"
        - "frontend/web_app/src/app/admin/ai/staging/page.tsx"
        - "frontend/web_app/src/app/admin/ai/settings/page.tsx"
        - "frontend/web_app/src/components/admin/ModelRegistry.tsx"
        - "frontend/web_app/src/components/admin/ProviderRoutes.tsx"
        - "frontend/web_app/src/components/admin/UsageCostDashboard.tsx"
        - "frontend/web_app/src/components/admin/StagingReviewQueue.tsx"
        - "frontend/web_app/src/components/admin/AiSettings.tsx"
        - "frontend/web_app/src/lib/ai/provider.ts"
        - "frontend/web_app/src/hooks/useAiModels.ts"
        - "frontend/web_app/src/hooks/useAiUsage.ts"
      frontend_mobile:
        - "frontend/mobile_app/app/admin/ai/usage.tsx"
        - "frontend/mobile_app/app/admin/ai/models.tsx"
      tests:
        - "backend/tests/ai/_test_provider_gateway.py"
        - "backend/tests/ai/_test_routing_fallback.py"
        - "backend/tests/ai/_test_embedding.py"
        - "backend/tests/ai/_test_transcription.py"
        - "backend/tests/ai/_test_staging_commit.py"
        - "backend/tests/ai/_test_cost_tracking.py"
        - "backend/tests/ai/_test_pii_masking.py"
        - "frontend/web_app/src/__tests__/components/ai/_test_model_registry.test.tsx"
        - "frontend/web_app/src/__tests__/pages/admin/ai/_test_ai_admin.test.tsx"
      api_routes:
        - "GET /ai/models"
        - "POST /ai/models"
        - "PATCH /ai/models/{id}"
        - "POST /ai/complete"
        - "POST /ai/embed"
        - "POST /ai/transcribe"
        - "POST /ai/vision"
        - "GET /ai/routes"
        - "POST /ai/routes"
        - "POST /ai/routes/{id}/health"
        - "GET /ai/usage"
        - "GET /ai/usage/cost-report"
        - "GET /ai/staging/{job_id}"
        - "POST /ai/staging/{job_id}/commit"
        - "POST /ai/staging/{job_id}/reject"
        - "POST /ai/settings"
      models:
        - "ModelRegistry"
        - "ProviderRoute"
        - "ProviderHealth"
        - "AiRequest"
        - "AiUsageLog"
        - "AiEmbedding"
        - "AiUploadJob"
        - "AiStagingProduct"
        - "AiStagingAsset"
    diagram: |
      flowchart TB
        CALL[callers: SYS_001/002/005/006] --> GW[provider gateway]
        GW --> RT["routing: capability match + fallback"]
        RT --> OLL[Ollama local: phi3/qwen/moondream]
        RT --> CLD[cloud LLM]
        RT --> WH[Whisper transcribe]
        RT --> CLIP[CLIP vision]
        GW --> EMB[ai_embeddings vector(1536) HNSW]
        GW --> USE[ai_usage_logs + cost]
        GW --> SAFE[PII mask + rate limit]
        GW --> STG[ai_staging -> commit -> business]
        USE --> BUD[configuration budgets]

    ui_diagram: |
      flowchart TB
        subgraph WIN["WINDOW - AI Provider System (admin)"]
          HD["Top bar: model registry nav - provider routes - usage"]
          NV["Left: Models - Providers - Staging review - Settings - Usage cost"]
          MA["Center: ModelRegistry - ProviderRoutes - StagingReviewQueue - UsageCostDashboard"]
          SB["Right: AutomationHealthTower - provider health"]
          CFG["Config-as-data: model selection - routing - safety"]
        end
        WIN --> GW["provider gateway -> callers SYS_001/002/005/006"]
  # ===========================================================================
  - id: SYS_010   # Supplier Product Upload System
    name: Supplier Product Upload
    weight: 8
    update_version: "v1_14-08-2026"
    scope: Supplier · Admin
    description: |
      ## Capabilities:
      - Supplier Product Upload — a rich, modal-popup-driven, automation-first authoring flow at `/supplier/products/add` for capturing products with images + video, then publishing through AI-assisted verification. Target: a full upload (BG removal + AI analysis + all variant quantity fills + publish) **in under 30 seconds** for an experienced supplier.
      - Two parallel processes: **Process A — Photo-First** (upload → BG removal → AI detect/auto-fill) and **Process B — Voice-First** (upload → BG removal → 🎤 voice note → NLP parse → auto-fill). Both converge on the same quantity + verify steps.
      - Capture/upload media (images + video) via `UploadModal` (file picker / `capture="environment"` camera / drag-and-drop); voice detail entry (`VoiceModal`) and Magic Photo Editing (`PhotoEditModal`) for cleanup.
      - AI auto-fill of `name` / `description` / `tags` / `category` / `colors` / `price_suggestion` from media through `AIResultsModal`; per-color×size quantity popups (`QuantityModal`) with auto total quantity and a "Fill All = 50" shortcut; price popup pre-filled by AI.
      - Universal variant support driven by `zozi_variant_config.json` (apparel color/size, electronics storage/RAM, beauty volume/scent, jewelry karat/plating) via `variantEngine.ts` `getVariantAxesForCategory()` and `variantConfig.ts`.
      - Verify gate `VerifyPublishModal` with Edit Details / Edit Images / Publish before publish; AI suggestions (incl. background removal via **SYS_009** `br05`–`br13`, CLIP auto-tag) staged into `ai_staging_products` and held for human review — **no auto-publish**.
      - Upload orchestration through `src/lib/uploadOrchestrator.ts` (`UploadPhase` state machine: `idle|media|processing|photo_edit|ai_results|quantity|verify|done`); fires parallel `Promise.all([removeBg(), analyzeImage()])` at end of Step 1; caches results; tracks current color index; computes `totalStock` reactively. Voice NLP also wired to **SYS_001** comms/proxy for transcription.

      ## Non-negotiables:
      - **AI assist with human review** (no auto-publish — `ai_staging_products` requires review before commit to `products`)
      - **per-color×size quantity** with auto total (`QuantityModal` loops colors, only relevant sizes shown)
      - **verify gate before publish** (Edit Details / Edit Images / Publish in `VerifyPublishModal`)
      - **media to object storage** (refs in `media_assets`, no blobs)
      - **explicit validation errors** on missing required fields (`REJECTED` on invalid payload)
      - **parallel BG removal + AI analyze** to meet the ≤30s speed budget
      - **universal variant matrix** from `zozi_variant_config.json` (no hardcoded axes)

      ## Data model
      - `catalog.products`
      - `catalog.product_variants`
      - `catalog.product_upload_sessions`
      - `catalog.filter_attributes`
      - `catalog.embedding`
      - `ai_staging_products`
      - `media.media_assets`

      ## API
      - `/supplier/products/add`
      - `/supplier/products/upload-media`
      - `/supplier/products/ai-fill`
      - `/supplier/products/verify`
      - `/supplier/products`
      - `/supplier/upload/remove-background` (BG removal, **SYS_009** `br05`–`br13`)
      - `/supplier/upload/ai-analyze`
      - `/supplier/upload/voice-transcribe`
      - `/supplier/upload/analyze-parallel` (POST, `asyncio.gather` BG + AI, returns combined JSON)
      - `/supplier/upload/variant-axes` (GET, `category`+`subcategory` → axes + default options)

      ## State machine
      - `DRAFT` -> `MEDIA_UPLOADED`
      - `MEDIA_UPLOADED` -> `AI_FILLED`
      - `AI_FILLED` -> `VERIFYING`
      - `VERIFYING` -> `PUBLISHED`
      - `VERIFYING` -> `REJECTED`
      - `BULK_UPLOAD` -> `DRAFT` (batch ingest via **SYS_002** bulk pipeline)

      ## Step-by-step
      - **Step 1 — Capture & media.** `UploadModal` uploads images+video; `uploadOrchestrator.ts` streams bytes to object storage; refs stored in `media_assets`. On Next, fires parallel `removeBg()` + `analyzeImage()`. *Done when:* media present and processing kicked off before quantity step.
      - **Step 2 — Variants & quantity.** `variantEngine.ts` reads `zozi_variant_config.json` to render axes; `QuantityModal` loops per color×size with auto total qty and "Fill All = 50"; price popup pre-filled by `price_suggestion`. *Done when:* `totalStock` equals sum of cells across all colors.
      - **Step 3 — Voice & photo edit.** `VoiceModal` records note → NLP parse → editable chips (Process B); `PhotoEditModal` Magic Photo Editing applies `br05`–`br13` one-tap fixes. *Done when:* voice transcript fills details; edits applied and cached.
      - **Step 4 — AI auto-fill.** `AIResultsModal` shows staged `ai_staging_products` suggestions (name/tags/description/category/colors) as editable inline fields. *Done when:* suggestions reviewed/edited, not auto-applied; `AI_FILLED`.
      - **Step 5 — Verify & publish.** `VerifyPublishModal` (Edit Details re-opens AIResultsModal / Edit Images re-opens PhotoEditModal / Publish → `PUBLISHED`). *Done when:* publish blocked unless verify gate passed; product committed from `ai_staging_products` to `products` and visible in `/supplier/products` (**SYS_002**).

      ## Automations
      - **Parallel media processing:** at end of capture, `uploadOrchestrator.ts` fires `removeBg()` + `analyzeImage()` via `Promise.all` to hold the ≤30s speed budget.
      - **AI auto-fill pipeline:** media → CLIP tag + caption → staged into `ai_staging_products`; held for human review (no auto-publish).
      - **Voice NLP:** `VoiceModal` note → transcription (SYS_001 proxy / SYS_009 Whisper) → parse → editable chips (Process B).
      - **Bulk ingest:** CSV/feed → SYS_002 bulk pipeline → `DRAFT`.

      ## UI/UX layout
      - **`/supplier/products/add` page:** modal-driven flow — `UploadModal` (capture), `QuantityModal` (per color×size), `VoiceModal`, `PhotoEditModal` (Magic Edit), `AIResultsModal` (editable suggestions), `VerifyPublishModal` (publish gate).
      - **`/supplier/products` list:** published + staged products with status badges.
      - **UX principles:** explicit validation errors, skeleton loaders, ARIA + keyboard, density toggle, mobile camera (`capture="environment"`), drag-and-drop.
    sections:
      §I: "Catalog schema for variants, upload session, media wiring, seed data."
      §II: "Customer: consumes published products only."
      §III: "Supplier: full `/supplier/products/add` flow, modals, orchestrator, zozi_variant_config.json."
      §IV: "Logistics: product dimensions/weight from upload feed packaging."
      §V: "Admin: moderation/verification queue for supplier uploads."
    expected:
      backend_files:
        - backend/routers/supplier_product_upload_router.py
        - backend/controllers/supplier/product_upload_controller.py
        - backend/services/supplier/product_upload_service.py
        - backend/models/supplier/supplier_product_upload_model.py
        - backend/jobs/supplier_upload_ai_job.py
        - backend/events/catalog_events.py
        - backend/providers/ai/catalog_ai_provider.py
      frontend_web:
        - "frontend/web_app/src/components/supplier/upload/PhotoEditModal.tsx"
        - "frontend/web_app/src/components/supplier/upload/AIResultsModal.tsx"
        - "frontend/web_app/src/components/supplier/upload/QuantityModal.tsx"
        - "frontend/web_app/src/components/supplier/upload/VerifyPublishModal.tsx"
        - "frontend/web_app/src/components/supplier/upload/VoiceModal.tsx"
        - "frontend/web_app/src/lib/uploadOrchestrator.ts"
      frontend_mobile:
        - "frontend/mobile_app/app/supplier/products/add.tsx"
      tests:
        - "backend/tests/_test_supplier_product_upload.py"
        - "frontend/web_app/src/__tests__/pages/_test_supplier_product_upload.test.tsx"
      api_routes:
        - "GET /supplier/products/add"
        - "POST /supplier/products/upload-media"
        - "POST /supplier/products/ai-fill"
        - "POST /supplier/products/verify"
      models:
        - "ProductUploadSession"
        - "ProductVariant"
    diagram: |
      flowchart LR
        CAP[Capture images + video] --> MED[uploadOrchestrator -> object storage]
        MED --> VAR[fabric / color x size QuantityModal auto-total]
        VAR --> VOICE[VoiceModal details]
        VOICE --> PHOTO[PhotoEditModal Magic Edit]
        PHOTO --> AIFILL[AIResultsModal name / tags / desc]
        AIFILL --> VERIFY[VerifyPublishModal]
        VERIFY -->|publish| PUB[PUBLISHED catalog.products]

    ui_diagram: |
      flowchart TB
        subgraph WIN["WINDOW - Supplier Product Upload"]
          HD["Top bar: upload nav - supplier storefront"]
          PH["UploadPhase state machine: idle>media>processing>photo_edit>ai_results>quantity>verify>done"]
          MA["Center: PhotoEditModal - AIResultsModal - QuantityModal - VerifyPublishModal - VoiceModal"]
          SB["Right: bulk import status - publish preview"]
        end
        WIN --> AI["AI: removeBg + analyzeImage -> staged product"]
  # ===========================================================================
  - id: SYS_011   # Logistic Panel
    name: Logistic Panel
    weight: 8
    update_version: "v1_14-08-2026"
    scope: Logistor · Admin
    description: |
      ## Capabilities:
      - Logistic Panel — the `/logistics-partner/` operations surface for managing **cities, countries and delivery charges** that reflect into cart and order pricing in real time.
      - **Charges & cart reflection:** per-route `delivery_charges` (draft → live) recompute cart total and order shipping cost immediately on publish; no stale pricing.
      - **Coverage & GPS:** `service_cities` + `partner_coverage` with GPS/geo linkage for coverage validation (out-of-area addresses are rejected with an **explicit coverage error**) and last-mile routing.
      - **Partner profile & approval:** `logistics_partners` is hidden until **admin approval** of the profile and any charge changes before they go live (Maker-Checker for critical edits).
      - **Handover contract:** integrates with order-management pick-up/delivery (SYS_004) — flashing pick-up board, claim, QR-scan/confirm handover, transit sub-statuses; reads `ORDER_MANAGEMENT.md` supplier flow for the handover contract.
      - **COD remittance** reconciles into the finance ledger (SYS_003 / SYS_004): collected cash → `finance.bank_transactions` / `transaction_ledger` with zero-variance nightly reconciliation.
      - **Monitoring:** partner health, SLA and remittance dashboards; suspension stops new order assignment.
      - **Profile page:** cities + countries + charges management surfaced as a unified profile; changes reflected to customer order and cart system.

      ## Non-negotiables:
      - **charge changes reflected to cart/order** immediately on publish
      - **admin approval** before partner profile/charges go live (Maker-Checker for critical)
      - **GPS/location linkage** for coverage validation and routing
      - **COD remittance into ledger** (never ad-hoc) with zero-variance reconciliation
      - **explicit coverage error** when an address is outside service area
      - **suspended partner stops receiving orders** without data loss

      ## Data model
      - `logistics.logistics_partners`
      - `logistics.service_cities`
      - `logistics.delivery_charges`
      - `logistics.partner_coverage`
      - `logistics.partner_vehicles`
      - `logistics.partner_sla_alerts`
      - `finance.bank_transactions`
      - `finance.transaction_ledger`

      ## API
      - `GET /logistics-partner/cities`
      - `GET /logistics-partner/charges`
      - `GET /logistics-partner/profile`
      - `POST /logistics-partner/charges`        (draft)
      - `POST /logistics-partner/charges/{id}/publish`
      - `POST /admin/logistics-partners/{partner_id}/approve`
      - `POST /admin/logistics-partners/{partner_id}/suspend`

      ## State machine
      - `PENDING_APPROVAL` -> `APPROVED`
      - `APPROVED` -> `ACTIVE`
      - `ACTIVE` -> `SUSPENDED`
      - `CHARGE_DRAFT` -> `CHARGE_LIVE`
      - `CHARGE_LIVE` -> `CHARGE_DRAFT`        (edit → re-draft)
      - `OUT_FOR_DELIVERY` -> `DELIVERED`       (via SYS_004 handover)

      ## Step-by-step
      - **Step 1 — Partner profile.** `logistics_partners` + admin approval workflow (Maker-Checker). *Done when:* profile hidden until approved; suspension stops new orders.
      - **Step 2 — Cities & coverage.** `service_cities` + `partner_coverage` + `partner_vehicles` with GPS linkage; `partner_sla_alerts`. *Done when:* out-of-coverage address rejected explicitly.
      - **Step 3 — Charges & cart reflect.** `delivery_charges` draft → publish (live); cart/order recompute on publish. *Done when:* changing charge updates cart total in test; edits re-draft.
      - **Step 4 — Handover contract.** Integrate with order-management pick-up/delivery (SYS_004): flashing board, claim, QR-scan/confirm, transit sub-statuses. *Done when:* handover paths produce audited shipment events.
      - **Step 5 — COD remittance & monitoring.** Collected COD → `finance.bank_transactions` / `transaction_ledger`; nightly zero-variance reconciliation (SYS_003). Partner health/SLA/remittance dashboards. *Done when:* COD run reconciles to treasury with zero variance.

      ## Automations
      - **Charge publish reflection:** on `delivery_charges` publish → recompute active cart/order shipping totals (event to commerce/cart).
      - **Coverage validation:** address GPS → `partner_coverage` check → explicit out-of-area error at checkout.
      - **Handover board:** flashing pick-up board, claim, QR-scan/confirm → audited shipment events (SYS_004).
      - **COD remittance:** nightly job → `finance.bank_transactions` / `transaction_ledger` zero-variance reconciliation (SYS_003).
      - **SLA/health monitor:** `partner_sla_alerts` → suspend partner on breach; stops new order assignment.

      ## UI/UX layout
      - **`/logistics-partner/` panel:** profile, cities (`service_cities` + GPS map), charges (draft/live), coverage, vehicles, COD remittance, SLA dashboards.
      - **Admin approval console:** approve/suspend partner profile + charge changes (Maker-Checker).
      - **UX principles:** explicit coverage errors, skeleton loaders, ARIA + keyboard, density toggle.
    sections:
      §I: "Logistics schema, GPS/geo wiring, charge propagation, seed data."
      §II: "Customer: sees logistic charges at cart/checkout only."
      §III: "Supplier: handover contract with logistic partner (SYS_004)."
      §IV: "Logistics: full `/logistics-partner/` panel — cities, charges, profile, GPS, COD remittance."
      §V: "Admin: approve partner profile + charges, monitor SLA, reconcile remittance."
    expected:
      backend_files:
        - backend/routers/logistics_panel_router.py
        - backend/controllers/logistics/panel_controller.py
        - backend/services/logistics/panel_service.py
        - backend/models/logistics/logistics_panel_model.py
        - backend/jobs/logistics_remittance_job.py
        - backend/events/logistics_events.py
        - backend/providers/geography/location_provider.py
      frontend_web:
        - "frontend/web_app/src/app/logistics-partner/page.tsx"
      frontend_mobile:
        - "frontend/mobile_app/app/logistics-partner/index.tsx"
      tests:
        - "backend/tests/_test_logistics_panel.py"
        - "frontend/web_app/src/__tests__/pages/_test_logistics_panel.test.tsx"
      api_routes:
        - "GET /logistics-partner/cities"
        - "GET /logistics-partner/charges"
        - "GET /logistics-partner/profile"
        - "POST /admin/logistics-partners/{partner_id}/approve"
      models:
        - "LogisticsPartner"
        - "ServiceCity"
        - "DeliveryCharge"
    diagram: |
      flowchart TD
        PROF[logistics_partners profile] --> ADM[Admin approval]
        ADM --> ACTIVE[ACTIVE]
        CITY[service_cities + GPS coverage] --> CHARGE[delivery_charges draft]
        CHARGE -->|live| CART[cart / order recompute]
        ACTIVE --> HAND[handover SYS_004 pick-up / deliver]
        HAND --> COD[COD remittance -> ledger SYS_003]


    ui_diagram: |
      flowchart TB
        subgraph WIN["WINDOW - Logistic Panel (logistics-partner)"]
          HD["Top bar: shipments nav - pod - remittance"]
          NV["Left: shipment list (status) - exceptions"]
          MA["Center: shipment detail - POD capture - remittance job"]
          SB["Right: tracking + customer notify"]
        end
        WIN --> EV["Events -> Order SYS_004 tracking"]