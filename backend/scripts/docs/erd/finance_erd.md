# FINANCE Schema ERD

```mermaid
erDiagram
    finance__finance.account_balances {
        guid uuid [UK]
        integer version
        datetime created_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK]
        integer account_id [FK]
        integer user_id [FK]
        numeric balance
        string currency
        integer last_entry_id
        datetime last_entry_at
        datetime last_updated
        datetime updated_at
        string country_code
    }
    finance__finance.account_balances ||--o| finance__accounts : has
    finance__finance.account_balances ||--o| accounts__users : has
    finance__finance.account_groups {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK]
        string code [UK]
        string name
        text description
        string account_type
        string normal_side
        integer display_order
        datetime created_at
        string country_code
    }
    finance__finance.accounts {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK]
        integer group_id [FK]
        string code [UK]
        string name
        string normal_side
        string currency
        boolean is_active
        integer display_order
        datetime created_at
        string country_code
    }
    finance__finance.accounts ||--o| finance__account_groups : has
    finance__finance.accruals {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer updated_by
        integer id [PK]
        string accrual_type
        string description
        numeric amount
        string expense_account_code
        string accrual_account_code
        datetime accrual_date
        datetime reversal_date
        string status
        integer journal_entry_id [FK]
        integer reversal_entry_id [FK]
        string country_code
        integer created_by_id [FK]
        datetime created_at
    }
    finance__finance.accruals ||--o| finance__journal_entries : has
    finance__finance.accruals ||--o| finance__journal_entries : has
    finance__finance.accruals ||--o| accounts__users : has
    finance__finance.ap_bills {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer updated_by
        integer id [PK]
        integer vendor_id [FK]
        string bill_number
        datetime bill_date
        datetime due_date
        string account_code
        numeric amount
        numeric tax_amount
        text description
        string status
        integer linked_journal_entry_id [FK]
        integer paid_journal_entry_id [FK]
        string country_code
        integer created_by_id [FK]
        datetime created_at
        datetime updated_at
    }
    finance__finance.ap_bills ||--o| finance__vendors : has
    finance__finance.ap_bills ||--o| finance__journal_entries : has
    finance__finance.ap_bills ||--o| finance__journal_entries : has
    finance__finance.ap_bills ||--o| accounts__users : has
    finance__finance.ap_ledger_entries {
        guid uuid [UK]
        integer version
        datetime updated_at
        integer deleted_by_id
        integer updated_by
        integer id [PK]
        integer supplier_id [FK]
        integer order_id [FK]
        integer invoice_id [FK]
        integer settlement_id [FK]
        string reference_type
        integer reference_id
        string entry_type
        numeric amount
        numeric balance_after
        string currency
        string status
        datetime due_date
        datetime paid_at
        text description
        integer created_by_id [FK]
        datetime created_at
        string country_code
        boolean is_deleted
        datetime deleted_at
    }
    finance__finance.ap_ledger_entries ||--o| accounts__users : has
    finance__finance.ap_ledger_entries ||--o| orders__orders : has
    finance__finance.ap_ledger_entries ||--o| finance__invoices : has
    finance__finance.ap_ledger_entries ||--o| finance__supplier_settlements : has
    finance__finance.ap_ledger_entries ||--o| accounts__users : has
    finance__finance.ar_invoices {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer updated_by
        integer id [PK]
        integer customer_id [FK]
        string invoice_number
        datetime invoice_date
        datetime due_date
        string account_code
        numeric amount
        numeric tax_amount
        text description
        string status
        integer linked_journal_entry_id [FK]
        integer paid_journal_entry_id [FK]
        string country_code
        integer created_by_id [FK]
        datetime created_at
        datetime updated_at
    }
    finance__finance.ar_invoices ||--o| finance__customers : has
    finance__finance.ar_invoices ||--o| finance__journal_entries : has
    finance__finance.ar_invoices ||--o| finance__journal_entries : has
    finance__finance.ar_invoices ||--o| accounts__users : has
    finance__finance.ar_ledger_entries {
        guid uuid [UK]
        integer version
        datetime updated_at
        integer deleted_by_id
        integer updated_by
        integer id [PK]
        integer customer_id [FK]
        integer order_id [FK]
        integer invoice_id [FK]
        string reference_type
        integer reference_id
        string entry_type
        numeric amount
        numeric balance_after
        string currency
        string status
        datetime due_date
        datetime settled_at
        text description
        integer created_by_id [FK]
        datetime created_at
        string country_code
        boolean is_deleted
        datetime deleted_at
    }
    finance__finance.ar_ledger_entries ||--o| accounts__users : has
    finance__finance.ar_ledger_entries ||--o| orders__orders : has
    finance__finance.ar_ledger_entries ||--o| finance__invoices : has
    finance__finance.ar_ledger_entries ||--o| accounts__users : has
    finance__finance.automation_logs {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer id [PK]
        integer rule_id [FK]
        string status
        text message
        integer records_affected
        string country_code
        datetime created_at
        datetime updated_at
        integer created_by_id
        integer updated_by
    }
    finance__finance.automation_logs ||--o| finance__automation_rules : has
    finance__finance.automation_rules {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK]
        string name
        text description
        string rule_type
        string trigger
        string action
        text config
        boolean is_active
        string country_code
        datetime created_at
        datetime updated_at
    }
    finance__finance.bank_accounts {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK]
        string bank_name
        string account_name
        string account_number
        string iban
        string swift_bic
        string currency
        string gl_account_code
        string country_code
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    finance__finance.bank_mapping_rules {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer updated_by
        integer id [PK]
        string country_code
        string name
        string match_pattern
        string description_contains
        string account_code
        string normal_side
        string category
        integer priority
        boolean is_active
        integer created_by_id [FK]
        datetime created_at
        datetime updated_at
    }
    finance__finance.bank_mapping_rules ||--o| accounts__users : has
    finance__finance.bank_reconciliations {
        guid uuid [UK]
        integer version
        datetime created_at
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK]
        integer statement_line_id [FK]
        integer journal_entry_id [FK]
        numeric matched_amount
        string status
        text note
        integer matched_by_id [FK]
        datetime matched_at
        string country_code
    }
    finance__finance.bank_reconciliations ||--o| finance__bank_statement_lines : has
    finance__finance.bank_reconciliations ||--o| finance__journal_entries : has
    finance__finance.bank_reconciliations ||--o| accounts__users : has
    finance__finance.bank_statement_imports {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK]
        string bank_name
        string file_name
        datetime statement_period_start
        datetime statement_period_end
        string currency
        integer total_lines
        integer matched_lines
        integer unmatched_lines
        string status
        integer imported_by_id [FK]
        string country_code
        datetime created_at
    }
    finance__finance.bank_statement_imports ||--o| accounts__users : has
    finance__finance.bank_statement_lines {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK]
        integer import_id [FK]
        datetime txn_date
        string description
        string reference
        numeric amount
        string mapped_account_code
        string mapped_side
        integer mapping_rule_id [FK]
        string status
        integer posted_journal_entry_id [FK]
        integer reconciled_transaction_id [FK]
        string country_code
        datetime created_at
    }
    finance__finance.bank_statement_lines ||--o| finance__bank_statement_imports : has
    finance__finance.bank_statement_lines ||--o| finance__bank_mapping_rules : has
    finance__finance.bank_statement_lines ||--o| finance__journal_entries : has
    finance__finance.bank_statement_lines ||--o| finance__bank_transactions : has
    finance__finance.bank_transactions {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK]
        string transaction_ref
        string source
        string transaction_type
        string category
        numeric amount
        string currency
        text description
        integer linked_order_id [FK]
        integer linked_supplier_id [FK]
        integer linked_logistics_id
        integer linked_payout_id
        integer linked_refund_id
        boolean reconciled
        integer reconciled_by_id [FK]
        datetime reconciled_at
        datetime transaction_date
        string status
        datetime created_at
        string country_code
        boolean flagged
        text flag_reason
    }
    finance__finance.bank_transactions ||--o| orders__orders : has
    finance__finance.bank_transactions ||--o| accounts__users : has
    finance__finance.bank_transactions ||--o| accounts__users : has
    finance__finance.budgets {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer updated_by
        integer id [PK]
        string account_code
        integer fiscal_period_id [FK]
        numeric amount
        string currency
        string country_code
        text notes
        integer created_by_id [FK]
        datetime created_at
        datetime updated_at
    }
    finance__finance.budgets ||--o| finance__fiscal_periods : has
    finance__finance.budgets ||--o| accounts__users : has
    finance__finance.cash_accounts {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer updated_by
        integer id [PK]
        string name
        string account_type
        string currency
        numeric balance
        text description
        boolean is_active
        integer created_by_id [FK]
        datetime created_at
        datetime updated_at
        string country_code
    }
    finance__finance.cash_accounts ||--o| accounts__users : has
    finance__finance.cash_flow_forecasts {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK]
        datetime forecast_date
        datetime period_start
        datetime period_end
        numeric net_cash_flow
        numeric opening_balance
        numeric closing_balance
        string country_code
        datetime created_at
    }
    finance__finance.cash_position_snapshots {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK]
        datetime snapshot_time
        integer account_id [FK]
        numeric balance
        string currency
        string country_code
        datetime created_at
    }
    finance__finance.cash_position_snapshots ||--o| finance__treasury_accounts : has
    finance__finance.cash_transactions {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK]
        integer account_id [FK]
        string transaction_type
        numeric amount
        numeric balance_after
        text description
        string reference
        string category
        integer performed_by_id [FK]
        datetime created_at
        string country_code
    }
    finance__finance.cash_transactions ||--o| finance__cash_accounts : has
    finance__finance.cash_transactions ||--o| accounts__users : has
    finance__finance.commission_agreements {
        string uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer created_by
        integer updated_by
        integer id [PK]
        integer supplier_id [FK]
        string country_code
        string tier
        numeric rate
        integer set_by_admin_id [FK]
        boolean is_active
        datetime effective_from
        datetime effective_to
        text note
        datetime created_at
        datetime updated_at
    }
    finance__finance.commission_agreements ||--o| accounts__users : has
    finance__finance.commission_agreements ||--o| accounts__users : has
    finance__finance.commission_category_rates {
        string uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer created_by
        integer updated_by
        integer id [PK]
        integer category_id [FK]
        string category_slug
        string category_display_name
        string country_code [FK]
        numeric rate_percent
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    finance__finance.commission_category_rates ||--o| catalog__categories : has
    finance__finance.commission_category_rates ||--o| country__country_configs : has
    finance__finance.commission_ledger_entries {
        string uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer created_by
        integer updated_by
        integer id [PK]
        integer supplier_id [FK]
        integer order_id [FK]
        integer order_item_id [FK]
        integer product_id [FK]
        string category_slug
        string badge_level
        numeric global_default_rate
        numeric category_rate
        numeric badge_rate
        numeric override_rate
        numeric applied_rate
        string calculation_method
        numeric order_value
        numeric commission_pct
        boolean cap_applied
        numeric commission_amount
        boolean low_value_threshold_used
        boolean fixed_cap_used
        boolean override_flag
        boolean is_adjusted
        string currency
        numeric amount
        integer adjusted_by_id [FK]
        string status
        datetime credited_at
        datetime created_at
        datetime updated_at
        string country_code
    }
    finance__finance.commission_ledger_entries ||--o| accounts__users : has
    finance__finance.commission_ledger_entries ||--o| orders__orders : has
    finance__finance.commission_ledger_entries ||--o| orders__order_items : has
    finance__finance.commission_ledger_entries ||--o| catalog__products : has
    finance__finance.commission_ledger_entries ||--o| accounts__users : has
    finance__finance.cost_centers {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK]
        string code
        string name
        string country_code
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    finance__finance.customers {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK]
        string name
        string tax_id
        string contact_email
        string currency
        integer payment_terms_days
        numeric credit_limit
        string country_code
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    finance__finance.finance_audit_logs {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK]
        string action
        integer actor_id [FK]
        string actor_role
        string entity_type
        integer entity_id
        string country_code
        json detail
        datetime created_at
    }
    finance__finance.finance_audit_logs ||--o| accounts__users : has
    finance__finance.finance_automation_logs {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK]
        string kind
        integer records_processed
        integer records_changed
        json detail
        integer run_by_id [FK]
        string country_code
        datetime created_at
    }
    finance__finance.finance_automation_logs ||--o| accounts__users : has
    finance__finance.financial_reports {
        guid uuid [UK]
        integer version
        datetime created_at
        datetime updated_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK]
        string report_type
        datetime period_start
        datetime period_end
        string country_code
        json data
        datetime generated_at
        boolean is_deleted
        datetime deleted_at
    }
    finance__finance.fiscal_periods {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK]
        string country_code
        integer period_year
        integer period_month
        datetime period_start
        datetime period_end
        string status
        boolean is_locked
        datetime closed_at
        integer closed_by_id [FK]
        text notes
        datetime created_at
    }
    finance__finance.fiscal_periods ||--o| accounts__users : has
    finance__finance.fixed_assets {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer updated_by
        integer id [PK]
        string name
        string asset_code
        string category
        datetime purchase_date
        numeric purchase_cost
        numeric salvage_value
        integer useful_life_months
        numeric accumulated_depreciation
        datetime last_depreciated_date
        string asset_account_code
        string depreciation_account_code
        string accumulated_depr_account_code
        string status
        string country_code
        integer created_by_id [FK]
        datetime created_at
        datetime updated_at
    }
    finance__finance.fixed_assets ||--o| accounts__users : has
    finance__finance.gateway_settlement_schedules {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK]
        integer gateway_id [FK]
        datetime settlement_date
        numeric amount
        string currency
        string status
        string country_code
        datetime created_at
    }
    finance__finance.gateway_settlement_schedules ||--o| finance__payment_gateway_connections : has
    finance__finance.invoice_items {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK]
        integer invoice_id [FK]
        integer product_id [FK]
        string description
        integer quantity
        numeric unit_price
        numeric discount_amount
        numeric tax_rate
        numeric line_total
        datetime created_at
        string country_code
    }
    finance__finance.invoice_items ||--o| finance__invoices : has
    finance__finance.invoice_items ||--o| catalog__products : has
    finance__finance.invoices {
        guid uuid [UK]
        integer version
        integer created_by_id
        integer updated_by
        integer id [PK]
        integer order_id [FK]
        integer shipment_id [FK]
        integer supplier_id [FK]
        string invoice_number [UK]
        string invoice_type
        numeric subtotal
        numeric tax_amount
        numeric shipping_amount
        numeric discount_amount
        numeric total_amount
        string currency
        string status
        datetime issued_at
        datetime due_at
        datetime picked_at
        datetime dispatched_at
        datetime delivered_at
        datetime paid_at
        text notes
        datetime created_at
        datetime updated_at
        string country_code
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id [FK]
    }
    finance__finance.invoices ||--o| orders__orders : has
    finance__finance.invoices ||--o| logistics__shipments : has
    finance__finance.invoices ||--o| accounts__users : has
    finance__finance.invoices ||--o| accounts__users : has
    finance__finance.journal_entries {
        guid uuid [UK]
        integer version
        datetime updated_at
        integer updated_by
        integer id [PK]
        datetime entry_date
        string reference_number [UK]
        text description
        string source
        string country_code
        string currency
        boolean is_reconciled
        integer created_by_id [FK]
        string reference_type
        integer reference_id
        integer period_id [FK]
        integer reversal_of_id [FK]
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id [FK]
        datetime created_at
    }
    finance__finance.journal_entries ||--o| accounts__users : has
    finance__finance.journal_entries ||--o| finance__fiscal_periods : has
    finance__finance.journal_entries ||--o| finance__journal_entries : has
    finance__finance.journal_entries ||--o| accounts__users : has
    finance__finance.journal_entry_lines {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK]
        integer entry_id [FK]
        integer account_id [FK]
        integer cost_center_id [FK]
        numeric amount
        string side
        text description
        string entity_type
        integer entity_id
        datetime created_at
        string country_code
    }
    finance__finance.journal_entry_lines ||--o| finance__journal_entries : has
    finance__finance.journal_entry_lines ||--o| finance__accounts : has
    finance__finance.journal_entry_lines ||--o| finance__cost_centers : has
    finance__finance.logistics_partner_payouts {
        integer id [PK]
        boolean is_deleted
        integer partner_id [FK]
        numeric amount
        string currency
        datetime period_start
        datetime period_end
        string status
        string reference_id
        datetime processed_at
        string country_code [FK]
        datetime created_at
        datetime updated_at
        string method
        text notes
    }
    finance__finance.logistics_partner_payouts ||--o| logistics__logistics_partners : has
    finance__finance.logistics_partner_payouts ||--o| country__country_configs : has
    finance__finance.payment_gateway_connections {
        integer id [PK]
        boolean is_deleted
        string provider_code
        string gateway_name
        string country_code
        string environment
        boolean is_active
        json credentials
        json fee_config
        json supported_methods
        datetime last_sync_at
        string provider_kind
        string display_name
        boolean is_enabled
        boolean supports_customer_checkout
        boolean supports_payouts
        string payment_mode
        string public_key
        string secret_key
        string webhook_secret
        string merchant_id
        string api_base_url
        string webhook_url
        string test_url
        string settlement_cycle
        text supported_currencies_json
        text extra_config_json
        text notes
        numeric fee_percent
        numeric fixed_fee_amount
        numeric payout_fee_percent
        numeric payout_fixed_fee_amount
        boolean pass_fee_to_customer
        string test_status
        string test_message
        datetime last_tested_at
        integer updated_by_id [FK]
        boolean adapter_supported
        datetime created_at
        datetime updated_at
    }
    finance__finance.payment_gateway_connections ||--o| accounts__users : has
    finance__finance.payment_reconciliation_runs {
        integer id [PK]
        boolean is_deleted
        datetime run_date
        numeric total_amount
        integer reconciled_count
        integer unmatched_count
        integer processed_count
        integer stale_pending_orders
        integer recent_webhook_count
        text result_json
        datetime started_at
        datetime completed_at
        string status
        string country_code
        datetime created_at
        datetime updated_at
    }
    finance__finance.payments {
        integer id [PK]
        boolean is_deleted
        integer order_id [FK]
        numeric amount
        string payment_method
        string provider
        string status
        string intent_id
        datetime created_at
        datetime updated_at
        string country_code [FK]
        text layout_json
    }
    finance__finance.payments ||--o| orders__orders : has
    finance__finance.payments ||--o| country__country_configs : has
    finance__finance.payout_batch_items {
        guid uuid [UK]
        integer version
        datetime created_at
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK]
        integer batch_id [FK]
        string entity_type
        integer entity_id
        numeric amount
        string currency
        string reference
        string status
        string country_code
    }
    finance__finance.payout_batch_items ||--o| finance__payout_batches : has
    finance__finance.payout_batches {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer updated_by
        integer id [PK]
        string batch_number [UK]
        string country_code
        numeric total_amount
        integer item_count
        string status
        integer created_by_id [FK]
        integer approved_by_id [FK]
        datetime dispatched_at
        datetime settled_at
        text notes
        datetime created_at
        datetime updated_at
    }
    finance__finance.payout_batches ||--o| accounts__users : has
    finance__finance.payout_batches ||--o| accounts__users : has
    finance__finance.payout_rule_categories {
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
        string category_slug
        numeric payout_rate
        numeric min_amount
        numeric max_amount
        boolean is_active
        datetime created_at
    }
    finance__finance.payout_rule_categories ||--o| country__country_configs : has
    finance__finance.payout_rule_products {
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
        integer product_id
        numeric payout_rate
        numeric min_amount
        numeric max_amount
        boolean is_active
        datetime created_at
    }
    finance__finance.payout_rule_products ||--o| country__country_configs : has
    finance__finance.payout_rules {
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
        numeric min_amount
        numeric max_amount
        numeric fixed_fee
        numeric percent_fee
        boolean is_active
        datetime created_at
    }
    finance__finance.payout_rules ||--o| country__country_configs : has
    finance__finance.payouts {
        integer id [PK]
        boolean is_deleted
        string batch_number
        integer order_id [FK]
        integer supplier_id [FK]
        numeric amount
        string currency
        string method
        string status
        string reference_id
        string reference
        string provider
        string provider_recipient_id
        string provider_transfer_id
        string provider_status
        text notes
        datetime processed_at
        string country_code [FK]
        datetime created_at
        datetime updated_at
    }
    finance__finance.payouts ||--o| orders__orders : has
    finance__finance.payouts ||--o| accounts__users : has
    finance__finance.payouts ||--o| country__country_configs : has
    finance__finance.pending_journal_entries {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer updated_by
        integer id [PK]
        text lines_json
        text description
        string source
        string country_code
        datetime entry_date
        boolean amount_threshold_triggered
        string status
        integer created_by_id [FK]
        integer approved_by_id [FK]
        integer rejected_by_id [FK]
        text rejection_reason
        datetime approved_at
        integer journal_entry_id [FK]
        datetime created_at
    }
    finance__finance.pending_journal_entries ||--o| accounts__users : has
    finance__finance.pending_journal_entries ||--o| accounts__users : has
    finance__finance.pending_journal_entries ||--o| accounts__users : has
    finance__finance.pending_journal_entries ||--o| finance__journal_entries : has
    finance__finance.product_commission_overrides {
        string uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer created_by
        integer updated_by
        integer id [PK]
        integer product_id [FK]
        integer supplier_id [FK]
        numeric rate_percent
        integer set_by_admin_id [FK]
        boolean is_active
        string country_code
        datetime created_at
        datetime updated_at
    }
    finance__finance.product_commission_overrides ||--o| catalog__products : has
    finance__finance.product_commission_overrides ||--o| accounts__users : has
    finance__finance.product_commission_overrides ||--o| accounts__users : has
    finance__finance.recurring_templates {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer updated_by
        integer id [PK]
        string name
        string frequency
        datetime next_run_date
        text description
        json lines
        string currency
        string country_code
        boolean is_active
        integer created_by_id [FK]
        datetime created_at
        datetime updated_at
    }
    finance__finance.recurring_templates ||--o| accounts__users : has
    finance__finance.refund_ledgers {
        guid uuid [UK]
        integer version
        datetime updated_at
        integer created_by_id
        integer updated_by
        integer id [PK]
        integer order_id [FK]
        integer return_request_id [FK]
        integer ledger_id
        integer bank_transaction_id
        text reason
        text refund_reason
        string refund_method
        numeric customer_refund_amount
        numeric supplier_reversal
        numeric logistics_reversal
        numeric delivery_fee_reversal
        numeric commission_reversal
        numeric vat_adjustment
        numeric vat_reversal
        integer performed_by_id [FK]
        datetime processed_at
        string currency
        string status
        datetime created_at
        string country_code
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id [FK]
    }
    finance__finance.refund_ledgers ||--o| orders__orders : has
    finance__finance.refund_ledgers ||--o| orders__return_requests : has
    finance__finance.refund_ledgers ||--o| accounts__users : has
    finance__finance.refund_ledgers ||--o| accounts__users : has
    finance__finance.scanned_expenses {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK]
        integer employee_id [FK]
        string vendor_name
        string invoice_number
        datetime expense_date
        numeric amount
        string currency
        numeric tax_amount
        string category
        text description
        string expense_account_code
        string image_url
        text ocr_raw_text
        numeric ocr_confidence
        string status
        integer posted_journal_entry_id [FK]
        integer reviewed_by_id [FK]
        string country_code
        datetime created_at
        datetime updated_at
    }
    finance__finance.scanned_expenses ||--o| hr__employees : has
    finance__finance.scanned_expenses ||--o| finance__journal_entries : has
    finance__finance.scanned_expenses ||--o| accounts__users : has
    finance__finance.supplier_settlements {
        guid uuid [UK]
        integer version
        integer created_by_id
        integer updated_by
        integer id [PK]
        integer supplier_id [FK]
        integer order_id [FK]
        integer ledger_id [FK]
        integer payout_id [FK]
        integer shipment_id [FK]
        numeric gross_amount
        numeric commission_amount
        numeric commission_deducted
        numeric commission_rate
        numeric vat_on_commission
        numeric net_amount
        string status
        datetime settled_at
        datetime eligible_at
        integer bank_transaction_id
        string currency
        datetime created_at
        datetime updated_at
        string country_code
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id [FK]
    }
    finance__finance.supplier_settlements ||--o| accounts__users : has
    finance__finance.supplier_settlements ||--o| orders__orders : has
    finance__finance.supplier_settlements ||--o| finance__transaction_ledgers : has
    finance__finance.supplier_settlements ||--o| finance__payouts : has
    finance__finance.supplier_settlements ||--o| logistics__shipments : has
    finance__finance.supplier_settlements ||--o| accounts__users : has
    finance__finance.tax_rules {
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
        string tax_name
        numeric tax_rate
        boolean is_active
        datetime created_at
    }
    finance__finance.tax_rules ||--o| country__country_configs : has
    finance__finance.transaction_ledgers {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK]
        integer user_id [FK]
        integer supplier_id [FK]
        integer logistics_partner_id [FK]
        integer order_id [FK]
        integer order_item_id [FK]
        integer shipment_id [FK]
        string payment_method
        numeric product_subtotal
        numeric discount_amount
        numeric delivery_pickup_charge
        numeric delivery_dropoff_charge
        numeric delivery_total
        numeric vat_amount
        numeric zozi_commission_rate
        numeric zozi_commission
        numeric net_supplier_amount
        numeric net_logistics_amount
        numeric net_zozi_amount
        numeric cod_collected_amount
        numeric cod_remittance_due
        string settlement_status
        string currency
        string transaction_type
        string reference_id
        numeric balance_after
        text notes
        numeric amount
        string country_code
        datetime created_at
        datetime updated_at
    }
    finance__finance.transaction_ledgers ||--o| accounts__users : has
    finance__finance.transaction_ledgers ||--o| accounts__users : has
    finance__finance.transaction_ledgers ||--o| logistics__logistics_partners : has
    finance__finance.transaction_ledgers ||--o| orders__orders : has
    finance__finance.transaction_ledgers ||--o| orders__order_items : has
    finance__finance.transaction_ledgers ||--o| logistics__shipments : has
    finance__finance.treasury_accounts {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK]
        string slug [UK]
        string name
        string account_type
        string currency
        string gl_account_code
        text description
        integer employee_id [FK]
        numeric balance
        boolean is_active
        string country_code
        datetime created_at
        datetime updated_at
    }
    finance__finance.treasury_accounts ||--o| hr__employees : has
    finance__finance.treasury_transactions {
        guid uuid [UK]
        integer version
        datetime created_at
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK]
        integer from_account_id [FK]
        integer to_account_id [FK]
        integer account_id [FK]
        string transaction_type
        numeric amount
        string currency
        string reference
        text description
        datetime posted_at
        string country_code
    }
    finance__finance.treasury_transactions ||--o| finance__treasury_accounts : has
    finance__finance.treasury_transactions ||--o| finance__treasury_accounts : has
    finance__finance.treasury_transactions ||--o| finance__treasury_accounts : has
    finance__finance.vat_remittances {
        guid uuid [UK]
        integer version
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK]
        datetime period_start
        datetime period_end
        numeric vat_collected_amount
        numeric vat_adjustment_amount
        numeric amount_due
        numeric amount
        numeric amount_remitted
        string currency
        integer bank_transaction_id
        integer remitted_by_id [FK]
        datetime remitted_at
        text notes
        string status
        datetime created_at
        string country_code
    }
    finance__finance.vat_remittances ||--o| accounts__users : has
    finance__finance.vendors {
        guid uuid [UK]
        integer version
        boolean is_deleted
        datetime deleted_at
        integer deleted_by_id
        integer created_by_id
        integer updated_by
        integer id [PK]
        string name
        string tax_id
        string contact_email
        string currency
        integer payment_terms_days
        string country_code
        boolean is_active
        datetime created_at
        datetime updated_at
    }
```