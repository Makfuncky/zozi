"""Tests for security utilities and RBAC."""

import os
import time
import pytest
from jose import jwt, JWTError
from fastapi import HTTPException

from utils.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    blacklist_token,
    is_token_blacklisted,
    validate_password_complexity,
)
from utils.config import settings


@pytest.mark.integration
def test_password_hash_and_verify():
    password = os.environ.get("ZOZI_TEST_PASSWORD", "SecurePass1!")
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPass", hashed) is False


@pytest.mark.integration
def test_password_hash_truncates_long_input():
    long_password = "A" * 100 + "1!"
    hashed = get_password_hash(long_password)
    assert verify_password(long_password[:72], hashed) is True


@pytest.mark.integration
def test_access_token_contains_sub_and_role():
    token = create_access_token({"sub": "42", "role": "customer"})
    payload = decode_token(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "customer"
    assert payload["type"] == "access"


@pytest.mark.integration
def test_access_token_expires():
    token = create_access_token({"sub": "1", "role": "customer"}, expires_delta=__import__("datetime").timedelta(seconds=2))
    time.sleep(3)
    with pytest.raises(HTTPException):
        decode_token(token)


@pytest.mark.integration
def test_refresh_token_creation():
    token = create_refresh_token({"sub": "1", "role": "customer"})
    payload = decode_token(token)
    assert payload["type"] == "refresh"
    assert payload["sub"] == "1"


@pytest.mark.integration
def test_blacklist_token():
    token = create_access_token({"sub": "1", "role": "customer"})
    jti = decode_token(token).get("jti", "test-jti")
    blacklist_token(jti, ttl_seconds=60)
    assert is_token_blacklisted(jti) is True


@pytest.mark.integration
def test_invalid_token_rejected():
    with pytest.raises(HTTPException):
        decode_token("not.a.valid.token")


@pytest.mark.integration
def test_password_complexity_valid():
    assert validate_password_complexity("SecurePass1!") is None


@pytest.mark.integration
def test_password_complexity_too_short():
    with pytest.raises(HTTPException):
        validate_password_complexity("Ab1!")


@pytest.mark.integration
def test_password_complexity_no_digit():
    with pytest.raises(HTTPException):
        validate_password_complexity("SecurePass!")


@pytest.mark.integration
def test_password_complexity_no_uppercase():
    with pytest.raises(HTTPException):
        validate_password_complexity("securepass1!")


@pytest.mark.integration
def test_password_complexity_no_special():
    with pytest.raises(HTTPException):
        validate_password_complexity("SecurePass1")


@pytest.mark.integration
def test_decode_token_wrong_algorithm():
    token = jwt.encode({"sub": "1"}, "secret", algorithm="HS512")
    with pytest.raises(HTTPException):
        decode_token(token)
