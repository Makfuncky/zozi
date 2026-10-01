# COUNTRY Schema ERD

```mermaid
erDiagram
    country__country.country_basics {
        guid uuid [UK]
        integer version
        datetime deleted_at
        integer deleted_by
        integer id [PK]
        string code [UK]
        string name
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
    country__country.country_basics ||--o| country__country_configs : has
    country__country.country_category_tax_rates {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string country_code [FK]
        integer category_id
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
    country__country.country_category_tax_rates ||--o| country__country_configs : has
    country__country.country_cities {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string country_code [FK]
        string name
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
    country__country.country_cities ||--o| country__country_configs : has
    country__country.country_commission_rate_histories {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string country_code
        integer category_id
        string supplier_tier
        numeric rate_percent
        datetime effective_from
        datetime effective_to
        integer changed_by
        text change_reason
        datetime created_at
    }
    country__country.country_commission_rates {
        guid uuid [UK]
        integer version
        datetime created_at
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string country_code [FK]
        string supplier_tier
        string name
        numeric rate_percent
        numeric fixed_fee
        datetime effective_from
        datetime effective_to
    }
    country__country.country_commission_rates ||--o| country__country_configs : has
    country__country.country_communication_threads {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string country_code
        string entity_type
        integer entity_id
        text participants
        boolean is_active
        datetime last_message_at
        datetime created_at
    }
    country__country.country_communications {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string country_code [FK]
        integer from_user_id
        integer to_user_id
        string subject
        text body
        string priority
        string category
        string status
        string related_entity_type
        integer related_entity_id
        datetime read_at
        text attachments_json
        datetime created_at
    }
    country__country.country_communications ||--o| country__country_configs : has
    country__country.country_config_versions {
        guid uuid [UK]
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string country_code [FK]
        string config_type
        integer version
        text payload_json
        string status
        integer draft_by
        integer approved_by
        datetime published_at
        datetime effective_from
        datetime created_at
        datetime updated_at
    }
    country__country.country_config_versions ||--o| country__country_configs : has
    country__country.country_configs {
        guid uuid [UK]
        integer version
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer basics_id [FK]
        string code [UK]
        string name
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
    country__country.country_configs ||--o| country__country_basics : has
    country__country.country_economics {
        datetime deleted_at
        integer deleted_by
        integer id [PK]
        string uuid [UK]
        integer version
        string country_code [UK, FK]
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
    country__country.country_economics ||--o| country__country_configs : has
    country__country.country_feature_flags {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string country_code [FK]
        string feature_key
        string feature_name
        boolean is_enabled
        text config
        string rollout_audience
        text notes
        datetime created_at
        datetime updated_at
    }
    country__country.country_feature_flags ||--o| country__country_configs : has
    country__country.country_gateway_configs {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string country_code
        string gateway_id
        string gateway_name
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
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string country_code [FK]
        string gateway_name
        string environment
        json credentials
        boolean is_active
        datetime created_at
    }
    country__country.country_gateway_credentials ||--o| country__country_configs : has
    country__country.country_holiday_calendars {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string country_code
        datetime holiday_date
        string name
        string local_name
        boolean is_observed
        datetime created_at
    }
    country__country.country_legal_contracts {
        guid uuid [UK]
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string country_code
        string contract_type
        string version
        text content_html
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    country__country.country_legals {
        datetime deleted_at
        integer deleted_by
        integer id [PK]
        string uuid [UK]
        integer version
        string country_code [UK, FK]
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
    country__country.country_legals ||--o| country__country_configs : has
    country__country.country_localizations {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string country_code [UK]
        string default_numeral_system
        boolean hijri_calendar_enabled
        boolean rtl_layout_enabled
        string address_format
        datetime created_at
        datetime updated_at
    }
    country__country.country_logistics_zones {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string country_code
        string zone_code
        string zone_name
        string zone_type
        text cities
        text pricing_config
        boolean is_active
        datetime created_at
    }
    country__country.country_map_configs {
        integer id [PK]
        string country_code [UK, FK]
        string map_provider
        string api_key_ref
        integer default_zoom
        boolean show_regions
        boolean show_cities
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    country__country.country_map_configs ||--o| country__country_configs : has
    country__country.country_payment_aliases {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string country_code
        string alias_type
        string alias_value
        boolean is_active
        datetime created_at
    }
    country__country.country_payout_rules {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string country_code
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
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer user_id
        string country_code [FK]
        string role_in_country
        boolean is_active
        integer assigned_by
        text notes
        datetime created_at
        datetime updated_at
    }
    country__country.country_staff_assignments ||--o| country__country_configs : has
    country__country.country_taxes {
        datetime deleted_at
        integer deleted_by
        integer id [PK]
        string uuid [UK]
        string country_code [UK, FK]
        boolean is_active
        boolean is_deleted
        integer version
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
    country__country.country_taxes ||--o| country__country_configs : has
    country__country.data_residency_records {
        integer id [PK]
        string country_code [FK]
        string data_type
        string storage_location
        boolean cross_border_allowed
        string compliance_status
        datetime last_audit_at
        datetime next_audit_at
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    country__country.data_residency_records ||--o| country__country_configs : has
    country__country.logistics_partner_kyc_requirements {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string country_code [UK, FK]
        integer min_experience_months
        text required_documents
        boolean insurance_required
        numeric insurance_min_coverage
        text vehicle_requirements
        boolean background_check_required
        datetime created_at
        datetime updated_at
    }
    country__country.logistics_partner_kyc_requirements ||--o| country__country_configs : has
    country__country.logistics_partner_locations {
        integer id [PK]
        integer partner_id [FK]
        string country_code [FK]
        string location_type
        float latitude
        float longitude
        text address
        boolean is_active
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    country__country.logistics_partner_locations ||--o| logistics__logistics_partners : has
    country__country.logistics_partner_locations ||--o| country__country_configs : has
    country__country.oman_delivery_zones {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string zone_code [UK]
        string zone_name
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
        integer id [PK]
        integer parcel_id [FK]
        string country_code [FK]
        float latitude
        float longitude
        string location_name
        datetime timestamp
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    country__country.parcel_location_trackers ||--o| logistics__shipments : has
    country__country.parcel_location_trackers ||--o| country__country_configs : has
    country__country.payment_orchestrator_syncs {
        integer id [PK]
        string country_code [FK]
        string gateway_id
        string gateway_name
        string environment
        boolean is_active
        numeric fee_percent
        numeric fee_fixed
        text supported_payment_methods
        datetime last_sync_at
        string status
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    country__country.payment_orchestrator_syncs ||--o| country__country_configs : has
    country__country.shift_handover_logs {
        integer id [PK]
        integer user_id [FK]
        string country_code [FK]
        datetime shift_start
        datetime shift_end
        text notes
        integer handover_to_user_id [FK]
        text handover_notes
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    country__country.shift_handover_logs ||--o| accounts__users : has
    country__country.shift_handover_logs ||--o| country__country_configs : has
    country__country.shift_handover_logs ||--o| accounts__users : has
    country__country.shop_warehouse_locations {
        integer id [PK]
        string country_code [FK]
        string name
        string warehouse_code
        float latitude
        float longitude
        text address
        boolean is_active
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    country__country.shop_warehouse_locations ||--o| country__country_configs : has
    country__country.supplier_kyc_requirements {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string country_code [UK, FK]
        string kyc_tier_required
        text document_types_required
        integer verification_wait_days
        numeric auto_approve_threshold
        datetime created_at
        datetime updated_at
    }
    country__country.supplier_kyc_requirements ||--o| country__country_configs : has
    country__country.supplier_onboarding_syncs {
        integer id [PK]
        string country_code [FK]
        integer supplier_id [FK]
        string kyc_status
        text kyc_documents
        boolean onboarding_fee_paid
        string monthly_fee_status
        string status
        text notes
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    country__country.supplier_onboarding_syncs ||--o| country__country_configs : has
    country__country.supplier_onboarding_syncs ||--o| accounts__users : has
```