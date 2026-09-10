# SUPPLIERS Schema ERD

```mermaid
erDiagram
    suppliers__suppliers.supplier_badge_billing_histories {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer supplier_id [FK]
        integer badge_id [FK]
        integer catalog_id [FK]
        string billing_reference [UK]
        string charge_type
        numeric amount
        string currency
        string status
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
    suppliers__suppliers.supplier_badge_billing_histories ||--o| suppliers__supplier_profiles : has
    suppliers__suppliers.supplier_badge_billing_histories ||--o| suppliers__supplier_badges : has
    suppliers__suppliers.supplier_badge_billing_histories ||--o| suppliers__supplier_badge_catalogs : has
    suppliers__suppliers.supplier_badge_catalogs {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string name [UK]
        string badge_level
        text description
        json benefits
        numeric price
        string currency
        integer validity_days
        boolean is_active
        float credibility_weight
        datetime created_at
        datetime updated_at
        string country_code
    }
    suppliers__suppliers.supplier_badges {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer supplier_id [FK]
        integer catalog_id [FK]
        string badge_name
        string badge_level
        string status
        datetime issued_at
        datetime expires_at
        integer assigned_by
        string billing_reference
        float credibility_weight
        datetime created_at
        datetime updated_at
        string country_code
    }
    suppliers__suppliers.supplier_badges ||--o| suppliers__supplier_profiles : has
    suppliers__suppliers.supplier_badges ||--o| suppliers__supplier_badge_catalogs : has
    suppliers__suppliers.supplier_disputes {
        integer id [PK]
        integer supplier_id [FK]
        integer order_id
        text reason
        string status
        string country_code
        datetime created_at
    }
    suppliers__suppliers.supplier_disputes ||--o| accounts__users : has
    suppliers__suppliers.supplier_documents {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer supplier_id [FK]
        string doc_type
        string document_name
        string file_url
        string status
        datetime expires_at
        text review_note
        integer reviewed_by
        datetime reviewed_at
        boolean verified
        integer verified_by
        datetime created_at
        datetime updated_at
        string country_code
    }
    suppliers__suppliers.supplier_documents ||--o| suppliers__supplier_profiles : has
    suppliers__suppliers.supplier_fraud_indicators {
        integer id [PK]
        integer supplier_id [FK]
        string indicator_type
        string value
        boolean is_active
        boolean is_deleted
        string country_code
        datetime created_at
        datetime updated_at
    }
    suppliers__suppliers.supplier_fraud_indicators ||--o| accounts__users : has
    suppliers__suppliers.supplier_notification_preferences {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer supplier_id [FK]
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
        string country_code
    }
    suppliers__suppliers.supplier_notification_preferences ||--o| suppliers__supplier_profiles : has
    suppliers__suppliers.supplier_profiles {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer user_id [FK]
        string business_name
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
    suppliers__suppliers.supplier_profiles ||--o| accounts__users : has
```