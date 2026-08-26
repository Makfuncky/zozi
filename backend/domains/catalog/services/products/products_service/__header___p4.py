"""
def get_product_by_slug_hash(db: Session, slug_hash: str) -> Optional[Product]:
    return db.query(Product).filter(Product.slug_hash == slug_hash).first()


def get_supplier_profile(db: Session, user_id: int) -> SupplierProfile:
    profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == user_id).first()
    if profile is None: raise SupplierProfileNotFoundError("Supplier profile not found")
    return profile


def get_supplier_products_query(db: Session, supplier_id: int) -> Query:
    return db.query(Product).filter(Product.supplier_id == supplier_id).order_by(Product.id.desc())


def list_products_for_supplier(db: Session, supplier_id: int) -> Query:
    return get_supplier_products_query(db, supplier_id)


def get_supplier_product(db: Session, product_id: int, supplier_id: int) -> Optional[Product]:
    return db.query(Product).filter(Product.id == product_id, Product.supplier_id == supplier_id).first()


def get_owned_product(db: Session, product_id: int, supplier_id: int, *, exclude_deleted: bool = False) -> Product:
    query = db.query(Product).filter(Product.id == product_id, Product.supplier_id == supplier_id)
    if exclude_deleted: query = query.filter(Product.is_deleted.is_(False))
    product = query.first()
    if product is None: raise ProductNotFoundError("Product not found")
    return product


def get_country_products_query(db: Session, country_code: str, *, moderation_status: Optional[str] = None, include_deleted: bool = False) -> Query:
    query = db.query(Product).filter(Product.country_code == country_code.upper())
    if moderation_status: query = query.filter(Product.moderation_status == moderation_status)
    if not include_deleted: query = query.filter(Product.is_deleted.is_(False))
    return query.order_by(Product.id.desc())


def list_country_products_query(db: Session, country_code: str, *, moderation_status: Optional[str] = None, include_deleted: bool = False) -> Query:
    query = db.query(Product).filter(Product.country_code == country_code.upper()).order_by(Product.id.desc())
    if moderation_status: query = query.filter(Product.moderation_status == moderation_status)
    if not include_deleted: query = query.filter(Product.is_deleted == False)
    return query


def get_country_product(db: Session, product_id: int, country_code: str) -> Product:
    product = db.query(Product).filter(Product.id == product_id, Product.country_code == country_code.upper()).first()
    if product is None: raise ProductNotFoundError("Product not found")
    return product


def create_product(db: Session, *, name: str, supplier_id: int, payload: Optional[Mapping[str, Any]] = None, is_active: bool = True, is_featured: bool = False, is_digital: bool = False, is_verified: bool = True, is_approved: bool = True, moderation_status: str = MODERATION_APPROVED) -> Product:
    clean_name = str(name or "").strip()
    if not clean_name: raise ValueError("Product name is required")
    data = _normalize(payload or {}, _CREATE_FIELDS)
    product = Product(name=clean_name, slug=unique_slug(db, clean_name), slug_hash=generate_slug_hash(clean_name), supplier_id=int(supplier_id), price=data.pop("price", None) or 0, stock=data.pop("stock", None) or 0, low_stock_threshold=data.pop("low_stock_threshold", None) or 5, rating=float(data.pop("rating", 0.0) or 0.0), is_active=bool(is_active), is_featured=bool(is_featured), is_digital=bool(is_digital), is_verified=bool(is_verified), is_approved=bool(is_approved), is_deleted=False, moderation_status=str(moderation_status or MODERATION_APPROVED))
    for field, value in data.items(): setattr(product, field, value)
    db.add(product); db.commit(); db.refresh(product)
    logger.info("product.created id=%s supplier_id=%s", product.id, supplier_id)
    return product


def update_product(db: Session, product: Product, updates: Mapping[str, Any], *, allowed_fields: Optional[frozenset[str]] = None, regenerate_slug: bool = True) -> Product:
    data = _normalize(updates, allowed_fields or _UPDATE_FIELDS)
    for field, value in data.items(): setattr(product, field, value)
    if regenerate_slug and data.get("name"): product.slug = unique_slug(db, str(data["name"]))
    db.commit(); db.refresh(product)
    logger.info("product.updated id=%s fields=%s", product.id, sorted(data))
    return product


def update_supplier_product(db: Session, product: Product, updates: Mapping[str, Any]) -> Product:
    return update_product(db, product, updates, allowed_fields=_SUPPLIER_UPDATE_FIELDS, regenerate_slug=False)


def update_product_discount(db: Session, product: Product, *, clear: bool = False, compare_price: Any = ..., discount_starts_at: Any = ..., discount_ends_at: Any = ...) -> Product:
    if clear:
        product.compare_price = None; product.discount_starts_at = None; product.discount_ends_at = None
        db.commit(); db.refresh(product); return product
    if compare_price is not ...: product.compare_price = float(compare_price) if compare_price is not None else None
    if discount_starts_at is not ...: product.discount_starts_at = discount_starts_at
    if discount_ends_at is not ...: product.discount_ends_at = discount_ends_at
    db.commit(); db.refresh(product); return product


def set_product_image(db: Session, product: Product, image_url: str) -> Product:
    product.image_url = image_url; db.commit(); db.refresh(product); return product


def soft_delete_product(db: Session, product: Product, *, deactivate: bool = True) -> Product:
    product.is_deleted = True
    if deactivate: product.is_active = False
    db.commit(); db.refresh(product); return product


def set_moderation_status(db: Session, product: Product, status: str, *, notes: Optional[str] = None) -> Product:
    normalized = str(status or "").lower()
    if normalized not in {MODERATION_APPROVED, MODERATION_REJECTED, MODERATION_PENDING}: raise ValueError(f"Unsupported moderation status: {status!r}")
    product.moderation_status = normalized
    if normalized == MODERATION_APPROVED: product.is_verified = True
    if notes is not None and hasattr(product, "moderation_notes"): product.moderation_notes = notes
    db.commit(); db.refresh(product); return product


def set_product_badge(db: Session, product: Product, field: str, value: bool) -> Product:
    if field not in BADGE_FIELDS: raise ValueError(f"field must be one of {sorted(BADGE_FIELDS)}")
    setattr(product, field, bool(value)); db.commit(); db.refresh(product); return product


def set_product_verified(db: Session, product: Product, value: bool) -> Product:
    product.is_verified = bool(value); db.commit(); db.refresh(product); return product


def _parse_discount_datetime(raw: Any, field: str) -> Optional[datetime]:
    if raw in (None, ""): return None
    try: return datetime.fromisoformat(str(raw)).replace(tzinfo=timezone.utc)
    except (TypeError, ValueError) as exc:
        logger.exception("_parse_discount_datetime_failed", error=str(exc))
        raise HTTPException(status_code=400, detail=f"Invalid {field} format: {raw}") from exc


def build_discount_summary(product: Product, now: datetime) -> dict[str, Any]:
    price = float(product.price or 0)
    compare_price = float(product.compare_price) if product.compare_price is not None else None
    discount_pct = 0.0
    if compare_price and compare_price > 0: discount_pct = round((1 - price / compare_price) * 100, 1)
    active = bool(compare_price and compare_price > price)
    starts_at = product.discount_starts_at; ends_at = product.discount_ends_at
    if starts_at and ends_at: active = active and starts_at <= now <= ends_at
    elif starts_at: active = active and starts_at <= now
    return {"product_id": product.id, "price": price, "compare_price": compare_price, "discount_percentage": discount_pct, "discount_active": active}


def build_image_filename(product_id: int, original_filename: Optional[str]) -> str:
    name = original_filename or "product.jpg"
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else "jpg"
    return f"product_{product_id}_{uuid4().hex[:8]}.{ext}"


# ── Supplier Product Functions (merged from supplier_products_service.py) ───

from fastapi import File, UploadFile
from infrastructure.utils.file_validation import validate_upload_image
from infrastructure.utils.storage import storage as _storage
from infrastructure.utils.config import settings
from infrastructure.utils.datetime_utils import utcnow


def list_my_products(page: int, size: int, current_user, db: Session):
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier: raise HTTPException(404, "Supplier profile not found")
    q = db.query(Product).filter(Product.supplier_id == supplier.id)
    return paginated_response(q, page, size)


def get_supplier_product(product_id: int, current_user, db: Session):
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier: raise HTTPException(404, "Supplier profile not found")
    product = db.query(Product).filter(Product.id == product_id, Product.supplier_id == supplier.id).first()
    if not product: raise HTTPException(404, "Product not found")
    return product


def update_product_discount_supplier(product_id: int, payload: dict, current_user, db: Session):
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier: raise HTTPException(404, "Supplier profile not found")
    product = db.query(Product).filter(Product.id == product_id, Product.supplier_id == supplier.id).first()
    if not product: raise HTTPException(404, "Product not found")
    if payload.get("clear"):
        product.compare_price = None; product.discount_starts_at = None; product.discount_ends_at = None
        db.commit(); db.refresh(product)
        return {"status": "success", "message": "Discount cleared", "product_id": product.id}
    if "compare_price" in payload: product.compare_price = float(payload["compare_price"]) if payload["compare_price"] is not None else None
    if "discount_starts_at" in payload:
        raw = payload["discount_starts_at"]
        try: product.discount_starts_at = datetime.fromisoformat(raw).replace(tzinfo=timezone.utc) if raw else None
        except (ValueError, TypeError): raise HTTPException(400, f"Invalid discount_starts_at format: {raw}")
    if "discount_ends_at" in payload:
        raw = payload["discount_ends_at"]
        try: product.discount_ends_at = datetime.fromisoformat(raw).replace(tzinfo=timezone.utc) if raw else None
        except (ValueError, TypeError): raise HTTPException(400, f"Invalid discount_ends_at format: {raw}")
    db.commit(); db.refresh(product)
    discount_pct = 0; now = utcnow()
    if product.compare_price and product.price and float(product.compare_price) > 0:
        discount_pct = round((1 - float(product.price) / float(product.compare_price)) * 100, 1)
    is_active = bool(product.compare_price and product.compare_price > product.price)
    if product.discount_starts_at and product.discount_ends_at: is_active = is_active and product.discount_starts_at <= now <= product.discount_ends_at
    elif product.discount_starts_at: is_active = is_active and product.discount_starts_at <= now
    return {"status": "success", "product_id": product.id, "price": float(product.price), "compare_price": float(product.compare_price) if product.compare_price else None, "discount_percentage": discount_pct, "discount_active": is_active}


def update_supplier_product_fields(product_id: int, payload: dict, current_user, db: Session):
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier: raise HTTPException(404, "Supplier profile not found")
    product = db.query(Product).filter(Product.id == product_id, Product.supplier_id == supplier.id).first()
    if not product: raise HTTPException(404, "Product not found")
    field_map = {"name": "name", "description": "description", "price": "price", "stock": "stock", "stock_quantity": "stock", "category": "category", "is_active": "is_active", "tags": "tags", "image_url": "image_url"}
    for key, attr in field_map.items():
        if key in payload: setattr(product, attr, payload[key])
    db.commit(); db.refresh(product)
    return product


async def upload_supplier_product_image(product_id: int, file: UploadFile, current_user, db: Session):
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier: raise HTTPException(404, "Supplier profile not found")
    product = db.query(Product).filter(Product.id == product_id, Product.supplier_id == supplier.id).first()
    if not product: raise HTTPException(404, "Product not found")
    content = await file.read()
    max_size = getattr(settings, "MAX_UPLOAD_SIZE_MB", 10) * 1024 * 1024
    if len(content) > max_size: raise HTTPException(400, f"File too large (max {getattr(settings, 'MAX_UPLOAD_SIZE_MB', 10)}MB)")
    validate_upload_image(content, file.filename or "product.jpg")
    ext = file.filename.rsplit(".", 1)[-1] if "." in (file.filename or "") else "jpg"
    filename = f"product_{product_id}_{uuid.uuid4().hex[:8]}.{ext}"
    key = f"products/{filename}"
    new_url = _storage.save(key, content, content_type=file.content_type)
    old_url = product.image_url or ""
    if old_url:
        old_key = None
        if old_url.startswith("/uploads/"): old_key = old_url.lstrip("/")
        elif getattr(_storage, "cdn_base", "") and old_url.startswith(_storage.cdn_base): old_key = old_url[len(_storage.cdn_base):].lstrip("/")
        if old_key:
            try:
                _storage.delete(old_key)
            except Exception:
                logger.warning(
                    "Failed to delete old product image after upload",
                    extra={"old_key": old_key, "product_id": product_id},
                )
    product.image_url = new_url; db.commit(); db.refresh(product)
    return {"image_url": new_url, "filename": filename, "product_id": product.id}


def delete_supplier_product(product_id: int, current_user, db: Session):
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier: raise HTTPException(404, "Supplier profile not found")
    product = db.query(Product).filter(Product.id == product_id, Product.supplier_id == supplier.id, Product.is_deleted == False).first()
    if not product: raise HTTPException(404, "Product not found")
    product.is_deleted = True; db.commit()
    return {"status": "success", "message": "Product deleted"}

