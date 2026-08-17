# Models Reshaping Plan — ZOZI backend

> Source of truth: `documents/NEW_STRUCTURE.md` (§2 Models, §1 vertical slices, §5 schema 1:1, migration mapping lines 119-141, RBAC lines 146-167).
> **REVISED 2026-08-18** to reflect that `backend/domains/` (plural) **already exists** as a partial restructure — see §2b. The original plan assumed a greenfield `backend/domain`; that assumption is now superseded.
>
> Current state audited from `backend/models/` (AST scan, 2026-08-18) **and** the existing `backend/domains/` (filesystem + import-graph scan, 2026-08-18).
> Phase 0 mapping table at the bottom of this file was **generated programmatically** from the live AST (319 classes enumerated in `backend/models`). Target domain names in that table must be reconciled with the *existing* `backend/domains` folder names (§3 / §2b).

---

## 1 · What NEW_STRUCTURE.md prescribes for models

- **ORM only** in `domains/{d}/models/`. No Pydantic DTOs (→ `schemas/`), no business rules (→ `services/`/`policies/`), no `Base`/metadata (→ `infrastructure/database/base.py`).
- **Flat inside the domain**: one file per *entity aggregate* (`ledger.py`, `payouts.py`, `banking.py` …). No subfolders per table. The domain folder already gives the grouping the old `models/{domain}/` used to.
- **Slice only when heavy**: rule of thumb `> ~8 services or > ~12 tables → slice`; otherwise flat. finance/comms/hr/logistics/orders are expected to slice; small domains stay flat.
- **`Base` lives** in `infrastructure/database/base.py` (already exists). ⚠️ There is **also** a second `Base` defined in `backend/models/__init__.py` — these two must be collapsed into ONE registry before any merge (see §2b). Every model gets `__table_args__ = {"schema": "<domain>"}`.
- **Old `backend/models/`** becomes a `_legacy/` re-export shim (or is deleted) only AFTER all ~1,455 `from models import …` sites are repointed at `backend/domains/{d}/models`. Do **not** delete it yet — it is the live ORM source today.
- **Schema ↔ domain 1:1** (law #5): CI asserts `schema name == owning domain name`, `country_code` present on business tables, naming conventions (`<thing>_id`, `created_at`/`updated_at`, plural snake_case).

---

## 2 · Current-state audit of `backend/models/`

> **Status: `backend/models/` is the LIVE, single source of truth today.** The running app (`main.py`, `database.py`, `alembic/env.py`, seeds) imports `from models import Base/…`; ~1,455 call sites across the backend (including the new `backend/domains/*/services`) still resolve models from here. It must NOT be deleted until §4 is complete.

The folder is a **mid-reorg mess** with 5 overlapping categories:

| Cat | Location | State | Action |
|---|---|---|---|
| **C1** | `finance/`, `core/`, `logistics/`, `orders/`, `permissions/`, `comms/`, `geography/` | Promoted packages, UUID + `TenantMixin`, ACTIVE canonical ORM | Relocate as-is |
| **C2** | `hr/`, `identity/`, `security/`, `media/`, `ai/`, `catalog/`, `gateway/`, `configuration/` | Facade re-export `__init__.py` packages | Re-point to real homes |
| **C3** | `communication.py`, `countries.py`, `marketing.py`, `suppliers.py`, `country_enhancements.py`, `supplier/suppliers.py` | Flat SHIMS re-exporting from C1 packages | **DELETE** (superseded) |
| **C4** | `admin.py`, `user.py`, `products.py`, `payments.py`, `fraud.py`, `incident.py`, `employee_models.py`, `erp.py`, `commission.py`, `country_control.py`, `ai_upload.py`, `media_models.py`, `onboarding.py`, `promotions.py`, `upload_job.py` | Still-active flat files, **the god-files** | Relocate + split per table |
| **DEAD** | `finance.py`, `core.py`, `logistics.py`, `orders.py`, `permissions.py` | Duplicate re-export of C1 packages (same `__tablename__`, different classes) | **DELETE** (do not migrate) |

**Key hazards found during audit**
- `admin.py` is a ~36 KB god-file spanning ~8 domains — must be split **per table**, not moved as one unit.
- `finance.py` (dead) and `finance/general_ledger.py` (canonical) both define `Account`, `JournalEntry`, … with identical `__tablename__` — importing both would raise *"Table 'X' is already defined"*. Confirm at runtime which wins, then delete the dead copy.
- `comms/` packages duplicate the classes that the root `core.py`/`communication.py`/`marketing.py` shims mirror — C1 packages are canonical; root shims are deleted.
- **Mixed PK strategies**: C1 packages use UUID + `TenantMixin`; C4 flat files use `Integer` PK. **Keep each table's existing PK** to avoid a DB migration.
- **Schema spread ≠ domain names**: live schemas include `finance, treasury, commerce, customer, logistics, hr, supplier, security, communication, audit, analytics, configuration, core, media, ai`. They must be remapped to the 15 final domains (Phase 3).
- **`backend/domains/` already exists with a STALE duplicate model layer** (see §2b): ~401 model classes are re-defined there under a *separate* `Base` and are orphaned (nothing loads them into the live metadata). This must be de-duplicated before relocation.

---

## 2b · Critical finding — `backend/domains/` already exists (revised reality)

A prior restructure **already created `backend/domains/`** (plural). It is NOT greenfield. Measured 2026-08-18 (filesystem + import-graph scan):

- **15 domain folders exist**: `UNMAPPED, accounts, catalog, comms, country, customers, finance, governance, hr, logistics, mcp, media, orders, payments, suppliers`.
- `backend/domains/*/models/` holds **~401 model class definitions** vs **247 in `backend/models/`**, and **314 class names are duplicated across both layers** (e.g. `User`, `Order`, `Account`, `Product`, `Payment` exist in both).
- **Two independent `Base` registries**:
  - `backend/models/__init__.py` → `class Base(DeclarativeBase)` (registry #1 — the one the app actually uses).
  - `backend/infrastructure/database/base.py` → `class Base(DeclarativeBase)` (registry #2 — used by `backend/domains/*/models`).
  - Because they are separate objects, the ~401 domain model classes register into a metadata that **no bootstrap code loads** → they are effectively dead duplicates.
- `backend/domains/__init__.py` is **empty** — importing the package does not pull in the model subpackages.
- **Proof the app ignores the domain models**: domain services import the top-level package, e.g. `backend/domains/accounts/services/admin_banners_service.py:30` → `from models import User` (NOT `from domains.accounts.models import User`).
- **`User` is defined twice with the SAME `__tablename__="users"` and `{"schema":"core"}`** — in `backend/models/user.py` and `backend/domains/accounts/models/user.py`. If both were ever loaded into one registry it would raise *"Table 'core.users' is already defined"*.

**Conclusion:** nothing was "transferred". The model layer (the DB-critical part) was never migrated. `backend/domains` received a *parallel copy* of the models plus the new services/schemas/events, but the app still binds to `backend/models`. Deleting `backend/models` today would break the entire app.

**Taxonomy drift (must reconcile before relocation):**

| Plan target (NEW_STRUCTURE.md) | Existing `backend/domains` folder | Action |
|---|---|---|
| `customers` (User/Address/Cart/Referral…) | `accounts` holds these (45 model defs); `customers` folder has **no models** | Rename/merge `accounts` → `customers` (or adopt `accounts` as canonical and update the plan) |
| `ai` | *(missing)* | Create `backend/domains/ai/models` |
| `security` | *(missing)* | Create `backend/domains/security/models` |
| `rbac` | not under `domains/` (root-level `rbac/`) | Decide: move `rbac` under `domains/` or keep root-level per NEW_STRUCTURE |
| `mcp`, `UNMAPPED` | exist but **not** in the 15-domain plan | `mcp` → fold into its real domain; `UNMAPPED` → triage each class to a real domain, then delete the folder |

---

## 3 · Target domain topology

15 domains + `rbac` (RBAC owns the Feature axis; see NEW_STRUCTURE.md §RBAC):

`finance` · `catalog` · `orders` · `payments` · `logistics` · `suppliers` · `customers` · `hr` · `comms` · `media` · `country` · `governance` · `security` · `ai` · `rbac`

> **Reconcile names with the existing folders first (§2b):** the live tree uses `accounts` not `customers`, and is missing `ai`/`security` as folders; `mcp`/`UNMAPPED` are extra. The Phase 0 table below uses the *plan* names — map them onto the reconciled folder set during Phase 1.

(`treasury` is a **slice inside `finance`**, not a separate domain — it reuses the `finance` schema.)

Each table's Postgres schema is set to its owning domain name (law #5). During relocation, **preserve existing `__tablename__`**; align the schema only in a dedicated migration (see Phase 3 / risks).

Cross-cutting remaps applied in the Phase 0 table:
- `commerce` schema → `catalog` (Product/Category/Review/Variant/Coupon/Promotion/Badge/Commission), `orders` (Cart/OrderLogisticsAllocation/ReturnRequest), `customers` (Address/Referral/Wishlist).
- `Supplier*` + procurement (purchase_orders, goods_receipt) → `suppliers`.
- `Permission*` tables → `rbac/models.py` (with `admin.RolePermissionSetting`).
- `Employee*` + shift/handover → `hr`.
- `Fraud*` + DLP → `security`; meeting transcripts → `ai`.
- `admin` analytics/audit/alert/setting/webhook → `governance` (or `security` for API keys).

---

## 4 · The plan (revised for an existing `backend/domains`)

> Guiding principle: **single `Base`, single source of truth, no double-registration.** The work is no longer "create the target" — it is "reconcile the stale duplicate model layer inside the target and repoint the app at it."

### Phase 0 — Taxonomy & class-level mapping  ✅ (this document)
- Enumerate every canonical model class → target `domains/{d}/models/{file}.py` + PG schema (table at bottom; 319 classes enumerated).
- Produce delete-list of C3 shims + DEAD duplicates + duplicate domain-model twins.
- **Add (this revision):** reconcile plan domain names with existing `backend/domains` folders (§2b table). Decide `accounts`↔`customers`, create `ai`/`security`, resolve `mcp`/`UNMAPPED`/`rbac`.

### Phase 1 — Unify `Base` and reconcile taxonomy  (do this BEFORE touching models)
1. **Collapse the two `Base` objects into one.** Either (a) make `backend/models/__init__.py` import `Base` from `infrastructure/database/base.py` (so both names resolve to the same registry), or (b) adopt `infrastructure/database/base.py` as canonical and repoint `backend/models`. Pick one; never keep two.
2. Apply the §2b taxonomy reconciliation: rename `accounts`→`customers` (or vice-versa), create `ai`/`security` model folders, triage `mcp`/`UNMAPPED`.
3. Keep `backend/models` as-is (still live). No deletions yet.

### Phase 2 — De-duplicate the domain model layer
- For each of the **314 duplicated class names**, pick the **canonical definition = the one in `backend/models`** (it matches the running DB). **Delete the orphan twin** in `backend/domains/{d}/models/*.py` that is not yet wired to the app. (These twins were never loaded into the live metadata, so deleting them is safe once `Base` is unified.)
- Where a domain model file is empty/only re-exports `Base` (the `accounts/models/__init__.py` pattern), leave it — it becomes the relocation target in Phase 3.
- After this phase, `backend/domains/*/models` should contain **no live class that also exists in `backend/models`** (zero overlap).

### Phase 3 — Relocate canonical classes into `backend/domains/{d}/models`
- For each row in the Phase 0 table: move the class definition (whole `ClassDef` + needed imports) from `backend/models/...` to `backend/domains/{target}/models/{file}.py`, **replacing** the now-deleted stale twin.
- Collapse same-file groups; split god-files (`admin.py`, `country_control.py`, `comms/core.py`, `erp.py`) class-by-class.
- Update each `backend/domains/{d}/models/__init__.py` to re-export the relocated classes.
- Run the import smoke test after every domain.

### Phase 4 — Repoint imports & retire `backend/models`
1. Replace the **~1,455 `from models import X` / `import models`** sites (including inside `backend/domains/*/services`) with `from domains.{d}.models import X`. Drive this with a codemod; keep `backend/models` importable meanwhile via a thin re-export shim.
2. When all sites resolve to `backend/domains` and the app boots with a **single registry and zero duplicate-`__tablename__` errors**, delete `backend/models` (or leave it as the documented `_legacy` shim, then delete after a soak period).

### Phase 5 — Normalize & enforce (CI)
- Add `__table_args__ = {"schema": "<domain>"}` to every migrated model (preserve `__tablename__`; migrate schema separately — see risks).
- CI asserts: schema == domain, `country_code` on business tables, naming conventions, and **no duplicate `__tablename__`** across the single registry.
- Wire `rbac` catalog scanner (`domains/*/features.py`).

---

## 5 · Correctness checklist (gate before each domain ships)

- [ ] **Exactly one `Base`** object exists; `backend/models` and `infrastructure/database/base.py` resolve to the same registry. No second `DeclarativeBase`.
- [ ] `uvicorn`/app imports with **no** `Table 'X' is already defined` / duplicate registry error.
- [ ] **Zero overlap**: no class name/table is defined in BOTH `backend/models` and `backend/domains/*/models` (the 314 duplicates are resolved).
- [ ] Every public model name still importable from its `domains/{d}/models` home (and, during transition, from the `backend/models` shim).
- [ ] **Zero DB drift**: no `CREATE/DROP/ALTER TABLE` emitted by the ORM against the existing schema during relocation (rely on existing `__tablename__` + existing schema).
- [ ] All `from models import …` sites repointed at `domains.{d}.models` (incl. inside `backend/domains/*/services`).
- [ ] Each domain's models carry `__table_args__={"schema": "<domain>"}`.
- [ ] Law conformance: no `from domains.X.(services|models|repositories)` outside `domains/X` (only `ports`/`events` allowed).
- [ ] Structure: domain ≤ ~12 tables stays flat; heavier cases sliced; no global flat `models/`.
- [ ] Taxonomy reconciled: `accounts`/`customers` naming decided; `ai`/`security` folders exist; `mcp`/`UNMAPPED` emptied.

---

## 6 · Risks / open questions

1. **Dual-`Base` hazard (NEW, top priority).** Two independent `DeclarativeBase` objects will cause duplicate-table or silent metadata-split errors if merged carelessly. Unify to one registry (Phase 1) before any class move. *Mitigation:* after unifying, running the app import must load exactly one set of tables.
2. **314 duplicate class definitions** across `backend/models` and `backend/domains/*/models`. The domain copies are orphaned today, but a naive "move everything" risks double-registration. Always delete the stale twin before/with relocation (Phase 2 → 3). *Mitigation:* assert zero name overlap in CI.
3. **Schema rename is a real migration.** Law #5 wants `schema == domain`, but live tables sit in `commerce`, `communication`, `treasury`, `audit`, `analytics`, `core`, …. Recommend: relocate first preserving schemas, then a separate `ALTER TABLE … SET SCHEMA` migration + `__table_args__` update. Flag if DB is authoritative.
4. **Taxonomy drift.** Existing folders use `accounts` (not `customers`), lack `ai`/`security`, and include `mcp`/`UNMAPPED` not in the plan. Decide canonical names before relocation or the move targets will be wrong.
5. **Duplicate `finance`/`core` class defs** — confirm runtime winner, delete the other. The Phase 0 table treats the *package* (`finance/general_ledger.py`, `comms/*`) as canonical and marks root `finance.py`/`core.py`/etc. for deletion.
6. **`finance.Customer` vs `customers.User`** — finance AR/AP `Customer`/`Vendor` are finance-managed parties; keep in `finance` (do not merge with `customers.User`).
7. **`Banner`/`Coupon`** placed in `catalog` (promo surface); move to `comms` if they are purely notification banners.
8. **`governance` vs `security`** split (API keys, webhooks, alerts) — table assignment is a judgement call; revisit during Phase 3.

---

## Phase 0 — Full class-level current → target mapping

Total canonical model classes mapped: 319

> **Read with §2b in mind.** The *Target domain* column uses the plan's canonical names (`customers`, `ai`, `security`, `rbac`). Reconcile these against the **existing** `backend/domains` folders (`accounts` not `customers`; `ai`/`security` folders to be created; `mcp`/`UNMAPPED` to be triaged) during Phase 1 before acting on any row.

| Target domain | Current file | Class | `__tablename__` | Target `domains/<d>/models/` | PG schema |
|---|---|---|---|---|---|
| ai | `./ai_upload.py` | `AIGenerationLog` | `ai_generation_logs` | `log.py` | `ai` |
| ai | `./ai_upload.py` | `AIStagingProduct` | `ai_staging_products` | `staging.py` | `ai` |
| ai | `./ai_upload.py` | `AIStagingVariant` | `ai_staging_variants` | `staging.py` | `ai` |
| ai | `./ai_upload.py` | `AIUploadJob` | `ai_upload_jobs` | `upload.py` | `ai` |
| ai | `./fraud.py` | `MeetingActionItem` | `meeting_action_items` | `transcript.py` | `ai` |
| ai | `./fraud.py` | `MeetingRecording` | `meeting_recordings` | `transcript.py` | `ai` |
| ai | `./fraud.py` | `MeetingTranscript` | `meeting_transcripts` | `transcript.py` | `ai` |
| catalog | `./promotions.py` | `BOGOPromotion` | `bogo_promotions` | `promotion.py` | `catalog` |
| catalog | `./admin.py` | `BadgeBillingRecord` | `badge_billing_records` | `badge.py` | `catalog` |
| catalog | `./admin.py` | `BadgeTier` | `badge_tiers` | `badge.py` | `catalog` |
| catalog | `./admin.py` | `BadgeTransaction` | `badge_transactions` | `badge.py` | `catalog` |
| catalog | `./payments.py` | `Banner` | `banners` | `catalog_misc.py` | `catalog` |
| catalog | `./products.py` | `Category` | `categories` | `category.py` | `catalog` |
| catalog | `./commission.py` | `CommissionAgreement` | `commission_agreements` | `commission.py` | `catalog` |
| catalog | `./admin.py` | `CommissionBadgeTier` | `commission_badge_tiers` | `badge.py` | `catalog` |
| catalog | `./commission.py` | `CommissionCategoryRate` | `commission_category_rates` | `commission.py` | `catalog` |
| catalog | `./admin.py` | `CommissionGlobalConfig` | `commission_global_configs` | `badge.py` | `catalog` |
| catalog | `./commission.py` | `CommissionLedgerEntry` | `commission_ledger_entries` | `commission.py` | `catalog` |
| catalog | `./payments.py` | `Coupon` | `coupons` | `catalog_misc.py` | `catalog` |
| catalog | `./admin.py` | `CouponUsage` | `coupon_usage` | `promotion.py` | `catalog` |
| catalog | `./products.py` | `Product` | `products` | `product.py` | `catalog` |
| catalog | `./commission.py` | `ProductCommissionOverride` | `product_commission_overrides` | `commission.py` | `catalog` |
| catalog | `./products.py` | `ProductFilterMetadata` | `product_filter_metadata` | `product.py` | `catalog` |
| catalog | `./products.py` | `ProductFilterOption` | `product_filter_options` | `product.py` | `catalog` |
| catalog | `./products.py` | `ProductVariant` | `product_variants` | `product.py` | `catalog` |
| catalog | `./admin.py` | `ProductVerification` | `product_verifications` | `product.py` | `catalog` |
| catalog | `./products.py` | `ProductVideo` | `product_videos` | `product.py` | `catalog` |
| catalog | `./admin.py` | `PromotionEngineConfig` | `promotion_engine_configs` | `promotion.py` | `catalog` |
| catalog | `./admin.py` | `PromotionLedgerEntry` | `promotion_ledger_entries` | `promotion.py` | `catalog` |
| catalog | `./admin.py` | `PromotionOrderTier` | `promotion_order_tiers` | `promotion.py` | `catalog` |
| catalog | `./products.py` | `Review` | `reviews` | `review.py` | `catalog` |
| catalog | `./products.py` | `VideoAnalytics` | `video_analytics` | `product.py` | `catalog` |
| catalog | `./products.py` | `Wishlist` | `wishlists` | `wishlist.py` | `catalog` |
| catalog | `./products.py` | `WishlistItem` | `wishlist_items` | `wishlist.py` | `catalog` |
| comms | `comms/communication.py` | `Announcement` | `announcements` | `announcement.py` | `comms` |
| comms | `comms/marketing.py` | `CampaignRecipient` | `campaign_recipients` | `marketing.py` | `comms` |
| comms | `comms/communication.py` | `ChatAttachment` | `chat_attachments` | `channel.py` | `comms` |
| comms | `comms/communication.py` | `ChatReadReceipt` | `chat_read_receipts` | `channel.py` | `comms` |
| comms | `./admin.py` | `ChatbotQueryEvent` | `chatbot_query_events` | `chatbot.py` | `comms` |
| comms | `comms/communication.py` | `CommunicationAuditTrail` | `communication_audit_trail` | `audit.py` | `comms` |
| comms | `comms/core.py` | `DirectChatMessage` | `direct_chat_messages` | `chat.py` | `comms` |
| comms | `comms/core.py` | `DirectChatRoom` | `direct_chat_rooms` | `chat.py` | `comms` |
| comms | `comms/marketing.py` | `EmailCampaign` | `email_campaigns` | `marketing.py` | `comms` |
| comms | `comms/marketing.py` | `EmailCampaignLog` | `email_campaign_logs` | `marketing.py` | `comms` |
| comms | `comms/marketing.py` | `EmailDeliveryEvent` | `email_delivery_events` | `marketing.py` | `comms` |
| comms | `comms/communication.py` | `EmailFolder` | `email_folders` | `email.py` | `comms` |
| comms | `./admin.py` | `EmailProviderConfig` | `email_provider_configs` | `comms_misc.py` | `comms` |
| comms | `comms/marketing.py` | `EmailRuntimeConfig` | `email_runtime_config` | `marketing.py` | `comms` |
| comms | `comms/marketing.py` | `EmailSuppression` | `email_suppressions` | `marketing.py` | `comms` |
| comms | `comms/marketing.py` | `EmailTemplate` | `email_templates` | `marketing.py` | `comms` |
| comms | `comms/communication.py` | `EmployeeCommunicationThread` | `employee_communication_threads` | `thread.py` | `comms` |
| comms | `comms/core.py` | `EntityChatMessage` | `entity_chat_messages` | `chat.py` | `comms` |
| comms | `comms/core.py` | `EntityChatThread` | `entity_chat_threads` | `chat.py` | `comms` |
| comms | `comms/communication.py` | `ExternalContactMasking` | `external_contact_masking` | `proxy.py` | `comms` |
| comms | `comms/communication.py` | `FAQ` | `faqs` | `faq.py` | `comms` |
| comms | `comms/marketing.py` | `FlashSale` | `flash_sales` | `marketing.py` | `comms` |
| comms | `comms/marketing.py` | `FlashSaleItem` | `flash_sale_items` | `marketing.py` | `comms` |
| comms | `comms/core.py` | `GroupChatMember` | `group_chat_members` | `chat.py` | `comms` |
| comms | `comms/core.py` | `GroupChatMessage` | `group_chat_messages` | `chat.py` | `comms` |
| comms | `comms/core.py` | `GroupChatRoom` | `group_chat_rooms` | `chat.py` | `comms` |
| comms | `comms/communication.py` | `HelpCategory` | `help_categories` | `support.py` | `comms` |
| comms | `comms/communication.py` | `InternalChannel` | `internal_channels` | `channel.py` | `comms` |
| comms | `comms/communication.py` | `InternalChannelMember` | `internal_channel_members` | `channel.py` | `comms` |
| comms | `comms/communication.py` | `InternalEmail` | `internal_emails` | `email.py` | `comms` |
| comms | `comms/communication.py` | `InternalMessage` | `internal_messages` | `channel.py` | `comms` |
| comms | `comms/communication.py` | `MaskedMessage` | `masked_messages` | `proxy.py` | `comms` |
| comms | `comms/marketing.py` | `NewsletterSubscriber` | `newsletter_subscribers` | `marketing.py` | `comms` |
| comms | `comms/communication.py` | `Notification` | `notifications` | `notification.py` | `comms` |
| comms | `comms/marketing.py` | `PointsTransaction` | `points_transactions` | `loyalty.py` | `comms` |
| comms | `comms/communication.py` | `ProxyCallLog` | `proxy_call_logs` | `proxy.py` | `comms` |
| comms | `comms/communication.py` | `ProxyChannel` | `proxy_channels` | `proxy.py` | `comms` |
| comms | `comms/communication.py` | `ProxyMessage` | `proxy_messages` | `proxy.py` | `comms` |
| comms | `comms/communication.py` | `ProxySession` | `proxy_sessions` | `proxy.py` | `comms` |
| comms | `./admin.py` | `PushNotificationToken` | `push_notification_tokens` | `notification.py` | `comms` |
| comms | `comms/core.py` | `SupportTicket` | `support_tickets` | `support.py` | `comms` |
| comms | `comms/core.py` | `SupportTicketReply` | `support_ticket_replies` | `support.py` | `comms` |
| comms | `comms/core.py` | `TicketAttachment` | `ticket_attachments` | `support.py` | `comms` |
| comms | `comms/communication.py` | `TicketMessage` | `ticket_messages` | `support.py` | `comms` |
| comms | `./admin.py` | `TicketReply` | `ticket_replies` | `support.py` | `comms` |
| comms | `comms/marketing.py` | `UserPoints` | `user_points` | `loyalty.py` | `comms` |
| comms | `comms/core.py` | `VideoRoom` | `video_rooms` | `video.py` | `comms` |
| comms | `comms/core.py` | `VideoRoomParticipant` | `video_room_participants` | `video.py` | `comms` |
| comms | `comms/core.py` | `VideoRoomRecording` | `video_room_recordings` | `video.py` | `comms` |
| country | `geography/country_basics.py` | `CountryBasics` | `country_basics` | `basics.py` | `country` |
| country | `geography/country_enhancements.py` | `CountryCategoryTaxRate` | `country_category_tax_rates` | `enhancement.py` | `country` |
| country | `geography/country_enhancements.py` | `CountryCity` | `country_cities` | `enhancement.py` | `country` |
| country | `geography/country_enhancements.py` | `CountryCommissionRate` | `country_commission_rates` | `enhancement.py` | `country` |
| country | `geography/country_enhancements.py` | `CountryCommissionRateHistory` | `country_commission_rate_history` | `enhancement.py` | `country` |
| country | `geography/countries.py` | `CountryCommunication` | `country_communications` | `config.py` | `country` |
| country | `geography/country_enhancements.py` | `CountryCommunicationThread` | `country_communication_threads` | `enhancement.py` | `country` |
| country | `geography/countries.py` | `CountryConfig` | `country_configs` | `config.py` | `country` |
| country | `geography/country_enhancements.py` | `CountryConfigVersion` | `country_config_versions` | `enhancement.py` | `country` |
| country | `geography/country_economics.py` | `CountryEconomics` | `country_economics` | `economics.py` | `country` |
| country | `geography/country_enhancements.py` | `CountryFeatureFlag` | `country_feature_flags` | `enhancement.py` | `country` |
| country | `geography/country_enhancements.py` | `CountryGatewayConfig` | `country_gateway_configs` | `enhancement.py` | `country` |
| country | `geography/countries.py` | `CountryGatewayCredentials` | `country_gateway_credentials` | `config.py` | `country` |
| country | `geography/country_enhancements.py` | `CountryHolidayCalendar` | `country_holiday_calendars` | `enhancement.py` | `country` |
| country | `geography/country_legal.py` | `CountryLegal` | `country_legal` | `legal.py` | `country` |
| country | `geography/country_enhancements.py` | `CountryLegalContract` | `country_legal_contracts` | `legal.py` | `country` |
| country | `geography/country_enhancements.py` | `CountryLocalization` | `country_localization` | `enhancement.py` | `country` |
| country | `geography/country_enhancements.py` | `CountryLogisticsZone` | `country_logistics_zones` | `enhancement.py` | `country` |
| country | `./country_control.py` | `CountryMapConfig` | `country_map_configs` | `country_misc.py` | `country` |
| country | `geography/country_enhancements.py` | `CountryPaymentAlias` | `country_payment_aliases` | `enhancement.py` | `country` |
| country | `geography/country_enhancements.py` | `CountryPayoutRule` | `country_payout_rules` | `enhancement.py` | `country` |
| country | `geography/country_enhancements.py` | `CountryStaffAssignment` | `country_staff_assignments` | `enhancement.py` | `country` |
| country | `geography/country_tax.py` | `CountryTax` | `country_tax` | `tax.py` | `country` |
| country | `geography/country_enhancements.py` | `CrossCountryCustomerSession` | `cross_country_customer_sessions` | `enhancement.py` | `country` |
| country | `./country_control.py` | `DataResidencyRecord` | `data_residency_records` | `country_misc.py` | `country` |
| country | `./country_control.py` | `LegalContractTemplate` | `legal_contract_templates` | `country_misc.py` | `country` |
| country | `geography/country_enhancements.py` | `LogisticsPartnerKYCRequirement` | `logistics_partner_kyc_requirements` | `enhancement.py` | `country` |
| country | `geography/countries.py` | `Message` | `messages` | `config.py` | `country` |
| country | `geography/country_enhancements.py` | `OmanDeliveryZone` | `oman_delivery_zones` | `enhancement.py` | `country` |
| country | `geography/countries.py` | `PayoutRule` | `payout_rules` | `rule.py` | `country` |
| country | `geography/countries.py` | `PayoutRuleCategory` | `payout_rule_categories` | `rule.py` | `country` |
| country | `geography/countries.py` | `PayoutRuleProduct` | `payout_rule_products` | `rule.py` | `country` |
| country | `geography/countries.py` | `ShippingRule` | `shipping_rules` | `rule.py` | `country` |
| country | `geography/country_enhancements.py` | `SupplierKYCRequirement` | `supplier_kyc_requirements` | `enhancement.py` | `country` |
| country | `geography/countries.py` | `TaxRule` | `tax_rules` | `rule.py` | `country` |
| customers | `comms/core.py` | `Address` | `addresses` | `address.py` | `customers` |
| customers | `comms/core.py` | `Cart` | `carts` | `cart.py` | `customers` |
| customers | `comms/core.py` | `CartItem` | `cart_items` | `cart.py` | `customers` |
| customers | `./user.py` | `EmailVerificationToken` | `email_verification_tokens` | `auth.py` | `customers` |
| customers | `./user.py` | `PasswordResetToken` | `password_reset_tokens` | `auth.py` | `customers` |
| customers | `./user.py` | `Referral` | `referrals` | `referral.py` | `customers` |
| customers | `./user.py` | `ReferralPointEvent` | `referral_point_events` | `referral.py` | `customers` |
| customers | `./admin.py` | `RetentionJobRun` | `retention_job_runs` | `retention.py` | `customers` |
| customers | `./user.py` | `RevokedToken` | `revoked_tokens` | `auth.py` | `customers` |
| customers | `./user.py` | `User` | `users` | `user.py` | `customers` |
| customers | `comms/core.py` | `UserBrowsingHistory` | `user_browsing_history` | `user.py` | `customers` |
| customers | `./user.py` | `UserDevice` | `user_devices` | `user.py` | `customers` |
| customers | `./user.py` | `UserLoginHistory` | `user_login_history` | `user.py` | `customers` |
| finance | `finance/general_ledger.py` | `APBill` | `ap_bills` | `ar_ap.py` | `finance` |
| finance | `finance/general_ledger.py` | `APLedger` | `ap_ledger_entries` | `ar_ap.py` | `finance` |
| finance | `finance/general_ledger.py` | `ARInvoice` | `ar_invoices` | `ar_ap.py` | `finance` |
| finance | `finance/general_ledger.py` | `ARLedgerEntry` | `ar_ledger_entries` | `ar_ap.py` | `finance` |
| finance | `finance/general_ledger.py` | `Account` | `accounts` | `ledger.py` | `finance` |
| finance | `finance/general_ledger.py` | `AccountBalance` | `account_balances` | `ledger.py` | `finance` |
| finance | `finance/general_ledger.py` | `AccountGroup` | `account_groups` | `ledger.py` | `finance` |
| finance | `finance/general_ledger.py` | `Accrual` | `accruals` | `ledger.py` | `finance` |
| finance | `finance/general_ledger.py` | `AutomationLog` | `automation_logs` | `finance_misc.py` | `finance` |
| finance | `finance/general_ledger.py` | `AutomationRule` | `automation_rules` | `automation.py` | `finance` |
| finance | `finance/general_ledger.py` | `BankAccount` | `bank_accounts` | `banking.py` | `finance` |
| finance | `finance/general_ledger.py` | `BankMappingRule` | `bank_mapping_rules` | `banking.py` | `finance` |
| finance | `finance/general_ledger.py` | `BankReconciliation` | `bank_reconciliations` | `banking.py` | `finance` |
| finance | `finance/general_ledger.py` | `BankStatementImport` | `bank_statement_imports` | `banking.py` | `finance` |
| finance | `finance/general_ledger.py` | `BankStatementLine` | `bank_statement_lines` | `banking.py` | `finance` |
| finance | `finance/general_ledger.py` | `BankTransaction` | `bank_transactions` | `banking.py` | `finance` |
| finance | `finance/general_ledger.py` | `Budget` | `budgets` | `reporting.py` | `finance` |
| finance | `finance/general_ledger.py` | `CashAccount` | `cash_accounts` | `cash.py` | `finance` |
| finance | `finance/general_ledger.py` | `CashFlowForecast` | `cash_flow_forecasts` | `treasury.py` | `finance` |
| finance | `finance/general_ledger.py` | `CashPositionSnapshot` | `cash_position_snapshots` | `treasury.py` | `finance` |
| finance | `finance/general_ledger.py` | `CashTransaction` | `cash_transactions` | `cash.py` | `finance` |
| finance | `finance/general_ledger.py` | `CostCenter` | `cost_centers` | `reporting.py` | `finance` |
| finance | `finance/general_ledger.py` | `Customer` | `customers` | `ar_ap.py` | `finance` |
| finance | `finance/general_ledger.py` | `FinanceAuditLog` | `finance_audit_logs` | `audit.py` | `finance` |
| finance | `finance/general_ledger.py` | `FinanceAutomationLog` | `finance_automation_logs` | `automation.py` | `finance` |
| finance | `./admin.py` | `FinanceBankAccount` | `finance_bank_accounts` | `banking.py` | `finance` |
| finance | `finance/general_ledger.py` | `FinancialReport` | `financial_reports` | `reporting.py` | `finance` |
| finance | `finance/general_ledger.py` | `FiscalPeriod` | `fiscal_periods` | `ledger.py` | `finance` |
| finance | `finance/general_ledger.py` | `FixedAsset` | `fixed_assets` | `assets.py` | `finance` |
| finance | `finance/general_ledger.py` | `GatewaySettlementSchedule` | `gateway_settlement_schedules` | `payouts.py` | `finance` |
| finance | `finance/general_ledger.py` | `Invoice` | `invoices` | `ar_ap.py` | `finance` |
| finance | `finance/general_ledger.py` | `InvoiceItem` | `invoice_items` | `ar_ap.py` | `finance` |
| finance | `finance/general_ledger.py` | `JournalEntry` | `journal_entries` | `ledger.py` | `finance` |
| finance | `finance/general_ledger.py` | `JournalEntryLine` | `journal_entry_lines` | `ledger.py` | `finance` |
| finance | `finance/general_ledger.py` | `PayoutBatch` | `payout_batches` | `payouts.py` | `finance` |
| finance | `finance/general_ledger.py` | `PayoutBatchItem` | `payout_batch_items` | `payouts.py` | `finance` |
| finance | `finance/general_ledger.py` | `PendingJournalEntry` | `pending_journal_entries` | `ledger.py` | `finance` |
| finance | `finance/general_ledger.py` | `RecurringTemplate` | `recurring_templates` | `ledger.py` | `finance` |
| finance | `finance/general_ledger.py` | `RefundLedger` | `refund_ledger` | `ar_ap.py` | `finance` |
| finance | `finance/general_ledger.py` | `ScannedExpense` | `scanned_expenses` | `expenses.py` | `finance` |
| finance | `finance/general_ledger.py` | `SupplierSettlement` | `supplier_settlements` | `ledger.py` | `finance` |
| finance | `finance/general_ledger.py` | `TransactionLedger` | `transaction_ledgers` | `ledger.py` | `finance` |
| finance | `finance/general_ledger.py` | `TreasuryAccount` | `treasury_accounts` | `treasury.py` | `finance` |
| finance | `finance/general_ledger.py` | `TreasuryTransaction` | `treasury_transactions` | `treasury.py` | `finance` |
| finance | `finance/general_ledger.py` | `VATRemittance` | `vat_remittances` | `tax.py` | `finance` |
| finance | `finance/general_ledger.py` | `Vendor` | `vendors` | `ar_ap.py` | `finance` |
| governance | `./admin.py` | `AdminActivityLog` | `admin_activity_logs` | `audit.py` | `governance` |
| governance | `./admin.py` | `AdminAnalyticsSnapshot` | `admin_analytics_snapshots` | `analytics.py` | `governance` |
| governance | `./admin.py` | `AdminChangeAuditLog` | `admin_change_audit_logs` | `audit.py` | `governance` |
| governance | `comms/core.py` | `AlertEscalationRule` | `alert_escalation_rules` | `escalation.py` | `governance` |
| governance | `comms/core.py` | `AuditLog` | `audit_logs` | `audit.py` | `governance` |
| governance | `comms/core.py` | `CommandCenterView` | `command_center_views` | `command_center.py` | `governance` |
| governance | `comms/core.py` | `EscalationSLALog` | `escalation_sla_logs` | `escalation.py` | `governance` |
| governance | `comms/core.py` | `EscalationSLARule` | `escalation_sla_rules` | `escalation.py` | `governance` |
| governance | `comms/core.py` | `ExecutiveNews` | `executive_news` | `news.py` | `governance` |
| governance | `./incident.py` | `IncidentActionItem` | `incident_action_items` | `incident.py` | `governance` |
| governance | `./incident.py` | `IncidentThread` | `incident_threads` | `incident.py` | `governance` |
| governance | `./incident.py` | `IncidentWarRoom` | `incident_war_rooms` | `incident.py` | `governance` |
| governance | `comms/core.py` | `InternalNotice` | `internal_notices` | `notice.py` | `governance` |
| governance | `comms/core.py` | `NewsArticle` | `news_articles` | `news.py` | `governance` |
| governance | `comms/core.py` | `NewsSource` | `news_sources` | `news.py` | `governance` |
| governance | `./admin.py` | `NormalizedWebhookEvent` | `normalized_webhook_events` | `webhook.py` | `governance` |
| governance | `comms/core.py` | `PredictiveSimulation` | `predictive_simulations` | `sim.py` | `governance` |
| governance | `./admin.py` | `ProcessedWebhookEvent` | `processed_webhook_events` | `webhook.py` | `governance` |
| governance | `./admin.py` | `SystemAlert` | `system_alerts` | `alert.py` | `governance` |
| governance | `comms/core.py` | `SystemHealthEvent` | `system_health_events` | `health.py` | `governance` |
| governance | `./admin.py` | `SystemSetting` | `system_settings` | `setting.py` | `governance` |
| governance | `./incident.py` | `WarRoomTemplate` | `war_room_templates` | `incident.py` | `governance` |
| hr | `./employee_models.py` | `AlumniNetwork` | `alumni_network` | `alumni.py` | `hr` |
| hr | `./employee_models.py` | `COIReport` | `coi_reports` | `compliance.py` | `hr` |
| hr | `./employee_models.py` | `DisciplinaryCase` | `disciplinary_cases` | `disciplinary.py` | `hr` |
| hr | `./employee_models.py` | `DynamicQRSession` | `dynamic_qr_sessions` | `identity.py` | `hr` |
| hr | `./employee_models.py` | `Employee` | `employees` | `employee.py` | `hr` |
| hr | `./employee_models.py` | `EmployeeActivityLog` | `employee_activity_logs` | `audit.py` | `hr` |
| hr | `./employee_models.py` | `EmployeeAddress` | `employee_addresses` | `employee.py` | `hr` |
| hr | `./employee_models.py` | `EmployeeAsset` | `employee_assets` | `asset.py` | `hr` |
| hr | `./employee_models.py` | `EmployeeAttendance` | `employee_attendance` | `attendance.py` | `hr` |
| hr | `./employee_models.py` | `EmployeeBiometric` | `employee_biometrics` | `identity.py` | `hr` |
| hr | `./employee_models.py` | `EmployeeCertification` | `employee_certifications` | `cert.py` | `hr` |
| hr | `./employee_models.py` | `EmployeeDependent` | `employee_dependents` | `dependent.py` | `hr` |
| hr | `./employee_models.py` | `EmployeeDocument` | `employee_documents` | `document.py` | `hr` |
| hr | `./admin.py` | `EmployeeExpense` | `employee_expenses` | `hr_misc.py` | `hr` |
| hr | `./employee_models.py` | `EmployeeLeaveLedger` | `employee_leave_ledgers` | `leave.py` | `hr` |
| hr | `./employee_models.py` | `EmployeeLeaveRequest` | `employee_leave_requests` | `leave.py` | `hr` |
| hr | `./employee_models.py` | `EmployeeRelation` | `employee_relations` | `relation.py` | `hr` |
| hr | `./employee_models.py` | `EmployeeRiskScore` | `employee_risk_scores` | `risk.py` | `hr` |
| hr | `./employee_models.py` | `EmployeeRole` | `employee_roles` | `role.py` | `hr` |
| hr | `./employee_models.py` | `EmployeeShiftRoster` | `employee_shift_rosters` | `roster.py` | `hr` |
| hr | `./employee_models.py` | `EmployeeTraining` | `employee_trainings` | `training.py` | `hr` |
| hr | `./employee_models.py` | `EmployeeWorkLog` | `employee_work_logs` | `worklog.py` | `hr` |
| hr | `./employee_models.py` | `GeoFenceLog` | `geo_fence_logs` | `attendance.py` | `hr` |
| hr | `./employee_models.py` | `OffboardingCase` | `offboarding_cases` | `offboarding.py` | `hr` |
| hr | `./employee_models.py` | `Office` | `offices` | `office.py` | `hr` |
| hr | `./employee_models.py` | `OrgUnit` | `org_units` | `org.py` | `hr` |
| hr | `./employee_models.py` | `PayrollRecord` | `payroll_records` | `payroll.py` | `hr` |
| hr | `./employee_models.py` | `PhysicalIDCard` | `physical_id_cards` | `identity.py` | `hr` |
| hr | `./country_control.py` | `ShiftHandoverLog` | `shift_handover_logs` | `handover.py` | `hr` |
| hr | `comms/core.py` | `ShiftHandoverSession` | `shift_handover_sessions` | `handover.py` | `hr` |
| hr | `comms/core.py` | `ShiftHandoverTask` | `shift_handover_tasks` | `handover.py` | `hr` |
| hr | `./employee_models.py` | `TrainingModule` | `training_modules` | `training.py` | `hr` |
| hr | `./employee_models.py` | `TravelRequest` | `employee_travel_requests` | `travel.py` | `hr` |
| logistics | `comms/core.py` | `CityDistanceMatrix` | `city_distance_matrix` | `geo.py` | `logistics` |
| logistics | `./erp.py` | `CustomsEntry` | `customs_entries` | `import.py` | `logistics` |
| logistics | `./erp.py` | `ImportCostTemplate` | `import_cost_templates` | `import.py` | `logistics` |
| logistics | `./erp.py` | `ImportShipment` | `import_shipments` | `import.py` | `logistics` |
| logistics | `./erp.py` | `ImportShipmentLine` | `import_shipment_lines` | `import.py` | `logistics` |
| logistics | `./erp.py` | `LandedCostAllocation` | `landed_cost_allocations` | `import.py` | `logistics` |
| logistics | `./admin.py` | `LogisticsCODRemittanceReceipt` | `logistics_cod_remittance_receipts` | `settlement.py` | `logistics` |
| logistics | `logistics/logistics_entities.py` | `LogisticsCategoryPricingRule` | `logistics_category_pricing_rules` | `pricing.py` | `logistics` |
| logistics | `logistics/logistics_entities.py` | `LogisticsPartner` | `logistics_partners` | `partner.py` | `logistics` |
| logistics | `./admin.py` | `LogisticsPartnerBankAccount` | `logistics_partner_bank_accounts` | `partner.py` | `logistics` |
| logistics | `./admin.py` | `LogisticsPartnerDocument` | `logistics_partner_documents` | `partner.py` | `logistics` |
| logistics | `./country_control.py` | `LogisticsPartnerLocation` | `logistics_partner_locations` | `partner.py` | `logistics` |
| logistics | `logistics/logistics_entities.py` | `LogisticsPartnerProfile` | `logistics_partner_profiles` | `partner.py` | `logistics` |
| logistics | `logistics/logistics_entities.py` | `LogisticsPartnerServiceArea` | `logistics_partner_service_areas` | `partner.py` | `logistics` |
| logistics | `logistics/logistics_entities.py` | `LogisticsPricingProfile` | `logistics_pricing_profiles` | `pricing.py` | `logistics` |
| logistics | `./admin.py` | `LogisticsSettlement` | `logistics_settlements` | `settlement.py` | `logistics` |
| logistics | `logistics/logistics_entities.py` | `LogisticsVehicleRule` | `logistics_vehicle_rules` | `pricing.py` | `logistics` |
| logistics | `./country_control.py` | `ParcelLocationTracker` | `parcel_location_trackers` | `tracking.py` | `logistics` |
| logistics | `logistics/logistics_entities.py` | `Shipment` | `shipments` | `shipment.py` | `logistics` |
| logistics | `./admin.py` | `ShipmentConfirmation` | `shipment_confirmations` | `shipment.py` | `logistics` |
| logistics | `logistics/logistics_entities.py` | `ShipmentEvent` | `shipment_events` | `shipment.py` | `logistics` |
| logistics | `./admin.py` | `ShippingCarrier` | `shipping_carriers` | `carrier.py` | `logistics` |
| logistics | `./admin.py` | `ShippingZone` | `shipping_zones` | `zone.py` | `logistics` |
| logistics | `./country_control.py` | `ShopWarehouseLocation` | `shop_warehouse_locations` | `partner.py` | `logistics` |
| logistics | `./erp.py` | `StockMovement` | `stock_movements` | `stock.py` | `logistics` |
| logistics | `./erp.py` | `Warehouse` | `warehouses` | `warehouse.py` | `logistics` |
| media | `./media_models.py` | `MediaAsset` | `media_assets` | `asset.py` | `media` |
| media | `./media_models.py` | `MediaUploadSession` | `media_upload_sessions` | `upload.py` | `media` |
| media | `./upload_job.py` | `UploadJob` | `upload_jobs` | `upload.py` | `media` |
| orders | `orders/order_entities.py` | `Order` | `orders` | `order.py` | `orders` |
| orders | `orders/order_entities.py` | `OrderItem` | `order_items` | `order.py` | `orders` |
| orders | `orders/order_entities.py` | `OrderLogisticsAllocation` | `order_logistics_allocations` | `allocation.py` | `orders` |
| orders | `orders/order_entities.py` | `OrderNotification` | `order_notifications` | `order.py` | `orders` |
| orders | `orders/order_entities.py` | `ReturnRequest` | `return_requests` | `return.py` | `orders` |
| orders | `./erp.py` | `SalesOrder` | `sales_orders` | `orders_misc.py` | `orders` |
| orders | `./erp.py` | `SalesOrderLine` | `sales_order_lines` | `orders_misc.py` | `orders` |
| payments | `./payments.py` | `LogisticsPartnerPayout` | `logistics_partner_payouts` | `payout.py` | `payments` |
| payments | `./payments.py` | `Payment` | `payments` | `payment.py` | `payments` |
| payments | `./payments.py` | `PaymentGatewayConnection` | `payment_gateway_connections` | `gateway.py` | `payments` |
| payments | `./country_control.py` | `PaymentOrchestratorSync` | `payment_orchestrator_sync` | `gateway.py` | `payments` |
| payments | `./admin.py` | `PaymentProviderConfig` | `payment_provider_configs` | `gateway.py` | `payments` |
| payments | `./payments.py` | `PaymentReconciliationRun` | `payment_reconciliation_runs` | `reconciliation.py` | `payments` |
| payments | `./payments.py` | `Payout` | `payouts` | `payout.py` | `payments` |
| rbac | `permissions/permission_entities.py` | `Permission` | `permissions` | `catalog.py` | `rbac` |
| rbac | `permissions/permission_entities.py` | `PermissionAuditLog` | `permission_audit_log` | `audit.py` | `rbac` |
| rbac | `permissions/permission_entities.py` | `PermissionCategory` | `permission_categories` | `catalog.py` | `rbac` |
| rbac | `permissions/permission_entities.py` | `RolePermissionAssignment` | `role_permission_assignments` | `assignment.py` | `rbac` |
| rbac | `./admin.py` | `RolePermissionSetting` | `role_permission_settings` | `assignment.py` | `rbac` |
| rbac | `permissions/permission_entities.py` | `UserPermissionOverride` | `user_permission_overrides` | `assignment.py` | `rbac` |
| security | `./admin.py` | `APIKey` | `api_keys` | `key.py` | `security` |
| security | `./fraud.py` | `CreditCardBin` | `credit_card_bins` | `fraud.py` | `security` |
| security | `./fraud.py` | `DLPViolation` | `dlp_violations` | `dlp.py` | `security` |
| security | `./fraud.py` | `DeviceFingerprint` | `device_fingerprints` | `fraud.py` | `security` |
| security | `./fraud.py` | `FraudAlert` | `fraud_alerts` | `fraud.py` | `security` |
| security | `./fraud.py` | `FraudBlacklist` | `fraud_blacklist` | `fraud.py` | `security` |
| security | `./fraud.py` | `FraudCase` | `fraud_cases` | `fraud.py` | `security` |
| security | `./fraud.py` | `FraudCaseAssignment` | `fraud_case_assignments` | `fraud.py` | `security` |
| security | `./fraud.py` | `FraudEvent` | `fraud_events` | `fraud.py` | `security` |
| security | `./fraud.py` | `FraudRule` | `fraud_rules` | `fraud.py` | `security` |
| security | `./fraud.py` | `FraudScoringLog` | `fraud_scoring_logs` | `fraud.py` | `security` |
| security | `./fraud.py` | `IPAccountLinkage` | `ip_account_linkages` | `fraud.py` | `security` |
| security | `./fraud.py` | `IPReputation` | `ip_reputations` | `fraud.py` | `security` |
| security | `./fraud.py` | `LogisticsFraudIndicator` | `logistics_fraud_indicators` | `fraud.py` | `security` |
| security | `./fraud.py` | `ManualReviewQueue` | `manual_review_queue` | `fraud.py` | `security` |
| security | `./fraud.py` | `ReturnAbusePattern` | `return_abuse_patterns` | `fraud.py` | `security` |
| security | `./fraud.py` | `SupplierFraudIndicator` | `supplier_fraud_indicators` | `fraud.py` | `security` |
| security | `comms/core.py` | `UserSession` | `user_sessions` | `session.py` | `security` |
| security | `./fraud.py` | `VelocityCounter` | `fraud_velocity_counters` | `fraud.py` | `security` |
| suppliers | `./onboarding.py` | `DocumentVerification` | `document_verifications` | `onboarding.py` | `suppliers` |
| suppliers | `./erp.py` | `GoodsReceiptLine` | `goods_receipt_lines` | `procurement.py` | `suppliers` |
| suppliers | `./erp.py` | `GoodsReceiptNote` | `goods_receipt_notes` | `procurement.py` | `suppliers` |
| suppliers | `./onboarding.py` | `KYCVerification` | `kyc_verifications` | `onboarding.py` | `suppliers` |
| suppliers | `./onboarding.py` | `OCRResult` | `ocr_results` | `onboarding.py` | `suppliers` |
| suppliers | `./onboarding.py` | `OnboardingPipeline` | `onboarding_pipelines` | `onboarding.py` | `suppliers` |
| suppliers | `./onboarding.py` | `OnboardingStep` | `onboarding_steps` | `onboarding.py` | `suppliers` |
| suppliers | `./erp.py` | `PurchaseOrder` | `purchase_orders` | `procurement.py` | `suppliers` |
| suppliers | `./erp.py` | `PurchaseOrderLine` | `purchase_order_lines` | `procurement.py` | `suppliers` |
| suppliers | `comms/suppliers.py` | `SupplierBadge` | `supplier_badges` | `badge.py` | `suppliers` |
| suppliers | `comms/suppliers.py` | `SupplierBadgeBillingHistory` | `supplier_badge_billing_history` | `badge.py` | `suppliers` |
| suppliers | `comms/suppliers.py` | `SupplierBadgeCatalog` | `supplier_badge_catalog` | `badge.py` | `suppliers` |
| suppliers | `./admin.py` | `SupplierBankAccount` | `supplier_bank_accounts` | `profile.py` | `suppliers` |
| suppliers | `./admin.py` | `SupplierCountryCommission` | `supplier_country_commissions` | `commission.py` | `suppliers` |
| suppliers | `./admin.py` | `SupplierDispute` | `supplier_disputes` | `dispute.py` | `suppliers` |
| suppliers | `comms/suppliers.py` | `SupplierDocument` | `supplier_documents` | `profile.py` | `suppliers` |
| suppliers | `comms/suppliers.py` | `SupplierNotificationPreference` | `supplier_notification_preferences` | `profile.py` | `suppliers` |
| suppliers | `./country_control.py` | `SupplierOnboardingSync` | `supplier_onboarding_sync` | `onboarding.py` | `suppliers` |
| suppliers | `comms/suppliers.py` | `SupplierProfile` | `supplier_profiles` | `profile.py` | `suppliers` |

## Files to DELETE (not migration sources)

**Two deletion waves — order matters:**

**Wave A — after Phase 2 (de-duplicate, safe because twins are orphaned):**
The ~314 stale duplicate model classes living in `backend/domains/{d}/models/*.py` that mirror `backend/models` and are not yet wired into the live `Base`. Delete the domain-side twin; keep the `backend/models` definition. (Empty/`Base`-only `__init__.py` files in `backend/domains/{d}/models` are kept as relocation targets.)

**Wave B — after Phase 4 (retire `backend/models`):**
The following `backend/models` root-level shims/duplicates are superseded by canonical packages/files. Do **not** delete while `backend/models` is still the live source.

- `models/communication.py` (shim → `models/comms/`)
- `models/core.py` (shim)
- `models/countries.py` (shim → `models/geography/`)
- `models/country_enhancements.py` (shim → `models/geography/`)
- `models/finance.py` (DEAD duplicate of `models/finance/general_ledger.py`)
- `models/logistics.py` (DEAD duplicate of `models/logistics/logistics_entities.py`)
- `models/marketing.py` (shim → `models/comms/`)
- `models/orders.py` (DEAD duplicate of `models/orders/order_entities.py`)
- `models/permissions.py` (DEAD duplicate of `models/permissions/permission_entities.py`)
- `models/suppliers.py` (shim → `models/comms/`)
- `models/supplier/` (shim, canonical definitions live in `models/comms/`)

Finally, after all imports are repointed (Phase 4), delete the entire `backend/models` package (or keep it as a documented `_legacy` shim for one release).