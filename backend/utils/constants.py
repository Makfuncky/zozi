
"""
Shared application constants.

Import from here instead of defining values in individual modules
to give a single source of truth and avoid silent divergence.
"""

# ── Country codes ─────────────────────────────────────────────────────────────

DEFAULT_COUNTRY: str = "AE"
FALLBACK_COUNTRY: str = "AE"

SUPPORTED_COUNTRY_CODES: frozenset[str] = frozenset({"AE", "SA", "QA", "KW", "BH", "OM", "IN", "PK", "GB", "US"})

# ── Role sets ─────────────────────────────────────────────────────────────────

#: All roles that have any degree of staff-level access to the admin panel.
STAFF_ROLES: frozenset[str] = frozenset({"admin", "sub_admin", "moderator", "support", "country_head", "country_manager"})

#: Roles allowed to access treasury / finance admin endpoints.
TREASURY_ROLES: frozenset[str] = frozenset({"admin", "finance_admin", "country_head", "super_admin"})
FINANCE_ROLES: frozenset[str] = frozenset({"admin", "finance_admin", "country_head"})
COUNTRY_ADMIN_ROLES: frozenset[str] = frozenset({"country_head", "country_manager", "country_moderator", "country_finance"})

#: Roles that may own / manage supplier inventory.
SUPPLIER_ROLES: frozenset[str] = frozenset({"supplier", "admin", "sub_admin"})

# ── Status values ─────────────────────────────────────────────────────────────

PAYOUT_STATUSES: frozenset[str] = frozenset({"pending", "approved", "rejected", "paid", "processing", "batched", "verified"})
SETTLEMENT_STATUSES: frozenset[str] = frozenset({"pending", "settled", "paid", "partial"})
BATCH_STATUSES: frozenset[str] = frozenset({"draft", "approved", "dispatched"})
ORDER_STATUSES: frozenset[str] = frozenset({"pending", "confirmed", "shipped", "delivered", "completed", "cancelled", "returned", "dispatched"})
PAYMENT_STATUSES: frozenset[str] = frozenset({"pending", "completed", "failed", "refunded"})
COD_REMITTANCE_STATUSES: frozenset[str] = frozenset({"pending", "remitted"})
COMMISSION_STATUSES: frozenset[str] = frozenset({"active", "inactive"})
GATEWAY_SETTLEMENT_STATUSES: frozenset[str] = frozenset({"pending", "settled", "flagged", "reconciled"})

# ── Account codes (Chart of Accounts) ─────────────────────────────────────────

CASH_ACCOUNT: str = "1010-001"
COD_RECEIVABLE_ACCOUNT: str = "1030"
PAYABLES_ACCOUNT: str = "2010-001"
LOGISTICS_PAYABLES_ACCOUNT: str = "2020"
OUTPUT_VAT_ACCOUNT: str = "2030"
INPUT_VAT_ACCOUNT: str = "2031"
REVENUE_ACCOUNTS: tuple[str, ...] = ("4010", "4020")

# ── Inventory ─────────────────────────────────────────────────────────────────

#: Products at or below this stock level trigger a low-stock notification.
LOW_STOCK_THRESHOLD: int = 5

# ── Pagination ────────────────────────────────────────────────────────────────

#: Default number of items returned per page when no limit is supplied.
DEFAULT_PAGE_SIZE: int = 24

#: Hard upper limit on the number of items that can be returned in one request.
MAX_PAGE_SIZE: int = 100

# ── Admin Pagination ─────────────────────────────────────────────────────────

#: Default page size for admin endpoints (larger for admin panels).
_ADMIN_DEFAULT_PAGE_SIZE: int = 50

#: Maximum page size for admin endpoints.
_ADMIN_MAX_PAGE_SIZE: int = 500

# ── Token TTLs ────────────────────────────────────────────────────────────────

VERIFY_TOKEN_TTL_HOURS: int = 24
RESET_TOKEN_TTL_HOURS: int = 1

# ── Notifications ─────────────────────────────────────────────────────────────

#: Maximum notifications returned per list request.
NOTIFICATIONS_PAGE_LIMIT: int = 50

# ── Bulk-operation caps ───────────────────────────────────────────────────────

#: Maximum IDs accepted in a single bulk admin request (delete, toggle, etc.).
MAX_BULK_ITEMS: int = 500

#: Maximum rows written in a single CSV export to prevent DoS via full-table dumps.
MAX_EXPORT_ROWS: int = 5_000

# ── File upload limits ────────────────────────────────────────────────────────

#: Absolute maximum upload size (10 MB).  Checked before content inspection.
MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024

#: Allowed MIME types for user-submitted images.
ALLOWED_IMAGE_MIME_TYPES: frozenset[str] = frozenset({
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
})

#: Allowed MIME types for KYC / supplier document uploads.
ALLOWED_DOCUMENT_MIME_TYPES: frozenset[str] = frozenset({
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
})

# ── Finance ───────────────────────────────────────────────────────────────────

#: Max subscriber rows loaded per campaign-send batch to avoid OOM on large lists.
CAMPAIGN_MAX_BATCH_SIZE: int = 10_000

