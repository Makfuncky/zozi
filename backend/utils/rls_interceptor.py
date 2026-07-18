from __future__ import annotations

import logging
from contextvars import ContextVar
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import Engine

rls_country_scope_ctx: ContextVar[frozenset[str] | None] = ContextVar("rls_country_scope", default=None)
rls_is_restricted_ctx: ContextVar[bool] = ContextVar("rls_is_restricted", default=False)

COUNTRY_AWARE_TABLES: dict[str, str] = {
    "orders": "country_code",
    "order_logistics_allocations": "destination_country",
    "country_staff_assignments": "country_code",
    "country_communications": "country_code",
    "country_gateway_credentials": "country_code",
    "supplier_country_commissions": "country_code",
    "country_cities": "country_code",
    "country_category_tax_rates": "country_code",
    "country_feature_flags": "country_code",
    "country_payout_rules": "country_code",
    "country_config_versions": "country_code",
    "country_configs": "code",
    "country_holiday_calendars": "country_code",
    "country_localization": "country_code",
    "country_logistics_zones": "country_code",
    "country_map_configs": "country_code",
    "country_payment_aliases": "country_code",
    "country_legal_contracts": "country_code",
    "employees": "country_code",
    "banners": "country_code",
    "coupons": "country_code",
    "payments": "country_code",
    "support_tickets": "country_code",
    "promotion_engine_configs": "country_code",
    "return_requests": "country_code",
    "logistics_partner_profiles": "country_code",
    "order_items": "country_code",
    "role_permission_assignments": "country_code",
    "user_permission_overrides": "country_code",
    "permission_audit_log": "country_code",
    "tax_rules": "country_code",
    "shipping_rules": "country_code",
    "fraud_rules": "country_code",
    "commission_agreements": "country_code",
    "payout_batches": "country_code",
    "payout_rules": "country_code",
    "journal_entries": "country_code",
    "pending_journal_entries": "country_code",
    "media_assets": "country_code",
    "escalation_sla_rules": "country_code",
    "supplier_kyc_requirements": "country_code",
    "logistics_partner_kyc_requirements": "country_code",
    "logistics_partner_locations": "country_code",
    "logistics_partner_service_areas": "country_code",
    "shop_warehouse_locations": "country_code",
    "payment_gateway_connections": "country_code",
    "country_gateway_configs": "country_code",
    "legal_contract_templates": "country_code",
    "ip_reputations": "country_code",
    "parcel_location_trackers": "country_code",
    "org_units": "country_code",
    "employee_addresses": "country_code",
    "messages": "country_code",
    "internal_channels": "country_code",
    "video_rooms": "country_code",
    "shift_handover_logs": "country_code",
    "shift_handover_sessions": "country_code",
    "supplier_onboarding_sync": "country_code",
    "news_articles": "country_code",
    "offices": "country_code",
    "supplier_profiles": "country_code",
    "products": "country_code",
    "flash_sales": "country_code",
    "logistics_partners": "country_code",
    "payouts": "country_code",
    "logistics_partner_payouts": "country_code",
    "email_campaigns": "country_code",
    # Users / Customers
    "users": "country_code",
    "addresses": "country_code",
    "carts": "country_code",
    "cart_items": "country_code",
    "wishlists": "country_code",
    "wishlist_items": "country_code",
    "reviews": "country_code",
    "notifications": "country_code",
    "user_sessions": "country_code",
    "user_devices": "country_code",
    "user_login_history": "country_code",
    "referrals": "country_code",
    "referral_point_events": "country_code",
    "ticket_replies": "country_code",
    "ticket_messages": "country_code",
    # Products
    "categories": "country_code",
    "product_variants": "country_code",
    "product_filter_options": "country_code",
    "product_filter_metadata": "country_code",
    "product_videos": "country_code",
    "faqs": "country_code",
    # AI upload pipeline (Phase 4) — country-scoped staging/jobs/logs
    "ai_upload_jobs": "country_code",
    "ai_staging_products": "country_code",
    "ai_staging_variants": "country_code",
    "ai_generation_logs": "country_code",
    # Suppliers
    "supplier_bank_accounts": "country_code",
    "supplier_disputes": "country_code",
    "supplier_fraud_indicators": "country_code",
    "supplier_notification_preferences": "country_code",
    "supplier_settlements": "country_code",
    "commission_global_configs": "country_code",
    "commission_badge_tiers": "country_code",
    "commission_ledger_entries": "country_code",
    # Logistics
    "shipments": "country_code",
    "shipment_events": "country_code",
    "shipment_confirmations": "country_code",
    "shipping_zones": "country_code",
    "shipping_carriers": "country_code",
    "logistics_pricing_profiles": "country_code",
    "logistics_vehicle_rules": "country_code",
    "logistics_fraud_indicators": "country_code",
    "logistics_cod_remittance_receipts": "country_code",
    "logistics_category_pricing_rules": "country_code",
    "logistics_settlements": "country_code",
    "logistics_partner_bank_accounts": "country_code",
    "logistics_partner_documents": "country_code",
    # Employees
    "employee_roles": "country_code",
    "employee_attendance": "country_code",
    "employee_leave_requests": "country_code",
    "employee_leave_ledgers": "country_code",
    "employee_assets": "country_code",
    "employee_biometrics": "country_code",
    "employee_dependents": "country_code",
    "employee_certifications": "country_code",
    "employee_documents": "country_code",
    "employee_expenses": "country_code",
    "employee_relations": "country_code",
    "employee_shift_rosters": "country_code",
    "employee_travel_requests": "country_code",
    "employee_work_logs": "country_code",
    # Finance / Admin
    "invoices": "country_code",
    "invoice_items": "country_code",
    "fraud_cases": "country_code",
    "fraud_alerts": "country_code",
    "fraud_events": "country_code",
    "fraud_scoring_logs": "country_code",
    # accounts/account_groups/account_balances form a single GLOBAL chart of
    # accounts (seeded with country_code=NULL); country scoping is applied at the
    # journal-entry / transaction level, NOT at the account master level. Filtering
    # the account master by country would hide the seeded COA and break GL posting.
    "journal_entry_lines": "country_code",
    "bank_transactions": "country_code",
    "cash_accounts": "country_code",
    "cash_transactions": "country_code",
    "payout_batch_items": "country_code",
    "admin_activity_logs": "country_code",
    "admin_analytics_snapshots": "country_code",
    "admin_change_audit_logs": "country_code",
    # "commissions": "country_code",  # table doesn't exist in DB
    # Financial & Treasury (missing tables added)
    "fiscal_periods": "country_code",
    "treasury_accounts": "country_code",
    "treasury_transactions": "country_code",
    "cash_flow_forecasts": "country_code",
    "cash_position_snapshots": "country_code",
    "gateway_settlement_schedules": "country_code",
    "ar_ledger_entries": "country_code",
    "ap_ledger_entries": "country_code",
    "financial_reports": "country_code",
    "vat_remittances": "country_code",
    "refund_ledger": "country_code",
    "finance_bank_accounts": "country_code",
    "transaction_ledgers": "country_code",
    "promotion_ledger_entries": "country_code",
}

logger = logging.getLogger(__name__)


def derive_country_aware_tables_from_db(engine=None) -> dict[str, str]:
    """Auto-derive the country-aware registry from the LIVE database.

    Any table that actually contains a ``country_code`` column (or the explicit
    special-case columns below) is treated as country-aware. Deriving from the
    connected DB — rather than the ORM models — guarantees we never inject an RLS
    filter against a column that is absent from the table (which would raise a
    "no such column" error and break otherwise-valid queries).

    This is the automation that keeps the RLS registry honest: new country-scoped
    tables are picked up automatically per environment, and the CI drift gate
    (see ``scripts/inventory_database.py --check``) flags any divergence between
    the models, the registry, and the DB.
    """
    from sqlalchemy import inspect

    if engine is None:
        from db.database import engine as engine

    try:
        insp = inspect(engine)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("RLS auto-derivation skipped (inspector unavailable): %s", exc)
        return dict(COUNTRY_AWARE_TABLES)

    explicit_columns = {"destination_country", "code"}
    derived: dict[str, str] = {}
    for table_name in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns(table_name)}
        if "country_code" in cols:
            derived[table_name] = "country_code"
        elif table_name in COUNTRY_AWARE_TABLES and COUNTRY_AWARE_TABLES[table_name] in explicit_columns:
            # Preserve hand-maintained special-case columns (e.g. destination_country).
            derived[table_name] = COUNTRY_AWARE_TABLES[table_name]
    return derived


def validate_rls_coverage(engine=None) -> list[str]:
    """Return a list of RLS drift issues for CI.

    Flags:
      * a registry entry whose table/column is missing from the live DB
      * a model table that declares ``country_code`` but is absent from the DB
        (orphaned model column — the migration to add it has not been applied)
    """
    from sqlalchemy import inspect

    if engine is None:
        from db.database import engine as engine

    issues: list[str] = []
    try:
        insp = inspect(engine)
    except Exception as exc:  # pragma: no cover - defensive
        return [f"inspector unavailable: {exc}"]

    db_tables = set(insp.get_table_names())
    for table_name, column_name in COUNTRY_AWARE_TABLES.items():
        if table_name not in db_tables:
            continue  # table not yet created; not a query-breaking issue
        cols = {c["name"] for c in insp.get_columns(table_name)}
        if column_name not in cols:
            issues.append(f"{table_name}: registry references missing column '{column_name}'")

    try:
        from models import Base
    except Exception:
        return issues

    for table in Base.metadata.tables.values():
        tname = table.name
        if tname not in db_tables:
            continue
        cols = {c["name"] for c in insp.get_columns(tname)}
        if "country_code" in {c.name for c in table.columns} and "country_code" not in cols:
            issues.append(f"{tname}: model declares country_code but DB column is missing")
    return issues


class SecurityContextMissingError(RuntimeError):
    """Raised when a country-aware query is executed without a security context."""


def set_rls_context(scope: set[str] | frozenset[str] | None, is_restricted: bool = True) -> None:
    rls_country_scope_ctx.set(frozenset(scope) if scope is not None else None)
    rls_is_restricted_ctx.set(is_restricted)


def clear_rls_context() -> None:
    rls_country_scope_ctx.set(None)
    rls_is_restricted_ctx.set(False)


def _extract_table_names(clause: Any) -> list[str]:
    tables: list[str] = []

    def _walk_froms(from_obj: Any) -> None:
        if hasattr(from_obj, "name"):
            tables.append(from_obj.name.lower())

        if hasattr(from_obj, "element"):
            _walk_froms(from_obj.element)
        if hasattr(from_obj, "froms"):
            for child in from_obj.froms:
                _walk_froms(child)

    if hasattr(clause, "froms"):
        for from_obj in clause.froms:
            _walk_froms(from_obj)

    # NOTE: Do NOT walk the WHERE clause for table names. Columns referenced in
    # the WHERE clause (e.g. `products.country_code`) would be re-resolved as a
    # second FROM entry, producing a Cartesian self-join (`FROM products, products`)
    # and "ambiguous column" errors once RLS appends its country filter.

    return tables


def _inject_country_filter(clause: Any, table_name: str, column_name: str, scope: frozenset[str]) -> Any:
    # Reuse the exact Table object already present in the query's FROM clause so the
    # injected column does not become a second (ambiguous) copy of the table.
    country_column = None
    try:
        for from_obj in getattr(clause, "froms", []) or []:
            table_obj = getattr(from_obj, "element", from_obj)
            candidate = getattr(table_obj, "columns", None)
            if candidate is not None and table_obj.name.lower() == table_name and column_name in candidate:
                country_column = candidate[column_name]
                break
    except Exception:
        country_column = None

    if country_column is None:
        from sqlalchemy import sql
        table = sql.table(table_name, sql.column(column_name))
        country_column = table.columns[column_name]

    filter_condition = country_column.in_(list(scope))

    if clause.whereclause is not None:
        new_where = clause.whereclause & filter_condition
        return clause.where(new_where)
    else:
        return clause.where(filter_condition)


@event.listens_for(Engine, "before_execute", retval=True)
def rls_before_execute(conn: Any, clause: Any, multiparams: Any, params: Any, execution_options: Any, **kwargs: Any) -> tuple[Any, Any, Any]:
    scope = rls_country_scope_ctx.get()
    is_restricted = rls_is_restricted_ctx.get()

    if not is_restricted:
        return clause, multiparams, params

    table_names = _extract_table_names(clause)

    for table_name in table_names:
        if table_name not in COUNTRY_AWARE_TABLES:
            continue

        if scope is None:
            raise SecurityContextMissingError(
                f"Query targets country-aware table '{table_name}' "
                f"but no RLS country scope is set. "
                f"Call set_rls_context() before executing this query."
            )

        column_name = COUNTRY_AWARE_TABLES[table_name]
        clause = _inject_country_filter(clause, table_name, column_name, scope)

    return clause, multiparams, params


def instrument_rls(engine: Engine) -> None:
    event.listen(engine, "before_execute", rls_before_execute, retval=True)
    logger.info("RLS interceptor installed on database engine")


def generate_rls_policy_sql(schema: str = "public") -> str:
    """Generate PostgreSQL CREATE POLICY SQL for all country-aware tables.

    Each table gets a policy that restricts rows based on the
    ``auth.country_access_check(<column>)`` security-definer function.
    """
    lines: list[str] = []

    lines.append(
        "CREATE OR REPLACE FUNCTION auth.country_access_check(p_country_code TEXT)\n"
        "RETURNS BOOLEAN AS $$\n"
        "DECLARE\n"
        "    v_role TEXT;\n"
        "BEGIN\n"
        "    SELECT current_user INTO v_role;\n"
        "\n"
        "    IF v_role = 'admin' OR v_role = 'postgres' OR v_role = 'service_role' THEN\n"
        "        RETURN TRUE;\n"
        "    END IF;\n"
        "\n"
        "    RETURN EXISTS (\n"
        "        SELECT 1\n"
        "        FROM country_staff_assignments csa\n"
        "        WHERE csa.country_code = p_country_code\n"
        "          AND csa.is_active = TRUE\n"
        "          AND csa.user_id = (\n"
        "              SELECT u.id FROM users u WHERE u.email = current_user LIMIT 1\n"
        "          )\n"
        "    );\n"
        "END;\n"
        "$$ LANGUAGE plpgsql SECURITY DEFINER;\n"
    )

    for table_name, column_name in COUNTRY_AWARE_TABLES.items():
        policy_name = f"{table_name}_rls_policy"
        lines.append(
            f"CREATE POLICY {policy_name}\n"
            f"    ON {schema}.{table_name}\n"
            f"    FOR ALL\n"
            f"    USING (\n"
            f"        {schema}.{table_name}.{column_name} IS NULL\n"
            f"        OR auth.country_access_check({schema}.{table_name}.{column_name})\n"
            f"    );\n"
        )

    return "\n".join(lines)


def install_rls_policies(engine: Engine, schema: str = "public") -> None:
    """Enable RLS and apply policies on every country-aware Postgres table."""
    from sqlalchemy import text

    policy_sql = generate_rls_policy_sql(schema=schema)

    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        for table_name in COUNTRY_AWARE_TABLES.keys():
            conn.execute(
                text(f"ALTER TABLE {schema}.{table_name} ENABLE ROW LEVEL SECURITY;")
            )
            conn.execute(text(f"ALTER TABLE {schema}.{table_name} FORCE ROW LEVEL SECURITY;"))

        conn.execute(text(policy_sql))

    logger.info("Installed RLS policies for %d tables", len(COUNTRY_AWARE_TABLES))

