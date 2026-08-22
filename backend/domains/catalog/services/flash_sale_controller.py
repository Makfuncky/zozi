"""controllers.commerce.flash_sale_controller controller.

Business logic is delegated to services.commerce.flash_sale_controller_service (routers -> controllers -> services)."""

from domains.catalog.services.flash_sale_controller_service import _FLASH_SALE_CACHE_TTL
from domains.catalog.services.flash_sale_controller_service import _build_list_page_payload
from domains.catalog.services.flash_sale_controller_service import create_flash_sale
from domains.catalog.services.flash_sale_controller_service import delete_flash_sale
from domains.catalog.services.flash_sale_controller_service import get_active_flash_sales
from domains.catalog.services.flash_sale_controller_service import get_all_flash_sales
from domains.catalog.services.flash_sale_controller_service import update_flash_sale

__all__ = [
    "_FLASH_SALE_CACHE_TTL", "_build_list_page_payload", "create_flash_sale", "delete_flash_sale", "get_active_flash_sales", "get_all_flash_sales",
    "update_flash_sale"
]

# === migration bridge (architecture realignment): re-export from domains.catalog.services.flash_sale_controller_service ===
def get_all_flash_sales(*args, **kwargs):
    from domains.catalog.services.flash_sale_controller_service import get_all_flash_sales as _impl
    return _impl(*args, **kwargs)


# === migration bridge (architecture realignment): re-export from domains.catalog.services.admin_promotions_write_service ===
def create_flash_sale(*args, **kwargs):
    from domains.catalog.services.admin_promotions_write_service import create_flash_sale as _impl
    return _impl(*args, **kwargs)


# === migration bridge (architecture realignment): re-export from domains.catalog.services.admin_promotions_write_service ===
def update_flash_sale(*args, **kwargs):
    from domains.catalog.services.admin_promotions_write_service import update_flash_sale as _impl
    return _impl(*args, **kwargs)


# === migration bridge (architecture realignment): re-export from domains.catalog.services.flash_sale_controller_service ===
def delete_flash_sale(*args, **kwargs):
    from domains.catalog.services.flash_sale_controller_service import delete_flash_sale as _impl
    return _impl(*args, **kwargs)
