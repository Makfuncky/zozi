"""
class SupplierProfileNotFoundError(LookupError):
    """Raised when the acting user has no supplier profile."""


MODERATION_APPROVED = "approved"
MODERATION_REJECTED = "rejected"
MODERATION_PENDING = "pending"

BADGE_FIELDS: frozenset[str] = frozenset({"is_hot", "is_featured"})

_CREATE_FIELDS: frozenset[str] = frozenset({
    "description", "short_description", "sku", "barcode", "price", "compare_price",
    "cost_price", "stock", "low_stock_threshold", "weight", "dimensions", "image_url",
    "images", "category", "subcategory", "category_id", "tags", "attributes", "brand",
    "color", "sizes", "materials", "meta_title", "meta_description", "country_code",
})

_UPDATE_FIELDS: frozenset[str] = frozenset({
    "name", "description", "short_description", "price", "compare_price", "cost_price",
    "stock", "low_stock_threshold", "weight", "dimensions", "image_url", "images",
    "category", "subcategory", "category_id", "tags", "attributes", "is_active",
    "is_featured", "brand", "color", "sizes", "materials", "rating", "meta_title",
    "meta_description",
})

_SUPPLIER_UPDATE_FIELDS: frozenset[str] = frozenset({
    "name", "description", "price", "stock", "category", "is_active", "tags", "image_url",
})

_FIELD_ALIASES: dict[str, str] = {"stock_quantity": "stock"}


def _normalize(payload: Mapping[str, Any], allowed: frozenset[str]) -> dict[str, Any]:
    resolved: dict[str, Any] = {}
    for key, value in (payload or {}).items():
        canonical = _FIELD_ALIASES.get(key, key)
        if canonical in allowed:
            resolved[canonical] = value
    return resolved


def unique_slug(db: Session, name: str) -> str:
    base = generate_slug(name); slug = base; counter = 1
    while db.query(Product.id).filter(Product.slug == slug).first() is not None:
        slug = f"{base}-{counter}"; counter += 1
    return slug


def get_product_by_id(db: Session, product_id: int) -> Optional[Product]:
    return db.query(Product).filter(Product.id == product_id).first()


