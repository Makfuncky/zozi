"""Orders Trading Service — wraps finance trading_service for orders domain.

This module re-exports trading functions from the finance domain to avoid
cross-domain imports in routers (Law 6 compliance).
"""

from domains.finance.ports import confirm_purchase_order, confirm_sales_order, create_purchase_order, create_sales_order, create_warehouse, dispatch_sales_order, get_goods_receipt, get_purchase_order, get_sales_order, get_stock_level, invoice_sales_order, list_goods_receipts, list_purchase_orders, list_sales_orders, list_stock_movements, list_warehouses, receive_purchase_order, run_dunning_engine, three_way_match
