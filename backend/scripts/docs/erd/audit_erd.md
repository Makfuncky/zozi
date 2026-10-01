# AUDIT Schema ERD

```mermaid
erDiagram
    audit__audit.audit_logs {
        integer id [PK]
        string action
        string entity_type
        integer entity_id
        integer user_id [FK]
        string username
        string user_role
        json details
        string ip_address
        boolean is_deleted
        string country_code [FK]
        datetime created_at
        datetime updated_at
    }
    audit__audit.audit_logs ||--o| accounts__users : has
    audit__audit.audit_logs ||--o| country__country_configs : has
    audit__audit.command_center_views {
        integer id [PK]
        integer user_id [FK]
        string view_name
        json config
        boolean is_default
        boolean is_deleted
        string country_code [FK]
        datetime created_at
        datetime updated_at
    }
    audit__audit.command_center_views ||--o| accounts__users : has
    audit__audit.command_center_views ||--o| country__country_configs : has
```