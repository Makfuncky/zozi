import json
from pathlib import Path

report = {
    "audit_metadata": {
        "agent_id": 17,
        "topic": "Country scope enforcement",
        "date": "2026-09-09",
        "output_path": "_audit_results/09_09_26/agent_17_country_scope.json"
    },
    "findings": [
        {
            "id": "C-17-001",
            "severity": "High",
            "category": "missing_country_code_column",
            "model": "WishlistItem",
            "file": "domains/catalog/models/products.py",
            "line": 139,
            "description": "WishlistItem ORM table is missing country_code column. All user-scoped tables should carry country_code for country-level data isolation.",
            "remediation": "Add country_code Column(String(2), nullable=False, default='SA') to WishlistItem model and create Alembic migration."
        },
        {
            "id": "C-17-002",
            "severity": "High",
            "category": "missing_country_code_column",
            "model": "country_staff_assignments",
            "file": "infrastructure/database/seed_data/country_staff_assignments_full.json",
            "line": None,
            "description": "country_staff_assignments exists only as seed data / JSON constant, not as an ORM model. RLS country-aware table list and staff assignment lookups require a real table.",
            "remediation": "Create a proper ORM model for country_staff_assignments (or verify it is intentionally externalized and update rls_interceptor COUNTRY_AWARE_TABLES accordingly)."
        },
        {
            "id": "C-17-003",
            "severity": "Medium",
            "category": "missing_country_filter_in_query",
            "service_file": "domains/customers/services/wishlist_read_service.py",
            "queries": [
                "get_user_wishlist (line 41)",
                "get_wishlist_item_by_product (line 53)",
                "get_wishlist_item_by_id (line 63)"
            ],
            "model": "WishlistItem",
            "description": "Wishlist read service queries WishlistItem by user_id only, without country_code filter or set_rls_context. Because WishlistItem lacks country_code entirely, cross-country data leakage is possible if a user_id exists in multiple countries.",
            "remediation": "Add country_code to WishlistItem model, then add .filter(WishlistItem.country_code == <current_country>) to all queries, or wrap calls with set_rls_context."
        },
        {
            "id": "C-17-004",
            "severity": "Medium",
            "category": "missing_country_filter_in_query",
            "service_file": "domains/customers/services/wishlist_service_from_accounts.py",
            "queries": [
                "get_wishlist (line 21)",
                "add_to_wishlist (line 26)",
                "remove_from_wishlist (line 33)"
            ],
            "model": "WishlistItem",
            "description": "Wishlist service queries WishlistItem by user_id only, without country_code filter or set_rls_context.",
            "remediation": "Same as C-17-003."
        },
        {
            "id": "C-17-005",
            "severity": "Medium",
            "category": "missing_country_filter_in_query",
            "service_file": "domains/suppliers/services/products/supplier_products_service.py",
            "queries": [
                "list_my_products (line 34)",
                "get_supplier_product (line 42)",
                "update_product_discount (line 64)",
                "update_supplier_product (line 131)",
                "upload_supplier_product_image (line 170)",
                "delete_supplier_product (line 217)"
            ],
            "model": "Product",
            "description": "Supplier product service queries Product by supplier_id only. Product has country_code but queries do not filter by it. set_rls_context is not used in this file.",
            "remediation": "Add .filter(Product.country_code == <current_country>) to all Product queries, or set RLS context at the start of each public method."
        },
        {
            "id": "C-17-006",
            "severity": "Medium",
            "category": "missing_country_filter_in_query",
            "service_file": "domains/comms/services/tickets/tickets_service.py",
            "queries": [
                "get_tickets_query (line 20)",
                "get_ticket_by_id (line 27)",
                "get_ticket_with_details (line 35)",
                "list_tickets (line 58)",
                "count_tickets (line 76)"
            ],
            "model": "SupportTicket",
            "description": "Support ticket service queries SupportTicket without country_code filter. SupportTicket has country_code. No set_rls_context call in this file.",
            "remediation": "Add country_code filter to all SupportTicket queries, or call set_rls_context with the admin/country context before querying."
        }
    ],
    "summary": {
        "total_findings": 6,
        "critical": 0,
        "high": 2,
        "medium": 4,
        "models_with_country_code": 337,
        "models_missing_country_code": 1,
        "service_files_with_set_rls_context": 25,
        "service_files_importing_country_code_models_without_rls": 98
    },
    "positive_findings": [
        "instrument_rls(engine) is called in backend/main.py:48 — RLS is enabled at the DB engine level.",
        "337 out of 338 ORM tables have country_code (WishlistItem is the sole missing table).",
        "25 service files explicitly call set_rls_context to enforce country scoping."
    ]
}

out_path = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\_audit_results\09_09_26\agent_17_country_scope.json")
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(f"Written to {out_path}")
print(f"Findings: {len(report['findings'])}")
