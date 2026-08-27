"""Orders Trading Service — wraps finance trading_service for orders domain.

This module re-exports trading functions from the finance domain to avoid
cross-domain imports in routers (Law 6 compliance).
"""

from domains.finance.services.trading_service import (
    create_purchase_order,
    list_purchase_orders,
    get_purchase_order,
    confirm_purchase_order,
    receive_purchase_order,
    list_goods_receipts,
    get_goods_receipt,
    three_way_match,
    create_sales_order,
    list_sales_orders,
    get_sales_order,
    confirm_sales_order,
    invoice_sales_order,
    dispatch_sales_order,
    create_warehouse,
    list_warehouses,
    get_stock_level,
    list_stock_movements,
    run_dunning_engine,
)
