# CUSTOMERS Schema ERD

```mermaid
erDiagram
    customers__customers.cross_country_customer_sessions {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer user_id
        string source_country_code
        string target_country_code
        text session_data
        boolean conversion
        integer order_id
        string ip_address
        string user_agent
        datetime created_at
    }
    customers__customers.referral_point_events {
        integer id [PK]
        integer user_id [FK]
        string event_type
        integer points
        integer referred_user_id [FK]
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    customers__customers.referral_point_events ||--o| accounts__users : has
    customers__customers.referral_point_events ||--o| accounts__users : has
    customers__customers.referrals {
        integer id [PK]
        integer referrer_id [FK]
        integer referred_id [UK, FK]
        string referral_code [UK]
        string status
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    customers__customers.referrals ||--o| accounts__users : has
    customers__customers.referrals ||--o| accounts__users : has
```