# LOGISTICS Schema ERD

```mermaid
erDiagram
    logistics__logistics.city_distance_matrices {
        integer id [PK]
        string origin_country_code
        string origin_city_name
        string destination_country_code
        string destination_city_name
        numeric distance_km
        text notes
        integer created_by_id [FK]
        integer updated_by_id [FK]
        boolean is_deleted
        string country_code [FK]
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.city_distance_matrices ||--o| accounts__users : has
    logistics__logistics.city_distance_matrices ||--o| accounts__users : has
    logistics__logistics.city_distance_matrices ||--o| country__country_configs : has
    logistics__logistics.customs_entries {
        guid uuid [UK]
        boolean is_deleted
        datetime deleted_at
        integer version
        integer created_by_id
        integer updated_by
        integer id [PK]
        integer shipment_id [FK]
        string customs_declaration_number
        string customs_broker
        datetime entry_date
        numeric duty_rate_applied
        numeric duty_amount
        numeric vat_on_duty
        numeric penalties
        numeric total_customs_cost
        string status
        text notes
        string country_code
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.customs_entries ||--o| logistics__import_shipments : has
    logistics__logistics.goods_receipt_lines {
        guid uuid [UK]
        boolean is_deleted
        datetime deleted_at
        integer version
        integer created_by_id
        integer updated_by
        integer id [PK]
        integer grn_id [FK]
        integer po_line_id [FK]
        integer product_id [FK]
        string product_name
        string sku
        numeric quantity_received
        numeric quantity_accepted
        numeric quantity_rejected
        string rejection_reason
        string lot_number
        datetime expiry_date
        numeric unit_cost
        string country_code
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.goods_receipt_lines ||--o| logistics__goods_receipt_notes : has
    logistics__logistics.goods_receipt_lines ||--o| logistics__purchase_order_lines : has
    logistics__logistics.goods_receipt_lines ||--o| catalog__products : has
    logistics__logistics.goods_receipt_notes {
        guid uuid [UK]
        boolean is_deleted
        datetime deleted_at
        integer version
        integer created_by_id
        integer updated_by
        integer id [PK]
        string grn_number [UK]
        integer po_id [FK]
        integer supplier_id [FK]
        datetime receipt_date
        integer warehouse_id [FK]
        string status
        text notes
        integer received_by_id [FK]
        string country_code
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.goods_receipt_notes ||--o| logistics__purchase_orders : has
    logistics__logistics.goods_receipt_notes ||--o| finance__vendors : has
    logistics__logistics.goods_receipt_notes ||--o| logistics__warehouses : has
    logistics__logistics.goods_receipt_notes ||--o| accounts__users : has
    logistics__logistics.import_cost_templates {
        guid uuid [UK]
        boolean is_deleted
        datetime deleted_at
        integer version
        integer created_by_id
        integer updated_by
        integer id [PK]
        string name
        numeric default_duty_rate
        numeric default_freight_percent
        numeric default_insurance_percent
        numeric default_port_charges_percent
        numeric default_bank_charges_percent
        string allocation_method
        string country_code
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.import_shipment_lines {
        guid uuid [UK]
        boolean is_deleted
        datetime deleted_at
        integer version
        integer created_by_id
        integer updated_by
        integer id [PK]
        integer shipment_id [FK]
        integer po_line_id [FK]
        integer product_id [FK]
        string product_name
        string sku
        string hs_code
        numeric quantity
        numeric unit_cost_fx
        numeric unit_cost_local
        numeric line_total_fx
        numeric weight_kg
        numeric volume_cbm
        numeric allocated_freight
        numeric allocated_insurance
        numeric allocated_port
        numeric allocated_other
        numeric duty_amount
        numeric landed_unit_cost
        string country_code
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.import_shipment_lines ||--o| logistics__import_shipments : has
    logistics__logistics.import_shipment_lines ||--o| logistics__purchase_order_lines : has
    logistics__logistics.import_shipment_lines ||--o| catalog__products : has
    logistics__logistics.import_shipments {
        guid uuid [UK]
        boolean is_deleted
        datetime deleted_at
        integer version
        integer updated_by
        integer id [PK]
        string shipment_ref [UK]
        integer po_id [FK]
        integer supplier_id [FK]
        string supplier_name
        string origin_country
        string port_of_loading
        string port_of_discharge
        string vessel_name
        string bill_of_lading
        string container_number
        datetime shipment_date
        datetime estimated_arrival
        datetime actual_arrival
        string currency
        numeric exchange_rate
        integer warehouse_id [FK]
        string country_code
        text notes
        integer created_by_id [FK]
        string status
        numeric product_cost_total
        numeric freight_cost
        numeric insurance_cost
        numeric port_charges
        numeric inland_freight
        numeric bank_charges
        numeric other_costs
        numeric total_landed_cost
        numeric duty_cost
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.import_shipments ||--o| logistics__purchase_orders : has
    logistics__logistics.import_shipments ||--o| finance__vendors : has
    logistics__logistics.import_shipments ||--o| logistics__warehouses : has
    logistics__logistics.import_shipments ||--o| accounts__users : has
    logistics__logistics.landed_cost_allocations {
        guid uuid [UK]
        boolean is_deleted
        datetime deleted_at
        integer version
        integer created_by_id
        integer updated_by
        integer id [PK]
        integer shipment_id [FK]
        string cost_type
        text description
        numeric total_amount
        string allocation_method
        string currency
        numeric exchange_rate
        string country_code
        string status
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.landed_cost_allocations ||--o| logistics__import_shipments : has
    logistics__logistics.logistics_category_pricing_rules {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer partner_id [FK]
        integer service_area_id [FK]
        string category_name
        numeric flat_fee_override
        numeric special_handling_fee
        string currency
        boolean is_active
        string approval_status
        string review_note
        integer reviewed_by_id [FK]
        datetime reviewed_at
        datetime created_at
        datetime updated_at
        string country_code
    }
    logistics__logistics.logistics_category_pricing_rules ||--o| logistics__logistics_partners : has
    logistics__logistics.logistics_category_pricing_rules ||--o| logistics__logistics_partner_service_areas : has
    logistics__logistics.logistics_category_pricing_rules ||--o| accounts__users : has
    logistics__logistics.logistics_partner_profiles {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer partner_id [UK, FK]
        string tax_id
        string registration_number
        string business_type
        integer years_in_business
        string insurance_provider
        string insurance_policy_number
        datetime insurance_expiry
        datetime created_at
        datetime updated_at
        string country_code [FK]
    }
    logistics__logistics.logistics_partner_profiles ||--o| logistics__logistics_partners : has
    logistics__logistics.logistics_partner_profiles ||--o| country__country_configs : has
    logistics__logistics.logistics_partner_service_areas {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer partner_id [FK]
        string country_code
        string country_name
        string origin_city
        string city_name
        string zone_label
        numeric charge_amount
        numeric minimum_charge
        numeric per_kg_rate
        numeric pickup_charge
        numeric dropoff_charge
        numeric per_km_rate
        string currency
        integer delivery_days_min
        integer delivery_days_max
        boolean is_active
        string approval_status
        string review_note
        integer reviewed_by_id
        datetime reviewed_at
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.logistics_partner_service_areas ||--o| logistics__logistics_partners : has
    logistics__logistics.logistics_partners {
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
        string name
        string code [UK]
        string contact_name
        string contact_email
        string contact_phone
        string website
        json coverage_regions
        json service_types
        string status_code
        string verification_status
        string verification_note
        integer verified_by
        datetime verified_at
        string country_code [FK]
        datetime created_at
        string business_type
        string region
        string city
        text address
        string postal_code
        string tax_id
        text bio
        text about_us
        string logo_url
        string banner_url
        numeric latitude
        numeric longitude
        json social_links
        text notes
        boolean is_terms_accepted
        string terms_version
        datetime terms_accepted_at
    }
    logistics__logistics.logistics_partners ||--o| accounts__users : has
    logistics__logistics.logistics_partners ||--o| country__country_configs : has
    logistics__logistics.logistics_pricing_profiles {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer partner_id [FK]
        integer service_area_id [FK]
        string profile_name
        numeric base_in_city_fee
        numeric per_kg_rate
        numeric minimum_charge
        numeric maximum_charge
        numeric fuel_multiplier
        numeric base_inter_city_fee
        numeric per_km_rate
        numeric bulk_discount_threshold_kg
        numeric bulk_discount_percent
        string currency
        boolean is_active
        string approval_status
        string review_note
        integer reviewed_by_id [FK]
        datetime reviewed_at
        datetime created_at
        datetime updated_at
        string country_code
    }
    logistics__logistics.logistics_pricing_profiles ||--o| logistics__logistics_partners : has
    logistics__logistics.logistics_pricing_profiles ||--o| logistics__logistics_partner_service_areas : has
    logistics__logistics.logistics_pricing_profiles ||--o| accounts__users : has
    logistics__logistics.logistics_vehicle_rules {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer partner_id [FK]
        integer service_area_id [FK]
        string vehicle_type
        numeric max_weight_kg
        numeric cost_multiplier
        integer priority_rank
        string route_scope
        numeric max_volume_cm3
        boolean is_active
        string approval_status
        string review_note
        integer reviewed_by_id [FK]
        datetime reviewed_at
        datetime created_at
        datetime updated_at
        string country_code
    }
    logistics__logistics.logistics_vehicle_rules ||--o| logistics__logistics_partners : has
    logistics__logistics.logistics_vehicle_rules ||--o| logistics__logistics_partner_service_areas : has
    logistics__logistics.logistics_vehicle_rules ||--o| accounts__users : has
    logistics__logistics.partner_performance_projections {
        integer id [PK]
        integer partner_id [FK]
        string country_code
        integer total_shipments
        integer delivered_shipments
        integer cancelled_shipments
        numeric avg_delivery_hours
        numeric on_time_rate
        datetime period_start
        datetime period_end
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.partner_performance_projections ||--o| logistics__logistics_partners : has
    logistics__logistics.purchase_order_lines {
        guid uuid [UK]
        boolean is_deleted
        datetime deleted_at
        integer version
        integer created_by_id
        integer updated_by
        integer id [PK]
        integer po_id [FK]
        integer product_id [FK]
        string product_name
        string sku
        text description
        numeric quantity_ordered
        numeric quantity_received
        numeric unit_price
        numeric discount_percent
        numeric discount_amount
        numeric tax_rate
        numeric tax_amount
        numeric line_total
        numeric weight
        numeric volume
        string country_code
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.purchase_order_lines ||--o| logistics__purchase_orders : has
    logistics__logistics.purchase_order_lines ||--o| catalog__products : has
    logistics__logistics.purchase_orders {
        guid uuid [UK]
        boolean is_deleted
        datetime deleted_at
        integer version
        integer updated_by
        integer id [PK]
        string po_number [UK]
        integer supplier_id [FK]
        string supplier_name
        datetime order_date
        datetime expected_delivery_date
        integer warehouse_id [FK]
        string currency
        text notes
        text terms
        text shipping_address
        string country_code
        integer created_by_id [FK]
        string status
        numeric subtotal
        numeric discount_total
        numeric tax_total
        numeric grand_total
        numeric total_amount
        datetime delivery_date
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.purchase_orders ||--o| finance__vendors : has
    logistics__logistics.purchase_orders ||--o| logistics__warehouses : has
    logistics__logistics.purchase_orders ||--o| accounts__users : has
    logistics__logistics.sales_order_lines {
        guid uuid [UK]
        boolean is_deleted
        datetime deleted_at
        integer version
        integer created_by_id
        integer updated_by
        integer id [PK]
        integer so_id [FK]
        integer product_id [FK]
        string product_name
        string sku
        text description
        numeric quantity_ordered
        numeric quantity_dispatched
        numeric unit_price
        numeric discount_percent
        numeric discount_amount
        numeric tax_rate
        numeric tax_amount
        numeric line_total
        numeric weight
        numeric volume
        string country_code
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.sales_order_lines ||--o| logistics__sales_orders : has
    logistics__logistics.sales_order_lines ||--o| catalog__products : has
    logistics__logistics.sales_orders {
        guid uuid [UK]
        boolean is_deleted
        datetime deleted_at
        integer version
        integer updated_by
        integer id [PK]
        string so_number [UK]
        integer customer_id [FK]
        string customer_name
        string customer_po_number
        datetime order_date
        datetime expected_delivery_date
        integer warehouse_id [FK]
        string currency
        text shipping_address
        text billing_address
        text notes
        text terms
        string country_code
        integer created_by_id [FK]
        string status
        numeric subtotal
        numeric discount_total
        numeric tax_total
        numeric grand_total
        datetime delivery_date
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.sales_orders ||--o| finance__customers : has
    logistics__logistics.sales_orders ||--o| logistics__warehouses : has
    logistics__logistics.sales_orders ||--o| accounts__users : has
    logistics__logistics.shipment_events {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by
        integer created_by
        integer updated_by
        integer id [PK]
        integer shipment_id [FK]
        integer order_id [FK]
        integer supplier_id [FK]
        integer actor_user_id [FK]
        string actor_role
        string event_type
        string status_after
        string distribution_channel
        string location
        numeric latitude
        numeric longitude
        string scan_code
        string notes
        datetime created_at
        string country_code
    }
    logistics__logistics.shipment_events ||--o| logistics__shipments : has
    logistics__logistics.shipment_events ||--o| orders__orders : has
    logistics__logistics.shipment_events ||--o| accounts__users : has
    logistics__logistics.shipment_events ||--o| accounts__users : has
    logistics__logistics.shipment_tracking_projections {
        integer id [PK]
        integer shipment_id [FK]
        integer order_id
        string status_code
        string carrier_name
        string tracking_number
        string current_hub
        datetime estimated_delivery
        datetime actual_delivery
        json event_log
        datetime last_event_at
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.shipment_tracking_projections ||--o| logistics__shipments : has
    logistics__logistics.shipments {
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
        integer assigned_partner_id [FK]
        integer carrier_id [FK]
        string tracking_number [UK]
        string carrier_name
        string status_code
        string distribution_channel
        string current_hub
        string scan_code
        integer package_count
        numeric package_weight_kg
        string package_dimensions
        datetime packaged_at
        integer packaged_by_user_id
        string packaged_notes
        string packaging_notes
        datetime shipped_at
        datetime estimated_delivery
        datetime actual_delivery
        string delivery_signature_name
        string delivery_signature_data_url
        datetime delivery_signature_captured_at
        text notes
        string accepted_vehicle_type
        numeric accepted_vehicle_multiplier
        datetime accepted_vehicle_selected_at
        datetime created_at
        datetime updated_at
        string country_code
    }
    logistics__logistics.shipments ||--o| orders__orders : has
    logistics__logistics.shipments ||--o| accounts__users : has
    logistics__logistics.shipments ||--o| logistics__logistics_partners : has
    logistics__logistics.shipments ||--o| governance__shipping_carriers : has
    logistics__logistics.shipping_rules {
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
        string method
        numeric base_rate
        numeric per_kg_rate
        boolean is_active
        datetime created_at
    }
    logistics__logistics.shipping_rules ||--o| country__country_configs : has
    logistics__logistics.stock_movements {
        guid uuid [UK]
        boolean is_deleted
        datetime deleted_at
        integer version
        integer updated_by
        integer id [PK]
        integer product_id [FK]
        integer warehouse_id [FK]
        string movement_type
        string reference_type
        integer reference_id
        numeric quantity_change
        numeric quantity_after
        numeric unit_cost
        numeric total_cost
        string country_code
        integer created_by_id [FK]
        datetime created_at
        datetime updated_at
    }
    logistics__logistics.stock_movements ||--o| catalog__products : has
    logistics__logistics.stock_movements ||--o| logistics__warehouses : has
    logistics__logistics.stock_movements ||--o| accounts__users : has
    logistics__logistics.warehouses {
        guid uuid [UK]
        boolean is_deleted
        datetime deleted_at
        integer version
        integer created_by_id
        integer updated_by
        integer id [PK]
        string name
        string code [UK]
        string address
        string city
        string country_code
        boolean is_active
        datetime created_at
        datetime updated_at
    }
```