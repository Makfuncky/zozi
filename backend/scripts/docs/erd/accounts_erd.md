# ACCOUNTS Schema ERD

```mermaid
erDiagram
    accounts__accounts.addresses {
        integer id [PK]
        integer user_id [FK]
        string label
        string full_name
        string phone
        string address_line1
        string address_line2
        string city
        string state
        string postal_code
        string country
        boolean is_default
        datetime created_at
        datetime updated_at
        string country_code
        boolean is_deleted
    }
    accounts__accounts.addresses ||--o| accounts__users : has
    accounts__accounts.cart_items {
        integer id [PK]
        integer user_id [FK]
        integer product_id [FK]
        integer quantity
        string selected_size
        string selected_color
        integer variant_id
        datetime created_at
        datetime updated_at
        string country_code
        boolean is_deleted
    }
    accounts__accounts.cart_items ||--o| accounts__users : has
    accounts__accounts.cart_items ||--o| catalog__products : has
    accounts__accounts.carts {
        integer id [PK]
        integer user_id [FK]
        datetime created_at
        datetime updated_at
        string country_code
        boolean is_deleted
    }
    accounts__accounts.carts ||--o| accounts__users : has
    accounts__accounts.email_verification_tokens {
        integer id [PK]
        integer user_id [FK]
        string token [UK]
        datetime expires_at
        boolean is_used
        datetime created_at
        datetime updated_at
        string country_code
        boolean is_deleted
    }
    accounts__accounts.email_verification_tokens ||--o| accounts__users : has
    accounts__accounts.logistics_partner_bank_accounts {
        integer id [PK]
        integer partner_id [FK]
        string account_number
        string bank_name
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
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    accounts__accounts.logistics_partner_bank_accounts ||--o| logistics__logistics_partners : has
    accounts__accounts.logistics_partner_bank_accounts ||--o| accounts__users : has
    accounts__accounts.mfa_factors {
        integer id [PK]
        integer user_id [FK]
        enum factor_type
        string secret
        boolean enabled
        datetime created_at
        datetime last_used_at
        json backup_codes
        string country_code
        datetime updated_at
        boolean is_deleted
    }
    accounts__accounts.mfa_factors ||--o| accounts__users : has
    accounts__accounts.ocr_results {
        integer id [PK]
        integer document_verification_id [UK, FK]
        text extracted_text
        numeric confidence_score
        json fields
        datetime processed_at
        datetime created_at
        datetime updated_at
        string country_code
        boolean is_deleted
    }
    accounts__accounts.ocr_results ||--o| security__document_verifications : has
    accounts__accounts.otp_codes {
        integer id [PK]
        integer user_id [FK]
        string purpose
        string channel
        string destination
        string code_hash
        datetime expires_at
        integer attempts
        boolean verified
        string country_code [FK]
        datetime created_at
        datetime updated_at
        boolean is_deleted
    }
    accounts__accounts.otp_codes ||--o| accounts__users : has
    accounts__accounts.otp_codes ||--o| country__country_configs : has
    accounts__accounts.password_histories {
        integer id [PK]
        integer user_id [FK]
        string password_hash
        datetime created_at
        string country_code
        datetime updated_at
        boolean is_deleted
    }
    accounts__accounts.password_histories ||--o| accounts__users : has
    accounts__accounts.password_reset_tokens {
        integer id [PK]
        integer user_id [FK]
        string token [UK]
        datetime expires_at
        boolean is_used
        datetime created_at
        datetime updated_at
        string country_code
        boolean is_deleted
    }
    accounts__accounts.password_reset_tokens ||--o| accounts__users : has
    accounts__accounts.refresh_token_families {
        integer id [PK]
        integer user_id [FK]
        guid family_id
        datetime created_at
        datetime updated_at
        datetime revoked_at
        datetime reused_at
        string ip_address
        string user_agent
        string country_code
        boolean is_deleted
    }
    accounts__accounts.refresh_token_families ||--o| accounts__users : has
    accounts__accounts.revoked_tokens {
        integer id [PK]
        integer user_id [FK]
        string token [UK]
        datetime expires_at
        datetime revoked_at
        datetime updated_at
        string country_code
        boolean is_deleted
    }
    accounts__accounts.revoked_tokens ||--o| accounts__users : has
    accounts__accounts.social_identities {
        integer id [PK]
        integer user_id [FK]
        string provider
        string provider_user_id
        string email
        string full_name
        json raw_data
        datetime created_at
        datetime updated_at
        string country_code
        boolean is_deleted
    }
    accounts__accounts.social_identities ||--o| accounts__users : has
    accounts__accounts.supplier_bank_accounts {
        integer id [PK]
        integer supplier_id [FK]
        string account_number
        string bank_name
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
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    accounts__accounts.supplier_bank_accounts ||--o| accounts__users : has
    accounts__accounts.supplier_bank_accounts ||--o| accounts__users : has
    accounts__accounts.user_consents {
        integer id [PK]
        integer user_id [FK]
        string consent_type
        boolean granted
        datetime granted_at
        datetime revoked_at
        string ip_address
        string user_agent
        string consent_version
        string country_code
        datetime created_at
        datetime updated_at
        boolean is_deleted
    }
    accounts__accounts.user_consents ||--o| accounts__users : has
    accounts__accounts.user_devices {
        integer id [PK]
        integer user_id [FK]
        string device_fingerprint
        string fingerprint_hash
        string device_id
        boolean is_active
        datetime created_at
        datetime updated_at
        string country_code
        boolean is_deleted
    }
    accounts__accounts.user_devices ||--o| accounts__users : has
    accounts__accounts.user_login_histories {
        integer id [PK]
        integer user_id [FK]
        string ip_address
        text user_agent
        boolean success
        datetime created_at
        datetime updated_at
        string country_code
        boolean is_deleted
    }
    accounts__accounts.user_login_histories ||--o| accounts__users : has
    accounts__accounts.user_preferences {
        integer id [PK]
        integer user_id [FK]
        string key
        json value
        datetime updated_at
        string country_code
        datetime created_at
        boolean is_deleted
    }
    accounts__accounts.user_preferences ||--o| accounts__users : has
    accounts__accounts.user_sessions {
        integer id [PK]
        integer user_id [FK]
        string token_jti
        string refresh_token_jti
        string ip_address
        text user_agent
        string device_fingerprint
        boolean is_active
        datetime expires_at
        datetime created_at
        datetime updated_at
        string country_code
        boolean is_deleted
    }
    accounts__accounts.user_sessions ||--o| accounts__users : has
    accounts__accounts.users {
        integer id [PK]
        string email [UK]
        string hashed_password
        string full_name
        string role
        string country_code
        boolean is_active
        boolean email_verified
        text staff_country_codes
        integer referred_by_user_id [FK]
        datetime created_at
        datetime updated_at
        boolean is_deleted
        string profile_image
        string phone
        string referral_code [UK]
        integer referral_points
        integer sharing_points
        string preferred_language
        string preferred_currency
        string preferred_country
    }
    accounts__accounts.users ||--o| accounts__users : has
```