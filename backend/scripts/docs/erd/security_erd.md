# SECURITY Schema ERD

```mermaid
erDiagram
    security__security.alert_escalation_rules {
        integer id [PK]
        string alert_type
        string severity
        numeric threshold_value
        integer current_tier
        boolean is_active
        boolean is_deleted
        string country_code [FK]
        datetime created_at
        datetime updated_at
    }
    security__security.alert_escalation_rules ||--o| country__country_configs : has
    security__security.credit_card_bins {
        integer id [PK]
        string bin [UK]
        string brand
        string bank
        string country
        boolean is_blacklisted
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    security__security.device_fingerprints {
        integer id [PK]
        integer user_id [FK]
        string fingerprint_hash
        string user_agent
        text ip_addresses
        boolean is_trusted
        boolean is_blocked
        integer risk_score
        integer headless_attempts
        integer account_count
        datetime first_seen_at
        datetime last_seen_at
        boolean is_deleted
    }
    security__security.device_fingerprints ||--o| accounts__users : has
    security__security.dlp_violations {
        integer id [PK]
        string violation_type
        string severity
        integer sender_id [FK]
        string recipient_email
        text detected_content
        string action_taken
        string status_code
        integer reviewed_by_id [FK]
        datetime reviewed_at
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    security__security.dlp_violations ||--o| accounts__users : has
    security__security.dlp_violations ||--o| accounts__users : has
    security__security.document_verifications {
        integer id [PK]
        integer pipeline_id [FK]
        string document_type
        json document_data
        string status
        datetime verified_at
        integer verifier_id [FK]
        boolean is_deleted
        string country_code [FK]
        datetime created_at
        datetime updated_at
    }
    security__security.document_verifications ||--o| hr__onboarding_pipelines : has
    security__security.document_verifications ||--o| accounts__users : has
    security__security.document_verifications ||--o| country__country_configs : has
    security__security.fraud_alerts {
        integer id [PK]
        string alert_type
        string entity_type
        integer entity_id
        numeric fraud_score
        text triggered_rules
        string priority
        text details
        boolean is_resolved
        datetime resolved_at
        boolean is_deleted
        datetime created_at
        string country_code
    }
    security__security.fraud_blacklists {
        integer id [PK]
        string identifier_type
        string identifier_value
        string identifier_value_hash
        string reason
        boolean is_active
        string status_code
        datetime created_at
        boolean is_deleted
        datetime expires_at
    }
    security__security.fraud_case_assignments {
        integer id [PK]
        integer case_id [FK]
        integer assigned_to_id [FK]
        integer assigned_by_id [FK]
        string role_at_assignment
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    security__security.fraud_case_assignments ||--o| security__fraud_cases : has
    security__security.fraud_case_assignments ||--o| accounts__users : has
    security__security.fraud_case_assignments ||--o| accounts__users : has
    security__security.fraud_cases {
        integer id [PK]
        string case_number [UK]
        string title
        text description
        integer fraud_score
        string priority
        string status_code
        string entity_type
        integer entity_id
        integer assigned_to_id [FK]
        integer created_by_id [FK]
        datetime resolved_at
        text resolution_notes
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    security__security.fraud_cases ||--o| accounts__users : has
    security__security.fraud_cases ||--o| accounts__users : has
    security__security.fraud_events {
        integer id [PK]
        integer user_id [FK]
        integer order_id [FK]
        string event_type
        string ip_address
        string device_hash
        string session_id
        numeric fraud_score
        text triggered_rules
        json details
        boolean is_flagged
        string status_code
        integer reviewed_by_id [FK]
        datetime reviewed_at
        boolean is_deleted
        datetime created_at
        string country_code
    }
    security__security.fraud_events ||--o| accounts__users : has
    security__security.fraud_events ||--o| orders__orders : has
    security__security.fraud_events ||--o| accounts__users : has
    security__security.fraud_rules {
        integer id [PK]
        string rule_key [UK]
        string name
        text description
        integer weight
        text condition_json
        string action
        boolean is_active
        boolean is_global
        string country_code
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    security__security.fraud_scoring_logs {
        integer id [PK]
        string event_type
        integer user_id [FK]
        integer order_id [FK]
        string ip_address
        string device_hash
        string session_id
        integer raw_score
        json triggered_rules
        json metadata_json
        string action_taken
        boolean is_deleted
        datetime created_at
        string country_code
    }
    security__security.fraud_scoring_logs ||--o| accounts__users : has
    security__security.fraud_scoring_logs ||--o| orders__orders : has
    security__security.fraud_velocity_counters {
        integer id [PK]
        string key
        integer count
        datetime window_start
        datetime window_end
        string entity_type
        integer entity_id
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    security__security.ip_account_linkages {
        integer id [PK]
        string ip_address
        integer user_id [FK]
        string device_fingerprint
        string session_id
        integer interaction_count
        boolean is_suspicious
        datetime last_seen
        boolean is_deleted
    }
    security__security.ip_account_linkages ||--o| accounts__users : has
    security__security.ip_reputations {
        integer id [PK]
        string ip_address
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
        boolean is_deleted
    }
    security__security.kyc_verifications {
        integer id [PK]
        integer user_id [FK]
        string status
        string provider
        json verification_data
        json document_types
        datetime submitted_at
        datetime reviewed_at
        integer reviewer_id [FK]
        boolean is_deleted
        string country_code [FK]
        datetime created_at
        datetime updated_at
    }
    security__security.kyc_verifications ||--o| accounts__users : has
    security__security.kyc_verifications ||--o| accounts__users : has
    security__security.kyc_verifications ||--o| country__country_configs : has
    security__security.logistics_fraud_indicators {
        integer id [PK]
        integer partner_id [FK]
        string indicator_type
        string value
        boolean is_active
        boolean is_deleted
        datetime created_at
        string country_code
    }
    security__security.logistics_fraud_indicators ||--o| logistics__logistics_partners : has
    security__security.manual_review_queues {
        integer id [PK]
        string entity_type
        integer entity_id
        integer fraud_score
        text triggered_rules
        string reason
        string priority
        integer assigned_to_id [FK]
        text admin_notes
        string status_code
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    security__security.manual_review_queues ||--o| accounts__users : has
    security__security.meeting_action_items {
        integer id [PK]
        integer meeting_id [FK]
        string entity_type
        integer entity_id
        string action
        json metadata_json
        string status_code
        integer assigned_to_id [FK]
        boolean is_deleted
        datetime created_at
        datetime due_date
    }
    security__security.meeting_action_items ||--o| security__meeting_transcripts : has
    security__security.meeting_action_items ||--o| accounts__users : has
    security__security.meeting_transcripts {
        integer id [PK]
        string room_id
        string language
        json segments
        json action_items
        text summary
        integer word_count
        integer duration_seconds
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    security__security.return_abuse_patterns {
        integer id [PK]
        integer user_id [FK]
        string abuse_type
        integer occurrence_count
        datetime first_occurrence
        datetime last_occurrence
        boolean is_blocked
        boolean is_deleted
    }
    security__security.return_abuse_patterns ||--o| accounts__users : has
```