"""catalog domain — services sub-package."""
from __future__ import annotations

from domains.catalog.services.products.products_service import (  # noqa: F401
    get_products,
    get_product,
    get_product_by_barcode,
    get_supplier_names,
    _bump_product_cache_version,
    create_product,
    update_product,
    soft_delete_product,
)
from domains.catalog.services.products.bulk_ops_write_service import (  # noqa: F401
    bulk_archive_entities,
    bulk_restore_entities,
)
from domains.catalog.services.products.country_dropdown_service import (  # noqa: F401
    get_cities_dropdown,
)
from domains.catalog.services.products.admin_products_service import (  # noqa: F401
    approve_product_route,
    bulk_delete_products_route,
    list_pending_products,
    reject_product_route,
    toggle_product_badge_route,
    unarchive_product_route,
)
from domains.catalog.services.search.search_service import (  # noqa: F401
    parse_query,
    smart_search,
    smart_search_from_parsed,
    get_recommendations,
    AdvancedFilterService,
    AdvancedSearchEngine,
    fetch_visually_similar_products,
)
from domains.catalog.services.categories.category_service import (  # noqa: F401
    get_category_query,
    list_categories,
    get_category_by_id,
    get_category_by_ref,
    category_slug_exists,
    create_category,
    update_category,
    deactivate_category,
    delete_category,
    reorder_categories,
    serialize_category_summary,
    rebuild_category_paths,
    category_subtree_ids,
    category_subtree_ids_inclusive,
)
from domains.catalog.services.categories.category_admin_read_service import list_categories_paginated  # noqa: F401
from domains.catalog.services.categories.category_admin_write_service import (  # noqa: F401
    create_category,
    update_category,
    delete_category,
    reorder_categories,
)

__all__: list[str] = []
