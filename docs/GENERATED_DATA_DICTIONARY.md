# ZOZI Database Data Dictionary

**Generated:** 2026-07-31T18:42:48.057152
**Total Tables:** 327

## Schema: core

Tables: 14

### users

**Primary Key:** id

**Foreign Keys:**
- `referred_by_user_id` → `core.users.id`
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `email` | `VARCHAR` | Yes | No | No | Yes |
| `username` | `VARCHAR` | Yes | No | No | Yes |
| `full_name` | `VARCHAR(160)` | Yes | No | No | No |
| `hashed_password` | `VARCHAR` | Yes | No | No | No |
| `role` | `VARCHAR` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `phone` | `VARCHAR` | Yes | No | No | No |
| `profile_image` | `VARCHAR` | Yes | No | No | No |
| `preferred_language` | `VARCHAR` | Yes | No | No | No |
| `preferred_currency` | `VARCHAR(10)` | Yes | No | No | No |
| `preferred_country` | `VARCHAR(10)` | Yes | No | No | No |
| `email_verified` | `BOOLEAN` | Yes | No | No | No |
| `last_login` | `DATETIME` | Yes | No | No | No |
| `is_verified` | `BOOLEAN` | Yes | No | No | No |
| `staff_role_label` | `VARCHAR(120)` | Yes | No | No | No |
| `staff_title` | `VARCHAR(120)` | Yes | No | No | No |
| `staff_department` | `VARCHAR(120)` | Yes | No | No | No |
| `staff_country_codes` | `TEXT` | Yes | No | No | No |
| `staff_permissions` | `TEXT` | Yes | No | No | No |
| `staff_area_of_operation` | `TEXT` | Yes | No | No | No |
| `staff_hire_date` | `DATETIME` | Yes | No | No | No |
| `staff_experience_level` | `VARCHAR(50)` | Yes | No | No | No |
| `staff_performance_summary` | `TEXT` | Yes | No | No | No |
| `staff_assigned_tasks` | `JSON` | Yes | No | No | No |
| `staff_assigned_projects` | `JSON` | Yes | No | No | No |
| `staff_notes` | `TEXT` | Yes | No | No | No |
| `is_deleted` | `BOOLEAN` | Yes | No | No | No |
| `deleted_at` | `DATETIME` | Yes | No | No | No |
| `referral_code` | `VARCHAR` | Yes | No | No | Yes |
| `referred_by_user_id` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `referral_points` | `INTEGER` | Yes | No | No | No |
| `sharing_points` | `INTEGER` | Yes | No | No | No |
| `totp_enabled` | `BOOLEAN` | Yes | No | No | No |
| `totp_secret` | `VARCHAR` | Yes | No | No | No |
| `last_seen_at` | `DATETIME` | Yes | No | No | No |
| `is_current` | `BOOLEAN` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `address_book` | `TEXT` | Yes | No | No | No |

### user_login_history

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `ip_address` | `VARCHAR` | No | No | No | No |
| `user_agent` | `VARCHAR` | Yes | No | No | No |
| `timestamp` | `DATETIME` | Yes | No | No | No |
| `success` | `BOOLEAN` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### user_devices

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `device_id` | `VARCHAR(255)` | No | No | No | No |
| `device_type` | `VARCHAR(50)` | Yes | No | No | No |
| `last_seen_at` | `DATETIME` | Yes | No | No | No |
| `is_current` | `BOOLEAN` | Yes | No | No | No |
| `is_trusted` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### password_reset_tokens

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | Yes | No | Yes | No |
| `token` | `VARCHAR` | Yes | No | No | Yes |
| `expires_at` | `DATETIME` | No | No | No | No |
| `used` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### email_verification_tokens

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | Yes | No | Yes | No |
| `token` | `VARCHAR` | Yes | No | No | Yes |
| `expires_at` | `DATETIME` | No | No | No | No |
| `used` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### revoked_tokens

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `jti` | `VARCHAR(64)` | No | No | No | Yes |
| `user_id` | `INTEGER` | Yes | No | Yes | No |
| `expires_at` | `DATETIME` | No | No | No | No |
| `revoked_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### role_permission_settings

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `role` | `VARCHAR` | No | No | No | No |
| `permissions_json` | `JSON` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### api_keys

**Primary Key:** id

**Foreign Keys:**
- `created_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `name` | `VARCHAR` | No | No | No | No |
| `key_hash` | `VARCHAR` | No | No | No | No |
| `permissions` | `JSON` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `expires_at` | `DATETIME` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### user_browsing_history

**Primary Key:** id

**Foreign Keys:**
- `product_id` → `commerce.products.id`
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `product_id` | `INTEGER` | No | No | Yes | No |
| `viewed_at` | `DATETIME` | Yes | No | No | No |

### permission_categories

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `name` | `VARCHAR(100)` | No | No | No | Yes |
| `slug` | `VARCHAR(100)` | No | No | No | Yes |
| `description` | `TEXT` | Yes | No | No | No |
| `icon` | `VARCHAR(50)` | Yes | No | No | No |
| `sort_order` | `INTEGER` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | No | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### permissions

**Primary Key:** id

**Foreign Keys:**
- `category_id` → `core.permission_categories.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `category_id` | `INTEGER` | No | No | Yes | No |
| `name` | `VARCHAR(150)` | No | No | No | No |
| `slug` | `VARCHAR(150)` | No | No | No | Yes |
| `description` | `TEXT` | Yes | No | No | No |
| `scope` | `VARCHAR(20)` | No | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | No | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### role_permission_assignments

**Primary Key:** id

**Foreign Keys:**
- `permission_id` → `core.permissions.id`
- `granted_by` → `core.users.id`
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `role_name` | `VARCHAR(80)` | No | No | No | No |
| `permission_id` | `INTEGER` | No | No | Yes | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `granted_by` | `INTEGER` | Yes | No | Yes | No |
| `is_granted` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### user_permission_overrides

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`
- `permission_id` → `core.permissions.id`
- `granted_by` → `core.users.id`
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `permission_id` | `INTEGER` | No | No | Yes | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `is_granted` | `BOOLEAN` | Yes | No | No | No |
| `granted_by` | `INTEGER` | Yes | No | Yes | No |
| `expires_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### permission_audit_log

**Primary Key:** id

**Foreign Keys:**
- `target_user_id` → `core.users.id`
- `permission_id` → `core.permissions.id`
- `actor_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `actor_id` | `INTEGER` | No | No | Yes | No |
| `action` | `VARCHAR(50)` | No | No | No | No |
| `target_user_id` | `INTEGER` | Yes | No | Yes | No |
| `target_role` | `VARCHAR(80)` | Yes | No | No | No |
| `permission_id` | `INTEGER` | Yes | No | Yes | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `details` | `TEXT` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

## Schema: customer

Tables: 15

### referrals

**Primary Key:** id

**Foreign Keys:**
- `referrer_id` → `core.users.id`
- `referred_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `referrer_id` | `INTEGER` | No | No | Yes | No |
| `referred_id` | `INTEGER` | No | No | Yes | Yes |
| `status` | `VARCHAR` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### referral_point_events

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`
- `referred_user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `event_type` | `VARCHAR(40)` | No | No | No | No |
| `points` | `INTEGER` | No | No | No | No |
| `referred_user_id` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### wishlist_items

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`
- `product_id` → `commerce.products.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `product_id` | `INTEGER` | No | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### wishlists

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`
- `product_id` → `commerce.products.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `product_id` | `INTEGER` | No | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### addresses

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `label` | `VARCHAR` | Yes | No | No | No |
| `full_name` | `VARCHAR` | No | No | No | No |
| `phone` | `VARCHAR` | Yes | No | No | No |
| `address_line1` | `VARCHAR` | No | No | No | No |
| `address_line2` | `VARCHAR` | Yes | No | No | No |
| `city` | `VARCHAR` | No | No | No | No |
| `state` | `VARCHAR` | Yes | No | No | No |
| `postal_code` | `VARCHAR` | Yes | No | No | No |
| `country` | `VARCHAR` | Yes | No | No | No |
| `is_default` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### system_health_events

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `service` | `VARCHAR(100)` | Yes | No | No | No |
| `metric_name` | `VARCHAR(100)` | No | No | No | No |
| `metric_value` | `NUMERIC(12, 4)` | No | No | No | No |
| `severity` | `VARCHAR(20)` | Yes | No | No | No |
| `message` | `TEXT` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### user_sessions

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `session_token` | `VARCHAR(255)` | No | No | No | Yes |
| `ip_address` | `VARCHAR(45)` | Yes | No | No | No |
| `user_agent` | `VARCHAR(500)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `last_activity` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### news_articles

**Primary Key:** id

**Foreign Keys:**
- `source_id` → `communication.news_sources.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `source_id` | `INTEGER` | Yes | No | Yes | No |
| `external_id` | `VARCHAR(255)` | Yes | No | No | No |
| `content_hash` | `VARCHAR(64)` | Yes | No | No | No |
| `title` | `VARCHAR(300)` | No | No | No | No |
| `summary` | `TEXT` | Yes | No | No | No |
| `content` | `TEXT` | Yes | No | No | No |
| `url` | `VARCHAR(500)` | Yes | No | No | No |
| `image_url` | `VARCHAR(500)` | Yes | No | No | No |
| `published_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `ai_sentiment` | `VARCHAR(20)` | Yes | No | No | No |
| `ai_tags` | `JSON` | Yes | No | No | No |
| `is_published` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### entity_chat_threads

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `entity_type` | `VARCHAR` | No | No | No | No |
| `entity_id` | `INTEGER` | No | No | No | No |
| `title` | `VARCHAR(200)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### video_rooms

**Primary Key:** id

**Foreign Keys:**
- `created_by` → `core.users.id`
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `room_id` | `VARCHAR(64)` | No | No | No | Yes |
| `room_uuid` | `VARCHAR(32)` | Yes | No | No | Yes |
| `name` | `VARCHAR(200)` | No | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `created_by` | `INTEGER` | Yes | No | Yes | No |
| `is_boardroom` | `BOOLEAN` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `max_participants` | `INTEGER` | Yes | No | No | No |
| `recording_enabled` | `BOOLEAN` | Yes | No | No | No |
| `watermark_enabled` | `BOOLEAN` | Yes | No | No | No |
| `transcription_enabled` | `BOOLEAN` | Yes | No | No | No |
| `started_at` | `DATETIME` | Yes | No | No | No |
| `ended_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### video_room_participants

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`
- `room_id` → `customer.video_rooms.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `room_id` | `INTEGER` | No | No | Yes | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `role` | `VARCHAR(20)` | Yes | No | No | No |
| `joined_at` | `DATETIME` | Yes | No | No | No |
| `left_at` | `DATETIME` | Yes | No | No | No |

### direct_chat_rooms

**Primary Key:** id

**Foreign Keys:**
- `participant_one` → `core.users.id`
- `country_code` → `country.country_configs.code`
- `participant_two` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `chat_id` | `VARCHAR(64)` | No | No | No | Yes |
| `participant_one` | `INTEGER` | No | No | Yes | No |
| `participant_two` | `INTEGER` | No | No | Yes | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `is_masked` | `BOOLEAN` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### group_chat_members

**Primary Key:** id

**Foreign Keys:**
- `room_id` → `communication.group_chat_rooms.id`
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `room_id` | `INTEGER` | No | No | Yes | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `role` | `VARCHAR(20)` | Yes | No | No | No |
| `joined_at` | `DATETIME` | Yes | No | No | No |

### shift_handover_sessions

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`
- `incoming_employee_id` → `logistics.employees.id`
- `outgoing_employee_id` → `logistics.employees.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `outgoing_employee_id` | `INTEGER` | No | No | Yes | No |
| `incoming_employee_id` | `INTEGER` | Yes | No | Yes | No |
| `shift_date` | `DATETIME` | No | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `acknowledged_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### escalation_sla_logs

**Primary Key:** id

**Foreign Keys:**
- `escalated_to_user_id` → `core.users.id`
- `original_recipient_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `message_id` | `INTEGER` | No | No | No | No |
| `message_type` | `VARCHAR(30)` | No | No | No | No |
| `original_recipient_id` | `INTEGER` | Yes | No | Yes | No |
| `escalated_to_user_id` | `INTEGER` | Yes | No | Yes | No |
| `escalated_to_role` | `VARCHAR(40)` | Yes | No | No | No |
| `priority` | `VARCHAR(20)` | No | No | No | No |
| `elapsed_minutes` | `INTEGER` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `escalated_at` | `DATETIME` | Yes | No | No | No |
| `acknowledged_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

## Schema: commerce

Tables: 34

### categories

**Primary Key:** id

**Foreign Keys:**
- `parent_id` → `commerce.categories.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `name` | `VARCHAR` | No | No | No | No |
| `slug` | `VARCHAR` | Yes | No | No | Yes |
| `description` | `TEXT` | Yes | No | No | No |
| `parent_id` | `INTEGER` | Yes | No | Yes | No |
| `icon` | `VARCHAR` | Yes | No | No | No |
| `image_url` | `VARCHAR` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `is_featured` | `BOOLEAN` | Yes | No | No | No |
| `sort_order` | `INTEGER` | Yes | No | No | No |
| `commission_rate` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `meta_title` | `VARCHAR` | Yes | No | No | No |
| `meta_description` | `TEXT` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `path` | `VARCHAR(255)` | Yes | No | No | No |
| `depth` | `INTEGER` | Yes | No | No | No |

### products

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`
- `supplier_id` → `core.users.id`
- `category_id` → `commerce.categories.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `name` | `VARCHAR` | No | No | No | No |
| `slug` | `VARCHAR` | Yes | No | No | Yes |
| `description` | `TEXT` | Yes | No | No | No |
| `short_description` | `TEXT` | Yes | No | No | No |
| `ai_description` | `TEXT` | Yes | No | No | No |
| `sku` | `VARCHAR` | Yes | No | No | Yes |
| `barcode` | `VARCHAR` | Yes | No | No | Yes |
| `price` | `NUMERIC(10, 2)` | No | No | No | No |
| `compare_price` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `cost_price` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `stock` | `INTEGER` | Yes | No | No | No |
| `low_stock_threshold` | `INTEGER` | Yes | No | No | No |
| `weight` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `dimensions` | `VARCHAR` | Yes | No | No | No |
| `materials` | `JSON` | Yes | No | No | No |
| `image_url` | `VARCHAR` | Yes | No | No | No |
| `images` | `JSON` | Yes | No | No | No |
| `category` | `VARCHAR` | Yes | No | No | No |
| `category_id` | `INTEGER` | Yes | No | Yes | No |
| `tags` | `JSON` | Yes | No | No | No |
| `attributes` | `JSON` | Yes | No | No | No |
| `supplier_id` | `INTEGER` | Yes | No | Yes | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `is_featured` | `BOOLEAN` | Yes | No | No | No |
| `is_digital` | `BOOLEAN` | Yes | No | No | No |
| `is_verified` | `BOOLEAN` | Yes | No | No | No |
| `moderation_status` | `VARCHAR` | Yes | No | No | No |
| `brand` | `VARCHAR` | Yes | No | No | No |
| `color` | `VARCHAR` | Yes | No | No | No |
| `sizes` | `JSON` | Yes | No | No | No |
| `rating` | `NUMERIC(3, 2)` | Yes | No | No | No |
| `sales_count` | `INTEGER` | Yes | No | No | No |
| `meta_title` | `VARCHAR` | Yes | No | No | No |
| `meta_description` | `TEXT` | Yes | No | No | No |
| `is_approved` | `BOOLEAN` | Yes | No | No | No |
| `is_deleted` | `BOOLEAN` | Yes | No | No | No |
| `discount_starts_at` | `DATETIME` | Yes | No | No | No |
| `discount_ends_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `filter_attributes` | `JSON` | Yes | No | No | No |
| `search_vector` | `JSON` | Yes | No | No | No |
| `video_count` | `INTEGER` | Yes | No | No | No |
| `variant_axes` | `JSON` | Yes | No | No | No |
| `bg_preset` | `VARCHAR` | Yes | No | No | No |
| `visibility_regions` | `TEXT` | Yes | No | No | No |
| `slug_hash` | `VARCHAR(32)` | Yes | No | No | Yes |
| `subcategory` | `VARCHAR` | Yes | No | No | No |
| `return_window_days` | `INTEGER` | Yes | No | No | No |
| `is_new` | `BOOLEAN` | Yes | No | No | No |

### reviews

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`
- `product_id` → `commerce.products.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `product_id` | `INTEGER` | No | No | Yes | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `rating` | `INTEGER` | No | No | No | No |
| `title` | `VARCHAR` | Yes | No | No | No |
| `comment` | `TEXT` | Yes | No | No | No |
| `image_url` | `VARCHAR` | Yes | No | No | No |
| `is_approved` | `BOOLEAN` | Yes | No | No | No |
| `is_deleted` | `BOOLEAN` | Yes | No | No | No |
| `is_verified_purchase` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### product_variants

**Primary Key:** id

**Foreign Keys:**
- `product_id` → `commerce.products.id`
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `product_id` | `INTEGER` | No | No | Yes | No |
| `sku` | `VARCHAR` | Yes | No | No | Yes |
| `title` | `VARCHAR` | Yes | No | No | No |
| `size` | `VARCHAR` | Yes | No | No | No |
| `color` | `VARCHAR` | Yes | No | No | No |
| `material` | `VARCHAR` | Yes | No | No | No |
| `pattern` | `VARCHAR` | Yes | No | No | No |
| `gender` | `VARCHAR` | Yes | No | No | No |
| `barcode` | `VARCHAR` | Yes | No | No | Yes |
| `product_code` | `VARCHAR` | Yes | No | No | No |
| `price` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `stock` | `INTEGER` | Yes | No | No | No |
| `media_url` | `VARCHAR` | Yes | No | No | No |
| `attributes_json` | `TEXT` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `sort_order` | `INTEGER` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `variant_key` | `VARCHAR(64)` | Yes | No | No | No |

### product_images

**Primary Key:** id

**Foreign Keys:**
- `product_id` → `commerce.products.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `product_id` | `INTEGER` | No | No | Yes | No |
| `image_url` | `VARCHAR(500)` | No | No | No | No |
| `alt_text` | `VARCHAR(255)` | Yes | No | No | No |
| `sort_order` | `INTEGER` | Yes | No | No | No |
| `is_primary` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### product_filter_metadata

**Primary Key:** id

**Foreign Keys:**
- `category_id` → `commerce.categories.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `category_id` | `INTEGER` | Yes | No | Yes | No |
| `filter_name` | `VARCHAR(100)` | No | No | No | No |
| `filter_type` | `VARCHAR(50)` | No | No | No | No |
| `display_order` | `INTEGER` | No | No | No | No |
| `is_active` | `BOOLEAN` | No | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### product_filter_options

**Primary Key:** id

**Foreign Keys:**
- `filter_metadata_id` → `commerce.product_filter_metadata.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `filter_metadata_id` | `INTEGER` | No | No | Yes | No |
| `option_value` | `VARCHAR(255)` | No | No | No | No |
| `option_display_name` | `VARCHAR(255)` | No | No | No | No |
| `product_count` | `INTEGER` | No | No | No | No |
| `sort_order` | `INTEGER` | No | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### orders

**Primary Key:** id

**Foreign Keys:**
- `customer_id` → `core.users.id`
- `country_code` → `country.country_configs.code`
- `invoice_id` → `finance.ar_invoices.id`
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `order_number` | `VARCHAR` | Yes | No | No | Yes |
| `customer_id` | `INTEGER` | Yes | No | Yes | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `status_label` | `VARCHAR(50)` | Yes | No | No | No |
| `payment_status` | `VARCHAR` | Yes | No | No | No |
| `payment_method` | `VARCHAR` | Yes | No | No | No |
| `payment_provider` | `VARCHAR` | Yes | No | No | No |
| `payment_intent_id` | `VARCHAR` | Yes | No | No | No |
| `subtotal` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `subtotal_amount` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `shipping_fee` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `shipping_amount` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `tax_amount` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `vat_amount` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `discount_amount` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `total` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `total_amount` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `coupon_code` | `VARCHAR` | Yes | No | No | No |
| `fraud_score` | `NUMERIC(5, 2)` | Yes | No | No | No |
| `fraud_action` | `VARCHAR` | Yes | No | No | No |
| `currency` | `VARCHAR` | Yes | No | No | No |
| `shipping_address` | `TEXT` | Yes | No | No | No |
| `shipping_city` | `VARCHAR` | Yes | No | No | No |
| `shipping_country` | `VARCHAR` | Yes | No | No | No |
| `shipping_postal_code` | `VARCHAR` | Yes | No | No | No |
| `customer_phone` | `VARCHAR` | Yes | No | No | No |
| `delivery_location` | `VARCHAR` | Yes | No | No | No |
| `delivery_note` | `VARCHAR` | Yes | No | No | No |
| `tracking_number` | `VARCHAR` | Yes | No | No | Yes |
| `selected_partner_id` | `INTEGER` | Yes | No | No | No |
| `selected_service_area_id` | `INTEGER` | Yes | No | No | No |
| `estimated_delivery_min` | `INTEGER` | Yes | No | No | No |
| `estimated_delivery_max` | `INTEGER` | Yes | No | No | No |
| `payment_gateway_code` | `VARCHAR` | Yes | No | No | No |
| `payment_gateway_fee_amount` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `payment_customer_total_amount` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `payment_gateway_fee_passed_to_customer` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `paid_at` | `DATETIME` | Yes | No | No | No |
| `invoice_id` | `INTEGER` | Yes | No | Yes | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `is_deleted` | `BOOLEAN` | Yes | No | No | No |
| `deleted_at` | `DATETIME` | Yes | No | No | No |

### order_items

**Primary Key:** id

**Foreign Keys:**
- `product_id` → `commerce.products.id`
- `order_id` → `commerce.orders.id`
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `order_id` | `INTEGER` | No | No | Yes | No |
| `product_id` | `INTEGER` | No | No | Yes | No |
| `variant_id` | `INTEGER` | Yes | No | No | No |
| `supplier_id` | `INTEGER` | Yes | No | No | No |
| `quantity` | `INTEGER` | Yes | No | No | No |
| `unit_price` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `price` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `total_price` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `product_name` | `VARCHAR` | Yes | No | No | No |
| `product_image` | `VARCHAR` | Yes | No | No | No |
| `selected_size` | `VARCHAR` | Yes | No | No | No |
| `selected_color` | `VARCHAR` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |

### order_logistics_allocations

**Primary Key:** id

**Foreign Keys:**
- `order_id` → `commerce.orders.id`
- `shipment_id` → `logistics.shipments.id`
- `supplier_id` → `core.users.id`
- `country_code` → `country.country_configs.code`
- `partner_id` → `logistics.logistics_partners.id`
- `service_area_id` → `logistics.logistics_partner_service_areas.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `order_id` | `INTEGER` | No | No | Yes | No |
| `supplier_id` | `INTEGER` | No | No | Yes | No |
| `shipment_id` | `INTEGER` | Yes | No | Yes | No |
| `partner_id` | `INTEGER` | Yes | No | Yes | No |
| `service_area_id` | `INTEGER` | Yes | No | Yes | No |
| `allocation_source` | `VARCHAR` | Yes | No | No | No |
| `partner_name_snapshot` | `VARCHAR` | Yes | No | No | No |
| `partner_code_snapshot` | `VARCHAR` | Yes | No | No | No |
| `service_area_label_snapshot` | `VARCHAR` | Yes | No | No | No |
| `destination_country` | `VARCHAR` | Yes | No | No | No |
| `destination_city` | `VARCHAR` | Yes | No | No | No |
| `shipping_amount` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `pickup_charge` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `dropoff_charge` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `accepted_vehicle_rule_id` | `INTEGER` | Yes | No | No | No |
| `accepted_vehicle_type` | `VARCHAR` | Yes | No | No | No |
| `accepted_vehicle_multiplier` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `accepted_shipping_amount` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `accepted_pickup_charge` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `accepted_dropoff_charge` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `estimated_delivery_min` | `INTEGER` | Yes | No | No | No |
| `estimated_delivery_max` | `INTEGER` | Yes | No | No | No |
| `currency` | `VARCHAR` | Yes | No | No | No |
| `pricing_breakdown_json` | `TEXT` | Yes | No | No | No |
| `accepted_pricing_breakdown_json` | `TEXT` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### return_requests

**Primary Key:** id

**Foreign Keys:**
- `customer_id` → `core.users.id`
- `order_id` → `commerce.orders.id`
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `order_id` | `INTEGER` | No | No | Yes | No |
| `order_item_id` | `INTEGER` | Yes | No | No | No |
| `customer_id` | `INTEGER` | Yes | No | Yes | No |
| `intent` | `VARCHAR` | Yes | No | No | No |
| `reason` | `VARCHAR` | No | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `details` | `TEXT` | Yes | No | No | No |
| `supplier_review_state` | `TEXT` | Yes | No | No | No |
| `images` | `TEXT` | Yes | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `refund_amount` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `items` | `TEXT` | Yes | No | No | No |
| `return_window_days` | `INTEGER` | Yes | No | No | No |
| `delivered_at` | `DATETIME` | Yes | No | No | No |
| `return_deadline` | `DATETIME` | Yes | No | No | No |
| `resolution_notes` | `TEXT` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### order_notifications

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`
- `order_id` → `commerce.orders.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `order_id` | `INTEGER` | No | No | Yes | No |
| `notification_type` | `VARCHAR(50)` | No | No | No | No |
| `is_read` | `BOOLEAN` | Yes | No | No | No |
| `metadata_json` | `TEXT` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### coupons

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`
- `deleted_by_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `code` | `VARCHAR` | No | No | No | Yes |
| `title` | `VARCHAR` | Yes | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `discount_type` | `VARCHAR` | Yes | No | No | No |
| `discount_value` | `NUMERIC(5, 2)` | Yes | No | No | No |
| `minimum_order` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `maximum_discount` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `min_order_amount` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `valid_from` | `DATETIME` | Yes | No | No | No |
| `valid_until` | `DATETIME` | Yes | No | No | No |
| `usage_limit` | `INTEGER` | Yes | No | No | No |
| `usage_count` | `INTEGER` | Yes | No | No | No |
| `starts_at` | `DATETIME` | Yes | No | No | No |
| `expires_at` | `DATETIME` | Yes | No | No | No |
| `allow_product_coupons` | `BOOLEAN` | Yes | No | No | No |
| `allow_category_coupons` | `BOOLEAN` | Yes | No | No | No |
| `allow_global_coupons` | `BOOLEAN` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `is_deleted` | `BOOLEAN` | Yes | No | No | No |
| `deleted_at` | `DATETIME` | Yes | No | No | No |
| `deleted_by_id` | `INTEGER` | Yes | No | Yes | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### banners

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`
- `deleted_by_id` → `core.users.id`
- `created_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `title` | `VARCHAR` | No | No | No | No |
| `subtitle` | `VARCHAR` | Yes | No | No | No |
| `image_url` | `VARCHAR` | Yes | No | No | No |
| `link` | `VARCHAR` | Yes | No | No | No |
| `banner_type` | `VARCHAR` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `is_deleted` | `BOOLEAN` | Yes | No | No | No |
| `deleted_at` | `DATETIME` | Yes | No | No | No |
| `deleted_by_id` | `INTEGER` | Yes | No | Yes | No |
| `sort_order` | `INTEGER` | Yes | No | No | No |
| `bg_color` | `VARCHAR` | Yes | No | No | No |
| `text_color` | `VARCHAR` | Yes | No | No | No |
| `subtitle_color` | `VARCHAR` | Yes | No | No | No |
| `btn_bg_color` | `VARCHAR` | Yes | No | No | No |
| `btn_text_color` | `VARCHAR` | Yes | No | No | No |
| `badge_text` | `VARCHAR` | Yes | No | No | No |
| `badge_color` | `VARCHAR` | Yes | No | No | No |
| `effect` | `VARCHAR` | Yes | No | No | No |
| `video_url` | `VARCHAR` | Yes | No | No | No |
| `cta_label` | `VARCHAR` | Yes | No | No | No |
| `cta_url` | `VARCHAR` | Yes | No | No | No |
| `starts_at` | `DATETIME` | Yes | No | No | No |
| `ends_at` | `DATETIME` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | Yes | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### flash_sales

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`
- `deleted_by_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `title` | `VARCHAR` | No | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `starts_at` | `DATETIME` | No | No | No | No |
| `ends_at` | `DATETIME` | No | No | No | No |
| `discount_pct` | `NUMERIC(5, 2)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `is_deleted` | `BOOLEAN` | Yes | No | No | No |
| `deleted_at` | `DATETIME` | Yes | No | No | No |
| `deleted_by_id` | `INTEGER` | Yes | No | Yes | No |
| `product_ids` | `JSON` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### flash_sale_items

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`
- `product_id` → `commerce.products.id`
- `flash_sale_id` → `commerce.flash_sales.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `flash_sale_id` | `INTEGER` | No | No | Yes | No |
| `product_id` | `INTEGER` | No | No | Yes | No |
| `original_price` | `NUMERIC(10, 2)` | No | No | No | No |
| `discounted_price` | `NUMERIC(10, 2)` | No | No | No | No |
| `quantity_limit` | `INTEGER` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### commission_agreements

**Primary Key:** id

**Foreign Keys:**
- `set_by_admin_id` → `core.users.id`
- `supplier_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `supplier_id` | `INTEGER` | No | No | Yes | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `tier` | `VARCHAR(20)` | No | No | No | No |
| `rate` | `NUMERIC(5, 4)` | No | No | No | No |
| `set_by_admin_id` | `INTEGER` | Yes | No | Yes | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `effective_from` | `DATETIME` | Yes | No | No | No |
| `effective_to` | `DATETIME` | Yes | No | No | No |
| `note` | `TEXT` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### product_commission_overrides

**Primary Key:** id

**Foreign Keys:**
- `supplier_id` → `core.users.id`
- `product_id` → `commerce.products.id`
- `set_by_admin_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `product_id` | `INTEGER` | No | No | Yes | No |
| `supplier_id` | `INTEGER` | No | No | Yes | No |
| `rate_percent` | `NUMERIC(5, 2)` | No | No | No | No |
| `set_by_admin_id` | `INTEGER` | Yes | No | Yes | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### commission_ledger_entries

**Primary Key:** id

**Foreign Keys:**
- `adjusted_by` → `core.users.id`
- `order_item_id` → `commerce.order_items.id`
- `order_id` → `commerce.orders.id`
- `supplier_id` → `core.users.id`
- `product_id` → `commerce.products.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `supplier_id` | `INTEGER` | No | No | Yes | No |
| `order_id` | `INTEGER` | Yes | No | Yes | No |
| `order_item_id` | `INTEGER` | Yes | No | Yes | No |
| `product_id` | `INTEGER` | Yes | No | Yes | No |
| `category_slug` | `VARCHAR(100)` | Yes | No | No | No |
| `badge_level` | `VARCHAR(20)` | Yes | No | No | No |
| `global_default_rate` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `category_rate` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `badge_rate` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `override_rate` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `applied_rate` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `calculation_method` | `VARCHAR(20)` | Yes | No | No | No |
| `order_value` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `commission_pct` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `cap_applied` | `BOOLEAN` | Yes | No | No | No |
| `commission_amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `low_value_threshold_used` | `BOOLEAN` | Yes | No | No | No |
| `fixed_cap_used` | `BOOLEAN` | Yes | No | No | No |
| `override_flag` | `BOOLEAN` | Yes | No | No | No |
| `is_adjusted` | `BOOLEAN` | Yes | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `adjusted_by` | `INTEGER` | Yes | No | Yes | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `credited_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### commission_category_rates

**Primary Key:** id

**Foreign Keys:**
- `category_id` → `commerce.categories.id`
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `category_id` | `INTEGER` | Yes | No | Yes | No |
| `category_slug` | `VARCHAR(100)` | Yes | No | No | No |
| `category_display_name` | `VARCHAR(100)` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `rate_percent` | `NUMERIC(5, 2)` | No | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### commission_rules

**Primary Key:** id

**Foreign Keys:**
- `created_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `rule_name` | `VARCHAR(255)` | No | No | No | No |
| `rule_type` | `VARCHAR(50)` | No | No | No | No |
| `tier` | `VARCHAR(20)` | Yes | No | No | No |
| `rate_percent` | `NUMERIC(5, 2)` | No | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### badge_billing_records

**Primary Key:** id

**Foreign Keys:**
- `supplier_id` → `core.users.id`
- `bank_transaction_id` → `finance.bank_transactions.id`
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | Yes | No | Yes | No |
| `supplier_id` | `INTEGER` | Yes | No | Yes | No |
| `billing_reference` | `VARCHAR` | Yes | No | No | Yes |
| `badge_level` | `VARCHAR(50)` | Yes | No | No | No |
| `charge_type` | `VARCHAR` | Yes | No | No | No |
| `charge_source` | `VARCHAR` | Yes | No | No | No |
| `amount` | `NUMERIC(12, 2)` | No | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `reference_id` | `VARCHAR` | Yes | No | No | No |
| `period_start` | `DATETIME` | Yes | No | No | No |
| `period_end` | `DATETIME` | Yes | No | No | No |
| `due_at` | `DATETIME` | Yes | No | No | No |
| `billed_at` | `DATETIME` | Yes | No | No | No |
| `paid_at` | `DATETIME` | Yes | No | No | No |
| `payment_method` | `VARCHAR` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | No | No |
| `bank_transaction_id` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### badge_transactions

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `amount` | `NUMERIC(12, 2)` | No | No | No | No |
| `transaction_type` | `VARCHAR` | No | No | No | No |
| `reference_id` | `VARCHAR` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### badge_tiers

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `name` | `VARCHAR` | No | No | No | No |
| `min_points` | `INTEGER` | No | No | No | No |
| `benefits` | `JSON` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### commission_badge_tiers

**Primary Key:** id

**Foreign Keys:**
- `updated_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `name` | `VARCHAR(100)` | No | No | No | No |
| `badge_level` | `VARCHAR(50)` | No | No | No | Yes |
| `commission_rate` | `NUMERIC(5, 4)` | No | No | No | No |
| `setup_fee` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `recurring_fee` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `recurring_interval` | `VARCHAR(20)` | Yes | No | No | No |
| `benefits_json` | `TEXT` | Yes | No | No | No |
| `min_fulfilled_orders` | `INTEGER` | Yes | No | No | No |
| `min_monthly_revenue` | `NUMERIC(15, 2)` | Yes | No | No | No |
| `sort_order` | `INTEGER` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `updated_by` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### commission_global_configs

**Primary Key:** id

**Foreign Keys:**
- `updated_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `default_rate` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `low_value_threshold` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `fixed_cap_amount` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `fixed_cap_enabled` | `BOOLEAN` | Yes | No | No | No |
| `margin_protection_enabled` | `BOOLEAN` | Yes | No | No | No |
| `margin_threshold` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `updated_by` | `INTEGER` | Yes | No | Yes | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### coupon_usage

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`
- `order_id` → `commerce.orders.id`
- `user_id` → `core.users.id`
- `coupon_id` → `commerce.coupons.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `coupon_id` | `INTEGER` | No | No | Yes | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `order_id` | `INTEGER` | Yes | No | Yes | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### promotion_engine_configs

**Primary Key:** id

**Foreign Keys:**
- `updated_by` → `core.users.id`
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `engine_enabled` | `BOOLEAN` | Yes | No | No | No |
| `allow_product_coupons` | `BOOLEAN` | Yes | No | No | No |
| `allow_category_coupons` | `BOOLEAN` | Yes | No | No | No |
| `allow_order_tier_discounts` | `BOOLEAN` | Yes | No | No | No |
| `allow_referral_rewards` | `BOOLEAN` | Yes | No | No | No |
| `allow_supplier_promotions` | `BOOLEAN` | Yes | No | No | No |
| `allow_global_coupons` | `BOOLEAN` | Yes | No | No | No |
| `stacking_mode` | `VARCHAR` | Yes | No | No | No |
| `max_combined_discount_percent` | `NUMERIC(5, 2)` | Yes | No | No | No |
| `max_combined_discount_amount` | `NUMERIC(12, 3)` | Yes | No | No | No |
| `show_savings_line_item` | `BOOLEAN` | Yes | No | No | No |
| `tier_discount_visible` | `BOOLEAN` | Yes | No | No | No |
| `points_per_omr` | `INTEGER` | Yes | No | No | No |
| `referral_referrer_points` | `INTEGER` | Yes | No | No | No |
| `referral_referee_points` | `INTEGER` | Yes | No | No | No |
| `points_expiry_months` | `INTEGER` | Yes | No | No | No |
| `referral_monthly_cap` | `INTEGER` | Yes | No | No | No |
| `referral_verification_delay_days` | `INTEGER` | Yes | No | No | No |
| `min_points_redeem` | `INTEGER` | Yes | No | No | No |
| `allow_partial_points_redemption` | `BOOLEAN` | Yes | No | No | No |
| `updated_by` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### promotion_ledger_entries

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `promotion_id` | `INTEGER` | Yes | No | No | No |
| `user_id` | `INTEGER` | Yes | No | Yes | No |
| `amount` | `NUMERIC(12, 2)` | No | No | No | No |
| `entry_type` | `VARCHAR` | No | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### promotion_order_tiers

**Primary Key:** id

**Foreign Keys:**
- `updated_by` → `core.users.id`
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `promotion_id` | `INTEGER` | Yes | No | No | No |
| `tier_name` | `VARCHAR` | Yes | No | No | No |
| `min_order_amount` | `NUMERIC(10, 2)` | No | No | No | No |
| `max_order_amount` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `discount_type` | `VARCHAR` | No | No | No | No |
| `discount_amount` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `discount_value` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `stacking_allowed` | `BOOLEAN` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `sort_order` | `INTEGER` | Yes | No | No | No |
| `updated_by` | `INTEGER` | Yes | No | Yes | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### product_verifications

**Primary Key:** id

**Foreign Keys:**
- `product_id` → `commerce.products.id`
- `verified_by` → `core.users.id`
- `shipment_id` → `logistics.shipments.id`
- `order_id` → `commerce.orders.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `product_id` | `INTEGER` | No | No | Yes | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `verified_by` | `INTEGER` | Yes | No | Yes | No |
| `shipment_id` | `INTEGER` | Yes | No | Yes | No |
| `verification_type` | `VARCHAR` | Yes | No | No | No |
| `result` | `VARCHAR` | Yes | No | No | No |
| `expected_specs` | `TEXT` | Yes | No | No | No |
| `actual_specs` | `TEXT` | Yes | No | No | No |
| `discrepancies` | `TEXT` | Yes | No | No | No |
| `scan_code` | `VARCHAR` | Yes | No | No | No |
| `image_urls` | `TEXT` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `order_id` | `INTEGER` | Yes | No | Yes | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### return_abuse_patterns

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `abuse_type` | `VARCHAR(50)` | No | No | No | No |
| `occurrence_count` | `INTEGER` | Yes | No | No | No |
| `first_occurrence` | `DATETIME` | Yes | No | No | No |
| `last_occurrence` | `DATETIME` | Yes | No | No | No |
| `is_blocked` | `BOOLEAN` | Yes | No | No | No |

### carts

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### cart_items

**Primary Key:** id

**Foreign Keys:**
- `product_id` → `commerce.products.id`
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `product_id` | `INTEGER` | No | No | Yes | No |
| `quantity` | `INTEGER` | Yes | No | No | No |
| `selected_size` | `VARCHAR(50)` | No | No | No | No |
| `selected_color` | `VARCHAR(50)` | No | No | No | No |
| `variant_id` | `INTEGER` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

## Schema: media

Tables: 6

### product_videos

**Primary Key:** id

**Foreign Keys:**
- `product_id` → `commerce.products.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `product_id` | `INTEGER` | No | No | Yes | No |
| `video_url` | `VARCHAR(500)` | No | No | No | No |
| `thumbnail_url` | `VARCHAR(500)` | Yes | No | No | No |
| `duration_seconds` | `INTEGER` | Yes | No | No | No |
| `video_type` | `VARCHAR(50)` | Yes | No | No | No |
| `title` | `VARCHAR(255)` | Yes | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `views_count` | `INTEGER` | Yes | No | No | No |
| `is_featured` | `BOOLEAN` | Yes | No | No | No |
| `upload_status` | `VARCHAR(50)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### video_analytics

**Primary Key:** id

**Foreign Keys:**
- `video_id` → `media.product_videos.id`
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `video_id` | `INTEGER` | No | No | Yes | No |
| `user_id` | `INTEGER` | Yes | No | Yes | No |
| `event_type` | `VARCHAR(50)` | No | No | No | No |
| `watch_duration_seconds` | `INTEGER` | Yes | No | No | No |
| `device_type` | `VARCHAR(50)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### video_room_recordings

**Primary Key:** id

**Foreign Keys:**
- `started_by` → `core.users.id`
- `room_id` → `customer.video_rooms.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `room_id` | `INTEGER` | No | No | Yes | No |
| `started_by` | `INTEGER` | No | No | Yes | No |
| `recording_url` | `VARCHAR(500)` | Yes | No | No | No |
| `duration_seconds` | `INTEGER` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `started_at` | `DATETIME` | Yes | No | No | No |
| `ended_at` | `DATETIME` | Yes | No | No | No |

### media_assets

**Primary Key:** id

**Foreign Keys:**
- `uploaded_by` → `core.users.id`
- `supplier_id` → `core.users.id`
- `product_id` → `commerce.products.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | No | No |
| `supplier_id` | `INTEGER` | Yes | No | Yes | No |
| `product_id` | `INTEGER` | Yes | No | Yes | No |
| `entity_type` | `VARCHAR(20)` | No | No | No | No |
| `entity_id` | `INTEGER` | Yes | No | No | No |
| `variant` | `VARCHAR(20)` | No | No | No | No |
| `file_path` | `VARCHAR(500)` | No | No | No | No |
| `file_url` | `VARCHAR(500)` | No | No | No | No |
| `file_size_bytes` | `INTEGER` | No | No | No | No |
| `mime_type` | `VARCHAR(100)` | No | No | No | No |
| `width` | `INTEGER` | Yes | No | No | No |
| `height` | `INTEGER` | Yes | No | No | No |
| `is_primary` | `BOOLEAN` | Yes | No | No | No |
| `alt_text` | `VARCHAR(255)` | Yes | No | No | No |
| `caption` | `TEXT` | Yes | No | No | No |
| `uploaded_by` | `INTEGER` | Yes | No | Yes | No |
| `uploaded_at` | `DATETIME` | Yes | No | No | No |
| `is_deleted` | `BOOLEAN` | Yes | No | No | No |
| `deleted_at` | `DATETIME` | Yes | No | No | No |

### media_upload_sessions

**Primary Key:** id

**Foreign Keys:**
- `created_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `session_id` | `VARCHAR(64)` | No | No | No | Yes |
| `country_code` | `VARCHAR(10)` | No | No | No | No |
| `entity_type` | `VARCHAR(20)` | No | No | No | No |
| `entity_id` | `INTEGER` | Yes | No | No | No |
| `filename` | `VARCHAR(255)` | No | No | No | No |
| `file_size` | `INTEGER` | No | No | No | No |
| `mime_type` | `VARCHAR(100)` | No | No | No | No |
| `chunk_size` | `INTEGER` | Yes | No | No | No |
| `total_chunks` | `INTEGER` | No | No | No | No |
| `uploaded_chunks` | `INTEGER` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `error_message` | `TEXT` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `completed_at` | `DATETIME` | Yes | No | No | No |

### ocr_results

**Primary Key:** id

**Foreign Keys:**
- `document_verification_id` → `security.document_verifications.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `document_verification_id` | `INTEGER` | No | No | Yes | Yes |
| `extracted_text` | `TEXT` | Yes | No | No | No |
| `confidence_score` | `VARCHAR` | Yes | No | No | No |
| `fields` | `JSON` | Yes | No | No | No |
| `processed_at` | `DATETIME` | Yes | No | No | No |

## Schema: logistics

Tables: 31

### warehouses

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `name` | `VARCHAR(255)` | No | No | No | No |
| `code` | `VARCHAR(50)` | No | No | No | Yes |
| `address` | `TEXT` | Yes | No | No | No |
| `city` | `VARCHAR(100)` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### stock_movements

**Primary Key:** id

**Foreign Keys:**
- `created_by` → `core.users.id`
- `product_id` → `commerce.products.id`
- `warehouse_id` → `logistics.warehouses.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `product_id` | `INTEGER` | No | No | Yes | No |
| `warehouse_id` | `INTEGER` | Yes | No | Yes | No |
| `movement_type` | `VARCHAR(50)` | No | No | No | No |
| `reference_type` | `VARCHAR(50)` | Yes | No | No | No |
| `reference_id` | `INTEGER` | Yes | No | No | No |
| `quantity_change` | `NUMERIC(14, 4)` | No | No | No | No |
| `quantity_after` | `NUMERIC(14, 4)` | No | No | No | No |
| `unit_cost` | `NUMERIC(14, 4)` | Yes | No | No | No |
| `total_cost` | `NUMERIC(14, 4)` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### logistics_zones

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `zone_name` | `VARCHAR(255)` | No | No | No | No |
| `zone_code` | `VARCHAR(50)` | No | No | No | Yes |
| `country_codes` | `JSON` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### logistics_rates

**Primary Key:** id

**Foreign Keys:**
- `zone_id` → `logistics.logistics_zones.id`
- `carrier_id` → `logistics.shipping_carriers.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `zone_id` | `INTEGER` | No | No | Yes | No |
| `carrier_id` | `INTEGER` | Yes | No | Yes | No |
| `service_level` | `VARCHAR(50)` | Yes | No | No | No |
| `rate` | `NUMERIC(14, 4)` | No | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `estimated_days_min` | `INTEGER` | Yes | No | No | No |
| `estimated_days_max` | `INTEGER` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### logistics_pricing_rules

**Primary Key:** id

**Foreign Keys:**
- `zone_id` → `logistics.logistics_zones.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `zone_id` | `INTEGER` | No | No | Yes | No |
| `vehicle_type` | `VARCHAR(50)` | No | No | No | No |
| `distance_band_start` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `distance_band_end` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `weight_band_start` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `weight_band_end` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `base_rate` | `NUMERIC(14, 4)` | No | No | No | No |
| `per_km_rate` | `NUMERIC(14, 4)` | Yes | No | No | No |
| `per_kg_rate` | `NUMERIC(14, 4)` | Yes | No | No | No |
| `fuel_surcharge_percent` | `NUMERIC(5, 2)` | Yes | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### logistics_partner_payouts

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`
- `partner_id` → `logistics.logistics_partners.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `partner_id` | `INTEGER` | No | No | Yes | No |
| `amount` | `NUMERIC(12, 2)` | No | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `period_start` | `DATETIME` | Yes | No | No | No |
| `period_end` | `DATETIME` | Yes | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `reference_id` | `VARCHAR` | Yes | No | No | No |
| `processed_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `method` | `VARCHAR` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |

### logistics_partners

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | Yes | No | Yes | No |
| `name` | `VARCHAR` | No | No | No | No |
| `code` | `VARCHAR` | No | No | No | Yes |
| `contact_name` | `VARCHAR` | Yes | No | No | No |
| `contact_email` | `VARCHAR` | Yes | No | No | No |
| `contact_phone` | `VARCHAR` | Yes | No | No | No |
| `website` | `VARCHAR` | Yes | No | No | No |
| `coverage_regions` | `JSON` | Yes | No | No | No |
| `service_types` | `JSON` | Yes | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `verification_status` | `VARCHAR` | Yes | No | No | No |
| `verification_note` | `VARCHAR` | Yes | No | No | No |
| `verified_by` | `INTEGER` | Yes | No | No | No |
| `verified_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `business_type` | `VARCHAR` | Yes | No | No | No |
| `region` | `VARCHAR` | Yes | No | No | No |
| `city` | `VARCHAR` | Yes | No | No | No |
| `address` | `TEXT` | Yes | No | No | No |
| `postal_code` | `VARCHAR` | Yes | No | No | No |
| `tax_id` | `VARCHAR` | Yes | No | No | No |
| `bio` | `TEXT` | Yes | No | No | No |
| `about_us` | `TEXT` | Yes | No | No | No |
| `logo_url` | `VARCHAR` | Yes | No | No | No |
| `banner_url` | `VARCHAR` | Yes | No | No | No |
| `latitude` | `NUMERIC(10, 7)` | Yes | No | No | No |
| `longitude` | `NUMERIC(10, 7)` | Yes | No | No | No |
| `social_links` | `JSON` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `is_terms_accepted` | `BOOLEAN` | Yes | No | No | No |
| `terms_version` | `VARCHAR` | Yes | No | No | No |
| `terms_accepted_at` | `DATETIME` | Yes | No | No | No |

### logistics_partner_profiles

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`
- `partner_id` → `logistics.logistics_partners.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `partner_id` | `INTEGER` | No | No | Yes | Yes |
| `tax_id` | `VARCHAR` | Yes | No | No | No |
| `registration_number` | `VARCHAR` | Yes | No | No | No |
| `business_type` | `VARCHAR` | Yes | No | No | No |
| `years_in_business` | `INTEGER` | Yes | No | No | No |
| `insurance_provider` | `VARCHAR` | Yes | No | No | No |
| `insurance_policy_number` | `VARCHAR` | Yes | No | No | No |
| `insurance_expiry` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |

### logistics_partner_service_areas

**Primary Key:** id

**Foreign Keys:**
- `partner_id` → `logistics.logistics_partners.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `partner_id` | `INTEGER` | No | No | Yes | No |
| `country_code` | `VARCHAR(10)` | No | No | No | No |
| `country_name` | `VARCHAR` | No | No | No | No |
| `origin_city` | `VARCHAR` | No | No | No | No |
| `city_name` | `VARCHAR` | No | No | No | No |
| `zone_label` | `VARCHAR` | Yes | No | No | No |
| `charge_amount` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `minimum_charge` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `per_kg_rate` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `pickup_charge` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `dropoff_charge` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `per_km_rate` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `delivery_days_min` | `INTEGER` | Yes | No | No | No |
| `delivery_days_max` | `INTEGER` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `approval_status` | `VARCHAR` | Yes | No | No | No |
| `review_note` | `VARCHAR` | Yes | No | No | No |
| `reviewed_by` | `INTEGER` | Yes | No | No | No |
| `reviewed_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### logistics_pricing_profiles

**Primary Key:** id

**Foreign Keys:**
- `partner_id` → `logistics.logistics_partners.id`
- `reviewed_by` → `core.users.id`
- `service_area_id` → `logistics.logistics_partner_service_areas.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `partner_id` | `INTEGER` | No | No | Yes | No |
| `service_area_id` | `INTEGER` | No | No | Yes | No |
| `profile_name` | `VARCHAR` | No | No | No | No |
| `base_in_city_fee` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `per_kg_rate` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `minimum_charge` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `maximum_charge` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `fuel_multiplier` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `base_inter_city_fee` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `per_km_rate` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `bulk_discount_threshold_kg` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `bulk_discount_percent` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `approval_status` | `VARCHAR` | Yes | No | No | No |
| `review_note` | `VARCHAR` | Yes | No | No | No |
| `reviewed_by` | `INTEGER` | Yes | No | Yes | No |
| `reviewed_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### logistics_vehicle_rules

**Primary Key:** id

**Foreign Keys:**
- `reviewed_by` → `core.users.id`
- `partner_id` → `logistics.logistics_partners.id`
- `service_area_id` → `logistics.logistics_partner_service_areas.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `partner_id` | `INTEGER` | No | No | Yes | No |
| `service_area_id` | `INTEGER` | No | No | Yes | No |
| `vehicle_type` | `VARCHAR` | No | No | No | No |
| `max_weight_kg` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `cost_multiplier` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `priority_rank` | `INTEGER` | Yes | No | No | No |
| `route_scope` | `VARCHAR` | Yes | No | No | No |
| `max_volume_cm3` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `approval_status` | `VARCHAR` | Yes | No | No | No |
| `review_note` | `VARCHAR` | Yes | No | No | No |
| `reviewed_by` | `INTEGER` | Yes | No | Yes | No |
| `reviewed_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### logistics_category_pricing_rules

**Primary Key:** id

**Foreign Keys:**
- `partner_id` → `logistics.logistics_partners.id`
- `service_area_id` → `logistics.logistics_partner_service_areas.id`
- `reviewed_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `partner_id` | `INTEGER` | No | No | Yes | No |
| `service_area_id` | `INTEGER` | Yes | No | Yes | No |
| `category_name` | `VARCHAR` | No | No | No | No |
| `flat_fee_override` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `special_handling_fee` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `approval_status` | `VARCHAR` | Yes | No | No | No |
| `review_note` | `VARCHAR` | Yes | No | No | No |
| `reviewed_by` | `INTEGER` | Yes | No | Yes | No |
| `reviewed_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### shipments

**Primary Key:** id

**Foreign Keys:**
- `order_id` → `commerce.orders.id`
- `supplier_id` → `core.users.id`
- `carrier_id` → `logistics.shipping_carriers.id`
- `assigned_partner_id` → `logistics.logistics_partners.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `order_id` | `INTEGER` | No | No | Yes | No |
| `supplier_id` | `INTEGER` | No | No | Yes | No |
| `assigned_partner_id` | `INTEGER` | Yes | No | Yes | No |
| `carrier_id` | `INTEGER` | Yes | No | Yes | No |
| `tracking_number` | `VARCHAR` | Yes | No | No | Yes |
| `carrier_name` | `VARCHAR` | Yes | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `distribution_channel` | `VARCHAR` | Yes | No | No | No |
| `current_hub` | `VARCHAR` | Yes | No | No | No |
| `scan_code` | `VARCHAR` | Yes | No | No | No |
| `package_count` | `INTEGER` | Yes | No | No | No |
| `package_weight_kg` | `NUMERIC(5, 2)` | Yes | No | No | No |
| `package_dimensions` | `VARCHAR` | Yes | No | No | No |
| `packaged_at` | `DATETIME` | Yes | No | No | No |
| `packaged_by_user_id` | `INTEGER` | Yes | No | No | No |
| `packaged_notes` | `VARCHAR` | Yes | No | No | No |
| `packaging_notes` | `VARCHAR` | Yes | No | No | No |
| `shipped_at` | `DATETIME` | Yes | No | No | No |
| `estimated_delivery` | `DATETIME` | Yes | No | No | No |
| `actual_delivery` | `DATETIME` | Yes | No | No | No |
| `delivery_signature_name` | `VARCHAR` | Yes | No | No | No |
| `delivery_signature_data_url` | `VARCHAR` | Yes | No | No | No |
| `delivery_signature_captured_at` | `DATETIME` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `accepted_vehicle_type` | `VARCHAR` | Yes | No | No | No |
| `accepted_vehicle_multiplier` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `accepted_vehicle_selected_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### shipment_events

**Primary Key:** id

**Foreign Keys:**
- `actor_user_id` → `core.users.id`
- `shipment_id` → `logistics.shipments.id`
- `order_id` → `commerce.orders.id`
- `supplier_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `shipment_id` | `INTEGER` | No | No | Yes | No |
| `order_id` | `INTEGER` | No | No | Yes | No |
| `supplier_id` | `INTEGER` | No | No | Yes | No |
| `actor_user_id` | `INTEGER` | Yes | No | Yes | No |
| `actor_role` | `VARCHAR` | Yes | No | No | No |
| `event_type` | `VARCHAR` | No | No | No | No |
| `status_after` | `VARCHAR` | Yes | No | No | No |
| `distribution_channel` | `VARCHAR` | Yes | No | No | No |
| `location` | `VARCHAR` | Yes | No | No | No |
| `latitude` | `NUMERIC(10, 8)` | Yes | No | No | No |
| `longitude` | `NUMERIC(11, 8)` | Yes | No | No | No |
| `scan_code` | `VARCHAR` | Yes | No | No | No |
| `notes` | `VARCHAR` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### shipping_rules

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `method` | `VARCHAR` | No | No | No | No |
| `base_rate` | `NUMERIC(10, 2)` | No | No | No | No |
| `per_kg_rate` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### shipping_carriers

**Primary Key:** id

**Foreign Keys:**
- `supplier_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `supplier_id` | `INTEGER` | Yes | No | Yes | No |
| `name` | `VARCHAR` | No | No | No | No |
| `code` | `VARCHAR` | No | No | No | Yes |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### shipping_zones

**Primary Key:** id

**Foreign Keys:**
- `supplier_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `supplier_id` | `INTEGER` | Yes | No | Yes | No |
| `name` | `VARCHAR` | No | No | No | No |
| `countries` | `JSON` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### logistics_cod_remittance_receipts

**Primary Key:** id

**Foreign Keys:**
- `reviewed_by` → `core.users.id`
- `shipment_id` → `logistics.shipments.id`
- `settlement_id` → `logistics.logistics_settlements.id`
- `partner_id` → `logistics.logistics_partners.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `partner_id` | `INTEGER` | Yes | No | Yes | No |
| `shipment_id` | `INTEGER` | Yes | No | Yes | No |
| `settlement_id` | `INTEGER` | Yes | No | Yes | No |
| `amount` | `NUMERIC(12, 2)` | No | No | No | No |
| `bank_reference` | `VARCHAR` | Yes | No | No | No |
| `receipt_file_url` | `VARCHAR` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `review_note` | `TEXT` | Yes | No | No | No |
| `reviewed_by` | `INTEGER` | Yes | No | Yes | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### logistics_partner_bank_accounts

**Primary Key:** id

**Foreign Keys:**
- `verified_by` → `core.users.id`
- `partner_id` → `logistics.logistics_partners.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `partner_id` | `INTEGER` | No | No | Yes | No |
| `account_number` | `VARCHAR` | Yes | No | No | No |
| `bank_name` | `VARCHAR` | No | No | No | No |
| `beneficiary_name` | `VARCHAR` | Yes | No | No | No |
| `branch_name` | `VARCHAR` | Yes | No | No | No |
| `iban` | `VARCHAR` | Yes | No | No | No |
| `swift_code` | `VARCHAR` | Yes | No | No | No |
| `routing_number` | `VARCHAR` | Yes | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `bank_country` | `VARCHAR(3)` | Yes | No | No | No |
| `verification_status` | `VARCHAR` | Yes | No | No | No |
| `verification_note` | `TEXT` | Yes | No | No | No |
| `provider` | `VARCHAR` | Yes | No | No | No |
| `provider_recipient_id` | `VARCHAR` | Yes | No | No | No |
| `provider_status` | `VARCHAR` | Yes | No | No | No |
| `provider_last_synced_at` | `DATETIME` | Yes | No | No | No |
| `verified_at` | `DATETIME` | Yes | No | No | No |
| `verified_by` | `INTEGER` | Yes | No | Yes | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### logistics_partner_documents

**Primary Key:** id

**Foreign Keys:**
- `partner_id` → `logistics.logistics_partners.id`
- `reviewed_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `partner_id` | `INTEGER` | No | No | Yes | No |
| `doc_type` | `VARCHAR` | No | No | No | No |
| `file_url` | `VARCHAR` | No | No | No | No |
| `reviewed_by` | `INTEGER` | Yes | No | Yes | No |
| `is_verified` | `BOOLEAN` | Yes | No | No | No |
| `verified_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### logistics_settlements

**Primary Key:** id

**Foreign Keys:**
- `partner_id` → `logistics.logistics_partners.id`
- `shipment_id` → `logistics.shipments.id`
- `order_id` → `commerce.orders.id`
- `payout_id` → `treasury.payouts.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `partner_id` | `INTEGER` | No | No | Yes | No |
| `order_id` | `INTEGER` | Yes | No | Yes | No |
| `ledger_id` | `INTEGER` | Yes | No | No | No |
| `shipment_id` | `INTEGER` | Yes | No | Yes | No |
| `amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `pickup_charge` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `dropoff_charge` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `total_delivery_fee` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `cod_collected` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `cod_remitted` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `cod_retained` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `cod_remittance_status` | `VARCHAR` | Yes | No | No | No |
| `eligible_at` | `DATETIME` | Yes | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `payout_id` | `INTEGER` | Yes | No | Yes | No |
| `bank_transaction_id` | `INTEGER` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### shipment_confirmations

**Primary Key:** id

**Foreign Keys:**
- `shipment_id` → `logistics.shipments.id`
- `requester_user_id` → `core.users.id`
- `supplier_id` → `core.users.id`
- `order_id` → `commerce.orders.id`
- `target_user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `shipment_id` | `INTEGER` | No | No | Yes | No |
| `order_id` | `INTEGER` | Yes | No | Yes | No |
| `supplier_id` | `INTEGER` | Yes | No | Yes | No |
| `requester_user_id` | `INTEGER` | Yes | No | Yes | No |
| `requester_role` | `VARCHAR` | Yes | No | No | No |
| `target_user_id` | `INTEGER` | Yes | No | Yes | No |
| `target_role` | `VARCHAR` | Yes | No | No | No |
| `confirmation_type` | `VARCHAR` | Yes | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `requested_status` | `VARCHAR` | Yes | No | No | No |
| `requested_event_type` | `VARCHAR` | Yes | No | No | No |
| `current_hub` | `VARCHAR` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `confirmation_code` | `VARCHAR` | Yes | No | No | No |
| `confirmed_at` | `DATETIME` | Yes | No | No | No |
| `responded_at` | `DATETIME` | Yes | No | No | No |
| `tracking_number` | `VARCHAR` | Yes | No | No | No |
| `delivery_signature_name` | `VARCHAR` | Yes | No | No | No |
| `delivery_signature_data_url` | `VARCHAR` | Yes | No | No | No |
| `delivery_signature_captured_at` | `DATETIME` | Yes | No | No | No |
| `response_notes` | `TEXT` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### logistics_fraud_indicators

**Primary Key:** id

**Foreign Keys:**
- `partner_id` → `logistics.logistics_partners.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `partner_id` | `INTEGER` | No | No | Yes | No |
| `indicator_type` | `VARCHAR(50)` | No | No | No | No |
| `value` | `VARCHAR` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### city_distance_matrix

**Primary Key:** id

**Foreign Keys:**
- `created_by` → `core.users.id`
- `updated_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `origin_country_code` | `VARCHAR(10)` | No | No | No | No |
| `origin_city_name` | `VARCHAR` | No | No | No | No |
| `destination_country_code` | `VARCHAR(10)` | No | No | No | No |
| `destination_city_name` | `VARCHAR` | No | No | No | No |
| `distance_km` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | Yes | No |
| `updated_by` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### offices

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `name` | `VARCHAR(200)` | No | No | No | No |
| `country_code` | `VARCHAR(10)` | No | No | No | No |
| `city` | `VARCHAR(100)` | Yes | No | No | No |
| `latitude` | `FLOAT` | Yes | No | No | No |
| `longitude` | `FLOAT` | Yes | No | No | No |
| `geo_fence_radius_meters` | `INTEGER` | Yes | No | No | No |
| `address` | `TEXT` | Yes | No | No | No |
| `phone` | `VARCHAR(50)` | Yes | No | No | No |
| `email` | `VARCHAR(200)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |

### dynamic_qr_sessions

**Primary Key:** id

**Foreign Keys:**
- `employee_id` → `logistics.employees.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `employee_id` | `INTEGER` | No | No | Yes | No |
| `qr_token` | `VARCHAR(255)` | No | No | No | Yes |
| `expires_at` | `DATETIME` | No | No | No | No |
| `used_at` | `DATETIME` | Yes | No | No | No |
| `ip_address` | `VARCHAR(45)` | Yes | No | No | No |
| `user_agent` | `VARCHAR(500)` | Yes | No | No | No |
| `device_fingerprint` | `VARCHAR(255)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### geo_fence_logs

**Primary Key:** id

**Foreign Keys:**
- `employee_id` → `logistics.employees.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `employee_id` | `INTEGER` | No | No | Yes | No |
| `latitude` | `FLOAT` | No | No | No | No |
| `longitude` | `FLOAT` | No | No | No | No |
| `accuracy_meters` | `INTEGER` | Yes | No | No | No |
| `scanned_at` | `DATETIME` | Yes | No | No | No |
| `is_within_fence` | `BOOLEAN` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### employees

**Primary Key:** id

**Foreign Keys:**
- `office_id` → `logistics.offices.id`
- `org_unit_id` → `hr.org_units.id`
- `reporting_manager_id` → `logistics.employees.id`
- `user_id` → `core.users.id`
- `hiring_manager_id` → `core.users.id`
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | Yes | No | Yes | Yes |
| `employee_code` | `VARCHAR(20)` | No | No | No | Yes |
| `office_id` | `INTEGER` | Yes | No | Yes | No |
| `department` | `VARCHAR(100)` | Yes | No | No | No |
| `position` | `VARCHAR(100)` | Yes | No | No | No |
| `employment_type` | `VARCHAR(30)` | Yes | No | No | No |
| `employment_status` | `VARCHAR(30)` | Yes | No | No | No |
| `salary` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `hire_date` | `DATE` | No | No | No | No |
| `termination_date` | `DATE` | Yes | No | No | No |
| `is_verified` | `BOOLEAN` | Yes | No | No | No |
| `gender` | `VARCHAR(20)` | Yes | No | No | No |
| `years_of_experience` | `INTEGER` | Yes | No | No | No |
| `performance_score` | `INTEGER` | Yes | No | No | No |
| `education_level` | `VARCHAR(50)` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `reporting_manager_id` | `INTEGER` | Yes | No | Yes | No |
| `hiring_manager_id` | `INTEGER` | Yes | No | Yes | No |
| `authority_level` | `INTEGER` | Yes | No | No | No |
| `org_unit_id` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### employee_attendance

**Primary Key:** id

**Foreign Keys:**
- `employee_id` → `logistics.employees.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `employee_id` | `INTEGER` | No | No | Yes | No |
| `date` | `DATE` | No | No | No | No |
| `scan_in_time` | `DATETIME` | Yes | No | No | No |
| `scan_out_time` | `DATETIME` | Yes | No | No | No |
| `scan_type` | `VARCHAR(20)` | Yes | No | No | No |
| `location_lat` | `FLOAT` | Yes | No | No | No |
| `location_long` | `FLOAT` | Yes | No | No | No |
| `device_fingerprint` | `VARCHAR(255)` | Yes | No | No | No |
| `is_anomaly` | `BOOLEAN` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### employee_leave_ledgers

**Primary Key:** id

**Foreign Keys:**
- `employee_id` → `logistics.employees.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `employee_id` | `INTEGER` | No | No | Yes | No |
| `leave_type` | `VARCHAR(50)` | No | No | No | No |
| `year` | `INTEGER` | No | No | No | No |
| `allocated_days` | `INTEGER` | Yes | No | No | No |
| `used_days` | `INTEGER` | Yes | No | No | No |
| `carried_forward` | `INTEGER` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### employee_shift_rosters

**Primary Key:** id

**Foreign Keys:**
- `employee_id` → `logistics.employees.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `employee_id` | `INTEGER` | No | No | Yes | No |
| `shift_date` | `DATE` | No | No | No | No |
| `start_time` | `TIME` | No | No | No | No |
| `end_time` | `TIME` | No | No | No | No |
| `shift_type` | `VARCHAR(30)` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

## Schema: trading

Tables: 6

### purchase_orders

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`
- `supplier_id` → `finance.vendors.id`
- `created_by` → `core.users.id`
- `warehouse_id` → `logistics.warehouses.id`
- `vendor_id` → `finance.vendors.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `po_number` | `VARCHAR(80)` | Yes | No | No | Yes |
| `supplier_id` | `INTEGER` | No | No | Yes | No |
| `vendor_id` | `INTEGER` | Yes | No | Yes | No |
| `supplier_name` | `VARCHAR(255)` | Yes | No | No | No |
| `order_date` | `DATETIME` | No | No | No | No |
| `expected_delivery_date` | `DATETIME` | Yes | No | No | No |
| `delivery_date` | `DATETIME` | Yes | No | No | No |
| `warehouse_id` | `INTEGER` | Yes | No | Yes | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `subtotal` | `NUMERIC(14, 2)` | Yes | No | No | No |
| `discount_total` | `NUMERIC(14, 2)` | Yes | No | No | No |
| `tax_total` | `NUMERIC(14, 2)` | Yes | No | No | No |
| `grand_total` | `NUMERIC(14, 2)` | Yes | No | No | No |
| `total_amount` | `NUMERIC(14, 2)` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `terms` | `TEXT` | Yes | No | No | No |
| `shipping_address` | `TEXT` | Yes | No | No | No |
| `status` | `VARCHAR(50)` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `created_by` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### purchase_order_lines

**Primary Key:** id

**Foreign Keys:**
- `po_id` → `trading.purchase_orders.id`
- `product_id` → `commerce.products.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `po_id` | `INTEGER` | No | No | Yes | No |
| `product_id` | `INTEGER` | Yes | No | Yes | No |
| `product_name` | `VARCHAR(255)` | Yes | No | No | No |
| `sku` | `VARCHAR(100)` | Yes | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `quantity_ordered` | `NUMERIC(14, 4)` | No | No | No | No |
| `quantity_received` | `NUMERIC(14, 4)` | Yes | No | No | No |
| `unit_price` | `NUMERIC(14, 4)` | No | No | No | No |
| `discount_percent` | `NUMERIC(5, 2)` | Yes | No | No | No |
| `discount_amount` | `NUMERIC(14, 2)` | Yes | No | No | No |
| `tax_rate` | `NUMERIC(5, 2)` | Yes | No | No | No |
| `tax_amount` | `NUMERIC(14, 2)` | Yes | No | No | No |
| `line_total` | `NUMERIC(14, 2)` | Yes | No | No | No |
| `weight` | `NUMERIC(10, 3)` | Yes | No | No | No |
| `volume` | `NUMERIC(10, 3)` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### goods_receipt_notes

**Primary Key:** id

**Foreign Keys:**
- `received_by` → `core.users.id`
- `warehouse_id` → `logistics.warehouses.id`
- `supplier_id` → `finance.vendors.id`
- `po_id` → `trading.purchase_orders.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `grn_number` | `VARCHAR(80)` | Yes | No | No | Yes |
| `po_id` | `INTEGER` | No | No | Yes | No |
| `supplier_id` | `INTEGER` | Yes | No | Yes | No |
| `receipt_date` | `DATETIME` | No | No | No | No |
| `warehouse_id` | `INTEGER` | Yes | No | Yes | No |
| `status` | `VARCHAR(50)` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `received_by` | `INTEGER` | Yes | No | Yes | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### goods_receipt_lines

**Primary Key:** id

**Foreign Keys:**
- `po_line_id` → `trading.purchase_order_lines.id`
- `grn_id` → `trading.goods_receipt_notes.id`
- `product_id` → `commerce.products.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `grn_id` | `INTEGER` | No | No | Yes | No |
| `po_line_id` | `INTEGER` | Yes | No | Yes | No |
| `product_id` | `INTEGER` | Yes | No | Yes | No |
| `product_name` | `VARCHAR(255)` | Yes | No | No | No |
| `sku` | `VARCHAR(100)` | Yes | No | No | No |
| `quantity_received` | `NUMERIC(14, 4)` | Yes | No | No | No |
| `quantity_accepted` | `NUMERIC(14, 4)` | Yes | No | No | No |
| `quantity_rejected` | `NUMERIC(14, 4)` | Yes | No | No | No |
| `rejection_reason` | `VARCHAR(255)` | Yes | No | No | No |
| `lot_number` | `VARCHAR(100)` | Yes | No | No | No |
| `expiry_date` | `DATETIME` | Yes | No | No | No |
| `unit_cost` | `NUMERIC(14, 4)` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### sales_orders

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`
- `warehouse_id` → `logistics.warehouses.id`
- `customer_id` → `finance.customers.id`
- `created_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `so_number` | `VARCHAR(80)` | Yes | No | No | Yes |
| `customer_id` | `INTEGER` | No | No | Yes | No |
| `customer_name` | `VARCHAR(255)` | Yes | No | No | No |
| `customer_po_number` | `VARCHAR(100)` | Yes | No | No | No |
| `order_date` | `DATETIME` | No | No | No | No |
| `expected_delivery_date` | `DATETIME` | Yes | No | No | No |
| `delivery_date` | `DATETIME` | Yes | No | No | No |
| `warehouse_id` | `INTEGER` | Yes | No | Yes | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `subtotal` | `NUMERIC(14, 2)` | Yes | No | No | No |
| `discount_total` | `NUMERIC(14, 2)` | Yes | No | No | No |
| `tax_total` | `NUMERIC(14, 2)` | Yes | No | No | No |
| `grand_total` | `NUMERIC(14, 2)` | Yes | No | No | No |
| `shipping_address` | `TEXT` | Yes | No | No | No |
| `billing_address` | `TEXT` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `terms` | `TEXT` | Yes | No | No | No |
| `status` | `VARCHAR(50)` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `created_by` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### sales_order_lines

**Primary Key:** id

**Foreign Keys:**
- `product_id` → `commerce.products.id`
- `so_id` → `trading.sales_orders.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `so_id` | `INTEGER` | No | No | Yes | No |
| `product_id` | `INTEGER` | Yes | No | Yes | No |
| `product_name` | `VARCHAR(255)` | Yes | No | No | No |
| `sku` | `VARCHAR(100)` | Yes | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `quantity_ordered` | `NUMERIC(14, 4)` | No | No | No | No |
| `quantity_dispatched` | `NUMERIC(14, 4)` | Yes | No | No | No |
| `unit_price` | `NUMERIC(14, 4)` | No | No | No | No |
| `discount_percent` | `NUMERIC(5, 2)` | Yes | No | No | No |
| `discount_amount` | `NUMERIC(14, 2)` | Yes | No | No | No |
| `tax_rate` | `NUMERIC(5, 2)` | Yes | No | No | No |
| `tax_amount` | `NUMERIC(14, 2)` | Yes | No | No | No |
| `line_total` | `NUMERIC(14, 2)` | Yes | No | No | No |
| `weight` | `NUMERIC(10, 3)` | Yes | No | No | No |
| `volume` | `NUMERIC(10, 3)` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

## Schema: finance

Tables: 40

### trade_deals

**Primary Key:** id

**Foreign Keys:**
- `counterparty_id` → `finance.vendors.id`
- `created_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `deal_number` | `VARCHAR(80)` | Yes | No | No | Yes |
| `counterparty_id` | `INTEGER` | No | No | Yes | No |
| `counterparty_legal_name` | `VARCHAR(255)` | Yes | No | No | No |
| `status` | `VARCHAR(50)` | Yes | No | No | No |
| `deal_date` | `DATETIME` | No | No | No | No |
| `settlement_date` | `DATETIME` | Yes | No | No | No |
| `buy_currency` | `VARCHAR(3)` | Yes | No | No | No |
| `sell_currency` | `VARCHAR(3)` | Yes | No | No | No |
| `buy_amount` | `NUMERIC(14, 2)` | Yes | No | No | No |
| `sell_amount` | `NUMERIC(14, 2)` | Yes | No | No | No |
| `rate` | `NUMERIC(14, 6)` | Yes | No | No | No |
| `total_value` | `NUMERIC(14, 2)` | Yes | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### trade_deal_items

**Primary Key:** id

**Foreign Keys:**
- `deal_id` → `finance.trade_deals.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `deal_id` | `INTEGER` | No | No | Yes | No |
| `asset_code` | `VARCHAR(50)` | No | No | No | No |
| `quantity` | `NUMERIC(14, 4)` | No | No | No | No |
| `unit_price` | `NUMERIC(14, 4)` | No | No | No | No |
| `total_value` | `NUMERIC(14, 2)` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### trade_settlements

**Primary Key:** id

**Foreign Keys:**
- `created_by` → `core.users.id`
- `deal_id` → `finance.trade_deals.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `deal_id` | `INTEGER` | No | No | Yes | No |
| `settlement_date` | `DATETIME` | No | No | No | No |
| `amount` | `NUMERIC(14, 2)` | No | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `status` | `VARCHAR(50)` | Yes | No | No | No |
| `reference_number` | `VARCHAR(100)` | Yes | No | No | No |
| `payment_method` | `VARCHAR(50)` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### trading_configs

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `config_key` | `VARCHAR(100)` | No | No | No | No |
| `config_value` | `TEXT` | Yes | No | No | No |
| `value_type` | `VARCHAR(20)` | Yes | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### finance_reports

**Primary Key:** id

**Foreign Keys:**
- `generated_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `report_type` | `VARCHAR(100)` | No | No | No | No |
| `period_start` | `DATETIME` | No | No | No | No |
| `period_end` | `DATETIME` | No | No | No | No |
| `generated_at` | `DATETIME` | Yes | No | No | No |
| `generated_by` | `INTEGER` | Yes | No | Yes | No |
| `status` | `VARCHAR(50)` | Yes | No | No | No |
| `payload_json` | `TEXT` | Yes | No | No | No |
| `file_url` | `VARCHAR(500)` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### finance_dashboard_metrics

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `metric_key` | `VARCHAR(100)` | No | No | No | No |
| `metric_value` | `NUMERIC(18, 4)` | Yes | No | No | No |
| `metric_label` | `VARCHAR(255)` | Yes | No | No | No |
| `category` | `VARCHAR(50)` | Yes | No | No | No |
| `computed_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### payments

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`
- `order_id` → `commerce.orders.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `order_id` | `INTEGER` | No | No | Yes | No |
| `amount` | `NUMERIC(10, 2)` | No | No | No | No |
| `payment_method` | `VARCHAR` | No | No | No | No |
| `provider` | `VARCHAR` | Yes | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `intent_id` | `VARCHAR` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `layout_json` | `TEXT` | Yes | No | No | No |

### fiscal_periods

**Primary Key:** id

**Foreign Keys:**
- `closed_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | No | No |
| `period_year` | `INTEGER` | No | No | No | No |
| `period_month` | `INTEGER` | No | No | No | No |
| `period_start` | `DATETIME` | No | No | No | No |
| `period_end` | `DATETIME` | No | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `is_locked` | `BOOLEAN` | Yes | No | No | No |
| `closed_at` | `DATETIME` | Yes | No | No | No |
| `closed_by` | `INTEGER` | Yes | No | Yes | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### transaction_ledgers

**Primary Key:** id

**Foreign Keys:**
- `supplier_id` → `core.users.id`
- `order_id` → `commerce.orders.id`
- `user_id` → `core.users.id`
- `shipment_id` → `logistics.shipments.id`
- `logistics_partner_id` → `logistics.logistics_partners.id`
- `order_item_id` → `commerce.order_items.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | Yes | No | Yes | No |
| `supplier_id` | `INTEGER` | Yes | No | Yes | No |
| `logistics_partner_id` | `INTEGER` | Yes | No | Yes | No |
| `order_id` | `INTEGER` | Yes | No | Yes | No |
| `order_item_id` | `INTEGER` | Yes | No | Yes | No |
| `shipment_id` | `INTEGER` | Yes | No | Yes | No |
| `payment_method` | `VARCHAR(20)` | Yes | No | No | No |
| `product_subtotal` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `discount_amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `delivery_pickup_charge` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `delivery_dropoff_charge` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `delivery_total` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `vat_amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `zozi_commission_rate` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `zozi_commission` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `net_supplier_amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `net_logistics_amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `net_zozi_amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `cod_collected_amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `cod_remittance_due` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `settlement_status` | `VARCHAR(30)` | Yes | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `transaction_type` | `VARCHAR` | Yes | No | No | No |
| `reference_id` | `VARCHAR` | Yes | No | No | No |
| `balance_after` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### supplier_settlements

**Primary Key:** id

**Foreign Keys:**
- `payout_id` → `treasury.payouts.id`
- `deleted_by` → `core.users.id`
- `supplier_id` → `core.users.id`
- `ledger_id` → `finance.transaction_ledgers.id`
- `order_id` → `commerce.orders.id`
- `shipment_id` → `logistics.shipments.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `supplier_id` | `INTEGER` | No | No | Yes | No |
| `order_id` | `INTEGER` | Yes | No | Yes | No |
| `ledger_id` | `INTEGER` | Yes | No | Yes | No |
| `payout_id` | `INTEGER` | Yes | No | Yes | No |
| `shipment_id` | `INTEGER` | Yes | No | Yes | No |
| `gross_amount` | `NUMERIC(12, 2)` | No | No | No | No |
| `commission_amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `commission_deducted` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `commission_rate` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `vat_on_commission` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `net_amount` | `NUMERIC(12, 2)` | No | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `settled_at` | `DATETIME` | Yes | No | No | No |
| `eligible_at` | `DATETIME` | Yes | No | No | No |
| `bank_transaction_id` | `INTEGER` | Yes | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `is_deleted` | `BOOLEAN` | Yes | No | No | No |
| `deleted_at` | `DATETIME` | Yes | No | No | No |
| `deleted_by` | `INTEGER` | Yes | No | Yes | No |

### journal_entries

**Primary Key:** id

**Foreign Keys:**
- `reversal_of_id` → `finance.journal_entries.id`
- `period_id` → `finance.fiscal_periods.id`
- `created_by` → `core.users.id`
- `deleted_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `entry_date` | `DATETIME` | No | No | No | No |
| `reference_number` | `VARCHAR(50)` | No | No | No | Yes |
| `description` | `TEXT` | Yes | No | No | No |
| `source` | `VARCHAR(50)` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `is_reconciled` | `BOOLEAN` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | Yes | No |
| `reference_type` | `VARCHAR(50)` | Yes | No | No | No |
| `reference_id` | `INTEGER` | Yes | No | No | No |
| `period_id` | `INTEGER` | Yes | No | Yes | No |
| `reversal_of_id` | `INTEGER` | Yes | No | Yes | No |
| `is_deleted` | `BOOLEAN` | Yes | No | No | No |
| `deleted_at` | `DATETIME` | Yes | No | No | No |
| `deleted_by` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### journal_entry_lines

**Primary Key:** id

**Foreign Keys:**
- `cost_center_id` → `finance.cost_centers.id`
- `entry_id` → `finance.journal_entries.id`
- `account_id` → `finance.accounts.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `entry_id` | `INTEGER` | No | No | Yes | No |
| `account_id` | `INTEGER` | No | No | Yes | No |
| `cost_center_id` | `INTEGER` | Yes | No | Yes | No |
| `amount` | `NUMERIC(12, 2)` | No | No | No | No |
| `side` | `VARCHAR(10)` | No | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `entity_type` | `VARCHAR(50)` | Yes | No | No | No |
| `entity_id` | `INTEGER` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### accounts

**Primary Key:** id

**Foreign Keys:**
- `group_id` → `finance.account_groups.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `group_id` | `INTEGER` | Yes | No | Yes | No |
| `code` | `VARCHAR(20)` | No | No | No | Yes |
| `name` | `VARCHAR(200)` | No | No | No | No |
| `normal_side` | `VARCHAR(10)` | No | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `display_order` | `INTEGER` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### account_groups

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `code` | `VARCHAR(10)` | No | No | No | Yes |
| `name` | `VARCHAR(100)` | No | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `account_type` | `VARCHAR(30)` | No | No | No | No |
| `normal_side` | `VARCHAR(10)` | No | No | No | No |
| `display_order` | `INTEGER` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### account_balances

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`
- `account_id` → `finance.accounts.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `account_id` | `INTEGER` | No | No | Yes | No |
| `user_id` | `INTEGER` | Yes | No | Yes | No |
| `balance` | `NUMERIC(16, 4)` | Yes | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `last_entry_id` | `INTEGER` | Yes | No | No | No |
| `last_entry_at` | `DATETIME` | Yes | No | No | No |
| `last_updated` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### ar_ledger_entries

**Primary Key:** id

**Foreign Keys:**
- `order_id` → `commerce.orders.id`
- `created_by` → `core.users.id`
- `customer_id` → `core.users.id`
- `invoice_id` → `finance.invoices.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `customer_id` | `INTEGER` | No | No | Yes | No |
| `order_id` | `INTEGER` | Yes | No | Yes | No |
| `invoice_id` | `INTEGER` | Yes | No | Yes | No |
| `reference_type` | `VARCHAR(50)` | Yes | No | No | No |
| `reference_id` | `INTEGER` | Yes | No | No | No |
| `entry_type` | `VARCHAR(20)` | No | No | No | No |
| `amount` | `NUMERIC(12, 2)` | No | No | No | No |
| `balance_after` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `due_date` | `DATETIME` | Yes | No | No | No |
| `settled_at` | `DATETIME` | Yes | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `is_deleted` | `BOOLEAN` | Yes | No | No | No |
| `deleted_at` | `DATETIME` | Yes | No | No | No |

### ap_ledger_entries

**Primary Key:** id

**Foreign Keys:**
- `invoice_id` → `finance.invoices.id`
- `supplier_id` → `core.users.id`
- `settlement_id` → `finance.supplier_settlements.id`
- `order_id` → `commerce.orders.id`
- `created_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `supplier_id` | `INTEGER` | No | No | Yes | No |
| `order_id` | `INTEGER` | Yes | No | Yes | No |
| `invoice_id` | `INTEGER` | Yes | No | Yes | No |
| `settlement_id` | `INTEGER` | Yes | No | Yes | No |
| `reference_type` | `VARCHAR(50)` | Yes | No | No | No |
| `reference_id` | `INTEGER` | Yes | No | No | No |
| `entry_type` | `VARCHAR(20)` | No | No | No | No |
| `amount` | `NUMERIC(12, 2)` | No | No | No | No |
| `balance_after` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `due_date` | `DATETIME` | Yes | No | No | No |
| `paid_at` | `DATETIME` | Yes | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `is_deleted` | `BOOLEAN` | Yes | No | No | No |
| `deleted_at` | `DATETIME` | Yes | No | No | No |

### invoices

**Primary Key:** id

**Foreign Keys:**
- `supplier_id` → `core.users.id`
- `order_id` → `commerce.orders.id`
- `shipment_id` → `logistics.shipments.id`
- `deleted_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `order_id` | `INTEGER` | No | No | Yes | No |
| `shipment_id` | `INTEGER` | Yes | No | Yes | No |
| `supplier_id` | `INTEGER` | Yes | No | Yes | No |
| `invoice_number` | `VARCHAR` | Yes | No | No | Yes |
| `invoice_type` | `VARCHAR` | Yes | No | No | No |
| `subtotal` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `tax_amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `shipping_amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `discount_amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `total_amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `issued_at` | `DATETIME` | Yes | No | No | No |
| `due_at` | `DATETIME` | Yes | No | No | No |
| `picked_at` | `DATETIME` | Yes | No | No | No |
| `dispatched_at` | `DATETIME` | Yes | No | No | No |
| `delivered_at` | `DATETIME` | Yes | No | No | No |
| `paid_at` | `DATETIME` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `is_deleted` | `BOOLEAN` | Yes | No | No | No |
| `deleted_at` | `DATETIME` | Yes | No | No | No |
| `deleted_by` | `INTEGER` | Yes | No | Yes | No |

### invoice_items

**Primary Key:** id

**Foreign Keys:**
- `invoice_id` → `finance.invoices.id`
- `product_id` → `commerce.products.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `invoice_id` | `INTEGER` | No | No | Yes | No |
| `product_id` | `INTEGER` | Yes | No | Yes | No |
| `description` | `VARCHAR` | No | No | No | No |
| `quantity` | `INTEGER` | Yes | No | No | No |
| `unit_price` | `NUMERIC(10, 2)` | No | No | No | No |
| `discount_amount` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `tax_rate` | `NUMERIC(5, 2)` | Yes | No | No | No |
| `line_total` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### refund_ledger

**Primary Key:** id

**Foreign Keys:**
- `order_id` → `commerce.orders.id`
- `performed_by` → `core.users.id`
- `deleted_by` → `core.users.id`
- `return_request_id` → `commerce.return_requests.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `order_id` | `INTEGER` | No | No | Yes | No |
| `return_request_id` | `INTEGER` | Yes | No | Yes | No |
| `ledger_id` | `INTEGER` | Yes | No | No | No |
| `bank_transaction_id` | `INTEGER` | Yes | No | No | No |
| `reason` | `TEXT` | Yes | No | No | No |
| `refund_reason` | `TEXT` | Yes | No | No | No |
| `refund_method` | `VARCHAR` | Yes | No | No | No |
| `customer_refund_amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `supplier_reversal` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `logistics_reversal` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `delivery_fee_reversal` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `commission_reversal` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `vat_adjustment` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `vat_reversal` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `performed_by` | `INTEGER` | Yes | No | Yes | No |
| `processed_at` | `DATETIME` | Yes | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `is_deleted` | `BOOLEAN` | Yes | No | No | No |
| `deleted_at` | `DATETIME` | Yes | No | No | No |
| `deleted_by` | `INTEGER` | Yes | No | Yes | No |

### bank_transactions

**Primary Key:** id

**Foreign Keys:**
- `reconciled_by` → `core.users.id`
- `linked_order_id` → `commerce.orders.id`
- `linked_supplier_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `transaction_ref` | `VARCHAR` | Yes | No | No | No |
| `source` | `VARCHAR` | Yes | No | No | No |
| `transaction_type` | `VARCHAR` | No | No | No | No |
| `category` | `VARCHAR` | Yes | No | No | No |
| `amount` | `NUMERIC(12, 2)` | No | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `linked_order_id` | `INTEGER` | Yes | No | Yes | No |
| `linked_supplier_id` | `INTEGER` | Yes | No | Yes | No |
| `linked_logistics_id` | `INTEGER` | Yes | No | No | No |
| `linked_payout_id` | `INTEGER` | Yes | No | No | No |
| `linked_refund_id` | `INTEGER` | Yes | No | No | No |
| `reconciled` | `BOOLEAN` | Yes | No | No | No |
| `reconciled_by` | `INTEGER` | Yes | No | Yes | No |
| `reconciled_at` | `DATETIME` | Yes | No | No | No |
| `transaction_date` | `DATETIME` | Yes | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `flagged` | `BOOLEAN` | Yes | No | No | No |
| `flag_reason` | `TEXT` | Yes | No | No | No |

### vat_remittances

**Primary Key:** id

**Foreign Keys:**
- `remitted_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `period_start` | `DATETIME` | No | No | No | No |
| `period_end` | `DATETIME` | No | No | No | No |
| `vat_collected_amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `vat_adjustment_amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `amount_due` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `amount` | `NUMERIC(12, 2)` | No | No | No | No |
| `amount_remitted` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `bank_transaction_id` | `INTEGER` | Yes | No | No | No |
| `remitted_by` | `INTEGER` | Yes | No | Yes | No |
| `remitted_at` | `DATETIME` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### pending_journal_entries

**Primary Key:** id

**Foreign Keys:**
- `journal_entry_id` → `finance.journal_entries.id`
- `rejected_by` → `core.users.id`
- `created_by` → `core.users.id`
- `approved_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `lines_json` | `TEXT` | No | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `source` | `VARCHAR(50)` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `entry_date` | `DATETIME` | No | No | No | No |
| `amount_threshold_triggered` | `BOOLEAN` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `created_by` | `INTEGER` | No | No | Yes | No |
| `approved_by` | `INTEGER` | Yes | No | Yes | No |
| `rejected_by` | `INTEGER` | Yes | No | Yes | No |
| `rejection_reason` | `TEXT` | Yes | No | No | No |
| `approved_at` | `DATETIME` | Yes | No | No | No |
| `journal_entry_id` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### bank_mapping_rules

**Primary Key:** id

**Foreign Keys:**
- `created_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `name` | `VARCHAR(120)` | No | No | No | No |
| `match_pattern` | `VARCHAR(300)` | No | No | No | No |
| `description_contains` | `VARCHAR(300)` | Yes | No | No | No |
| `account_code` | `VARCHAR(20)` | No | No | No | No |
| `normal_side` | `VARCHAR(10)` | No | No | No | No |
| `category` | `VARCHAR(40)` | Yes | No | No | No |
| `priority` | `INTEGER` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### bank_statement_imports

**Primary Key:** id

**Foreign Keys:**
- `imported_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `bank_name` | `VARCHAR(120)` | Yes | No | No | No |
| `file_name` | `VARCHAR(255)` | Yes | No | No | No |
| `statement_period_start` | `DATETIME` | Yes | No | No | No |
| `statement_period_end` | `DATETIME` | Yes | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `total_lines` | `INTEGER` | Yes | No | No | No |
| `matched_lines` | `INTEGER` | Yes | No | No | No |
| `unmatched_lines` | `INTEGER` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `imported_by` | `INTEGER` | Yes | No | Yes | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### bank_statement_lines

**Primary Key:** id

**Foreign Keys:**
- `reconciled_transaction_id` → `finance.bank_transactions.id`
- `import_id` → `finance.bank_statement_imports.id`
- `posted_journal_entry_id` → `finance.journal_entries.id`
- `mapping_rule_id` → `finance.bank_mapping_rules.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `import_id` | `INTEGER` | No | No | Yes | No |
| `txn_date` | `DATETIME` | Yes | No | No | No |
| `description` | `VARCHAR(500)` | Yes | No | No | No |
| `reference` | `VARCHAR(120)` | Yes | No | No | No |
| `amount` | `NUMERIC(14, 2)` | No | No | No | No |
| `mapped_account_code` | `VARCHAR(20)` | Yes | No | No | No |
| `mapped_side` | `VARCHAR(10)` | Yes | No | No | No |
| `mapping_rule_id` | `INTEGER` | Yes | No | Yes | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `posted_journal_entry_id` | `INTEGER` | Yes | No | Yes | No |
| `reconciled_transaction_id` | `INTEGER` | Yes | No | Yes | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### fixed_assets

**Primary Key:** id

**Foreign Keys:**
- `created_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `name` | `VARCHAR(200)` | No | No | No | No |
| `asset_code` | `VARCHAR(40)` | Yes | No | No | No |
| `category` | `VARCHAR(40)` | Yes | No | No | No |
| `purchase_date` | `DATETIME` | No | No | No | No |
| `purchase_cost` | `NUMERIC(14, 2)` | No | No | No | No |
| `salvage_value` | `NUMERIC(14, 2)` | Yes | No | No | No |
| `useful_life_months` | `INTEGER` | No | No | No | No |
| `accumulated_depreciation` | `NUMERIC(14, 2)` | Yes | No | No | No |
| `last_depreciated_date` | `DATETIME` | Yes | No | No | No |
| `asset_account_code` | `VARCHAR(20)` | Yes | No | No | No |
| `depreciation_account_code` | `VARCHAR(20)` | Yes | No | No | No |
| `accumulated_depr_account_code` | `VARCHAR(20)` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### accruals

**Primary Key:** id

**Foreign Keys:**
- `created_by` → `core.users.id`
- `journal_entry_id` → `finance.journal_entries.id`
- `reversal_entry_id` → `finance.journal_entries.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `accrual_type` | `VARCHAR(20)` | No | No | No | No |
| `description` | `VARCHAR(500)` | Yes | No | No | No |
| `amount` | `NUMERIC(14, 2)` | No | No | No | No |
| `expense_account_code` | `VARCHAR(20)` | No | No | No | No |
| `accrual_account_code` | `VARCHAR(20)` | No | No | No | No |
| `accrual_date` | `DATETIME` | No | No | No | No |
| `reversal_date` | `DATETIME` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `journal_entry_id` | `INTEGER` | Yes | No | Yes | No |
| `reversal_entry_id` | `INTEGER` | Yes | No | Yes | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### scanned_expenses

**Primary Key:** id

**Foreign Keys:**
- `employee_id` → `logistics.employees.id`
- `reviewed_by` → `core.users.id`
- `posted_journal_entry_id` → `finance.journal_entries.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `employee_id` | `INTEGER` | Yes | No | Yes | No |
| `vendor_name` | `VARCHAR(200)` | Yes | No | No | No |
| `invoice_number` | `VARCHAR(100)` | Yes | No | No | No |
| `expense_date` | `DATETIME` | Yes | No | No | No |
| `amount` | `NUMERIC(14, 2)` | No | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `tax_amount` | `NUMERIC(14, 2)` | Yes | No | No | No |
| `category` | `VARCHAR(50)` | Yes | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `expense_account_code` | `VARCHAR(20)` | Yes | No | No | No |
| `image_url` | `VARCHAR(500)` | Yes | No | No | No |
| `ocr_raw_text` | `TEXT` | Yes | No | No | No |
| `ocr_confidence` | `NUMERIC(5, 2)` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `posted_journal_entry_id` | `INTEGER` | Yes | No | Yes | No |
| `reviewed_by` | `INTEGER` | Yes | No | Yes | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### vendors

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `name` | `VARCHAR(200)` | No | No | No | No |
| `tax_id` | `VARCHAR(60)` | Yes | No | No | No |
| `contact_email` | `VARCHAR(160)` | Yes | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `payment_terms_days` | `INTEGER` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### customers

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `name` | `VARCHAR(200)` | No | No | No | No |
| `tax_id` | `VARCHAR(60)` | Yes | No | No | No |
| `contact_email` | `VARCHAR(160)` | Yes | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `payment_terms_days` | `INTEGER` | Yes | No | No | No |
| `credit_limit` | `NUMERIC(14, 2)` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### cost_centers

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `code` | `VARCHAR(30)` | No | No | No | No |
| `name` | `VARCHAR(160)` | No | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### ap_bills

**Primary Key:** id

**Foreign Keys:**
- `linked_journal_entry_id` → `finance.journal_entries.id`
- `created_by` → `core.users.id`
- `paid_journal_entry_id` → `finance.journal_entries.id`
- `vendor_id` → `finance.vendors.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `vendor_id` | `INTEGER` | No | No | Yes | No |
| `bill_number` | `VARCHAR(80)` | Yes | No | No | No |
| `bill_date` | `DATETIME` | No | No | No | No |
| `due_date` | `DATETIME` | Yes | No | No | No |
| `account_code` | `VARCHAR(20)` | No | No | No | No |
| `amount` | `NUMERIC(14, 2)` | No | No | No | No |
| `tax_amount` | `NUMERIC(14, 2)` | Yes | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `linked_journal_entry_id` | `INTEGER` | Yes | No | Yes | No |
| `paid_journal_entry_id` | `INTEGER` | Yes | No | Yes | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### ar_invoices

**Primary Key:** id

**Foreign Keys:**
- `customer_id` → `finance.customers.id`
- `paid_journal_entry_id` → `finance.journal_entries.id`
- `linked_journal_entry_id` → `finance.journal_entries.id`
- `created_by` → `core.users.id`
- `reference_order_id` → `commerce.orders.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `customer_id` | `INTEGER` | No | No | Yes | No |
| `invoice_number` | `VARCHAR(80)` | Yes | No | No | No |
| `invoice_date` | `DATETIME` | No | No | No | No |
| `due_date` | `DATETIME` | Yes | No | No | No |
| `account_code` | `VARCHAR(20)` | Yes | No | No | No |
| `amount` | `NUMERIC(14, 2)` | No | No | No | No |
| `tax_amount` | `NUMERIC(14, 2)` | Yes | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `linked_journal_entry_id` | `INTEGER` | Yes | No | Yes | No |
| `paid_journal_entry_id` | `INTEGER` | Yes | No | Yes | No |
| `reference_order_id` | `INTEGER` | Yes | No | Yes | No |
| `vat_amount` | `NUMERIC(14, 2)` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### bank_accounts

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `bank_name` | `VARCHAR(160)` | No | No | No | No |
| `account_name` | `VARCHAR(200)` | Yes | No | No | No |
| `account_number` | `VARCHAR(60)` | Yes | No | No | No |
| `iban` | `VARCHAR(60)` | Yes | No | No | No |
| `swift_bic` | `VARCHAR(20)` | Yes | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `gl_account_code` | `VARCHAR(20)` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### budgets

**Primary Key:** id

**Foreign Keys:**
- `fiscal_period_id` → `finance.fiscal_periods.id`
- `created_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `account_code` | `VARCHAR(20)` | No | No | No | No |
| `fiscal_period_id` | `INTEGER` | No | No | Yes | No |
| `amount` | `NUMERIC(16, 4)` | No | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### bank_reconciliations

**Primary Key:** id

**Foreign Keys:**
- `statement_line_id` → `finance.bank_statement_lines.id`
- `journal_entry_id` → `finance.journal_entries.id`
- `matched_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `statement_line_id` | `INTEGER` | No | No | Yes | No |
| `journal_entry_id` | `INTEGER` | Yes | No | Yes | No |
| `matched_amount` | `NUMERIC(14, 2)` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `note` | `TEXT` | Yes | No | No | No |
| `matched_by` | `INTEGER` | Yes | No | Yes | No |
| `matched_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### recurring_templates

**Primary Key:** id

**Foreign Keys:**
- `created_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `name` | `VARCHAR(200)` | No | No | No | No |
| `frequency` | `VARCHAR(20)` | Yes | No | No | No |
| `next_run_date` | `DATETIME` | Yes | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `lines` | `JSON` | No | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### finance_audit_logs

**Primary Key:** id

**Foreign Keys:**
- `actor_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `action` | `VARCHAR(60)` | No | No | No | No |
| `actor_id` | `INTEGER` | Yes | No | Yes | No |
| `actor_role` | `VARCHAR(40)` | Yes | No | No | No |
| `entity_type` | `VARCHAR(40)` | Yes | No | No | No |
| `entity_id` | `INTEGER` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `detail` | `JSON` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### finance_automation_logs

**Primary Key:** id

**Foreign Keys:**
- `run_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `kind` | `VARCHAR(40)` | No | No | No | No |
| `records_processed` | `INTEGER` | Yes | No | No | No |
| `records_changed` | `INTEGER` | Yes | No | No | No |
| `detail` | `JSON` | Yes | No | No | No |
| `run_by` | `INTEGER` | Yes | No | Yes | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

## Schema: treasury

Tables: 15

### payment_reconciliation_runs

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `run_date` | `DATETIME` | No | No | No | No |
| `total_amount` | `NUMERIC(15, 2)` | Yes | No | No | No |
| `reconciled_count` | `INTEGER` | Yes | No | No | No |
| `unmatched_count` | `INTEGER` | Yes | No | No | No |
| `processed_count` | `INTEGER` | Yes | No | No | No |
| `stale_pending_orders` | `INTEGER` | Yes | No | No | No |
| `recent_webhook_count` | `INTEGER` | Yes | No | No | No |
| `result_json` | `TEXT` | Yes | No | No | No |
| `started_at` | `DATETIME` | Yes | No | No | No |
| `completed_at` | `DATETIME` | Yes | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### payment_gateway_connections

**Primary Key:** id

**Foreign Keys:**
- `updated_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `provider_code` | `VARCHAR(100)` | No | No | No | No |
| `gateway_name` | `VARCHAR(100)` | No | No | No | No |
| `country_code` | `VARCHAR(10)` | No | No | No | No |
| `environment` | `VARCHAR(20)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `credentials` | `JSON` | Yes | No | No | No |
| `fee_config` | `JSON` | Yes | No | No | No |
| `supported_methods` | `JSON` | Yes | No | No | No |
| `last_sync_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `provider_kind` | `VARCHAR(20)` | No | No | No | No |
| `display_name` | `VARCHAR(120)` | No | No | No | No |
| `is_enabled` | `BOOLEAN` | Yes | No | No | No |
| `supports_customer_checkout` | `BOOLEAN` | Yes | No | No | No |
| `supports_payouts` | `BOOLEAN` | Yes | No | No | No |
| `mode` | `VARCHAR(20)` | No | No | No | No |
| `public_key` | `VARCHAR(500)` | Yes | No | No | No |
| `secret_key` | `VARCHAR(1000)` | Yes | No | No | No |
| `webhook_secret` | `VARCHAR(1000)` | Yes | No | No | No |
| `merchant_id` | `VARCHAR(255)` | Yes | No | No | No |
| `api_base_url` | `VARCHAR(500)` | Yes | No | No | No |
| `webhook_url` | `VARCHAR(500)` | Yes | No | No | No |
| `test_url` | `VARCHAR(500)` | Yes | No | No | No |
| `settlement_cycle` | `VARCHAR(50)` | Yes | No | No | No |
| `supported_currencies_json` | `TEXT` | Yes | No | No | No |
| `extra_config_json` | `TEXT` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `fee_percent` | `NUMERIC(8, 4)` | No | No | No | No |
| `fixed_fee_amount` | `NUMERIC(12, 2)` | No | No | No | No |
| `payout_fee_percent` | `NUMERIC(8, 4)` | No | No | No | No |
| `payout_fixed_fee_amount` | `NUMERIC(12, 2)` | No | No | No | No |
| `pass_fee_to_customer` | `BOOLEAN` | Yes | No | No | No |
| `test_status` | `VARCHAR(20)` | No | No | No | No |
| `test_message` | `VARCHAR(500)` | Yes | No | No | No |
| `last_tested_at` | `DATETIME` | Yes | No | No | No |
| `updated_by` | `INTEGER` | Yes | No | Yes | No |
| `adapter_supported` | `BOOLEAN` | Yes | No | No | No |

### payouts

**Primary Key:** id

**Foreign Keys:**
- `supplier_id` → `core.users.id`
- `order_id` → `commerce.orders.id`
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `batch_number` | `VARCHAR(50)` | Yes | No | No | No |
| `order_id` | `INTEGER` | Yes | No | Yes | No |
| `supplier_id` | `INTEGER` | No | No | Yes | No |
| `amount` | `NUMERIC(12, 2)` | No | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `method` | `VARCHAR` | No | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `reference_id` | `VARCHAR` | Yes | No | No | No |
| `reference` | `VARCHAR` | Yes | No | No | No |
| `provider` | `VARCHAR` | Yes | No | No | No |
| `provider_recipient_id` | `VARCHAR` | Yes | No | No | No |
| `provider_transfer_id` | `VARCHAR` | Yes | No | No | No |
| `provider_status` | `VARCHAR` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `processed_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### payout_rules

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `min_amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `max_amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `fixed_fee` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `percent_fee` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### cash_accounts

**Primary Key:** id

**Foreign Keys:**
- `created_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `name` | `VARCHAR` | No | No | No | No |
| `account_type` | `VARCHAR` | No | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `balance` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### cash_transactions

**Primary Key:** id

**Foreign Keys:**
- `account_id` → `treasury.cash_accounts.id`
- `performed_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `account_id` | `INTEGER` | No | No | Yes | No |
| `transaction_type` | `VARCHAR` | No | No | No | No |
| `amount` | `NUMERIC(12, 2)` | No | No | No | No |
| `balance_after` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `reference` | `VARCHAR` | Yes | No | No | No |
| `category` | `VARCHAR` | Yes | No | No | No |
| `performed_by` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### treasury_accounts

**Primary Key:** id

**Foreign Keys:**
- `employee_id` → `logistics.employees.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `slug` | `VARCHAR` | No | No | No | Yes |
| `name` | `VARCHAR` | No | No | No | No |
| `account_type` | `VARCHAR` | No | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `gl_account_code` | `VARCHAR` | No | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `employee_id` | `INTEGER` | Yes | No | Yes | No |
| `balance` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### treasury_transactions

**Primary Key:** id

**Foreign Keys:**
- `from_account_id` → `treasury.treasury_accounts.id`
- `account_id` → `treasury.treasury_accounts.id`
- `to_account_id` → `treasury.treasury_accounts.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `from_account_id` | `INTEGER` | Yes | No | Yes | No |
| `to_account_id` | `INTEGER` | Yes | No | Yes | No |
| `account_id` | `INTEGER` | Yes | No | Yes | No |
| `transaction_type` | `VARCHAR` | No | No | No | No |
| `amount` | `NUMERIC(12, 2)` | No | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `reference` | `VARCHAR` | Yes | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `posted_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### cash_flow_forecasts

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `forecast_date` | `DATETIME` | No | No | No | No |
| `period_start` | `DATETIME` | No | No | No | No |
| `period_end` | `DATETIME` | No | No | No | No |
| `net_cash_flow` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `opening_balance` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `closing_balance` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### cash_position_snapshots

**Primary Key:** id

**Foreign Keys:**
- `account_id` → `treasury.treasury_accounts.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `snapshot_time` | `DATETIME` | No | No | No | No |
| `account_id` | `INTEGER` | No | No | Yes | No |
| `balance` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### gateway_settlement_schedules

**Primary Key:** id

**Foreign Keys:**
- `gateway_id` → `treasury.payment_gateway_connections.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `gateway_id` | `INTEGER` | No | No | Yes | No |
| `settlement_date` | `DATETIME` | No | No | No | No |
| `amount` | `NUMERIC(12, 2)` | No | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### payout_batches

**Primary Key:** id

**Foreign Keys:**
- `created_by` → `core.users.id`
- `approved_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `batch_number` | `VARCHAR(50)` | No | No | No | Yes |
| `country_code` | `VARCHAR(10)` | No | No | No | No |
| `total_amount` | `NUMERIC(16, 4)` | Yes | No | No | No |
| `item_count` | `INTEGER` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `created_by` | `INTEGER` | No | No | Yes | No |
| `approved_by` | `INTEGER` | Yes | No | Yes | No |
| `dispatched_at` | `DATETIME` | Yes | No | No | No |
| `settled_at` | `DATETIME` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### payout_batch_items

**Primary Key:** id

**Foreign Keys:**
- `batch_id` → `treasury.payout_batches.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `batch_id` | `INTEGER` | No | No | Yes | No |
| `entity_type` | `VARCHAR(20)` | No | No | No | No |
| `entity_id` | `INTEGER` | No | No | No | No |
| `amount` | `NUMERIC(16, 4)` | No | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `reference` | `VARCHAR(100)` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### payment_provider_configs

**Primary Key:** id

**Foreign Keys:**
- `updated_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `provider_name` | `VARCHAR` | No | No | No | No |
| `config` | `JSON` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `updated_by` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### finance_bank_accounts

**Primary Key:** id

**Foreign Keys:**
- `updated_by` → `core.users.id`
- `created_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `account_name` | `VARCHAR` | Yes | No | No | No |
| `account_number` | `VARCHAR` | No | No | No | No |
| `bank_name` | `VARCHAR` | No | No | No | No |
| `account_label` | `VARCHAR` | Yes | No | No | No |
| `branch_name` | `VARCHAR` | Yes | No | No | No |
| `iban` | `VARCHAR` | Yes | No | No | No |
| `swift_code` | `VARCHAR` | Yes | No | No | No |
| `routing_number` | `VARCHAR` | Yes | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `support_email` | `VARCHAR` | Yes | No | No | No |
| `support_phone` | `VARCHAR` | Yes | No | No | No |
| `remittance_reference_prefix` | `VARCHAR` | Yes | No | No | No |
| `instructions` | `TEXT` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `scope` | `VARCHAR` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | Yes | No |
| `updated_by` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

## Schema: supplier

Tables: 7

### supplier_profiles

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`
- `user_id` → `core.users.id`
- `deleted_by_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `business_name` | `VARCHAR` | No | No | No | No |
| `slug` | `VARCHAR` | Yes | No | No | Yes |
| `business_type` | `VARCHAR` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `phone_business` | `VARCHAR` | Yes | No | No | No |
| `website` | `VARCHAR` | Yes | No | No | No |
| `address` | `TEXT` | Yes | No | No | No |
| `city` | `VARCHAR` | Yes | No | No | No |
| `region` | `VARCHAR` | Yes | No | No | No |
| `is_terms_accepted` | `BOOLEAN` | Yes | No | No | No |
| `terms_version` | `VARCHAR` | Yes | No | No | No |
| `verification_status` | `VARCHAR` | Yes | No | No | No |
| `verified_at` | `DATETIME` | Yes | No | No | No |
| `is_deleted` | `BOOLEAN` | Yes | No | No | No |
| `deleted_at` | `DATETIME` | Yes | No | No | No |
| `deleted_by_id` | `INTEGER` | Yes | No | Yes | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `bio` | `TEXT` | Yes | No | No | No |
| `about_us` | `TEXT` | Yes | No | No | No |
| `postal_code` | `VARCHAR` | Yes | No | No | No |
| `tax_id` | `VARCHAR` | Yes | No | No | No |
| `logo_url` | `VARCHAR` | Yes | No | No | No |
| `banner_url` | `VARCHAR` | Yes | No | No | No |
| `video_url` | `VARCHAR` | Yes | No | No | No |
| `certifications` | `JSON` | Yes | No | No | No |
| `social_links` | `JSON` | Yes | No | No | No |
| `established_year` | `INTEGER` | Yes | No | No | No |
| `operating_regions` | `JSON` | Yes | No | No | No |
| `verified_documents` | `JSON` | Yes | No | No | No |
| `document_expires_at` | `DATETIME` | Yes | No | No | No |
| `terms_accepted_at` | `DATETIME` | Yes | No | No | No |
| `badge_level` | `VARCHAR` | Yes | No | No | No |
| `credibility_score` | `INTEGER` | Yes | No | No | No |
| `badge_granted_at` | `DATETIME` | Yes | No | No | No |

### supplier_documents

**Primary Key:** id

**Foreign Keys:**
- `supplier_id` → `supplier.supplier_profiles.id`
- `verified_by` → `core.users.id`
- `reviewed_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `supplier_id` | `INTEGER` | No | No | Yes | No |
| `doc_type` | `VARCHAR` | No | No | No | No |
| `document_name` | `VARCHAR` | Yes | No | No | No |
| `file_url` | `VARCHAR` | No | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `expires_at` | `DATETIME` | Yes | No | No | No |
| `review_note` | `TEXT` | Yes | No | No | No |
| `reviewed_by` | `INTEGER` | Yes | No | Yes | No |
| `reviewed_at` | `DATETIME` | Yes | No | No | No |
| `verified_by` | `INTEGER` | Yes | No | Yes | No |
| `is_verified` | `BOOLEAN` | Yes | No | No | No |
| `verified_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### supplier_notification_preferences

**Primary Key:** id

**Foreign Keys:**
- `supplier_id` → `supplier.supplier_profiles.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `supplier_id` | `INTEGER` | No | No | Yes | No |
| `notify_new_order` | `BOOLEAN` | Yes | No | No | No |
| `notify_low_stock` | `BOOLEAN` | Yes | No | No | No |
| `notify_payout_processed` | `BOOLEAN` | Yes | No | No | No |
| `notify_doc_expiry` | `BOOLEAN` | Yes | No | No | No |
| `notify_return_updates` | `BOOLEAN` | Yes | No | No | No |
| `notify_dispute_updates` | `BOOLEAN` | Yes | No | No | No |
| `in_app_enabled` | `BOOLEAN` | Yes | No | No | No |
| `email_enabled` | `BOOLEAN` | Yes | No | No | No |
| `push_enabled` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### supplier_bank_accounts

**Primary Key:** id

**Foreign Keys:**
- `supplier_id` → `core.users.id`
- `verified_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `supplier_id` | `INTEGER` | No | No | Yes | No |
| `account_number` | `VARCHAR` | Yes | No | No | No |
| `bank_name` | `VARCHAR` | No | No | No | No |
| `beneficiary_name` | `VARCHAR` | Yes | No | No | No |
| `branch_name` | `VARCHAR` | Yes | No | No | No |
| `iban` | `VARCHAR` | Yes | No | No | No |
| `swift_code` | `VARCHAR` | Yes | No | No | No |
| `routing_number` | `VARCHAR` | Yes | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `bank_country` | `VARCHAR(3)` | Yes | No | No | No |
| `verification_status` | `VARCHAR` | Yes | No | No | No |
| `verification_note` | `TEXT` | Yes | No | No | No |
| `provider` | `VARCHAR` | Yes | No | No | No |
| `provider_recipient_id` | `VARCHAR` | Yes | No | No | No |
| `provider_status` | `VARCHAR` | Yes | No | No | No |
| `provider_last_synced_at` | `DATETIME` | Yes | No | No | No |
| `verified_at` | `DATETIME` | Yes | No | No | No |
| `verified_by` | `INTEGER` | Yes | No | Yes | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### supplier_disputes

**Primary Key:** id

**Foreign Keys:**
- `return_request_id` → `commerce.return_requests.id`
- `resolved_by` → `core.users.id`
- `created_by` → `core.users.id`
- `order_id` → `commerce.orders.id`
- `supplier_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `supplier_id` | `INTEGER` | No | No | Yes | No |
| `order_id` | `INTEGER` | Yes | No | Yes | No |
| `dispute_type` | `VARCHAR(40)` | Yes | No | No | No |
| `priority` | `VARCHAR(20)` | Yes | No | No | No |
| `title` | `VARCHAR(200)` | Yes | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `return_request_id` | `INTEGER` | Yes | No | Yes | No |
| `verification_id` | `INTEGER` | Yes | No | No | No |
| `invoice_id` | `INTEGER` | Yes | No | No | No |
| `related_order_id` | `INTEGER` | Yes | No | No | No |
| `evidence_urls` | `JSON` | Yes | No | No | No |
| `metadata_json` | `JSON` | Yes | No | No | No |
| `supplier_notes` | `TEXT` | Yes | No | No | No |
| `admin_notes` | `TEXT` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | Yes | No |
| `reason` | `TEXT` | Yes | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `resolved_by` | `INTEGER` | Yes | No | Yes | No |
| `resolved_at` | `DATETIME` | Yes | No | No | No |
| `resolution_notes` | `TEXT` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### supplier_country_commissions

**Primary Key:** id

**Foreign Keys:**
- `supplier_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `supplier_id` | `INTEGER` | No | No | Yes | No |
| `country_code` | `VARCHAR(10)` | No | No | No | No |
| `commission_rate` | `NUMERIC(5, 2)` | No | No | No | No |
| `category_slug` | `VARCHAR(100)` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### supplier_fraud_indicators

**Primary Key:** id

**Foreign Keys:**
- `supplier_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `supplier_id` | `INTEGER` | No | No | Yes | No |
| `indicator_type` | `VARCHAR(50)` | No | No | No | No |
| `value` | `VARCHAR` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

## Schema: communication

Tables: 42

### email_campaigns

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`
- `created_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `name` | `VARCHAR` | No | No | No | No |
| `subject` | `VARCHAR` | No | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `send_at` | `DATETIME` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `from_email` | `VARCHAR(200)` | Yes | No | No | No |
| `from_name` | `VARCHAR(200)` | Yes | No | No | No |
| `target_audience` | `TEXT` | Yes | No | No | No |
| `scheduled_at` | `DATETIME` | Yes | No | No | No |
| `sent_at` | `DATETIME` | Yes | No | No | No |
| `sent_count` | `INTEGER` | Yes | No | No | No |
| `open_count` | `INTEGER` | Yes | No | No | No |
| `click_count` | `INTEGER` | Yes | No | No | No |

### email_templates

**Primary Key:** id

**Foreign Keys:**
- `created_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `name` | `VARCHAR(200)` | No | No | No | Yes |
| `subject` | `VARCHAR(500)` | No | No | No | No |
| `content` | `TEXT` | Yes | No | No | No |
| `template_type` | `VARCHAR(50)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### newsletter_subscribers

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `email` | `VARCHAR` | No | No | No | Yes |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `subscribed_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### email_campaign_logs

**Primary Key:** id

**Foreign Keys:**
- `campaign_id` → `communication.email_campaigns.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `campaign_id` | `INTEGER` | No | No | Yes | No |
| `recipient_email` | `VARCHAR` | No | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `sent_at` | `DATETIME` | Yes | No | No | No |
| `delivered_at` | `DATETIME` | Yes | No | No | No |
| `opened_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### campaign_recipients

**Primary Key:** id

**Foreign Keys:**
- `campaign_id` → `communication.email_campaigns.id`
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `campaign_id` | `INTEGER` | No | No | Yes | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `email` | `VARCHAR` | No | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `sent_at` | `DATETIME` | Yes | No | No | No |
| `delivered_at` | `DATETIME` | Yes | No | No | No |
| `opened_at` | `DATETIME` | Yes | No | No | No |
| `clicked_at` | `DATETIME` | Yes | No | No | No |
| `bounced_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### email_delivery_events

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `event_type` | `VARCHAR` | No | No | No | No |
| `recipient_email` | `VARCHAR` | No | No | No | No |
| `subject` | `VARCHAR` | Yes | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `details` | `JSON` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### email_suppressions

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `email` | `VARCHAR` | No | No | No | No |
| `reason` | `VARCHAR` | No | No | No | No |
| `source` | `VARCHAR` | No | No | No | No |
| `provider` | `VARCHAR` | Yes | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `suppressed_at` | `DATETIME` | Yes | No | No | No |
| `last_event_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### notifications

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `type` | `VARCHAR` | Yes | No | No | No |
| `title` | `VARCHAR` | No | No | No | No |
| `message` | `TEXT` | No | No | No | No |
| `channel` | `VARCHAR` | Yes | No | No | No |
| `priority` | `VARCHAR` | Yes | No | No | No |
| `is_read` | `BOOLEAN` | Yes | No | No | No |
| `read_at` | `DATETIME` | Yes | No | No | No |
| `link` | `VARCHAR` | Yes | No | No | No |
| `template` | `VARCHAR` | Yes | No | No | No |
| `variables` | `JSON` | Yes | No | No | No |
| `scheduled_at` | `DATETIME` | Yes | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### ticket_messages

**Primary Key:** id

**Foreign Keys:**
- `ticket_id` → `communication.support_tickets.id`
- `sender_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `ticket_id` | `INTEGER` | No | No | Yes | No |
| `sender_id` | `INTEGER` | No | No | Yes | No |
| `message` | `TEXT` | No | No | No | No |
| `is_admin` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### announcements

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `title` | `VARCHAR` | No | No | No | No |
| `content` | `TEXT` | No | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `starts_at` | `DATETIME` | Yes | No | No | No |
| `ends_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### faqs

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `question` | `TEXT` | No | No | No | No |
| `answer` | `TEXT` | No | No | No | No |
| `category` | `VARCHAR` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `sort_order` | `INTEGER` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### help_categories

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `name` | `VARCHAR` | No | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `sort_order` | `INTEGER` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### proxy_channels

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `entity_type` | `VARCHAR` | No | No | No | No |
| `entity_id` | `INTEGER` | No | No | No | No |
| `proxy_phone` | `VARCHAR` | No | No | No | Yes |
| `proxy_email` | `VARCHAR` | No | No | No | Yes |
| `participants` | `JSON` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### proxy_sessions

**Primary Key:** id

**Foreign Keys:**
- `channel_id` → `communication.proxy_channels.id`
- `participant_one_id` → `core.users.id`
- `participant_two_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `channel_id` | `INTEGER` | No | No | Yes | No |
| `participant_one_id` | `INTEGER` | No | No | Yes | No |
| `participant_two_id` | `INTEGER` | No | No | Yes | No |
| `started_at` | `DATETIME` | Yes | No | No | No |
| `ended_at` | `DATETIME` | Yes | No | No | No |
| `is_encrypted` | `BOOLEAN` | Yes | No | No | No |
| `session_metadata` | `JSON` | Yes | No | No | No |

### proxy_messages

**Primary Key:** id

**Foreign Keys:**
- `recipient_id` → `core.users.id`
- `sender_id` → `core.users.id`
- `session_id` → `communication.proxy_sessions.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `session_id` | `INTEGER` | No | No | Yes | No |
| `sender_id` | `INTEGER` | No | No | Yes | No |
| `recipient_id` | `INTEGER` | No | No | Yes | No |
| `message_type` | `VARCHAR` | Yes | No | No | No |
| `content` | `TEXT` | No | No | No | No |
| `is_masked` | `BOOLEAN` | Yes | No | No | No |
| `read_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### proxy_call_logs

**Primary Key:** id

**Foreign Keys:**
- `caller_id` → `core.users.id`
- `callee_id` → `core.users.id`
- `channel_id` → `communication.proxy_channels.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `channel_id` | `INTEGER` | No | No | Yes | No |
| `caller_id` | `INTEGER` | No | No | Yes | No |
| `callee_id` | `INTEGER` | No | No | Yes | No |
| `direction` | `VARCHAR` | No | No | No | No |
| `duration_seconds` | `INTEGER` | Yes | No | No | No |
| `call_recording_url` | `VARCHAR` | Yes | No | No | No |
| `is_recorded` | `BOOLEAN` | Yes | No | No | No |
| `started_at` | `DATETIME` | Yes | No | No | No |
| `ended_at` | `DATETIME` | Yes | No | No | No |

### employee_communication_threads

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `entity_type` | `VARCHAR(50)` | No | No | No | No |
| `entity_id` | `INTEGER` | No | No | No | No |
| `participants` | `TEXT` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `last_message_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### external_contact_masking

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `external_contact_type` | `VARCHAR(50)` | No | No | No | No |
| `external_contact_id` | `INTEGER` | No | No | No | No |
| `masked_phone` | `VARCHAR(20)` | Yes | No | No | No |
| `masked_email` | `VARCHAR(255)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### communication_audit_trail

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `entity_type` | `VARCHAR(50)` | No | No | No | No |
| `entity_id` | `INTEGER` | No | No | No | No |
| `user_id` | `INTEGER` | Yes | No | Yes | No |
| `action` | `VARCHAR(50)` | No | No | No | No |
| `channel` | `VARCHAR(50)` | No | No | No | No |
| `content_preview` | `TEXT` | Yes | No | No | No |
| `metadata_json` | `JSON` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### internal_channels

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `entity_type` | `VARCHAR(50)` | No | No | No | No |
| `entity_id` | `INTEGER` | No | No | No | No |
| `name` | `VARCHAR(200)` | No | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### internal_channel_members

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`
- `channel_id` → `communication.internal_channels.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `channel_id` | `INTEGER` | No | No | Yes | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `role` | `VARCHAR(20)` | Yes | No | No | No |
| `joined_at` | `DATETIME` | Yes | No | No | No |

### internal_messages

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`
- `channel_id` → `communication.internal_channels.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `channel_id` | `INTEGER` | No | No | Yes | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `message` | `TEXT` | No | No | No | No |
| `message_type` | `VARCHAR(20)` | Yes | No | No | No |
| `is_masked` | `BOOLEAN` | Yes | No | No | No |
| `read_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### chat_attachments

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `message_id` | `INTEGER` | No | No | No | No |
| `message_type` | `VARCHAR(20)` | No | No | No | No |
| `attachment_type` | `VARCHAR(20)` | No | No | No | No |
| `file_url` | `VARCHAR(500)` | No | No | No | No |
| `file_name` | `VARCHAR(200)` | No | No | No | No |
| `file_size_bytes` | `INTEGER` | No | No | No | No |
| `mime_type` | `VARCHAR(100)` | No | No | No | No |
| `thumbnail_url` | `VARCHAR(500)` | Yes | No | No | No |
| `duration_seconds` | `INTEGER` | Yes | No | No | No |
| `waveform_json` | `TEXT` | Yes | No | No | No |
| `is_processed` | `BOOLEAN` | Yes | No | No | No |

### internal_emails

**Primary Key:** id

**Foreign Keys:**
- `in_reply_to` → `communication.internal_emails.id`
- `sender_id` → `core.users.id`
- `folder_id` → `communication.email_folders.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `sender_id` | `INTEGER` | No | No | Yes | No |
| `subject` | `VARCHAR(200)` | No | No | No | No |
| `body_html` | `TEXT` | Yes | No | No | No |
| `body_text` | `TEXT` | Yes | No | No | No |
| `recipients` | `TEXT` | Yes | No | No | No |
| `thread_id` | `VARCHAR(64)` | Yes | No | No | No |
| `is_external` | `BOOLEAN` | Yes | No | No | No |
| `external_message_id` | `VARCHAR(200)` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `folder_id` | `INTEGER` | Yes | No | Yes | No |
| `in_reply_to` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### email_folders

**Primary Key:** id

**Foreign Keys:**
- `employee_id` → `logistics.employees.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `employee_id` | `INTEGER` | No | No | Yes | No |
| `name` | `VARCHAR(50)` | No | No | No | No |
| `folder_type` | `VARCHAR(20)` | Yes | No | No | No |
| `sort_order` | `INTEGER` | Yes | No | No | No |
| `is_system` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### ticket_replies

**Primary Key:** id

**Foreign Keys:**
- `ticket_id` → `communication.support_tickets.id`
- `sender_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `ticket_id` | `INTEGER` | No | No | Yes | No |
| `sender_id` | `INTEGER` | No | No | Yes | No |
| `message` | `TEXT` | No | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### push_notification_tokens

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `token` | `VARCHAR` | No | No | No | No |
| `device_type` | `VARCHAR` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### meeting_recordings

**Primary Key:** id

**Foreign Keys:**
- `started_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `room_id` | `VARCHAR(64)` | No | No | No | No |
| `started_by` | `INTEGER` | No | No | Yes | No |
| `recording_url` | `VARCHAR(500)` | Yes | No | No | No |
| `duration_seconds` | `INTEGER` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `started_at` | `DATETIME` | Yes | No | No | No |
| `ended_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### support_tickets

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `subject` | `VARCHAR` | No | No | No | No |
| `priority` | `VARCHAR` | Yes | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### support_ticket_replies

**Primary Key:** id

**Foreign Keys:**
- `sender_id` → `core.users.id`
- `ticket_id` → `communication.support_tickets.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `ticket_id` | `INTEGER` | No | No | Yes | No |
| `sender_id` | `INTEGER` | No | No | Yes | No |
| `message` | `TEXT` | No | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### ticket_attachments

**Primary Key:** id

**Foreign Keys:**
- `ticket_id` → `communication.support_tickets.id`
- `ticket_reply_id` → `communication.support_ticket_replies.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `ticket_reply_id` | `INTEGER` | Yes | No | Yes | No |
| `ticket_id` | `INTEGER` | Yes | No | Yes | No |
| `file_url` | `VARCHAR` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### news_sources

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `name` | `VARCHAR(100)` | No | No | No | No |
| `url` | `VARCHAR(500)` | No | No | No | No |
| `source_type` | `VARCHAR(20)` | Yes | No | No | No |
| `api_key_required` | `BOOLEAN` | Yes | No | No | No |
| `category` | `VARCHAR(50)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### internal_notices

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `title` | `VARCHAR(200)` | No | No | No | No |
| `content` | `TEXT` | No | No | No | No |
| `priority` | `VARCHAR(20)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `valid_from` | `DATETIME` | Yes | No | No | No |
| `valid_to` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### entity_chat_messages

**Primary Key:** id

**Foreign Keys:**
- `thread_id` → `customer.entity_chat_threads.id`
- `sender_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `thread_id` | `INTEGER` | No | No | Yes | No |
| `sender_id` | `INTEGER` | No | No | Yes | No |
| `message` | `TEXT` | No | No | No | No |
| `message_type` | `VARCHAR(20)` | Yes | No | No | No |
| `read_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### direct_chat_messages

**Primary Key:** id

**Foreign Keys:**
- `room_id` → `customer.direct_chat_rooms.id`
- `sender_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `room_id` | `INTEGER` | No | No | Yes | No |
| `sender_id` | `INTEGER` | No | No | Yes | No |
| `message` | `TEXT` | No | No | No | No |
| `message_type` | `VARCHAR(20)` | Yes | No | No | No |
| `read_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### group_chat_rooms

**Primary Key:** id

**Foreign Keys:**
- `created_by` → `core.users.id`
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `chat_id` | `VARCHAR(64)` | No | No | No | Yes |
| `name` | `VARCHAR(200)` | No | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `is_encrypted` | `BOOLEAN` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_by` | `INTEGER` | No | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### group_chat_messages

**Primary Key:** id

**Foreign Keys:**
- `room_id` → `communication.group_chat_rooms.id`
- `sender_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `room_id` | `INTEGER` | No | No | Yes | No |
| `sender_id` | `INTEGER` | No | No | Yes | No |
| `message` | `TEXT` | No | No | No | No |
| `message_type` | `VARCHAR(20)` | Yes | No | No | No |
| `read_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### escalation_sla_rules

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `priority` | `VARCHAR(20)` | No | No | No | No |
| `escalate_after_minutes` | `INTEGER` | No | No | No | No |
| `escalate_to_role` | `VARCHAR(40)` | No | No | No | No |
| `notify_via` | `VARCHAR(100)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### incident_war_rooms

**Primary Key:** id

**Foreign Keys:**
- `created_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `incident_id` | `VARCHAR` | No | No | No | Yes |
| `title` | `VARCHAR(200)` | No | No | No | No |
| `severity` | `VARCHAR` | Yes | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `created_by` | `INTEGER` | No | No | Yes | No |
| `started_at` | `DATETIME` | Yes | No | No | No |
| `resolved_at` | `DATETIME` | Yes | No | No | No |
| `closed_at` | `DATETIME` | Yes | No | No | No |
| `context_data` | `JSON` | Yes | No | No | No |

### incident_threads

**Primary Key:** id

**Foreign Keys:**
- `participant_id` → `core.users.id`
- `war_room_id` → `communication.incident_war_rooms.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `war_room_id` | `INTEGER` | No | No | Yes | No |
| `participant_id` | `INTEGER` | No | No | Yes | No |
| `message` | `TEXT` | No | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### incident_action_items

**Primary Key:** id

**Foreign Keys:**
- `assignee_id` → `core.users.id`
- `war_room_id` → `communication.incident_war_rooms.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `war_room_id` | `INTEGER` | No | No | Yes | No |
| `assignee_id` | `INTEGER` | Yes | No | Yes | No |
| `title` | `VARCHAR(200)` | No | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `priority` | `VARCHAR` | Yes | No | No | No |
| `due_date` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `completed_at` | `DATETIME` | Yes | No | No | No |

### war_room_templates

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `name` | `VARCHAR(100)` | No | No | No | No |
| `severity` | `VARCHAR` | No | No | No | No |
| `auto_assign` | `BOOLEAN` | Yes | No | No | No |
| `template_data` | `JSON` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

## Schema: configuration

Tables: 21

### email_runtime_config

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `provider` | `VARCHAR(50)` | Yes | No | No | No |
| `resend_api_key` | `VARCHAR` | Yes | No | No | No |
| `resend_webhook_secret` | `VARCHAR` | Yes | No | No | No |
| `smtp_host` | `VARCHAR` | Yes | No | No | No |
| `smtp_port` | `INTEGER` | Yes | No | No | No |
| `smtp_username` | `VARCHAR` | Yes | No | No | No |
| `smtp_password` | `VARCHAR` | Yes | No | No | No |
| `smtp_use_tls` | `BOOLEAN` | Yes | No | No | No |
| `smtp_use_ssl` | `BOOLEAN` | Yes | No | No | No |
| `smtp_timeout_seconds` | `INTEGER` | Yes | No | No | No |
| `email_from_default` | `VARCHAR` | Yes | No | No | No |
| `email_from_promotional` | `VARCHAR` | Yes | No | No | No |
| `email_from_transactional` | `VARCHAR` | Yes | No | No | No |
| `email_from_notification` | `VARCHAR` | Yes | No | No | No |
| `email_from_alert` | `VARCHAR` | Yes | No | No | No |
| `email_from_verification` | `VARCHAR` | Yes | No | No | No |
| `email_from_login_verification` | `VARCHAR` | Yes | No | No | No |
| `email_from_password_reset` | `VARCHAR` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### system_alerts

**Primary Key:** id

**Foreign Keys:**
- `acknowledged_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `alert_type` | `VARCHAR` | No | No | No | No |
| `severity` | `VARCHAR` | Yes | No | No | No |
| `title` | `VARCHAR` | No | No | No | No |
| `message` | `TEXT` | No | No | No | No |
| `is_acknowledged` | `BOOLEAN` | Yes | No | No | No |
| `acknowledged_by` | `INTEGER` | Yes | No | Yes | No |
| `acknowledged_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### system_settings

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `key` | `VARCHAR` | No | No | No | Yes |
| `value` | `TEXT` | Yes | No | No | No |
| `value_type` | `VARCHAR` | Yes | No | No | No |
| `description` | `VARCHAR` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### email_provider_configs

**Primary Key:** id

**Foreign Keys:**
- `updated_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `provider` | `VARCHAR` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `updated_by` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `email_from_default` | `VARCHAR` | Yes | No | No | No |
| `email_from_promotional` | `VARCHAR` | Yes | No | No | No |
| `email_from_transactional` | `VARCHAR` | Yes | No | No | No |
| `email_from_notification` | `VARCHAR` | Yes | No | No | No |
| `email_from_alert` | `VARCHAR` | Yes | No | No | No |
| `email_from_verification` | `VARCHAR` | Yes | No | No | No |
| `email_from_login_verification` | `VARCHAR` | Yes | No | No | No |
| `email_from_password_reset` | `VARCHAR` | Yes | No | No | No |
| `resend_api_key` | `VARCHAR` | Yes | No | No | No |
| `resend_webhook_secret` | `VARCHAR` | Yes | No | No | No |
| `smtp_host` | `VARCHAR` | Yes | No | No | No |
| `smtp_port` | `INTEGER` | Yes | No | No | No |
| `smtp_username` | `VARCHAR` | Yes | No | No | No |
| `smtp_password` | `VARCHAR` | Yes | No | No | No |
| `smtp_use_tls` | `BOOLEAN` | Yes | No | No | No |
| `smtp_use_ssl` | `BOOLEAN` | Yes | No | No | No |
| `smtp_timeout_seconds` | `INTEGER` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### country_feature_flags

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `feature_key` | `VARCHAR(100)` | No | No | No | No |
| `feature_name` | `VARCHAR(200)` | Yes | No | No | No |
| `is_enabled` | `BOOLEAN` | Yes | No | No | No |
| `config` | `TEXT` | Yes | No | No | No |
| `rollout_audience` | `VARCHAR(100)` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### country_staff_assignments

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`
- `country_code` → `country.country_configs.code`
- `assigned_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `role_in_country` | `VARCHAR(40)` | No | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `assigned_by` | `INTEGER` | Yes | No | Yes | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### cross_country_customer_sessions

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`
- `order_id` → `commerce.orders.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `source_country_code` | `VARCHAR(10)` | No | No | No | No |
| `target_country_code` | `VARCHAR(10)` | No | No | No | No |
| `session_data` | `TEXT` | Yes | No | No | No |
| `conversion` | `BOOLEAN` | Yes | No | No | No |
| `order_id` | `INTEGER` | Yes | No | Yes | No |
| `ip_address` | `VARCHAR(45)` | Yes | No | No | No |
| `user_agent` | `VARCHAR(500)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### oman_delivery_zones

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `zone_code` | `VARCHAR(20)` | No | No | No | Yes |
| `zone_name` | `VARCHAR(100)` | No | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `car_rate` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `van_rate` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `truck_rate` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `weight_surcharge_rate` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `weight_surcharge_threshold_kg` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `cities_json` | `TEXT` | Yes | No | No | No |
| `sort_order` | `INTEGER` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### country_config_versions

**Primary Key:** id

**Foreign Keys:**
- `draft_by` → `core.users.id`
- `approved_by` → `core.users.id`
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `config_type` | `VARCHAR(50)` | No | No | No | No |
| `version` | `INTEGER` | No | No | No | No |
| `payload_json` | `TEXT` | No | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `draft_by` | `INTEGER` | Yes | No | Yes | No |
| `approved_by` | `INTEGER` | Yes | No | Yes | No |
| `published_at` | `DATETIME` | Yes | No | No | No |
| `effective_from` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### country_commission_rates

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `supplier_tier` | `VARCHAR(20)` | No | No | No | No |
| `name` | `VARCHAR(50)` | No | No | No | No |
| `rate_percent` | `NUMERIC(5, 2)` | No | No | No | No |
| `fixed_fee` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `effective_from` | `DATETIME` | Yes | No | No | No |
| `effective_to` | `DATETIME` | Yes | No | No | No |

### country_localization

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | Yes |
| `default_numeral_system` | `VARCHAR(20)` | Yes | No | No | No |
| `hijri_calendar_enabled` | `BOOLEAN` | Yes | No | No | No |
| `rtl_layout_enabled` | `BOOLEAN` | Yes | No | No | No |
| `address_format` | `VARCHAR(200)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### country_payment_aliases

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `alias_type` | `VARCHAR(50)` | No | No | No | No |
| `alias_value` | `VARCHAR(200)` | No | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### country_legal_contracts

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `contract_type` | `VARCHAR(50)` | No | No | No | No |
| `version` | `VARCHAR(20)` | Yes | No | No | No |
| `content_html` | `TEXT` | No | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### country_category_tax_rates

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`
- `category_id` → `commerce.categories.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `category_id` | `INTEGER` | No | No | Yes | No |
| `tax_rate` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `tax_name` | `VARCHAR(50)` | Yes | No | No | No |
| `category_slug` | `VARCHAR(100)` | Yes | No | No | No |
| `rate` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `is_exempt` | `BOOLEAN` | Yes | No | No | No |
| `is_reduced` | `BOOLEAN` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `source` | `VARCHAR(50)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### country_holiday_calendars

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `holiday_date` | `DATETIME` | No | No | No | No |
| `name` | `VARCHAR(200)` | No | No | No | No |
| `local_name` | `VARCHAR(200)` | Yes | No | No | No |
| `is_observed` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### country_gateway_configs

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `gateway_id` | `VARCHAR(50)` | No | No | No | No |
| `gateway_name` | `VARCHAR(100)` | No | No | No | No |
| `is_enabled` | `BOOLEAN` | Yes | No | No | No |
| `priority` | `INTEGER` | Yes | No | No | No |
| `credentials` | `TEXT` | Yes | No | No | No |
| `environment` | `VARCHAR(20)` | Yes | No | No | No |
| `settings` | `TEXT` | Yes | No | No | No |
| `last_tested_at` | `DATETIME` | Yes | No | No | No |
| `last_test_result` | `VARCHAR(20)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### country_communication_threads

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `entity_type` | `VARCHAR(50)` | No | No | No | No |
| `entity_id` | `INTEGER` | No | No | No | No |
| `participants` | `TEXT` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `last_message_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### country_commission_rate_history

**Primary Key:** id

**Foreign Keys:**
- `category_id` → `commerce.categories.id`
- `changed_by` → `core.users.id`
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `category_id` | `INTEGER` | Yes | No | Yes | No |
| `supplier_tier` | `VARCHAR(20)` | No | No | No | No |
| `rate_percent` | `NUMERIC(5, 4)` | No | No | No | No |
| `effective_from` | `DATETIME` | No | No | No | No |
| `effective_to` | `DATETIME` | Yes | No | No | No |
| `changed_by` | `INTEGER` | Yes | No | Yes | No |
| `change_reason` | `TEXT` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### country_logistics_zones

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `zone_code` | `VARCHAR(50)` | No | No | No | No |
| `zone_name` | `VARCHAR(200)` | No | No | No | No |
| `zone_type` | `VARCHAR(20)` | Yes | No | No | No |
| `cities` | `TEXT` | Yes | No | No | No |
| `pricing_config` | `TEXT` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### country_payout_rules

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `supplier_tier` | `VARCHAR(20)` | Yes | No | No | No |
| `min_amount` | `NUMERIC(15, 3)` | Yes | No | No | No |
| `max_amount` | `NUMERIC(15, 3)` | Yes | No | No | No |
| `fixed_fee` | `NUMERIC(15, 3)` | Yes | No | No | No |
| `percent_fee` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `settlement_days` | `INTEGER` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### feature_flags

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `flag_key` | `VARCHAR(100)` | No | No | No | Yes |
| `flag_name` | `VARCHAR(255)` | No | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `enabled_for` | `JSON` | Yes | No | No | No |
| `disabled_for` | `JSON` | Yes | No | No | No |
| `rollout_percentage` | `INTEGER` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

## Schema: country

Tables: 14

### country_configs

**Primary Key:** id

**Foreign Keys:**
- `basics_id` → `country.country_basics.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `basics_id` | `INTEGER` | Yes | No | Yes | No |
| `code` | `VARCHAR(10)` | No | No | No | Yes |
| `name` | `VARCHAR` | No | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `currency_symbol` | `VARCHAR(10)` | Yes | No | No | No |
| `phone_code` | `VARCHAR(10)` | Yes | No | No | No |
| `language` | `VARCHAR(10)` | Yes | No | No | No |
| `timezone` | `VARCHAR(60)` | Yes | No | No | No |
| `date_format` | `VARCHAR(20)` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `is_deleted` | `BOOLEAN` | Yes | No | No | No |
| `is_default` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `official_name` | `VARCHAR(200)` | Yes | No | No | No |
| `alpha3` | `VARCHAR(3)` | Yes | No | No | No |
| `flag_url` | `VARCHAR(500)` | Yes | No | No | No |
| `currency_name` | `VARCHAR(50)` | Yes | No | No | No |
| `exchange_rate_to_usd` | `NUMERIC(12, 6)` | Yes | No | No | No |
| `capital` | `VARCHAR(100)` | Yes | No | No | No |
| `region` | `VARCHAR(60)` | Yes | No | No | No |
| `subregion` | `VARCHAR(60)` | Yes | No | No | No |
| `population` | `INTEGER` | Yes | No | No | No |
| `internet_penetration_pct` | `NUMERIC(5, 2)` | Yes | No | No | No |
| `gdp_per_capita_usd` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `urbanization_pct` | `NUMERIC(5, 2)` | Yes | No | No | No |
| `mobile_subs_per_100` | `NUMERIC(5, 2)` | Yes | No | No | No |
| `public_holidays_json` | `TEXT` | Yes | No | No | No |
| `macro_indicators_json` | `TEXT` | Yes | No | No | No |
| `tax_type` | `VARCHAR(20)` | Yes | No | No | No |
| `tax_rate` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `tax_name` | `VARCHAR(50)` | Yes | No | No | No |
| `tax_inclusive` | `BOOLEAN` | Yes | No | No | No |
| `tax_exempt_categories_json` | `TEXT` | Yes | No | No | No |
| `tax_reduced_rates_json` | `TEXT` | Yes | No | No | No |
| `logistics_model` | `VARCHAR(30)` | Yes | No | No | No |
| `default_vehicle_type` | `VARCHAR(30)` | Yes | No | No | No |
| `base_rate` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `per_km_rate` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `minimum_charge` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `weight_surcharge_rate` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `weight_surcharge_threshold_kg` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `payment_methods_json` | `TEXT` | Yes | No | No | No |
| `payment_gateways_json` | `TEXT` | Yes | No | No | No |
| `logistics_providers_json` | `TEXT` | Yes | No | No | No |
| `legal_rules_json` | `TEXT` | Yes | No | No | No |
| `product_restrictions_json` | `TEXT` | Yes | No | No | No |
| `address_format_json` | `TEXT` | Yes | No | No | No |
| `regions_json` | `TEXT` | Yes | No | No | No |
| `supplier_requirements_json` | `TEXT` | Yes | No | No | No |
| `payout_settings_json` | `TEXT` | Yes | No | No | No |
| `commission_tiers_json` | `TEXT` | Yes | No | No | No |
| `suggested_gateway_rankings_json` | `TEXT` | Yes | No | No | No |
| `suggested_commission_ranges_json` | `TEXT` | Yes | No | No | No |
| `consumer_behavior_profile_json` | `TEXT` | Yes | No | No | No |
| `economic_tier` | `VARCHAR(20)` | Yes | No | No | No |
| `fraud_risk_tier` | `VARCHAR(10)` | Yes | No | No | No |
| `suggested_logistics_model` | `VARCHAR(30)` | Yes | No | No | No |
| `data_residency_tier` | `VARCHAR(20)` | Yes | No | No | No |
| `data_residency_encrypted` | `TEXT` | Yes | No | No | No |
| `confidence_score` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `audit_trail_json` | `TEXT` | Yes | No | No | No |
| `cod_enabled` | `BOOLEAN` | Yes | No | No | No |
| `cod_max_amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `cod_verification_required` | `BOOLEAN` | Yes | No | No | No |
| `cod_remittance_days` | `INTEGER` | Yes | No | No | No |
| `settlement_hold_days` | `INTEGER` | Yes | No | No | No |
| `minimum_payout_amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `payout_currency` | `VARCHAR(10)` | Yes | No | No | No |
| `supplier_kyc_tier` | `VARCHAR(20)` | Yes | No | No | No |
| `supplier_onboarding_fee` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `supplier_monthly_fee` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `supplier_rating_threshold` | `NUMERIC(5, 2)` | Yes | No | No | No |
| `legal_entity_required` | `BOOLEAN` | Yes | No | No | No |
| `consumer_protection_days` | `INTEGER` | Yes | No | No | No |
| `data_privacy_framework` | `VARCHAR(20)` | Yes | No | No | No |
| `max_package_weight_kg` | `NUMERIC(8, 2)` | Yes | No | No | No |
| `max_package_dimensions_cm` | `VARCHAR(200)` | Yes | No | No | No |
| `signature_required_threshold` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `measurement_system` | `VARCHAR(10)` | Yes | No | No | No |
| `working_days_json` | `TEXT` | Yes | No | No | No |
| `supported_languages_json` | `TEXT` | Yes | No | No | No |
| `payout_methods_json` | `TEXT` | Yes | No | No | No |
| `logistics_zones_json` | `TEXT` | Yes | No | No | No |

### country_communications

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`
- `from_user_id` → `core.users.id`
- `to_user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `from_user_id` | `INTEGER` | Yes | No | Yes | No |
| `to_user_id` | `INTEGER` | Yes | No | Yes | No |
| `subject` | `VARCHAR(200)` | No | No | No | No |
| `body` | `TEXT` | No | No | No | No |
| `priority` | `VARCHAR(20)` | Yes | No | No | No |
| `category` | `VARCHAR(50)` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `related_entity_type` | `VARCHAR(50)` | Yes | No | No | No |
| `related_entity_id` | `INTEGER` | Yes | No | No | No |
| `read_at` | `DATETIME` | Yes | No | No | No |
| `attachments_json` | `TEXT` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### country_gateway_credentials

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `gateway_name` | `VARCHAR(100)` | No | No | No | No |
| `environment` | `VARCHAR(20)` | Yes | No | No | No |
| `credentials` | `JSON` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### tax_rules

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `tax_name` | `VARCHAR(100)` | No | No | No | No |
| `tax_rate` | `NUMERIC(5, 4)` | No | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### messages

**Primary Key:** id

**Foreign Keys:**
- `to_user_id` → `core.users.id`
- `country_code` → `country.country_configs.code`
- `from_user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | Yes | No |
| `from_user_id` | `INTEGER` | No | No | Yes | No |
| `to_user_id` | `INTEGER` | No | No | Yes | No |
| `subject` | `VARCHAR(200)` | No | No | No | No |
| `body` | `TEXT` | Yes | No | No | No |
| `entity_type` | `VARCHAR(50)` | Yes | No | No | No |
| `entity_id` | `INTEGER` | Yes | No | No | No |
| `priority` | `VARCHAR(20)` | Yes | No | No | No |
| `category` | `VARCHAR(50)` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `read_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### payout_rule_categories

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `category_slug` | `VARCHAR` | No | No | No | No |
| `payout_rate` | `NUMERIC(5, 4)` | No | No | No | No |
| `min_amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `max_amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### payout_rule_products

**Primary Key:** id

**Foreign Keys:**
- `product_id` → `commerce.products.id`
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `product_id` | `INTEGER` | No | No | Yes | No |
| `payout_rate` | `NUMERIC(5, 4)` | No | No | No | No |
| `min_amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `max_amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### supplier_kyc_requirements

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | Yes |
| `kyc_tier_required` | `VARCHAR(20)` | No | No | No | No |
| `document_types_required` | `TEXT` | Yes | No | No | No |
| `verification_wait_days` | `INTEGER` | Yes | No | No | No |
| `auto_approve_threshold` | `NUMERIC(5, 2)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### logistics_partner_kyc_requirements

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | Yes |
| `min_experience_months` | `INTEGER` | Yes | No | No | No |
| `required_documents` | `TEXT` | Yes | No | No | No |
| `insurance_required` | `BOOLEAN` | Yes | No | No | No |
| `insurance_min_coverage` | `NUMERIC(15, 2)` | Yes | No | No | No |
| `vehicle_requirements` | `TEXT` | Yes | No | No | No |
| `background_check_required` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### country_cities

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `name` | `VARCHAR(200)` | No | No | No | No |
| `name_local` | `VARCHAR(200)` | Yes | No | No | No |
| `population` | `INTEGER` | Yes | No | No | No |
| `is_capital` | `BOOLEAN` | Yes | No | No | No |
| `latitude` | `NUMERIC(10, 7)` | Yes | No | No | No |
| `longitude` | `NUMERIC(10, 7)` | Yes | No | No | No |
| `postal_code_prefix` | `VARCHAR(20)` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `region` | `VARCHAR(100)` | Yes | No | No | No |
| `sort_order` | `INTEGER` | Yes | No | No | No |
| `source` | `VARCHAR(50)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### country_basics

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `code` | `VARCHAR(3)` | No | No | No | Yes |
| `name` | `VARCHAR` | No | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `currency_symbol` | `VARCHAR(10)` | Yes | No | No | No |
| `phone_code` | `VARCHAR(10)` | Yes | No | No | No |
| `language` | `VARCHAR(10)` | Yes | No | No | No |
| `timezone` | `VARCHAR(60)` | Yes | No | No | No |
| `date_format` | `VARCHAR(20)` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `is_deleted` | `BOOLEAN` | Yes | No | No | No |
| `is_default` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | No | No |
| `updated_by` | `INTEGER` | Yes | No | No | No |
| `official_name` | `VARCHAR(200)` | Yes | No | No | No |
| `alpha3` | `VARCHAR(3)` | Yes | No | No | No |
| `flag_url` | `VARCHAR(500)` | Yes | No | No | No |
| `currency_name` | `VARCHAR(50)` | Yes | No | No | No |
| `exchange_rate_to_usd` | `NUMERIC(12, 6)` | Yes | No | No | No |
| `capital` | `VARCHAR(100)` | Yes | No | No | No |
| `region` | `VARCHAR(60)` | Yes | No | No | No |
| `subregion` | `VARCHAR(60)` | Yes | No | No | No |
| `population` | `INTEGER` | Yes | No | No | No |
| `internet_penetration_pct` | `NUMERIC(5, 2)` | Yes | No | No | No |
| `gdp_per_capita_usd` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `urbanization_pct` | `NUMERIC(5, 2)` | Yes | No | No | No |
| `mobile_subs_per_100` | `NUMERIC(5, 2)` | Yes | No | No | No |
| `public_holidays_json` | `TEXT` | Yes | No | No | No |
| `macro_indicators_json` | `TEXT` | Yes | No | No | No |

### country_economics

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(3)` | No | No | Yes | Yes |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `is_deleted` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | No | No |
| `updated_by` | `INTEGER` | Yes | No | No | No |
| `economic_tier` | `VARCHAR(20)` | Yes | No | No | No |
| `fraud_risk_tier` | `VARCHAR(10)` | Yes | No | No | No |
| `suggested_logistics_model` | `VARCHAR(30)` | Yes | No | No | No |
| `data_residency_tier` | `VARCHAR(20)` | Yes | No | No | No |
| `data_residency_encrypted` | `TEXT` | Yes | No | No | No |
| `confidence_score` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `audit_trail_json` | `TEXT` | Yes | No | No | No |
| `cod_enabled` | `VARCHAR(1)` | Yes | No | No | No |
| `cod_max_amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `cod_verification_required` | `VARCHAR(1)` | Yes | No | No | No |
| `cod_remittance_days` | `INTEGER` | Yes | No | No | No |
| `settlement_hold_days` | `INTEGER` | Yes | No | No | No |
| `minimum_payout_amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `payout_currency` | `VARCHAR(10)` | Yes | No | No | No |
| `supplier_kyc_tier` | `VARCHAR(20)` | Yes | No | No | No |
| `supplier_onboarding_fee` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `supplier_monthly_fee` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `supplier_rating_threshold` | `NUMERIC(5, 2)` | Yes | No | No | No |
| `legal_entity_required` | `VARCHAR(1)` | Yes | No | No | No |
| `consumer_protection_days` | `INTEGER` | Yes | No | No | No |
| `data_privacy_framework` | `VARCHAR(20)` | Yes | No | No | No |
| `max_package_weight_kg` | `NUMERIC(8, 2)` | Yes | No | No | No |
| `max_package_dimensions_cm` | `VARCHAR(200)` | Yes | No | No | No |
| `signature_required_threshold` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `measurement_system` | `VARCHAR(10)` | Yes | No | No | No |
| `working_days_json` | `TEXT` | Yes | No | No | No |
| `supported_languages_json` | `TEXT` | Yes | No | No | No |
| `payout_methods_json` | `TEXT` | Yes | No | No | No |
| `logistics_zones_json` | `TEXT` | Yes | No | No | No |

### country_legal

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(3)` | No | No | Yes | Yes |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `is_deleted` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | No | No |
| `updated_by` | `INTEGER` | Yes | No | No | No |
| `legal_entity_required` | `VARCHAR(1)` | Yes | No | No | No |
| `consumer_protection_days` | `INTEGER` | Yes | No | No | No |
| `data_privacy_framework` | `VARCHAR(20)` | Yes | No | No | No |
| `gdpr_compliant` | `BOOLEAN` | Yes | No | No | No |
| `local_data_residency` | `BOOLEAN` | Yes | No | No | No |
| `compliance_score` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `legal_risk_tier` | `VARCHAR(10)` | Yes | No | No | No |
| `contract_templates_json` | `TEXT` | Yes | No | No | No |
| `regulatory_bodies_json` | `TEXT` | Yes | No | No | No |

### country_tax

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(3)` | No | No | Yes | Yes |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `is_deleted` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `created_by` | `INTEGER` | Yes | No | No | No |
| `updated_by` | `INTEGER` | Yes | No | No | No |
| `tax_type` | `VARCHAR(20)` | Yes | No | No | No |
| `tax_rate` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `tax_name` | `VARCHAR(50)` | Yes | No | No | No |
| `tax_inclusive` | `BOOLEAN` | Yes | No | No | No |
| `tax_exempt_categories_json` | `TEXT` | Yes | No | No | No |
| `tax_reduced_rates_json` | `TEXT` | Yes | No | No | No |

## Schema: analytics

Tables: 19

### financial_reports

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `report_type` | `VARCHAR` | No | No | No | No |
| `period_start` | `DATETIME` | No | No | No | No |
| `period_end` | `DATETIME` | No | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `data` | `JSON` | Yes | No | No | No |
| `generated_at` | `DATETIME` | Yes | No | No | No |
| `is_deleted` | `BOOLEAN` | Yes | No | No | No |
| `deleted_at` | `DATETIME` | Yes | No | No | No |

### processed_webhook_events

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `processor` | `VARCHAR` | No | No | No | No |
| `event_id` | `VARCHAR` | No | No | No | No |
| `payload_hash` | `VARCHAR` | No | No | No | No |
| `processed_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### normalized_webhook_events

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `provider_code` | `VARCHAR` | No | No | No | No |
| `gateway_event_id` | `VARCHAR` | No | No | No | No |
| `event_type` | `VARCHAR` | No | No | No | No |
| `status` | `VARCHAR` | No | No | No | No |
| `environment` | `VARCHAR` | Yes | No | No | No |
| `processed_at` | `DATETIME` | Yes | No | No | No |
| `zozi_order_id` | `INTEGER` | Yes | No | No | No |
| `gateway_transaction_id` | `VARCHAR` | Yes | No | No | No |
| `gateway_customer_id` | `VARCHAR` | Yes | No | No | No |
| `gross_amount` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `currency` | `VARCHAR(3)` | Yes | No | No | No |
| `gateway_fee` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `net_settlement` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `fraud_score` | `NUMERIC(5, 2)` | Yes | No | No | No |
| `three_ds_status` | `VARCHAR` | Yes | No | No | No |
| `avs_result` | `VARCHAR` | Yes | No | No | No |
| `raw_payload` | `TEXT` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### executive_news

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `title` | `VARCHAR(200)` | No | No | No | No |
| `summary` | `TEXT` | Yes | No | No | No |
| `content` | `TEXT` | Yes | No | No | No |
| `url` | `VARCHAR(500)` | Yes | No | No | No |
| `category` | `VARCHAR(50)` | Yes | No | No | No |
| `priority` | `VARCHAR(20)` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `is_published` | `BOOLEAN` | Yes | No | No | No |
| `ai_sentiment` | `VARCHAR(20)` | Yes | No | No | No |
| `published_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### outbox_events

**Primary Key:** id

**Foreign Keys:**
- `created_by_id` → `core.users.id`
- `updated_by_id` → `core.users.id`
- `deleted_by_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `uuid` | `VARCHAR(36)` | No | No | No | No |
| `event_type` | `VARCHAR(100)` | No | No | No | No |
| `aggregate_type` | `VARCHAR(50)` | No | No | No | No |
| `aggregate_id` | `INTEGER` | No | No | No | No |
| `payload_json` | `TEXT` | No | No | No | No |
| `status` | `VARCHAR(20)` | No | No | No | No |
| `country_code` | `VARCHAR(3)` | Yes | No | No | No |
| `published_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | No | No | No | No |
| `updated_at` | `DATETIME` | No | No | No | No |
| `is_deleted` | `BOOLEAN` | No | No | No | No |
| `deleted_at` | `DATETIME` | Yes | No | No | No |
| `deleted_by_id` | `INTEGER` | Yes | No | Yes | No |
| `created_by_id` | `INTEGER` | Yes | No | Yes | No |
| `updated_by_id` | `INTEGER` | Yes | No | Yes | No |

### inbox_events

**Primary Key:** id

**Foreign Keys:**
- `created_by_id` → `core.users.id`
- `updated_by_id` → `core.users.id`
- `deleted_by_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `idempotency_key` | `VARCHAR(64)` | No | No | No | Yes |
| `event_type` | `VARCHAR(100)` | No | No | No | No |
| `status` | `VARCHAR(20)` | No | No | No | No |
| `processed_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(3)` | Yes | No | No | No |
| `created_at` | `DATETIME` | No | No | No | No |
| `updated_at` | `DATETIME` | No | No | No | No |
| `is_deleted` | `BOOLEAN` | No | No | No | No |
| `deleted_at` | `DATETIME` | Yes | No | No | No |
| `deleted_by_id` | `INTEGER` | Yes | No | Yes | No |
| `created_by_id` | `INTEGER` | Yes | No | Yes | No |
| `updated_by_id` | `INTEGER` | Yes | No | Yes | No |

### event_retry_queue

**Primary Key:** id

**Foreign Keys:**
- `updated_by_id` → `core.users.id`
- `deleted_by_id` → `core.users.id`
- `event_id` → `analytics.outbox_events.id`
- `created_by_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `event_id` | `INTEGER` | No | No | Yes | No |
| `attempt` | `INTEGER` | No | No | No | No |
| `next_attempt_at` | `DATETIME` | No | No | No | No |
| `last_error` | `TEXT` | Yes | No | No | No |
| `country_code` | `VARCHAR(3)` | Yes | No | No | No |
| `created_at` | `DATETIME` | No | No | No | No |
| `updated_at` | `DATETIME` | No | No | No | No |
| `is_deleted` | `BOOLEAN` | No | No | No | No |
| `deleted_at` | `DATETIME` | Yes | No | No | No |
| `deleted_by_id` | `INTEGER` | Yes | No | Yes | No |
| `created_by_id` | `INTEGER` | Yes | No | Yes | No |
| `updated_by_id` | `INTEGER` | Yes | No | Yes | No |

### event_dead_letter

**Primary Key:** id

**Foreign Keys:**
- `event_id` → `analytics.outbox_events.id`
- `updated_by_id` → `core.users.id`
- `deleted_by_id` → `core.users.id`
- `resolved_by` → `core.users.id`
- `created_by_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `event_id` | `INTEGER` | No | No | Yes | No |
| `payload_json` | `TEXT` | No | No | No | No |
| `failed_at` | `DATETIME` | No | No | No | No |
| `reason` | `VARCHAR(255)` | Yes | No | No | No |
| `resolved_by` | `INTEGER` | Yes | No | Yes | No |
| `country_code` | `VARCHAR(3)` | Yes | No | No | No |
| `created_at` | `DATETIME` | No | No | No | No |
| `updated_at` | `DATETIME` | No | No | No | No |
| `is_deleted` | `BOOLEAN` | No | No | No | No |
| `deleted_at` | `DATETIME` | Yes | No | No | No |
| `deleted_by_id` | `INTEGER` | Yes | No | Yes | No |
| `created_by_id` | `INTEGER` | Yes | No | Yes | No |
| `updated_by_id` | `INTEGER` | Yes | No | Yes | No |

### mv_daily_sales

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(3)` | No | No | No | No |
| `snapshot_date` | `DATE` | No | No | No | No |
| `currency` | `VARCHAR(3)` | No | No | No | No |
| `total_orders` | `INTEGER` | No | No | No | No |
| `total_revenue` | `NUMERIC(14, 2)` | No | No | No | No |
| `total_gross_sales` | `NUMERIC(14, 2)` | No | No | No | No |
| `total_net_sales` | `NUMERIC(14, 2)` | No | No | No | No |
| `total_refunds` | `NUMERIC(14, 2)` | No | No | No | No |
| `created_at` | `DATETIME` | No | No | No | No |
| `updated_at` | `DATETIME` | No | No | No | No |

### mv_monthly_sales

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(3)` | No | No | No | No |
| `period_year` | `INTEGER` | No | No | No | No |
| `period_month` | `INTEGER` | No | No | No | No |
| `currency` | `VARCHAR(3)` | No | No | No | No |
| `total_orders` | `INTEGER` | No | No | No | No |
| `total_revenue` | `NUMERIC(14, 2)` | No | No | No | No |
| `total_gross_sales` | `NUMERIC(14, 2)` | No | No | No | No |
| `total_net_sales` | `NUMERIC(14, 2)` | No | No | No | No |
| `total_refunds` | `NUMERIC(14, 2)` | No | No | No | No |
| `created_at` | `DATETIME` | No | No | No | No |
| `updated_at` | `DATETIME` | No | No | No | No |

### kpi_customer

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(3)` | No | No | No | No |
| `kpi_date` | `DATE` | No | No | No | No |
| `new_customers` | `INTEGER` | No | No | No | No |
| `active_customers` | `INTEGER` | No | No | No | No |
| `total_customers` | `INTEGER` | No | No | No | No |
| `repeat_customers` | `INTEGER` | No | No | No | No |
| `churned_customers` | `INTEGER` | No | No | No | No |
| `customer_lifetime_value` | `NUMERIC(14, 2)` | No | No | No | No |
| `created_at` | `DATETIME` | No | No | No | No |
| `updated_at` | `DATETIME` | No | No | No | No |

### kpi_supplier

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(3)` | No | No | No | No |
| `kpi_date` | `DATE` | No | No | No | No |
| `new_suppliers` | `INTEGER` | No | No | No | No |
| `active_suppliers` | `INTEGER` | No | No | No | No |
| `total_suppliers` | `INTEGER` | No | No | No | No |
| `avg_products_per_supplier` | `NUMERIC(10, 2)` | No | No | No | No |
| `fulfillment_rate` | `NUMERIC(5, 4)` | No | No | No | No |
| `created_at` | `DATETIME` | No | No | No | No |
| `updated_at` | `DATETIME` | No | No | No | No |

### kpi_country

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(3)` | No | No | No | No |
| `kpi_date` | `DATE` | No | No | No | No |
| `gmv` | `NUMERIC(14, 2)` | No | No | No | No |
| `revenue` | `NUMERIC(14, 2)` | No | No | No | No |
| `orders_count` | `INTEGER` | No | No | No | No |
| `active_users` | `INTEGER` | No | No | No | No |
| `conversion_rate` | `NUMERIC(5, 4)` | No | No | No | No |
| `avg_order_value` | `NUMERIC(14, 2)` | No | No | No | No |
| `created_at` | `DATETIME` | No | No | No | No |
| `updated_at` | `DATETIME` | No | No | No | No |

### kpi_revenue

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(3)` | No | No | No | No |
| `kpi_date` | `DATE` | No | No | No | No |
| `gross_revenue` | `NUMERIC(14, 2)` | No | No | No | No |
| `net_revenue` | `NUMERIC(14, 2)` | No | No | No | No |
| `refunds` | `NUMERIC(14, 2)` | No | No | No | No |
| `chargebacks` | `NUMERIC(14, 2)` | No | No | No | No |
| `platform_commission` | `NUMERIC(14, 2)` | No | No | No | No |
| `logistics_revenue` | `NUMERIC(14, 2)` | No | No | No | No |
| `created_at` | `DATETIME` | No | No | No | No |
| `updated_at` | `DATETIME` | No | No | No | No |

### kpi_orders

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(3)` | No | No | No | No |
| `kpi_date` | `DATE` | No | No | No | No |
| `total_orders` | `INTEGER` | No | No | No | No |
| `completed_orders` | `INTEGER` | No | No | No | No |
| `cancelled_orders` | `INTEGER` | No | No | No | No |
| `returned_orders` | `INTEGER` | No | No | No | No |
| `avg_order_value` | `NUMERIC(14, 2)` | No | No | No | No |
| `on_time_delivery_rate` | `NUMERIC(5, 4)` | No | No | No | No |
| `created_at` | `DATETIME` | No | No | No | No |
| `updated_at` | `DATETIME` | No | No | No | No |

### kpi_retention

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(3)` | No | No | No | No |
| `cohort_month` | `VARCHAR(7)` | No | No | No | No |
| `retained_customers` | `INTEGER` | No | No | No | No |
| `retention_rate_1m` | `NUMERIC(5, 4)` | No | No | No | No |
| `retention_rate_3m` | `NUMERIC(5, 4)` | No | No | No | No |
| `retention_rate_6m` | `NUMERIC(5, 4)` | No | No | No | No |
| `created_at` | `DATETIME` | No | No | No | No |
| `updated_at` | `DATETIME` | No | No | No | No |

### kpi_conversion

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(3)` | No | No | No | No |
| `kpi_date` | `DATE` | No | No | No | No |
| `sessions` | `INTEGER` | No | No | No | No |
| `unique_visitors` | `INTEGER` | No | No | No | No |
| `add_to_cart_rate` | `NUMERIC(5, 4)` | No | No | No | No |
| `checkout_conversion_rate` | `NUMERIC(5, 4)` | No | No | No | No |
| `cart_abandonment_rate` | `NUMERIC(5, 4)` | No | No | No | No |
| `created_at` | `DATETIME` | No | No | No | No |
| `updated_at` | `DATETIME` | No | No | No | No |

### mv_cash_position

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(3)` | No | No | No | No |
| `snapshot_date` | `DATE` | No | No | No | No |
| `currency` | `VARCHAR(3)` | No | No | No | No |
| `total_cash` | `NUMERIC(14, 2)` | No | No | No | No |
| `cash_in_banks` | `NUMERIC(14, 2)` | No | No | No | No |
| `cash_in_transit` | `NUMERIC(14, 2)` | No | No | No | No |
| `pending_payouts` | `NUMERIC(14, 2)` | No | No | No | No |
| `pending_settlements` | `NUMERIC(14, 2)` | No | No | No | No |
| `net_cash_position` | `NUMERIC(14, 2)` | No | No | No | No |
| `created_at` | `DATETIME` | No | No | No | No |
| `updated_at` | `DATETIME` | No | No | No | No |

### mv_facet_counts

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(3)` | No | No | No | No |
| `snapshot_date` | `DATE` | No | No | No | No |
| `facet_type` | `VARCHAR(50)` | No | No | No | No |
| `facet_value` | `VARCHAR(200)` | No | No | No | No |
| `item_count` | `INTEGER` | No | No | No | No |
| `created_at` | `DATETIME` | No | No | No | No |
| `updated_at` | `DATETIME` | No | No | No | No |

## Schema: audit

Tables: 8

### admin_analytics_snapshots

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `snapshot_key` | `VARCHAR(120)` | No | No | No | No |
| `snapshot_group` | `VARCHAR(80)` | No | No | No | No |
| `period` | `VARCHAR(40)` | Yes | No | No | No |
| `payload_json` | `TEXT` | No | No | No | No |
| `computed_at` | `DATETIME` | No | No | No | No |
| `expires_at` | `DATETIME` | No | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### admin_change_audit_logs

**Primary Key:** id

**Foreign Keys:**
- `admin_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `admin_id` | `INTEGER` | No | No | Yes | No |
| `action` | `VARCHAR` | No | No | No | No |
| `entity` | `VARCHAR` | No | No | No | No |
| `entity_key` | `VARCHAR` | Yes | No | No | No |
| `before_json` | `TEXT` | Yes | No | No | No |
| `after_json` | `TEXT` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### admin_activity_logs

**Primary Key:** id

**Foreign Keys:**
- `admin_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `admin_id` | `INTEGER` | No | No | Yes | No |
| `action` | `VARCHAR` | No | No | No | No |
| `details` | `JSON` | Yes | No | No | No |
| `ip_address` | `VARCHAR` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### chatbot_query_events

**Primary Key:** id

**Foreign Keys:**
- `clicked_product_id` → `commerce.products.id`
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | Yes | No | Yes | No |
| `session_id` | `VARCHAR(64)` | No | No | No | No |
| `event_type` | `VARCHAR(30)` | No | No | No | No |
| `message` | `TEXT` | Yes | No | No | No |
| `normalized_query` | `VARCHAR(500)` | Yes | No | No | No |
| `intent` | `VARCHAR(100)` | Yes | No | No | No |
| `filters_json` | `TEXT` | Yes | No | No | No |
| `result_count` | `INTEGER` | No | No | No | No |
| `product_ids_json` | `TEXT` | Yes | No | No | No |
| `clicked_product_id` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | No | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### retention_job_runs

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `job_type` | `VARCHAR(50)` | Yes | No | No | No |
| `target_table` | `VARCHAR(100)` | Yes | No | No | No |
| `target_name` | `VARCHAR(100)` | Yes | No | No | No |
| `cutoff_days` | `INTEGER` | Yes | No | No | No |
| `records_deleted` | `INTEGER` | Yes | No | No | No |
| `archived_count` | `INTEGER` | Yes | No | No | No |
| `deleted_count` | `INTEGER` | Yes | No | No | No |
| `artifact_path` | `VARCHAR` | Yes | No | No | No |
| `result_json` | `TEXT` | Yes | No | No | No |
| `started_at` | `DATETIME` | Yes | No | No | No |
| `completed_at` | `DATETIME` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `error_message` | `TEXT` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### audit_logs

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `action` | `VARCHAR` | No | No | No | No |
| `entity_type` | `VARCHAR` | No | No | No | No |
| `entity_id` | `INTEGER` | Yes | No | No | No |
| `user_id` | `INTEGER` | Yes | No | Yes | No |
| `username` | `VARCHAR` | Yes | No | No | No |
| `user_role` | `VARCHAR` | Yes | No | No | No |
| `details` | `JSON` | Yes | No | No | No |
| `ip_address` | `VARCHAR` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### command_center_views

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `view_name` | `VARCHAR(100)` | No | No | No | No |
| `config` | `JSON` | Yes | No | No | No |
| `is_default` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### worm_audit

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `entity_type` | `VARCHAR(100)` | No | No | No | No |
| `entity_id` | `VARCHAR(100)` | No | No | No | No |
| `action` | `VARCHAR(50)` | No | No | No | No |
| `actor_id` | `INTEGER` | Yes | No | No | No |
| `actor_type` | `VARCHAR(50)` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `timestamp` | `DATETIME` | No | No | No | No |
| `payload_json` | `JSON` | Yes | No | No | No |
| `signature` | `VARCHAR(255)` | Yes | No | No | No |
| `is_valid` | `BOOLEAN` | Yes | No | No | No |
| `previous_state_hash` | `VARCHAR(255)` | Yes | No | No | No |
| `new_state_hash` | `VARCHAR(255)` | Yes | No | No | No |

## Schema: hr

Tables: 30

### employee_expenses

**Primary Key:** id

**Foreign Keys:**
- `approved_by` → `core.users.id`
- `employee_id` → `logistics.employees.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `employee_id` | `INTEGER` | No | No | Yes | No |
| `expense_type` | `VARCHAR(50)` | No | No | No | No |
| `amount` | `NUMERIC(12, 2)` | No | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `approved_by` | `INTEGER` | Yes | No | Yes | No |
| `approved_at` | `DATETIME` | Yes | No | No | No |
| `receipt_url` | `VARCHAR(500)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### shift_handover_tasks

**Primary Key:** id

**Foreign Keys:**
- `assigned_to` → `core.users.id`
- `session_id` → `customer.shift_handover_sessions.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `session_id` | `INTEGER` | No | No | Yes | No |
| `description` | `TEXT` | No | No | No | No |
| `priority` | `VARCHAR(20)` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `assigned_to` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### shift_handover_logs

**Primary Key:** id

**Foreign Keys:**
- `handover_to_user_id` → `core.users.id`
- `country_code` → `country.country_configs.code`
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `shift_start` | `DATETIME` | No | No | No | No |
| `shift_end` | `DATETIME` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `handover_to_user_id` | `INTEGER` | Yes | No | Yes | No |
| `handover_notes` | `TEXT` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### payment_orchestrator_sync

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `gateway_id` | `VARCHAR(60)` | No | No | No | No |
| `gateway_name` | `VARCHAR(100)` | Yes | No | No | No |
| `environment` | `VARCHAR(20)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `fee_percent` | `NUMERIC(8, 4)` | Yes | No | No | No |
| `fee_fixed` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `supported_payment_methods` | `TEXT` | Yes | No | No | No |
| `last_sync_at` | `DATETIME` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### supplier_onboarding_sync

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`
- `supplier_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `supplier_id` | `INTEGER` | No | No | Yes | No |
| `kyc_status` | `VARCHAR(30)` | Yes | No | No | No |
| `kyc_documents` | `TEXT` | Yes | No | No | No |
| `onboarding_fee_paid` | `BOOLEAN` | Yes | No | No | No |
| `monthly_fee_status` | `VARCHAR(20)` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### legal_contract_templates

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `template_type` | `VARCHAR(50)` | No | No | No | No |
| `version` | `VARCHAR(20)` | Yes | No | No | No |
| `content` | `TEXT` | No | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### data_residency_records

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `data_type` | `VARCHAR(50)` | No | No | No | No |
| `storage_location` | `VARCHAR(100)` | Yes | No | No | No |
| `cross_border_allowed` | `BOOLEAN` | Yes | No | No | No |
| `compliance_status` | `VARCHAR(30)` | Yes | No | No | No |
| `last_audit_at` | `DATETIME` | Yes | No | No | No |
| `next_audit_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### country_map_configs

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | Yes |
| `map_provider` | `VARCHAR(30)` | Yes | No | No | No |
| `api_key_ref` | `VARCHAR(100)` | Yes | No | No | No |
| `default_zoom` | `INTEGER` | Yes | No | No | No |
| `show_regions` | `BOOLEAN` | Yes | No | No | No |
| `show_cities` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### shop_warehouse_locations

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `name` | `VARCHAR(100)` | No | No | No | No |
| `warehouse_code` | `VARCHAR(30)` | No | No | No | No |
| `latitude` | `FLOAT` | Yes | No | No | No |
| `longitude` | `FLOAT` | Yes | No | No | No |
| `address` | `TEXT` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### logistics_partner_locations

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`
- `partner_id` → `logistics.logistics_partners.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `partner_id` | `INTEGER` | No | No | Yes | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `location_type` | `VARCHAR(30)` | Yes | No | No | No |
| `latitude` | `FLOAT` | Yes | No | No | No |
| `longitude` | `FLOAT` | Yes | No | No | No |
| `address` | `TEXT` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### parcel_location_trackers

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`
- `parcel_id` → `logistics.shipments.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `parcel_id` | `INTEGER` | No | No | Yes | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `latitude` | `FLOAT` | Yes | No | No | No |
| `longitude` | `FLOAT` | Yes | No | No | No |
| `location_name` | `VARCHAR(200)` | Yes | No | No | No |
| `timestamp` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### physical_id_cards

**Primary Key:** id

**Foreign Keys:**
- `employee_id` → `logistics.employees.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `employee_id` | `INTEGER` | No | No | Yes | Yes |
| `card_number` | `VARCHAR(50)` | No | No | No | Yes |
| `issued_at` | `DATETIME` | Yes | No | No | No |
| `expires_at` | `DATETIME` | Yes | No | No | No |
| `is_revoked` | `BOOLEAN` | Yes | No | No | No |
| `revoked_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### employee_biometrics

**Primary Key:** id

**Foreign Keys:**
- `employee_id` → `logistics.employees.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `employee_id` | `INTEGER` | No | No | Yes | Yes |
| `fingerprint_hash` | `VARCHAR(255)` | Yes | No | No | No |
| `face_encoding` | `TEXT` | Yes | No | No | No |
| `biometric_type` | `VARCHAR(20)` | Yes | No | No | No |
| `enrolled_at` | `DATETIME` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### employee_roles

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `role_name` | `VARCHAR(100)` | Yes | No | No | Yes |
| `permissions` | `JSON` | Yes | No | No | No |
| `authority_level` | `INTEGER` | Yes | No | No | No |
| `can_approve_leave` | `BOOLEAN` | Yes | No | No | No |
| `can_approve_expense` | `BOOLEAN` | Yes | No | No | No |
| `can_manage_users` | `BOOLEAN` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### org_units

**Primary Key:** id

**Foreign Keys:**
- `parent_id` → `hr.org_units.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `name` | `VARCHAR(200)` | No | No | No | No |
| `parent_id` | `INTEGER` | Yes | No | Yes | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `level` | `INTEGER` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### employee_work_logs

**Primary Key:** id

**Foreign Keys:**
- `employee_id` → `logistics.employees.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `employee_id` | `INTEGER` | No | No | Yes | No |
| `date` | `DATE` | No | No | No | No |
| `hours_worked` | `NUMERIC(5, 2)` | Yes | No | No | No |
| `task_description` | `TEXT` | Yes | No | No | No |
| `location_lat` | `FLOAT` | Yes | No | No | No |
| `location_long` | `FLOAT` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### employee_leave_requests

**Primary Key:** id

**Foreign Keys:**
- `approved_by` → `core.users.id`
- `employee_id` → `logistics.employees.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `employee_id` | `INTEGER` | No | No | Yes | No |
| `leave_type` | `VARCHAR(50)` | No | No | No | No |
| `start_date` | `DATE` | No | No | No | No |
| `end_date` | `DATE` | No | No | No | No |
| `days_requested` | `INTEGER` | No | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `approved_by` | `INTEGER` | Yes | No | Yes | No |
| `approved_at` | `DATETIME` | Yes | No | No | No |
| `rejection_reason` | `TEXT` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### employee_assets

**Primary Key:** id

**Foreign Keys:**
- `employee_id` → `logistics.employees.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `employee_id` | `INTEGER` | No | No | Yes | No |
| `asset_type` | `VARCHAR(50)` | No | No | No | No |
| `asset_id` | `VARCHAR(100)` | No | No | No | No |
| `serial_no` | `VARCHAR(100)` | Yes | No | No | No |
| `assigned_at` | `DATETIME` | Yes | No | No | No |
| `returned_at` | `DATETIME` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### employee_certifications

**Primary Key:** id

**Foreign Keys:**
- `employee_id` → `logistics.employees.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `employee_id` | `INTEGER` | No | No | Yes | No |
| `cert_type` | `VARCHAR(100)` | No | No | No | No |
| `cert_name` | `VARCHAR(200)` | No | No | No | No |
| `issued_date` | `DATE` | Yes | No | No | No |
| `expiry_date` | `DATE` | Yes | No | No | No |
| `is_valid` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### employee_documents

**Primary Key:** id

**Foreign Keys:**
- `employee_id` → `logistics.employees.id`
- `verified_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `employee_id` | `INTEGER` | No | No | Yes | No |
| `doc_type` | `VARCHAR(50)` | No | No | No | No |
| `file_url` | `VARCHAR(500)` | No | No | No | No |
| `expiry_date` | `DATE` | Yes | No | No | No |
| `verified_by` | `INTEGER` | Yes | No | Yes | No |
| `verified_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### employee_dependents

**Primary Key:** id

**Foreign Keys:**
- `employee_id` → `logistics.employees.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `employee_id` | `INTEGER` | No | No | Yes | No |
| `name` | `VARCHAR(160)` | No | No | No | No |
| `relation` | `VARCHAR(50)` | No | No | No | No |
| `dob` | `DATE` | Yes | No | No | No |
| `is_insured` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### employee_relations

**Primary Key:** id

**Foreign Keys:**
- `internal_employee_id` → `logistics.employees.id`
- `employee_id` → `logistics.employees.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `employee_id` | `INTEGER` | No | No | Yes | No |
| `related_person_name` | `VARCHAR(160)` | No | No | No | No |
| `relation_type` | `VARCHAR(30)` | No | No | No | No |
| `is_internal_employee` | `BOOLEAN` | Yes | No | No | No |
| `internal_employee_id` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### employee_addresses

**Primary Key:** id

**Foreign Keys:**
- `country_code` → `country.country_configs.code`
- `employee_id` → `logistics.employees.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `employee_id` | `INTEGER` | No | No | Yes | No |
| `address_type` | `VARCHAR(30)` | No | No | No | No |
| `street` | `VARCHAR(200)` | No | No | No | No |
| `city` | `VARCHAR(100)` | No | No | No | No |
| `state` | `VARCHAR(100)` | Yes | No | No | No |
| `postal_code` | `VARCHAR(20)` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | No | No | Yes | No |
| `is_primary` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### coi_reports

**Primary Key:** id

**Foreign Keys:**
- `approved_by` → `core.users.id`
- `employee_id` → `logistics.employees.id`
- `internal_employee_id` → `logistics.employees.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `employee_id` | `INTEGER` | No | No | Yes | No |
| `related_person_name` | `VARCHAR(160)` | No | No | No | No |
| `relation_type` | `VARCHAR(30)` | No | No | No | No |
| `is_internal` | `BOOLEAN` | Yes | No | No | No |
| `internal_employee_id` | `INTEGER` | Yes | No | Yes | No |
| `risk_level` | `VARCHAR(20)` | Yes | No | No | No |
| `is_approved` | `BOOLEAN` | Yes | No | No | No |
| `approved_by` | `INTEGER` | Yes | No | Yes | No |
| `approved_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### employee_travel_requests

**Primary Key:** id

**Foreign Keys:**
- `approved_by` → `core.users.id`
- `employee_id` → `logistics.employees.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `employee_id` | `INTEGER` | No | No | Yes | No |
| `destination_country` | `VARCHAR(10)` | No | No | No | No |
| `start_date` | `DATE` | No | No | No | No |
| `end_date` | `DATE` | No | No | No | No |
| `purpose` | `VARCHAR(200)` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `approved_by` | `INTEGER` | Yes | No | Yes | No |
| `approved_at` | `DATETIME` | Yes | No | No | No |
| `per_diem_json` | `JSON` | Yes | No | No | No |
| `total_cost` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### alumni_network

**Primary Key:** id

**Foreign Keys:**
- `employee_id` → `logistics.employees.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `employee_id` | `INTEGER` | No | No | Yes | Yes |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `granted_at` | `DATETIME` | Yes | No | No | No |
| `eligibility_expires_at` | `DATETIME` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### disciplinary_cases

**Primary Key:** id

**Foreign Keys:**
- `employee_id` → `logistics.employees.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `employee_id` | `INTEGER` | No | No | Yes | No |
| `employee_name` | `VARCHAR(200)` | Yes | No | No | No |
| `stage` | `VARCHAR(30)` | No | No | No | No |
| `description` | `TEXT` | No | No | No | No |
| `issued_at` | `DATETIME` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### offboarding_cases

**Primary Key:** id

**Foreign Keys:**
- `employee_id` → `logistics.employees.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `employee_id` | `INTEGER` | No | No | Yes | No |
| `employee_name` | `VARCHAR(200)` | Yes | No | No | No |
| `reason` | `VARCHAR(50)` | No | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `initiated_at` | `DATETIME` | Yes | No | No | No |
| `completed_at` | `DATETIME` | Yes | No | No | No |
| `notes` | `TEXT` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### onboarding_pipelines

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `pipeline_type` | `VARCHAR` | No | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `current_step` | `INTEGER` | Yes | No | No | No |
| `steps_data` | `JSON` | Yes | No | No | No |
| `started_at` | `DATETIME` | Yes | No | No | No |
| `completed_at` | `DATETIME` | Yes | No | No | No |

### onboarding_steps

**Primary Key:** id

**Foreign Keys:**
- `pipeline_id` → `hr.onboarding_pipelines.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `pipeline_id` | `INTEGER` | No | No | Yes | No |
| `step_name` | `VARCHAR` | No | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `data` | `JSON` | Yes | No | No | No |
| `started_at` | `DATETIME` | Yes | No | No | No |
| `completed_at` | `DATETIME` | Yes | No | No | No |

## Schema: security

Tables: 19

### fraud_events

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`
- `reviewed_by` → `core.users.id`
- `order_id` → `commerce.orders.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | Yes | No | Yes | No |
| `order_id` | `INTEGER` | Yes | No | Yes | No |
| `event_type` | `VARCHAR(50)` | No | No | No | No |
| `ip_address` | `VARCHAR(45)` | Yes | No | No | No |
| `device_hash` | `VARCHAR(64)` | Yes | No | No | No |
| `session_id` | `VARCHAR(128)` | Yes | No | No | No |
| `fraud_score` | `NUMERIC(5, 2)` | No | No | No | No |
| `triggered_rules` | `TEXT` | Yes | No | No | No |
| `details` | `JSON` | Yes | No | No | No |
| `is_flagged` | `BOOLEAN` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `reviewed_by` | `INTEGER` | Yes | No | Yes | No |
| `reviewed_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### fraud_blacklist

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `identifier_type` | `VARCHAR` | No | No | No | No |
| `identifier_value` | `VARCHAR` | No | No | No | No |
| `identifier_value_hash` | `VARCHAR` | Yes | No | No | No |
| `reason` | `VARCHAR` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `expires_at` | `DATETIME` | Yes | No | No | No |

### fraud_rules

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `rule_key` | `VARCHAR(100)` | No | No | No | Yes |
| `name` | `VARCHAR(200)` | No | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `weight` | `INTEGER` | Yes | No | No | No |
| `condition_json` | `TEXT` | Yes | No | No | No |
| `action` | `VARCHAR(50)` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `is_global` | `BOOLEAN` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### manual_review_queue

**Primary Key:** id

**Foreign Keys:**
- `assigned_to` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `entity_type` | `VARCHAR(50)` | No | No | No | No |
| `entity_id` | `INTEGER` | No | No | No | No |
| `fraud_score` | `INTEGER` | No | No | No | No |
| `triggered_rules` | `TEXT` | Yes | No | No | No |
| `reason` | `VARCHAR` | No | No | No | No |
| `priority` | `VARCHAR` | Yes | No | No | No |
| `assigned_to` | `INTEGER` | Yes | No | Yes | No |
| `admin_notes` | `TEXT` | Yes | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### ip_reputations

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `ip_address` | `VARCHAR` | No | No | No | No |
| `reputation_score` | `NUMERIC(5, 2)` | Yes | No | No | No |
| `is_blocked` | `BOOLEAN` | Yes | No | No | No |
| `is_proxy` | `BOOLEAN` | Yes | No | No | No |
| `is_tor` | `BOOLEAN` | Yes | No | No | No |
| `is_vpn` | `BOOLEAN` | Yes | No | No | No |
| `is_hosting` | `BOOLEAN` | Yes | No | No | No |
| `asn` | `VARCHAR` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `last_seen_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### device_fingerprints

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | Yes | No | Yes | No |
| `fingerprint_hash` | `VARCHAR` | No | No | No | No |
| `user_agent` | `VARCHAR` | Yes | No | No | No |
| `ip_addresses` | `TEXT` | Yes | No | No | No |
| `is_trusted` | `BOOLEAN` | Yes | No | No | No |
| `is_blocked` | `BOOLEAN` | Yes | No | No | No |
| `risk_score` | `INTEGER` | Yes | No | No | No |
| `headless_attempts` | `INTEGER` | Yes | No | No | No |
| `account_count` | `INTEGER` | Yes | No | No | No |
| `first_seen_at` | `DATETIME` | Yes | No | No | No |
| `last_seen_at` | `DATETIME` | Yes | No | No | No |

### credit_card_bins

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `bin` | `VARCHAR(10)` | No | No | No | Yes |
| `brand` | `VARCHAR(50)` | Yes | No | No | No |
| `bank` | `VARCHAR(100)` | Yes | No | No | No |
| `country` | `VARCHAR(10)` | Yes | No | No | No |
| `is_blacklisted` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### fraud_alerts

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `alert_type` | `VARCHAR(50)` | No | No | No | No |
| `entity_type` | `VARCHAR(50)` | No | No | No | No |
| `entity_id` | `INTEGER` | No | No | No | No |
| `fraud_score` | `NUMERIC(5, 2)` | No | No | No | No |
| `triggered_rules` | `TEXT` | Yes | No | No | No |
| `priority` | `VARCHAR(20)` | Yes | No | No | No |
| `details` | `TEXT` | Yes | No | No | No |
| `is_resolved` | `BOOLEAN` | Yes | No | No | No |
| `resolved_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### ip_account_linkages

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `ip_address` | `VARCHAR` | No | No | No | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `device_fingerprint` | `VARCHAR` | Yes | No | No | No |
| `session_id` | `VARCHAR` | Yes | No | No | No |
| `interaction_count` | `INTEGER` | Yes | No | No | No |
| `is_suspicious` | `BOOLEAN` | Yes | No | No | No |
| `last_seen` | `DATETIME` | Yes | No | No | No |

### fraud_velocity_counters

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `key` | `VARCHAR(255)` | No | No | No | No |
| `count` | `INTEGER` | Yes | No | No | No |
| `window_start` | `DATETIME` | Yes | No | No | No |
| `window_end` | `DATETIME` | No | No | No | No |
| `entity_type` | `VARCHAR(50)` | Yes | No | No | No |
| `entity_id` | `INTEGER` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### fraud_scoring_logs

**Primary Key:** id

**Foreign Keys:**
- `user_id` → `core.users.id`
- `order_id` → `commerce.orders.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `event_type` | `VARCHAR(50)` | No | No | No | No |
| `user_id` | `INTEGER` | Yes | No | Yes | No |
| `order_id` | `INTEGER` | Yes | No | Yes | No |
| `ip_address` | `VARCHAR(45)` | Yes | No | No | No |
| `device_hash` | `VARCHAR(64)` | Yes | No | No | No |
| `session_id` | `VARCHAR(128)` | Yes | No | No | No |
| `raw_score` | `INTEGER` | No | No | No | No |
| `triggered_rules` | `JSON` | Yes | No | No | No |
| `metadata_json` | `JSON` | Yes | No | No | No |
| `action_taken` | `VARCHAR(50)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### fraud_cases

**Primary Key:** id

**Foreign Keys:**
- `assigned_to` → `core.users.id`
- `created_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `case_number` | `VARCHAR(50)` | No | No | No | Yes |
| `title` | `VARCHAR(200)` | No | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `fraud_score` | `INTEGER` | No | No | No | No |
| `priority` | `VARCHAR(20)` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `entity_type` | `VARCHAR(50)` | Yes | No | No | No |
| `entity_id` | `INTEGER` | Yes | No | No | No |
| `assigned_to` | `INTEGER` | Yes | No | Yes | No |
| `created_by` | `INTEGER` | Yes | No | Yes | No |
| `resolved_at` | `DATETIME` | Yes | No | No | No |
| `resolution_notes` | `TEXT` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### fraud_case_assignments

**Primary Key:** id

**Foreign Keys:**
- `assigned_to` → `core.users.id`
- `case_id` → `security.fraud_cases.id`
- `assigned_by` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `case_id` | `INTEGER` | No | No | Yes | No |
| `assigned_to` | `INTEGER` | No | No | Yes | No |
| `assigned_by` | `INTEGER` | Yes | No | Yes | No |
| `role_at_assignment` | `VARCHAR(50)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### dlp_violations

**Primary Key:** id

**Foreign Keys:**
- `reviewed_by` → `core.users.id`
- `sender_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `violation_type` | `VARCHAR(50)` | No | No | No | No |
| `severity` | `VARCHAR(20)` | Yes | No | No | No |
| `sender_id` | `INTEGER` | Yes | No | Yes | No |
| `recipient_email` | `VARCHAR(255)` | Yes | No | No | No |
| `detected_content` | `TEXT` | Yes | No | No | No |
| `action_taken` | `VARCHAR(50)` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `reviewed_by` | `INTEGER` | Yes | No | Yes | No |
| `reviewed_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### meeting_transcripts

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `room_id` | `VARCHAR(64)` | No | No | No | No |
| `language` | `VARCHAR(10)` | Yes | No | No | No |
| `segments` | `JSON` | Yes | No | No | No |
| `action_items` | `JSON` | Yes | No | No | No |
| `summary` | `TEXT` | Yes | No | No | No |
| `word_count` | `INTEGER` | Yes | No | No | No |
| `duration_seconds` | `INTEGER` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### meeting_action_items

**Primary Key:** id

**Foreign Keys:**
- `meeting_id` → `security.meeting_transcripts.id`
- `assigned_to` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `meeting_id` | `INTEGER` | No | No | Yes | No |
| `entity_type` | `VARCHAR(50)` | Yes | No | No | No |
| `entity_id` | `INTEGER` | Yes | No | No | No |
| `action` | `VARCHAR` | No | No | No | No |
| `metadata_json` | `JSON` | Yes | No | No | No |
| `status` | `VARCHAR(20)` | Yes | No | No | No |
| `assigned_to` | `INTEGER` | Yes | No | Yes | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `due_date` | `DATETIME` | Yes | No | No | No |

### alert_escalation_rules

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `alert_type` | `VARCHAR(50)` | No | No | No | No |
| `severity` | `VARCHAR(20)` | Yes | No | No | No |
| `threshold_value` | `NUMERIC(15, 2)` | Yes | No | No | No |
| `current_tier` | `INTEGER` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### document_verifications

**Primary Key:** id

**Foreign Keys:**
- `verifier_id` → `core.users.id`
- `pipeline_id` → `hr.onboarding_pipelines.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `pipeline_id` | `INTEGER` | No | No | Yes | No |
| `document_type` | `VARCHAR` | No | No | No | No |
| `document_data` | `JSON` | Yes | No | No | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `verified_at` | `DATETIME` | Yes | No | No | No |
| `verifier_id` | `INTEGER` | Yes | No | Yes | No |

### kyc_verifications

**Primary Key:** id

**Foreign Keys:**
- `reviewer_id` → `core.users.id`
- `user_id` → `core.users.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `user_id` | `INTEGER` | No | No | Yes | No |
| `status` | `VARCHAR` | Yes | No | No | No |
| `provider` | `VARCHAR` | Yes | No | No | No |
| `verification_data` | `JSON` | Yes | No | No | No |
| `document_types` | `JSON` | Yes | No | No | No |
| `submitted_at` | `DATETIME` | Yes | No | No | No |
| `reviewed_at` | `DATETIME` | Yes | No | No | No |
| `reviewer_id` | `INTEGER` | Yes | No | Yes | No |

## Schema: ai

Tables: 6

### predictive_simulations

**Primary Key:** id

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `simulation_type` | `VARCHAR(50)` | No | No | No | No |
| `parameters_json` | `TEXT` | No | No | No | No |
| `result_json` | `TEXT` | No | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### ai_upload_jobs

**Primary Key:** id

**Foreign Keys:**
- `supplier_id` → `core.users.id`
- `created_product_id` → `commerce.products.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `supplier_id` | `INTEGER` | No | No | Yes | No |
| `status` | `VARCHAR(20)` | No | No | No | No |
| `model_used` | `VARCHAR(100)` | Yes | No | No | No |
| `prompt_hash` | `VARCHAR(64)` | Yes | No | No | No |
| `tokens_used` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `source_media_json` | `TEXT` | Yes | No | No | No |
| `created_product_id` | `INTEGER` | Yes | No | Yes | No |
| `error_log` | `TEXT` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |
| `updated_at` | `DATETIME` | Yes | No | No | No |

### ai_staging_products

**Primary Key:** id

**Foreign Keys:**
- `product_id` → `commerce.products.id`
- `job_id` → `ai.ai_upload_jobs.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `job_id` | `INTEGER` | No | No | Yes | No |
| `product_id` | `INTEGER` | Yes | No | Yes | No |
| `name` | `VARCHAR` | No | No | No | No |
| `description` | `TEXT` | Yes | No | No | No |
| `price` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `stock` | `INTEGER` | Yes | No | No | No |
| `category` | `VARCHAR` | Yes | No | No | No |
| `subcategory` | `VARCHAR` | Yes | No | No | No |
| `color` | `VARCHAR` | Yes | No | No | No |
| `brand` | `VARCHAR` | Yes | No | No | No |
| `tags` | `JSON` | Yes | No | No | No |
| `sizes` | `JSON` | Yes | No | No | No |
| `materials` | `JSON` | Yes | No | No | No |
| `image_url` | `VARCHAR` | Yes | No | No | No |
| `additional_media` | `JSON` | Yes | No | No | No |
| `ai_description` | `TEXT` | Yes | No | No | No |
| `variant_axes` | `JSON` | Yes | No | No | No |
| `attributes` | `JSON` | Yes | No | No | No |
| `confidence_score` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `requires_human_review` | `BOOLEAN` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### ai_staging_variants

**Primary Key:** id

**Foreign Keys:**
- `job_id` → `ai.ai_upload_jobs.id`
- `staging_product_id` → `ai.ai_staging_products.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `job_id` | `INTEGER` | No | No | Yes | No |
| `staging_product_id` | `INTEGER` | No | No | Yes | No |
| `variant_key` | `VARCHAR(64)` | Yes | No | No | No |
| `size` | `VARCHAR` | Yes | No | No | No |
| `color` | `VARCHAR` | Yes | No | No | No |
| `material` | `VARCHAR` | Yes | No | No | No |
| `pattern` | `VARCHAR` | Yes | No | No | No |
| `gender` | `VARCHAR` | Yes | No | No | No |
| `sku` | `VARCHAR` | Yes | No | No | No |
| `barcode` | `VARCHAR` | Yes | No | No | No |
| `product_code` | `VARCHAR` | Yes | No | No | No |
| `price` | `NUMERIC(10, 2)` | Yes | No | No | No |
| `stock` | `INTEGER` | Yes | No | No | No |
| `media_url` | `VARCHAR` | Yes | No | No | No |
| `attributes_json` | `TEXT` | Yes | No | No | No |
| `is_active` | `BOOLEAN` | Yes | No | No | No |
| `confidence_score` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `requires_human_review` | `BOOLEAN` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |

### ai_generation_logs

**Primary Key:** id

**Foreign Keys:**
- `job_id` → `ai.ai_upload_jobs.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `job_id` | `INTEGER` | No | No | Yes | No |
| `field` | `VARCHAR(40)` | No | No | No | No |
| `model_used` | `VARCHAR(100)` | Yes | No | No | No |
| `prompt_hash` | `VARCHAR(64)` | Yes | No | No | No |
| `tokens_used` | `NUMERIC(12, 2)` | Yes | No | No | No |
| `cost` | `NUMERIC(12, 6)` | Yes | No | No | No |
| `confidence` | `NUMERIC(5, 4)` | Yes | No | No | No |
| `country_code` | `VARCHAR(10)` | Yes | No | No | No |
| `created_at` | `DATETIME` | Yes | No | No | No |

### upload_jobs

**Primary Key:** id

**Foreign Keys:**
- `supplier_id` → `core.users.id`
- `product_id` → `commerce.products.id`

| Column | Type | Nullable | PK | FK | Unique |
|--------|------|----------|-----|-----|--------|
| `id` | `INTEGER` | No | Yes | No | No |
| `supplier_id` | `INTEGER` | No | No | Yes | No |
| `filename` | `VARCHAR(512)` | No | No | No | No |
| `status` | `VARCHAR(32)` | No | No | No | No |
| `progress` | `FLOAT` | No | No | No | No |
| `strategy_winner` | `VARCHAR(64)` | Yes | No | No | No |
| `strategy_score` | `FLOAT` | Yes | No | No | No |
| `ai_result` | `JSON` | Yes | No | No | No |
| `product_id` | `INTEGER` | Yes | No | Yes | No |
| `error_message` | `TEXT` | Yes | No | No | No |
| `image_url` | `VARCHAR(1024)` | Yes | No | No | No |
| `processed_image_url` | `VARCHAR(1024)` | Yes | No | No | No |
| `started_at` | `DATETIME` | Yes | No | No | No |
| `completed_at` | `DATETIME` | Yes | No | No | No |
| `created_at` | `DATETIME` | No | No | No | No |
| `updated_at` | `DATETIME` | No | No | No | No |
| `stt_duration_ms` | `FLOAT` | Yes | No | No | No |
| `nlp_duration_ms` | `FLOAT` | Yes | No | No | No |
| `bg_duration_ms` | `FLOAT` | Yes | No | No | No |
| `ai_duration_ms` | `FLOAT` | Yes | No | No | No |
| `total_duration_ms` | `FLOAT` | Yes | No | No | No |
