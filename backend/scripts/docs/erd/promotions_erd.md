# PROMOTIONS Schema ERD

```mermaid
erDiagram
    promotions__promotions.banners {
        integer id [PK]
        string title
        string subtitle
        string image_url
        string link
        string banner_type
        boolean is_active
        boolean is_deleted
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
        datetime created_at
        datetime updated_at
    }
    promotions__promotions.banners ||--o| accounts__users : has
    promotions__promotions.banners ||--o| accounts__users : has
    promotions__promotions.banners ||--o| country__country_configs : has
    promotions__promotions.bogo_promotions {
        integer id [PK]
        string title
        text description
        integer buy_quantity
        integer free_quantity
        integer free_discount_pct
        string apply_to
        integer target_id
        integer max_uses_per_customer
        boolean stacking_allowed
        boolean is_active
        datetime starts_at
        datetime ends_at
        string country_code [FK]
        datetime created_at
        datetime updated_at
        boolean is_deleted
    }
    promotions__promotions.bogo_promotions ||--o| country__country_configs : has
    promotions__promotions.coupon_usages {
        integer id [PK]
        integer coupon_id
        integer user_id
        integer order_id
        string country_code [FK]
        datetime created_at
        datetime updated_at
        boolean is_deleted
    }
    promotions__promotions.coupon_usages ||--o| country__country_configs : has
    promotions__promotions.coupons {
        integer id [PK]
        string code [UK]
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
        datetime created_at
        datetime updated_at
    }
    promotions__promotions.coupons ||--o| accounts__users : has
    promotions__promotions.coupons ||--o| country__country_configs : has
    promotions__promotions.flash_sales {
        integer id [PK]
        string title
        text description
        datetime starts_at
        datetime ends_at
        numeric discount_pct
        boolean is_active
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        string country_code [FK]
        datetime created_at
        datetime updated_at
    }
    promotions__promotions.flash_sales ||--o| country__country_configs : has
    promotions__promotions.points_transactions {
        integer id [PK]
        integer user_id [FK]
        integer points
        string transaction_type
        integer order_id
        string source_description
        integer balance_after
        boolean is_deleted
        string country_code
        datetime created_at
        datetime updated_at
    }
    promotions__promotions.points_transactions ||--o| accounts__users : has
    promotions__promotions.promotion_engine_configs {
        integer id [PK]
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
        boolean is_deleted
    }
    promotions__promotions.promotion_engine_configs ||--o| country__country_configs : has
    promotions__promotions.promotion_ledger_entries {
        integer id [PK]
        integer promotion_id
        integer order_id
        integer user_id [FK]
        string promotion_type
        string promotion_code
        integer tier_id
        numeric amount
        string entry_type
        numeric discount_amount
        integer points_awarded
        integer points_redeemed
        integer stacking_flag
        string source
        string metadata_json
        boolean is_deleted
        datetime created_at
        datetime updated_at
        string country_code
    }
    promotions__promotions.promotion_ledger_entries ||--o| accounts__users : has
    promotions__promotions.user_points {
        integer id [PK]
        integer user_id [UK, FK]
        integer balance
        integer lifetime_earned
        integer lifetime_redeemed
        string loyalty_tier
        datetime points_expire_at
        boolean is_deleted
        string country_code
        datetime created_at
        datetime updated_at
    }
    promotions__promotions.user_points ||--o| accounts__users : has
```