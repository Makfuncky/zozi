# ORDERS Schema ERD

```mermaid
erDiagram
    orders__orders.order_items {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer order_id [FK]
        integer product_id [FK]
        integer variant_id
        integer supplier_id
        integer quantity
        numeric unit_price
        numeric price
        numeric total_price
        string product_name
        string product_image
        string selected_size
        string selected_color
        datetime created_at
        string country_code [FK]
    }
    orders__orders.order_items ||--o| orders__orders : has
    orders__orders.order_items ||--o| catalog__products : has
    orders__orders.order_items ||--o| country__country_configs : has
    orders__orders.order_logistics_allocations {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer order_id [FK]
        integer supplier_id [FK]
        integer shipment_id [FK]
        integer partner_id [FK]
        integer service_area_id [FK]
        string allocation_source
        string partner_name_snapshot
        string partner_code_snapshot
        string service_area_label_snapshot
        string destination_country
        string destination_city
        numeric shipping_amount
        numeric pickup_charge
        numeric dropoff_charge
        integer accepted_vehicle_rule_id
        string accepted_vehicle_type
        numeric accepted_vehicle_multiplier
        numeric accepted_shipping_amount
        numeric accepted_pickup_charge
        numeric accepted_dropoff_charge
        integer estimated_delivery_min
        integer estimated_delivery_max
        string currency
        text pricing_breakdown_json
        text accepted_pricing_breakdown_json
        string country_code [FK]
        datetime created_at
        datetime updated_at
    }
    orders__orders.order_logistics_allocations ||--o| orders__orders : has
    orders__orders.order_logistics_allocations ||--o| accounts__users : has
    orders__orders.order_logistics_allocations ||--o| logistics__shipments : has
    orders__orders.order_logistics_allocations ||--o| logistics__logistics_partners : has
    orders__orders.order_logistics_allocations ||--o| logistics__logistics_partner_service_areas : has
    orders__orders.order_logistics_allocations ||--o| country__country_configs : has
    orders__orders.order_notifications {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer user_id [FK]
        integer order_id [FK]
        string title
        text message
        string channel
        boolean is_read
        datetime created_at
    }
    orders__orders.order_notifications ||--o| accounts__users : has
    orders__orders.order_notifications ||--o| orders__orders : has
    orders__orders.orders {
        guid uuid [UK]
        integer version
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        string order_number [UK]
        integer customer_id [FK]
        integer user_id [FK]
        string status_code
        string status_label
        string payment_status
        string payment_method
        string payment_provider
        string payment_intent_id
        numeric subtotal
        numeric subtotal_amount
        numeric shipping_fee
        numeric shipping_amount
        numeric tax_amount
        numeric vat_amount
        numeric discount_amount
        numeric total
        numeric total_amount
        string coupon_code
        numeric fraud_score
        string fraud_action
        string currency
        text shipping_address
        string shipping_city
        string shipping_country
        string shipping_postal_code
        string customer_phone
        string delivery_location
        string delivery_note
        string tracking_number [UK]
        integer selected_partner_id
        integer selected_service_area_id
        integer estimated_delivery_min
        integer estimated_delivery_max
        string payment_gateway_code
        numeric payment_gateway_fee_amount
        numeric payment_customer_total_amount
        numeric payment_gateway_fee_passed_to_customer
        datetime paid_at
        string country_code [FK]
        datetime created_at
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
    }
    orders__orders.orders ||--o| accounts__users : has
    orders__orders.orders ||--o| accounts__users : has
    orders__orders.orders ||--o| country__country_configs : has
    orders__orders.return_requests {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer order_id [FK]
        integer order_item_id
        integer customer_id [FK]
        string intent
        string reason
        text description
        text details
        text supplier_review_state
        text images
        string status_code
        numeric refund_amount
        text items
        integer return_window_days
        datetime delivered_at
        datetime return_deadline
        text resolution_notes
        string country_code [FK]
        datetime created_at
        datetime updated_at
    }
    orders__orders.return_requests ||--o| orders__orders : has
    orders__orders.return_requests ||--o| accounts__users : has
    orders__orders.return_requests ||--o| country__country_configs : has
```