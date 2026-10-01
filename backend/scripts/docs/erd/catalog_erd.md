# CATALOG Schema ERD

```mermaid
erDiagram
    catalog__catalog.ai_generation_logs {
        integer id [PK]
        integer job_id [FK]
        string field
        string model_used
        string prompt_hash
        numeric tokens_used
        numeric cost
        numeric confidence
        string country_code
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    catalog__catalog.ai_generation_logs ||--o| catalog__ai_upload_jobs : has
    catalog__catalog.ai_staging_products {
        integer id [PK]
        integer job_id [FK]
        integer product_id [FK]
        string name
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
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    catalog__catalog.ai_staging_products ||--o| catalog__ai_upload_jobs : has
    catalog__catalog.ai_staging_products ||--o| catalog__products : has
    catalog__catalog.ai_staging_variants {
        integer id [PK]
        integer job_id [FK]
        integer staging_product_id [FK]
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
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    catalog__catalog.ai_staging_variants ||--o| catalog__ai_upload_jobs : has
    catalog__catalog.ai_staging_variants ||--o| catalog__ai_staging_products : has
    catalog__catalog.ai_upload_jobs {
        integer id [PK]
        integer supplier_id [FK]
        string status
        string model_used
        string prompt_hash
        numeric tokens_used
        text source_media_json
        integer created_product_id [FK]
        text error_log
        string country_code
        boolean is_deleted
        datetime created_at
        datetime updated_at
    }
    catalog__catalog.ai_upload_jobs ||--o| accounts__users : has
    catalog__catalog.ai_upload_jobs ||--o| catalog__products : has
    catalog__catalog.categories {
        integer id [PK]
        string name
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
        datetime created_at
        datetime updated_at
        string country_code
        boolean is_deleted
        string path
        integer depth
    }
    catalog__catalog.categories ||--o| catalog__categories : has
    catalog__catalog.product_filter_metadatas {
        integer id [PK]
        integer category_id [FK]
        string filter_name
        string filter_type
        integer display_order
        boolean is_active
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    catalog__catalog.product_filter_metadatas ||--o| catalog__categories : has
    catalog__catalog.product_filter_options {
        integer id [PK]
        integer filter_metadata_id [FK]
        string option_value
        string option_display_name
        integer product_count
        integer sort_order
        boolean is_deleted
        string country_code
        datetime created_at
        datetime updated_at
    }
    catalog__catalog.product_filter_options ||--o| catalog__product_filter_metadatas : has
    catalog__catalog.product_variants {
        integer id [PK]
        integer product_id [FK]
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
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code [FK]
        string variant_key
    }
    catalog__catalog.product_variants ||--o| catalog__products : has
    catalog__catalog.product_variants ||--o| country__country_configs : has
    catalog__catalog.product_videos {
        integer id [PK]
        integer product_id [FK]
        string video_url
        string thumbnail_url
        integer duration_seconds
        string video_type
        string title
        text description
        integer views_count
        boolean is_featured
        string upload_status
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    catalog__catalog.product_videos ||--o| catalog__products : has
    catalog__catalog.products {
        integer id [PK]
        string name
        string slug [UK]
        text description
        text short_description
        text ai_description
        string sku [UK]
        string barcode [UK]
        numeric price
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
        datetime created_at
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
    catalog__catalog.products ||--o| catalog__categories : has
    catalog__catalog.products ||--o| accounts__users : has
    catalog__catalog.products ||--o| country__country_configs : has
    catalog__catalog.reviews {
        integer id [PK]
        integer product_id [FK]
        integer user_id [FK]
        integer rating
        string title
        text comment
        string image_url
        boolean is_approved
        boolean is_deleted
        boolean is_verified_purchase
        datetime created_at
        datetime updated_at
        string country_code
    }
    catalog__catalog.reviews ||--o| catalog__products : has
    catalog__catalog.reviews ||--o| accounts__users : has
    catalog__catalog.upload_jobs {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string filename
        string stored_path
        string content_type
        integer file_size
        string status
        integer progress
        text error_log
        string country_code
        datetime created_at
        datetime updated_at
    }
    catalog__catalog.video_analytics {
        integer id [PK]
        integer video_id [FK]
        integer user_id [FK]
        string event_type
        integer watch_duration_seconds
        string device_type
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    catalog__catalog.video_analytics ||--o| catalog__product_videos : has
    catalog__catalog.video_analytics ||--o| accounts__users : has
    catalog__catalog.wishlist_items {
        integer id [PK]
        integer user_id [FK]
        integer product_id [FK]
        datetime created_at
        datetime updated_at
        string country_code
        boolean is_deleted
    }
    catalog__catalog.wishlist_items ||--o| accounts__users : has
    catalog__catalog.wishlist_items ||--o| catalog__products : has
    catalog__catalog.wishlists {
        integer id [PK]
        integer user_id [FK]
        integer product_id [FK]
        datetime created_at
        datetime updated_at
        string country_code
        boolean is_deleted
    }
    catalog__catalog.wishlists ||--o| accounts__users : has
    catalog__catalog.wishlists ||--o| catalog__products : has
```