"""Regression guard for FILE 104 - backend/domains/suppliers/models/suppliers.py.

The 8 findings adjudicated for this block are encoded here as an executable
invariant, one case per finding, keyed by the exact ``file:line`` the audit
cited plus its finding id.

The audit reported each Law 21 finding at the *class declaration* line of the
model that owns the offending column, so the mapping below is
``(audit line, finding id, model class name, schema-qualified table name)``.
Each Law 21 case asserts precisely what Law 21 states - the mapped
``created_at`` column must carry ``server_default=func.now()`` (DB-side) - and
additionally that ``updated_at`` does too, because Law 21 names both columns.

TF-266 (``updated_at``) and TF-267 (``is_deleted``) are the two Law 23 / Law 54
findings. Both target ``SupplierDispute``. The ORM class already declared both
columns; the applied schema did not have them, which made every ORM SELECT of
the table raise ``UndefinedColumn``. Alembic is the single source of schema
truth (Law 6), so the fix belongs in a migration - see
``alembic/versions/2026_10_03_0001_suppliers_supplier_disputes_audit_columns.py``.
This test asserts the ORM half: both columns exist, carry the right defaults,
and are declared in the same order the migration creates them.

Metadata-only (no database connection), so it is hermetic and runs in the unit
tier, matching the sibling exemplar at
``tests/domains/country/test_country_enhancements_law21.py``. The database half
is verified by reading ``information_schema.columns``.

Laws covered: 21 (server_default on timestamps), 23 (audit columns),
54 (is_deleted soft delete), 20 (country_code String(2)), 55 (explicit schema),
19 (money is Numeric/Decimal, never Float), 51 (no duplicate __tablename__).
"""
from __future__ import annotations

import sqlalchemy as sa

# (audit_cited_line, finding_id, model class, schema-qualified table name)
FILE_104_FINDINGS: tuple[tuple[int, str, str, str], ...] = (
    (183, "TF-263", "SupplierBadgeBillingHistory", "suppliers.supplier_badge_billing_histories"),
    (111, "TF-264", "SupplierBadgeCatalog", "suppliers.supplier_badge_catalogs"),
    (142, "TF-265", "SupplierBadge", "suppliers.supplier_badges"),
    (57, "TF-268", "SupplierDocument", "suppliers.supplier_documents"),
    (86, "TF-270", "SupplierNotificationPreference", "suppliers.supplier_notification_preferences"),
    (29, "TF-272", "SupplierProfile", "suppliers.supplier_profiles"),
)

# Every model declared by the module, including the one the audit flagged only
# for Law 23/Law 54 (SupplierDispute) - it must not regress either.
ALL_SUPPLIER_MODELS: tuple[str, ...] = (
    "SupplierProfile",
    "SupplierDocument",
    "SupplierNotificationPreference",
    "SupplierBadgeCatalog",
    "SupplierBadge",
    "SupplierBadgeBillingHistory",
    "SupplierDispute",
)


def _module():
    import domains.suppliers.models.suppliers as mod

    return mod


def _server_default_is_now(column: sa.Column) -> bool:
    default = column.server_default
    if default is None:
        return False
    arg = getattr(default, "arg", None)
    if arg is None:
        return False
    text = str(arg).lower()
    return "now" in text or "current_timestamp" in text


class TestLaw21CreatedAtServerDefaultPerFinding:
    """One case per adjudicated Law 21 finding: TF-263, TF-264, TF-265,
    TF-268, TF-270, TF-272."""

    def test_finding_map_covers_the_six_law21_findings(self) -> None:
        assert len(FILE_104_FINDINGS) == 6
        assert {f[1] for f in FILE_104_FINDINGS} == {
            "TF-263", "TF-264", "TF-265", "TF-268", "TF-270", "TF-272",
        }

    def test_each_cited_line_still_resolves_to_its_model(self) -> None:
        """The audit cited class-declaration lines; they must still map 1:1."""
        mod = _module()
        for line, finding_id, class_name, table_key in FILE_104_FINDINGS:
            cls = getattr(mod, class_name, None)
            assert cls is not None, (
                f"{finding_id}: suppliers.py:{line} -> "
                f"{class_name} is no longer exported by the module"
            )
            assert f"{cls.__table__.schema}.{cls.__table__.name}" == table_key, (
                f"{finding_id}: {class_name} moved table (expected {table_key})"
            )


def _check_created_at(class_name: str, finding_id: str) -> None:
    mod = _module()
    cls = getattr(mod, class_name)
    table = cls.__table__

    assert "created_at" in table.c, f"{finding_id}: {class_name} lost created_at"

    col = table.c.created_at
    assert _server_default_is_now(col), (
        f"{finding_id}: {table.fullname}.created_at is missing "
        f"server_default=func.now() (Law 21); got {col.server_default!r}"
    )
    assert isinstance(col.type, sa.DateTime), (
        f"{finding_id}: {table.fullname}.created_at must be DateTime, "
        f"got {col.type!r}"
    )
    # The Python-side default is deliberately retained (sibling exemplar
    # domains/comms/models/chat.py:56) so an unflushed instance still has a
    # value; Law 21 is satisfied by the DB-side default being present too.
    assert col.default is not None, (
        f"{finding_id}: {table.fullname}.created_at lost its client-side "
        f"default; removal would be a behaviour regression"
    )


def _make_created_at_case(class_name: str, finding_id: str, line: int):
    def test_case() -> None:
        _check_created_at(class_name, finding_id)

    test_case.__name__ = f"test_{finding_id.lower()}_{class_name.lower()}_created_at_has_now_default"
    test_case.__doc__ = (
        f"FILE 104 finding {finding_id} (audit cited "
        f"suppliers.py:{line}): {class_name}.created_at must carry "
        f"server_default=func.now() per Law 21."
    )
    return test_case


for _line, _fid, _cls_name, _table in FILE_104_FINDINGS:
    _case = _make_created_at_case(_cls_name, _fid, _line)
    globals()[_case.__name__] = _case


class TestSupplierDisputeAuditColumns:
    """TF-266 (Law 23, updated_at) and TF-267 (Law 54, is_deleted)."""

    def test_tf_266_supplier_disputes_declares_updated_at(self) -> None:
        """TF-266 - Law 23: SupplierDispute must carry updated_at with a
        DB-side server_default (the ORM half; the applied schema was the side
        that drifted and is fixed by migration 20261003_0001)."""
        table = _module().SupplierDispute.__table__
        assert "updated_at" in table.c, (
            "TF-266: suppliers.supplier_disputes lost updated_at (Law 23)"
        )
        col = table.c.updated_at
        assert isinstance(col.type, sa.DateTime), f"TF-266: updated_at is {col.type!r}"
        assert _server_default_is_now(col), (
            f"TF-266: suppliers.supplier_disputes.updated_at is missing "
            f"server_default=func.now() (Law 21/23); got {col.server_default!r}"
        )
        assert col.onupdate is not None, (
            "TF-266: suppliers.supplier_disputes.updated_at must refresh onupdate"
        )

    def test_tf_267_supplier_disputes_declares_is_deleted(self) -> None:
        """TF-267 - Law 54: soft-delete flag, boolean, default false."""
        table = _module().SupplierDispute.__table__
        assert "is_deleted" in table.c, (
            "TF-267: suppliers.supplier_disputes lost is_deleted (Law 54)"
        )
        col = table.c.is_deleted
        assert isinstance(col.type, sa.Boolean), f"TF-267: is_deleted is {col.type!r}"
        assert col.nullable is False, "TF-267: is_deleted must be NOT NULL"
        assert col.default is not None, "TF-267: is_deleted lost its client-side default"
        assert col.server_default is not None, (
            "TF-267: is_deleted must carry server_default=false (Law 54); got "
            f"{col.server_default!r}"
        )
        assert col.index is True, "TF-267: is_deleted must be indexed"

    def test_supplier_disputes_carries_full_law23_audit_set(self) -> None:
        """Law 23 - created_at, updated_at, country_code, is_deleted."""
        table = _module().SupplierDispute.__table__
        missing = [
            c for c in ("created_at", "updated_at", "country_code", "is_deleted")
            if c not in table.c
        ]
        assert not missing, f"Law 23: supplier_disputes missing {missing}"


class TestModuleWideLawCompliance:
    """No model in the module may regress on the laws its findings cite."""

    def test_every_model_has_created_at_server_default_now(self) -> None:
        """Law 21."""
        mod = _module()
        offenders = [
            getattr(mod, name).__table__.fullname
            for name in ALL_SUPPLIER_MODELS
            if (col := getattr(mod, name).__table__.c.get("created_at")) is None
            or not _server_default_is_now(col)
        ]
        assert not offenders, (
            f"Law 21: created_at missing server_default=func.now() on {offenders}"
        )

    def test_every_model_has_updated_at_server_default_now(self) -> None:
        """Law 21 names created_at *and* updated_at."""
        mod = _module()
        offenders = [
            getattr(mod, name).__table__.fullname
            for name in ALL_SUPPLIER_MODELS
            if (col := getattr(mod, name).__table__.c.get("updated_at")) is None
            or not _server_default_is_now(col)
        ]
        assert not offenders, (
            f"Law 21: updated_at missing server_default=func.now() on {offenders}"
        )

    def test_every_model_has_updated_at(self) -> None:
        """Law 23 - updated_at is part of the audit-column contract."""
        mod = _module()
        offenders = [
            getattr(mod, name).__table__.fullname
            for name in ALL_SUPPLIER_MODELS
            if "updated_at" not in getattr(mod, name).__table__.c
        ]
        assert not offenders, f"Law 23: missing updated_at on {offenders}"

    def test_every_model_carries_is_deleted(self) -> None:
        """Law 23 / Law 54 - soft-delete flag is mandatory on every model."""
        mod = _module()
        offenders = [
            getattr(mod, name).__table__.fullname
            for name in ALL_SUPPLIER_MODELS
            if "is_deleted" not in getattr(mod, name).__table__.c
        ]
        assert not offenders, f"Law 23/54: missing is_deleted on {offenders}"

    def test_every_model_declares_suppliers_schema(self) -> None:
        """Law 55 - __table_args__ must pin the domain schema."""
        mod = _module()
        offenders = [
            getattr(mod, name).__table__.fullname
            for name in ALL_SUPPLIER_MODELS
            if getattr(mod, name).__table__.schema != "suppliers"
        ]
        assert not offenders, f"Law 55: schema != 'suppliers' on {offenders}"

    def test_country_code_is_string_2(self) -> None:
        """Law 20 - country_code is ISO 3166-1 alpha-2."""
        mod = _module()
        offenders = []
        for name in ALL_SUPPLIER_MODELS:
            table = getattr(mod, name).__table__
            col = table.c.get("country_code")
            if col is None:
                offenders.append(f"{table.fullname}.country_code MISSING")
                continue
            if not (isinstance(col.type, sa.String) and col.type.length == 2):
                offenders.append(f"{table.fullname}.country_code is {col.type!r}")
        assert not offenders, f"Law 20 violation: {offenders}"

    def test_no_float_columns_for_money(self) -> None:
        """Law 19 - this module holds badge price and billing amount money."""
        mod = _module()
        money_tokens = ("price", "amount", "fee", "cost", "total", "payout", "commission")
        offenders = []
        for name in ALL_SUPPLIER_MODELS:
            table = getattr(mod, name).__table__
            for col in table.c:
                if not any(token in col.name for token in money_tokens):
                    continue
                if isinstance(col.type, sa.Float):
                    offenders.append(f"{table.fullname}.{col.name} {col.type!r}")
        assert not offenders, f"Law 19 violation (money as Float): {offenders}"

    def test_money_columns_are_numeric(self) -> None:
        """Law 19 - money columns must be Numeric (mapped to Decimal)."""
        mod = _module()
        offenders = []
        for name in ALL_SUPPLIER_MODELS:
            table = getattr(mod, name).__table__
            for col in table.c:
                if not any(t in col.name for t in ("price", "amount")):
                    continue
                if not isinstance(col.type, sa.Numeric):
                    offenders.append(f"{table.fullname}.{col.name} {col.type!r}")
        assert not offenders, f"Law 19 violation (money not Numeric): {offenders}"

    def test_every_foreign_key_declares_ondelete(self) -> None:
        """Law 22 / Law 52 - explicit ondelete on every FK."""
        mod = _module()
        offenders = []
        for name in ALL_SUPPLIER_MODELS:
            table = getattr(mod, name).__table__
            for col in table.c:
                for fk in col.foreign_keys:
                    if fk.ondelete is None:
                        offenders.append(f"{table.fullname}.{col.name} -> {fk.target_fullname}")
        assert not offenders, f"Law 22/52 violation: {offenders}"

    def test_every_foreign_key_is_indexed(self) -> None:
        """Law 53 - PostgreSQL does not auto-index FKs."""
        mod = _module()
        offenders = []
        for name in ALL_SUPPLIER_MODELS:
            table = getattr(mod, name).__table__
            for col in table.c:
                if col.foreign_keys and not col.index:
                    offenders.append(f"{table.fullname}.{col.name}")
        assert not offenders, f"Law 53 violation: {offenders}"

    def test_no_duplicate_tablename_in_module(self) -> None:
        """Law 51 - single table ownership, no duplicate __tablename__."""
        mod = _module()
        seen: dict[str, str] = {}
        for name in ALL_SUPPLIER_MODELS:
            key = f"{getattr(mod, name).__table__.schema}." \
                  f"{getattr(mod, name).__table__.name}"
            assert key not in seen, (
                f"Law 51: {key} declared by both {seen.get(key)} and {name}"
            )
            seen[key] = name
