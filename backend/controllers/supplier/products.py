"""Supplier product operations.

Re-exports product-related functions from the monolithic supplier_controller.
New product-related business logic should be added here.
"""
from controllers.supplier_controller import (  # noqa: F401
    get_supplier_products,
    get_supplier_product,
    create_supplier_product,
    create_supplier_product_upload,
    update_supplier_product,
    delete_supplier_product,
    execute_bulk_operation,
    export_products_csv,
    import_products_csv,
    bulk_upload_products,
    get_public_supplier_products,
    run_supplier_ai_audit,
    queue_supplier_ai_audit,
    process_product_image,
)
