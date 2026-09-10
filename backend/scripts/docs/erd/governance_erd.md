# GOVERNANCE Schema ERD

```mermaid
erDiagram
    governance__governance.admin_activity_logs {
        integer id [PK]
        integer admin_id [FK]
        string action
        json details
        string ip_address
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    governance__governance.admin_activity_logs ||--o| accounts__users : has
    governance__governance.admin_analytics_snapshots {
        integer id [PK]
        string snapshot_key
        string snapshot_group
        string period
        text payload_json
        datetime computed_at
        datetime expires_at
        boolean is_deleted
        string country_code
    }
    governance__governance.admin_change_audit_logs {
        integer id [PK]
        integer admin_id [FK]
        string action
        string entity
        string entity_key
        text before_json
        text after_json
        text notes
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    governance__governance.admin_change_audit_logs ||--o| accounts__users : has
    governance__governance.api_keys {
        integer id [PK]
        string name
        string key_hash
        json permissions
        boolean is_active
        datetime expires_at
        integer created_by_id [FK]
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    governance__governance.api_keys ||--o| accounts__users : has
    governance__governance.badge_billing_records {
        integer id [PK]
        integer user_id [FK]
        integer supplier_id [FK]
        string billing_reference [UK]
        string badge_level
        string charge_type
        string charge_source
        numeric amount
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
        datetime created_at
        datetime updated_at
        string country_code
        boolean is_deleted
    }
    governance__governance.badge_billing_records ||--o| accounts__users : has
    governance__governance.badge_billing_records ||--o| accounts__users : has
    governance__governance.badge_billing_records ||--o| finance__bank_transactions : has
    governance__governance.badge_tiers {
        integer id [PK]
        string name
        integer min_points
        json benefits
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    governance__governance.badge_transactions {
        integer id [PK]
        integer user_id [FK]
        numeric amount
        string transaction_type
        string reference_id
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    governance__governance.badge_transactions ||--o| accounts__users : has
    governance__governance.chatbot_query_events {
        integer id [PK]
        integer user_id [FK]
        string session_id
        string event_type
        text message
        string normalized_query
        string intent
        text filters_json
        integer result_count
        text product_ids_json
        integer clicked_product_id [FK]
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    governance__governance.chatbot_query_events ||--o| accounts__users : has
    governance__governance.chatbot_query_events ||--o| catalog__products : has
    governance__governance.commission_badge_tiers {
        integer id [PK]
        string name
        string badge_level [UK]
        numeric commission_rate
        numeric setup_fee
        numeric recurring_fee
        string recurring_interval
        text benefits_json
        integer min_fulfilled_orders
        numeric min_monthly_revenue
        integer sort_order
        boolean is_active
        boolean is_deleted
        integer updated_by_id [FK]
        datetime created_at
        datetime updated_at
        string country_code
    }
    governance__governance.commission_badge_tiers ||--o| accounts__users : has
    governance__governance.commission_global_configs {
        integer id [PK]
        numeric default_rate
        numeric low_value_threshold
        numeric fixed_cap_amount
        boolean fixed_cap_enabled
        boolean margin_protection_enabled
        numeric margin_threshold
        boolean is_deleted
        integer updated_by_id [FK]
        datetime updated_at
        datetime created_at
        string country_code
    }
    governance__governance.commission_global_configs ||--o| accounts__users : has
    governance__governance.email_provider_configs {
        integer id [PK]
        string provider
        boolean is_active
        integer updated_by_id [FK]
        datetime created_at
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
        boolean is_deleted
        string country_code
    }
    governance__governance.email_provider_configs ||--o| accounts__users : has
    governance__governance.employee_expenses {
        integer id [PK]
        integer employee_id [FK]
        string expense_type
        numeric amount
        text description
        string status
        integer approved_by_id [FK]
        datetime approved_at
        string receipt_url
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    governance__governance.employee_expenses ||--o| hr__employees : has
    governance__governance.employee_expenses ||--o| accounts__users : has
    governance__governance.finance_bank_accounts {
        integer id [PK]
        string account_name
        string account_number
        string bank_name
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
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    governance__governance.finance_bank_accounts ||--o| accounts__users : has
    governance__governance.finance_bank_accounts ||--o| accounts__users : has
    governance__governance.legal_contract_templates {
        integer id [PK]
        string country_code [FK]
        string template_type
        string version
        text content
        boolean is_active
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    governance__governance.legal_contract_templates ||--o| country__country_configs : has
    governance__governance.logistics_cod_remittance_receipts {
        integer id [PK]
        integer partner_id [FK]
        integer shipment_id [FK]
        integer settlement_id [FK]
        numeric amount
        string bank_reference
        string receipt_file_url
        text notes
        text review_note
        integer reviewed_by_id [FK]
        string status
        string currency
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    governance__governance.logistics_cod_remittance_receipts ||--o| logistics__logistics_partners : has
    governance__governance.logistics_cod_remittance_receipts ||--o| logistics__shipments : has
    governance__governance.logistics_cod_remittance_receipts ||--o| governance__logistics_settlements : has
    governance__governance.logistics_cod_remittance_receipts ||--o| accounts__users : has
    governance__governance.logistics_partner_documents {
        integer id [PK]
        integer partner_id [FK]
        string doc_type
        string file_url
        integer reviewed_by_id [FK]
        boolean is_verified
        datetime verified_at
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    governance__governance.logistics_partner_documents ||--o| logistics__logistics_partners : has
    governance__governance.logistics_partner_documents ||--o| accounts__users : has
    governance__governance.logistics_settlements {
        integer id [PK]
        integer partner_id [FK]
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
        boolean is_deleted
        integer payout_id [FK]
        integer bank_transaction_id
        datetime created_at
        datetime updated_at
        string country_code
    }
    governance__governance.logistics_settlements ||--o| logistics__logistics_partners : has
    governance__governance.logistics_settlements ||--o| orders__orders : has
    governance__governance.logistics_settlements ||--o| logistics__shipments : has
    governance__governance.logistics_settlements ||--o| finance__payouts : has
    governance__governance.normalized_webhook_events {
        integer id [PK]
        string provider_code
        string gateway_event_id
        string event_type
        string status
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
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    governance__governance.payment_provider_configs {
        integer id [PK]
        string provider_name
        json config
        boolean is_active
        boolean is_deleted
        integer updated_by_id [FK]
        datetime created_at
        datetime updated_at
        string country_code
    }
    governance__governance.payment_provider_configs ||--o| accounts__users : has
    governance__governance.processed_webhook_events {
        integer id [PK]
        string processor
        string event_id
        string payload_hash
        datetime processed_at
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    governance__governance.product_verifications {
        integer id [PK]
        integer product_id [FK]
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
        datetime created_at
        datetime updated_at
        integer order_id [FK]
        boolean is_deleted
        string country_code
    }
    governance__governance.product_verifications ||--o| catalog__products : has
    governance__governance.product_verifications ||--o| accounts__users : has
    governance__governance.product_verifications ||--o| logistics__shipments : has
    governance__governance.product_verifications ||--o| orders__orders : has
    governance__governance.promotion_order_tiers {
        integer id [PK]
        integer promotion_id
        string tier_name
        numeric min_order_amount
        numeric max_order_amount
        string discount_type
        numeric discount_amount
        numeric discount_value
        boolean stacking_allowed
        boolean is_active
        integer sort_order
        integer updated_by_id [FK]
        boolean is_deleted
        string country_code [FK]
        datetime created_at
        datetime updated_at
    }
    governance__governance.promotion_order_tiers ||--o| accounts__users : has
    governance__governance.promotion_order_tiers ||--o| country__country_configs : has
    governance__governance.push_notification_tokens {
        integer id [PK]
        integer user_id [FK]
        string token
        string device_type
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    governance__governance.push_notification_tokens ||--o| accounts__users : has
    governance__governance.retention_job_runs {
        integer id [PK]
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
        boolean is_deleted
        string country_code
        datetime created_at
        datetime updated_at
    }
    governance__governance.role_permission_settings {
        integer id [PK]
        string role
        json permissions_json
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    governance__governance.shipment_confirmations {
        integer id [PK]
        integer shipment_id [FK]
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
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    governance__governance.shipment_confirmations ||--o| logistics__shipments : has
    governance__governance.shipment_confirmations ||--o| orders__orders : has
    governance__governance.shipment_confirmations ||--o| accounts__users : has
    governance__governance.shipment_confirmations ||--o| accounts__users : has
    governance__governance.shipment_confirmations ||--o| accounts__users : has
    governance__governance.shipping_carriers {
        integer id [PK]
        integer supplier_id [FK]
        string name
        string code [UK]
        boolean is_active
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    governance__governance.shipping_carriers ||--o| accounts__users : has
    governance__governance.shipping_zones {
        integer id [PK]
        integer supplier_id [FK]
        string name
        json countries
        boolean is_active
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    governance__governance.shipping_zones ||--o| accounts__users : has
    governance__governance.supplier_country_commissions {
        integer id [PK]
        integer supplier_id [FK]
        string country_code
        numeric commission_rate
        string category_slug
        text notes
        boolean is_active
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    governance__governance.supplier_country_commissions ||--o| accounts__users : has
    governance__governance.system_alerts {
        integer id [PK]
        string alert_type
        string severity
        string title
        text message
        boolean is_acknowledged
        integer acknowledged_by_id [FK]
        datetime acknowledged_at
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    governance__governance.system_alerts ||--o| accounts__users : has
    governance__governance.system_health_events {
        integer id [PK]
        string service
        string metric_name
        numeric metric_value
        string severity
        text message
        datetime created_at
        datetime updated_at
        boolean is_deleted
        string country_code [FK]
    }
    governance__governance.system_health_events ||--o| country__country_configs : has
    governance__governance.system_settings {
        integer id [PK]
        string key [UK]
        text value
        string value_type
        string description
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    governance__governance.ticket_replies {
        integer id [PK]
        integer ticket_id [FK]
        integer sender_id [FK]
        text message
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    governance__governance.ticket_replies ||--o| comms__support_tickets : has
    governance__governance.ticket_replies ||--o| accounts__users : has
    governance__governance.user_browsing_histories {
        integer id [PK]
        integer user_id [FK]
        integer product_id [FK]
        datetime viewed_at
        boolean is_deleted
        string country_code [FK]
        datetime created_at
        datetime updated_at
    }
    governance__governance.user_browsing_histories ||--o| accounts__users : has
    governance__governance.user_browsing_histories ||--o| catalog__products : has
    governance__governance.user_browsing_histories ||--o| country__country_configs : has
```