"""Law-aligned architecture tests for the accounts domain.

Guarded laws (ARCHITECTURE_DIAGRAM.md):
  Law 3  - Cross-domain writes via events, reads via ports (no cross-domain FKs)
  Law 4  - Features single-sourced in features.py, aggregated by rbac/catalog.py
  Law 6  - Schema discipline: every table in a domain Postgres schema
  Law 21 - Timestamps use server_default (DB-side), not Python-side defaults
  Law 22 - Every ForeignKey declares explicit ondelete
  Law 23 - Audit columns: created_at, updated_at, country_code, is_deleted
  Law 52 - FK constraints with ondelete
  Law 55 - Schema-per-domain
"""
from __future__ import annotations

import pytest

from tests._support.laws import (
    assert_feature_in_catalog,
    assert_foreign_keys_have_ondelete,
    assert_schema_discipline,
    iter_domain_models,
)

# Ensure every accounts model submodule is registered with Base before
# iter_domain_models() collects them (conftest only imports a subset).
import domains.accounts.models.user  # noqa: F401
import domains.accounts.models.core  # noqa: F401
import domains.accounts.models.otp  # noqa: F401
import domains.accounts.models.social  # noqa: F401
import domains.accounts.models.onboarding  # noqa: F401
import domains.accounts.models.mfa_factor  # noqa: F401
import domains.accounts.models.user_consent  # noqa: F401
import domains.accounts.models.refresh_token_family  # noqa: F401
import domains.accounts.models.password_history  # noqa: F401
import domains.accounts.models.user_preference  # noqa: F401

DOMAIN = "accounts"


def _models():
    return list(iter_domain_models(DOMAIN))


def _model_schema(model):
    args = getattr(model, "__table_args__", None) or ()
    if isinstance(args, dict):
        return args.get("schema")
    for item in args:
        if isinstance(item, dict) and "schema" in item:
            return item["schema"]
    return None


def _cross_domain_fk_violations(model):
    """Law 3: FK references must not point outside the model's own domain schema."""
    schema = _model_schema(model)
    if not schema:
        return []
    bad = []
    for col in model.__table__.columns:
        for fk in col.foreign_keys:
            tgt_schema = fk.column.table.schema
            if tgt_schema and tgt_schema != schema:
                bad.append(
                    f"{model.__name__}.{col.name} -> {tgt_schema}.{fk.column.table.name}"
                )
    return bad


def _python_default_timestamp_columns(model):
    """Law 21: created_at/updated_at must use server_default, not Python default."""
    bad = []
    for name in ("created_at", "updated_at"):
        col = model.__table__.columns.get(name)
        if col is None:
            continue
        if col.server_default is None:
            bad.append(f"{model.__name__}.{name}")
    return bad


# ---------------------------------------------------------------------------
# Law 6 / 23 / 55 — schema discipline + audit columns for every model
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "model", _models(), ids=lambda m: m.__name__
)
def test_model_schema_discipline(model):
    """Every accounts model declares a domain schema and the four audit columns."""
    assert_schema_discipline(model)


# ---------------------------------------------------------------------------
# Law 22 / 52 — every FK declares ondelete
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "model", _models(), ids=lambda m: m.__name__
)
def test_model_foreign_keys_have_ondelete(model):
    assert_foreign_keys_have_ondelete(model)


# ---------------------------------------------------------------------------
# Law 3 — no cross-domain foreign keys
# ---------------------------------------------------------------------------

# Known Law-3 violations (cross-domain FKs awaiting migration). Each is an
# expected failure guarded by this test; fixing the FK removes the xfail.
_KNOWN_CROSS_DOMAIN_FK_VIOLATIONS = {
    # domains/accounts/models/core.py — Address/Cart/CartItem -> governance.users
    "Address.user_id",
    "Cart.user_id",
    "CartItem.user_id",
    # domains/accounts/models/core.py — CartItem -> commerce.products
    "CartItem.product_id",
    # domains/accounts/models/otp.py — OtpCode -> governance.users / country
    "OtpCode.user_id",
    "OtpCode.country_code",
    # domains/accounts/models/social.py — SocialIdentity -> governance.users
    "SocialIdentity.user_id",
    # domains/accounts/models/onboarding.py — pipelines -> governance.users,
    # OCRResult -> security.document_verifications
    "OnboardingPipeline.user_id",
    "OCRResult.document_verification_id",
}


@pytest.mark.parametrize(
    "model", _models(), ids=lambda m: m.__name__
)
def test_no_cross_domain_foreign_keys(model):
    """Law 3: FKs must reference tables inside the same domain schema."""
    violations = _cross_domain_fk_violations(model)
    known = {v for v in violations if v in _KNOWN_CROSS_DOMAIN_FK_VIOLATIONS}
    unknown = [v for v in violations if v not in _KNOWN_CROSS_DOMAIN_FK_VIOLATIONS]
    if unknown:
        pytest.fail(f"New cross-domain FK violations in accounts: {unknown}")
    if known:
        pytest.xfail(
            f"Known Law-3 cross-domain FKs (awaiting migration): {sorted(known)}"
        )


# ---------------------------------------------------------------------------
# Law 21 — timestamps use server_default
# ---------------------------------------------------------------------------

_KNOWN_PYTHON_DEFAULT_TIMESTAMPS: set[str] = set()


@pytest.mark.parametrize(
    "model", _models(), ids=lambda m: m.__name__
)
def test_timestamps_use_server_default(model):
    """Law 21: created_at/updated_at must default server-side."""
    bad = _python_default_timestamp_columns(model)
    known = [c for c in bad if c in _KNOWN_PYTHON_DEFAULT_TIMESTAMPS]
    unknown = [c for c in bad if c not in _KNOWN_PYTHON_DEFAULT_TIMESTAMPS]
    if unknown:
        pytest.fail(f"Python-side timestamp defaults in accounts: {unknown}")
    if known:
        pytest.xfail(f"Known Law-21 violations: {known}")


# ---------------------------------------------------------------------------
# Law 4 — features single-sourced and present in the catalog
# ---------------------------------------------------------------------------


def test_accounts_features_in_catalog():
    """Every accounts feature atom is registered in rbac/catalog.py (Law 4)."""
    from domains.accounts.features import FEATURES

    for feature in FEATURES:
        assert_feature_in_catalog(feature)


def test_accounts_events_file_is_wired():
    """Law 3: accounts/events.py exposes the cross-domain write surface."""
    from domains.accounts import events

    assert hasattr(events, "EVENT_USER_CREATED")
    assert hasattr(events, "publish_user_created")
    assert callable(events.publish_user_created)


def test_accounts_ports_file_is_wired():
    """Law 3: accounts/ports.py exposes the sanctioned read surface."""
    from domains.accounts import ports

    assert callable(ports.get_user_by_id)
    assert callable(ports.get_user_by_email)
    # Law 222 (keyset pagination): list helpers must exist.
    assert callable(ports.list_users)


def test_accounts_subscribers_file_is_wired():
    """Law 3: accounts/subscribers.py registers cross-domain reaction hooks."""
    from domains.accounts import subscribers

    assert callable(subscribers.register)
