# K-08 ORM vs Migration Chain Delta Table

## Summary
Database is at migration `20261004_0013`; head is `20261004_0018` (5 unapplied migrations).
This delta focuses on the **confirmed schema gaps** between the ORM metadata and the
migration chain that require new migrations.

---

## Confirmed Gaps Requiring New Migrations

| # | Schema | Table | Column / Issue | ORM Declaration | Migration Chain State | Gap Kind | Risk |
|---|--------|-------|----------------|-----------------|----------------------|----------|------|
| 1 | catalog | products | currency | String(3) NOT NULL DEFAULT 'USD' | ABSENT | MISSING_IN_MIGRATION | Low — additive column |
| 2 | accounts | mfa_factors | secret | EncryptedString(512) (renders VARCHAR when encryptor active; impl=Text) | String(1024) per 0016 | TYPE_MISMATCH | Medium — type change on live table |
| 3 | accounts | mfa_factors | entire table | Present in ORM; created by create_all outside chain | No create_table migration | TABLE_NOT_IN_CHAIN | Low — IF NOT EXISTS guard needed |
| 4 | catalog | products | category_id | Integer, FK→catalog.categories(id) ON DELETE RESTRICT | Plain Integer, no FK | MISSING_FK_CONSTRAINT | Medium — requires DROP/CREATE constraint |
| 5 | catalog | products | supplier_id | Integer, FK→accounts.users(id) ON DELETE SET NULL | Plain Integer, no FK | MISSING_FK_CONSTRAINT | Medium — requires DROP/CREATE constraint |
| 6 | catalog | products | country_code | String(2), FK→country.country_configs(code) ON DELETE RESTRICT | String(3), no FK | TYPE_AND_FK_MISMATCH | Medium — type shrink + FK add |
| 7 | catalog | products | is_deleted | Boolean NOT NULL DEFAULT false, indexed | Boolean nullable=True, no default, no index | NULLABLE_AND_DEFAULT_MISMATCH | Low — alter column |
| 8 | catalog | products | created_at | DateTime NOT NULL DEFAULT now() | DateTime nullable=True, no default | MISSING_SERVER_DEFAULT | Low — alter column default |
| 9 | catalog | products | updated_at | DateTime DEFAULT now() ON UPDATE now() | DateTime nullable=True, no default | MISSING_SERVER_DEFAULT | Low — alter column default |
| 10 | accounts | mfa_factors | version | NOT in ORM model | Integer NOT NULL DEFAULT 1 (added by 0013) | EXTRA_IN_DB | Low — column exists in DB but not declared in ORM |

---

## Migrations Covered by Existing Chain (No Action Needed)

| Schema | Table | Column | Covered By |
|--------|-------|--------|------------|
| audit | audit_logs | worm_hash, worm_prev_hash | 0017 |
| audit | audit_logs | version | 0012 |
| suppliers | supplier_disputes | updated_at, is_deleted | 0009 |
| suppliers | supplier_disputes | version | 0013 |
| comms | entity_chat_threads | created_at, updated_at defaults | 0018 |
| comms | chat_messages | created_at, updated_at defaults | 0018 (create table) |
| comms | chat_rooms | created_at, updated_at defaults | 0018 (create table) |
| comms | chat_participants | created_at, updated_at defaults | 0018 (create table) |
| comms | campaigns | created_at, updated_at defaults | 0018 (create table) |
| country | country_tax_rules | created_at, updated_at defaults | 0018 (create table) |
| comms | faqs | created_at default | 0011 |
| comms | announcements | updated_at default | 0011 |
| comms | internal_emails | updated_at default | 0011 |
| comms | proxy_channels | updated_at default | 0011 |
| logistics | logistics_* (8 tables) | created_at default | 0001 |

---

## Notes

- `PermissionGate` model does **not exist** in the codebase; no action needed.
- `accounts.mfa_factors` was created by ORM `create_all` outside the migration chain.
  New migration 0019+ will use `IF NOT EXISTS` guard so it is safe on production.
- `catalog.products` originated as `commerce.products` in baseline, moved to `catalog`
  schema by migration `20260821_split_commerce`. All column drift below is relative
  to the current `catalog.products` state.
- `EncryptedString(512)` impl is `Text`; with `field_encryptor` active it renders as
  `String(_encrypted_storage_length(512))` (observed VARCHAR(725) in task notes).
  Migration 0016 set `String(1024)` which is wider than ORM expects.
