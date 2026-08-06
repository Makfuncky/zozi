# Generated Data Dictionary

_Auto-generated from `Base.metadata` (264 tables). Do not edit by hand._

Regenerate with: `python backend/scripts/generate_data_dictionary.py`

## Domain Index

- **audit**: 3 tables
- **commerce**: 17 tables
- **comms**: 23 tables
- **core**: 22 tables
- **finance**: 20 tables
- **hr**: 21 tables
- **logistics**: 22 tables
- **media**: 10 tables
- **other**: 100 tables
- **risk**: 14 tables
- **supplier**: 10 tables
- **treasury**: 2 tables


## audit (3 tables)

### `admin_activity_logs`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| admin_id | INTEGER | no |  | users.id |
| action | VARCHAR | no |  |  |
| details | JSON | yes |  |  |
| ip_address | VARCHAR | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_admin_activity_logs_country_code, ix_admin_activity_logs_id

### `admin_change_audit_logs`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| admin_id | INTEGER | no |  | users.id |
| action | VARCHAR | no |  |  |
| entity | VARCHAR | no |  |  |
| entity_key | VARCHAR | yes |  |  |
| before_json | TEXT | yes |  |  |
| after_json | TEXT | yes |  |  |
| notes | TEXT | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_admin_change_audit_logs_country_code, ix_admin_change_audit_logs_id

### `permission_audit_log`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| actor_id | INTEGER | no |  | users.id |
| action | VARCHAR(50) | no |  |  |
| target_user_id | INTEGER | yes |  | users.id |
| target_role | VARCHAR(80) | yes |  |  |
| permission_id | INTEGER | yes |  | permissions.id |
| country_code | VARCHAR(10) | yes |  |  |
| details | TEXT | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_permission_audit_log_id


## commerce (17 tables)

### `banners`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| title | VARCHAR | no |  |  |
| subtitle | VARCHAR | yes |  |  |
| image_url | VARCHAR | yes |  |  |
| link | VARCHAR | yes |  |  |
| banner_type | VARCHAR | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| is_deleted | BOOLEAN | yes |  |  |
| deleted_at | DATETIME | yes |  |  |
| deleted_by_id | INTEGER | yes |  | users.id |
| sort_order | INTEGER | yes |  |  |
| bg_color | VARCHAR | yes |  |  |
| text_color | VARCHAR | yes |  |  |
| subtitle_color | VARCHAR | yes |  |  |
| btn_bg_color | VARCHAR | yes |  |  |
| btn_text_color | VARCHAR | yes |  |  |
| badge_text | VARCHAR | yes |  |  |
| badge_color | VARCHAR | yes |  |  |
| effect | VARCHAR | yes |  |  |
| video_url | VARCHAR | yes |  |  |
| cta_label | VARCHAR | yes |  |  |
| cta_url | VARCHAR | yes |  |  |
| starts_at | DATETIME | yes |  |  |
| ends_at | DATETIME | yes |  |  |
| created_by | INTEGER | yes |  | users.id |
| country_code | VARCHAR(10) | yes |  | country_configs.code |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_banners_country_code, ix_banners_id

### `cart_items`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | no |  | users.id |
| product_id | INTEGER | no |  | products.id |
| quantity | INTEGER | yes |  |  |
| selected_size | VARCHAR(50) | no |  |  |
| selected_color | VARCHAR(50) | no |  |  |
| variant_id | INTEGER | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_cart_items_country_code, ix_cart_items_id

### `carts`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | no |  | users.id |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_carts_country_code, ix_carts_id

### `categories`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| name | VARCHAR | no |  |  |
| slug | VARCHAR | yes |  |  |
| description | TEXT | yes |  |  |
| parent_id | INTEGER | yes |  | categories.id |
| icon | VARCHAR | yes |  |  |
| image_url | VARCHAR | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| is_featured | BOOLEAN | yes |  |  |
| sort_order | INTEGER | yes |  |  |
| commission_rate | NUMERIC(5, 4) | yes |  |  |
| meta_title | VARCHAR | yes |  |  |
| meta_description | TEXT | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |
| path | VARCHAR(255) | yes |  |  |
| depth | INTEGER | yes |  |  |

Indexes: ix_categories_country_code, ix_categories_id, ix_categories_path, ix_categories_slug

### `coupon_usage`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| coupon_id | INTEGER | no |  | coupons.id |
| user_id | INTEGER | no |  | users.id |
| order_id | INTEGER | yes |  | orders.id |
| country_code | VARCHAR(10) | yes |  | country_configs.code |
| created_at | DATETIME | yes |  |  |

Indexes: ix_coupon_usage_country_code, ix_coupon_usage_id

### `coupons`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| code | VARCHAR | no |  |  |
| discount_type | VARCHAR | yes |  |  |
| discount_value | NUMERIC(5, 2) | yes |  |  |
| minimum_order | NUMERIC(10, 2) | yes |  |  |
| maximum_discount | NUMERIC(10, 2) | yes |  |  |
| usage_limit | INTEGER | yes |  |  |
| usage_count | INTEGER | yes |  |  |
| starts_at | DATETIME | yes |  |  |
| expires_at | DATETIME | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| is_deleted | BOOLEAN | yes |  |  |
| deleted_at | DATETIME | yes |  |  |
| deleted_by_id | INTEGER | yes |  | users.id |
| country_code | VARCHAR(10) | yes |  | country_configs.code |
| created_at | DATETIME | yes |  |  |

Indexes: ix_coupons_code, ix_coupons_country_code, ix_coupons_id

### `flash_sale_items`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| flash_sale_id | INTEGER | no |  | flash_sales.id |
| product_id | INTEGER | no |  | products.id |
| original_price | NUMERIC(10, 2) | no |  |  |
| discounted_price | NUMERIC(10, 2) | no |  |  |
| quantity_limit | INTEGER | yes |  |  |
| country_code | VARCHAR(10) | yes |  | country_configs.code |
| created_at | DATETIME | yes |  |  |

Indexes: ix_flash_sale_items_country_code, ix_flash_sale_items_id

### `flash_sales`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| title | VARCHAR | no |  |  |
| description | TEXT | yes |  |  |
| starts_at | DATETIME | no |  |  |
| ends_at | DATETIME | no |  |  |
| discount_pct | NUMERIC(5, 2) | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| is_deleted | BOOLEAN | yes |  |  |
| deleted_at | DATETIME | yes |  |  |
| deleted_by_id | INTEGER | yes |  | users.id |
| product_ids | JSON | yes |  |  |
| country_code | VARCHAR(10) | yes |  | country_configs.code |
| created_at | DATETIME | yes |  |  |

Indexes: ix_flash_sales_country_code, ix_flash_sales_id

### `order_items`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| order_id | INTEGER | no |  | orders.id |
| product_id | INTEGER | no |  | products.id |
| variant_id | INTEGER | yes |  |  |
| supplier_id | INTEGER | yes |  |  |
| quantity | INTEGER | yes |  |  |
| unit_price | NUMERIC(10, 2) | yes |  |  |
| price | NUMERIC(10, 2) | yes |  |  |
| total_price | NUMERIC(10, 2) | yes |  |  |
| product_name | VARCHAR | yes |  |  |
| product_image | VARCHAR | yes |  |  |
| selected_size | VARCHAR | yes |  |  |
| selected_color | VARCHAR | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  | country_configs.code |

Indexes: ix_order_items_country_code, ix_order_items_id, ix_order_items_order_id, ix_order_items_product_id

### `order_logistics_allocations`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| order_id | INTEGER | no |  | orders.id |
| supplier_id | INTEGER | no |  | users.id |
| shipment_id | INTEGER | yes |  | shipments.id |
| partner_id | INTEGER | yes |  | logistics_partners.id |
| service_area_id | INTEGER | yes |  | logistics_partner_service_areas.id |
| allocation_source | VARCHAR | yes |  |  |
| partner_name_snapshot | VARCHAR | yes |  |  |
| partner_code_snapshot | VARCHAR | yes |  |  |
| service_area_label_snapshot | VARCHAR | yes |  |  |
| destination_country | VARCHAR | yes |  |  |
| destination_city | VARCHAR | yes |  |  |
| shipping_amount | NUMERIC(10, 2) | yes |  |  |
| pickup_charge | NUMERIC(10, 2) | yes |  |  |
| dropoff_charge | NUMERIC(10, 2) | yes |  |  |
| accepted_vehicle_rule_id | INTEGER | yes |  |  |
| accepted_vehicle_type | VARCHAR | yes |  |  |
| accepted_vehicle_multiplier | NUMERIC(5, 4) | yes |  |  |
| accepted_shipping_amount | NUMERIC(10, 2) | yes |  |  |
| accepted_pickup_charge | NUMERIC(10, 2) | yes |  |  |
| accepted_dropoff_charge | NUMERIC(10, 2) | yes |  |  |
| estimated_delivery_min | INTEGER | yes |  |  |
| estimated_delivery_max | INTEGER | yes |  |  |
| currency | VARCHAR | yes |  |  |
| pricing_breakdown_json | TEXT | yes |  |  |
| accepted_pricing_breakdown_json | TEXT | yes |  |  |
| country_code | VARCHAR(10) | yes |  | country_configs.code |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_order_logistics_allocations_country_code, ix_order_logistics_allocations_id

### `orders`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| order_number | VARCHAR | yes |  |  |
| customer_id | INTEGER | yes |  | users.id |
| user_id | INTEGER | no |  | users.id |
| status | VARCHAR | yes |  |  |
| status_label | VARCHAR(50) | yes |  |  |
| payment_status | VARCHAR | yes |  |  |
| payment_method | VARCHAR | yes |  |  |
| payment_provider | VARCHAR | yes |  |  |
| payment_intent_id | VARCHAR | yes |  |  |
| subtotal | NUMERIC(10, 2) | yes |  |  |
| subtotal_amount | NUMERIC(10, 2) | yes |  |  |
| shipping_fee | NUMERIC(10, 2) | yes |  |  |
| shipping_amount | NUMERIC(10, 2) | yes |  |  |
| tax_amount | NUMERIC(10, 2) | yes |  |  |
| vat_amount | NUMERIC(10, 2) | yes |  |  |
| discount_amount | NUMERIC(10, 2) | yes |  |  |
| total | NUMERIC(10, 2) | yes |  |  |
| total_amount | NUMERIC(10, 2) | yes |  |  |
| coupon_code | VARCHAR | yes |  |  |
| fraud_score | NUMERIC(5, 2) | yes |  |  |
| fraud_action | VARCHAR | yes |  |  |
| currency | VARCHAR | yes |  |  |
| shipping_address | TEXT | yes |  |  |
| shipping_city | VARCHAR | yes |  |  |
| shipping_country | VARCHAR | yes |  |  |
| shipping_postal_code | VARCHAR | yes |  |  |
| customer_phone | VARCHAR | yes |  |  |
| delivery_location | VARCHAR | yes |  |  |
| delivery_note | VARCHAR | yes |  |  |
| tracking_number | VARCHAR | yes |  |  |
| selected_partner_id | INTEGER | yes |  |  |
| selected_service_area_id | INTEGER | yes |  |  |
| estimated_delivery_min | INTEGER | yes |  |  |
| estimated_delivery_max | INTEGER | yes |  |  |
| payment_gateway_code | VARCHAR | yes |  |  |
| payment_gateway_fee_amount | NUMERIC(10, 2) | yes |  |  |
| payment_customer_total_amount | NUMERIC(10, 2) | yes |  |  |
| payment_gateway_fee_passed_to_customer | NUMERIC(10, 2) | yes |  |  |
| paid_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  | country_configs.code |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| is_deleted | BOOLEAN | yes |  |  |
| deleted_at | DATETIME | yes |  |  |

Indexes: ix_orders_country_code, ix_orders_customer_id, ix_orders_id, ix_orders_order_number, ix_orders_status, ix_orders_user_id

### `products`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| name | VARCHAR | no |  |  |
| slug | VARCHAR | yes |  |  |
| description | TEXT | yes |  |  |
| short_description | TEXT | yes |  |  |
| ai_description | TEXT | yes |  |  |
| sku | VARCHAR | yes |  |  |
| barcode | VARCHAR | yes |  |  |
| price | NUMERIC(10, 2) | no |  |  |
| compare_price | NUMERIC(10, 2) | yes |  |  |
| cost_price | NUMERIC(10, 2) | yes |  |  |
| stock | INTEGER | yes |  |  |
| low_stock_threshold | INTEGER | yes |  |  |
| weight | NUMERIC(10, 2) | yes |  |  |
| dimensions | VARCHAR | yes |  |  |
| materials | JSON | yes |  |  |
| image_url | VARCHAR | yes |  |  |
| images | JSON | yes |  |  |
| category | VARCHAR | yes |  |  |
| category_id | INTEGER | yes |  | categories.id |
| tags | JSON | yes |  |  |
| attributes | JSON | yes |  |  |
| supplier_id | INTEGER | yes |  | users.id |
| country_code | VARCHAR(10) | yes |  | country_configs.code |
| is_active | BOOLEAN | yes |  |  |
| is_featured | BOOLEAN | yes |  |  |
| is_digital | BOOLEAN | yes |  |  |
| is_verified | BOOLEAN | yes |  |  |
| moderation_status | VARCHAR | yes |  |  |
| brand | VARCHAR | yes |  |  |
| color | VARCHAR | yes |  |  |
| sizes | JSON | yes |  |  |
| rating | NUMERIC(3, 2) | yes |  |  |
| sales_count | INTEGER | yes |  |  |
| meta_title | VARCHAR | yes |  |  |
| meta_description | TEXT | yes |  |  |
| is_approved | BOOLEAN | yes |  |  |
| is_deleted | BOOLEAN | yes |  |  |
| discount_starts_at | DATETIME | yes |  |  |
| discount_ends_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| filter_attributes | JSON | yes |  |  |
| search_vector | JSON | yes |  |  |
| video_count | INTEGER | yes |  |  |
| variant_axes | JSON | yes |  |  |
| bg_preset | VARCHAR | yes |  |  |
| visibility_regions | TEXT | yes |  |  |
| slug_hash | VARCHAR(32) | yes |  |  |
| subcategory | VARCHAR | yes |  |  |
| return_window_days | INTEGER | yes |  |  |
| is_new | BOOLEAN | yes |  |  |

Indexes: ix_products_country_code, ix_products_id, ix_products_slug, ix_products_slug_hash

### `return_abuse_patterns`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | no |  | users.id |
| abuse_type | VARCHAR(50) | no |  |  |
| occurrence_count | INTEGER | yes |  |  |
| first_occurrence | DATETIME | yes |  |  |
| last_occurrence | DATETIME | yes |  |  |
| is_blocked | BOOLEAN | yes |  |  |

Indexes: ix_return_abuse_patterns_id

### `return_requests`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| order_id | INTEGER | no |  | orders.id |
| order_item_id | INTEGER | yes |  |  |
| customer_id | INTEGER | yes |  | users.id |
| intent | VARCHAR | yes |  |  |
| reason | VARCHAR | no |  |  |
| description | TEXT | yes |  |  |
| details | TEXT | yes |  |  |
| supplier_review_state | TEXT | yes |  |  |
| images | TEXT | yes |  |  |
| status | VARCHAR | yes |  |  |
| refund_amount | NUMERIC(10, 2) | yes |  |  |
| items | TEXT | yes |  |  |
| return_window_days | INTEGER | yes |  |  |
| delivered_at | DATETIME | yes |  |  |
| return_deadline | DATETIME | yes |  |  |
| resolution_notes | TEXT | yes |  |  |
| country_code | VARCHAR(10) | yes |  | country_configs.code |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_return_requests_country_code, ix_return_requests_id

### `reviews`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| product_id | INTEGER | no |  | products.id |
| user_id | INTEGER | no |  | users.id |
| rating | INTEGER | no |  |  |
| title | VARCHAR | yes |  |  |
| comment | TEXT | yes |  |  |
| image_url | VARCHAR | yes |  |  |
| is_approved | BOOLEAN | yes |  |  |
| is_deleted | BOOLEAN | yes |  |  |
| is_verified_purchase | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_reviews_country_code, ix_reviews_id

### `wishlist_items`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | no |  | users.id |
| product_id | INTEGER | no |  | products.id |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_wishlist_items_country_code, ix_wishlist_items_id

### `wishlists`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | no |  | users.id |
| product_id | INTEGER | no |  | products.id |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_wishlists_country_code, ix_wishlists_id


## comms (23 tables)

### `chatbot_query_events`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | yes |  | users.id |
| session_id | VARCHAR(64) | no |  |  |
| event_type | VARCHAR(30) | no |  |  |
| message | TEXT | yes |  |  |
| normalized_query | VARCHAR(500) | yes |  |  |
| intent | VARCHAR(100) | yes |  |  |
| filters_json | TEXT | yes |  |  |
| result_count | INTEGER | no |  |  |
| product_ids_json | TEXT | yes |  |  |
| clicked_product_id | INTEGER | yes |  | products.id |
| created_at | DATETIME | no |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_chatbot_events_clicked_product_id, ix_chatbot_events_created_at, ix_chatbot_events_intent_created, ix_chatbot_events_normalized_query, ix_chatbot_events_session_created, ix_chatbot_events_session_id, ix_chatbot_events_type_created, ix_chatbot_events_user_created, ix_chatbot_query_events_country_code, ix_chatbot_query_events_id

### `command_center_views`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | no |  | users.id |
| view_name | VARCHAR(100) | no |  |  |
| config | JSON | yes |  |  |
| is_default | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_command_center_views_id

### `communication_audit_trail`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| entity_type | VARCHAR(50) | no |  |  |
| entity_id | INTEGER | no |  |  |
| user_id | INTEGER | yes |  | users.id |
| action | VARCHAR(50) | no |  |  |
| channel | VARCHAR(50) | no |  |  |
| content_preview | TEXT | yes |  |  |
| metadata_json | JSON | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_comm_entity, ix_comm_user, ix_communication_audit_trail_id

### `email_campaign_logs`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| campaign_id | INTEGER | no |  | email_campaigns.id |
| recipient_email | VARCHAR | no |  |  |
| status | VARCHAR | yes |  |  |
| sent_at | DATETIME | yes |  |  |
| delivered_at | DATETIME | yes |  |  |
| opened_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_email_campaign_logs_id

### `email_campaigns`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| name | VARCHAR | no |  |  |
| subject | VARCHAR | no |  |  |
| status | VARCHAR | yes |  |  |
| send_at | DATETIME | yes |  |  |
| created_by | INTEGER | yes |  | users.id |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  | country_configs.code |

Indexes: ix_email_campaigns_country_code, ix_email_campaigns_id

### `email_delivery_events`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| event_type | VARCHAR | no |  |  |
| recipient_email | VARCHAR | no |  |  |
| subject | VARCHAR | yes |  |  |
| status | VARCHAR | yes |  |  |
| details | JSON | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_email_delivery_events_id

### `email_provider_configs`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| provider | VARCHAR | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| updated_by | INTEGER | yes |  | users.id |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| email_from_default | VARCHAR | yes |  |  |
| email_from_promotional | VARCHAR | yes |  |  |
| email_from_transactional | VARCHAR | yes |  |  |
| email_from_notification | VARCHAR | yes |  |  |
| email_from_alert | VARCHAR | yes |  |  |
| email_from_verification | VARCHAR | yes |  |  |
| email_from_login_verification | VARCHAR | yes |  |  |
| email_from_password_reset | VARCHAR | yes |  |  |
| resend_api_key | VARCHAR | yes |  |  |
| resend_webhook_secret | VARCHAR | yes |  |  |
| smtp_host | VARCHAR | yes |  |  |
| smtp_port | INTEGER | yes |  |  |
| smtp_username | VARCHAR | yes |  |  |
| smtp_password | VARCHAR | yes |  |  |
| smtp_use_tls | BOOLEAN | yes |  |  |
| smtp_use_ssl | BOOLEAN | yes |  |  |
| smtp_timeout_seconds | INTEGER | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_email_provider_configs_country_code, ix_email_provider_configs_id

### `email_suppressions`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| email | VARCHAR | no |  |  |
| reason | VARCHAR | no |  |  |
| source | VARCHAR | no |  |  |
| status | VARCHAR | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_email_suppressions_email, ix_email_suppressions_id

### `email_templates`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| name | VARCHAR(200) | no |  |  |
| subject | VARCHAR(500) | no |  |  |
| template_type | VARCHAR(50) | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_by | INTEGER | yes |  | users.id |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_email_templates_id, ix_email_templates_name

### `email_verification_tokens`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | yes |  | users.id |
| token | VARCHAR | yes |  |  |
| expires_at | DATETIME | no |  |  |
| used | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_email_verification_tokens_country_code, ix_email_verification_tokens_id, ix_email_verification_tokens_token, ix_email_verification_tokens_user_id

### `entity_chat_messages`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| thread_id | INTEGER | no |  | entity_chat_threads.id |
| sender_id | INTEGER | no |  | users.id |
| message | TEXT | no |  |  |
| message_type | VARCHAR(20) | yes |  |  |
| read_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_entity_chat_messages_id

### `entity_chat_threads`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| entity_type | VARCHAR | no |  |  |
| entity_id | INTEGER | no |  |  |
| title | VARCHAR(200) | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: idx_entity_thread, ix_entity_chat_threads_id

### `internal_channel_members`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| channel_id | INTEGER | no |  | internal_channels.id |
| user_id | INTEGER | no |  | users.id |
| role | VARCHAR(20) | yes |  |  |
| joined_at | DATETIME | yes |  |  |

Indexes: ix_internal_channel_members_id

### `internal_channels`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | yes |  | country_configs.code |
| entity_type | VARCHAR(50) | no |  |  |
| entity_id | INTEGER | no |  |  |
| name | VARCHAR(200) | no |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_internal_channel_entity, ix_internal_channels_id

### `internal_messages`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| channel_id | INTEGER | no |  | internal_channels.id |
| user_id | INTEGER | no |  | users.id |
| message | TEXT | no |  |  |
| message_type | VARCHAR(20) | yes |  |  |
| is_masked | BOOLEAN | yes |  |  |
| read_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_internal_messages_id, ix_internal_msg_channel, ix_internal_msg_user

### `internal_notices`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| title | VARCHAR(200) | no |  |  |
| content | TEXT | no |  |  |
| priority | VARCHAR(20) | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| valid_from | DATETIME | yes |  |  |
| valid_to | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_internal_notices_id

### `messages`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | yes |  | country_configs.code |
| from_user_id | INTEGER | no |  | users.id |
| to_user_id | INTEGER | no |  | users.id |
| subject | VARCHAR(200) | no |  |  |
| body | TEXT | yes |  |  |
| entity_type | VARCHAR(50) | yes |  |  |
| entity_id | INTEGER | yes |  |  |
| priority | VARCHAR(20) | yes |  |  |
| category | VARCHAR(50) | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| read_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_message_recipient, ix_message_sender, ix_messages_id

### `notifications`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | no |  | users.id |
| type | VARCHAR | yes |  |  |
| title | VARCHAR | no |  |  |
| message | TEXT | no |  |  |
| channel | VARCHAR | yes |  |  |
| priority | VARCHAR | yes |  |  |
| is_read | BOOLEAN | yes |  |  |
| read_at | DATETIME | yes |  |  |
| link | VARCHAR | yes |  |  |
| template | VARCHAR | yes |  |  |
| variables | JSON | yes |  |  |
| scheduled_at | DATETIME | yes |  |  |
| status | VARCHAR | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_notifications_country_code, ix_notifications_id, ix_notifications_is_read, ix_notifications_user_id, ix_notifications_user_read

### `proxy_call_logs`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| channel_id | INTEGER | no |  | proxy_channels.id |
| caller_id | INTEGER | no |  | users.id |
| callee_id | INTEGER | no |  | users.id |
| direction | VARCHAR | no |  |  |
| duration_seconds | INTEGER | yes |  |  |
| call_recording_url | VARCHAR | yes |  |  |
| is_recorded | BOOLEAN | yes |  |  |
| started_at | DATETIME | yes |  |  |
| ended_at | DATETIME | yes |  |  |

Indexes: ix_proxy_call_logs_id

### `proxy_channels`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| entity_type | VARCHAR | no |  |  |
| entity_id | INTEGER | no |  |  |
| proxy_phone | VARCHAR | no |  |  |
| proxy_email | VARCHAR | no |  |  |
| participants | JSON | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: idx_proxy_entity, ix_proxy_channels_id, ix_proxy_channels_proxy_email, ix_proxy_channels_proxy_phone

### `proxy_messages`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| session_id | INTEGER | no |  | proxy_sessions.id |
| sender_id | INTEGER | no |  | users.id |
| recipient_id | INTEGER | no |  | users.id |
| message_type | VARCHAR | yes |  |  |
| content | TEXT | no |  |  |
| is_masked | BOOLEAN | yes |  |  |
| read_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_proxy_messages_id

### `proxy_sessions`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| channel_id | INTEGER | no |  | proxy_channels.id |
| participant_one_id | INTEGER | no |  | users.id |
| participant_two_id | INTEGER | no |  | users.id |
| started_at | DATETIME | yes |  |  |
| ended_at | DATETIME | yes |  |  |
| is_encrypted | BOOLEAN | yes |  |  |
| session_metadata | JSON | yes |  |  |

Indexes: ix_proxy_sessions_id

### `push_notification_tokens`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | no |  | users.id |
| token | VARCHAR | no |  |  |
| device_type | VARCHAR | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_push_notification_tokens_country_code, ix_push_notification_tokens_id


## core (22 tables)

### `addresses`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | no |  | users.id |
| label | VARCHAR | yes |  |  |
| full_name | VARCHAR | no |  |  |
| phone | VARCHAR | yes |  |  |
| address_line1 | VARCHAR | no |  |  |
| address_line2 | VARCHAR | yes |  |  |
| city | VARCHAR | no |  |  |
| state | VARCHAR | yes |  |  |
| postal_code | VARCHAR | yes |  |  |
| country | VARCHAR | yes |  |  |
| is_default | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_addresses_country_code, ix_addresses_id

### `country_category_tax_rates`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| category_id | INTEGER | no |  | categories.id |
| tax_rate | NUMERIC(5, 4) | no |  |  |
| tax_name | VARCHAR(50) | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_country_category_tax_rates_id

### `country_cities`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| name | VARCHAR(200) | no |  |  |
| name_local | VARCHAR(200) | yes |  |  |
| population | INTEGER | yes |  |  |
| is_capital | BOOLEAN | yes |  |  |
| latitude | NUMERIC(10, 7) | yes |  |  |
| longitude | NUMERIC(10, 7) | yes |  |  |
| postal_code_prefix | VARCHAR(20) | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_country_cities_id

### `country_commission_rate_history`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| category_id | INTEGER | yes |  | categories.id |
| supplier_tier | VARCHAR(20) | no |  |  |
| rate_percent | NUMERIC(5, 4) | no |  |  |
| effective_from | DATETIME | no |  |  |
| effective_to | DATETIME | yes |  |  |
| changed_by | INTEGER | yes |  | users.id |
| change_reason | TEXT | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_comm_rate_effective, ix_country_commission_rate_history_id

### `country_commission_rates`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| supplier_tier | VARCHAR(20) | no |  |  |
| name | VARCHAR(50) | no |  |  |
| rate_percent | NUMERIC(5, 2) | no |  |  |
| fixed_fee | NUMERIC(10, 2) | yes |  |  |
| effective_from | DATETIME | yes |  |  |
| effective_to | DATETIME | yes |  |  |

Indexes: ix_country_commission_rates_id

### `country_communication_threads`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| entity_type | VARCHAR(50) | no |  |  |
| entity_id | INTEGER | no |  |  |
| participants | TEXT | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| last_message_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_comm_thread_entity, ix_country_communication_threads_id

### `country_communications`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| from_user_id | INTEGER | yes |  | users.id |
| to_user_id | INTEGER | yes |  | users.id |
| subject | VARCHAR(200) | no |  |  |
| body | TEXT | no |  |  |
| priority | VARCHAR(20) | yes |  |  |
| category | VARCHAR(50) | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| related_entity_type | VARCHAR(50) | yes |  |  |
| related_entity_id | INTEGER | yes |  |  |
| read_at | DATETIME | yes |  |  |
| attachments_json | TEXT | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_country_communications_id, ix_country_communications_recipient

### `country_config_versions`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| config_type | VARCHAR(50) | no |  |  |
| version | INTEGER | no |  |  |
| payload_json | TEXT | no |  |  |
| status | VARCHAR(20) | yes |  |  |
| draft_by | INTEGER | yes |  | users.id |
| approved_by | INTEGER | yes |  | users.id |
| published_at | DATETIME | yes |  |  |
| effective_from | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_country_config_version_status, ix_country_config_version_type, ix_country_config_versions_id

### `country_configs`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| code | VARCHAR(10) | no |  |  |
| name | VARCHAR | no |  |  |
| currency | VARCHAR(3) | yes |  |  |
| currency_symbol | VARCHAR(10) | yes |  |  |
| phone_code | VARCHAR(10) | yes |  |  |
| language | VARCHAR(10) | yes |  |  |
| timezone | VARCHAR(60) | yes |  |  |
| date_format | VARCHAR(20) | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| is_deleted | BOOLEAN | yes |  |  |
| is_default | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| official_name | VARCHAR(200) | yes |  |  |
| alpha3 | VARCHAR(3) | yes |  |  |
| flag_url | VARCHAR(500) | yes |  |  |
| currency_name | VARCHAR(50) | yes |  |  |
| exchange_rate_to_usd | NUMERIC(12, 6) | yes |  |  |
| capital | VARCHAR(100) | yes |  |  |
| region | VARCHAR(60) | yes |  |  |
| subregion | VARCHAR(60) | yes |  |  |
| population | INTEGER | yes |  |  |
| internet_penetration_pct | NUMERIC(5, 2) | yes |  |  |
| gdp_per_capita_usd | NUMERIC(12, 2) | yes |  |  |
| urbanization_pct | NUMERIC(5, 2) | yes |  |  |
| mobile_subs_per_100 | NUMERIC(5, 2) | yes |  |  |
| public_holidays_json | TEXT | yes |  |  |
| macro_indicators_json | TEXT | yes |  |  |
| tax_type | VARCHAR(20) | yes |  |  |
| tax_rate | NUMERIC(5, 4) | yes |  |  |
| tax_name | VARCHAR(50) | yes |  |  |
| tax_inclusive | BOOLEAN | yes |  |  |
| tax_exempt_categories_json | TEXT | yes |  |  |
| tax_reduced_rates_json | TEXT | yes |  |  |
| logistics_model | VARCHAR(30) | yes |  |  |
| default_vehicle_type | VARCHAR(30) | yes |  |  |
| base_rate | NUMERIC(10, 2) | yes |  |  |
| per_km_rate | NUMERIC(10, 2) | yes |  |  |
| minimum_charge | NUMERIC(10, 2) | yes |  |  |
| weight_surcharge_rate | NUMERIC(5, 4) | yes |  |  |
| weight_surcharge_threshold_kg | NUMERIC(10, 2) | yes |  |  |
| payment_methods_json | TEXT | yes |  |  |
| payment_gateways_json | TEXT | yes |  |  |
| logistics_providers_json | TEXT | yes |  |  |
| legal_rules_json | TEXT | yes |  |  |
| product_restrictions_json | TEXT | yes |  |  |
| address_format_json | TEXT | yes |  |  |
| regions_json | TEXT | yes |  |  |
| supplier_requirements_json | TEXT | yes |  |  |
| payout_settings_json | TEXT | yes |  |  |
| commission_tiers_json | TEXT | yes |  |  |
| suggested_gateway_rankings_json | TEXT | yes |  |  |
| suggested_commission_ranges_json | TEXT | yes |  |  |
| consumer_behavior_profile_json | TEXT | yes |  |  |
| economic_tier | VARCHAR(20) | yes |  |  |
| fraud_risk_tier | VARCHAR(10) | yes |  |  |
| suggested_logistics_model | VARCHAR(30) | yes |  |  |
| data_residency_tier | VARCHAR(20) | yes |  |  |
| data_residency_encrypted | TEXT | yes |  |  |
| confidence_score | NUMERIC(5, 4) | yes |  |  |
| audit_trail_json | TEXT | yes |  |  |
| cod_enabled | BOOLEAN | yes |  |  |
| cod_max_amount | NUMERIC(12, 2) | yes |  |  |
| cod_verification_required | BOOLEAN | yes |  |  |
| cod_remittance_days | INTEGER | yes |  |  |
| settlement_hold_days | INTEGER | yes |  |  |
| minimum_payout_amount | NUMERIC(12, 2) | yes |  |  |
| payout_currency | VARCHAR(10) | yes |  |  |
| supplier_kyc_tier | VARCHAR(20) | yes |  |  |
| supplier_onboarding_fee | NUMERIC(12, 2) | yes |  |  |
| supplier_monthly_fee | NUMERIC(12, 2) | yes |  |  |
| supplier_rating_threshold | NUMERIC(5, 2) | yes |  |  |
| legal_entity_required | BOOLEAN | yes |  |  |
| consumer_protection_days | INTEGER | yes |  |  |
| data_privacy_framework | VARCHAR(20) | yes |  |  |
| max_package_weight_kg | NUMERIC(8, 2) | yes |  |  |
| max_package_dimensions_cm | VARCHAR(200) | yes |  |  |
| signature_required_threshold | NUMERIC(10, 2) | yes |  |  |
| measurement_system | VARCHAR(10) | yes |  |  |
| working_days_json | TEXT | yes |  |  |
| supported_languages_json | TEXT | yes |  |  |
| payout_methods_json | TEXT | yes |  |  |
| logistics_zones_json | TEXT | yes |  |  |

Indexes: ix_country_configs_code, ix_country_configs_id

### `country_feature_flags`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| feature_key | VARCHAR(100) | no |  |  |
| feature_name | VARCHAR(200) | yes |  |  |
| is_enabled | BOOLEAN | yes |  |  |
| config | TEXT | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_country_feature_flags_id

### `country_gateway_configs`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| gateway_id | VARCHAR(50) | no |  |  |
| gateway_name | VARCHAR(100) | no |  |  |
| is_enabled | BOOLEAN | yes |  |  |
| priority | INTEGER | yes |  |  |
| credentials | TEXT | yes |  |  |
| environment | VARCHAR(20) | yes |  |  |
| settings | TEXT | yes |  |  |
| last_tested_at | DATETIME | yes |  |  |
| last_test_result | VARCHAR(20) | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_country_gateway_configs_id

### `country_gateway_credentials`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| gateway_name | VARCHAR(100) | no |  |  |
| environment | VARCHAR(20) | yes |  |  |
| credentials | JSON | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_country_gateway_credentials_id

### `country_holiday_calendars`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| holiday_date | DATETIME | no |  |  |
| name | VARCHAR(200) | no |  |  |
| local_name | VARCHAR(200) | yes |  |  |
| is_observed | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_country_holiday_calendars_id, ix_country_holiday_date

### `country_legal_contracts`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| contract_type | VARCHAR(50) | no |  |  |
| version | VARCHAR(20) | yes |  |  |
| content_html | TEXT | no |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_country_legal_contracts_id

### `country_localization`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| default_numeral_system | VARCHAR(20) | yes |  |  |
| hijri_calendar_enabled | BOOLEAN | yes |  |  |
| rtl_layout_enabled | BOOLEAN | yes |  |  |
| address_format | VARCHAR(200) | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_country_localization_id

### `country_logistics_zones`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| zone_code | VARCHAR(50) | no |  |  |
| zone_name | VARCHAR(200) | no |  |  |
| zone_type | VARCHAR(20) | yes |  |  |
| cities | TEXT | yes |  |  |
| pricing_config | TEXT | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_country_logistics_zones_id

### `country_map_configs`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| map_provider | VARCHAR(30) | yes |  |  |
| api_key_ref | VARCHAR(100) | yes |  |  |
| default_zoom | INTEGER | yes |  |  |
| show_regions | BOOLEAN | yes |  |  |
| show_cities | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_country_map_configs_country_code, ix_country_map_configs_id

### `country_payment_aliases`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| alias_type | VARCHAR(50) | no |  |  |
| alias_value | VARCHAR(200) | no |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_country_payment_aliases_id

### `country_payout_rules`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| supplier_tier | VARCHAR(20) | yes |  |  |
| min_amount | NUMERIC(15, 3) | yes |  |  |
| max_amount | NUMERIC(15, 3) | yes |  |  |
| fixed_fee | NUMERIC(15, 3) | yes |  |  |
| percent_fee | NUMERIC(5, 4) | yes |  |  |
| settlement_days | INTEGER | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_country_payout_rules_id, ix_payout_supplier

### `country_staff_assignments`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | no |  | users.id |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| role_in_country | VARCHAR(40) | no |  |  |
| is_active | BOOLEAN | yes |  |  |
| assigned_by | INTEGER | yes |  | users.id |
| notes | TEXT | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_country_staff_assignments_id, ix_staff_user

### `permissions`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| category_id | INTEGER | no |  | permission_categories.id |
| name | VARCHAR(150) | no |  |  |
| slug | VARCHAR(150) | no |  |  |
| description | TEXT | yes |  |  |
| scope | VARCHAR(20) | no |  |  |
| is_active | BOOLEAN | yes |  |  |
| country_code | VARCHAR(10) | no |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_permissions_id

### `users`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| email | VARCHAR | yes |  |  |
| username | VARCHAR | yes |  |  |
| full_name | VARCHAR(160) | yes |  |  |
| hashed_password | VARCHAR | yes |  |  |
| role | VARCHAR | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| phone | VARCHAR | yes |  |  |
| profile_image | VARCHAR | yes |  |  |
| preferred_language | VARCHAR | yes |  |  |
| preferred_currency | VARCHAR(10) | yes |  |  |
| preferred_country | VARCHAR(10) | yes |  |  |
| email_verified | BOOLEAN | yes |  |  |
| last_login | DATETIME | yes |  |  |
| is_verified | BOOLEAN | yes |  |  |
| staff_role_label | VARCHAR(120) | yes |  |  |
| staff_title | VARCHAR(120) | yes |  |  |
| staff_department | VARCHAR(120) | yes |  |  |
| staff_country_codes | TEXT | yes |  |  |
| staff_permissions | TEXT | yes |  |  |
| staff_area_of_operation | TEXT | yes |  |  |
| staff_hire_date | DATETIME | yes |  |  |
| staff_experience_level | VARCHAR(50) | yes |  |  |
| staff_performance_summary | TEXT | yes |  |  |
| staff_assigned_tasks | JSON | yes |  |  |
| staff_assigned_projects | JSON | yes |  |  |
| staff_notes | TEXT | yes |  |  |
| is_deleted | BOOLEAN | yes |  |  |
| deleted_at | DATETIME | yes |  |  |
| referral_code | VARCHAR | yes |  |  |
| referred_by_user_id | INTEGER | yes |  | users.id |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| referral_points | INTEGER | yes |  |  |
| sharing_points | INTEGER | yes |  |  |
| totp_enabled | BOOLEAN | yes |  |  |
| totp_secret | VARCHAR | yes |  |  |
| last_seen_at | DATETIME | yes |  |  |
| is_current | BOOLEAN | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_users_country_code, ix_users_id, ix_users_referral_code, ix_users_role


## finance (20 tables)

### `account_balances`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| account_id | INTEGER | no |  | accounts.id |
| user_id | INTEGER | yes |  | users.id |
| balance | NUMERIC(16, 4) | yes |  |  |
| currency | VARCHAR(3) | yes |  |  |
| last_entry_id | INTEGER | yes |  |  |
| last_entry_at | DATETIME | yes |  |  |
| last_updated | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_account_balance_account, ix_account_balance_user, ix_account_balances_country_code, ix_account_balances_id

### `account_groups`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| code | VARCHAR(10) | no |  |  |
| name | VARCHAR(100) | no |  |  |
| description | TEXT | yes |  |  |
| account_type | VARCHAR(30) | no |  |  |
| normal_side | VARCHAR(10) | no |  |  |
| display_order | INTEGER | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_account_groups_code, ix_account_groups_country_code, ix_account_groups_id, ix_account_groups_order

### `accounts`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| group_id | INTEGER | yes |  | account_groups.id |
| code | VARCHAR(20) | no |  |  |
| name | VARCHAR(200) | no |  |  |
| normal_side | VARCHAR(10) | no |  |  |
| currency | VARCHAR(3) | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| display_order | INTEGER | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_accounts_code, ix_accounts_country_code, ix_accounts_group, ix_accounts_id

### `ap_ledger_entries`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| supplier_id | INTEGER | no |  | users.id |
| order_id | INTEGER | yes |  | orders.id |
| invoice_id | INTEGER | yes |  | invoices.id |
| settlement_id | INTEGER | yes |  | supplier_settlements.id |
| reference_type | VARCHAR(50) | yes |  |  |
| reference_id | INTEGER | yes |  |  |
| entry_type | VARCHAR(20) | no |  |  |
| amount | NUMERIC(12, 2) | no |  |  |
| balance_after | NUMERIC(12, 2) | yes |  |  |
| currency | VARCHAR(3) | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| due_date | DATETIME | yes |  |  |
| paid_at | DATETIME | yes |  |  |
| description | TEXT | yes |  |  |
| created_by | INTEGER | yes |  | users.id |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |
| is_deleted | BOOLEAN | yes |  |  |
| deleted_at | DATETIME | yes |  |  |

Indexes: ix_ap_ledger_entries_country_code, ix_ap_ledger_entries_id, ix_ap_ledger_entries_is_deleted, ix_ap_ledger_entries_supplier_id, ix_ap_ledger_status, ix_ap_ledger_supplier

### `ar_ledger_entries`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| customer_id | INTEGER | no |  | users.id |
| order_id | INTEGER | yes |  | orders.id |
| invoice_id | INTEGER | yes |  | invoices.id |
| reference_type | VARCHAR(50) | yes |  |  |
| reference_id | INTEGER | yes |  |  |
| entry_type | VARCHAR(20) | no |  |  |
| amount | NUMERIC(12, 2) | no |  |  |
| balance_after | NUMERIC(12, 2) | yes |  |  |
| currency | VARCHAR(3) | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| due_date | DATETIME | yes |  |  |
| settled_at | DATETIME | yes |  |  |
| description | TEXT | yes |  |  |
| created_by | INTEGER | yes |  | users.id |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |
| is_deleted | BOOLEAN | yes |  |  |
| deleted_at | DATETIME | yes |  |  |

Indexes: ix_ar_ledger_entries_country_code, ix_ar_ledger_entries_customer_id, ix_ar_ledger_entries_id, ix_ar_ledger_entries_is_deleted, ix_ar_ledger_status, ix_ar_ledger_user

### `commission_agreements`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| supplier_id | INTEGER | no |  | users.id |
| country_code | VARCHAR(10) | yes |  |  |
| tier | VARCHAR(20) | no |  |  |
| rate | NUMERIC(5, 4) | no |  |  |
| set_by_admin_id | INTEGER | yes |  | users.id |
| is_active | BOOLEAN | yes |  |  |
| effective_from | DATETIME | yes |  |  |
| effective_to | DATETIME | yes |  |  |
| note | TEXT | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_commission_agreements_id

### `commission_badge_tiers`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| name | VARCHAR(100) | no |  |  |
| badge_level | VARCHAR(50) | no |  |  |
| commission_rate | NUMERIC(5, 4) | no |  |  |
| setup_fee | NUMERIC(12, 2) | yes |  |  |
| recurring_fee | NUMERIC(12, 2) | yes |  |  |
| recurring_interval | VARCHAR(20) | yes |  |  |
| benefits_json | TEXT | yes |  |  |
| min_fulfilled_orders | INTEGER | yes |  |  |
| min_monthly_revenue | NUMERIC(15, 2) | yes |  |  |
| sort_order | INTEGER | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| updated_by | INTEGER | yes |  | users.id |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_commission_badge_tiers_country_code, ix_commission_badge_tiers_id

### `commission_category_rates`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| category_id | INTEGER | yes |  | categories.id |
| category_slug | VARCHAR(100) | yes |  |  |
| category_display_name | VARCHAR(100) | yes |  |  |
| country_code | VARCHAR(10) | yes |  | country_configs.code |
| rate_percent | NUMERIC(5, 2) | no |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_commission_category_rates_id

### `commission_global_configs`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| default_rate | NUMERIC(5, 4) | yes |  |  |
| low_value_threshold | NUMERIC(10, 2) | yes |  |  |
| fixed_cap_amount | NUMERIC(10, 2) | yes |  |  |
| fixed_cap_enabled | BOOLEAN | yes |  |  |
| margin_protection_enabled | BOOLEAN | yes |  |  |
| margin_threshold | NUMERIC(5, 4) | yes |  |  |
| updated_by | INTEGER | yes |  | users.id |
| updated_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_commission_global_configs_country_code, ix_commission_global_configs_id

### `commission_ledger_entries`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| supplier_id | INTEGER | no |  | users.id |
| order_id | INTEGER | yes |  | orders.id |
| order_item_id | INTEGER | yes |  | order_items.id |
| product_id | INTEGER | yes |  | products.id |
| category_slug | VARCHAR(100) | yes |  |  |
| badge_level | VARCHAR(20) | yes |  |  |
| global_default_rate | NUMERIC(5, 4) | yes |  |  |
| category_rate | NUMERIC(5, 4) | yes |  |  |
| badge_rate | NUMERIC(5, 4) | yes |  |  |
| override_rate | NUMERIC(5, 4) | yes |  |  |
| applied_rate | NUMERIC(5, 4) | yes |  |  |
| calculation_method | VARCHAR(20) | yes |  |  |
| order_value | NUMERIC(12, 2) | yes |  |  |
| commission_pct | NUMERIC(12, 2) | yes |  |  |
| cap_applied | BOOLEAN | yes |  |  |
| commission_amount | NUMERIC(12, 2) | yes |  |  |
| low_value_threshold_used | BOOLEAN | yes |  |  |
| fixed_cap_used | BOOLEAN | yes |  |  |
| override_flag | BOOLEAN | yes |  |  |
| is_adjusted | BOOLEAN | yes |  |  |
| currency | VARCHAR(3) | yes |  |  |
| amount | NUMERIC(12, 2) | yes |  |  |
| adjusted_by | INTEGER | yes |  | users.id |
| status | VARCHAR | yes |  |  |
| credited_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_commission_ledger_entries_country_code, ix_commission_ledger_entries_id

### `invoice_items`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| invoice_id | INTEGER | no |  | invoices.id |
| product_id | INTEGER | yes |  | products.id |
| description | VARCHAR | no |  |  |
| quantity | INTEGER | yes |  |  |
| unit_price | NUMERIC(10, 2) | no |  |  |
| discount_amount | NUMERIC(10, 2) | yes |  |  |
| tax_rate | NUMERIC(5, 2) | yes |  |  |
| line_total | NUMERIC(10, 2) | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_invoice_items_country_code, ix_invoice_items_id

### `invoices`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| order_id | INTEGER | no |  | orders.id |
| shipment_id | INTEGER | yes |  | shipments.id |
| supplier_id | INTEGER | yes |  | users.id |
| invoice_number | VARCHAR | yes |  |  |
| invoice_type | VARCHAR | yes |  |  |
| subtotal | NUMERIC(12, 2) | yes |  |  |
| tax_amount | NUMERIC(12, 2) | yes |  |  |
| shipping_amount | NUMERIC(12, 2) | yes |  |  |
| discount_amount | NUMERIC(12, 2) | yes |  |  |
| total_amount | NUMERIC(12, 2) | yes |  |  |
| currency | VARCHAR(3) | yes |  |  |
| status | VARCHAR | yes |  |  |
| issued_at | DATETIME | yes |  |  |
| due_at | DATETIME | yes |  |  |
| picked_at | DATETIME | yes |  |  |
| dispatched_at | DATETIME | yes |  |  |
| delivered_at | DATETIME | yes |  |  |
| paid_at | DATETIME | yes |  |  |
| notes | TEXT | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |
| is_deleted | BOOLEAN | yes |  |  |
| deleted_at | DATETIME | yes |  |  |
| deleted_by | INTEGER | yes |  | users.id |

Indexes: ix_invoices_country_code, ix_invoices_id, ix_invoices_is_deleted

### `journal_entries`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| entry_date | DATETIME | no |  |  |
| reference_number | VARCHAR(50) | no |  |  |
| description | TEXT | yes |  |  |
| source | VARCHAR(50) | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |
| currency | VARCHAR(3) | yes |  |  |
| is_reconciled | BOOLEAN | yes |  |  |
| created_by | INTEGER | yes |  | users.id |
| reference_type | VARCHAR(50) | yes |  |  |
| reference_id | INTEGER | yes |  |  |
| period_id | INTEGER | yes |  | fiscal_periods.id |
| reversal_of_id | INTEGER | yes |  | journal_entries.id |
| is_deleted | BOOLEAN | yes |  |  |
| deleted_at | DATETIME | yes |  |  |
| deleted_by | INTEGER | yes |  | users.id |
| created_at | DATETIME | yes |  |  |

Indexes: ix_journal_entries_id, ix_journal_entries_is_deleted, ix_journal_entries_period_id, ix_journal_entries_reversal_of_id, ix_journal_entry_country, ix_journal_entry_date, ix_journal_entry_ref

### `journal_entry_lines`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| entry_id | INTEGER | no |  | journal_entries.id |
| account_id | INTEGER | no |  | accounts.id |
| amount | NUMERIC(12, 2) | no |  |  |
| side | VARCHAR(10) | no |  |  |
| description | TEXT | yes |  |  |
| entity_type | VARCHAR(50) | yes |  |  |
| entity_id | INTEGER | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_jel_account, ix_jel_entry, ix_journal_entry_lines_country_code, ix_journal_entry_lines_id

### `payout_batch_items`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| batch_id | INTEGER | no |  | payout_batches.id |
| entity_type | VARCHAR(20) | no |  |  |
| entity_id | INTEGER | no |  |  |
| amount | NUMERIC(16, 4) | no |  |  |
| currency | VARCHAR(3) | yes |  |  |
| reference | VARCHAR(100) | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_payout_batch_items_country_code, ix_payout_batch_items_id

### `payout_batches`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| batch_number | VARCHAR(50) | no |  |  |
| country_code | VARCHAR(10) | no |  |  |
| total_amount | NUMERIC(16, 4) | yes |  |  |
| item_count | INTEGER | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| created_by | INTEGER | no |  | users.id |
| approved_by | INTEGER | yes |  | users.id |
| dispatched_at | DATETIME | yes |  |  |
| settled_at | DATETIME | yes |  |  |
| notes | TEXT | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_payout_batches_country_code, ix_payout_batches_id

### `payout_rule_categories`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| category_slug | VARCHAR | no |  |  |
| payout_rate | NUMERIC(5, 4) | no |  |  |
| min_amount | NUMERIC(12, 2) | yes |  |  |
| max_amount | NUMERIC(12, 2) | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_payout_rule_categories_id

### `payout_rule_products`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| product_id | INTEGER | no |  | products.id |
| payout_rate | NUMERIC(5, 4) | no |  |  |
| min_amount | NUMERIC(12, 2) | yes |  |  |
| max_amount | NUMERIC(12, 2) | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_payout_rule_products_id

### `payout_rules`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| min_amount | NUMERIC(12, 2) | yes |  |  |
| max_amount | NUMERIC(12, 2) | yes |  |  |
| fixed_fee | NUMERIC(12, 2) | yes |  |  |
| percent_fee | NUMERIC(5, 4) | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_payout_rules_id

### `payouts`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| batch_number | VARCHAR(50) | yes |  |  |
| order_id | INTEGER | yes |  | orders.id |
| supplier_id | INTEGER | no |  | users.id |
| amount | NUMERIC(12, 2) | no |  |  |
| currency | VARCHAR(3) | yes |  |  |
| method | VARCHAR | no |  |  |
| status | VARCHAR | yes |  |  |
| reference_id | VARCHAR | yes |  |  |
| reference | VARCHAR | yes |  |  |
| provider | VARCHAR | yes |  |  |
| provider_recipient_id | VARCHAR | yes |  |  |
| provider_transfer_id | VARCHAR | yes |  |  |
| provider_status | VARCHAR | yes |  |  |
| notes | TEXT | yes |  |  |
| processed_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  | country_configs.code |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_payouts_country_code, ix_payouts_id


## hr (21 tables)

### `employee_addresses`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| employee_id | INTEGER | no |  | employees.id |
| address_type | VARCHAR(30) | no |  |  |
| street | VARCHAR(200) | no |  |  |
| city | VARCHAR(100) | no |  |  |
| state | VARCHAR(100) | yes |  |  |
| postal_code | VARCHAR(20) | yes |  |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| is_primary | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_employee_addresses_employee_id, ix_employee_addresses_id

### `employee_assets`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| employee_id | INTEGER | no |  | employees.id |
| asset_type | VARCHAR(50) | no |  |  |
| asset_id | VARCHAR(100) | no |  |  |
| serial_no | VARCHAR(100) | yes |  |  |
| assigned_at | DATETIME | yes |  |  |
| returned_at | DATETIME | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_employee_assets_country_code, ix_employee_assets_employee_id, ix_employee_assets_id

### `employee_attendance`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| employee_id | INTEGER | no |  | employees.id |
| date | DATE | no |  |  |
| scan_in_time | DATETIME | yes |  |  |
| scan_out_time | DATETIME | yes |  |  |
| scan_type | VARCHAR(20) | yes |  |  |
| location_lat | FLOAT | yes |  |  |
| location_long | FLOAT | yes |  |  |
| device_fingerprint | VARCHAR(255) | yes |  |  |
| is_anomaly | BOOLEAN | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_employee_attendance_country_code, ix_employee_attendance_employee_id, ix_employee_attendance_id

### `employee_biometrics`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| employee_id | INTEGER | no |  | employees.id |
| fingerprint_hash | VARCHAR(255) | yes |  |  |
| face_encoding | TEXT | yes |  |  |
| biometric_type | VARCHAR(20) | yes |  |  |
| enrolled_at | DATETIME | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_employee_biometrics_country_code, ix_employee_biometrics_id

### `employee_certifications`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| employee_id | INTEGER | no |  | employees.id |
| cert_type | VARCHAR(100) | no |  |  |
| cert_name | VARCHAR(200) | no |  |  |
| issued_date | DATE | yes |  |  |
| expiry_date | DATE | yes |  |  |
| is_valid | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_employee_certifications_country_code, ix_employee_certifications_employee_id, ix_employee_certifications_id

### `employee_communication_threads`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | yes |  | country_configs.code |
| entity_type | VARCHAR(50) | no |  |  |
| entity_id | INTEGER | no |  |  |
| participants | TEXT | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| last_message_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_emp_comm_entity, ix_employee_communication_threads_id

### `employee_dependents`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| employee_id | INTEGER | no |  | employees.id |
| name | VARCHAR(160) | no |  |  |
| relation | VARCHAR(50) | no |  |  |
| dob | DATE | yes |  |  |
| is_insured | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_employee_dependents_country_code, ix_employee_dependents_employee_id, ix_employee_dependents_id

### `employee_documents`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| employee_id | INTEGER | no |  | employees.id |
| doc_type | VARCHAR(50) | no |  |  |
| file_url | VARCHAR(500) | no |  |  |
| expiry_date | DATE | yes |  |  |
| verified_by | INTEGER | yes |  | users.id |
| verified_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_employee_documents_country_code, ix_employee_documents_employee_id, ix_employee_documents_id

### `employee_expenses`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| employee_id | INTEGER | no |  | employees.id |
| expense_type | VARCHAR(50) | no |  |  |
| amount | NUMERIC(12, 2) | no |  |  |
| description | TEXT | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| approved_by | INTEGER | yes |  | users.id |
| approved_at | DATETIME | yes |  |  |
| receipt_url | VARCHAR(500) | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_employee_expenses_country_code, ix_employee_expenses_employee_id, ix_employee_expenses_id

### `employee_leave_ledgers`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| employee_id | INTEGER | no |  | employees.id |
| leave_type | VARCHAR(50) | no |  |  |
| year | INTEGER | no |  |  |
| allocated_days | INTEGER | yes |  |  |
| used_days | INTEGER | yes |  |  |
| carried_forward | INTEGER | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_employee_leave_ledgers_country_code, ix_employee_leave_ledgers_employee_id, ix_employee_leave_ledgers_id

### `employee_leave_requests`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| employee_id | INTEGER | no |  | employees.id |
| leave_type | VARCHAR(50) | no |  |  |
| start_date | DATE | no |  |  |
| end_date | DATE | no |  |  |
| days_requested | INTEGER | no |  |  |
| status | VARCHAR(20) | yes |  |  |
| approved_by | INTEGER | yes |  | users.id |
| approved_at | DATETIME | yes |  |  |
| rejection_reason | TEXT | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_employee_leave_requests_country_code, ix_employee_leave_requests_employee_id, ix_employee_leave_requests_id

### `employee_relations`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| employee_id | INTEGER | no |  | employees.id |
| related_person_name | VARCHAR(160) | no |  |  |
| relation_type | VARCHAR(30) | no |  |  |
| is_internal_employee | BOOLEAN | yes |  |  |
| internal_employee_id | INTEGER | yes |  | employees.id |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_employee_relations_country_code, ix_employee_relations_employee_id, ix_employee_relations_id

### `employee_roles`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| role_name | VARCHAR(100) | yes |  |  |
| permissions | JSON | yes |  |  |
| authority_level | INTEGER | yes |  |  |
| can_approve_leave | BOOLEAN | yes |  |  |
| can_approve_expense | BOOLEAN | yes |  |  |
| can_manage_users | BOOLEAN | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_employee_roles_country_code, ix_employee_roles_id

### `employee_shift_rosters`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| employee_id | INTEGER | no |  | employees.id |
| shift_date | DATE | no |  |  |
| start_time | TIME | no |  |  |
| end_time | TIME | no |  |  |
| shift_type | VARCHAR(30) | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_employee_shift_rosters_country_code, ix_employee_shift_rosters_employee_id, ix_employee_shift_rosters_id

### `employee_travel_requests`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| employee_id | INTEGER | no |  | employees.id |
| destination_country | VARCHAR(10) | no |  |  |
| start_date | DATE | no |  |  |
| end_date | DATE | no |  |  |
| purpose | VARCHAR(200) | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| approved_by | INTEGER | yes |  | users.id |
| approved_at | DATETIME | yes |  |  |
| per_diem_json | JSON | yes |  |  |
| total_cost | NUMERIC(12, 2) | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_employee_travel_requests_country_code, ix_employee_travel_requests_id

### `employee_work_logs`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| employee_id | INTEGER | no |  | employees.id |
| date | DATE | no |  |  |
| hours_worked | NUMERIC(5, 2) | yes |  |  |
| task_description | TEXT | yes |  |  |
| location_lat | FLOAT | yes |  |  |
| location_long | FLOAT | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_employee_work_logs_country_code, ix_employee_work_logs_employee_id, ix_employee_work_logs_id

### `employees`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | yes |  | users.id |
| employee_code | VARCHAR(20) | no |  |  |
| office_id | INTEGER | yes |  | offices.id |
| department | VARCHAR(100) | yes |  |  |
| position | VARCHAR(100) | yes |  |  |
| employment_type | VARCHAR(30) | yes |  |  |
| employment_status | VARCHAR(30) | yes |  |  |
| salary | NUMERIC(12, 2) | yes |  |  |
| currency | VARCHAR(3) | yes |  |  |
| country_code | VARCHAR(10) | yes |  | country_configs.code |
| hire_date | DATE | no |  |  |
| termination_date | DATE | yes |  |  |
| is_verified | BOOLEAN | yes |  |  |
| gender | VARCHAR(20) | yes |  |  |
| years_of_experience | INTEGER | yes |  |  |
| performance_score | INTEGER | yes |  |  |
| education_level | VARCHAR(50) | yes |  |  |
| notes | TEXT | yes |  |  |
| reporting_manager_id | INTEGER | yes |  | employees.id |
| hiring_manager_id | INTEGER | yes |  | users.id |
| authority_level | INTEGER | yes |  |  |
| org_unit_id | INTEGER | yes |  | org_units.id |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_employees_id, ix_employees_office, ix_employees_user_id

### `offboarding_cases`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| employee_id | INTEGER | no |  | employees.id |
| employee_name | VARCHAR(200) | yes |  |  |
| reason | VARCHAR(50) | no |  |  |
| status | VARCHAR(20) | yes |  |  |
| initiated_at | DATETIME | yes |  |  |
| completed_at | DATETIME | yes |  |  |
| notes | TEXT | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_offboarding_cases_country_code, ix_offboarding_cases_employee_id, ix_offboarding_cases_id

### `shift_handover_logs`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | no |  | users.id |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| shift_start | DATETIME | no |  |  |
| shift_end | DATETIME | yes |  |  |
| notes | TEXT | yes |  |  |
| handover_to_user_id | INTEGER | yes |  | users.id |
| handover_notes | TEXT | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_handover_user_created, ix_shift_handover_logs_country_code, ix_shift_handover_logs_id, ix_shift_handover_logs_user_id

### `shift_handover_sessions`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | yes |  | country_configs.code |
| outgoing_employee_id | INTEGER | no |  | employees.id |
| incoming_employee_id | INTEGER | yes |  | employees.id |
| shift_date | DATETIME | no |  |  |
| notes | TEXT | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| acknowledged_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_handover_incoming, ix_handover_outgoing, ix_handover_status, ix_shift_handover_sessions_id

### `shift_handover_tasks`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| session_id | INTEGER | no |  | shift_handover_sessions.id |
| description | TEXT | no |  |  |
| priority | VARCHAR(20) | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| assigned_to | INTEGER | yes |  | users.id |
| created_at | DATETIME | yes |  |  |

Indexes: ix_shift_handover_tasks_id


## logistics (22 tables)

### `logistics_category_pricing_rules`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| partner_id | INTEGER | no |  | logistics_partners.id |
| service_area_id | INTEGER | yes |  | logistics_partner_service_areas.id |
| category_name | VARCHAR | no |  |  |
| flat_fee_override | NUMERIC(10, 2) | yes |  |  |
| special_handling_fee | NUMERIC(10, 2) | yes |  |  |
| currency | VARCHAR(3) | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| approval_status | VARCHAR | yes |  |  |
| review_note | VARCHAR | yes |  |  |
| reviewed_by | INTEGER | yes |  | users.id |
| reviewed_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_logistics_category_pricing_rules_country_code, ix_logistics_category_pricing_rules_id

### `logistics_cod_remittance_receipts`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| partner_id | INTEGER | yes |  | logistics_partners.id |
| shipment_id | INTEGER | yes |  | shipments.id |
| settlement_id | INTEGER | yes |  | logistics_settlements.id |
| amount | NUMERIC(12, 2) | no |  |  |
| bank_reference | VARCHAR | yes |  |  |
| receipt_file_url | VARCHAR | yes |  |  |
| notes | TEXT | yes |  |  |
| review_note | TEXT | yes |  |  |
| reviewed_by | INTEGER | yes |  | users.id |
| status | VARCHAR | yes |  |  |
| currency | VARCHAR(3) | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_logistics_cod_remittance_receipts_country_code, ix_logistics_cod_remittance_receipts_id

### `logistics_fraud_indicators`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| partner_id | INTEGER | no |  | logistics_partners.id |
| indicator_type | VARCHAR(50) | no |  |  |
| value | VARCHAR | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_logistics_fraud_indicators_country_code, ix_logistics_fraud_indicators_id

### `logistics_partner_bank_accounts`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| partner_id | INTEGER | no |  | logistics_partners.id |
| account_number | VARCHAR | yes |  |  |
| bank_name | VARCHAR | no |  |  |
| beneficiary_name | VARCHAR | yes |  |  |
| branch_name | VARCHAR | yes |  |  |
| iban | VARCHAR | yes |  |  |
| swift_code | VARCHAR | yes |  |  |
| routing_number | VARCHAR | yes |  |  |
| currency | VARCHAR(3) | yes |  |  |
| bank_country | VARCHAR(3) | yes |  |  |
| verification_status | VARCHAR | yes |  |  |
| verification_note | TEXT | yes |  |  |
| provider | VARCHAR | yes |  |  |
| provider_recipient_id | VARCHAR | yes |  |  |
| provider_status | VARCHAR | yes |  |  |
| provider_last_synced_at | DATETIME | yes |  |  |
| verified_at | DATETIME | yes |  |  |
| verified_by | INTEGER | yes |  | users.id |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_logistics_partner_bank_accounts_country_code, ix_logistics_partner_bank_accounts_id

### `logistics_partner_documents`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| partner_id | INTEGER | no |  | logistics_partners.id |
| doc_type | VARCHAR | no |  |  |
| file_url | VARCHAR | no |  |  |
| reviewed_by | INTEGER | yes |  | users.id |
| is_verified | BOOLEAN | yes |  |  |
| verified_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_logistics_partner_documents_country_code, ix_logistics_partner_documents_id

### `logistics_partner_kyc_requirements`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| min_experience_months | INTEGER | yes |  |  |
| required_documents | TEXT | yes |  |  |
| insurance_required | BOOLEAN | yes |  |  |
| insurance_min_coverage | NUMERIC(15, 2) | yes |  |  |
| vehicle_requirements | TEXT | yes |  |  |
| background_check_required | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_logistics_partner_kyc_requirements_id

### `logistics_partner_locations`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| partner_id | INTEGER | no |  | logistics_partners.id |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| location_type | VARCHAR(30) | yes |  |  |
| latitude | FLOAT | yes |  |  |
| longitude | FLOAT | yes |  |  |
| address | TEXT | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_logistics_partner_locations_country_code, ix_logistics_partner_locations_id, ix_logistics_partner_locations_partner_id, ix_lpl_partner

### `logistics_partner_payouts`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| partner_id | INTEGER | no |  | logistics_partners.id |
| amount | NUMERIC(12, 2) | no |  |  |
| currency | VARCHAR(3) | yes |  |  |
| period_start | DATETIME | yes |  |  |
| period_end | DATETIME | yes |  |  |
| status | VARCHAR | yes |  |  |
| reference_id | VARCHAR | yes |  |  |
| processed_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  | country_configs.code |
| created_at | DATETIME | yes |  |  |
| method | VARCHAR | yes |  |  |
| notes | TEXT | yes |  |  |

Indexes: ix_logistics_partner_payouts_country_code, ix_logistics_partner_payouts_id

### `logistics_partner_profiles`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| partner_id | INTEGER | no |  | logistics_partners.id |
| tax_id | VARCHAR | yes |  |  |
| registration_number | VARCHAR | yes |  |  |
| business_type | VARCHAR | yes |  |  |
| years_in_business | INTEGER | yes |  |  |
| insurance_provider | VARCHAR | yes |  |  |
| insurance_policy_number | VARCHAR | yes |  |  |
| insurance_expiry | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  | country_configs.code |

Indexes: ix_logistics_partner_profiles_country_code, ix_logistics_partner_profiles_id

### `logistics_partner_service_areas`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| partner_id | INTEGER | no |  | logistics_partners.id |
| country_code | VARCHAR(10) | no |  |  |
| country_name | VARCHAR | no |  |  |
| origin_city | VARCHAR | no |  |  |
| city_name | VARCHAR | no |  |  |
| zone_label | VARCHAR | yes |  |  |
| charge_amount | NUMERIC(10, 2) | yes |  |  |
| minimum_charge | NUMERIC(10, 2) | yes |  |  |
| per_kg_rate | NUMERIC(10, 2) | yes |  |  |
| pickup_charge | NUMERIC(10, 2) | yes |  |  |
| dropoff_charge | NUMERIC(10, 2) | yes |  |  |
| per_km_rate | NUMERIC(10, 2) | yes |  |  |
| currency | VARCHAR(3) | yes |  |  |
| delivery_days_min | INTEGER | yes |  |  |
| delivery_days_max | INTEGER | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| approval_status | VARCHAR | yes |  |  |
| review_note | VARCHAR | yes |  |  |
| reviewed_by | INTEGER | yes |  |  |
| reviewed_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_logistics_partner_service_areas_id

### `logistics_partners`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | yes |  | users.id |
| name | VARCHAR | no |  |  |
| code | VARCHAR | no |  |  |
| contact_name | VARCHAR | yes |  |  |
| contact_email | VARCHAR | yes |  |  |
| contact_phone | VARCHAR | yes |  |  |
| website | VARCHAR | yes |  |  |
| coverage_regions | JSON | yes |  |  |
| service_types | JSON | yes |  |  |
| status | VARCHAR | yes |  |  |
| verification_status | VARCHAR | yes |  |  |
| verification_note | VARCHAR | yes |  |  |
| verified_by | INTEGER | yes |  |  |
| verified_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  | country_configs.code |
| created_at | DATETIME | yes |  |  |
| business_type | VARCHAR | yes |  |  |
| region | VARCHAR | yes |  |  |
| city | VARCHAR | yes |  |  |
| address | TEXT | yes |  |  |
| postal_code | VARCHAR | yes |  |  |
| tax_id | VARCHAR | yes |  |  |
| bio | TEXT | yes |  |  |
| about_us | TEXT | yes |  |  |
| logo_url | VARCHAR | yes |  |  |
| banner_url | VARCHAR | yes |  |  |
| latitude | NUMERIC(10, 7) | yes |  |  |
| longitude | NUMERIC(10, 7) | yes |  |  |
| social_links | JSON | yes |  |  |
| notes | TEXT | yes |  |  |
| is_terms_accepted | BOOLEAN | yes |  |  |
| terms_version | VARCHAR | yes |  |  |
| terms_accepted_at | DATETIME | yes |  |  |

Indexes: ix_logistics_partners_country_code, ix_logistics_partners_id

### `logistics_pricing_profiles`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| partner_id | INTEGER | no |  | logistics_partners.id |
| service_area_id | INTEGER | no |  | logistics_partner_service_areas.id |
| profile_name | VARCHAR | no |  |  |
| base_in_city_fee | NUMERIC(10, 2) | yes |  |  |
| per_kg_rate | NUMERIC(10, 2) | yes |  |  |
| minimum_charge | NUMERIC(10, 2) | yes |  |  |
| maximum_charge | NUMERIC(10, 2) | yes |  |  |
| fuel_multiplier | NUMERIC(5, 4) | yes |  |  |
| base_inter_city_fee | NUMERIC(10, 2) | yes |  |  |
| per_km_rate | NUMERIC(10, 2) | yes |  |  |
| bulk_discount_threshold_kg | NUMERIC(10, 2) | yes |  |  |
| bulk_discount_percent | NUMERIC(5, 4) | yes |  |  |
| currency | VARCHAR(3) | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| approval_status | VARCHAR | yes |  |  |
| review_note | VARCHAR | yes |  |  |
| reviewed_by | INTEGER | yes |  | users.id |
| reviewed_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_logistics_pricing_profiles_country_code, ix_logistics_pricing_profiles_id

### `logistics_settlements`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| partner_id | INTEGER | no |  | logistics_partners.id |
| order_id | INTEGER | yes |  | orders.id |
| ledger_id | INTEGER | yes |  |  |
| shipment_id | INTEGER | yes |  | shipments.id |
| amount | NUMERIC(12, 2) | yes |  |  |
| pickup_charge | NUMERIC(12, 2) | yes |  |  |
| dropoff_charge | NUMERIC(12, 2) | yes |  |  |
| total_delivery_fee | NUMERIC(12, 2) | yes |  |  |
| cod_collected | NUMERIC(12, 2) | yes |  |  |
| cod_remitted | NUMERIC(12, 2) | yes |  |  |
| cod_retained | NUMERIC(12, 2) | yes |  |  |
| cod_remittance_status | VARCHAR | yes |  |  |
| eligible_at | DATETIME | yes |  |  |
| status | VARCHAR | yes |  |  |
| currency | VARCHAR(3) | yes |  |  |
| payout_id | INTEGER | yes |  | payouts.id |
| bank_transaction_id | INTEGER | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_logistics_settlements_country_code, ix_logistics_settlements_id

### `logistics_vehicle_rules`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| partner_id | INTEGER | no |  | logistics_partners.id |
| service_area_id | INTEGER | no |  | logistics_partner_service_areas.id |
| vehicle_type | VARCHAR | no |  |  |
| max_weight_kg | NUMERIC(10, 2) | yes |  |  |
| cost_multiplier | NUMERIC(5, 4) | yes |  |  |
| priority_rank | INTEGER | yes |  |  |
| route_scope | VARCHAR | yes |  |  |
| max_volume_cm3 | NUMERIC(12, 2) | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| approval_status | VARCHAR | yes |  |  |
| review_note | VARCHAR | yes |  |  |
| reviewed_by | INTEGER | yes |  | users.id |
| reviewed_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_logistics_vehicle_rules_country_code, ix_logistics_vehicle_rules_id

### `parcel_location_trackers`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| parcel_id | INTEGER | no |  | shipments.id |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| latitude | FLOAT | yes |  |  |
| longitude | FLOAT | yes |  |  |
| location_name | VARCHAR(200) | yes |  |  |
| timestamp | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_parcel_location_trackers_country_code, ix_parcel_location_trackers_id, ix_parcel_location_trackers_parcel_id, ixplt_created, ixplt_parcel

### `shipment_confirmations`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| shipment_id | INTEGER | no |  | shipments.id |
| order_id | INTEGER | yes |  | orders.id |
| supplier_id | INTEGER | yes |  | users.id |
| requester_user_id | INTEGER | yes |  | users.id |
| requester_role | VARCHAR | yes |  |  |
| target_user_id | INTEGER | yes |  | users.id |
| target_role | VARCHAR | yes |  |  |
| confirmation_type | VARCHAR | yes |  |  |
| status | VARCHAR | yes |  |  |
| requested_status | VARCHAR | yes |  |  |
| requested_event_type | VARCHAR | yes |  |  |
| current_hub | VARCHAR | yes |  |  |
| notes | TEXT | yes |  |  |
| confirmation_code | VARCHAR | yes |  |  |
| confirmed_at | DATETIME | yes |  |  |
| responded_at | DATETIME | yes |  |  |
| tracking_number | VARCHAR | yes |  |  |
| delivery_signature_name | VARCHAR | yes |  |  |
| delivery_signature_data_url | VARCHAR | yes |  |  |
| delivery_signature_captured_at | DATETIME | yes |  |  |
| response_notes | TEXT | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_shipment_confirmations_country_code, ix_shipment_confirmations_id

### `shipment_events`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| shipment_id | INTEGER | no |  | shipments.id |
| order_id | INTEGER | no |  | orders.id |
| supplier_id | INTEGER | no |  | users.id |
| actor_user_id | INTEGER | yes |  | users.id |
| actor_role | VARCHAR | yes |  |  |
| event_type | VARCHAR | no |  |  |
| status_after | VARCHAR | yes |  |  |
| distribution_channel | VARCHAR | yes |  |  |
| location | VARCHAR | yes |  |  |
| latitude | NUMERIC(10, 8) | yes |  |  |
| longitude | NUMERIC(11, 8) | yes |  |  |
| scan_code | VARCHAR | yes |  |  |
| notes | VARCHAR | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_shipment_events_country_code, ix_shipment_events_id, ix_shipment_events_order_id, ix_shipment_events_shipment_id

### `shipments`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| order_id | INTEGER | no |  | orders.id |
| supplier_id | INTEGER | no |  | users.id |
| assigned_partner_id | INTEGER | yes |  | logistics_partners.id |
| carrier_id | INTEGER | yes |  | shipping_carriers.id |
| tracking_number | VARCHAR | yes |  |  |
| carrier_name | VARCHAR | yes |  |  |
| status | VARCHAR | yes |  |  |
| distribution_channel | VARCHAR | yes |  |  |
| current_hub | VARCHAR | yes |  |  |
| scan_code | VARCHAR | yes |  |  |
| package_count | INTEGER | yes |  |  |
| package_weight_kg | NUMERIC(5, 2) | yes |  |  |
| package_dimensions | VARCHAR | yes |  |  |
| packaged_at | DATETIME | yes |  |  |
| packaged_by_user_id | INTEGER | yes |  |  |
| packaged_notes | VARCHAR | yes |  |  |
| packaging_notes | VARCHAR | yes |  |  |
| shipped_at | DATETIME | yes |  |  |
| estimated_delivery | DATETIME | yes |  |  |
| actual_delivery | DATETIME | yes |  |  |
| delivery_signature_name | VARCHAR | yes |  |  |
| delivery_signature_data_url | VARCHAR | yes |  |  |
| delivery_signature_captured_at | DATETIME | yes |  |  |
| notes | TEXT | yes |  |  |
| accepted_vehicle_type | VARCHAR | yes |  |  |
| accepted_vehicle_multiplier | NUMERIC(5, 4) | yes |  |  |
| accepted_vehicle_selected_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_shipments_country_code, ix_shipments_id, ix_shipments_order_id

### `shipping_carriers`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| supplier_id | INTEGER | yes |  | users.id |
| name | VARCHAR | no |  |  |
| code | VARCHAR | no |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_shipping_carriers_country_code, ix_shipping_carriers_id

### `shipping_rules`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| method | VARCHAR | no |  |  |
| base_rate | NUMERIC(10, 2) | no |  |  |
| per_kg_rate | NUMERIC(10, 2) | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_shipping_rules_id

### `shipping_zones`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| supplier_id | INTEGER | yes |  | users.id |
| name | VARCHAR | no |  |  |
| countries | JSON | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_shipping_zones_country_code, ix_shipping_zones_id

### `shop_warehouse_locations`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| name | VARCHAR(100) | no |  |  |
| warehouse_code | VARCHAR(30) | no |  |  |
| latitude | FLOAT | yes |  |  |
| longitude | FLOAT | yes |  |  |
| address | TEXT | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_shop_warehouse_locations_country_code, ix_shop_warehouse_locations_id, ix_swl_active


## media (10 tables)

### `ai_generation_logs`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| job_id | INTEGER | no |  | ai_upload_jobs.id |
| field | VARCHAR(40) | no |  |  |
| model_used | VARCHAR(100) | yes |  |  |
| prompt_hash | VARCHAR(64) | yes |  |  |
| tokens_used | NUMERIC(12, 2) | yes |  |  |
| cost | NUMERIC(12, 6) | yes |  |  |
| confidence | NUMERIC(5, 4) | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_ai_generation_logs_country_code, ix_ai_generation_logs_id, ix_ai_generation_logs_job_id, ix_ai_generation_logs_prompt_hash

### `ai_staging_products`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| job_id | INTEGER | no |  | ai_upload_jobs.id |
| product_id | INTEGER | yes |  | products.id |
| name | VARCHAR | no |  |  |
| description | TEXT | yes |  |  |
| price | NUMERIC(10, 2) | yes |  |  |
| stock | INTEGER | yes |  |  |
| category | VARCHAR | yes |  |  |
| subcategory | VARCHAR | yes |  |  |
| color | VARCHAR | yes |  |  |
| brand | VARCHAR | yes |  |  |
| tags | JSON | yes |  |  |
| sizes | JSON | yes |  |  |
| materials | JSON | yes |  |  |
| image_url | VARCHAR | yes |  |  |
| additional_media | JSON | yes |  |  |
| ai_description | TEXT | yes |  |  |
| variant_axes | JSON | yes |  |  |
| attributes | JSON | yes |  |  |
| confidence_score | NUMERIC(5, 4) | yes |  |  |
| requires_human_review | BOOLEAN | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_ai_staging_products_country_code, ix_ai_staging_products_id, ix_ai_staging_products_job_id

### `ai_staging_variants`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| job_id | INTEGER | no |  | ai_upload_jobs.id |
| staging_product_id | INTEGER | no |  | ai_staging_products.id |
| variant_key | VARCHAR(64) | yes |  |  |
| size | VARCHAR | yes |  |  |
| color | VARCHAR | yes |  |  |
| material | VARCHAR | yes |  |  |
| pattern | VARCHAR | yes |  |  |
| gender | VARCHAR | yes |  |  |
| sku | VARCHAR | yes |  |  |
| barcode | VARCHAR | yes |  |  |
| product_code | VARCHAR | yes |  |  |
| price | NUMERIC(10, 2) | yes |  |  |
| stock | INTEGER | yes |  |  |
| media_url | VARCHAR | yes |  |  |
| attributes_json | TEXT | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| confidence_score | NUMERIC(5, 4) | yes |  |  |
| requires_human_review | BOOLEAN | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_ai_staging_variants_country_code, ix_ai_staging_variants_id, ix_ai_staging_variants_job_id, ix_ai_staging_variants_job_staging, ix_ai_staging_variants_staging_product_id, ix_ai_staging_variants_variant_key

### `ai_upload_jobs`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| supplier_id | INTEGER | no |  | users.id |
| status | VARCHAR(20) | no |  |  |
| model_used | VARCHAR(100) | yes |  |  |
| prompt_hash | VARCHAR(64) | yes |  |  |
| tokens_used | NUMERIC(12, 2) | yes |  |  |
| source_media_json | TEXT | yes |  |  |
| created_product_id | INTEGER | yes |  | products.id |
| error_log | TEXT | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_ai_upload_jobs_country_code, ix_ai_upload_jobs_id, ix_ai_upload_jobs_prompt_hash, ix_ai_upload_jobs_status, ix_ai_upload_jobs_supplier_id

### `media_assets`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  |  |
| supplier_id | INTEGER | yes |  | users.id |
| product_id | INTEGER | yes |  | products.id |
| entity_type | VARCHAR(20) | no |  |  |
| entity_id | INTEGER | yes |  |  |
| variant | VARCHAR(20) | no |  |  |
| file_path | VARCHAR(500) | no |  |  |
| file_url | VARCHAR(500) | no |  |  |
| file_size_bytes | INTEGER | no |  |  |
| mime_type | VARCHAR(100) | no |  |  |
| width | INTEGER | yes |  |  |
| height | INTEGER | yes |  |  |
| is_primary | BOOLEAN | yes |  |  |
| alt_text | VARCHAR(255) | yes |  |  |
| caption | TEXT | yes |  |  |
| uploaded_by | INTEGER | yes |  | users.id |
| uploaded_at | DATETIME | yes |  |  |
| is_deleted | BOOLEAN | yes |  |  |
| deleted_at | DATETIME | yes |  |  |

Indexes: ix_media_assets_country_code, ix_media_assets_entity, ix_media_assets_entity_id, ix_media_assets_id, ix_media_assets_product_id, ix_media_assets_supplier_id, ix_media_assets_variant

### `media_upload_sessions`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| session_id | VARCHAR(64) | no |  |  |
| country_code | VARCHAR(10) | no |  |  |
| entity_type | VARCHAR(20) | no |  |  |
| entity_id | INTEGER | yes |  |  |
| filename | VARCHAR(255) | no |  |  |
| file_size | INTEGER | no |  |  |
| mime_type | VARCHAR(100) | no |  |  |
| chunk_size | INTEGER | yes |  |  |
| total_chunks | INTEGER | no |  |  |
| uploaded_chunks | INTEGER | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| error_message | TEXT | yes |  |  |
| created_by | INTEGER | yes |  | users.id |
| created_at | DATETIME | yes |  |  |
| completed_at | DATETIME | yes |  |  |

Indexes: ix_media_upload_sessions_id, ix_media_upload_sessions_session_id

### `video_analytics`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| video_id | INTEGER | no |  | product_videos.id |
| user_id | INTEGER | yes |  | users.id |
| event_type | VARCHAR(50) | no |  |  |
| watch_duration_seconds | INTEGER | yes |  |  |
| device_type | VARCHAR(50) | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_video_analytics_country_code, ix_video_analytics_id, ix_video_analytics_user_id, ix_video_analytics_video_id

### `video_room_participants`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| room_id | INTEGER | no |  | video_rooms.id |
| user_id | INTEGER | no |  | users.id |
| role | VARCHAR(20) | yes |  |  |
| joined_at | DATETIME | yes |  |  |
| left_at | DATETIME | yes |  |  |

Indexes: ix_video_room_participants_id

### `video_room_recordings`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| room_id | INTEGER | no |  | video_rooms.id |
| started_by | INTEGER | no |  | users.id |
| recording_url | VARCHAR(500) | yes |  |  |
| duration_seconds | INTEGER | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| started_at | DATETIME | yes |  |  |
| ended_at | DATETIME | yes |  |  |

Indexes: ix_video_room_recordings_id

### `video_rooms`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| room_id | VARCHAR(64) | no |  |  |
| room_uuid | VARCHAR(32) | yes |  |  |
| name | VARCHAR(200) | no |  |  |
| country_code | VARCHAR(10) | yes |  | country_configs.code |
| created_by | INTEGER | yes |  | users.id |
| is_boardroom | BOOLEAN | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| max_participants | INTEGER | yes |  |  |
| recording_enabled | BOOLEAN | yes |  |  |
| watermark_enabled | BOOLEAN | yes |  |  |
| transcription_enabled | BOOLEAN | yes |  |  |
| started_at | DATETIME | yes |  |  |
| ended_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_video_room_created, ix_video_room_status, ix_video_rooms_id, ix_video_rooms_room_id


## other (100 tables)

### `admin_analytics_snapshots`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| snapshot_key | VARCHAR(120) | no |  |  |
| snapshot_group | VARCHAR(80) | no |  |  |
| period | VARCHAR(40) | yes |  |  |
| payload_json | TEXT | no |  |  |
| computed_at | DATETIME | no |  |  |
| expires_at | DATETIME | no |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_admin_analytics_snapshots_computed_at, ix_admin_analytics_snapshots_country_code, ix_admin_analytics_snapshots_expires, ix_admin_analytics_snapshots_expires_at, ix_admin_analytics_snapshots_group_computed, ix_admin_analytics_snapshots_id, ix_admin_analytics_snapshots_snapshot_group, ix_admin_analytics_snapshots_snapshot_key

### `alert_escalation_rules`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| alert_type | VARCHAR(50) | no |  |  |
| severity | VARCHAR(20) | yes |  |  |
| threshold_value | NUMERIC(15, 2) | yes |  |  |
| current_tier | INTEGER | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_alert_escalation_rules_id

### `alumni_network`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| employee_id | INTEGER | no |  | employees.id |
| status | VARCHAR(20) | yes |  |  |
| granted_at | DATETIME | yes |  |  |
| eligibility_expires_at | DATETIME | yes |  |  |
| notes | TEXT | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_alumni_network_country_code, ix_alumni_network_id

### `announcements`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| title | VARCHAR | no |  |  |
| content | TEXT | no |  |  |
| is_active | BOOLEAN | yes |  |  |
| starts_at | DATETIME | yes |  |  |
| ends_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_announcements_id

### `api_keys`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| name | VARCHAR | no |  |  |
| key_hash | VARCHAR | no |  |  |
| permissions | JSON | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| expires_at | DATETIME | yes |  |  |
| created_by | INTEGER | yes |  | users.id |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_api_keys_country_code, ix_api_keys_id

### `badge_billing_records`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | yes |  | users.id |
| supplier_id | INTEGER | yes |  | users.id |
| billing_reference | VARCHAR | yes |  |  |
| badge_level | VARCHAR(50) | yes |  |  |
| charge_type | VARCHAR | yes |  |  |
| charge_source | VARCHAR | yes |  |  |
| amount | NUMERIC(12, 2) | no |  |  |
| currency | VARCHAR(3) | yes |  |  |
| status | VARCHAR | yes |  |  |
| reference_id | VARCHAR | yes |  |  |
| period_start | DATETIME | yes |  |  |
| period_end | DATETIME | yes |  |  |
| due_at | DATETIME | yes |  |  |
| billed_at | DATETIME | yes |  |  |
| paid_at | DATETIME | yes |  |  |
| payment_method | VARCHAR | yes |  |  |
| notes | TEXT | yes |  |  |
| created_by | INTEGER | yes |  |  |
| bank_transaction_id | INTEGER | yes |  | bank_transactions.id |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_badge_billing_records_country_code, ix_badge_billing_records_id

### `badge_tiers`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| name | VARCHAR | no |  |  |
| min_points | INTEGER | no |  |  |
| benefits | JSON | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_badge_tiers_country_code, ix_badge_tiers_id

### `badge_transactions`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | no |  | users.id |
| amount | NUMERIC(12, 2) | no |  |  |
| transaction_type | VARCHAR | no |  |  |
| reference_id | VARCHAR | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_badge_transactions_country_code, ix_badge_transactions_id

### `bank_transactions`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| transaction_ref | VARCHAR | yes |  |  |
| source | VARCHAR | yes |  |  |
| transaction_type | VARCHAR | no |  |  |
| category | VARCHAR | yes |  |  |
| amount | NUMERIC(12, 2) | no |  |  |
| currency | VARCHAR(3) | yes |  |  |
| description | TEXT | yes |  |  |
| linked_order_id | INTEGER | yes |  | orders.id |
| linked_supplier_id | INTEGER | yes |  | users.id |
| linked_logistics_id | INTEGER | yes |  |  |
| linked_payout_id | INTEGER | yes |  |  |
| linked_refund_id | INTEGER | yes |  |  |
| reconciled | BOOLEAN | yes |  |  |
| reconciled_by | INTEGER | yes |  | users.id |
| reconciled_at | DATETIME | yes |  |  |
| transaction_date | DATETIME | yes |  |  |
| status | VARCHAR | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |
| flagged | BOOLEAN | yes |  |  |
| flag_reason | TEXT | yes |  |  |

Indexes: ix_bank_transactions_country_code, ix_bank_transactions_id, ix_bank_transactions_transaction_ref

### `campaign_recipients`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| campaign_id | INTEGER | no |  | email_campaigns.id |
| user_id | INTEGER | no |  | users.id |
| email | VARCHAR | no |  |  |
| status | VARCHAR | yes |  |  |
| sent_at | DATETIME | yes |  |  |
| delivered_at | DATETIME | yes |  |  |
| opened_at | DATETIME | yes |  |  |
| clicked_at | DATETIME | yes |  |  |
| bounced_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_campaign_recipients_id

### `cash_accounts`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| name | VARCHAR | no |  |  |
| account_type | VARCHAR | no |  |  |
| currency | VARCHAR(3) | yes |  |  |
| balance | NUMERIC(12, 2) | yes |  |  |
| description | TEXT | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_by | INTEGER | yes |  | users.id |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_cash_accounts_country_code, ix_cash_accounts_id

### `cash_flow_forecasts`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| forecast_date | DATETIME | no |  |  |
| period_start | DATETIME | no |  |  |
| period_end | DATETIME | no |  |  |
| net_cash_flow | NUMERIC(12, 2) | yes |  |  |
| opening_balance | NUMERIC(12, 2) | yes |  |  |
| closing_balance | NUMERIC(12, 2) | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_cash_flow_forecasts_country_code, ix_cash_flow_forecasts_id

### `cash_position_snapshots`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| snapshot_time | DATETIME | no |  |  |
| account_id | INTEGER | no |  | treasury_accounts.id |
| balance | NUMERIC(12, 2) | yes |  |  |
| currency | VARCHAR(3) | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_cash_position_snapshots_country_code, ix_cash_position_snapshots_id

### `cash_transactions`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| account_id | INTEGER | no |  | cash_accounts.id |
| transaction_type | VARCHAR | no |  |  |
| amount | NUMERIC(12, 2) | no |  |  |
| balance_after | NUMERIC(12, 2) | yes |  |  |
| description | TEXT | yes |  |  |
| reference | VARCHAR | yes |  |  |
| category | VARCHAR | yes |  |  |
| performed_by | INTEGER | yes |  | users.id |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_cash_transactions_country_code, ix_cash_transactions_id

### `city_distance_matrix`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| origin_country_code | VARCHAR(10) | no |  |  |
| origin_city_name | VARCHAR | no |  |  |
| destination_country_code | VARCHAR(10) | no |  |  |
| destination_city_name | VARCHAR | no |  |  |
| distance_km | NUMERIC(10, 2) | yes |  |  |
| notes | TEXT | yes |  |  |
| created_by | INTEGER | yes |  | users.id |
| updated_by | INTEGER | yes |  | users.id |
| created_at | DATETIME | yes |  |  |

Indexes: ix_city_distance_matrix_id

### `coi_reports`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| employee_id | INTEGER | no |  | employees.id |
| related_person_name | VARCHAR(160) | no |  |  |
| relation_type | VARCHAR(30) | no |  |  |
| is_internal | BOOLEAN | yes |  |  |
| internal_employee_id | INTEGER | yes |  | employees.id |
| risk_level | VARCHAR(20) | yes |  |  |
| is_approved | BOOLEAN | yes |  |  |
| approved_by | INTEGER | yes |  | users.id |
| approved_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_coi_reports_country_code, ix_coi_reports_id

### `credit_card_bins`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| bin | VARCHAR(10) | no |  |  |
| brand | VARCHAR(50) | yes |  |  |
| bank | VARCHAR(100) | yes |  |  |
| country | VARCHAR(10) | yes |  |  |
| is_blacklisted | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_credit_card_bins_id

### `cross_country_customer_sessions`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | no |  | users.id |
| source_country_code | VARCHAR(10) | no |  |  |
| target_country_code | VARCHAR(10) | no |  |  |
| session_data | TEXT | yes |  |  |
| conversion | BOOLEAN | yes |  |  |
| order_id | INTEGER | yes |  | orders.id |
| ip_address | VARCHAR(45) | yes |  |  |
| user_agent | VARCHAR(500) | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_cross_country_customer_sessions_id, ix_cross_country_user

### `data_residency_records`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| data_type | VARCHAR(50) | no |  |  |
| storage_location | VARCHAR(100) | yes |  |  |
| cross_border_allowed | BOOLEAN | yes |  |  |
| compliance_status | VARCHAR(30) | yes |  |  |
| last_audit_at | DATETIME | yes |  |  |
| next_audit_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_data_residency_records_country_code, ix_data_residency_records_id, ix_drr_compliance

### `device_fingerprints`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | yes |  | users.id |
| fingerprint_hash | VARCHAR | no |  |  |
| user_agent | VARCHAR | yes |  |  |
| ip_addresses | TEXT | yes |  |  |
| is_trusted | BOOLEAN | yes |  |  |
| is_blocked | BOOLEAN | yes |  |  |
| risk_score | INTEGER | yes |  |  |
| headless_attempts | INTEGER | yes |  |  |
| account_count | INTEGER | yes |  |  |
| first_seen_at | DATETIME | yes |  |  |
| last_seen_at | DATETIME | yes |  |  |

Indexes: ix_device_fingerprint, ix_device_fingerprints_fingerprint_hash, ix_device_fingerprints_id

### `direct_chat_messages`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| room_id | INTEGER | no |  | direct_chat_rooms.id |
| sender_id | INTEGER | no |  | users.id |
| message | TEXT | no |  |  |
| message_type | VARCHAR(20) | yes |  |  |
| read_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_direct_chat_messages_id

### `direct_chat_rooms`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| chat_id | VARCHAR(64) | no |  |  |
| participant_one | INTEGER | no |  | users.id |
| participant_two | INTEGER | no |  | users.id |
| country_code | VARCHAR(10) | yes |  | country_configs.code |
| is_masked | BOOLEAN | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_direct_chat_rooms_chat_id, ix_direct_chat_rooms_id

### `disciplinary_cases`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| employee_id | INTEGER | no |  | employees.id |
| employee_name | VARCHAR(200) | yes |  |  |
| stage | VARCHAR(30) | no |  |  |
| description | TEXT | no |  |  |
| issued_at | DATETIME | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_disciplinary_cases_country_code, ix_disciplinary_cases_employee_id, ix_disciplinary_cases_id

### `dlp_violations`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| violation_type | VARCHAR(50) | no |  |  |
| severity | VARCHAR(20) | yes |  |  |
| sender_id | INTEGER | yes |  | users.id |
| recipient_email | VARCHAR(255) | yes |  |  |
| detected_content | TEXT | yes |  |  |
| action_taken | VARCHAR(50) | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| reviewed_by | INTEGER | yes |  | users.id |
| reviewed_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_dlp_created_at, ix_dlp_status, ix_dlp_violations_id

### `document_verifications`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| pipeline_id | INTEGER | no |  | onboarding_pipelines.id |
| document_type | VARCHAR | no |  |  |
| document_data | JSON | yes |  |  |
| status | VARCHAR | yes |  |  |
| verified_at | DATETIME | yes |  |  |
| verifier_id | INTEGER | yes |  | users.id |

Indexes: ix_document_verifications_id

### `dynamic_qr_sessions`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| employee_id | INTEGER | no |  | employees.id |
| qr_token | VARCHAR(255) | no |  |  |
| expires_at | DATETIME | no |  |  |
| used_at | DATETIME | yes |  |  |
| ip_address | VARCHAR(45) | yes |  |  |
| user_agent | VARCHAR(500) | yes |  |  |
| device_fingerprint | VARCHAR(255) | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_dynamic_qr_sessions_country_code, ix_dynamic_qr_sessions_id, ix_dynamic_qr_sessions_qr_token, ix_qr_session_employee_expires

### `executive_news`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| title | VARCHAR(200) | no |  |  |
| summary | TEXT | yes |  |  |
| content | TEXT | yes |  |  |
| url | VARCHAR(500) | yes |  |  |
| category | VARCHAR(50) | yes |  |  |
| priority | VARCHAR(20) | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |
| is_published | BOOLEAN | yes |  |  |
| ai_sentiment | VARCHAR(20) | yes |  |  |
| published_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_executive_news_id

### `external_contact_masking`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | no |  | users.id |
| external_contact_type | VARCHAR(50) | no |  |  |
| external_contact_id | INTEGER | no |  |  |
| masked_phone | VARCHAR(20) | yes |  |  |
| masked_email | VARCHAR(255) | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_external_contact_masking_id, ix_masking_user

### `faqs`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| question | TEXT | no |  |  |
| answer | TEXT | no |  |  |
| category | VARCHAR | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| sort_order | INTEGER | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_faqs_country_code, ix_faqs_id

### `finance_bank_accounts`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| account_name | VARCHAR | yes |  |  |
| account_number | VARCHAR | no |  |  |
| bank_name | VARCHAR | no |  |  |
| account_label | VARCHAR | yes |  |  |
| branch_name | VARCHAR | yes |  |  |
| iban | VARCHAR | yes |  |  |
| swift_code | VARCHAR | yes |  |  |
| routing_number | VARCHAR | yes |  |  |
| currency | VARCHAR(3) | yes |  |  |
| support_email | VARCHAR | yes |  |  |
| support_phone | VARCHAR | yes |  |  |
| remittance_reference_prefix | VARCHAR | yes |  |  |
| instructions | TEXT | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| scope | VARCHAR | yes |  |  |
| created_by | INTEGER | yes |  | users.id |
| updated_by | INTEGER | yes |  | users.id |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_finance_bank_accounts_country_code, ix_finance_bank_accounts_id

### `financial_reports`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| report_type | VARCHAR | no |  |  |
| period_start | DATETIME | no |  |  |
| period_end | DATETIME | no |  |  |
| country_code | VARCHAR(10) | yes |  |  |
| data | JSON | yes |  |  |
| generated_at | DATETIME | yes |  |  |
| is_deleted | BOOLEAN | yes |  |  |
| deleted_at | DATETIME | yes |  |  |

Indexes: ix_financial_reports_country_code, ix_financial_reports_id, ix_financial_reports_is_deleted

### `fiscal_periods`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  |  |
| period_year | INTEGER | no |  |  |
| period_month | INTEGER | no |  |  |
| period_start | DATETIME | no |  |  |
| period_end | DATETIME | no |  |  |
| status | VARCHAR(20) | yes |  |  |
| is_locked | BOOLEAN | yes |  |  |
| closed_at | DATETIME | yes |  |  |
| closed_by | INTEGER | yes |  | users.id |
| notes | TEXT | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_fiscal_period_country, ix_fiscal_periods_country_code, ix_fiscal_periods_id

### `gateway_settlement_schedules`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| gateway_id | INTEGER | no |  | payment_gateway_connections.id |
| settlement_date | DATETIME | no |  |  |
| amount | NUMERIC(12, 2) | no |  |  |
| currency | VARCHAR(3) | yes |  |  |
| status | VARCHAR | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_gateway_settlement_schedules_country_code, ix_gateway_settlement_schedules_id

### `geo_fence_logs`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| employee_id | INTEGER | no |  | employees.id |
| latitude | FLOAT | no |  |  |
| longitude | FLOAT | no |  |  |
| accuracy_meters | INTEGER | yes |  |  |
| scanned_at | DATETIME | yes |  |  |
| is_within_fence | BOOLEAN | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_geo_fence_logs_country_code, ix_geo_fence_logs_id

### `group_chat_members`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| room_id | INTEGER | no |  | group_chat_rooms.id |
| user_id | INTEGER | no |  | users.id |
| role | VARCHAR(20) | yes |  |  |
| joined_at | DATETIME | yes |  |  |

Indexes: ix_group_chat_members_id

### `group_chat_messages`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| room_id | INTEGER | no |  | group_chat_rooms.id |
| sender_id | INTEGER | no |  | users.id |
| message | TEXT | no |  |  |
| message_type | VARCHAR(20) | yes |  |  |
| read_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_group_chat_messages_id

### `group_chat_rooms`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| chat_id | VARCHAR(64) | no |  |  |
| name | VARCHAR(200) | no |  |  |
| country_code | VARCHAR(10) | yes |  | country_configs.code |
| is_encrypted | BOOLEAN | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_by | INTEGER | no |  | users.id |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_group_chat_rooms_chat_id, ix_group_chat_rooms_id

### `help_categories`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| name | VARCHAR | no |  |  |
| description | TEXT | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| sort_order | INTEGER | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_help_categories_id

### `ip_account_linkages`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| ip_address | VARCHAR | no |  |  |
| user_id | INTEGER | no |  | users.id |
| device_fingerprint | VARCHAR | yes |  |  |
| session_id | VARCHAR | yes |  |  |
| interaction_count | INTEGER | yes |  |  |
| is_suspicious | BOOLEAN | yes |  |  |
| last_seen | DATETIME | yes |  |  |

Indexes: ix_ip_account_linkages_id, ix_ip_account_linkages_ip_address

### `ip_reputations`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| ip_address | VARCHAR | no |  |  |
| reputation_score | NUMERIC(5, 2) | yes |  |  |
| is_blocked | BOOLEAN | yes |  |  |
| is_proxy | BOOLEAN | yes |  |  |
| is_tor | BOOLEAN | yes |  |  |
| is_vpn | BOOLEAN | yes |  |  |
| is_hosting | BOOLEAN | yes |  |  |
| asn | VARCHAR | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |
| last_seen_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_ip_reputation_ip, ix_ip_reputations_id, ix_ip_reputations_ip_address

### `kyc_verifications`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | no |  | users.id |
| status | VARCHAR | yes |  |  |
| provider | VARCHAR | yes |  |  |
| verification_data | JSON | yes |  |  |
| document_types | JSON | yes |  |  |
| submitted_at | DATETIME | yes |  |  |
| reviewed_at | DATETIME | yes |  |  |
| reviewer_id | INTEGER | yes |  | users.id |

Indexes: ix_kyc_verifications_id, ix_kyc_verifications_user_id

### `legal_contract_templates`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| template_type | VARCHAR(50) | no |  |  |
| version | VARCHAR(20) | yes |  |  |
| content | TEXT | no |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_lct_type, ix_legal_contract_templates_country_code, ix_legal_contract_templates_id

### `manual_review_queue`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| entity_type | VARCHAR(50) | no |  |  |
| entity_id | INTEGER | no |  |  |
| fraud_score | INTEGER | no |  |  |
| triggered_rules | TEXT | yes |  |  |
| reason | VARCHAR | no |  |  |
| priority | VARCHAR | yes |  |  |
| assigned_to | INTEGER | yes |  | users.id |
| admin_notes | TEXT | yes |  |  |
| status | VARCHAR | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_manual_review_priority, ix_manual_review_queue_id, ix_manual_review_status

### `meeting_action_items`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| meeting_id | INTEGER | no |  | meeting_transcripts.id |
| entity_type | VARCHAR(50) | yes |  |  |
| entity_id | INTEGER | yes |  |  |
| action | VARCHAR | no |  |  |
| metadata_json | JSON | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| assigned_to | INTEGER | yes |  | users.id |
| created_at | DATETIME | yes |  |  |
| due_date | DATETIME | yes |  |  |

Indexes: ix_action_item_meeting, ix_action_item_status, ix_meeting_action_items_id

### `meeting_recordings`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| room_id | VARCHAR(64) | no |  |  |
| started_by | INTEGER | no |  | users.id |
| recording_url | VARCHAR(500) | yes |  |  |
| duration_seconds | INTEGER | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| started_at | DATETIME | yes |  |  |
| ended_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_meeting_recordings_id

### `meeting_transcripts`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| room_id | VARCHAR(64) | no |  |  |
| language | VARCHAR(10) | yes |  |  |
| segments | JSON | yes |  |  |
| action_items | JSON | yes |  |  |
| summary | TEXT | yes |  |  |
| word_count | INTEGER | yes |  |  |
| duration_seconds | INTEGER | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_meeting_transcripts_id, ix_transcript_room

### `news_articles`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| source_id | INTEGER | yes |  | news_sources.id |
| external_id | VARCHAR(255) | yes |  |  |
| content_hash | VARCHAR(64) | yes |  |  |
| title | VARCHAR(300) | no |  |  |
| summary | TEXT | yes |  |  |
| content | TEXT | yes |  |  |
| url | VARCHAR(500) | yes |  |  |
| image_url | VARCHAR(500) | yes |  |  |
| published_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |
| ai_sentiment | VARCHAR(20) | yes |  |  |
| ai_tags | JSON | yes |  |  |
| is_published | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_news_articles_content_hash, ix_news_articles_id, ix_news_articles_published

### `news_sources`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| name | VARCHAR(100) | no |  |  |
| url | VARCHAR(500) | no |  |  |
| source_type | VARCHAR(20) | yes |  |  |
| api_key_required | BOOLEAN | yes |  |  |
| category | VARCHAR(50) | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_news_sources_id

### `newsletter_subscribers`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| email | VARCHAR | no |  |  |
| is_active | BOOLEAN | yes |  |  |
| subscribed_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_newsletter_subscribers_email, ix_newsletter_subscribers_id

### `normalized_webhook_events`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| provider_code | VARCHAR | no |  |  |
| gateway_event_id | VARCHAR | no |  |  |
| event_type | VARCHAR | no |  |  |
| status | VARCHAR | no |  |  |
| environment | VARCHAR | yes |  |  |
| processed_at | DATETIME | yes |  |  |
| zozi_order_id | INTEGER | yes |  |  |
| gateway_transaction_id | VARCHAR | yes |  |  |
| gateway_customer_id | VARCHAR | yes |  |  |
| gross_amount | NUMERIC(12, 2) | yes |  |  |
| currency | VARCHAR(3) | yes |  |  |
| gateway_fee | NUMERIC(12, 2) | yes |  |  |
| net_settlement | NUMERIC(12, 2) | yes |  |  |
| fraud_score | NUMERIC(5, 2) | yes |  |  |
| three_ds_status | VARCHAR | yes |  |  |
| avs_result | VARCHAR | yes |  |  |
| raw_payload | TEXT | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_normalized_webhook_events_country_code, ix_normalized_webhook_events_id, ix_normalized_webhook_events_provider_code

### `ocr_results`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| document_verification_id | INTEGER | no |  | document_verifications.id |
| extracted_text | TEXT | yes |  |  |
| confidence_score | VARCHAR | yes |  |  |
| fields | JSON | yes |  |  |
| processed_at | DATETIME | yes |  |  |

Indexes: ix_ocr_results_id

### `offices`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| name | VARCHAR(200) | no |  |  |
| country_code | VARCHAR(10) | no |  |  |
| city | VARCHAR(100) | yes |  |  |
| latitude | FLOAT | yes |  |  |
| longitude | FLOAT | yes |  |  |
| geo_fence_radius_meters | INTEGER | yes |  |  |
| address | TEXT | yes |  |  |
| phone | VARCHAR(50) | yes |  |  |
| email | VARCHAR(200) | yes |  |  |
| is_active | BOOLEAN | yes |  |  |

Indexes: ix_offices_id

### `oman_delivery_zones`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| zone_code | VARCHAR(20) | no |  |  |
| zone_name | VARCHAR(100) | no |  |  |
| description | TEXT | yes |  |  |
| car_rate | NUMERIC(10, 2) | yes |  |  |
| van_rate | NUMERIC(10, 2) | yes |  |  |
| truck_rate | NUMERIC(10, 2) | yes |  |  |
| weight_surcharge_rate | NUMERIC(5, 4) | yes |  |  |
| weight_surcharge_threshold_kg | NUMERIC(10, 2) | yes |  |  |
| cities_json | TEXT | yes |  |  |
| sort_order | INTEGER | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_oman_delivery_zones_id, ix_oman_zone_code

### `onboarding_pipelines`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | no |  | users.id |
| pipeline_type | VARCHAR | no |  |  |
| status | VARCHAR | yes |  |  |
| current_step | INTEGER | yes |  |  |
| steps_data | JSON | yes |  |  |
| started_at | DATETIME | yes |  |  |
| completed_at | DATETIME | yes |  |  |

Indexes: ix_onboarding_pipelines_id, ix_onboarding_pipelines_user_id

### `onboarding_steps`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| pipeline_id | INTEGER | no |  | onboarding_pipelines.id |
| step_name | VARCHAR | no |  |  |
| status | VARCHAR | yes |  |  |
| data | JSON | yes |  |  |
| started_at | DATETIME | yes |  |  |
| completed_at | DATETIME | yes |  |  |

Indexes: ix_onboarding_steps_id

### `org_units`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| name | VARCHAR(200) | no |  |  |
| parent_id | INTEGER | yes |  | org_units.id |
| country_code | VARCHAR(10) | yes |  |  |
| level | INTEGER | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_org_units_id

### `password_reset_tokens`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | yes |  | users.id |
| token | VARCHAR | yes |  |  |
| expires_at | DATETIME | no |  |  |
| used | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_password_reset_tokens_country_code, ix_password_reset_tokens_id, ix_password_reset_tokens_token, ix_password_reset_tokens_user_id

### `payment_gateway_connections`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| provider_code | VARCHAR(100) | no |  |  |
| gateway_name | VARCHAR(100) | no |  |  |
| country_code | VARCHAR(10) | no |  |  |
| environment | VARCHAR(20) | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| credentials | JSON | yes |  |  |
| fee_config | JSON | yes |  |  |
| supported_methods | JSON | yes |  |  |
| last_sync_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| provider_kind | VARCHAR(20) | no |  |  |
| display_name | VARCHAR(120) | no |  |  |
| is_enabled | BOOLEAN | yes |  |  |
| supports_customer_checkout | BOOLEAN | yes |  |  |
| supports_payouts | BOOLEAN | yes |  |  |
| mode | VARCHAR(20) | no |  |  |
| public_key | VARCHAR(500) | yes |  |  |
| secret_key | VARCHAR(1000) | yes |  |  |
| webhook_secret | VARCHAR(1000) | yes |  |  |
| merchant_id | VARCHAR(255) | yes |  |  |
| api_base_url | VARCHAR(500) | yes |  |  |
| webhook_url | VARCHAR(500) | yes |  |  |
| test_url | VARCHAR(500) | yes |  |  |
| settlement_cycle | VARCHAR(50) | yes |  |  |
| supported_currencies_json | TEXT | yes |  |  |
| extra_config_json | TEXT | yes |  |  |
| notes | TEXT | yes |  |  |
| fee_percent | NUMERIC(8, 4) | no |  |  |
| fixed_fee_amount | NUMERIC(12, 2) | no |  |  |
| payout_fee_percent | NUMERIC(8, 4) | no |  |  |
| payout_fixed_fee_amount | NUMERIC(12, 2) | no |  |  |
| pass_fee_to_customer | BOOLEAN | yes |  |  |
| test_status | VARCHAR(20) | no |  |  |
| test_message | VARCHAR(500) | yes |  |  |
| last_tested_at | DATETIME | yes |  |  |
| updated_by | INTEGER | yes |  | users.id |

Indexes: ix_payment_gateway_connections_id

### `payment_orchestrator_sync`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| gateway_id | VARCHAR(60) | no |  |  |
| gateway_name | VARCHAR(100) | yes |  |  |
| environment | VARCHAR(20) | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| fee_percent | NUMERIC(8, 4) | yes |  |  |
| fee_fixed | NUMERIC(12, 2) | yes |  |  |
| supported_payment_methods | TEXT | yes |  |  |
| last_sync_at | DATETIME | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_payment_orchestrator_sync_country_code, ix_payment_orchestrator_sync_id, ix_pos_status

### `payment_provider_configs`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| provider_name | VARCHAR | no |  |  |
| config | JSON | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| updated_by | INTEGER | yes |  | users.id |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_payment_provider_configs_country_code, ix_payment_provider_configs_id

### `payment_reconciliation_runs`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| run_date | DATETIME | no |  |  |
| total_amount | NUMERIC(15, 2) | yes |  |  |
| reconciled_count | INTEGER | yes |  |  |
| unmatched_count | INTEGER | yes |  |  |
| processed_count | INTEGER | yes |  |  |
| stale_pending_orders | INTEGER | yes |  |  |
| recent_webhook_count | INTEGER | yes |  |  |
| result_json | TEXT | yes |  |  |
| started_at | DATETIME | yes |  |  |
| completed_at | DATETIME | yes |  |  |
| status | VARCHAR | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_payment_reconciliation_runs_country_code, ix_payment_reconciliation_runs_id

### `payments`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| order_id | INTEGER | no |  | orders.id |
| amount | NUMERIC(10, 2) | no |  |  |
| payment_method | VARCHAR | no |  |  |
| provider | VARCHAR | yes |  |  |
| status | VARCHAR | yes |  |  |
| intent_id | VARCHAR | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  | country_configs.code |
| layout_json | TEXT | yes |  |  |

Indexes: ix_payments_country_code, ix_payments_id, ix_payments_order_id

### `pending_journal_entries`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| lines_json | TEXT | no |  |  |
| description | TEXT | yes |  |  |
| source | VARCHAR(50) | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |
| entry_date | DATETIME | no |  |  |
| amount_threshold_triggered | BOOLEAN | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| created_by | INTEGER | no |  | users.id |
| approved_by | INTEGER | yes |  | users.id |
| rejected_by | INTEGER | yes |  | users.id |
| rejection_reason | TEXT | yes |  |  |
| approved_at | DATETIME | yes |  |  |
| journal_entry_id | INTEGER | yes |  | journal_entries.id |
| created_at | DATETIME | yes |  |  |

Indexes: ix_pending_je_country, ix_pending_je_maker, ix_pending_je_status, ix_pending_journal_entries_id

### `permission_categories`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| name | VARCHAR(100) | no |  |  |
| slug | VARCHAR(100) | no |  |  |
| description | TEXT | yes |  |  |
| icon | VARCHAR(50) | yes |  |  |
| sort_order | INTEGER | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| country_code | VARCHAR(10) | no |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_permission_categories_id

### `physical_id_cards`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| employee_id | INTEGER | no |  | employees.id |
| card_number | VARCHAR(50) | no |  |  |
| issued_at | DATETIME | yes |  |  |
| expires_at | DATETIME | yes |  |  |
| is_revoked | BOOLEAN | yes |  |  |
| revoked_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_physical_id_cards_card_number, ix_physical_id_cards_country_code, ix_physical_id_cards_id

### `predictive_simulations`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| simulation_type | VARCHAR(50) | no |  |  |
| parameters_json | TEXT | no |  |  |
| result_json | TEXT | no |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_predictive_simulations_id

### `processed_webhook_events`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| processor | VARCHAR | no |  |  |
| event_id | VARCHAR | no |  |  |
| payload_hash | VARCHAR | no |  |  |
| processed_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_processed_webhook_events_country_code, ix_processed_webhook_events_id

### `product_commission_overrides`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| product_id | INTEGER | no |  | products.id |
| supplier_id | INTEGER | no |  | users.id |
| rate_percent | NUMERIC(5, 2) | no |  |  |
| set_by_admin_id | INTEGER | yes |  | users.id |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_product_commission_overrides_country_code, ix_product_commission_overrides_id

### `product_filter_metadata`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| category_id | INTEGER | yes |  | categories.id |
| filter_name | VARCHAR(100) | no |  |  |
| filter_type | VARCHAR(50) | no |  |  |
| display_order | INTEGER | no |  |  |
| is_active | BOOLEAN | no |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_product_filter_metadata_category_id, ix_product_filter_metadata_country_code, ix_product_filter_metadata_id

### `product_filter_options`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| filter_metadata_id | INTEGER | no |  | product_filter_metadata.id |
| option_value | VARCHAR(255) | no |  |  |
| option_display_name | VARCHAR(255) | no |  |  |
| product_count | INTEGER | no |  |  |
| sort_order | INTEGER | no |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_product_filter_options_country_code, ix_product_filter_options_filter_metadata_id, ix_product_filter_options_id

### `product_variants`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| product_id | INTEGER | no |  | products.id |
| sku | VARCHAR | yes |  |  |
| title | VARCHAR | yes |  |  |
| size | VARCHAR | yes |  |  |
| color | VARCHAR | yes |  |  |
| material | VARCHAR | yes |  |  |
| pattern | VARCHAR | yes |  |  |
| gender | VARCHAR | yes |  |  |
| barcode | VARCHAR | yes |  |  |
| product_code | VARCHAR | yes |  |  |
| price | NUMERIC(10, 2) | yes |  |  |
| stock | INTEGER | yes |  |  |
| media_url | VARCHAR | yes |  |  |
| attributes_json | TEXT | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| sort_order | INTEGER | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |
| variant_key | VARCHAR(64) | yes |  |  |

Indexes: ix_product_variants_color, ix_product_variants_country_code, ix_product_variants_gender, ix_product_variants_id, ix_product_variants_material, ix_product_variants_pattern, ix_product_variants_size, ix_product_variants_variant_key

### `product_verifications`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| product_id | INTEGER | no |  | products.id |
| status | VARCHAR | yes |  |  |
| verified_by | INTEGER | yes |  | users.id |
| shipment_id | INTEGER | yes |  | shipments.id |
| verification_type | VARCHAR | yes |  |  |
| result | VARCHAR | yes |  |  |
| expected_specs | TEXT | yes |  |  |
| actual_specs | TEXT | yes |  |  |
| discrepancies | TEXT | yes |  |  |
| scan_code | VARCHAR | yes |  |  |
| image_urls | TEXT | yes |  |  |
| notes | TEXT | yes |  |  |
| created_at | DATETIME | yes |  |  |
| order_id | INTEGER | yes |  | orders.id |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_product_verifications_country_code, ix_product_verifications_id

### `product_videos`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| product_id | INTEGER | no |  | products.id |
| video_url | VARCHAR(500) | no |  |  |
| thumbnail_url | VARCHAR(500) | yes |  |  |
| duration_seconds | INTEGER | yes |  |  |
| video_type | VARCHAR(50) | yes |  |  |
| title | VARCHAR(255) | yes |  |  |
| description | TEXT | yes |  |  |
| views_count | INTEGER | yes |  |  |
| is_featured | BOOLEAN | yes |  |  |
| upload_status | VARCHAR(50) | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_product_videos_country_code, ix_product_videos_id, ix_product_videos_product_id

### `promotion_engine_configs`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | yes |  | country_configs.code |
| engine_enabled | BOOLEAN | yes |  |  |
| allow_product_coupons | BOOLEAN | yes |  |  |
| allow_category_coupons | BOOLEAN | yes |  |  |
| allow_order_tier_discounts | BOOLEAN | yes |  |  |
| allow_referral_rewards | BOOLEAN | yes |  |  |
| allow_supplier_promotions | BOOLEAN | yes |  |  |
| allow_global_coupons | BOOLEAN | yes |  |  |
| stacking_mode | VARCHAR | yes |  |  |
| max_combined_discount_percent | NUMERIC(5, 2) | yes |  |  |
| max_combined_discount_amount | NUMERIC(12, 3) | yes |  |  |
| show_savings_line_item | BOOLEAN | yes |  |  |
| tier_discount_visible | BOOLEAN | yes |  |  |
| points_per_omr | INTEGER | yes |  |  |
| referral_referrer_points | INTEGER | yes |  |  |
| referral_referee_points | INTEGER | yes |  |  |
| points_expiry_months | INTEGER | yes |  |  |
| referral_monthly_cap | INTEGER | yes |  |  |
| referral_verification_delay_days | INTEGER | yes |  |  |
| min_points_redeem | INTEGER | yes |  |  |
| allow_partial_points_redemption | BOOLEAN | yes |  |  |
| updated_by | INTEGER | yes |  | users.id |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_promotion_engine_configs_country_code, ix_promotion_engine_configs_id

### `promotion_ledger_entries`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| promotion_id | INTEGER | yes |  |  |
| user_id | INTEGER | yes |  | users.id |
| amount | NUMERIC(12, 2) | no |  |  |
| entry_type | VARCHAR | no |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_promotion_ledger_entries_country_code, ix_promotion_ledger_entries_id

### `promotion_order_tiers`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| promotion_id | INTEGER | yes |  |  |
| tier_name | VARCHAR | yes |  |  |
| min_order_amount | NUMERIC(10, 2) | no |  |  |
| max_order_amount | NUMERIC(10, 2) | yes |  |  |
| discount_type | VARCHAR | no |  |  |
| discount_amount | NUMERIC(10, 2) | yes |  |  |
| discount_value | NUMERIC(10, 2) | yes |  |  |
| stacking_allowed | BOOLEAN | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| sort_order | INTEGER | yes |  |  |
| updated_by | INTEGER | yes |  | users.id |
| country_code | VARCHAR(10) | yes |  | country_configs.code |
| created_at | DATETIME | yes |  |  |

Indexes: ix_promotion_order_tiers_country_code, ix_promotion_order_tiers_id

### `referral_point_events`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | no |  | users.id |
| event_type | VARCHAR(40) | no |  |  |
| points | INTEGER | no |  |  |
| referred_user_id | INTEGER | yes |  | users.id |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_referral_point_events_country_code, ix_referral_point_events_id, ix_referral_point_events_user_id

### `referrals`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| referrer_id | INTEGER | no |  | users.id |
| referred_id | INTEGER | no |  | users.id |
| status | VARCHAR | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_referrals_country_code, ix_referrals_id, ix_referrals_referred_id, ix_referrals_referrer_id

### `refund_ledger`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| order_id | INTEGER | no |  | orders.id |
| return_request_id | INTEGER | yes |  | return_requests.id |
| ledger_id | INTEGER | yes |  |  |
| bank_transaction_id | INTEGER | yes |  |  |
| reason | TEXT | yes |  |  |
| refund_reason | TEXT | yes |  |  |
| refund_method | VARCHAR | yes |  |  |
| customer_refund_amount | NUMERIC(12, 2) | yes |  |  |
| supplier_reversal | NUMERIC(12, 2) | yes |  |  |
| logistics_reversal | NUMERIC(12, 2) | yes |  |  |
| delivery_fee_reversal | NUMERIC(12, 2) | yes |  |  |
| commission_reversal | NUMERIC(12, 2) | yes |  |  |
| vat_adjustment | NUMERIC(12, 2) | yes |  |  |
| vat_reversal | NUMERIC(12, 2) | yes |  |  |
| performed_by | INTEGER | yes |  | users.id |
| processed_at | DATETIME | yes |  |  |
| currency | VARCHAR(3) | yes |  |  |
| status | VARCHAR | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |
| is_deleted | BOOLEAN | yes |  |  |
| deleted_at | DATETIME | yes |  |  |
| deleted_by | INTEGER | yes |  | users.id |

Indexes: ix_refund_ledger_country_code, ix_refund_ledger_id, ix_refund_ledger_is_deleted

### `retention_job_runs`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| job_type | VARCHAR(50) | yes |  |  |
| target_table | VARCHAR(100) | yes |  |  |
| target_name | VARCHAR(100) | yes |  |  |
| cutoff_days | INTEGER | yes |  |  |
| records_deleted | INTEGER | yes |  |  |
| archived_count | INTEGER | yes |  |  |
| deleted_count | INTEGER | yes |  |  |
| artifact_path | VARCHAR | yes |  |  |
| result_json | TEXT | yes |  |  |
| started_at | DATETIME | yes |  |  |
| completed_at | DATETIME | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| error_message | TEXT | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_retention_job_runs_country_code, ix_retention_job_runs_id

### `revoked_tokens`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| jti | VARCHAR(64) | no |  |  |
| user_id | INTEGER | yes |  | users.id |
| expires_at | DATETIME | no |  |  |
| revoked_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_revoked_tokens_country_code, ix_revoked_tokens_id

### `role_permission_assignments`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| role_name | VARCHAR(80) | no |  |  |
| permission_id | INTEGER | no |  | permissions.id |
| country_code | VARCHAR(10) | yes |  | country_configs.code |
| granted_by | INTEGER | yes |  | users.id |
| is_granted | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_role_permission_assignments_id

### `role_permission_settings`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| role | VARCHAR | no |  |  |
| permissions_json | JSON | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_role_permission_settings_country_code, ix_role_permission_settings_id

### `support_ticket_replies`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| ticket_id | INTEGER | no |  | support_tickets.id |
| sender_id | INTEGER | no |  | users.id |
| message | TEXT | no |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_support_ticket_replies_country_code, ix_support_ticket_replies_id

### `support_tickets`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | no |  | users.id |
| subject | VARCHAR | no |  |  |
| priority | VARCHAR | yes |  |  |
| status | VARCHAR | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_support_tickets_country_code, ix_support_tickets_id

### `system_alerts`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| alert_type | VARCHAR | no |  |  |
| severity | VARCHAR | yes |  |  |
| title | VARCHAR | no |  |  |
| message | TEXT | no |  |  |
| is_acknowledged | BOOLEAN | yes |  |  |
| acknowledged_by | INTEGER | yes |  | users.id |
| acknowledged_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_system_alerts_country_code, ix_system_alerts_id

### `system_health_events`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| service | VARCHAR(100) | yes |  |  |
| metric_name | VARCHAR(100) | no |  |  |
| metric_value | NUMERIC(12, 4) | no |  |  |
| severity | VARCHAR(20) | yes |  |  |
| message | TEXT | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_health_events_metric_time, ix_system_health_events_id

### `system_settings`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| key | VARCHAR | no |  |  |
| value | TEXT | yes |  |  |
| value_type | VARCHAR | yes |  |  |
| description | VARCHAR | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_system_settings_country_code, ix_system_settings_id

### `tax_rules`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| tax_name | VARCHAR(100) | no |  |  |
| tax_rate | NUMERIC(5, 4) | no |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_tax_rules_id

### `ticket_attachments`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| ticket_reply_id | INTEGER | yes |  | support_ticket_replies.id |
| ticket_id | INTEGER | yes |  | support_tickets.id |
| file_url | VARCHAR | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_ticket_attachments_country_code, ix_ticket_attachments_id

### `ticket_messages`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| ticket_id | INTEGER | no |  | support_tickets.id |
| sender_id | INTEGER | no |  | users.id |
| message | TEXT | no |  |  |
| is_admin | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_ticket_messages_country_code, ix_ticket_messages_id

### `ticket_replies`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| ticket_id | INTEGER | no |  | support_tickets.id |
| sender_id | INTEGER | no |  | users.id |
| message | TEXT | no |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_ticket_replies_country_code, ix_ticket_replies_id

### `transaction_ledgers`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | yes |  | users.id |
| supplier_id | INTEGER | yes |  | users.id |
| logistics_partner_id | INTEGER | yes |  | logistics_partners.id |
| order_id | INTEGER | yes |  | orders.id |
| order_item_id | INTEGER | yes |  | order_items.id |
| shipment_id | INTEGER | yes |  | shipments.id |
| payment_method | VARCHAR(20) | yes |  |  |
| product_subtotal | NUMERIC(12, 2) | yes |  |  |
| discount_amount | NUMERIC(12, 2) | yes |  |  |
| delivery_pickup_charge | NUMERIC(12, 2) | yes |  |  |
| delivery_dropoff_charge | NUMERIC(12, 2) | yes |  |  |
| delivery_total | NUMERIC(12, 2) | yes |  |  |
| vat_amount | NUMERIC(12, 2) | yes |  |  |
| zozi_commission_rate | NUMERIC(5, 4) | yes |  |  |
| zozi_commission | NUMERIC(12, 2) | yes |  |  |
| net_supplier_amount | NUMERIC(12, 2) | yes |  |  |
| net_logistics_amount | NUMERIC(12, 2) | yes |  |  |
| net_zozi_amount | NUMERIC(12, 2) | yes |  |  |
| cod_collected_amount | NUMERIC(12, 2) | yes |  |  |
| cod_remittance_due | NUMERIC(12, 2) | yes |  |  |
| settlement_status | VARCHAR(30) | yes |  |  |
| currency | VARCHAR(3) | yes |  |  |
| transaction_type | VARCHAR | yes |  |  |
| reference_id | VARCHAR | yes |  |  |
| balance_after | NUMERIC(12, 2) | yes |  |  |
| notes | TEXT | yes |  |  |
| amount | NUMERIC(12, 2) | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_transaction_ledger_country, ix_transaction_ledgers_country_code, ix_transaction_ledgers_id

### `user_browsing_history`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | no |  | users.id |
| product_id | INTEGER | no |  | products.id |
| viewed_at | DATETIME | yes |  |  |

Indexes: ix_user_browsing_history_id, ix_user_browsing_history_product_id, ix_user_browsing_history_user_id

### `user_devices`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | no |  | users.id |
| device_id | VARCHAR(255) | no |  |  |
| device_type | VARCHAR(50) | yes |  |  |
| last_seen_at | DATETIME | yes |  |  |
| is_current | BOOLEAN | yes |  |  |
| is_trusted | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_user_devices_country_code, ix_user_devices_id, ix_user_devices_user_id

### `user_login_history`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | no |  | users.id |
| ip_address | VARCHAR | no |  |  |
| user_agent | VARCHAR | yes |  |  |
| timestamp | DATETIME | yes |  |  |
| success | BOOLEAN | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_user_login_history_country_code, ix_user_login_history_id, ix_user_login_history_user_id

### `user_permission_overrides`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | no |  | users.id |
| permission_id | INTEGER | no |  | permissions.id |
| country_code | VARCHAR(10) | yes |  | country_configs.code |
| is_granted | BOOLEAN | yes |  |  |
| granted_by | INTEGER | yes |  | users.id |
| expires_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_user_permission_overrides_id

### `user_sessions`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | no |  | users.id |
| session_token | VARCHAR(255) | no |  |  |
| ip_address | VARCHAR(45) | yes |  |  |
| user_agent | VARCHAR(500) | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| last_activity | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_user_sessions_country_code, ix_user_sessions_id, ix_user_sessions_session_token, ix_user_sessions_user_active, ix_user_sessions_user_id

### `vat_remittances`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| period_start | DATETIME | no |  |  |
| period_end | DATETIME | no |  |  |
| vat_collected_amount | NUMERIC(12, 2) | yes |  |  |
| vat_adjustment_amount | NUMERIC(12, 2) | yes |  |  |
| amount_due | NUMERIC(12, 2) | yes |  |  |
| amount | NUMERIC(12, 2) | no |  |  |
| amount_remitted | NUMERIC(12, 2) | yes |  |  |
| currency | VARCHAR(3) | yes |  |  |
| bank_transaction_id | INTEGER | yes |  |  |
| remitted_by | INTEGER | yes |  | users.id |
| remitted_at | DATETIME | yes |  |  |
| notes | TEXT | yes |  |  |
| status | VARCHAR | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_vat_remittances_country_code, ix_vat_remittances_id

### `war_room_templates`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| name | VARCHAR(100) | no |  |  |
| severity | VARCHAR | no |  |  |
| auto_assign | BOOLEAN | yes |  |  |
| template_data | JSON | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_war_room_templates_id


## risk (14 tables)

### `audit_logs`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| action | VARCHAR | no |  |  |
| entity_type | VARCHAR | no |  |  |
| entity_id | INTEGER | yes |  |  |
| user_id | INTEGER | yes |  | users.id |
| username | VARCHAR | yes |  |  |
| user_role | VARCHAR | yes |  |  |
| details | JSON | yes |  |  |
| ip_address | VARCHAR | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_audit_logs_id

### `escalation_sla_logs`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| message_id | INTEGER | no |  |  |
| message_type | VARCHAR(30) | no |  |  |
| original_recipient_id | INTEGER | yes |  | users.id |
| escalated_to_user_id | INTEGER | yes |  | users.id |
| escalated_to_role | VARCHAR(40) | yes |  |  |
| priority | VARCHAR(20) | no |  |  |
| elapsed_minutes | INTEGER | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| escalated_at | DATETIME | yes |  |  |
| acknowledged_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_escalation_message, ix_escalation_sla_logs_id, ix_escalation_status

### `escalation_sla_rules`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | yes |  | country_configs.code |
| priority | VARCHAR(20) | no |  |  |
| escalate_after_minutes | INTEGER | no |  |  |
| escalate_to_role | VARCHAR(40) | no |  |  |
| notify_via | VARCHAR(100) | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_escalation_sla_rules_id

### `fraud_alerts`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| alert_type | VARCHAR(50) | no |  |  |
| entity_type | VARCHAR(50) | no |  |  |
| entity_id | INTEGER | no |  |  |
| fraud_score | NUMERIC(5, 2) | no |  |  |
| triggered_rules | TEXT | yes |  |  |
| priority | VARCHAR(20) | yes |  |  |
| details | TEXT | yes |  |  |
| is_resolved | BOOLEAN | yes |  |  |
| resolved_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_fraud_alerts_country_code, ix_fraud_alerts_id

### `fraud_blacklist`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| identifier_type | VARCHAR | no |  |  |
| identifier_value | VARCHAR | no |  |  |
| identifier_value_hash | VARCHAR | yes |  |  |
| reason | VARCHAR | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| status | VARCHAR | yes |  |  |
| created_at | DATETIME | yes |  |  |
| expires_at | DATETIME | yes |  |  |

Indexes: ix_fraud_blacklist_id

### `fraud_case_assignments`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| case_id | INTEGER | no |  | fraud_cases.id |
| assigned_to | INTEGER | no |  | users.id |
| assigned_by | INTEGER | yes |  | users.id |
| role_at_assignment | VARCHAR(50) | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_fraud_case_assignments_id

### `fraud_cases`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| case_number | VARCHAR(50) | no |  |  |
| title | VARCHAR(200) | no |  |  |
| description | TEXT | yes |  |  |
| fraud_score | INTEGER | no |  |  |
| priority | VARCHAR(20) | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| entity_type | VARCHAR(50) | yes |  |  |
| entity_id | INTEGER | yes |  |  |
| assigned_to | INTEGER | yes |  | users.id |
| created_by | INTEGER | yes |  | users.id |
| resolved_at | DATETIME | yes |  |  |
| resolution_notes | TEXT | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_fraud_case_priority, ix_fraud_case_status, ix_fraud_cases_country_code, ix_fraud_cases_id

### `fraud_events`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | yes |  | users.id |
| order_id | INTEGER | yes |  | orders.id |
| event_type | VARCHAR(50) | no |  |  |
| ip_address | VARCHAR(45) | yes |  |  |
| device_hash | VARCHAR(64) | yes |  |  |
| session_id | VARCHAR(128) | yes |  |  |
| fraud_score | NUMERIC(5, 2) | no |  |  |
| triggered_rules | TEXT | yes |  |  |
| details | JSON | yes |  |  |
| is_flagged | BOOLEAN | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| reviewed_by | INTEGER | yes |  | users.id |
| reviewed_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_fraud_event_score, ix_fraud_event_type, ix_fraud_event_user, ix_fraud_events_country_code, ix_fraud_events_id

### `fraud_rules`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| rule_key | VARCHAR(100) | no |  |  |
| name | VARCHAR(200) | no |  |  |
| description | TEXT | yes |  |  |
| weight | INTEGER | yes |  |  |
| condition_json | TEXT | yes |  |  |
| action | VARCHAR(50) | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| is_global | BOOLEAN | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_fraud_rule_active, ix_fraud_rules_id

### `fraud_scoring_logs`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| event_type | VARCHAR(50) | no |  |  |
| user_id | INTEGER | yes |  | users.id |
| order_id | INTEGER | yes |  | orders.id |
| ip_address | VARCHAR(45) | yes |  |  |
| device_hash | VARCHAR(64) | yes |  |  |
| session_id | VARCHAR(128) | yes |  |  |
| raw_score | INTEGER | no |  |  |
| triggered_rules | JSON | yes |  |  |
| metadata_json | JSON | yes |  |  |
| action_taken | VARCHAR(50) | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_fraud_scoring_logs_country_code, ix_fraud_scoring_logs_id, ix_scoring_event, ix_scoring_score

### `fraud_velocity_counters`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| key | VARCHAR(255) | no |  |  |
| count | INTEGER | yes |  |  |
| window_start | DATETIME | yes |  |  |
| window_end | DATETIME | no |  |  |
| entity_type | VARCHAR(50) | yes |  |  |
| entity_id | INTEGER | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_fraud_velocity_counters_id, ix_fraud_velocity_counters_key, ix_velocity_key

### `incident_action_items`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| war_room_id | INTEGER | no |  | incident_war_rooms.id |
| assignee_id | INTEGER | yes |  | users.id |
| title | VARCHAR(200) | no |  |  |
| description | TEXT | yes |  |  |
| status | VARCHAR | yes |  |  |
| priority | VARCHAR | yes |  |  |
| due_date | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |
| completed_at | DATETIME | yes |  |  |

Indexes: ix_incident_action_items_id

### `incident_threads`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| war_room_id | INTEGER | no |  | incident_war_rooms.id |
| participant_id | INTEGER | no |  | users.id |
| message | TEXT | no |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_incident_threads_id

### `incident_war_rooms`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| incident_id | VARCHAR | no |  |  |
| title | VARCHAR(200) | no |  |  |
| severity | VARCHAR | yes |  |  |
| status | VARCHAR | yes |  |  |
| created_by | INTEGER | no |  | users.id |
| started_at | DATETIME | yes |  |  |
| resolved_at | DATETIME | yes |  |  |
| closed_at | DATETIME | yes |  |  |
| context_data | JSON | yes |  |  |

Indexes: ix_incident_war_rooms_id, ix_incident_war_rooms_incident_id


## supplier (10 tables)

### `supplier_bank_accounts`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| supplier_id | INTEGER | no |  | users.id |
| account_number | VARCHAR | yes |  |  |
| bank_name | VARCHAR | no |  |  |
| beneficiary_name | VARCHAR | yes |  |  |
| branch_name | VARCHAR | yes |  |  |
| iban | VARCHAR | yes |  |  |
| swift_code | VARCHAR | yes |  |  |
| routing_number | VARCHAR | yes |  |  |
| currency | VARCHAR(3) | yes |  |  |
| bank_country | VARCHAR(3) | yes |  |  |
| verification_status | VARCHAR | yes |  |  |
| verification_note | TEXT | yes |  |  |
| provider | VARCHAR | yes |  |  |
| provider_recipient_id | VARCHAR | yes |  |  |
| provider_status | VARCHAR | yes |  |  |
| provider_last_synced_at | DATETIME | yes |  |  |
| verified_at | DATETIME | yes |  |  |
| verified_by | INTEGER | yes |  | users.id |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_supplier_bank_accounts_country_code, ix_supplier_bank_accounts_id

### `supplier_country_commissions`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| supplier_id | INTEGER | no |  | users.id |
| country_code | VARCHAR(10) | no |  |  |
| commission_rate | NUMERIC(5, 2) | no |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |

Indexes: ix_supplier_country_commissions_id

### `supplier_disputes`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| supplier_id | INTEGER | no |  | users.id |
| order_id | INTEGER | yes |  | orders.id |
| dispute_type | VARCHAR(40) | yes |  |  |
| priority | VARCHAR(20) | yes |  |  |
| title | VARCHAR(200) | yes |  |  |
| description | TEXT | yes |  |  |
| return_request_id | INTEGER | yes |  | return_requests.id |
| verification_id | INTEGER | yes |  |  |
| invoice_id | INTEGER | yes |  |  |
| related_order_id | INTEGER | yes |  |  |
| evidence_urls | JSON | yes |  |  |
| metadata_json | JSON | yes |  |  |
| supplier_notes | TEXT | yes |  |  |
| admin_notes | TEXT | yes |  |  |
| created_by | INTEGER | yes |  | users.id |
| reason | TEXT | yes |  |  |
| status | VARCHAR | yes |  |  |
| resolved_by | INTEGER | yes |  | users.id |
| resolved_at | DATETIME | yes |  |  |
| resolution_notes | TEXT | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_supplier_disputes_country_code, ix_supplier_disputes_id

### `supplier_documents`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| supplier_id | INTEGER | no |  | supplier_profiles.id |
| doc_type | VARCHAR | no |  |  |
| document_name | VARCHAR | yes |  |  |
| file_url | VARCHAR | no |  |  |
| status | VARCHAR | yes |  |  |
| expires_at | DATETIME | yes |  |  |
| review_note | TEXT | yes |  |  |
| reviewed_by | INTEGER | yes |  | users.id |
| reviewed_at | DATETIME | yes |  |  |
| verified_by | INTEGER | yes |  | users.id |
| is_verified | BOOLEAN | yes |  |  |
| verified_at | DATETIME | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_supplier_documents_id

### `supplier_fraud_indicators`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| supplier_id | INTEGER | no |  | users.id |
| indicator_type | VARCHAR(50) | no |  |  |
| value | VARCHAR | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_supplier_fraud_indicators_country_code, ix_supplier_fraud_indicators_id

### `supplier_kyc_requirements`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| kyc_tier_required | VARCHAR(20) | no |  |  |
| document_types_required | TEXT | yes |  |  |
| verification_wait_days | INTEGER | yes |  |  |
| auto_approve_threshold | NUMERIC(5, 2) | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_supplier_kyc_requirements_id

### `supplier_notification_preferences`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| supplier_id | INTEGER | no |  | supplier_profiles.id |
| notify_new_order | BOOLEAN | yes |  |  |
| notify_low_stock | BOOLEAN | yes |  |  |
| notify_payout_processed | BOOLEAN | yes |  |  |
| notify_doc_expiry | BOOLEAN | yes |  |  |
| notify_return_updates | BOOLEAN | yes |  |  |
| notify_dispute_updates | BOOLEAN | yes |  |  |
| in_app_enabled | BOOLEAN | yes |  |  |
| email_enabled | BOOLEAN | yes |  |  |
| push_enabled | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_supplier_notification_preferences_country_code, ix_supplier_notification_preferences_id

### `supplier_onboarding_sync`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| country_code | VARCHAR(10) | no |  | country_configs.code |
| supplier_id | INTEGER | no |  | users.id |
| kyc_status | VARCHAR(30) | yes |  |  |
| kyc_documents | TEXT | yes |  |  |
| onboarding_fee_paid | BOOLEAN | yes |  |  |
| monthly_fee_status | VARCHAR(20) | yes |  |  |
| status | VARCHAR(20) | yes |  |  |
| notes | TEXT | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_sos_status, ix_supplier_onboarding_sync_country_code, ix_supplier_onboarding_sync_id, ix_supplier_onboarding_sync_supplier_id

### `supplier_profiles`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| user_id | INTEGER | no |  | users.id |
| business_name | VARCHAR | no |  |  |
| slug | VARCHAR | yes |  |  |
| business_type | VARCHAR | yes |  |  |
| country_code | VARCHAR(10) | yes |  | country_configs.code |
| phone_business | VARCHAR | yes |  |  |
| website | VARCHAR | yes |  |  |
| address | TEXT | yes |  |  |
| city | VARCHAR | yes |  |  |
| region | VARCHAR | yes |  |  |
| is_terms_accepted | BOOLEAN | yes |  |  |
| terms_version | VARCHAR | yes |  |  |
| verification_status | VARCHAR | yes |  |  |
| verified_at | DATETIME | yes |  |  |
| is_deleted | BOOLEAN | yes |  |  |
| deleted_at | DATETIME | yes |  |  |
| deleted_by_id | INTEGER | yes |  | users.id |
| is_active | BOOLEAN | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| bio | TEXT | yes |  |  |
| about_us | TEXT | yes |  |  |
| postal_code | VARCHAR | yes |  |  |
| tax_id | VARCHAR | yes |  |  |
| logo_url | VARCHAR | yes |  |  |
| banner_url | VARCHAR | yes |  |  |
| video_url | VARCHAR | yes |  |  |
| certifications | JSON | yes |  |  |
| social_links | JSON | yes |  |  |
| established_year | INTEGER | yes |  |  |
| operating_regions | JSON | yes |  |  |
| verified_documents | JSON | yes |  |  |
| document_expires_at | DATETIME | yes |  |  |
| terms_accepted_at | DATETIME | yes |  |  |
| badge_level | VARCHAR | yes |  |  |
| credibility_score | INTEGER | yes |  |  |
| badge_granted_at | DATETIME | yes |  |  |

Indexes: ix_supplier_profiles_country_code, ix_supplier_profiles_id, ix_supplier_profiles_slug

### `supplier_settlements`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| supplier_id | INTEGER | no |  | users.id |
| order_id | INTEGER | yes |  | orders.id |
| ledger_id | INTEGER | yes |  | transaction_ledgers.id |
| payout_id | INTEGER | yes |  | payouts.id |
| shipment_id | INTEGER | yes |  | shipments.id |
| gross_amount | NUMERIC(12, 2) | no |  |  |
| commission_amount | NUMERIC(12, 2) | yes |  |  |
| commission_deducted | NUMERIC(12, 2) | yes |  |  |
| commission_rate | NUMERIC(5, 4) | yes |  |  |
| vat_on_commission | NUMERIC(12, 2) | yes |  |  |
| net_amount | NUMERIC(12, 2) | no |  |  |
| status | VARCHAR | yes |  |  |
| settled_at | DATETIME | yes |  |  |
| eligible_at | DATETIME | yes |  |  |
| bank_transaction_id | INTEGER | yes |  |  |
| currency | VARCHAR(3) | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |
| is_deleted | BOOLEAN | yes |  |  |
| deleted_at | DATETIME | yes |  |  |
| deleted_by | INTEGER | yes |  | users.id |

Indexes: ix_supplier_settlements_country_code, ix_supplier_settlements_id, ix_supplier_settlements_is_deleted


## treasury (2 tables)

### `treasury_accounts`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| slug | VARCHAR | no |  |  |
| name | VARCHAR | no |  |  |
| account_type | VARCHAR | no |  |  |
| currency | VARCHAR(3) | yes |  |  |
| gl_account_code | VARCHAR | no |  |  |
| description | TEXT | yes |  |  |
| employee_id | INTEGER | yes |  | employees.id |
| balance | NUMERIC(12, 2) | yes |  |  |
| is_active | BOOLEAN | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |
| created_at | DATETIME | yes |  |  |
| updated_at | DATETIME | yes |  |  |

Indexes: ix_treasury_accounts_country_code, ix_treasury_accounts_id

### `treasury_transactions`

| Column | Type | Nullable | PK | FK |
|---|---|---|---|---|
| id | INTEGER | no | PK |  |
| from_account_id | INTEGER | yes |  | treasury_accounts.id |
| to_account_id | INTEGER | yes |  | treasury_accounts.id |
| account_id | INTEGER | yes |  | treasury_accounts.id |
| transaction_type | VARCHAR | no |  |  |
| amount | NUMERIC(12, 2) | no |  |  |
| currency | VARCHAR(3) | yes |  |  |
| reference | VARCHAR | yes |  |  |
| description | TEXT | yes |  |  |
| posted_at | DATETIME | yes |  |  |
| country_code | VARCHAR(10) | yes |  |  |

Indexes: ix_treasury_transactions_country_code, ix_treasury_transactions_id
