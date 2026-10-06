"""Fail-before test: json_login_user must issue a TOTP challenge when MfaFactor exists.

R-06 left auth_service.py half-finished: authenticate_password reads from MfaFactor,
but json_login_user still checks the transient `user.totp_enabled` attribute, which
is not a mapped column. After enabling TOTP, json_login_user returns full tokens
instead of a 2FA challenge.
"""
from __future__ import annotations

import pyotp
from starlette.responses import Response

from domains.accounts.models.mfa_factor import MfaFactor
from domains.accounts.models.user import User
from domains.accounts.services.auth.auth_service import (
    complete_totp_login,
    create_temp_token,
    disable_totp,
    enable_totp,
    get_totp_status,
    json_login_user,
    setup_totp,
)
from fastapi import HTTPException
from infrastructure.utils.auth import get_password_hash


class LoginRequest:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password


def _make_user(db, email: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            hashed_password=get_password_hash("testpass123"),
            role="admin",
            country_code="AE",
            is_active=True,
            email_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def _ensure_employee(db, user: User) -> None:
    from domains.hr.models.employee_models import Employee
    from datetime import date
    emp = db.query(Employee).filter(Employee.user_id == user.id).first()
    if not emp:
        emp = Employee(
            user_id=user.id,
            employee_code=f"EMP-{user.id:06d}",
            hire_date=date(2024, 1, 1),
            country_code="AE",
            employment_status="active",
            is_deleted=False,
        )
        db.add(emp)
        db.commit()


def test_json_login_issues_totp_challenge_after_enrollment(db_session):
    db = db_session
    user = _make_user(db, "mfa-login-fail@zozi.com")
    current_user = {"id": user.id, "role": "admin"}
    setup_result = setup_totp(current_user, db)
    db.commit()

    totp = pyotp.TOTP(setup_result["secret"])
    valid_code = totp.now()
    enable_totp(current_user, db, valid_code)
    db.commit()

    factor = db.query(MfaFactor).filter(
        MfaFactor.user_id == user.id, MfaFactor.factor_type == "TOTP"
    ).first()
    assert factor is not None
    assert factor.enabled is True

    response = Response()
    db.close()
    new_db = db_session
    result = json_login_user(
        response,
        LoginRequest(email="mfa-login-fail@zozi.com", password="testpass123"),
        new_db,
    )
    assert "requires_2fa" in result, (
        f"json_login_user must return a 2FA challenge when TOTP is enabled, got: {result}"
    )
    assert result.get("requires_2fa") is True
    assert "temp_token" in result


def test_setup_totp_persists_factor_in_db(db_session):
    db = db_session
    user = _make_user(db, "mfa-setup-persist@zozi.com")
    current_user = {"id": user.id, "role": "admin"}
    result = setup_totp(current_user, db)
    db.commit()

    factor = db.query(MfaFactor).filter(
        MfaFactor.user_id == user.id, MfaFactor.factor_type == "TOTP"
    ).first()
    assert factor is not None, "setup_totp must create an MfaFactor record"
    assert factor.enabled is False
    assert factor.secret == result["secret"]
    assert result["secret"]  # secret returned to caller for QR scanning


def test_valid_totp_code_verifies_after_enrollment(db_session):
    db = db_session
    user = _make_user(db, "mfa-verify-diag@zozi.com")
    current_user = {"id": user.id, "role": "admin"}
    setup_result = setup_totp(current_user, db)
    db.commit()

    factor = db.query(MfaFactor).filter(
        MfaFactor.user_id == user.id, MfaFactor.factor_type == "TOTP"
    ).first()
    assert factor is not None

    totp = pyotp.TOTP(setup_result["secret"])
    valid_code = totp.now()
    enable_result = enable_totp(current_user, db, valid_code)
    db.commit()

    assert enable_result.get("detail") == "TOTP 2FA enabled successfully."
    factor_after = db.query(MfaFactor).filter(
        MfaFactor.user_id == user.id, MfaFactor.factor_type == "TOTP"
    ).first()
    assert factor_after.enabled is True
    assert len(enable_result.get("recovery_codes", [])) == 8


def test_invalid_totp_code_is_rejected(db_session):
    db = db_session
    user = _make_user(db, "mfa-invalid-diag@zozi.com")
    current_user = {"id": user.id, "role": "admin"}
    setup_totp(current_user, db)
    db.commit()

    try:
        enable_totp(current_user, db, "000000")
        raise AssertionError("Invalid TOTP code should have been rejected")
    except HTTPException as e:
        assert e.status_code == 400
        assert "Invalid TOTP code" in str(e.detail)


def test_replayed_recovery_code_is_rejected(db_session):
    db = db_session
    user = _make_user(db, "mfa-replay-diag@zozi.com")
    current_user = {"id": user.id, "role": "admin"}
    setup_result = setup_totp(current_user, db)
    db.commit()

    totp = pyotp.TOTP(setup_result["secret"])
    valid_code = totp.now()
    enable_totp(current_user, db, valid_code)
    db.commit()

    factor = db.query(MfaFactor).filter(
        MfaFactor.user_id == user.id, MfaFactor.factor_type == "TOTP"
    ).first()
    recovery_code = factor.backup_codes[0]

    # Use recovery code once — should succeed
    from domains.accounts.services.auth.auth_service import _verify_totp_code_with_fallback
    assert _verify_totp_code_with_fallback(db, user, recovery_code) is True
    db.commit()

    # Replay the same recovery code — should fail
    assert _verify_totp_code_with_fallback(db, user, recovery_code) is False


def test_get_totp_status_never_leaks_secret(db_session):
    db = db_session
    user = _make_user(db, "mfa-leak-diag@zozi.com")
    current_user = {"id": user.id, "role": "admin"}
    setup_result = setup_totp(current_user, db)
    db.commit()

    status = get_totp_status(current_user, db)
    assert "secret" not in str(status).lower()
    assert "totp_secret" not in str(status).lower()
    assert status.get("totp_enabled") is False


def test_disable_totp_removes_factor(db_session):
    db = db_session
    user = _make_user(db, "mfa-disable-diag@zozi.com")
    current_user = {"id": user.id, "role": "admin"}
    setup_result = setup_totp(current_user, db)
    db.commit()

    totp = pyotp.TOTP(setup_result["secret"])
    valid_code = totp.now()
    enable_totp(current_user, db, valid_code)
    db.commit()

    factor = db.query(MfaFactor).filter(
        MfaFactor.user_id == user.id, MfaFactor.factor_type == "TOTP"
    ).first()
    assert factor.enabled is True

    disable_totp(current_user, db, "testpass123")
    db.commit()

    factor_after = db.query(MfaFactor).filter(
        MfaFactor.user_id == user.id, MfaFactor.factor_type == "TOTP"
    ).first()
    assert factor_after is not None
    assert factor_after.enabled is False
    assert factor_after.is_deleted is True


def test_complete_totp_login_issues_tokens_after_valid_code(db_session):
    db = db_session
    user = _make_user(db, "mfa-complete-diag@zozi.com")
    current_user = {"id": user.id, "role": "admin"}
    setup_result = setup_totp(current_user, db)
    db.commit()

    totp = pyotp.TOTP(setup_result["secret"])
    valid_code = totp.now()
    enable_totp(current_user, db, valid_code)
    db.commit()

    # json_login issues a temp token challenge
    response = Response()
    login_result = json_login_user(
        response,
        LoginRequest(email="mfa-complete-diag@zozi.com", password="testpass123"),
        db,
    )
    assert login_result.get("requires_2fa") is True
    temp_token = login_result["temp_token"]

    # complete_totp_login should issue real tokens
    complete_result = complete_totp_login(temp_token, valid_code, db, response)
    assert "access_token" in complete_result
    assert "refresh_token" in complete_result


def test_authenticate_password_requires_totp_when_enabled(db_session):
    db = db_session
    user = _make_user(db, "mfa-door1-diag@zozi.com")
    _ensure_employee(db, user)
    current_user = {"id": user.id, "role": "admin"}
    setup_result = setup_totp(current_user, db)
    db.commit()

    totp = pyotp.TOTP(setup_result["secret"])
    valid_code = totp.now()
    enable_totp(current_user, db, valid_code)
    db.commit()

    from unittest import mock
    from domains.accounts.services.auth.auth_service import authenticate_password
    with mock.patch(
        "domains.accounts.services.auth.auth_service._check_login_rate_limit"
    ):
        try:
            authenticate_password(
                email="mfa-door1-diag@zozi.com",
                password="testpass123",
                totp_code=None,
                db=db,
            )
            raise AssertionError("authenticate_password should require TOTP code")
        except HTTPException as e:
            assert e.status_code == 428
            assert "TOTP code required" in str(e.detail)


def test_authenticate_password_succeeds_with_valid_totp(db_session):
    db = db_session
    user = _make_user(db, "mfa-door1-ok@zozi.com")
    _ensure_employee(db, user)
    current_user = {"id": user.id, "role": "admin"}
    setup_result = setup_totp(current_user, db)
    db.commit()

    totp = pyotp.TOTP(setup_result["secret"])
    valid_code = totp.now()
    enable_totp(current_user, db, valid_code)
    db.commit()

    # Generate a fresh code for authenticate_password (TOTP is time-bound)
    fresh_code = totp.now()
    from unittest import mock
    from domains.accounts.services.auth.auth_service import authenticate_password
    with mock.patch(
        "domains.accounts.services.auth.auth_service._check_login_rate_limit"
    ), mock.patch(
        "domains.accounts.services.auth.auth_service._issue_session",
        return_value={"access_token": "tok", "refresh_token": "rtok"},
    ):
        result = authenticate_password(
            email="mfa-door1-ok@zozi.com",
            password="testpass123",
            totp_code=fresh_code,
            db=db,
        )
    assert "access_token" in result
    assert "refresh_token" in result
