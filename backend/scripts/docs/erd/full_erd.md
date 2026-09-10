# ZOZI Platform — Full ERD

```mermaid
erDiagram
    accounts__accounts.addresses {
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        string label
        string full_name [NOT NULL]
        string phone
        string address_line1 [NOT NULL]
        string address_line2
        string city [NOT NULL]
        string state
        string postal_code
        string country
        boolean is_default
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code [NOT NULL]
        boolean is_deleted [NOT NULL]
    }
    accounts__accounts.addresses }o--|| accounts__users : has
    accounts__accounts.cart_items {
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        integer product_id [FK, NOT NULL]
        integer quantity
        string selected_size [NOT NULL]
        string selected_color [NOT NULL]
        integer variant_id
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code [NOT NULL]
        boolean is_deleted [NOT NULL]
    }
    accounts__accounts.cart_items }o--|| accounts__users : has
    accounts__accounts.cart_items }o--|| catalog__products : has
    accounts__accounts.carts {
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code [NOT NULL]
        boolean is_deleted [NOT NULL]
    }
    accounts__accounts.carts }o--|| accounts__users : has
    accounts__accounts.email_verification_tokens {
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        string token [UK, NOT NULL]
        datetime expires_at [NOT NULL]
        boolean is_used [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
        boolean is_deleted [NOT NULL]
    }
    accounts__accounts.email_verification_tokens }o--|| accounts__users : has
    accounts__accounts.logistics_partner_bank_accounts {
        integer id [PK, NOT NULL]
        integer partner_id [FK, NOT NULL]
        string account_number
        string bank_name [NOT NULL]
        string beneficiary_name
        string branch_name
        string iban
        string swift_code
        string routing_number
        string currency
        string bank_country
        string verification_status
        text verification_note
        string provider
        string provider_recipient_id
        string provider_status
        datetime provider_last_synced_at
        datetime verified_at
        integer verified_by_id [FK]
        boolean is_active
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    accounts__accounts.logistics_partner_bank_accounts }o--|| logistics__logistics_partners : has
    accounts__accounts.logistics_partner_bank_accounts }o--|| accounts__users : has
    accounts__accounts.mfa_factors {
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        enum factor_type [NOT NULL]
        string secret [NOT NULL]
        boolean enabled [NOT NULL]
        datetime created_at [NOT NULL]
        datetime last_used_at
        json backup_codes
        string country_code
        datetime updated_at
        boolean is_deleted [NOT NULL]
    }
    accounts__accounts.mfa_factors }o--|| accounts__users : has
    accounts__accounts.ocr_results {
        integer id [PK, NOT NULL]
        integer document_verification_id [UK, FK, NOT NULL]
        text extracted_text
        numeric confidence_score
        json fields
        datetime processed_at
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code [NOT NULL]
        boolean is_deleted [NOT NULL]
    }
    accounts__accounts.ocr_results }o--|| security__document_verifications : has
    accounts__accounts.otp_codes {
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        string purpose [NOT NULL]
        string channel [NOT NULL]
        string destination [NOT NULL]
        string code_hash [NOT NULL]
        datetime expires_at [NOT NULL]
        integer attempts
        boolean verified
        string country_code [FK, NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        boolean is_deleted [NOT NULL]
    }
    accounts__accounts.otp_codes }o--|| accounts__users : has
    accounts__accounts.otp_codes }o--|| country__country_configs : has
    accounts__accounts.password_histories {
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        string password_hash [NOT NULL]
        datetime created_at [NOT NULL]
        string country_code
        datetime updated_at
        boolean is_deleted [NOT NULL]
    }
    accounts__accounts.password_histories }o--|| accounts__users : has
    accounts__accounts.password_reset_tokens {
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        string token [UK, NOT NULL]
        datetime expires_at [NOT NULL]
        boolean is_used [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
        boolean is_deleted [NOT NULL]
    }
    accounts__accounts.password_reset_tokens }o--|| accounts__users : has
    accounts__accounts.refresh_token_families {
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        guid family_id [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        datetime revoked_at
        datetime reused_at
        string ip_address
        string user_agent
        string country_code
        boolean is_deleted [NOT NULL]
    }
    accounts__accounts.refresh_token_families }o--|| accounts__users : has
    accounts__accounts.revoked_tokens {
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        string token [UK, NOT NULL]
        datetime expires_at [NOT NULL]
        datetime revoked_at [NOT NULL]
        datetime updated_at
        string country_code
        boolean is_deleted [NOT NULL]
    }
    accounts__accounts.revoked_tokens }o--|| accounts__users : has
    accounts__accounts.social_identities {
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        string provider [NOT NULL]
        string provider_user_id [NOT NULL]
        string email [NOT NULL]
        string full_name
        json raw_data
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code [NOT NULL]
        boolean is_deleted [NOT NULL]
    }
    accounts__accounts.social_identities }o--|| accounts__users : has
    accounts__accounts.supplier_bank_accounts {
        integer id [PK, NOT NULL]
        integer supplier_id [FK, NOT NULL]
        string account_number
        string bank_name [NOT NULL]
        string beneficiary_name
        string branch_name
        string iban
        string swift_code
        string routing_number
        string currency
        string bank_country
        string verification_status
        text verification_note
        string provider
        string provider_recipient_id
        string provider_status
        datetime provider_last_synced_at
        datetime verified_at
        integer verified_by_id [FK]
        boolean is_active
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    accounts__accounts.supplier_bank_accounts }o--|| accounts__users : has
    accounts__accounts.user_consents {
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        string consent_type [NOT NULL]
        boolean granted [NOT NULL]
        datetime granted_at [NOT NULL]
        datetime revoked_at
        string ip_address
        string user_agent
        string consent_version
        string country_code
        datetime created_at [NOT NULL]
        datetime updated_at
        boolean is_deleted [NOT NULL]
    }
    accounts__accounts.user_consents }o--|| accounts__users : has
    accounts__accounts.user_devices {
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        string device_fingerprint [NOT NULL]
        string fingerprint_hash
        string device_id
        boolean is_active [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
        boolean is_deleted [NOT NULL]
    }
    accounts__accounts.user_devices }o--|| accounts__users : has
    accounts__accounts.user_login_histories {
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        string ip_address
        text user_agent
        boolean success [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
        boolean is_deleted [NOT NULL]
    }
    accounts__accounts.user_login_histories }o--|| accounts__users : has
    accounts__accounts.user_preferences {
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        string key [NOT NULL]
        json value
        datetime updated_at [NOT NULL]
        string country_code
        datetime created_at [NOT NULL]
        boolean is_deleted [NOT NULL]
    }
    accounts__accounts.user_preferences }o--|| accounts__users : has
    accounts__accounts.user_sessions {
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        string token_jti [NOT NULL]
        string refresh_token_jti
        string ip_address
        text user_agent
        string device_fingerprint
        boolean is_active [NOT NULL]
        datetime expires_at [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
        boolean is_deleted [NOT NULL]
    }
    accounts__accounts.user_sessions }o--|| accounts__users : has
    accounts__accounts.users {
        integer id [PK, NOT NULL]
        string email [UK, NOT NULL]
        string hashed_password [NOT NULL]
        string full_name
        string role [NOT NULL]
        string country_code [NOT NULL]
        boolean is_active [NOT NULL]
        boolean email_verified [NOT NULL]
        text staff_country_codes
        integer referred_by_user_id [FK]
        datetime created_at [NOT NULL]
        datetime updated_at
        boolean is_deleted [NOT NULL]
        string profile_image
        string phone
        string referral_code [UK]
        integer referral_points [NOT NULL]
        integer sharing_points [NOT NULL]
        string preferred_language
        string preferred_currency
        string preferred_country
    }
    accounts__accounts.users }o--|| accounts__users : has
    analytics__analytics.executive_news {
        integer id [PK, NOT NULL]
        string title [NOT NULL]
        text summary
        text content
        string url
        string category
        string priority
        boolean is_published
        string ai_sentiment
        datetime published_at
        boolean is_deleted [NOT NULL]
        string country_code
        datetime created_at [NOT NULL]
        datetime updated_at
        string uuid [UK]
        integer version [NOT NULL]
        integer created_by_id
        integer updated_by_id
        datetime deleted_at
        integer deleted_by_id
    }
    analytics__analytics.predictive_simulations {
        integer id [PK, NOT NULL]
        string simulation_type [NOT NULL]
        text parameters_json [NOT NULL]
        text result_json [NOT NULL]
        boolean is_deleted [NOT NULL]
        string country_code
        datetime created_at [NOT NULL]
        datetime updated_at
        string uuid [UK]
        integer version [NOT NULL]
        integer created_by_id
        integer updated_by_id
        datetime deleted_at
        integer deleted_by_id
    }
    audit__audit.audit_logs {
        integer id [PK, NOT NULL]
        string action [NOT NULL]
        string entity_type [NOT NULL]
        integer entity_id
        integer user_id [FK]
        string username
        string user_role
        json details
        string ip_address
        boolean is_deleted [NOT NULL]
        string country_code [FK]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    audit__audit.audit_logs ||--o{ accounts__users : has
    audit__audit.audit_logs }o--|| country__country_configs : has
    audit__audit.command_center_views {
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        string view_name [NOT NULL]
        json config
        boolean is_default
        boolean is_deleted [NOT NULL]
        string country_code [FK]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    audit__audit.command_center_views ||--o{ accounts__users : has
    audit__audit.command_center_views }o--|| country__country_configs : has
    catalog__catalog.ai_generation_logs {
        integer id [PK, NOT NULL]
        integer job_id [FK, NOT NULL]
        string field [NOT NULL]
        string model_used
        string prompt_hash
        numeric tokens_used
        numeric cost
        numeric confidence
        string country_code
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    catalog__catalog.ai_generation_logs ||--o{ catalog__ai_upload_jobs : has
    catalog__catalog.ai_staging_products {
        integer id [PK, NOT NULL]
        integer job_id [FK, NOT NULL]
        integer product_id [FK]
        string name [NOT NULL]
        text description
        numeric price
        integer stock
        string category
        string subcategory
        string color
        string brand
        json tags
        json sizes
        json materials
        string image_url
        json additional_media
        text ai_description
        json variant_axes
        json attributes
        numeric confidence_score
        boolean requires_human_review
        string country_code
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    catalog__catalog.ai_staging_products ||--o{ catalog__ai_upload_jobs : has
    catalog__catalog.ai_staging_products }o--|| catalog__products : has
    catalog__catalog.ai_staging_variants {
        integer id [PK, NOT NULL]
        integer job_id [FK, NOT NULL]
        integer staging_product_id [FK, NOT NULL]
        string variant_key
        string size
        string color
        string material
        string pattern
        string gender
        string sku
        string barcode
        string product_code
        numeric price
        integer stock
        string media_url
        text attributes_json
        boolean is_active
        numeric confidence_score
        boolean requires_human_review
        string country_code
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    catalog__catalog.ai_staging_variants ||--o{ catalog__ai_upload_jobs : has
    catalog__catalog.ai_staging_variants ||--o{ catalog__ai_staging_products : has
    catalog__catalog.ai_upload_jobs {
        integer id [PK, NOT NULL]
        integer supplier_id [FK, NOT NULL]
        string status [NOT NULL]
        string model_used
        string prompt_hash
        numeric tokens_used
        text source_media_json
        integer created_product_id [FK]
        text error_log
        string country_code
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    catalog__catalog.ai_upload_jobs ||--o{ accounts__users : has
    catalog__catalog.ai_upload_jobs }o--|| catalog__products : has
    catalog__catalog.categories {
        integer id [PK, NOT NULL]
        string name [NOT NULL]
        string slug [UK]
        text description
        integer parent_id [FK]
        string icon
        string image_url
        boolean is_active
        boolean is_featured
        integer sort_order
        numeric commission_rate
        string meta_title
        text meta_description
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
        boolean is_deleted [NOT NULL]
        string path
        integer depth
    }
    catalog__catalog.categories }o--|| catalog__categories : has
    catalog__catalog.product_filter_metadatas {
        integer id [PK, NOT NULL]
        integer category_id [FK]
        string filter_name [NOT NULL]
        string filter_type [NOT NULL]
        integer display_order [NOT NULL]
        boolean is_active [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    catalog__catalog.product_filter_metadatas }o--|| catalog__categories : has
    catalog__catalog.product_filter_options {
        integer id [PK, NOT NULL]
        integer filter_metadata_id [FK, NOT NULL]
        string option_value [NOT NULL]
        string option_display_name [NOT NULL]
        integer product_count [NOT NULL]
        integer sort_order [NOT NULL]
        boolean is_deleted [NOT NULL]
        string country_code
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    catalog__catalog.product_filter_options }o--|| catalog__product_filter_metadatas : has
    catalog__catalog.product_variants {
        integer id [PK, NOT NULL]
        integer product_id [FK, NOT NULL]
        string sku [UK]
        string title
        string size
        string color
        string material
        string pattern
        string gender
        string barcode [UK]
        string product_code
        numeric price
        integer stock
        string media_url
        text attributes_json
        boolean is_active
        integer sort_order
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code [FK]
        string variant_key
    }
    catalog__catalog.product_variants }o--|| catalog__products : has
    catalog__catalog.product_variants }o--|| country__country_configs : has
    catalog__catalog.product_videos {
        integer id [PK, NOT NULL]
        integer product_id [FK, NOT NULL]
        string video_url [NOT NULL]
        string thumbnail_url
        integer duration_seconds
        string video_type
        string title
        text description
        integer views_count
        boolean is_featured
        string upload_status
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    catalog__catalog.product_videos }o--|| catalog__products : has
    catalog__catalog.products {
        integer id [PK, NOT NULL]
        string name [NOT NULL]
        string slug [UK]
        text description
        text short_description
        text ai_description
        string sku [UK]
        string barcode [UK]
        numeric price [NOT NULL]
        numeric compare_price
        numeric cost_price
        integer stock
        integer low_stock_threshold
        numeric weight
        string dimensions
        json materials
        string image_url
        json images
        string category
        integer category_id [FK]
        json tags
        json attributes
        integer supplier_id [FK]
        string country_code [FK]
        boolean is_active
        boolean is_featured
        boolean is_digital
        boolean is_verified
        string moderation_status
        string brand
        string color
        json sizes
        numeric rating
        integer sales_count
        string meta_title
        text meta_description
        boolean is_approved
        boolean is_deleted
        datetime discount_starts_at
        datetime discount_ends_at
        datetime created_at [NOT NULL]
        datetime updated_at
        json filter_attributes
        json search_vector
        integer video_count
        json variant_axes
        string bg_preset
        text visibility_regions
        string slug_hash [UK]
        string subcategory
        integer return_window_days
        boolean is_new
    }
    catalog__catalog.products }o--|| catalog__categories : has
    catalog__catalog.products ||--o{ accounts__users : has
    catalog__catalog.products }o--|| country__country_configs : has
    catalog__catalog.reviews {
        integer id [PK, NOT NULL]
        integer product_id [FK, NOT NULL]
        integer user_id [FK, NOT NULL]
        integer rating [NOT NULL]
        string title
        text comment
        string image_url
        boolean is_approved
        boolean is_deleted [NOT NULL]
        boolean is_verified_purchase
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    catalog__catalog.reviews }o--|| catalog__products : has
    catalog__catalog.reviews ||--o{ accounts__users : has
    catalog__catalog.upload_jobs {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string filename [NOT NULL]
        string stored_path
        string content_type
        integer file_size
        string status [NOT NULL]
        integer progress [NOT NULL]
        text error_log
        string country_code
        datetime created_at
        datetime updated_at
    }
    catalog__catalog.video_analytics {
        integer id [PK, NOT NULL]
        integer video_id [FK, NOT NULL]
        integer user_id [FK]
        string event_type [NOT NULL]
        integer watch_duration_seconds
        string device_type
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    catalog__catalog.video_analytics }o--|| catalog__product_videos : has
    catalog__catalog.video_analytics ||--o{ accounts__users : has
    catalog__catalog.wishlist_items {
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        integer product_id [FK, NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
        boolean is_deleted [NOT NULL]
    }
    catalog__catalog.wishlist_items ||--o{ accounts__users : has
    catalog__catalog.wishlist_items }o--|| catalog__products : has
    catalog__catalog.wishlists {
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        integer product_id [FK, NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
        boolean is_deleted [NOT NULL]
    }
    catalog__catalog.wishlists ||--o{ accounts__users : has
    catalog__catalog.wishlists }o--|| catalog__products : has
    comms__comms.announcements {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string title [NOT NULL]
        text content [NOT NULL]
        boolean is_active
        datetime starts_at
        datetime ends_at
        datetime created_at
        datetime updated_at
    }
    comms__comms.campaign_recipients {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer campaign_id [FK, NOT NULL]
        integer user_id [NOT NULL]
        string email [NOT NULL]
        string status_code
        datetime sent_at
        datetime delivered_at
        datetime opened_at
        datetime clicked_at
        datetime bounced_at
        datetime created_at
    }
    comms__comms.campaign_recipients }o--|| comms__email_campaigns : has
    comms__comms.chat_attachments {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer message_id [NOT NULL]
        string message_type [NOT NULL]
        string attachment_type [NOT NULL]
        string file_url [NOT NULL]
        string file_name [NOT NULL]
        integer file_size_bytes [NOT NULL]
        string mime_type [NOT NULL]
        string thumbnail_url
        integer duration_seconds
        text waveform_json
        boolean is_processed
    }
    comms__comms.chat_read_receipts {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer message_id [NOT NULL]
        string message_type [NOT NULL]
        integer employee_id [NOT NULL]
        datetime read_at
    }
    comms__comms.communication_audit_trails {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string entity_type [NOT NULL]
        integer entity_id [NOT NULL]
        integer user_id
        string action [NOT NULL]
        string channel [NOT NULL]
        text content_preview
        json metadata_json
        datetime created_at
    }
    comms__comms.direct_chat_messages {
        integer id [PK, NOT NULL]
        integer room_id [FK, NOT NULL]
        integer sender_id [FK, NOT NULL]
        text message [NOT NULL]
        string message_type
        datetime read_at
        boolean is_deleted [NOT NULL]
        datetime created_at
    }
    comms__comms.direct_chat_messages }o--|| comms__direct_chat_rooms : has
    comms__comms.direct_chat_messages ||--o{ accounts__users : has
    comms__comms.direct_chat_rooms {
        integer id [PK, NOT NULL]
        string chat_id [UK, NOT NULL]
        integer participant_one_id [FK, NOT NULL]
        integer participant_two_id [FK, NOT NULL]
        string country_code [FK]
        boolean is_masked
        boolean is_active
        boolean is_deleted [NOT NULL]
        datetime created_at
        datetime updated_at
    }
    comms__comms.direct_chat_rooms ||--o{ accounts__users : has
    comms__comms.direct_chat_rooms }o--|| country__country_configs : has
    comms__comms.email_campaign_logs {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer campaign_id [FK, NOT NULL]
        string recipient_email [NOT NULL]
        string status_code
        datetime sent_at
        datetime delivered_at
        datetime opened_at
        datetime created_at
    }
    comms__comms.email_campaign_logs }o--|| comms__email_campaigns : has
    comms__comms.email_campaigns {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer updated_by
        integer id [PK, NOT NULL]
        string name [NOT NULL]
        string subject [NOT NULL]
        string status_code
        datetime send_at
        integer created_by
        datetime created_at
        datetime updated_at
        string from_name
        text target_audience
        datetime scheduled_at
        datetime sent_at
        integer sent_count
        integer open_count
        integer click_count
        string country_code [NOT NULL]
    }
    comms__comms.email_delivery_events {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string event_type [NOT NULL]
        string recipient_email [NOT NULL]
        string subject
        string status_code
        json details
        datetime created_at
    }
    comms__comms.email_folders {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer employee_id [NOT NULL]
        string name [NOT NULL]
        string folder_type
        integer sort_order
        boolean is_system
        datetime created_at
    }
    comms__comms.email_runtime_configs {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime created_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string provider
        string resend_api_key
        string resend_webhook_secret
        string smtp_host
        integer smtp_port
        string smtp_username
        string smtp_password
        boolean is_smtp_use_tls
        boolean is_smtp_use_ssl
        integer smtp_timeout_seconds
        string email_from_default
        string email_from_promotional
        string email_from_transactional
        string email_from_notification
        string email_from_alert
        string email_from_verification
        string email_from_login_verification
        string email_from_password_reset
        datetime updated_at
    }
    comms__comms.email_suppressions {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string email [NOT NULL]
        string reason [NOT NULL]
        string source [NOT NULL]
        string provider
        string status_code
        text notes
        datetime suppressed_at
        datetime last_event_at
        datetime created_at
    }
    comms__comms.email_templates {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer updated_by
        integer id [PK, NOT NULL]
        string name [UK, NOT NULL]
        string subject [NOT NULL]
        text content
        string template_type
        boolean is_active
        integer created_by
        datetime created_at
        datetime updated_at
    }
    comms__comms.employee_communication_threads {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer entity_id [NOT NULL]
        string entity_type [NOT NULL]
        text participants
        datetime created_at
        string country_code
    }
    comms__comms.entity_chat_messages {
        integer id [PK, NOT NULL]
        integer thread_id [FK, NOT NULL]
        integer sender_id [FK, NOT NULL]
        text message [NOT NULL]
        string message_type
        datetime read_at
        boolean is_deleted [NOT NULL]
        datetime created_at
    }
    comms__comms.entity_chat_messages }o--|| comms__entity_chat_threads : has
    comms__comms.entity_chat_messages ||--o{ accounts__users : has
    comms__comms.entity_chat_threads {
        integer id [PK, NOT NULL]
        string entity_type [NOT NULL]
        integer entity_id [NOT NULL]
        string title
        boolean is_active
        boolean is_deleted [NOT NULL]
        datetime created_at
        datetime updated_at
    }
    comms__comms.escalation_sla_logs {
        integer id [PK, NOT NULL]
        integer message_id [NOT NULL]
        string message_type [NOT NULL]
        integer original_recipient_id [FK]
        integer escalated_to_user_id [FK]
        string escalated_to_role
        string priority [NOT NULL]
        integer elapsed_minutes
        string status
        datetime escalated_at
        datetime acknowledged_at
        boolean is_deleted [NOT NULL]
        datetime created_at
    }
    comms__comms.escalation_sla_logs ||--o{ accounts__users : has
    comms__comms.escalation_sla_rules {
        integer id [PK, NOT NULL]
        string country_code [FK]
        string priority [NOT NULL]
        integer escalate_after_minutes [NOT NULL]
        string escalate_to_role [NOT NULL]
        string notify_via
        boolean is_active
        datetime created_at
    }
    comms__comms.escalation_sla_rules }o--|| country__country_configs : has
    comms__comms.external_contact_maskings {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer user_id [NOT NULL]
        string external_contact_type [NOT NULL]
        integer external_contact_id [NOT NULL]
        string masked_phone
        string masked_email
    }
    comms__comms.faqs {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        text question [NOT NULL]
        text answer [NOT NULL]
        string category
        datetime created_at
        string country_code [NOT NULL]
    }
    comms__comms.flash_sale_items {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer flash_sale_id [FK, NOT NULL]
        integer product_id [FK, NOT NULL]
        numeric original_price [NOT NULL]
        numeric discounted_price [NOT NULL]
        string country_code
        integer quantity_limit
    }
    comms__comms.flash_sale_items }o--|| promotions__flash_sales : has
    comms__comms.flash_sale_items ||--o{ catalog__products : has
    comms__comms.group_chat_members {
        integer id [PK, NOT NULL]
        integer room_id [FK, NOT NULL]
        integer user_id [FK, NOT NULL]
        string role
        datetime joined_at
        boolean is_deleted [NOT NULL]
    }
    comms__comms.group_chat_members }o--|| comms__group_chat_rooms : has
    comms__comms.group_chat_members ||--o{ accounts__users : has
    comms__comms.group_chat_messages {
        integer id [PK, NOT NULL]
        integer room_id [FK, NOT NULL]
        integer sender_id [FK, NOT NULL]
        text message [NOT NULL]
        string message_type
        datetime read_at
        boolean is_deleted [NOT NULL]
        datetime created_at
    }
    comms__comms.group_chat_messages }o--|| comms__group_chat_rooms : has
    comms__comms.group_chat_messages ||--o{ accounts__users : has
    comms__comms.group_chat_rooms {
        integer id [PK, NOT NULL]
        string chat_id [UK, NOT NULL]
        string name [NOT NULL]
        string country_code [FK]
        boolean is_encrypted
        boolean is_active
        integer created_by_id [FK, NOT NULL]
        datetime created_at
        datetime updated_at
        boolean is_deleted [NOT NULL]
    }
    comms__comms.group_chat_rooms }o--|| country__country_configs : has
    comms__comms.group_chat_rooms ||--o{ accounts__users : has
    comms__comms.help_categories {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string name [NOT NULL]
        text description
        datetime created_at
    }
    comms__comms.incident_action_items {
        integer id [PK, NOT NULL]
        integer war_room_id [FK, NOT NULL]
        integer assignee_id [FK]
        string title [NOT NULL]
        text description
        string status
        string priority
        datetime due_date
        datetime created_at
        datetime completed_at
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
    }
    comms__comms.incident_action_items }o--|| comms__incident_war_rooms : has
    comms__comms.incident_action_items ||--o{ accounts__users : has
    comms__comms.incident_threads {
        integer id [PK, NOT NULL]
        integer war_room_id [FK, NOT NULL]
        integer participant_id [FK, NOT NULL]
        text message [NOT NULL]
        datetime created_at
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
    }
    comms__comms.incident_threads }o--|| comms__incident_war_rooms : has
    comms__comms.incident_threads ||--o{ accounts__users : has
    comms__comms.incident_war_rooms {
        integer id [PK, NOT NULL]
        string incident_id [UK, NOT NULL]
        string title [NOT NULL]
        string severity
        string status
        integer created_by_id [FK, NOT NULL]
        datetime started_at
        datetime resolved_at
        datetime closed_at
        json context_data
        boolean is_deleted [NOT NULL]
        datetime updated_at [NOT NULL]
    }
    comms__comms.incident_war_rooms ||--o{ accounts__users : has
    comms__comms.internal_channel_members {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer channel_id [FK, NOT NULL]
        integer user_id [NOT NULL]
        string role
        datetime joined_at
    }
    comms__comms.internal_channel_members }o--|| comms__internal_channels : has
    comms__comms.internal_channels {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer updated_by
        integer id [PK, NOT NULL]
        string entity_type [NOT NULL]
        integer entity_id [NOT NULL]
        string name [NOT NULL]
        string channel_id [UK]
        text description
        boolean is_public
        integer created_by
        string country_code
        json allowed_roles
    }
    comms__comms.internal_emails {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer sender_id [NOT NULL]
        string subject [NOT NULL]
        text body_html
        text body_text
        text recipients
        string thread_id
        boolean is_external
        string external_message_id
        integer in_reply_to_id [FK]
        integer folder_id [FK]
        datetime created_at
        datetime updated_at
        string country_code [NOT NULL]
    }
    comms__comms.internal_emails }o--|| comms__internal_emails : has
    comms__comms.internal_emails }o--|| comms__email_folders : has
    comms__comms.internal_messages {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer channel_id [FK, NOT NULL]
        integer user_id [NOT NULL]
        text message [NOT NULL]
        string message_type
        boolean is_masked
        datetime read_at
        datetime created_at
    }
    comms__comms.internal_messages }o--|| comms__internal_channels : has
    comms__comms.internal_notices {
        integer id [PK, NOT NULL]
        string title [NOT NULL]
        text content [NOT NULL]
        string priority
        boolean is_active
        datetime valid_from
        datetime valid_to
        datetime created_at
    }
    comms__comms.masked_messages {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer sender_id [NOT NULL]
        string recipient_ref [NOT NULL]
        integer message_hash [NOT NULL]
        text content [NOT NULL]
        datetime created_at
        string country_code [NOT NULL]
    }
    comms__comms.meeting_recordings {
        integer id [PK, NOT NULL]
        boolean is_deleted [NOT NULL]
        string room_id [NOT NULL]
        integer started_by_id [FK, NOT NULL]
        string recording_url
        integer duration_seconds
        string status_code
        datetime started_at
        datetime ended_at
        datetime created_at
        datetime updated_at [NOT NULL]
    }
    comms__comms.meeting_recordings ||--o{ accounts__users : has
    comms__comms.messages {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string country_code [FK]
        integer from_user_id [NOT NULL]
        integer to_user_id [NOT NULL]
        string subject [NOT NULL]
        text body
        string entity_type
        integer entity_id
        string priority
        string category
        string status
        datetime read_at
        datetime created_at
    }
    comms__comms.messages }o--|| country__country_configs : has
    comms__comms.news_articles {
        integer id [PK, NOT NULL]
        boolean is_deleted [NOT NULL]
        integer source_id [FK]
        string external_id
        string content_hash
        string title [NOT NULL]
        text summary
        text content
        string url
        string image_url
        datetime published_at
        string country_code
        string ai_sentiment
        json ai_tags
        boolean is_published
        datetime created_at
        datetime updated_at
    }
    comms__comms.news_articles }o--|| comms__news_sources : has
    comms__comms.news_sources {
        integer id [PK, NOT NULL]
        string name [NOT NULL]
        string url [NOT NULL]
        string source_type
        boolean api_key_required
        string category
        boolean is_active
        datetime created_at
    }
    comms__comms.newsletter_subscribers {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string email [UK, NOT NULL]
        datetime created_at
        datetime updated_at
    }
    comms__comms.notifications {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer user_id [NOT NULL]
        string type
        string title [NOT NULL]
        text message [NOT NULL]
        string channel
        string priority
        boolean is_read
        datetime read_at
        string link
        string template
        json variables
        datetime scheduled_at
        string status_code
        datetime created_at
        string country_code [NOT NULL]
    }
    comms__comms.proxy_call_logs {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer channel_id [FK, NOT NULL]
        integer caller_id [NOT NULL]
        integer callee_id [NOT NULL]
        string direction [NOT NULL]
        integer duration_seconds
        string call_recording_url
        boolean is_recorded
        datetime started_at
        datetime ended_at
    }
    comms__comms.proxy_call_logs }o--|| comms__proxy_channels : has
    comms__comms.proxy_channels {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime created_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string entity_type [NOT NULL]
        integer entity_id [NOT NULL]
        string proxy_phone [UK, NOT NULL]
        string proxy_email [UK, NOT NULL]
        json participants
        datetime updated_at
    }
    comms__comms.proxy_messages {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer session_id [FK, NOT NULL]
        integer sender_id [NOT NULL]
        integer recipient_id [NOT NULL]
        string message_type
        text content [NOT NULL]
        boolean is_masked
        datetime read_at
        datetime created_at
    }
    comms__comms.proxy_messages }o--|| comms__proxy_sessions : has
    comms__comms.proxy_sessions {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer channel_id [FK, NOT NULL]
        integer participant_one_id [NOT NULL]
        integer participant_two_id [NOT NULL]
        datetime started_at
        datetime ended_at
        boolean is_encrypted
        json session_metadata
    }
    comms__comms.proxy_sessions }o--|| comms__proxy_channels : has
    comms__comms.support_ticket_replies {
        integer id [PK, NOT NULL]
        integer ticket_id [FK, NOT NULL]
        integer sender_id [FK, NOT NULL]
        text message [NOT NULL]
        datetime created_at
        string country_code
    }
    comms__comms.support_ticket_replies }o--|| comms__support_tickets : has
    comms__comms.support_ticket_replies ||--o{ accounts__users : has
    comms__comms.support_tickets {
        integer id [PK, NOT NULL]
        boolean is_deleted [NOT NULL]
        integer user_id [FK, NOT NULL]
        string subject [NOT NULL]
        string priority
        string status
        datetime created_at
        datetime updated_at
        string country_code
    }
    comms__comms.support_tickets ||--o{ accounts__users : has
    comms__comms.ticket_attachments {
        integer id [PK, NOT NULL]
        integer ticket_reply_id [FK]
        integer ticket_id [FK]
        string file_url
        datetime created_at
        string country_code
    }
    comms__comms.ticket_attachments }o--|| comms__support_ticket_replies : has
    comms__comms.ticket_attachments }o--|| comms__support_tickets : has
    comms__comms.ticket_messages {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer ticket_id [FK, NOT NULL]
        integer sender_id [NOT NULL]
        text message [NOT NULL]
        boolean is_admin
        datetime created_at
        string country_code [NOT NULL]
    }
    comms__comms.ticket_messages }o--|| comms__support_tickets : has
    comms__comms.video_room_participants {
        integer id [PK, NOT NULL]
        integer room_id [FK, NOT NULL]
        integer user_id [FK, NOT NULL]
        string role
        datetime joined_at
        datetime left_at
        boolean is_deleted [NOT NULL]
    }
    comms__comms.video_room_participants }o--|| comms__video_rooms : has
    comms__comms.video_room_participants ||--o{ accounts__users : has
    comms__comms.video_room_recordings {
        integer id [PK, NOT NULL]
        integer room_id [FK, NOT NULL]
        integer started_by_id [FK, NOT NULL]
        string recording_url
        integer duration_seconds
        string status
        datetime started_at
        datetime ended_at
        boolean is_deleted [NOT NULL]
    }
    comms__comms.video_room_recordings }o--|| comms__video_rooms : has
    comms__comms.video_room_recordings ||--o{ accounts__users : has
    comms__comms.video_rooms {
        integer id [PK, NOT NULL]
        string room_id [UK, NOT NULL]
        string room_uuid [UK]
        string name [NOT NULL]
        string country_code [FK]
        integer created_by_id [FK]
        boolean is_boardroom
        string status
        integer max_participants
        boolean recording_enabled
        boolean watermark_enabled
        boolean transcription_enabled
        datetime started_at
        datetime ended_at
        datetime created_at
        datetime updated_at
        boolean is_deleted [NOT NULL]
    }
    comms__comms.video_rooms }o--|| country__country_configs : has
    comms__comms.video_rooms ||--o{ accounts__users : has
    comms__comms.war_room_templates {
        integer id [PK, NOT NULL]
        string name [NOT NULL]
        string severity [NOT NULL]
        boolean auto_assign
        json template_data
        boolean is_deleted [NOT NULL]
        datetime created_at
    }
    country__country.country_basics {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer id [PK, NOT NULL]
        string code [UK, NOT NULL]
        string name [NOT NULL]
        string currency
        string currency_symbol
        string phone_code
        string language
        string timezone
        string date_format
        string status
        boolean is_active
        boolean is_deleted
        boolean is_default
        datetime created_at
        datetime updated_at
        string country_code [FK]
        integer created_by
        integer updated_by
        string official_name
        string alpha3
        string flag_url
        string currency_name
        numeric exchange_rate_to_usd
        string capital
        string region
        string subregion
        integer population
        numeric internet_penetration_pct
        numeric gdp_per_capita_usd
        numeric urbanization_pct
        numeric mobile_subs_per_100
        text public_holidays_json
        text macro_indicators_json
    }
    country__country.country_basics }o--|| country__country_configs : has
    country__country.country_category_tax_rates {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string country_code [FK, NOT NULL]
        integer category_id [NOT NULL]
        numeric tax_rate
        string tax_name
        string category_slug
        numeric rate
        boolean is_exempt
        boolean is_reduced
        text notes
        string source
        boolean is_active
        datetime created_at
    }
    country__country.country_category_tax_rates }o--|| country__country_configs : has
    country__country.country_cities {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string country_code [FK, NOT NULL]
        string name [NOT NULL]
        string name_local
        integer population
        boolean is_capital
        numeric latitude
        numeric longitude
        string postal_code_prefix
        string status
        boolean is_active
        string region
        integer sort_order
        string source
        datetime created_at
        datetime updated_at
    }
    country__country.country_cities }o--|| country__country_configs : has
    country__country.country_commission_rate_histories {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string country_code [NOT NULL]
        integer category_id
        string supplier_tier [NOT NULL]
        numeric rate_percent [NOT NULL]
        datetime effective_from [NOT NULL]
        datetime effective_to
        integer changed_by
        text change_reason
        datetime created_at
    }
    country__country.country_commission_rates {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string country_code [FK, NOT NULL]
        string supplier_tier [NOT NULL]
        string name [NOT NULL]
        numeric rate_percent [NOT NULL]
        numeric fixed_fee
        datetime effective_from
        datetime effective_to
    }
    country__country.country_commission_rates }o--|| country__country_configs : has
    country__country.country_communication_threads {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string country_code [NOT NULL]
        string entity_type [NOT NULL]
        integer entity_id [NOT NULL]
        text participants
        boolean is_active
        datetime last_message_at
        datetime created_at
    }
    country__country.country_communications {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string country_code [FK, NOT NULL]
        integer from_user_id
        integer to_user_id
        string subject [NOT NULL]
        text body [NOT NULL]
        string priority
        string category
        string status
        string related_entity_type
        integer related_entity_id
        datetime read_at
        text attachments_json
        datetime created_at
    }
    country__country.country_communications }o--|| country__country_configs : has
    country__country.country_config_versions {
        guid uuid [UK]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string country_code [FK, NOT NULL]
        string config_type [NOT NULL]
        integer version [NOT NULL]
        text payload_json [NOT NULL]
        string status
        integer draft_by
        integer approved_by
        datetime published_at
        datetime effective_from
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    country__country.country_config_versions }o--|| country__country_configs : has
    country__country.country_configs {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer basics_id [FK]
        string code [UK, NOT NULL]
        string name [NOT NULL]
        string currency
        string currency_symbol
        string phone_code
        string language
        string timezone
        string date_format
        string status
        boolean is_active
        boolean is_deleted
        boolean is_default
        datetime created_at
        datetime updated_at
        string official_name
        string alpha3
        string flag_url
        string currency_name
        numeric exchange_rate_to_usd
        string capital
        string region
        string subregion
        integer population
        numeric internet_penetration_pct
        numeric gdp_per_capita_usd
        numeric urbanization_pct
        numeric mobile_subs_per_100
        text public_holidays_json
        text macro_indicators_json
        string tax_type
        numeric tax_rate
        string tax_name
        boolean tax_inclusive
        text tax_exempt_categories_json
        text tax_reduced_rates_json
        string logistics_model
        string default_vehicle_type
        numeric base_rate
        numeric per_km_rate
        numeric minimum_charge
        numeric weight_surcharge_rate
        numeric weight_surcharge_threshold_kg
        text payment_methods_json
        text payment_gateways_json
        text logistics_providers_json
        text legal_rules_json
        text product_restrictions_json
        text address_format_json
        text regions_json
        text supplier_requirements_json
        text payout_settings_json
        text commission_tiers_json
        text suggested_gateway_rankings_json
        text suggested_commission_ranges_json
        text consumer_behavior_profile_json
        string economic_tier
        string fraud_risk_tier
        string suggested_logistics_model
        string data_residency_tier
        text data_residency_encrypted
        numeric confidence_score
        text audit_trail_json
        boolean cod_enabled
        numeric cod_max_amount
        boolean cod_verification_required
        integer cod_remittance_days
        integer settlement_hold_days
        numeric minimum_payout_amount
        string payout_currency
        string supplier_kyc_tier
        numeric supplier_onboarding_fee
        numeric supplier_monthly_fee
        numeric supplier_rating_threshold
        boolean legal_entity_required
        integer consumer_protection_days
        string data_privacy_framework
        numeric max_package_weight_kg
        string max_package_dimensions_cm
        numeric signature_required_threshold
        string measurement_system
        text working_days_json
        text supported_languages_json
        text payout_methods_json
        text logistics_zones_json
        string country_code [UK]
    }
    country__country.country_configs }o--|| country__country_basics : has
    country__country.country_economics {
        datetime deleted_at
        integer deleted_by
        integer id [PK, NOT NULL]
        string uuid [UK]
        integer version [NOT NULL]
        string country_code [UK, FK, NOT NULL]
        boolean is_active
        boolean is_deleted
        datetime created_at
        datetime updated_at
        integer created_by
        integer updated_by
        string economic_tier
        string fraud_risk_tier
        string suggested_logistics_model
        string data_residency_tier
        text data_residency_encrypted
        numeric confidence_score
        text audit_trail_json
        string cod_enabled
        numeric cod_max_amount
        string cod_verification_required
        integer cod_remittance_days
        integer settlement_hold_days
        numeric minimum_payout_amount
        string payout_currency
        string supplier_kyc_tier
        numeric supplier_onboarding_fee
        numeric supplier_monthly_fee
        numeric supplier_rating_threshold
        string legal_entity_required
        integer consumer_protection_days
        string data_privacy_framework
        numeric max_package_weight_kg
        string max_package_dimensions_cm
        numeric signature_required_threshold
        string measurement_system
        text working_days_json
        text supported_languages_json
        text payout_methods_json
        text logistics_zones_json
    }
    country__country.country_economics }o--|| country__country_configs : has
    country__country.country_feature_flags {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string country_code [FK, NOT NULL]
        string feature_key [NOT NULL]
        string feature_name
        boolean is_enabled
        text config
        string rollout_audience
        text notes
        datetime created_at
        datetime updated_at
    }
    country__country.country_feature_flags }o--|| country__country_configs : has
    country__country.country_gateway_configs {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string country_code [NOT NULL]
        string gateway_id [NOT NULL]
        string gateway_name [NOT NULL]
        boolean is_enabled
        integer priority
        text credentials
        string environment
        text settings
        datetime last_tested_at
        string last_test_result
        datetime created_at
        datetime updated_at
    }
    country__country.country_gateway_credentials {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string country_code [FK, NOT NULL]
        string gateway_name [NOT NULL]
        string environment
        json credentials
        boolean is_active
        datetime created_at [NOT NULL]
    }
    country__country.country_gateway_credentials }o--|| country__country_configs : has
    country__country.country_holiday_calendars {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string country_code [NOT NULL]
        datetime holiday_date [NOT NULL]
        string name [NOT NULL]
        string local_name
        boolean is_observed
        datetime created_at
    }
    country__country.country_legal_contracts {
        guid uuid [UK]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string country_code [NOT NULL]
        string contract_type [NOT NULL]
        string version
        text content_html [NOT NULL]
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    country__country.country_legals {
        datetime deleted_at
        integer deleted_by
        integer id [PK, NOT NULL]
        string uuid [UK]
        integer version [NOT NULL]
        string country_code [UK, FK, NOT NULL]
        boolean is_active
        boolean is_deleted
        datetime created_at
        datetime updated_at
        integer created_by
        integer updated_by
        string legal_entity_required
        integer consumer_protection_days
        string data_privacy_framework
        boolean gdpr_compliant
        boolean local_data_residency
        numeric compliance_score
        string legal_risk_tier
        text contract_templates_json
        text regulatory_bodies_json
    }
    country__country.country_legals }o--|| country__country_configs : has
    country__country.country_localizations {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string country_code [UK, NOT NULL]
        string default_numeral_system
        boolean hijri_calendar_enabled
        boolean rtl_layout_enabled
        string address_format
        datetime created_at
        datetime updated_at
    }
    country__country.country_logistics_zones {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string country_code [NOT NULL]
        string zone_code [NOT NULL]
        string zone_name [NOT NULL]
        string zone_type
        text cities
        text pricing_config
        boolean is_active
        datetime created_at
    }
    country__country.country_map_configs {
        integer id [PK, NOT NULL]
        string country_code [UK, FK, NOT NULL]
        string map_provider
        string api_key_ref
        integer default_zoom
        boolean show_regions
        boolean show_cities
        boolean is_deleted [NOT NULL]
        datetime created_at
        datetime updated_at
    }
    country__country.country_map_configs }o--|| country__country_configs : has
    country__country.country_payment_aliases {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string country_code [NOT NULL]
        string alias_type [NOT NULL]
        string alias_value [NOT NULL]
        boolean is_active
        datetime created_at
    }
    country__country.country_payout_rules {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string country_code [NOT NULL]
        string supplier_tier
        numeric min_amount
        numeric max_amount
        numeric fixed_fee
        numeric percent_fee
        integer settlement_days
        boolean is_active
        datetime created_at
    }
    country__country.country_staff_assignments {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer user_id [NOT NULL]
        string country_code [FK, NOT NULL]
        string role_in_country [NOT NULL]
        boolean is_active
        integer assigned_by
        text notes
        datetime created_at
        datetime updated_at
    }
    country__country.country_staff_assignments }o--|| country__country_configs : has
    country__country.country_taxes {
        datetime deleted_at
        integer deleted_by
        integer id [PK, NOT NULL]
        string uuid [UK, NOT NULL]
        string country_code [UK, FK, NOT NULL]
        boolean is_active
        boolean is_deleted
        integer version [NOT NULL]
        datetime created_at
        datetime updated_at
        integer created_by
        integer updated_by
        string tax_type
        numeric tax_rate
        string tax_name
        boolean tax_inclusive
        text tax_exempt_categories_json
        text tax_reduced_rates_json
    }
    country__country.country_taxes }o--|| country__country_configs : has
    country__country.data_residency_records {
        integer id [PK, NOT NULL]
        string country_code [FK, NOT NULL]
        string data_type [NOT NULL]
        string storage_location
        boolean cross_border_allowed
        string compliance_status
        datetime last_audit_at
        datetime next_audit_at
        boolean is_deleted [NOT NULL]
        datetime created_at
        datetime updated_at
    }
    country__country.data_residency_records }o--|| country__country_configs : has
    country__country.logistics_partner_kyc_requirements {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string country_code [UK, FK, NOT NULL]
        integer min_experience_months
        text required_documents
        boolean insurance_required
        numeric insurance_min_coverage
        text vehicle_requirements
        boolean background_check_required
        datetime created_at
        datetime updated_at
    }
    country__country.logistics_partner_kyc_requirements }o--|| country__country_configs : has
    country__country.logistics_partner_locations {
        integer id [PK, NOT NULL]
        integer partner_id [FK, NOT NULL]
        string country_code [FK, NOT NULL]
        string location_type
        float latitude
        float longitude
        text address
        boolean is_active
        boolean is_deleted [NOT NULL]
        datetime created_at
        datetime updated_at
    }
    country__country.logistics_partner_locations }o--|| logistics__logistics_partners : has
    country__country.logistics_partner_locations }o--|| country__country_configs : has
    country__country.oman_delivery_zones {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string zone_code [UK, NOT NULL]
        string zone_name [NOT NULL]
        text description
        numeric car_rate
        numeric van_rate
        numeric truck_rate
        numeric weight_surcharge_rate
        numeric weight_surcharge_threshold_kg
        text cities_json
        integer sort_order
        boolean is_active
        datetime created_at
    }
    country__country.parcel_location_trackers {
        integer id [PK, NOT NULL]
        integer parcel_id [FK, NOT NULL]
        string country_code [FK, NOT NULL]
        float latitude
        float longitude
        string location_name
        datetime timestamp
        boolean is_deleted [NOT NULL]
        datetime created_at
        datetime updated_at
    }
    country__country.parcel_location_trackers }o--|| logistics__shipments : has
    country__country.parcel_location_trackers }o--|| country__country_configs : has
    country__country.payment_orchestrator_syncs {
        integer id [PK, NOT NULL]
        string country_code [FK, NOT NULL]
        string gateway_id [NOT NULL]
        string gateway_name
        string environment
        boolean is_active
        numeric fee_percent
        numeric fee_fixed
        text supported_payment_methods
        datetime last_sync_at
        string status
        boolean is_deleted [NOT NULL]
        datetime created_at
        datetime updated_at
    }
    country__country.payment_orchestrator_syncs }o--|| country__country_configs : has
    country__country.shift_handover_logs {
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        string country_code [FK, NOT NULL]
        datetime shift_start [NOT NULL]
        datetime shift_end
        text notes
        integer handover_to_user_id [FK]
        text handover_notes
        boolean is_deleted [NOT NULL]
        datetime created_at
        datetime updated_at
    }
    country__country.shift_handover_logs ||--o{ accounts__users : has
    country__country.shift_handover_logs }o--|| country__country_configs : has
    country__country.shop_warehouse_locations {
        integer id [PK, NOT NULL]
        string country_code [FK, NOT NULL]
        string name [NOT NULL]
        string warehouse_code [NOT NULL]
        float latitude
        float longitude
        text address
        boolean is_active
        boolean is_deleted [NOT NULL]
        datetime created_at
        datetime updated_at
    }
    country__country.shop_warehouse_locations }o--|| country__country_configs : has
    country__country.supplier_kyc_requirements {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string country_code [UK, FK, NOT NULL]
        string kyc_tier_required [NOT NULL]
        text document_types_required
        integer verification_wait_days
        numeric auto_approve_threshold
        datetime created_at
        datetime updated_at
    }
    country__country.supplier_kyc_requirements }o--|| country__country_configs : has
    country__country.supplier_onboarding_syncs {
        integer id [PK, NOT NULL]
        string country_code [FK, NOT NULL]
        integer supplier_id [FK, NOT NULL]
        string kyc_status
        text kyc_documents
        boolean onboarding_fee_paid
        string monthly_fee_status
        string status
        text notes
        boolean is_deleted [NOT NULL]
        datetime created_at
        datetime updated_at
    }
    country__country.supplier_onboarding_syncs }o--|| country__country_configs : has
    country__country.supplier_onboarding_syncs ||--o{ accounts__users : has
    customers__customers.cross_country_customer_sessions {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer user_id [NOT NULL]
        string source_country_code [NOT NULL]
        string target_country_code [NOT NULL]
        text session_data
        boolean conversion
        integer order_id
        string ip_address
        string user_agent
        datetime created_at
    }
    customers__customers.referral_point_events {
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        string event_type [NOT NULL]
        integer points [NOT NULL]
        integer referred_user_id [FK]
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    customers__customers.referral_point_events ||--o{ accounts__users : has
    customers__customers.referrals {
        integer id [PK, NOT NULL]
        integer referrer_id [FK, NOT NULL]
        integer referred_id [UK, FK, NOT NULL]
        string referral_code [UK]
        string status
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    customers__customers.referrals ||--o{ accounts__users : has
    public__employee_trainings {
        integer id [PK, NOT NULL]
        integer employee_id [FK, NOT NULL]
        string module_id [FK, NOT NULL]
        string status
        float score
        datetime completed_at
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    public__employee_trainings ||--o{ hr__employees : has
    public__employee_trainings ||--o{ hr__training_modules : has
    finance__finance.account_balances {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime created_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        integer account_id [FK, NOT NULL]
        integer user_id [FK]
        numeric balance
        string currency
        integer last_entry_id
        datetime last_entry_at
        datetime last_updated
        datetime updated_at
        string country_code
    }
    finance__finance.account_balances ||--o{ finance__accounts : has
    finance__finance.account_balances ||--o{ accounts__users : has
    finance__finance.account_groups {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        string code [UK, NOT NULL]
        string name [NOT NULL]
        text description
        string account_type [NOT NULL]
        string normal_side [NOT NULL]
        integer display_order
        datetime created_at
        string country_code
    }
    finance__finance.accounts {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        integer group_id [FK]
        string code [UK, NOT NULL]
        string name [NOT NULL]
        string normal_side [NOT NULL]
        string currency
        boolean is_active
        integer display_order
        datetime created_at
        string country_code
    }
    finance__finance.accounts ||--o{ finance__account_groups : has
    finance__finance.accruals {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        string accrual_type [NOT NULL]
        string description
        numeric amount [NOT NULL]
        string expense_account_code [NOT NULL]
        string accrual_account_code [NOT NULL]
        datetime accrual_date [NOT NULL]
        datetime reversal_date
        string status
        integer journal_entry_id [FK]
        integer reversal_entry_id [FK]
        string country_code
        integer created_by_id [FK]
        datetime created_at
    }
    finance__finance.accruals }o--|| finance__journal_entries : has
    finance__finance.accruals ||--o{ accounts__users : has
    finance__finance.ap_bills {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        integer vendor_id [FK, NOT NULL]
        string bill_number
        datetime bill_date [NOT NULL]
        datetime due_date
        string account_code [NOT NULL]
        numeric amount [NOT NULL]
        numeric tax_amount
        text description
        string status
        integer linked_journal_entry_id [FK]
        integer paid_journal_entry_id [FK]
        string country_code
        integer created_by_id [FK]
        datetime created_at
        datetime updated_at
    }
    finance__finance.ap_bills }o--|| finance__vendors : has
    finance__finance.ap_bills }o--|| finance__journal_entries : has
    finance__finance.ap_bills ||--o{ accounts__users : has
    finance__finance.ap_ledger_entries {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        integer deleted_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        integer supplier_id [FK, NOT NULL]
        integer order_id [FK]
        integer invoice_id [FK]
        integer settlement_id [FK]
        string reference_type
        integer reference_id
        string entry_type [NOT NULL]
        numeric amount [NOT NULL]
        numeric balance_after
        string currency
        string status
        datetime due_date
        datetime paid_at
        text description
        integer created_by_id [FK]
        datetime created_at
        string country_code
        boolean is_deleted
        datetime deleted_at
    }
    finance__finance.ap_ledger_entries ||--o{ accounts__users : has
    finance__finance.ap_ledger_entries }o--|| orders__orders : has
    finance__finance.ap_ledger_entries }o--|| finance__invoices : has
    finance__finance.ap_ledger_entries }o--|| finance__supplier_settlements : has
    finance__finance.ar_invoices {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        integer customer_id [FK, NOT NULL]
        string invoice_number
        datetime invoice_date [NOT NULL]
        datetime due_date
        string account_code
        numeric amount [NOT NULL]
        numeric tax_amount
        text description
        string status
        integer linked_journal_entry_id [FK]
        integer paid_journal_entry_id [FK]
        string country_code
        integer created_by_id [FK]
        datetime created_at
        datetime updated_at
    }
    finance__finance.ar_invoices ||--o{ finance__customers : has
    finance__finance.ar_invoices }o--|| finance__journal_entries : has
    finance__finance.ar_invoices ||--o{ accounts__users : has
    finance__finance.ar_ledger_entries {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        integer deleted_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        integer customer_id [FK, NOT NULL]
        integer order_id [FK]
        integer invoice_id [FK]
        string reference_type
        integer reference_id
        string entry_type [NOT NULL]
        numeric amount [NOT NULL]
        numeric balance_after
        string currency
        string status
        datetime due_date
        datetime settled_at
        text description
        integer created_by_id [FK]
        datetime created_at
        string country_code
        boolean is_deleted
        datetime deleted_at
    }
    finance__finance.ar_ledger_entries ||--o{ accounts__users : has
    finance__finance.ar_ledger_entries }o--|| orders__orders : has
    finance__finance.ar_ledger_entries }o--|| finance__invoices : has
    finance__finance.automation_logs {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer id [PK, NOT NULL]
        integer rule_id [FK, NOT NULL]
        string status
        text message
        integer records_affected
        string country_code
        datetime created_at
        datetime updated_at
        integer created_by_id
        integer updated_by
    }
    finance__finance.automation_logs ||--o{ finance__automation_rules : has
    finance__finance.automation_rules {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        string name [NOT NULL]
        text description
        string rule_type
        string trigger
        string action
        text config
        boolean is_active
        string country_code
        datetime created_at
        datetime updated_at
    }
    finance__finance.bank_accounts {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        string bank_name [NOT NULL]
        string account_name
        string account_number
        string iban
        string swift_bic
        string currency
        string gl_account_code
        string country_code
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    finance__finance.bank_mapping_rules {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        string country_code
        string name [NOT NULL]
        string match_pattern [NOT NULL]
        string description_contains
        string account_code [NOT NULL]
        string normal_side [NOT NULL]
        string category
        integer priority
        boolean is_active
        integer created_by_id [FK]
        datetime created_at
        datetime updated_at
    }
    finance__finance.bank_mapping_rules ||--o{ accounts__users : has
    finance__finance.bank_reconciliations {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        integer statement_line_id [FK, NOT NULL]
        integer journal_entry_id [FK]
        numeric matched_amount
        string status
        text note
        integer matched_by_id [FK]
        datetime matched_at
        string country_code
    }
    finance__finance.bank_reconciliations ||--o{ finance__bank_statement_lines : has
    finance__finance.bank_reconciliations }o--|| finance__journal_entries : has
    finance__finance.bank_reconciliations ||--o{ accounts__users : has
    finance__finance.bank_statement_imports {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        string bank_name
        string file_name
        datetime statement_period_start
        datetime statement_period_end
        string currency
        integer total_lines
        integer matched_lines
        integer unmatched_lines
        string status
        integer imported_by_id [FK]
        string country_code
        datetime created_at
    }
    finance__finance.bank_statement_imports ||--o{ accounts__users : has
    finance__finance.bank_statement_lines {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        integer import_id [FK, NOT NULL]
        datetime txn_date
        string description
        string reference
        numeric amount [NOT NULL]
        string mapped_account_code
        string mapped_side
        integer mapping_rule_id [FK]
        string status
        integer posted_journal_entry_id [FK]
        integer reconciled_transaction_id [FK]
        string country_code
        datetime created_at
    }
    finance__finance.bank_statement_lines ||--o{ finance__bank_statement_imports : has
    finance__finance.bank_statement_lines ||--o{ finance__bank_mapping_rules : has
    finance__finance.bank_statement_lines }o--|| finance__journal_entries : has
    finance__finance.bank_statement_lines ||--o{ finance__bank_transactions : has
    finance__finance.bank_transactions {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        string transaction_ref
        string source
        string transaction_type [NOT NULL]
        string category
        numeric amount [NOT NULL]
        string currency
        text description
        integer linked_order_id [FK]
        integer linked_supplier_id [FK]
        integer linked_logistics_id
        integer linked_payout_id
        integer linked_refund_id
        boolean reconciled
        integer reconciled_by_id [FK]
        datetime reconciled_at
        datetime transaction_date
        string status
        datetime created_at
        string country_code
        boolean flagged
        text flag_reason
    }
    finance__finance.bank_transactions }o--|| orders__orders : has
    finance__finance.bank_transactions ||--o{ accounts__users : has
    finance__finance.budgets {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        string account_code [NOT NULL]
        integer fiscal_period_id [FK, NOT NULL]
        numeric amount [NOT NULL]
        string currency
        string country_code
        text notes
        integer created_by_id [FK]
        datetime created_at
        datetime updated_at
    }
    finance__finance.budgets }o--|| finance__fiscal_periods : has
    finance__finance.budgets ||--o{ accounts__users : has
    finance__finance.cash_accounts {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        string name [NOT NULL]
        string account_type [NOT NULL]
        string currency
        numeric balance
        text description
        boolean is_active
        integer created_by_id [FK]
        datetime created_at
        datetime updated_at
        string country_code
    }
    finance__finance.cash_accounts ||--o{ accounts__users : has
    finance__finance.cash_flow_forecasts {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        datetime forecast_date [NOT NULL]
        datetime period_start [NOT NULL]
        datetime period_end [NOT NULL]
        numeric net_cash_flow
        numeric opening_balance
        numeric closing_balance
        string country_code
        datetime created_at
    }
    finance__finance.cash_position_snapshots {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        datetime snapshot_time [NOT NULL]
        integer account_id [FK, NOT NULL]
        numeric balance
        string currency
        string country_code
        datetime created_at
    }
    finance__finance.cash_position_snapshots }o--|| finance__treasury_accounts : has
    finance__finance.cash_transactions {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        integer account_id [FK, NOT NULL]
        string transaction_type [NOT NULL]
        numeric amount [NOT NULL]
        numeric balance_after
        text description
        string reference
        string category
        integer performed_by_id [FK]
        datetime created_at
        string country_code
    }
    finance__finance.cash_transactions ||--o{ finance__cash_accounts : has
    finance__finance.cash_transactions ||--o{ accounts__users : has
    finance__finance.commission_agreements {
        string uuid [UK, NOT NULL]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer supplier_id [FK, NOT NULL]
        string country_code [NOT NULL]
        string tier [NOT NULL]
        numeric rate [NOT NULL]
        integer set_by_admin_id [FK]
        boolean is_active [NOT NULL]
        datetime effective_from
        datetime effective_to
        text note
        datetime created_at
        datetime updated_at
    }
    finance__finance.commission_agreements ||--o{ accounts__users : has
    finance__finance.commission_category_rates {
        string uuid [UK, NOT NULL]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer category_id [FK]
        string category_slug
        string category_display_name
        string country_code [FK]
        numeric rate_percent [NOT NULL]
        boolean is_active [NOT NULL]
        datetime created_at
        datetime updated_at
    }
    finance__finance.commission_category_rates ||--o{ catalog__categories : has
    finance__finance.commission_category_rates ||--o{ country__country_configs : has
    finance__finance.commission_ledger_entries {
        string uuid [UK, NOT NULL]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer supplier_id [FK, NOT NULL]
        integer order_id [FK]
        integer order_item_id [FK]
        integer product_id [FK]
        string category_slug
        string badge_level
        numeric global_default_rate
        numeric category_rate
        numeric badge_rate
        numeric override_rate
        numeric applied_rate
        string calculation_method
        numeric order_value
        numeric commission_pct
        boolean cap_applied
        numeric commission_amount
        boolean low_value_threshold_used
        boolean fixed_cap_used
        boolean override_flag
        boolean is_adjusted
        string currency
        numeric amount
        integer adjusted_by_id [FK]
        string status
        datetime credited_at
        datetime created_at
        datetime updated_at
        string country_code
    }
    finance__finance.commission_ledger_entries ||--o{ accounts__users : has
    finance__finance.commission_ledger_entries }o--|| orders__orders : has
    finance__finance.commission_ledger_entries }o--|| orders__order_items : has
    finance__finance.commission_ledger_entries ||--o{ catalog__products : has
    finance__finance.cost_centers {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        string code [NOT NULL]
        string name [NOT NULL]
        string country_code
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    finance__finance.customers {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        string name [NOT NULL]
        string tax_id
        string contact_email
        string currency
        integer payment_terms_days
        numeric credit_limit
        string country_code
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    finance__finance.finance_audit_logs {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        string action [NOT NULL]
        integer actor_id [FK]
        string actor_role
        string entity_type
        integer entity_id
        string country_code
        json detail
        datetime created_at
    }
    finance__finance.finance_audit_logs ||--o{ accounts__users : has
    finance__finance.finance_automation_logs {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        string kind [NOT NULL]
        integer records_processed
        integer records_changed
        json detail
        integer run_by_id [FK]
        string country_code
        datetime created_at
    }
    finance__finance.finance_automation_logs ||--o{ accounts__users : has
    finance__finance.financial_reports {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at [NOT NULL]
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        string report_type [NOT NULL]
        datetime period_start [NOT NULL]
        datetime period_end [NOT NULL]
        string country_code
        json data
        datetime generated_at
        boolean is_deleted
        datetime deleted_at
    }
    finance__finance.fiscal_periods {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        string country_code [NOT NULL]
        integer period_year [NOT NULL]
        integer period_month [NOT NULL]
        datetime period_start [NOT NULL]
        datetime period_end [NOT NULL]
        string status
        boolean is_locked
        datetime closed_at
        integer closed_by_id [FK]
        text notes
        datetime created_at
    }
    finance__finance.fiscal_periods ||--o{ accounts__users : has
    finance__finance.fixed_assets {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        string name [NOT NULL]
        string asset_code
        string category
        datetime purchase_date [NOT NULL]
        numeric purchase_cost [NOT NULL]
        numeric salvage_value
        integer useful_life_months [NOT NULL]
        numeric accumulated_depreciation
        datetime last_depreciated_date
        string asset_account_code
        string depreciation_account_code
        string accumulated_depr_account_code
        string status
        string country_code
        integer created_by_id [FK]
        datetime created_at
        datetime updated_at
    }
    finance__finance.fixed_assets ||--o{ accounts__users : has
    finance__finance.gateway_settlement_schedules {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        integer gateway_id [FK, NOT NULL]
        datetime settlement_date [NOT NULL]
        numeric amount [NOT NULL]
        string currency
        string status
        string country_code
        datetime created_at
    }
    finance__finance.gateway_settlement_schedules }o--|| finance__payment_gateway_connections : has
    finance__finance.invoice_items {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        integer invoice_id [FK, NOT NULL]
        integer product_id [FK]
        string description [NOT NULL]
        integer quantity
        numeric unit_price [NOT NULL]
        numeric discount_amount
        numeric tax_rate
        numeric line_total
        datetime created_at
        string country_code
    }
    finance__finance.invoice_items }o--|| finance__invoices : has
    finance__finance.invoice_items ||--o{ catalog__products : has
    finance__finance.invoices {
        guid uuid [UK]
        integer version [NOT NULL]
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        integer order_id [FK, NOT NULL]
        integer shipment_id [FK]
        integer supplier_id [FK]
        string invoice_number [UK]
        string invoice_type
        numeric subtotal
        numeric tax_amount
        numeric shipping_amount
        numeric discount_amount
        numeric total_amount
        string currency
        string status
        datetime issued_at
        datetime due_at
        datetime picked_at
        datetime dispatched_at
        datetime delivered_at
        datetime paid_at
        text notes
        datetime created_at
        datetime updated_at
        string country_code
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id [FK]
    }
    finance__finance.invoices }o--|| orders__orders : has
    finance__finance.invoices }o--|| logistics__shipments : has
    finance__finance.invoices ||--o{ accounts__users : has
    finance__finance.journal_entries {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        integer updated_by
        integer id [PK, NOT NULL]
        datetime entry_date [NOT NULL]
        string reference_number [UK, NOT NULL]
        text description
        string source
        string country_code
        string currency
        boolean is_reconciled
        integer created_by_id [FK]
        string reference_type
        integer reference_id
        integer period_id [FK]
        integer reversal_of_id [FK]
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id [FK]
        datetime created_at
    }
    finance__finance.journal_entries ||--o{ accounts__users : has
    finance__finance.journal_entries }o--|| finance__fiscal_periods : has
    finance__finance.journal_entries }o--|| finance__journal_entries : has
    finance__finance.journal_entry_lines {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        integer entry_id [FK, NOT NULL]
        integer account_id [FK, NOT NULL]
        integer cost_center_id [FK]
        numeric amount [NOT NULL]
        string side [NOT NULL]
        text description
        string entity_type
        integer entity_id
        datetime created_at
        string country_code
    }
    finance__finance.journal_entry_lines }o--|| finance__journal_entries : has
    finance__finance.journal_entry_lines ||--o{ finance__accounts : has
    finance__finance.journal_entry_lines ||--o{ finance__cost_centers : has
    finance__finance.logistics_partner_payouts {
        integer id [PK, NOT NULL]
        boolean is_deleted [NOT NULL]
        integer partner_id [FK, NOT NULL]
        numeric amount [NOT NULL]
        string currency
        datetime period_start
        datetime period_end
        string status
        string reference_id
        datetime processed_at
        string country_code [FK]
        datetime created_at [NOT NULL]
        datetime updated_at
        string method
        text notes
    }
    finance__finance.logistics_partner_payouts }o--|| logistics__logistics_partners : has
    finance__finance.logistics_partner_payouts ||--o{ country__country_configs : has
    finance__finance.payment_gateway_connections {
        integer id [PK, NOT NULL]
        boolean is_deleted [NOT NULL]
        string provider_code [NOT NULL]
        string gateway_name [NOT NULL]
        string country_code [NOT NULL]
        string environment
        boolean is_active
        json credentials
        json fee_config
        json supported_methods
        datetime last_sync_at
        string provider_kind [NOT NULL]
        string display_name [NOT NULL]
        boolean is_enabled
        boolean supports_customer_checkout
        boolean supports_payouts
        string payment_mode [NOT NULL]
        string public_key
        string secret_key
        string webhook_secret
        string merchant_id
        string api_base_url
        string webhook_url
        string test_url
        string settlement_cycle
        text supported_currencies_json
        text extra_config_json
        text notes
        numeric fee_percent [NOT NULL]
        numeric fixed_fee_amount [NOT NULL]
        numeric payout_fee_percent [NOT NULL]
        numeric payout_fixed_fee_amount [NOT NULL]
        boolean pass_fee_to_customer
        string test_status [NOT NULL]
        string test_message
        datetime last_tested_at
        integer updated_by_id [FK]
        boolean adapter_supported
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    finance__finance.payment_gateway_connections ||--o{ accounts__users : has
    finance__finance.payment_reconciliation_runs {
        integer id [PK, NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime run_date [NOT NULL]
        numeric total_amount
        integer reconciled_count
        integer unmatched_count
        integer processed_count
        integer stale_pending_orders
        integer recent_webhook_count
        text result_json
        datetime started_at
        datetime completed_at
        string status
        string country_code
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    finance__finance.payments {
        integer id [PK, NOT NULL]
        boolean is_deleted [NOT NULL]
        integer order_id [FK, NOT NULL]
        numeric amount [NOT NULL]
        string payment_method [NOT NULL]
        string provider
        string status
        string intent_id
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code [FK]
        text layout_json
    }
    finance__finance.payments }o--|| orders__orders : has
    finance__finance.payments ||--o{ country__country_configs : has
    finance__finance.payout_batch_items {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        integer batch_id [FK, NOT NULL]
        string entity_type [NOT NULL]
        integer entity_id [NOT NULL]
        numeric amount [NOT NULL]
        string currency
        string reference
        string status
        string country_code
    }
    finance__finance.payout_batch_items }o--|| finance__payout_batches : has
    finance__finance.payout_batches {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        string batch_number [UK, NOT NULL]
        string country_code [NOT NULL]
        numeric total_amount
        integer item_count
        string status
        integer created_by_id [FK, NOT NULL]
        integer approved_by_id [FK]
        datetime dispatched_at
        datetime settled_at
        text notes
        datetime created_at
        datetime updated_at
    }
    finance__finance.payout_batches ||--o{ accounts__users : has
    finance__finance.payout_rule_categories {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string country_code [FK, NOT NULL]
        string category_slug [NOT NULL]
        numeric payout_rate [NOT NULL]
        numeric min_amount
        numeric max_amount
        boolean is_active
        datetime created_at
    }
    finance__finance.payout_rule_categories ||--o{ country__country_configs : has
    finance__finance.payout_rule_products {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string country_code [FK, NOT NULL]
        integer product_id [NOT NULL]
        numeric payout_rate [NOT NULL]
        numeric min_amount
        numeric max_amount
        boolean is_active
        datetime created_at
    }
    finance__finance.payout_rule_products ||--o{ country__country_configs : has
    finance__finance.payout_rules {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string country_code [FK, NOT NULL]
        numeric min_amount
        numeric max_amount
        numeric fixed_fee
        numeric percent_fee
        boolean is_active
        datetime created_at
    }
    finance__finance.payout_rules ||--o{ country__country_configs : has
    finance__finance.payouts {
        integer id [PK, NOT NULL]
        boolean is_deleted [NOT NULL]
        string batch_number
        integer order_id [FK]
        integer supplier_id [FK, NOT NULL]
        numeric amount [NOT NULL]
        string currency
        string method [NOT NULL]
        string status
        string reference_id
        string reference
        string provider
        string provider_recipient_id
        string provider_transfer_id
        string provider_status
        text notes
        datetime processed_at
        string country_code [FK]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    finance__finance.payouts }o--|| orders__orders : has
    finance__finance.payouts ||--o{ accounts__users : has
    finance__finance.payouts ||--o{ country__country_configs : has
    finance__finance.pending_journal_entries {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        text lines_json [NOT NULL]
        text description
        string source
        string country_code
        datetime entry_date [NOT NULL]
        boolean amount_threshold_triggered
        string status
        integer created_by_id [FK, NOT NULL]
        integer approved_by_id [FK]
        integer rejected_by_id [FK]
        text rejection_reason
        datetime approved_at
        integer journal_entry_id [FK]
        datetime created_at
    }
    finance__finance.pending_journal_entries ||--o{ accounts__users : has
    finance__finance.pending_journal_entries }o--|| finance__journal_entries : has
    finance__finance.product_commission_overrides {
        string uuid [UK, NOT NULL]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer product_id [FK, NOT NULL]
        integer supplier_id [FK, NOT NULL]
        numeric rate_percent [NOT NULL]
        integer set_by_admin_id [FK]
        boolean is_active [NOT NULL]
        string country_code
        datetime created_at
        datetime updated_at
    }
    finance__finance.product_commission_overrides ||--o{ catalog__products : has
    finance__finance.product_commission_overrides ||--o{ accounts__users : has
    finance__finance.recurring_templates {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        string name [NOT NULL]
        string frequency
        datetime next_run_date
        text description
        json lines [NOT NULL]
        string currency
        string country_code
        boolean is_active
        integer created_by_id [FK]
        datetime created_at
        datetime updated_at
    }
    finance__finance.recurring_templates ||--o{ accounts__users : has
    finance__finance.refund_ledgers {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        integer order_id [FK, NOT NULL]
        integer return_request_id [FK]
        integer ledger_id
        integer bank_transaction_id
        text reason
        text refund_reason
        string refund_method
        numeric customer_refund_amount
        numeric supplier_reversal
        numeric logistics_reversal
        numeric delivery_fee_reversal
        numeric commission_reversal
        numeric vat_adjustment
        numeric vat_reversal
        integer performed_by_id [FK]
        datetime processed_at
        string currency
        string status
        datetime created_at
        string country_code
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id [FK]
    }
    finance__finance.refund_ledgers }o--|| orders__orders : has
    finance__finance.refund_ledgers }o--|| orders__return_requests : has
    finance__finance.refund_ledgers ||--o{ accounts__users : has
    finance__finance.scanned_expenses {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        integer employee_id [FK]
        string vendor_name
        string invoice_number
        datetime expense_date
        numeric amount [NOT NULL]
        string currency
        numeric tax_amount
        string category
        text description
        string expense_account_code
        string image_url
        text ocr_raw_text
        numeric ocr_confidence
        string status
        integer posted_journal_entry_id [FK]
        integer reviewed_by_id [FK]
        string country_code
        datetime created_at
        datetime updated_at
    }
    finance__finance.scanned_expenses }o--|| hr__employees : has
    finance__finance.scanned_expenses }o--|| finance__journal_entries : has
    finance__finance.scanned_expenses ||--o{ accounts__users : has
    finance__finance.supplier_settlements {
        guid uuid [UK]
        integer version [NOT NULL]
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        integer supplier_id [FK, NOT NULL]
        integer order_id [FK]
        integer ledger_id [FK]
        integer payout_id [FK]
        integer shipment_id [FK]
        numeric gross_amount [NOT NULL]
        numeric commission_amount
        numeric commission_deducted
        numeric commission_rate
        numeric vat_on_commission
        numeric net_amount [NOT NULL]
        string status
        datetime settled_at
        datetime eligible_at
        integer bank_transaction_id
        string currency
        datetime created_at
        datetime updated_at
        string country_code
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id [FK]
    }
    finance__finance.supplier_settlements ||--o{ accounts__users : has
    finance__finance.supplier_settlements }o--|| orders__orders : has
    finance__finance.supplier_settlements }o--|| finance__transaction_ledgers : has
    finance__finance.supplier_settlements }o--|| finance__payouts : has
    finance__finance.supplier_settlements }o--|| logistics__shipments : has
    finance__finance.tax_rules {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string country_code [FK, NOT NULL]
        string tax_name [NOT NULL]
        numeric tax_rate [NOT NULL]
        boolean is_active
        datetime created_at
    }
    finance__finance.tax_rules ||--o{ country__country_configs : has
    finance__finance.transaction_ledgers {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        integer user_id [FK]
        integer supplier_id [FK]
        integer logistics_partner_id [FK]
        integer order_id [FK]
        integer order_item_id [FK]
        integer shipment_id [FK]
        string payment_method
        numeric product_subtotal
        numeric discount_amount
        numeric delivery_pickup_charge
        numeric delivery_dropoff_charge
        numeric delivery_total
        numeric vat_amount
        numeric zozi_commission_rate
        numeric zozi_commission
        numeric net_supplier_amount
        numeric net_logistics_amount
        numeric net_zozi_amount
        numeric cod_collected_amount
        numeric cod_remittance_due
        string settlement_status
        string currency
        string transaction_type
        string reference_id
        numeric balance_after
        text notes
        numeric amount
        string country_code
        datetime created_at
        datetime updated_at
    }
    finance__finance.transaction_ledgers ||--o{ accounts__users : has
    finance__finance.transaction_ledgers }o--|| logistics__logistics_partners : has
    finance__finance.transaction_ledgers }o--|| orders__orders : has
    finance__finance.transaction_ledgers }o--|| orders__order_items : has
    finance__finance.transaction_ledgers }o--|| logistics__shipments : has
    finance__finance.treasury_accounts {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        string slug [UK, NOT NULL]
        string name [NOT NULL]
        string account_type [NOT NULL]
        string currency
        string gl_account_code [NOT NULL]
        text description
        integer employee_id [FK]
        numeric balance
        boolean is_active
        string country_code
        datetime created_at
        datetime updated_at
    }
    finance__finance.treasury_accounts }o--|| hr__employees : has
    finance__finance.treasury_transactions {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        integer from_account_id [FK]
        integer to_account_id [FK]
        integer account_id [FK]
        string transaction_type [NOT NULL]
        numeric amount [NOT NULL]
        string currency
        string reference
        text description
        datetime posted_at
        string country_code
    }
    finance__finance.treasury_transactions }o--|| finance__treasury_accounts : has
    finance__finance.vat_remittances {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        datetime period_start [NOT NULL]
        datetime period_end [NOT NULL]
        numeric vat_collected_amount
        numeric vat_adjustment_amount
        numeric amount_due
        numeric amount [NOT NULL]
        numeric amount_remitted
        string currency
        integer bank_transaction_id
        integer remitted_by_id [FK]
        datetime remitted_at
        text notes
        string status
        datetime created_at
        string country_code
    }
    finance__finance.vat_remittances ||--o{ accounts__users : has
    finance__finance.vendors {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        string name [NOT NULL]
        string tax_id
        string contact_email
        string currency
        integer payment_terms_days
        string country_code
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    governance__governance.admin_activity_logs {
        integer id [PK, NOT NULL]
        integer admin_id [FK, NOT NULL]
        string action [NOT NULL]
        json details
        string ip_address
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    governance__governance.admin_activity_logs ||--o{ accounts__users : has
    governance__governance.admin_analytics_snapshots {
        integer id [PK, NOT NULL]
        string snapshot_key [NOT NULL]
        string snapshot_group [NOT NULL]
        string period
        text payload_json [NOT NULL]
        datetime computed_at [NOT NULL]
        datetime expires_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        string country_code
    }
    governance__governance.admin_change_audit_logs {
        integer id [PK, NOT NULL]
        integer admin_id [FK, NOT NULL]
        string action [NOT NULL]
        string entity [NOT NULL]
        string entity_key
        text before_json
        text after_json
        text notes
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    governance__governance.admin_change_audit_logs ||--o{ accounts__users : has
    governance__governance.api_keys {
        integer id [PK, NOT NULL]
        string name [NOT NULL]
        string key_hash [NOT NULL]
        json permissions
        boolean is_active
        datetime expires_at
        integer created_by_id [FK]
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    governance__governance.api_keys ||--o{ accounts__users : has
    governance__governance.badge_billing_records {
        integer id [PK, NOT NULL]
        integer user_id [FK]
        integer supplier_id [FK]
        string billing_reference [UK]
        string badge_level
        string charge_type
        string charge_source
        numeric amount [NOT NULL]
        string currency
        string status
        string reference_id
        datetime period_start
        datetime period_end
        datetime due_at
        datetime billed_at
        datetime paid_at
        string payment_method
        text notes
        integer created_by_id
        integer bank_transaction_id [FK]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
        boolean is_deleted [NOT NULL]
    }
    governance__governance.badge_billing_records ||--o{ accounts__users : has
    governance__governance.badge_billing_records ||--o{ finance__bank_transactions : has
    governance__governance.badge_tiers {
        integer id [PK, NOT NULL]
        string name [NOT NULL]
        integer min_points [NOT NULL]
        json benefits
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    governance__governance.badge_transactions {
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        numeric amount [NOT NULL]
        string transaction_type [NOT NULL]
        string reference_id
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    governance__governance.badge_transactions ||--o{ accounts__users : has
    governance__governance.chatbot_query_events {
        integer id [PK, NOT NULL]
        integer user_id [FK]
        string session_id [NOT NULL]
        string event_type [NOT NULL]
        text message
        string normalized_query
        string intent
        text filters_json
        integer result_count [NOT NULL]
        text product_ids_json
        integer clicked_product_id [FK]
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    governance__governance.chatbot_query_events ||--o{ accounts__users : has
    governance__governance.chatbot_query_events ||--o{ catalog__products : has
    governance__governance.commission_badge_tiers {
        integer id [PK, NOT NULL]
        string name [NOT NULL]
        string badge_level [UK, NOT NULL]
        numeric commission_rate [NOT NULL]
        numeric setup_fee
        numeric recurring_fee
        string recurring_interval
        text benefits_json
        integer min_fulfilled_orders
        numeric min_monthly_revenue
        integer sort_order
        boolean is_active
        boolean is_deleted [NOT NULL]
        integer updated_by_id [FK]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    governance__governance.commission_badge_tiers ||--o{ accounts__users : has
    governance__governance.commission_global_configs {
        integer id [PK, NOT NULL]
        numeric default_rate
        numeric low_value_threshold
        numeric fixed_cap_amount
        boolean fixed_cap_enabled
        boolean margin_protection_enabled
        numeric margin_threshold
        boolean is_deleted [NOT NULL]
        integer updated_by_id [FK]
        datetime updated_at
        datetime created_at [NOT NULL]
        string country_code
    }
    governance__governance.commission_global_configs ||--o{ accounts__users : has
    governance__governance.email_provider_configs {
        integer id [PK, NOT NULL]
        string provider
        boolean is_active
        integer updated_by_id [FK]
        datetime created_at [NOT NULL]
        datetime updated_at
        string email_from_default
        string email_from_promotional
        string email_from_transactional
        string email_from_notification
        string email_from_alert
        string email_from_verification
        string email_from_login_verification
        string email_from_password_reset
        string resend_api_key
        string resend_webhook_secret
        string smtp_host
        integer smtp_port
        string smtp_username
        string smtp_password
        boolean smtp_use_tls
        boolean smtp_use_ssl
        integer smtp_timeout_seconds
        boolean is_deleted [NOT NULL]
        string country_code
    }
    governance__governance.email_provider_configs ||--o{ accounts__users : has
    governance__governance.employee_expenses {
        integer id [PK, NOT NULL]
        integer employee_id [FK, NOT NULL]
        string expense_type [NOT NULL]
        numeric amount [NOT NULL]
        text description
        string status
        integer approved_by_id [FK]
        datetime approved_at
        string receipt_url
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    governance__governance.employee_expenses }o--|| hr__employees : has
    governance__governance.employee_expenses ||--o{ accounts__users : has
    governance__governance.finance_bank_accounts {
        integer id [PK, NOT NULL]
        string account_name
        string account_number [NOT NULL]
        string bank_name [NOT NULL]
        string account_label
        string branch_name
        string iban
        string swift_code
        string routing_number
        string currency
        string support_email
        string support_phone
        string remittance_reference_prefix
        text instructions
        boolean is_active
        string scope
        integer created_by_id [FK]
        integer updated_by_id [FK]
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    governance__governance.finance_bank_accounts ||--o{ accounts__users : has
    governance__governance.legal_contract_templates {
        integer id [PK, NOT NULL]
        string country_code [FK, NOT NULL]
        string template_type [NOT NULL]
        string version
        text content [NOT NULL]
        boolean is_active
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    governance__governance.legal_contract_templates ||--o{ country__country_configs : has
    governance__governance.logistics_cod_remittance_receipts {
        integer id [PK, NOT NULL]
        integer partner_id [FK]
        integer shipment_id [FK]
        integer settlement_id [FK]
        numeric amount [NOT NULL]
        string bank_reference
        string receipt_file_url
        text notes
        text review_note
        integer reviewed_by_id [FK]
        string status
        string currency
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    governance__governance.logistics_cod_remittance_receipts }o--|| logistics__logistics_partners : has
    governance__governance.logistics_cod_remittance_receipts }o--|| logistics__shipments : has
    governance__governance.logistics_cod_remittance_receipts }o--|| governance__logistics_settlements : has
    governance__governance.logistics_cod_remittance_receipts ||--o{ accounts__users : has
    governance__governance.logistics_partner_documents {
        integer id [PK, NOT NULL]
        integer partner_id [FK, NOT NULL]
        string doc_type [NOT NULL]
        string file_url [NOT NULL]
        integer reviewed_by_id [FK]
        boolean is_verified
        datetime verified_at
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    governance__governance.logistics_partner_documents }o--|| logistics__logistics_partners : has
    governance__governance.logistics_partner_documents ||--o{ accounts__users : has
    governance__governance.logistics_settlements {
        integer id [PK, NOT NULL]
        integer partner_id [FK, NOT NULL]
        integer order_id [FK]
        integer ledger_id
        integer shipment_id [FK]
        numeric amount
        numeric pickup_charge
        numeric dropoff_charge
        numeric total_delivery_fee
        numeric cod_collected
        numeric cod_remitted
        numeric cod_retained
        string cod_remittance_status
        datetime eligible_at
        string status
        string currency
        boolean is_deleted [NOT NULL]
        integer payout_id [FK]
        integer bank_transaction_id
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    governance__governance.logistics_settlements }o--|| logistics__logistics_partners : has
    governance__governance.logistics_settlements }o--|| orders__orders : has
    governance__governance.logistics_settlements }o--|| logistics__shipments : has
    governance__governance.logistics_settlements ||--o{ finance__payouts : has
    governance__governance.normalized_webhook_events {
        integer id [PK, NOT NULL]
        string provider_code [NOT NULL]
        string gateway_event_id [NOT NULL]
        string event_type [NOT NULL]
        string status [NOT NULL]
        string environment
        datetime processed_at
        integer zozi_order_id
        string gateway_transaction_id
        string gateway_customer_id
        numeric gross_amount
        string currency
        numeric gateway_fee
        numeric net_settlement
        numeric fraud_score
        string three_ds_status
        string avs_result
        text raw_payload
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    governance__governance.payment_provider_configs {
        integer id [PK, NOT NULL]
        string provider_name [NOT NULL]
        json config
        boolean is_active
        boolean is_deleted [NOT NULL]
        integer updated_by_id [FK]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    governance__governance.payment_provider_configs ||--o{ accounts__users : has
    governance__governance.processed_webhook_events {
        integer id [PK, NOT NULL]
        string processor [NOT NULL]
        string event_id [NOT NULL]
        string payload_hash [NOT NULL]
        datetime processed_at
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    governance__governance.product_verifications {
        integer id [PK, NOT NULL]
        integer product_id [FK, NOT NULL]
        string status
        integer verified_by_id [FK]
        integer shipment_id [FK]
        string verification_type
        string result
        text expected_specs
        text actual_specs
        text discrepancies
        string scan_code
        text image_urls
        text notes
        datetime created_at [NOT NULL]
        datetime updated_at
        integer order_id [FK]
        boolean is_deleted [NOT NULL]
        string country_code
    }
    governance__governance.product_verifications ||--o{ catalog__products : has
    governance__governance.product_verifications ||--o{ accounts__users : has
    governance__governance.product_verifications }o--|| logistics__shipments : has
    governance__governance.product_verifications }o--|| orders__orders : has
    governance__governance.promotion_order_tiers {
        integer id [PK, NOT NULL]
        integer promotion_id
        string tier_name
        numeric min_order_amount [NOT NULL]
        numeric max_order_amount
        string discount_type [NOT NULL]
        numeric discount_amount
        numeric discount_value
        boolean stacking_allowed
        boolean is_active
        integer sort_order
        integer updated_by_id [FK]
        boolean is_deleted [NOT NULL]
        string country_code [FK]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    governance__governance.promotion_order_tiers ||--o{ accounts__users : has
    governance__governance.promotion_order_tiers ||--o{ country__country_configs : has
    governance__governance.push_notification_tokens {
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        string token [NOT NULL]
        string device_type
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    governance__governance.push_notification_tokens ||--o{ accounts__users : has
    governance__governance.retention_job_runs {
        integer id [PK, NOT NULL]
        string job_type
        string target_table
        string target_name
        integer cutoff_days
        integer records_deleted
        integer archived_count
        integer deleted_count
        string artifact_path
        text result_json
        datetime started_at
        datetime completed_at
        string status
        text error_message
        boolean is_deleted [NOT NULL]
        string country_code
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    governance__governance.role_permission_settings {
        integer id [PK, NOT NULL]
        string role [NOT NULL]
        json permissions_json
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    governance__governance.shipment_confirmations {
        integer id [PK, NOT NULL]
        integer shipment_id [FK, NOT NULL]
        integer order_id [FK]
        integer supplier_id [FK]
        integer requester_user_id [FK]
        string requester_role
        integer target_user_id [FK]
        string target_role
        string confirmation_type
        string status
        string requested_status
        string requested_event_type
        string current_hub
        text notes
        string confirmation_code
        datetime confirmed_at
        datetime responded_at
        string tracking_number
        string delivery_signature_name
        string delivery_signature_data_url
        datetime delivery_signature_captured_at
        text response_notes
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    governance__governance.shipment_confirmations }o--|| logistics__shipments : has
    governance__governance.shipment_confirmations }o--|| orders__orders : has
    governance__governance.shipment_confirmations ||--o{ accounts__users : has
    governance__governance.shipping_carriers {
        integer id [PK, NOT NULL]
        integer supplier_id [FK]
        string name [NOT NULL]
        string code [UK, NOT NULL]
        boolean is_active
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    governance__governance.shipping_carriers ||--o{ accounts__users : has
    governance__governance.shipping_zones {
        integer id [PK, NOT NULL]
        integer supplier_id [FK]
        string name [NOT NULL]
        json countries
        boolean is_active
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    governance__governance.shipping_zones ||--o{ accounts__users : has
    governance__governance.supplier_country_commissions {
        integer id [PK, NOT NULL]
        integer supplier_id [FK, NOT NULL]
        string country_code [NOT NULL]
        numeric commission_rate [NOT NULL]
        string category_slug
        text notes
        boolean is_active
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    governance__governance.supplier_country_commissions ||--o{ accounts__users : has
    governance__governance.system_alerts {
        integer id [PK, NOT NULL]
        string alert_type [NOT NULL]
        string severity
        string title [NOT NULL]
        text message [NOT NULL]
        boolean is_acknowledged
        integer acknowledged_by_id [FK]
        datetime acknowledged_at
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    governance__governance.system_alerts ||--o{ accounts__users : has
    governance__governance.system_health_events {
        integer id [PK, NOT NULL]
        string service
        string metric_name [NOT NULL]
        numeric metric_value [NOT NULL]
        string severity
        text message
        datetime created_at [NOT NULL]
        datetime updated_at
        boolean is_deleted [NOT NULL]
        string country_code [FK]
    }
    governance__governance.system_health_events ||--o{ country__country_configs : has
    governance__governance.system_settings {
        integer id [PK, NOT NULL]
        string key [UK, NOT NULL]
        text value
        string value_type
        string description
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    governance__governance.ticket_replies {
        integer id [PK, NOT NULL]
        integer ticket_id [FK, NOT NULL]
        integer sender_id [FK, NOT NULL]
        text message [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    governance__governance.ticket_replies ||--o{ comms__support_tickets : has
    governance__governance.ticket_replies ||--o{ accounts__users : has
    governance__governance.user_browsing_histories {
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        integer product_id [FK, NOT NULL]
        datetime viewed_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        string country_code [FK]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    governance__governance.user_browsing_histories ||--o{ accounts__users : has
    governance__governance.user_browsing_histories ||--o{ catalog__products : has
    governance__governance.user_browsing_histories ||--o{ country__country_configs : has
    hr__hr.alumni_networks {
        integer id [PK, NOT NULL]
        integer employee_id [UK, FK, NOT NULL]
        string status
        datetime granted_at
        datetime eligibility_expires_at
        text notes
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    hr__hr.alumni_networks ||--o{ hr__employees : has
    hr__hr.coi_reports {
        integer id [PK, NOT NULL]
        integer employee_id [FK, NOT NULL]
        string related_person_name [NOT NULL]
        string relation_type [NOT NULL]
        boolean is_internal
        integer internal_employee_id [FK]
        string risk_level
        boolean is_approved
        integer approved_by_id [FK]
        datetime approved_at
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    hr__hr.coi_reports ||--o{ hr__employees : has
    hr__hr.coi_reports ||--o{ accounts__users : has
    hr__hr.disciplinary_cases {
        integer id [PK, NOT NULL]
        integer employee_id [FK, NOT NULL]
        string employee_name
        string stage [NOT NULL]
        text description [NOT NULL]
        datetime issued_at
        string status
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    hr__hr.disciplinary_cases ||--o{ hr__employees : has
    hr__hr.dynamic_qr_sessions {
        integer id [PK, NOT NULL]
        integer employee_id [FK, NOT NULL]
        string qr_token [UK, NOT NULL]
        datetime expires_at [NOT NULL]
        datetime used_at
        string ip_address
        string user_agent
        string device_fingerprint
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    hr__hr.dynamic_qr_sessions ||--o{ hr__employees : has
    hr__hr.employee_activity_logs {
        integer id [PK, NOT NULL]
        integer actor_employee_id [FK, NOT NULL]
        string action [NOT NULL]
        string entity_type
        integer entity_id
        json metadata_json
        string ip_address
        string device_fingerprint
        string country_code
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    hr__hr.employee_activity_logs ||--o{ hr__employees : has
    hr__hr.employee_addresses {
        integer id [PK, NOT NULL]
        integer employee_id [FK, NOT NULL]
        string address_type [NOT NULL]
        string street [NOT NULL]
        string city [NOT NULL]
        string state
        string postal_code
        string country_code [FK, NOT NULL]
        boolean is_primary
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    hr__hr.employee_addresses ||--o{ hr__employees : has
    hr__hr.employee_addresses ||--o{ country__country_configs : has
    hr__hr.employee_assets {
        integer id [PK, NOT NULL]
        integer employee_id [FK, NOT NULL]
        string asset_type [NOT NULL]
        string asset_id [NOT NULL]
        string serial_no
        datetime assigned_at
        datetime returned_at
        string status
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    hr__hr.employee_assets ||--o{ hr__employees : has
    hr__hr.employee_attendances {
        integer id [PK, NOT NULL]
        integer employee_id [FK, NOT NULL]
        date record_date [NOT NULL]
        datetime scan_in_time
        datetime scan_out_time
        string scan_type
        float location_lat
        float location_long
        string device_fingerprint
        boolean is_anomaly
        string status
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    hr__hr.employee_attendances ||--o{ hr__employees : has
    hr__hr.employee_biometrics {
        integer id [PK, NOT NULL]
        integer employee_id [UK, FK, NOT NULL]
        string fingerprint_hash
        text face_encoding
        string biometric_type
        datetime enrolled_at
        boolean is_active
        boolean is_deleted [NOT NULL]
        string country_code
    }
    hr__hr.employee_biometrics ||--o{ hr__employees : has
    hr__hr.employee_certifications {
        integer id [PK, NOT NULL]
        integer employee_id [FK, NOT NULL]
        string cert_type [NOT NULL]
        string cert_name [NOT NULL]
        date issued_date
        date expiry_date
        boolean is_valid
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    hr__hr.employee_certifications ||--o{ hr__employees : has
    hr__hr.employee_dependents {
        integer id [PK, NOT NULL]
        integer employee_id [FK, NOT NULL]
        string name [NOT NULL]
        string relation [NOT NULL]
        date dob
        boolean is_insured
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    hr__hr.employee_dependents ||--o{ hr__employees : has
    hr__hr.employee_documents {
        integer id [PK, NOT NULL]
        integer employee_id [FK, NOT NULL]
        string doc_type [NOT NULL]
        string file_url [NOT NULL]
        date expiry_date
        integer verified_by_id [FK]
        datetime verified_at
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    hr__hr.employee_documents ||--o{ hr__employees : has
    hr__hr.employee_documents ||--o{ accounts__users : has
    hr__hr.employee_leave_ledgers {
        integer id [PK, NOT NULL]
        integer employee_id [FK, NOT NULL]
        string leave_type [NOT NULL]
        integer year [NOT NULL]
        integer allocated_days
        integer used_days
        integer carried_forward
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    hr__hr.employee_leave_ledgers ||--o{ hr__employees : has
    hr__hr.employee_leave_requests {
        integer id [PK, NOT NULL]
        integer employee_id [FK, NOT NULL]
        string leave_type [NOT NULL]
        date start_date [NOT NULL]
        date end_date [NOT NULL]
        integer days_requested [NOT NULL]
        string status
        integer approved_by_id [FK]
        datetime approved_at
        text rejection_reason
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    hr__hr.employee_leave_requests ||--o{ hr__employees : has
    hr__hr.employee_leave_requests ||--o{ accounts__users : has
    hr__hr.employee_relations {
        integer id [PK, NOT NULL]
        integer employee_id [FK, NOT NULL]
        string related_person_name [NOT NULL]
        string relation_type [NOT NULL]
        boolean is_internal_employee
        integer internal_employee_id [FK]
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    hr__hr.employee_relations ||--o{ hr__employees : has
    hr__hr.employee_risk_scores {
        integer id [PK, NOT NULL]
        integer employee_id [FK, NOT NULL]
        date assessment_date [NOT NULL]
        float score
        string risk_level
        json factors
        text notes
        string country_code
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    hr__hr.employee_risk_scores ||--o{ hr__employees : has
    hr__hr.employee_roles {
        integer id [PK, NOT NULL]
        string role_name [UK]
        json permissions
        integer authority_level
        boolean can_approve_leave
        boolean can_approve_expense
        boolean can_manage_users
        boolean is_deleted [NOT NULL]
        string country_code
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    hr__hr.employee_shift_rosters {
        integer id [PK, NOT NULL]
        integer employee_id [FK, NOT NULL]
        date shift_date [NOT NULL]
        time start_time [NOT NULL]
        time end_time [NOT NULL]
        string shift_type
        string status
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    hr__hr.employee_shift_rosters ||--o{ hr__employees : has
    hr__hr.employee_travel_requests {
        integer id [PK, NOT NULL]
        integer employee_id [FK, NOT NULL]
        string destination_country [NOT NULL]
        date start_date [NOT NULL]
        date end_date [NOT NULL]
        string purpose
        string status
        integer approved_by_id [FK]
        datetime approved_at
        json per_diem_json
        numeric total_cost
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    hr__hr.employee_travel_requests ||--o{ hr__employees : has
    hr__hr.employee_travel_requests ||--o{ accounts__users : has
    hr__hr.employee_work_logs {
        integer id [PK, NOT NULL]
        integer employee_id [FK, NOT NULL]
        date record_date [NOT NULL]
        numeric hours_worked
        text task_description
        float location_lat
        float location_long
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    hr__hr.employee_work_logs ||--o{ hr__employees : has
    hr__hr.employees {
        integer id [PK, NOT NULL]
        integer user_id [UK, FK]
        string employee_code [UK, NOT NULL]
        integer office_id [FK]
        string department
        string position
        string employment_type
        string employment_status
        numeric salary
        string currency
        string country_code [FK]
        date hire_date [NOT NULL]
        date termination_date
        boolean is_verified
        string gender
        integer years_of_experience
        integer performance_score
        string education_level
        text notes
        integer reporting_manager_id [FK]
        integer hiring_manager_id [FK]
        integer authority_level
        integer org_unit_id [FK]
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    hr__hr.employees ||--o{ accounts__users : has
    hr__hr.employees }o--|| hr__offices : has
    hr__hr.employees ||--o{ country__country_configs : has
    hr__hr.employees ||--o{ hr__employees : has
    hr__hr.employees }o--|| hr__org_units : has
    hr__hr.geo_fence_logs {
        integer id [PK, NOT NULL]
        integer employee_id [FK, NOT NULL]
        float latitude [NOT NULL]
        float longitude [NOT NULL]
        integer accuracy_meters
        datetime scanned_at
        boolean is_within_fence
        boolean is_deleted [NOT NULL]
        string country_code
    }
    hr__hr.geo_fence_logs ||--o{ hr__employees : has
    hr__hr.offboarding_cases {
        integer id [PK, NOT NULL]
        integer employee_id [FK, NOT NULL]
        string employee_name
        string reason [NOT NULL]
        string status
        datetime initiated_at
        datetime completed_at
        text notes
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    hr__hr.offboarding_cases ||--o{ hr__employees : has
    hr__hr.offices {
        integer id [PK, NOT NULL]
        string name [NOT NULL]
        string city
        float latitude
        float longitude
        integer geo_fence_radius_meters
        text address
        string phone
        string email
        boolean is_active
        boolean is_deleted [NOT NULL]
        string country_code
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    hr__hr.onboarding_pipelines {
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        string pipeline_type [NOT NULL]
        string status
        integer current_step
        json steps_data
        datetime started_at
        datetime completed_at
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code [NOT NULL]
        boolean is_deleted [NOT NULL]
    }
    hr__hr.onboarding_pipelines ||--o{ accounts__users : has
    hr__hr.onboarding_steps {
        integer id [PK, NOT NULL]
        integer pipeline_id [FK, NOT NULL]
        string step_name [NOT NULL]
        string status
        json data
        datetime started_at
        datetime completed_at
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code [NOT NULL]
        boolean is_deleted [NOT NULL]
    }
    hr__hr.onboarding_steps }o--|| hr__onboarding_pipelines : has
    hr__hr.org_units {
        integer id [PK, NOT NULL]
        string name [NOT NULL]
        integer parent_id [FK]
        string country_code
        integer level
        boolean is_active
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    hr__hr.org_units }o--|| hr__org_units : has
    hr__hr.physical_id_cards {
        integer id [PK, NOT NULL]
        integer employee_id [UK, FK, NOT NULL]
        string card_number [UK, NOT NULL]
        datetime issued_at
        datetime expires_at
        boolean is_revoked
        datetime revoked_at
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    hr__hr.physical_id_cards ||--o{ hr__employees : has
    hr__hr.shift_handover_sessions {
        integer id [PK, NOT NULL]
        string country_code [FK]
        integer outgoing_employee_id [FK, NOT NULL]
        integer incoming_employee_id [FK]
        datetime shift_date [NOT NULL]
        text notes
        string status
        datetime acknowledged_at
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    hr__hr.shift_handover_sessions ||--o{ country__country_configs : has
    hr__hr.shift_handover_sessions ||--o{ hr__employees : has
    hr__hr.shift_handover_tasks {
        integer id [PK, NOT NULL]
        integer session_id [FK, NOT NULL]
        text description [NOT NULL]
        string priority
        string status
        integer assigned_to_id [FK]
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    hr__hr.shift_handover_tasks }o--|| hr__shift_handover_sessions : has
    hr__hr.shift_handover_tasks ||--o{ accounts__users : has
    hr__hr.training_modules {
        string module_id [PK, NOT NULL]
        string title [NOT NULL]
        text description
        string required_for_role
        integer duration_minutes
        boolean is_active
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    logistics__logistics.city_distance_matrices {
        integer id [PK, NOT NULL]
        string origin_country_code [NOT NULL]
        string origin_city_name [NOT NULL]
        string destination_country_code [NOT NULL]
        string destination_city_name [NOT NULL]
        numeric distance_km
        text notes
        integer created_by_id [FK]
        integer updated_by_id [FK]
        boolean is_deleted [NOT NULL]
        string country_code [FK]
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.city_distance_matrices ||--o{ accounts__users : has
    logistics__logistics.city_distance_matrices ||--o{ country__country_configs : has
    logistics__logistics.customs_entries {
        guid uuid [UK, NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer version [NOT NULL]
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        integer shipment_id [FK, NOT NULL]
        string customs_declaration_number
        string customs_broker
        datetime entry_date
        numeric duty_rate_applied
        numeric duty_amount
        numeric vat_on_duty
        numeric penalties
        numeric total_customs_cost
        string status
        text notes
        string country_code
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.customs_entries ||--o{ logistics__import_shipments : has
    logistics__logistics.goods_receipt_lines {
        guid uuid [UK, NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer version [NOT NULL]
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        integer grn_id [FK, NOT NULL]
        integer po_line_id [FK]
        integer product_id [FK]
        string product_name
        string sku
        numeric quantity_received
        numeric quantity_accepted
        numeric quantity_rejected
        string rejection_reason
        string lot_number
        datetime expiry_date
        numeric unit_cost
        string country_code
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.goods_receipt_lines ||--o{ logistics__goods_receipt_notes : has
    logistics__logistics.goods_receipt_lines }o--|| logistics__purchase_order_lines : has
    logistics__logistics.goods_receipt_lines ||--o{ catalog__products : has
    logistics__logistics.goods_receipt_notes {
        guid uuid [UK, NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer version [NOT NULL]
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        string grn_number [UK, NOT NULL]
        integer po_id [FK]
        integer supplier_id [FK]
        datetime receipt_date
        integer warehouse_id [FK]
        string status
        text notes
        integer received_by_id [FK]
        string country_code
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.goods_receipt_notes }o--|| logistics__purchase_orders : has
    logistics__logistics.goods_receipt_notes ||--o{ finance__vendors : has
    logistics__logistics.goods_receipt_notes }o--|| logistics__warehouses : has
    logistics__logistics.goods_receipt_notes ||--o{ accounts__users : has
    logistics__logistics.import_cost_templates {
        guid uuid [UK, NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer version [NOT NULL]
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        string name [NOT NULL]
        numeric default_duty_rate
        numeric default_freight_percent
        numeric default_insurance_percent
        numeric default_port_charges_percent
        numeric default_bank_charges_percent
        string allocation_method
        string country_code
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.import_shipment_lines {
        guid uuid [UK, NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer version [NOT NULL]
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        integer shipment_id [FK, NOT NULL]
        integer po_line_id [FK]
        integer product_id [FK]
        string product_name
        string sku
        string hs_code
        numeric quantity
        numeric unit_cost_fx
        numeric unit_cost_local
        numeric line_total_fx
        numeric weight_kg
        numeric volume_cbm
        numeric allocated_freight
        numeric allocated_insurance
        numeric allocated_port
        numeric allocated_other
        numeric duty_amount
        numeric landed_unit_cost
        string country_code
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.import_shipment_lines ||--o{ logistics__import_shipments : has
    logistics__logistics.import_shipment_lines }o--|| logistics__purchase_order_lines : has
    logistics__logistics.import_shipment_lines ||--o{ catalog__products : has
    logistics__logistics.import_shipments {
        guid uuid [UK, NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer version [NOT NULL]
        integer updated_by
        integer id [PK, NOT NULL]
        string shipment_ref [UK, NOT NULL]
        integer po_id [FK]
        integer supplier_id [FK]
        string supplier_name
        string origin_country
        string port_of_loading
        string port_of_discharge
        string vessel_name
        string bill_of_lading
        string container_number
        datetime shipment_date
        datetime estimated_arrival
        datetime actual_arrival
        string currency
        numeric exchange_rate
        integer warehouse_id [FK]
        string country_code
        text notes
        integer created_by_id [FK]
        string status
        numeric product_cost_total
        numeric freight_cost
        numeric insurance_cost
        numeric port_charges
        numeric inland_freight
        numeric bank_charges
        numeric other_costs
        numeric total_landed_cost
        numeric duty_cost
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.import_shipments }o--|| logistics__purchase_orders : has
    logistics__logistics.import_shipments ||--o{ finance__vendors : has
    logistics__logistics.import_shipments }o--|| logistics__warehouses : has
    logistics__logistics.import_shipments ||--o{ accounts__users : has
    logistics__logistics.landed_cost_allocations {
        guid uuid [UK, NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer version [NOT NULL]
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        integer shipment_id [FK, NOT NULL]
        string cost_type
        text description
        numeric total_amount
        string allocation_method
        string currency
        numeric exchange_rate
        string country_code
        string status
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.landed_cost_allocations ||--o{ logistics__import_shipments : has
    logistics__logistics.logistics_category_pricing_rules {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer partner_id [FK, NOT NULL]
        integer service_area_id [FK]
        string category_name [NOT NULL]
        numeric flat_fee_override
        numeric special_handling_fee
        string currency
        boolean is_active
        string approval_status
        string review_note
        integer reviewed_by_id [FK]
        datetime reviewed_at
        datetime created_at
        datetime updated_at
        string country_code
    }
    logistics__logistics.logistics_category_pricing_rules }o--|| logistics__logistics_partners : has
    logistics__logistics.logistics_category_pricing_rules }o--|| logistics__logistics_partner_service_areas : has
    logistics__logistics.logistics_category_pricing_rules ||--o{ accounts__users : has
    logistics__logistics.logistics_partner_profiles {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer partner_id [UK, FK, NOT NULL]
        string tax_id
        string registration_number
        string business_type
        integer years_in_business
        string insurance_provider
        string insurance_policy_number
        datetime insurance_expiry
        datetime created_at
        datetime updated_at
        string country_code [FK]
    }
    logistics__logistics.logistics_partner_profiles }o--|| logistics__logistics_partners : has
    logistics__logistics.logistics_partner_profiles ||--o{ country__country_configs : has
    logistics__logistics.logistics_partner_service_areas {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer partner_id [FK, NOT NULL]
        string country_code [NOT NULL]
        string country_name [NOT NULL]
        string origin_city [NOT NULL]
        string city_name [NOT NULL]
        string zone_label
        numeric charge_amount
        numeric minimum_charge
        numeric per_kg_rate
        numeric pickup_charge
        numeric dropoff_charge
        numeric per_km_rate
        string currency
        integer delivery_days_min
        integer delivery_days_max
        boolean is_active
        string approval_status
        string review_note
        integer reviewed_by_id
        datetime reviewed_at
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.logistics_partner_service_areas }o--|| logistics__logistics_partners : has
    logistics__logistics.logistics_partners {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer user_id [FK]
        string name [NOT NULL]
        string code [UK, NOT NULL]
        string contact_name
        string contact_email
        string contact_phone
        string website
        json coverage_regions
        json service_types
        string status_code
        string verification_status
        string verification_note
        integer verified_by
        datetime verified_at
        string country_code [FK]
        datetime created_at
        string business_type
        string region
        string city
        text address
        string postal_code
        string tax_id
        text bio
        text about_us
        string logo_url
        string banner_url
        numeric latitude
        numeric longitude
        json social_links
        text notes
        boolean is_terms_accepted
        string terms_version
        datetime terms_accepted_at
    }
    logistics__logistics.logistics_partners ||--o{ accounts__users : has
    logistics__logistics.logistics_partners ||--o{ country__country_configs : has
    logistics__logistics.logistics_pricing_profiles {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer partner_id [FK, NOT NULL]
        integer service_area_id [FK, NOT NULL]
        string profile_name [NOT NULL]
        numeric base_in_city_fee
        numeric per_kg_rate
        numeric minimum_charge
        numeric maximum_charge
        numeric fuel_multiplier
        numeric base_inter_city_fee
        numeric per_km_rate
        numeric bulk_discount_threshold_kg
        numeric bulk_discount_percent
        string currency
        boolean is_active
        string approval_status
        string review_note
        integer reviewed_by_id [FK]
        datetime reviewed_at
        datetime created_at
        datetime updated_at
        string country_code
    }
    logistics__logistics.logistics_pricing_profiles }o--|| logistics__logistics_partners : has
    logistics__logistics.logistics_pricing_profiles }o--|| logistics__logistics_partner_service_areas : has
    logistics__logistics.logistics_pricing_profiles ||--o{ accounts__users : has
    logistics__logistics.logistics_vehicle_rules {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer partner_id [FK, NOT NULL]
        integer service_area_id [FK, NOT NULL]
        string vehicle_type [NOT NULL]
        numeric max_weight_kg
        numeric cost_multiplier
        integer priority_rank
        string route_scope
        numeric max_volume_cm3
        boolean is_active
        string approval_status
        string review_note
        integer reviewed_by_id [FK]
        datetime reviewed_at
        datetime created_at
        datetime updated_at
        string country_code
    }
    logistics__logistics.logistics_vehicle_rules }o--|| logistics__logistics_partners : has
    logistics__logistics.logistics_vehicle_rules }o--|| logistics__logistics_partner_service_areas : has
    logistics__logistics.logistics_vehicle_rules ||--o{ accounts__users : has
    logistics__logistics.partner_performance_projections {
        integer id [PK, NOT NULL]
        integer partner_id [FK, NOT NULL]
        string country_code
        integer total_shipments
        integer delivered_shipments
        integer cancelled_shipments
        numeric avg_delivery_hours
        numeric on_time_rate
        datetime period_start
        datetime period_end
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.partner_performance_projections }o--|| logistics__logistics_partners : has
    logistics__logistics.purchase_order_lines {
        guid uuid [UK, NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer version [NOT NULL]
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        integer po_id [FK, NOT NULL]
        integer product_id [FK]
        string product_name
        string sku
        text description
        numeric quantity_ordered
        numeric quantity_received
        numeric unit_price
        numeric discount_percent
        numeric discount_amount
        numeric tax_rate
        numeric tax_amount
        numeric line_total
        numeric weight
        numeric volume
        string country_code
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.purchase_order_lines }o--|| logistics__purchase_orders : has
    logistics__logistics.purchase_order_lines ||--o{ catalog__products : has
    logistics__logistics.purchase_orders {
        guid uuid [UK, NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer version [NOT NULL]
        integer updated_by
        integer id [PK, NOT NULL]
        string po_number [UK, NOT NULL]
        integer supplier_id [FK]
        string supplier_name
        datetime order_date
        datetime expected_delivery_date
        integer warehouse_id [FK]
        string currency
        text notes
        text terms
        text shipping_address
        string country_code
        integer created_by_id [FK]
        string status
        numeric subtotal
        numeric discount_total
        numeric tax_total
        numeric grand_total
        numeric total_amount
        datetime delivery_date
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.purchase_orders ||--o{ finance__vendors : has
    logistics__logistics.purchase_orders }o--|| logistics__warehouses : has
    logistics__logistics.purchase_orders ||--o{ accounts__users : has
    logistics__logistics.sales_order_lines {
        guid uuid [UK, NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer version [NOT NULL]
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        integer so_id [FK, NOT NULL]
        integer product_id [FK]
        string product_name
        string sku
        text description
        numeric quantity_ordered
        numeric quantity_dispatched
        numeric unit_price
        numeric discount_percent
        numeric discount_amount
        numeric tax_rate
        numeric tax_amount
        numeric line_total
        numeric weight
        numeric volume
        string country_code
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.sales_order_lines }o--|| logistics__sales_orders : has
    logistics__logistics.sales_order_lines ||--o{ catalog__products : has
    logistics__logistics.sales_orders {
        guid uuid [UK, NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer version [NOT NULL]
        integer updated_by
        integer id [PK, NOT NULL]
        string so_number [UK, NOT NULL]
        integer customer_id [FK]
        string customer_name
        string customer_po_number
        datetime order_date
        datetime expected_delivery_date
        integer warehouse_id [FK]
        string currency
        text shipping_address
        text billing_address
        text notes
        text terms
        string country_code
        integer created_by_id [FK]
        string status
        numeric subtotal
        numeric discount_total
        numeric tax_total
        numeric grand_total
        datetime delivery_date
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.sales_orders ||--o{ finance__customers : has
    logistics__logistics.sales_orders }o--|| logistics__warehouses : has
    logistics__logistics.sales_orders ||--o{ accounts__users : has
    logistics__logistics.shipment_events {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer shipment_id [FK]
        integer order_id [FK]
        integer supplier_id [FK, NOT NULL]
        integer actor_user_id [FK]
        string actor_role
        string event_type [NOT NULL]
        string status_after
        string distribution_channel
        string location
        numeric latitude
        numeric longitude
        string scan_code
        string notes
        datetime created_at
        string country_code
    }
    logistics__logistics.shipment_events }o--|| logistics__shipments : has
    logistics__logistics.shipment_events }o--|| orders__orders : has
    logistics__logistics.shipment_events ||--o{ accounts__users : has
    logistics__logistics.shipment_tracking_projections {
        integer id [PK, NOT NULL]
        integer shipment_id [FK, NOT NULL]
        integer order_id [NOT NULL]
        string status_code [NOT NULL]
        string carrier_name
        string tracking_number
        string current_hub
        datetime estimated_delivery
        datetime actual_delivery
        json event_log
        datetime last_event_at
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.shipment_tracking_projections }o--|| logistics__shipments : has
    logistics__logistics.shipments {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer order_id [FK, NOT NULL]
        integer supplier_id [FK, NOT NULL]
        integer assigned_partner_id [FK]
        integer carrier_id [FK]
        string tracking_number [UK]
        string carrier_name
        string status_code
        string distribution_channel
        string current_hub
        string scan_code
        integer package_count
        numeric package_weight_kg
        string package_dimensions
        datetime packaged_at
        integer packaged_by_user_id
        string packaged_notes
        string packaging_notes
        datetime shipped_at
        datetime estimated_delivery
        datetime actual_delivery
        string delivery_signature_name
        string delivery_signature_data_url
        datetime delivery_signature_captured_at
        text notes
        string accepted_vehicle_type
        numeric accepted_vehicle_multiplier
        datetime accepted_vehicle_selected_at
        datetime created_at
        datetime updated_at
        string country_code
    }
    logistics__logistics.shipments }o--|| orders__orders : has
    logistics__logistics.shipments ||--o{ accounts__users : has
    logistics__logistics.shipments }o--|| logistics__logistics_partners : has
    logistics__logistics.shipments ||--o{ governance__shipping_carriers : has
    logistics__logistics.shipping_rules {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string country_code [FK, NOT NULL]
        string method [NOT NULL]
        numeric base_rate [NOT NULL]
        numeric per_kg_rate
        boolean is_active
        datetime created_at
    }
    logistics__logistics.shipping_rules ||--o{ country__country_configs : has
    logistics__logistics.stock_movements {
        guid uuid [UK, NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer version [NOT NULL]
        integer updated_by
        integer id [PK, NOT NULL]
        integer product_id [FK]
        integer warehouse_id [FK]
        string movement_type
        string reference_type
        integer reference_id
        numeric quantity_change
        numeric quantity_after
        numeric unit_cost
        numeric total_cost
        string country_code
        integer created_by_id [FK]
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.stock_movements ||--o{ catalog__products : has
    logistics__logistics.stock_movements }o--|| logistics__warehouses : has
    logistics__logistics.stock_movements ||--o{ accounts__users : has
    logistics__logistics.warehouses {
        guid uuid [UK, NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer version [NOT NULL]
        integer created_by_id
        integer updated_by
        integer id [PK, NOT NULL]
        string name [NOT NULL]
        string code [UK, NOT NULL]
        string address
        string city
        string country_code
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    orders__orders.order_items {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer order_id [FK, NOT NULL]
        integer product_id [FK, NOT NULL]
        integer variant_id
        integer supplier_id
        integer quantity
        numeric unit_price
        numeric price
        numeric total_price
        string product_name
        string product_image
        string selected_size
        string selected_color
        datetime created_at [NOT NULL]
        string country_code [FK]
    }
    orders__orders.order_items ||--o{ orders__orders : has
    orders__orders.order_items ||--o{ catalog__products : has
    orders__orders.order_items ||--o{ country__country_configs : has
    orders__orders.order_logistics_allocations {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer order_id [FK, NOT NULL]
        integer supplier_id [FK, NOT NULL]
        integer shipment_id [FK]
        integer partner_id [FK]
        integer service_area_id [FK]
        string allocation_source
        string partner_name_snapshot
        string partner_code_snapshot
        string service_area_label_snapshot
        string destination_country
        string destination_city
        numeric shipping_amount
        numeric pickup_charge
        numeric dropoff_charge
        integer accepted_vehicle_rule_id
        string accepted_vehicle_type
        numeric accepted_vehicle_multiplier
        numeric accepted_shipping_amount
        numeric accepted_pickup_charge
        numeric accepted_dropoff_charge
        integer estimated_delivery_min
        integer estimated_delivery_max
        string currency
        text pricing_breakdown_json
        text accepted_pricing_breakdown_json
        string country_code [FK]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    orders__orders.order_logistics_allocations ||--o{ orders__orders : has
    orders__orders.order_logistics_allocations ||--o{ accounts__users : has
    orders__orders.order_logistics_allocations ||--o{ logistics__shipments : has
    orders__orders.order_logistics_allocations ||--o{ logistics__logistics_partners : has
    orders__orders.order_logistics_allocations ||--o{ logistics__logistics_partner_service_areas : has
    orders__orders.order_logistics_allocations ||--o{ country__country_configs : has
    orders__orders.order_notifications {
        guid uuid [UK]
        integer version [NOT NULL]
        datetime updated_at [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        integer order_id [FK, NOT NULL]
        string title
        text message
        string channel
        boolean is_read
        datetime created_at [NOT NULL]
    }
    orders__orders.order_notifications ||--o{ accounts__users : has
    orders__orders.order_notifications ||--o{ orders__orders : has
    orders__orders.orders {
        guid uuid [UK]
        integer version [NOT NULL]
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string order_number [UK]
        integer customer_id [FK]
        integer user_id [FK, NOT NULL]
        string status_code
        string status_label
        string payment_status
        string payment_method
        string payment_provider
        string payment_intent_id
        numeric subtotal
        numeric subtotal_amount
        numeric shipping_fee
        numeric shipping_amount
        numeric tax_amount
        numeric vat_amount
        numeric discount_amount
        numeric total
        numeric total_amount
        string coupon_code
        numeric fraud_score
        string fraud_action
        string currency
        text shipping_address
        string shipping_city
        string shipping_country
        string shipping_postal_code
        string customer_phone
        string delivery_location
        string delivery_note
        string tracking_number [UK]
        integer selected_partner_id
        integer selected_service_area_id
        integer estimated_delivery_min
        integer estimated_delivery_max
        string payment_gateway_code
        numeric payment_gateway_fee_amount
        numeric payment_customer_total_amount
        numeric payment_gateway_fee_passed_to_customer
        datetime paid_at
        string country_code [FK]
        datetime created_at [NOT NULL]
        datetime updated_at
        boolean is_deleted [NOT NULL]
        datetime deleted_at
    }
    orders__orders.orders ||--o{ accounts__users : has
    orders__orders.orders ||--o{ country__country_configs : has
    orders__orders.return_requests {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer order_id [FK, NOT NULL]
        integer order_item_id
        integer customer_id [FK]
        string intent
        string reason [NOT NULL]
        text description
        text details
        text supplier_review_state
        text images
        string status_code
        numeric refund_amount
        text items
        integer return_window_days
        datetime delivered_at
        datetime return_deadline
        text resolution_notes
        string country_code [FK]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    orders__orders.return_requests ||--o{ orders__orders : has
    orders__orders.return_requests ||--o{ accounts__users : has
    orders__orders.return_requests ||--o{ country__country_configs : has
    public__payroll_records {
        integer id [PK, NOT NULL]
        string country_code [NOT NULL]
        integer employee_id [FK]
        numeric net_pay
        string status
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    public__payroll_records ||--o{ hr__employees : has
    promotions__promotions.banners {
        integer id [PK, NOT NULL]
        string title [NOT NULL]
        string subtitle
        string image_url
        string link
        string banner_type
        boolean is_active
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id [FK]
        integer sort_order
        string bg_color
        string text_color
        string subtitle_color
        string btn_bg_color
        string btn_text_color
        string badge_text
        string badge_color
        string effect
        string video_url
        string cta_label
        string cta_url
        datetime starts_at
        datetime ends_at
        integer created_by_id [FK]
        string country_code [FK]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    promotions__promotions.banners ||--o{ accounts__users : has
    promotions__promotions.banners ||--o{ country__country_configs : has
    promotions__promotions.bogo_promotions {
        integer id [PK, NOT NULL]
        string title [NOT NULL]
        text description
        integer buy_quantity [NOT NULL]
        integer free_quantity [NOT NULL]
        integer free_discount_pct [NOT NULL]
        string apply_to [NOT NULL]
        integer target_id
        integer max_uses_per_customer
        boolean stacking_allowed
        boolean is_active
        datetime starts_at
        datetime ends_at
        string country_code [FK]
        datetime created_at [NOT NULL]
        datetime updated_at
        boolean is_deleted [NOT NULL]
    }
    promotions__promotions.bogo_promotions ||--o{ country__country_configs : has
    promotions__promotions.coupon_usages {
        integer id [PK, NOT NULL]
        integer coupon_id [NOT NULL]
        integer user_id [NOT NULL]
        integer order_id
        string country_code [FK]
        datetime created_at
        datetime updated_at
        boolean is_deleted [NOT NULL]
    }
    promotions__promotions.coupon_usages ||--o{ country__country_configs : has
    promotions__promotions.coupons {
        integer id [PK, NOT NULL]
        string code [UK, NOT NULL]
        string discount_type
        numeric discount_value
        numeric minimum_order
        numeric maximum_discount
        integer usage_limit
        integer usage_count
        datetime starts_at
        datetime expires_at
        boolean is_active
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id [FK]
        string country_code [FK]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    promotions__promotions.coupons ||--o{ accounts__users : has
    promotions__promotions.coupons ||--o{ country__country_configs : has
    promotions__promotions.flash_sales {
        integer id [PK, NOT NULL]
        string title [NOT NULL]
        text description
        datetime starts_at [NOT NULL]
        datetime ends_at [NOT NULL]
        numeric discount_pct
        boolean is_active
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by_id
        string country_code [FK]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    promotions__promotions.flash_sales ||--o{ country__country_configs : has
    promotions__promotions.points_transactions {
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        integer points [NOT NULL]
        string transaction_type [NOT NULL]
        integer order_id
        string source_description
        integer balance_after
        boolean is_deleted [NOT NULL]
        string country_code
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    promotions__promotions.points_transactions ||--o{ accounts__users : has
    promotions__promotions.promotion_engine_configs {
        integer id [PK, NOT NULL]
        string country_code [FK]
        boolean engine_enabled
        boolean allow_product_coupons
        boolean allow_category_coupons
        boolean allow_order_tier_discounts
        boolean allow_referral_rewards
        boolean allow_supplier_promotions
        boolean allow_global_coupons
        string stacking_mode
        numeric max_combined_discount_percent
        numeric max_combined_discount_amount
        boolean show_savings_line_item
        boolean tier_discount_visible
        integer points_per_omr
        integer referral_referrer_points
        integer referral_referee_points
        integer points_expiry_months
        integer referral_monthly_cap
        integer referral_verification_delay_days
        integer min_points_redeem
        boolean allow_partial_points_redemption
        integer updated_by
        datetime created_at
        datetime updated_at
        boolean is_deleted [NOT NULL]
    }
    promotions__promotions.promotion_engine_configs ||--o{ country__country_configs : has
    promotions__promotions.promotion_ledger_entries {
        integer id [PK, NOT NULL]
        integer promotion_id
        integer order_id
        integer user_id [FK]
        string promotion_type
        string promotion_code
        integer tier_id
        numeric amount [NOT NULL]
        string entry_type [NOT NULL]
        numeric discount_amount [NOT NULL]
        integer points_awarded
        integer points_redeemed
        integer stacking_flag
        string source
        string metadata_json
        boolean is_deleted [NOT NULL]
        datetime created_at [NOT NULL]
        datetime updated_at
        string country_code
    }
    promotions__promotions.promotion_ledger_entries ||--o{ accounts__users : has
    promotions__promotions.user_points {
        integer id [PK, NOT NULL]
        integer user_id [UK, FK, NOT NULL]
        integer balance [NOT NULL]
        integer lifetime_earned [NOT NULL]
        integer lifetime_redeemed [NOT NULL]
        string loyalty_tier [NOT NULL]
        datetime points_expire_at
        boolean is_deleted [NOT NULL]
        string country_code
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    promotions__promotions.user_points ||--o{ accounts__users : has
    security__security.alert_escalation_rules {
        integer id [PK, NOT NULL]
        string alert_type [NOT NULL]
        string severity
        numeric threshold_value
        integer current_tier
        boolean is_active
        boolean is_deleted [NOT NULL]
        string country_code [FK]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    security__security.alert_escalation_rules ||--o{ country__country_configs : has
    security__security.credit_card_bins {
        integer id [PK, NOT NULL]
        string bin [UK, NOT NULL]
        string brand
        string bank
        string country
        boolean is_blacklisted
        boolean is_deleted [NOT NULL]
        datetime created_at
        datetime updated_at
    }
    security__security.device_fingerprints {
        integer id [PK, NOT NULL]
        integer user_id [FK]
        string fingerprint_hash [NOT NULL]
        string user_agent
        text ip_addresses
        boolean is_trusted
        boolean is_blocked
        integer risk_score
        integer headless_attempts
        integer account_count
        datetime first_seen_at
        datetime last_seen_at
        boolean is_deleted [NOT NULL]
    }
    security__security.device_fingerprints ||--o{ accounts__users : has
    security__security.dlp_violations {
        integer id [PK, NOT NULL]
        string violation_type [NOT NULL]
        string severity
        integer sender_id [FK]
        string recipient_email
        text detected_content
        string action_taken
        string status_code
        integer reviewed_by_id [FK]
        datetime reviewed_at
        boolean is_deleted [NOT NULL]
        datetime created_at
        datetime updated_at
    }
    security__security.dlp_violations ||--o{ accounts__users : has
    security__security.document_verifications {
        integer id [PK, NOT NULL]
        integer pipeline_id [FK, NOT NULL]
        string document_type [NOT NULL]
        json document_data
        string status
        datetime verified_at
        integer verifier_id [FK]
        boolean is_deleted [NOT NULL]
        string country_code [FK]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    security__security.document_verifications ||--o{ hr__onboarding_pipelines : has
    security__security.document_verifications ||--o{ accounts__users : has
    security__security.document_verifications ||--o{ country__country_configs : has
    security__security.fraud_alerts {
        integer id [PK, NOT NULL]
        string alert_type [NOT NULL]
        string entity_type [NOT NULL]
        integer entity_id [NOT NULL]
        numeric fraud_score [NOT NULL]
        text triggered_rules
        string priority
        text details
        boolean is_resolved
        datetime resolved_at
        boolean is_deleted [NOT NULL]
        datetime created_at
        string country_code
    }
    security__security.fraud_blacklists {
        integer id [PK, NOT NULL]
        string identifier_type [NOT NULL]
        string identifier_value [NOT NULL]
        string identifier_value_hash
        string reason
        boolean is_active
        string status_code
        datetime created_at
        boolean is_deleted [NOT NULL]
        datetime expires_at
    }
    security__security.fraud_case_assignments {
        integer id [PK, NOT NULL]
        integer case_id [FK, NOT NULL]
        integer assigned_to_id [FK, NOT NULL]
        integer assigned_by_id [FK]
        string role_at_assignment
        boolean is_deleted [NOT NULL]
        datetime created_at
        datetime updated_at
    }
    security__security.fraud_case_assignments ||--o{ security__fraud_cases : has
    security__security.fraud_case_assignments ||--o{ accounts__users : has
    security__security.fraud_cases {
        integer id [PK, NOT NULL]
        string case_number [UK, NOT NULL]
        string title [NOT NULL]
        text description
        integer fraud_score [NOT NULL]
        string priority
        string status_code
        string entity_type
        integer entity_id
        integer assigned_to_id [FK]
        integer created_by_id [FK]
        datetime resolved_at
        text resolution_notes
        boolean is_deleted [NOT NULL]
        datetime created_at
        datetime updated_at
        string country_code
    }
    security__security.fraud_cases ||--o{ accounts__users : has
    security__security.fraud_events {
        integer id [PK, NOT NULL]
        integer user_id [FK]
        integer order_id [FK]
        string event_type [NOT NULL]
        string ip_address
        string device_hash
        string session_id
        numeric fraud_score [NOT NULL]
        text triggered_rules
        json details
        boolean is_flagged
        string status_code
        integer reviewed_by_id [FK]
        datetime reviewed_at
        boolean is_deleted [NOT NULL]
        datetime created_at
        string country_code
    }
    security__security.fraud_events ||--o{ accounts__users : has
    security__security.fraud_events ||--o{ orders__orders : has
    security__security.fraud_rules {
        integer id [PK, NOT NULL]
        string rule_key [UK, NOT NULL]
        string name [NOT NULL]
        text description
        integer weight
        text condition_json
        string action
        boolean is_active
        boolean is_global
        string country_code
        boolean is_deleted [NOT NULL]
        datetime created_at
        datetime updated_at
    }
    security__security.fraud_scoring_logs {
        integer id [PK, NOT NULL]
        string event_type [NOT NULL]
        integer user_id [FK]
        integer order_id [FK]
        string ip_address
        string device_hash
        string session_id
        integer raw_score [NOT NULL]
        json triggered_rules
        json metadata_json
        string action_taken
        boolean is_deleted [NOT NULL]
        datetime created_at
        string country_code
    }
    security__security.fraud_scoring_logs ||--o{ accounts__users : has
    security__security.fraud_scoring_logs ||--o{ orders__orders : has
    security__security.fraud_velocity_counters {
        integer id [PK, NOT NULL]
        string key [NOT NULL]
        integer count
        datetime window_start
        datetime window_end [NOT NULL]
        string entity_type
        integer entity_id
        boolean is_deleted [NOT NULL]
        datetime created_at
        datetime updated_at
    }
    security__security.ip_account_linkages {
        integer id [PK, NOT NULL]
        string ip_address [NOT NULL]
        integer user_id [FK, NOT NULL]
        string device_fingerprint
        string session_id
        integer interaction_count
        boolean is_suspicious
        datetime last_seen
        boolean is_deleted [NOT NULL]
    }
    security__security.ip_account_linkages ||--o{ accounts__users : has
    security__security.ip_reputations {
        integer id [PK, NOT NULL]
        string ip_address [NOT NULL]
        numeric reputation_score
        boolean is_blocked
        boolean is_proxy
        boolean is_tor
        boolean is_vpn
        boolean is_hosting
        string asn
        string country_code
        datetime last_seen_at
        datetime updated_at
        datetime created_at
        boolean is_deleted [NOT NULL]
    }
    security__security.kyc_verifications {
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        string status
        string provider
        json verification_data
        json document_types
        datetime submitted_at
        datetime reviewed_at
        integer reviewer_id [FK]
        boolean is_deleted [NOT NULL]
        string country_code [FK]
        datetime created_at [NOT NULL]
        datetime updated_at
    }
    security__security.kyc_verifications ||--o{ accounts__users : has
    security__security.kyc_verifications ||--o{ country__country_configs : has
    security__security.logistics_fraud_indicators {
        integer id [PK, NOT NULL]
        integer partner_id [FK, NOT NULL]
        string indicator_type [NOT NULL]
        string value
        boolean is_active
        boolean is_deleted [NOT NULL]
        datetime created_at
        string country_code
    }
    security__security.logistics_fraud_indicators ||--o{ logistics__logistics_partners : has
    security__security.manual_review_queues {
        integer id [PK, NOT NULL]
        string entity_type [NOT NULL]
        integer entity_id [NOT NULL]
        integer fraud_score [NOT NULL]
        text triggered_rules
        string reason [NOT NULL]
        string priority
        integer assigned_to_id [FK]
        text admin_notes
        string status_code
        boolean is_deleted [NOT NULL]
        datetime created_at
        datetime updated_at
    }
    security__security.manual_review_queues ||--o{ accounts__users : has
    security__security.meeting_action_items {
        integer id [PK, NOT NULL]
        integer meeting_id [FK, NOT NULL]
        string entity_type
        integer entity_id
        string action [NOT NULL]
        json metadata_json
        string status_code
        integer assigned_to_id [FK]
        boolean is_deleted [NOT NULL]
        datetime created_at
        datetime due_date
    }
    security__security.meeting_action_items ||--o{ security__meeting_transcripts : has
    security__security.meeting_action_items ||--o{ accounts__users : has
    security__security.meeting_transcripts {
        integer id [PK, NOT NULL]
        string room_id [NOT NULL]
        string language
        json segments
        json action_items
        text summary
        integer word_count
        integer duration_seconds
        boolean is_deleted [NOT NULL]
        datetime created_at
        datetime updated_at
    }
    security__security.return_abuse_patterns {
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        string abuse_type [NOT NULL]
        integer occurrence_count
        datetime first_occurrence
        datetime last_occurrence
        boolean is_blocked
        boolean is_deleted [NOT NULL]
    }
    security__security.return_abuse_patterns ||--o{ accounts__users : has
    suppliers__suppliers.supplier_badge_billing_histories {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer supplier_id [FK, NOT NULL]
        integer badge_id [FK]
        integer catalog_id [FK]
        string billing_reference [UK]
        string charge_type
        numeric amount [NOT NULL]
        string currency [NOT NULL]
        string status [NOT NULL]
        datetime period_start
        datetime period_end
        datetime due_at
        datetime billed_at
        datetime paid_at
        string payment_method
        text notes
        datetime created_at
        datetime updated_at
        string country_code
    }
    suppliers__suppliers.supplier_badge_billing_histories ||--o{ suppliers__supplier_profiles : has
    suppliers__suppliers.supplier_badge_billing_histories ||--o{ suppliers__supplier_badges : has
    suppliers__suppliers.supplier_badge_billing_histories ||--o{ suppliers__supplier_badge_catalogs : has
    suppliers__suppliers.supplier_badge_catalogs {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        string name [UK, NOT NULL]
        string badge_level [NOT NULL]
        text description
        json benefits
        numeric price [NOT NULL]
        string currency [NOT NULL]
        integer validity_days
        boolean is_active [NOT NULL]
        float credibility_weight [NOT NULL]
        datetime created_at
        datetime updated_at
        string country_code
    }
    suppliers__suppliers.supplier_badges {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer supplier_id [FK, NOT NULL]
        integer catalog_id [FK]
        string badge_name [NOT NULL]
        string badge_level [NOT NULL]
        string status [NOT NULL]
        datetime issued_at
        datetime expires_at
        integer assigned_by
        string billing_reference
        float credibility_weight [NOT NULL]
        datetime created_at
        datetime updated_at
        string country_code
    }
    suppliers__suppliers.supplier_badges ||--o{ suppliers__supplier_profiles : has
    suppliers__suppliers.supplier_badges ||--o{ suppliers__supplier_badge_catalogs : has
    suppliers__suppliers.supplier_disputes {
        integer id [PK, NOT NULL]
        integer supplier_id [FK]
        integer order_id
        text reason
        string status
        string country_code
        datetime created_at
    }
    suppliers__suppliers.supplier_disputes ||--o{ accounts__users : has
    suppliers__suppliers.supplier_documents {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer supplier_id [FK, NOT NULL]
        string doc_type [NOT NULL]
        string document_name
        string file_url [NOT NULL]
        string status
        datetime expires_at
        text review_note
        integer reviewed_by
        datetime reviewed_at
        boolean verified
        integer verified_by
        datetime created_at
        datetime updated_at
        string country_code [NOT NULL]
    }
    suppliers__suppliers.supplier_documents ||--o{ suppliers__supplier_profiles : has
    suppliers__suppliers.supplier_fraud_indicators {
        integer id [PK, NOT NULL]
        integer supplier_id [FK, NOT NULL]
        string indicator_type [NOT NULL]
        string value
        boolean is_active
        boolean is_deleted [NOT NULL]
        string country_code
        datetime created_at [NOT NULL]
        datetime updated_at [NOT NULL]
    }
    suppliers__suppliers.supplier_fraud_indicators ||--o{ accounts__users : has
    suppliers__suppliers.supplier_notification_preferences {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer supplier_id [FK, NOT NULL]
        boolean notify_new_order
        boolean notify_low_stock
        boolean notify_payout_processed
        boolean notify_doc_expiry
        boolean notify_return_updates
        boolean notify_dispute_updates
        boolean in_app_enabled
        boolean email_enabled
        boolean push_enabled
        datetime created_at
        datetime updated_at
        string country_code [NOT NULL]
    }
    suppliers__suppliers.supplier_notification_preferences ||--o{ suppliers__supplier_profiles : has
    suppliers__suppliers.supplier_profiles {
        guid uuid [UK]
        integer version [NOT NULL]
        boolean is_deleted [NOT NULL]
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK, NOT NULL]
        integer user_id [FK, NOT NULL]
        string business_name [NOT NULL]
        string country_code
        string address
        string website
        text bio
        text about_us
        string business_type
        text verified_documents
        boolean is_verified
        string verification_status
        numeric credibility_score
        datetime created_at
        datetime updated_at
    }
    suppliers__suppliers.supplier_profiles ||--o{ accounts__users : has
```