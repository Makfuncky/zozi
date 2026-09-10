# ZOZI Platform — Data Dictionary

> AUTO-GENERATED from SQLAlchemy metadata. Do NOT edit by hand.
> Run `python scripts/generate_data_dictionary.py` to regenerate.

**Total tables:** 321

---

## Table of Contents

- [ACCOUNTS](#accounts) (20 tables)
- [ANALYTICS](#analytics) (2 tables)
- [AUDIT](#audit) (2 tables)
- [CATALOG](#catalog) (15 tables)
- [COMMS](#comms) (53 tables)
- [COUNTRY](#country) (33 tables)
- [CUSTOMERS](#customers) (3 tables)
- [FINANCE](#finance) (58 tables)
- [GOVERNANCE](#governance) (34 tables)
- [HR](#hr) (31 tables)
- [LOGISTICS](#logistics) (25 tables)
- [ORDERS](#orders) (5 tables)
- [PROMOTIONS](#promotions) (9 tables)
- [PUBLIC](#public) (2 tables)
- [SECURITY](#security) (21 tables)
- [SUPPLIERS](#suppliers) (8 tables)

---

## ACCOUNTS

*Schema: `accounts` · 20 tables*

### `accounts.accounts.addresses`

*Table: `accounts.accounts.addresses`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| label | string |  |  |  | Y |  |
| full_name | string |  |  |  |  |  |
| phone | string |  |  |  | Y |  |
| address_line1 | string |  |  |  |  |  |
| address_line2 | string |  |  |  | Y |  |
| city | string |  |  |  |  |  |
| state | string |  |  |  | Y |  |
| postal_code | string |  |  |  | Y |  |
| country | string |  |  |  | Y | US |
| is_default | boolean |  |  |  | Y | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  |  |  |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_accounts_addresses_user_id` (user_id)
- `ix_accounts_addresses_country_code` (country_code)
- `ix_accounts_addresses_id` (id)

**Foreign Keys:**

- `user_id` → `accounts.users.id`

---

### `accounts.accounts.cart_items`

*Table: `accounts.accounts.cart_items`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| product_id | integer |  | Y |  |  |  |
| quantity | integer |  |  |  | Y | 1 |
| selected_size | string |  |  |  |  |  |
| selected_color | string |  |  |  |  |  |
| variant_id | integer |  |  |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  |  |  |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_accounts_cart_items_country_code` (country_code)
- `ix_accounts_cart_items_product_id` (product_id)
- `ix_cart_items_created` (created_at)
- `ix_cart_items_user_product` (user_id, product_id)
- `ix_accounts_cart_items_id` (id)
- `ix_accounts_cart_items_user_id` (user_id)

**Foreign Keys:**

- `user_id` → `accounts.users.id`
- `product_id` → `catalog.products.id`

---

### `accounts.accounts.carts`

*Table: `accounts.accounts.carts`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  |  |  |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_accounts_carts_id` (id)
- `ix_accounts_carts_user_id` (user_id)
- `ix_accounts_carts_country_code` (country_code)

**Foreign Keys:**

- `user_id` → `accounts.users.id`

---

### `accounts.accounts.email_verification_tokens`

*Table: `accounts.accounts.email_verification_tokens`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| token | string |  |  | Y |  |  |
| expires_at | datetime |  |  |  |  |  |
| is_used | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_accounts_email_verification_tokens_id` (id)
- `ix_accounts_email_verification_tokens_user_id` (user_id)
- `ix_accounts_email_verification_tokens_country_code` (country_code)

**Foreign Keys:**

- `user_id` → `accounts.users.id`

---

### `accounts.accounts.logistics_partner_bank_accounts`

*Table: `accounts.accounts.logistics_partner_bank_accounts`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| partner_id | integer |  | Y |  |  |  |
| account_number | string |  |  |  | Y |  |
| bank_name | string |  |  |  |  |  |
| beneficiary_name | string |  |  |  | Y |  |
| branch_name | string |  |  |  | Y |  |
| iban | string |  |  |  | Y |  |
| swift_code | string |  |  |  | Y |  |
| routing_number | string |  |  |  | Y |  |
| currency | string |  |  |  | Y |  |
| bank_country | string |  |  |  | Y |  |
| verification_status | string |  |  |  | Y | pending |
| verification_note | text |  |  |  | Y |  |
| provider | string |  |  |  | Y |  |
| provider_recipient_id | string |  |  |  | Y |  |
| provider_status | string |  |  |  | Y |  |
| provider_last_synced_at | datetime |  |  |  | Y |  |
| verified_at | datetime |  |  |  | Y |  |
| verified_by_id | integer |  | Y |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_accounts_logistics_partner_bank_accounts_id` (id)
- `ix_accounts_logistics_partner_bank_accounts_is_deleted` (is_deleted)
- `ix_accounts_logistics_partner_bank_accounts_country_code` (country_code)

**Foreign Keys:**

- `partner_id` → `logistics.logistics_partners.id`
- `verified_by_id` → `accounts.users.id`

---

### `accounts.accounts.mfa_factors`

*Table: `accounts.accounts.mfa_factors`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| factor_type | enum |  |  |  |  |  |
| secret | string |  |  |  |  |  |
| enabled | boolean |  |  |  |  | True |
| created_at | datetime |  |  |  |  | now() |
| last_used_at | datetime |  |  |  | Y |  |
| backup_codes | json |  |  |  | Y |  |
| country_code | string |  |  |  | Y |  |
| updated_at | datetime |  |  |  | Y | now() |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_accounts_mfa_factors_country_code` (country_code)
- `ix_mfa_factors_factor_type` (factor_type)
- `ix_mfa_factors_user_id` (user_id)

**Foreign Keys:**

- `user_id` → `accounts.users.id`

---

### `accounts.accounts.ocr_results`

*Table: `accounts.accounts.ocr_results`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| document_verification_id | integer |  | Y | Y |  |  |
| extracted_text | text |  |  |  | Y |  |
| confidence_score | numeric |  |  |  | Y |  |
| fields | json |  |  |  | Y |  |
| processed_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7AFF2A680> |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  |  |  |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_accounts_ocr_results_country_code` (country_code)
- `ix_accounts_ocr_results_id` (id)
- UNIQUE `ix_accounts_ocr_results_document_verification_id` (document_verification_id)

**Foreign Keys:**

- `document_verification_id` → `security.document_verifications.id`

---

### `accounts.accounts.otp_codes`

*Table: `accounts.accounts.otp_codes`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| purpose | string |  |  |  |  |  |
| channel | string |  |  |  |  | email |
| destination | string |  |  |  |  |  |
| code_hash | string |  |  |  |  |  |
| expires_at | datetime |  |  |  |  |  |
| attempts | integer |  |  |  | Y | 0 |
| verified | boolean |  |  |  | Y | False |
| country_code | string |  | Y |  |  |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_accounts_otp_codes_code_hash` (code_hash)
- `ix_accounts_otp_codes_expires_at` (expires_at)
- `ix_accounts_otp_codes_country_code` (country_code)
- `ix_accounts_otp_codes_user_id` (user_id)

**Foreign Keys:**

- `user_id` → `accounts.users.id`
- `country_code` → `country.country_configs.code`

---

### `accounts.accounts.password_histories`

*Table: `accounts.accounts.password_histories`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| password_hash | string |  |  |  |  |  |
| created_at | datetime |  |  |  |  | now() |
| country_code | string |  |  |  | Y |  |
| updated_at | datetime |  |  |  | Y | now() |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_password_histories_user_id` (user_id)
- `ix_accounts_password_histories_country_code` (country_code)

**Foreign Keys:**

- `user_id` → `accounts.users.id`

---

### `accounts.accounts.password_reset_tokens`

*Table: `accounts.accounts.password_reset_tokens`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| token | string |  |  | Y |  |  |
| expires_at | datetime |  |  |  |  |  |
| is_used | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_accounts_password_reset_tokens_user_id` (user_id)
- `ix_accounts_password_reset_tokens_country_code` (country_code)
- `ix_accounts_password_reset_tokens_id` (id)

**Foreign Keys:**

- `user_id` → `accounts.users.id`

---

### `accounts.accounts.refresh_token_families`

*Table: `accounts.accounts.refresh_token_families`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| family_id | guid |  |  |  |  | <function uuid4 at 0x000001C7AFD440D0> |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| revoked_at | datetime |  |  |  | Y |  |
| reused_at | datetime |  |  |  | Y |  |
| ip_address | string |  |  |  | Y |  |
| user_agent | string |  |  |  | Y |  |
| country_code | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_accounts_refresh_token_families_country_code` (country_code)
- `ix_refresh_token_families_family_id` (family_id)
- `ix_refresh_token_families_user_id` (user_id)

**Foreign Keys:**

- `user_id` → `accounts.users.id`

---

### `accounts.accounts.revoked_tokens`

*Table: `accounts.accounts.revoked_tokens`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| token | string |  |  | Y |  |  |
| expires_at | datetime |  |  |  |  |  |
| revoked_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_accounts_revoked_tokens_country_code` (country_code)
- `ix_accounts_revoked_tokens_id` (id)
- `ix_accounts_revoked_tokens_user_id` (user_id)

**Foreign Keys:**

- `user_id` → `accounts.users.id`

---

### `accounts.accounts.social_identities`

*Table: `accounts.accounts.social_identities`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| provider | string |  |  |  |  |  |
| provider_user_id | string |  |  |  |  |  |
| email | string |  |  |  |  |  |
| full_name | string |  |  |  | Y |  |
| raw_data | json |  |  |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  |  |  |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_accounts_social_identities_user_id` (user_id)
- `ix_accounts_social_identities_country_code` (country_code)

**Foreign Keys:**

- `user_id` → `accounts.users.id`

---

### `accounts.accounts.supplier_bank_accounts`

*Table: `accounts.accounts.supplier_bank_accounts`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| supplier_id | integer |  | Y |  |  |  |
| account_number | string |  |  |  | Y |  |
| bank_name | string |  |  |  |  |  |
| beneficiary_name | string |  |  |  | Y |  |
| branch_name | string |  |  |  | Y |  |
| iban | string |  |  |  | Y |  |
| swift_code | string |  |  |  | Y |  |
| routing_number | string |  |  |  | Y |  |
| currency | string |  |  |  | Y |  |
| bank_country | string |  |  |  | Y |  |
| verification_status | string |  |  |  | Y | pending |
| verification_note | text |  |  |  | Y |  |
| provider | string |  |  |  | Y |  |
| provider_recipient_id | string |  |  |  | Y |  |
| provider_status | string |  |  |  | Y |  |
| provider_last_synced_at | datetime |  |  |  | Y |  |
| verified_at | datetime |  |  |  | Y |  |
| verified_by_id | integer |  | Y |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_accounts_supplier_bank_accounts_id` (id)
- `ix_accounts_supplier_bank_accounts_is_deleted` (is_deleted)
- `ix_accounts_supplier_bank_accounts_country_code` (country_code)

**Foreign Keys:**

- `supplier_id` → `accounts.users.id`
- `verified_by_id` → `accounts.users.id`

---

### `accounts.accounts.user_consents`

*Table: `accounts.accounts.user_consents`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| consent_type | string |  |  |  |  |  |
| granted | boolean |  |  |  |  |  |
| granted_at | datetime |  |  |  |  | now() |
| revoked_at | datetime |  |  |  | Y |  |
| ip_address | string |  |  |  | Y |  |
| user_agent | string |  |  |  | Y |  |
| consent_version | string |  |  |  | Y |  |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_accounts_user_consents_country_code` (country_code)
- `ix_user_consents_consent_type` (consent_type)
- `ix_user_consents_user_id` (user_id)

**Foreign Keys:**

- `user_id` → `accounts.users.id`

---

### `accounts.accounts.user_devices`

*Table: `accounts.accounts.user_devices`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| device_fingerprint | string |  |  |  |  |  |
| fingerprint_hash | string |  |  |  | Y |  |
| device_id | string |  |  |  | Y |  |
| is_active | boolean |  |  |  |  | True |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_accounts_user_devices_id` (id)
- `ix_accounts_user_devices_country_code` (country_code)
- `ix_accounts_user_devices_user_id` (user_id)
- `ix_accounts_user_devices_fingerprint` (fingerprint_hash)

**Foreign Keys:**

- `user_id` → `accounts.users.id`

---

### `accounts.accounts.user_login_histories`

*Table: `accounts.accounts.user_login_histories`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| ip_address | string |  |  |  | Y |  |
| user_agent | text |  |  |  | Y |  |
| success | boolean |  |  |  |  | True |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_accounts_user_login_history_user_id` (user_id)
- `ix_accounts_user_login_history_created` (created_at)
- `ix_accounts_user_login_histories_id` (id)
- `ix_accounts_user_login_histories_country_code` (country_code)

**Foreign Keys:**

- `user_id` → `accounts.users.id`

---

### `accounts.accounts.user_preferences`

*Table: `accounts.accounts.user_preferences`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| key | string |  |  |  |  |  |
| value | json |  |  |  | Y |  |
| updated_at | datetime |  |  |  |  | now() |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_accounts_user_preferences_country_code` (country_code)

**Foreign Keys:**

- `user_id` → `accounts.users.id`

---

### `accounts.accounts.user_sessions`

*Table: `accounts.accounts.user_sessions`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| token_jti | string |  |  |  |  |  |
| refresh_token_jti | string |  |  |  | Y |  |
| ip_address | string |  |  |  | Y |  |
| user_agent | text |  |  |  | Y |  |
| device_fingerprint | string |  |  |  | Y |  |
| is_active | boolean |  |  |  |  | True |
| expires_at | datetime |  |  |  |  |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_accounts_user_sessions_country_code` (country_code)
- `ix_accounts_user_sessions_id` (id)
- `ix_accounts_user_sessions_token_jti` (token_jti)
- `ix_accounts_user_sessions_user_id` (user_id)

**Foreign Keys:**

- `user_id` → `accounts.users.id`

---

### `accounts.accounts.users`

*Table: `accounts.accounts.users`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| email | string |  |  | Y |  |  |
| hashed_password | string |  |  |  |  |  |
| full_name | string |  |  |  | Y |  |
| role | string |  |  |  |  | customer |
| country_code | string |  |  |  |  | US |
| is_active | boolean |  |  |  |  | True |
| email_verified | boolean |  |  |  |  | False |
| staff_country_codes | text |  |  |  | Y |  |
| referred_by_user_id | integer |  | Y |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| is_deleted | boolean |  |  |  |  | False |
| profile_image | string |  |  |  | Y |  |
| phone | string |  |  |  | Y |  |
| referral_code | string |  |  | Y | Y |  |
| referral_points | integer |  |  |  |  | 0 |
| sharing_points | integer |  |  |  |  | 0 |
| preferred_language | string |  |  |  | Y |  |
| preferred_currency | string |  |  |  | Y |  |
| preferred_country | string |  |  |  | Y |  |

**Indexes:**

- `ix_accounts_users_id` (id)
- `ix_accounts_users_email` (email)
- UNIQUE `ix_accounts_users_referral_code` (referral_code)
- `ix_accounts_users_country_code` (country_code)

**Foreign Keys:**

- `referred_by_user_id` → `accounts.users.id`

---

## ANALYTICS

*Schema: `analytics` · 2 tables*

### `analytics.analytics.executive_news`

*Table: `analytics.analytics.executive_news`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| title | string |  |  |  |  |  |
| summary | text |  |  |  | Y |  |
| content | text |  |  |  | Y |  |
| url | string |  |  |  | Y |  |
| category | string |  |  |  | Y | general |
| priority | string |  |  |  | Y | normal |
| is_published | boolean |  |  |  | Y | False |
| ai_sentiment | string |  |  |  | Y | neutral |
| published_at | datetime |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| uuid | string |  |  | Y | Y | <function _new_uuid at 0x000001C7B1701B40> |
| version | integer |  |  |  |  | 1 |
| created_by_id | integer |  |  |  | Y |  |
| updated_by_id | integer |  |  |  | Y |  |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |

**Indexes:**

- UNIQUE `ix_analytics_executive_news_uuid` (uuid)
- `ix_analytics_executive_news_is_deleted` (is_deleted)
- `ix_analytics_executive_news_deleted_at` (deleted_at)
- `ix_analytics_executive_news_created_by_id` (created_by_id)
- `ix_analytics_executive_news_id` (id)
- `ix_analytics_executive_news_country_code` (country_code)
- `ix_executive_news_country_created` (country_code, created_at)
- `ix_analytics_executive_news_updated_by_id` (updated_by_id)

---

### `analytics.analytics.predictive_simulations`

*Table: `analytics.analytics.predictive_simulations`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| simulation_type | string |  |  |  |  |  |
| parameters_json | text |  |  |  |  |  |
| result_json | text |  |  |  |  |  |
| is_deleted | boolean |  |  |  |  | False |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| uuid | string |  |  | Y | Y | <function _new_uuid at 0x000001C7B17020E0> |
| version | integer |  |  |  |  | 1 |
| created_by_id | integer |  |  |  | Y |  |
| updated_by_id | integer |  |  |  | Y |  |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |

**Indexes:**

- `ix_analytics_predictive_simulations_country_code` (country_code)
- `ix_analytics_predictive_simulations_id` (id)
- `ix_analytics_predictive_simulations_updated_by_id` (updated_by_id)
- UNIQUE `ix_analytics_predictive_simulations_uuid` (uuid)
- `ix_predictive_simulations_country_created` (country_code, created_at)
- `ix_analytics_predictive_simulations_deleted_at` (deleted_at)
- `ix_analytics_predictive_simulations_created_by_id` (created_by_id)
- `ix_analytics_predictive_simulations_is_deleted` (is_deleted)

---

## AUDIT

*Schema: `audit` · 2 tables*

### `audit.audit.audit_logs`

*Table: `audit.audit.audit_logs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| action | string |  |  |  |  |  |
| entity_type | string |  |  |  |  |  |
| entity_id | integer |  |  |  | Y |  |
| user_id | integer |  | Y |  | Y |  |
| username | string |  |  |  | Y |  |
| user_role | string |  |  |  | Y |  |
| details | json |  |  |  | Y |  |
| ip_address | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| country_code | string |  | Y |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_audit_audit_logs_is_deleted` (is_deleted)
- `ix_audit_audit_logs_id` (id)
- `ix_audit_audit_logs_country_code` (country_code)

**Foreign Keys:**

- `user_id` → `accounts.users.id`
- `country_code` → `country.country_configs.code`

---

### `audit.audit.command_center_views`

*Table: `audit.audit.command_center_views`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| view_name | string |  |  |  |  |  |
| config | json |  |  |  | Y |  |
| is_default | boolean |  |  |  | Y | False |
| is_deleted | boolean |  |  |  |  | False |
| country_code | string |  | Y |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_audit_command_center_views_is_deleted` (is_deleted)
- `ix_audit_command_center_views_id` (id)
- `ix_audit_command_center_views_country_code` (country_code)

**Foreign Keys:**

- `user_id` → `accounts.users.id`
- `country_code` → `country.country_configs.code`

---

## CATALOG

*Schema: `catalog` · 15 tables*

### `catalog.catalog.ai_generation_logs`

*Table: `catalog.catalog.ai_generation_logs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| job_id | integer |  | Y |  |  |  |
| field | string |  |  |  |  |  |
| model_used | string |  |  |  | Y |  |
| prompt_hash | string |  |  |  | Y |  |
| tokens_used | numeric |  |  |  | Y |  |
| cost | numeric |  |  |  | Y |  |
| confidence | numeric |  |  |  | Y |  |
| country_code | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_catalog_ai_generation_logs_is_deleted` (is_deleted)
- `ix_catalog_ai_generation_logs_id` (id)
- `ix_catalog_ai_generation_logs_prompt_hash` (prompt_hash)
- `ix_catalog_ai_generation_logs_job_id` (job_id)
- `ix_catalog_ai_generation_logs_country_code` (country_code)

**Foreign Keys:**

- `job_id` → `catalog.ai_upload_jobs.id`

---

### `catalog.catalog.ai_staging_products`

*Table: `catalog.catalog.ai_staging_products`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| job_id | integer |  | Y |  |  |  |
| product_id | integer |  | Y |  | Y |  |
| name | string |  |  |  |  |  |
| description | text |  |  |  | Y |  |
| price | numeric |  |  |  | Y |  |
| stock | integer |  |  |  | Y | 0 |
| category | string |  |  |  | Y |  |
| subcategory | string |  |  |  | Y |  |
| color | string |  |  |  | Y |  |
| brand | string |  |  |  | Y |  |
| tags | json |  |  |  | Y |  |
| sizes | json |  |  |  | Y |  |
| materials | json |  |  |  | Y |  |
| image_url | string |  |  |  | Y |  |
| additional_media | json |  |  |  | Y |  |
| ai_description | text |  |  |  | Y |  |
| variant_axes | json |  |  |  | Y |  |
| attributes | json |  |  |  | Y |  |
| confidence_score | numeric |  |  |  | Y |  |
| requires_human_review | boolean |  |  |  | Y | False |
| country_code | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_catalog_ai_staging_products_job_id` (job_id)
- `ix_catalog_ai_staging_products_id` (id)
- `ix_catalog_ai_staging_products_is_deleted` (is_deleted)
- `ix_catalog_ai_staging_products_country_code` (country_code)

**Foreign Keys:**

- `job_id` → `catalog.ai_upload_jobs.id`
- `product_id` → `catalog.products.id`

---

### `catalog.catalog.ai_staging_variants`

*Table: `catalog.catalog.ai_staging_variants`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| job_id | integer |  | Y |  |  |  |
| staging_product_id | integer |  | Y |  |  |  |
| variant_key | string |  |  |  | Y |  |
| size | string |  |  |  | Y |  |
| color | string |  |  |  | Y |  |
| material | string |  |  |  | Y |  |
| pattern | string |  |  |  | Y |  |
| gender | string |  |  |  | Y |  |
| sku | string |  |  |  | Y |  |
| barcode | string |  |  |  | Y |  |
| product_code | string |  |  |  | Y |  |
| price | numeric |  |  |  | Y |  |
| stock | integer |  |  |  | Y | 0 |
| media_url | string |  |  |  | Y |  |
| attributes_json | text |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| confidence_score | numeric |  |  |  | Y |  |
| requires_human_review | boolean |  |  |  | Y | False |
| country_code | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_catalog_ai_staging_variants_job_id` (job_id)
- `ix_catalog_ai_staging_variants_staging_product_id` (staging_product_id)
- `ix_catalog_ai_staging_variants_country_code` (country_code)
- `ix_catalog_ai_staging_variants_id` (id)
- `ix_ai_staging_variants_job_staging` (job_id, staging_product_id)
- `ix_catalog_ai_staging_variants_variant_key` (variant_key)
- `ix_catalog_ai_staging_variants_is_deleted` (is_deleted)

**Foreign Keys:**

- `job_id` → `catalog.ai_upload_jobs.id`
- `staging_product_id` → `catalog.ai_staging_products.id`

---

### `catalog.catalog.ai_upload_jobs`

*Table: `catalog.catalog.ai_upload_jobs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| supplier_id | integer |  | Y |  |  |  |
| status | string |  |  |  |  | pending |
| model_used | string |  |  |  | Y |  |
| prompt_hash | string |  |  |  | Y |  |
| tokens_used | numeric |  |  |  | Y |  |
| source_media_json | text |  |  |  | Y |  |
| created_product_id | integer |  | Y |  | Y |  |
| error_log | text |  |  |  | Y |  |
| country_code | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_catalog_ai_upload_jobs_prompt_hash` (prompt_hash)
- `ix_catalog_ai_upload_jobs_country_code` (country_code)
- `ix_catalog_ai_upload_jobs_supplier_id` (supplier_id)
- `ix_catalog_ai_upload_jobs_is_deleted` (is_deleted)
- `ix_catalog_ai_upload_jobs_id` (id)
- `ix_catalog_ai_upload_jobs_status` (status)

**Foreign Keys:**

- `supplier_id` → `accounts.users.id`
- `created_product_id` → `catalog.products.id`

---

### `catalog.catalog.categories`

*Table: `catalog.catalog.categories`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| name | string |  |  |  |  |  |
| slug | string |  |  | Y | Y |  |
| description | text |  |  |  | Y |  |
| parent_id | integer |  | Y |  | Y |  |
| icon | string |  |  |  | Y |  |
| image_url | string |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| is_featured | boolean |  |  |  | Y | False |
| sort_order | integer |  |  |  | Y | 0 |
| commission_rate | numeric |  |  |  | Y |  |
| meta_title | string |  |  |  | Y |  |
| meta_description | text |  |  |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| path | string |  |  |  | Y |  |
| depth | integer |  |  |  | Y | 0 |

**Indexes:**

- `ix_catalog_categories_is_deleted` (is_deleted)
- `ix_catalog_categories_path` (path)
- UNIQUE `ix_catalog_categories_slug` (slug)
- `ix_catalog_categories_country_code` (country_code)
- `ix_catalog_categories_id` (id)

**Foreign Keys:**

- `parent_id` → `catalog.categories.id`

---

### `catalog.catalog.product_filter_metadatas`

*Table: `catalog.catalog.product_filter_metadatas`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| category_id | integer |  | Y |  | Y |  |
| filter_name | string |  |  |  |  |  |
| filter_type | string |  |  |  |  |  |
| display_order | integer |  |  |  |  | 0 |
| is_active | boolean |  |  |  |  | true |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_catalog_product_filter_metadatas_category_id` (category_id)
- `ix_catalog_product_filter_metadatas_id` (id)
- `ix_catalog_product_filter_metadatas_is_deleted` (is_deleted)
- `ix_catalog_product_filter_metadatas_country_code` (country_code)

**Foreign Keys:**

- `category_id` → `catalog.categories.id`

---

### `catalog.catalog.product_filter_options`

*Table: `catalog.catalog.product_filter_options`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| filter_metadata_id | integer |  | Y |  |  |  |
| option_value | string |  |  |  |  |  |
| option_display_name | string |  |  |  |  |  |
| product_count | integer |  |  |  |  | 0 |
| sort_order | integer |  |  |  |  | 0 |
| is_deleted | boolean |  |  |  |  | False |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_catalog_product_filter_options_filter_metadata_id` (filter_metadata_id)
- `ix_catalog_product_filter_options_id` (id)
- `ix_catalog_product_filter_options_is_deleted` (is_deleted)
- `ix_catalog_product_filter_options_country_code` (country_code)

**Foreign Keys:**

- `filter_metadata_id` → `catalog.product_filter_metadatas.id`

---

### `catalog.catalog.product_variants`

*Table: `catalog.catalog.product_variants`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| product_id | integer |  | Y |  |  |  |
| sku | string |  |  | Y | Y |  |
| title | string |  |  |  | Y |  |
| size | string |  |  |  | Y |  |
| color | string |  |  |  | Y |  |
| material | string |  |  |  | Y |  |
| pattern | string |  |  |  | Y |  |
| gender | string |  |  |  | Y |  |
| barcode | string |  |  | Y | Y |  |
| product_code | string |  |  |  | Y |  |
| price | numeric |  |  |  | Y |  |
| stock | integer |  |  |  | Y | 0 |
| media_url | string |  |  |  | Y |  |
| attributes_json | text |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| sort_order | integer |  |  |  | Y | 0 |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  | Y |  | Y |  |
| variant_key | string |  |  |  | Y |  |

**Indexes:**

- `ix_catalog_product_variants_color` (color)
- `ix_catalog_product_variants_country_code` (country_code)
- `ix_catalog_product_variants_id` (id)
- `ix_catalog_product_variants_gender` (gender)
- `ix_catalog_product_variants_size` (size)
- `ix_catalog_product_variants_material` (material)
- `ix_catalog_product_variants_is_deleted` (is_deleted)
- `ix_catalog_product_variants_variant_key` (variant_key)
- `ix_catalog_product_variants_pattern` (pattern)

**Foreign Keys:**

- `product_id` → `catalog.products.id`
- `country_code` → `country.country_configs.code`

---

### `catalog.catalog.product_videos`

*Table: `catalog.catalog.product_videos`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| product_id | integer |  | Y |  |  |  |
| video_url | string |  |  |  |  |  |
| thumbnail_url | string |  |  |  | Y |  |
| duration_seconds | integer |  |  |  | Y |  |
| video_type | string |  |  |  | Y |  |
| title | string |  |  |  | Y |  |
| description | text |  |  |  | Y |  |
| views_count | integer |  |  |  | Y | 0 |
| is_featured | boolean |  |  |  | Y | False |
| upload_status | string |  |  |  | Y | pending |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_catalog_product_videos_product_id` (product_id)
- `ix_catalog_product_videos_is_deleted` (is_deleted)
- `ix_catalog_product_videos_id` (id)
- `ix_catalog_product_videos_country_code` (country_code)

**Foreign Keys:**

- `product_id` → `catalog.products.id`

---

### `catalog.catalog.products`

*Table: `catalog.catalog.products`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| name | string |  |  |  |  |  |
| slug | string |  |  | Y | Y |  |
| description | text |  |  |  | Y |  |
| short_description | text |  |  |  | Y |  |
| ai_description | text |  |  |  | Y |  |
| sku | string |  |  | Y | Y |  |
| barcode | string |  |  | Y | Y |  |
| price | numeric |  |  |  |  |  |
| compare_price | numeric |  |  |  | Y |  |
| cost_price | numeric |  |  |  | Y |  |
| stock | integer |  |  |  | Y | 0 |
| low_stock_threshold | integer |  |  |  | Y | 5 |
| weight | numeric |  |  |  | Y |  |
| dimensions | string |  |  |  | Y |  |
| materials | json |  |  |  | Y |  |
| image_url | string |  |  |  | Y |  |
| images | json |  |  |  | Y |  |
| category | string |  |  |  | Y |  |
| category_id | integer |  | Y |  | Y |  |
| tags | json |  |  |  | Y |  |
| attributes | json |  |  |  | Y |  |
| supplier_id | integer |  | Y |  | Y |  |
| country_code | string |  | Y |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| is_featured | boolean |  |  |  | Y | False |
| is_digital | boolean |  |  |  | Y | False |
| is_verified | boolean |  |  |  | Y | True |
| moderation_status | string |  |  |  | Y | approved |
| brand | string |  |  |  | Y |  |
| color | string |  |  |  | Y |  |
| sizes | json |  |  |  | Y |  |
| rating | numeric |  |  |  | Y | 0 |
| sales_count | integer |  |  |  | Y | 0 |
| meta_title | string |  |  |  | Y |  |
| meta_description | text |  |  |  | Y |  |
| is_approved | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  | Y | False |
| discount_starts_at | datetime |  |  |  | Y |  |
| discount_ends_at | datetime |  |  |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| filter_attributes | json |  |  |  | Y |  |
| search_vector | json |  |  |  | Y |  |
| video_count | integer |  |  |  | Y | 0 |
| variant_axes | json |  |  |  | Y |  |
| bg_preset | string |  |  |  | Y |  |
| visibility_regions | text |  |  |  | Y |  |
| slug_hash | string |  |  | Y | Y |  |
| subcategory | string |  |  |  | Y |  |
| return_window_days | integer |  |  |  | Y | 10 |
| is_new | boolean |  |  |  | Y | False |

**Indexes:**

- `ix_catalog_products_country_code` (country_code)
- `ix_products_created_sort` (created_at, id)
- `ix_products_supplier_active` (supplier_id, is_active)
- `ix_products_category_active` (category, is_active)
- `ix_products_country_status` (country_code, moderation_status)
- `ix_catalog_products_id` (id)
- UNIQUE `ix_catalog_products_slug` (slug)
- UNIQUE `ix_catalog_products_slug_hash` (slug_hash)

**Foreign Keys:**

- `category_id` → `catalog.categories.id`
- `supplier_id` → `accounts.users.id`
- `country_code` → `country.country_configs.code`

---

### `catalog.catalog.reviews`

*Table: `catalog.catalog.reviews`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| product_id | integer |  | Y |  |  |  |
| user_id | integer |  | Y |  |  |  |
| rating | integer |  |  |  |  |  |
| title | string |  |  |  | Y |  |
| comment | text |  |  |  | Y |  |
| image_url | string |  |  |  | Y |  |
| is_approved | boolean |  |  |  | Y | False |
| is_deleted | boolean |  |  |  |  | False |
| is_verified_purchase | boolean |  |  |  | Y | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_catalog_reviews_country_code` (country_code)
- `ix_catalog_reviews_is_deleted` (is_deleted)
- `ix_catalog_reviews_id` (id)

**Foreign Keys:**

- `product_id` → `catalog.products.id`
- `user_id` → `accounts.users.id`

---

### `catalog.catalog.upload_jobs`

*Table: `catalog.catalog.upload_jobs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B00211B0> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| filename | string |  |  |  |  |  |
| stored_path | string |  |  |  | Y |  |
| content_type | string |  |  |  | Y |  |
| file_size | integer |  |  |  | Y |  |
| status | string |  |  |  |  | pending |
| progress | integer |  |  |  |  | 0 |
| error_log | text |  |  |  | Y |  |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B00212D0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0021240> |

**Indexes:**

- `ix_catalog_upload_jobs_id` (id)
- `ix_catalog_upload_jobs_country_code` (country_code)
- `ix_catalog_upload_jobs_is_deleted` (is_deleted)
- `ix_catalog_upload_jobs_created_by` (created_by)
- `ix_upload_jobs_country_created` (country_code, created_at)
- `ix_catalog_upload_jobs_updated_by` (updated_by)
- `ix_catalog_upload_jobs_status` (status)

---

### `catalog.catalog.video_analytics`

*Table: `catalog.catalog.video_analytics`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| video_id | integer |  | Y |  |  |  |
| user_id | integer |  | Y |  | Y |  |
| event_type | string |  |  |  |  |  |
| watch_duration_seconds | integer |  |  |  | Y |  |
| device_type | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_catalog_video_analytics_is_deleted` (is_deleted)
- `ix_catalog_video_analytics_video_id` (video_id)
- `ix_catalog_video_analytics_user_id` (user_id)
- `ix_catalog_video_analytics_country_code` (country_code)
- `ix_catalog_video_analytics_id` (id)

**Foreign Keys:**

- `video_id` → `catalog.product_videos.id`
- `user_id` → `accounts.users.id`

---

### `catalog.catalog.wishlist_items`

*Table: `catalog.catalog.wishlist_items`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| product_id | integer |  | Y |  |  |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_catalog_wishlist_items_country_code` (country_code)
- `ix_catalog_wishlist_items_id` (id)
- `ix_catalog_wishlist_items_is_deleted` (is_deleted)

**Foreign Keys:**

- `user_id` → `accounts.users.id`
- `product_id` → `catalog.products.id`

---

### `catalog.catalog.wishlists`

*Table: `catalog.catalog.wishlists`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| product_id | integer |  | Y |  |  |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_catalog_wishlists_id` (id)
- `ix_catalog_wishlists_is_deleted` (is_deleted)
- `ix_catalog_wishlists_country_code` (country_code)

**Foreign Keys:**

- `user_id` → `accounts.users.id`
- `product_id` → `catalog.products.id`

---

## COMMS

*Schema: `comms` · 53 tables*

### `comms.comms.announcements`

*Table: `comms.comms.announcements`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0DBDCF0> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| title | string |  |  |  |  |  |
| content | text |  |  |  |  |  |
| is_active | boolean |  |  |  | Y | True |
| starts_at | datetime |  |  |  | Y |  |
| ends_at | datetime |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0DBE170> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0DBE200> |

**Indexes:**

- `ix_comms_announcements_is_deleted` (is_deleted)
- `ix_comms_announcements_created_by` (created_by)
- `ix_comms_announcements_updated_by` (updated_by)
- `ix_comms_announcements_id` (id)

---

### `comms.comms.campaign_recipients`

*Table: `comms.comms.campaign_recipients`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0F72950> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| campaign_id | integer |  | Y |  |  |  |
| user_id | integer |  |  |  |  |  |
| email | string |  |  |  |  |  |
| status_code | string |  |  |  | Y | pending |
| sent_at | datetime |  |  |  | Y |  |
| delivered_at | datetime |  |  |  | Y |  |
| opened_at | datetime |  |  |  | Y |  |
| clicked_at | datetime |  |  |  | Y |  |
| bounced_at | datetime |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0F729E0> |

**Indexes:**

- `ix_comms_campaign_recipients_created_by` (created_by)
- `ix_comms_campaign_recipients_id` (id)
- `ix_comms_campaign_recipients_campaign_id` (campaign_id)
- `ix_comms_campaign_recipients_updated_by` (updated_by)
- `ix_comms_campaign_recipients_is_deleted` (is_deleted)

**Foreign Keys:**

- `campaign_id` → `comms.email_campaigns.id`

---

### `comms.comms.chat_attachments`

*Table: `comms.comms.chat_attachments`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0E930A0> |
| version | integer |  |  |  |  | 1 |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| message_id | integer |  |  |  |  |  |
| message_type | string |  |  |  |  | direct |
| attachment_type | string |  |  |  |  |  |
| file_url | string |  |  |  |  |  |
| file_name | string |  |  |  |  |  |
| file_size_bytes | integer |  |  |  |  |  |
| mime_type | string |  |  |  |  |  |
| thumbnail_url | string |  |  |  | Y |  |
| duration_seconds | integer |  |  |  | Y |  |
| waveform_json | text |  |  |  | Y |  |
| is_processed | boolean |  |  |  | Y | False |

**Indexes:**

- `ix_comms_chat_attachments_id` (id)
- `ix_comms_chat_attachments_created_by` (created_by)
- `ix_comms_chat_attachments_message_id` (message_id)
- `ix_comms_chat_attachments_updated_by` (updated_by)
- `ix_comms_chat_attachments_is_deleted` (is_deleted)

---

### `comms.comms.chat_read_receipts`

*Table: `comms.comms.chat_read_receipts`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0E92B00> |
| version | integer |  |  |  |  | 1 |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| message_id | integer |  |  |  |  |  |
| message_type | string |  |  |  |  | direct |
| employee_id | integer |  |  |  |  |  |
| read_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0E92C20> |

**Indexes:**

- `ix_comms_chat_read_receipts_created_by` (created_by)
- `ix_chat_read_receipts_employee` (employee_id)
- `ix_comms_chat_read_receipts_message_id` (message_id)
- `ix_comms_chat_read_receipts_updated_by` (updated_by)
- `ix_comms_chat_read_receipts_is_deleted` (is_deleted)
- `ix_comms_chat_read_receipts_id` (id)

---

### `comms.comms.communication_audit_trails`

*Table: `comms.comms.communication_audit_trails`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0E91510> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| entity_type | string |  |  |  |  |  |
| entity_id | integer |  |  |  |  |  |
| user_id | integer |  |  |  | Y |  |
| action | string |  |  |  |  |  |
| channel | string |  |  |  |  |  |
| content_preview | text |  |  |  | Y |  |
| metadata_json | json |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0E91630> |

**Indexes:**

- `ix_comm_entity` (entity_type, entity_id)
- `ix_comms_communication_audit_trails_is_deleted` (is_deleted)
- `ix_comms_communication_audit_trails_id` (id)
- `ix_comms_communication_audit_trails_created_by` (created_by)
- `ix_communication_audit_trail_metadata_json` (metadata_json)
- `ix_comms_communication_audit_trails_updated_by` (updated_by)
- `ix_comm_user` (user_id, created_at)

---

### `comms.comms.direct_chat_messages`

*Table: `comms.comms.direct_chat_messages`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| room_id | integer |  | Y |  |  |  |
| sender_id | integer |  | Y |  |  |  |
| message | text |  |  |  |  |  |
| message_type | string |  |  |  | Y | text |
| read_at | datetime |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0DBC430> |

**Indexes:**

- `ix_comms_direct_chat_messages_id` (id)
- `ix_comms_direct_chat_messages_is_deleted` (is_deleted)

**Foreign Keys:**

- `room_id` → `comms.direct_chat_rooms.id`
- `sender_id` → `accounts.users.id`

---

### `comms.comms.direct_chat_rooms`

*Table: `comms.comms.direct_chat_rooms`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| chat_id | string |  |  | Y |  |  |
| participant_one_id | integer |  | Y |  |  |  |
| participant_two_id | integer |  | Y |  |  |  |
| country_code | string |  | Y |  | Y |  |
| is_masked | boolean |  |  |  | Y | False |
| is_active | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0D028C0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0D02950> |

**Indexes:**

- `ix_comms_direct_chat_rooms_id` (id)
- `ix_comms_direct_chat_rooms_is_deleted` (is_deleted)
- UNIQUE `ix_comms_direct_chat_rooms_chat_id` (chat_id)

**Foreign Keys:**

- `participant_one_id` → `accounts.users.id`
- `participant_two_id` → `accounts.users.id`
- `country_code` → `country.country_configs.code`

---

### `comms.comms.email_campaign_logs`

*Table: `comms.comms.email_campaign_logs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0F72320> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| campaign_id | integer |  | Y |  |  |  |
| recipient_email | string |  |  |  |  |  |
| status_code | string |  |  |  | Y | sent |
| sent_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0F723B0> |
| delivered_at | datetime |  |  |  | Y |  |
| opened_at | datetime |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0F72440> |

**Indexes:**

- `ix_comms_email_campaign_logs_id` (id)
- `ix_comms_email_campaign_logs_campaign_id` (campaign_id)
- `ix_comms_email_campaign_logs_created_by` (created_by)
- `ix_comms_email_campaign_logs_updated_by` (updated_by)
- `ix_comms_email_campaign_logs_is_deleted` (is_deleted)

**Foreign Keys:**

- `campaign_id` → `comms.email_campaigns.id`

---

### `comms.comms.email_campaigns`

*Table: `comms.comms.email_campaigns`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0F709D0> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| name | string |  |  |  |  |  |
| subject | string |  |  |  |  |  |
| status_code | string |  |  |  | Y | draft |
| send_at | datetime |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0F70F70> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0F70EE0> |
| from_name | string |  |  |  | Y |  |
| target_audience | text |  |  |  | Y |  |
| scheduled_at | datetime |  |  |  | Y |  |
| sent_at | datetime |  |  |  | Y |  |
| sent_count | integer |  |  |  | Y | 0 |
| open_count | integer |  |  |  | Y | 0 |
| click_count | integer |  |  |  | Y | 0 |
| country_code | string |  |  |  |  |  |

**Indexes:**

- `ix_comms_email_campaigns_country_code` (country_code)
- `ix_comms_email_campaigns_updated_by` (updated_by)
- `ix_comms_email_campaigns_is_deleted` (is_deleted)
- `ix_comms_email_campaigns_id` (id)
- `ix_email_campaigns_country_created` (country_code, created_at)

---

### `comms.comms.email_delivery_events`

*Table: `comms.comms.email_delivery_events`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0F72EF0> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| event_type | string |  |  |  |  |  |
| recipient_email | string |  |  |  |  |  |
| subject | string |  |  |  | Y |  |
| status_code | string |  |  |  | Y | sent |
| details | json |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0F73010> |

**Indexes:**

- `ix_comms_email_delivery_events_is_deleted` (is_deleted)
- `ix_comms_email_delivery_events_id` (id)
- `ix_email_delivery_events_details` (details)
- `ix_comms_email_delivery_events_created_by` (created_by)
- `ix_comms_email_delivery_events_updated_by` (updated_by)

---

### `comms.comms.email_folders`

*Table: `comms.comms.email_folders`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0E93880> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| employee_id | integer |  |  |  |  |  |
| name | string |  |  |  |  |  |
| folder_type | string |  |  |  | Y | inbox |
| sort_order | integer |  |  |  | Y | 0 |
| is_system | boolean |  |  |  | Y | True |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0E93D00> |

**Indexes:**

- `ix_comms_email_folders_updated_by` (updated_by)
- `ix_comms_email_folders_id` (id)
- `ix_comms_email_folders_is_deleted` (is_deleted)
- `ix_comms_email_folders_created_by` (created_by)

---

### `comms.comms.email_runtime_configs`

*Table: `comms.comms.email_runtime_configs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0F73A30> |
| version | integer |  |  |  |  | 1 |
| created_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| provider | string |  |  |  | Y | environment |
| resend_api_key | string |  |  |  | Y |  |
| resend_webhook_secret | string |  |  |  | Y |  |
| smtp_host | string |  |  |  | Y |  |
| smtp_port | integer |  |  |  | Y | 587 |
| smtp_username | string |  |  |  | Y |  |
| smtp_password | string |  |  |  | Y |  |
| is_smtp_use_tls | boolean |  |  |  | Y | True |
| is_smtp_use_ssl | boolean |  |  |  | Y | False |
| smtp_timeout_seconds | integer |  |  |  | Y | 15 |
| email_from_default | string |  |  |  | Y |  |
| email_from_promotional | string |  |  |  | Y |  |
| email_from_transactional | string |  |  |  | Y |  |
| email_from_notification | string |  |  |  | Y |  |
| email_from_alert | string |  |  |  | Y |  |
| email_from_verification | string |  |  |  | Y |  |
| email_from_login_verification | string |  |  |  | Y |  |
| email_from_password_reset | string |  |  |  | Y |  |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0F73B50> |

**Indexes:**

- `ix_comms_email_runtime_configs_is_deleted` (is_deleted)
- `ix_comms_email_runtime_configs_created_by` (created_by)
- `ix_comms_email_runtime_configs_updated_by` (updated_by)
- `ix_comms_email_runtime_configs_id` (id)

---

### `comms.comms.email_suppressions`

*Table: `comms.comms.email_suppressions`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0F73490> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| email | string |  |  |  |  |  |
| reason | string |  |  |  |  |  |
| source | string |  |  |  |  |  |
| provider | string |  |  |  | Y |  |
| status_code | string |  |  |  | Y | active |
| notes | text |  |  |  | Y |  |
| suppressed_at | datetime |  |  |  | Y |  |
| last_event_at | datetime |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0F735B0> |

**Indexes:**

- `ix_comms_email_suppressions_email` (email)
- `ix_comms_email_suppressions_created_by` (created_by)
- `ix_comms_email_suppressions_updated_by` (updated_by)
- `ix_comms_email_suppressions_is_deleted` (is_deleted)
- `ix_comms_email_suppressions_id` (id)

---

### `comms.comms.email_templates`

*Table: `comms.comms.email_templates`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0F71120> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| name | string |  |  | Y |  |  |
| subject | string |  |  |  |  |  |
| content | text |  |  |  | Y |  |
| template_type | string |  |  |  | Y | marketing |
| is_active | boolean |  |  |  | Y | True |
| created_by | integer |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0F715A0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0F71630> |

**Indexes:**

- `ix_comms_email_templates_updated_by` (updated_by)
- `ix_comms_email_templates_id` (id)
- UNIQUE `ix_comms_email_templates_name` (name)
- `ix_comms_email_templates_is_deleted` (is_deleted)

---

### `comms.comms.employee_communication_threads`

*Table: `comms.comms.employee_communication_threads`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0E90A60> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| entity_id | integer |  |  |  |  |  |
| entity_type | string |  |  |  |  |  |
| participants | text |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0E90B80> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_comms_employee_communication_threads_created_by` (created_by)
- `ix_comms_employee_communication_threads_id` (id)
- `ix_emp_comm_country_created` (country_code, created_at)
- `ix_comms_employee_communication_threads_updated_by` (updated_by)
- `ix_emp_comm_entity` (entity_type, entity_id)
- `ix_comms_employee_communication_threads_is_deleted` (is_deleted)

---

### `comms.comms.entity_chat_messages`

*Table: `comms.comms.entity_chat_messages`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| thread_id | integer |  | Y |  |  |  |
| sender_id | integer |  | Y |  |  |  |
| message | text |  |  |  |  |  |
| message_type | string |  |  |  | Y | text |
| read_at | datetime |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0D039A0> |

**Indexes:**

- `ix_comms_entity_chat_messages_id` (id)
- `ix_comms_entity_chat_messages_is_deleted` (is_deleted)

**Foreign Keys:**

- `thread_id` → `comms.entity_chat_threads.id`
- `sender_id` → `accounts.users.id`

---

### `comms.comms.entity_chat_threads`

*Table: `comms.comms.entity_chat_threads`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| entity_type | string |  |  |  |  |  |
| entity_id | integer |  |  |  |  |  |
| title | string |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0D016C0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0D017E0> |

**Indexes:**

- `ix_comms_entity_chat_threads_id` (id)
- `ix_comms_entity_chat_threads_is_deleted` (is_deleted)
- `ix_entity_thread` (entity_type, entity_id)

---

### `comms.comms.escalation_sla_logs`

*Table: `comms.comms.escalation_sla_logs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| message_id | integer |  |  |  |  |  |
| message_type | string |  |  |  |  |  |
| original_recipient_id | integer |  | Y |  | Y |  |
| escalated_to_user_id | integer |  | Y |  | Y |  |
| escalated_to_role | string |  |  |  | Y |  |
| priority | string |  |  |  |  |  |
| elapsed_minutes | integer |  |  |  | Y | 0 |
| status | string |  |  |  | Y | pending |
| escalated_at | datetime |  |  |  | Y |  |
| acknowledged_at | datetime |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0D03490> |

**Indexes:**

- `ix_escalation_message` (message_id)
- `ix_comms_escalation_sla_logs_is_deleted` (is_deleted)
- `ix_escalation_status` (status)
- `ix_comms_escalation_sla_logs_id` (id)

**Foreign Keys:**

- `original_recipient_id` → `accounts.users.id`
- `escalated_to_user_id` → `accounts.users.id`

---

### `comms.comms.escalation_sla_rules`

*Table: `comms.comms.escalation_sla_rules`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| country_code | string |  | Y |  | Y |  |
| priority | string |  |  |  |  |  |
| escalate_after_minutes | integer |  |  |  |  |  |
| escalate_to_role | string |  |  |  |  |  |
| notify_via | string |  |  |  | Y | email,sms |
| is_active | boolean |  |  |  | Y | True |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B103A200> |

**Indexes:**

- `ix_comms_escalation_sla_rules_id` (id)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `comms.comms.external_contact_maskings`

*Table: `comms.comms.external_contact_maskings`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0E90C10> |
| version | integer |  |  |  |  | 1 |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| user_id | integer |  |  |  |  |  |
| external_contact_type | string |  |  |  |  |  |
| external_contact_id | integer |  |  |  |  |  |
| masked_phone | string |  |  |  | Y |  |
| masked_email | string |  |  |  | Y |  |

**Indexes:**

- `ix_masking_user` (user_id)
- `ix_comms_external_contact_maskings_updated_by` (updated_by)
- `ix_comms_external_contact_maskings_is_deleted` (is_deleted)
- `ix_comms_external_contact_maskings_id` (id)
- `ix_comms_external_contact_maskings_created_by` (created_by)

---

### `comms.comms.faqs`

*Table: `comms.comms.faqs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0DBE7A0> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| question | text |  |  |  |  |  |
| answer | text |  |  |  |  |  |
| category | string |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0DBE8C0> |
| country_code | string |  |  |  |  |  |

**Indexes:**

- `ix_comms_faqs_updated_by` (updated_by)
- `ix_faqs_country_created` (country_code, created_at)
- `ix_comms_faqs_is_deleted` (is_deleted)
- `ix_comms_faqs_id` (id)
- `ix_comms_faqs_created_by` (created_by)
- `ix_comms_faqs_country_code` (country_code)

---

### `comms.comms.flash_sale_items`

*Table: `comms.comms.flash_sale_items`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0F70940> |
| version | integer |  |  |  |  | 1 |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| flash_sale_id | integer |  | Y |  |  |  |
| product_id | integer |  | Y |  |  |  |
| original_price | numeric |  |  |  |  |  |
| discounted_price | numeric |  |  |  |  |  |
| country_code | string |  |  |  | Y |  |
| quantity_limit | integer |  |  |  | Y |  |

**Indexes:**

- `ix_comms_flash_sale_items_flash_sale_id` (flash_sale_id)
- `ix_comms_flash_sale_items_updated_by` (updated_by)
- `ix_flash_sale_items_country_created` (country_code, created_at)
- `ix_comms_flash_sale_items_is_deleted` (is_deleted)
- `ix_comms_flash_sale_items_id` (id)
- `ix_comms_flash_sale_items_product_id` (product_id)
- `ix_comms_flash_sale_items_created_by` (created_by)

**Foreign Keys:**

- `flash_sale_id` → `promotions.flash_sales.id`
- `product_id` → `catalog.products.id`

---

### `comms.comms.group_chat_members`

*Table: `comms.comms.group_chat_members`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| room_id | integer |  | Y |  |  |  |
| user_id | integer |  | Y |  |  |  |
| role | string |  |  |  | Y | member |
| joined_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0D02EF0> |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_comms_group_chat_members_is_deleted` (is_deleted)
- `ix_comms_group_chat_members_id` (id)

**Foreign Keys:**

- `room_id` → `comms.group_chat_rooms.id`
- `user_id` → `accounts.users.id`

---

### `comms.comms.group_chat_messages`

*Table: `comms.comms.group_chat_messages`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| room_id | integer |  | Y |  |  |  |
| sender_id | integer |  | Y |  |  |  |
| message | text |  |  |  |  |  |
| message_type | string |  |  |  | Y | text |
| read_at | datetime |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0DBD000> |

**Indexes:**

- `ix_comms_group_chat_messages_is_deleted` (is_deleted)
- `ix_comms_group_chat_messages_id` (id)

**Foreign Keys:**

- `room_id` → `comms.group_chat_rooms.id`
- `sender_id` → `accounts.users.id`

---

### `comms.comms.group_chat_rooms`

*Table: `comms.comms.group_chat_rooms`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| chat_id | string |  |  | Y |  |  |
| name | string |  |  |  |  |  |
| country_code | string |  | Y |  | Y |  |
| is_encrypted | boolean |  |  |  | Y | False |
| is_active | boolean |  |  |  | Y | True |
| created_by_id | integer |  | Y |  |  |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0DBC8B0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0DBC940> |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_comms_group_chat_rooms_id` (id)
- `ix_comms_group_chat_rooms_is_deleted` (is_deleted)
- UNIQUE `ix_comms_group_chat_rooms_chat_id` (chat_id)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`
- `created_by_id` → `accounts.users.id`

---

### `comms.comms.help_categories`

*Table: `comms.comms.help_categories`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0DBE950> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| name | string |  |  |  |  |  |
| description | text |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0DBEE60> |

**Indexes:**

- `ix_comms_help_categories_created_by` (created_by)
- `ix_comms_help_categories_updated_by` (updated_by)
- `ix_comms_help_categories_id` (id)
- `ix_comms_help_categories_is_deleted` (is_deleted)

---

### `comms.comms.incident_action_items`

*Table: `comms.comms.incident_action_items`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| war_room_id | integer |  | Y |  |  |  |
| assignee_id | integer |  | Y |  | Y |  |
| title | string |  |  |  |  |  |
| description | text |  |  |  | Y |  |
| status | string |  |  |  | Y | pending |
| priority | string |  |  |  | Y | medium |
| due_date | datetime |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | now() |
| completed_at | datetime |  |  |  | Y |  |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_comms_incident_action_items_is_deleted` (is_deleted)
- `ix_comms_incident_action_items_id` (id)

**Foreign Keys:**

- `war_room_id` → `comms.incident_war_rooms.id`
- `assignee_id` → `accounts.users.id`

---

### `comms.comms.incident_threads`

*Table: `comms.comms.incident_threads`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| war_room_id | integer |  | Y |  |  |  |
| participant_id | integer |  | Y |  |  |  |
| message | text |  |  |  |  |  |
| created_at | datetime |  |  |  | Y | now() |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_comms_incident_threads_is_deleted` (is_deleted)
- `ix_comms_incident_threads_id` (id)

**Foreign Keys:**

- `war_room_id` → `comms.incident_war_rooms.id`
- `participant_id` → `accounts.users.id`

---

### `comms.comms.incident_war_rooms`

*Table: `comms.comms.incident_war_rooms`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| incident_id | string |  |  | Y |  |  |
| title | string |  |  |  |  |  |
| severity | string |  |  |  | Y | medium |
| status | string |  |  |  | Y | active |
| created_by_id | integer |  | Y |  |  |  |
| started_at | datetime |  |  |  | Y | now() |
| resolved_at | datetime |  |  |  | Y |  |
| closed_at | datetime |  |  |  | Y |  |
| context_data | json |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| updated_at | datetime |  |  |  |  | now() |

**Indexes:**

- `ix_comms_incident_war_rooms_id` (id)
- UNIQUE `ix_comms_incident_war_rooms_incident_id` (incident_id)
- `ix_comms_incident_war_rooms_is_deleted` (is_deleted)

**Foreign Keys:**

- `created_by_id` → `accounts.users.id`

---

### `comms.comms.internal_channel_members`

*Table: `comms.comms.internal_channel_members`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0E91BD0> |
| version | integer |  |  |  |  | 1 |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| channel_id | integer |  | Y |  |  |  |
| user_id | integer |  |  |  |  |  |
| role | string |  |  |  | Y | member |
| joined_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0E92050> |

**Indexes:**

- `ix_comms_internal_channel_members_id` (id)
- `ix_comms_internal_channel_members_created_by` (created_by)
- `ix_comms_internal_channel_members_channel_id` (channel_id)
- `ix_comms_internal_channel_members_updated_by` (updated_by)
- `ix_comms_internal_channel_members_is_deleted` (is_deleted)

**Foreign Keys:**

- `channel_id` → `comms.internal_channels.id`

---

### `comms.comms.internal_channels`

*Table: `comms.comms.internal_channels`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0E91AB0> |
| version | integer |  |  |  |  | 1 |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| entity_type | string |  |  |  |  |  |
| entity_id | integer |  |  |  |  |  |
| name | string |  |  |  |  |  |
| channel_id | string |  |  | Y | Y |  |
| description | text |  |  |  | Y |  |
| is_public | boolean |  |  |  | Y | True |
| created_by | integer |  |  |  | Y |  |
| country_code | string |  |  |  | Y |  |
| allowed_roles | json |  |  |  | Y |  |

**Indexes:**

- UNIQUE `ix_comms_internal_channels_channel_id` (channel_id)
- `ix_comms_internal_channels_updated_by` (updated_by)
- `ix_internal_channel_entity` (entity_type, entity_id)
- `ix_comms_internal_channels_id` (id)
- `ix_internal_channels_allowed_roles` (allowed_roles)
- `ix_comms_internal_channels_is_deleted` (is_deleted)
- `ix_internal_channels_country_created` (country_code, created_at)

---

### `comms.comms.internal_emails`

*Table: `comms.comms.internal_emails`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0E935B0> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| sender_id | integer |  |  |  |  |  |
| subject | string |  |  |  |  |  |
| body_html | text |  |  |  | Y |  |
| body_text | text |  |  |  | Y |  |
| recipients | text |  |  |  | Y |  |
| thread_id | string |  |  |  | Y |  |
| is_external | boolean |  |  |  | Y | False |
| external_message_id | string |  |  |  | Y |  |
| in_reply_to_id | integer |  | Y |  | Y |  |
| folder_id | integer |  | Y |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0E93640> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0E936D0> |
| country_code | string |  |  |  |  |  |

**Indexes:**

- `ix_internal_emails_country_created` (country_code, created_at)
- `ix_comms_internal_emails_is_deleted` (is_deleted)
- `ix_comms_internal_emails_folder_id` (folder_id)
- `ix_internal_emails_folder_id` (folder_id)
- `ix_comms_internal_emails_updated_by` (updated_by)
- `ix_comms_internal_emails_id` (id)
- `ix_internal_emails_sender_id` (sender_id)
- `ix_comms_internal_emails_in_reply_to_id` (in_reply_to_id)
- `ix_internal_emails_thread_id` (thread_id)
- `ix_comms_internal_emails_created_by` (created_by)
- `ix_comms_internal_emails_country_code` (country_code)

**Foreign Keys:**

- `in_reply_to_id` → `comms.internal_emails.id`
- `folder_id` → `comms.email_folders.id`

---

### `comms.comms.internal_messages`

*Table: `comms.comms.internal_messages`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0E92560> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| channel_id | integer |  | Y |  |  |  |
| user_id | integer |  |  |  |  |  |
| message | text |  |  |  |  |  |
| message_type | string |  |  |  | Y | text |
| is_masked | boolean |  |  |  | Y | True |
| read_at | datetime |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0E92680> |

**Indexes:**

- `ix_internal_msg_user` (user_id)
- `ix_internal_msg_channel` (channel_id)
- `ix_comms_internal_messages_channel_id` (channel_id)
- `ix_comms_internal_messages_created_by` (created_by)
- `ix_comms_internal_messages_updated_by` (updated_by)
- `ix_comms_internal_messages_is_deleted` (is_deleted)
- `ix_comms_internal_messages_id` (id)

**Foreign Keys:**

- `channel_id` → `comms.internal_channels.id`

---

### `comms.comms.internal_notices`

*Table: `comms.comms.internal_notices`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| title | string |  |  |  |  |  |
| content | text |  |  |  |  |  |
| priority | string |  |  |  | Y | normal |
| is_active | boolean |  |  |  | Y | True |
| valid_from | datetime |  |  |  | Y |  |
| valid_to | datetime |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B1039D80> |

**Indexes:**

- `ix_comms_internal_notices_id` (id)

---

### `comms.comms.masked_messages`

*Table: `comms.comms.masked_messages`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0F70280> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| sender_id | integer |  |  |  |  |  |
| recipient_ref | string |  |  |  |  |  |
| message_hash | integer |  |  |  |  |  |
| content | text |  |  |  |  |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0F703A0> |
| country_code | string |  |  |  |  |  |

**Indexes:**

- `ix_masked_messages_country_created` (country_code, created_at)
- `ix_masked_messages_hash` (message_hash)
- `ix_comms_masked_messages_is_deleted` (is_deleted)
- `ix_comms_masked_messages_created_by` (created_by)
- `ix_masked_messages_recipient` (recipient_ref)
- `ix_masked_messages_sender` (sender_id)
- `ix_comms_masked_messages_country_code` (country_code)
- `ix_comms_masked_messages_updated_by` (updated_by)
- `ix_comms_masked_messages_id` (id)

---

### `comms.comms.meeting_recordings`

*Table: `comms.comms.meeting_recordings`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| is_deleted | boolean |  |  |  |  | False |
| room_id | string |  |  |  |  |  |
| started_by_id | integer |  | Y |  |  |  |
| recording_url | string |  |  |  | Y |  |
| duration_seconds | integer |  |  |  | Y | 0 |
| status_code | string |  |  |  | Y | recording |
| started_at | datetime |  |  |  | Y | now() |
| ended_at | datetime |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | now() |
| updated_at | datetime |  |  |  |  | now() |

**Indexes:**

- `ix_comms_meeting_recordings_is_deleted` (is_deleted)
- `ix_comms_meeting_recordings_id` (id)

**Foreign Keys:**

- `started_by_id` → `accounts.users.id`

---

### `comms.comms.messages`

*Table: `comms.comms.messages`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B103A710> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| country_code | string |  | Y |  | Y |  |
| from_user_id | integer |  |  |  |  |  |
| to_user_id | integer |  |  |  |  |  |
| subject | string |  |  |  |  |  |
| body | text |  |  |  | Y |  |
| entity_type | string |  |  |  | Y |  |
| entity_id | integer |  |  |  | Y |  |
| priority | string |  |  |  | Y | normal |
| category | string |  |  |  | Y |  |
| status | string |  |  |  | Y | sent |
| read_at | datetime |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B103ACB0> |

**Indexes:**

- `ix_messages_country_created` (country_code, created_at)
- `ix_comms_messages_updated_by` (updated_by)
- `ix_comms_messages_id` (id)
- `ix_comms_messages_created_by` (created_by)
- `ix_comms_messages_is_deleted` (is_deleted)
- `ix_message_recipient` (to_user_id, created_at)
- `ix_message_sender` (from_user_id, created_at)
- `ix_comms_messages_country_code` (country_code)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `comms.comms.news_articles`

*Table: `comms.comms.news_articles`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| is_deleted | boolean |  |  |  |  | False |
| source_id | integer |  | Y |  | Y |  |
| external_id | string |  |  |  | Y |  |
| content_hash | string |  |  |  | Y |  |
| title | string |  |  |  |  |  |
| summary | text |  |  |  | Y |  |
| content | text |  |  |  | Y |  |
| url | string |  |  |  | Y |  |
| image_url | string |  |  |  | Y |  |
| published_at | datetime |  |  |  | Y |  |
| country_code | string |  |  |  | Y |  |
| ai_sentiment | string |  |  |  | Y | neutral |
| ai_tags | json |  |  |  | Y |  |
| is_published | boolean |  |  |  | Y | True |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B1038280> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B10381F0> |

**Indexes:**

- `ix_comms_news_articles_id` (id)
- `ix_news_articles_published` (published_at)
- `ix_comms_news_articles_is_deleted` (is_deleted)
- `ix_comms_news_articles_content_hash` (content_hash)

**Foreign Keys:**

- `source_id` → `comms.news_sources.id`

---

### `comms.comms.news_sources`

*Table: `comms.comms.news_sources`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| name | string |  |  |  |  |  |
| url | string |  |  |  |  |  |
| source_type | string |  |  |  | Y | rss |
| api_key_required | boolean |  |  |  | Y | False |
| category | string |  |  |  | Y | general |
| is_active | boolean |  |  |  | Y | True |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B10397E0> |

**Indexes:**

- `ix_comms_news_sources_id` (id)

---

### `comms.comms.newsletter_subscribers`

*Table: `comms.comms.newsletter_subscribers`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0F71BD0> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| email | string |  |  | Y |  |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0F71CF0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0F71C60> |

**Indexes:**

- UNIQUE `ix_comms_newsletter_subscribers_email` (email)
- `ix_comms_newsletter_subscribers_created_by` (created_by)
- `ix_comms_newsletter_subscribers_updated_by` (updated_by)
- `ix_comms_newsletter_subscribers_is_deleted` (is_deleted)
- `ix_comms_newsletter_subscribers_id` (id)

---

### `comms.comms.notifications`

*Table: `comms.comms.notifications`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0DBD5A0> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| user_id | integer |  |  |  |  |  |
| type | string |  |  |  | Y |  |
| title | string |  |  |  |  |  |
| message | text |  |  |  |  |  |
| channel | string |  |  |  | Y | in_app |
| priority | string |  |  |  | Y | medium |
| is_read | boolean |  |  |  | Y | False |
| read_at | datetime |  |  |  | Y |  |
| link | string |  |  |  | Y |  |
| template | string |  |  |  | Y |  |
| variables | json |  |  |  | Y |  |
| scheduled_at | datetime |  |  |  | Y |  |
| status_code | string |  |  |  | Y | delivered |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0DBD630> |
| country_code | string |  |  |  |  |  |

**Indexes:**

- `ix_notifications_country_created` (country_code, created_at)
- `ix_comms_notifications_updated_by` (updated_by)
- `ix_notifications_variables` (variables)
- `ix_comms_notifications_country_code` (country_code)
- `ix_notifications_user_read` (user_id, is_read)
- `ix_notifications_user_id` (user_id)
- `ix_comms_notifications_id` (id)
- `ix_notifications_is_read` (is_read)
- `ix_comms_notifications_is_deleted` (is_deleted)
- `ix_comms_notifications_created_by` (created_by)

---

### `comms.comms.proxy_call_logs`

*Table: `comms.comms.proxy_call_logs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0E904C0> |
| version | integer |  |  |  |  | 1 |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| channel_id | integer |  | Y |  |  |  |
| caller_id | integer |  |  |  |  |  |
| callee_id | integer |  |  |  |  |  |
| direction | string |  |  |  |  |  |
| duration_seconds | integer |  |  |  | Y | 0 |
| call_recording_url | string |  |  |  | Y |  |
| is_recorded | boolean |  |  |  | Y | False |
| started_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0E905E0> |
| ended_at | datetime |  |  |  | Y |  |

**Indexes:**

- `ix_comms_proxy_call_logs_id` (id)
- `ix_comms_proxy_call_logs_created_by` (created_by)
- `ix_comms_proxy_call_logs_channel_id` (channel_id)
- `ix_comms_proxy_call_logs_updated_by` (updated_by)
- `ix_comms_proxy_call_logs_is_deleted` (is_deleted)

**Foreign Keys:**

- `channel_id` → `comms.proxy_channels.id`

---

### `comms.comms.proxy_channels`

*Table: `comms.comms.proxy_channels`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0DBF2E0> |
| version | integer |  |  |  |  | 1 |
| created_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| entity_type | string |  |  |  |  |  |
| entity_id | integer |  |  |  |  |  |
| proxy_phone | string |  |  | Y |  |  |
| proxy_email | string |  |  | Y |  |  |
| participants | json |  |  |  | Y |  |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0DBF400> |

**Indexes:**

- UNIQUE `ix_comms_proxy_channels_proxy_phone` (proxy_phone)
- `ix_comms_proxy_channels_is_deleted` (is_deleted)
- `ix_proxy_channels_participants` (participants)
- `ix_comms_proxy_channels_updated_by` (updated_by)
- `idx_proxy_entity` (entity_type, entity_id)
- `ix_comms_proxy_channels_id` (id)
- UNIQUE `ix_comms_proxy_channels_proxy_email` (proxy_email)
- `ix_comms_proxy_channels_created_by` (created_by)

---

### `comms.comms.proxy_messages`

*Table: `comms.comms.proxy_messages`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0DBFEB0> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| session_id | integer |  | Y |  |  |  |
| sender_id | integer |  |  |  |  |  |
| recipient_id | integer |  |  |  |  |  |
| message_type | string |  |  |  | Y | text |
| content | text |  |  |  |  |  |
| is_masked | boolean |  |  |  | Y | True |
| read_at | datetime |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0DBFF40> |

**Indexes:**

- `ix_comms_proxy_messages_session_id` (session_id)
- `ix_comms_proxy_messages_updated_by` (updated_by)
- `ix_comms_proxy_messages_is_deleted` (is_deleted)
- `ix_comms_proxy_messages_id` (id)
- `ix_comms_proxy_messages_created_by` (created_by)

**Foreign Keys:**

- `session_id` → `comms.proxy_sessions.id`

---

### `comms.comms.proxy_sessions`

*Table: `comms.comms.proxy_sessions`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0DBF910> |
| version | integer |  |  |  |  | 1 |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| channel_id | integer |  | Y |  |  |  |
| participant_one_id | integer |  |  |  |  |  |
| participant_two_id | integer |  |  |  |  |  |
| started_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0DBF9A0> |
| ended_at | datetime |  |  |  | Y |  |
| is_encrypted | boolean |  |  |  | Y | True |
| session_metadata | json |  |  |  | Y |  |

**Indexes:**

- `ix_comms_proxy_sessions_is_deleted` (is_deleted)
- `ix_comms_proxy_sessions_created_by` (created_by)
- `ix_comms_proxy_sessions_channel_id` (channel_id)
- `ix_comms_proxy_sessions_updated_by` (updated_by)
- `ix_proxy_sessions_session_metadata` (session_metadata)
- `ix_comms_proxy_sessions_id` (id)

**Foreign Keys:**

- `channel_id` → `comms.proxy_channels.id`

---

### `comms.comms.support_ticket_replies`

*Table: `comms.comms.support_ticket_replies`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| ticket_id | integer |  | Y |  |  |  |
| sender_id | integer |  | Y |  |  |  |
| message | text |  |  |  |  |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B1038DC0> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_comms_support_ticket_replies_id` (id)
- `ix_comms_support_ticket_replies_country_code` (country_code)

**Foreign Keys:**

- `ticket_id` → `comms.support_tickets.id`
- `sender_id` → `accounts.users.id`

---

### `comms.comms.support_tickets`

*Table: `comms.comms.support_tickets`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| is_deleted | boolean |  |  |  |  | False |
| user_id | integer |  | Y |  |  |  |
| subject | string |  |  |  |  |  |
| priority | string |  |  |  | Y | medium |
| status | string |  |  |  | Y | open |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B10380D0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B1038820> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_comms_support_tickets_id` (id)
- `ix_comms_support_tickets_country_code` (country_code)
- `ix_comms_support_tickets_is_deleted` (is_deleted)

**Foreign Keys:**

- `user_id` → `accounts.users.id`

---

### `comms.comms.ticket_attachments`

*Table: `comms.comms.ticket_attachments`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| ticket_reply_id | integer |  | Y |  | Y |  |
| ticket_id | integer |  | Y |  | Y |  |
| file_url | string |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B10392D0> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_comms_ticket_attachments_id` (id)
- `ix_comms_ticket_attachments_country_code` (country_code)

**Foreign Keys:**

- `ticket_reply_id` → `comms.support_ticket_replies.id`
- `ticket_id` → `comms.support_tickets.id`

---

### `comms.comms.ticket_messages`

*Table: `comms.comms.ticket_messages`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0DBD750> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| ticket_id | integer |  | Y |  |  |  |
| sender_id | integer |  |  |  |  |  |
| message | text |  |  |  |  |  |
| is_admin | boolean |  |  |  | Y | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0DBDC60> |
| country_code | string |  |  |  |  |  |

**Indexes:**

- `ix_comms_ticket_messages_country_code` (country_code)
- `ix_comms_ticket_messages_ticket_id` (ticket_id)
- `ix_comms_ticket_messages_updated_by` (updated_by)
- `ix_comms_ticket_messages_created_by` (created_by)
- `ix_ticket_messages_country_created` (country_code, created_at)
- `ix_comms_ticket_messages_id` (id)
- `ix_comms_ticket_messages_is_deleted` (is_deleted)

**Foreign Keys:**

- `ticket_id` → `comms.support_tickets.id`

---

### `comms.comms.video_room_participants`

*Table: `comms.comms.video_room_participants`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| room_id | integer |  | Y |  |  |  |
| user_id | integer |  | Y |  |  |  |
| role | string |  |  |  | Y | participant |
| joined_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0D023B0> |
| left_at | datetime |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_comms_video_room_participants_id` (id)
- `ix_comms_video_room_participants_is_deleted` (is_deleted)

**Foreign Keys:**

- `room_id` → `comms.video_rooms.id`
- `user_id` → `accounts.users.id`

---

### `comms.comms.video_room_recordings`

*Table: `comms.comms.video_room_recordings`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| room_id | integer |  | Y |  |  |  |
| started_by_id | integer |  | Y |  |  |  |
| recording_url | string |  |  |  | Y |  |
| duration_seconds | integer |  |  |  | Y | 0 |
| status | string |  |  |  | Y | recording |
| started_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0D03E20> |
| ended_at | datetime |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_comms_video_room_recordings_id` (id)
- `ix_comms_video_room_recordings_is_deleted` (is_deleted)

**Foreign Keys:**

- `room_id` → `comms.video_rooms.id`
- `started_by_id` → `accounts.users.id`

---

### `comms.comms.video_rooms`

*Table: `comms.comms.video_rooms`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| room_id | string |  |  | Y |  |  |
| room_uuid | string |  |  | Y | Y |  |
| name | string |  |  |  |  |  |
| country_code | string |  | Y |  | Y |  |
| created_by_id | integer |  | Y |  | Y |  |
| is_boardroom | boolean |  |  |  | Y | False |
| status | string |  |  |  | Y | waiting |
| max_participants | integer |  |  |  | Y | 100 |
| recording_enabled | boolean |  |  |  | Y | False |
| watermark_enabled | boolean |  |  |  | Y | True |
| transcription_enabled | boolean |  |  |  | Y | True |
| started_at | datetime |  |  |  | Y |  |
| ended_at | datetime |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0D01D80> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0D01E10> |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_video_room_created` (created_at)
- `ix_comms_video_rooms_id` (id)
- `ix_video_room_status` (status)
- UNIQUE `ix_comms_video_rooms_room_id` (room_id)
- `ix_comms_video_rooms_is_deleted` (is_deleted)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`
- `created_by_id` → `accounts.users.id`

---

### `comms.comms.war_room_templates`

*Table: `comms.comms.war_room_templates`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| name | string |  |  |  |  |  |
| severity | string |  |  |  |  |  |
| auto_assign | boolean |  |  |  | Y | False |
| template_data | json |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_comms_war_room_templates_is_deleted` (is_deleted)
- `ix_comms_war_room_templates_id` (id)

---

## COUNTRY

*Schema: `country` · 33 tables*

### `country.country.country_basics`

*Table: `country.country.country_basics`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0022290> |
| version | integer |  |  |  |  | 1 |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| code | string |  |  | Y |  |  |
| name | string |  |  |  |  |  |
| currency | string |  |  |  | Y | USD |
| currency_symbol | string |  |  |  | Y |  |
| phone_code | string |  |  |  | Y |  |
| language | string |  |  |  | Y | en |
| timezone | string |  |  |  | Y |  |
| date_format | string |  |  |  | Y | DD/MM/YYYY |
| status | string |  |  |  | Y | active |
| is_active | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  | Y | False |
| is_default | boolean |  |  |  | Y | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B00223B0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0022320> |
| country_code | string |  | Y |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| official_name | string |  |  |  | Y |  |
| alpha3 | string |  |  |  | Y |  |
| flag_url | string |  |  |  | Y |  |
| currency_name | string |  |  |  | Y |  |
| exchange_rate_to_usd | numeric |  |  |  | Y |  |
| capital | string |  |  |  | Y |  |
| region | string |  |  |  | Y |  |
| subregion | string |  |  |  | Y |  |
| population | integer |  |  |  | Y |  |
| internet_penetration_pct | numeric |  |  |  | Y |  |
| gdp_per_capita_usd | numeric |  |  |  | Y |  |
| urbanization_pct | numeric |  |  |  | Y |  |
| mobile_subs_per_100 | numeric |  |  |  | Y |  |
| public_holidays_json | text |  |  |  | Y |  |
| macro_indicators_json | text |  |  |  | Y |  |

**Indexes:**

- UNIQUE `ix_country_country_basics_code` (code)
- UNIQUE `ix_country_basics_code` (code)
- `ix_country_country_basics_country_code` (country_code)
- `ix_country_country_basics_id` (id)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `country.country.country_category_tax_rates`

*Table: `country.country.country_category_tax_rates`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B02340D0> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| country_code | string |  | Y |  |  |  |
| category_id | integer |  |  |  |  |  |
| tax_rate | numeric |  |  |  | Y |  |
| tax_name | string |  |  |  | Y |  |
| category_slug | string |  |  |  | Y |  |
| rate | numeric |  |  |  | Y |  |
| is_exempt | boolean |  |  |  | Y | False |
| is_reduced | boolean |  |  |  | Y | False |
| notes | text |  |  |  | Y |  |
| source | string |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B02341F0> |

**Indexes:**

- `ix_country_country_category_tax_rates_id` (id)
- `ix_country_category_tax_rates_country_created` (country_code, created_at)
- `ix_country_country_category_tax_rates_created_by` (created_by)
- `ix_country_country_category_tax_rates_updated_by` (updated_by)
- `ix_country_country_category_tax_rates_is_deleted` (is_deleted)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `country.country.country_cities`

*Table: `country.country.country_cities`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0234670> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| country_code | string |  | Y |  |  |  |
| name | string |  |  |  |  |  |
| name_local | string |  |  |  | Y |  |
| population | integer |  |  |  | Y | 0 |
| is_capital | boolean |  |  |  | Y | False |
| latitude | numeric |  |  |  | Y |  |
| longitude | numeric |  |  |  | Y |  |
| postal_code_prefix | string |  |  |  | Y |  |
| status | string |  |  |  | Y | active |
| is_active | boolean |  |  |  | Y | True |
| region | string |  |  |  | Y |  |
| sort_order | integer |  |  |  | Y | 0 |
| source | string |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0234700> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0234790> |

**Indexes:**

- `ix_country_country_cities_id` (id)
- `ix_country_country_cities_created_by` (created_by)
- `ix_country_country_cities_country_code` (country_code)
- `ix_country_country_cities_is_deleted` (is_deleted)
- `ix_country_country_cities_updated_by` (updated_by)
- `ix_country_cities_country_created` (country_code, created_at)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `country.country.country_commission_rate_histories`

*Table: `country.country.country_commission_rate_histories`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0235F30> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| country_code | string |  |  |  |  |  |
| category_id | integer |  |  |  | Y |  |
| supplier_tier | string |  |  |  |  |  |
| rate_percent | numeric |  |  |  |  |  |
| effective_from | datetime |  |  |  |  |  |
| effective_to | datetime |  |  |  | Y |  |
| changed_by | integer |  |  |  | Y |  |
| change_reason | text |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0236050> |

**Indexes:**

- `ix_country_country_commission_rate_histories_updated_by` (updated_by)
- `ix_country_country_commission_rate_histories_is_deleted` (is_deleted)
- `ix_country_country_commission_rate_histories_id` (id)
- `ix_country_country_commission_rate_histories_created_by` (created_by)
- `ix_country_commission_rate_history_country_created` (country_code, created_at)
- `ix_comm_rate_effective` (effective_from)

---

### `country.country.country_commission_rates`

*Table: `country.country.country_commission_rates`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0172710> |
| version | integer |  |  |  |  | 1 |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| country_code | string |  | Y |  |  |  |
| supplier_tier | string |  |  |  |  |  |
| name | string |  |  |  |  |  |
| rate_percent | numeric |  |  |  |  | 0 |
| fixed_fee | numeric |  |  |  | Y | 0 |
| effective_from | datetime |  |  |  | Y | <function utcnow at 0x000001C7B01727A0> |
| effective_to | datetime |  |  |  | Y |  |

**Indexes:**

- `ix_country_country_commission_rates_is_deleted` (is_deleted)
- `ix_country_country_commission_rates_updated_by` (updated_by)
- `ix_country_commission_rates_country_created` (country_code, created_at)
- `ix_country_country_commission_rates_id` (id)
- `ix_country_country_commission_rates_created_by` (created_by)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `country.country.country_communication_threads`

*Table: `country.country.country_communication_threads`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0235990> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| country_code | string |  |  |  |  |  |
| entity_type | string |  |  |  |  |  |
| entity_id | integer |  |  |  |  |  |
| participants | text |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| last_message_at | datetime |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0235A20> |

**Indexes:**

- `ix_country_country_communication_threads_updated_by` (updated_by)
- `ix_country_country_communication_threads_is_deleted` (is_deleted)
- `ix_country_country_communication_threads_id` (id)
- `ix_country_communication_threads_country_created` (country_code, created_at)
- `ix_comm_thread_entity` (entity_type, entity_id)
- `ix_country_country_communication_threads_created_by` (created_by)

---

### `country.country.country_communications`

*Table: `country.country.country_communications`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B02372E0> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| country_code | string |  | Y |  |  |  |
| from_user_id | integer |  |  |  | Y |  |
| to_user_id | integer |  |  |  | Y |  |
| subject | string |  |  |  |  |  |
| body | text |  |  |  |  |  |
| priority | string |  |  |  | Y | normal |
| category | string |  |  |  | Y |  |
| status | string |  |  |  | Y | sent |
| related_entity_type | string |  |  |  | Y |  |
| related_entity_id | integer |  |  |  | Y |  |
| read_at | datetime |  |  |  | Y |  |
| attachments_json | text |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0237010> |

**Indexes:**

- `ix_country_communications_recipient` (to_user_id, status)
- `ix_country_country_communications_updated_by` (updated_by)
- `ix_country_country_communications_is_deleted` (is_deleted)
- `ix_country_country_communications_created_by` (created_by)
- `ix_country_country_communications_id` (id)
- `ix_country_country_communications_country_code` (country_code)
- `ix_country_communications_country_created` (country_code, created_at)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `country.country.country_config_versions`

*Table: `country.country.country_config_versions`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B01712D0> |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| country_code | string |  | Y |  |  |  |
| config_type | string |  |  |  |  |  |
| version | integer |  |  |  |  |  |
| payload_json | text |  |  |  |  |  |
| status | string |  |  |  | Y | draft |
| draft_by | integer |  |  |  | Y |  |
| approved_by | integer |  |  |  | Y |  |
| published_at | datetime |  |  |  | Y |  |
| effective_from | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0171360> |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B01713F0> |

**Indexes:**

- `ix_country_country_config_versions_created_by` (created_by)
- `ix_country_country_config_versions_updated_by` (updated_by)
- `ix_country_config_versions_country_created` (country_code, created_at)
- `ix_country_config_version_status` (status)
- `ix_country_country_config_versions_is_deleted` (is_deleted)
- `ix_country_country_config_versions_id` (id)
- `ix_country_config_version_type` (config_type)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `country.country.country_configs`

*Table: `country.country.country_configs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0021EA0> |
| version | integer |  |  |  |  | 1 |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| basics_id | integer |  | Y |  | Y |  |
| code | string |  |  | Y |  |  |
| name | string |  |  |  |  |  |
| currency | string |  |  |  | Y | USD |
| currency_symbol | string |  |  |  | Y |  |
| phone_code | string |  |  |  | Y |  |
| language | string |  |  |  | Y | en |
| timezone | string |  |  |  | Y |  |
| date_format | string |  |  |  | Y | DD/MM/YYYY |
| status | string |  |  |  | Y | active |
| is_active | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  | Y | False |
| is_default | boolean |  |  |  | Y | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0021F30> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0021FC0> |
| official_name | string |  |  |  | Y |  |
| alpha3 | string |  |  |  | Y |  |
| flag_url | string |  |  |  | Y |  |
| currency_name | string |  |  |  | Y |  |
| exchange_rate_to_usd | numeric |  |  |  | Y |  |
| capital | string |  |  |  | Y |  |
| region | string |  |  |  | Y |  |
| subregion | string |  |  |  | Y |  |
| population | integer |  |  |  | Y |  |
| internet_penetration_pct | numeric |  |  |  | Y |  |
| gdp_per_capita_usd | numeric |  |  |  | Y |  |
| urbanization_pct | numeric |  |  |  | Y |  |
| mobile_subs_per_100 | numeric |  |  |  | Y |  |
| public_holidays_json | text |  |  |  | Y |  |
| macro_indicators_json | text |  |  |  | Y |  |
| tax_type | string |  |  |  | Y | VAT |
| tax_rate | numeric |  |  |  | Y | 0.0000 |
| tax_name | string |  |  |  | Y | VAT |
| tax_inclusive | boolean |  |  |  | Y | False |
| tax_exempt_categories_json | text |  |  |  | Y | [] |
| tax_reduced_rates_json | text |  |  |  | Y | {} |
| logistics_model | string |  |  |  | Y | fixed |
| default_vehicle_type | string |  |  |  | Y |  |
| base_rate | numeric |  |  |  | Y |  |
| per_km_rate | numeric |  |  |  | Y |  |
| minimum_charge | numeric |  |  |  | Y |  |
| weight_surcharge_rate | numeric |  |  |  | Y |  |
| weight_surcharge_threshold_kg | numeric |  |  |  | Y |  |
| payment_methods_json | text |  |  |  | Y | [] |
| payment_gateways_json | text |  |  |  | Y |  |
| logistics_providers_json | text |  |  |  | Y |  |
| legal_rules_json | text |  |  |  | Y |  |
| product_restrictions_json | text |  |  |  | Y | [] |
| address_format_json | text |  |  |  | Y | {"fields":["street","city","postal_code"],"required":["street","city"]} |
| regions_json | text |  |  |  | Y | [] |
| supplier_requirements_json | text |  |  |  | Y |  |
| payout_settings_json | text |  |  |  | Y |  |
| commission_tiers_json | text |  |  |  | Y |  |
| suggested_gateway_rankings_json | text |  |  |  | Y |  |
| suggested_commission_ranges_json | text |  |  |  | Y |  |
| consumer_behavior_profile_json | text |  |  |  | Y |  |
| economic_tier | string |  |  |  | Y |  |
| fraud_risk_tier | string |  |  |  | Y |  |
| suggested_logistics_model | string |  |  |  | Y |  |
| data_residency_tier | string |  |  |  | Y | standard |
| data_residency_encrypted | text |  |  |  | Y |  |
| confidence_score | numeric |  |  |  | Y | 0.0000 |
| audit_trail_json | text |  |  |  | Y |  |
| cod_enabled | boolean |  |  |  | Y |  |
| cod_max_amount | numeric |  |  |  | Y |  |
| cod_verification_required | boolean |  |  |  | Y |  |
| cod_remittance_days | integer |  |  |  | Y |  |
| settlement_hold_days | integer |  |  |  | Y | 3 |
| minimum_payout_amount | numeric |  |  |  | Y |  |
| payout_currency | string |  |  |  | Y |  |
| supplier_kyc_tier | string |  |  |  | Y |  |
| supplier_onboarding_fee | numeric |  |  |  | Y |  |
| supplier_monthly_fee | numeric |  |  |  | Y |  |
| supplier_rating_threshold | numeric |  |  |  | Y |  |
| legal_entity_required | boolean |  |  |  | Y | False |
| consumer_protection_days | integer |  |  |  | Y | 14 |
| data_privacy_framework | string |  |  |  | Y |  |
| max_package_weight_kg | numeric |  |  |  | Y |  |
| max_package_dimensions_cm | string |  |  |  | Y |  |
| signature_required_threshold | numeric |  |  |  | Y |  |
| measurement_system | string |  |  |  | Y | metric |
| working_days_json | text |  |  |  | Y | [] |
| supported_languages_json | text |  |  |  | Y | [] |
| payout_methods_json | text |  |  |  | Y | [] |
| logistics_zones_json | text |  |  |  | Y | [] |
| country_code | string |  |  | Y | Y |  |

**Indexes:**

- `ix_country_country_configs_created_by` (created_by)
- `ix_country_country_configs_basics_id` (basics_id)
- `ix_country_country_configs_updated_by` (updated_by)
- `ix_country_configs_country_created` (country_code, created_at)
- `ix_country_country_configs_id` (id)
- UNIQUE `ix_country_country_configs_code` (code)
- UNIQUE `ix_country_country_configs_country_code` (country_code)

**Foreign Keys:**

- `basics_id` → `country.country_basics.id`

---

### `country.country.country_economics`

*Table: `country.country.country_economics`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| uuid | string |  |  | Y | Y |  |
| version | integer |  |  |  |  | 1 |
| country_code | string |  | Y | Y |  |  |
| is_active | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  | Y | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0022A70> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B00229E0> |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| economic_tier | string |  |  |  | Y |  |
| fraud_risk_tier | string |  |  |  | Y |  |
| suggested_logistics_model | string |  |  |  | Y |  |
| data_residency_tier | string |  |  |  | Y | standard |
| data_residency_encrypted | text |  |  |  | Y |  |
| confidence_score | numeric |  |  |  | Y | 0.0000 |
| audit_trail_json | text |  |  |  | Y |  |
| cod_enabled | string |  |  |  | Y |  |
| cod_max_amount | numeric |  |  |  | Y |  |
| cod_verification_required | string |  |  |  | Y |  |
| cod_remittance_days | integer |  |  |  | Y |  |
| settlement_hold_days | integer |  |  |  | Y | 3 |
| minimum_payout_amount | numeric |  |  |  | Y |  |
| payout_currency | string |  |  |  | Y |  |
| supplier_kyc_tier | string |  |  |  | Y |  |
| supplier_onboarding_fee | numeric |  |  |  | Y |  |
| supplier_monthly_fee | numeric |  |  |  | Y |  |
| supplier_rating_threshold | numeric |  |  |  | Y |  |
| legal_entity_required | string |  |  |  | Y | false |
| consumer_protection_days | integer |  |  |  | Y | 14 |
| data_privacy_framework | string |  |  |  | Y |  |
| max_package_weight_kg | numeric |  |  |  | Y |  |
| max_package_dimensions_cm | string |  |  |  | Y |  |
| signature_required_threshold | numeric |  |  |  | Y |  |
| measurement_system | string |  |  |  | Y | metric |
| working_days_json | text |  |  |  | Y | [] |
| supported_languages_json | text |  |  |  | Y | [] |
| payout_methods_json | text |  |  |  | Y | [] |
| logistics_zones_json | text |  |  |  | Y | [] |

**Indexes:**

- UNIQUE `ix_country_country_economics_uuid` (uuid)
- `ix_country_country_economics_id` (id)
- UNIQUE `ix_country_economics_code` (country_code)
- `ix_country_economics_country_created` (country_code, created_at)
- UNIQUE `ix_country_country_economics_country_code` (country_code)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `country.country.country_feature_flags`

*Table: `country.country.country_feature_flags`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0023F40> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| country_code | string |  | Y |  |  |  |
| feature_key | string |  |  |  |  |  |
| feature_name | string |  |  |  | Y |  |
| is_enabled | boolean |  |  |  | Y | True |
| config | text |  |  |  | Y |  |
| rollout_audience | string |  |  |  | Y |  |
| notes | text |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B01700D0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0170040> |

**Indexes:**

- `ix_country_country_feature_flags_created_by` (created_by)
- `ix_country_country_feature_flags_is_deleted` (is_deleted)
- `ix_country_country_feature_flags_updated_by` (updated_by)
- `ix_country_feature_flags_country_created` (country_code, created_at)
- `ix_country_country_feature_flags_id` (id)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `country.country.country_gateway_configs`

*Table: `country.country.country_gateway_configs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B02352D0> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| country_code | string |  |  |  |  |  |
| gateway_id | string |  |  |  |  |  |
| gateway_name | string |  |  |  |  |  |
| is_enabled | boolean |  |  |  | Y | True |
| priority | integer |  |  |  | Y | 0 |
| credentials | text |  |  |  | Y |  |
| environment | string |  |  |  | Y | test |
| settings | text |  |  |  | Y |  |
| last_tested_at | datetime |  |  |  | Y |  |
| last_test_result | string |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0235360> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B02353F0> |

**Indexes:**

- `ix_country_country_gateway_configs_created_by` (created_by)
- `ix_country_country_gateway_configs_is_deleted` (is_deleted)
- `ix_country_country_gateway_configs_updated_by` (updated_by)
- `ix_country_gateway_configs_country_created` (country_code, created_at)
- `ix_country_country_gateway_configs_id` (id)

---

### `country.country.country_gateway_credentials`

*Table: `country.country.country_gateway_credentials`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0311750> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| country_code | string |  | Y |  |  |  |
| gateway_name | string |  |  |  |  |  |
| environment | string |  |  |  | Y | test |
| credentials | json |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| created_at | datetime |  |  |  |  | now() |

**Indexes:**

- `ix_country_country_gateway_credentials_id` (id)
- `ix_country_country_gateway_credentials_country_code` (country_code)
- `ix_country_country_gateway_credentials_created_by` (created_by)
- `ix_country_gateway_credentials_country_created` (country_code, created_at)
- `ix_country_country_gateway_credentials_is_deleted` (is_deleted)
- `ix_country_country_gateway_credentials_updated_by` (updated_by)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `country.country.country_holiday_calendars`

*Table: `country.country.country_holiday_calendars`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0234D30> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| country_code | string |  |  |  |  |  |
| holiday_date | datetime |  |  |  |  |  |
| name | string |  |  |  |  |  |
| local_name | string |  |  |  | Y |  |
| is_observed | boolean |  |  |  | Y | True |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0234DC0> |

**Indexes:**

- `ix_country_country_holiday_calendars_is_deleted` (is_deleted)
- `ix_country_country_holiday_calendars_id` (id)
- `ix_country_holiday_calendars_country_created` (country_code, created_at)
- `ix_country_country_holiday_calendars_created_by` (created_by)
- `ix_country_country_holiday_calendars_updated_by` (updated_by)
- `ix_country_holiday_date` (holiday_date)

---

### `country.country.country_legal_contracts`

*Table: `country.country.country_legal_contracts`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B01739A0> |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| country_code | string |  |  |  |  |  |
| contract_type | string |  |  |  |  |  |
| version | string |  |  |  | Y | 1.0 |
| content_html | text |  |  |  |  |  |
| is_active | boolean |  |  |  | Y | True |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0173A30> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0173AC0> |

**Indexes:**

- `ix_country_country_legal_contracts_is_deleted` (is_deleted)
- `ix_country_country_legal_contracts_updated_by` (updated_by)
- `ix_country_country_legal_contracts_id` (id)
- `ix_country_legal_contracts_country_created` (country_code, created_at)
- `ix_country_country_legal_contracts_created_by` (created_by)

---

### `country.country.country_legals`

*Table: `country.country.country_legals`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| uuid | string |  |  | Y | Y |  |
| version | integer |  |  |  |  | 1 |
| country_code | string |  | Y | Y |  |  |
| is_active | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  | Y | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0023130> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B00230A0> |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| legal_entity_required | string |  |  |  | Y | true |
| consumer_protection_days | integer |  |  |  | Y | 14 |
| data_privacy_framework | string |  |  |  | Y |  |
| gdpr_compliant | boolean |  |  |  | Y | False |
| local_data_residency | boolean |  |  |  | Y | False |
| compliance_score | numeric |  |  |  | Y | 0.5000 |
| legal_risk_tier | string |  |  |  | Y | medium |
| contract_templates_json | text |  |  |  | Y | [] |
| regulatory_bodies_json | text |  |  |  | Y | [] |

**Indexes:**

- `ix_country_country_legals_id` (id)
- UNIQUE `ix_country_legal_code` (country_code)
- UNIQUE `ix_country_country_legals_uuid` (uuid)
- `ix_country_legal_country_created` (country_code, created_at)
- UNIQUE `ix_country_country_legals_country_code` (country_code)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `country.country.country_localizations`

*Table: `country.country.country_localizations`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0172CB0> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| country_code | string |  |  | Y |  |  |
| default_numeral_system | string |  |  |  | Y | western |
| hijri_calendar_enabled | boolean |  |  |  | Y | False |
| rtl_layout_enabled | boolean |  |  |  | Y | False |
| address_format | string |  |  |  | Y | {street}, {city}, {postal_code} |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0172DD0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0172D40> |

**Indexes:**

- `ix_country_country_localizations_created_by` (created_by)
- `ix_country_country_localizations_updated_by` (updated_by)
- `ix_country_country_localizations_is_deleted` (is_deleted)
- `ix_country_country_localizations_id` (id)
- `ix_country_localization_country_created` (country_code, created_at)

---

### `country.country.country_logistics_zones`

*Table: `country.country.country_logistics_zones`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B02364D0> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| country_code | string |  |  |  |  |  |
| zone_code | string |  |  |  |  |  |
| zone_name | string |  |  |  |  |  |
| zone_type | string |  |  |  | Y | local |
| cities | text |  |  |  | Y |  |
| pricing_config | text |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0236560> |

**Indexes:**

- `ix_country_logistics_zones_country_created` (country_code, created_at)
- `ix_country_country_logistics_zones_created_by` (created_by)
- `ix_country_country_logistics_zones_updated_by` (updated_by)
- `ix_country_country_logistics_zones_is_deleted` (is_deleted)
- `ix_country_country_logistics_zones_id` (id)

---

### `country.country.country_map_configs`

*Table: `country.country.country_map_configs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| country_code | string |  | Y | Y |  |  |
| map_provider | string |  |  |  | Y | google |
| api_key_ref | string |  |  |  | Y |  |
| default_zoom | integer |  |  |  | Y | 5 |
| show_regions | boolean |  |  |  | Y | True |
| show_cities | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0C2A9E0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0C2AB90> |

**Indexes:**

- UNIQUE `ix_country_country_map_configs_country_code` (country_code)
- `ix_country_country_map_configs_is_deleted` (is_deleted)
- `ix_country_country_map_configs_id` (id)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `country.country.country_payment_aliases`

*Table: `country.country.country_payment_aliases`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0173370> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| country_code | string |  |  |  |  |  |
| alias_type | string |  |  |  |  |  |
| alias_value | string |  |  |  |  |  |
| is_active | boolean |  |  |  | Y | True |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0173400> |

**Indexes:**

- `ix_country_payment_aliases_country_created` (country_code, created_at)
- `ix_country_country_payment_aliases_created_by` (created_by)
- `ix_country_country_payment_aliases_updated_by` (updated_by)
- `ix_country_country_payment_aliases_is_deleted` (is_deleted)
- `ix_country_country_payment_aliases_id` (id)

---

### `country.country.country_payout_rules`

*Table: `country.country.country_payout_rules`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0236A70> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| country_code | string |  |  |  |  |  |
| supplier_tier | string |  |  |  | Y |  |
| min_amount | numeric |  |  |  | Y |  |
| max_amount | numeric |  |  |  | Y |  |
| fixed_fee | numeric |  |  |  | Y | 0 |
| percent_fee | numeric |  |  |  | Y | 0 |
| settlement_days | integer |  |  |  | Y | 3 |
| is_active | boolean |  |  |  | Y | True |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0236B00> |

**Indexes:**

- `ix_country_country_payout_rules_id` (id)
- `ix_country_payout_rules_country_created` (country_code, created_at)
- `ix_payout_supplier` (supplier_tier)
- `ix_country_country_payout_rules_created_by` (created_by)
- `ix_country_country_payout_rules_updated_by` (updated_by)
- `ix_country_country_payout_rules_is_deleted` (is_deleted)

---

### `country.country.country_staff_assignments`

*Table: `country.country.country_staff_assignments`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0170670> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| user_id | integer |  |  |  |  |  |
| country_code | string |  | Y |  |  |  |
| role_in_country | string |  |  |  |  | country_manager |
| is_active | boolean |  |  |  | Y | True |
| assigned_by | integer |  |  |  | Y |  |
| notes | text |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0170790> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0170700> |

**Indexes:**

- `ix_country_country_staff_assignments_id` (id)
- `ix_country_staff_assignments_country_created` (country_code, created_at)
- `ix_staff_user` (user_id)
- `ix_country_country_staff_assignments_created_by` (created_by)
- `ix_country_country_staff_assignments_updated_by` (updated_by)
- `ix_country_country_staff_assignments_is_deleted` (is_deleted)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `country.country.country_taxes`

*Table: `country.country.country_taxes`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| uuid | string |  |  | Y |  |  |
| country_code | string |  | Y | Y |  |  |
| is_active | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  | Y | False |
| version | integer |  |  |  |  | 1 |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B00237F0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0023760> |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| tax_type | string |  |  |  | Y | VAT |
| tax_rate | numeric |  |  |  | Y | 0.0000 |
| tax_name | string |  |  |  | Y | VAT |
| tax_inclusive | boolean |  |  |  | Y | False |
| tax_exempt_categories_json | text |  |  |  | Y | [] |
| tax_reduced_rates_json | text |  |  |  | Y | {} |

**Indexes:**

- UNIQUE `ix_country_country_taxes_uuid` (uuid)
- `ix_country_tax_country_created` (country_code, created_at)
- UNIQUE `ix_country_tax_code` (country_code)
- UNIQUE `ix_country_country_taxes_country_code` (country_code)
- `ix_country_tax_active` (is_active, is_deleted)
- `ix_country_country_taxes_id` (id)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `country.country.data_residency_records`

*Table: `country.country.data_residency_records`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| country_code | string |  | Y |  |  |  |
| data_type | string |  |  |  |  |  |
| storage_location | string |  |  |  | Y |  |
| cross_border_allowed | boolean |  |  |  | Y | False |
| compliance_status | string |  |  |  | Y | pending |
| last_audit_at | datetime |  |  |  | Y |  |
| next_audit_at | datetime |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0C2A3B0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0C2A320> |

**Indexes:**

- `ix_country_data_residency_records_country_code` (country_code)
- `ix_drr_compliance` (compliance_status)
- `ix_country_data_residency_records_is_deleted` (is_deleted)
- `ix_country_data_residency_records_id` (id)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `country.country.logistics_partner_kyc_requirements`

*Table: `country.country.logistics_partner_kyc_requirements`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0172050> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| country_code | string |  | Y | Y |  |  |
| min_experience_months | integer |  |  |  | Y | 6 |
| required_documents | text |  |  |  | Y |  |
| insurance_required | boolean |  |  |  | Y | True |
| insurance_min_coverage | numeric |  |  |  | Y |  |
| vehicle_requirements | text |  |  |  | Y |  |
| background_check_required | boolean |  |  |  | Y | True |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B01720E0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0172170> |

**Indexes:**

- `ix_logistics_partner_kyc_requirements_country_created` (country_code, created_at)
- `ix_country_logistics_partner_kyc_requirements_created_by` (created_by)
- UNIQUE `ix_country_logistics_partner_kyc_requirements_country_code` (country_code)
- `ix_country_logistics_partner_kyc_requirements_is_deleted` (is_deleted)
- `ix_country_logistics_partner_kyc_requirements_updated_by` (updated_by)
- `ix_country_logistics_partner_kyc_requirements_id` (id)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `country.country.logistics_partner_locations`

*Table: `country.country.logistics_partner_locations`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| partner_id | integer |  | Y |  |  |  |
| country_code | string |  | Y |  |  |  |
| location_type | string |  |  |  | Y | warehouse |
| latitude | float |  |  |  | Y |  |
| longitude | float |  |  |  | Y |  |
| address | text |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0C2B7F0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0C2B880> |

**Indexes:**

- `ix_country_logistics_partner_locations_country_code` (country_code)
- `ix_country_logistics_partner_locations_id` (id)
- `ix_country_logistics_partner_locations_partner_id` (partner_id)
- `ix_lpl_partner` (partner_id)
- `ix_country_logistics_partner_locations_is_deleted` (is_deleted)

**Foreign Keys:**

- `partner_id` → `logistics.logistics_partners.id`
- `country_code` → `country.country_configs.code`

---

### `country.country.oman_delivery_zones`

*Table: `country.country.oman_delivery_zones`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0170D30> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| zone_code | string |  |  | Y |  |  |
| zone_name | string |  |  |  |  |  |
| description | text |  |  |  | Y |  |
| car_rate | numeric |  |  |  | Y | 0 |
| van_rate | numeric |  |  |  | Y | 0 |
| truck_rate | numeric |  |  |  | Y | 0 |
| weight_surcharge_rate | numeric |  |  |  | Y |  |
| weight_surcharge_threshold_kg | numeric |  |  |  | Y |  |
| cities_json | text |  |  |  | Y | [] |
| sort_order | integer |  |  |  | Y | 0 |
| is_active | boolean |  |  |  | Y | True |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0170DC0> |

**Indexes:**

- `ix_country_oman_delivery_zones_created_by` (created_by)
- `ix_oman_zone_code` (zone_code)
- `ix_country_oman_delivery_zones_is_deleted` (is_deleted)
- `ix_country_oman_delivery_zones_updated_by` (updated_by)
- `ix_country_oman_delivery_zones_id` (id)

---

### `country.country.parcel_location_trackers`

*Table: `country.country.parcel_location_trackers`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| parcel_id | integer |  | Y |  |  |  |
| country_code | string |  | Y |  |  |  |
| latitude | float |  |  |  | Y |  |
| longitude | float |  |  |  | Y |  |
| location_name | string |  |  |  | Y |  |
| timestamp | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0C2BE20> |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0C2BF40> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0C2BEB0> |

**Indexes:**

- `ix_country_parcel_location_trackers_country_code` (country_code)
- `ixplt_created` (created_at)
- `ixplt_parcel` (parcel_id)
- `ix_country_parcel_location_trackers_id` (id)
- `ix_country_parcel_location_trackers_is_deleted` (is_deleted)
- `ix_country_parcel_location_trackers_parcel_id` (parcel_id)

**Foreign Keys:**

- `parcel_id` → `logistics.shipments.id`
- `country_code` → `country.country_configs.code`

---

### `country.country.payment_orchestrator_syncs`

*Table: `country.country.payment_orchestrator_syncs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| country_code | string |  | Y |  |  |  |
| gateway_id | string |  |  |  |  |  |
| gateway_name | string |  |  |  | Y |  |
| environment | string |  |  |  | Y | test |
| is_active | boolean |  |  |  | Y | True |
| fee_percent | numeric |  |  |  | Y |  |
| fee_fixed | numeric |  |  |  | Y |  |
| supported_payment_methods | text |  |  |  | Y |  |
| last_sync_at | datetime |  |  |  | Y |  |
| status | string |  |  |  | Y | active |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0C29750> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0C295A0> |

**Indexes:**

- `ix_country_payment_orchestrator_syncs_is_deleted` (is_deleted)
- `ix_country_payment_orchestrator_syncs_id` (id)
- `ix_country_payment_orchestrator_syncs_country_code` (country_code)
- `ix_pos_status` (status)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `country.country.shift_handover_logs`

*Table: `country.country.shift_handover_logs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| country_code | string |  | Y |  |  |  |
| shift_start | datetime |  |  |  |  |  |
| shift_end | datetime |  |  |  | Y |  |
| notes | text |  |  |  | Y |  |
| handover_to_user_id | integer |  | Y |  | Y |  |
| handover_notes | text |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0C29000> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0C28F70> |

**Indexes:**

- `ix_handover_user_created` (user_id, created_at)
- `ix_country_shift_handover_logs_user_id` (user_id)
- `ix_country_shift_handover_logs_id` (id)
- `ix_country_shift_handover_logs_country_code` (country_code)
- `ix_country_shift_handover_logs_is_deleted` (is_deleted)

**Foreign Keys:**

- `user_id` → `accounts.users.id`
- `country_code` → `country.country_configs.code`
- `handover_to_user_id` → `accounts.users.id`

---

### `country.country.shop_warehouse_locations`

*Table: `country.country.shop_warehouse_locations`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| country_code | string |  | Y |  |  |  |
| name | string |  |  |  |  |  |
| warehouse_code | string |  |  |  |  |  |
| latitude | float |  |  |  | Y |  |
| longitude | float |  |  |  | Y |  |
| address | text |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0C2B250> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0C2B1C0> |

**Indexes:**

- `ix_country_shop_warehouse_locations_id` (id)
- `ix_country_shop_warehouse_locations_is_deleted` (is_deleted)
- `ix_country_shop_warehouse_locations_country_code` (country_code)
- `ix_swl_active` (is_active)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `country.country.supplier_kyc_requirements`

*Table: `country.country.supplier_kyc_requirements`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0171990> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| country_code | string |  | Y | Y |  |  |
| kyc_tier_required | string |  |  |  |  | standard |
| document_types_required | text |  |  |  | Y |  |
| verification_wait_days | integer |  |  |  | Y | 3 |
| auto_approve_threshold | numeric |  |  |  | Y | 0.85 |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0171A20> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0171AB0> |

**Indexes:**

- `ix_country_supplier_kyc_requirements_created_by` (created_by)
- UNIQUE `ix_country_supplier_kyc_requirements_country_code` (country_code)
- `ix_country_supplier_kyc_requirements_is_deleted` (is_deleted)
- `ix_country_supplier_kyc_requirements_updated_by` (updated_by)
- `ix_supplier_kyc_requirements_country_created` (country_code, created_at)
- `ix_country_supplier_kyc_requirements_id` (id)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `country.country.supplier_onboarding_syncs`

*Table: `country.country.supplier_onboarding_syncs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| country_code | string |  | Y |  |  |  |
| supplier_id | integer |  | Y |  |  |  |
| kyc_status | string |  |  |  | Y | pending |
| kyc_documents | text |  |  |  | Y |  |
| onboarding_fee_paid | boolean |  |  |  | Y | False |
| monthly_fee_status | string |  |  |  | Y | pending |
| status | string |  |  |  | Y | pending |
| notes | text |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0C29CF0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0C29D80> |

**Indexes:**

- `ix_sos_status` (status)
- `ix_country_supplier_onboarding_syncs_id` (id)
- `ix_country_supplier_onboarding_syncs_supplier_id` (supplier_id)
- `ix_country_supplier_onboarding_syncs_country_code` (country_code)
- `ix_country_supplier_onboarding_syncs_is_deleted` (is_deleted)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`
- `supplier_id` → `accounts.users.id`

---

## CUSTOMERS

*Schema: `customers` · 3 tables*

### `customers.customers.cross_country_customer_sessions`

*Table: `customers.customers.cross_country_customer_sessions`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B1701900> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| user_id | integer |  |  |  |  |  |
| source_country_code | string |  |  |  |  |  |
| target_country_code | string |  |  |  |  |  |
| session_data | text |  |  |  | Y |  |
| conversion | boolean |  |  |  | Y | False |
| order_id | integer |  |  |  | Y |  |
| ip_address | string |  |  |  | Y |  |
| user_agent | string |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B17025F0> |

**Indexes:**

- `ix_cross_country_user` (user_id)
- `ix_customers_cross_country_customer_sessions_is_deleted` (is_deleted)
- `ix_customers_cross_country_customer_sessions_updated_by` (updated_by)
- `ix_customers_cross_country_customer_sessions_id` (id)
- `ix_customers_cross_country_customer_sessions_created_by` (created_by)

---

### `customers.customers.referral_point_events`

*Table: `customers.customers.referral_point_events`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| event_type | string |  |  |  |  |  |
| points | integer |  |  |  |  |  |
| referred_user_id | integer |  | Y |  | Y |  |
| is_deleted | boolean |  |  |  | Y | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7AFE59480> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7AFE593F0> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_referral_point_events_type` (event_type)
- `ix_referral_point_events_user` (user_id)
- `ix_customers_referral_point_events_id` (id)
- `ix_customers_referral_point_events_country_code` (country_code)

**Foreign Keys:**

- `user_id` → `accounts.users.id`
- `referred_user_id` → `accounts.users.id`

---

### `customers.customers.referrals`

*Table: `customers.customers.referrals`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| referrer_id | integer |  | Y |  |  |  |
| referred_id | integer |  | Y | Y |  |  |
| referral_code | string |  |  | Y | Y |  |
| status | string |  |  |  | Y | pending |
| is_deleted | boolean |  |  |  | Y | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7AFE58E50> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7AFE58DC0> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_customers_referrals_country_code` (country_code)
- `ix_referrals_code` (referral_code)
- `ix_customers_referrals_id` (id)
- `ix_referrals_referrer` (referrer_id)
- `ix_referrals_referred` (referred_id)

**Foreign Keys:**

- `referrer_id` → `accounts.users.id`
- `referred_id` → `accounts.users.id`

---

## FINANCE

*Schema: `finance` · 58 tables*

### `finance.finance.account_balances`

*Table: `finance.finance.account_balances`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B04EDB40> |
| version | integer |  |  |  |  | 1 |
| created_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| account_id | integer |  | Y |  |  |  |
| user_id | integer |  | Y |  | Y |  |
| balance | numeric |  |  |  | Y | 0 |
| currency | string |  |  |  | Y | OMR |
| last_entry_id | integer |  |  |  | Y |  |
| last_entry_at | datetime |  |  |  | Y |  |
| last_updated | datetime |  |  |  | Y | <function utcnow at 0x000001C7B04EDC60> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B04EDBD0> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_finance_account_balances_country_code` (country_code)
- `ix_account_balance_user` (user_id)
- `ix_finance_account_balances_created_by_id` (created_by_id)
- `ix_finance_account_balances_account_id` (account_id)
- `ix_finance_account_balances_updated_by` (updated_by)
- `ix_account_balance_account` (account_id)
- `ix_finance_account_balances_is_deleted` (is_deleted)
- `ix_finance_account_balances_id` (id)
- `ix_finance_account_balances_user_id` (user_id)

**Foreign Keys:**

- `account_id` → `finance.accounts.id`
- `user_id` → `accounts.users.id`

---

### `finance.finance.account_groups`

*Table: `finance.finance.account_groups`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B04ED5A0> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| code | string |  |  | Y |  |  |
| name | string |  |  |  |  |  |
| description | text |  |  |  | Y |  |
| account_type | string |  |  |  |  |  |
| normal_side | string |  |  |  |  |  |
| display_order | integer |  |  |  | Y | 0 |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B04ED6C0> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_finance_account_groups_updated_by` (updated_by)
- `ix_account_groups_country_created` (country_code, created_at)
- `ix_finance_account_groups_is_deleted` (is_deleted)
- `ix_finance_account_groups_id` (id)
- `ix_account_groups_order` (display_order)
- `ix_finance_account_groups_country_code` (country_code)
- `ix_finance_account_groups_created_by_id` (created_by_id)
- `ix_account_groups_code` (code)

---

### `finance.finance.accounts`

*Table: `finance.finance.accounts`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B04ED000> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| group_id | integer |  | Y |  | Y |  |
| code | string |  |  | Y |  |  |
| name | string |  |  |  |  |  |
| normal_side | string |  |  |  |  |  |
| currency | string |  |  |  | Y | USD |
| is_active | boolean |  |  |  | Y | True |
| display_order | integer |  |  |  | Y | 0 |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B04ED120> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_finance_accounts_id` (id)
- `ix_finance_accounts_group_id` (group_id)
- `ix_finance_accounts_created_by_id` (created_by_id)
- `ix_accounts_group` (group_id)
- `ix_finance_accounts_country_code` (country_code)
- `ix_finance_accounts_updated_by` (updated_by)
- `ix_accounts_country_created` (country_code, created_at)
- `ix_accounts_code` (code)
- `ix_finance_accounts_is_deleted` (is_deleted)

**Foreign Keys:**

- `group_id` → `finance.account_groups.id`

---

### `finance.finance.accruals`

*Table: `finance.finance.accruals`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0726560> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| accrual_type | string |  |  |  |  |  |
| description | string |  |  |  | Y |  |
| amount | numeric |  |  |  |  |  |
| expense_account_code | string |  |  |  |  |  |
| accrual_account_code | string |  |  |  |  |  |
| accrual_date | datetime |  |  |  |  |  |
| reversal_date | datetime |  |  |  | Y |  |
| status | string |  |  |  | Y | open |
| journal_entry_id | integer |  | Y |  | Y |  |
| reversal_entry_id | integer |  | Y |  | Y |  |
| country_code | string |  |  |  | Y |  |
| created_by_id | integer |  | Y |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B07265F0> |

**Indexes:**

- `ix_finance_accruals_reversal_entry_id` (reversal_entry_id)
- `ix_finance_accruals_updated_by` (updated_by)
- `ix_accruals_country_created` (country_code, created_at)
- `ix_finance_accruals_journal_entry_id` (journal_entry_id)
- `ix_finance_accruals_id` (id)
- `ix_accrual_status` (status)
- `ix_finance_accruals_country_code` (country_code)
- `ix_accrual_country` (country_code)
- `ix_finance_accruals_is_deleted` (is_deleted)
- `ix_finance_accruals_created_by_id` (created_by_id)

**Foreign Keys:**

- `journal_entry_id` → `finance.journal_entries.id`
- `reversal_entry_id` → `finance.journal_entries.id`
- `created_by_id` → `accounts.users.id`

---

### `finance.finance.ap_bills`

*Table: `finance.finance.ap_bills`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B08213F0> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| vendor_id | integer |  | Y |  |  |  |
| bill_number | string |  |  |  | Y |  |
| bill_date | datetime |  |  |  |  |  |
| due_date | datetime |  |  |  | Y |  |
| account_code | string |  |  |  |  |  |
| amount | numeric |  |  |  |  |  |
| tax_amount | numeric |  |  |  | Y | 0 |
| description | text |  |  |  | Y |  |
| status | string |  |  |  | Y | received |
| linked_journal_entry_id | integer |  | Y |  | Y |  |
| paid_journal_entry_id | integer |  | Y |  | Y |  |
| country_code | string |  |  |  | Y |  |
| created_by_id | integer |  | Y |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0821510> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0821480> |

**Indexes:**

- `ix_ap_bills_due` (due_date)
- `ix_finance_ap_bills_updated_by` (updated_by)
- `ix_finance_ap_bills_id` (id)
- `ix_finance_ap_bills_created_by_id` (created_by_id)
- `ix_finance_ap_bills_paid_journal_entry_id` (paid_journal_entry_id)
- `ix_ap_bills_status` (status)
- `ix_finance_ap_bills_is_deleted` (is_deleted)
- `ix_ap_bills_vendor` (vendor_id)
- `ix_finance_ap_bills_vendor_id` (vendor_id)
- `ix_finance_ap_bills_linked_journal_entry_id` (linked_journal_entry_id)
- `ix_finance_ap_bills_country_code` (country_code)
- `ix_ap_bills_country_created` (country_code, created_at)
- `ix_ap_bills_country` (country_code)

**Foreign Keys:**

- `vendor_id` → `finance.vendors.id`
- `linked_journal_entry_id` → `finance.journal_entries.id`
- `paid_journal_entry_id` → `finance.journal_entries.id`
- `created_by_id` → `accounts.users.id`

---

### `finance.finance.ap_ledger_entries`

*Table: `finance.finance.ap_ledger_entries`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B04EE7A0> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| deleted_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| supplier_id | integer |  | Y |  |  |  |
| order_id | integer |  | Y |  | Y |  |
| invoice_id | integer |  | Y |  | Y |  |
| settlement_id | integer |  | Y |  | Y |  |
| reference_type | string |  |  |  | Y |  |
| reference_id | integer |  |  |  | Y |  |
| entry_type | string |  |  |  |  |  |
| amount | numeric |  |  |  |  |  |
| balance_after | numeric |  |  |  | Y |  |
| currency | string |  |  |  | Y | OMR |
| status | string |  |  |  | Y | open |
| due_date | datetime |  |  |  | Y |  |
| paid_at | datetime |  |  |  | Y |  |
| description | text |  |  |  | Y |  |
| created_by_id | integer |  | Y |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B04EE8C0> |
| country_code | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  | Y | False |
| deleted_at | datetime |  |  |  | Y |  |

**Indexes:**

- `ix_ap_ledger_entries_country_created` (country_code, created_at)
- `ix_finance_ap_ledger_entries_created_by_id` (created_by_id)
- `ix_finance_ap_ledger_entries_order_id` (order_id)
- `ix_finance_ap_ledger_entries_settlement_id` (settlement_id)
- `ix_finance_ap_ledger_entries_id` (id)
- `ix_ap_ledger_status` (status)
- `ix_finance_ap_ledger_entries_country_code` (country_code)
- `ix_ap_ledger_supplier` (supplier_id)
- `ix_finance_ap_ledger_entries_invoice_id` (invoice_id)
- `ix_finance_ap_ledger_entries_supplier_id` (supplier_id)
- `ix_finance_ap_ledger_entries_is_deleted` (is_deleted)
- `ix_finance_ap_ledger_entries_updated_by` (updated_by)

**Foreign Keys:**

- `supplier_id` → `accounts.users.id`
- `order_id` → `orders.orders.id`
- `invoice_id` → `finance.invoices.id`
- `settlement_id` → `finance.supplier_settlements.id`
- `created_by_id` → `accounts.users.id`

---

### `finance.finance.ar_invoices`

*Table: `finance.finance.ar_invoices`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0821AB0> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| customer_id | integer |  | Y |  |  |  |
| invoice_number | string |  |  |  | Y |  |
| invoice_date | datetime |  |  |  |  |  |
| due_date | datetime |  |  |  | Y |  |
| account_code | string |  |  |  | Y | 4010 |
| amount | numeric |  |  |  |  |  |
| tax_amount | numeric |  |  |  | Y | 0 |
| description | text |  |  |  | Y |  |
| status | string |  |  |  | Y | issued |
| linked_journal_entry_id | integer |  | Y |  | Y |  |
| paid_journal_entry_id | integer |  | Y |  | Y |  |
| country_code | string |  |  |  | Y |  |
| created_by_id | integer |  | Y |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0821BD0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0821B40> |

**Indexes:**

- `ix_finance_ar_invoices_created_by_id` (created_by_id)
- `ix_ar_invoices_status` (status)
- `ix_finance_ar_invoices_paid_journal_entry_id` (paid_journal_entry_id)
- `ix_ar_invoices_customer` (customer_id)
- `ix_finance_ar_invoices_customer_id` (customer_id)
- `ix_finance_ar_invoices_updated_by` (updated_by)
- `ix_finance_ar_invoices_linked_journal_entry_id` (linked_journal_entry_id)
- `ix_ar_invoices_country_created` (country_code, created_at)
- `ix_finance_ar_invoices_is_deleted` (is_deleted)
- `ix_finance_ar_invoices_country_code` (country_code)
- `ix_ar_invoices_country` (country_code)
- `ix_finance_ar_invoices_id` (id)
- `ix_ar_invoices_due` (due_date)

**Foreign Keys:**

- `customer_id` → `finance.customers.id`
- `linked_journal_entry_id` → `finance.journal_entries.id`
- `paid_journal_entry_id` → `finance.journal_entries.id`
- `created_by_id` → `accounts.users.id`

---

### `finance.finance.ar_ledger_entries`

*Table: `finance.finance.ar_ledger_entries`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B04EE200> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| deleted_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| customer_id | integer |  | Y |  |  |  |
| order_id | integer |  | Y |  | Y |  |
| invoice_id | integer |  | Y |  | Y |  |
| reference_type | string |  |  |  | Y |  |
| reference_id | integer |  |  |  | Y |  |
| entry_type | string |  |  |  |  |  |
| amount | numeric |  |  |  |  |  |
| balance_after | numeric |  |  |  | Y |  |
| currency | string |  |  |  | Y | OMR |
| status | string |  |  |  | Y | open |
| due_date | datetime |  |  |  | Y |  |
| settled_at | datetime |  |  |  | Y |  |
| description | text |  |  |  | Y |  |
| created_by_id | integer |  | Y |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B04EE290> |
| country_code | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  | Y | False |
| deleted_at | datetime |  |  |  | Y |  |

**Indexes:**

- `ix_finance_ar_ledger_entries_order_id` (order_id)
- `ix_ar_ledger_status` (status)
- `ix_finance_ar_ledger_entries_id` (id)
- `ix_finance_ar_ledger_entries_created_by_id` (created_by_id)
- `ix_finance_ar_ledger_entries_is_deleted` (is_deleted)
- `ix_ar_ledger_entries_country_created` (country_code, created_at)
- `ix_ar_ledger_user` (customer_id)
- `ix_finance_ar_ledger_entries_customer_id` (customer_id)
- `ix_finance_ar_ledger_entries_invoice_id` (invoice_id)
- `ix_finance_ar_ledger_entries_country_code` (country_code)
- `ix_finance_ar_ledger_entries_updated_by` (updated_by)

**Foreign Keys:**

- `customer_id` → `accounts.users.id`
- `order_id` → `orders.orders.id`
- `invoice_id` → `finance.invoices.id`
- `created_by_id` → `accounts.users.id`

---

### `finance.finance.automation_logs`

*Table: `finance.finance.automation_logs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0727880> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| rule_id | integer |  | Y |  |  |  |
| status | string |  |  |  | Y | success |
| message | text |  |  |  | Y |  |
| records_affected | integer |  |  |  | Y | 0 |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0727910> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B07279A0> |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |

**Indexes:**

- `ix_finance_automation_logs_created_by_id` (created_by_id)
- `ix_finance_automation_logs_id` (id)
- `ix_finance_automation_logs_updated_by` (updated_by)
- `ix_finance_automation_logs_country_code` (country_code)
- `ix_automation_logs_country_created` (country_code, created_at)
- `ix_automation_logs_rule` (rule_id)
- `ix_finance_automation_logs_is_deleted` (is_deleted)
- `ix_finance_automation_logs_rule_id` (rule_id)

**Foreign Keys:**

- `rule_id` → `finance.automation_rules.id`

---

### `finance.finance.automation_rules`

*Table: `finance.finance.automation_rules`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B07271C0> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| name | string |  |  |  |  |  |
| description | text |  |  |  | Y |  |
| rule_type | string |  |  |  | Y |  |
| trigger | string |  |  |  | Y |  |
| action | string |  |  |  | Y |  |
| config | text |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0727250> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B07272E0> |

**Indexes:**

- `ix_finance_automation_rules_is_deleted` (is_deleted)
- `ix_finance_automation_rules_updated_by` (updated_by)
- `ix_finance_automation_rules_id` (id)
- `ix_finance_automation_rules_country_code` (country_code)
- `ix_finance_automation_rules_created_by_id` (created_by_id)
- `ix_automation_rules_country_created` (country_code, created_at)

---

### `finance.finance.bank_accounts`

*Table: `finance.finance.bank_accounts`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0822170> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| bank_name | string |  |  |  |  |  |
| account_name | string |  |  |  | Y |  |
| account_number | string |  |  |  | Y |  |
| iban | string |  |  |  | Y |  |
| swift_bic | string |  |  |  | Y |  |
| currency | string |  |  |  | Y | OMR |
| gl_account_code | string |  |  |  | Y | 1010 |
| country_code | string |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0822200> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0822290> |

**Indexes:**

- `ix_bank_accounts_country_created` (country_code, created_at)
- `ix_finance_bank_accounts_country_code` (country_code)
- `ix_bank_accounts_country` (country_code)
- `ix_finance_bank_accounts_created_by_id` (created_by_id)
- `ix_finance_bank_accounts_updated_by` (updated_by)
- `ix_finance_bank_accounts_is_deleted` (is_deleted)
- `ix_finance_bank_accounts_id` (id)

---

### `finance.finance.bank_mapping_rules`

*Table: `finance.finance.bank_mapping_rules`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0724CA0> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| country_code | string |  |  |  | Y |  |
| name | string |  |  |  |  |  |
| match_pattern | string |  |  |  |  |  |
| description_contains | string |  |  |  | Y |  |
| account_code | string |  |  |  |  |  |
| normal_side | string |  |  |  |  |  |
| category | string |  |  |  | Y |  |
| priority | integer |  |  |  | Y | 100 |
| is_active | boolean |  |  |  | Y | True |
| created_by_id | integer |  | Y |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0724DC0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0724D30> |

**Indexes:**

- `ix_finance_bank_mapping_rules_id` (id)
- `ix_finance_bank_mapping_rules_updated_by` (updated_by)
- `ix_bank_mapping_country` (country_code)
- `ix_bank_mapping_rules_country_created` (country_code, created_at)
- `ix_finance_bank_mapping_rules_is_deleted` (is_deleted)
- `ix_bank_mapping_priority` (priority)
- `ix_finance_bank_mapping_rules_country_code` (country_code)
- `ix_finance_bank_mapping_rules_created_by_id` (created_by_id)

**Foreign Keys:**

- `created_by_id` → `accounts.users.id`

---

### `finance.finance.bank_reconciliations`

*Table: `finance.finance.bank_reconciliations`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0822EF0> |
| version | integer |  |  |  |  | 1 |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| statement_line_id | integer |  | Y |  |  |  |
| journal_entry_id | integer |  | Y |  | Y |  |
| matched_amount | numeric |  |  |  | Y |  |
| status | string |  |  |  | Y | matched |
| note | text |  |  |  | Y |  |
| matched_by_id | integer |  | Y |  | Y |  |
| matched_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0822F80> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_finance_bank_reconciliations_created_by_id` (created_by_id)
- `ix_finance_bank_reconciliations_updated_by` (updated_by)
- `ix_finance_bank_reconciliations_matched_by_id` (matched_by_id)
- `ix_finance_bank_reconciliations_is_deleted` (is_deleted)
- `ix_finance_bank_reconciliations_journal_entry_id` (journal_entry_id)
- `ix_bank_recon_country` (country_code)
- `ix_finance_bank_reconciliations_id` (id)
- `ix_bank_recon_status` (status)
- `ix_finance_bank_reconciliations_country_code` (country_code)
- `ix_finance_bank_reconciliations_statement_line_id` (statement_line_id)

**Foreign Keys:**

- `statement_line_id` → `finance.bank_statement_lines.id`
- `journal_entry_id` → `finance.journal_entries.id`
- `matched_by_id` → `accounts.users.id`

---

### `finance.finance.bank_statement_imports`

*Table: `finance.finance.bank_statement_imports`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0725360> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| bank_name | string |  |  |  | Y |  |
| file_name | string |  |  |  | Y |  |
| statement_period_start | datetime |  |  |  | Y |  |
| statement_period_end | datetime |  |  |  | Y |  |
| currency | string |  |  |  | Y | OMR |
| total_lines | integer |  |  |  | Y | 0 |
| matched_lines | integer |  |  |  | Y | 0 |
| unmatched_lines | integer |  |  |  | Y | 0 |
| status | string |  |  |  | Y | imported |
| imported_by_id | integer |  | Y |  | Y |  |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B07253F0> |

**Indexes:**

- `ix_bsi_country` (country_code)
- `ix_finance_bank_statement_imports_created_by_id` (created_by_id)
- `ix_finance_bank_statement_imports_updated_by` (updated_by)
- `ix_finance_bank_statement_imports_country_code` (country_code)
- `ix_finance_bank_statement_imports_is_deleted` (is_deleted)
- `ix_finance_bank_statement_imports_id` (id)
- `ix_bank_statement_imports_country_created` (country_code, created_at)
- `ix_finance_bank_statement_imports_imported_by_id` (imported_by_id)

**Foreign Keys:**

- `imported_by_id` → `accounts.users.id`

---

### `finance.finance.bank_statement_lines`

*Table: `finance.finance.bank_statement_lines`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0725900> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| import_id | integer |  | Y |  |  |  |
| txn_date | datetime |  |  |  | Y |  |
| description | string |  |  |  | Y |  |
| reference | string |  |  |  | Y |  |
| amount | numeric |  |  |  |  |  |
| mapped_account_code | string |  |  |  | Y |  |
| mapped_side | string |  |  |  | Y |  |
| mapping_rule_id | integer |  | Y |  | Y |  |
| status | string |  |  |  | Y | unmapped |
| posted_journal_entry_id | integer |  | Y |  | Y |  |
| reconciled_transaction_id | integer |  | Y |  | Y |  |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0725A20> |

**Indexes:**

- `ix_finance_bank_statement_lines_country_code` (country_code)
- `ix_bank_statement_lines_country_created` (country_code, created_at)
- `ix_finance_bank_statement_lines_id` (id)
- `ix_finance_bank_statement_lines_posted_journal_entry_id` (posted_journal_entry_id)
- `ix_finance_bank_statement_lines_created_by_id` (created_by_id)
- `ix_bsl_country` (country_code)
- `ix_finance_bank_statement_lines_updated_by` (updated_by)
- `ix_finance_bank_statement_lines_import_id` (import_id)
- `ix_finance_bank_statement_lines_reconciled_transaction_id` (reconciled_transaction_id)
- `ix_finance_bank_statement_lines_mapping_rule_id` (mapping_rule_id)
- `ix_bsl_status` (status)
- `ix_finance_bank_statement_lines_is_deleted` (is_deleted)
- `ix_bsl_import` (import_id)

**Foreign Keys:**

- `import_id` → `finance.bank_statement_imports.id`
- `mapping_rule_id` → `finance.bank_mapping_rules.id`
- `posted_journal_entry_id` → `finance.journal_entries.id`
- `reconciled_transaction_id` → `finance.bank_transactions.id`

---

### `finance.finance.bank_transactions`

*Table: `finance.finance.bank_transactions`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B06185E0> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| transaction_ref | string |  |  |  | Y |  |
| source | string |  |  |  | Y |  |
| transaction_type | string |  |  |  |  |  |
| category | string |  |  |  | Y |  |
| amount | numeric |  |  |  |  |  |
| currency | string |  |  |  | Y | OMR |
| description | text |  |  |  | Y |  |
| linked_order_id | integer |  | Y |  | Y |  |
| linked_supplier_id | integer |  | Y |  | Y |  |
| linked_logistics_id | integer |  |  |  | Y |  |
| linked_payout_id | integer |  |  |  | Y |  |
| linked_refund_id | integer |  |  |  | Y |  |
| reconciled | boolean |  |  |  | Y | False |
| reconciled_by_id | integer |  | Y |  | Y |  |
| reconciled_at | datetime |  |  |  | Y |  |
| transaction_date | datetime |  |  |  | Y |  |
| status | string |  |  |  | Y | pending |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0618700> |
| country_code | string |  |  |  | Y |  |
| flagged | boolean |  |  |  | Y | False |
| flag_reason | text |  |  |  | Y |  |

**Indexes:**

- `ix_finance_bank_transactions_country_code` (country_code)
- `ix_finance_bank_transactions_reconciled_by_id` (reconciled_by_id)
- `ix_finance_bank_transactions_linked_supplier_id` (linked_supplier_id)
- `ix_finance_bank_transactions_id` (id)
- `ix_bank_transactions_country_created` (country_code, created_at)
- `ix_finance_bank_transactions_is_deleted` (is_deleted)
- `ix_finance_bank_transactions_linked_order_id` (linked_order_id)
- `ix_finance_bank_transactions_created_by_id` (created_by_id)
- `ix_finance_bank_transactions_transaction_ref` (transaction_ref)
- `ix_finance_bank_transactions_updated_by` (updated_by)

**Foreign Keys:**

- `linked_order_id` → `orders.orders.id`
- `linked_supplier_id` → `accounts.users.id`
- `reconciled_by_id` → `accounts.users.id`

---

### `finance.finance.budgets`

*Table: `finance.finance.budgets`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0822830> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| account_code | string |  |  |  |  |  |
| fiscal_period_id | integer |  | Y |  |  |  |
| amount | numeric |  |  |  |  |  |
| currency | string |  |  |  | Y | OMR |
| country_code | string |  |  |  | Y |  |
| notes | text |  |  |  | Y |  |
| created_by_id | integer |  | Y |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0822950> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B08228C0> |

**Indexes:**

- `ix_finance_budgets_fiscal_period_id` (fiscal_period_id)
- `ix_finance_budgets_created_by_id` (created_by_id)
- `ix_budgets_country` (country_code)
- `ix_budgets_country_created` (country_code, created_at)
- `ix_finance_budgets_updated_by` (updated_by)
- `ix_finance_budgets_is_deleted` (is_deleted)
- `ix_finance_budgets_id` (id)
- `ix_finance_budgets_country_code` (country_code)

**Foreign Keys:**

- `fiscal_period_id` → `finance.fiscal_periods.id`
- `created_by_id` → `accounts.users.id`

---

### `finance.finance.cash_accounts`

*Table: `finance.finance.cash_accounts`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0619120> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| name | string |  |  |  |  |  |
| account_type | string |  |  |  |  |  |
| currency | string |  |  |  | Y | USD |
| balance | numeric |  |  |  | Y | 0 |
| description | text |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| created_by_id | integer |  | Y |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0619240> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B06191B0> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_finance_cash_accounts_country_code` (country_code)
- `ix_finance_cash_accounts_id` (id)
- `ix_cash_accounts_country_created` (country_code, created_at)
- `ix_finance_cash_accounts_updated_by` (updated_by)
- `ix_finance_cash_accounts_created_by_id` (created_by_id)
- `ix_finance_cash_accounts_is_deleted` (is_deleted)

**Foreign Keys:**

- `created_by_id` → `accounts.users.id`

---

### `finance.finance.cash_flow_forecasts`

*Table: `finance.finance.cash_flow_forecasts`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B061A9E0> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| forecast_date | datetime |  |  |  |  |  |
| period_start | datetime |  |  |  |  |  |
| period_end | datetime |  |  |  |  |  |
| net_cash_flow | numeric |  |  |  | Y | 0 |
| opening_balance | numeric |  |  |  | Y | 0 |
| closing_balance | numeric |  |  |  | Y | 0 |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B061AB00> |

**Indexes:**

- `ix_finance_cash_flow_forecasts_updated_by` (updated_by)
- `ix_finance_cash_flow_forecasts_is_deleted` (is_deleted)
- `ix_finance_cash_flow_forecasts_id` (id)
- `ix_cash_flow_forecasts_country_created` (country_code, created_at)
- `ix_finance_cash_flow_forecasts_country_code` (country_code)
- `ix_finance_cash_flow_forecasts_created_by_id` (created_by_id)

---

### `finance.finance.cash_position_snapshots`

*Table: `finance.finance.cash_position_snapshots`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B061AF80> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| snapshot_time | datetime |  |  |  |  |  |
| account_id | integer |  | Y |  |  |  |
| balance | numeric |  |  |  | Y | 0 |
| currency | string |  |  |  | Y | USD |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B061B010> |

**Indexes:**

- `ix_finance_cash_position_snapshots_created_by_id` (created_by_id)
- `ix_finance_cash_position_snapshots_is_deleted` (is_deleted)
- `ix_finance_cash_position_snapshots_updated_by` (updated_by)
- `ix_cash_position_snapshots_country_created` (country_code, created_at)
- `ix_finance_cash_position_snapshots_id` (id)
- `ix_finance_cash_position_snapshots_country_code` (country_code)
- `ix_finance_cash_position_snapshots_account_id` (account_id)

**Foreign Keys:**

- `account_id` → `finance.treasury_accounts.id`

---

### `finance.finance.cash_transactions`

*Table: `finance.finance.cash_transactions`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B06197E0> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| account_id | integer |  | Y |  |  |  |
| transaction_type | string |  |  |  |  |  |
| amount | numeric |  |  |  |  |  |
| balance_after | numeric |  |  |  | Y |  |
| description | text |  |  |  | Y |  |
| reference | string |  |  |  | Y |  |
| category | string |  |  |  | Y |  |
| performed_by_id | integer |  | Y |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0619900> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_finance_cash_transactions_country_code` (country_code)
- `ix_finance_cash_transactions_created_by_id` (created_by_id)
- `ix_finance_cash_transactions_performed_by_id` (performed_by_id)
- `ix_finance_cash_transactions_account_id` (account_id)
- `ix_finance_cash_transactions_updated_by` (updated_by)
- `ix_finance_cash_transactions_is_deleted` (is_deleted)
- `ix_finance_cash_transactions_id` (id)
- `ix_cash_transactions_country_created` (country_code, created_at)

**Foreign Keys:**

- `account_id` → `finance.cash_accounts.id`
- `performed_by_id` → `accounts.users.id`

---

### `finance.finance.commission_agreements`

*Table: `finance.finance.commission_agreements`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | string |  |  | Y |  |  |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| supplier_id | integer |  | Y |  |  |  |
| country_code | string |  |  |  |  |  |
| tier | string |  |  |  |  |  |
| rate | numeric |  |  |  |  |  |
| set_by_admin_id | integer |  | Y |  | Y |  |
| is_active | boolean |  |  |  |  | True |
| effective_from | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0409240> |
| effective_to | datetime |  |  |  | Y |  |
| note | text |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B04092D0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0409360> |

**Indexes:**

- `ix_finance_commission_agreements_id` (id)
- `ix_finance_commission_agreements_is_deleted` (is_deleted)
- `ix_finance_commission_agreements_created_by` (created_by)
- `ix_finance_commission_agreements_country_code` (country_code)
- `ix_commission_agreements_supplier` (supplier_id)
- `ix_finance_commission_agreements_supplier_id` (supplier_id)
- `ix_finance_commission_agreements_updated_by` (updated_by)
- `ix_finance_commission_agreements_set_by_admin_id` (set_by_admin_id)
- `ix_commission_agreements_country` (country_code)

**Foreign Keys:**

- `supplier_id` → `accounts.users.id`
- `set_by_admin_id` → `accounts.users.id`

---

### `finance.finance.commission_category_rates`

*Table: `finance.finance.commission_category_rates`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | string |  |  | Y |  |  |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| category_id | integer |  | Y |  | Y |  |
| category_slug | string |  |  |  | Y |  |
| category_display_name | string |  |  |  | Y |  |
| country_code | string |  | Y |  | Y |  |
| rate_percent | numeric |  |  |  |  | 0 |
| is_active | boolean |  |  |  |  | True |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B040A560> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B040A5F0> |

**Indexes:**

- `ix_finance_commission_category_rates_category_id` (category_id)
- `ix_finance_commission_category_rates_updated_by` (updated_by)
- `ix_commission_category_rates_country` (country_code)
- `ix_finance_commission_category_rates_id` (id)
- `ix_finance_commission_category_rates_is_deleted` (is_deleted)
- `ix_finance_commission_category_rates_created_by` (created_by)
- `ix_finance_commission_category_rates_country_code` (country_code)

**Foreign Keys:**

- `category_id` → `catalog.categories.id`
- `country_code` → `country.country_configs.code`

---

### `finance.finance.commission_ledger_entries`

*Table: `finance.finance.commission_ledger_entries`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | string |  |  | Y |  |  |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| supplier_id | integer |  | Y |  |  |  |
| order_id | integer |  | Y |  | Y |  |
| order_item_id | integer |  | Y |  | Y |  |
| product_id | integer |  | Y |  | Y |  |
| category_slug | string |  |  |  | Y |  |
| badge_level | string |  |  |  | Y |  |
| global_default_rate | numeric |  |  |  | Y |  |
| category_rate | numeric |  |  |  | Y |  |
| badge_rate | numeric |  |  |  | Y |  |
| override_rate | numeric |  |  |  | Y |  |
| applied_rate | numeric |  |  |  | Y |  |
| calculation_method | string |  |  |  | Y |  |
| order_value | numeric |  |  |  | Y |  |
| commission_pct | numeric |  |  |  | Y |  |
| cap_applied | boolean |  |  |  | Y | False |
| commission_amount | numeric |  |  |  | Y |  |
| low_value_threshold_used | boolean |  |  |  | Y | False |
| fixed_cap_used | boolean |  |  |  | Y | False |
| override_flag | boolean |  |  |  | Y | False |
| is_adjusted | boolean |  |  |  | Y | False |
| currency | string |  |  |  | Y | OMR |
| amount | numeric |  |  |  | Y |  |
| adjusted_by_id | integer |  | Y |  | Y |  |
| status | string |  |  |  | Y | pending |
| credited_at | datetime |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0409FC0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0409F30> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_finance_commission_ledger_entries_updated_by` (updated_by)
- `ix_finance_commission_ledger_entries_order_item_id` (order_item_id)
- `ix_commission_ledger_supplier` (supplier_id)
- `ix_commission_ledger_country` (country_code)
- `ix_finance_commission_ledger_entries_order_id` (order_id)
- `ix_finance_commission_ledger_entries_product_id` (product_id)
- `ix_finance_commission_ledger_entries_id` (id)
- `ix_finance_commission_ledger_entries_is_deleted` (is_deleted)
- `ix_finance_commission_ledger_entries_created_by` (created_by)
- `ix_finance_commission_ledger_entries_country_code` (country_code)
- `ix_finance_commission_ledger_entries_adjusted_by_id` (adjusted_by_id)
- `ix_finance_commission_ledger_entries_supplier_id` (supplier_id)

**Foreign Keys:**

- `supplier_id` → `accounts.users.id`
- `order_id` → `orders.orders.id`
- `order_item_id` → `orders.order_items.id`
- `product_id` → `catalog.products.id`
- `adjusted_by_id` → `accounts.users.id`

---

### `finance.finance.cost_centers`

*Table: `finance.finance.cost_centers`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0820D30> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| code | string |  |  |  |  |  |
| name | string |  |  |  |  |  |
| country_code | string |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0820DC0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0820E50> |

**Indexes:**

- `ix_finance_cost_centers_is_deleted` (is_deleted)
- `ix_cost_centers_country` (country_code)
- `ix_finance_cost_centers_id` (id)
- `ix_finance_cost_centers_country_code` (country_code)
- `ix_finance_cost_centers_updated_by` (updated_by)
- `ix_finance_cost_centers_created_by_id` (created_by_id)
- `ix_cost_centers_country_created` (country_code, created_at)

---

### `finance.finance.customers`

*Table: `finance.finance.customers`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0820670> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| name | string |  |  |  |  |  |
| tax_id | string |  |  |  | Y |  |
| contact_email | string |  |  |  | Y |  |
| currency | string |  |  |  | Y | OMR |
| payment_terms_days | integer |  |  |  | Y | 30 |
| credit_limit | numeric |  |  |  | Y |  |
| country_code | string |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0820700> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0820790> |

**Indexes:**

- `ix_finance_customers_country_code` (country_code)
- `ix_finance_customers_is_deleted` (is_deleted)
- `ix_finance_customers_id` (id)
- `ix_customers_country_created` (country_code, created_at)
- `ix_finance_customers_created_by_id` (created_by_id)
- `ix_finance_customers_updated_by` (updated_by)
- `ix_customers_country` (country_code)

---

### `finance.finance.finance_audit_logs`

*Table: `finance.finance.finance_audit_logs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0823B50> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| action | string |  |  |  |  |  |
| actor_id | integer |  | Y |  | Y |  |
| actor_role | string |  |  |  | Y |  |
| entity_type | string |  |  |  | Y |  |
| entity_id | integer |  |  |  | Y |  |
| country_code | string |  |  |  | Y |  |
| detail | json |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0823BE0> |

**Indexes:**

- `ix_finance_finance_audit_logs_actor_id` (actor_id)
- `ix_finance_finance_audit_logs_country_code` (country_code)
- `ix_finance_finance_audit_logs_created_by_id` (created_by_id)
- `ix_finance_audit_logs_detail_gin` (detail)
- `ix_finance_finance_audit_logs_updated_by` (updated_by)
- `ix_finance_audit_at` (created_at)
- `ix_finance_audit_logs_country_created` (country_code, created_at)
- `ix_finance_audit_actor` (actor_id)
- `ix_finance_finance_audit_logs_is_deleted` (is_deleted)
- `ix_finance_finance_audit_logs_id` (id)
- `ix_finance_audit_action` (action)

**Foreign Keys:**

- `actor_id` → `accounts.users.id`

---

### `finance.finance.finance_automation_logs`

*Table: `finance.finance.finance_automation_logs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B08EC160> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| kind | string |  |  |  |  |  |
| records_processed | integer |  |  |  | Y | 0 |
| records_changed | integer |  |  |  | Y | 0 |
| detail | json |  |  |  | Y |  |
| run_by_id | integer |  | Y |  | Y |  |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B08EC1F0> |

**Indexes:**

- `ix_finance_finance_automation_logs_run_by_id` (run_by_id)
- `ix_finance_finance_automation_logs_id` (id)
- `ix_finance_automation_logs_country_created` (country_code, created_at)
- `ix_fal_country` (country_code)
- `ix_finance_finance_automation_logs_is_deleted` (is_deleted)
- `ix_fal_kind` (kind)
- `ix_finance_finance_automation_logs_created_by_id` (created_by_id)
- `ix_finance_finance_automation_logs_country_code` (country_code)
- `ix_finance_automation_logs_detail_gin` (detail)
- `ix_finance_finance_automation_logs_updated_by` (updated_by)

**Foreign Keys:**

- `run_by_id` → `accounts.users.id`

---

### `finance.finance.financial_reports`

*Table: `finance.finance.financial_reports`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B04EED40> |
| version | integer |  |  |  |  | 1 |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  |  | now() |
| deleted_by_id | integer |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| report_type | string |  |  |  |  |  |
| period_start | datetime |  |  |  |  |  |
| period_end | datetime |  |  |  |  |  |
| country_code | string |  |  |  | Y |  |
| data | json |  |  |  | Y |  |
| generated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B04EEDD0> |
| is_deleted | boolean |  |  |  | Y | False |
| deleted_at | datetime |  |  |  | Y |  |

**Indexes:**

- `ix_finance_financial_reports_is_deleted` (is_deleted)
- `ix_finance_financial_reports_created_by_id` (created_by_id)
- `ix_financial_reports_data` (data)
- `ix_finance_financial_reports_country_code` (country_code)
- `ix_finance_financial_reports_id` (id)
- `ix_finance_financial_reports_updated_by` (updated_by)

---

### `finance.finance.fiscal_periods`

*Table: `finance.finance.fiscal_periods`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B040B130> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| country_code | string |  |  |  |  |  |
| period_year | integer |  |  |  |  |  |
| period_month | integer |  |  |  |  |  |
| period_start | datetime |  |  |  |  |  |
| period_end | datetime |  |  |  |  |  |
| status | string |  |  |  | Y | open |
| is_locked | boolean |  |  |  | Y | False |
| closed_at | datetime |  |  |  | Y |  |
| closed_by_id | integer |  | Y |  | Y |  |
| notes | text |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B040B250> |

**Indexes:**

- `ix_fiscal_periods_country_created` (country_code, created_at)
- `ix_finance_fiscal_periods_id` (id)
- `ix_fiscal_period_country` (country_code)
- `ix_finance_fiscal_periods_is_deleted` (is_deleted)
- `ix_finance_fiscal_periods_created_by_id` (created_by_id)
- `ix_finance_fiscal_periods_closed_by_id` (closed_by_id)
- `ix_finance_fiscal_periods_country_code` (country_code)
- `ix_finance_fiscal_periods_updated_by` (updated_by)

**Foreign Keys:**

- `closed_by_id` → `accounts.users.id`

---

### `finance.finance.fixed_assets`

*Table: `finance.finance.fixed_assets`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0725EA0> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| name | string |  |  |  |  |  |
| asset_code | string |  |  |  | Y |  |
| category | string |  |  |  | Y |  |
| purchase_date | datetime |  |  |  |  |  |
| purchase_cost | numeric |  |  |  |  |  |
| salvage_value | numeric |  |  |  | Y | 0 |
| useful_life_months | integer |  |  |  |  |  |
| accumulated_depreciation | numeric |  |  |  | Y | 0 |
| last_depreciated_date | datetime |  |  |  | Y |  |
| asset_account_code | string |  |  |  | Y | 1100 |
| depreciation_account_code | string |  |  |  | Y | 5070 |
| accumulated_depr_account_code | string |  |  |  | Y | 1190 |
| status | string |  |  |  | Y | active |
| country_code | string |  |  |  | Y |  |
| created_by_id | integer |  | Y |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0725F30> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0725FC0> |

**Indexes:**

- `ix_fa_country` (country_code)
- `ix_finance_fixed_assets_created_by_id` (created_by_id)
- `ix_finance_fixed_assets_is_deleted` (is_deleted)
- `ix_finance_fixed_assets_country_code` (country_code)
- `ix_fixed_assets_country_created` (country_code, created_at)
- `ix_finance_fixed_assets_id` (id)
- `ix_finance_fixed_assets_updated_by` (updated_by)

**Foreign Keys:**

- `created_by_id` → `accounts.users.id`

---

### `finance.finance.gateway_settlement_schedules`

*Table: `finance.finance.gateway_settlement_schedules`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B061B520> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| gateway_id | integer |  | Y |  |  |  |
| settlement_date | datetime |  |  |  |  |  |
| amount | numeric |  |  |  |  |  |
| currency | string |  |  |  | Y | USD |
| status | string |  |  |  | Y | pending |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B061B5B0> |

**Indexes:**

- `ix_finance_gateway_settlement_schedules_gateway_id` (gateway_id)
- `ix_finance_gateway_settlement_schedules_updated_by` (updated_by)
- `ix_finance_gateway_settlement_schedules_is_deleted` (is_deleted)
- `ix_finance_gateway_settlement_schedules_id` (id)
- `ix_gateway_settlement_schedules_country_created` (country_code, created_at)
- `ix_finance_gateway_settlement_schedules_created_by_id` (created_by_id)
- `ix_finance_gateway_settlement_schedules_country_code` (country_code)

**Foreign Keys:**

- `gateway_id` → `finance.payment_gateway_connections.id`

---

### `finance.finance.invoice_items`

*Table: `finance.finance.invoice_items`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B04EFA30> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| invoice_id | integer |  | Y |  |  |  |
| product_id | integer |  | Y |  | Y |  |
| description | string |  |  |  |  |  |
| quantity | integer |  |  |  | Y | 1 |
| unit_price | numeric |  |  |  |  |  |
| discount_amount | numeric |  |  |  | Y |  |
| tax_rate | numeric |  |  |  | Y |  |
| line_total | numeric |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B04EFB50> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_finance_invoice_items_country_code` (country_code)
- `ix_invoice_items_country_created` (country_code, created_at)
- `ix_finance_invoice_items_invoice_id` (invoice_id)
- `ix_finance_invoice_items_created_by_id` (created_by_id)
- `ix_finance_invoice_items_updated_by` (updated_by)
- `ix_finance_invoice_items_is_deleted` (is_deleted)
- `ix_finance_invoice_items_id` (id)
- `ix_finance_invoice_items_product_id` (product_id)

**Foreign Keys:**

- `invoice_id` → `finance.invoices.id`
- `product_id` → `catalog.products.id`

---

### `finance.finance.invoices`

*Table: `finance.finance.invoices`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B04EF2E0> |
| version | integer |  |  |  |  | 1 |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| order_id | integer |  | Y |  |  |  |
| shipment_id | integer |  | Y |  | Y |  |
| supplier_id | integer |  | Y |  | Y |  |
| invoice_number | string |  |  | Y | Y |  |
| invoice_type | string |  |  |  | Y | sale |
| subtotal | numeric |  |  |  | Y |  |
| tax_amount | numeric |  |  |  | Y |  |
| shipping_amount | numeric |  |  |  | Y |  |
| discount_amount | numeric |  |  |  | Y |  |
| total_amount | numeric |  |  |  | Y |  |
| currency | string |  |  |  | Y | USD |
| status | string |  |  |  | Y | pending |
| issued_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B04EF400> |
| due_at | datetime |  |  |  | Y |  |
| picked_at | datetime |  |  |  | Y |  |
| dispatched_at | datetime |  |  |  | Y |  |
| delivered_at | datetime |  |  |  | Y |  |
| paid_at | datetime |  |  |  | Y |  |
| notes | text |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B04EF370> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B04EF490> |
| country_code | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  | Y | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  | Y |  | Y |  |

**Indexes:**

- `ix_invoices_country_created` (country_code, created_at)
- `ix_finance_invoices_country_code` (country_code)
- `ix_finance_invoices_supplier_id` (supplier_id)
- `ix_finance_invoices_id` (id)
- `ix_finance_invoices_updated_by` (updated_by)
- `ix_finance_invoices_is_deleted` (is_deleted)
- `ix_finance_invoices_deleted_by_id` (deleted_by_id)
- `ix_finance_invoices_order_id` (order_id)
- `ix_finance_invoices_created_by_id` (created_by_id)
- `ix_finance_invoices_shipment_id` (shipment_id)

**Foreign Keys:**

- `order_id` → `orders.orders.id`
- `shipment_id` → `logistics.shipments.id`
- `supplier_id` → `accounts.users.id`
- `deleted_by_id` → `accounts.users.id`

---

### `finance.finance.journal_entries`

*Table: `finance.finance.journal_entries`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B04EC4C0> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| entry_date | datetime |  |  |  |  |  |
| reference_number | string |  |  | Y |  |  |
| description | text |  |  |  | Y |  |
| source | string |  |  |  | Y |  |
| country_code | string |  |  |  | Y |  |
| currency | string |  |  |  | Y | OMR |
| is_reconciled | boolean |  |  |  | Y | False |
| created_by_id | integer |  | Y |  | Y |  |
| reference_type | string |  |  |  | Y |  |
| reference_id | integer |  |  |  | Y |  |
| period_id | integer |  | Y |  | Y |  |
| reversal_of_id | integer |  | Y |  | Y |  |
| is_deleted | boolean |  |  |  | Y | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  | Y |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B04EC550> |

**Indexes:**

- `ix_finance_journal_entries_updated_by` (updated_by)
- `ix_journal_entry_date` (entry_date)
- `ix_finance_journal_entries_period_id` (period_id)
- `ix_finance_journal_entries_id` (id)
- `ix_finance_journal_entries_is_deleted` (is_deleted)
- `ix_finance_journal_entries_created_by_id` (created_by_id)
- `ix_finance_journal_entries_deleted_by_id` (deleted_by_id)
- `ix_journal_entries_country_created` (country_code, created_at)
- `ix_journal_entry_country` (country_code)
- `ix_finance_journal_entries_reversal_of_id` (reversal_of_id)
- `ix_journal_entry_ref` (reference_number)

**Foreign Keys:**

- `created_by_id` → `accounts.users.id`
- `period_id` → `finance.fiscal_periods.id`
- `reversal_of_id` → `finance.journal_entries.id`
- `deleted_by_id` → `accounts.users.id`

---

### `finance.finance.journal_entry_lines`

*Table: `finance.finance.journal_entry_lines`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B04ECA60> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| entry_id | integer |  | Y |  |  |  |
| account_id | integer |  | Y |  |  |  |
| cost_center_id | integer |  | Y |  | Y |  |
| amount | numeric |  |  |  |  |  |
| side | string |  |  |  |  |  |
| description | text |  |  |  | Y |  |
| entity_type | string |  |  |  | Y |  |
| entity_id | integer |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B04ECAF0> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_finance_journal_entry_lines_entry_id` (entry_id)
- `ix_journal_entry_lines_country_created` (country_code, created_at)
- `ix_finance_journal_entry_lines_created_by_id` (created_by_id)
- `ix_finance_journal_entry_lines_updated_by` (updated_by)
- `ix_finance_journal_entry_lines_cost_center_id` (cost_center_id)
- `ix_jel_account` (account_id)
- `ix_finance_journal_entry_lines_is_deleted` (is_deleted)
- `ix_finance_journal_entry_lines_country_code` (country_code)
- `ix_jel_entry` (entry_id)
- `ix_finance_journal_entry_lines_id` (id)
- `ix_finance_journal_entry_lines_account_id` (account_id)

**Foreign Keys:**

- `entry_id` → `finance.journal_entries.id`
- `account_id` → `finance.accounts.id`
- `cost_center_id` → `finance.cost_centers.id`

---

### `finance.finance.logistics_partner_payouts`

*Table: `finance.finance.logistics_partner_payouts`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| is_deleted | boolean |  |  |  |  | False |
| partner_id | integer |  | Y |  |  |  |
| amount | numeric |  |  |  |  |  |
| currency | string |  |  |  | Y | USD |
| period_start | datetime |  |  |  | Y |  |
| period_end | datetime |  |  |  | Y |  |
| status | string |  |  |  | Y | pending |
| reference_id | string |  |  |  | Y |  |
| processed_at | datetime |  |  |  | Y |  |
| country_code | string |  | Y |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| method | string |  |  |  | Y |  |
| notes | text |  |  |  | Y |  |

**Indexes:**

- `ix_finance_logistics_partner_payouts_country_code` (country_code)
- `ix_finance_logistics_partner_payouts_is_deleted` (is_deleted)
- `ix_finance_logistics_partner_payouts_id` (id)

**Foreign Keys:**

- `partner_id` → `logistics.logistics_partners.id`
- `country_code` → `country.country_configs.code`

---

### `finance.finance.payment_gateway_connections`

*Table: `finance.finance.payment_gateway_connections`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| is_deleted | boolean |  |  |  |  | False |
| provider_code | string |  |  |  |  |  |
| gateway_name | string |  |  |  |  |  |
| country_code | string |  |  |  |  |  |
| environment | string |  |  |  | Y | test |
| is_active | boolean |  |  |  | Y | True |
| credentials | json |  |  |  | Y |  |
| fee_config | json |  |  |  | Y |  |
| supported_methods | json |  |  |  | Y |  |
| last_sync_at | datetime |  |  |  | Y |  |
| provider_kind | string |  |  |  |  | custom |
| display_name | string |  |  |  |  |  |
| is_enabled | boolean |  |  |  | Y | True |
| supports_customer_checkout | boolean |  |  |  | Y | False |
| supports_payouts | boolean |  |  |  | Y | False |
| payment_mode | string |  |  |  |  | test |
| public_key | string |  |  |  | Y |  |
| secret_key | string |  |  |  | Y |  |
| webhook_secret | string |  |  |  | Y |  |
| merchant_id | string |  |  |  | Y |  |
| api_base_url | string |  |  |  | Y |  |
| webhook_url | string |  |  |  | Y |  |
| test_url | string |  |  |  | Y |  |
| settlement_cycle | string |  |  |  | Y |  |
| supported_currencies_json | text |  |  |  | Y |  |
| extra_config_json | text |  |  |  | Y |  |
| notes | text |  |  |  | Y |  |
| fee_percent | numeric |  |  |  |  | 0 |
| fixed_fee_amount | numeric |  |  |  |  | 0 |
| payout_fee_percent | numeric |  |  |  |  | 0 |
| payout_fixed_fee_amount | numeric |  |  |  |  | 0 |
| pass_fee_to_customer | boolean |  |  |  | Y | False |
| test_status | string |  |  |  |  | untested |
| test_message | string |  |  |  | Y |  |
| last_tested_at | datetime |  |  |  | Y |  |
| updated_by_id | integer |  | Y |  | Y |  |
| adapter_supported | boolean |  |  |  | Y | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_finance_payment_gateway_connections_id` (id)
- `ix_finance_payment_gateway_connections_is_deleted` (is_deleted)

**Foreign Keys:**

- `updated_by_id` → `accounts.users.id`

---

### `finance.finance.payment_reconciliation_runs`

*Table: `finance.finance.payment_reconciliation_runs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| is_deleted | boolean |  |  |  |  | False |
| run_date | datetime |  |  |  |  |  |
| total_amount | numeric |  |  |  | Y |  |
| reconciled_count | integer |  |  |  | Y | 0 |
| unmatched_count | integer |  |  |  | Y | 0 |
| processed_count | integer |  |  |  | Y | 0 |
| stale_pending_orders | integer |  |  |  | Y | 0 |
| recent_webhook_count | integer |  |  |  | Y | 0 |
| result_json | text |  |  |  | Y |  |
| started_at | datetime |  |  |  | Y |  |
| completed_at | datetime |  |  |  | Y |  |
| status | string |  |  |  | Y | pending |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_finance_payment_reconciliation_runs_id` (id)
- `ix_finance_payment_reconciliation_runs_country_code` (country_code)
- `ix_finance_payment_reconciliation_runs_is_deleted` (is_deleted)

---

### `finance.finance.payments`

*Table: `finance.finance.payments`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| is_deleted | boolean |  |  |  |  | False |
| order_id | integer |  | Y |  |  |  |
| amount | numeric |  |  |  |  |  |
| payment_method | string |  |  |  |  |  |
| provider | string |  |  |  | Y |  |
| status | string |  |  |  | Y | pending |
| intent_id | string |  |  |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  | Y |  | Y |  |
| layout_json | text |  |  |  | Y |  |

**Indexes:**

- `ix_payments_status_created` (status, created_at)
- `ix_finance_payments_country_code` (country_code)
- `ix_finance_payments_id` (id)
- `ix_payments_provider_status` (provider, status)
- `ix_finance_payments_is_deleted` (is_deleted)
- `ix_payments_order_id` (order_id)

**Foreign Keys:**

- `order_id` → `orders.orders.id`
- `country_code` → `country.country_configs.code`

---

### `finance.finance.payout_batch_items`

*Table: `finance.finance.payout_batch_items`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0724790> |
| version | integer |  |  |  |  | 1 |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| batch_id | integer |  | Y |  |  |  |
| entity_type | string |  |  |  |  |  |
| entity_id | integer |  |  |  |  |  |
| amount | numeric |  |  |  |  |  |
| currency | string |  |  |  | Y | USD |
| reference | string |  |  |  | Y |  |
| status | string |  |  |  | Y | pending |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_finance_payout_batch_items_created_by_id` (created_by_id)
- `ix_finance_payout_batch_items_batch_id` (batch_id)
- `ix_finance_payout_batch_items_country_code` (country_code)
- `ix_finance_payout_batch_items_is_deleted` (is_deleted)
- `ix_finance_payout_batch_items_updated_by` (updated_by)
- `ix_finance_payout_batch_items_id` (id)

**Foreign Keys:**

- `batch_id` → `finance.payout_batches.id`

---

### `finance.finance.payout_batches`

*Table: `finance.finance.payout_batches`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B07240D0> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| batch_number | string |  |  | Y |  |  |
| country_code | string |  |  |  |  |  |
| total_amount | numeric |  |  |  | Y | 0 |
| item_count | integer |  |  |  | Y | 0 |
| status | string |  |  |  | Y | draft |
| created_by_id | integer |  | Y |  |  |  |
| approved_by_id | integer |  | Y |  | Y |  |
| dispatched_at | datetime |  |  |  | Y |  |
| settled_at | datetime |  |  |  | Y |  |
| notes | text |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B07241F0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0724160> |

**Indexes:**

- `ix_finance_payout_batches_created_by_id` (created_by_id)
- `ix_payout_batches_country_created` (country_code, created_at)
- `ix_finance_payout_batches_country_code` (country_code)
- `ix_finance_payout_batches_updated_by` (updated_by)
- `ix_finance_payout_batches_approved_by_id` (approved_by_id)
- `ix_finance_payout_batches_id` (id)
- `ix_finance_payout_batches_is_deleted` (is_deleted)

**Foreign Keys:**

- `created_by_id` → `accounts.users.id`
- `approved_by_id` → `accounts.users.id`

---

### `finance.finance.payout_rule_categories`

*Table: `finance.finance.payout_rule_categories`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0237F40> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| country_code | string |  | Y |  |  |  |
| category_slug | string |  |  |  |  |  |
| payout_rate | numeric |  |  |  |  |  |
| min_amount | numeric |  |  |  | Y |  |
| max_amount | numeric |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B03100D0> |

**Indexes:**

- `ix_finance_payout_rule_categories_is_deleted` (is_deleted)
- `ix_finance_payout_rule_categories_id` (id)
- `ix_payout_rule_categories_country_created` (country_code, created_at)
- `ix_finance_payout_rule_categories_created_by` (created_by)
- `ix_finance_payout_rule_categories_country_code` (country_code)
- `ix_finance_payout_rule_categories_updated_by` (updated_by)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `finance.finance.payout_rule_products`

*Table: `finance.finance.payout_rule_products`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0310550> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| country_code | string |  | Y |  |  |  |
| product_id | integer |  |  |  |  |  |
| payout_rate | numeric |  |  |  |  |  |
| min_amount | numeric |  |  |  | Y |  |
| max_amount | numeric |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0310670> |

**Indexes:**

- `ix_finance_payout_rule_products_created_by` (created_by)
- `ix_finance_payout_rule_products_country_code` (country_code)
- `ix_finance_payout_rule_products_updated_by` (updated_by)
- `ix_payout_rule_products_country_created` (country_code, created_at)
- `ix_finance_payout_rule_products_is_deleted` (is_deleted)
- `ix_finance_payout_rule_products_id` (id)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `finance.finance.payout_rules`

*Table: `finance.finance.payout_rules`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0237400> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| country_code | string |  | Y |  |  |  |
| min_amount | numeric |  |  |  | Y |  |
| max_amount | numeric |  |  |  | Y |  |
| fixed_fee | numeric |  |  |  | Y | 0 |
| percent_fee | numeric |  |  |  | Y | 0 |
| is_active | boolean |  |  |  | Y | True |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0237520> |

**Indexes:**

- `ix_finance_payout_rules_updated_by` (updated_by)
- `ix_finance_payout_rules_is_deleted` (is_deleted)
- `ix_finance_payout_rules_id` (id)
- `ix_payout_rules_country_created` (country_code, created_at)
- `ix_finance_payout_rules_created_by` (created_by)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `finance.finance.payouts`

*Table: `finance.finance.payouts`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| is_deleted | boolean |  |  |  |  | False |
| batch_number | string |  |  |  | Y |  |
| order_id | integer |  | Y |  | Y |  |
| supplier_id | integer |  | Y |  |  |  |
| amount | numeric |  |  |  |  |  |
| currency | string |  |  |  | Y | USD |
| method | string |  |  |  |  |  |
| status | string |  |  |  | Y | pending |
| reference_id | string |  |  |  | Y |  |
| reference | string |  |  |  | Y |  |
| provider | string |  |  |  | Y |  |
| provider_recipient_id | string |  |  |  | Y |  |
| provider_transfer_id | string |  |  |  | Y |  |
| provider_status | string |  |  |  | Y |  |
| notes | text |  |  |  | Y |  |
| processed_at | datetime |  |  |  | Y |  |
| country_code | string |  | Y |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_finance_payouts_is_deleted` (is_deleted)
- `ix_finance_payouts_country_code` (country_code)
- `ix_finance_payouts_id` (id)

**Foreign Keys:**

- `order_id` → `orders.orders.id`
- `supplier_id` → `accounts.users.id`
- `country_code` → `country.country_configs.code`

---

### `finance.finance.pending_journal_entries`

*Table: `finance.finance.pending_journal_entries`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B061BAC0> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| lines_json | text |  |  |  |  |  |
| description | text |  |  |  | Y |  |
| source | string |  |  |  | Y |  |
| country_code | string |  |  |  | Y |  |
| entry_date | datetime |  |  |  |  |  |
| amount_threshold_triggered | boolean |  |  |  | Y | False |
| status | string |  |  |  | Y | pending_approval |
| created_by_id | integer |  | Y |  |  |  |
| approved_by_id | integer |  | Y |  | Y |  |
| rejected_by_id | integer |  | Y |  | Y |  |
| rejection_reason | text |  |  |  | Y |  |
| approved_at | datetime |  |  |  | Y |  |
| journal_entry_id | integer |  | Y |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B061BB50> |

**Indexes:**

- `ix_finance_pending_journal_entries_approved_by_id` (approved_by_id)
- `ix_pending_je_country` (country_code)
- `ix_pending_journal_entries_country_created` (country_code, created_at)
- `ix_finance_pending_journal_entries_journal_entry_id` (journal_entry_id)
- `ix_finance_pending_journal_entries_rejected_by_id` (rejected_by_id)
- `ix_finance_pending_journal_entries_id` (id)
- `ix_finance_pending_journal_entries_updated_by` (updated_by)
- `ix_pending_je_status` (status)
- `ix_finance_pending_journal_entries_is_deleted` (is_deleted)
- `ix_finance_pending_journal_entries_created_by_id` (created_by_id)
- `ix_pending_je_maker` (created_by_id)

**Foreign Keys:**

- `created_by_id` → `accounts.users.id`
- `approved_by_id` → `accounts.users.id`
- `rejected_by_id` → `accounts.users.id`
- `journal_entry_id` → `finance.journal_entries.id`

---

### `finance.finance.product_commission_overrides`

*Table: `finance.finance.product_commission_overrides`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | string |  |  | Y |  |  |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| product_id | integer |  | Y |  |  |  |
| supplier_id | integer |  | Y |  |  |  |
| rate_percent | numeric |  |  |  |  |  |
| set_by_admin_id | integer |  | Y |  | Y |  |
| is_active | boolean |  |  |  |  | True |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0409990> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0409900> |

**Indexes:**

- `ix_finance_product_commission_overrides_product_id` (product_id)
- `ix_finance_product_commission_overrides_set_by_admin_id` (set_by_admin_id)
- `ix_finance_product_commission_overrides_created_by` (created_by)
- `ix_finance_product_commission_overrides_supplier_id` (supplier_id)
- `ix_finance_product_commission_overrides_updated_by` (updated_by)
- `ix_finance_product_commission_overrides_country_code` (country_code)
- `ix_finance_product_commission_overrides_id` (id)
- `ix_finance_product_commission_overrides_is_deleted` (is_deleted)
- `ix_product_commission_overrides_country` (country_code)

**Foreign Keys:**

- `product_id` → `catalog.products.id`
- `supplier_id` → `accounts.users.id`
- `set_by_admin_id` → `accounts.users.id`

---

### `finance.finance.recurring_templates`

*Table: `finance.finance.recurring_templates`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0823490> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| name | string |  |  |  |  |  |
| frequency | string |  |  |  | Y | monthly |
| next_run_date | datetime |  |  |  | Y |  |
| description | text |  |  |  | Y |  |
| lines | json |  |  |  |  |  |
| currency | string |  |  |  | Y | OMR |
| country_code | string |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| created_by_id | integer |  | Y |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B08235B0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0823520> |

**Indexes:**

- `ix_finance_recurring_templates_is_deleted` (is_deleted)
- `ix_finance_recurring_templates_id` (id)
- `ix_recurring_templates_country_created` (country_code, created_at)
- `ix_finance_recurring_templates_country_code` (country_code)
- `ix_recurring_templates_lines_gin` (lines)
- `ix_finance_recurring_templates_created_by_id` (created_by_id)
- `ix_recurring_country` (country_code)
- `ix_finance_recurring_templates_updated_by` (updated_by)

**Foreign Keys:**

- `created_by_id` → `accounts.users.id`

---

### `finance.finance.refund_ledgers`

*Table: `finance.finance.refund_ledgers`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0618040> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| order_id | integer |  | Y |  |  |  |
| return_request_id | integer |  | Y |  | Y |  |
| ledger_id | integer |  |  |  | Y |  |
| bank_transaction_id | integer |  |  |  | Y |  |
| reason | text |  |  |  | Y |  |
| refund_reason | text |  |  |  | Y |  |
| refund_method | string |  |  |  | Y |  |
| customer_refund_amount | numeric |  |  |  | Y |  |
| supplier_reversal | numeric |  |  |  | Y |  |
| logistics_reversal | numeric |  |  |  | Y |  |
| delivery_fee_reversal | numeric |  |  |  | Y |  |
| commission_reversal | numeric |  |  |  | Y |  |
| vat_adjustment | numeric |  |  |  | Y |  |
| vat_reversal | numeric |  |  |  | Y |  |
| performed_by_id | integer |  | Y |  | Y |  |
| processed_at | datetime |  |  |  | Y |  |
| currency | string |  |  |  | Y | OMR |
| status | string |  |  |  | Y | pending |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0618160> |
| country_code | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  | Y | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  | Y |  | Y |  |

**Indexes:**

- `ix_finance_refund_ledgers_order_id` (order_id)
- `ix_finance_refund_ledgers_country_code` (country_code)
- `ix_finance_refund_ledgers_updated_by` (updated_by)
- `ix_finance_refund_ledgers_performed_by_id` (performed_by_id)
- `ix_refund_ledger_country_created` (country_code, created_at)
- `ix_finance_refund_ledgers_return_request_id` (return_request_id)
- `ix_finance_refund_ledgers_is_deleted` (is_deleted)
- `ix_finance_refund_ledgers_id` (id)
- `ix_finance_refund_ledgers_deleted_by_id` (deleted_by_id)
- `ix_finance_refund_ledgers_created_by_id` (created_by_id)

**Foreign Keys:**

- `order_id` → `orders.orders.id`
- `return_request_id` → `orders.return_requests.id`
- `performed_by_id` → `accounts.users.id`
- `deleted_by_id` → `accounts.users.id`

---

### `finance.finance.scanned_expenses`

*Table: `finance.finance.scanned_expenses`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0726B00> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| employee_id | integer |  | Y |  | Y |  |
| vendor_name | string |  |  |  | Y |  |
| invoice_number | string |  |  |  | Y |  |
| expense_date | datetime |  |  |  | Y |  |
| amount | numeric |  |  |  |  |  |
| currency | string |  |  |  | Y | OMR |
| tax_amount | numeric |  |  |  | Y | 0 |
| category | string |  |  |  | Y |  |
| description | text |  |  |  | Y |  |
| expense_account_code | string |  |  |  | Y |  |
| image_url | string |  |  |  | Y |  |
| ocr_raw_text | text |  |  |  | Y |  |
| ocr_confidence | numeric |  |  |  | Y |  |
| status | string |  |  |  | Y | scanned |
| posted_journal_entry_id | integer |  | Y |  | Y |  |
| reviewed_by_id | integer |  | Y |  | Y |  |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0726B90> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0726C20> |

**Indexes:**

- `ix_finance_scanned_expenses_created_by_id` (created_by_id)
- `ix_finance_scanned_expenses_reviewed_by_id` (reviewed_by_id)
- `ix_finance_scanned_expenses_employee_id` (employee_id)
- `ix_scanned_expenses_country_created` (country_code, created_at)
- `ix_finance_scanned_expenses_updated_by` (updated_by)
- `ix_se_status` (status)
- `ix_finance_scanned_expenses_id` (id)
- `ix_finance_scanned_expenses_is_deleted` (is_deleted)
- `ix_se_country` (country_code)
- `ix_finance_scanned_expenses_posted_journal_entry_id` (posted_journal_entry_id)
- `ix_finance_scanned_expenses_country_code` (country_code)

**Foreign Keys:**

- `employee_id` → `hr.employees.id`
- `posted_journal_entry_id` → `finance.journal_entries.id`
- `reviewed_by_id` → `accounts.users.id`

---

### `finance.finance.supplier_settlements`

*Table: `finance.finance.supplier_settlements`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B040BD90> |
| version | integer |  |  |  |  | 1 |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| supplier_id | integer |  | Y |  |  |  |
| order_id | integer |  | Y |  | Y |  |
| ledger_id | integer |  | Y |  | Y |  |
| payout_id | integer |  | Y |  | Y |  |
| shipment_id | integer |  | Y |  | Y |  |
| gross_amount | numeric |  |  |  |  |  |
| commission_amount | numeric |  |  |  | Y |  |
| commission_deducted | numeric |  |  |  | Y |  |
| commission_rate | numeric |  |  |  | Y |  |
| vat_on_commission | numeric |  |  |  | Y |  |
| net_amount | numeric |  |  |  |  |  |
| status | string |  |  |  | Y | pending |
| settled_at | datetime |  |  |  | Y |  |
| eligible_at | datetime |  |  |  | Y |  |
| bank_transaction_id | integer |  |  |  | Y |  |
| currency | string |  |  |  | Y | USD |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B040BEB0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B040BE20> |
| country_code | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  | Y | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  | Y |  | Y |  |

**Indexes:**

- `ix_finance_supplier_settlements_supplier_id` (supplier_id)
- `ix_finance_supplier_settlements_ledger_id` (ledger_id)
- `ix_finance_supplier_settlements_country_code` (country_code)
- `ix_finance_supplier_settlements_updated_by` (updated_by)
- `ix_supplier_settlements_country_created` (country_code, created_at)
- `ix_finance_supplier_settlements_shipment_id` (shipment_id)
- `ix_finance_supplier_settlements_is_deleted` (is_deleted)
- `ix_finance_supplier_settlements_order_id` (order_id)
- `ix_finance_supplier_settlements_payout_id` (payout_id)
- `ix_finance_supplier_settlements_deleted_by_id` (deleted_by_id)
- `ix_finance_supplier_settlements_id` (id)
- `ix_finance_supplier_settlements_created_by_id` (created_by_id)

**Foreign Keys:**

- `supplier_id` → `accounts.users.id`
- `order_id` → `orders.orders.id`
- `ledger_id` → `finance.transaction_ledgers.id`
- `payout_id` → `finance.payouts.id`
- `shipment_id` → `logistics.shipments.id`
- `deleted_by_id` → `accounts.users.id`

---

### `finance.finance.tax_rules`

*Table: `finance.finance.tax_rules`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B02379A0> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| country_code | string |  | Y |  |  |  |
| tax_name | string |  |  |  |  |  |
| tax_rate | numeric |  |  |  |  |  |
| is_active | boolean |  |  |  | Y | True |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0237AC0> |

**Indexes:**

- `ix_finance_tax_rules_country_code` (country_code)
- `ix_tax_rules_country_created` (country_code, created_at)
- `ix_finance_tax_rules_created_by` (created_by)
- `ix_finance_tax_rules_updated_by` (updated_by)
- `ix_finance_tax_rules_is_deleted` (is_deleted)
- `ix_finance_tax_rules_id` (id)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `finance.finance.transaction_ledgers`

*Table: `finance.finance.transaction_ledgers`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B040B6D0> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  | Y |  |
| supplier_id | integer |  | Y |  | Y |  |
| logistics_partner_id | integer |  | Y |  | Y |  |
| order_id | integer |  | Y |  | Y |  |
| order_item_id | integer |  | Y |  | Y |  |
| shipment_id | integer |  | Y |  | Y |  |
| payment_method | string |  |  |  | Y |  |
| product_subtotal | numeric |  |  |  | Y |  |
| discount_amount | numeric |  |  |  | Y |  |
| delivery_pickup_charge | numeric |  |  |  | Y |  |
| delivery_dropoff_charge | numeric |  |  |  | Y |  |
| delivery_total | numeric |  |  |  | Y |  |
| vat_amount | numeric |  |  |  | Y |  |
| zozi_commission_rate | numeric |  |  |  | Y |  |
| zozi_commission | numeric |  |  |  | Y |  |
| net_supplier_amount | numeric |  |  |  | Y |  |
| net_logistics_amount | numeric |  |  |  | Y |  |
| net_zozi_amount | numeric |  |  |  | Y |  |
| cod_collected_amount | numeric |  |  |  | Y |  |
| cod_remittance_due | numeric |  |  |  | Y |  |
| settlement_status | string |  |  |  | Y |  |
| currency | string |  |  |  | Y | USD |
| transaction_type | string |  |  |  | Y |  |
| reference_id | string |  |  |  | Y |  |
| balance_after | numeric |  |  |  | Y |  |
| notes | text |  |  |  | Y |  |
| amount | numeric |  |  |  | Y |  |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B040B7F0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B040B760> |

**Indexes:**

- `ix_finance_transaction_ledgers_order_item_id` (order_item_id)
- `ix_finance_transaction_ledgers_country_code` (country_code)
- `ix_finance_transaction_ledgers_order_id` (order_id)
- `ix_finance_transaction_ledgers_id` (id)
- `ix_finance_transaction_ledgers_is_deleted` (is_deleted)
- `ix_transaction_ledger_country` (country_code)
- `ix_finance_transaction_ledgers_supplier_id` (supplier_id)
- `ix_transaction_ledgers_country_created` (country_code, created_at)
- `ix_finance_transaction_ledgers_shipment_id` (shipment_id)
- `ix_finance_transaction_ledgers_created_by_id` (created_by_id)
- `ix_finance_transaction_ledgers_user_id` (user_id)
- `ix_finance_transaction_ledgers_logistics_partner_id` (logistics_partner_id)
- `ix_finance_transaction_ledgers_updated_by` (updated_by)

**Foreign Keys:**

- `user_id` → `accounts.users.id`
- `supplier_id` → `accounts.users.id`
- `logistics_partner_id` → `logistics.logistics_partners.id`
- `order_id` → `orders.orders.id`
- `order_item_id` → `orders.order_items.id`
- `shipment_id` → `logistics.shipments.id`

---

### `finance.finance.treasury_accounts`

*Table: `finance.finance.treasury_accounts`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0619D80> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| slug | string |  |  | Y |  |  |
| name | string |  |  |  |  |  |
| account_type | string |  |  |  |  |  |
| currency | string |  |  |  | Y | USD |
| gl_account_code | string |  |  |  |  |  |
| description | text |  |  |  | Y |  |
| employee_id | integer |  | Y |  | Y |  |
| balance | numeric |  |  |  | Y | 0 |
| is_active | boolean |  |  |  | Y | True |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0619EA0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0619E10> |

**Indexes:**

- `ix_finance_treasury_accounts_employee_id` (employee_id)
- `ix_treasury_accounts_country_created` (country_code, created_at)
- `ix_finance_treasury_accounts_created_by_id` (created_by_id)
- `ix_finance_treasury_accounts_updated_by` (updated_by)
- `ix_finance_treasury_accounts_is_deleted` (is_deleted)
- `ix_finance_treasury_accounts_id` (id)
- `ix_finance_treasury_accounts_country_code` (country_code)

**Foreign Keys:**

- `employee_id` → `hr.employees.id`

---

### `finance.finance.treasury_transactions`

*Table: `finance.finance.treasury_transactions`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B061A440> |
| version | integer |  |  |  |  | 1 |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| from_account_id | integer |  | Y |  | Y |  |
| to_account_id | integer |  | Y |  | Y |  |
| account_id | integer |  | Y |  | Y |  |
| transaction_type | string |  |  |  |  |  |
| amount | numeric |  |  |  |  |  |
| currency | string |  |  |  | Y | USD |
| reference | string |  |  |  | Y |  |
| description | text |  |  |  | Y |  |
| posted_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B061A4D0> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_finance_treasury_transactions_created_by_id` (created_by_id)
- `ix_finance_treasury_transactions_from_account_id` (from_account_id)
- `ix_finance_treasury_transactions_account_id` (account_id)
- `ix_finance_treasury_transactions_is_deleted` (is_deleted)
- `ix_finance_treasury_transactions_updated_by` (updated_by)
- `ix_finance_treasury_transactions_country_code` (country_code)
- `ix_finance_treasury_transactions_to_account_id` (to_account_id)
- `ix_finance_treasury_transactions_id` (id)

**Foreign Keys:**

- `from_account_id` → `finance.treasury_accounts.id`
- `to_account_id` → `finance.treasury_accounts.id`
- `account_id` → `finance.treasury_accounts.id`

---

### `finance.finance.vat_remittances`

*Table: `finance.finance.vat_remittances`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0618B80> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| period_start | datetime |  |  |  |  |  |
| period_end | datetime |  |  |  |  |  |
| vat_collected_amount | numeric |  |  |  | Y |  |
| vat_adjustment_amount | numeric |  |  |  | Y |  |
| amount_due | numeric |  |  |  | Y |  |
| amount | numeric |  |  |  |  |  |
| amount_remitted | numeric |  |  |  | Y |  |
| currency | string |  |  |  | Y | OMR |
| bank_transaction_id | integer |  |  |  | Y |  |
| remitted_by_id | integer |  | Y |  | Y |  |
| remitted_at | datetime |  |  |  | Y |  |
| notes | text |  |  |  | Y |  |
| status | string |  |  |  | Y | pending |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0618C10> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_finance_vat_remittances_country_code` (country_code)
- `ix_finance_vat_remittances_remitted_by_id` (remitted_by_id)
- `ix_finance_vat_remittances_created_by_id` (created_by_id)
- `ix_finance_vat_remittances_updated_by` (updated_by)
- `ix_vat_remittances_country_created` (country_code, created_at)
- `ix_finance_vat_remittances_is_deleted` (is_deleted)
- `ix_finance_vat_remittances_id` (id)

**Foreign Keys:**

- `remitted_by_id` → `accounts.users.id`

---

### `finance.finance.vendors`

*Table: `finance.finance.vendors`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0727F40> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| name | string |  |  |  |  |  |
| tax_id | string |  |  |  | Y |  |
| contact_email | string |  |  |  | Y |  |
| currency | string |  |  |  | Y | OMR |
| payment_terms_days | integer |  |  |  | Y | 30 |
| country_code | string |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0820040> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B08200D0> |

**Indexes:**

- `ix_finance_vendors_is_deleted` (is_deleted)
- `ix_finance_vendors_id` (id)
- `ix_vendors_country` (country_code)
- `ix_vendors_country_created` (country_code, created_at)
- `ix_finance_vendors_created_by_id` (created_by_id)
- `ix_finance_vendors_updated_by` (updated_by)
- `ix_finance_vendors_country_code` (country_code)

---

## GOVERNANCE

*Schema: `governance` · 34 tables*

### `governance.governance.admin_activity_logs`

*Table: `governance.governance.admin_activity_logs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| admin_id | integer |  | Y |  |  |  |
| action | string |  |  |  |  |  |
| details | json |  |  |  | Y |  |
| ip_address | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_governance_admin_activity_logs_country_code` (country_code)
- `ix_governance_admin_activity_logs_id` (id)
- `ix_governance_admin_activity_logs_is_deleted` (is_deleted)

**Foreign Keys:**

- `admin_id` → `accounts.users.id`

---

### `governance.governance.admin_analytics_snapshots`

*Table: `governance.governance.admin_analytics_snapshots`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| snapshot_key | string |  |  |  |  |  |
| snapshot_group | string |  |  |  |  |  |
| period | string |  |  |  | Y |  |
| payload_json | text |  |  |  |  |  |
| computed_at | datetime |  |  |  |  | <function utcnow at 0x000001C7B14679A0> |
| expires_at | datetime |  |  |  |  |  |
| is_deleted | boolean |  |  |  |  | False |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_governance_admin_analytics_snapshots_is_deleted` (is_deleted)
- `ix_governance_admin_analytics_snapshots_computed_at` (computed_at)
- `ix_governance_admin_analytics_snapshots_country_code` (country_code)
- `ix_governance_admin_analytics_snapshots_snapshot_group` (snapshot_group)
- `ix_admin_analytics_snapshots_expires` (expires_at)
- `ix_admin_analytics_snapshots_group_computed` (snapshot_group, computed_at)
- `ix_governance_admin_analytics_snapshots_snapshot_key` (snapshot_key)
- `ix_governance_admin_analytics_snapshots_expires_at` (expires_at)
- `ix_governance_admin_analytics_snapshots_id` (id)

---

### `governance.governance.admin_change_audit_logs`

*Table: `governance.governance.admin_change_audit_logs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| admin_id | integer |  | Y |  |  |  |
| action | string |  |  |  |  |  |
| entity | string |  |  |  |  |  |
| entity_key | string |  |  |  | Y |  |
| before_json | text |  |  |  | Y |  |
| after_json | text |  |  |  | Y |  |
| notes | text |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_governance_admin_change_audit_logs_id` (id)
- `ix_governance_admin_change_audit_logs_country_code` (country_code)
- `ix_governance_admin_change_audit_logs_is_deleted` (is_deleted)

**Foreign Keys:**

- `admin_id` → `accounts.users.id`

---

### `governance.governance.api_keys`

*Table: `governance.governance.api_keys`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| name | string |  |  |  |  |  |
| key_hash | string |  |  |  |  |  |
| permissions | json |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| expires_at | datetime |  |  |  | Y |  |
| created_by_id | integer |  | Y |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_governance_api_keys_is_deleted` (is_deleted)
- `ix_governance_api_keys_id` (id)
- `ix_governance_api_keys_country_code` (country_code)

**Foreign Keys:**

- `created_by_id` → `accounts.users.id`

---

### `governance.governance.badge_billing_records`

*Table: `governance.governance.badge_billing_records`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  | Y |  |
| supplier_id | integer |  | Y |  | Y |  |
| billing_reference | string |  |  | Y | Y |  |
| badge_level | string |  |  |  | Y |  |
| charge_type | string |  |  |  | Y |  |
| charge_source | string |  |  |  | Y |  |
| amount | numeric |  |  |  |  |  |
| currency | string |  |  |  | Y | USD |
| status | string |  |  |  | Y | pending |
| reference_id | string |  |  |  | Y |  |
| period_start | datetime |  |  |  | Y |  |
| period_end | datetime |  |  |  | Y |  |
| due_at | datetime |  |  |  | Y |  |
| billed_at | datetime |  |  |  | Y |  |
| paid_at | datetime |  |  |  | Y |  |
| payment_method | string |  |  |  | Y |  |
| notes | text |  |  |  | Y |  |
| created_by_id | integer |  |  |  | Y |  |
| bank_transaction_id | integer |  | Y |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_governance_badge_billing_records_country_code` (country_code)
- `ix_governance_badge_billing_records_id` (id)
- `ix_governance_badge_billing_records_is_deleted` (is_deleted)

**Foreign Keys:**

- `user_id` → `accounts.users.id`
- `supplier_id` → `accounts.users.id`
- `bank_transaction_id` → `finance.bank_transactions.id`

---

### `governance.governance.badge_tiers`

*Table: `governance.governance.badge_tiers`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| name | string |  |  |  |  |  |
| min_points | integer |  |  |  |  |  |
| benefits | json |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_governance_badge_tiers_is_deleted` (is_deleted)
- `ix_governance_badge_tiers_country_code` (country_code)
- `ix_governance_badge_tiers_id` (id)

---

### `governance.governance.badge_transactions`

*Table: `governance.governance.badge_transactions`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| amount | numeric |  |  |  |  |  |
| transaction_type | string |  |  |  |  |  |
| reference_id | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_governance_badge_transactions_is_deleted` (is_deleted)
- `ix_governance_badge_transactions_id` (id)
- `ix_governance_badge_transactions_country_code` (country_code)

**Foreign Keys:**

- `user_id` → `accounts.users.id`

---

### `governance.governance.chatbot_query_events`

*Table: `governance.governance.chatbot_query_events`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  | Y |  |
| session_id | string |  |  |  |  |  |
| event_type | string |  |  |  |  | query |
| message | text |  |  |  | Y |  |
| normalized_query | string |  |  |  | Y |  |
| intent | string |  |  |  | Y |  |
| filters_json | text |  |  |  | Y |  |
| result_count | integer |  |  |  |  | 0 |
| product_ids_json | text |  |  |  | Y |  |
| clicked_product_id | integer |  | Y |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_chatbot_events_normalized_query` (normalized_query)
- `ix_chatbot_events_session_id` (session_id)
- `ix_governance_chatbot_query_events_id` (id)
- `ix_governance_chatbot_query_events_country_code` (country_code)
- `ix_chatbot_events_created_at` (created_at)
- `ix_chatbot_events_intent_created` (intent, created_at)
- `ix_chatbot_events_user_created` (user_id, created_at)
- `ix_chatbot_events_clicked_product_id` (clicked_product_id)
- `ix_chatbot_events_session_created` (session_id, created_at)
- `ix_governance_chatbot_query_events_is_deleted` (is_deleted)
- `ix_chatbot_events_type_created` (event_type, created_at)

**Foreign Keys:**

- `user_id` → `accounts.users.id`
- `clicked_product_id` → `catalog.products.id`

---

### `governance.governance.commission_badge_tiers`

*Table: `governance.governance.commission_badge_tiers`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| name | string |  |  |  |  |  |
| badge_level | string |  |  | Y |  |  |
| commission_rate | numeric |  |  |  |  |  |
| setup_fee | numeric |  |  |  | Y | 0.00 |
| recurring_fee | numeric |  |  |  | Y | 0.00 |
| recurring_interval | string |  |  |  | Y |  |
| benefits_json | text |  |  |  | Y |  |
| min_fulfilled_orders | integer |  |  |  | Y |  |
| min_monthly_revenue | numeric |  |  |  | Y |  |
| sort_order | integer |  |  |  | Y | 0 |
| is_active | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  |  | False |
| updated_by_id | integer |  | Y |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_governance_commission_badge_tiers_id` (id)
- `ix_governance_commission_badge_tiers_country_code` (country_code)
- `ix_governance_commission_badge_tiers_is_deleted` (is_deleted)

**Foreign Keys:**

- `updated_by_id` → `accounts.users.id`

---

### `governance.governance.commission_global_configs`

*Table: `governance.governance.commission_global_configs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| default_rate | numeric |  |  |  | Y | 0.1500 |
| low_value_threshold | numeric |  |  |  | Y | 5.00 |
| fixed_cap_amount | numeric |  |  |  | Y | 0.50 |
| fixed_cap_enabled | boolean |  |  |  | Y | True |
| margin_protection_enabled | boolean |  |  |  | Y | False |
| margin_threshold | numeric |  |  |  | Y | 0.10 |
| is_deleted | boolean |  |  |  |  | False |
| updated_by_id | integer |  | Y |  | Y |  |
| updated_at | datetime |  |  |  | Y | now() |
| created_at | datetime |  |  |  |  | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_governance_commission_global_configs_is_deleted` (is_deleted)
- `ix_governance_commission_global_configs_country_code` (country_code)
- `ix_governance_commission_global_configs_id` (id)

**Foreign Keys:**

- `updated_by_id` → `accounts.users.id`

---

### `governance.governance.email_provider_configs`

*Table: `governance.governance.email_provider_configs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| provider | string |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| updated_by_id | integer |  | Y |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| email_from_default | string |  |  |  | Y |  |
| email_from_promotional | string |  |  |  | Y |  |
| email_from_transactional | string |  |  |  | Y |  |
| email_from_notification | string |  |  |  | Y |  |
| email_from_alert | string |  |  |  | Y |  |
| email_from_verification | string |  |  |  | Y |  |
| email_from_login_verification | string |  |  |  | Y |  |
| email_from_password_reset | string |  |  |  | Y |  |
| resend_api_key | string |  |  |  | Y |  |
| resend_webhook_secret | string |  |  |  | Y |  |
| smtp_host | string |  |  |  | Y |  |
| smtp_port | integer |  |  |  | Y |  |
| smtp_username | string |  |  |  | Y |  |
| smtp_password | string |  |  |  | Y |  |
| smtp_use_tls | boolean |  |  |  | Y | True |
| smtp_use_ssl | boolean |  |  |  | Y | False |
| smtp_timeout_seconds | integer |  |  |  | Y | 10 |
| is_deleted | boolean |  |  |  |  | False |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_governance_email_provider_configs_id` (id)
- `ix_governance_email_provider_configs_country_code` (country_code)
- `ix_governance_email_provider_configs_is_deleted` (is_deleted)

**Foreign Keys:**

- `updated_by_id` → `accounts.users.id`

---

### `governance.governance.employee_expenses`

*Table: `governance.governance.employee_expenses`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| employee_id | integer |  | Y |  |  |  |
| expense_type | string |  |  |  |  |  |
| amount | numeric |  |  |  |  |  |
| description | text |  |  |  | Y |  |
| status | string |  |  |  | Y | pending |
| approved_by_id | integer |  | Y |  | Y |  |
| approved_at | datetime |  |  |  | Y |  |
| receipt_url | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_governance_employee_expenses_id` (id)
- `ix_governance_employee_expenses_is_deleted` (is_deleted)
- `ix_governance_employee_expenses_country_code` (country_code)
- `ix_governance_employee_expenses_employee_id` (employee_id)

**Foreign Keys:**

- `employee_id` → `hr.employees.id`
- `approved_by_id` → `accounts.users.id`

---

### `governance.governance.finance_bank_accounts`

*Table: `governance.governance.finance_bank_accounts`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| account_name | string |  |  |  | Y |  |
| account_number | string |  |  |  |  |  |
| bank_name | string |  |  |  |  |  |
| account_label | string |  |  |  | Y |  |
| branch_name | string |  |  |  | Y |  |
| iban | string |  |  |  | Y |  |
| swift_code | string |  |  |  | Y |  |
| routing_number | string |  |  |  | Y |  |
| currency | string |  |  |  | Y |  |
| support_email | string |  |  |  | Y |  |
| support_phone | string |  |  |  | Y |  |
| remittance_reference_prefix | string |  |  |  | Y |  |
| instructions | text |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| scope | string |  |  |  | Y | zozi_primary |
| created_by_id | integer |  | Y |  | Y |  |
| updated_by_id | integer |  | Y |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_governance_finance_bank_accounts_is_deleted` (is_deleted)
- `ix_governance_finance_bank_accounts_id` (id)
- `ix_governance_finance_bank_accounts_country_code` (country_code)

**Foreign Keys:**

- `created_by_id` → `accounts.users.id`
- `updated_by_id` → `accounts.users.id`

---

### `governance.governance.legal_contract_templates`

*Table: `governance.governance.legal_contract_templates`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| country_code | string |  | Y |  |  |  |
| template_type | string |  |  |  |  |  |
| version | string |  |  |  | Y | 1.0 |
| content | text |  |  |  |  |  |
| is_active | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_lct_type` (template_type)
- `ix_governance_legal_contract_templates_id` (id)
- `ix_governance_legal_contract_templates_is_deleted` (is_deleted)
- `ix_governance_legal_contract_templates_country_code` (country_code)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `governance.governance.logistics_cod_remittance_receipts`

*Table: `governance.governance.logistics_cod_remittance_receipts`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| partner_id | integer |  | Y |  | Y |  |
| shipment_id | integer |  | Y |  | Y |  |
| settlement_id | integer |  | Y |  | Y |  |
| amount | numeric |  |  |  |  |  |
| bank_reference | string |  |  |  | Y |  |
| receipt_file_url | string |  |  |  | Y |  |
| notes | text |  |  |  | Y |  |
| review_note | text |  |  |  | Y |  |
| reviewed_by_id | integer |  | Y |  | Y |  |
| status | string |  |  |  | Y | pending |
| currency | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_governance_logistics_cod_remittance_receipts_is_deleted` (is_deleted)
- `ix_governance_logistics_cod_remittance_receipts_country_code` (country_code)
- `ix_governance_logistics_cod_remittance_receipts_id` (id)

**Foreign Keys:**

- `partner_id` → `logistics.logistics_partners.id`
- `shipment_id` → `logistics.shipments.id`
- `settlement_id` → `governance.logistics_settlements.id`
- `reviewed_by_id` → `accounts.users.id`

---

### `governance.governance.logistics_partner_documents`

*Table: `governance.governance.logistics_partner_documents`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| partner_id | integer |  | Y |  |  |  |
| doc_type | string |  |  |  |  |  |
| file_url | string |  |  |  |  |  |
| reviewed_by_id | integer |  | Y |  | Y |  |
| is_verified | boolean |  |  |  | Y | False |
| verified_at | datetime |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_governance_logistics_partner_documents_country_code` (country_code)
- `ix_governance_logistics_partner_documents_is_deleted` (is_deleted)
- `ix_governance_logistics_partner_documents_id` (id)

**Foreign Keys:**

- `partner_id` → `logistics.logistics_partners.id`
- `reviewed_by_id` → `accounts.users.id`

---

### `governance.governance.logistics_settlements`

*Table: `governance.governance.logistics_settlements`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| partner_id | integer |  | Y |  |  |  |
| order_id | integer |  | Y |  | Y |  |
| ledger_id | integer |  |  |  | Y |  |
| shipment_id | integer |  | Y |  | Y |  |
| amount | numeric |  |  |  | Y |  |
| pickup_charge | numeric |  |  |  | Y |  |
| dropoff_charge | numeric |  |  |  | Y |  |
| total_delivery_fee | numeric |  |  |  | Y |  |
| cod_collected | numeric |  |  |  | Y |  |
| cod_remitted | numeric |  |  |  | Y |  |
| cod_retained | numeric |  |  |  | Y |  |
| cod_remittance_status | string |  |  |  | Y |  |
| eligible_at | datetime |  |  |  | Y |  |
| status | string |  |  |  | Y | pending |
| currency | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| payout_id | integer |  | Y |  | Y |  |
| bank_transaction_id | integer |  |  |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_governance_logistics_settlements_country_code` (country_code)
- `ix_governance_logistics_settlements_is_deleted` (is_deleted)
- `ix_governance_logistics_settlements_id` (id)

**Foreign Keys:**

- `partner_id` → `logistics.logistics_partners.id`
- `order_id` → `orders.orders.id`
- `shipment_id` → `logistics.shipments.id`
- `payout_id` → `finance.payouts.id`

---

### `governance.governance.normalized_webhook_events`

*Table: `governance.governance.normalized_webhook_events`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| provider_code | string |  |  |  |  |  |
| gateway_event_id | string |  |  |  |  |  |
| event_type | string |  |  |  |  |  |
| status | string |  |  |  |  |  |
| environment | string |  |  |  | Y |  |
| processed_at | datetime |  |  |  | Y |  |
| zozi_order_id | integer |  |  |  | Y |  |
| gateway_transaction_id | string |  |  |  | Y |  |
| gateway_customer_id | string |  |  |  | Y |  |
| gross_amount | numeric |  |  |  | Y |  |
| currency | string |  |  |  | Y |  |
| gateway_fee | numeric |  |  |  | Y |  |
| net_settlement | numeric |  |  |  | Y |  |
| fraud_score | numeric |  |  |  | Y |  |
| three_ds_status | string |  |  |  | Y |  |
| avs_result | string |  |  |  | Y |  |
| raw_payload | text |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_governance_normalized_webhook_events_provider_code` (provider_code)
- `ix_governance_normalized_webhook_events_id` (id)
- `ix_governance_normalized_webhook_events_is_deleted` (is_deleted)
- `ix_governance_normalized_webhook_events_country_code` (country_code)

---

### `governance.governance.payment_provider_configs`

*Table: `governance.governance.payment_provider_configs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| provider_name | string |  |  |  |  |  |
| config | json |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  |  | False |
| updated_by_id | integer |  | Y |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_governance_payment_provider_configs_country_code` (country_code)
- `ix_governance_payment_provider_configs_id` (id)
- `ix_governance_payment_provider_configs_is_deleted` (is_deleted)

**Foreign Keys:**

- `updated_by_id` → `accounts.users.id`

---

### `governance.governance.processed_webhook_events`

*Table: `governance.governance.processed_webhook_events`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| processor | string |  |  |  |  |  |
| event_id | string |  |  |  |  |  |
| payload_hash | string |  |  |  |  |  |
| processed_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B15F3010> |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_governance_processed_webhook_events_is_deleted` (is_deleted)
- `ix_governance_processed_webhook_events_country_code` (country_code)
- `ix_governance_processed_webhook_events_id` (id)

---

### `governance.governance.product_verifications`

*Table: `governance.governance.product_verifications`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| product_id | integer |  | Y |  |  |  |
| status | string |  |  |  | Y | pending |
| verified_by_id | integer |  | Y |  | Y |  |
| shipment_id | integer |  | Y |  | Y |  |
| verification_type | string |  |  |  | Y |  |
| result | string |  |  |  | Y |  |
| expected_specs | text |  |  |  | Y |  |
| actual_specs | text |  |  |  | Y |  |
| discrepancies | text |  |  |  | Y |  |
| scan_code | string |  |  |  | Y |  |
| image_urls | text |  |  |  | Y |  |
| notes | text |  |  |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| order_id | integer |  | Y |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_governance_product_verifications_country_code` (country_code)
- `ix_governance_product_verifications_is_deleted` (is_deleted)
- `ix_governance_product_verifications_id` (id)

**Foreign Keys:**

- `product_id` → `catalog.products.id`
- `verified_by_id` → `accounts.users.id`
- `shipment_id` → `logistics.shipments.id`
- `order_id` → `orders.orders.id`

---

### `governance.governance.promotion_order_tiers`

*Table: `governance.governance.promotion_order_tiers`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| promotion_id | integer |  |  |  | Y |  |
| tier_name | string |  |  |  | Y |  |
| min_order_amount | numeric |  |  |  |  |  |
| max_order_amount | numeric |  |  |  | Y |  |
| discount_type | string |  |  |  |  | fixed |
| discount_amount | numeric |  |  |  | Y |  |
| discount_value | numeric |  |  |  | Y |  |
| stacking_allowed | boolean |  |  |  | Y | False |
| is_active | boolean |  |  |  | Y | True |
| sort_order | integer |  |  |  | Y |  |
| updated_by_id | integer |  | Y |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| country_code | string |  | Y |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_governance_promotion_order_tiers_country_code` (country_code)
- `ix_governance_promotion_order_tiers_is_deleted` (is_deleted)
- `ix_governance_promotion_order_tiers_id` (id)

**Foreign Keys:**

- `updated_by_id` → `accounts.users.id`
- `country_code` → `country.country_configs.code`

---

### `governance.governance.push_notification_tokens`

*Table: `governance.governance.push_notification_tokens`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| token | string |  |  |  |  |  |
| device_type | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_governance_push_notification_tokens_id` (id)
- `ix_governance_push_notification_tokens_is_deleted` (is_deleted)
- `ix_governance_push_notification_tokens_country_code` (country_code)

**Foreign Keys:**

- `user_id` → `accounts.users.id`

---

### `governance.governance.retention_job_runs`

*Table: `governance.governance.retention_job_runs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| job_type | string |  |  |  | Y |  |
| target_table | string |  |  |  | Y |  |
| target_name | string |  |  |  | Y |  |
| cutoff_days | integer |  |  |  | Y |  |
| records_deleted | integer |  |  |  | Y | 0 |
| archived_count | integer |  |  |  | Y | 0 |
| deleted_count | integer |  |  |  | Y | 0 |
| artifact_path | string |  |  |  | Y |  |
| result_json | text |  |  |  | Y |  |
| started_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B17004C0> |
| completed_at | datetime |  |  |  | Y |  |
| status | string |  |  |  | Y | pending |
| error_message | text |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_governance_retention_job_runs_is_deleted` (is_deleted)
- `ix_governance_retention_job_runs_id` (id)
- `ix_governance_retention_job_runs_country_code` (country_code)

---

### `governance.governance.role_permission_settings`

*Table: `governance.governance.role_permission_settings`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| role | string |  |  |  |  |  |
| permissions_json | json |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_governance_role_permission_settings_country_code` (country_code)
- `ix_governance_role_permission_settings_is_deleted` (is_deleted)
- `ix_governance_role_permission_settings_id` (id)

---

### `governance.governance.shipment_confirmations`

*Table: `governance.governance.shipment_confirmations`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| shipment_id | integer |  | Y |  |  |  |
| order_id | integer |  | Y |  | Y |  |
| supplier_id | integer |  | Y |  | Y |  |
| requester_user_id | integer |  | Y |  | Y |  |
| requester_role | string |  |  |  | Y |  |
| target_user_id | integer |  | Y |  | Y |  |
| target_role | string |  |  |  | Y |  |
| confirmation_type | string |  |  |  | Y |  |
| status | string |  |  |  | Y | pending |
| requested_status | string |  |  |  | Y |  |
| requested_event_type | string |  |  |  | Y |  |
| current_hub | string |  |  |  | Y |  |
| notes | text |  |  |  | Y |  |
| confirmation_code | string |  |  |  | Y |  |
| confirmed_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B15F1E10> |
| responded_at | datetime |  |  |  | Y |  |
| tracking_number | string |  |  |  | Y |  |
| delivery_signature_name | string |  |  |  | Y |  |
| delivery_signature_data_url | string |  |  |  | Y |  |
| delivery_signature_captured_at | datetime |  |  |  | Y |  |
| response_notes | text |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_governance_shipment_confirmations_country_code` (country_code)
- `ix_governance_shipment_confirmations_is_deleted` (is_deleted)
- `ix_governance_shipment_confirmations_id` (id)

**Foreign Keys:**

- `shipment_id` → `logistics.shipments.id`
- `order_id` → `orders.orders.id`
- `supplier_id` → `accounts.users.id`
- `requester_user_id` → `accounts.users.id`
- `target_user_id` → `accounts.users.id`

---

### `governance.governance.shipping_carriers`

*Table: `governance.governance.shipping_carriers`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| supplier_id | integer |  | Y |  | Y |  |
| name | string |  |  |  |  |  |
| code | string |  |  | Y |  |  |
| is_active | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_governance_shipping_carriers_id` (id)
- `ix_governance_shipping_carriers_country_code` (country_code)
- `ix_governance_shipping_carriers_is_deleted` (is_deleted)

**Foreign Keys:**

- `supplier_id` → `accounts.users.id`

---

### `governance.governance.shipping_zones`

*Table: `governance.governance.shipping_zones`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| supplier_id | integer |  | Y |  | Y |  |
| name | string |  |  |  |  |  |
| countries | json |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_governance_shipping_zones_is_deleted` (is_deleted)
- `ix_governance_shipping_zones_country_code` (country_code)
- `ix_governance_shipping_zones_id` (id)

**Foreign Keys:**

- `supplier_id` → `accounts.users.id`

---

### `governance.governance.supplier_country_commissions`

*Table: `governance.governance.supplier_country_commissions`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| supplier_id | integer |  | Y |  |  |  |
| country_code | string |  |  |  |  |  |
| commission_rate | numeric |  |  |  |  |  |
| category_slug | string |  |  |  | Y |  |
| notes | text |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_governance_supplier_country_commissions_is_deleted` (is_deleted)
- `ix_governance_supplier_country_commissions_id` (id)

**Foreign Keys:**

- `supplier_id` → `accounts.users.id`

---

### `governance.governance.system_alerts`

*Table: `governance.governance.system_alerts`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| alert_type | string |  |  |  |  |  |
| severity | string |  |  |  | Y | info |
| title | string |  |  |  |  |  |
| message | text |  |  |  |  |  |
| is_acknowledged | boolean |  |  |  | Y | False |
| acknowledged_by_id | integer |  | Y |  | Y |  |
| acknowledged_at | datetime |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_governance_system_alerts_is_deleted` (is_deleted)
- `ix_governance_system_alerts_id` (id)
- `ix_governance_system_alerts_country_code` (country_code)

**Foreign Keys:**

- `acknowledged_by_id` → `accounts.users.id`

---

### `governance.governance.system_health_events`

*Table: `governance.governance.system_health_events`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| service | string |  |  |  | Y |  |
| metric_name | string |  |  |  |  |  |
| metric_value | numeric |  |  |  |  |  |
| severity | string |  |  |  | Y | info |
| message | text |  |  |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| is_deleted | boolean |  |  |  |  | False |
| country_code | string |  | Y |  | Y |  |

**Indexes:**

- `ix_governance_system_health_events_is_deleted` (is_deleted)
- `ix_health_events_metric_time` (metric_name, created_at)
- `ix_governance_system_health_events_id` (id)
- `ix_governance_system_health_events_country_code` (country_code)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `governance.governance.system_settings`

*Table: `governance.governance.system_settings`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| key | string |  |  | Y |  |  |
| value | text |  |  |  | Y |  |
| value_type | string |  |  |  | Y | string |
| description | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_governance_system_settings_country_code` (country_code)
- `ix_governance_system_settings_is_deleted` (is_deleted)
- `ix_governance_system_settings_id` (id)

---

### `governance.governance.ticket_replies`

*Table: `governance.governance.ticket_replies`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| ticket_id | integer |  | Y |  |  |  |
| sender_id | integer |  | Y |  |  |  |
| message | text |  |  |  |  |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_governance_ticket_replies_is_deleted` (is_deleted)
- `ix_governance_ticket_replies_country_code` (country_code)
- `ix_governance_ticket_replies_id` (id)

**Foreign Keys:**

- `ticket_id` → `comms.support_tickets.id`
- `sender_id` → `accounts.users.id`

---

### `governance.governance.user_browsing_histories`

*Table: `governance.governance.user_browsing_histories`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| product_id | integer |  | Y |  |  |  |
| viewed_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| country_code | string |  | Y |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_governance_user_browsing_histories_country_code` (country_code)
- `ix_governance_user_browsing_histories_is_deleted` (is_deleted)
- `ix_governance_user_browsing_histories_id` (id)
- `ix_governance_user_browsing_histories_product_id` (product_id)
- `ix_governance_user_browsing_histories_user_id` (user_id)

**Foreign Keys:**

- `user_id` → `accounts.users.id`
- `product_id` → `catalog.products.id`
- `country_code` → `country.country_configs.code`

---

## HR

*Schema: `hr` · 31 tables*

### `hr.hr.alumni_networks`

*Table: `hr.hr.alumni_networks`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| employee_id | integer |  | Y | Y |  |  |
| status | string |  |  |  | Y | active |
| granted_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B11E2B00> |
| eligibility_expires_at | datetime |  |  |  | Y |  |
| notes | text |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_hr_alumni_networks_id` (id)
- `ix_hr_alumni_networks_country_code` (country_code)
- `ix_hr_alumni_networks_is_deleted` (is_deleted)

**Foreign Keys:**

- `employee_id` → `hr.employees.id`

---

### `hr.hr.coi_reports`

*Table: `hr.hr.coi_reports`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| employee_id | integer |  | Y |  |  |  |
| related_person_name | string |  |  |  |  |  |
| relation_type | string |  |  |  |  |  |
| is_internal | boolean |  |  |  | Y | False |
| internal_employee_id | integer |  | Y |  | Y |  |
| risk_level | string |  |  |  | Y | low |
| is_approved | boolean |  |  |  | Y | False |
| approved_by_id | integer |  | Y |  | Y |  |
| approved_at | datetime |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_hr_coi_reports_id` (id)
- `ix_hr_coi_reports_is_deleted` (is_deleted)
- `ix_hr_coi_reports_country_code` (country_code)

**Foreign Keys:**

- `employee_id` → `hr.employees.id`
- `internal_employee_id` → `hr.employees.id`
- `approved_by_id` → `accounts.users.id`

---

### `hr.hr.disciplinary_cases`

*Table: `hr.hr.disciplinary_cases`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| employee_id | integer |  | Y |  |  |  |
| employee_name | string |  |  |  | Y |  |
| stage | string |  |  |  |  | verbal_warning |
| description | text |  |  |  |  |  |
| issued_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B11E3010> |
| status | string |  |  |  | Y | active |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_hr_disciplinary_cases_country_code` (country_code)
- `ix_hr_disciplinary_cases_id` (id)
- `ix_hr_disciplinary_cases_is_deleted` (is_deleted)
- `ix_hr_disciplinary_cases_employee_id` (employee_id)

**Foreign Keys:**

- `employee_id` → `hr.employees.id`

---

### `hr.hr.dynamic_qr_sessions`

*Table: `hr.hr.dynamic_qr_sessions`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| employee_id | integer |  | Y |  |  |  |
| qr_token | string |  |  | Y |  |  |
| expires_at | datetime |  |  |  |  |  |
| used_at | datetime |  |  |  | Y |  |
| ip_address | string |  |  |  | Y |  |
| user_agent | string |  |  |  | Y |  |
| device_fingerprint | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- UNIQUE `ix_hr_dynamic_qr_sessions_qr_token` (qr_token)
- `ix_hr_dynamic_qr_sessions_country_code` (country_code)
- `ix_qr_session_employee_expires` (employee_id, expires_at)
- `ix_hr_dynamic_qr_sessions_id` (id)
- `ix_hr_dynamic_qr_sessions_is_deleted` (is_deleted)

**Foreign Keys:**

- `employee_id` → `hr.employees.id`

---

### `hr.hr.employee_activity_logs`

*Table: `hr.hr.employee_activity_logs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| actor_employee_id | integer |  | Y |  |  |  |
| action | string |  |  |  |  |  |
| entity_type | string |  |  |  | Y |  |
| entity_id | integer |  |  |  | Y |  |
| metadata_json | json |  |  |  | Y |  |
| ip_address | string |  |  |  | Y |  |
| device_fingerprint | string |  |  |  | Y |  |
| country_code | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_hr_employee_activity_logs_action` (action)
- `ix_hr_employee_activity_logs_is_deleted` (is_deleted)
- `ix_hr_employee_activity_logs_id` (id)
- `ix_hr_employee_activity_logs_country_code` (country_code)
- `ix_hr_employee_activity_logs_actor_employee_id` (actor_employee_id)

**Foreign Keys:**

- `actor_employee_id` → `hr.employees.id`

---

### `hr.hr.employee_addresses`

*Table: `hr.hr.employee_addresses`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| employee_id | integer |  | Y |  |  |  |
| address_type | string |  |  |  |  |  |
| street | string |  |  |  |  |  |
| city | string |  |  |  |  |  |
| state | string |  |  |  | Y |  |
| postal_code | string |  |  |  | Y |  |
| country_code | string |  | Y |  |  |  |
| is_primary | boolean |  |  |  | Y | False |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_hr_employee_addresses_employee_id` (employee_id)
- `ix_hr_employee_addresses_is_deleted` (is_deleted)
- `ix_hr_employee_addresses_id` (id)

**Foreign Keys:**

- `employee_id` → `hr.employees.id`
- `country_code` → `country.country_configs.code`

---

### `hr.hr.employee_assets`

*Table: `hr.hr.employee_assets`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| employee_id | integer |  | Y |  |  |  |
| asset_type | string |  |  |  |  |  |
| asset_id | string |  |  |  |  |  |
| serial_no | string |  |  |  | Y |  |
| assigned_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B11E0670> |
| returned_at | datetime |  |  |  | Y |  |
| status | string |  |  |  | Y | assigned |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_hr_employee_assets_country_code` (country_code)
- `ix_hr_employee_assets_employee_id` (employee_id)
- `ix_hr_employee_assets_id` (id)
- `ix_hr_employee_assets_is_deleted` (is_deleted)

**Foreign Keys:**

- `employee_id` → `hr.employees.id`

---

### `hr.hr.employee_attendances`

*Table: `hr.hr.employee_attendances`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| employee_id | integer |  | Y |  |  |  |
| record_date | date |  |  |  |  |  |
| scan_in_time | datetime |  |  |  | Y |  |
| scan_out_time | datetime |  |  |  | Y |  |
| scan_type | string |  |  |  | Y |  |
| location_lat | float |  |  |  | Y |  |
| location_long | float |  |  |  | Y |  |
| device_fingerprint | string |  |  |  | Y |  |
| is_anomaly | boolean |  |  |  | Y | False |
| status | string |  |  |  | Y | present |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_hr_employee_attendances_id` (id)
- `ix_hr_employee_attendances_is_deleted` (is_deleted)
- `ix_hr_employee_attendances_country_code` (country_code)
- `ix_hr_employee_attendances_employee_id` (employee_id)

**Foreign Keys:**

- `employee_id` → `hr.employees.id`

---

### `hr.hr.employee_biometrics`

*Table: `hr.hr.employee_biometrics`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| employee_id | integer |  | Y | Y |  |  |
| fingerprint_hash | string |  |  |  | Y |  |
| face_encoding | text |  |  |  | Y |  |
| biometric_type | string |  |  |  | Y | fingerprint |
| enrolled_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B10F57E0> |
| is_active | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  |  | False |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_hr_employee_biometrics_country_code` (country_code)
- `ix_hr_employee_biometrics_is_deleted` (is_deleted)
- `ix_hr_employee_biometrics_id` (id)

**Foreign Keys:**

- `employee_id` → `hr.employees.id`

---

### `hr.hr.employee_certifications`

*Table: `hr.hr.employee_certifications`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| employee_id | integer |  | Y |  |  |  |
| cert_type | string |  |  |  |  |  |
| cert_name | string |  |  |  |  |  |
| issued_date | date |  |  |  | Y |  |
| expiry_date | date |  |  |  | Y |  |
| is_valid | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_hr_employee_certifications_country_code` (country_code)
- `ix_hr_employee_certifications_employee_id` (employee_id)
- `ix_hr_employee_certifications_id` (id)
- `ix_hr_employee_certifications_is_deleted` (is_deleted)

**Foreign Keys:**

- `employee_id` → `hr.employees.id`

---

### `hr.hr.employee_dependents`

*Table: `hr.hr.employee_dependents`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| employee_id | integer |  | Y |  |  |  |
| name | string |  |  |  |  |  |
| relation | string |  |  |  |  |  |
| dob | date |  |  |  | Y |  |
| is_insured | boolean |  |  |  | Y | False |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_hr_employee_dependents_is_deleted` (is_deleted)
- `ix_hr_employee_dependents_id` (id)
- `ix_hr_employee_dependents_country_code` (country_code)
- `ix_hr_employee_dependents_employee_id` (employee_id)

**Foreign Keys:**

- `employee_id` → `hr.employees.id`

---

### `hr.hr.employee_documents`

*Table: `hr.hr.employee_documents`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| employee_id | integer |  | Y |  |  |  |
| doc_type | string |  |  |  |  |  |
| file_url | string |  |  |  |  |  |
| expiry_date | date |  |  |  | Y |  |
| verified_by_id | integer |  | Y |  | Y |  |
| verified_at | datetime |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_hr_employee_documents_country_code` (country_code)
- `ix_hr_employee_documents_employee_id` (employee_id)
- `ix_hr_employee_documents_is_deleted` (is_deleted)
- `ix_hr_employee_documents_id` (id)

**Foreign Keys:**

- `employee_id` → `hr.employees.id`
- `verified_by_id` → `accounts.users.id`

---

### `hr.hr.employee_leave_ledgers`

*Table: `hr.hr.employee_leave_ledgers`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| employee_id | integer |  | Y |  |  |  |
| leave_type | string |  |  |  |  |  |
| year | integer |  |  |  |  |  |
| allocated_days | integer |  |  |  | Y | 0 |
| used_days | integer |  |  |  | Y | 0 |
| carried_forward | integer |  |  |  | Y | 0 |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_hr_employee_leave_ledgers_employee_id` (employee_id)
- `ix_hr_employee_leave_ledgers_is_deleted` (is_deleted)
- `ix_hr_employee_leave_ledgers_country_code` (country_code)
- `ix_hr_employee_leave_ledgers_id` (id)

**Foreign Keys:**

- `employee_id` → `hr.employees.id`

---

### `hr.hr.employee_leave_requests`

*Table: `hr.hr.employee_leave_requests`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| employee_id | integer |  | Y |  |  |  |
| leave_type | string |  |  |  |  |  |
| start_date | date |  |  |  |  |  |
| end_date | date |  |  |  |  |  |
| days_requested | integer |  |  |  |  |  |
| status | string |  |  |  | Y | pending |
| approved_by_id | integer |  | Y |  | Y |  |
| approved_at | datetime |  |  |  | Y |  |
| rejection_reason | text |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_hr_employee_leave_requests_id` (id)
- `ix_hr_employee_leave_requests_is_deleted` (is_deleted)
- `ix_hr_employee_leave_requests_employee_id` (employee_id)
- `ix_hr_employee_leave_requests_country_code` (country_code)

**Foreign Keys:**

- `employee_id` → `hr.employees.id`
- `approved_by_id` → `accounts.users.id`

---

### `hr.hr.employee_relations`

*Table: `hr.hr.employee_relations`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| employee_id | integer |  | Y |  |  |  |
| related_person_name | string |  |  |  |  |  |
| relation_type | string |  |  |  |  |  |
| is_internal_employee | boolean |  |  |  | Y | False |
| internal_employee_id | integer |  | Y |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_hr_employee_relations_is_deleted` (is_deleted)
- `ix_hr_employee_relations_country_code` (country_code)
- `ix_hr_employee_relations_employee_id` (employee_id)
- `ix_hr_employee_relations_id` (id)

**Foreign Keys:**

- `employee_id` → `hr.employees.id`
- `internal_employee_id` → `hr.employees.id`

---

### `hr.hr.employee_risk_scores`

*Table: `hr.hr.employee_risk_scores`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| employee_id | integer |  | Y |  |  |  |
| assessment_date | date |  |  |  |  |  |
| score | float |  |  |  | Y | 0.0 |
| risk_level | string |  |  |  | Y |  |
| factors | json |  |  |  | Y |  |
| notes | text |  |  |  | Y |  |
| country_code | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_hr_employee_risk_scores_employee_id` (employee_id)
- `ix_hr_employee_risk_scores_id` (id)
- `ix_hr_employee_risk_scores_is_deleted` (is_deleted)

**Foreign Keys:**

- `employee_id` → `hr.employees.id`

---

### `hr.hr.employee_roles`

*Table: `hr.hr.employee_roles`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| role_name | string |  |  | Y | Y |  |
| permissions | json |  |  |  | Y |  |
| authority_level | integer |  |  |  | Y |  |
| can_approve_leave | boolean |  |  |  | Y | False |
| can_approve_expense | boolean |  |  |  | Y | False |
| can_manage_users | boolean |  |  |  | Y | False |
| is_deleted | boolean |  |  |  |  | False |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_hr_employee_roles_id` (id)
- `ix_hr_employee_roles_country_code` (country_code)
- `ix_hr_employee_roles_is_deleted` (is_deleted)

---

### `hr.hr.employee_shift_rosters`

*Table: `hr.hr.employee_shift_rosters`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| employee_id | integer |  | Y |  |  |  |
| shift_date | date |  |  |  |  |  |
| start_time | time |  |  |  |  |  |
| end_time | time |  |  |  |  |  |
| shift_type | string |  |  |  | Y | scheduled |
| status | string |  |  |  | Y | scheduled |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_hr_employee_shift_rosters_is_deleted` (is_deleted)
- `ix_hr_employee_shift_rosters_id` (id)
- `ix_hr_employee_shift_rosters_employee_id` (employee_id)
- `ix_hr_employee_shift_rosters_country_code` (country_code)

**Foreign Keys:**

- `employee_id` → `hr.employees.id`

---

### `hr.hr.employee_travel_requests`

*Table: `hr.hr.employee_travel_requests`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| employee_id | integer |  | Y |  |  |  |
| destination_country | string |  |  |  |  |  |
| start_date | date |  |  |  |  |  |
| end_date | date |  |  |  |  |  |
| purpose | string |  |  |  | Y |  |
| status | string |  |  |  | Y | pending |
| approved_by_id | integer |  | Y |  | Y |  |
| approved_at | datetime |  |  |  | Y |  |
| per_diem_json | json |  |  |  | Y |  |
| total_cost | numeric |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_hr_employee_travel_requests_id` (id)
- `ix_hr_employee_travel_requests_is_deleted` (is_deleted)
- `ix_hr_employee_travel_requests_country_code` (country_code)

**Foreign Keys:**

- `employee_id` → `hr.employees.id`
- `approved_by_id` → `accounts.users.id`

---

### `hr.hr.employee_work_logs`

*Table: `hr.hr.employee_work_logs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| employee_id | integer |  | Y |  |  |  |
| record_date | date |  |  |  |  |  |
| hours_worked | numeric |  |  |  | Y | 0 |
| task_description | text |  |  |  | Y |  |
| location_lat | float |  |  |  | Y |  |
| location_long | float |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_hr_employee_work_logs_id` (id)
- `ix_hr_employee_work_logs_employee_id` (employee_id)
- `ix_hr_employee_work_logs_country_code` (country_code)
- `ix_hr_employee_work_logs_is_deleted` (is_deleted)

**Foreign Keys:**

- `employee_id` → `hr.employees.id`

---

### `hr.hr.employees`

*Table: `hr.hr.employees`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y | Y | Y |  |
| employee_code | string |  |  | Y |  |  |
| office_id | integer |  | Y |  | Y |  |
| department | string |  |  |  | Y |  |
| position | string |  |  |  | Y |  |
| employment_type | string |  |  |  | Y | full_time |
| employment_status | string |  |  |  | Y | active |
| salary | numeric |  |  |  | Y |  |
| currency | string |  |  |  | Y | OMR |
| country_code | string |  | Y |  | Y |  |
| hire_date | date |  |  |  |  |  |
| termination_date | date |  |  |  | Y |  |
| is_verified | boolean |  |  |  | Y | False |
| gender | string |  |  |  | Y |  |
| years_of_experience | integer |  |  |  | Y |  |
| performance_score | integer |  |  |  | Y |  |
| education_level | string |  |  |  | Y |  |
| notes | text |  |  |  | Y |  |
| reporting_manager_id | integer |  | Y |  | Y |  |
| hiring_manager_id | integer |  | Y |  | Y |  |
| authority_level | integer |  |  |  | Y |  |
| org_unit_id | integer |  | Y |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_hr_employees_id` (id)
- `ix_hr_employees_is_deleted` (is_deleted)
- `ix_employees_office` (office_id)
- `ix_employees_user_id` (user_id)

**Foreign Keys:**

- `user_id` → `accounts.users.id`
- `office_id` → `hr.offices.id`
- `country_code` → `country.country_configs.code`
- `reporting_manager_id` → `hr.employees.id`
- `hiring_manager_id` → `accounts.users.id`
- `org_unit_id` → `hr.org_units.id`

---

### `hr.hr.geo_fence_logs`

*Table: `hr.hr.geo_fence_logs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| employee_id | integer |  | Y |  |  |  |
| latitude | float |  |  |  |  |  |
| longitude | float |  |  |  |  |  |
| accuracy_meters | integer |  |  |  | Y |  |
| scanned_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B10F5CF0> |
| is_within_fence | boolean |  |  |  | Y | False |
| is_deleted | boolean |  |  |  |  | False |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_hr_geo_fence_logs_is_deleted` (is_deleted)
- `ix_hr_geo_fence_logs_country_code` (country_code)
- `ix_hr_geo_fence_logs_id` (id)

**Foreign Keys:**

- `employee_id` → `hr.employees.id`

---

### `hr.hr.offboarding_cases`

*Table: `hr.hr.offboarding_cases`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| employee_id | integer |  | Y |  |  |  |
| employee_name | string |  |  |  | Y |  |
| reason | string |  |  |  |  | resignation |
| status | string |  |  |  | Y | pending |
| initiated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B11E3520> |
| completed_at | datetime |  |  |  | Y |  |
| notes | text |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_hr_offboarding_cases_employee_id` (employee_id)
- `ix_hr_offboarding_cases_id` (id)
- `ix_hr_offboarding_cases_is_deleted` (is_deleted)
- `ix_hr_offboarding_cases_country_code` (country_code)

**Foreign Keys:**

- `employee_id` → `hr.employees.id`

---

### `hr.hr.offices`

*Table: `hr.hr.offices`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| name | string |  |  |  |  |  |
| city | string |  |  |  | Y |  |
| latitude | float |  |  |  | Y |  |
| longitude | float |  |  |  | Y |  |
| geo_fence_radius_meters | integer |  |  |  | Y | 100 |
| address | text |  |  |  | Y |  |
| phone | string |  |  |  | Y |  |
| email | string |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  |  | False |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_hr_offices_is_deleted` (is_deleted)
- `ix_hr_offices_country_code` (country_code)
- `ix_hr_offices_id` (id)

---

### `hr.hr.onboarding_pipelines`

*Table: `hr.hr.onboarding_pipelines`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| pipeline_type | string |  |  |  |  |  |
| status | string |  |  |  | Y | pending |
| current_step | integer |  |  |  | Y | 0 |
| steps_data | json |  |  |  | Y |  |
| started_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7AFF29C60> |
| completed_at | datetime |  |  |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  |  |  |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_hr_onboarding_pipelines_id` (id)
- `ix_hr_onboarding_pipelines_country_code` (country_code)
- `ix_hr_onboarding_pipelines_user_id` (user_id)

**Foreign Keys:**

- `user_id` → `accounts.users.id`

---

### `hr.hr.onboarding_steps`

*Table: `hr.hr.onboarding_steps`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| pipeline_id | integer |  | Y |  |  |  |
| step_name | string |  |  |  |  |  |
| status | string |  |  |  | Y | pending |
| data | json |  |  |  | Y |  |
| started_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7AFF2A170> |
| completed_at | datetime |  |  |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  |  |  |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_hr_onboarding_steps_pipeline_id` (pipeline_id)
- `ix_hr_onboarding_steps_country_code` (country_code)
- `ix_hr_onboarding_steps_id` (id)

**Foreign Keys:**

- `pipeline_id` → `hr.onboarding_pipelines.id`

---

### `hr.hr.org_units`

*Table: `hr.hr.org_units`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| name | string |  |  |  |  |  |
| parent_id | integer |  | Y |  | Y |  |
| country_code | string |  |  |  | Y |  |
| level | integer |  |  |  | Y | 1 |
| is_active | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_hr_org_units_id` (id)
- `ix_hr_org_units_is_deleted` (is_deleted)

**Foreign Keys:**

- `parent_id` → `hr.org_units.id`

---

### `hr.hr.physical_id_cards`

*Table: `hr.hr.physical_id_cards`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| employee_id | integer |  | Y | Y |  |  |
| card_number | string |  |  | Y |  |  |
| issued_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B10F4E50> |
| expires_at | datetime |  |  |  | Y |  |
| is_revoked | boolean |  |  |  | Y | False |
| revoked_at | datetime |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_hr_physical_id_cards_id` (id)
- UNIQUE `ix_hr_physical_id_cards_card_number` (card_number)
- `ix_hr_physical_id_cards_is_deleted` (is_deleted)
- `ix_hr_physical_id_cards_country_code` (country_code)

**Foreign Keys:**

- `employee_id` → `hr.employees.id`

---

### `hr.hr.shift_handover_sessions`

*Table: `hr.hr.shift_handover_sessions`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| country_code | string |  | Y |  | Y |  |
| outgoing_employee_id | integer |  | Y |  |  |  |
| incoming_employee_id | integer |  | Y |  | Y |  |
| shift_date | datetime |  |  |  |  |  |
| notes | text |  |  |  | Y |  |
| status | string |  |  |  | Y | pending |
| acknowledged_at | datetime |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_handover_outgoing` (outgoing_employee_id)
- `ix_hr_shift_handover_sessions_id` (id)
- `ix_handover_incoming` (incoming_employee_id)
- `ix_hr_shift_handover_sessions_is_deleted` (is_deleted)
- `ix_handover_status` (status)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`
- `outgoing_employee_id` → `hr.employees.id`
- `incoming_employee_id` → `hr.employees.id`

---

### `hr.hr.shift_handover_tasks`

*Table: `hr.hr.shift_handover_tasks`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| session_id | integer |  | Y |  |  |  |
| description | text |  |  |  |  |  |
| priority | string |  |  |  | Y | normal |
| status | string |  |  |  | Y | open |
| assigned_to_id | integer |  | Y |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_hr_shift_handover_tasks_is_deleted` (is_deleted)
- `ix_hr_shift_handover_tasks_id` (id)

**Foreign Keys:**

- `session_id` → `hr.shift_handover_sessions.id`
- `assigned_to_id` → `accounts.users.id`

---

### `hr.hr.training_modules`

*Table: `hr.hr.training_modules`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| module_id | string | Y |  |  |  |  |
| title | string |  |  |  |  |  |
| description | text |  |  |  | Y |  |
| required_for_role | string |  |  |  | Y |  |
| duration_minutes | integer |  |  |  | Y | 30 |
| is_active | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_hr_training_modules_is_deleted` (is_deleted)

---

## LOGISTICS

*Schema: `logistics` · 25 tables*

### `logistics.logistics.city_distance_matrices`

*Table: `logistics.logistics.city_distance_matrices`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| origin_country_code | string |  |  |  |  |  |
| origin_city_name | string |  |  |  |  |  |
| destination_country_code | string |  |  |  |  |  |
| destination_city_name | string |  |  |  |  |  |
| distance_km | numeric |  |  |  | Y |  |
| notes | text |  |  |  | Y |  |
| created_by_id | integer |  | Y |  | Y |  |
| updated_by_id | integer |  | Y |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| country_code | string |  | Y |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0B15A20> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0B15870> |

**Indexes:**

- `ix_logistics_city_distance_matrices_is_deleted` (is_deleted)
- `ix_logistics_city_distance_matrices_id` (id)
- `ix_logistics_city_distance_matrices_country_code` (country_code)

**Foreign Keys:**

- `created_by_id` → `accounts.users.id`
- `updated_by_id` → `accounts.users.id`
- `country_code` → `country.country_configs.code`

---

### `logistics.logistics.customs_entries`

*Table: `logistics.logistics.customs_entries`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y |  | <function uuid4 at 0x000001C7B0B14C10> |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| version | integer |  |  |  |  | 1 |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| shipment_id | integer |  | Y |  |  |  |
| customs_declaration_number | string |  |  |  | Y |  |
| customs_broker | string |  |  |  | Y |  |
| entry_date | datetime |  |  |  | Y | now() |
| duty_rate_applied | numeric |  |  |  | Y |  |
| duty_amount | numeric |  |  |  | Y | 0 |
| vat_on_duty | numeric |  |  |  | Y | 0 |
| penalties | numeric |  |  |  | Y | 0 |
| total_customs_cost | numeric |  |  |  | Y | 0 |
| status | string |  |  |  | Y | cleared |
| notes | text |  |  |  | Y |  |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_logistics_customs_entries_country_code` (country_code)
- `ix_customs_entries_country_created` (country_code, created_at)
- `ix_logistics_customs_entries_id` (id)
- `ix_logistics_customs_entries_shipment_id` (shipment_id)

**Foreign Keys:**

- `shipment_id` → `logistics.import_shipments.id`

---

### `logistics.logistics.goods_receipt_lines`

*Table: `logistics.logistics.goods_receipt_lines`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y |  | <function uuid4 at 0x000001C7B09E2A70> |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| version | integer |  |  |  |  | 1 |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| grn_id | integer |  | Y |  |  |  |
| po_line_id | integer |  | Y |  | Y |  |
| product_id | integer |  | Y |  | Y |  |
| product_name | string |  |  |  | Y |  |
| sku | string |  |  |  | Y |  |
| quantity_received | numeric |  |  |  | Y | 0 |
| quantity_accepted | numeric |  |  |  | Y | 0 |
| quantity_rejected | numeric |  |  |  | Y | 0 |
| rejection_reason | string |  |  |  | Y |  |
| lot_number | string |  |  |  | Y |  |
| expiry_date | datetime |  |  |  | Y |  |
| unit_cost | numeric |  |  |  | Y | 0 |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_goods_receipt_lines_country_created` (country_code, created_at)
- `ix_logistics_goods_receipt_lines_country_code` (country_code)
- `ix_logistics_goods_receipt_lines_po_line_id` (po_line_id)
- `ix_logistics_goods_receipt_lines_id` (id)
- `ix_logistics_goods_receipt_lines_product_id` (product_id)
- `ix_logistics_goods_receipt_lines_grn_id` (grn_id)

**Foreign Keys:**

- `grn_id` → `logistics.goods_receipt_notes.id`
- `po_line_id` → `logistics.purchase_order_lines.id`
- `product_id` → `catalog.products.id`

---

### `logistics.logistics.goods_receipt_notes`

*Table: `logistics.logistics.goods_receipt_notes`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y |  | <function uuid4 at 0x000001C7B09E2560> |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| version | integer |  |  |  |  | 1 |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| grn_number | string |  |  | Y |  |  |
| po_id | integer |  | Y |  | Y |  |
| supplier_id | integer |  | Y |  | Y |  |
| receipt_date | datetime |  |  |  | Y | now() |
| warehouse_id | integer |  | Y |  | Y |  |
| status | string |  |  |  | Y | confirmed |
| notes | text |  |  |  | Y |  |
| received_by_id | integer |  | Y |  | Y |  |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_logistics_goods_receipt_notes_country_code` (country_code)
- `ix_logistics_goods_receipt_notes_supplier_id` (supplier_id)
- UNIQUE `ix_logistics_goods_receipt_notes_grn_number` (grn_number)
- `ix_logistics_goods_receipt_notes_id` (id)
- `ix_goods_receipt_notes_country_created` (country_code, created_at)
- `ix_logistics_goods_receipt_notes_received_by_id` (received_by_id)
- `ix_logistics_goods_receipt_notes_po_id` (po_id)
- `ix_logistics_goods_receipt_notes_warehouse_id` (warehouse_id)

**Foreign Keys:**

- `po_id` → `logistics.purchase_orders.id`
- `supplier_id` → `finance.vendors.id`
- `warehouse_id` → `logistics.warehouses.id`
- `received_by_id` → `accounts.users.id`

---

### `logistics.logistics.import_cost_templates`

*Table: `logistics.logistics.import_cost_templates`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y |  | <function uuid4 at 0x000001C7B0B15120> |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| version | integer |  |  |  |  | 1 |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| name | string |  |  |  |  |  |
| default_duty_rate | numeric |  |  |  | Y |  |
| default_freight_percent | numeric |  |  |  | Y |  |
| default_insurance_percent | numeric |  |  |  | Y |  |
| default_port_charges_percent | numeric |  |  |  | Y |  |
| default_bank_charges_percent | numeric |  |  |  | Y |  |
| allocation_method | string |  |  |  | Y | by_value |
| country_code | string |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| created_at | datetime |  |  |  | Y | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_logistics_import_cost_templates_country_code` (country_code)
- `ix_import_cost_templates_country_created` (country_code, created_at)
- `ix_logistics_import_cost_templates_id` (id)

---

### `logistics.logistics.import_shipment_lines`

*Table: `logistics.logistics.import_shipment_lines`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y |  | <function uuid4 at 0x000001C7B0B141F0> |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| version | integer |  |  |  |  | 1 |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| shipment_id | integer |  | Y |  |  |  |
| po_line_id | integer |  | Y |  | Y |  |
| product_id | integer |  | Y |  | Y |  |
| product_name | string |  |  |  | Y |  |
| sku | string |  |  |  | Y |  |
| hs_code | string |  |  |  | Y |  |
| quantity | numeric |  |  |  | Y | 0 |
| unit_cost_fx | numeric |  |  |  | Y | 0 |
| unit_cost_local | numeric |  |  |  | Y | 0 |
| line_total_fx | numeric |  |  |  | Y | 0 |
| weight_kg | numeric |  |  |  | Y |  |
| volume_cbm | numeric |  |  |  | Y |  |
| allocated_freight | numeric |  |  |  | Y | 0 |
| allocated_insurance | numeric |  |  |  | Y | 0 |
| allocated_port | numeric |  |  |  | Y | 0 |
| allocated_other | numeric |  |  |  | Y | 0 |
| duty_amount | numeric |  |  |  | Y | 0 |
| landed_unit_cost | numeric |  |  |  | Y | 0 |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_logistics_import_shipment_lines_country_code` (country_code)
- `ix_logistics_import_shipment_lines_product_id` (product_id)
- `ix_logistics_import_shipment_lines_shipment_id` (shipment_id)
- `ix_logistics_import_shipment_lines_po_line_id` (po_line_id)
- `ix_logistics_import_shipment_lines_id` (id)
- `ix_import_shipment_lines_country_created` (country_code, created_at)

**Foreign Keys:**

- `shipment_id` → `logistics.import_shipments.id`
- `po_line_id` → `logistics.purchase_order_lines.id`
- `product_id` → `catalog.products.id`

---

### `logistics.logistics.import_shipments`

*Table: `logistics.logistics.import_shipments`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y |  | <function uuid4 at 0x000001C7B09E3C70> |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| version | integer |  |  |  |  | 1 |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| shipment_ref | string |  |  | Y |  |  |
| po_id | integer |  | Y |  | Y |  |
| supplier_id | integer |  | Y |  | Y |  |
| supplier_name | string |  |  |  | Y |  |
| origin_country | string |  |  |  | Y |  |
| port_of_loading | string |  |  |  | Y |  |
| port_of_discharge | string |  |  |  | Y |  |
| vessel_name | string |  |  |  | Y |  |
| bill_of_lading | string |  |  |  | Y |  |
| container_number | string |  |  |  | Y |  |
| shipment_date | datetime |  |  |  | Y | now() |
| estimated_arrival | datetime |  |  |  | Y |  |
| actual_arrival | datetime |  |  |  | Y |  |
| currency | string |  |  |  | Y | OMR |
| exchange_rate | numeric |  |  |  | Y | 1 |
| warehouse_id | integer |  | Y |  | Y |  |
| country_code | string |  |  |  | Y |  |
| notes | text |  |  |  | Y |  |
| created_by_id | integer |  | Y |  | Y |  |
| status | string |  |  |  | Y | draft |
| product_cost_total | numeric |  |  |  | Y | 0 |
| freight_cost | numeric |  |  |  | Y | 0 |
| insurance_cost | numeric |  |  |  | Y | 0 |
| port_charges | numeric |  |  |  | Y | 0 |
| inland_freight | numeric |  |  |  | Y | 0 |
| bank_charges | numeric |  |  |  | Y | 0 |
| other_costs | numeric |  |  |  | Y | 0 |
| total_landed_cost | numeric |  |  |  | Y | 0 |
| duty_cost | numeric |  |  |  | Y | 0 |
| created_at | datetime |  |  |  | Y | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_logistics_import_shipments_id` (id)
- `ix_logistics_import_shipments_warehouse_id` (warehouse_id)
- `ix_logistics_import_shipments_supplier_id` (supplier_id)
- `ix_import_shipments_country_created` (country_code, created_at)
- UNIQUE `ix_logistics_import_shipments_shipment_ref` (shipment_ref)
- `ix_logistics_import_shipments_country_code` (country_code)
- `ix_logistics_import_shipments_po_id` (po_id)
- `ix_logistics_import_shipments_created_by_id` (created_by_id)

**Foreign Keys:**

- `po_id` → `logistics.purchase_orders.id`
- `supplier_id` → `finance.vendors.id`
- `warehouse_id` → `logistics.warehouses.id`
- `created_by_id` → `accounts.users.id`

---

### `logistics.logistics.landed_cost_allocations`

*Table: `logistics.logistics.landed_cost_allocations`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y |  | <function uuid4 at 0x000001C7B0B14700> |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| version | integer |  |  |  |  | 1 |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| shipment_id | integer |  | Y |  |  |  |
| cost_type | string |  |  |  | Y |  |
| description | text |  |  |  | Y |  |
| total_amount | numeric |  |  |  | Y | 0 |
| allocation_method | string |  |  |  | Y |  |
| currency | string |  |  |  | Y | OMR |
| exchange_rate | numeric |  |  |  | Y | 1 |
| country_code | string |  |  |  | Y |  |
| status | string |  |  |  | Y | allocated |
| created_at | datetime |  |  |  | Y | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_logistics_landed_cost_allocations_shipment_id` (shipment_id)
- `ix_logistics_landed_cost_allocations_id` (id)
- `ix_landed_cost_allocations_country_created` (country_code, created_at)
- `ix_logistics_landed_cost_allocations_country_code` (country_code)

**Foreign Keys:**

- `shipment_id` → `logistics.import_shipments.id`

---

### `logistics.logistics.logistics_category_pricing_rules`

*Table: `logistics.logistics.logistics_category_pricing_rules`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0B17BE0> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| partner_id | integer |  | Y |  |  |  |
| service_area_id | integer |  | Y |  | Y |  |
| category_name | string |  |  |  |  |  |
| flat_fee_override | numeric |  |  |  | Y |  |
| special_handling_fee | numeric |  |  |  | Y |  |
| currency | string |  |  |  | Y | USD |
| is_active | boolean |  |  |  | Y | True |
| approval_status | string |  |  |  | Y | pending |
| review_note | string |  |  |  | Y |  |
| reviewed_by_id | integer |  | Y |  | Y |  |
| reviewed_at | datetime |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0B17D00> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0B17C70> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_logistics_logistics_category_pricing_rules_created_by` (created_by)
- `ix_logistics_logistics_category_pricing_rules_partner_id` (partner_id)
- `ix_logistics_logistics_category_pricing_rules_is_deleted` (is_deleted)
- `ix_logistics_logistics_category_pricing_rules_service_area_id` (service_area_id)
- `ix_logistics_logistics_category_pricing_rules_country_code` (country_code)
- `ix_logistics_category_pricing_rules_country_created` (country_code, created_at)
- `ix_logistics_logistics_category_pricing_rules_updated_by` (updated_by)
- `ix_logistics_logistics_category_pricing_rules_reviewed_by_id` (reviewed_by_id)
- `ix_logistics_logistics_category_pricing_rules_id` (id)

**Foreign Keys:**

- `partner_id` → `logistics.logistics_partners.id`
- `service_area_id` → `logistics.logistics_partner_service_areas.id`
- `reviewed_by_id` → `accounts.users.id`

---

### `logistics.logistics.logistics_partner_profiles`

*Table: `logistics.logistics.logistics_partner_profiles`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0B160E0> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| partner_id | integer |  | Y | Y |  |  |
| tax_id | string |  |  |  | Y |  |
| registration_number | string |  |  |  | Y |  |
| business_type | string |  |  |  | Y |  |
| years_in_business | integer |  |  |  | Y |  |
| insurance_provider | string |  |  |  | Y |  |
| insurance_policy_number | string |  |  |  | Y |  |
| insurance_expiry | datetime |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0B16170> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0B16200> |
| country_code | string |  | Y |  | Y |  |

**Indexes:**

- `ix_logistics_partner_profiles_country_created` (country_code, created_at)
- `ix_logistics_logistics_partner_profiles_country_code` (country_code)
- `ix_logistics_logistics_partner_profiles_updated_by` (updated_by)
- `ix_logistics_logistics_partner_profiles_id` (id)
- `ix_logistics_logistics_partner_profiles_is_deleted` (is_deleted)
- `ix_logistics_logistics_partner_profiles_created_by` (created_by)
- UNIQUE `ix_logistics_logistics_partner_profiles_partner_id` (partner_id)

**Foreign Keys:**

- `partner_id` → `logistics.logistics_partners.id`
- `country_code` → `country.country_configs.code`

---

### `logistics.logistics.logistics_partner_service_areas`

*Table: `logistics.logistics.logistics_partner_service_areas`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0B167A0> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| partner_id | integer |  | Y |  |  |  |
| country_code | string |  |  |  |  |  |
| country_name | string |  |  |  |  |  |
| origin_city | string |  |  |  |  |  |
| city_name | string |  |  |  |  |  |
| zone_label | string |  |  |  | Y |  |
| charge_amount | numeric |  |  |  | Y |  |
| minimum_charge | numeric |  |  |  | Y |  |
| per_kg_rate | numeric |  |  |  | Y |  |
| pickup_charge | numeric |  |  |  | Y |  |
| dropoff_charge | numeric |  |  |  | Y |  |
| per_km_rate | numeric |  |  |  | Y |  |
| currency | string |  |  |  | Y | USD |
| delivery_days_min | integer |  |  |  | Y |  |
| delivery_days_max | integer |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| approval_status | string |  |  |  | Y | pending |
| review_note | string |  |  |  | Y |  |
| reviewed_by_id | integer |  |  |  | Y |  |
| reviewed_at | datetime |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0B168C0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0B16830> |

**Indexes:**

- `ix_logistics_logistics_partner_service_areas_id` (id)
- `ix_logistics_partner_service_areas_country_created` (country_code, created_at)
- `ix_logistics_logistics_partner_service_areas_created_by` (created_by)
- `ix_logistics_logistics_partner_service_areas_partner_id` (partner_id)
- `ix_logistics_logistics_partner_service_areas_is_deleted` (is_deleted)
- `ix_logistics_logistics_partner_service_areas_updated_by` (updated_by)

**Foreign Keys:**

- `partner_id` → `logistics.logistics_partners.id`

---

### `logistics.logistics.logistics_partners`

*Table: `logistics.logistics.logistics_partners`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0B15B40> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  | Y |  |
| name | string |  |  |  |  |  |
| code | string |  |  | Y |  |  |
| contact_name | string |  |  |  | Y |  |
| contact_email | string |  |  |  | Y |  |
| contact_phone | string |  |  |  | Y |  |
| website | string |  |  |  | Y |  |
| coverage_regions | json |  |  |  | Y |  |
| service_types | json |  |  |  | Y |  |
| status_code | string |  |  |  | Y | active |
| verification_status | string |  |  |  | Y | pending |
| verification_note | string |  |  |  | Y |  |
| verified_by | integer |  |  |  | Y |  |
| verified_at | datetime |  |  |  | Y |  |
| country_code | string |  | Y |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0B15C60> |
| business_type | string |  |  |  | Y |  |
| region | string |  |  |  | Y |  |
| city | string |  |  |  | Y |  |
| address | text |  |  |  | Y |  |
| postal_code | string |  |  |  | Y |  |
| tax_id | string |  |  |  | Y |  |
| bio | text |  |  |  | Y |  |
| about_us | text |  |  |  | Y |  |
| logo_url | string |  |  |  | Y |  |
| banner_url | string |  |  |  | Y |  |
| latitude | numeric |  |  |  | Y |  |
| longitude | numeric |  |  |  | Y |  |
| social_links | json |  |  |  | Y |  |
| notes | text |  |  |  | Y |  |
| is_terms_accepted | boolean |  |  |  | Y | False |
| terms_version | string |  |  |  | Y |  |
| terms_accepted_at | datetime |  |  |  | Y |  |

**Indexes:**

- `ix_logistics_logistics_partners_country_code` (country_code)
- `ix_logistics_logistics_partners_user_id` (user_id)
- `ix_logistics_partners_coverage_regions` (coverage_regions)
- `ix_logistics_logistics_partners_updated_by` (updated_by)
- `ix_logistics_partners_service_types` (service_types)
- `ix_logistics_partners_social_links` (social_links)
- `ix_logistics_logistics_partners_is_deleted` (is_deleted)
- `ix_logistics_logistics_partners_id` (id)
- `ix_logistics_partners_country_created` (country_code, created_at)
- `ix_logistics_logistics_partners_created_by` (created_by)

**Foreign Keys:**

- `user_id` → `accounts.users.id`
- `country_code` → `country.country_configs.code`

---

### `logistics.logistics.logistics_pricing_profiles`

*Table: `logistics.logistics.logistics_pricing_profiles`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0B16E60> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| partner_id | integer |  | Y |  |  |  |
| service_area_id | integer |  | Y |  |  |  |
| profile_name | string |  |  |  |  |  |
| base_in_city_fee | numeric |  |  |  | Y |  |
| per_kg_rate | numeric |  |  |  | Y |  |
| minimum_charge | numeric |  |  |  | Y |  |
| maximum_charge | numeric |  |  |  | Y |  |
| fuel_multiplier | numeric |  |  |  | Y | 1.0 |
| base_inter_city_fee | numeric |  |  |  | Y |  |
| per_km_rate | numeric |  |  |  | Y |  |
| bulk_discount_threshold_kg | numeric |  |  |  | Y |  |
| bulk_discount_percent | numeric |  |  |  | Y |  |
| currency | string |  |  |  | Y | USD |
| is_active | boolean |  |  |  | Y | True |
| approval_status | string |  |  |  | Y | pending |
| review_note | string |  |  |  | Y |  |
| reviewed_by_id | integer |  | Y |  | Y |  |
| reviewed_at | datetime |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0B16F80> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0B16EF0> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_logistics_logistics_pricing_profiles_service_area_id` (service_area_id)
- `ix_logistics_logistics_pricing_profiles_updated_by` (updated_by)
- `ix_logistics_logistics_pricing_profiles_is_deleted` (is_deleted)
- `ix_logistics_logistics_pricing_profiles_id` (id)
- `ix_logistics_pricing_profiles_country_created` (country_code, created_at)
- `ix_logistics_logistics_pricing_profiles_created_by` (created_by)
- `ix_logistics_logistics_pricing_profiles_partner_id` (partner_id)
- `ix_logistics_logistics_pricing_profiles_country_code` (country_code)
- `ix_logistics_logistics_pricing_profiles_reviewed_by_id` (reviewed_by_id)

**Foreign Keys:**

- `partner_id` → `logistics.logistics_partners.id`
- `service_area_id` → `logistics.logistics_partner_service_areas.id`
- `reviewed_by_id` → `accounts.users.id`

---

### `logistics.logistics.logistics_vehicle_rules`

*Table: `logistics.logistics.logistics_vehicle_rules`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0B17520> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| partner_id | integer |  | Y |  |  |  |
| service_area_id | integer |  | Y |  |  |  |
| vehicle_type | string |  |  |  |  |  |
| max_weight_kg | numeric |  |  |  | Y |  |
| cost_multiplier | numeric |  |  |  | Y |  |
| priority_rank | integer |  |  |  | Y | 0 |
| route_scope | string |  |  |  | Y |  |
| max_volume_cm3 | numeric |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| approval_status | string |  |  |  | Y | pending |
| review_note | string |  |  |  | Y |  |
| reviewed_by_id | integer |  | Y |  | Y |  |
| reviewed_at | datetime |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0B17640> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0B175B0> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_logistics_logistics_vehicle_rules_created_by` (created_by)
- `ix_logistics_logistics_vehicle_rules_reviewed_by_id` (reviewed_by_id)
- `ix_logistics_logistics_vehicle_rules_partner_id` (partner_id)
- `ix_logistics_logistics_vehicle_rules_is_deleted` (is_deleted)
- `ix_logistics_logistics_vehicle_rules_updated_by` (updated_by)
- `ix_logistics_logistics_vehicle_rules_id` (id)
- `ix_logistics_vehicle_rules_country_created` (country_code, created_at)
- `ix_logistics_logistics_vehicle_rules_service_area_id` (service_area_id)
- `ix_logistics_logistics_vehicle_rules_country_code` (country_code)

**Foreign Keys:**

- `partner_id` → `logistics.logistics_partners.id`
- `service_area_id` → `logistics.logistics_partner_service_areas.id`
- `reviewed_by_id` → `accounts.users.id`

---

### `logistics.logistics.partner_performance_projections`

*Table: `logistics.logistics.partner_performance_projections`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| partner_id | integer |  | Y |  |  |  |
| country_code | string |  |  |  | Y |  |
| total_shipments | integer |  |  |  | Y | 0 |
| delivered_shipments | integer |  |  |  | Y | 0 |
| cancelled_shipments | integer |  |  |  | Y | 0 |
| avg_delivery_hours | numeric |  |  |  | Y |  |
| on_time_rate | numeric |  |  |  | Y |  |
| period_start | datetime |  |  |  | Y |  |
| period_end | datetime |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_partner_perf_partner_id` (partner_id)
- `ix_partner_perf_country` (country_code)
- `ix_logistics_partner_performance_projections_id` (id)

**Foreign Keys:**

- `partner_id` → `logistics.logistics_partners.id`

---

### `logistics.logistics.purchase_order_lines`

*Table: `logistics.logistics.purchase_order_lines`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y |  | <function uuid4 at 0x000001C7B09E2050> |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| version | integer |  |  |  |  | 1 |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| po_id | integer |  | Y |  |  |  |
| product_id | integer |  | Y |  | Y |  |
| product_name | string |  |  |  | Y |  |
| sku | string |  |  |  | Y |  |
| description | text |  |  |  | Y |  |
| quantity_ordered | numeric |  |  |  | Y | 0 |
| quantity_received | numeric |  |  |  | Y | 0 |
| unit_price | numeric |  |  |  | Y | 0 |
| discount_percent | numeric |  |  |  | Y | 0 |
| discount_amount | numeric |  |  |  | Y | 0 |
| tax_rate | numeric |  |  |  | Y | 0 |
| tax_amount | numeric |  |  |  | Y | 0 |
| line_total | numeric |  |  |  | Y | 0 |
| weight | numeric |  |  |  | Y |  |
| volume | numeric |  |  |  | Y |  |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_logistics_purchase_order_lines_po_id` (po_id)
- `ix_logistics_purchase_order_lines_country_code` (country_code)
- `ix_logistics_purchase_order_lines_product_id` (product_id)
- `ix_logistics_purchase_order_lines_id` (id)
- `ix_purchase_order_lines_country_created` (country_code, created_at)

**Foreign Keys:**

- `po_id` → `logistics.purchase_orders.id`
- `product_id` → `catalog.products.id`

---

### `logistics.logistics.purchase_orders`

*Table: `logistics.logistics.purchase_orders`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y |  | <function uuid4 at 0x000001C7B09E1B40> |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| version | integer |  |  |  |  | 1 |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| po_number | string |  |  | Y |  |  |
| supplier_id | integer |  | Y |  | Y |  |
| supplier_name | string |  |  |  | Y |  |
| order_date | datetime |  |  |  | Y | now() |
| expected_delivery_date | datetime |  |  |  | Y |  |
| warehouse_id | integer |  | Y |  | Y |  |
| currency | string |  |  |  | Y | OMR |
| notes | text |  |  |  | Y |  |
| terms | text |  |  |  | Y |  |
| shipping_address | text |  |  |  | Y |  |
| country_code | string |  |  |  | Y |  |
| created_by_id | integer |  | Y |  | Y |  |
| status | string |  |  |  | Y | draft |
| subtotal | numeric |  |  |  | Y | 0 |
| discount_total | numeric |  |  |  | Y | 0 |
| tax_total | numeric |  |  |  | Y | 0 |
| grand_total | numeric |  |  |  | Y | 0 |
| total_amount | numeric |  |  |  | Y | 0 |
| delivery_date | datetime |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- UNIQUE `ix_logistics_purchase_orders_po_number` (po_number)
- `ix_logistics_purchase_orders_supplier_id` (supplier_id)
- `ix_logistics_purchase_orders_created_by_id` (created_by_id)
- `ix_logistics_purchase_orders_id` (id)
- `ix_purchase_orders_country_created` (country_code, created_at)
- `ix_logistics_purchase_orders_country_code` (country_code)
- `ix_logistics_purchase_orders_warehouse_id` (warehouse_id)

**Foreign Keys:**

- `supplier_id` → `finance.vendors.id`
- `warehouse_id` → `logistics.warehouses.id`
- `created_by_id` → `accounts.users.id`

---

### `logistics.logistics.sales_order_lines`

*Table: `logistics.logistics.sales_order_lines`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y |  | <function uuid4 at 0x000001C7AFD45480> |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| version | integer |  |  |  |  | 1 |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| so_id | integer |  | Y |  |  |  |
| product_id | integer |  | Y |  | Y |  |
| product_name | string |  |  |  | Y |  |
| sku | string |  |  |  | Y |  |
| description | text |  |  |  | Y |  |
| quantity_ordered | numeric |  |  |  | Y | 0 |
| quantity_dispatched | numeric |  |  |  | Y | 0 |
| unit_price | numeric |  |  |  | Y | 0 |
| discount_percent | numeric |  |  |  | Y | 0 |
| discount_amount | numeric |  |  |  | Y | 0 |
| tax_rate | numeric |  |  |  | Y | 0 |
| tax_amount | numeric |  |  |  | Y | 0 |
| line_total | numeric |  |  |  | Y | 0 |
| weight | numeric |  |  |  | Y |  |
| volume | numeric |  |  |  | Y |  |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_sales_order_lines_country_created` (country_code, created_at)
- `ix_logistics_sales_order_lines_country_code` (country_code)
- `ix_logistics_sales_order_lines_so_id` (so_id)
- `ix_logistics_sales_order_lines_product_id` (product_id)
- `ix_logistics_sales_order_lines_id` (id)

**Foreign Keys:**

- `so_id` → `logistics.sales_orders.id`
- `product_id` → `catalog.products.id`

---

### `logistics.logistics.sales_orders`

*Table: `logistics.logistics.sales_orders`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y |  | <function uuid4 at 0x000001C7B09E2F80> |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| version | integer |  |  |  |  | 1 |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| so_number | string |  |  | Y |  |  |
| customer_id | integer |  | Y |  | Y |  |
| customer_name | string |  |  |  | Y |  |
| customer_po_number | string |  |  |  | Y |  |
| order_date | datetime |  |  |  | Y | now() |
| expected_delivery_date | datetime |  |  |  | Y |  |
| warehouse_id | integer |  | Y |  | Y |  |
| currency | string |  |  |  | Y | OMR |
| shipping_address | text |  |  |  | Y |  |
| billing_address | text |  |  |  | Y |  |
| notes | text |  |  |  | Y |  |
| terms | text |  |  |  | Y |  |
| country_code | string |  |  |  | Y |  |
| created_by_id | integer |  | Y |  | Y |  |
| status | string |  |  |  | Y | draft |
| subtotal | numeric |  |  |  | Y | 0 |
| discount_total | numeric |  |  |  | Y | 0 |
| tax_total | numeric |  |  |  | Y | 0 |
| grand_total | numeric |  |  |  | Y | 0 |
| delivery_date | datetime |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_sales_orders_country_created` (country_code, created_at)
- `ix_logistics_sales_orders_id` (id)
- UNIQUE `ix_logistics_sales_orders_so_number` (so_number)
- `ix_logistics_sales_orders_created_by_id` (created_by_id)
- `ix_logistics_sales_orders_warehouse_id` (warehouse_id)
- `ix_logistics_sales_orders_country_code` (country_code)
- `ix_logistics_sales_orders_customer_id` (customer_id)

**Foreign Keys:**

- `customer_id` → `finance.customers.id`
- `warehouse_id` → `logistics.warehouses.id`
- `created_by_id` → `accounts.users.id`

---

### `logistics.logistics.shipment_events`

*Table: `logistics.logistics.shipment_events`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0C289D0> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| shipment_id | integer |  | Y |  | Y |  |
| order_id | integer |  | Y |  | Y |  |
| supplier_id | integer |  | Y |  |  |  |
| actor_user_id | integer |  | Y |  | Y |  |
| actor_role | string |  |  |  | Y |  |
| event_type | string |  |  |  |  |  |
| status_after | string |  |  |  | Y |  |
| distribution_channel | string |  |  |  | Y |  |
| location | string |  |  |  | Y |  |
| latitude | numeric |  |  |  | Y |  |
| longitude | numeric |  |  |  | Y |  |
| scan_code | string |  |  |  | Y |  |
| notes | string |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0C28AF0> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_logistics_shipment_events_updated_by` (updated_by)
- `ix_logistics_shipment_events_supplier_id` (supplier_id)
- `ix_logistics_shipment_events_shipment_id` (shipment_id)
- `ix_logistics_shipment_events_country_code` (country_code)
- `ix_shipment_events_order_id` (order_id)
- `ix_logistics_shipment_events_is_deleted` (is_deleted)
- `ix_logistics_shipment_events_id` (id)
- `ix_logistics_shipment_events_order_id` (order_id)
- `ix_logistics_shipment_events_actor_user_id` (actor_user_id)
- `ix_shipment_events_shipment_id` (shipment_id)
- `ix_shipment_events_country_created` (country_code, created_at)
- `ix_logistics_shipment_events_created_by` (created_by)

**Foreign Keys:**

- `shipment_id` → `logistics.shipments.id`
- `order_id` → `orders.orders.id`
- `supplier_id` → `accounts.users.id`
- `actor_user_id` → `accounts.users.id`

---

### `logistics.logistics.shipment_tracking_projections`

*Table: `logistics.logistics.shipment_tracking_projections`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| shipment_id | integer |  | Y |  |  |  |
| order_id | integer |  |  |  |  |  |
| status_code | string |  |  |  |  |  |
| carrier_name | string |  |  |  | Y |  |
| tracking_number | string |  |  |  | Y |  |
| current_hub | string |  |  |  | Y |  |
| estimated_delivery | datetime |  |  |  | Y |  |
| actual_delivery | datetime |  |  |  | Y |  |
| event_log | json |  |  |  | Y |  |
| last_event_at | datetime |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_logistics_shipment_tracking_projections_id` (id)
- `ix_shipment_tracking_status` (status_code)
- `ix_shipment_tracking_order_id` (order_id)

**Foreign Keys:**

- `shipment_id` → `logistics.shipments.id`

---

### `logistics.logistics.shipments`

*Table: `logistics.logistics.shipments`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0C28310> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| order_id | integer |  | Y |  |  |  |
| supplier_id | integer |  | Y |  |  |  |
| assigned_partner_id | integer |  | Y |  | Y |  |
| carrier_id | integer |  | Y |  | Y |  |
| tracking_number | string |  |  | Y | Y |  |
| carrier_name | string |  |  |  | Y |  |
| status_code | string |  |  |  | Y | processing |
| distribution_channel | string |  |  |  | Y |  |
| current_hub | string |  |  |  | Y |  |
| scan_code | string |  |  |  | Y |  |
| package_count | integer |  |  |  | Y | 1 |
| package_weight_kg | numeric |  |  |  | Y |  |
| package_dimensions | string |  |  |  | Y |  |
| packaged_at | datetime |  |  |  | Y |  |
| packaged_by_user_id | integer |  |  |  | Y |  |
| packaged_notes | string |  |  |  | Y |  |
| packaging_notes | string |  |  |  | Y |  |
| shipped_at | datetime |  |  |  | Y |  |
| estimated_delivery | datetime |  |  |  | Y |  |
| actual_delivery | datetime |  |  |  | Y |  |
| delivery_signature_name | string |  |  |  | Y |  |
| delivery_signature_data_url | string |  |  |  | Y |  |
| delivery_signature_captured_at | datetime |  |  |  | Y |  |
| notes | text |  |  |  | Y |  |
| accepted_vehicle_type | string |  |  |  | Y |  |
| accepted_vehicle_multiplier | numeric |  |  |  | Y |  |
| accepted_vehicle_selected_at | datetime |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0C28430> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0C283A0> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_logistics_shipments_id` (id)
- `ix_logistics_shipments_carrier_id` (carrier_id)
- `ix_logistics_shipments_country_code` (country_code)
- `ix_shipments_country_created` (country_code, created_at)
- `ix_logistics_shipments_assigned_partner_id` (assigned_partner_id)
- `ix_logistics_shipments_order_id` (order_id)
- `ix_logistics_shipments_created_by` (created_by)
- `ix_logistics_shipments_updated_by` (updated_by)
- `ix_logistics_shipments_supplier_id` (supplier_id)
- `ix_shipments_order_id` (order_id)
- `ix_logistics_shipments_is_deleted` (is_deleted)

**Foreign Keys:**

- `order_id` → `orders.orders.id`
- `supplier_id` → `accounts.users.id`
- `assigned_partner_id` → `logistics.logistics_partners.id`
- `carrier_id` → `governance.shipping_carriers.id`

---

### `logistics.logistics.shipping_rules`

*Table: `logistics.logistics.shipping_rules`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0310E50> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| country_code | string |  | Y |  |  |  |
| method | string |  |  |  |  |  |
| base_rate | numeric |  |  |  |  |  |
| per_kg_rate | numeric |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B0310F70> |

**Indexes:**

- `ix_logistics_shipping_rules_id` (id)
- `ix_logistics_shipping_rules_created_by` (created_by)
- `ix_logistics_shipping_rules_updated_by` (updated_by)
- `ix_logistics_shipping_rules_is_deleted` (is_deleted)
- `ix_shipping_rules_country_created` (country_code, created_at)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `logistics.logistics.stock_movements`

*Table: `logistics.logistics.stock_movements`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y |  | <function uuid4 at 0x000001C7B09E3760> |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| version | integer |  |  |  |  | 1 |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| product_id | integer |  | Y |  | Y |  |
| warehouse_id | integer |  | Y |  | Y |  |
| movement_type | string |  |  |  | Y |  |
| reference_type | string |  |  |  | Y |  |
| reference_id | integer |  |  |  | Y |  |
| quantity_change | numeric |  |  |  | Y | 0 |
| quantity_after | numeric |  |  |  | Y | 0 |
| unit_cost | numeric |  |  |  | Y |  |
| total_cost | numeric |  |  |  | Y | 0 |
| country_code | string |  |  |  | Y |  |
| created_by_id | integer |  | Y |  | Y |  |
| created_at | datetime |  |  |  | Y | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_logistics_stock_movements_created_by_id` (created_by_id)
- `ix_logistics_stock_movements_product_id` (product_id)
- `ix_logistics_stock_movements_warehouse_id` (warehouse_id)
- `ix_stock_movements_country_created` (country_code, created_at)
- `ix_logistics_stock_movements_country_code` (country_code)
- `ix_logistics_stock_movements_id` (id)

**Foreign Keys:**

- `product_id` → `catalog.products.id`
- `warehouse_id` → `logistics.warehouses.id`
- `created_by_id` → `accounts.users.id`

---

### `logistics.logistics.warehouses`

*Table: `logistics.logistics.warehouses`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y |  | <function uuid4 at 0x000001C7B040ACB0> |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| version | integer |  |  |  |  | 1 |
| created_by_id | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| name | string |  |  |  |  |  |
| code | string |  |  | Y |  |  |
| address | string |  |  |  | Y |  |
| city | string |  |  |  | Y |  |
| country_code | string |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| created_at | datetime |  |  |  | Y | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_warehouses_country_created` (country_code, created_at)
- UNIQUE `ix_logistics_warehouses_code` (code)
- `ix_logistics_warehouses_country_code` (country_code)
- `ix_logistics_warehouses_id` (id)

---

## ORDERS

*Schema: `orders` · 5 tables*

### `orders.orders.order_items`

*Table: `orders.orders.order_items`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0312EF0> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| order_id | integer |  | Y |  |  |  |
| product_id | integer |  | Y |  |  |  |
| variant_id | integer |  |  |  | Y |  |
| supplier_id | integer |  |  |  | Y |  |
| quantity | integer |  |  |  | Y | 1 |
| unit_price | numeric |  |  |  | Y |  |
| price | numeric |  |  |  | Y |  |
| total_price | numeric |  |  |  | Y |  |
| product_name | string |  |  |  | Y |  |
| product_image | string |  |  |  | Y |  |
| selected_size | string |  |  |  | Y |  |
| selected_color | string |  |  |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| country_code | string |  | Y |  | Y |  |

**Indexes:**

- `ix_order_items_country_created` (country_code, created_at)
- `ix_orders_order_items_country_code` (country_code)
- `ix_orders_order_items_order_id` (order_id)
- `ix_orders_order_items_created_by` (created_by)
- `ix_orders_order_items_updated_by` (updated_by)
- `ix_orders_order_items_product_id` (product_id)
- `ix_orders_order_items_is_deleted` (is_deleted)
- `ix_order_items_order_id` (order_id)
- `ix_order_items_product_id` (product_id)
- `ix_orders_order_items_id` (id)

**Foreign Keys:**

- `order_id` → `orders.orders.id`
- `product_id` → `catalog.products.id`
- `country_code` → `country.country_configs.code`

---

### `orders.orders.order_logistics_allocations`

*Table: `orders.orders.order_logistics_allocations`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0313400> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| order_id | integer |  | Y |  |  |  |
| supplier_id | integer |  | Y |  |  |  |
| shipment_id | integer |  | Y |  | Y |  |
| partner_id | integer |  | Y |  | Y |  |
| service_area_id | integer |  | Y |  | Y |  |
| allocation_source | string |  |  |  | Y |  |
| partner_name_snapshot | string |  |  |  | Y |  |
| partner_code_snapshot | string |  |  |  | Y |  |
| service_area_label_snapshot | string |  |  |  | Y |  |
| destination_country | string |  |  |  | Y |  |
| destination_city | string |  |  |  | Y |  |
| shipping_amount | numeric |  |  |  | Y |  |
| pickup_charge | numeric |  |  |  | Y |  |
| dropoff_charge | numeric |  |  |  | Y |  |
| accepted_vehicle_rule_id | integer |  |  |  | Y |  |
| accepted_vehicle_type | string |  |  |  | Y |  |
| accepted_vehicle_multiplier | numeric |  |  |  | Y |  |
| accepted_shipping_amount | numeric |  |  |  | Y |  |
| accepted_pickup_charge | numeric |  |  |  | Y |  |
| accepted_dropoff_charge | numeric |  |  |  | Y |  |
| estimated_delivery_min | integer |  |  |  | Y |  |
| estimated_delivery_max | integer |  |  |  | Y |  |
| currency | string |  |  |  | Y | USD |
| pricing_breakdown_json | text |  |  |  | Y |  |
| accepted_pricing_breakdown_json | text |  |  |  | Y |  |
| country_code | string |  | Y |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_orders_order_logistics_allocations_id` (id)
- `ix_order_logistics_allocations_country_created` (country_code, created_at)
- `ix_orders_order_logistics_allocations_supplier_id` (supplier_id)
- `ix_orders_order_logistics_allocations_service_area_id` (service_area_id)
- `ix_orders_order_logistics_allocations_shipment_id` (shipment_id)
- `ix_orders_order_logistics_allocations_created_by` (created_by)
- `ix_orders_order_logistics_allocations_order_id` (order_id)
- `ix_orders_order_logistics_allocations_updated_by` (updated_by)
- `ix_orders_order_logistics_allocations_partner_id` (partner_id)
- `ix_orders_order_logistics_allocations_country_code` (country_code)
- `ix_orders_order_logistics_allocations_is_deleted` (is_deleted)

**Foreign Keys:**

- `order_id` → `orders.orders.id`
- `supplier_id` → `accounts.users.id`
- `shipment_id` → `logistics.shipments.id`
- `partner_id` → `logistics.logistics_partners.id`
- `service_area_id` → `logistics.logistics_partner_service_areas.id`
- `country_code` → `country.country_configs.code`

---

### `orders.orders.order_notifications`

*Table: `orders.orders.order_notifications`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0408B80> |
| version | integer |  |  |  |  | 1 |
| updated_at | datetime |  |  |  |  | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| order_id | integer |  | Y |  |  |  |
| title | string |  |  |  | Y |  |
| message | text |  |  |  | Y |  |
| channel | string |  |  |  | Y |  |
| is_read | boolean |  |  |  | Y | False |
| created_at | datetime |  |  |  |  | now() |

**Indexes:**

- `ix_orders_order_notifications_is_deleted` (is_deleted)
- `ix_orders_order_notifications_id` (id)
- `ix_orders_order_notifications_order_id` (order_id)
- `ix_order_notifications_user_id` (user_id)
- `ix_orders_order_notifications_created_by` (created_by)
- `ix_orders_order_notifications_user_id` (user_id)
- `ix_orders_order_notifications_updated_by` (updated_by)

**Foreign Keys:**

- `user_id` → `accounts.users.id`
- `order_id` → `orders.orders.id`

---

### `orders.orders.orders`

*Table: `orders.orders.orders`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7AFD47B50> |
| version | integer |  |  |  |  | 1 |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| order_number | string |  |  | Y | Y |  |
| customer_id | integer |  | Y |  | Y |  |
| user_id | integer |  | Y |  |  |  |
| status_code | string |  |  |  | Y | pending |
| status_label | string |  |  |  | Y |  |
| payment_status | string |  |  |  | Y | pending |
| payment_method | string |  |  |  | Y |  |
| payment_provider | string |  |  |  | Y |  |
| payment_intent_id | string |  |  |  | Y |  |
| subtotal | numeric |  |  |  | Y |  |
| subtotal_amount | numeric |  |  |  | Y |  |
| shipping_fee | numeric |  |  |  | Y | 0 |
| shipping_amount | numeric |  |  |  | Y | 0 |
| tax_amount | numeric |  |  |  | Y | 0 |
| vat_amount | numeric |  |  |  | Y | 0 |
| discount_amount | numeric |  |  |  | Y | 0 |
| total | numeric |  |  |  | Y |  |
| total_amount | numeric |  |  |  | Y |  |
| coupon_code | string |  |  |  | Y |  |
| fraud_score | numeric |  |  |  | Y | 0 |
| fraud_action | string |  |  |  | Y | allow |
| currency | string |  |  |  | Y | USD |
| shipping_address | text |  |  |  | Y |  |
| shipping_city | string |  |  |  | Y |  |
| shipping_country | string |  |  |  | Y |  |
| shipping_postal_code | string |  |  |  | Y |  |
| customer_phone | string |  |  |  | Y |  |
| delivery_location | string |  |  |  | Y |  |
| delivery_note | string |  |  |  | Y |  |
| tracking_number | string |  |  | Y | Y |  |
| selected_partner_id | integer |  |  |  | Y |  |
| selected_service_area_id | integer |  |  |  | Y |  |
| estimated_delivery_min | integer |  |  |  | Y |  |
| estimated_delivery_max | integer |  |  |  | Y |  |
| payment_gateway_code | string |  |  |  | Y |  |
| payment_gateway_fee_amount | numeric |  |  |  | Y |  |
| payment_customer_total_amount | numeric |  |  |  | Y |  |
| payment_gateway_fee_passed_to_customer | numeric |  |  |  | Y |  |
| paid_at | datetime |  |  |  | Y |  |
| country_code | string |  | Y |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |

**Indexes:**

- `ix_orders_orders_updated_by` (updated_by)
- `ix_orders_orders_country_code` (country_code)
- `ix_orders_country_created` (country_code, created_at)
- `ix_orders_status` (status_code)
- UNIQUE `ix_orders_orders_order_number` (order_number)
- `ix_orders_orders_is_deleted` (is_deleted)
- `ix_orders_orders_created_by` (created_by)
- `ix_orders_user_id` (user_id)
- `ix_orders_orders_customer_id` (customer_id)
- `ix_orders_customer_id` (customer_id)
- `ix_orders_orders_user_id` (user_id)
- `ix_orders_orders_id` (id)

**Foreign Keys:**

- `customer_id` → `accounts.users.id`
- `user_id` → `accounts.users.id`
- `country_code` → `country.country_configs.code`

---

### `orders.orders.return_requests`

*Table: `orders.orders.return_requests`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B0313910> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| order_id | integer |  | Y |  |  |  |
| order_item_id | integer |  |  |  | Y |  |
| customer_id | integer |  | Y |  | Y |  |
| intent | string |  |  |  | Y | return |
| reason | string |  |  |  |  |  |
| description | text |  |  |  | Y |  |
| details | text |  |  |  | Y |  |
| supplier_review_state | text |  |  |  | Y |  |
| images | text |  |  |  | Y |  |
| status_code | string |  |  |  | Y | requested |
| refund_amount | numeric |  |  |  | Y |  |
| items | text |  |  |  | Y |  |
| return_window_days | integer |  |  |  | Y | 10 |
| delivered_at | datetime |  |  |  | Y |  |
| return_deadline | datetime |  |  |  | Y |  |
| resolution_notes | text |  |  |  | Y |  |
| country_code | string |  | Y |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_orders_return_requests_created_by` (created_by)
- `ix_orders_return_requests_updated_by` (updated_by)
- `ix_orders_return_requests_order_id` (order_id)
- `ix_orders_return_requests_is_deleted` (is_deleted)
- `ix_orders_return_requests_country_code` (country_code)
- `ix_orders_return_requests_id` (id)
- `ix_return_requests_country_created` (country_code, created_at)
- `ix_orders_return_requests_customer_id` (customer_id)

**Foreign Keys:**

- `order_id` → `orders.orders.id`
- `customer_id` → `accounts.users.id`
- `country_code` → `country.country_configs.code`

---

## PROMOTIONS

*Schema: `promotions` · 9 tables*

### `promotions.promotions.banners`

*Table: `promotions.promotions.banners`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| title | string |  |  |  |  |  |
| subtitle | string |  |  |  | Y |  |
| image_url | string |  |  |  | Y |  |
| link | string |  |  |  | Y |  |
| banner_type | string |  |  |  | Y | hero |
| is_active | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  | Y |  | Y |  |
| sort_order | integer |  |  |  | Y | 0 |
| bg_color | string |  |  |  | Y |  |
| text_color | string |  |  |  | Y |  |
| subtitle_color | string |  |  |  | Y |  |
| btn_bg_color | string |  |  |  | Y |  |
| btn_text_color | string |  |  |  | Y |  |
| badge_text | string |  |  |  | Y |  |
| badge_color | string |  |  |  | Y |  |
| effect | string |  |  |  | Y |  |
| video_url | string |  |  |  | Y |  |
| cta_label | string |  |  |  | Y |  |
| cta_url | string |  |  |  | Y |  |
| starts_at | datetime |  |  |  | Y |  |
| ends_at | datetime |  |  |  | Y |  |
| created_by_id | integer |  | Y |  | Y |  |
| country_code | string |  | Y |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_promotions_banners_id` (id)
- `ix_promotions_banners_is_deleted` (is_deleted)
- `ix_promotions_banners_country_code` (country_code)

**Foreign Keys:**

- `deleted_by_id` → `accounts.users.id`
- `created_by_id` → `accounts.users.id`
- `country_code` → `country.country_configs.code`

---

### `promotions.promotions.bogo_promotions`

*Table: `promotions.promotions.bogo_promotions`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| title | string |  |  |  |  |  |
| description | text |  |  |  | Y |  |
| buy_quantity | integer |  |  |  |  | 1 |
| free_quantity | integer |  |  |  |  | 1 |
| free_discount_pct | integer |  |  |  |  | 100 |
| apply_to | string |  |  |  |  | all |
| target_id | integer |  |  |  | Y |  |
| max_uses_per_customer | integer |  |  |  | Y |  |
| stacking_allowed | boolean |  |  |  | Y | False |
| is_active | boolean |  |  |  | Y | True |
| starts_at | datetime |  |  |  | Y |  |
| ends_at | datetime |  |  |  | Y |  |
| country_code | string |  | Y |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_promotions_bogo_promotions_is_deleted` (is_deleted)
- `ix_promotions_bogo_promotions_id` (id)
- `ix_promotions_bogo_promotions_country_code` (country_code)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `promotions.promotions.coupon_usages`

*Table: `promotions.promotions.coupon_usages`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| coupon_id | integer |  |  |  |  |  |
| user_id | integer |  |  |  |  |  |
| order_id | integer |  |  |  | Y |  |
| country_code | string |  | Y |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B12D1E10> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B12D1D80> |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_promotions_coupon_usages_id` (id)
- `ix_promotions_coupon_usages_country_code` (country_code)
- `ix_promotions_coupon_usages_is_deleted` (is_deleted)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `promotions.promotions.coupons`

*Table: `promotions.promotions.coupons`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| code | string |  |  | Y |  |  |
| discount_type | string |  |  |  | Y | percentage |
| discount_value | numeric |  |  |  | Y |  |
| minimum_order | numeric |  |  |  | Y | 0 |
| maximum_discount | numeric |  |  |  | Y |  |
| usage_limit | integer |  |  |  | Y |  |
| usage_count | integer |  |  |  | Y | 0 |
| starts_at | datetime |  |  |  | Y |  |
| expires_at | datetime |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  | Y | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  | Y |  | Y |  |
| country_code | string |  | Y |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_promotions_coupons_id` (id)
- `ix_promotions_coupons_country_code` (country_code)
- UNIQUE `ix_promotions_coupons_code` (code)

**Foreign Keys:**

- `deleted_by_id` → `accounts.users.id`
- `country_code` → `country.country_configs.code`

---

### `promotions.promotions.flash_sales`

*Table: `promotions.promotions.flash_sales`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| title | string |  |  |  |  |  |
| description | text |  |  |  | Y |  |
| starts_at | datetime |  |  |  |  |  |
| ends_at | datetime |  |  |  |  |  |
| discount_pct | numeric |  |  |  | Y | 0 |
| is_active | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by_id | integer |  |  |  | Y |  |
| country_code | string |  | Y |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_promotions_flash_sales_id` (id)
- `ix_promotions_flash_sales_is_deleted` (is_deleted)
- `ix_promotions_flash_sales_country_code` (country_code)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `promotions.promotions.points_transactions`

*Table: `promotions.promotions.points_transactions`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| points | integer |  |  |  |  |  |
| transaction_type | string |  |  |  |  |  |
| order_id | integer |  |  |  | Y |  |
| source_description | string |  |  |  | Y |  |
| balance_after | integer |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_promotions_points_transactions_country_code` (country_code)
- `ix_promotions_points_transactions_id` (id)
- `ix_promotions_points_transactions_is_deleted` (is_deleted)

**Foreign Keys:**

- `user_id` → `accounts.users.id`

---

### `promotions.promotions.promotion_engine_configs`

*Table: `promotions.promotions.promotion_engine_configs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| country_code | string |  | Y |  | Y |  |
| engine_enabled | boolean |  |  |  | Y | False |
| allow_product_coupons | boolean |  |  |  | Y | True |
| allow_category_coupons | boolean |  |  |  | Y | True |
| allow_order_tier_discounts | boolean |  |  |  | Y | True |
| allow_referral_rewards | boolean |  |  |  | Y | True |
| allow_supplier_promotions | boolean |  |  |  | Y | True |
| allow_global_coupons | boolean |  |  |  | Y | True |
| stacking_mode | string |  |  |  | Y | best_only |
| max_combined_discount_percent | numeric |  |  |  | Y | 50.00 |
| max_combined_discount_amount | numeric |  |  |  | Y | 0.000 |
| show_savings_line_item | boolean |  |  |  | Y | True |
| tier_discount_visible | boolean |  |  |  | Y | True |
| points_per_omr | integer |  |  |  | Y | 1000 |
| referral_referrer_points | integer |  |  |  | Y | 100 |
| referral_referee_points | integer |  |  |  | Y | 100 |
| points_expiry_months | integer |  |  |  | Y | 12 |
| referral_monthly_cap | integer |  |  |  | Y | 20 |
| referral_verification_delay_days | integer |  |  |  | Y | 7 |
| min_points_redeem | integer |  |  |  | Y | 1000 |
| allow_partial_points_redemption | boolean |  |  |  | Y | True |
| updated_by | integer |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B12D2E60> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B12D2DD0> |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_promotions_promotion_engine_configs_id` (id)
- `ix_promotions_promotion_engine_configs_is_deleted` (is_deleted)
- `ix_promotions_promotion_engine_configs_country_code` (country_code)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `promotions.promotions.promotion_ledger_entries`

*Table: `promotions.promotions.promotion_ledger_entries`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| promotion_id | integer |  |  |  | Y |  |
| order_id | integer |  |  |  | Y |  |
| user_id | integer |  | Y |  | Y |  |
| promotion_type | string |  |  |  | Y |  |
| promotion_code | string |  |  |  | Y |  |
| tier_id | integer |  |  |  | Y |  |
| amount | numeric |  |  |  |  |  |
| entry_type | string |  |  |  |  |  |
| discount_amount | numeric |  |  |  |  |  |
| points_awarded | integer |  |  |  | Y | 0 |
| points_redeemed | integer |  |  |  | Y | 0 |
| stacking_flag | integer |  |  |  | Y | 0 |
| source | string |  |  |  | Y |  |
| metadata_json | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_promotions_promotion_ledger_entries_is_deleted` (is_deleted)
- `ix_promotions_promotion_ledger_entries_country_code` (country_code)
- `ix_promotions_promotion_ledger_entries_id` (id)

**Foreign Keys:**

- `user_id` → `accounts.users.id`

---

### `promotions.promotions.user_points`

*Table: `promotions.promotions.user_points`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y | Y |  |  |
| balance | integer |  |  |  |  | 0 |
| lifetime_earned | integer |  |  |  |  | 0 |
| lifetime_redeemed | integer |  |  |  |  | 0 |
| loyalty_tier | string |  |  |  |  | bronze |
| points_expire_at | datetime |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_promotions_user_points_country_code` (country_code)
- `ix_promotions_user_points_id` (id)
- `ix_promotions_user_points_is_deleted` (is_deleted)

**Foreign Keys:**

- `user_id` → `accounts.users.id`

---

## PUBLIC

*Schema: `public` · 2 tables*

### `public.employee_trainings`

*Table: `public.employee_trainings`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| employee_id | integer |  | Y |  |  |  |
| module_id | string |  | Y |  |  |  |
| status | string |  |  |  | Y | assigned |
| score | float |  |  |  | Y |  |
| completed_at | datetime |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_employee_trainings_is_deleted` (is_deleted)
- `ix_employee_trainings_employee_id` (employee_id)
- `ix_employee_trainings_id` (id)

**Foreign Keys:**

- `employee_id` → `hr.employees.id`
- `module_id` → `hr.training_modules.module_id`

---

### `public.payroll_records`

*Table: `public.payroll_records`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| country_code | string |  |  |  |  |  |
| employee_id | integer |  | Y |  | Y |  |
| net_pay | numeric |  |  |  | Y | 0 |
| status | string |  |  |  | Y | pending |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_payroll_records_is_deleted` (is_deleted)
- `ix_payroll_records_country_code` (country_code)
- `ix_payroll_records_id` (id)

**Foreign Keys:**

- `employee_id` → `hr.employees.id`

---

## SECURITY

*Schema: `security` · 21 tables*

### `security.security.alert_escalation_rules`

*Table: `security.security.alert_escalation_rules`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| alert_type | string |  |  |  |  |  |
| severity | string |  |  |  | Y | medium |
| threshold_value | numeric |  |  |  | Y |  |
| current_tier | integer |  |  |  | Y | 0 |
| is_active | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  |  | False |
| country_code | string |  | Y |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_security_alert_escalation_rules_id` (id)
- `ix_security_alert_escalation_rules_is_deleted` (is_deleted)
- `ix_security_alert_escalation_rules_country_code` (country_code)

**Foreign Keys:**

- `country_code` → `country.country_configs.code`

---

### `security.security.credit_card_bins`

*Table: `security.security.credit_card_bins`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| bin | string |  |  | Y |  |  |
| brand | string |  |  |  | Y |  |
| bank | string |  |  |  | Y |  |
| country | string |  |  |  | Y |  |
| is_blacklisted | boolean |  |  |  | Y | False |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B13A7130> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B13A71C0> |

**Indexes:**

- `ix_security_credit_card_bins_is_deleted` (is_deleted)
- `ix_security_credit_card_bins_id` (id)

---

### `security.security.device_fingerprints`

*Table: `security.security.device_fingerprints`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  | Y |  |
| fingerprint_hash | string |  |  |  |  |  |
| user_agent | string |  |  |  | Y |  |
| ip_addresses | text |  |  |  | Y |  |
| is_trusted | boolean |  |  |  | Y | False |
| is_blocked | boolean |  |  |  | Y | False |
| risk_score | integer |  |  |  | Y | 0 |
| headless_attempts | integer |  |  |  | Y | 0 |
| account_count | integer |  |  |  | Y | 0 |
| first_seen_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B13A6C20> |
| last_seen_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B13A6B90> |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_security_device_fingerprints_is_deleted` (is_deleted)
- `ix_device_fingerprint` (fingerprint_hash)
- `ix_security_device_fingerprints_fingerprint_hash` (fingerprint_hash)
- `ix_security_device_fingerprints_id` (id)

**Foreign Keys:**

- `user_id` → `accounts.users.id`

---

### `security.security.dlp_violations`

*Table: `security.security.dlp_violations`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| violation_type | string |  |  |  |  |  |
| severity | string |  |  |  | Y | medium |
| sender_id | integer |  | Y |  | Y |  |
| recipient_email | string |  |  |  | Y |  |
| detected_content | text |  |  |  | Y |  |
| action_taken | string |  |  |  | Y | blocked |
| status_code | string |  |  |  | Y | pending |
| reviewed_by_id | integer |  | Y |  | Y |  |
| reviewed_at | datetime |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B14665F0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B1466560> |

**Indexes:**

- `ix_security_dlp_violations_id` (id)
- `ix_dlp_status` (status_code)
- `ix_dlp_created_at` (created_at)
- `ix_security_dlp_violations_is_deleted` (is_deleted)

**Foreign Keys:**

- `sender_id` → `accounts.users.id`
- `reviewed_by_id` → `accounts.users.id`

---

### `security.security.document_verifications`

*Table: `security.security.document_verifications`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| pipeline_id | integer |  | Y |  |  |  |
| document_type | string |  |  |  |  |  |
| document_data | json |  |  |  | Y |  |
| status | string |  |  |  | Y | pending |
| verified_at | datetime |  |  |  | Y |  |
| verifier_id | integer |  | Y |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| country_code | string |  | Y |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_security_document_verifications_id` (id)
- `ix_security_document_verifications_country_code` (country_code)
- `ix_security_document_verifications_is_deleted` (is_deleted)

**Foreign Keys:**

- `pipeline_id` → `hr.onboarding_pipelines.id`
- `verifier_id` → `accounts.users.id`
- `country_code` → `country.country_configs.code`

---

### `security.security.fraud_alerts`

*Table: `security.security.fraud_alerts`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| alert_type | string |  |  |  |  |  |
| entity_type | string |  |  |  |  |  |
| entity_id | integer |  |  |  |  |  |
| fraud_score | numeric |  |  |  |  |  |
| triggered_rules | text |  |  |  | Y |  |
| priority | string |  |  |  | Y | medium |
| details | text |  |  |  | Y |  |
| is_resolved | boolean |  |  |  | Y | False |
| resolved_at | datetime |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B1464310> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_security_fraud_alerts_id` (id)
- `ix_security_fraud_alerts_is_deleted` (is_deleted)
- `ix_security_fraud_alerts_country_code` (country_code)

---

### `security.security.fraud_blacklists`

*Table: `security.security.fraud_blacklists`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| identifier_type | string |  |  |  |  |  |
| identifier_value | string |  |  |  |  |  |
| identifier_value_hash | string |  |  |  | Y |  |
| reason | string |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| status_code | string |  |  |  | Y | active |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B13A53F0> |
| is_deleted | boolean |  |  |  |  | False |
| expires_at | datetime |  |  |  | Y |  |

**Indexes:**

- `ix_security_fraud_blacklists_is_deleted` (is_deleted)
- `ix_security_fraud_blacklists_id` (id)

---

### `security.security.fraud_case_assignments`

*Table: `security.security.fraud_case_assignments`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| case_id | integer |  | Y |  |  |  |
| assigned_to_id | integer |  | Y |  |  |  |
| assigned_by_id | integer |  | Y |  | Y |  |
| role_at_assignment | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B1465F30> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B1465FC0> |

**Indexes:**

- `ix_security_fraud_case_assignments_is_deleted` (is_deleted)
- `ix_security_fraud_case_assignments_id` (id)

**Foreign Keys:**

- `case_id` → `security.fraud_cases.id`
- `assigned_to_id` → `accounts.users.id`
- `assigned_by_id` → `accounts.users.id`

---

### `security.security.fraud_cases`

*Table: `security.security.fraud_cases`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| case_number | string |  |  | Y |  |  |
| title | string |  |  |  |  |  |
| description | text |  |  |  | Y |  |
| fraud_score | integer |  |  |  |  |  |
| priority | string |  |  |  | Y | medium |
| status_code | string |  |  |  | Y | open |
| entity_type | string |  |  |  | Y |  |
| entity_id | integer |  |  |  | Y |  |
| assigned_to_id | integer |  | Y |  | Y |  |
| created_by_id | integer |  | Y |  | Y |  |
| resolved_at | datetime |  |  |  | Y |  |
| resolution_notes | text |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B1465990> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B1465900> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_fraud_case_status` (status_code)
- `ix_security_fraud_cases_country_code` (country_code)
- `ix_security_fraud_cases_is_deleted` (is_deleted)
- `ix_security_fraud_cases_id` (id)
- `ix_fraud_case_priority` (priority)

**Foreign Keys:**

- `assigned_to_id` → `accounts.users.id`
- `created_by_id` → `accounts.users.id`

---

### `security.security.fraud_events`

*Table: `security.security.fraud_events`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  | Y |  |
| order_id | integer |  | Y |  | Y |  |
| event_type | string |  |  |  |  |  |
| ip_address | string |  |  |  | Y |  |
| device_hash | string |  |  |  | Y |  |
| session_id | string |  |  |  | Y |  |
| fraud_score | numeric |  |  |  |  |  |
| triggered_rules | text |  |  |  | Y |  |
| details | json |  |  |  | Y |  |
| is_flagged | boolean |  |  |  | Y | False |
| status_code | string |  |  |  | Y | logged |
| reviewed_by_id | integer |  | Y |  | Y |  |
| reviewed_at | datetime |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B13A4EE0> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_fraud_event_user` (user_id)
- `ix_security_fraud_events_id` (id)
- `ix_security_fraud_events_country_code` (country_code)
- `ix_fraud_event_score` (fraud_score)
- `ix_fraud_event_type` (event_type)
- `ix_security_fraud_events_is_deleted` (is_deleted)

**Foreign Keys:**

- `user_id` → `accounts.users.id`
- `order_id` → `orders.orders.id`
- `reviewed_by_id` → `accounts.users.id`

---

### `security.security.fraud_rules`

*Table: `security.security.fraud_rules`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| rule_key | string |  |  | Y |  |  |
| name | string |  |  |  |  |  |
| description | text |  |  |  | Y |  |
| weight | integer |  |  |  | Y | 10 |
| condition_json | text |  |  |  | Y |  |
| action | string |  |  |  | Y | alert |
| is_active | boolean |  |  |  | Y | True |
| is_global | boolean |  |  |  | Y | True |
| country_code | string |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B13A5990> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B13A5870> |

**Indexes:**

- `ix_security_fraud_rules_is_deleted` (is_deleted)
- `ix_fraud_rule_active` (is_active)
- `ix_security_fraud_rules_id` (id)

---

### `security.security.fraud_scoring_logs`

*Table: `security.security.fraud_scoring_logs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| event_type | string |  |  |  |  |  |
| user_id | integer |  | Y |  | Y |  |
| order_id | integer |  | Y |  | Y |  |
| ip_address | string |  |  |  | Y |  |
| device_hash | string |  |  |  | Y |  |
| session_id | string |  |  |  | Y |  |
| raw_score | integer |  |  |  |  |  |
| triggered_rules | json |  |  |  | Y |  |
| metadata_json | json |  |  |  | Y |  |
| action_taken | string |  |  |  | Y | logged |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B1465480> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_scoring_score` (raw_score)
- `ix_security_fraud_scoring_logs_is_deleted` (is_deleted)
- `ix_security_fraud_scoring_logs_id` (id)
- `ix_scoring_event` (event_type, created_at)
- `ix_security_fraud_scoring_logs_country_code` (country_code)

**Foreign Keys:**

- `user_id` → `accounts.users.id`
- `order_id` → `orders.orders.id`

---

### `security.security.fraud_velocity_counters`

*Table: `security.security.fraud_velocity_counters`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| key | string |  |  |  |  |  |
| count | integer |  |  |  | Y | 1 |
| window_start | datetime |  |  |  | Y | <function utcnow at 0x000001C7B1464D30> |
| window_end | datetime |  |  |  |  |  |
| entity_type | string |  |  |  | Y |  |
| entity_id | integer |  |  |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B1464E50> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B1464DC0> |

**Indexes:**

- `ix_security_fraud_velocity_counters_key` (key)
- `ix_security_fraud_velocity_counters_is_deleted` (is_deleted)
- `ix_velocity_key` (key, window_start)
- `ix_security_fraud_velocity_counters_id` (id)

---

### `security.security.ip_account_linkages`

*Table: `security.security.ip_account_linkages`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| ip_address | string |  |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| device_fingerprint | string |  |  |  | Y |  |
| session_id | string |  |  |  | Y |  |
| interaction_count | integer |  |  |  | Y | 1 |
| is_suspicious | boolean |  |  |  | Y | False |
| last_seen | datetime |  |  |  | Y | <function utcnow at 0x000001C7B1464820> |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_security_ip_account_linkages_id` (id)
- `ix_security_ip_account_linkages_ip_address` (ip_address)
- `ix_security_ip_account_linkages_is_deleted` (is_deleted)

**Foreign Keys:**

- `user_id` → `accounts.users.id`

---

### `security.security.ip_reputations`

*Table: `security.security.ip_reputations`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| ip_address | string |  |  |  |  |  |
| reputation_score | numeric |  |  |  | Y | 0 |
| is_blocked | boolean |  |  |  | Y | False |
| is_proxy | boolean |  |  |  | Y | False |
| is_tor | boolean |  |  |  | Y | False |
| is_vpn | boolean |  |  |  | Y | False |
| is_hosting | boolean |  |  |  | Y | False |
| asn | string |  |  |  | Y |  |
| country_code | string |  |  |  | Y |  |
| last_seen_at | datetime |  |  |  | Y |  |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B13A65F0> |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B13A6680> |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_ip_reputation_ip` (ip_address)
- `ix_security_ip_reputations_ip_address` (ip_address)
- `ix_security_ip_reputations_is_deleted` (is_deleted)
- `ix_security_ip_reputations_id` (id)

---

### `security.security.kyc_verifications`

*Table: `security.security.kyc_verifications`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| status | string |  |  |  | Y | pending |
| provider | string |  |  |  | Y |  |
| verification_data | json |  |  |  | Y |  |
| document_types | json |  |  |  | Y |  |
| submitted_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7AFF292D0> |
| reviewed_at | datetime |  |  |  | Y |  |
| reviewer_id | integer |  | Y |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| country_code | string |  | Y |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_security_kyc_verifications_id` (id)
- `ix_security_kyc_verifications_country_code` (country_code)
- `ix_security_kyc_verifications_user_id` (user_id)
- `ix_security_kyc_verifications_is_deleted` (is_deleted)

**Foreign Keys:**

- `user_id` → `accounts.users.id`
- `reviewer_id` → `accounts.users.id`
- `country_code` → `country.country_configs.code`

---

### `security.security.logistics_fraud_indicators`

*Table: `security.security.logistics_fraud_indicators`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| partner_id | integer |  | Y |  |  |  |
| indicator_type | string |  |  |  |  |  |
| value | string |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B13A7E20> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_security_logistics_fraud_indicators_id` (id)
- `ix_security_logistics_fraud_indicators_country_code` (country_code)
- `ix_security_logistics_fraud_indicators_is_deleted` (is_deleted)

**Foreign Keys:**

- `partner_id` → `logistics.logistics_partners.id`

---

### `security.security.manual_review_queues`

*Table: `security.security.manual_review_queues`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| entity_type | string |  |  |  |  |  |
| entity_id | integer |  |  |  |  |  |
| fraud_score | integer |  |  |  |  |  |
| triggered_rules | text |  |  |  | Y |  |
| reason | string |  |  |  |  |  |
| priority | string |  |  |  | Y | medium |
| assigned_to_id | integer |  | Y |  | Y |  |
| admin_notes | text |  |  |  | Y |  |
| status_code | string |  |  |  | Y | queued |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B13A5F30> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B13A5FC0> |

**Indexes:**

- `ix_manual_review_status` (status_code)
- `ix_security_manual_review_queues_id` (id)
- `ix_manual_review_priority` (priority)
- `ix_security_manual_review_queues_is_deleted` (is_deleted)

**Foreign Keys:**

- `assigned_to_id` → `accounts.users.id`

---

### `security.security.meeting_action_items`

*Table: `security.security.meeting_action_items`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| meeting_id | integer |  | Y |  |  |  |
| entity_type | string |  |  |  | Y |  |
| entity_id | integer |  |  |  | Y |  |
| action | string |  |  |  |  |  |
| metadata_json | json |  |  |  | Y |  |
| status_code | string |  |  |  | Y | pending |
| assigned_to_id | integer |  | Y |  | Y |  |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B1467250> |
| due_date | datetime |  |  |  | Y |  |

**Indexes:**

- `ix_security_meeting_action_items_id` (id)
- `ix_action_item_status` (status_code)
- `ix_security_meeting_action_items_is_deleted` (is_deleted)
- `ix_action_item_meeting` (meeting_id)

**Foreign Keys:**

- `meeting_id` → `security.meeting_transcripts.id`
- `assigned_to_id` → `accounts.users.id`

---

### `security.security.meeting_transcripts`

*Table: `security.security.meeting_transcripts`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| room_id | string |  |  |  |  |  |
| language | string |  |  |  | Y | en |
| segments | json |  |  |  | Y |  |
| action_items | json |  |  |  | Y |  |
| summary | text |  |  |  | Y |  |
| word_count | integer |  |  |  | Y | 0 |
| duration_seconds | integer |  |  |  | Y | 0 |
| is_deleted | boolean |  |  |  |  | False |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B1466C20> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B1466B90> |

**Indexes:**

- `ix_security_meeting_transcripts_is_deleted` (is_deleted)
- `ix_transcript_room` (room_id)
- `ix_security_meeting_transcripts_id` (id)

---

### `security.security.return_abuse_patterns`

*Table: `security.security.return_abuse_patterns`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| abuse_type | string |  |  |  |  |  |
| occurrence_count | integer |  |  |  | Y | 1 |
| first_occurrence | datetime |  |  |  | Y | <function utcnow at 0x000001C7B13A77F0> |
| last_occurrence | datetime |  |  |  | Y | <function utcnow at 0x000001C7B13A7760> |
| is_blocked | boolean |  |  |  | Y | False |
| is_deleted | boolean |  |  |  |  | False |

**Indexes:**

- `ix_security_return_abuse_patterns_id` (id)
- `ix_security_return_abuse_patterns_is_deleted` (is_deleted)

**Foreign Keys:**

- `user_id` → `accounts.users.id`

---

## SUPPLIERS

*Schema: `suppliers` · 8 tables*

### `suppliers.suppliers.supplier_badge_billing_histories`

*Table: `suppliers.suppliers.supplier_badge_billing_histories`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B09E05E0> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| supplier_id | integer |  | Y |  |  |  |
| badge_id | integer |  | Y |  | Y |  |
| catalog_id | integer |  | Y |  | Y |  |
| billing_reference | string |  |  | Y | Y |  |
| charge_type | string |  |  |  | Y |  |
| amount | numeric |  |  |  |  | 0 |
| currency | string |  |  |  |  | USD |
| status | string |  |  |  |  | pending |
| period_start | datetime |  |  |  | Y |  |
| period_end | datetime |  |  |  | Y |  |
| due_at | datetime |  |  |  | Y |  |
| billed_at | datetime |  |  |  | Y |  |
| paid_at | datetime |  |  |  | Y |  |
| payment_method | string |  |  |  | Y |  |
| notes | text |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B09E0670> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B09E0700> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_suppliers_supplier_badge_billing_histories_supplier_id` (supplier_id)
- `ix_suppliers_supplier_badge_billing_histories_badge_id` (badge_id)
- `ix_supplier_badge_billing_country_created` (country_code, created_at)
- `ix_suppliers_supplier_badge_billing_histories_updated_by` (updated_by)
- `ix_suppliers_supplier_badge_billing_histories_id` (id)
- `ix_suppliers_supplier_badge_billing_histories_is_deleted` (is_deleted)
- `ix_suppliers_supplier_badge_billing_histories_created_by` (created_by)
- `ix_suppliers_supplier_badge_billing_histories_catalog_id` (catalog_id)
- `ix_suppliers_supplier_badge_billing_histories_country_code` (country_code)

**Foreign Keys:**

- `supplier_id` → `suppliers.supplier_profiles.id`
- `badge_id` → `suppliers.supplier_badges.id`
- `catalog_id` → `suppliers.supplier_badge_catalogs.id`

---

### `suppliers.suppliers.supplier_badge_catalogs`

*Table: `suppliers.suppliers.supplier_badge_catalogs`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B08EF370> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| name | string |  |  | Y |  |  |
| badge_level | string |  |  |  |  | bronze |
| description | text |  |  |  | Y |  |
| benefits | json |  |  |  | Y |  |
| price | numeric |  |  |  |  | 0 |
| currency | string |  |  |  |  | USD |
| validity_days | integer |  |  |  | Y |  |
| is_active | boolean |  |  |  |  | True |
| credibility_weight | float |  |  |  |  | 10.0 |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B08EF7F0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B08EF880> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_supplier_badge_catalog_country_created` (country_code, created_at)
- `ix_suppliers_supplier_badge_catalogs_created_by` (created_by)
- `ix_suppliers_supplier_badge_catalogs_updated_by` (updated_by)
- `ix_suppliers_supplier_badge_catalogs_country_code` (country_code)
- `ix_suppliers_supplier_badge_catalogs_is_deleted` (is_deleted)
- `ix_supplier_badge_catalog_benefits_gin` (benefits)
- `ix_suppliers_supplier_badge_catalogs_id` (id)

---

### `suppliers.suppliers.supplier_badges`

*Table: `suppliers.suppliers.supplier_badges`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B08EFE20> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| supplier_id | integer |  | Y |  |  |  |
| catalog_id | integer |  | Y |  | Y |  |
| badge_name | string |  |  |  |  |  |
| badge_level | string |  |  |  |  | bronze |
| status | string |  |  |  |  | active |
| issued_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B08EFF40> |
| expires_at | datetime |  |  |  | Y |  |
| assigned_by | integer |  |  |  | Y |  |
| billing_reference | string |  |  |  | Y |  |
| credibility_weight | float |  |  |  |  | 10.0 |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B08EFEB0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B09E0040> |
| country_code | string |  |  |  | Y |  |

**Indexes:**

- `ix_suppliers_supplier_badges_is_deleted` (is_deleted)
- `ix_suppliers_supplier_badges_id` (id)
- `ix_suppliers_supplier_badges_catalog_id` (catalog_id)
- `ix_suppliers_supplier_badges_assigned_by` (assigned_by)
- `ix_suppliers_supplier_badges_created_by` (created_by)
- `ix_suppliers_supplier_badges_updated_by` (updated_by)
- `ix_suppliers_supplier_badges_supplier_id` (supplier_id)
- `ix_supplier_badges_country_created` (country_code, created_at)
- `ix_suppliers_supplier_badges_country_code` (country_code)

**Foreign Keys:**

- `supplier_id` → `suppliers.supplier_profiles.id`
- `catalog_id` → `suppliers.supplier_badge_catalogs.id`

---

### `suppliers.suppliers.supplier_disputes`

*Table: `suppliers.suppliers.supplier_disputes`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| supplier_id | integer |  | Y |  | Y |  |
| order_id | integer |  |  |  | Y |  |
| reason | text |  |  |  | Y |  |
| status | string |  |  |  | Y | open |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | now() |

**Indexes:**

- `ix_suppliers_supplier_disputes_id` (id)
- `ix_suppliers_supplier_disputes_country_code` (country_code)
- `ix_suppliers_supplier_disputes_supplier_id` (supplier_id)
- `ix_suppliers_supplier_disputes_order_id` (order_id)

**Foreign Keys:**

- `supplier_id` → `accounts.users.id`

---

### `suppliers.suppliers.supplier_documents`

*Table: `suppliers.suppliers.supplier_documents`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B08EE5F0> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| supplier_id | integer |  | Y |  |  |  |
| doc_type | string |  |  |  |  |  |
| document_name | string |  |  |  | Y |  |
| file_url | string |  |  |  |  |  |
| status | string |  |  |  | Y | pending |
| expires_at | datetime |  |  |  | Y |  |
| review_note | text |  |  |  | Y |  |
| reviewed_by | integer |  |  |  | Y |  |
| reviewed_at | datetime |  |  |  | Y |  |
| verified | boolean |  |  |  | Y | False |
| verified_by | integer |  |  |  | Y |  |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B08EEB00> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B08EEA70> |
| country_code | string |  |  |  |  |  |

**Indexes:**

- `ix_suppliers_supplier_documents_supplier_id` (supplier_id)
- `ix_suppliers_supplier_documents_is_deleted` (is_deleted)
- `ix_suppliers_supplier_documents_updated_by` (updated_by)
- `ix_suppliers_supplier_documents_created_by` (created_by)
- `ix_suppliers_supplier_documents_id` (id)
- `ix_suppliers_supplier_documents_country_code` (country_code)

**Foreign Keys:**

- `supplier_id` → `suppliers.supplier_profiles.id`

---

### `suppliers.suppliers.supplier_fraud_indicators`

*Table: `suppliers.suppliers.supplier_fraud_indicators`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| id | integer | Y |  |  |  |  |
| supplier_id | integer |  | Y |  |  |  |
| indicator_type | string |  |  |  |  |  |
| value | string |  |  |  | Y |  |
| is_active | boolean |  |  |  | Y | True |
| is_deleted | boolean |  |  |  |  | False |
| country_code | string |  |  |  | Y |  |
| created_at | datetime |  |  |  |  | now() |
| updated_at | datetime |  |  |  |  | now() |

**Indexes:**

- `ix_suppliers_supplier_fraud_indicators_is_deleted` (is_deleted)
- `ix_suppliers_supplier_fraud_indicators_id` (id)
- `ix_suppliers_supplier_fraud_indicators_country_code` (country_code)

**Foreign Keys:**

- `supplier_id` → `accounts.users.id`

---

### `suppliers.suppliers.supplier_notification_preferences`

*Table: `suppliers.suppliers.supplier_notification_preferences`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B08EECB0> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| supplier_id | integer |  | Y |  |  |  |
| notify_new_order | boolean |  |  |  | Y | True |
| notify_low_stock | boolean |  |  |  | Y | True |
| notify_payout_processed | boolean |  |  |  | Y | True |
| notify_doc_expiry | boolean |  |  |  | Y | True |
| notify_return_updates | boolean |  |  |  | Y | True |
| notify_dispute_updates | boolean |  |  |  | Y | True |
| in_app_enabled | boolean |  |  |  | Y | True |
| email_enabled | boolean |  |  |  | Y | True |
| push_enabled | boolean |  |  |  | Y | True |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B08EF1C0> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B08EF130> |
| country_code | string |  |  |  |  |  |

**Indexes:**

- `ix_suppliers_supplier_notification_preferences_supplier_id` (supplier_id)
- `ix_supplier_notification_preferences_country_created` (country_code, created_at)
- `ix_suppliers_supplier_notification_preferences_is_deleted` (is_deleted)
- `ix_suppliers_supplier_notification_preferences_created_by` (created_by)
- `ix_suppliers_supplier_notification_preferences_country_code` (country_code)
- `ix_suppliers_supplier_notification_preferences_updated_by` (updated_by)
- `ix_suppliers_supplier_notification_preferences_id` (id)

**Foreign Keys:**

- `supplier_id` → `suppliers.supplier_profiles.id`

---

### `suppliers.suppliers.supplier_profiles`

*Table: `suppliers.suppliers.supplier_profiles`*

| Column | Type | PK | FK | Unique | Nullable | Default |
|--------|------|----|----|--------|----------|---------|
| uuid | guid |  |  | Y | Y | <function uuid4 at 0x000001C7B08EE170> |
| version | integer |  |  |  |  | 1 |
| is_deleted | boolean |  |  |  |  | False |
| deleted_at | datetime |  |  |  | Y |  |
| deleted_by | integer |  |  |  | Y |  |
| created_by | integer |  |  |  | Y |  |
| updated_by | integer |  |  |  | Y |  |
| id | integer | Y |  |  |  |  |
| user_id | integer |  | Y |  |  |  |
| business_name | string |  |  |  |  |  |
| country_code | string |  |  |  | Y |  |
| address | string |  |  |  | Y |  |
| website | string |  |  |  | Y |  |
| bio | text |  |  |  | Y |  |
| about_us | text |  |  |  | Y |  |
| business_type | string |  |  |  | Y |  |
| verified_documents | text |  |  |  | Y |  |
| is_verified | boolean |  |  |  | Y | False |
| verification_status | string |  |  |  | Y | unverified |
| credibility_score | numeric |  |  |  | Y | 0 |
| created_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B08EE440> |
| updated_at | datetime |  |  |  | Y | <function utcnow at 0x000001C7B08EE200> |

**Indexes:**

- `ix_suppliers_supplier_profiles_country_code` (country_code)
- `ix_suppliers_supplier_profiles_created_by` (created_by)
- `ix_suppliers_supplier_profiles_user_id` (user_id)
- `ix_suppliers_supplier_profiles_is_deleted` (is_deleted)
- `ix_suppliers_supplier_profiles_updated_by` (updated_by)
- `ix_suppliers_supplier_profiles_id` (id)

**Foreign Keys:**

- `user_id` → `accounts.users.id`

---
