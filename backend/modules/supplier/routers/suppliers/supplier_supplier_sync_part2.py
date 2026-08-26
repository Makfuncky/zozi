# === From supplier_supplier_sync.py ===
from suppliers.router import router  # noqa: F401
"""

def delete_product(
    product_id: int,
    current_user: dict = Depends(require_roles("supplier", "admin")),
    db: Session = Depends(get_db),
):
    return ctrl.delete_supplier_product(product_id, current_user, db)

@router.patch("/products/{product_id}/return-window")
def update_return_window(
    product_id: int,
    body: dict,
    current_user: dict = Depends(require_roles("supplier", "admin")),
    db: Session = Depends(get_db),
):
    """Set the return window (days) for a specific product. Min 10 days."""
    from pydantic import BaseModel, Field

    class ReturnWindowBody(BaseModel):
        days: int = Field(..., ge=10, le=365, description="Return window in days (minimum 10)")

    validated = ReturnWindowBody(**body)
    import domains.catalog.services as products_ctrl
    return products_ctrl.update_product_return_window(
        product_id=product_id,
        days=validated.days,
        current_user=current_user,
        db=db,
    )


# ── Analytics ─────────────────────────────────────────────────────────────────

@router.get("/analytics")
def get_analytics(
    period: str = "30d",
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.get_supplier_analytics(period, current_user, db)


@router.get("/reports")
def get_reports(
    period: str = "30d",
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.get_supplier_reports(period, current_user, db)

@router.post("/reports/ai-audit/run")
def run_reports_ai_audit(
    limit: int = 0,
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.queue_supplier_ai_audit(current_user, limit=limit)


# ── Inventory ─────────────────────────────────────────────────────────────────

@router.get("/inventory/alerts")
def get_inventory_alerts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.get_inventory_alerts(current_user, db)


@router.get("/inventory")
def get_inventory(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.get_supplier_inventory(current_user, db)

@router.put("/inventory/{product_id}/stock")
def update_stock(
    product_id: int,
    stock_update: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.update_product_stock(product_id, stock_update, current_user, db)

@router.put("/inventory/{product_id}/levels")
def update_levels(
    product_id: int,
    levels_update: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.update_inventory_levels(product_id, levels_update, current_user, db)

@router.post("/inventory/bulk-adjust")
def bulk_adjust_inventory(
    adjustments: List[dict],
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    """Bulk set or adjust stock levels for multiple products (up to 200)."""
    return ctrl.bulk_inventory_adjust(adjustments, current_user, db)


# ── Profile ───────────────────────────────────────────────────────────────────

@router.get("/profile")
def get_profile(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.get_supplier_profile(current_user, db)

@router.put("/profile")
def update_profile(
    profile_update: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.update_supplier_profile(profile_update, current_user, db)

@router.post("/profile/verify")
def request_verification(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.request_verification(current_user, db)


# ── Payouts ───────────────────────────────────────────────────────────────────

@router.get("/payouts")
def get_payouts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.get_payout_history(current_user, db)


@router.get("/shipments")
def get_shipments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.get_supplier_shipments(current_user, db)

@router.post("/payouts/request")
def request_payout(
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.request_payout(body, current_user, db)


# ── Business Profile ──────────────────────────────────────────────────────────

@router.get("/profile/business")
def get_business_profile(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    db: Session = Depends(get_db),
):
    """Return the supplier's business profile (creates one on first access)."""
    return ctrl.get_supplier_profile_business(current_user, db)

@router.put("/profile/business")
def update_business_profile(
    body: dict,
    current_user: dict = Depends(require_roles("supplier", "admin")),
    db: Session = Depends(get_db),
):
    """Update editable fields on the supplier's business profile."""
    return ctrl.update_supplier_profile_business(body, current_user, db)

@router.post("/profile/business/media")
async def upload_business_profile_media(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    field: str = Form(...),
    index: Optional[int] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a supplier storefront logo, banner, or hosted video file."""
    return ctrl.upload_supplier_profile_business_media(field, file, current_user, db, index=index)

@router.post("/terms/accept")
def accept_terms(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    db: Session = Depends(get_db),
):
    """Record that the current supplier has accepted the Terms & Conditions."""
    return ctrl.accept_supplier_terms(current_user, db)


@router.get("/onboarding/status")
def onboarding_status(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    db: Session = Depends(get_db),
):
    """Return the supplier's onboarding checklist status."""
    return ctrl.get_supplier_onboarding_status(current_user, db)


# ── Regions / Countries of Operation ─────────────────────────────────────────

@router.get("/regions")
def get_regions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    """Return the supplier's operating regions/countries."""
    return ctrl.get_supplier_regions(current_user, db)

@router.put("/regions")
def update_regions(
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    """Update the supplier's operating regions/countries."""
    return ctrl.update_supplier_regions(body, current_user, db)


# ── Credibility Badge & Document Verification ─────────────────────────────────

@router.get("/badge")
def get_supplier_badge(
    current_user: SupplierAdminOrSubAdminUser,
    db: Session = Depends(get_db),
):
    """Return the current supplier's credibility score and badge level."""
    return ctrl.refresh_supplier_badge(current_user["id"], db)


@router.get("/badge/catalog")
def get_supplier_badge_catalog(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    db: Session = Depends(get_db),
):
    """Return active badge tiers plus the supplier's current eligibility metrics."""
    return ctrl.list_supplier_badge_catalog(current_user, db)


@router.get("/badge/billing")
def get_supplier_badge_billing_history(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    db: Session = Depends(get_db),
):
    """Return badge billing records for the authenticated supplier."""
    return ctrl.list_supplier_badge_billing_history(current_user, db)

@router.post("/badge/purchase")
def purchase_supplier_badge(
    body: dict,
    current_user: dict = Depends(require_roles("supplier", "admin")),
    db: Session = Depends(get_db),
):
    """Create a badge purchase or renewal billing record for the authenticated supplier."""
    return ctrl.purchase_supplier_badge(body, current_user, db)

@router.post("/profile/verify-documents")
async def upload_verification_documents_route(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    files: List[UploadFile] = File(...),
    doc_types: List[str] = Form(...),
    db: Session = Depends(get_db),
):
    """Upload KYC documents (trade license, tax cert, ID, etc.) for verification."""
    return await ctrl.upload_verification_documents(files, doc_types, current_user, db)


# -- Supplier Analytics Timeseries ------------------------------------------

@router.get("/analytics/revenue")
def get_analytics_revenue(
    period: str = "30d",
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    """Return daily revenue + order timeseries for the authenticated supplier."""
    return ctrl.get_supplier_analytics_timeseries(current_user, period, db)


# ── Supplier Bank Account (Payout Beneficiary) ────────────────────────────────

@router.get("/bank-account")
def get_bank_account(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    """Get the supplier's saved payout bank account."""
    return ctrl.get_supplier_bank_account(current_user, db)

@router.put("/bank-account")
def upsert_bank_account(
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    """Submit or update the supplier's payout bank account. Triggers admin verification."""
    return ctrl.upsert_supplier_bank_account(body, current_user, db)

