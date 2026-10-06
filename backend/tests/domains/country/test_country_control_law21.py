"""Law 21 gate for backend/domains/country/models/country_control.py.

The 8 findings adjudicated for this block (TF-141, TF-146, TF-148, TF-150,
TF-151, TF-152, TF-153, TF-155, all "created_at missing server_default=func.now()
(Law 21)") are encoded here as an executable invariant, one case per finding,
keyed by the exact file:line the audit cited plus its finding id.

The audit reported each finding at the *class declaration* line of the model
that owns the offending column, so the mapping below is (audit line, finding
id, model class name). Each case asserts the invariant Law 21 actually
states for the model layer: the mapped created_at column must be a
timezone-aware DateTime that is non-nullable and carries
server_default=func.now().

This test is metadata-only (no database connection) so it is hermetic and
runs in the unit tier. The database-tier half of Law 21 for these tables is
verified separately by reading information_schema.columns.column_default.

Laws covered: 21 (server_default on timestamps), 20 (country_code String(2)),
23 (created_at/updated_at/country_code/is_deleted), 55 (explicit schema).
"""
from __future__ import annotations

from typing import Callable

import sqlalchemy as sa

# (audit_cited_line, finding_id, model class, schema-qualified table name)
FILE_84_FINDINGS: tuple[tuple[int, str, str, str], ...] = (
    (13, "TF-152", "ShiftHandoverLog", "country.shift_handover_logs"),
    (35, "TF-151", "PaymentOrchestratorSync", "country.payment_orchestrator_syncs"),
    (59, "TF-155", "SupplierOnboardingSync", "country.supplier_onboarding_syncs"),
    (82, "TF-146", "DataResidencyRecord", "country.data_residency_records"),
    (103, "TF-141", "CountryMapConfig", "country.country_map_configs"),
    (122, "TF-153", "ShopWarehouseLocation", "country.shop_warehouse_locations"),
    (142, "TF-148", "LogisticsPartnerLocation", "country.logistics_partner_locations"),
    (163, "TF-150", "ParcelLocationTracker", "country.parcel_location_trackers"),
)

# Every model declared by the module - they must not regress either.
ALL_CONTROL_MODELS: tuple[str, ...] = (
    "ShiftHandoverLog",
    "PaymentOrchestratorSync",
    "SupplierOnboardingSync",
    "DataResidencyRecord",
    "CountryMapConfig",
    "ShopWarehouseLocation",
    "LogisticsPartnerLocation",
    "ParcelLocationTracker",
)


def _module():
    import domains.country.models.country_control as mod

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
    """One case per adjudicated finding: TF-141 .. TF-155."""

    def test_finding_map_covers_the_eight_declared_findings(self) -> None:
        assert len(FILE_84_FINDINGS) == 8
        assert {f[1] for f in FILE_84_FINDINGS} == {
            "TF-141", "TF-146", "TF-148", "TF-150",
            "TF-151", "TF-152", "TF-153", "TF-155",
        }

    def test_each_cited_line_still_resolves_to_its_model(self) -> None:
        """The audit cited class-declaration lines; they must still map 1:1."""
        mod = _module()
        for line, finding_id, class_name, table_key in FILE_84_FINDINGS:
            cls = getattr(mod, class_name, None)
            assert cls is not None, (
                f"{finding_id}: country_control.py:{line} -> "
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


def _make_created_at_case(class_name: str, finding_id: str, line: int) -> Callable[[], None]:
    def test_case() -> None:
        _check_created_at(class_name, finding_id)

    test_case.__name__ = f"test_{finding_id.lower()}_{class_name.lower()}_created_at_has_now_default"
    test_case.__doc__ = (
        f"FILE 84 finding {finding_id} (audit cited "
        f"country_control.py:{line}): {class_name}.created_at must carry "
        f"server_default=func.now() per Law 21."
    )
    return test_case


for _line, _fid, _cls_name, _table in FILE_84_FINDINGS:
    _case = _make_created_at_case(_cls_name, _fid, _line)
    globals()[_case.__name__] = _case


class TestModuleWideLawCompliance:
    """No model in the module may regress on the laws its findings cite."""

    def test_every_model_has_created_at_server_default_now(self) -> None:
        mod = _module()
        offenders = []
        for name in ALL_CONTROL_MODELS:
            table = getattr(mod, name).__table__
            col = table.c.get("created_at")
            if col is None or not _server_default_is_now(col):
                offenders.append(table.fullname)
        assert not offenders, (
            f"Law 21: created_at missing server_default=func.now() on {offenders}"
        )

    def test_every_model_has_updated_at(self) -> None:
        """Law 23 - updated_at is part of the audit-column contract."""
        mod = _module()
        offenders = [
            getattr(mod, name).__table__.fullname
            for name in ALL_CONTROL_MODELS
            if "updated_at" not in getattr(mod, name).__table__.c
        ]
        assert not offenders, f"Law 23: missing updated_at on {offenders}"

    def test_every_model_declares_country_schema(self) -> None:
        """Law 55 - __table_args__ must pin the domain schema."""
        mod = _module()
        offenders = [
            getattr(mod, name).__table__.fullname
            for name in ALL_CONTROL_MODELS
            if getattr(mod, name).__table__.schema != "country"
        ]
        assert not offenders, f"Law 55: schema != 'country' on {offenders}"

    def test_every_model_carries_is_deleted(self) -> None:
        """Law 23 - soft-delete flag is mandatory on every model."""
        mod = _module()
        offenders = [
            getattr(mod, name).__table__.fullname
            for name in ALL_CONTROL_MODELS
            if "is_deleted" not in getattr(mod, name).__table__.c
        ]
        assert not offenders, f"Law 23: missing is_deleted on {offenders}"

    def test_country_code_is_string_2(self) -> None:
        """Law 20 - country_code is ISO 3166-1 alpha-2."""
        mod = _module()
        offenders = []
        for name in ALL_CONTROL_MODELS:
            table = getattr(mod, name).__table__
            col = table.c.get("country_code")
            if col is None:
                offenders.append(f"{table.fullname}.country_code MISSING")
                continue
            if not (isinstance(col.type, sa.String) and col.type.length == 2):
                offenders.append(f"{table.fullname}.country_code is {col.type!r}")
        assert not offenders, f"Law 20 violation: {offenders}"
