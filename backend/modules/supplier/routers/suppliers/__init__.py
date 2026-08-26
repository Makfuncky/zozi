"""Split router package — originally suppliers.py."""

from suppliers.router import router  # noqa: F401
import suppliers.onboarding  # noqa: F401
import suppliers.supplier_bg_ab_test  # noqa: F401
import suppliers.supplier_core_routes  # noqa: F401
import suppliers.supplier_documents  # noqa: F401
import suppliers.supplier_documents_review  # noqa: F401
import suppliers.supplier_health  # noqa: F401
import suppliers.supplier_health_list  # noqa: F401
import suppliers.supplier_orders_part1  # noqa: F401
import suppliers.supplier_orders_part2  # noqa: F401
import suppliers.supplier_orders_verify  # noqa: F401
import suppliers.supplier_part1_p1  # noqa: F401
import suppliers.supplier_part1_p2  # noqa: F401
import suppliers.supplier_part2  # noqa: F401
import suppliers.supplier_profile  # noqa: F401
import suppliers.supplier_profile_create  # noqa: F401
import suppliers.supplier_supplier_supplier_health  # noqa: F401
import suppliers.supplier_supplier_sync_part1_p1  # noqa: F401
import suppliers.supplier_supplier_sync_part1_p2  # noqa: F401
import suppliers.supplier_supplier_sync_part2  # noqa: F401
import suppliers.supplier_supplier_upload  # noqa: F401
import suppliers.supplier_sync  # noqa: F401
import suppliers.supplier_upload  # noqa: F401

__all__ = ["router"]
