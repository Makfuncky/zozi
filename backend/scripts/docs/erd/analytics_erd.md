# ANALYTICS Schema ERD

```mermaid
erDiagram
    analytics__analytics.executive_news {
        integer id [PK]
        string title
        text summary
        text content
        string url
        string category
        string priority
        boolean is_published
        string ai_sentiment
        datetime published_at
        boolean is_deleted
        string country_code
        datetime created_at
        datetime updated_at
        string uuid [UK]
        integer version
        integer created_by_id
        integer updated_by_id
        datetime deleted_at
        integer deleted_by_id
    }
    analytics__analytics.predictive_simulations {
        integer id [PK]
        string simulation_type
        text parameters_json
        text result_json
        boolean is_deleted
        string country_code
        datetime created_at
        datetime updated_at
        string uuid [UK]
        integer version
        integer created_by_id
        integer updated_by_id
        datetime deleted_at
        integer deleted_by_id
    }
```